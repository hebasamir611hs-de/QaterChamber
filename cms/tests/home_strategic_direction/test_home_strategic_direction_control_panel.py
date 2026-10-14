"""
cms/tests/home_strategic_direction/test_home_strategic_direction_control_panel.py
— Control_Panel cases for PBI 129381 (Home — Strategic Direction / Strategic
Pillar Cards), suite 134452, Test Plan 133534.

REWRITTEN 2026-10-07 (Phase 3, A-129381) to the 7-state workflow:
  - Object Authoring only (`manage-strategic-pillar-card`), via
    StrategicPillarCardAdminPage. No Content & Data, no TEST_USER.
  - Every case names its account: Site Content Editor (Submit for Review ->
    Published directly), Site Content Author (-> Pending Review), Site Member
    (denied). Credentials come from `cms_role_credentials()`.
  - Every record is a disposable `QCTEST-<tc_id>-<short>` card, deleted every
    run through the page's guarded `delete_disposable()` (exact QCTEST title,
    single row, entry id not one of 49056/49082/49108, form title re-read).
  - Public checks run in a fresh logged-out context (`authoring_checks`'
    probe), with both gates: status Published AND Active Status ticked.

ZERO WRITES TO REAL PILLARS. The cases naming the real Mission (135557, 135619),
Objectives (135558, 135619, 135620, 135621) or Vision (135622) card run on
QCTEST cards instead. The literal real-record variants are listed under
NEEDS USER in .claude/qa-runs/phase3_129381_2026-10-07_report.md — Mission
49082 needs ID-named approval, and Objectives 49108 was already destroyed
once by this PBI's batch.

SECTION-LEVEL cases ("section" heading/tag/description, section
publish/unpublish): Content-Admin-Guide §7 defines only StrategicPillarCard
for this section. The card-level variants of 135559/135560/135561/135562 are
scripted here as disclosed substitutions; the purely section-level cases
(135538, 135555, 135574-135590, 135624) are NEEDS USER.

Public carousel interplay: the web module asserts exactly 3 real cards; the
QCTEST cards here are published into the same carousel (Display Order 9900+,
after the real 100/200/300). Run the web module and this module in separate
invocations, web first.
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.components.disposable_object_admin import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    qctest_title,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.home_strategic_direction.home_strategic_direction_admin_page import (
    REAL_PILLAR_TITLES,
    StrategicPillarCardAdminPage,
)
from cms.tests import authoring_checks as ac
from config.settings import web_url

ADMIN = StrategicPillarCardAdminPage
FILES = StrategicPillarCardAdminPage.FILES
PNG_400KB = "cms/tests/home_social_icons/fixtures/icon_500kb.png"
SVG_50KB = "cms/tests/podcast/fixtures/valid_icon_45kb.svg"
STATUS_INACTIVE_RAW = "INACTIVE"  # Published + Active Status unticked renders this badge (2026-10-07)


def _open_home(anon) -> None:
    anon.goto(web_url("/home"), wait_until="domcontentloaded")
    anon.locator("section, .qc-sd-stage").first.wait_for(state="attached", timeout=30000)


PROBE = ac.make_public_probe(_open_home)


def _real_cards_present(anon) -> list[str]:
    """Positive control for every negative public check: the 3 real pillar
    titles still render (so 'absent' cannot pass on a broken page)."""
    _open_home(anon)
    titles = [t.strip() for t in anon.locator(".qc-sd-card .qc-sd-card-title").all_inner_texts()]
    return [t for t in REAL_PILLAR_TITLES if t not in titles]


def _public_titles(anon) -> list[str]:
    _open_home(anon)
    return [t.strip() for t in anon.locator(".qc-sd-card .qc-sd-card-title").all_inner_texts()]


def _marks(tc: int, severity=allure.severity_level.CRITICAL):
    def deco(fn):
        for m in (pytest.mark.control_panel, pytest.mark.about, pytest.mark.pbi_129381):
            fn = m(fn)
        fn = allure.label("pbi", "129381")(fn)
        fn = allure.label("testcase", str(tc))(fn)
        return allure.severity(severity)(fn)
    return deco


# =============================================================================
# Access (Auth)
# =============================================================================
@_marks(135548, allure.severity_level.NORMAL)
@pytest.mark.tc_135548
@allure.title("Site Content Editor can open the Strategic Pillar Card management screen")
def test_editor_can_access_management_screen(page):
    """TC 135548 — account: QC Site Content Editor. The form renders every
    pillar field and the entries list loads."""
    ac.check_form_renders(page, ADMIN, list(ADMIN.FIELDS))
    admin = ADMIN(page)
    admin.open_list(ROLE_EDITOR)
    assert admin.has_entries(), "Editor sees no entries on manage-strategic-pillar-card"


@_marks(135549)
@pytest.mark.tc_135549
@allure.title("A user without a content role cannot open the management screen")
def test_member_cannot_access_management_screen(page):
    """TC 135549 — account: QC site member (no CMS role); denial asserted
    positively after a confirmed sign-in."""
    ac.check_member_denied(page, ADMIN)


@_marks(135550)
@pytest.mark.tc_135550
@allure.title("An unauthenticated request to the management URL is sent to sign-in")
def test_anonymous_redirected_to_login(browser):
    """TC 135550 — no session (fresh logged-out context)."""
    ac.check_anonymous_denied(browser, ADMIN)


@_marks(135551, allure.severity_level.NORMAL)
@pytest.mark.tc_135551
@allure.title("Site Content Author can save a draft but cannot publish")
def test_author_saves_draft_but_cannot_publish(page):
    """TC 135551 — account: QC Site Content Author. Draft saves; Submit for
    Review lands on Pending Review (never Published) and the Author is offered
    no Approve / Publish row action. Teardown as Editor."""
    admin = ADMIN(page)
    title = qctest_title(135551, "author")
    try:
        admin.open_form(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), ac.NOT_ROLE
        admin.fill_required(title, active=True, files=FILES)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_DRAFT, "Author's draft did not save as Draft"
        admin.open_entry_by_edit_link(title)
        # The submit label differs per object/role (Submit for Review /
        # Submit for Publishing / Publish) — recorded, not asserted (Rule 5).
        allure.attach(admin.submit_button_label(), "Author submit button label", allure.attachment_type.TEXT)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_PENDING_REVIEW, (
            "Author's submit did not land on Pending Review (publish was not blocked)"
        )
        assert not admin.row_offers_action(title, "approve"), "Author is offered Approve on its own entry"
        assert not admin.row_offers_action(title, "publish"), "Author is offered Publish on its own entry"
    finally:
        admin.delete_disposable(title, ROLE_EDITOR)


# =============================================================================
# Lifecycle (Functional-High)
# =============================================================================
@_marks(135556)
@pytest.mark.tc_135556
@pytest.mark.xdist_group("strategic_pillar_carousel")
@pytest.mark.functional_high
@pytest.mark.regression
@allure.title("Site Content Editor creates, previews, publishes and sees a new pillar card live")
def test_create_preview_publish_new_pillar_card(page, browser):
    """TC 135556 — account: QC Site Content Editor. Draft -> row Preview ->
    Submit for Review (Editor: Published directly) -> Active Status ticked ->
    a logged-out visitor sees the card on /home."""
    admin = ADMIN(page)
    title = qctest_title(135556, "new-card")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True, submit=False)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        admin.filter_entries(title)
        preview = admin.row_preview_url(title)
        assert preview, f"{title!r}: the Draft row offers no Preview link"
        admin.open(preview)
        assert title in page.locator("body").inner_text(), "Preview did not render the draft card"
        admin.open_by_title(title)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        admin.open_by_title(title)
        assert admin.flag("active_status"), "Active Status is not ticked (second visibility gate)"
        assert PROBE(anon, title), f"{title!r} is Published + Active but not on the public Home Page"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135557)
@pytest.mark.tc_135557
@pytest.mark.xdist_group("strategic_pillar_carousel")
@pytest.mark.functional_high
@pytest.mark.regression
@allure.title("Editing a published pillar card's description reflects on the Home Page")
def test_edit_published_card_reflects_on_home_page(page, browser):
    """TC 135557 — account: QC Site Content Editor. Substitution: a published
    QCTEST card stands in for the real Mission card (49082 — needs ID-named
    approval; NEEDS USER). Edit the description, Submit for Review, the
    record stays Published and a logged-out visitor sees the new text."""
    admin = ADMIN(page)
    title = qctest_title(135557, "edit-desc")
    new_desc = "QCTEST-135557 edited pillar description"
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, title), f"precondition: {title!r} not public after publish"
        admin.open_by_title(title)
        admin.fill("pillar_description", new_desc)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        admin.open_by_title(title)
        assert admin.value("pillar_description") == new_desc
        assert PROBE(anon, new_desc), "public Home Page does not show the edited description"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135558)
@pytest.mark.tc_135558
@pytest.mark.xdist_group("strategic_pillar_carousel")
@pytest.mark.functional_high
@allure.title("Deleting a pillar card removes it from the Home Page")
def test_delete_card_removes_it_from_home_page(page, browser):
    """TC 135558 — account: QC Site Content Editor. Substitution: a published
    QCTEST card stands in for the real Objectives card (never deleted).
    After the guarded delete the card is gone from the list and the public
    carousel, and the 3 real cards still render."""
    admin = ADMIN(page)
    title = qctest_title(135558, "delete")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, title), f"precondition: {title!r} not public after publish"
        assert admin.delete_disposable(title), f"{title!r}: guarded delete did not complete"
        assert not admin.entry_exists(title, ROLE_EDITOR), f"{title!r} still in the entries list"
        assert not PROBE(anon, title, False), f"{title!r} still on the Home Page after delete"
        assert not _real_cards_present(anon), "a real pillar card disappeared from the carousel"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135559)
@pytest.mark.tc_135559
@pytest.mark.xdist_group("strategic_pillar_carousel")
@pytest.mark.functional_high
@allure.title("Unpublishing a pillar card removes it from the Home Page")
def test_unpublish_removes_card_from_home_page(page, browser):
    """TC 135559 — account: QC Site Content Editor. Card-level substitution
    for "the section" (no section object exists). Published -> Unpublish ->
    status Unpublished (not Draft) -> not public; real cards still render."""
    admin = ADMIN(page)
    title = qctest_title(135559, "unpublish")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, title), f"precondition: {title!r} not public after publish"
        admin.open_list(ROLE_EDITOR)
        admin.unpublish_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_UNPUBLISHED
        assert not PROBE(anon, title, False), f"{title!r} is Unpublished but still public"
        assert not _real_cards_present(anon), "positive control failed: real cards missing"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135560)
@pytest.mark.tc_135560
@pytest.mark.xdist_group("strategic_pillar_carousel")
@pytest.mark.functional_high
@allure.title("Save as Draft does not expose the change to public visitors")
def test_draft_not_public(page, browser):
    """TC 135560 — account: QC Site Content Editor. Card-level substitution:
    a new QCTEST card saved as Draft (Active ticked) is not public."""
    admin = ADMIN(page)
    title = qctest_title(135560, "draft")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True, submit=False)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        assert not PROBE(anon, title, False), f"{title!r} (Draft) is visible to a logged-out visitor"
        assert not _real_cards_present(anon), "positive control failed: real cards missing"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135561)
@pytest.mark.tc_135561
@pytest.mark.xdist_group("strategic_pillar_carousel")
@pytest.mark.functional_high
@allure.title("Submit for Review does not publish until approved")
def test_submit_for_review_not_public_until_approved(page, browser):
    """TC 135561 — account: QC Site Content AUTHOR. The TC says "Site
    Content Editor", but an Editor's submit bypasses review by design
    (standards.md, 7-state workflow), so the review gate is only observable
    as Author (NEEDS USER: TC wording). Submit -> Pending Review -> not
    public; then Editor approves -> Published -> public."""
    admin = ADMIN(page)
    title = qctest_title(135561, "review")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, role=ROLE_AUTHOR, active=True)
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_PENDING_REVIEW
        assert not PROBE(anon, title, False), f"{title!r} (Pending Review) is already public"
        assert not _real_cards_present(anon), "positive control failed: real cards missing"
        admin.open_list(ROLE_EDITOR)
        admin.approve_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, title), f"{title!r} approved + Active but not public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135562)
@pytest.mark.tc_135562
@pytest.mark.functional_high
@pytest.mark.regression
@allure.title("Publishing is blocked when a mandatory field is left empty")
def test_publish_blocked_when_mandatory_field_empty(page):
    """TC 135562 — account: QC Site Content Editor. No "Section Heading"
    field exists; the card's mandatory EN title (Pillar Title) is left empty
    on a new QCTEST card. Submit for Review is refused and nothing is
    published. (Message wording is not asserted — Rule 5.) Mission 49082 is
    not touched."""
    ac.check_empty_refused(page, ADMIN, 135562, "pillar_title", side="en", files=FILES)


# =============================================================================
# Field cases (Functional-Low, P2) — QCTEST drafts, Editor
# =============================================================================
@_marks(135591, allure.severity_level.NORMAL)
@pytest.mark.tc_135591
@allure.title("Pillar Icon accepts a valid PNG under 2 MB")
def test_icon_accepts_png(page):
    """TC 135591 — account: QC Site Content Editor; ~500 KB PNG fixture."""
    ac.check_file_accepted(page, ADMIN, 135591, "pillar_icon", PNG_400KB)


@_marks(135592, allure.severity_level.NORMAL)
@pytest.mark.tc_135592
@allure.title("Pillar Icon accepts a valid SVG under 2 MB")
def test_icon_accepts_svg(page):
    """TC 135592 — account: QC Site Content Editor; 45 KB SVG fixture."""
    ac.check_file_accepted(page, ADMIN, 135592, "pillar_icon", SVG_50KB)


@_marks(135593, allure.severity_level.NORMAL)
@pytest.mark.tc_135593
@allure.title("Submit is refused when no Pillar Icon is selected")
def test_icon_required(page):
    """TC 135593 — account: QC Site Content Editor."""
    ac.check_publish_refused(page, ADMIN, 135593, skip=("pillar_icon",), files=FILES)


@_marks(135598, allure.severity_level.NORMAL)
@pytest.mark.tc_135598
@allure.title("Pillar Title (EN) accepts valid text and persists")
def test_title_en_valid(page):
    """TC 135598 — account: QC Site Content Editor. "Vision" is carried in
    the QCTEST name (QCTEST-135598-Vision) so the record stays disposable."""
    ac.check_valid_persists(page, ADMIN, 135598, "pillar_title", "Vision", files=FILES)


@_marks(135599, allure.severity_level.NORMAL)
@pytest.mark.tc_135599
@allure.title("Pillar Title (EN) empty is refused")
def test_title_en_empty(page):
    """TC 135599 — account: QC Site Content Editor."""
    ac.check_empty_refused(page, ADMIN, 135599, "pillar_title", side="en", files=FILES)


@_marks(135602, allure.severity_level.NORMAL)
@pytest.mark.tc_135602
@allure.title("Pillar Title (AR) accepts valid Arabic text and persists")
def test_title_ar_valid(page):
    """TC 135602 — account: QC Site Content Editor; AR = "الرؤية"."""
    admin = ADMIN(page)
    title = qctest_title(135602, "ar-title")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=FILES)
        admin.fill("pillar_title", "الرؤية", locale="ar")
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        assert admin.value("pillar_title", "ar") == "الرؤية"
    finally:
        admin.delete_disposable(title)


@_marks(135603, allure.severity_level.NORMAL)
@pytest.mark.tc_135603
@allure.title("Pillar Title (AR) empty is refused")
def test_title_ar_empty(page):
    """TC 135603 — account: QC Site Content Editor. EN title is a QCTEST
    title (so a wrongly-accepted record is still found and torn down), AR
    title empty; Submit for Review must be refused and nothing published."""
    admin = ADMIN(page)
    title = qctest_title(135603, "ar-empty")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=FILES)
        admin.fill("pillar_title", "", locale="ar")
        ac._submit_and_expect_refusal(admin, title, "Pillar Title (AR) empty")
    finally:
        admin.delete_disposable(title)


@_marks(135606, allure.severity_level.NORMAL)
@pytest.mark.tc_135606
@allure.title("Pillar Description (EN) keeps text and bold formatting")
def test_description_en_formatted(page):
    """TC 135606 — account: QC Site Content Editor. Types plain text, then a
    bold phrase (Ctrl+B) in the EN editor; after save + reopen the text and
    a <strong>/<b> element survive."""
    _bold_description(page, 135606)


def _bold_description(page, tc: int) -> None:
    admin = ADMIN(page)
    title = qctest_title(tc, "bold")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=("pillar_description",), files=FILES)
        admin.fill("pillar_description", "وصف", locale="ar")
        body = page.frame_locator(admin._rich_iframe("pillar_description", "en")).locator("body")
        body.click()
        page.keyboard.type("To achieve global leadership ")
        page.keyboard.press("Control+B")
        page.keyboard.type("among chambers of commerce")
        page.keyboard.press("Control+B")
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        body = page.frame_locator(admin._rich_iframe("pillar_description", "en")).locator("body")
        html = body.inner_html()
        assert "To achieve global leadership" in body.inner_text()
        assert ("<strong>among chambers of commerce" in html) or ("<b>among chambers of commerce" in html), (
            f"bold formatting not persisted: {html[:300]!r}"
        )
    finally:
        admin.delete_disposable(title)


@_marks(135607, allure.severity_level.NORMAL)
@pytest.mark.tc_135607
@allure.title("Pillar Description (EN) empty is refused")
def test_description_en_empty(page):
    """TC 135607 — account: QC Site Content Editor."""
    ac.check_empty_refused(page, ADMIN, 135607, "pillar_description", side="en", files=FILES)


@_marks(135610, allure.severity_level.NORMAL)
@pytest.mark.tc_135610
@allure.title("Pillar Description (AR) accepts Arabic text and persists")
def test_description_ar_valid(page):
    """TC 135610 — account: QC Site Content Editor."""
    ac.check_valid_persists(
        page, ADMIN, 135610, "pillar_description",
        "QCTEST EN description", ar="تحقيق الريادة العالمية بين غرف التجارة", files=FILES,
    )


@_marks(135611, allure.severity_level.NORMAL)
@pytest.mark.tc_135611
@allure.title("Pillar Description (AR) empty is refused")
def test_description_ar_empty(page):
    """TC 135611 — account: QC Site Content Editor."""
    ac.check_empty_refused(page, ADMIN, 135611, "pillar_description", side="ar", files=FILES)


@_marks(135613, allure.severity_level.NORMAL)
@pytest.mark.tc_135613
@allure.title("Display Order accepts a valid positive integer and persists")
def test_display_order_valid(page):
    """TC 135613 — account: QC Site Content Editor. The TC's value 1 is used
    on a Draft only (never published), so it cannot reorder the live
    carousel; the editorial multiples-of-100 convention is noted in the
    report, not enforced here."""
    ac.check_valid_persists(page, ADMIN, 135613, "display_order", "1", files=FILES)


@_marks(135614, allure.severity_level.NORMAL)
@pytest.mark.tc_135614
@allure.title("Display Order empty is refused")
def test_display_order_empty(page):
    """TC 135614 — account: QC Site Content Editor."""
    ac.check_publish_refused(page, ADMIN, 135614, skip=("display_order",), files=FILES)


# =============================================================================
# Ordering / Active Status → public (Functional-Low, P2)
# =============================================================================
@_marks(135619, allure.severity_level.NORMAL)
@pytest.mark.tc_135619
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Changing Display Order changes the card's carousel position")
def test_display_order_reorders_carousel(page, browser):
    """TC 135619 — account: QC Site Content Editor. Substitution: two
    QCTEST cards (A=9800, B=9900) stand in for the real Mission/Objectives
    (NEEDS USER for the literal swap). After swapping to A=9900/B=9800 the
    public carousel order flips."""
    admin = ADMIN(page)
    a, b = qctest_title(135619, "A"), qctest_title(135619, "B")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(a, active=True, display_order="9800")
        admin.create(b, active=True, display_order="9900")
        assert admin.status_of(a, ROLE_EDITOR) == STATUS_PUBLISHED
        assert admin.status_of(b, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, b), "precondition: B not public"
        before = _public_titles(anon)
        assert before.index(a) < before.index(b), f"precondition order wrong: {before}"
        for title, order in ((a, "9900"), (b, "9800")):
            admin.open_by_title(title)
            admin.fill("display_order", order)
            admin.submit_for_review()
            assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED

        from core.utils.waits import WaitTimeoutError, wait_until
        seen = {"t": before}

        def _flipped() -> bool:
            seen["t"] = _public_titles(anon)
            return a in seen["t"] and b in seen["t"] and seen["t"].index(b) < seen["t"].index(a)

        try:
            wait_until(_flipped, timeout=60, poll=3, message="carousel order did not follow Display Order")
        except WaitTimeoutError:
            pass
        assert _flipped(), f"carousel order did not follow the new Display Order: {seen['t']}"
        assert seen["t"][:3] == list(REAL_PILLAR_TITLES), f"real cards no longer first: {seen['t']}"
    finally:
        admin.delete_disposable(a)
        admin.delete_disposable(b)
        ac._close(ctx)


@_marks(135620, allure.severity_level.NORMAL)
@pytest.mark.tc_135620
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Active Status = True shows the card on the Home Page")
def test_active_true_shows_card(page, browser):
    """TC 135620 — account: QC Site Content Editor. Substitution: a QCTEST
    card instead of the real Objectives card."""
    ac.check_editor_publish_public(page, browser, ADMIN, 135620, PROBE, files=FILES)


@_marks(135621, allure.severity_level.NORMAL)
@pytest.mark.tc_135621
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Active Status = False keeps the card off the Home Page")
def test_active_false_hides_card(page, browser):
    """TC 135621 — account: QC Site Content Editor. A QCTEST card submitted
    with Active Status unticked (status reads Published or the build's
    'Inactive' badge) is not public; real cards still render."""
    admin = ADMIN(page)
    title = qctest_title(135621, "inactive")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=False)
        raw = admin.raw_row_status(title)
        assert raw in ("PUBLISHED", STATUS_INACTIVE_RAW), f"{title!r} status after Editor submit: {raw!r}"
        assert not PROBE(anon, title, False), f"{title!r} (Active unticked) is public"
        assert not _real_cards_present(anon), "positive control failed: real cards missing"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135622, allure.severity_level.NORMAL)
@pytest.mark.tc_135622
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Toggling a published card to Inactive hides it but keeps the record")
def test_toggle_inactive_hides_but_keeps_record(page, browser):
    """TC 135622 — account: QC Site Content Editor. Substitution: a published
    QCTEST card instead of the real Vision card. Untick Active, Submit for
    Review: the card leaves the Home Page, the record stays in the list."""
    admin = ADMIN(page)
    title = qctest_title(135622, "toggle")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, title), f"precondition: {title!r} not public"
        admin.open_by_title(title)
        admin.set_flag("active_status", False)
        admin.submit_for_review()
        assert not PROBE(anon, title, False), f"{title!r} is still public after Active Status was unticked"
        assert admin.entry_exists(title, ROLE_EDITOR), f"{title!r} record was removed, not just hidden"
        assert not _real_cards_present(anon), "positive control failed: real cards missing"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


# =============================================================================
# Already-scripted P3
# =============================================================================
@_marks(135563, allure.severity_level.NORMAL)
@pytest.mark.tc_135563
@pytest.mark.functional_high
@allure.title("Abandoning the Add Pillar Card form discards the entered data")
def test_abandon_add_form_discards_data(page):
    """TC 135563 — account: QC Site Content Editor. The create form has no
    Cancel button; abandoning it (navigating away without Save/Submit) is the
    real equivalent. No record with the QCTEST title may exist afterwards."""
    admin = ADMIN(page)
    title = qctest_title(135563, "abandoned")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=FILES)
        admin.open_entries_list(locale="en")
        assert not admin.row_visible(title), f"{title!r} was created although the form was abandoned"
    finally:
        admin.delete_disposable(title)


# =============================================================================
# USER ORDER 2026-10-07 22:45 — every case executed. P3/P4 pillar-card cases.
# All on QCTEST cards, account QC Site Content Editor unless stated.
# =============================================================================
BIG_PNG_2_5MB = "cms/tests/home_social_icons/fixtures/icon_2_5mb.png"
JPG_500KB = "cms/tests/podcast/fixtures/valid_image_500kb.jpg"
PILLAR_PNG = StrategicPillarCardAdminPage.FILES["pillar_icon"]
AR_TITLE_NAME = "#qc-ar-pillarTitle"
EN_TITLE_NAME = 'input[name="ObjectField_pillarTitle"]'


def _attach(name: str, text) -> None:
    allure.attach(str(text), name, allure.attachment_type.TEXT)


def _has_arabic(text: str) -> bool:
    return any(0x0600 <= ord(ch) <= 0x06FF for ch in text or "")


@_marks(135539, allure.severity_level.MINOR)
@pytest.mark.tc_135539
@allure.title("The Add Pillar Card form displays every pillar-level field")
def test_add_form_shows_all_pillar_fields(page):
    """TC 135539 — Editor. Icon, Title EN/AR, Description EN/AR, Display
    Order, Active Status are present on the create form."""
    ac.check_form_renders(page, ADMIN, list(ADMIN.FIELDS))
    admin = ADMIN(page)
    assert page.locator(AR_TITLE_NAME).count() == 1, "Pillar Title (AR) control missing"
    assert page.locator(admin.RICH_TEXT_EDITOR_IFRAME_CSS).count() >= 2, "Pillar Description EN/AR editors missing"


def _toast_case(page, tc: int, locale: str) -> str:
    admin = ADMIN(page)
    title = qctest_title(tc, f"toast-{locale}")
    try:
        admin.open_form(ROLE_EDITOR, locale=locale)
        page.locator(EN_TITLE_NAME).fill(title)
        page.locator(AR_TITLE_NAME).fill(f"{title} AR")
        admin._pending_title = title
        admin.save_as_draft()
        toast = admin._toast_text()
        _attach(f"toast ({locale})", toast or "<no toast captured>")
        page.screenshot(path=f"reports/manual-exec-129381-{tc}.png")
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT, f"{title!r} was not saved"
        return toast
    finally:
        admin.delete_disposable(title)


@_marks(135540, allure.severity_level.MINOR)
@pytest.mark.tc_135540
@allure.title("A success toast (English) follows a successful save")
def test_success_toast_english(page):
    """TC 135540 — Editor, EN admin. The save must succeed; the toast text is
    recorded (a missing toast or different wording is not a bug), asserted
    only to be English when present."""
    toast = _toast_case(page, 135540, "en")
    if toast:
        assert not _has_arabic(toast), f"EN toast is not English: {toast!r}"


@_marks(135541, allure.severity_level.MINOR)
@pytest.mark.tc_135541
@allure.title("A success toast (Arabic) follows a successful save")
def test_success_toast_arabic(page):
    """TC 135541 — Editor, Arabic admin locale. Save must succeed; toast text
    recorded and, when present, must contain Arabic."""
    toast = _toast_case(page, 135541, "ar")
    if toast:
        assert _has_arabic(toast), f"AR toast is not Arabic: {toast!r}"


def _inline_required(page, tc: int, locale: str) -> None:
    admin = ADMIN(page)
    title = qctest_title(tc, f"inline-{locale}")
    try:
        admin.open_form(ROLE_EDITOR, locale=locale)
        # EN title is a QCTEST title so a wrongly-accepted record is found and
        # torn down; AR title, description and icon are left empty.
        page.locator(EN_TITLE_NAME).fill(title)
        admin._pending_title = title
        admin.submit_for_review()
        refused = admin.refusal_visible()
        _attach("refusal bar", admin.refusal_text())
        page.screenshot(path=f"reports/manual-exec-129381-{tc}.png", full_page=True)
        assert refused, "submit with empty mandatory fields raised no validation message"
        assert admin.status_of(title, ROLE_EDITOR) != STATUS_PUBLISHED, "record published despite empty mandatory fields"
    finally:
        admin.delete_disposable(title)


@_marks(135542, allure.severity_level.MINOR)
@pytest.mark.tc_135542
@allure.title("A mandatory-field validation error displays (English admin)")
def test_inline_required_error_english(page):
    """TC 135542 — Editor, EN admin. No "Section Heading" field exists; the
    card's mandatory fields are left empty instead. Wording recorded only."""
    _inline_required(page, 135542, "en")


@_marks(135543, allure.severity_level.MINOR)
@pytest.mark.tc_135543
@allure.title("A mandatory-field validation error displays (Arabic admin)")
def test_inline_required_error_arabic(page):
    """TC 135543 — Editor, Arabic admin locale; same as 135542."""
    _inline_required(page, 135543, "ar")


def _file_refused(page, tc: int, fixture: str, size_tolerated: bool) -> None:
    """Picker refusal or Submit refusal both pass. A >2 MB file up to 3 MB
    being accepted is within the agreed tolerance (recorded, not failed)."""
    admin = ADMIN(page)
    title = qctest_title(tc, "file")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=("pillar_icon",), active=False)
        attached = ""
        try:
            admin.upload("pillar_icon", fixture, tag=str(tc))
            attached = admin.value("pillar_icon")
        except Exception as exc:  # noqa: BLE001 — picker refused it
            _attach("picker", f"upload raised: {exc!r}"[:500])
        _attach("attached file", attached or "<none>")
        page.screenshot(path=f"reports/manual-exec-129381-{tc}.png", full_page=True)
        if not attached:
            return  # refused at the picker
        admin.submit_for_review()
        refused = admin.refusal_visible()
        _attach("submit refusal", admin.refusal_text())
        if refused:
            return
        status = admin.raw_row_status(title)
        _attach("status after submit", status)
        if size_tolerated:
            return  # <= 3 MB accepted: within tolerance
        pytest.fail(f"{fixture.rsplit('/', 1)[-1]} was accepted and the card saved (status {status!r})")
    finally:
        admin.delete_disposable(title)


@_marks(135594, allure.severity_level.MINOR)
@pytest.mark.tc_135594
@allure.title("Pillar Icon over 2 MB is refused")
def test_icon_over_2mb_refused(page):
    """TC 135594 — 2.5 MB PNG. Accepted up to 3 MB is tolerated (standing
    rule); > 3 MB accepted would be a bug."""
    _file_refused(page, 135594, BIG_PNG_2_5MB, size_tolerated=True)


@_marks(135595, allure.severity_level.MINOR)
@pytest.mark.tc_135595
@allure.title("Pillar Icon in an unsupported format (JPG) is refused")
def test_icon_unsupported_format_refused(page):
    """TC 135595 — 500 KB JPG; PBI: PNG/SVG only."""
    _file_refused(page, 135595, JPG_500KB, size_tolerated=False)


@_marks(135596, allure.severity_level.MINOR)
@pytest.mark.tc_135596
@allure.title("The uploaded Pillar Icon persists after save and reload")
def test_icon_persists(page):
    """TC 135596 — Editor; PNG fixture, Save as Draft, reopen."""
    ac.check_file_accepted(page, ADMIN, 135596, "pillar_icon", PILLAR_PNG)


@_marks(135597, allure.severity_level.MINOR)
@pytest.mark.tc_135597
@allure.title("A Pillar Icon can be replaced with a new image")
def test_icon_replaced(page):
    """TC 135597 — QCTEST card with a PNG icon (stand-in for Vision); reopen,
    upload a different PNG over it, save, reopen: only the new file."""
    admin = ADMIN(page)
    title = qctest_title(135597, "replace")
    try:
        admin.create(title, active=False, submit=False)
        admin.open_by_title(title)
        old = admin.value("pillar_icon")
        admin._pending_title = title
        admin.upload("pillar_icon", PNG_400KB, tag="135597")
        admin.save_as_draft()
        admin.open_by_title(title)
        new = admin.value("pillar_icon")
        _attach("icon before/after", f"{old!r} -> {new!r}")
        assert new and new != old, f"icon not replaced: {old!r} -> {new!r}"
    finally:
        admin.delete_disposable(title)


def _title_limit(page, tc: int, locale: str) -> None:
    """Rule 5: read the implemented limit live, enter 101 characters, save,
    reopen, check what was stored and that the form still renders it."""
    admin = ADMIN(page)
    if locale == "en":
        en_title = (qctest_title(tc, "max-") + "E" * 101)[:101]
        ar_value = "QCTEST AR"
    else:
        en_title = qctest_title(tc, "max-ar")
        ar_value = "ر" * 101
    stored_titles = [en_title, en_title[:100]] if locale == "en" else [en_title]
    sel = EN_TITLE_NAME if locale == "en" else AR_TITLE_NAME
    try:
        admin.open_form(ROLE_EDITOR)
        maxlength = page.locator(sel).get_attribute("maxlength")
        admin.fill_required(en_title, active=False, files=FILES)
        page.locator(AR_TITLE_NAME).fill(ar_value)
        admin.save_as_draft()
        stored = ""
        for t in stored_titles:
            if admin.code_for(t, refresh=True, wait=False):
                admin.open_by_title(t)
                stored = page.locator(sel).input_value()
                break
        _attach("Rule 5", f"maxlength attr={maxlength!r}; entered=101; stored length={len(stored)}")
        page.screenshot(path=f"reports/manual-exec-129381-{tc}.png", full_page=True)
        assert len(stored) >= 100, (
            f"implemented limit is shorter than the US limit of 100 (stored {len(stored)}) — Rule 5 case 3"
        )
    finally:
        for t in stored_titles:
            admin.delete_disposable(t)


@_marks(135600, allure.severity_level.MINOR)
@pytest.mark.tc_135600
@allure.title("Pillar Title (EN) 101 characters — Rule 5")
def test_title_en_char_limit(page):
    """TC 135600 — Rule 5: implemented limit read live; a limit >= 100 with
    an intact form passes; shorter than 100 fails."""
    _title_limit(page, 135600, "en")


@_marks(135604, allure.severity_level.MINOR)
@pytest.mark.tc_135604
@allure.title("Pillar Title (AR) 101 characters — Rule 5")
def test_title_ar_char_limit(page):
    """TC 135604 — Rule 5, Arabic title."""
    _title_limit(page, 135604, "ar")


def _rich_limit_na(page, tc: int, locale: str) -> None:
    """Rule 5.1: rich-text field -> Not Applicable. Executed anyway: 1001
    characters are entered and saved; stored length recorded."""
    admin = ADMIN(page)
    title = qctest_title(tc, "rich-max")
    other = "ar" if locale == "en" else "en"
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=False, files=FILES, skip=("pillar_description",))
        admin.fill("pillar_description", ("D" if locale == "en" else "و") * 1001, locale=locale)
        admin.fill("pillar_description", "QCTEST other locale", locale=other)
        admin.save_as_draft()
        admin.open_by_title(title)
        stored = admin.value("pillar_description", locale)
        _attach("Rule 5.1 (N/A)", f"rich text {locale}: entered 1001, stored {len(stored)}")
    finally:
        admin.delete_disposable(title)


@_marks(135608, allure.severity_level.MINOR)
@pytest.mark.tc_135608
@allure.title("Pillar Description (EN) 1001 characters — Rule 5 N/A")
def test_description_en_char_limit_na(page):
    """TC 135608 — rich text: Not Applicable by Rule 5.1 (executed, recorded)."""
    _rich_limit_na(page, 135608, "en")


@_marks(135612, allure.severity_level.MINOR)
@pytest.mark.tc_135612
@allure.title("Pillar Description (AR) 1001 characters — Rule 5 N/A")
def test_description_ar_char_limit_na(page):
    """TC 135612 — rich text: Not Applicable by Rule 5.1 (executed, recorded)."""
    _rich_limit_na(page, 135612, "ar")


@_marks(135601, allure.severity_level.MINOR)
@pytest.mark.tc_135601
@allure.title("Pillar Title (EN) persists after save and reload")
def test_title_en_persists(page):
    """TC 135601 — Editor."""
    ac.check_valid_persists(page, ADMIN, 135601, "pillar_title", "Vision-persist", files=FILES)


@_marks(135605, allure.severity_level.MINOR)
@pytest.mark.tc_135605
@allure.title("Pillar Title (AR) persists after save and reload")
def test_title_ar_persists(page):
    """TC 135605 — Editor."""
    admin = ADMIN(page)
    title = qctest_title(135605, "ar-persist")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=FILES)
        page.locator(AR_TITLE_NAME).fill("الرؤية")
        admin.save_as_draft()
        admin.open_by_title(title)
        page.reload()
        page.locator(AR_TITLE_NAME).wait_for(timeout=30000)
        assert page.locator(AR_TITLE_NAME).input_value() == "الرؤية"
    finally:
        admin.delete_disposable(title)


@_marks(135609, allure.severity_level.MINOR)
@pytest.mark.tc_135609
@allure.title("Pillar Description (EN) text and formatting persist after reload")
def test_description_formatting_persists(page):
    """TC 135609 — Editor; same body as 135606 (bold phrase survives save +
    fresh reopen)."""
    _bold_description(page, 135609)


@_marks(135618, allure.severity_level.MINOR)
@pytest.mark.tc_135618
@allure.title("Display Order persists after save and reload")
def test_display_order_persists(page):
    """TC 135618 — Editor; 9700 on a Draft."""
    ac.check_valid_persists(page, ADMIN, 135618, "display_order", "9700", files=FILES)


@_marks(135615, allure.severity_level.MINOR)
@pytest.mark.tc_135615
@allure.title("Display Order 0 is refused")
def test_display_order_zero_refused(page):
    """TC 135615 — PBI: "Positive number required"."""
    ac.check_value_refused(page, ADMIN, 135615, "display_order", "0", short="zero", files=FILES)


@_marks(135616, allure.severity_level.MINOR)
@pytest.mark.tc_135616
@allure.title("Display Order -1 is refused")
def test_display_order_negative_refused(page):
    """TC 135616."""
    ac.check_value_refused(page, ADMIN, 135616, "display_order", "-1", short="neg", files=FILES)


@_marks(135617, allure.severity_level.MINOR)
@pytest.mark.tc_135617
@allure.title("Display Order non-numeric is refused")
def test_display_order_non_numeric_refused(page):
    """TC 135617 — a number input that will not take "abc" is the refusal."""
    ac.check_value_refused(page, ADMIN, 135617, "display_order", "abc", short="nan", files=FILES)


@_marks(135630, allure.severity_level.MINOR)
@pytest.mark.tc_135630
@allure.title("Active Status has a defined default on a new card")
def test_active_status_default(page):
    """TC 135630 — Editor. Reads the untouched default, saves a Draft, and the
    stored value equals the observed default."""
    admin = ADMIN(page)
    title = qctest_title(135630, "default")
    try:
        admin.open_form(ROLE_EDITOR)
        default = admin.flag("active_status")
        _attach("Active Status default", str(default))
        admin.fill_required(title, files=FILES, skip=("active_status",))
        assert admin.flag("active_status") == default
        admin.save_as_draft()
        admin.open_by_title(title)
        assert admin.flag("active_status") == default, "stored Active Status differs from the form default"
    finally:
        admin.delete_disposable(title)


@_marks(135626, allure.severity_level.MINOR)
@pytest.mark.tc_135626
@allure.title("Concurrent edits by two Editors do not corrupt the card")
def test_concurrent_editors(page, browser):
    """TC 135626 — two QC Site Content Editor sessions on one QCTEST card
    (stand-in for the real Vision card)."""
    ac.check_two_editors(page, browser, ADMIN, 135626, "pillar_description", files=FILES)


def _bring_on_screen(sd, title: str) -> None:
    for _ in range(6):
        if sd.active_card_title_text() == title:
            return
        sd.click_next()
    assert sd.active_card_title_text() == title, f"could not bring {title!r} on screen"


def _cycle_titles(sd, n: int = 6) -> list:
    seen = [sd.active_card_title_text()]
    for _ in range(n):
        sd.click_next()
        seen.append(sd.active_card_title_text())
    return seen


@_marks(135627, allure.severity_level.MINOR)
@pytest.mark.tc_135627
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Deleting the currently-displayed card leaves no broken carousel slot")
def test_delete_displayed_card_no_broken_slot(page, browser):
    """TC 135627 — Editor + anonymous visitor. A published QCTEST card stands
    in for Mission. The visitor has it on screen; it is deleted; after a
    reload the carousel cycles only the real cards, no blank slot."""
    from web.pages.home_strategic_direction.home_strategic_direction_page import HomeStrategicDirectionPage
    admin = ADMIN(page)
    title = qctest_title(135627, "displayed")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert PROBE(anon, title), "precondition: QCTEST card not public"
        sd = HomeStrategicDirectionPage(anon)
        sd.open_home()
        _bring_on_screen(sd, title)
        assert admin.delete_disposable(title), "guarded delete did not complete"
        assert not PROBE(anon, title, False), "deleted card still public"
        sd.open_home()
        seen = _cycle_titles(sd)
        _attach("cycle", seen)
        assert all(t.strip() for t in seen), f"blank slot in carousel: {seen}"
        assert set(seen) == set(REAL_PILLAR_TITLES), f"unexpected cards: {seen}"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135628, allure.severity_level.MINOR)
@pytest.mark.tc_135628
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Inactive mid-session leaves no broken slot for a visitor")
def test_inactive_mid_session_no_broken_slot(page, browser):
    """TC 135628 — visitor on a published QCTEST card (stand-in for Mission);
    Editor unticks Active and submits; the visitor's next click moves on with
    no JS error or blank card; after a full reload the card is gone."""
    from web.pages.home_strategic_direction.home_strategic_direction_page import HomeStrategicDirectionPage
    admin = ADMIN(page)
    title = qctest_title(135628, "midsession")
    ctx, anon = ac._anon_page(browser)
    errors = []
    anon.on("pageerror", lambda e: errors.append(str(e)))
    try:
        admin.create(title, active=True)
        assert PROBE(anon, title), "precondition: QCTEST card not public"
        sd = HomeStrategicDirectionPage(anon)
        sd.open_home()
        _bring_on_screen(sd, title)
        admin.open_by_title(title)
        admin.set_flag("active_status", False)
        admin.submit_for_review()
        sd.click_next()
        assert sd.active_card_title_text().strip(), "blank card after moving on"
        assert not errors, f"JS errors: {errors}"
        assert not PROBE(anon, title, False), "inactive card still public after reload"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@_marks(135633, allure.severity_level.MINOR)
@pytest.mark.tc_135633
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("Two cards sharing a Display Order each render once, in a stable order")
def test_same_display_order(page, browser):
    """TC 135633 — two QCTEST cards both at 9900 (stand-ins for Mission and
    Objectives). Each card appears exactly once; order is the same on two
    reloads."""
    admin = ADMIN(page)
    a, b = qctest_title(135633, "A"), qctest_title(135633, "B")
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(a, active=True, display_order="9900")
        admin.create(b, active=True, display_order="9900")
        assert PROBE(anon, a) and PROBE(anon, b), "precondition: cards not public"
        first, second = _public_titles(anon), _public_titles(anon)
        _attach("orders", f"{first}\n{second}")
        for t in (*REAL_PILLAR_TITLES, a, b):
            assert first.count(t) == 1, f"{t!r} appears {first.count(t)} times: {first}"
        assert first == second, f"order not deterministic: {first} vs {second}"
    finally:
        admin.delete_disposable(a)
        admin.delete_disposable(b)
        ac._close(ctx)


@_marks(135625, allure.severity_level.MINOR)
@pytest.mark.tc_135625
@pytest.mark.xdist_group("strategic_pillar_carousel")
@allure.title("A published edit reaches visitors after the cache refresh")
def test_published_edit_after_cache_refresh(page, browser):
    """TC 135625 — QCTEST card stand-in for Mission (the title is this
    record's identity, so the description is edited). Records whether the
    first immediate load is stale, then asserts the edit is visible after the
    refresh window (poll)."""
    admin = ADMIN(page)
    title = qctest_title(135625, "cache")
    new_desc = "QCTEST-135625 edited after publish"
    ctx, anon = ac._anon_page(browser)
    try:
        admin.create(title, active=True)
        assert PROBE(anon, title), "precondition: card not public"
        admin.open_by_title(title)
        admin.fill("pillar_description", new_desc)
        admin.submit_for_review()
        _open_home(anon)
        _attach("immediately after publish", f"new text visible: {new_desc in anon.locator('body').inner_text()}")
        assert PROBE(anon, new_desc), "edit never reached the public page"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)

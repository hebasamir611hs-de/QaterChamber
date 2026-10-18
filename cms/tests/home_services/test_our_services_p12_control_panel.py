"""
cms/tests/home_services/test_our_services_p12_control_panel.py — PBI 129371
(QC-HOME-003 — Our Services), suite 134449: the P1/P2 Control_Panel cases,
rewritten 2026-10-15 (Phase 3) on Object Authoring.

Replaces, for these TCs, the 2026-09 tests in test_home_services_control_panel.py
(Content & Data, TEST_USER, "Assigned Tab" combobox read from an older form,
135346/135350 skipped as "Page Builder fragment"). Bug 139172 (Done) moved the
section Tag / Heading / Description into the "Our Services Section" object, so
those cases are now authorable.

Accounts: Site Content Editor (its submit reads "Publish" and lands on
Published); Site Member for the denial case.

Records:
  - Service-card cases use a disposable `QCTEST-<tc>-*` Service Card
    (Display Order 9900). Nothing is deleted (PBI running rules, rule 10):
    a card that reached Published is unpublished in `finally`, so it does not
    stay on the live Home Page, and is left for the QA lead to clean.
  - Section cases (135346 / 135348 / 135350) write to the ONE live section
    record, QCDEMO-129371-OSS-DEFAULT (rule 10 allows test data on real
    records). Each snapshots the form first, logs every write to
    reports/live-writes-*.jsonl before the click, and in `finally` puts the
    snapshot back and leaves the record Published (rule 11). Group
    `our_services_section` keeps them off each other.

Public reads use a fresh logged-out context (standards.md).
"""

from __future__ import annotations

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED, STATUS_UNPUBLISHED
from cms.pages.home_services.our_services_admin_page import (
    OSS_ENTRY_CODE,
    OurServicesSectionAdminPage as Section,
    ServiceCardAdminPage as Card,
    default_png,
)
from cms.tests import authoring_checks as ac
from cms.tests.live_write_guard import LiveRecord, log_live_write
from config.settings import control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.home_services.home_services_page import HomeServicesPage

pytestmark = [pytest.mark.control_panel, pytest.mark.pbi_129371]

OSS = LiveRecord("our-services-section", OSS_ENTRY_CODE, "Our Services Section (singleton)")
PUBLIC_S = 90.0


def _poll(fn, timeout=PUBLIC_S, poll=5.0) -> bool:
    try:
        wait_until(fn, timeout=timeout, poll=poll)
        return True
    except WaitTimeoutError:
        return False


def _cards(home: HomeServicesPage) -> list[str]:
    return [t.strip() for t in home.page.locator(home.CARD_TITLE).all_text_contents()]


# ---------------------------------------------------------------------------
# service-card helpers
# ---------------------------------------------------------------------------
def _publish_card(admin: Card, title: str, extra: dict | None = None, files: dict | None = None) -> None:
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(title, active=True, files=files)
    for key, val in (extra or {}).items():
        admin.fill(key, val)
    log_live_write(LiveRecord("service-card", title, "disposable QCTEST record"), "<create>", title, None,
                   action="publish", note="QCTEST card published for a public check; unpublished in finally")
    admin.submit_for_review()
    status = admin.status_of(title, ROLE_EDITOR)
    assert status == STATUS_PUBLISHED, f"{title!r}: Editor Publish left it {status or 'absent'!r}"


def _retire_card(admin: Card, title: str, tc: int) -> None:
    """Unpublish (never delete) so the QCTEST card leaves the live site."""
    try:
        admin.open_list(ROLE_EDITOR)
        if admin.row_status_text(title) == STATUS_PUBLISHED:
            log_live_write(LiveRecord("service-card", title, "disposable QCTEST record"), "<workflow>",
                           STATUS_UNPUBLISHED, tc, action="unpublish", note="teardown")
            admin.unpublish_entry(title)
    except Exception:  # noqa: BLE001 — teardown never masks the result
        pass
    ac.dispose(admin, title, tc)


# ---------------------------------------------------------------------------
# access
# ---------------------------------------------------------------------------
@allure.title("Site Content Editor can access Our Services management")
@pytest.mark.auth
@pytest.mark.tc_135333
def test_editor_can_access_our_services_management(page):
    """Editor opens the section record (Tag / Heading / Description editable)
    and the Service Card and Filter Tab authoring forms. Nothing is saved."""
    section = Section(page).open_record(ROLE_EDITOR)
    for key in ("section_tag", "section_heading", "section_description"):
        for loc in ("en", "ar"):
            box = page.get_by_role("textbox", name=section.label_pattern(section._label(key, loc)))
            assert box.is_editable(), f"{section._label(key, loc)} is not editable for the Editor"
    ac.check_form_renders(page, Card, ["title", "redirect_url", "assigned_tab", "thumbnail", "icon"])
    page.goto(Card(page)._manage_url().replace("manage-service-card", "manage-filter-tab"),
              wait_until="domcontentloaded")
    page.locator(Card.SAVE_AS_DRAFT_BUTTON).first.wait_for(state="visible", timeout=35000)


@allure.title("User without Site Content Editor rights is denied Our Services management")
@pytest.mark.auth
@pytest.mark.tc_135334
def test_member_denied_our_services_management(page):
    """Account: Site Member, by direct URL to the section and the card list."""
    ac.check_member_denied(page, Section)
    ac.check_member_denied(page, Card)


# ---------------------------------------------------------------------------
# section lifecycle (the ONE live record)
# ---------------------------------------------------------------------------
def _section_restore(section: Section, snap: dict, tc: int) -> None:
    """Put the snapshot back and leave the record Published. Raises when the
    record is not Published afterwards (rule 11 — the QA lead must know)."""
    section.sign_in(ROLE_EDITOR)
    status = section.list_status()
    if status == STATUS_UNPUBLISHED:
        log_live_write(OSS, "<workflow>", STATUS_PUBLISHED, tc, action="publish", note="restore: row Publish")
        section.publish_entry(OSS_ENTRY_CODE)
    section.open_entry_by_code(OSS_ENTRY_CODE)
    if section.snapshot() != snap:
        _edit_section(section)
        section.apply(snap)
        log_live_write(OSS, "<all text fields>", snap, tc, action="publish", note="restore snapshot")
        section.submit_for_review()
    final = section.list_status()
    if final != STATUS_PUBLISHED:
        log_live_write(OSS, "<workflow>", STATUS_PUBLISHED, tc, action="publish", note="restore: row Publish")
        section.publish_entry(OSS_ENTRY_CODE)
        final = section.list_status()
    assert final == STATUS_PUBLISHED, f"{OSS_ENTRY_CODE} is {final!r} after restore — re-publish it by hand"


def _edit_section(section: Section) -> None:
    """Get the open record into an editable form. Read live 2026-10-15: the
    Published record's fields are editable as they are (135333), so the
    section is NOT unpublished first — that would take it off the live Home
    Page for the length of the test. Unpublish-to-edit only when the field
    is read-only."""
    box = section.page.get_by_role("textbox", name=section.label_pattern(section._label("section_tag", "en")))
    if not box.is_editable() and section.page.locator(section.UNPUBLISH_BUTTON).count():
        section.unpublish_to_edit_as_draft()


@allure.title("Saving the section as Draft keeps the change off the live Home Page")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.tc_135346
def test_section_draft_hidden_from_live_home(page, browser):
    tag = f"QCTEST-135346-{ac._RUN_UID}"
    section = Section(page).open_record(ROLE_EDITOR)
    snap = section.snapshot()
    ctx, anon = ac._anon_page(browser)
    try:
        # Read live 2026-10-15: a Published record's form offers no Save as
        # Draft — only "Unpublish to edit as draft" (banner: "To take it off
        # the site while you work on it, use Unpublish to edit as draft").
        # That is the product's draft path; the restore re-publishes.
        log_live_write(OSS, "<workflow>", "Unpublished", 135346, action="unpublish",
                       note="Unpublish to edit as draft; re-published in finally (rule 11)")
        section.unpublish_to_edit_as_draft()
        log_live_write(OSS, "Section Tag", tag, 135346, action="save-draft", note=f"snapshot {snap}")
        section.fill("section_tag", tag)
        section.save_as_draft()
        home = HomeServicesPage(anon)
        shown = _poll(lambda: (home.open_home(), tag in home.tag_text())[1], timeout=45.0)
        assert not shown, f"the drafted Section Tag {tag!r} is visible on the live Home Page"
    finally:
        ac._close(ctx)
        _section_restore(section, snap, 135346)


@allure.title("Publish makes the configured section live on the Home Page")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.tc_135348
def test_section_publish_goes_live(page, browser):
    tag = f"QCTEST-135348-{ac._RUN_UID}"
    section = Section(page).open_record(ROLE_EDITOR)
    snap = section.snapshot()
    ctx, anon = ac._anon_page(browser)
    try:
        log_live_write(OSS, "Section Tag", tag, 135348, action="publish", note=f"snapshot {snap}")
        _edit_section(section)
        section.fill("section_tag", tag)
        section.submit_for_review()
        assert section.list_status() == STATUS_PUBLISHED, "Editor Publish did not leave the section Published"
        home = HomeServicesPage(anon)
        assert _poll(lambda: (home.open_home(), tag in home.tag_text())[1]), (
            f"published Section Tag {tag!r} never reached the live Home Page"
        )
        home.scroll_to_section()
        assert home.heading_text().strip(), "section heading rendered empty"
        assert home.is_tablist_visible() and home.tab_texts(), "tab strip not rendered"
        assert home.total_card_count() > 0, "no service cards rendered"
    finally:
        ac._close(ctx)
        _section_restore(section, snap, 135348)


@allure.title("Unpublish removes the section from the live Home Page")
@pytest.mark.xdist_group("our_services_section")
@pytest.mark.tc_135350
def test_section_unpublish_hides_section(page, browser):
    section = Section(page).open_record(ROLE_EDITOR)
    snap = section.snapshot()
    ctx, anon = ac._anon_page(browser)
    try:
        log_live_write(OSS, "<workflow>", STATUS_UNPUBLISHED, 135350, action="unpublish",
                       note="re-published in finally (rule 11)")
        section.open_entries_list()
        section.unpublish_entry(OSS_ENTRY_CODE)
        assert section.list_status() == STATUS_UNPUBLISHED, "row Unpublish did not land on Unpublished"
        home = HomeServicesPage(anon)
        gone = _poll(lambda: (home.open_home(), not home.is_section_visible())[1])
        assert gone, "the Our Services section is still visible after Unpublish"
    finally:
        ac._close(ctx)
        _section_restore(section, snap, 135350)


# ---------------------------------------------------------------------------
# service cards (disposable QCTEST cards)
# ---------------------------------------------------------------------------
@allure.title("Card assigned to a filter tab appears under that tab")
@pytest.mark.tc_135351
def test_card_assigned_to_tab_shows_under_tab(page, browser):
    """Case card "Halls Reservation" / tab "Information Services": the live tab
    is "Information"; the card is a QCTEST card (no real card is edited)."""
    admin = Card(page)
    title = ac.run_title(135351, "Halls-Reservation")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_card(admin, title, extra={"assigned_tab": "Information"})
        home = HomeServicesPage(anon)
        assert _poll(lambda: (home.open_home(), home.open_tab("Information"), title in _cards(home))[2]), (
            f"{title!r} never appeared under the Information tab"
        )
    finally:
        ac._close(ctx)
        _retire_card(admin, title, 135351)


@allure.title("Reassigning a card to another tab moves it out of the original tab")
@pytest.mark.tc_135352
def test_card_reassigned_moves_tabs(page, browser):
    admin = Card(page)
    title = ac.run_title(135352, "reassign")
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_card(admin, title, extra={"assigned_tab": "Information"})
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        _edit_card(admin)
        admin.fill("assigned_tab", "Membership")
        log_live_write(LiveRecord("service-card", title, "disposable QCTEST record"), "Assigned Tab",
                       "Membership", 135352, action="publish")
        admin.submit_for_review()
        home = HomeServicesPage(anon)

        def _moved() -> bool:
            home.open_home()
            home.open_tab("Information")
            under_info = title in _cards(home)
            home.open_tab("Membership")
            return not under_info and title in _cards(home)

        assert _poll(_moved), f"{title!r} did not move from Information to Membership"
    finally:
        ac._close(ctx)
        _retire_card(admin, title, 135352)


def _edit_card(admin: Card) -> None:
    """A Published card is edited in place and re-published (as the section
    is — 135348). Unpublish-to-edit only when the field is read-only: after
    it, the form's Publish button never became clickable (135352, run 1)."""
    title_box = admin.page.get_by_role("textbox", name=admin.label_pattern("Title"))
    if not title_box.first.is_editable() and admin.page.locator(admin.UNPUBLISH_BUTTON).count():
        admin.unpublish_to_edit_as_draft()


@allure.title("Valid PNG thumbnail under 2 MB uploads and shows on the card")
@pytest.mark.tc_135376
def test_valid_png_thumbnail_shows_on_card(page, browser):
    admin = Card(page)
    title = ac.run_title(135376, "thumb")
    png = default_png("QCTEST-135376-thumb.png", size=(800, 600))
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_card(admin, title, files={"thumbnail": png})
        home = HomeServicesPage(anon)
        assert _poll(lambda: (home.open_home(), title in _cards(home))[1]), f"{title!r} never reached the Home Page"
        card = anon.locator(f"{home.CARD}:has({home.CARD_TITLE}:text-is('{title}'))").first
        imgs = card.locator("img[src*='135376-thumb']")
        assert imgs.count() > 0, f"the uploaded thumbnail is not on the card (srcs {[i.get_attribute('src') for i in card.locator('img').all()]})"
        # HEALED 2026-10-15: the card can sit off-screen in the carousel with a
        # lazy image, so `complete/naturalWidth` read 0 without a fault. The
        # visitor-facing fact is that the image URL serves an image.
        src = imgs.first.get_attribute("src")
        resp = anon.request.get(src if src.startswith("http") else control_panel_url(src))
        assert resp.ok and resp.headers.get("content-type", "").startswith("image/"), (
            f"thumbnail URL does not serve an image (HTTP {resp.status}, {resp.headers.get('content-type')})"
        )
    finally:
        ac._close(ctx)
        _retire_card(admin, title, 135376)


@allure.title("Valid Service Card Redirect URL saves and Read More navigates to it")
@pytest.mark.tc_135400
def test_card_redirect_url_read_more(page, browser):
    admin = Card(page)
    title = ac.run_title(135400, "redirect")
    url = "https://qatarchamber.com/en/services/qctest-135400"
    ctx, anon = ac._anon_page(browser)
    try:
        _publish_card(admin, title, extra={"redirect_url": url})
        home = HomeServicesPage(anon)
        assert _poll(lambda: (home.open_home(), title in _cards(home))[1]), f"{title!r} never reached the Home Page"
        card = anon.locator(f"{home.CARD}:has({home.CARD_TITLE}:text-is('{title}'))").first
        href = card.locator(home.CARD_READMORE).first.get_attribute("href") or card.locator("a").first.get_attribute("href")
        assert href and href.rstrip("/") == url.rstrip("/"), f"Read More points to {href!r}, not {url!r}"
    finally:
        ac._close(ctx)
        _retire_card(admin, title, 135400)


@allure.title("Valid View All URL saves and the CTA redirects to it")
@pytest.mark.tc_135388
def test_view_all_url_field_present(page):
    """Read live 2026-10-15: no object in the Our Services group (section,
    card, filter tab, tab mapping) carries a View All label or URL field.
    The test checks for the field and stops when it is missing — that is a
    requirements-vs-implementation question for the QA lead, not a bug."""
    section = Section(page).open_record(ROLE_EDITOR)
    found = page.get_by_role("textbox", name=section.label_pattern("View All URL")).count()
    if not found:
        pytest.fail("NEEDS USER — no 'View All URL' field on Our Services Section "
                    "(nor on Service Card / Filter Tab / Tab Mapping); the CTA is not authorable",
                    pytrace=False)

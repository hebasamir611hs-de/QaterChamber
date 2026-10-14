"""
cms/tests/home_promo_banners/test_home_promo_banners_control_panel.py —
PBI 129368 (QC-HOME-002 — Promotional Banners / Ad Slots), suite 134448.

REWRITTEN 2026-10-07 (Phase 3, 7-state workflow). The previous module drove
Content & Data, ran every lifecycle step as TEST_USER, asserted a two-state
Draft/"Approved" model ("Unpublish lands on Draft", "Submit goes straight to
live"), read the public page through the CMS-authenticated `page`, and
deleted by substring `.first`. All of that is replaced:

  - Object Authoring only (`manage-promotional-banner`) via
    PromotionalBannerAdminPage (a DisposableObjectAdminPage).
  - Every lifecycle case names its account: Editor (privileged submit ->
    Published), Author (submit -> Pending Review), Site Member (denial).
  - Every record is `QCTEST-<tc_id>-<short>` (its Banner Alt Text (EN), which
    is the list's Entry column) and is deleted by exact title in `finally`.
    The three real banners (REAL_BANNER_TITLES) are never opened for edit.
  - Public reads use a fresh logged-out context and look for the banner's
    <img alt> on REAL (non-clone) slides; both gates (Published + Active
    Status) are set and checked before a "visible" assertion.

Web-platform cases whose precondition is a CMS record (135126-135130,
135188-135190) live here because they need the authoring session to build
their disposable banner; they carry `web` as well as `control_panel`.

Data adaptations, disclosed: Display Order uses 9900/10000 instead of the
cases' 1/2/3 (OBJECT-AUTHORING-GUIDE: multiples of 100; a QCTEST banner at 1
would jump ahead of the real banners on the live Home Page). Oversized-image
cases use a 3.5 MB file: uploads up to 3 MB are an accepted tolerance on this
project, so only > 3 MB being accepted would be a finding.
"""

from __future__ import annotations

import datetime
import struct
import tempfile
import zlib
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_SITE_MEMBER,
    qctest_title,
)
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_promo_banners.home_promo_banners_admin_page import (
    REAL_BANNER_TITLES,
    PromotionalBannerAdminPage as Admin,
)
from cms.tests import authoring_checks as ac
from core.utils.waits import WaitTimeoutError, wait_until
from web.pages.home_promo_banners.home_promo_banners_page import HomePromoBannersPage

pytestmark = [pytest.mark.control_panel, pytest.mark.global_, pytest.mark.pbi_129368]

IMG = str(Path(__file__).parent / "fixtures" / "promo_banner_v2_qctest.png")
FILES = {"image_en": IMG, "image_ar": IMG}
NOT_ROLE = ac.NOT_ROLE

PUBLIC_APPEAR_S = 60.0
PUBLIC_POLL_S = 3.0


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def _day(offset: int) -> str:
    return (datetime.date.today() + datetime.timedelta(days=offset)).strftime(Admin.DATE_FORMAT)


def _anon(browser):
    return ac._anon_page(browser)


def _public_present(anon, alt: str, expect: bool = True, arabic: bool = False,
                    timeout: float = PUBLIC_APPEAR_S) -> bool:
    """Reload the public Home Page (logged-out context) until the banner's
    presence on a real slide equals `expect`; return the last reading."""
    home = HomePromoBannersPage(anon)
    seen = {"present": not expect}

    def _matches() -> bool:
        home.open_home_arabic() if arabic else home.open_home()
        seen["present"] = home.real_banner_count(alt) > 0
        return seen["present"] == expect

    try:
        wait_until(_matches, timeout=timeout, poll=PUBLIC_POLL_S,
                   message=f"public Home Page never {'showed' if expect else 'dropped'} {alt!r}")
    except WaitTimeoutError:
        pass
    return seen["present"]


def _create(admin: Admin, title: str, role: str = ROLE_EDITOR, active: bool = True,
            extra: dict | None = None, skip: tuple = ()) -> None:
    admin.open_form(role)
    if role != ROLE_EDITOR:
        assert not admin.has_admin_toolbar(), NOT_ROLE
    admin.fill_required(title, active=active, files=FILES, skip=skip)
    for key, val in (extra or {}).items():
        admin.fill(key, val)


def _publish_as_editor(admin: Admin, title: str, active: bool = True, extra: dict | None = None) -> None:
    _create(admin, title, ROLE_EDITOR, active, extra)
    admin.submit_for_review()
    status = admin.status_of(title, ROLE_EDITOR)
    assert status == STATUS_PUBLISHED, (
        f"{title!r}: Editor submit left the record {status or 'absent from the list'!r} "
        f"(raw cell {admin.last_status_raw!r}), "
        f"not {STATUS_PUBLISHED!r}"
    )


def _reopen(admin: Admin, title: str, role: str = ROLE_EDITOR) -> None:
    admin.open_list(role)
    admin.open_entry_by_edit_link(title)


def _bring_to_front(home: HomePromoBannersPage, alt: str) -> None:
    for _ in range(home.real_slide_count() + 2):
        if home.current_slide_alt_text() == alt:
            return
        home.click_next()
    assert home.current_slide_alt_text() == alt, f"could not bring slide {alt!r} on screen"


def _big_jpg(tag: str) -> str:
    """A real, decodable JPEG over 3 MB, written to temp (never fixtures/)."""
    import os

    from PIL import Image

    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}-big.jpg"
    img = Image.frombytes("RGB", (2600, 2600), os.urandom(2600 * 2600 * 3))
    img.save(path, "JPEG", quality=100)
    assert path.stat().st_size > 3 * 1024 * 1024, f"generated file is only {path.stat().st_size} bytes"
    return str(path)


def _small_image(tag: str, fmt: str) -> str:
    from PIL import Image

    path = Path(tempfile.gettempdir()) / f"QCTEST-{tag}.{fmt.lower()}"
    Image.new("RGB", (40, 20), (120, 20, 40)).save(path, fmt)
    return str(path)


def _denial(page, locale: str | None) -> None:
    """Site Member (signed in, no CMS role) on the manage URL: no form, no
    rows, a positive denial signal, and nothing created."""
    admin = Admin(page)
    admin.sign_in(ROLE_SITE_MEMBER)
    assert CmsLoginPage(page).login_succeeded(), "Site Member did not sign in — a denial would prove nothing"
    resp = page.goto(admin._manage_url(locale=locale), wait_until="domcontentloaded")
    assert page.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 0, "Site Member was given the Add Banner form"
    assert page.locator("a[data-qc-oel-delete]").count() == 0, "Site Member was shown banner rows"
    body = page.locator("body").inner_text().casefold()
    signals = ("permission", "not found", "access denied", "sign in", "صلاحية", "رفض", "غير موجود")
    denied = (resp is not None and resp.status in (401, 403, 404)) or any(s in body for s in signals)
    assert denied, f"no positive denial signal for Site Member (HTTP {resp.status if resp else '?'})"


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@allure.title("Site Member is denied Promotional Banners management (English)")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.tc_135115
def test_member_denied_promo_banner_management_en(page):
    """Account: Site Member (no CMS role). 135115 steps 1-3."""
    _denial(page, "en")


@allure.title("Site Member is denied Promotional Banners management (Arabic)")
@pytest.mark.auth
@pytest.mark.bilingual
@pytest.mark.tc_135116
def test_member_denied_promo_banner_management_ar(page):
    """Account: Site Member, Arabic admin locale (`/ar/...manage-promotional-banner`)."""
    _denial(page, "ar")


@allure.title("User without Home Page content permission is denied by direct URL")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.tc_135226
def test_user_without_permission_denied_by_direct_url(page):
    """Account: Site Member. Direct navigation to the management URL."""
    _denial(page, None)


@allure.title("Site Content Editor can access Promotional Banners management with its controls")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_135225
def test_editor_can_access_promo_banner_management(page):
    """Account: Site Content Editor. List + Add form + Delete/submit controls."""
    admin = Admin(page)
    admin.open_list(ROLE_EDITOR)
    assert page.locator(admin.ENTRIES_TABLE_ROW).count() >= 1, "no banner list rendered for the Editor"
    assert page.locator("a[data-qc-oel-delete]").count() >= 1, "Editor is offered no Delete control"
    assert page.get_by_role("link", name="Edit").count() >= 1, "Editor is offered no Edit control"
    assert page.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 1, "Add (Save as Draft) form missing"
    assert page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).count() == 1, "publish/submit control missing"


# ---------------------------------------------------------------------------
# Lifecycle (Functional-High)
# ---------------------------------------------------------------------------
@allure.title("Site Content Editor can create and publish a new promotional banner slot")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.tc_135117
def test_create_and_publish_new_banner_slot(page):
    """Account: Site Content Editor (privileged submit -> Published).
    Save as Draft first, then submit; History must record the transition."""
    admin = Admin(page)
    title = qctest_title(135117, "create-publish")
    try:
        _create(admin, title, extra={"redirect_url": "https://qatarchamber.com/news"})
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert ac._history_has(admin, title), f"{title!r}: no History trail recorded"
    finally:
        admin.delete_disposable(title)


@allure.title("Site Content Editor can edit an existing published banner slot (Display Order)")
@pytest.mark.functional_high
@pytest.mark.tc_135118
def test_edit_existing_banner_display_order(page):
    """Account: Site Content Editor. QCTEST banner published at 9900, edited to
    10000 (case: 1 -> 2; see module docstring), stored value re-read."""
    admin = Admin(page)
    title = qctest_title(135118, "edit-order")
    try:
        _publish_as_editor(admin, title)
        _reopen(admin, title)
        assert admin.value("display_order") == "9900"
        admin.fill("display_order", "10000")
        admin.submit_for_review()
        _reopen(admin, title)
        assert admin.value("display_order") == "10000", f"Display Order stored {admin.value('display_order')!r}"
    finally:
        admin.delete_disposable(title)


@pytest.mark.functional_high
@pytest.mark.parametrize(
    "tc_id,start,end",
    [pytest.param(135119, False, True, marks=pytest.mark.tc_135119, id="135119-enable"),
     pytest.param(135120, True, False, marks=pytest.mark.tc_135120, id="135120-disable")],
)
def test_toggle_banner_active_status(page, tc_id, start, end):
    """Account: Site Content Editor. Active Status flipped on a QCTEST banner and
    the stored value re-read after save. The cases have no workflow-state step
    (locate, toggle, Save, stored value), so the record is saved with Save as
    Draft and no workflow state is asserted (CORRECTED 2026-10-07: a Published
    precondition here failed 135119 on the "Inactive" display state, which the
    case does not mention)."""
    admin = Admin(page)
    title = qctest_title(tc_id, "toggle")
    try:
        _create(admin, title, active=start)
        admin.save_as_draft()
        _reopen(admin, title)
        assert admin.flag("active_status") is start
        admin.set_flag("active_status", end)
        admin.save_as_draft()
        _reopen(admin, title)
        assert admin.flag("active_status") is end, f"Active Status stored {admin.flag('active_status')!r}"
    finally:
        admin.delete_disposable(title)


@allure.title("Site Content Editor can delete a promotional banner slot")
@pytest.mark.functional_high
@pytest.mark.tc_135121
def test_delete_banner_slot(page, browser):
    """Account: Site Content Editor. Draft QCTEST banner deleted by exact title."""
    admin = Admin(page)
    title = qctest_title(135121, "delete")
    ctx, anon = _anon(browser)
    try:
        _create(admin, title)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        assert admin.delete_disposable(title), f"{title!r}: Delete did not run"
        assert not admin.entry_exists(title, ROLE_EDITOR), f"{title!r} still listed after delete"
        assert not _public_present(anon, title, expect=False, timeout=15)
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("Site Content Editor can save a new banner slot as Draft; not public")
@pytest.mark.functional_high
@pytest.mark.tc_135122
def test_save_new_banner_slot_as_draft(page, browser):
    """Account: Site Content Editor. Draft with Active ticked; logged-out
    visitor must not see it."""
    _draft_not_public(page, browser, 135122)


@allure.title("Submitting a draft banner for review lands on Pending Review (Author)")
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.tc_135123
def test_submit_draft_banner_for_review(page):
    """Account: Site Content Author. The case expects Pending Review, which is
    the Author's path; an Editor's submit bypasses review (standards.md,
    Content Editorial Workflow), so the Editor cannot produce this outcome."""
    admin = Admin(page)
    title = qctest_title(135123, "review")
    try:
        _create(admin, title, ROLE_AUTHOR)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_PENDING_REVIEW
        assert not admin.row_offers_action(title, "approve"), "Author is offered Approve on its own entry"
    finally:
        admin.delete_disposable(title, ROLE_EDITOR)


@allure.title("Publishing a Pending Review banner makes it live on the Home Page")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.workflow
@pytest.mark.tc_135124
def test_publishing_pending_review_banner_makes_it_live(page, browser):
    """Accounts: Author submits (-> Pending Review), Editor approves
    (-> Published). Public check in a logged-out context."""
    _author_then_editor_publish(page, browser, 135124)


@allure.title("Unpublishing a published banner removes it from the Home Page")
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.tc_135125
def test_unpublishing_banner_removes_it_from_home_page(page, browser):
    """Account: Site Content Editor. Published+Active -> visible; Unpublish ->
    Unpublished (its own state, not Draft) -> gone for a visitor."""
    _unpublish_hides(page, browser, 135125)


@allure.title("Unpublishing a banner removes it from the Home Page after cache refresh")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.tc_135185
def test_unpublishing_banner_removes_it_after_cache_refresh(page, browser):
    """Account: Site Content Editor. As 135125, polled through the cache."""
    _unpublish_hides(page, browser, 135185)


@allure.title("Admin creates, submits, publishes and sees a banner on the Home Page end to end")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.web
@pytest.mark.tc_135184
def test_create_publish_and_see_banner_on_home_page_e2e(page, browser):
    """Accounts: Author (Draft -> Submit -> Pending Review), Editor (approve ->
    Published). Visitor sees the EN image, alt text and redirect link."""
    _author_then_editor_publish(page, browser, 135184, redirect="https://qatarchamber.com/news")


@allure.title("Deactivating a published banner hides it without changing its workflow state")
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.tc_135186
def test_deactivate_published_banner_preserves_workflow_state(page, browser):
    """Account: Site Content Editor."""
    admin = Admin(page)
    title = qctest_title(135186, "deactivate")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title)
        assert _public_present(anon, title), f"precondition: {title!r} not visible after publish"
        _reopen(admin, title)
        admin.set_flag("active_status", False)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED, "workflow state changed on deactivate"
        assert not _public_present(anon, title, expect=False), f"{title!r} inactive but still public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("A banner only displays within its Start/End date range")
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.tc_135191
def test_banner_visible_only_within_start_end_date_range(page, browser):
    """Account: Site Content Editor. Manual-tagged case automated with QA
    Manager approval (2026-09-02). Start=today, End=today+7 -> visible; the
    "after End Date" half is reached by moving the window into the past
    (Start=today-8, End=today-1) instead of waiting a week — disclosed."""
    admin = Admin(page)
    title = qctest_title(135191, "range")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, extra={"start_date": _day(0), "end_date": _day(7)})
        assert _public_present(anon, title), f"{title!r} in range but not public"
        _reopen(admin, title)
        admin.fill("start_date", _day(-8))
        admin.fill("end_date", _day(-1))
        admin.submit_for_review()
        assert not _public_present(anon, title, expect=False), f"{title!r} past its End Date but still public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


# ---------------------------------------------------------------------------
# Public-visibility rules driven by a disposable banner (Web)
# ---------------------------------------------------------------------------
@allure.title("A published, active, in-range banner displays on the Home Page")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_135127
def test_in_range_published_active_banner_displays(page, browser):
    """Account: Site Content Editor; both gates + Start=today-1, End=today+7."""
    admin = Admin(page)
    title = qctest_title(135127, "in-range")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, extra={"start_date": _day(-1), "end_date": _day(7)})
        ac._assert_active_ticked(admin, title)
        assert _public_present(anon, title), f"{title!r} Published+Active+in range but not public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("A banner outside its date range does not display")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.tc_135128
def test_out_of_range_banner_not_displayed(page, browser):
    """Account: Site Content Editor; Published + Active, range in the future."""
    admin = Admin(page)
    title = qctest_title(135128, "future")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, extra={"start_date": _day(30), "end_date": _day(37)})
        ac._assert_active_ticked(admin, title)
        assert not _public_present(anon, title, expect=False, timeout=30), f"{title!r} future range but public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("A Draft banner slot does not display on the Home Page")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.tc_135129
def test_draft_banner_not_displayed(page, browser):
    """Account: Site Content Editor."""
    _draft_not_public(page, browser, 135129)


@allure.title("A Draft banner never displays even with Active = true")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.tc_135262
def test_draft_active_banner_never_displays(page, browser):
    """Account: Site Content Editor (Draft, Active ticked)."""
    _draft_not_public(page, browser, 135262)


@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.parametrize(
    "tc_id",
    [pytest.param(135130, marks=pytest.mark.tc_135130, id="135130-inactive"),
     pytest.param(135257, marks=pytest.mark.tc_135257, id="135257-active-false")],
)
def test_published_inactive_banner_not_displayed(page, browser, tc_id):
    """Account: Site Content Editor. Published with Active Status = false:
    status must be Published and the visitor must not see it."""
    admin = Admin(page)
    title = qctest_title(tc_id, "inactive")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, active=False)
        _reopen(admin, title)
        assert admin.flag("active_status") is False
        assert not _public_present(anon, title, expect=False, timeout=30), f"{title!r} inactive but public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("Active Status = true saves and takes effect")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_135256
def test_active_status_true_takes_effect(page, browser):
    """Account: Site Content Editor."""
    admin = Admin(page)
    title = qctest_title(135256, "active")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title)
        ac._assert_active_ticked(admin, title)
        assert _public_present(anon, title), f"{title!r} Active + Published but not public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.parametrize(
    "tc_id,url,new_tab",
    [pytest.param(135126, "https://qatarchamber.com/about", False, marks=pytest.mark.tc_135126, id="135126"),
     pytest.param(135188, "https://qatarchamber.com/news", True, marks=pytest.mark.tc_135188, id="135188-new-tab"),
     pytest.param(135189, "https://qatarchamber.com/about", False, marks=pytest.mark.tc_135189, id="135189-same-tab")],
)
def test_banner_click_opens_redirect(page, browser, tc_id, url, new_tab):
    """Account: Site Content Editor builds the banner; a logged-out visitor
    clicks it. New tab: a popup opens on the URL and the Home tab stays.
    Same tab: the current tab navigates and no popup opens."""
    admin = Admin(page)
    title = qctest_title(tc_id, "click")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, extra={"redirect_url": url, "open_new_tab": "true" if new_tab else ""})
        assert _public_present(anon, title), f"precondition: {title!r} not public"
        home = HomePromoBannersPage(anon)
        link = home.real_banner_link(title)
        assert link.get("href", "").rstrip("/") == url.rstrip("/"), f"banner href {link!r} != {url!r}"
        _bring_to_front(home, title)
        img = anon.locator(f'{home.REAL_SLIDE_IMG}[alt="{title}"]').first
        if new_tab:
            with ctx.expect_page(timeout=30000) as popup:
                img.click()
            assert "qatarchamber.com" in popup.value.url, f"new tab opened {popup.value.url!r}"
            assert "/home" in anon.url, "the original Home Page tab did not stay open"
        else:
            opened = []
            ctx.on("page", lambda p: opened.append(p))
            img.click()
            # HEALED 2026-10-07: the external site never fired `load` within 30s;
            # the navigation commit is the same-tab signal the case asserts.
            anon.wait_for_url("**qatarchamber.com/**", timeout=30000, wait_until="commit")
            assert not opened, "a new tab was opened for an Open in New Tab = false banner"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("Clicking a banner with a broken redirect target shows the 404 page")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.tc_135190
def test_banner_broken_redirect_shows_404(page, browser):
    """Account: Site Content Editor; redirect to https://qatarchamber.com/deleted-page,
    same tab. The navigation response must be a 404."""
    url = "https://qatarchamber.com/deleted-page"
    admin = Admin(page)
    title = qctest_title(135190, "404")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, extra={"redirect_url": url})
        assert _public_present(anon, title), f"precondition: {title!r} not public"
        home = HomePromoBannersPage(anon)
        _bring_to_front(home, title)
        img = anon.locator(f'{home.REAL_SLIDE_IMG}[alt="{title}"]').first
        with anon.expect_navigation(timeout=30000) as nav:
            img.click()
        resp = nav.value
        assert resp is not None and resp.status == 404, (
            f"broken redirect landed on HTTP {resp.status if resp else '?'} at {anon.url!r}, not 404"
        )
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


# ---------------------------------------------------------------------------
# Field validation (Functional-Low)
# ---------------------------------------------------------------------------
@pytest.mark.functional_low
@pytest.mark.parametrize(
    "tc_id,key,other",
    [pytest.param(135133, "image_en", "image_ar", marks=pytest.mark.tc_135133, id="135133-en"),
     pytest.param(135230, "image_en", "image_ar", marks=pytest.mark.tc_135230, id="135230-en"),
     pytest.param(135136, "image_ar", "image_en", marks=[pytest.mark.tc_135136, pytest.mark.bilingual], id="135136-ar"),
     pytest.param(135233, "image_ar", "image_en", marks=[pytest.mark.tc_135233, pytest.mark.bilingual], id="135233-ar")],
)
def test_valid_banner_image_accepted(page, tc_id, key, other):
    """Account: Site Content Editor. A valid image is attached and still
    attached after save + reopen (QCTEST Draft)."""
    ac.check_file_accepted(page, Admin, tc_id, key, IMG, files={other: IMG})


@pytest.mark.functional_low
@pytest.mark.parametrize(
    "tc_id,key,other",
    [pytest.param(135134, "image_en", "image_ar", marks=pytest.mark.tc_135134, id="135134-en"),
     pytest.param(135231, "image_en", "image_ar", marks=pytest.mark.tc_135231, id="135231-en"),
     pytest.param(135137, "image_ar", "image_en", marks=[pytest.mark.tc_135137, pytest.mark.bilingual], id="135137-ar"),
     pytest.param(135234, "image_ar", "image_en", marks=[pytest.mark.tc_135234, pytest.mark.bilingual], id="135234-ar")],
)
def test_missing_banner_image_refused(page, tc_id, key, other):
    """Account: Site Content Editor. Required image left empty: Submit is
    refused and nothing is published (Save as Draft skips validation by
    design, so Submit is the validating action)."""
    ac.check_empty_refused(page, Admin, tc_id, key, files={other: IMG})


@pytest.mark.functional_low
@pytest.mark.parametrize(
    "tc_id,key,other,bad_fmt",
    [pytest.param(135232, "image_en", "image_ar", "GIF", marks=pytest.mark.tc_135232, id="135232-en"),
     pytest.param(135235, "image_ar", "image_en", "BMP", marks=[pytest.mark.tc_135235, pytest.mark.bilingual], id="135235-ar")],
)
def test_oversized_or_unsupported_banner_image_refused(page, tc_id, key, other, bad_fmt):
    """Account: Site Content Editor. A > 3 MB JPG, then an unsupported
    format, must each be refused: after Submit the refusal is shown (the size
    branch names the size limit), the field is empty, and nothing is
    persisted. CORRECTED 2026-10-07: the refusal is asserted at Submit, not at
    the picker — the picker attaches an over-size file and Submit refuses it
    ("… accepts files up to 2 MB … Nothing was saved"); a picker exception is
    no longer counted as a refusal."""
    _image_refused_at_submit(page, tc_id, key, other, _big_jpg(str(tc_id)), "size", expect_size_msg=True)
    _image_refused_at_submit(page, tc_id, key, other, _small_image(f"{tc_id}-fmt", bad_fmt), "format")


def _image_refused_at_submit(page, tc_id, key, other, fixture, short, expect_size_msg=False):
    admin = Admin(page)
    title = qctest_title(tc_id, short)
    label = Admin.FIELDS[key].label
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=(key,), files={other: IMG})
        try:
            admin.upload(key, fixture, tag=f"{tc_id}-{short}")
        except Exception:  # noqa: BLE001 — picker may refuse the file; the end state below decides
            page.keyboard.press("Escape")
            try:
                page.locator(admin.UPLOAD_MODAL_IFRAME).first.wait_for(state="detached", timeout=15000)
            except Exception:  # noqa: BLE001
                pass
        admin.submit_for_review()
        assert admin.refusal_visible(), f"{label} {short}: Submit raised no refusal"
        text = admin.refusal_text()
        if expect_size_msg:
            assert "MB" in text, f"{label}: refusal does not name the size limit: {text!r}"
        assert admin.value(key) == "", f"{label} {short}: field still holds {admin.value(key)!r} after the refusal"
        status = admin.status_of(title, ROLE_EDITOR)
        if status:
            assert status != STATUS_PUBLISHED, f"{title!r} was Published despite the refusal"
            admin.open_entry_by_edit_link(title)
            assert admin.value(key) == "", f"{label} {short}: a file persisted on the saved record"
    finally:
        admin.delete_disposable(title)


@allure.title("A valid Banner Alt Text (EN) is saved and rendered as the image alt")
@pytest.mark.functional_low
@pytest.mark.tc_135139
def test_valid_alt_text_en_saved_and_rendered(page, browser):
    """Account: Site Content Editor. The EN alt text is the QCTEST title."""
    admin = Admin(page)
    title = qctest_title(135139, "Valid English alt text")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title)
        _reopen(admin, title)
        assert admin.value("alt_en") == title
        assert _public_present(anon, title), f"alt {title!r} not rendered on the EN Home Page"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("A valid Banner Alt Text (AR) is saved and rendered on the Arabic Home Page")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_135143
def test_valid_alt_text_ar_saved_and_rendered(page, browser):
    """Account: Site Content Editor."""
    admin = Admin(page)
    title = qctest_title(135143, "ar-alt")
    alt_ar = "نص بديل اختبار QCTEST-135143"
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title, extra={"alt_ar": alt_ar})
        _reopen(admin, title)
        assert admin.value("alt_ar") == alt_ar, f"AR alt stored {admin.value('alt_ar')!r}"
        assert _public_present(anon, alt_ar, arabic=True), f"AR alt {alt_ar!r} not rendered on /ar/home"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@pytest.mark.functional_low
@pytest.mark.parametrize(
    "tc_id,url",
    [pytest.param(135147, "https://qatarchamber.com/news", marks=pytest.mark.tc_135147, id="135147"),
     pytest.param(135244, "https://qatarchamber.com/news/summit-2026", marks=pytest.mark.tc_135244, id="135244")],
)
def test_valid_redirect_url_saved(page, tc_id, url):
    """Account: Site Content Editor."""
    ac.check_valid_persists(page, Admin, tc_id, "redirect_url", url, files=FILES, short="url")


@allure.title("A valid Redirect URL (AR) is accepted and stored")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_135247
def test_valid_redirect_url_ar_saved(page):
    """Account: Site Content Editor. AR control "Redirect URL — العربية"."""
    ac.check_valid_persists(page, Admin, 135247, "redirect_url", "https://qatarchamber.com/news/summit-2026",
                            ar="https://qatarchamber.com/ar/news/summit-2026", files=FILES, short="url-ar")


@allure.title("An invalid Redirect URL (AR) format is refused")
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_135248
def test_invalid_redirect_url_ar_refused(page):
    """Account: Site Content Editor. EN valid, AR `htp:/broken`: Submit refused,
    nothing published."""
    admin = Admin(page)
    title = qctest_title(135248, "bad-url-ar")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=FILES)
        admin.fill("redirect_url", "https://qatarchamber.com/news")
        admin.fill("redirect_url", "htp:/broken", locale="ar")
        ac._submit_and_expect_refusal(admin, title, "Redirect URL (AR)='htp:/broken'")
    finally:
        admin.delete_disposable(title)


@allure.title("An invalid Redirect URL (EN) format is refused")
@pytest.mark.functional_low
@pytest.mark.tc_135245
def test_invalid_redirect_url_refused(page):
    """Account: Site Content Editor. `not-a-valid-url`."""
    ac.check_value_refused(page, Admin, 135245, "redirect_url", "not-a-valid-url", files=FILES)


@allure.title("A javascript: Redirect URL is refused or stored inert")
@pytest.mark.edge
@pytest.mark.tc_135271
def test_script_scheme_redirect_url_refused_or_inert(page, browser):
    """Account: Site Content Editor. Pass = Submit refused, OR the banner
    publishes and a visitor's click raises no script dialog."""
    admin = Admin(page)
    title = qctest_title(135271, "xss")
    ctx, anon = _anon(browser)
    try:
        _create(admin, title, extra={"redirect_url": "javascript:alert('xss')"})
        admin.submit_for_review()
        if admin.refusal_visible():
            assert admin.status_of(title, ROLE_EDITOR) != STATUS_PUBLISHED
            return
        if admin.status_of(title, ROLE_EDITOR) != STATUS_PUBLISHED:
            return
        if not _public_present(anon, title):
            return
        dialogs = []
        anon.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
        home = HomePromoBannersPage(anon)
        _bring_to_front(home, title)
        anon.locator(f'{home.REAL_SLIDE_IMG}[alt="{title}"]').first.click()
        anon.wait_for_load_state("domcontentloaded")
        assert not dialogs, f"javascript: redirect executed on click: {dialogs!r}"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


@allure.title("A valid positive Display Order is saved and reflected in slider order")
@pytest.mark.functional_low
@pytest.mark.tc_135152
def test_valid_display_order_saved(page, browser):
    """Account: Site Content Editor. 9900 (case: 3 — see module docstring);
    the QCTEST slide must come after every real banner."""
    admin = Admin(page)
    title = qctest_title(135152, "order")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title)
        _reopen(admin, title)
        assert admin.value("display_order") == "9900"
        assert _public_present(anon, title), f"{title!r} not public"
        alts = HomePromoBannersPage(anon).real_banner_alts()
        real_idx = [alts.index(t) for t in REAL_BANNER_TITLES if t in alts]
        assert real_idx and alts.index(title) > max(real_idx), f"slider order {alts!r}"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


# ---------------------------------------------------------------------------
# shared bodies
# ---------------------------------------------------------------------------
def _draft_not_public(page, browser, tc_id: int) -> None:
    admin = Admin(page)
    title = qctest_title(tc_id, "draft")
    ctx, anon = _anon(browser)
    try:
        _create(admin, title, active=True)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_DRAFT
        assert not _public_present(anon, title, expect=False, timeout=30), f"{title!r} (Draft) is public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


def _unpublish_hides(page, browser, tc_id: int) -> None:
    admin = Admin(page)
    title = qctest_title(tc_id, "unpublish")
    ctx, anon = _anon(browser)
    try:
        _publish_as_editor(admin, title)
        assert _public_present(anon, title), f"precondition: {title!r} not visible after publish"
        admin.unpublish(title)
        status = admin.status_of(title, ROLE_EDITOR)
        assert status == STATUS_UNPUBLISHED, f"Unpublish left {title!r} on {status!r}"
        assert not _public_present(anon, title, expect=False), f"{title!r} Unpublished but still public"
    finally:
        admin.delete_disposable(title)
        ac._close(ctx)


def _author_then_editor_publish(page, browser, tc_id: int, redirect: str | None = None) -> None:
    admin = Admin(page)
    title = qctest_title(tc_id, "review-publish")
    ctx, anon = _anon(browser)
    try:
        _create(admin, title, ROLE_AUTHOR, extra={"redirect_url": redirect} if redirect else None)
        admin.save_as_draft()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_DRAFT
        admin.open_entry_by_edit_link(title)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_AUTHOR) == STATUS_PENDING_REVIEW
        admin.open_list(ROLE_EDITOR)
        admin.approve_entry(title)
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        ac._assert_active_ticked(admin, title)
        assert _public_present(anon, title), f"{title!r} Published + Active but not public"
        home = HomePromoBannersPage(anon)
        assert home.banner_image_src(title), f"{title!r}: no image rendered"
        if redirect:
            href = home.real_banner_link(title).get("href", "")
            assert href.rstrip("/") == redirect.rstrip("/"), f"banner href {href!r} != {redirect!r}"
    finally:
        admin.delete_disposable(title, ROLE_EDITOR)
        ac._close(ctx)

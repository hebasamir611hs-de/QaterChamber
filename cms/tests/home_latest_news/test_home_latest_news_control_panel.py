"""
cms/tests/home_latest_news/test_home_latest_news_control_panel.py —
Control_Panel cases for PBI 129372 (Home "Latest News" section), suite 134450.

REWRITTEN 2026-10-07 (Phase 3, 7-state workflow migration):
  - ACCOUNT: every case signs in as a named role through
    `config.settings.cms_role_credentials()` — Site Content Editor (the PBI's
    admin role: Publish lands on Published directly) or Site Member for the
    permission-denial case. Never TEST_USER.
  - PATH: Object Authoring only (manage-news-article,
    manage-home-latest-news-section). Content & Data is gone.
  - VOCABULARY: STATUS_* constants; Unpublish lands on Unpublished (not Draft).
  - VISIBILITY: both gates (Published + Active ticked) are set explicitly on
    every create->public case; public reads use a fresh logged-out context.
  - TEST DATA: disposable QCTEST-<tc> records, deleted in `finally` every run,
    by exact QCTEST title (news) or by verified entry code (section). The real
    section record QCDEMO-129372-HOME_LATEST_NEWS_SECTION-MAIN and the real
    articles are never opened for write.
  - Mandatory-field cases press Publish (Save as Draft skips required-field
    validation by design) with Active Status UNticked, so an unexpected
    accept can never reach the public page.
  - Toast wording is not asserted (not a bug class on this project); the
    status transition and the public effect are.

Withdrawn from the old docstring: "no Pending Review on this build",
"Published is Approved", "Unpublished is Draft" — artifacts of TEST_USER.
"""

from __future__ import annotations

import datetime
import importlib.util
from pathlib import Path

import allure
import pytest

from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_latest_news.home_latest_news_admin_page import (
    F_ACTIVE,
    F_PUB_DATE,
    F_THUMBNAIL,
    F_TITLE,
    F_TITLE_AR,
    S_ACTIVE,
    S_DESC,
    S_DESC_AR,
    S_HEADING,
    S_HEADING_AR,
    S_TAG,
    HomeLatestNewsAdminPage,
)
from config.settings import cms_role_credentials, control_panel_url
from core.utils.logger import get_logger
from web.pages.home_latest_news.home_latest_news_page import HomeLatestNewsPage

logger = get_logger("test_home_latest_news_control_panel")

EDITOR = "Site Content Editor"
THUMBNAIL_FIXTURE = "cms/tests/home_latest_news/fixtures/news_thumbnail.png"
PUBLIC_TIMEOUT_MS = 90000

# One group for everything that publishes a QCTEST article or reads which
# cards are live (web module shares it).
NEWS_GROUP = pytest.mark.xdist_group("news_article_129372")
# Section entries are created beside the live section record; keep them serial.
SECTION_GROUP = pytest.mark.xdist_group("home_latest_news_section_129372")

TODAY = datetime.date.today()


def _anon_home(browser):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    return ctx, HomeLatestNewsPage(ctx.new_page())


def _editor(page) -> HomeLatestNewsAdminPage:
    return HomeLatestNewsAdminPage(page).sign_in_as(EDITOR)


def _publish_article(admin: HomeLatestNewsAdminPage, title: str, title_ar: str,
                     pub_date: datetime.date, active: bool = True) -> str:
    """Create -> Save as Draft -> Publish as Editor; returns the polled status."""
    admin.fill_news_article(title, title_ar, pub_date, THUMBNAIL_FIXTURE, active=active)
    admin.news.save_as_draft()
    assert admin.wait_row_status(admin.news, title, STATUS_DRAFT) == STATUS_DRAFT, (
        f"{title!r} did not save as Draft"
    )
    admin.news.open_entry_by_edit_link(title)
    admin.news.submit_for_review()
    return admin.wait_row_status(admin.news, title, STATUS_PUBLISHED)


# ===========================================================================
# Lifecycle
# ===========================================================================
@allure.epic("Home Page")
@allure.feature("Latest News")
@allure.story("Content workflow - publish")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing a news article surfaces it in the Latest News section, newest first")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129372
@pytest.mark.tc_135273
@NEWS_GROUP
def test_publishing_news_article_surfaces_it_newest_first(page, browser):
    """ADO-135273 (P1). Account: QC Site Content Editor (156488) — the role the
    case names; its Publish lands on Published directly, which is the
    "submit for review, then publish" path for a privileged submitter.
    Category and body (step 3) are not fields of NewsArticle (guide §11 and
    the live form); every field that exists is filled. Dated today so it must
    be card 0."""
    title = "QCTEST-135273 Published News Article"
    title_ar = "QCTEST-135273 خبر منشور"
    admin = _editor(page)
    anon_ctx, home = _anon_home(browser)
    try:
        admin.delete_qctest_article(title)
        with allure.step("Create, Save as Draft, Publish as Editor (Active ticked)"):
            admin.fill_news_article(title, title_ar, TODAY, THUMBNAIL_FIXTURE, active=True)
            assert admin.value(F_TITLE) == title
            assert admin.value(F_TITLE_AR) == title_ar
            assert admin.checkbox_checked(F_ACTIVE)
            admin.news.save_as_draft()
            assert admin.wait_row_status(admin.news, title, STATUS_DRAFT) == STATUS_DRAFT
            admin.news.open_entry_by_edit_link(title)
            admin.news.submit_for_review()
            status = admin.wait_row_status(admin.news, title, STATUS_PUBLISHED)
        assert status == STATUS_PUBLISHED, f"{title!r} status {status!r}, expected Published"

        with allure.step("Logged-out visitor sees it in Latest News"):
            appeared = home.reload_until_article_matches(title, True, timeout_ms=PUBLIC_TIMEOUT_MS)
        assert appeared, f"published+active {title!r} not in Latest News within {PUBLIC_TIMEOUT_MS}ms"

        with allure.step("It is the first card (newest first)"):
            home.scroll_to_section()
            first = home.card_title_text(0)
        assert first == title, f"expected {title!r} as card 0, got {first!r} ({home.card_titles()})"
    finally:
        admin.delete_qctest_article(title)
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("Latest News")
@allure.story("Content workflow - unpublish")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Unpublishing a news article removes it from the Latest News section")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129372
@pytest.mark.tc_135274
@NEWS_GROUP
def test_unpublishing_news_article_removes_it_from_latest_news(page, browser):
    """ADO-135274 (P1). Account: QC Site Content Editor. The "published
    article" is a disposable QCTEST one (never a real article). Unpublish is
    the row action and lands on Unpublished (its own state, not Draft)."""
    title = "QCTEST-135274 Unpublish News Article"
    title_ar = "QCTEST-135274 خبر لإلغاء النشر"
    admin = _editor(page)
    anon_ctx, home = _anon_home(browser)
    try:
        admin.delete_qctest_article(title)
        with allure.step("Precondition: a published, active QCTEST article"):
            status = _publish_article(admin, title, title_ar, TODAY)
        assert status == STATUS_PUBLISHED, f"precondition: {title!r} is {status!r}"
        live = home.reload_until_article_matches(title, True, timeout_ms=PUBLIC_TIMEOUT_MS)
        assert live, f"precondition: {title!r} never went live, so removal cannot be observed"

        with allure.step("Unpublish it from the entries list"):
            admin.news.open_entries_list()
            admin.news.unpublish_entry(title)
            after = admin.wait_row_status(admin.news, title, STATUS_UNPUBLISHED)
        assert after == STATUS_UNPUBLISHED, f"after Unpublish {title!r} is {after!r}"

        with allure.step("Logged-out visitor no longer sees it"):
            gone = home.reload_until_article_matches(title, False, timeout_ms=PUBLIC_TIMEOUT_MS)
        assert gone, f"unpublished {title!r} still in Latest News after {PUBLIC_TIMEOUT_MS}ms"
    finally:
        admin.delete_qctest_article(title)
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("Latest News")
@allure.story("CMS authoring workflow — save as draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Saving an article as Draft does not surface it in the Latest News section")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129372
@pytest.mark.tc_135279
@NEWS_GROUP
def test_save_article_as_draft_not_in_latest_news(page, browser):
    """ADO-135279 (P2). Account: QC Site Content Editor. Active Status is
    TICKED and the date is today, so the only thing keeping the article off
    the section is its Draft state — absence cannot pass for the wrong reason."""
    title = "QCTEST-135279 Draft Test Article"
    admin = _editor(page)
    anon_ctx, home = _anon_home(browser)
    try:
        admin.delete_qctest_article(title)
        with allure.step("Create and Save as Draft (Active ticked, dated today)"):
            admin.fill_news_article(title, "QCTEST-135279 مسودة", TODAY, THUMBNAIL_FIXTURE, active=True)
            admin.news.save_as_draft()
            status = admin.wait_row_status(admin.news, title, STATUS_DRAFT)
        assert status == STATUS_DRAFT, f"{title!r} is {status!r}, expected Draft"

        with allure.step("Logged-out visitor does not see it"):
            home.open_home()
            home.scroll_to_section()
            visible = home.article_visible_by_title(title)
        assert not visible, f"Draft {title!r} is visible in Latest News"
    finally:
        admin.delete_qctest_article(title)
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("Latest News")
@allure.story("Sort order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Latest News section sorts cards by publication date descending")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129372
@pytest.mark.tc_135275
@NEWS_GROUP
def test_latest_news_sorts_by_publication_date_descending(page, browser):
    """ADO-135275 (P2, tagged Web; its step 1 is a CMS publish, so it lives
    here). Account: QC Site Content Editor. Three QCTEST articles dated
    today-2, today, today-1 (published in that scrambled order so creation
    order cannot fake the sort). The section holds 3 cards
    (data-qc-count=3), so they must fill it newest -> oldest."""
    arts = [
        ("QCTEST-135275 Sort Oldest", TODAY - datetime.timedelta(days=2)),
        ("QCTEST-135275 Sort Newest", TODAY),
        ("QCTEST-135275 Sort Middle", TODAY - datetime.timedelta(days=1)),
    ]
    admin = _editor(page)
    anon_ctx, home = _anon_home(browser)
    try:
        for t, _ in arts:
            admin.delete_qctest_article(t)
        with allure.step("Publish three articles with distinct dates"):
            for t, d in arts:
                status = _publish_article(admin, t, f"{t} ع", d)
                assert status == STATUS_PUBLISHED, f"{t!r} is {status!r}"
        with allure.step("Logged-out Home Page: card order"):
            home.reload_until_article_matches(arts[0][0], True, timeout_ms=PUBLIC_TIMEOUT_MS)
            home.scroll_to_section()
            titles = home.card_titles()
            dates = home.card_dates()
        expected = ["QCTEST-135275 Sort Newest", "QCTEST-135275 Sort Middle", "QCTEST-135275 Sort Oldest"]
        assert titles[:3] == expected, f"card order {titles}, expected {expected}"
        assert dates == sorted(dates, reverse=True), f"card dates not descending: {dates}"
    finally:
        for t, _ in arts:
            admin.delete_qctest_article(t)
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("Latest News")
@allure.story("Card navigation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking a news card navigates to the correct full article page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129372
@pytest.mark.tc_135278
@NEWS_GROUP
def test_clicking_news_card_opens_matching_article(page, browser):
    """ADO-135278 (P1, tagged Web). The case names a 'Trade Fair 2026' card;
    no such real article exists, so a disposable one is published by the
    Editor as "QCTEST-135278 Trade Fair 2026" (prefix required by the
    test-data rule). A logged-out visitor clicks it and the detail page
    title must match exactly."""
    title = "QCTEST-135278 Trade Fair 2026"
    admin = _editor(page)
    anon_ctx, home = _anon_home(browser)
    try:
        admin.delete_qctest_article(title)
        status = _publish_article(admin, title, "QCTEST-135278 معرض التجارة 2026", TODAY)
        assert status == STATUS_PUBLISHED, f"precondition: {title!r} is {status!r}"
        with allure.step("Logged-out Home Page renders the card with all four elements"):
            assert home.reload_until_article_matches(title, True, timeout_ms=PUBLIC_TIMEOUT_MS), (
                f"{title!r} never appeared in Latest News"
            )
            home.scroll_to_section()
            idx = home.card_index_by_title(title)
            assert idx >= 0
            assert home.card_elements_all_visible(idx), "card is missing thumbnail/date/title/view count"
        with allure.step("Click the card"):
            home.click_card(idx)
            heading = home.detail_heading_text()
        assert "news-article" in home.page.url, f"card went to {home.page.url!r}"
        assert heading == title, f"detail title {heading!r} != {title!r}"
    finally:
        admin.delete_qctest_article(title)
        anon_ctx.close()


# ===========================================================================
# News Article field validation (Functional-Low, P2) — Editor
# ===========================================================================
def _read_back(admin: HomeLatestNewsAdminPage, title: str, label: str, expected: str) -> str:
    """Stored value of `label`, polled until it equals `expected` (the edit
    form populates after it mounts) or 10 s pass."""
    admin.news.open_entries_list()
    admin.news.open_entry_by_edit_link(title)
    admin._await_value(label, expected)
    return admin.value(label)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("News Article Title (EN) accepts a valid value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135302
@NEWS_GROUP
def test_news_title_en_accepts_valid_value(page):
    """ADO-135302. Editor. Enter Title (EN), Save as Draft -> Draft saved
    with the entered title (read back from the stored record)."""
    title = "QCTEST-135302 Chamber Signs Trade Agreement"
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        admin.fill_news_article(title=title, title_ar="QCTEST-135302 ع", active=False)
        admin.news.save_as_draft()
        assert admin.wait_row_status(admin.news, title, STATUS_DRAFT) == STATUS_DRAFT
        assert _read_back(admin, title, F_TITLE, title) == title
    finally:
        admin.delete_qctest_article(title)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("News Article Title (AR) accepts a valid value, rendered RTL")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129372
@pytest.mark.tc_135306
@NEWS_GROUP
def test_news_title_ar_accepts_valid_value(page):
    """ADO-135306. Editor. Enter Title (AR), Save as Draft -> stored, RTL."""
    title = "QCTEST-135306 Arabic Title Article"
    title_ar = "QCTEST-135306 الغرفة توقع اتفاقية تجارية"
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        admin.fill_news_article(title=title, title_ar=title_ar, active=False)
        admin.news.save_as_draft()
        assert admin.wait_row_status(admin.news, title, STATUS_DRAFT) == STATUS_DRAFT
        assert _read_back(admin, title, F_TITLE_AR, title_ar) == title_ar
        direction = admin.box(F_TITLE_AR).evaluate(
            "el => getComputedStyle(el).direction"
        )
        assert direction == "rtl", f"Title (AR) renders {direction!r}, expected rtl"
    finally:
        admin.delete_qctest_article(title)


def _make_jpg(tmp_path: Path, size: int = 800 * 1024) -> str:
    spec = importlib.util.spec_from_file_location("fixture_factory", "tools/fixture_factory.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = tmp_path / "thumbnail.jpg"
    out.write_bytes(mod.make_jpg(size))
    return str(out)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("A valid JPG thumbnail under 2MB uploads successfully")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135310
@NEWS_GROUP
def test_news_thumbnail_valid_jpg_uploads(page, browser, tmp_path):
    """ADO-135310. Editor. Upload thumbnail.jpg (800 KB, generated by
    tools/fixture_factory.make_jpg) -> uploads; Save as Draft -> stored with
    the thumbnail. The "previewed on the card" half needs a published card;
    a draft has none, so it is asserted on the stored record."""
    title = "QCTEST-135310 JPG Thumbnail"
    jpg = _make_jpg(tmp_path)
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        admin.fill_news_article(title=title, title_ar="QCTEST-135310 ع", thumbnail=jpg, active=False)
        assert "thumbnail" in admin.news.uploaded_filename(F_THUMBNAIL), "JPG did not populate the field"
        admin.news.save_as_draft()
        assert admin.wait_row_status(admin.news, title, STATUS_DRAFT) == STATUS_DRAFT
        admin.news.open_entry_by_edit_link(title)
        stored = admin.news.current_file_name(F_THUMBNAIL)
        assert "thumbnail" in stored, f"stored thumbnail is {stored!r}"

        # Card half ("previewed on the card"): publish it with Active ticked
        # (dated today -> it is card 0 for a visitor), read the card, then
        # the finally removes it at once.
        with allure.step("Publish with Active ticked and check the visitor's card thumbnail"):
            admin.news.set_checkbox(F_ACTIVE, True)
            admin.news.submit_for_review()
            assert admin.wait_row_status(admin.news, title, STATUS_PUBLISHED) == STATUS_PUBLISHED
            anon_ctx, home = _anon_home(browser)
            try:
                assert home.reload_until_article_matches(title, True, timeout_ms=PUBLIC_TIMEOUT_MS), (
                    f"{title!r} never reached the section"
                )
                home.scroll_to_section()
                idx = home.card_index_by_title(title)
                img = home._card(idx).locator(home.CARD_IMAGE)
                src = img.get_attribute("src") or ""
                loaded = img.evaluate("i => i.complete && i.naturalWidth > 0")
            finally:
                anon_ctx.close()
        assert "thumbnail" in src and loaded, f"card thumbnail not shown (src={src!r}, loaded={loaded})"
    finally:
        admin.delete_qctest_article(title)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("A valid Publication Date is accepted and stored")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135313
@NEWS_GROUP
def test_news_publication_date_accepted(page, browser):
    """ADO-135313. Editor. Publication Date 2026-08-12, Publish (Active
    ticked) -> Published, date stored; the card half is read in a visitor
    context with the stored record moved first (it ranks behind the live
    top 3). Deleted in the finally right after the read."""
    title = "QCTEST-135313 Publication Date"
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        status = _publish_article(admin, title, "QCTEST-135313 ع", datetime.date(2026, 8, 12), active=True)
        assert status == STATUS_PUBLISHED, f"{title!r} is {status!r}"
        admin.news.open_entry_by_edit_link(title)
        stored = admin.date_value(F_PUB_DATE)
        assert any(s in stored for s in ("12/08/2026", "08/12/2026", "2026-08-12")), (
            f"stored Publication Date {stored!r} is not 2026-08-12"
        )
        # Card half: an Aug-12 article ranks behind the live top 3, so the
        # visitor's articles response is served with THIS stored, published
        # record moved first (visitor context only); the fragment renders it.
        with allure.step("Card shows the publication date (stored record moved first for this visitor)"):
            anon_ctx, home = _anon_home(browser)
            try:
                home.put_article_first(title)
                home.open_home()
                home.page.locator(home.CARD).first.wait_for(timeout=30000)
                home.scroll_to_section()
                first_title = home.card_title_text(0)
                card_date = home.card_date_text(0)
            finally:
                anon_ctx.close()
        assert first_title == title, f"card 0 is {first_title!r}"
        assert card_date in ("Aug 12, 2026", "August 12, 2026", "2026-08-12"), f"card date {card_date!r}"
    finally:
        admin.delete_qctest_article(title)


def _assert_publish_refused(admin: HomeLatestNewsAdminPage, authoring, what: str) -> None:
    if admin.publish_disabled(authoring):
        allure.attach("Publish button rendered disabled — submit blocked client-side",
                      "refusal", allure.attachment_type.TEXT)
        return
    authoring.submit_for_review()
    outcome = admin.save_outcome(authoring)
    allure.attach(admin.refusal_text(authoring) or "(none)", "refusal text", allure.attachment_type.TEXT)
    assert outcome != "unknown", f"Publish with {what}: no success banner and no refusal seen"
    assert outcome == "refused", (
        f"Publish with {what} empty was ACCEPTED — the PBI marks it mandatory"
    )


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("News Article Title (EN) rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135303
@NEWS_GROUP
def test_news_title_en_rejects_empty(page):
    """ADO-135303. Editor. Every other field filled, Title (EN) empty,
    Publish (Draft skips validation) -> refused. Active UNticked."""
    marker = "QCTEST-135303 عنوان فقط"
    admin = _editor(page)
    try:
        admin.fill_news_article(title_ar=marker, pub_date=TODAY, thumbnail=THUMBNAIL_FIXTURE, active=False)
        _assert_publish_refused(admin, admin.news, "Title (EN)")
    finally:
        admin.delete_verified_entry(admin.news, F_TITLE_AR, marker)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("News Article Title (AR) rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129372
@pytest.mark.tc_135307
@NEWS_GROUP
def test_news_title_ar_rejects_empty(page):
    """ADO-135307. Editor. Title (AR) empty, Publish -> refused. Message
    language is not asserted (wording is not a bug class)."""
    title = "QCTEST-135307 Missing Arabic Title"
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        admin.fill_news_article(title=title, pub_date=TODAY, thumbnail=THUMBNAIL_FIXTURE, active=False)
        _assert_publish_refused(admin, admin.news, "Title (AR)")
    finally:
        admin.delete_qctest_article(title)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("Saving an article without a thumbnail is rejected")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135311
@NEWS_GROUP
def test_news_missing_thumbnail_rejected(page):
    """ADO-135311. Editor. All fields but the thumbnail, Publish -> refused."""
    title = "QCTEST-135311 No Thumbnail"
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        admin.fill_news_article(title=title, title_ar="QCTEST-135311 ع", pub_date=TODAY, active=False)
        _assert_publish_refused(admin, admin.news, "Thumbnail Image")
    finally:
        admin.delete_qctest_article(title)


@allure.epic("Home Page")
@allure.feature("Latest News — News Article fields")
@allure.title("Publication Date rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135314
@NEWS_GROUP
def test_news_publication_date_rejects_empty(page):
    """ADO-135314. Editor. Publication Date empty, Publish -> refused."""
    title = "QCTEST-135314 No Publication Date"
    admin = _editor(page)
    try:
        admin.delete_qctest_article(title)
        admin.fill_news_article(title=title, title_ar="QCTEST-135314 ع", thumbnail=THUMBNAIL_FIXTURE, active=False)
        _assert_publish_refused(admin, admin.news, "Publication Date")
    finally:
        admin.delete_qctest_article(title)


# ===========================================================================
# Permission boundary
# ===========================================================================
@allure.epic("Home Page")
@allure.feature("Latest News")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A user without News permissions cannot publish/unpublish articles")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_129372
@pytest.mark.tc_135327
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_user_without_news_permission_cannot_publish(page):
    """ADO-135327 (P2). Account: qc.member.test (site member, no content role)
    — the negative-case account. Login must SUCCEED (so the denial is not a
    broken login), then manage-news-article must offer no create form, no
    rows and no row actions."""
    email, password = cms_role_credentials("Site Member")
    login = CmsLoginPage(page)
    with allure.step("Log in as a site member"):
        login.open_login().login(email, password)
    assert login.login_succeeded(), "site-member login did not succeed"

    with allure.step("Navigate to News Article create/edit"):
        page.goto(control_panel_url("/en/web/qatar-chamber/manage-news-article"), wait_until="domcontentloaded")
        page.wait_for_load_state("load")
    assert login.login_succeeded(), "session was dropped — denial would be meaningless"
    assert page.locator('button:has-text("Save as Draft")').count() == 0, "create form is available"
    assert page.locator('button[type="submit"]:text-is("Publish")').count() == 0, "Publish is available"
    assert page.locator("[data-qc-oel-publish], [data-qc-oel-unpublish], [data-qc-oel-delete]").count() == 0, (
        "row publish/unpublish/delete actions are available"
    )


# ===========================================================================
# Home Latest News Section fields (Functional-Low, P2) — Editor, + Add New only
# ===========================================================================
SECTION_VALUES = {
    S_HEADING: "QCTEST Latest News",
    S_HEADING_AR: "QCTEST آخر الأخبار",
    S_DESC: "QCTEST section description.",
    S_DESC_AR: "QCTEST وصف القسم.",
}


def _fill_section(admin: HomeLatestNewsAdminPage, tag: str, overrides: dict) -> None:
    """Empty create form only; Active Status UNticked (the live section
    record must stay the one visitors see)."""
    admin.open_new_section_form()
    admin.fill(S_TAG, tag)
    values = {**SECTION_VALUES, **overrides}
    for label, value in values.items():
        if value:
            admin.fill(label, value)
    admin.section.set_checkbox(S_ACTIVE, False)


def _section_accepts(admin, tc: str, label: str, value: str) -> None:
    tag = f"QCTEST-{tc} tag"
    try:
        _fill_section(admin, tag, {label: value})
        admin.section.save_as_draft()
        assert admin.save_outcome(admin.section) == "saved", admin.refusal_text(admin.section)
        code = admin.find_code_by_field(admin.section, S_TAG, tag)
        assert code, f"saved section entry with tag {tag!r} not found"
        assert admin._await_value(label, value), f"{label} not stored as {value!r} (read {admin.value(label)!r})"
    finally:
        admin.delete_verified_entry(admin.section, S_TAG, tag)


def _section_rejects_empty(admin, tc: str, label: str) -> None:
    tag = f"QCTEST-{tc} tag"
    try:
        _fill_section(admin, tag, {label: ""})
        _assert_publish_refused(admin, admin.section, label)
    finally:
        admin.delete_verified_entry(admin.section, S_TAG, tag)


_SECTION_MARKS = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.functional_low,
                  pytest.mark.pbi_129372, SECTION_GROUP]


def _section_case(fn):
    for m in _SECTION_MARKS:
        fn = m(fn)
    return allure.feature("Latest News — Section config")(allure.epic("Home Page")(fn))


@_section_case
@pytest.mark.tc_135286
def test_section_heading_en_accepts_valid_value(page):
    """ADO-135286. Editor, new QCTEST section entry. Public "displays as main
    title" half needs the live record -> NEEDS USER."""
    _section_accepts(_editor(page), "135286", S_HEADING, "QCTEST Latest News")


@_section_case
@pytest.mark.tc_135287
def test_section_heading_en_rejects_empty(page):
    """ADO-135287. Section Heading (EN) empty, Publish -> refused."""
    _section_rejects_empty(_editor(page), "135287", S_HEADING)


@_section_case
@pytest.mark.bilingual
@pytest.mark.tc_135290
def test_section_heading_ar_accepts_valid_value(page):
    """ADO-135290. Arabic heading stored. Public RTL half -> NEEDS USER."""
    _section_accepts(_editor(page), "135290", S_HEADING_AR, "QCTEST ابقَ على اطلاع")


@_section_case
@pytest.mark.bilingual
@pytest.mark.tc_135291
def test_section_heading_ar_rejects_empty(page):
    """ADO-135291. Section Heading (AR) empty, Publish -> refused."""
    _section_rejects_empty(_editor(page), "135291", S_HEADING_AR)


@_section_case
@pytest.mark.tc_135294
def test_section_description_en_accepts_rich_text(page):
    """ADO-135294. Description (EN) is Rich Text per the PBI; step 3 applies
    bold. Asserts the field offers a Bold control, then stores the text."""
    admin = _editor(page)
    tag = "QCTEST-135294 tag"
    try:
        _fill_section(admin, tag, {})
        assert admin.has_rich_text_bold_control(S_DESC), (
            "Section Description (EN) is a plain text area with no Bold control; "
            "the PBI types it Rich Text"
        )
    finally:
        admin.delete_verified_entry(admin.section, S_TAG, tag)
    _section_accepts(admin, "135294", S_DESC, "QCTEST Stay informed with the latest developments.")


@_section_case
@pytest.mark.tc_135295
def test_section_description_en_rejects_empty(page):
    """ADO-135295. Section Description (EN) empty, Publish -> refused."""
    _section_rejects_empty(_editor(page), "135295", S_DESC)


@_section_case
@pytest.mark.bilingual
@pytest.mark.tc_135298
def test_section_description_ar_accepts_rich_text(page):
    """ADO-135298. Arabic description stored. Public RTL half -> NEEDS USER."""
    _section_accepts(_editor(page), "135298", S_DESC_AR, "QCTEST ابقَ على اطلاع بآخر المستجدات.")


@_section_case
@pytest.mark.bilingual
@pytest.mark.tc_135299
def test_section_description_ar_rejects_empty(page):
    """ADO-135299. Section Description (AR) empty, Publish -> refused."""
    _section_rejects_empty(_editor(page), "135299", S_DESC_AR)


# ===========================================================================
# P3/P4 cases scripted 2026-10-07 (Rule-4 "Run" list). Editor account.
# Titles carry a per-run suffix: this round runs with QC_KEEP_QCTEST=1 (user:
# "delete nothing this round"), so a re-run must not collide with the last
# run's records. Every create keeps Active Status UNticked -> never public.
# ===========================================================================
import os as _os  # noqa: E402
import time as _time  # noqa: E402

RUN = _os.getenv("QC_RUN_TAG") or _time.strftime("%H%M%S")
S_TAG_AR = "Section Tag — العربية"


def _fill_checked(admin: HomeLatestNewsAdminPage, label: str, value: str) -> None:
    """Fill and read back; refill once if the freshly mounted form dropped it
    (live 2026-10-07: a first fill of Section Tag came back empty twice)."""
    for _ in range(2):
        admin.fill(label, value)
        if admin.value(label) == value:
            return
        admin.page.wait_for_timeout(1000)
    assert admin.value(label) == value, f"{label} would not hold {value!r}"


def _new_section(admin: HomeLatestNewsAdminPage, tc: str, overrides: dict) -> dict:
    values = {
        S_HEADING: f"QCTEST-{tc}-{RUN} Latest News",
        S_HEADING_AR: f"QCTEST-{tc}-{RUN} عنوان",
        S_DESC: f"QCTEST-{tc}-{RUN} description",
        S_DESC_AR: f"QCTEST-{tc}-{RUN} وصف",
        **overrides,
    }
    admin.open_new_section_form()
    for label, value in values.items():
        if value != "":
            _fill_checked(admin, label, value)
    admin.section.set_checkbox(S_ACTIVE, False)
    return values


def _key(values: dict, avoid: str) -> tuple:
    """A QCTEST-prefixed field (not the one under test) to find the entry by."""
    for label in (S_HEADING_AR, S_DESC_AR, S_HEADING, S_DESC):
        if label != avoid and str(values.get(label, "")).startswith("QCTEST-"):
            return label, values[label]
    raise AssertionError("no QCTEST key field")


_P3_SECTION = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.functional_low,
               pytest.mark.pbi_129372, SECTION_GROUP]


def _p3_section(fn):
    for m in _P3_SECTION:
        fn = m(fn)
    return allure.feature("Latest News — Section config")(allure.epic("Home Page")(fn))


def _section_accept_case(page, tc: str, label: str, value: str, via_publish: bool):
    admin = _editor(page)
    values = _new_section(admin, tc, {label: value})
    key = _key(values, label)
    try:
        if via_publish:
            admin.section.submit_for_review()
        else:
            admin.section.save_as_draft()
        outcome = admin.save_outcome(admin.section)
        assert outcome != "refused", f"save refused: {admin.refusal_text(admin.section)}"
        code = admin.find_code_by_field(admin.section, *key)  # the stored record is the proof
        assert code, f"stored entry with {key} not found"
        stored = admin.value(label)
        assert stored == value, f"{label} stored as {stored!r}, expected {value!r}"
        return admin
    finally:
        admin.delete_verified_entry(admin.section, *key)


@_p3_section
@pytest.mark.tc_135280
def test_section_tag_en_accepts_valid_value(page):
    """ADO-135280 (P3). Tag EN 'Latest Updates' stored. Public half -> NEEDS USER."""
    _section_accept_case(page, "135280", S_TAG, "Latest Updates", via_publish=False)


@_p3_section
@pytest.mark.tc_135281
def test_section_tag_en_optional(page):
    """ADO-135281 (P4). Tag EN empty, Publish (Active unticked) -> no
    validation error, stored with an empty tag."""
    _section_accept_case(page, "135281", S_TAG, "", via_publish=True)


@_p3_section
@pytest.mark.bilingual
@pytest.mark.tc_135283
def test_section_tag_ar_accepts_valid_value(page):
    """ADO-135283 (P3). Arabic tag stored and the input renders RTL."""
    admin = _section_accept_case(page, "135283", S_TAG_AR, "آخر المستجدات", via_publish=False)
    direction = admin.box(S_TAG_AR).evaluate("el => getComputedStyle(el).direction")
    assert direction == "rtl", f"Section Tag (AR) input renders {direction!r}"


@_p3_section
@pytest.mark.bilingual
@pytest.mark.tc_135284
def test_section_tag_ar_optional(page):
    """ADO-135284 (P4). Tag AR empty, Publish -> no validation error."""
    _section_accept_case(page, "135284", S_TAG_AR, "", via_publish=True)


def _section_whitespace_case(page, tc: str, label: str):
    admin = _editor(page)
    values = _new_section(admin, tc, {label: "   "})
    key = _key(values, label)
    try:
        _assert_publish_refused(admin, admin.section, f"{label} (whitespace only)")
    finally:
        admin.delete_verified_entry(admin.section, *key)


@_p3_section
@pytest.mark.tc_135288
def test_section_heading_en_rejects_whitespace(page):
    """ADO-135288 (P3). Heading EN spaces only, Publish -> refused as if empty."""
    _section_whitespace_case(page, "135288", S_HEADING)


@_p3_section
@pytest.mark.bilingual
@pytest.mark.tc_135292
def test_section_heading_ar_rejects_whitespace(page):
    """ADO-135292 (P3)."""
    _section_whitespace_case(page, "135292", S_HEADING_AR)


@_p3_section
@pytest.mark.tc_135296
def test_section_description_en_rejects_whitespace(page):
    """ADO-135296 (P3)."""
    _section_whitespace_case(page, "135296", S_DESC)


@_p3_section
@pytest.mark.bilingual
@pytest.mark.tc_135300
def test_section_description_ar_rejects_whitespace(page):
    """ADO-135300 (P3)."""
    _section_whitespace_case(page, "135300", S_DESC_AR)


_P3_NEWS = [pytest.mark.control_panel, pytest.mark.media, pytest.mark.functional_low,
            pytest.mark.pbi_129372, NEWS_GROUP]


def _p3_news(fn):
    for m in _P3_NEWS:
        fn = m(fn)
    return allure.feature("Latest News — News Article fields")(allure.epic("Home Page")(fn))


@_p3_news
@pytest.mark.tc_135304
def test_news_title_en_rejects_whitespace(page):
    """ADO-135304 (P3). Title EN spaces only, everything else valid,
    Active unticked, Publish -> refused as if empty."""
    marker = f"QCTEST-135304-{RUN} ع"
    admin = _editor(page)
    try:
        admin.fill_news_article(title="   ", title_ar=marker, pub_date=TODAY,
                                thumbnail=THUMBNAIL_FIXTURE, active=False)
        _assert_publish_refused(admin, admin.news, "Title (EN) whitespace-only")
    finally:
        admin.delete_verified_entry(admin.news, F_TITLE_AR, marker)


@_p3_news
@pytest.mark.bilingual
@pytest.mark.tc_135308
def test_news_title_ar_rejects_whitespace(page):
    """ADO-135308 (P3). Title AR spaces only -> refused as if empty."""
    title = f"QCTEST-135308-{RUN} Whitespace AR"
    admin = _editor(page)
    try:
        admin.fill_news_article(title=title, title_ar="   ", pub_date=TODAY,
                                thumbnail=THUMBNAIL_FIXTURE, active=False)
        _assert_publish_refused(admin, admin.news, "Title (AR) whitespace-only")
    finally:
        admin.delete_qctest_article(title)


@_p3_news
@pytest.mark.tc_135312
def test_news_oversized_thumbnail_rejected(page, tmp_path):
    """ADO-135312 (P3). thumbnail-large.png at 3.5 MB (above the 3 MB
    tolerance, so acceptance would be a real defect). Pass = the picker
    refuses it, or the field stays empty, or Publish is refused."""
    spec = importlib.util.spec_from_file_location("fixture_factory", "tools/fixture_factory.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    big = tmp_path / "thumbnail-large.png"
    big.write_bytes(mod.make_png(3_670_016))
    title = f"QCTEST-135312-{RUN} Oversized Thumbnail"
    admin = _editor(page)
    try:
        admin.fill_news_article(title=title, title_ar=f"QCTEST-135312-{RUN} ع", pub_date=TODAY, active=False)
        picker_refused = False
        try:
            admin.news.upload_file(F_THUMBNAIL, str(big))
        except Exception:  # noqa: BLE001 — the picker would not take the file
            picker_refused = True
            admin.page.keyboard.press("Escape")
        attached = "" if picker_refused else admin.news.uploaded_filename(F_THUMBNAIL)
        allure.attach(f"picker_refused={picker_refused} attached={attached!r}", "upload",
                      allure.attachment_type.TEXT)
        if attached:
            _assert_publish_refused(admin, admin.news, "a 3.5 MB thumbnail")
    finally:
        admin.delete_qctest_article(title)


@_p3_news
@pytest.mark.tc_135315
def test_news_publication_date_rejects_malformed(page):
    """ADO-135315 (P3). Type 32/13/2026 into Publication Date, Publish ->
    blocked (the widget rejecting the text and Publish then refusing the
    empty required date also counts as blocked)."""
    title = f"QCTEST-135315-{RUN} Malformed Date"
    admin = _editor(page)
    try:
        admin.fill_news_article(title=title, title_ar=f"QCTEST-135315-{RUN} ع",
                                thumbnail=THUMBNAIL_FIXTURE, active=False)
        box = admin.date_box(F_PUB_DATE)
        box.click()
        admin.page.keyboard.type("32/13/2026", delay=20)
        allure.attach(box.input_value(), "date field after typing", allure.attachment_type.TEXT)
        _assert_publish_refused(admin, admin.news, "a malformed Publication Date")
    finally:
        admin.delete_qctest_article(title)



# ===========================================================================
# Section public half (USER ORDER 2026-10-07 22:45: execute every case with
# test data). A NEW QCTEST section record, Published + Active, stands in for
# the live one. The fragment asks for the first activeStatus=true record
# (pageSize=1): if it picks ours naturally, that is the path used; if it keeps
# the live record, the visitor's section response is narrowed to OUR stored,
# published record (visitor context only) and the real fragment renders it.
# The record is deleted in the finally right after the read, so visitors
# never keep seeing it.
# ===========================================================================
def _publish_public_section(admin, tc: str, overrides: dict) -> dict:
    values = _new_section(admin, tc, overrides)
    admin.section.set_checkbox(S_ACTIVE, True)
    admin.section.submit_for_review()
    assert admin.save_outcome(admin.section) != "refused", admin.refusal_text(admin.section)
    return values


def _visitor_section(browser, values: dict, locale: str):
    """(path, tag, heading, description, section dir, visible tag count)."""
    anon_ctx, home = _anon_home(browser)
    try:
        want = values[S_HEADING_AR] if locale == "ar" else values[S_HEADING]
        opener = home.open_home_arabic if locale == "ar" else home.open_home

        def ours():
            opener()
            home.page.locator(home.HEADING).wait_for(timeout=30000)
            return home.heading_text() == want

        path = "natural (fragment picked the QCTEST record)"
        if not ours():
            # second read = a fresh reload (guest API caching), no blind sleep
            if not ours():
                home.pick_section_record(values[S_HEADING_AR])
                ours()
                path = "visitor response narrowed to the stored QCTEST record"
        home.scroll_to_section()
        tag_visible = home.page.locator(home.TAG + ":visible").count()
        tag = home.tag_text() if tag_visible else ""
        return (path, tag, home.heading_text(), home.description_text(),
                home.section_direction(), tag_visible)
    finally:
        anon_ctx.close()


@allure.epic("Home Page")
@allure.feature("Latest News — Section config")
@allure.title("Section tag, heading and description values render on the Home Page (EN + AR)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129372
@pytest.mark.tc_135280
@pytest.mark.tc_135283
@pytest.mark.tc_135286
@pytest.mark.tc_135290
@pytest.mark.tc_135294
@pytest.mark.tc_135298
@SECTION_GROUP
def test_section_values_render_on_home(page, browser):
    """Public halves of ADO-135280 / 135283 / 135286 / 135290 / 135294 /
    135298 on one QCTEST section record (Editor): EN tag above the heading,
    AR tag, heading as the main title, description (EN/AR, RTL on AR).
    Bold (135294) is impossible — plain textarea (finding G2)."""
    admin = _editor(page)
    values = {}
    try:
        values = _publish_public_section(admin, "135286", {S_TAG: "Latest Updates", S_TAG_AR: "آخر المستجدات"})
        en = _visitor_section(browser, values, "en")
        ar = _visitor_section(browser, values, "ar")
        allure.attach(f"EN path: {en[0]} | AR path: {ar[0]}", "how the record was reached",
                      allure.attachment_type.TEXT)
    finally:
        if values:
            admin.delete_verified_entry(admin.section, S_HEADING_AR, values[S_HEADING_AR])
    assert en[1] == "Latest Updates", f"EN tag {en[1]!r} (135280)"
    assert en[2] == values[S_HEADING], f"EN heading {en[2]!r} (135286)"
    assert en[3] == values[S_DESC], f"EN description {en[3]!r} (135294)"
    assert ar[1] == "آخر المستجدات", f"AR tag {ar[1]!r} (135283)"
    assert ar[2] == values[S_HEADING_AR], f"AR heading {ar[2]!r} (135290)"
    assert ar[3] == values[S_DESC_AR], f"AR description {ar[3]!r} (135298)"
    assert ar[4] == "rtl", f"AR section direction {ar[4]!r}"


@allure.epic("Home Page")
@allure.feature("Latest News — Section config")
@allure.title("With no section tag the Home Page section renders without a tag label (EN + AR)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.tc_135281
@pytest.mark.tc_135284
@SECTION_GROUP
def test_section_without_tags_renders_on_home(page, browser):
    """Public halves of ADO-135281 / 135284: tags empty -> no tag label
    above the heading, EN and AR."""
    admin = _editor(page)
    values = {}
    try:
        values = _publish_public_section(admin, "135281", {})
        en = _visitor_section(browser, values, "en")
        ar = _visitor_section(browser, values, "ar")
        allure.attach(f"EN path: {en[0]} | AR path: {ar[0]}", "how the record was reached",
                      allure.attachment_type.TEXT)
    finally:
        if values:
            admin.delete_verified_entry(admin.section, S_HEADING_AR, values[S_HEADING_AR])
    assert en[2] == values[S_HEADING] and ar[2] == values[S_HEADING_AR], "our record did not render"
    assert en[5] == 0 and not en[1].strip(), f"EN shows a tag label {en[1]!r}"
    assert ar[5] == 0 and not ar[1].strip(), f"AR shows a tag label {ar[1]!r}"


# ===========================================================================
# Character-limit cases — bug-rules Rule 5 (USER ORDER: execute them).
# Type US limit + 1 characters (maxlength only binds typed input) and read
# what the field kept. Nothing is saved, so no over-limit record is created.
# ===========================================================================
CHAR_LIMIT_CASES = [
    ("135282", "section", S_TAG, 50),
    ("135285", "section", S_TAG_AR, 50),
    ("135289", "section", S_HEADING, 200),
    ("135293", "section", S_HEADING_AR, 200),
    ("135297", "section", S_DESC, 1000),
    ("135301", "section", S_DESC_AR, 1000),
    ("135305", "news", F_TITLE, 200),
    ("135309", "news", F_TITLE_AR, 200),
]


@allure.epic("Home Page")
@allure.feature("Latest News — character limits")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129372
@pytest.mark.parametrize(
    "tc,obj,label,us_limit",
    [pytest.param(*c, marks=getattr(pytest.mark, f"tc_{c[0]}"), id=f"tc_{c[0]}") for c in CHAR_LIMIT_CASES],
)
def test_char_limit(page, tc, obj, label, us_limit):
    """ADO-135282/285/289/293/297/301/305/309 (Rule 5). Step 2: the field
    takes US limit + 1 characters (the inputs carry no maxlength — measured
    live 2026-10-07: 51/201/1001 kept). Step 3: Save -> the TC expects a
    validation error and nothing saved. So: a valid form with only this
    field over the limit, Active UNticked, Publish -> must be refused. A
    silent cap or different wording would not be a bug; an accepted save
    means the implemented limit is above the US one (Rule 5.2) and the case
    fails with that evidence. Any record that does get saved carries a
    QCTEST- value and is removed by exact value in the finally."""
    admin = _editor(page)
    over = (f"QCTEST-{tc}-" + "x" * (us_limit + 1))[: us_limit + 1]
    marker = f"QCTEST-{tc}-{RUN} key"
    authoring = admin.section if obj == "section" else admin.news
    key_label = None
    try:
        if obj == "section":
            key_label = S_DESC_AR if label != S_DESC_AR else S_HEADING_AR
            _new_section(admin, tc, {key_label: marker})
        else:
            key_label = F_TITLE_AR if label != F_TITLE_AR else F_TITLE
            admin.fill_news_article(
                title=marker if key_label == F_TITLE else f"QCTEST-{tc}-{RUN} title",
                title_ar=marker if key_label == F_TITLE_AR else f"QCTEST-{tc}-{RUN} ع",
                pub_date=TODAY, thumbnail=THUMBNAIL_FIXTURE, active=False)
        box = admin.box(label)
        box.fill("")
        box.click()
        admin.page.keyboard.insert_text(over[: us_limit - 5])
        admin.page.keyboard.type(over[us_limit - 5:], delay=10)
        kept = len(box.input_value())
        counter = admin.page.get_by_text(f"{kept} / {us_limit}", exact=True).count()
        allure.attach(f"typed={us_limit + 1} kept={kept} maxlength={box.get_attribute('maxlength')} "
                      f"counter_shows_over={bool(counter)}", "char limit", allure.attachment_type.TEXT)
        if kept <= us_limit:
            return  # the field itself refuses the excess — nothing over the limit can be saved
        if obj == "section":
            admin.section.set_checkbox(S_ACTIVE, False)
        _assert_publish_refused(admin, authoring, f"{label} at {kept} characters (US limit {us_limit})")
    finally:
        if key_label:
            if obj == "news" and key_label == F_TITLE:
                admin.delete_qctest_article(marker)
            elif obj == "news":
                admin.delete_qctest_article(f"QCTEST-{tc}-{RUN} title")
            else:
                admin.delete_verified_entry(admin.section, key_label, marker)

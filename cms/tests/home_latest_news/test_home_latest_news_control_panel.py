"""
cms/tests/home_latest_news/test_home_latest_news_control_panel.py —
Control_Panel-tagged cases for PBI 129372 (Home Page "Stay Connected &
Informed" / Latest News section).

SOURCE: ADO Test Case 135279's full step text was supplied verbatim by the
task that authored this module (2026-09-02) — quoted in the test's own
docstring below, not re-interpreted from the title alone.

UNBLOCKED 2026-09-03: originally skipped because the raw "News Article"
Object Definition has Workflow Assigned = "No Workflow" (no Save-as-Draft
control, no reachable Draft status — see
cms/pages/home_latest_news/home_latest_news_admin_page.py's WORKFLOW
FINDING for the full original evidence, kept for history). A newly
confirmed Control_Panel surface, `object-authoring` ->
`manage-news-article` (documented in
.claude/context/active/standards.md's "Object Authoring — Draft / Preview
/ Publish / Unpublish Lifecycle" section), manages this same object's
entries through a real Draft/Submit-for-Publishing/Unpublish state
machine, independent of the raw Object Definition's own workflow setting.
TC 135279 is now driven through that surface via
cms/pages/components/object_authoring_page.py (ObjectAuthoringPage),
composed onto HomeLatestNewsAdminPage as
open_new_article_form_via_object_authoring()/etc. The activeStatus
checkbox is still not substituted for anything — the object-authoring
surface's own Status column IS the workflow-status field the case names.

TEST-DATA POLICY (cms-profile.md): DISPOSABLE. The test creates its own
`QCTEST-`-prefixed article (via Title) and deletes it via
ObjectAuthoringPage.delete_entry_by_title() in a `finally` block. Never
touches the 3 real editorial rows (48759/48789/48819).
"""

import datetime

import allure
import pytest

from cms.pages.home_latest_news.home_latest_news_admin_page import HomeLatestNewsAdminPage
from core.utils.logger import get_logger
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from web.pages.home_latest_news.home_latest_news_page import HomeLatestNewsPage

logger = get_logger("test_home_latest_news_control_panel")

THUMBNAIL_FIXTURE = "cms/tests/home_latest_news/fixtures/news_thumbnail.png"


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
def test_save_article_as_draft_not_in_latest_news(page, browser):
    """ADO-135279. Steps (from Azure DevOps, quoted verbatim):
      1. Log in to CMS as Site Content Editor -> CMS loads
      2. Navigate to News module > Create Article -> Create Article form
         displayed
      3. Fill mandatory fields with Title EN = 'Draft Test Article' ->
         Fields populated
      4. Click Save as Draft -> Article saved with status = Draft; article
         does not appear in Home Page Latest News section

    UNBLOCKED 2026-09-03 via the object-authoring surface (see module
    docstring) — driven through manage-news-article instead of the raw
    Object Definition admin. Asserts BOTH halves of the case's own
    expected result: stored status = Draft on the authoring surface, AND
    absence from the public Home Page Latest News section
    (cms-testing.md's dual-surface requirement).

    PUBLIC-PAGE-ANONYMOUS-CONTEXT (mandatory per standards.md, added
    2026-09-07): the public Home Page read goes through a fresh, logged-out
    browser context, never the CMS-authenticated `page` — mirrors
    home_business_events_admin_page's established pattern.
    """
    from core.web.browser import new_context

    admin = HomeLatestNewsAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="news-article")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeLatestNewsPage(anon_context.new_page())
    title = "QCTEST-135279 Draft Test Article"

    try:
        with allure.step("Log in to CMS and open manage-news-article's create-new form"):
            admin.open_news_articles_list()
            authoring.open_new_entry_form()

        with allure.step("Fill mandatory fields with Title EN = 'Draft Test Article'"):
            authoring.fill_text("Title", title)
            authoring.type_date("Publication Date", "09/02/2026")
            authoring.upload_file("Thumbnail Image", THUMBNAIL_FIXTURE)
            assert authoring.uploaded_filename("Thumbnail Image") != "", (
                "Thumbnail Image upload did not populate the field before Save"
            )

        with allure.step("Click Save as Draft"):
            authoring.save_as_draft()

        with allure.step("Assert stored status = Draft on the entries list"):
            assert authoring.row_status_text(title) == "Draft", (
                f"article {title!r} status did not persist as Draft, got "
                f"{authoring.row_status_text(title)!r}"
            )

        with allure.step("Assert the article does NOT appear in the public Home Page Latest News section"):
            absent = home.reload_until_article_matches(title, expected_visible=False)
        assert absent, (
            f"draft article {title!r} unexpectedly visible in the Home Page "
            f"Latest News section within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        # Teardown must land on manage-news-article's own entries list
        # (authoring.open_entries_list(), NOT admin.open_news_articles_list()
        # — the raw admin's list has no `data-qc-oel-delete` rows at all,
        # confirmed live 2026-09-03 after a 30s timeout on the first attempt).
        try:
            authoring.open_entries_list()
            authoring.delete_entry_by_title(title)
        except Exception:
            logger.warning("teardown for %r did not complete — leftover QCTEST data may remain", title)
        anon_context.close()


# ---------------------------------------------------------------------------
# ADO 135273 / 135274 -- added 2026-09-10
#
# OBJECT NAME (per standards.md, taken from cms/Content-Admin-Guide.docx
# section 11 "Home - Latest News (+ News detail page)", never guessed):
# **NewsArticle**, one entry per article -> Object Authoring slug
# `news-article` (`/web/qatar-chamber/manage-news-article`). Guide field
# list: title (bilingual), thumbnailImage, publicationDate (drives
# newest-first), activeStatus, viewCount (auto -- do not edit).
#
# CONFIRMED LIVE 2026-09-10 (headless Chromium against qcdev, fresh
# `.auth/state.json`, scoped CLI probe -- never the Playwright MCP). The
# form renders exactly six fields, matching the guide:
#     Title (required) | Title - العربية | Thumbnail Image (file)
#     Publication Date (required, date) | View Count (auto)
#     Active/Published Status (checkbox)
# Lifecycle buttons present: Save as Draft, Submit for Publishing, and
# (on an Approved entry) Unpublish to edit as draft. 3 real editorial
# entries exist, all APPROVED -- never touched by these tests.
#
# DISCLOSED CASE-VS-BUILD GAPS (both cases):
#   - 135273 step 3 names "category" and "body EN/AR". NEITHER FIELD
#     EXISTS on this object -- not on the live form and not in the guide's
#     field list. The body lives on the News detail page, and there is no
#     category/taxonomy field at all. The tests fill every field the case
#     names THAT EXISTS and this note records the rest, rather than
#     silently dropping them or inventing a substitute.
#   - "Submit for Review" / "Pending Review" does not exist on this build:
#     Submit for Publishing moves Draft -> Approved directly. Same finding
#     already reported for the Promotional Banner cases.
#   - "Published" is status `Approved`; "Unpublished" is status `Draft`.
#   - The success toast is not asserted -- ObjectAuthoringPage has no
#     toast/error reader, so it would be unverifiable rather than merely
#     unwritten. Each step's real outcome (the status transition and the
#     public-page effect) IS asserted.
#
# TEST-DATA POLICY -- DISCLOSED DEVIATION from this module's original
# delete-on-teardown convention, per the QA Manager's standing instruction
# that newly-created entries are LEFT IN PLACE: these two cases never
# delete their article. They sweep a previous run's same-titled leftover
# FIRST (otherwise a re-run produces two identically-titled rows and
# `open_entry_by_edit_link()` fails with a strict-mode violation -- a real
# failure hit on the Promotional Banner batch), then retire the article at
# the end to Draft + inactive so the public Home Page returns to its
# baseline while the QCTEST record survives for inspection.
# ---------------------------------------------------------------------------

NEWS_XDIST_GROUP = pytest.mark.xdist_group("news_article_129372")

# Publication Date drives newest-first ordering (guide section 11). Using
# TODAY guarantees the fixture article sorts above the real editorial rows
# (all older) without inventing a future-dated article, which would be a
# different scenario than the one 135273 describes.
_TODAY_MMDDYYYY = datetime.date.today().strftime("%m/%d/%Y")


def _create_news_article(authoring: ObjectAuthoringPage, title: str, title_ar: str) -> None:
    """Fill every field ADO-135273 step 3 names that actually exists on
    this object -- see the DISCLOSED CASE-VS-BUILD GAPS note above for the
    two it names that do not."""
    authoring.open_new_entry_form()
    authoring.fill_text("Title", title)
    authoring.fill_text("Title — العربية", title_ar)
    authoring.type_date("Publication Date", _TODAY_MMDDYYYY)
    authoring.set_checkbox("Active/Published Status", True)
    authoring.upload_file("Thumbnail Image", THUMBNAIL_FIXTURE)
    assert authoring.uploaded_filename("Thumbnail Image") != "", (
        "Thumbnail Image upload did not populate the field before Save"
    )


def _retire_created_article(authoring: ObjectAuthoringPage, title: str) -> None:
    """Restore-not-delete teardown -- keeps the record, returns the public
    Latest News section to its baseline. Tolerant: no-ops when the row is
    absent, so it is safe to call from a `finally` after an early failure."""
    authoring.open_entries_list()
    if not authoring.row_visible(title):
        return
    authoring.open_entry_by_edit_link(title)
    if authoring.current_status() == "Approved":
        authoring.unpublish_to_edit_as_draft()
    authoring.set_checkbox("Active/Published Status", False)
    authoring.save_as_draft()


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
@pytest.mark.traceability("135273")
@NEWS_XDIST_GROUP
def test_publishing_news_article_surfaces_it_newest_first(page, browser):
    """ADO-135273 (Control_Panel, MEDIA, Regression, UAT; Priority 1).
    Steps, quoted verbatim from the Azure DevOps work item:
      1. Log in to Liferay CMS as Site Content Editor -> CMS loads
      2. Navigate to News module > Create Article -> Create Article form
         displayed
      3. Fill Title EN/AR, category, publication date, thumbnail, body
         EN/AR -> All fields accept entered values
      4. Save as Draft, Submit for Review, then Publish -> Liferay generic
         success toast displayed after publish; article status = Published;
         article appears on Home Page Latest News section, newest first,
         above older articles

    See the module note above for the two step-3 fields that do not exist
    on this object (category, body) and for the missing Submit-for-Review
    state. The "newest first, above older articles" half of the expected
    result IS asserted properly: the fixture article is dated today, so it
    must render as the FIRST card in the section.

    The public read runs in a fresh LOGGED-OUT context (mandatory per
    standards.md).
    """
    from core.web.browser import new_context

    authoring = ObjectAuthoringPage(page, slug="news-article")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeLatestNewsPage(anon_context.new_page())
    title = "QCTEST-135273 Published News Article"
    title_ar = "QCTEST-135273 خبر منشور"

    try:
        with allure.step("Clear any same-titled leftover from a previous run of this case"):
            authoring.delete_all_entries_by_title(title)

        with allure.step("Create Article and fill the fields the case names"):
            _create_news_article(authoring, title, title_ar)
            assert authoring.field_value("Title") == title
            assert authoring.field_value("Title — العربية") == title_ar
            assert authoring.is_checked("Active/Published Status")

        with allure.step("Save as Draft"):
            authoring.save_as_draft()
            status_draft = authoring.row_status_text(title)
        assert status_draft == "Draft", (
            f"article {title!r} did not save as Draft, got {status_draft!r}"
        )

        with allure.step("Submit for Review, then Publish (one transition on this build)"):
            authoring.open_entry_by_edit_link(title)
            authoring.submit_for_publishing()
            status_published = authoring.row_status_text(title)
        assert status_published == "Approved", (
            f"article {title!r} did not reach Approved (this build's "
            f"Published), got {status_published!r}"
        )

        with allure.step("Assert the article appears in the public Home Page Latest News section"):
            appeared = home.reload_until_article_matches(title, expected_visible=True)
        assert appeared, (
            f"published article {title!r} did not appear in the Latest News "
            f"section within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )

        with allure.step("Assert it renders newest-first, above the older articles"):
            home.scroll_to_section()
            first_card_title = home.card_title_text(0)
            card_total = home.card_count()
        assert first_card_title.strip() == title, (
            f"expected today's article to sort newest-first as card 0; the "
            f"first card is {first_card_title.strip()!r} (section has "
            f"{card_total} cards)"
        )
    finally:
        try:
            _retire_created_article(authoring, title)
        except Exception:  # noqa: BLE001 -- teardown must never mask the real failure
            logger.warning(
                "restore for %r did not complete -- a QCTEST article may still be "
                "published on the public Home Page", title
            )
        anon_context.close()


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
@pytest.mark.traceability("135274")
@NEWS_XDIST_GROUP
def test_unpublishing_news_article_removes_it_from_latest_news(page, browser):
    """ADO-135274 (Control_Panel, MEDIA, Regression; Priority 1).
    Steps, quoted verbatim from the Azure DevOps work item:
      1. Log in to Liferay CMS as Site Content Editor -> CMS loads
      2. Navigate to News module -> News module list displayed
      3. Select the published article -> Article selected, status =
         Published
      4. Click Unpublish -> Liferay generic success toast displayed;
         article status = Unpublished; article no longer appears in Home
         Page Latest News section

    PRECONDITION: step 3 says "the published article" without naming one.
    This test creates and publishes its OWN fixture article rather than
    unpublishing one of the three real editorial rows -- taking real news
    off the live Home Page for the duration of a run is exactly what
    standards.md forbids when a disposable fixture proves the same thing.
    The precondition is asserted publicly before the unpublish, so the
    removal is a genuine observed transition, not an assumed one.

    Both public reads run in a fresh LOGGED-OUT context (mandatory per
    standards.md).
    """
    from core.web.browser import new_context

    authoring = ObjectAuthoringPage(page, slug="news-article")
    anon_context = new_context(browser, use_auth_state=False)
    home = HomeLatestNewsPage(anon_context.new_page())
    title = "QCTEST-135274 Unpublish News Article"
    title_ar = "QCTEST-135274 خبر لإلغاء النشر"

    try:
        with allure.step("Clear any same-titled leftover from a previous run of this case"):
            authoring.delete_all_entries_by_title(title)

        with allure.step("Establish the precondition: a published article"):
            _create_news_article(authoring, title, title_ar)
            authoring.save_as_draft()
            authoring.open_entry_by_edit_link(title)
            authoring.submit_for_publishing()
            status_before = authoring.row_status_text(title)
        assert status_before == "Approved", (
            f"precondition failed: fixture article {title!r} is not Published/"
            f"Approved, got {status_before!r}"
        )

        with allure.step("Confirm it IS in the public Latest News section before unpublishing"):
            live_before = home.reload_until_article_matches(title, expected_visible=True)
        assert live_before, (
            f"precondition failed: article {title!r} is not live in the Latest "
            "News section, so its removal cannot be observed"
        )

        with allure.step("Select the published article and click Unpublish"):
            authoring.open_entries_list()
            authoring.open_entry_by_edit_link(title)
            assert authoring.is_save_as_draft_disabled(), (
                "Save as Draft was not disabled on the opened article -- it is "
                "not in the published state step 3 requires"
            )
            authoring.unpublish_to_edit_as_draft()
            status_after = authoring.row_status_text(title)
        assert status_after == "Draft", (
            f"article {title!r} did not leave the published state after "
            f"Unpublish, got {status_after!r} (this build labels the "
            "unpublished state 'Draft', not 'Unpublished')"
        )

        with allure.step("Assert the article no longer appears in the Latest News section"):
            gone = home.reload_until_article_matches(title, expected_visible=False)
        assert gone, (
            f"unpublished article {title!r} still appears in the Latest News "
            f"section within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        try:
            _retire_created_article(authoring, title)
        except Exception:  # noqa: BLE001
            logger.warning(
                "restore for %r did not complete -- a QCTEST article may still be "
                "published on the public Home Page", title
            )
        anon_context.close()

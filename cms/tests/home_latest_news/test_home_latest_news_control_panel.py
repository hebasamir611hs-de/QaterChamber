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
def test_save_article_as_draft_not_in_latest_news(page):
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
    """
    admin = HomeLatestNewsAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="news-article")
    home = HomeLatestNewsPage(page)
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

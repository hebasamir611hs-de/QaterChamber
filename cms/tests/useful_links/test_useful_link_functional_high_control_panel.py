"""
cms/tests/useful_links/test_useful_link_functional_high_control_panel.py —
Functional-High, Control_Panel cases for PBI 130702 (Useful Links): the
end-to-end create/edit/delete -> public-directory checks spanning the
"Useful Link Category" and "Useful Link" objects.

Same conventions as the Functional-Low modules (Publish = "Save"/"Publish";
QCTEST- disposable data only, exact-title teardown; fresh logged-out context
for every visitor check; authored as the Site Content Editor — see the page
module's ROLE note). External destinations are answered by a local stub page inside
the anonymous context so the redirect assertion checks WHERE the card goes,
not whether a third-party site is reachable from the runner.

Not automatable through the UI and therefore not asserted: "refreshes cache"
and "records an audit-log entry" (no editor-facing surface exposes either;
the row History trail is the closest evidence and is noted where used).
"""

import pytest

from cms.pages.useful_links.useful_link_admin_page import (
    FIELD_EXTERNAL_URL,
    OPEN_BEHAVIOR_NEW_TAB,
    UsefulLinkAdminPage,
)
from cms.pages.useful_links.useful_link_category_admin_page import (
    UsefulLinkCategoryAdminPage,
    anonymous_public_view,
    qctest_title,
)

pytestmark = [
    pytest.mark.control_panel,
    pytest.mark.links,
    pytest.mark.functional_high,
    pytest.mark.pbi_130702,
    # Role context: an auth-free page, signed in as the Site Content Editor
    # by the Page Object's ensure_session() (see the category page module's
    # ROLE note) — never the cached TEST_USER storageState.
    pytest.mark.parametrize("page", [{"auth": False}], indirect=True),
]

STUB_HOSTS = r"^https?://(www\.)?(new-)?example\.com(/.*)?$"


@pytest.fixture
def logo(request) -> str:
    return str(request.path.parent / "fixtures" / "useful_link_qctest_moci-logo.png")


@pytest.mark.tc_140695
@pytest.mark.web
@pytest.mark.traceability("140695")
@pytest.mark.regression
@pytest.mark.uat
def test_create_publish_and_see_new_entry_live_end_to_end(page, browser, logo):
    cat_title = qctest_title(140695, "ULCAT", "Test Partners")
    org = qctest_title(140695, "ULINK", "Partner")
    categories = UsefulLinkCategoryAdminPage(page)
    links = UsefulLinkAdminPage(page)
    try:
        # Step 2 — Category "06 — Test Partners". DISCLOSED DEVIATION: the
        # case's display order "6" is refused by the app's 100-grid rule
        # ("Display Order must be 100 or greater ..."); the order is not what
        # this end-to-end case verifies, so the grid equivalent 600 is used.
        categories.open_new_form()
        categories.fill_category(
            number="06", eyebrow_en="Test Partners", eyebrow_ar="شركاء الاختبار",
            title_en=cat_title, title_ar="شركاء الاختبار", display_order="600", active=True,
        )
        assert categories.publish(), (
            f"Category with Display Order 600 was not created: {categories.validation_errors()}"
        )
        categories.open_list()
        assert categories.row_exists(cat_title), "Category not listed in the admin grid"

        # Step 3/4 — Link Item inside it, then Publish.
        links.open_new_form()
        links.upload_logo(logo)
        links.fill_link(
            org_en=org, org_ar="شريك الاختبار", external_url="https://example.com",
            open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", active=True,
            category_title=cat_title,
        )
        assert links.publish(), f"Link Item refused: {links.last_submit}"
        # Toast checked at the end so a missing toast does not hide the
        # visitor-side evidence of steps 3-5 (the test still fails on it).
        toast = links.success_notice()
        links.open_list()
        assert links.row_status(org) == "Published"

        # Step 5 — anonymous visitor sees and can use it.
        with anonymous_public_view(browser, stub_hosts=STUB_HOSTS) as public:
            assert public.wait_for_card(cat_title, org), "New category/link not visible to the visitor"
            popup_url, _ = public.click_card_new_tab(cat_title, org)
            assert popup_url.rstrip("/") == "https://example.com"
        assert toast, "No success toast after Publish"
    finally:
        categories.teardown_category(cat_title)


@pytest.mark.tc_140698
@pytest.mark.web
@pytest.mark.traceability("140698")
@pytest.mark.regression
def test_edit_external_url_updates_live_redirect(page, browser, logo):
    cat_title = qctest_title(140698, "ULCAT")
    org = qctest_title(140698, "ULINK")
    old_url, new_url = "https://example.com", "https://new-example.com"
    categories = UsefulLinkCategoryAdminPage(page)
    links = UsefulLinkAdminPage(page)
    try:
        assert categories.create_category(cat_title, active=True), categories.last_submit
        assert links.create_link(org, cat_title, logo, external_url=old_url), links.last_submit
        links.open_for_edit(org)
        assert links.field(FIELD_EXTERNAL_URL) == old_url, "Edit form does not show the old URL"
        links.fill_link(external_url=new_url)
        assert links.field(FIELD_EXTERNAL_URL) == new_url
        assert links.publish(), f"Republish refused: {links.last_submit}"
        assert links.success_notice(), "No success toast after republishing"

        with anonymous_public_view(browser, stub_hosts=STUB_HOSTS) as public:
            assert public.wait_for_card(cat_title, org)
            popup_url, _ = public.click_card_new_tab(cat_title, org)
            assert popup_url.rstrip("/") == new_url, f"Visitor redirected to {popup_url}, expected {new_url}"
    finally:
        categories.teardown_category(cat_title)


@pytest.mark.tc_140699
@pytest.mark.web
@pytest.mark.traceability("140699")
def test_delete_link_item_removes_it_from_live_directory(page, browser, logo):
    cat_title = qctest_title(140699, "ULCAT")
    org = qctest_title(140699, "ULINK")
    categories = UsefulLinkCategoryAdminPage(page)
    links = UsefulLinkAdminPage(page)
    try:
        assert categories.create_category(cat_title, active=True), categories.last_submit
        assert links.create_link(org, cat_title, logo), links.last_submit
        with anonymous_public_view(browser) as public:
            assert public.wait_for_card(cat_title, org), "Precondition: card not visible"

        # Steps 1-3 — locate, confirm disposable (QCTEST-), delete.
        links.open_list()
        assert links.row_exists(org) and org.startswith("QCTEST-")
        assert links.delete_disposable(org), "Link Item still in the admin grid after Delete"
        assert links.in_recycle_bin(org), "Deleted Link Item is not recorded in the Recycle Bin"

        # Step 4 — gone for the visitor, category still there.
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(cat_title)
            assert not public.wait_for_card(cat_title, org, present=False), "Deleted card still rendered"
    finally:
        categories.teardown_category(cat_title, recycled_link_titles=[org])

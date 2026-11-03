"""
cms/tests/useful_links/test_useful_link_edge_control_panel.py — Edge,
Control_Panel cases for PBI 130702 (Useful Links) on the "Useful Link"
object. Disposable QCTEST data only; visitor view through a fresh logged-out
context; authored as the Site Content Editor (see the category page
module's ROLE note).
"""

import pytest

from cms.pages.useful_links.useful_link_admin_page import UsefulLinkAdminPage
from cms.pages.useful_links.useful_link_category_admin_page import (
    UsefulLinkCategoryAdminPage,
    anonymous_public_view,
    qctest_title,
)

pytestmark = [
    pytest.mark.control_panel,
    pytest.mark.links,
    pytest.mark.edge,
    pytest.mark.pbi_130702,
    # Role context: an auth-free page, signed in as the Site Content Editor
    # by the Page Object's ensure_session() (see the category page module's
    # ROLE note) — never the cached TEST_USER storageState.
    pytest.mark.parametrize("page", [{"auth": False}], indirect=True),
]


@pytest.mark.tc_140784
@pytest.mark.web
@pytest.mark.traceability("140784")
def test_link_item_disabled_in_cms_absent_from_public_site(page, browser, request):
    cat_title = qctest_title(140784, "ULCAT")
    keep = qctest_title(140784, "ULINK", "A")
    target = qctest_title(140784, "ULINK", "B")
    logo = str(request.path.parent / "fixtures" / "useful_link_qctest_moci-logo.png")
    categories = UsefulLinkCategoryAdminPage(page)
    links = UsefulLinkAdminPage(page)
    try:
        assert categories.create_category(cat_title, active=True), categories.last_submit
        assert links.create_link(keep, cat_title, logo, display_order="100", external_url="https://example.com"), links.last_submit
        assert links.create_link(target, cat_title, logo, display_order="200"), links.last_submit
        with anonymous_public_view(browser) as public:
            assert public.wait_for_card(cat_title, target), "Precondition: active link not visible"

        links.open_for_edit(target)
        links.set_active_status(False)
        assert links.publish(), f"Save refused: {links.last_submit}"
        links.open_for_edit(target)
        assert not links.is_active_status_checked(), "Link Item status did not become Inactive"

        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(cat_title), "Parent category (still Active) disappeared"
            assert not public.wait_for_card(cat_title, target, present=False), "Inactive card still rendered"
            remaining = public.card(cat_title, keep)
            assert remaining is not None, "The category's other active item no longer renders"
            assert remaining["href"].rstrip("/") == "https://example.com" and remaining["org"].strip() == keep
    finally:
        categories.teardown_category(cat_title)

"""
cms/tests/useful_links/test_useful_link_category_edge_control_panel.py —
Edge, Control_Panel cases for PBI 130702 (Useful Links) on the "Useful Link
Category" object. Disposable QCTEST data only; visitor view through a fresh
logged-out context; authored as the Site Content Editor (see the page module's
ROLE note).
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


def _seeded_numbering(public) -> list[tuple[str, str]]:
    """(number, title) of every non-QCTEST category, in render order."""
    return [
        (n, t) for n, t in zip(public.category_numbers(), public.category_titles())
        if not t.startswith("QCTEST-")
    ]


@pytest.mark.tc_140783
@pytest.mark.web
@pytest.mark.traceability("140783")
def test_category_disabled_in_cms_absent_from_public_site(page, browser, request):
    title = qctest_title(140783, "ULCAT")
    org = qctest_title(140783, "ULINK")
    logo = str(request.path.parent / "fixtures" / "useful_link_qctest_moci-logo.png")
    categories = UsefulLinkCategoryAdminPage(page)
    links = UsefulLinkAdminPage(page)
    try:
        with anonymous_public_view(browser) as public:
            public.open_page()
            baseline = _seeded_numbering(public)
        assert categories.create_category(title, active=True), categories.last_submit
        assert links.create_link(org, title, logo), links.last_submit
        with anonymous_public_view(browser) as public:
            assert public.wait_for_card(title, org), "Precondition: active, published category not visible"

        categories.open_for_edit(title)
        categories.set_active_status(False)
        assert categories.publish(), f"Save refused: {categories.last_submit}"
        categories.open_for_edit(title)
        assert not categories.is_active_status_checked(), "Category status did not become Inactive"

        with anonymous_public_view(browser) as public:
            assert not public.wait_for_category(title, present=False), "Inactive category still rendered"
            assert org not in public.all_card_orgs(), "A link item of the inactive category is rendered"
            assert _seeded_numbering(public) == baseline, (
                "Accordion numbering changed after hiding the category (gap / renumbering)"
            )
    finally:
        categories.teardown_category(title)

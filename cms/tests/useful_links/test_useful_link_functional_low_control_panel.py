"""
cms/tests/useful_links/test_useful_link_functional_low_control_panel.py —
Functional-Low, Control_Panel cases for PBI 130702 (Useful Links) on the
"Useful Link" object (`manage-useful-link`): Logo, Organization Name,
Website Label, External URL, Open Behavior and Display Order validation,
plus add / edit / reorder / enable / disable / delete.

Conventions (evidence in the page modules' docstrings):
  - "Click Save" = the form's Publish button (the commit that validates).
  - Every negative case fills every OTHER field validly — logo uploaded,
    parent category chosen — so the refusal can only come from the field
    under test.
  - Each test creates its own QCTEST parent category (unless the case names
    real category 01) and tears it down in `finally`; deleting the category
    takes its Link Items with it.
  - Where a case names a real organization ("Ministry of Commerce and
    Industry") the QCTEST- prefix is added (safety rule: a disposable record
    must never share an exact title with real content).
  - Display Order: 100/200 unless the case dictates a value; case-dictated
    non-grid values ("2", "1") are used verbatim and the platform's 100-grid
    refusal is reported, not worked around.
  - Visitor checks use a fresh logged-out context; external destinations are
    answered by a local stub page inside that context.
  - Account: the Site Content Editor (see the category page module's ROLE
    note). The QCTEST parent category is created by that same Editor, so
    while Bug 1 stands (the Editor's Category form cannot store a Display
    Order) the `parent` setup fails with that server message — the parent
    is never created through the admin account.
  - 140772 / 140774 add QCTEST cards to REAL category 01. The Recycle Bin
    has no permanent delete (Restore only), so their teardown leaves each
    card in the Link Recycle Bin as known debris (titles logged as
    "KNOWN DEBRIS").
"""

import pytest

from core.utils.logger import get_logger
from cms.pages.useful_links.useful_link_admin_page import (
    FIELD_EXTERNAL_URL,
    FIELD_OPEN_BEHAVIOR,
    FIELD_ORG_NAME_AR,
    FIELD_ORG_NAME_EN,
    FIELD_WEBSITE_LABEL_AR,
    FIELD_WEBSITE_LABEL_EN,
    MSG_LABEL_MAX,
    MSG_ORG_MAX,
    MSG_ORG_SPACES,
    MSG_PICKER_BAD_EXTENSION,
    MSG_URL_INVALID,
    MSG_URL_SPACES,
    OPEN_BEHAVIOR_NEW_TAB,
    OPEN_BEHAVIOR_SAME_TAB,
    UsefulLinkAdminPage,
)
from cms.pages.useful_links.useful_link_category_admin_page import (
    FIELD_DISPLAY_ORDER,
    MSG_DISPLAY_ORDER_GRID,
    UsefulLinkCategoryAdminPage,
    anonymous_public_view,
    qctest_title,
)

pytestmark = [
    pytest.mark.control_panel,
    pytest.mark.links,
    pytest.mark.functional_low,
    pytest.mark.pbi_130702,
    # Role context: an auth-free page, signed in as the Site Content Editor
    # by the Page Object's ensure_session() (see the category page module's
    # ROLE note) — never the cached TEST_USER storageState.
    pytest.mark.parametrize("page", [{"auth": False}], indirect=True),
]

logger = get_logger(__name__)
REAL_CATEGORY_01 = "State of Qatar — Ministries"  # read-only use: parent picker only
STUB_HOSTS = r"^https?://(www\.)?(example\.com|moci\.gov\.qa)(/.*)?$"
ORG_AR = "منظمة اختبار"


@pytest.fixture
def fixtures_dir(request):
    return request.path.parent / "fixtures"


@pytest.fixture
def logo(fixtures_dir) -> str:
    return str(fixtures_dir / "useful_link_qctest_moci-logo.png")


@pytest.fixture
def parent(page, request):
    """A disposable, ACTIVE, published QCTEST parent category for one test,
    torn down afterwards together with every Link Item under it. Tests that
    recycle a link themselves register its title on `parent.recycled`."""
    categories = UsefulLinkCategoryAdminPage(page)
    tc = next((m.name[3:] for m in request.node.iter_markers() if m.name.startswith("tc_")), "0")
    title = qctest_title(tc, "ULCAT")
    if not categories.create_category(title, active=True):
        outcome = dict(categories.last_submit)
        categories.teardown_category(title)  # a wrongly-reported refusal may still have written it
        pytest.fail(f"Setup: parent category refused: {outcome}")

    class _Parent:
        pass

    info = _Parent()
    info.title = title
    info.recycled = []
    yield info
    categories.teardown_category(title, recycled_link_titles=info.recycled)


def _form_with_logo(page, logo_path: str) -> UsefulLinkAdminPage:
    links = UsefulLinkAdminPage(page)
    links.open_new_form()
    links.upload_logo(logo_path)
    return links


def _log_known_debris(links: UsefulLinkAdminPage, *titles: str) -> None:
    """A QCTEST card recycled out of REAL category 01 cannot be purged (the
    Recycle Bin offers Restore only) — record each by exact title."""
    for title in titles:
        try:
            if links.in_recycle_bin(title):
                logger.warning("KNOWN DEBRIS (Link Recycle Bin, category 01): %s", title)
        except Exception as exc:  # noqa: BLE001 — reporting only
            logger.warning("could not check the Recycle Bin for %s: %s", title, exc)


def _assert_blocked(links: UsefulLinkAdminPage, saved: bool, title: str | None) -> None:
    assert not saved, f"Publish committed although the case expects a refusal; alerts={links.validation_errors()}"
    if title:
        assert not links.row_exists_fresh(title), f"A Link Item titled {title!r} was created despite the refusal"


# ---- Logo ------------------------------------------------------------------

@pytest.mark.tc_140744
@pytest.mark.traceability("140744")
def test_valid_png_logo_under_2mb_uploads(page, browser, parent, fixtures_dir):
    org = qctest_title(140744, "ULINK")
    png = fixtures_dir / "useful_link_qctest_moci-logo.png"
    assert png.stat().st_size < 2 * 1024 * 1024
    links = UsefulLinkAdminPage(page)
    links.open_new_form()
    result = links.attempt_logo_upload(str(png))
    assert result["accepted"], f"Valid PNG refused by the picker: {result['message']}"
    assert links.logo_filename().startswith("useful_link_qctest_moci-logo"), "No preview/filename after upload"
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", active=True,
                    category_title=parent.title)
    assert links.publish(), f"Save refused: {links.last_submit}"
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, org)
        card = public.card(parent.title, org)
        assert "useful_link_qctest_moci-logo" in card["logo"], f"Logo not rendered on the card: {card}"


@pytest.mark.tc_140745
@pytest.mark.traceability("140745")
def test_unsupported_logo_format_rejected(page, fixtures_dir):
    links = UsefulLinkAdminPage(page)
    links.open_new_form()
    result = links.attempt_logo_upload(str(fixtures_dir / "useful_link_qctest_moci-logo.bmp"))
    assert not result["accepted"], "A .bmp logo was accepted"
    assert MSG_PICKER_BAD_EXTENSION in result["message"], f"No format-not-supported message: {result}"
    assert links.logo_filename() == "", "The rejected .bmp ended up attached to the form"


@pytest.mark.tc_140746
@pytest.mark.traceability("140746")
def test_logo_over_2mb_rejected(page, parent, fixtures_dir):
    org = qctest_title(140746, "ULINK")
    big = fixtures_dir / "useful_link_qctest_logo_oversized_2_3mb.png"
    assert big.stat().st_size > 2 * 1024 * 1024
    links = UsefulLinkAdminPage(page)
    links.open_new_form()
    result = links.attempt_logo_upload(str(big))
    if not result["accepted"]:
        assert "size" in result["message"].lower() or "2 MB" in result["message"], (
            f"Oversized logo refused, but not with a file-size message: {result['message']!r}"
        )
        return
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", active=False,
                    category_title=parent.title)
    saved = links.publish()
    errors = links.validation_errors()
    _assert_blocked(links, saved, org)
    assert any("MB" in e or "size" in e.lower() for e in errors), (
        f"No file-size-exceeded message for a 2.3 MB logo; alerts={errors}"
    )


# ---- Organization Name -------------------------------------------------------

@pytest.mark.tc_140747
@pytest.mark.traceability("140747")
def test_valid_organization_name_en_ar_saves_and_renders(page, browser, parent, logo):
    org = qctest_title(140747, "ULINK", "Ministry of Commerce and Industry")
    org_ar = "وزارة التجارة والصناعة"
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=org_ar, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", active=True,
                    category_title=parent.title)
    assert links.field(FIELD_ORG_NAME_EN) == org and links.field(FIELD_ORG_NAME_AR) == org_ar
    assert links.publish(), f"Save refused: {links.last_submit}"
    arabic_notice = links.last_submit.get("arabic_notice")
    links.open_for_edit(org)
    assert links.field(FIELD_ORG_NAME_EN) == org
    assert links.field(FIELD_ORG_NAME_AR) == org_ar, f"AR value not persisted; post-save notice: {arabic_notice!r}"
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, org), "Organization name not rendered on the card"
        public.open_page(locale="ar")
        assert org_ar in public.all_card_orgs(), "AR organization name not rendered"


@pytest.mark.tc_140748
@pytest.mark.traceability("140748")
def test_empty_organization_name_blocks_save(page, parent, logo):
    links = _form_with_logo(page, logo)
    links.fill_link(org_en="", org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", category_title=parent.title)
    assert links.field(FIELD_ORG_NAME_EN) == ""
    saved = links.publish()
    native = links.native_validation_message(FIELD_ORG_NAME_EN)
    assert not saved, f"Publish committed with an empty Organization Name; alerts={links.validation_errors()}"
    assert native or links.required_fields_message_shown(), "No required-field message for Organization Name"


@pytest.mark.tc_140749
@pytest.mark.traceability("140749")
def test_organization_name_over_150_chars_rejected(page, parent, logo):
    prefix = qctest_title(140749, "ULINK") + "-"
    org = prefix + "O" * (151 - len(prefix))
    assert len(org) == 151
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", category_title=parent.title)
    held = len(links.field(FIELD_ORG_NAME_EN))
    saved = links.publish()
    errors = links.validation_errors()
    if held <= 150:
        return  # truncated on input — an accepted outcome of the case
    _assert_blocked(links, saved, org)
    assert any(MSG_ORG_MAX in e for e in errors), f"No max-length message; alerts={errors}"


@pytest.mark.tc_140750
@pytest.mark.traceability("140750")
def test_whitespace_only_organization_name_rejected_as_empty(page, parent, logo):
    links = _form_with_logo(page, logo)
    links.fill_link(org_en="    ", org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", category_title=parent.title)
    assert links.field(FIELD_ORG_NAME_EN) == "    "
    saved = links.publish()
    errors = links.validation_errors()
    assert not saved, f"Publish committed with a whitespace-only Organization Name; alerts={errors}"
    assert links.required_fields_message_shown() or any(MSG_ORG_SPACES in e for e in errors), (
        f"Whitespace-only Organization Name not rejected as empty; alerts={errors}"
    )


# ---- Website Label ----------------------------------------------------------

@pytest.mark.tc_140751
@pytest.mark.traceability("140751")
def test_valid_website_label_en_ar_saves_and_renders(page, browser, parent, logo):
    org = qctest_title(140751, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, website_label_en="moci.gov.qa", website_label_ar="moci.gov.qa",
                    external_url="https://example.com", open_behavior=OPEN_BEHAVIOR_NEW_TAB,
                    display_order="100", active=True, category_title=parent.title)
    assert links.field(FIELD_WEBSITE_LABEL_EN) == "moci.gov.qa"
    assert links.field(FIELD_WEBSITE_LABEL_AR) == "moci.gov.qa"
    assert links.publish(), f"Save refused: {links.last_submit}"
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, org)
        assert public.card(parent.title, org)["site"].strip() == "moci.gov.qa"


@pytest.mark.tc_140752
@pytest.mark.traceability("140752")
def test_website_label_over_150_chars_rejected(page, parent, logo):
    org = qctest_title(140752, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, website_label_en="L" * 151, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", category_title=parent.title)
    held = len(links.field(FIELD_WEBSITE_LABEL_EN))
    saved = links.publish()
    errors = links.validation_errors()
    if held <= 150:
        return  # truncated on input — an accepted outcome of the case
    _assert_blocked(links, saved, org)
    assert any(MSG_LABEL_MAX in e for e in errors), f"No max-length message; alerts={errors}"


@pytest.mark.tc_140753
@pytest.mark.traceability("140753")
def test_empty_website_label_is_accepted(page, browser, parent, logo):
    org = qctest_title(140753, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", active=True,
                    category_title=parent.title)
    assert links.field(FIELD_WEBSITE_LABEL_EN) == "" and links.field(FIELD_WEBSITE_LABEL_AR) == ""
    assert links.publish(), f"Optional Website Label was treated as required: {links.validation_errors()}"
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, org)
        assert public.card(parent.title, org)["site"].strip() == "", "Card shows a website label although none was set"


# ---- External URL -------------------------------------------------------------

@pytest.mark.tc_140754
@pytest.mark.traceability("140754")
def test_valid_external_url_saves_and_is_used_for_redirect(page, browser, parent, logo):
    org = qctest_title(140754, "ULINK")
    url = "https://www.moci.gov.qa"
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url=url, open_behavior=OPEN_BEHAVIOR_NEW_TAB,
                    display_order="100", active=True, category_title=parent.title)
    assert links.field(FIELD_EXTERNAL_URL) == url
    assert links.publish(), f"Save refused: {links.last_submit}"
    links.open_for_edit(org)
    assert links.field(FIELD_EXTERNAL_URL) == url, "Stored URL differs from the entered one"
    with anonymous_public_view(browser, stub_hosts=STUB_HOSTS) as public:
        assert public.wait_for_card(parent.title, org)
        assert public.card(parent.title, org)["href"].rstrip("/") == url
        popup_url, _ = public.click_card_new_tab(parent.title, org)
        assert popup_url.rstrip("/") == url


@pytest.mark.tc_140755
@pytest.mark.traceability("140755")
@pytest.mark.regression
def test_invalid_external_url_rejected_with_exact_message(page, parent, logo):
    """EN context only: the AR wording ("يرجى إدخال رابط صالح.") needs the
    admin UI in Arabic, which this project's English-only CMS locator policy
    does not drive."""
    org = qctest_title(140755, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="not-a-url", open_behavior=OPEN_BEHAVIOR_NEW_TAB,
                    display_order="100", category_title=parent.title)
    assert links.field(FIELD_EXTERNAL_URL) == "not-a-url"
    saved = links.publish()
    errors = links.validation_errors()
    _assert_blocked(links, saved, org)
    assert any("Please enter a valid URL." == e.strip() or "Please enter a valid URL." in e for e in errors), (
        f'Expected exact message "Please enter a valid URL."; actual alerts={errors}'
    )


@pytest.mark.tc_140756
@pytest.mark.traceability("140756")
def test_whitespace_only_external_url_rejected_as_empty(page, parent, logo):
    org = qctest_title(140756, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="   ", open_behavior=OPEN_BEHAVIOR_NEW_TAB,
                    display_order="100", category_title=parent.title)
    assert links.field(FIELD_EXTERNAL_URL) == "   "
    saved = links.publish()
    errors = links.validation_errors()
    _assert_blocked(links, saved, org)
    assert links.required_fields_message_shown() or any(
        MSG_URL_SPACES in e or MSG_URL_INVALID in e for e in errors
    ), f"Whitespace-only External URL not rejected as empty/invalid; alerts={errors}"


# ---- Open Behavior ------------------------------------------------------------

@pytest.mark.tc_140757
@pytest.mark.web
@pytest.mark.traceability("140757")
def test_same_tab_open_behavior_opens_in_same_tab(page, browser, parent, logo):
    org = qctest_title(140757, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_SAME_TAB, display_order="100", active=True,
                    category_title=parent.title)
    assert links.publish(), f"Save refused: {links.last_submit}"
    links.open_for_edit(org)
    assert links.select_list_value(FIELD_OPEN_BEHAVIOR) == OPEN_BEHAVIOR_SAME_TAB
    with anonymous_public_view(browser, stub_hosts=STUB_HOSTS) as public:
        assert public.wait_for_card(parent.title, org)
        url_after, tabs = public.click_card_same_tab(parent.title, org)
        assert url_after.rstrip("/") == "https://example.com", f"Same tab did not navigate to the site: {url_after}"
        assert tabs == 1, f"A new tab opened for a Same Tab link ({tabs} tabs)"


@pytest.mark.tc_140758
@pytest.mark.web
@pytest.mark.traceability("140758")
def test_new_tab_open_behavior_opens_in_new_tab(page, browser, parent, logo):
    org = qctest_title(140758, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="100", active=True,
                    category_title=parent.title)
    assert links.publish(), f"Save refused: {links.last_submit}"
    links.open_for_edit(org)
    assert links.select_list_value(FIELD_OPEN_BEHAVIOR) == OPEN_BEHAVIOR_NEW_TAB
    with anonymous_public_view(browser, stub_hosts=STUB_HOSTS) as public:
        assert public.wait_for_card(parent.title, org)
        popup_url, original = public.click_card_new_tab(parent.title, org)
        assert popup_url.rstrip("/") == "https://example.com"
        assert "/useful-links" in original, f"Original tab left the Useful Links page: {original}"


# ---- Display Order --------------------------------------------------------------

@pytest.mark.tc_140759
@pytest.mark.traceability("140759")
def test_valid_link_display_order_saves(page, browser, parent, logo):
    """Case value "2" used verbatim; a first card (order 100) is created so
    "2nd card within its category" is observable."""
    first = qctest_title(140759, "ULINK", "A")
    second = qctest_title(140759, "ULINK", "B")
    links = UsefulLinkAdminPage(page)
    assert links.create_link(first, parent.title, logo, display_order="100"), links.last_submit
    links.open_new_form()
    links.upload_logo(logo)
    links.fill_link(org_en=second, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="2", active=True,
                    category_title=parent.title)
    assert links.display_order_value() == "2"
    assert links.publish(), f"Display Order 2 was refused: {links.last_submit}"
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, second)
        assert public.card_orgs(parent.title).index(second) == 1, "Item is not the 2nd card"


@pytest.mark.tc_140760
@pytest.mark.traceability("140760")
def test_non_numeric_or_negative_link_display_order_rejected(page, parent, logo):
    org = qctest_title(140760, "ULINK")
    for value in ("-2", "two"):
        links = _form_with_logo(page, logo)
        links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                        open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order=value, category_title=parent.title)
        saved = links.publish()
        errors = links.validation_errors()
        native = links.native_validation_message(FIELD_DISPLAY_ORDER, role="spinbutton")
        assert not saved, f"Display Order {value!r} was accepted"
        assert any(MSG_DISPLAY_ORDER_GRID in e for e in errors) or native, (
            f"No Display Order validation message for {value!r}; alerts={errors}"
        )
    assert not links.row_exists_fresh(org)


@pytest.mark.tc_140761
@pytest.mark.traceability("140761")
def test_link_display_order_zero_rejected(page, parent, logo):
    org = qctest_title(140761, "ULINK")
    links = _form_with_logo(page, logo)
    links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                    open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="0", category_title=parent.title)
    assert links.display_order_value() == "0"
    saved = links.publish()
    errors = links.validation_errors()
    _assert_blocked(links, saved, org)
    assert any(MSG_DISPLAY_ORDER_GRID in e for e in errors), (
        f"No positive-order validation message for Display Order 0; alerts={errors}"
    )


# ---- Add / edit / reorder / enable / disable / delete ----------------------------

@pytest.mark.tc_140772
@pytest.mark.web
@pytest.mark.traceability("140772")
def test_add_link_item_in_category_01_appears_live(page, browser, logo):
    """The case targets real category 01; a disposable QCTEST Link Item is
    added to it (the category itself is never edited) and deleted by exact
    title afterwards."""
    org = qctest_title(140772, "ULINK")
    links = UsefulLinkAdminPage(page)
    try:
        links.open_new_form()
        links.upload_logo(logo)
        links.fill_link(org_en=org, org_ar=ORG_AR, external_url="https://example.com",
                        open_behavior=OPEN_BEHAVIOR_NEW_TAB, display_order="900", active=True,
                        category_title=REAL_CATEGORY_01)
        assert links.publish(), f"Save refused: {links.last_submit}"
        with anonymous_public_view(browser) as public:
            assert public.wait_for_card(REAL_CATEGORY_01, org), "New card not inside category 01 on the public page"
    finally:
        links.safe_cleanup(org)
        _log_known_debris(links, org)


@pytest.mark.tc_140773
@pytest.mark.traceability("140773")
def test_edit_link_item_organization_name(page, parent, logo):
    org = qctest_title(140773, "ULINK")
    new_org = org + "-EDITED"
    new_org_ar = "منظمة معدلة"
    links = UsefulLinkAdminPage(page)
    assert links.create_link(org, parent.title, logo), links.last_submit
    links.open_for_edit(org)
    assert links.field(FIELD_ORG_NAME_EN) == org
    links.fill_link(org_en=new_org, org_ar=new_org_ar)
    assert links.publish(), f"Edit refused: {links.last_submit}"
    assert links.success_notice(), "No success toast after saving the edit"
    links.open_for_edit(new_org)
    assert links.field(FIELD_ORG_NAME_EN) == new_org
    assert links.field(FIELD_ORG_NAME_AR) == new_org_ar


@pytest.mark.tc_140774
@pytest.mark.web
@pytest.mark.traceability("140774")
def test_reorder_link_items_within_category_01(page, browser, logo):
    """Two disposable QCTEST cards in category 01 (never a real card):
    A=900, B=1000, then B is moved ahead of A. DISCLOSED DEVIATION: the
    case's literal Display Order "1" is refused by the app's 100-grid rule
    (minimum 100), so B is moved to the accepted value 800; what is verified
    is the reorder itself. "First among category 01's cards" is not
    reachable without editing real cards, which the test-data rule forbids."""
    org = qctest_title(140774, "ULINK", "B")
    other = qctest_title(140774, "ULINK", "A")
    links = UsefulLinkAdminPage(page)
    try:
        assert links.create_link(other, REAL_CATEGORY_01, logo, display_order="900"), links.last_submit
        assert links.create_link(org, REAL_CATEGORY_01, logo, display_order="1000"), links.last_submit
        with anonymous_public_view(browser) as public:
            orgs = public.wait_for_order(other, org, category_title=REAL_CATEGORY_01)
            assert other in orgs and org in orgs and orgs.index(other) < orgs.index(org), (
                f"Precondition: A not before B: {orgs}"
            )
        links.open_for_edit(org)
        links.set_display_order("800")
        assert links.display_order_value() == "800"
        assert links.publish(), f"Display Order 800 was refused: {links.last_submit}"
        with anonymous_public_view(browser) as public:
            orgs = public.wait_for_order(org, other, category_title=REAL_CATEGORY_01)
            assert org in orgs and other in orgs and orgs.index(org) < orgs.index(other), (
                f"Re-ordered card does not render ahead of the other: {orgs}"
            )
    finally:
        links.safe_cleanup(org)
        links.safe_cleanup(other)
        _log_known_debris(links, org, other)


@pytest.mark.tc_140775
@pytest.mark.web
@pytest.mark.traceability("140775")
def test_disabling_link_item_hides_it_from_public_page(page, browser, parent, logo):
    keep = qctest_title(140775, "ULINK", "A")
    target = qctest_title(140775, "ULINK", "B")
    links = UsefulLinkAdminPage(page)
    assert links.create_link(keep, parent.title, logo, display_order="100"), links.last_submit
    assert links.create_link(target, parent.title, logo, display_order="200"), links.last_submit
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, target), "Precondition: card not visible"
    links.open_for_edit(target)
    links.set_active_status(False)
    assert not links.is_active_status_checked()
    assert links.publish(), f"Save refused: {links.last_submit}"
    with anonymous_public_view(browser) as public:
        assert not public.wait_for_card(parent.title, target, present=False), "Inactive card still rendered"
        assert keep in public.card_orgs(parent.title), "Other active card disappeared too"


@pytest.mark.tc_140776
@pytest.mark.web
@pytest.mark.traceability("140776")
def test_re_enabling_link_item_shows_it_again(page, browser, parent, logo):
    keep = qctest_title(140776, "ULINK", "A")
    target = qctest_title(140776, "ULINK", "B")
    links = UsefulLinkAdminPage(page)
    assert links.create_link(keep, parent.title, logo, display_order="100"), links.last_submit
    assert links.create_link(target, parent.title, logo, display_order="200", active=False), links.last_submit
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, keep)
        assert target not in public.card_orgs(parent.title), "Precondition: inactive card visible"
    links.open_for_edit(target)
    links.set_active_status(True)
    assert links.is_active_status_checked()
    assert links.publish(), f"Save refused: {links.last_submit}"
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, target), "Re-enabled card did not reappear"
        assert public.card_orgs(parent.title) == [keep, target], "Card not at its configured display order"


@pytest.mark.tc_140777
@pytest.mark.web
@pytest.mark.traceability("140777")
def test_delete_disposable_link_item(page, browser, parent, logo):
    keep = qctest_title(140777, "ULINK", "A")
    target = qctest_title(140777, "ULINK", "B")
    links = UsefulLinkAdminPage(page)
    assert links.create_link(keep, parent.title, logo, display_order="100"), links.last_submit
    assert links.create_link(target, parent.title, logo, display_order="200"), links.last_submit
    with anonymous_public_view(browser) as public:
        assert public.wait_for_card(parent.title, target), "Precondition: card not visible"
    assert target.startswith("QCTEST-")  # step 1: disposable
    parent.recycled.append(target)
    assert links.delete_disposable(target), "Link Item still in the admin grid after Delete"
    with anonymous_public_view(browser) as public:
        assert not public.wait_for_card(parent.title, target, present=False), "Deleted card still rendered"
        assert keep in public.card_orgs(parent.title)

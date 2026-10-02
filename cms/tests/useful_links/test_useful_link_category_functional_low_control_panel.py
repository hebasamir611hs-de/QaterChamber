"""
cms/tests/useful_links/test_useful_link_category_functional_low_control_panel.py
— Functional-Low, Control_Panel cases for PBI 130702 (Useful Links) on the
"Useful Link Category" object (`manage-useful-link-category`).

Conventions (see the page module's docstring for the live evidence):
  - "Click Save" in these cases is the form's Publish button — the only
    commit action that runs validation and puts the record on the site
    (the form says "As an Editor, what you publish here goes live straight
    away"). Save as Draft skips required-field validation by design.
  - Every record a test creates is a disposable QCTEST-<tc>-ULCAT-<stamp>
    row, deleted in `finally` by exact-title match only. Where a case names
    a real title (e.g. "State of Qatar — Ministries") the QCTEST- prefix is
    added so the record can never be confused with — or deleted instead
    of — the real one.
  - Display Order: where a case does not dictate a value, 900 is used (a
    valid 100-grid value that sorts after the seeded 100..500 categories).
    Where a case dictates a non-grid value ("3", "1") it is used verbatim;
    the platform's own 100-grid rule refuses it, and the test reports that
    honestly rather than substituting a grid value.
  - Category Number: "09" unless the case dictates one (the platform only
    accepts two-character values 01..09; duplicates are allowed).
  - Visitor-side checks always use a fresh logged-out context.
  - Account: the Site Content Editor (the role the cases name; see the
    page module's ROLE note). Bug 1 — the Editor's Category form binds
    Display Order to the Link relationship — keeps valid-Publish cases red.
"""

import pytest

from cms.pages.useful_links.useful_link_category_admin_page import (
    FIELD_CATEGORY_EYEBROW_AR,
    FIELD_CATEGORY_EYEBROW_EN,
    FIELD_CATEGORY_NUMBER,
    FIELD_CATEGORY_TITLE_AR,
    FIELD_CATEGORY_TITLE_EN,
    FIELD_DISPLAY_ORDER,
    MSG_CATEGORY_NUMBER_SPACES,
    MSG_DISPLAY_ORDER_GRID,
    UsefulLinkCategoryAdminPage,
    anonymous_public_view,
    qctest_title,
)
from cms.pages.useful_links.useful_link_admin_page import UsefulLinkAdminPage

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

EYEBROW_EN = "QCTEST eyebrow"
EYEBROW_AR = "حاجب اختبار"
TITLE_AR = "فئة اختبار"
GRID_ORDER = "900"
NUMBER = "09"


def _new_form(page) -> UsefulLinkCategoryAdminPage:
    admin = UsefulLinkCategoryAdminPage(page)
    admin.open_new_form()
    return admin


def _assert_blocked(admin: UsefulLinkCategoryAdminPage, saved: bool, title: str) -> None:
    assert not saved, (
        f"Publish committed although the case expects it to be blocked; "
        f"alerts={admin.validation_errors()}"
    )
    assert not admin.row_exists_fresh(title), f"A record titled {title!r} was created despite the refusal"


def _required_feedback(admin: UsefulLinkCategoryAdminPage, label: str) -> str:
    """The required-field feedback the surface gives for `label`: the native
    constraint message on the control plus the page's own required-fields
    notice. Empty string when neither is present."""
    native = admin.native_validation_message(label)
    notice = "required-fields notice" if admin.required_fields_message_shown() else ""
    return " | ".join(x for x in (native, notice) if x)


# ---- Category Number -------------------------------------------------------

@pytest.mark.tc_140730
@pytest.mark.traceability("140730")
def test_valid_category_number_saves_and_shows_in_accordion(page, browser):
    """Enter Category Number "06" -> Save succeeds; the accordion shows "06"."""
    title = qctest_title(140730, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category("06", EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=True)
        assert admin.field(FIELD_CATEGORY_NUMBER) == "06"
        assert admin.publish(), f"Save refused: {admin.last_submit}"
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title), "Category did not appear on the public accordion"
            assert public.category_header(title)["number"] == "06"
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140731
@pytest.mark.traceability("140731")
def test_empty_category_number_blocks_save(page):
    title = qctest_title(140731, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(None, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=False)
        assert admin.field(FIELD_CATEGORY_NUMBER) == ""
        saved = admin.publish()
        feedback = _required_feedback(admin, FIELD_CATEGORY_NUMBER)
        _assert_blocked(admin, saved, title)
        assert feedback, "No required-field validation message was shown for Category Number"
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140732
@pytest.mark.traceability("140732")
def test_whitespace_only_category_number_rejected_as_empty(page):
    title = qctest_title(140732, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(" ", EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=False)
        assert admin.field(FIELD_CATEGORY_NUMBER) == " ", "Field should appear populated with the space"
        saved = admin.publish()
        errors = admin.validation_errors()
        required = _required_feedback(admin, FIELD_CATEGORY_NUMBER)
        _assert_blocked(admin, saved, title)
        # Empty gives the required-field message; whitespace-only is refused
        # by the surface's own "cannot be only spaces" rule for the same field.
        assert required or any(MSG_CATEGORY_NUMBER_SPACES in e for e in errors), (
            f"Whitespace-only Category Number was not rejected as empty; alerts={errors}"
        )
    finally:
        admin.safe_cleanup(title)


# ---- Category Eyebrow ------------------------------------------------------

@pytest.mark.tc_140733
@pytest.mark.traceability("140733")
def test_valid_category_eyebrow_en_ar_saves_and_renders(page, browser):
    title = qctest_title(140733, "ULCAT")
    eyebrow_en, eyebrow_ar = "Official institutions", "المؤسسات الرسمية"
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, eyebrow_en, eyebrow_ar, title, TITLE_AR, GRID_ORDER, active=True)
        assert admin.field(FIELD_CATEGORY_EYEBROW_EN) == eyebrow_en
        assert admin.field(FIELD_CATEGORY_EYEBROW_AR) == eyebrow_ar
        assert admin.publish(), f"Save refused: {admin.last_submit}"
        admin.open_for_edit(title)
        assert admin.field(FIELD_CATEGORY_EYEBROW_EN) == eyebrow_en
        assert admin.field(FIELD_CATEGORY_EYEBROW_AR) == eyebrow_ar
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title)
            assert public.category_header(title)["eyebrow"] == eyebrow_en
            public.open_page(locale="ar")
            assert eyebrow_ar in public.category_eyebrows(), "AR eyebrow not rendered on the Arabic page"
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140734
@pytest.mark.traceability("140734")
def test_empty_category_eyebrow_blocks_save(page):
    title = qctest_title(140734, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, "", EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=False)
        assert admin.field(FIELD_CATEGORY_EYEBROW_EN) == ""
        saved = admin.publish()
        feedback = _required_feedback(admin, FIELD_CATEGORY_EYEBROW_EN)
        _assert_blocked(admin, saved, title)
        assert feedback, "No required-field validation message was shown for Category Eyebrow"
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140735
@pytest.mark.traceability("140735")
def test_category_eyebrow_over_100_chars_rejected(page):
    title = qctest_title(140735, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, "E" * 101, EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=False)
        held = len(admin.field(FIELD_CATEGORY_EYEBROW_EN))
        saved = admin.publish()
        errors = admin.validation_errors()
        if held <= 100:
            return  # truncated to the limit on input — an accepted outcome of the case
        _assert_blocked(admin, saved, title)
        # Client-side wording (admin) or the server's own max-length refusal
        # (what the Site Content Editor is shown) — both are the case's
        # "max-length validation message".
        assert any(("Category Eyebrow" in e and "maximum is 100" in e)
                   or ("maximum length of 100" in e and '"categoryEyebrow"' in e) for e in errors), (
            f"No max-length validation message for Category Eyebrow; alerts={errors}"
        )
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140736
@pytest.mark.traceability("140736")
def test_whitespace_only_category_eyebrow_rejected_as_empty(page):
    title = qctest_title(140736, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, "   ", EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=False)
        assert admin.field(FIELD_CATEGORY_EYEBROW_EN) == "   "
        saved = admin.publish()
        errors = admin.validation_errors()
        required = _required_feedback(admin, FIELD_CATEGORY_EYEBROW_EN)
        _assert_blocked(admin, saved, title)
        assert required or any("Category Eyebrow cannot be only spaces" in e for e in errors), (
            f"Whitespace-only Category Eyebrow was not rejected as empty; alerts={errors}"
        )
    finally:
        admin.safe_cleanup(title)


# ---- Category Title --------------------------------------------------------

@pytest.mark.tc_140737
@pytest.mark.traceability("140737")
def test_valid_category_title_en_ar_saves_and_renders(page, browser):
    # Case data "State of Qatar — Ministries" is the REAL category 01's title;
    # the disposable record carries it behind the QCTEST- prefix.
    title = qctest_title(140737, "ULCAT", "State of Qatar — Ministries")
    title_ar = "دولة قطر — الوزارات"
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, title_ar, GRID_ORDER, active=True)
        assert admin.field(FIELD_CATEGORY_TITLE_EN) == title
        assert admin.field(FIELD_CATEGORY_TITLE_AR) == title_ar
        assert admin.publish(), f"Save refused: {admin.last_submit}"
        admin.open_for_edit(title)
        assert admin.field(FIELD_CATEGORY_TITLE_EN) == title
        assert admin.field(FIELD_CATEGORY_TITLE_AR) == title_ar
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title)
            assert public.category_header(title)["title"] == title
            public.open_page(locale="ar")
            assert title_ar in public.category_titles(), "AR title not rendered on the Arabic page"
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140738
@pytest.mark.traceability("140738")
def test_empty_category_title_blocks_save(page):
    marker = qctest_title(140738, "ULCAT")  # AR title carries the marker so any wrongful save is findable
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, "", marker, GRID_ORDER, active=False)
        assert admin.field(FIELD_CATEGORY_TITLE_EN) == ""
        saved = admin.publish()
        feedback = _required_feedback(admin, FIELD_CATEGORY_TITLE_EN)
        assert not saved, f"Publish committed with an empty Category Title; alerts={admin.validation_errors()}"
        assert feedback, "No required-field validation message was shown for Category Title"
    finally:
        admin.safe_cleanup(marker)


@pytest.mark.tc_140739
@pytest.mark.traceability("140739")
def test_category_title_over_150_chars_rejected(page):
    prefix = qctest_title(140739, "ULCAT") + "-"
    title = prefix + "T" * (151 - len(prefix))
    assert len(title) == 151
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=False)
        held = len(admin.field(FIELD_CATEGORY_TITLE_EN))
        saved = admin.publish()
        errors = admin.validation_errors()
        if held <= 150:
            return  # truncated on input — an accepted outcome of the case
        _assert_blocked(admin, saved, title)
        assert any(("Category Title" in e and "maximum is 150" in e)
                   or ("maximum length of 150" in e and '"categoryTitle"' in e) for e in errors), (
            f"No max-length validation message for Category Title; alerts={errors}"
        )
    finally:
        admin.safe_cleanup(title)
        admin.safe_cleanup(title[:150])


@pytest.mark.tc_140740
@pytest.mark.traceability("140740")
def test_whitespace_only_category_title_rejected_as_empty(page):
    admin = _new_form(page)
    admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, "    ", qctest_title(140740, "ULCAT"), GRID_ORDER, active=False)
    assert admin.field(FIELD_CATEGORY_TITLE_EN) == "    "
    saved = admin.publish()
    errors = admin.validation_errors()
    required = _required_feedback(admin, FIELD_CATEGORY_TITLE_EN)
    assert not saved, (
        "Publish committed with a whitespace-only Category Title — a leftover row titled '    ' "
        f"now needs manual review (not auto-deleted: it has no QCTEST- identity); alerts={errors}"
    )
    assert required or any("Category Title cannot be only spaces" in e for e in errors), (
        f"Whitespace-only Category Title was not rejected as empty; alerts={errors}"
    )


# ---- Display Order ---------------------------------------------------------

@pytest.mark.tc_140741
@pytest.mark.traceability("140741")
def test_valid_positive_integer_display_order_saves(page, browser):
    """Case value "3" is used verbatim (see module docstring)."""
    title = qctest_title(140741, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, "3", active=True)
        assert admin.display_order_value() == "3"
        saved = admin.publish()
        assert saved, f"Display Order 3 was refused: {admin.last_submit}"
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title)
            assert public.category_titles().index(title) == 2, "Category is not rendered at position 3"
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140742
@pytest.mark.traceability("140742")
def test_non_numeric_or_negative_display_order_rejected(page):
    title = qctest_title(140742, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, "-1", active=False)
        saved_negative = admin.publish()
        errors_negative = admin.validation_errors()
        assert not saved_negative, "Display Order -1 was accepted"
        assert any(MSG_DISPLAY_ORDER_GRID in e for e in errors_negative), (
            f"No Display Order validation message for -1; alerts={errors_negative}"
        )

        admin.open_new_form()
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, "abc", active=False)
        saved_text = admin.publish()
        errors_text = admin.validation_errors()
        native = admin.native_validation_message(FIELD_DISPLAY_ORDER, role="spinbutton")
        assert not saved_text, "Display Order 'abc' was accepted"
        assert any(MSG_DISPLAY_ORDER_GRID in e for e in errors_text) or native, (
            f"No Display Order validation message for 'abc'; alerts={errors_text}"
        )
        assert not admin.row_exists_fresh(title)
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140743
@pytest.mark.traceability("140743")
def test_display_order_zero_rejected(page):
    title = qctest_title(140743, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, "0", active=False)
        assert admin.display_order_value() == "0"
        saved = admin.publish()
        errors = admin.validation_errors()
        _assert_blocked(admin, saved, title)
        assert any(MSG_DISPLAY_ORDER_GRID in e for e in errors), (
            f"No positive-integer validation message for Display Order 0; alerts={errors}"
        )
    finally:
        admin.safe_cleanup(title)


# ---- Add / edit / reorder / enable / disable / delete ----------------------

@pytest.mark.tc_140766
@pytest.mark.web
@pytest.mark.traceability("140766")
def test_add_new_category_appears_live_once_published(page, browser):
    title = qctest_title(140766, "ULCAT")
    admin = _new_form(page)
    try:
        admin.fill_category(NUMBER, EYEBROW_EN, EYEBROW_AR, title, TITLE_AR, GRID_ORDER, active=True)
        assert admin.publish(), f"Save refused: {admin.last_submit}"
        admin.open_list()
        assert admin.row_status(title) == "Published"
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title), "New category not on the public accordion"
            titles = public.category_titles()
            real = [t for t in titles if not t.startswith("QCTEST-")]
            # Display Order 900 is above every seeded category's order, so it
            # must render after all of them.
            assert all(titles.index(title) > titles.index(r) for r in real), (
                f"Category not at its configured order: {titles}"
            )
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140767
@pytest.mark.traceability("140767")
def test_edit_category_title_saved_with_success_toast(page):
    title = qctest_title(140767, "ULCAT")
    new_title = title + "-EDITED"
    new_title_ar = "فئة اختبار معدلة"
    admin = UsefulLinkCategoryAdminPage(page)
    try:
        assert admin.create_category(title, active=False), f"Setup refused: {admin.last_submit}"
        admin.open_for_edit(title)
        assert admin.field(FIELD_CATEGORY_TITLE_EN) == title
        admin.fill_category(title_en=new_title, title_ar=new_title_ar)
        assert admin.publish(), f"Edit refused: {admin.last_submit}"
        notice = admin.success_notice()
        assert notice, "No success toast was shown after saving the edit"
        admin.open_for_edit(new_title)
        assert admin.field(FIELD_CATEGORY_TITLE_EN) == new_title
        assert admin.field(FIELD_CATEGORY_TITLE_AR) == new_title_ar
    finally:
        admin.safe_cleanup(new_title)
        admin.safe_cleanup(title)


@pytest.mark.tc_140768
@pytest.mark.web
@pytest.mark.traceability("140768")
def test_reorder_categories_reflects_on_public_page(page, browser):
    """The case edits real category 05; per the disposable-data rule two
    QCTEST categories are created (A=900, B=1000) and B is moved ahead of A.
    DISCLOSED DEVIATION: the case's literal Display Order "1" is refused by
    the app's 100-grid rule (minimum 100), so B is moved to the accepted
    value 800; what is verified is the reorder itself (B now renders before
    A). "Renders first overall" is not reachable without editing real
    categories, which the test-data rule forbids."""
    first = qctest_title(140768, "ULCAT", "A")
    second = qctest_title(140768, "ULCAT", "B")
    admin = UsefulLinkCategoryAdminPage(page)
    try:
        assert admin.create_category(first, display_order="900", active=True), admin.last_submit
        assert admin.create_category(second, display_order="1000", active=True), admin.last_submit
        with anonymous_public_view(browser) as public:
            order = public.wait_for_order(first, second)
            assert first in order and second in order, f"Precondition: A/B not both rendered: {order}"
            assert order.index(first) < order.index(second), f"Precondition: A not before B: {order}"
        admin.open_for_edit(second)
        admin.set_display_order("800")
        assert admin.display_order_value() == "800"
        assert admin.publish(), f"Display Order 800 was refused: {admin.last_submit}"
        with anonymous_public_view(browser) as public:
            order = public.wait_for_order(second, first)
            assert second in order and first in order and order.index(second) < order.index(first), (
                f"Re-ordered category does not render ahead of the other one: {order}"
            )
    finally:
        admin.safe_cleanup(second)
        admin.safe_cleanup(first)


@pytest.mark.tc_140769
@pytest.mark.web
@pytest.mark.traceability("140769")
def test_disabling_category_hides_it_from_public_page(page, browser):
    title = qctest_title(140769, "ULCAT")
    admin = UsefulLinkCategoryAdminPage(page)
    try:
        assert admin.create_category(title, active=True), admin.last_submit
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title), "Precondition: active category not visible"
        admin.open_for_edit(title)
        admin.set_active_status(False)
        assert not admin.is_active_status_checked()
        assert admin.publish(), f"Save refused: {admin.last_submit}"
        with anonymous_public_view(browser) as public:
            assert not public.wait_for_category(title, present=False), (
                "Inactive category still rendered on the public accordion"
            )
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140770
@pytest.mark.web
@pytest.mark.traceability("140770")
def test_re_enabling_category_shows_it_again(page, browser):
    title = qctest_title(140770, "ULCAT")
    admin = UsefulLinkCategoryAdminPage(page)
    try:
        assert admin.create_category(title, active=False), admin.last_submit
        with anonymous_public_view(browser) as public:
            assert not public.wait_for_category(title, present=False), "Precondition: inactive category visible"
        admin.open_for_edit(title)
        admin.set_active_status(True)
        assert admin.is_active_status_checked()
        assert admin.publish(), f"Save refused: {admin.last_submit}"
        with anonymous_public_view(browser) as public:
            assert public.wait_for_category(title), "Re-enabled category did not reappear"
            titles = public.category_titles()
            real = [t for t in titles if not t.startswith("QCTEST-")]
            assert all(titles.index(title) > titles.index(r) for r in real), (
                f"Re-enabled category not at its configured order: {titles}"
            )
    finally:
        admin.safe_cleanup(title)


@pytest.mark.tc_140771
@pytest.mark.web
@pytest.mark.traceability("140771")
def test_delete_disposable_category(page, browser, request):
    title = qctest_title(140771, "ULCAT")
    link_org = qctest_title(140771, "ULINK")
    admin = UsefulLinkCategoryAdminPage(page)
    links = UsefulLinkAdminPage(page)
    logo = str(request.path.parent / "fixtures" / "useful_link_qctest_moci-logo.png")
    try:
        assert admin.create_category(title, active=True), admin.last_submit
        assert links.create_link(link_org, title, logo), f"Setup link refused: {links.last_submit}"
        with anonymous_public_view(browser) as public:
            assert public.wait_for_card(title, link_org), "Precondition: category/link not visible"
        assert title.startswith("QCTEST-")  # step 1: target confirmed disposable
        assert admin.delete_disposable(title), "Category row still in the admin grid after Delete"
        with anonymous_public_view(browser) as public:
            assert not public.wait_for_category(title, present=False), "Deleted category still on the public page"
            assert link_org not in public.all_card_orgs(), "Deleted category's link still rendered"
    finally:
        # Deleting the category takes its Link Item into the Recycle Bin too.
        admin.teardown_category(title)

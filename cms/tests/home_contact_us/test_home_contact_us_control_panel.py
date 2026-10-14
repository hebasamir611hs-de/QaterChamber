"""
cms/tests/home_contact_us/test_home_contact_us_control_panel.py — Control_Panel
cases for PBI 129390 (QC-HOME-014, Home "Quick Contact Us" section), suite 134461.

REWRITTEN 2026-10-08 (Phase 3, B-129390). See the Page Object docstring for the
live model. In short:

* **Inquiry Category** (Object Authoring `manage-inquiry-category`): every case
  runs as **QC Site Content Editor** on a disposable `QCTEST-<tc>-*` category.
  The 11 live QCDEMO rows (52706..52746) are never written. A category made
  public for a dropdown assertion is deleted right after the assertion.
* **Contact Us Section article** (Journal, structure 52431 — the documented
  exception to "Object Authoring only"): the QC Site Content Editor has no
  access to Web Content (live: "You do not have the roles required to access
  this portlet."), so the field cases run as **TEST_USER** — the only account
  that can open the form — on a disposable `QCTEST-129390-<tc>` article, Save
  as Draft only (136498 publishes its own QCTEST article with Searchable off).
  The live article 53012 is only ever opened read-only. Each disposable article
  is moved to the Recycle Bin by exact title and the list re-read.
* Public-reflection halves ("renders on Home Page", "used for routing") need the
  live article 53012 to change — NEEDS USER; they are not asserted here.
* Inline-message wording that differs from the PBI is recorded, not asserted.
"""

import json

import allure
import pytest

from cms.pages.home_contact_us.home_contact_us_admin_page import (
    ARTICLE_53012_EDIT_PATH,
    FIELD_ACTIVE_STATUS,
    FIELD_CATEGORY_LABEL_AR,
    FIELD_CATEGORY_LABEL_EN,
    FIELD_DISPLAY_ORDER,
    LIVE_CATEGORY_CODES,
    NO_ROLE_MESSAGE,
    ContactUsSectionArticlePage,
    Disposables,
    InquiryCategoryAdminPage,
    sign_in,
)
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import control_panel_url
from core.web.browser import new_context
from web.pages.home_quick_contact.home_quick_contact_page import HomeQuickContactPage

ANON_PAGE = pytest.mark.parametrize("page", [{"auth": False}], indirect=["page"])
ARTICLE_GROUP = pytest.mark.xdist_group("contact_us_qctest_article_129390")
CATEGORY_GROUP = pytest.mark.xdist_group("inquiry_category_qctest_129390")
IC_MANAGE_PATH = "/en/web/qatar-chamber/manage-inquiry-category"


def _attach(name: str, data) -> None:
    allure.attach(json.dumps(data, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _marks(*names):
    def deco(fn):
        for n in reversed(names):
            fn = getattr(pytest.mark, n)(fn)
        return fn
    return deco


COMMON = _marks("control_panel", "global_", "pbi_129390")


# =============================================================================
# Fixtures
# =============================================================================
class _Disposables(Disposables):
    def cleanup(self) -> None:
        out = super().cleanup()
        _attach("teardown", out)
        assert not out["left"], f"QCTEST teardown left records behind: {out['left']}"


@pytest.fixture
def qc_category(page):
    admin = InquiryCategoryAdminPage(page)
    d = _Disposables(admin)
    yield admin, d
    from cms.tests.live_write_guard import deletes_suppressed

    if not deletes_suppressed():  # nothing to delete under rule 10 -> no re-sign-in
        sign_in(page, "Site Content Editor")
    d.cleanup()


@pytest.fixture
def qc_article(page):
    """TEST_USER on the Web Content form. Tracks every saved QCTEST article as
    {title, article_id}; teardown deletes each by ID through headless-delivery
    (exact title + QCTEST- guarded, re-GET expects 404) — the Web Content list
    itself is unavailable on qcdev."""
    sign_in(page, None)
    art = ContactUsSectionArticlePage(page)
    created: list = []
    yield art, created
    out, left = [], []
    from cms.tests.live_write_guard import LiveRecord, deletes_suppressed, keep_instead_of_delete

    if deletes_suppressed():
        # PBI running rules, rule 10: nothing is deleted -- log each article as kept.
        for rec in created:
            keep_instead_of_delete(LiveRecord("journal-article", str(rec.get("article_id") or "?"),
                                              rec["title"]), rec["title"])
        _attach("article teardown", {"created": created, "kept": created})
        return
    for rec in created:
        if not rec.get("article_id"):
            left.append(f"{rec['title']} (saved, no articleId captured)")
            continue
        try:
            res = art.delete_qctest_article(rec["article_id"], rec["title"])
            out.append(res)
            if not res["gone"]:
                left.append(f"{rec['title']} ({rec['article_id']})")
        except AssertionError:
            raise
        except Exception as e:  # noqa: BLE001
            left.append(f"{rec['title']} ({type(e).__name__})")
    _attach("article teardown", {"created": created, "deleted": out, "left": left})
    assert not left, f"QCTEST articles left behind: {left}"


def _public_dropdown(browser, locale: str = "en") -> list:
    ctx = new_context(browser, use_auth_state=False)
    try:
        home = HomeQuickContactPage(ctx.new_page())
        home.open_home_arabic() if locale == "ar" else home.open_home()
        home.scroll_to_section()
        home.page.wait_for_function(
            "() => document.querySelectorAll('#qc-cu-category option').length > 1", timeout=30000)
        return home.category_option_labels()
    finally:
        ctx.close()


# =============================================================================
# Inquiry Category — Object Authoring, QC Site Content Editor, QCTEST records
# =============================================================================
def _create_category(admin, d, prefix: str, *, draft: bool, **kw) -> dict:
    admin.open_new_form()
    values = admin.fill_category(prefix, **kw)
    result = admin.resolve_created(admin.submit_outcome(draft=draft), prefix)
    d.track(prefix, result)
    result["values"] = values
    return result


def _assert_category_refused(admin, d, prefix: str, what: str, **kw) -> dict:
    """Save as Draft is recorded (Object Authoring drafts skip required
    validation by design); the PUBLISH attempt must be refused."""
    draft = _create_category(admin, d, prefix + "-D", draft=True, **kw)
    publish = _create_category(admin, d, prefix + "-P", draft=False, **kw)
    _attach(f"{what}: draft / publish", {"draft": draft, "publish": publish})
    assert not publish["created_code"] and publish["outcome"] in ("refused", None), (
        f"{what}: Publish was ACCEPTED — {publish}")
    assert publish["refusal"] or publish["invalid_inputs"], f"{what}: refused silently — {publish}"
    return {"draft": draft, "publish": publish}


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (EN) valid value saves and appears in the public dropdown (ADO-136534)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136534
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_en_valid_value_saves_136534(page, qc_category, browser):
    """Account: QC Site Content Editor. Disposable category; Save as Draft
    (not public), then Publish with Active ticked -> visible to a logged-out
    visitor; deleted in teardown."""
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    label = "QCTEST-136534 General Inquiry"
    draft = _create_category(admin, d, "QCTEST-136534", draft=True, label_en=label, active=True)
    _attach("draft", draft)
    assert draft["created_code"], f"Save as Draft did not create the category: {draft}"
    admin.open_entry_by_code(draft["created_code"], locale="en")
    assert admin.current_status() == STATUS_DRAFT
    assert admin.field_value(FIELD_CATEGORY_LABEL_EN) == label
    assert label not in _public_dropdown(browser), "a DRAFT category is visible to visitors"
    with allure.step("Publish it and check the logged-out dropdown"):
        admin.submit_outcome(draft=False)
        assert admin.goto_row(draft["created_code"]), "category row not found after publish"
        assert admin.row_status_text_by_code(draft["created_code"]) == STATUS_PUBLISHED
        options = _public_dropdown(browser)
        _attach("public options", options)
        _attach("unpublished right after the check", admin.deactivate(draft["created_code"]))
        assert label in options, f"published category not in the public dropdown: {options}"


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Display Order valid value saves and sorts first (ADO-136538)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136538
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_display_order_valid_value_saves_136538(page, qc_category, browser):
    """Account: QC Site Content Editor. Display Order = 1 (the case's value; the
    live rows use 100..1100) -> the category is listed first after the
    placeholder. Public for the length of the assertion, then deleted."""
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    label = "QCTEST-136538 First"
    res = _create_category(admin, d, "QCTEST-136538", draft=False, label_en=label, display_order="1", active=True)
    _attach("publish", res)
    assert res["created_code"], f"category not created: {res}"
    admin.open_entry_by_code(res["created_code"], locale="en")
    assert admin.display_order_value() == "1"
    options = _public_dropdown(browser)
    _attach("public options", options)
    _attach("unpublished right after the check", admin.deactivate(res["created_code"]))
    assert len(options) > 1 and options[1] == label, f"display order 1 is not listed first: {options}"


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (AR) valid value saves and appears in the public dropdown (ADO-136569)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.tc_136569
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_ar_valid_value_saves_136569(page, qc_category, browser):
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    label_ar = "QCTEST-136569 استفسار عام"
    res = _create_category(admin, d, "QCTEST-136569", draft=False, label_ar=label_ar, active=True)
    _attach("publish", res)
    assert res["created_code"], f"category not created: {res}"
    admin.open_entry_by_code(res["created_code"], locale="en")
    assert admin.field_value(FIELD_CATEGORY_LABEL_AR) == label_ar
    options = _public_dropdown(browser, "ar")
    _attach("public AR options", options)
    _attach("unpublished right after the check", admin.deactivate(res["created_code"]))
    assert label_ar in options, f"Arabic label not in the AR public dropdown: {options}"


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (EN) empty is rejected (ADO-136535)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136535
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_en_empty_rejected_136535(page, qc_category):
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    _assert_category_refused(admin, d, "QCTEST-136535", "Label EN empty", label_en="")


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (EN) whitespace-only is rejected (ADO-136537)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136537
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_en_whitespace_rejected_136537(page, qc_category):
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    _assert_category_refused(admin, d, "QCTEST-136537", "Label EN whitespace", label_en="   ")


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (AR) empty is rejected (ADO-136570)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_136570
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_ar_empty_rejected_136570(page, qc_category):
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    _assert_category_refused(admin, d, "QCTEST-136570", "Label AR empty", label_ar="")


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Display Order empty is rejected (ADO-136539)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136539
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_display_order_empty_rejected_136539(page, qc_category):
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    _assert_category_refused(admin, d, "QCTEST-136539", "Display Order empty", display_order="")


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Display Order rejects zero, negative and non-numeric values (ADO-136540)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136540
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_display_order_invalid_values_rejected_136540(page, qc_category):
    """'abc' cannot be typed into the number input at all (the browser drops
    it) — recorded as rejected at input level, then the empty value it leaves
    must also be refused on Publish."""
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    accepted = []
    for tag, value in (("zero", "0"), ("neg", "-1")):
        prefix = f"QCTEST-136540-{tag}"
        res = _create_category(admin, d, prefix, draft=False, display_order=value)
        _attach(f"Display Order {value}", res)
        if res["created_code"] or res["outcome"] not in ("refused", None):
            accepted.append(value)
    admin.open_new_form()
    box = page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True)
    try:
        box.fill("abc")
        typed = box.input_value()
    except Exception as e:  # noqa: BLE001 — Playwright refuses text into type=number
        typed = f"refused by input: {type(e).__name__}"
    _attach("Display Order 'abc'", {"value_after_typing": typed})
    assert typed in ("",) or typed.startswith("refused"), f"'abc' was accepted by the input: {typed!r}"
    assert not accepted, f"Display Order accepted invalid values {accepted} (PBI: 'Positive number required.')"


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (EN) at 101 characters (ADO-136536) — Rule 5")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136536
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_en_101_chars_136536(page, qc_category, browser):
    """bug-rules Rule 5: read the implemented limit live; the value at that
    limit (or at 101 when the field has none) must save and render without
    breaking the CMS form or the public dropdown/section."""
    _category_char_limit_case(page, qc_category, browser, "136536", "en")


@allure.feature("Contact Us Section — Inquiry Categories")
@allure.title("Inquiry Category Label (AR) at 101 characters (ADO-136571) — Rule 5")
@COMMON
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_136571
@CATEGORY_GROUP
@ANON_PAGE
def test_inquiry_category_label_ar_101_chars_136571(page, qc_category, browser):
    _category_char_limit_case(page, qc_category, browser, "136571", "ar")


def _category_char_limit_case(page, qc_category, browser, tc: str, locale: str):
    """Char limit (QA lead 2026-10-14): the PBI limit (100) is binding. A
    101-character label on an INACTIVE QCTEST category must be refused or cut
    to 100."""
    admin, d = qc_category
    sign_in(page, "Site Content Editor")
    admin.open_new_form()
    field = FIELD_CATEGORY_LABEL_AR if locale == "ar" else FIELD_CATEGORY_LABEL_EN
    implemented = admin.maxlength(field)
    limit = 100
    head = f"QCTEST-{tc} "
    filler = "ع" if locale == "ar" else "x"
    value = (head + filler * (limit + 1))[:limit + 1]
    kw = {"label_ar": value} if locale == "ar" else {"label_en": value}
    res = _create_category(admin, d, f"QCTEST-{tc}", draft=False, active=False, **kw)
    stored = ""
    if res.get("created_code"):
        admin.open_entry_by_code(res["created_code"], locale="en")
        stored = admin.field_value(field)
    _attach("char limit (PBI)", {"pbi_limit": limit, "implemented_maxlength": implemented,
                                 "typed": len(value), "result": res, "stored_length": len(stored)})
    assert not res.get("created_code") or len(stored) <= limit, (
        f"Inquiry Category Label ({locale}) accepted {len(stored)} characters; the PBI limit is {limit} "
        f"(maxlength attribute: {implemented})")


# =============================================================================
# Contact Us Section article — TEST_USER, disposable QCTEST articles
# =============================================================================
def _article_case(art, titles, tc: str, *, label: str | None = None, value: str | None = None,
                  locale: str = "en_US") -> dict:
    """New QCTEST article, every required field valid (EN, plus AR when the
    case is Arabic), then `label` := `value` in `locale`, Save as Draft."""
    title = f"QCTEST-129390-{tc}"
    art.open_new_article()
    art.set_title(title)
    art.fill_all_valid(title, "en_US")
    if locale != "en_US":
        art.switch_content_locale("ar-SA")
        art.fill_all_valid(title, locale)
    if label is not None:
        art.fill(label, value, locale)
    result = art.save_as_draft()
    result["title"] = title
    _track(titles, result)
    result["field_error"] = art.field_error(label) if label else ""
    _attach(f"{tc} save outcome", result)
    return result


def _track(created: list, result: dict) -> None:
    """Record a saved article for teardown; a save without an articleId in
    the URL cannot be torn down by ID, so it fails the test."""
    if result.get("saved") or result.get("success_alert") or result.get("article_id"):
        created.append({"title": result["title"], "article_id": result.get("article_id")})
        assert result.get("article_id"), f"article saved but no articleId captured for teardown: {result}"


def _assert_saved(art, result: dict, label: str, value: str, locale: str = "en_US") -> None:
    assert result["saved"], f"valid value was refused: {result}"
    assert art.value(label, locale) == value, "value not kept after save"


def _assert_refused(result: dict, label: str) -> None:
    assert not result["saved"], f"{label}: the article SAVED with an invalid value — {result}"
    assert result["field_error"] or result["error"], f"{label}: refused with no message — {result}"


def _article_test(tc, title, *, label, value, expect, locale="en_US", extra_marks=()):
    """Factory for the one-field article cases (keeps 40 near-identical
    tests readable). `expect` is 'saved', 'refused' or 'rule5'."""

    @allure.feature("Contact Us Section — section content (Journal article)")
    @allure.title(f"{title} (ADO-{tc})")
    @COMMON
    @pytest.mark.functional_low
    @ARTICLE_GROUP
    @ANON_PAGE
    def _t(page, qc_article):
        art, titles = qc_article
        result = _article_case(art, titles, tc, label=label, value=value, locale=locale)
        if expect == "saved":
            _assert_saved(art, result, label, value, locale)
        elif expect == "refused":
            _assert_refused(result, label)
        else:  # char limit (QA lead 2026-10-14): the PBI limit is binding
            limit = len(value) - 1
            attrs = art.attrs(label)
            kept = art.value(label, locale) if result["saved"] else ""
            _attach("char limit (PBI)", {"pbi_limit": limit, "typed": len(value), "attrs": attrs,
                                         "result": result, "stored_length": len(kept)})
            assert not result["saved"] or len(kept) <= limit, (
                f"{label} ({locale}) accepted {len(kept)} characters; the PBI limit is {limit} "
                f"(maxlength attribute: {attrs.get('maxlength')})")

    _t.__name__ = f"test_article_{tc}"
    for m in (getattr(pytest.mark, f"tc_{tc}"),) + tuple(getattr(pytest.mark, x) for x in extra_marks):
        _t = m(_t)
    return _t


AR = "ar_SA"
S51 = "QCTEST tag " + "x" * 40                      # 51
S101 = "QCTEST heading " + "x" * 86                 # 101
S501 = "QCTEST description " + "x" * 482            # 501
S301 = "QCTEST address " + "x" * 286                # 301
S21 = "+974 4455 9111 123456"                       # 21
E151 = "q" * 142 + "@qcci.org"                      # 151
U501 = "https://www.google.com/maps/embed?pb=" + "x" * 464  # 501
R301 = ";".join(["qctest%02d@qcci.org" % i for i in range(16)]) + ";q016@qcci.org"  # 17 valid emails, 301 chars
A51 = "QCTEST " + "ع" * 44
A101 = "QCTEST " + "ع" * 94
A501 = "QCTEST " + "ع" * 494
A301 = "QCTEST " + "ع" * 294
assert (len(S51), len(S101), len(S501), len(S301), len(S21), len(E151), len(U501), len(R301),
        len(A51), len(A101), len(A501), len(A301)) == (51, 101, 501, 301, 21, 151, 501, 301, 51, 101, 501, 301)

test_section_tag_en_valid_136508 = _article_test("136508", "Section Tag (EN) valid value saves", label="Section Tag", value="Get in touch", expect="saved", extra_marks=("regression",))
test_section_tag_en_empty_136509 = _article_test("136509", "Section Tag (EN) empty is rejected", label="Section Tag", value="", expect="refused")
test_section_tag_en_51_136510 = _article_test("136510", "Section Tag (EN) at 51 characters — Rule 5", label="Section Tag", value=S51, expect="rule5")
test_section_tag_en_ws_136511 = _article_test("136511", "Section Tag (EN) whitespace-only is rejected", label="Section Tag", value="   ", expect="refused")
test_section_heading_en_valid_136512 = _article_test("136512", "Section Heading (EN) valid value saves", label="Section Heading", value="Connect with Qatar Chamber to Move Your Business Forward", expect="saved", extra_marks=("regression",))
test_section_heading_en_empty_136513 = _article_test("136513", "Section Heading (EN) empty is rejected", label="Section Heading", value="", expect="refused")
test_section_heading_en_101_136514 = _article_test("136514", "Section Heading (EN) at 101 characters — Rule 5", label="Section Heading", value=S101, expect="rule5")
test_section_heading_en_ws_136515 = _article_test("136515", "Section Heading (EN) whitespace-only is rejected", label="Section Heading", value="   ", expect="refused")
test_section_desc_en_valid_136516 = _article_test("136516", "Section Description (EN) valid value saves", label="Section Description", value="Reach out to us for enquiries, support, or information.", expect="saved")
test_section_desc_en_501_136517 = _article_test("136517", "Section Description (EN) at 501 characters — Rule 5", label="Section Description", value=S501, expect="rule5")
test_email_support_valid_136518 = _article_test("136518", "Email Support Address valid value saves", label="Email Support Address", value="support@qcci.org", expect="saved", extra_marks=("regression",))
test_email_support_empty_136519 = _article_test("136519", "Email Support Address empty is rejected", label="Email Support Address", value="", expect="refused")
test_email_support_invalid_136520 = _article_test("136520", "Email Support Address invalid format is rejected", label="Email Support Address", value="support@@qcci", expect="refused")
test_email_support_151_136521 = _article_test("136521", "Email Support Address at 151 characters — Rule 5", label="Email Support Address", value=E151, expect="rule5")
test_email_support_ws_136522 = _article_test("136522", "Email Support Address whitespace-only is rejected", label="Email Support Address", value="   ", expect="refused")
test_telephone_valid_136523 = _article_test("136523", "Telephone Number valid value saves", label="Telephone Number", value="+974 44559111", expect="saved", extra_marks=("regression",))
test_telephone_empty_136524 = _article_test("136524", "Telephone Number empty is rejected", label="Telephone Number", value="", expect="refused")
test_telephone_21_136525 = _article_test("136525", "Telephone Number at 21 characters — Rule 5", label="Telephone Number", value=S21, expect="rule5")
test_telephone_ws_136526 = _article_test("136526", "Telephone Number whitespace-only is rejected", label="Telephone Number", value="   ", expect="refused")
test_location_en_valid_136527 = _article_test("136527", "Location Address (EN) valid value saves", label="Location Address", value="Lusail Boulevard 69, Al Kharayej – Street 169, Doha, Qatar", expect="saved", extra_marks=("regression",))
test_location_en_empty_136528 = _article_test("136528", "Location Address (EN) empty is rejected", label="Location Address", value="", expect="refused")
test_location_en_301_136529 = _article_test("136529", "Location Address (EN) at 301 characters — Rule 5", label="Location Address", value=S301, expect="rule5")
test_location_en_ws_136530 = _article_test("136530", "Location Address (EN) whitespace-only is rejected", label="Location Address", value="   ", expect="refused")
test_map_url_valid_136531 = _article_test("136531", "Map Embed URL valid value saves", label="Map Embed URL", value="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3606.0!2d51.5!3d25.3", expect="saved")
test_map_url_invalid_136532 = _article_test("136532", "Map Embed URL invalid format is rejected", label="Map Embed URL", value="not-a-url", expect="refused")
test_map_url_501_136533 = _article_test("136533", "Map Embed URL at 501 characters — Rule 5", label="Map Embed URL", value=U501, expect="rule5")
test_recipients_valid_136541 = _article_test("136541", "Form Recipient Email(s) valid multi-value saves", label="Form Recipient Email(s)", value="contact@qcci.org;info@qcci.org", expect="saved", extra_marks=("regression",))
test_recipients_empty_136542 = _article_test("136542", "Form Recipient Email(s) empty is rejected", label="Form Recipient Email(s)", value="", expect="refused")
test_recipients_invalid_136543 = _article_test("136543", "Form Recipient Email(s) invalid format is rejected", label="Form Recipient Email(s)", value="contact@qcci.org;;bad-email", expect="refused")
test_recipients_301_136544 = _article_test("136544", "Form Recipient Email(s) at 301 characters — Rule 5", label="Form Recipient Email(s)", value=R301, expect="rule5")
test_recipients_ws_136545 = _article_test("136545", "Form Recipient Email(s) whitespace-only is rejected", label="Form Recipient Email(s)", value="   ", expect="refused")
test_button_label_en_empty_136547 = _article_test("136547", "Send Message Button Label (EN) empty is rejected", label="Send Message Button Label", value="", expect="refused")
test_button_label_en_51_136548 = _article_test("136548", "Send Message Button Label (EN) at 51 characters — Rule 5", label="Send Message Button Label", value=S51, expect="rule5")
test_button_label_en_ws_136549 = _article_test("136549", "Send Message Button Label (EN) whitespace-only is rejected", label="Send Message Button Label", value="   ", expect="refused")
test_section_tag_ar_valid_136555 = _article_test("136555", "Section Tag (AR) valid value saves", label="Section Tag", value="تواصل معنا", expect="saved", locale=AR, extra_marks=("regression", "bilingual"))
test_section_tag_ar_empty_136556 = _article_test("136556", "Section Tag (AR) empty is rejected", label="Section Tag", value="", expect="refused", locale=AR, extra_marks=("bilingual",))
test_section_tag_ar_51_136557 = _article_test("136557", "Section Tag (AR) at 51 characters — Rule 5", label="Section Tag", value=A51, expect="rule5", locale=AR, extra_marks=("bilingual",))
test_section_tag_ar_ws_136558 = _article_test("136558", "Section Tag (AR) whitespace-only is rejected", label="Section Tag", value="   ", expect="refused", locale=AR, extra_marks=("bilingual",))
test_section_heading_ar_valid_136559 = _article_test("136559", "Section Heading (AR) valid value saves", label="Section Heading", value="تواصل مع قطر لدفع أعمالك إلى الأمام", expect="saved", locale=AR, extra_marks=("regression", "bilingual"))
test_section_heading_ar_empty_136560 = _article_test("136560", "Section Heading (AR) empty is rejected", label="Section Heading", value="", expect="refused", locale=AR, extra_marks=("bilingual",))
test_section_heading_ar_101_136561 = _article_test("136561", "Section Heading (AR) at 101 characters — Rule 5", label="Section Heading", value=A101, expect="rule5", locale=AR, extra_marks=("bilingual",))
test_section_heading_ar_ws_136562 = _article_test("136562", "Section Heading (AR) whitespace-only is rejected", label="Section Heading", value="   ", expect="refused", locale=AR, extra_marks=("bilingual",))
test_section_desc_ar_valid_136563 = _article_test("136563", "Section Description (AR) valid value saves", label="Section Description", value="تواصلوا معنا للاستفسارات والدعم والمعلومات.", expect="saved", locale=AR, extra_marks=("bilingual",))
test_section_desc_ar_501_136564 = _article_test("136564", "Section Description (AR) at 501 characters — Rule 5", label="Section Description", value=A501, expect="rule5", locale=AR, extra_marks=("bilingual",))
test_location_ar_valid_136565 = _article_test("136565", "Location Address (AR) valid value saves", label="Location Address", value="شارع لوسيل بوليفارد 69، الخرائج - شارع 169، الدوحة، قطر", expect="saved", locale=AR, extra_marks=("regression", "bilingual"))
test_location_ar_empty_136566 = _article_test("136566", "Location Address (AR) empty is rejected", label="Location Address", value="", expect="refused", locale=AR, extra_marks=("bilingual",))
test_location_ar_301_136567 = _article_test("136567", "Location Address (AR) at 301 characters — Rule 5", label="Location Address", value=A301, expect="rule5", locale=AR, extra_marks=("bilingual",))
test_location_ar_ws_136568 = _article_test("136568", "Location Address (AR) whitespace-only is rejected", label="Location Address", value="   ", expect="refused", locale=AR, extra_marks=("bilingual",))
test_button_label_ar_empty_136573 = _article_test("136573", "Send Message Button Label (AR) empty is rejected", label="Send Message Button Label", value="", expect="refused", locale=AR, extra_marks=("bilingual",))
test_button_label_ar_51_136574 = _article_test("136574", "Send Message Button Label (AR) at 51 characters — Rule 5", label="Send Message Button Label", value=A51, expect="rule5", locale=AR, extra_marks=("bilingual",))
test_button_label_ar_ws_136575 = _article_test("136575", "Send Message Button Label (AR) whitespace-only is rejected", label="Send Message Button Label", value="   ", expect="refused", locale=AR, extra_marks=("bilingual",))


def _button_label_publish_case(page, qc_article, browser, tc: str, locale: str, value: str):
    """Save as Draft, then Publish — on a QCTEST article with Searchable
    unticked (it renders nowhere). The public-CTA half needs the live article
    53012 (NEEDS USER); the logged-out CTA is read and recorded only."""
    art, titles = qc_article
    title = f"QCTEST-129390-{tc}"
    art.open_new_article()
    art.set_title(title)
    art.set_searchable(False)
    art.fill_all_valid(title, "en_US")
    if locale != "en_US":
        art.switch_content_locale("ar-SA")
        art.fill_all_valid(title, locale)
    art.fill("Send Message Button Label", value, locale)
    draft = art.save_as_draft()
    draft["title"] = title
    _track(titles, draft)
    assert draft["saved"], f"Save as Draft refused: {draft}"
    pub = art.publish()
    _attach("draft / publish", {"draft": draft, "publish": pub})
    assert pub["saved"], f"Publish refused: {pub}"
    ctx = new_context(browser, use_auth_state=False)
    try:
        home = HomeQuickContactPage(ctx.new_page())
        home.open_home_arabic() if locale != "en_US" else home.open_home()
        home.scroll_to_section()
        _attach("live CTA (53012, not changed by this test)", {"cta": home.text(home.SUBMIT_LABEL)})
    finally:
        ctx.close()


@allure.feature("Contact Us Section — section content (Journal article)")
@allure.title("Send Message Button Label (EN) valid value saves and publishes (ADO-136546)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.tc_136546
@ARTICLE_GROUP
@ANON_PAGE
def test_send_message_button_label_en_valid_136546(page, qc_article, browser):
    _button_label_publish_case(page, qc_article, browser, "136546", "en_US", "Send Message")


@allure.feature("Contact Us Section — section content (Journal article)")
@allure.title("Send Message Button Label (AR) valid value saves and publishes (ADO-136572)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.tc_136572
@ARTICLE_GROUP
@ANON_PAGE
def test_send_message_button_label_ar_valid_136572(page, qc_article, browser):
    _button_label_publish_case(page, qc_article, browser, "136572", AR, "إرسال الرسالة")


@allure.feature("Contact Us Section — section content (Journal article)")
@allure.title("CMS end-to-end configuration flow saves, previews and publishes (ADO-136498)")
@COMMON
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.tc_136498
@ARTICLE_GROUP
@ANON_PAGE
def test_contact_us_section_full_admin_configuration_flow_136498(page, qc_article, browser):
    """Steps 1-5 on a QCTEST article (Searchable unticked). Step 5's "Home Page
    reflects new content" can only be shown on the live article 53012 — NEEDS
    USER; here the logged-out heading is read and must NOT carry the QCTEST
    value (the disposable article must not leak)."""
    art, titles = qc_article
    title = "QCTEST-129390-136498"
    with allure.step("Step 1-2: open the form, enter all fields EN + AR"):
        art.open_new_article()
        art.set_title(title)
        art.set_searchable(False)
        en = art.fill_all_valid(title, "en_US")
        art.switch_content_locale("ar-SA")
        ar = art.fill_all_valid(title, AR)
        assert art.value("Section Heading", AR) == ar["Section Heading"]
    with allure.step("Step 3: Save as Draft"):
        draft = art.save_as_draft()
        draft["title"] = title
        _track(titles, draft)
        assert draft["saved"], f"draft refused: {draft}"
    with allure.step("Step 4: Preview renders the entered values"):
        preview = art.preview_text()
        _attach("preview", preview[:1500])
        assert title in preview or en["Section Heading"] in preview, "preview does not show the entered values"
    with allure.step("Step 5: Publish"):
        pub = art.publish()
        _attach("publish", pub)
        assert pub["saved"], f"publish refused: {pub}"
    ctx = new_context(browser, use_auth_state=False)
    try:
        home = HomeQuickContactPage(ctx.new_page())
        home.open_home()
        home.scroll_to_section()
        heading = home.heading_text()
    finally:
        ctx.close()
    _attach("live heading", heading)
    assert title not in heading, "a disposable QCTEST article leaked into the public section"


# =============================================================================
# RBAC / screens
# =============================================================================
@allure.feature("Contact Us Section — access")
@allure.title("A Site Content Editor can access Contact Us Section Management (ADO-136483)")
@COMMON
@pytest.mark.auth
@pytest.mark.tc_136483
@ANON_PAGE
def test_site_content_editor_can_access_management_136483(page):
    """Account: QC Site Content Editor (US002's named actor). Read-only: opens
    the section's content (article 53012) and the Inquiry Category list."""
    sign_in(page, "Site Content Editor")
    art = ContactUsSectionArticlePage(page)
    status = art.goto_bare(ARTICLE_53012_EDIT_PATH)
    page.wait_for_timeout(4000)  # measured: the Journal form needs ~3 s to mount its DDM fields
    fields = art.fields_rendered()
    denied = art.no_role_message_shown()
    page.screenshot(path="reports/manual-exec-129390-136483.png", full_page=False)
    ic_status = art.goto_bare(IC_MANAGE_PATH)
    try:  # HEALED: the entries table renders client-side after load
        page.locator("table tbody tr").first.wait_for(timeout=45000)
    except Exception:  # noqa: BLE001 — counted as 0 below
        pass
    ic_rows = page.locator("table tbody tr").count()
    _attach("editor access", {"article_status": status, "fields": fields, "no_role_message": denied,
                              "inquiry_category_status": ic_status, "inquiry_category_rows": ic_rows})
    assert ic_rows > 0, "Editor cannot list Inquiry Categories"
    assert not denied, f"Editor is refused the Contact Us Section content: '{NO_ROLE_MESSAGE}'"
    assert all(fields.values()), f"section fields not editable for Editor: {fields}"


@allure.feature("Contact Us Section — access")
@allure.title("A user without the Content Editor role is denied Contact Us Section Management (ADO-136484)")
@COMMON
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.tc_136484
@ANON_PAGE
def test_user_without_editor_role_denied_136484(page):
    """Account: QC site member (no CMS role). Bare page.goto (no session guard)."""
    sign_in(page, "Site Member")
    assert CmsLoginPage(page).login_succeeded(), "site-member login failed"
    art = ContactUsSectionArticlePage(page)
    out = {}
    for key, path in (("article", ARTICLE_53012_EDIT_PATH), ("inquiry_category", IC_MANAGE_PATH)):
        st = art.goto_bare(path)
        page.wait_for_timeout(2000)  # let a late portlet render before reading
        out[key] = {"status": st, "fields": art.fields_rendered(),
                    "object_fields": page.locator('[name*="ObjectField_"]').count(),
                    "values_exposed": "info@qcci.org" in page.locator("body").inner_text(),
                    "no_role_message": art.no_role_message_shown()}
    _attach("site member", out)
    for key, v in out.items():
        assert not any(v["fields"].values()) and v["object_fields"] == 0, f"{key}: form rendered for a site member"
        assert not v["values_exposed"], f"{key}: field values exposed"


@allure.feature("Contact Us Section — access")
@allure.title("A Public Visitor cannot reach the CMS Contact Us Section Management by forced browsing (ADO-136486)")
@COMMON
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.tc_136486
@ANON_PAGE
def test_public_visitor_forced_browsing_denied_136486(page):
    art = ContactUsSectionArticlePage(page)
    out = {}
    for key, path in (("article", ARTICLE_53012_EDIT_PATH), ("inquiry_category", IC_MANAGE_PATH)):
        st = art.goto_bare(path)
        page.wait_for_timeout(2000)  # let a late portlet render before reading
        out[key] = {"status": st, "url": page.url, "fields": art.fields_rendered(),
                    "object_fields": page.locator('[name*="ObjectField_"]').count(),
                    "values_exposed": "info@qcci.org" in page.locator("body").inner_text(),
                    "login_form": CmsLoginPage(page).login_form_visible()}
    _attach("anonymous", out)
    for key, v in out.items():
        assert not any(v["fields"].values()) and v["object_fields"] == 0, f"{key}: form rendered for a visitor"
        assert not v["values_exposed"], f"{key}: values exposed"


@allure.feature("Contact Us Section — screens")
@allure.title("The CMS Contact Us Section Management screen renders all configuration fields (ADO-136480)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136480
@ANON_PAGE
def test_management_screen_renders_all_configuration_fields_136480(page):
    """Account: TEST_USER (the only account that can open the article — see
    136483). Read-only on 53012: nothing is typed or saved."""
    sign_in(page, None)
    art = ContactUsSectionArticlePage(page)
    art.open_article_53012()
    art._field("Section Heading").wait_for(timeout=60000)
    fields = art.fields_rendered()
    actions = art.form_actions()
    art.switch_content_locale("ar-SA")
    ar_fields = art.fields_rendered()
    page.screenshot(path="reports/manual-exec-129390-136480.png", full_page=True)
    art.goto_bare(IC_MANAGE_PATH)
    grid = page.locator("table tbody tr").count()
    unpublish = page.locator("[data-qc-oel-unpublish]").count()
    _attach("screen", {"fields_en": fields, "fields_ar": ar_fields, "actions": actions,
                       "inquiry_category_rows": grid, "inquiry_unpublish_actions": unpublish})
    assert all(fields.values()), f"missing fields: {[k for k, v in fields.items() if not v]}"
    assert all(ar_fields.values()), "fields missing in the ar-SA translation"
    assert all(actions.values()), f"missing actions: {actions}"
    assert grid > 0, "Inquiry Category grid empty"


@allure.feature("Contact Us Section — screens")
@allure.title("The Contact Us Section Management screen renders correctly in Arabic in the CMS (ADO-136551)")
@COMMON
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_136551
@ANON_PAGE
def test_management_screen_renders_in_arabic_136551(page):
    """Account: TEST_USER. The CMS UI language is switched for this request by
    the /ar/ path prefix, then reset to en_US. Arabic is typed into a field of
    a NEW, never-saved form (nothing is written)."""
    sign_in(page, None)
    art = ContactUsSectionArticlePage(page)
    try:
        from cms.pages.home_contact_us.home_contact_us_admin_page import NEW_ARTICLE_PATH
        art.goto_bare(NEW_ARTICLE_PATH.replace("/en/", "/ar/", 1))
        art._field("Section Heading").wait_for(timeout=60000)
        data = page.evaluate("""() => ({dir: document.documentElement.dir, lang: document.documentElement.lang,
            buttons: [...document.querySelectorAll('button')].filter(b => b.offsetWidth).map(b => b.innerText.trim()).filter(Boolean).slice(0, 12),
            labels: [...document.querySelectorAll('label')].filter(l => l.offsetWidth).map(l => l.innerText.trim()).filter(Boolean).slice(0, 20)})""")
        art.fill("Section Heading", "قسم تواصل معنا")
        typed = art.value("Section Heading")
        field_dir = art._field("Section Heading").evaluate("el => getComputedStyle(el).direction")
        page.screenshot(path="reports/manual-exec-129390-136551.png", full_page=True)
    finally:
        page.goto(control_panel_url("/c/portal/update_language?languageId=en_US"), wait_until="domcontentloaded")
    data.update({"typed": typed, "field_direction": field_dir})
    _attach("Arabic CMS", data)
    assert data["dir"] == "rtl", f"CMS UI not RTL: {data['dir']}"
    assert typed == "قسم تواصل معنا"
    arabic_labels = [t for t in data["labels"] if any("؀" <= ch <= "ۿ" for ch in t)]
    assert arabic_labels, f"no Arabic field labels / help text: {data['labels']}"

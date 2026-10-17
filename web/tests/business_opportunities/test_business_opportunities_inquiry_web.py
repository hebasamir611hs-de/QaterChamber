"""
web/tests/business_opportunities/test_business_opportunities_inquiry_web.py
- Web cases for PBI 130697 (INVEST - Business Opportunities): the
"Express Your Interest" inquiry modal opened from an opportunity's Detail page.

Owner: Agent W2 (Phase-3 web run, 2026-10-12). Azure plan 137724, suite 140361.
Scripted (25): 143216, 143219, 143228, 143239, 143258, 143259, 143283, 143289,
143309-143313, 143319-143330. 143230 is Manual (a solved captcha) and has no
script; reCAPTCHA is switched off on qcdev (/o/qc-recaptcha-api/config
enabled=false), so the three captcha cases report exactly that.

LIVE FACTS (qcdev, unauthenticated context, 2026-10-12)
  host records   QC-BIZOPP-130697-04 "Digital Banking Platform" (Published,
                 Active) for the modal; QC-BIZOPP-130697-01 (Technology) is
                 what the Sector=Technology filter returns (end-to-end case);
                 QC-BIZOPP-130697-05 "Agricultural Technology Hub" (Archived).
                 All are real records and are only read, never edited.
  endpoint       POST /o/qc-business-opportunities-api/inquiries (multipart):
                 200 {status: success, id, referenceNumber QC-BO-INQ-<date>-<code>,
                 entryStatus: pending}; 400 {status: invalid, errors{field: code}};
                 409 {status: archived}.
  stored row     manage-opportunity-inquiry (view only). The View modal (as
                 TEST_USER) lists every stored field; localized fields show
                 "en_US: ..." / "ar_SA: ..." lines.

Test data: every submission uses the QCTEST-130697-W2- prefix on name and
company and qctest.130697.w2@example.com, instead of the cases' sample person
(user's standing rule). Three real submissions per full run (one EN, one AR,
one end-to-end); every row they create is deleted at module teardown with the
guarded delete (exact name + id + ERC, TEST_USER) from
cms/pages/business_opportunities/opportunity_submissions_admin_page.py.

Design source: Figma J3e1thav8NIu6a3XhC6Wcl, the unnamed inquiry-modal frames on
page 3963:142821 (found by content; the 24 PBI-linked frames contain no modal):
  4964:223124 EN light desktop (648 wide)   4964:229919 EN dark desktop
  4964:223156 AR light desktop              4964:229951 AR dark desktop
  4964:223141 EN light mobile (350 wide)    4964:229936 EN dark mobile
  4964:223173 AR light mobile               4964:229968 AR dark mobile
The PBI has no success-screen frame; its success copy comes from the PBI text.
"""

from __future__ import annotations

import json
import os
import re
import warnings
from pathlib import Path
from unittest import mock

import allure
import pytest

import cms.pages.business_opportunities.opportunity_submissions_admin_page as review_admin
from core.web.browser import new_context
from web.pages.business_opportunities.detail_page import BusinessOpportunityDetailPage, INQUIRY_FIELD_KEYS
from web.pages.business_opportunities.listing_page import BusinessOpportunitiesListingPage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

EPIC = "Business Opportunities"
FEATURE = "Express Your Interest - Inquiry Modal"

HOST_ERC = "QC-BIZOPP-130697-04"       # real Published + Active record (read only)
ARCHIVED_ERC = "QC-BIZOPP-130697-05"   # real Published + Archived record (read only)
W2_PREFIX = "QCTEST-130697-W2-"
W2_EMAIL = "qctest.130697.w2@example.com"
PROTECTED_INQUIRY_ID = "633573"        # a real inquiry: never touched

EVIDENCE = Path(__file__).resolve().parents[3] / "reports" / "evidence" / "130697_web_w2"

PUBLIC = {"auth": False}
PUBLIC_DESKTOP = {"auth": False, "viewport": (1920, 1080)}

MANDATORY = ("your_name", "email", "mobile", "company", "message")
REQUIRED_MSG = {"en": "This field is required.", "ar": "هذا الحقل مطلوب."}
EMAIL_MSG = {"en": "Enter a valid email address.", "ar": "أدخل بريداً إلكترونياً صحيحاً."}
MOBILE_MSG_CASE = "Enter a valid mobile number"

# PBI "Success Screen - Inquiry (EN / AR)", {{reference_number}} substituted.
PBI_SUCCESS = {
    "en": ("Thank you for your interest. Your inquiry has been received successfully. Your Reference Number is "
           "{ref}. The Qatar Chamber team will review and follow up with you."),
    "ar": ("شكرًا لاهتمامك. تم استلام استفسارك بنجاح. رقم مرجعك هو {ref}. سيتولى فريق غرفة قطر مراجعة استفسارك "
           "والتواصل معك."),
}
REF_RE = re.compile(r"^QC-BO-INQ-\d{8}-[A-Z0-9]+$")

# ---- Figma expectations (exact copy / colours / type; layout +-2 px) ----------
FIGMA_COPY = {
    "en": {"eyebrow": "Contact & Inquire", "title": "Express Your Interest",
           "lead": ("Fill out the form below to send an inquiry to the opportunity owner. Your information will be "
                    "kept confidential and routed securely."),
           "labels": {"your_name": "Your Name", "email": "Email Address", "mobile": "Mobile Number",
                      "company": "Company", "inquiry_type": "Inquiry Type", "message": "Message"},
           "cancel": "Cancel", "submit": "Submit Inquiry",
           "ph_mobile": "Enter Mobile Number", "ph_type": "Select",
           "ph_message": "Describe your interest, questions, or proposal..."},
    "ar": {"eyebrow": "تواصل واستفسر", "title": "أبدِ اهتمامك",
           "lead": "املأ النموذج أدناه لإرسال استفسار إلى مالك الفرصة. سيتم الحفاظ على سرية معلوماتك وتوجيهها بشكل آمن.",
           "labels": {"your_name": "اسمك", "email": "البريد الإلكتروني", "mobile": "رقم الموبايل",
                      "company": "الشركة", "inquiry_type": "نوع الاستفسار", "message": "الرسالة"},
           "cancel": "إلغاء", "submit": "إرسال الاستفسار",
           "ph_mobile": "ادخل رقم الموبايل", "ph_type": "اختر", "ph_message": "صِف اهتمامك أو أسئلتك أو مقترحك..."},
}
FIGMA_COLOURS = {
    "light": {"panel_bg": "#FFFFFF", "eyebrow": "#911731", "title": "#1D1D1B", "lead": "#7C7B7B",
              "label": "#1D1D1B", "req": "#E11D48", "submit_bg": "#911731"},
    "dark": {"panel_bg": "#1D1D1B", "eyebrow": "#C44561", "title": "#FFFFFF", "lead": "#D0D0D0",
             "label": "#FFFFFF", "req": "#FDA4AF", "submit_bg": "#C44561"},
}
FIGMA_FRAME = {("en", "light", "desktop"): "4964:223124", ("en", "dark", "desktop"): "4964:229919",
               ("ar", "light", "desktop"): "4964:223156", ("ar", "dark", "desktop"): "4964:229951",
               ("en", "light", "mobile"): "4964:223141", ("en", "dark", "mobile"): "4964:229936",
               ("ar", "light", "mobile"): "4964:223173", ("ar", "dark", "mobile"): "4964:229968"}

VIEW_LABELS = ("Your Name", "Email Address", "Mobile Number", "Company", "Inquiry Type", "Message",
               "Inquiry Status", "Reference Number", "Opportunity Inquiries ERC", "Id", "External Reference Code")

# Rows created by this module: [{"id", "name"}]; deleted at module teardown.
CREATED: list[dict] = []


def _sev(priority: int):
    return {1: allure.severity_level.BLOCKER, 2: allure.severity_level.CRITICAL,
            3: allure.severity_level.NORMAL, 4: allure.severity_level.MINOR}[priority]


def _hex_rgb(hex_colour: str) -> str:
    h = hex_colour.lstrip("#")
    return f"rgb({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})"


def _evidence(page, name: str) -> str:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = str(EVIDENCE / (re.sub(r"[^\w.-]+", "_", name)[:120] + ".png"))
    png = page.screenshot(path=path)
    allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    return path


def _attach_json(name: str, data) -> None:
    allure.attach(json.dumps(data, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _register(entry_id: str, name: str) -> None:
    if not entry_id or entry_id == PROTECTED_INQUIRY_ID or not name.startswith(W2_PREFIX):
        return
    if any(r["id"] == entry_id for r in CREATED):
        return
    CREATED.append({"id": entry_id, "name": name})
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / "w2_created_rows.json").write_text(json.dumps(CREATED, ensure_ascii=False, indent=1),
                                                    encoding="utf-8")


def _open_modal(page, locale: str = "en", erc: str = HOST_ERC) -> BusinessOpportunityDetailPage:
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(erc, locale=locale)
    dp.open_inquiry_modal()
    return dp


def _valid_values(**overrides) -> dict:
    values = {"your_name": f"{W2_PREFIX}Ahmed Al-Sayed", "email": W2_EMAIL, "mobile": "+974 5512 3456",
              "company": f"{W2_PREFIX}Al-Sayed Trading LLC",
              "message": f"{W2_PREFIX}Interested in co-investment opportunities."}
    values.update(overrides)
    return values


def _parse_view(lines: list[str]) -> dict:
    """{label: value} from a View-modal line list; localized fields keep en_US / ar_SA."""
    out: dict = {}
    for i, line in enumerate(lines):
        if line not in VIEW_LABELS or line in out:
            continue
        nxt = lines[i + 1: i + 3]
        loc = {v.split(": ", 1)[0]: v.split(": ", 1)[1] for v in nxt if re.match(r"^(en_US|ar_SA): ", v)}
        out[line] = loc if loc else (nxt[0] if nxt else "")
    return out


def _value(stored: dict, label: str) -> str:
    v = stored.get(label, "")
    return v.get("en_US", "") if isinstance(v, dict) else v


# ---- module fixtures: admin session, shared submissions, cleanup ---------------
@pytest.fixture(scope="module")
def review(browser):
    """TEST_USER session on manage-opportunity-inquiry (read + guarded delete only)."""
    ctx = new_context(browser, viewport=(1600, 1000), use_auth_state=False)
    adm = review_admin.OpportunityReviewAdminPage(ctx.new_page(), review_admin.INQUIRY_SLUG)
    state = {"adm": adm, "logged_in": False}

    def ensure():
        if not state["logged_in"]:
            # qcdev is slow under the 4-agent load: the login can time out and read "unknown"; retry.
            def signed_in() -> bool:
                try:
                    return bool(adm.signed_in_user()[0])
                except Exception:  # noqa: BLE001 - page mid-navigation
                    return False

            outcomes = []
            for _ in range(3):
                outcomes.append(adm.login_as_role(review_admin.ROLE_ADMIN))
                if outcomes[-1] == "ok" or signed_in():
                    break
            assert outcomes[-1] == "ok" or signed_in(), f"TEST_USER login failed: {outcomes}"
            state["logged_in"] = True
        return adm

    yield ensure
    try:
        ctx.close()
    except Exception:  # noqa: BLE001
        pass


def _stored(review, entry_id: str) -> dict:
    adm = review()
    adm.open_manage(review_admin.INQUIRY_SLUG)
    view = adm.view_entry(entry_id)
    return _parse_view(view["lines"])


def _list_ids(review) -> set:
    adm = review()
    adm.open_manage(review_admin.INQUIRY_SLUG)
    return set(adm.entry_ids())


@pytest.fixture(scope="module", autouse=True)
def _w2_cleanup(review):
    yield
    if not CREATED:
        return
    adm = review()
    results = []
    with mock.patch.object(review_admin, "QCTEST_PREFIX", W2_PREFIX):
        for row in list(CREATED):
            if row["id"] == PROTECTED_INQUIRY_ID:
                continue
            try:
                outcome = adm.guarded_delete(review_admin.INQUIRY_SLUG, row["id"], row["name"])
            except Exception as exc:  # noqa: BLE001 - reported, never retried blindly
                outcome = f"error: {exc}"
            results.append({**row, "outcome": outcome})
    (EVIDENCE / "w2_cleanup.json").write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding="utf-8")
    left = [r for r in results if r["outcome"] != "deleted"]
    if left:
        warnings.warn(f"W2 QCTEST inquiry rows NOT deleted: {left}")


def _submit_shared(browser, review, locale: str, values: dict, tag: str, double_click: bool = False) -> dict:
    before = _list_ids(review)
    ctx = new_context(browser, viewport=(1440, 900), use_auth_state=False)
    page = ctx.new_page()
    try:
        dp = _open_modal(page, locale)
        dp.fill_inquiry_form(values)
        result = dp.submit_inquiry_and_capture(double_click=double_click, hold_ms=1)
        result["texts"] = dp.inquiry_success_texts() if result["success"] else {}
        result["screenshot"] = _evidence(page, f"{tag}_after_submit")
        result["modal_open_after"] = dp.is_inquiry_modal_open()
    finally:
        ctx.close()
    entry_id = str(result["body"].get("id", ""))
    _register(entry_id, values["your_name"])
    new_ids = sorted(_list_ids(review) - before - {PROTECTED_INQUIRY_ID})
    same_name = []
    for nid in new_ids:
        stored = _stored(review, nid)
        if _value(stored, "Your Name") == values["your_name"]:
            same_name.append(nid)
            _register(nid, values["your_name"])
    result.update({"entry_id": entry_id, "new_ids_same_name": same_name,
                   "stored": _stored(review, entry_id) if entry_id else {}})
    (EVIDENCE / f"{tag}.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, default=str),
                                          encoding="utf-8")
    return result


@pytest.fixture(scope="module")
def en_inquiry(browser, review):
    """ONE real EN submission (double-clicked) with the 200-character name and
    Inquiry Type = Investment Inquiry; read back from the CMS."""
    name = (f"{W2_PREFIX}Ahmed Al-Sayed " + "x" * 200)[:200]
    values = _valid_values(your_name=name, inquiry_type="Investment Inquiry")
    result = _submit_shared(browser, review, "en", values, "w2_en_submission", double_click=True)
    result["values"] = values
    return result


@pytest.fixture(scope="module")
def ar_inquiry(browser, review):
    """ONE real submission from the Arabic UI: Inquiry Type left unselected,
    200-character Company, 2000-character Message."""
    company = (f"{W2_PREFIX}Al-Sayed Trading LLC " + "c" * 200)[:200]
    message = (f"{W2_PREFIX}Interested in co-investment opportunities. " + "m" * 2000)[:2000]
    values = _valid_values(your_name=f"{W2_PREFIX}AR-Ahmed Al-Sayed", company=company, message=message)
    result = _submit_shared(browser, review, "ar", values, "w2_ar_submission")
    result["values"] = values
    return result


def _common(fn):
    """Shared epic/feature + surface/scope markers."""
    for deco in (allure.epic(EPIC), allure.feature(FEATURE), allure.label("pbi", "130697"),
                 pytest.mark.web, pytest.mark.invest, pytest.mark.pbi_130697):
        fn = deco(fn)
    return fn


# ===========================================================================
# P1
# ===========================================================================
@_common
@allure.story("CAPTCHA")
@allure.severity(_sev(1))
@allure.title("Captcha is enforced on the Express Your Interest modal")
@pytest.mark.functional_low
@pytest.mark.tc_143228
@pytest.mark.traceability("143228")
@allure.label("testcase", "143228")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_captcha_enforced(page):
    dp = _open_modal(page)
    state = dp.inquiry_captcha_state()
    _attach_json("captcha state", state)
    _evidence(page, "143228_modal_captcha_area")
    if not state["visible"]:
        pytest.skip("BLOCKED: reCAPTCHA is disabled on qcdev (/o/qc-recaptcha-api/config enabled=false); "
                    f"the modal renders no captcha control ([data-qc-recaptcha] hidden, {state['iframes']} iframes)")
    dp.fill_inquiry_form(_valid_values())
    dp.click_submit_inquiry_button()
    assert not dp.is_inquiry_success_visible()


@_common
@allure.story("End to end")
@allure.severity(_sev(1))
@allure.title("A Public Visitor can browse, filter, view an opportunity's details and submit an inquiry end to end")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.tc_143283
@pytest.mark.traceability("143283")
@allure.label("testcase", "143283")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_end_to_end_browse_filter_detail_and_submit(page, review):
    lp = BusinessOpportunitiesListingPage(page)
    lp.open_listing(locale="en")
    lp.select_filter("sector", "Technology")
    lp.apply_filters()
    page.wait_for_timeout(2500)
    tags = [t.split("\n")[0].strip() for t in page.locator(lp.CARD_TAG).all_inner_texts()]
    titles = lp.card_titles()
    assert titles, "Sector = Technology returned no Active opportunity"
    assert all(t == "Technology" for t in tags), f"non-Technology cards after the filter: {tags}"
    page.locator(lp.CARD, has_text=titles[0]).first.click()
    dp = BusinessOpportunityDetailPage(page)
    page.locator(dp.HEADER_TITLE).wait_for(state="visible", timeout=30000)
    assert dp.title_text() == titles[0]
    dp.open_inquiry_modal()
    values = _valid_values(your_name=f"{W2_PREFIX}E2E-Ahmed Al-Sayed", company=f"{W2_PREFIX}Al-Sayed Trading Co.")
    dp.fill_inquiry_form(values)
    assert not any(dp.inquiry_field_errors().values())
    result = dp.submit_inquiry_and_capture()
    _evidence(page, "143283_success")
    entry_id = str(result["body"].get("id", ""))
    _register(entry_id, values["your_name"])
    _attach_json("submit result", result)
    assert result["http"] == 200 and result["success"], result
    assert REF_RE.match(dp.inquiry_success_texts()["ref"])
    stored = _stored(review, entry_id)
    _attach_json("stored inquiry", stored)
    assert _value(stored, "Inquiry Status") == "Pending"
    assert _value(stored, "Your Name") == values["your_name"]
    assert _value(stored, "Email Address") == W2_EMAIL
    # The acknowledgement e-mail cannot be observed from here (no mailbox access); reported in the run notes.


@_common
@allure.story("Success screen")
@allure.severity(_sev(1))
@allure.title("Submitting a fully valid inquiry displays the bilingual success message with the generated reference number")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.tc_143311
@pytest.mark.traceability("143311")
@allure.label("testcase", "143311")
def test_inquiry_valid_submission_shows_bilingual_success_with_reference(en_inquiry, ar_inquiry):
    wording = {}
    for locale, res in (("en", en_inquiry), ("ar", ar_inquiry)):
        assert res["http"] == 200 and res["success"], f"{locale}: {res['http']} {res['body']} {res['error']}"
        ref = res["texts"]["ref"]
        assert REF_RE.match(ref), f"{locale}: reference {ref!r}"
        assert ref == res["body"]["referenceNumber"] == _value(res["stored"], "Reference Number")
        expected = PBI_SUCCESS[locale].format(ref=ref)
        shown = f"{res['texts']['title']} {res['texts']['body']} {res['texts']['all']}"
        if expected not in shown:
            wording[locale] = {"expected (PBI)": expected, "actual": res["texts"]["all"]}
    assert en_inquiry["texts"]["ref"] != ar_inquiry["texts"]["ref"], "reference numbers are not unique"
    if wording:
        # Rule 4: behaviour correct (stored, unique reference shown) but copy differs -> Passed + Low wording bug.
        _attach_json("success copy differs from the PBI (wording finding)", wording)
        warnings.warn(f"143311 wording finding: {wording}")


# ===========================================================================
# P2
# ===========================================================================
@_common
@allure.story("Opening the modal")
@allure.severity(_sev(2))
@allure.title("Clicking the Submit Inquiry CTA on an Active opportunity opens the Express Your Interest modal")
@pytest.mark.functional_low
@pytest.mark.tc_143216
@pytest.mark.traceability("143216")
@allure.label("testcase", "143216")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_cta_opens_modal(page):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(HOST_ERC, locale="en")
    assert dp.is_submit_inquiry_cta_enabled(), "Submit Inquiry CTA not visible/enabled on an Active opportunity"
    assert not dp.is_inquiry_modal_open()
    dp.open_inquiry_modal()
    _evidence(page, "143216_modal_open")
    assert dp.is_inquiry_modal_open()
    assert dp.inquiry_dialog_attrs() == {"role": "dialog", "aria_modal": "true"}
    assert dp.visible_inquiry_field_keys() == list(INQUIRY_FIELD_KEYS)


@_common
@allure.story("Submission")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Inquiry with all fields valid submits the inquiry and disables the button during processing")
@pytest.mark.functional_low
@pytest.mark.tc_143219
@pytest.mark.traceability("143219")
@allure.label("testcase", "143219")
def test_inquiry_valid_submission_disables_button_and_shows_success(en_inquiry):
    _attach_json("EN submission", en_inquiry)
    assert en_inquiry["during"].get("disabled") is True, f"button state in flight: {en_inquiry['during']}"
    assert en_inquiry["http"] == 200 and en_inquiry["success"]
    assert en_inquiry["body"].get("entryStatus") == "pending"
    assert _value(en_inquiry["stored"], "Inquiry Status") == "Pending"


@_common
@allure.story("Submission")
@allure.severity(_sev(2))
@allure.title("Rapidly double-clicking Submit on the Inquiry modal does not create two duplicate inquiry records")
@pytest.mark.edge
@pytest.mark.tc_143239
@pytest.mark.traceability("143239")
@allure.label("testcase", "143239")
def test_inquiry_double_click_does_not_duplicate(en_inquiry):
    assert en_inquiry["http"] == 200 and en_inquiry["success"]
    assert en_inquiry["posts"] == 1, f"{en_inquiry['posts']} POSTs fired by the double-click"
    assert en_inquiry["new_ids_same_name"] == [en_inquiry["entry_id"]], \
        f"rows stored for the double-clicked submission: {en_inquiry['new_ids_same_name']}"


@_common
@allure.story("Archived state")
@allure.severity(_sev(2))
@allure.title("Submitting an inquiry on an Archived opportunity is blocked with the CTA hidden or disabled")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_143289
@pytest.mark.traceability("143289")
@allure.label("testcase", "143289")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_blocked_on_archived_opportunity(page, review):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(ARCHIVED_ERC, locale="en")
    assert dp.archived_note_text(), "archived note not shown"
    assert not dp.is_submit_inquiry_cta_enabled(), "Submit Inquiry CTA is visible/enabled on an Archived record"
    before = _list_ids(review)
    dp.force_open_inquiry_modal_via_script()
    opened = dp.is_inquiry_modal_open()
    outcome = None
    if opened:
        _evidence(page, "143289_modal_opened_by_script_on_archived")
        name = f"{W2_PREFIX}Archived-Probe"
        dp.fill_inquiry_form(_valid_values(your_name=name))
        outcome = dp.submit_inquiry_and_capture()
        _register(str(outcome["body"].get("id", "")), name)
        _attach_json("forced submission outcome", outcome)
    new_ids = _list_ids(review) - before - {PROTECTED_INQUIRY_ID}
    for nid in new_ids:
        if _value(_stored(review, nid), "Opportunity Inquiries ERC") == ARCHIVED_ERC:
            pytest.fail(f"an inquiry was stored for the Archived opportunity: {nid}")
    if outcome:
        assert outcome["http"] == 409 and not outcome["success"], outcome
    assert not opened, ("the hidden CTA still carries its click handler: firing it opens the inquiry modal on an "
                        "Archived opportunity (the server then refuses the POST with 409 'archived')")


@_common
@allure.story("Validation")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Inquiry with all mandatory fields empty shows inline validation errors")
@pytest.mark.functional_low
@pytest.mark.tc_143309
@pytest.mark.traceability("143309")
@allure.label("testcase", "143309")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_all_mandatory_fields_empty_shows_errors(page):
    dp = _open_modal(page)
    posts = []
    page.on("request", lambda r: posts.append(r.url) if dp.INQUIRY_API_PATH in r.url else None)
    dp.click_submit_inquiry_button()
    page.wait_for_timeout(800)
    errors = dp.inquiry_field_errors()
    _evidence(page, "143309_empty_submit")
    _attach_json("inline errors", errors)
    assert not posts and not dp.is_inquiry_success_visible()
    for key in MANDATORY:
        assert errors[key] == REQUIRED_MSG["en"], f"{key}: {errors[key]!r}"
        assert dp.is_inquiry_field_invalid(key)
    assert errors["inquiry_type"] == ""


@_common
@allure.story("Validation")
@allure.severity(_sev(2))
@allure.title("Clicking Submit Inquiry with an invalid email and mobile format shows format validation errors")
@pytest.mark.functional_low
@pytest.mark.tc_143310
@pytest.mark.traceability("143310")
@allure.label("testcase", "143310")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_invalid_email_and_mobile_format_shows_errors(page):
    dp = _open_modal(page)
    dp.fill_inquiry_form(_valid_values(email="ahmed.alsayedexample.com", mobile="12abc45"))
    assert dp.inquiry_field_value("email") == "ahmed.alsayedexample.com"
    assert dp.inquiry_field_value("mobile") == "12abc45"
    dp.click_submit_inquiry_button()
    page.wait_for_timeout(800)
    errors = dp.inquiry_field_errors()
    _evidence(page, "143310_invalid_formats")
    _attach_json("inline errors", errors)
    assert not dp.is_inquiry_success_visible()
    assert errors["email"] == EMAIL_MSG["en"], errors
    assert MOBILE_MSG_CASE.lower() in errors["mobile"].lower(), \
        f"no mobile-format error under Mobile Number: {errors['mobile']!r}"


@_common
@allure.story("CAPTCHA")
@allure.severity(_sev(2))
@allure.title("Submitting the inquiry form without solving the Captcha is blocked")
@pytest.mark.functional_low
@pytest.mark.tc_143312
@pytest.mark.traceability("143312")
@allure.label("testcase", "143312")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_unsolved_captcha_blocks_submission(page):
    dp = _open_modal(page)
    state = dp.inquiry_captcha_state()
    _attach_json("captcha state", state)
    if not state["visible"]:
        pytest.skip("BLOCKED: reCAPTCHA is disabled on qcdev (/o/qc-recaptcha-api/config enabled=false); "
                    "no captcha widget is rendered, so 'unsolved captcha' cannot be reached")
    dp.fill_inquiry_form(_valid_values())
    dp.click_submit_inquiry_button()
    assert "Please complete the Captcha verification" in dp.inquiry_generic_error_text()
    assert dp.is_inquiry_modal_open()


@_common
@allure.story("Archived state")
@allure.severity(_sev(2))
@allure.title("The Submit Inquiry CTA is hidden or disabled on an Archived opportunity's detail page")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_143313
@pytest.mark.traceability("143313")
@allure.label("testcase", "143313")
@pytest.mark.parametrize("locale", ["en", "ar"])
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_cta_hidden_or_disabled_on_archived(page, locale):
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(ARCHIVED_ERC, locale=locale)
    _evidence(page, f"143313_archived_{locale}")
    assert page.locator(dp.SECTION).count() >= 3, "archived detail page did not render its sections"
    assert not dp.is_submit_inquiry_cta_enabled()
    assert dp.archived_note_text()


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Your Name accepts a valid value up to the 200-character maximum")
@pytest.mark.functional_low
@pytest.mark.tc_143319
@pytest.mark.traceability("143319")
@allure.label("testcase", "143319")
def test_inquiry_your_name_accepts_200_char_boundary(en_inquiry):
    name = en_inquiry["values"]["your_name"]
    assert len(name) == 200
    assert en_inquiry["success"], en_inquiry["error"]
    assert _value(en_inquiry["stored"], "Your Name") == name


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Your Name rejects an empty or whitespace-only value on submit")
@pytest.mark.functional_low
@pytest.mark.tc_143320
@pytest.mark.traceability("143320")
@allure.label("testcase", "143320")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_your_name_rejects_empty_whitespace_and_over_max(page):
    dp = _open_modal(page)
    assert dp.inquiry_field_meta("your_name")["maxlength"] == 200
    dp.fill_inquiry_form(_valid_values(your_name=""))
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("your_name") == REQUIRED_MSG["en"]
    dp.fill_inquiry_field("your_name", "   ")
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("your_name") == REQUIRED_MSG["en"]
    dp.type_inquiry_field("your_name", "A" * 201)
    assert len(dp.inquiry_field_value("your_name")) == 200, "typing past 200 characters was not stopped"
    dp.fill_inquiry_field("your_name", "B" * 201)  # paste-like set
    assert len(dp.inquiry_field_value("your_name")) == 200
    _evidence(page, "143320_name_max")
    assert not dp.is_inquiry_success_visible()


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Email Address accepts a valid email and is stored exactly as entered")
@pytest.mark.functional_low
@pytest.mark.tc_143321
@pytest.mark.traceability("143321")
@allure.label("testcase", "143321")
def test_inquiry_email_accepts_valid_value(en_inquiry):
    assert en_inquiry["success"], en_inquiry["error"]
    assert _value(en_inquiry["stored"], "Email Address") == W2_EMAIL


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Email Address rejects an empty value and a malformed value")
@pytest.mark.functional_low
@pytest.mark.tc_143322
@pytest.mark.traceability("143322")
@allure.label("testcase", "143322")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_email_rejects_empty_and_malformed(page):
    dp = _open_modal(page)
    dp.fill_inquiry_form(_valid_values(email=""))
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("email") == REQUIRED_MSG["en"]
    dp.fill_inquiry_field("email", "ahmed.alsayed@@example")
    dp.click_submit_inquiry_button()
    page.wait_for_timeout(500)
    _evidence(page, "143322_email_malformed")
    assert dp.inquiry_field_error_text("email") == EMAIL_MSG["en"]
    assert not dp.is_inquiry_success_visible()


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Mobile Number defaults to the +974 Qatar country code and accepts a valid international format")
@pytest.mark.functional_low
@pytest.mark.tc_143323
@pytest.mark.traceability("143323")
@allure.label("testcase", "143323")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_mobile_defaults_to_qatar_code_and_accepts_valid(page, en_inquiry):
    # Stored part comes from the shared EN submission (typed as '+974 5512 3456').
    assert en_inquiry["success"], en_inquiry["error"]
    stored_mobile = _value(en_inquiry["stored"], "Mobile Number")
    dp = _open_modal(page)
    prefix = dp.inquiry_mobile_prefix()
    meta = dp.inquiry_field_meta("mobile")
    _attach_json("mobile control", {"prefix": prefix, "meta": meta, "stored": stored_mobile})
    _evidence(page, "143323_mobile_default")
    assert stored_mobile == "+974 5512 3456"
    assert prefix["has974"] and prefix["graphics"] >= 1, \
        f"no default Qatar flag / '+974' in the Mobile Number control: {prefix}"


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Mobile Number rejects an empty value and a value with non-numeric characters")
@pytest.mark.functional_low
@pytest.mark.tc_143324
@pytest.mark.traceability("143324")
@allure.label("testcase", "143324")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_mobile_rejects_empty_and_non_numeric(page):
    dp = _open_modal(page)
    dp.fill_inquiry_form(_valid_values(mobile=""))
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("mobile") == REQUIRED_MSG["en"]
    dp.fill_inquiry_field("mobile", "55AB3456")
    dp.fill_inquiry_field("your_name", f"{W2_PREFIX}Mobile-Probe")
    # Live: there is no client-side format check, so this click reaches the server.
    posts = []
    page.on("request", lambda r: posts.append(r.url) if dp.INQUIRY_API_PATH in r.url and r.method == "POST" else None)
    server = None
    try:
        server = dp.submit_inquiry_and_capture()
        _register(str(server["body"].get("id", "")), f"{W2_PREFIX}Mobile-Probe")
    except Exception:  # noqa: BLE001 - no POST = the client blocked it, which is what the case wants
        pass
    client_error = "" if posts else dp.inquiry_field_error_text("mobile")
    errors = dp.inquiry_field_errors()
    _evidence(page, "143324_mobile_non_numeric")
    _attach_json("outcome", {"client_error_before_post": client_error, "server": server, "errors_after": errors})
    assert not dp.is_inquiry_success_visible(), "an inquiry with mobile '55AB3456' was accepted"
    assert MOBILE_MSG_CASE.lower() in errors["mobile"].lower(), \
        f"Mobile Number shows {errors['mobile']!r} (server: {server and server['body']}; banner: {dp.inquiry_generic_error_text()!r})"


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Company accepts a valid value up to the 200-character maximum")
@pytest.mark.functional_low
@pytest.mark.tc_143325
@pytest.mark.traceability("143325")
@allure.label("testcase", "143325")
def test_inquiry_company_accepts_200_char_boundary(en_inquiry, ar_inquiry):
    assert en_inquiry["success"] and ar_inquiry["success"]
    assert _value(en_inquiry["stored"], "Company") == en_inquiry["values"]["company"]
    company_200 = ar_inquiry["values"]["company"]
    assert len(company_200) == 200
    assert _value(ar_inquiry["stored"], "Company") == company_200


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Company rejects an empty value and a value exceeding 200 characters")
@pytest.mark.functional_low
@pytest.mark.tc_143326
@pytest.mark.traceability("143326")
@allure.label("testcase", "143326")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_company_rejects_empty_and_over_max(page):
    dp = _open_modal(page)
    assert dp.inquiry_field_meta("company")["maxlength"] == 200
    dp.fill_inquiry_form(_valid_values(company=""))
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("company") == REQUIRED_MSG["en"]
    dp.type_inquiry_field("company", "C" * 201)
    assert len(dp.inquiry_field_value("company")) == 200
    dp.fill_inquiry_field("company", "D" * 201)
    assert len(dp.inquiry_field_value("company")) == 200
    _evidence(page, "143326_company_max")
    assert not dp.is_inquiry_success_visible()


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Message accepts a valid value up to the 2000-character maximum")
@pytest.mark.functional_low
@pytest.mark.tc_143327
@pytest.mark.traceability("143327")
@allure.label("testcase", "143327")
def test_inquiry_message_accepts_2000_char_boundary(en_inquiry, ar_inquiry):
    assert en_inquiry["success"] and ar_inquiry["success"]
    assert _value(en_inquiry["stored"], "Message") == en_inquiry["values"]["message"]
    msg_2000 = ar_inquiry["values"]["message"]
    assert len(msg_2000) == 2000
    assert _value(ar_inquiry["stored"], "Message") == msg_2000


@_common
@allure.story("Field validation")
@allure.severity(_sev(2))
@allure.title("Message rejects an empty value and a value exceeding 2000 characters")
@pytest.mark.functional_low
@pytest.mark.tc_143328
@pytest.mark.traceability("143328")
@allure.label("testcase", "143328")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_message_rejects_empty_and_over_max(page):
    dp = _open_modal(page)
    assert dp.inquiry_field_meta("message")["maxlength"] == 2000
    dp.fill_inquiry_form(_valid_values(message=""))
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("message") == REQUIRED_MSG["en"]
    dp.fill_inquiry_field("message", "   ")
    dp.click_submit_inquiry_button()
    assert dp.inquiry_field_error_text("message") == REQUIRED_MSG["en"]
    dp.fill_inquiry_field("message", "M" * 2001)
    assert len(dp.inquiry_field_value("message")) == 2000
    _evidence(page, "143328_message_max")
    assert not dp.is_inquiry_success_visible()


# ===========================================================================
# P3
# ===========================================================================
def _figma_check(dp: BusinessOpportunityDetailPage, locale: str, theme: str, device: str) -> list:
    """Every difference between the open modal and its Figma frame."""
    copy, colours = FIGMA_COPY[locale], FIGMA_COLOURS[theme]
    lay = dp.inquiry_layout()
    head = dp.inquiry_header_texts()
    labels = dp.inquiry_field_labels()
    out = []

    def diff(what, expected, actual):
        if expected != actual:
            out.append(f"{what}: Figma {expected!r} vs live {actual!r}")

    diff("eyebrow copy (rendered)", copy["eyebrow"], head["eyebrow"])
    diff("title copy", copy["title"], head["title"])
    diff("lead copy", copy["lead"], head["lead"])
    for key, expected in copy["labels"].items():
        diff(f"label {key}", expected, labels[key])
    diff("cancel button copy", copy["cancel"], dp.page.locator(dp.INQUIRY_CANCEL_BUTTON).inner_text().strip())
    diff("submit button copy", copy["submit"], dp.page.locator(dp.INQUIRY_SUBMIT_BUTTON).inner_text().strip())
    diff("mobile placeholder", copy["ph_mobile"], dp.inquiry_field_meta("mobile")["placeholder"])
    diff("message placeholder", copy["ph_message"], dp.inquiry_field_meta("message")["placeholder"])
    diff("inquiry type placeholder", copy["ph_type"], dp.selected_inquiry_type_label())
    diff("'(Optional)' marker next to Inquiry Type (absent in Figma)", 0,
         dp.page.locator(dp.INQUIRY_OPTIONAL_MARK).count())
    prefix = dp.inquiry_mobile_prefix()
    diff("mobile flag + '+974' prefix shown", True, bool(prefix["has974"] and prefix["graphics"]))
    diff("header icon tile (44x44) shown", True, lay["head_icons"] >= 2)
    diff("submit arrow icon shown", True, lay["submit_icon"])

    diff("panel background", _hex_rgb(colours["panel_bg"]), lay["panel"]["bg"])
    diff("eyebrow colour", _hex_rgb(colours["eyebrow"]), lay["eyebrow"]["color"])
    diff("eyebrow text-transform", "none", lay["eyebrow"]["transform"])
    diff("eyebrow font", ("Cairo", "12px", "400", "18px"),
         (lay["eyebrow"]["ff"], lay["eyebrow"]["fs"], lay["eyebrow"]["fw"], lay["eyebrow"]["lh"]))
    diff("title colour", _hex_rgb(colours["title"]), lay["title"]["color"])
    diff("title font", ("Cairo", "24px", "600", "32px"),
         (lay["title"]["ff"], lay["title"]["fs"], lay["title"]["fw"], lay["title"]["lh"]))
    diff("lead colour", _hex_rgb(colours["lead"]), lay["lead"]["color"])
    diff("lead font", ("Cairo", "14px", "400", "22px"),
         (lay["lead"]["ff"], lay["lead"]["fs"], lay["lead"]["fw"], lay["lead"]["lh"]))
    diff("label colour", _hex_rgb(colours["label"]), lay["label"]["color"])
    diff("label font", ("Cairo", "14px", "600", "22px"),
         (lay["label"]["ff"], lay["label"]["fs"], lay["label"]["fw"], lay["label"]["lh"]))
    diff("required-asterisk colour", _hex_rgb(colours["req"]), lay["req"]["color"])
    diff("submit background", _hex_rgb(colours["submit_bg"]), lay["submit"]["bg"])
    diff("submit font", ("16px", "600", "24px"), (lay["submit"]["fs"], lay["submit"]["fw"], lay["submit"]["lh"]))
    diff("submit padding", "12px 18px", lay["submit"]["padding"])
    diff("cancel padding", "12px 18px", lay["cancel"]["padding"])
    if abs(lay["submit"]["h"] - 48) > 2:
        out.append(f"submit height: Figma 48 vs live {lay['submit']['h']}")
    diff("panel radius", "16px", lay["panel"]["radius"])
    diff("close button size", (24, 24), (round(lay["close"]["w"]), round(lay["close"]["h"])))
    for name, box in lay["inputs"].items():
        if name != "message" and abs(box["h"] - 44) > 2:
            out.append(f"input {name} height: Figma 44 vs live {box['h']}")
    if abs(lay["inputs"]["message"]["h"] - 132) > 2:
        out.append(f"message box height: Figma 132 vs live {lay['inputs']['message']['h']}")
    width_type, width_msg = lay["inputs"]["inquiryType"]["w"], lay["inputs"]["message"]["w"]
    if abs(width_type - width_msg) > 2:
        out.append(f"Inquiry Type width: Figma full row ({width_msg}) vs live {width_type}")
    if device == "desktop":
        if abs(lay["panel"]["w"] - 648) > 2:
            out.append(f"panel width: Figma 648 vs live {lay['panel']['w']}")
        diff("panel padding", "40px", lay["panel"]["padding"])
    else:
        if abs(lay["panel"]["w"] - 350) > 2:
            out.append(f"panel width (mobile card): Figma 350 vs live {lay['panel']['w']}")
        diff("panel padding (mobile)", "24px 20px", lay["panel"]["padding"])
        if abs(lay["cancel"]["y"] - lay["submit"]["y"]) > 2:
            out.append(f"mobile buttons: Figma one row (Cancel + Submit) vs live stacked "
                       f"(submit y={lay['submit']['y']}, cancel y={lay['cancel']['y']})")
    if locale == "ar":
        diff("panel direction", "rtl", lay["panel"]["dir"])
        diff("mobile input direction (LTR digits)", "ltr", dp.inquiry_field_meta("mobile")["dir"])
        name_box, email_box = lay["inputs"]["yourName"], lay["inputs"]["emailAddress"]
        if device == "desktop" and not name_box["x"] > email_box["x"]:
            out.append("AR: Your Name is not the right-hand field of the first row")
        if lay["submit"]["x"] > lay["cancel"]["x"]:
            out.append("AR: Submit is not on the left of Cancel (Figma RTL order)")
    return out


LAYOUT_PARAMS = [
    pytest.param({"auth": False, "viewport": (1920, 1080)}, "light", "desktop", id="desktop-light"),
    pytest.param({"auth": False, "viewport": (1920, 1080)}, "dark", "desktop", id="desktop-dark"),
    pytest.param({"auth": False, "viewport": (390, 844)}, "light", "mobile", id="mobile-light"),
    pytest.param({"auth": False, "viewport": (390, 844)}, "dark", "mobile", id="mobile-dark"),
]


def _render_modal(page, locale: str, theme: str) -> BusinessOpportunityDetailPage:
    dp = BusinessOpportunityDetailPage(page)
    dp.open_detail(HOST_ERC, locale=locale)
    page.wait_for_function("() => document.fonts.status === 'loaded'", timeout=15000)
    if theme == "dark":
        AccessibilityToolsComponent(page).enable_dark_mode()
        page.wait_for_function("() => document.getAnimations().every((a) => a.playState !== 'running')",
                               timeout=10000)
    dp.open_inquiry_modal()
    return dp


@_common
@allure.story("Layout")
@allure.severity(_sev(3))
@allure.title("The Express Your Interest inquiry modal renders all fields and element states correctly")
@pytest.mark.ui
@pytest.mark.tc_143258
@pytest.mark.traceability("143258")
@allure.label("testcase", "143258")
@pytest.mark.parametrize("page,theme,device", LAYOUT_PARAMS, indirect=["page"])
def test_inquiry_modal_renders_every_field(page, theme, device):
    dp = _render_modal(page, "en", theme)
    frame = FIGMA_FRAME[("en", theme, device)]
    dp.inquiry_panel_screenshot(str(EVIDENCE / f"143258_live_en_{theme}_{device}.png"))
    _evidence(page, f"143258_page_en_{theme}_{device}")
    # Case steps.
    assert dp.is_inquiry_modal_open() and dp.inquiry_dialog_attrs()["role"] == "dialog"
    assert page.locator(dp.INQUIRY_CLOSE_BUTTON).is_visible()
    assert dp.visible_inquiry_field_keys() == list(INQUIRY_FIELD_KEYS)
    submit = page.locator(dp.INQUIRY_SUBMIT_BUTTON)
    assert submit.is_visible() and submit.is_enabled()
    captcha = dp.inquiry_captcha_state()
    # Figma (frame named in the evidence).
    findings = _figma_check(dp, "en", theme, device)
    if not captcha["visible"]:
        findings.append("captcha control not rendered (reCAPTCHA disabled on qcdev; Figma frame has no captcha either)")
    _attach_json(f"Figma {frame} vs live", {"frame": frame, "findings": findings, "layout": dp.inquiry_layout()})
    real = [f for f in findings if not f.startswith("captcha control")]
    assert not real, f"Figma {frame} ({theme}/{device}) differences:\n- " + "\n- ".join(real)


@_common
@allure.story("Layout")
@allure.severity(_sev(3))
@allure.title("The Express Your Interest inquiry modal renders correctly in Arabic RTL")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_143259
@pytest.mark.traceability("143259")
@allure.label("testcase", "143259")
@pytest.mark.parametrize("page,theme,device", LAYOUT_PARAMS, indirect=["page"])
def test_inquiry_modal_renders_arabic_rtl(page, theme, device):
    dp = _render_modal(page, "ar", theme)
    frame = FIGMA_FRAME[("ar", theme, device)]
    dp.inquiry_panel_screenshot(str(EVIDENCE / f"143259_live_ar_{theme}_{device}.png"))
    _evidence(page, f"143259_page_ar_{theme}_{device}")
    assert dp.document_direction() == "rtl"
    assert dp.is_inquiry_modal_open()
    dp.fill_inquiry_field("your_name", "أحمد السيد")
    assert dp.inquiry_field_value("your_name") == "أحمد السيد"
    assert dp.inquiry_field_meta("your_name")["dir"] == "rtl"
    options = [o[1] for o in dp.inquiry_field_meta("inquiry_type")["options"]][1:]
    findings = _figma_check(dp, "ar", theme, device)
    untranslated = [o for o in options if o.endswith("(AR)") or re.fullmatch(r"[A-Za-z ()]+", o)]
    if untranslated:
        findings.append(f"Inquiry Type options not translated in AR: {untranslated}")
    _attach_json(f"Figma {frame} vs live", {"frame": frame, "findings": findings, "layout": dp.inquiry_layout()})
    assert not findings, f"Figma {frame} ({theme}/{device}) differences:\n- " + "\n- ".join(findings)


@_common
@allure.story("Field validation")
@allure.severity(_sev(3))
@allure.title("Selecting an Inquiry Type value is accepted and stored with the submission")
@pytest.mark.functional_low
@pytest.mark.tc_143329
@pytest.mark.traceability("143329")
@allure.label("testcase", "143329")
@pytest.mark.parametrize("page", [PUBLIC], indirect=True, ids=["public"])
def test_inquiry_type_accepts_valid_selection(page, en_inquiry):
    dp = _open_modal(page)
    meta = dp.inquiry_field_meta("inquiry_type")
    assert meta["value"] == "", "Inquiry Type is pre-selected"
    labels = [o[1] for o in meta["options"]][1:]
    assert labels == ["General Interest", "Investment Inquiry", "Partnership Proposal", "Information Request"]
    dp.fill_inquiry_field("inquiry_type", "Investment Inquiry")
    assert dp.selected_inquiry_type_label() == "Investment Inquiry"
    assert en_inquiry["success"], en_inquiry["error"]
    assert _value(en_inquiry["stored"], "Inquiry Type") == "Investment Inquiry"


@_common
@allure.story("Field validation")
@allure.severity(_sev(3))
@allure.title("Leaving Inquiry Type unselected still allows the inquiry to be submitted successfully")
@pytest.mark.functional_low
@pytest.mark.tc_143330
@pytest.mark.traceability("143330")
@allure.label("testcase", "143330")
def test_inquiry_type_optional_allows_submission_when_blank(ar_inquiry):
    _attach_json("AR submission (Inquiry Type blank)", ar_inquiry)
    assert ar_inquiry["http"] == 200 and ar_inquiry["success"], ar_inquiry["error"]
    stored_type = _value(ar_inquiry["stored"], "Inquiry Type")
    # The CMS View modal renders an empty value as an em dash.
    assert stored_type in ("", None, "—") or "Inquiry Type" not in ar_inquiry["stored"], \
        f"stored Inquiry Type is {stored_type!r}"

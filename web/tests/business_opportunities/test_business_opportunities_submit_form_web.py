"""
web/tests/business_opportunities/test_business_opportunities_submit_form_web.py
— Web cases of PBI 130697 (INVEST — Business Opportunities) for the public
"Submit a Business Opportunity" webform and its success screen
(Azure plan 137724, suite 140361). Agent W1, Phase-3 run 2026-10-12.

57 cases: 143188-143197, 143220, 143229, 143242, 143260, 143261, 143284,
143290, 143331-143370.

How the run keeps qcdev clean
-----------------------------
* Every validation / field-level case runs in a fresh UNAUTHENTICATED context
  with `block_submissions()`: any POST to the intake endpoint is recorded and
  aborted. "No submission is stored" is proven by "the form never POSTed"
  (`sp.posts == []`), and no validation case can ever create a record.
* Exactly TWO real submissions are made, once per module, by the
  `real_submissions` fixture (EN + AR, data prefix QCTEST-130697-W1-, email
  qctest.130697.w1@example.com). Every case that needs a stored submission
  reads its evidence from that fixture. The EN submission first goes through
  one ABORTED attempt (143242: interrupted upload), then the retry.
* The fixture checks both rows in the CMS as the Form Manager (the reviewer
  role) and deletes ONLY those two rows at teardown as TEST_USER through
  `OpportunityReviewAdminPage.guarded_delete()` (exact name + entry id + ERC
  re-checked immediately before the click). The cleanup result is written to
  reports/evidence/130697_web_w1/cleanup_<stamp>.json.

Design source: Figma file J3e1thav8NIu6a3XhC6Wcl, "Business Opportunities-
submit" frames — light 4964:222747 (EN desktop), 4964:222847 (AR desktop),
4964:222802 (EN mobile 390), 4964:222902 (AR mobile); dark 4964:229542 (EN
desktop), 4964:229642 (AR desktop). The success screen has no frame (the
fragment says "Not designed"); its copy is the PBI's verbatim text.

Out of reach (reported, never faked): mailbox access for the acknowledgement
/ admin emails, and the reCAPTCHA (disabled on qcdev: the Security Check field
stays hidden, so captcha cases skip as BLOCKED with that reason).
"""

from __future__ import annotations

import io
import json
import os
import re
import time
from datetime import datetime
from pathlib import Path

import allure
import pytest

import cms.pages.business_opportunities.opportunity_submissions_admin_page as review_mod
from cms.pages.business_opportunities.opportunity_submissions_admin_page import (
    ROLE_ADMIN,
    ROLE_FORM_MANAGER,
    SUBMISSION_SLUG,
    OpportunityReviewAdminPage,
)
from core.web.browser import new_context
from web.pages.business_opportunities.submit_opportunity_page import (
    FIELD_NAMES,
    MANDATORY_FIELD_KEYS,
    MSG,
    SAMPLE_SELECT_VALUES,
    SubmitBusinessOpportunityPage,
)

EPIC = "Business Opportunities"
FEATURE = "Submit a Business Opportunity — Webform"
PREFIX = "QCTEST-130697-W1-"
EMAIL = "qctest.130697.w1@example.com"
STAMP = datetime.now().strftime("%m%d%H%M%S")
PROJECT_ROOT = Path(__file__).resolve().parents[3]
EVIDENCE = PROJECT_ROOT / "reports" / "evidence" / "130697_web_w1"
FIG_EN_D, FIG_AR_D, FIG_EN_M, FIG_AR_M = "4964:222747", "4964:222847", "4964:222802", "4964:222902"
FIG_EN_D_DARK, FIG_AR_D_DARK = "4964:229542", "4964:229642"

CAPTCHA_BLOCKED = ("BLOCKED — reCAPTCHA is disabled on qcdev (/o/qc-recaptcha-api/config enabled:false); the "
                   "form's 'Security Check' field stays hidden, so there is no captcha to leave unsolved or "
                   "answer wrongly. Observed: {observed}")
NO_MAILBOX = "acknowledgement / admin notification emails not verifiable (no mailbox access)"

pytestmark = [
    pytest.mark.web,
    pytest.mark.invest,
    pytest.mark.pbi_130697,
    pytest.mark.xdist_group("bizopp_web_w1"),
    # Rule 1: every public check in a fresh unauthenticated context.
    pytest.mark.parametrize("page", [{"auth": False}], indirect=True),
]


def case(*tc_ids: str, title: str, story: str, prio: int, cats: tuple = ("functional_low",)):
    severity = {1: allure.severity_level.BLOCKER, 2: allure.severity_level.CRITICAL,
                3: allure.severity_level.NORMAL, 4: allure.severity_level.MINOR}[prio]

    def deco(fn):
        for tc in tc_ids:
            fn = getattr(pytest.mark, f"tc_{tc}")(fn)
            fn = allure.label("testcase", tc)(fn)
        for cat in cats:
            fn = getattr(pytest.mark, cat)(fn)
        fn = pytest.mark.traceability(tc_ids[0])(fn)
        fn = allure.label("pbi", "130697")(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.story(story)(fn)
        fn = allure.feature(FEATURE)(fn)
        fn = allure.epic(EPIC)(fn)
        return allure.title(title)(fn)
    return deco


def evidence(page, name: str) -> str:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    path = EVIDENCE / (re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    png = page.screenshot(path=str(path), full_page=True)
    allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
    return str(path)


def attach_json(name: str, data) -> None:
    allure.attach(json.dumps(data, indent=2, ensure_ascii=False, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


# ===========================================================================
# Upload fixtures (generated, never committed): names/sizes mirror the cases.
# ===========================================================================
MB = 1024 * 1024


@pytest.fixture(scope="module")
def fx(tmp_path_factory) -> dict:
    from PIL import Image

    d = tmp_path_factory.mktemp("bizopp_w1_files")

    def img(name, fmt, size):
        buf = io.BytesIO()
        Image.new("RGB", (1200, 400), (145, 23, 49)).save(buf, fmt)
        data = buf.getvalue()
        (d / name).write_bytes(data + b"\0" * max(0, size - len(data)))

    def pdf(name, size):
        base = (b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>"
                b"endobj\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\ntrailer<</Root 1 0 R>>\n")
        (d / name).write_bytes(base + b"%" + b"0" * max(0, size - len(base) - 7) + b"\n%%EOF")

    img("banner.jpg", "JPEG", int(1.5 * MB))
    img("banner.gif", "GIF", 50 * 1024)
    img("banner-large.jpg", "JPEG", int(3.2 * MB))
    img("logo.png", "PNG", 800 * 1024)
    img("logo.bmp", "BMP", 0)
    img("logo-large.png", "PNG", int(2.8 * MB))
    img("gallery1.jpg", "JPEG", 2 * MB - 4096)  # "2MB" kept just under the live 2 MB cap
    img("gallery2.jpg", "JPEG", 3 * MB)
    img("gallery.webp", "WEBP", 30 * 1024)
    img("gallery-large.jpg", "JPEG", int(6.4 * MB))
    img("small.jpg", "JPEG", 200 * 1024)
    pdf("investment-brief.pdf", 3 * MB)
    pdf("investment-brief-4.9mb.pdf", int(4.9 * MB))
    pdf("investment-brief-large.pdf", 6 * MB)
    (d / "investment-brief.docx").write_bytes(b"PK\x03\x04" + b"0" * 20000)
    return {p.name: str(p) for p in d.iterdir()}


def valid_values(fx: dict, **overrides) -> dict:
    """A complete valid entry (QCTEST data). Used by validation cases (with the
    POST blocked) and, with overrides, by the two real submissions."""
    values = {
        "name_en": f"{PREFIX}Probe Opportunity",
        "name_ar": f"{PREFIX}فرصة اختبار",
        "sector": SAMPLE_SELECT_VALUES["sector"],
        "country": "Qatar",
        "company_name": f"{PREFIX}Company",
        "investment_brief_en": "QCTEST investment brief (EN). " * 5,
        "investment_brief_ar": "ملخص استثماري تجريبي. " * 6,
        "key_highlights": "QCTEST key highlights.",
        "investment_amount": "5000000",
        "currency": "QAR",
        "investment_type": SAMPLE_SELECT_VALUES["investment_type"],
        "timeline": SAMPLE_SELECT_VALUES["timeline"],
        "risk_profile": SAMPLE_SELECT_VALUES["risk_profile"],
        "industry_pool": SAMPLE_SELECT_VALUES["industry_pool"],
        "banner_image": fx["small.jpg"],
        "opportunity_logo": fx["small.jpg"],
        "gallery_images": fx["small.jpg"],
        "supporting_documents": fx["investment-brief.pdf"],
        "contact_full_name": f"{PREFIX}Contact",
        "contact_email": EMAIL,
        "contact_mobile": "55123456",
        "consent": True,
    }
    values.update(overrides)
    return values


def guarded_form(page, locale: str = "en") -> SubmitBusinessOpportunityPage:
    sp = SubmitBusinessOpportunityPage(page)
    sp.block_submissions()
    return sp.open_submit_form(locale=locale)


def assert_blocked(sp: SubmitBusinessOpportunityPage, field_key: str, expected_msg: str) -> None:
    errors = sp.errors()
    assert not sp.is_success_visible(), "success screen shown for an invalid entry"
    assert sp.posts == [], f"the form POSTed an invalid entry: {sp.posts}"
    assert errors.get(FIELD_NAMES[field_key]) == expected_msg, f"inline error on {field_key}: {errors}"


# ===========================================================================
# The two real submissions (module scope) + CMS check + guarded cleanup
# ===========================================================================
LONG_BRIEF_EN = ("Solar park expansion with a long-term PPA, phased construction and grid connection. " * 70)[:4800]
LONG_BRIEF_AR = ("فرصة استثمارية في توسعة مجمع الطاقة الشمسية مع اتفاقية شراء طاقة طويلة الأجل. " * 70)[:4800]


def _submission_plan(fx: dict) -> dict:
    return {
        "en": valid_values(
            fx,
            name_en=f"{PREFIX}Solar Energy Park Expansion {STAMP}",
            name_ar=f"{PREFIX}توسعة مجمع الطاقة الشمسية {STAMP}",
            company_name=f"{PREFIX}Doha Green Investments LLC",
            investment_brief_en=LONG_BRIEF_EN,
            investment_brief_ar=LONG_BRIEF_AR,
            key_highlights="High ROI, government-backed PPP structure, and a 3-year payback period.",
            banner_image=fx["banner.jpg"],
            opportunity_logo=fx["logo.png"],
            gallery_images=fx["gallery1.jpg"],
            supporting_documents=fx["investment-brief-4.9mb.pdf"],
            contact_full_name=f"{PREFIX}Sara Al-Kuwari",
            contact_mobile="3312 9988",
            contact_website="https://alkuwari-holdings.qa",
        ),
        "ar": valid_values(
            fx,
            name_en=f"{PREFIX}Doha Green Logistics Hub {STAMP}",
            name_ar=f"{PREFIX}مركز الدوحة الأخضر للخدمات اللوجستية {STAMP}",
            sector="infrastructure",
            company_name=f"{PREFIX}Doha Green Ltd.",
            investment_amount="15000000",
            timeline="twelvePlusMonths",
            contact_full_name=f"{PREFIX}Fatima Al-Kaabi",
            contact_mobile="5598 7654",
        ),  # Website left BLANK on purpose (143197 / 143359 optional-field check)
    }


def _public_submit(browser, locale: str, values: dict, interrupt_first: bool) -> dict:
    ctx = new_context(browser, use_auth_state=False)
    page = ctx.new_page()
    result: dict = {"locale": locale, "name": values["name_en"]}
    try:
        sp = SubmitBusinessOpportunityPage(page).open_submit_form(locale=locale)
        sp.fill_valid(values)
        result["files_selected"] = {k: sp.selected_file_names(k) for k in
                                    ("banner_image", "opportunity_logo", "gallery_images", "supporting_documents")}
        if interrupt_first:  # 143242 — the uploads travel in the one multipart POST: drop it mid-flight
            sp.block_submissions()
            sp.click_submit()
            page.wait_for_timeout(2500)
            result["interrupted"] = {
                "aborted_posts": len(sp.posts),
                **sp.outcome(),
                "files_still_selected": sp.selected_file_names("supporting_documents"),
                "evidence": evidence(page, f"w1_{locale}_interrupted_upload"),
            }
            sp.unblock_submissions()
        started = time.monotonic()
        result.update(sp.submit_and_wait())
        result["seconds"] = round(time.monotonic() - started, 2)
        result["evidence"] = evidence(page, f"w1_{locale}_success_screen")
        if locale == "en" and result.get("success"):
            # 143368 step 4: toggle the site language while the success screen is shown
            sp.click_language_switcher()
            page.wait_for_timeout(3000)
            result["after_language_toggle"] = {
                "url": page.url,
                "success_still_visible": sp.is_success_visible(),
                "form_visible": page.locator(sp.FORM).is_visible(),
                "evidence": evidence(page, "w1_en_success_then_language_toggle"),
            }
    finally:
        ctx.close()
    return result


def _signed_in(browser, role):
    ctx = new_context(browser, use_auth_state=False)
    admin = OpportunityReviewAdminPage(ctx.new_page())
    return ctx, admin, admin.login_as_role(role)


@pytest.fixture(scope="module")
def real_submissions(browser, fx):
    plan = _submission_plan(fx)
    data: dict = {"en": {}, "ar": {}, "cleanup": []}
    for locale in ("en", "ar"):
        data[locale] = _public_submit(browser, locale, plan[locale], interrupt_first=(locale == "en"))

    # Form Manager (the reviewer role): the stored rows, by the id the API returned.
    ctx, admin, login = _signed_in(browser, ROLE_FORM_MANAGER)
    data["form_manager_login"] = login
    try:
        for locale in ("en", "ar"):
            item = data[locale]
            entry_id = str((item.get("body") or {}).get("id", ""))
            item["id"] = entry_id
            if not (item.get("success") and entry_id):
                continue
            admin.open_manage(SUBMISSION_SLUG)
            item["listed"] = entry_id in admin.entry_ids()
            if item["listed"]:
                view = admin.view_entry(entry_id)
                item["view_lines"] = view["lines"]
                item["view_fields"] = view["fields"]
                item["view_name"] = admin.entry_name(view)
                item["view_evidence"] = admin.evidence(f"w1_FormManager_view_{entry_id}")
    finally:
        ctx.close()
    attach_json("W1 real submissions (live)", data)

    yield data

    # Guarded cleanup: ONLY these two rows, as TEST_USER, exact name + id + ERC.
    original_prefix = review_mod.QCTEST_PREFIX
    review_mod.QCTEST_PREFIX = PREFIX  # guarded_delete() refuses any name outside this prefix
    ctx, admin, _ = _signed_in(browser, ROLE_ADMIN)
    try:
        for locale in ("en", "ar"):
            item = data[locale]
            if item.get("id") and item.get("view_name"):
                result = admin.guarded_delete(SUBMISSION_SLUG, item["id"], item["view_name"])
            elif item.get("success"):
                result = "NOT deleted: created but not located by id/name — clean up manually"
            else:
                result = "nothing created"
            data["cleanup"].append({"locale": locale, "id": item.get("id"), "name": item.get("view_name") or
                                    item.get("name"), "reference": item.get("reference"), "result": result})
    finally:
        review_mod.QCTEST_PREFIX = original_prefix
        ctx.close()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / f"cleanup_{STAMP}.json").write_text(json.dumps(data["cleanup"], indent=2, ensure_ascii=False),
                                                    encoding="utf-8")
    attach_json("W1 cleanup", data["cleanup"])


def _view_text(item: dict) -> str:
    return "\n".join(item.get("view_lines") or [])


def _require_stored(item: dict) -> None:
    assert item.get("http") == 200 and item.get("success"), (
        f"submission did not succeed: http={item.get('http')} status={item.get('status')!r} body={item.get('body')}")
    assert item.get("listed"), f"submission {item.get('id')} not found in manage-opportunity-submission"


# ===========================================================================
# Contact Information — 143188 / 143353, 143189 / 143354
# ===========================================================================
@case("143188", title="Contact Information full name accepts a valid value and is stored", story="Contact Information", prio=2)
def test_contact_full_name_accepts_and_stores(page, real_submissions):
    item = real_submissions["en"]
    _require_stored(item)
    assert f"{PREFIX}Sara Al-Kuwari" in _view_text(item), "contact name not recorded on the stored submission"


@case("143353", title="Contact Information full name field accepts a valid value", story="Contact Information", prio=2)
def test_contact_full_name_field_accepts_value(page, fx):
    sp = guarded_form(page)
    sp.fill_field("contact_full_name", "Ahmed Al-Kuwari")
    sp.blur()
    assert sp.field_value("contact_full_name") == "Ahmed Al-Kuwari"
    assert sp.field_error_text("contact_full_name") == ""


@case("143189", "143354", title="Submission is blocked when the Contact full name is empty or whitespace-only",
      story="Contact Information", prio=2)
def test_contact_full_name_empty_and_whitespace_blocked(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("contact_full_name",)).click_submit()
    assert_blocked(sp, "contact_full_name", MSG["en"]["required"])
    assert sp.field_value("name_en") == f"{PREFIX}Probe Opportunity", "entered data not retained"
    sp.fill_field("contact_full_name", " " * 6)
    sp.click_submit()
    assert_blocked(sp, "contact_full_name", MSG["en"]["required"])


# ===========================================================================
# Contact Email — 143190 / 143355, 143191, 143192 / 143356
# ===========================================================================
@case("143190", title="Contact Email accepts a valid email format and is stored", story="Contact Information", prio=1)
def test_contact_email_accepts_and_stores(page, fx, real_submissions):
    sp = guarded_form(page)
    sp.fill_field("contact_email", "sara.alkuwari@example.com")
    sp.blur()
    assert sp.field_error_text("contact_email") == ""
    item = real_submissions["en"]
    _require_stored(item)
    assert EMAIL in _view_text(item), "contact email not recorded on the stored submission"


@case("143355", title="Contact Email field accepts a valid email address", story="Contact Information", prio=2)
def test_contact_email_field_accepts_value(page, fx):
    sp = guarded_form(page)
    sp.fill_field("contact_email", "ahmed.alkuwari@dohagreeninvest.com")
    sp.blur()
    assert sp.field_value("contact_email") == "ahmed.alkuwari@dohagreeninvest.com"
    assert sp.field_error_text("contact_email") == ""


@case("143191", title="Submission is blocked when Contact Email is left empty", story="Contact Information", prio=2)
def test_contact_email_empty_blocked(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("contact_email",)).click_submit()
    assert_blocked(sp, "contact_email", MSG["en"]["required"])


@case("143192", "143356", title="An empty or malformed Contact Email is rejected", story="Contact Information", prio=2)
def test_contact_email_empty_and_malformed_blocked(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("contact_email",)).click_submit()
    assert_blocked(sp, "contact_email", MSG["en"]["required"])
    for bad in ("sara@@example", "ahmed.alkuwari@@invalid"):
        sp.fill_field("contact_email", bad)
        sp.click_submit()
        assert_blocked(sp, "contact_email", MSG["en"]["invalid_email"])


# ===========================================================================
# Mobile Number — 143193 / 143357, 143194, 143195 / 143358
# ===========================================================================
@case("143193", title="Mobile Number defaults to +974 and a valid number is stored", story="Contact Information", prio=2)
def test_contact_mobile_default_and_stored(page, fx, real_submissions):
    sp = guarded_form(page)
    assert sp.contact_mobile_country_code_text() == "+974"
    item = real_submissions["en"]
    _require_stored(item)
    stored = _view_text(item)
    assert "+974" in stored and "33129988" in stored.replace(" ", ""), "mobile number not recorded with +974"


@case("143357", title="Mobile Number defaults to the +974 Qatar flag and accepts a valid number", story="Contact Information", prio=2)
def test_contact_mobile_field_default_and_accepts(page, fx):
    sp = guarded_form(page)
    assert sp.contact_mobile_country_code_text() == "+974"
    assert sp.page.locator(sp.FLAG).is_visible(), "no flag chip next to +974"
    sp.type_field("contact_mobile", "5512 3456")
    sp.blur()
    assert sp.field_value("contact_mobile") == "5512 3456"
    assert sp.field_error_text("contact_mobile") == ""
    evidence(page, "w1_143357_mobile_default_flag")


@case("143194", title="Submission is blocked when Mobile Number is left empty", story="Contact Information", prio=2)
def test_contact_mobile_empty_blocked(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("contact_mobile",)).click_submit()
    assert_blocked(sp, "contact_mobile", MSG["en"]["required"])


@case("143195", "143358", title="An empty or invalid Mobile Number is rejected", story="Contact Information", prio=2)
def test_contact_mobile_invalid_blocked(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("contact_mobile",)).click_submit()
    assert_blocked(sp, "contact_mobile", MSG["en"]["required"])
    for bad in ("xyz789", "123"):
        sp.type_field("contact_mobile", bad)
        sp.click_submit()
        assert_blocked(sp, "contact_mobile", MSG["en"]["invalid_phone"])


# ===========================================================================
# Website (optional) — 143196, 143197, 143359
# ===========================================================================
@case("143196", title="A valid Website URL is accepted and stored", story="Contact Information", prio=4)
def test_website_valid_url_stored(page, real_submissions):
    item = real_submissions["en"]
    _require_stored(item)
    assert "https://alkuwari-holdings.qa" in _view_text(item), "Website URL not recorded"


@case("143197", "143359", title="A malformed Website URL is rejected and a blank Website still submits",
      story="Contact Information", prio=3)
def test_website_malformed_rejected_blank_allowed(page, fx, real_submissions):
    sp = guarded_form(page)
    sp.fill_field("contact_website", "https://www.dohagreeninvest.com")
    sp.blur()
    assert sp.field_error_text("contact_website") == ""
    sp.fill_valid(valid_values(fx))
    for bad in ("not-a-url", "htp:/badurl"):
        sp.fill_field("contact_website", bad)
        sp.click_submit()
        # Case wording "Please enter a valid URL"; live copy below (wording finding, behaviour correct).
        assert_blocked(sp, "contact_website", MSG["en"]["invalid_url"])
    # Blank optional Website: the AR real submission left it empty and was stored.
    item = real_submissions["ar"]
    _require_stored(item)


# ===========================================================================
# Submission behaviour — 143220, 143242, 143284, 143368
# ===========================================================================
@case("143220", title="Submit with all fields valid disables the button during processing, then shows success",
      story="Submission", prio=2)
def test_submit_disables_button_then_success(page, real_submissions):
    item = real_submissions["en"]
    assert item["busy_state"]["disabled"] is True, f"button not disabled while submitting: {item['busy_state']}"
    _require_stored(item)
    assert item["form_hidden"] and item["reference"].startswith("QC-BO-SUB-")
    assert "Pending" in _view_text(item), "stored submission is not Pending"


@case("143242", title="An interrupted large-file upload fails gracefully and the retry stores one valid document",
      story="Media & Documents", prio=2, cats=("edge",))
def test_interrupted_upload_then_retry(page, real_submissions):
    item = real_submissions["en"]
    cut = item["interrupted"]
    attach_json("interrupted attempt", cut)
    assert cut["aborted_posts"] == 1 and not cut["success"], "interrupted attempt did not fail"
    assert cut["status"] == MSG["en"]["generic_error"], f"failure message: {cut['status']!r}"
    assert cut["button_disabled"] is False, "Submit not re-enabled for a retry"
    assert cut["files_still_selected"] == ["investment-brief-4.9mb.pdf"], "selected PDF lost after the failure"
    _require_stored(item)
    stored = _view_text(item)
    assert stored.count("investment-brief-4.9mb") <= 1, "duplicate supporting document stored"


@case("143284", title="A Public Visitor can submit a Business Opportunity end to end", story="End to end",
      prio=1, cats=("functional_high", "regression", "uat", "webform"))
def test_end_to_end_submission(page, real_submissions):
    item = real_submissions["en"]
    allure.dynamic.description(f"Not verified here: {NO_MAILBOX}.")
    _require_stored(item)
    assert item["files_selected"]["banner_image"] == ["banner.jpg"]
    assert "Pending" in _view_text(item), "CMS submission status is not Pending"
    assert item["reference"] in _view_text(item), "CMS record does not carry the screen's reference number"


@case("143368", title="Valid submission is stored as Pending with the bilingual success message and reference number",
      story="End to end", prio=1, cats=("functional_low", "regression"))
def test_success_screen_bilingual_reference(page, real_submissions):
    allure.dynamic.description(f"Not verified here: {NO_MAILBOX}.")
    for locale in ("en", "ar"):
        item = real_submissions[locale]
        _require_stored(item)
        ref = item["reference"]
        assert re.fullmatch(r"QC-BO-SUB-\d{8}-[A-Z0-9]+", ref), f"{locale} reference {ref!r}"
        assert item["done_title"] == MSG[locale]["done_title"]
        assert item["done_text"] == MSG[locale]["done_text"].format(ref=ref), f"{locale} success copy differs"
        assert "Pending" in _view_text(item) and ref in _view_text(item)


# ===========================================================================
# Validation — 143290, 143369
# ===========================================================================
@case("143290", title="Missing Investment Amount blocks the submission with inline validation, nothing stored",
      story="Validation", prio=2, cats=("functional_high", "regression", "webform"))
def test_missing_investment_amount_blocked(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("investment_amount",)).click_submit()
    assert_blocked(sp, "investment_amount", MSG["en"]["required"])
    assert sp.is_field_invalid("investment_amount"), "Investment Amount not highlighted"
    assert sp.page.locator(sp.FORM).is_visible()


@case("143369", title="Submit with every field empty shows an inline error on every mandatory field",
      story="Validation", prio=2)
def test_all_empty_shows_every_required_error(page, fx):
    sp = guarded_form(page)
    sp.click_submit()
    errors = sp.errors()
    assert sp.posts == [] and not sp.is_success_visible()
    missing = [k for k in MANDATORY_FIELD_KEYS if k != "consent" and errors.get(FIELD_NAMES[k]) != MSG["en"]["required"]]
    assert not missing, f"mandatory fields without 'This field is required.': {missing}"
    assert sp.status_text() == MSG["en"]["fix_errors"]
    evidence(page, "w1_143369_all_required_errors")


# ===========================================================================
# CAPTCHA — 143229, 143370
# ===========================================================================
@case("143229", title="Captcha is enforced on the Submit a Business Opportunity webform", story="CAPTCHA", prio=1)
def test_captcha_enforced(page, fx):
    sp = guarded_form(page)
    visible = sp.is_captcha_visible()
    if not visible:
        pytest.skip(CAPTCHA_BLOCKED.format(observed="no captcha control on the form"))
    pytest.fail("A captcha control is now visible — script this case against it (never bypass a live captcha).")


@case("143370", title="Submission is blocked when the captcha is incomplete or wrong", story="CAPTCHA", prio=2)
def test_captcha_incomplete_or_wrong_blocks(page, fx):
    sp = guarded_form(page)
    if not sp.is_captcha_visible():
        pytest.skip(CAPTCHA_BLOCKED.format(observed="no captcha control on the form"))
    pytest.fail("A captcha control is now visible — script this case against it (never bypass a live captcha).")


# ===========================================================================
# Basic Information — 143331-143339
# ===========================================================================
@case("143331", title="Project/Opportunity Name accepts valid EN and AR text within 150 characters", story="Basic Information", prio=2)
def test_name_accepts_en_and_ar(page, fx):
    sp = guarded_form(page)
    sp.fill_field("name_en", "Solar Energy Park Expansion")
    sp.fill_field("name_ar", "توسعة مجمع الطاقة الشمسية")
    sp.blur()
    assert sp.field_value("name_en") == "Solar Energy Park Expansion"
    assert sp.field_value("name_ar") == "توسعة مجمع الطاقة الشمسية"
    assert sp.style(sp.field("name_ar"))["direction"] == "rtl", "Arabic name not rendered right-to-left"
    assert sp.field_error_text("name_en") == sp.field_error_text("name_ar") == ""


def _cap_then_whitespace(sp, key: str, char: str, limit: int, spaces: int) -> None:
    assert sp.maxlength(key) == limit, f"{key} maxlength {sp.maxlength(key)} != {limit}"
    if limit <= 600:
        sp.type_field(key, char * (limit + 1))
    else:
        sp.fill_field(key, char * (limit + 1))
    assert len(sp.field_value(key)) == limit, f"{key} accepted {len(sp.field_value(key))} chars"
    sp.fill_field(key, " " * spaces)
    sp.click_submit()
    assert_blocked(sp, key, MSG["en"]["required"])


@case("143332", title="Project/Opportunity Name caps at 150 characters and rejects whitespace-only", story="Basic Information", prio=2)
def test_name_cap_and_whitespace(page, fx):
    _cap_then_whitespace(guarded_form(page), "name_en", "A", 150, 10)


@case("143333", title="Sector dropdown accepts a valid selection from the Sector lookup", story="Basic Information", prio=2)
def test_sector_selection(page, fx):
    sp = guarded_form(page)
    assert sp.placeholder("sector") == "Select Sector"
    assert "Energy" in sp.option_labels("sector")
    sp.fill_field("sector", "energy")
    assert sp.selected_label("sector") == "Energy" and sp.field_error_text("sector") == ""


@case("143334", title="Submission is blocked when Sector is left unselected", story="Basic Information", prio=2)
def test_sector_required(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("sector",)).click_submit()
    # Case wording "Please select a Sector"; live copy is the generic required message.
    assert_blocked(sp, "sector", MSG["en"]["required"])


@case("143335", title="Optional Sub-Sector accepts a valid selection and allows a blank submission", story="Basic Information", prio=3)
def test_sub_sector_optional(page, fx, real_submissions):
    sp = guarded_form(page)
    sp.fill_field("sector", "energy")
    disabled, options = sp.is_disabled("sub_sector"), sp.option_labels("sub_sector")
    _require_stored(real_submissions["en"])  # blank Sub-Sector did not block the stored submission
    if disabled and options == ["Not yet configured"]:
        pytest.skip("BLOCKED — the Sub-Sector CMS lookup is empty on qcdev: the select is disabled with "
                    "'Not yet configured', so 'Renewable Energy' cannot be selected (no CMS data may be "
                    "created). Blank Sub-Sector: the EN QCTEST submission with no Sub-Sector was stored.")
    assert "Renewable Energy" in options


@case("143336", title="Country dropdown accepts a valid selection from the Country lookup", story="Basic Information", prio=2)
def test_country_selection(page, fx):
    sp = guarded_form(page)
    select_visible = sp.page.locator("#qc-bos-country").is_visible()
    if not select_visible:
        sp.fill_field("country", "Qatar")
        assert sp.field_value("country") == "Qatar"
        pytest.skip("BLOCKED — the Country CMS lookup is empty on qcdev, so the form renders a free-text input "
                    "(placeholder 'Qatar') instead of the dropdown; 'Qatar' typed is accepted.")
    assert "Qatar" in sp.page.locator("#qc-bos-country option").all_inner_texts()


@case("143337", title="Submission is blocked when Country is left empty", story="Basic Information", prio=2)
def test_country_required(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("country",)).click_submit()
    assert_blocked(sp, "country", MSG["en"]["required"])


@case("143338", title="Company/Organization Name accepts a valid value", story="Basic Information", prio=2)
def test_company_accepts(page, fx):
    sp = guarded_form(page)
    sp.fill_field("company_name", "Doha Green Investments LLC")
    sp.blur()
    assert sp.field_value("company_name") == "Doha Green Investments LLC"
    assert sp.field_error_text("company_name") == ""


@case("143339", title="Company/Organization Name caps at 150 characters and rejects whitespace-only", story="Basic Information", prio=2)
def test_company_cap_and_whitespace(page, fx):
    _cap_then_whitespace(guarded_form(page), "company_name", "B", 150, 10)


# ===========================================================================
# Opportunity Details — 143340-143352
# ===========================================================================
@case("143340", title="Investment Brief accepts valid EN and AR rich text within 5000 characters", story="Opportunity Details", prio=2)
def test_investment_brief_accepts_en_ar(page, fx):
    sp = guarded_form(page)
    sp.fill_field("investment_brief_en", LONG_BRIEF_EN)
    sp.fill_field("investment_brief_ar", LONG_BRIEF_AR)
    sp.blur()
    assert len(sp.field_value("investment_brief_en")) == 4800 and len(sp.field_value("investment_brief_ar")) == 4800
    assert sp.field_error_text("investment_brief_en") == sp.field_error_text("investment_brief_ar") == ""
    assert sp.style(sp.field("investment_brief_ar"))["direction"] == "rtl"
    tag = sp.page.evaluate("(s) => document.querySelector(s).tagName", sp.field("investment_brief_en"))
    toolbar = sp.page.locator(".qc-bos__field:has(#qc-bos-investmentBrief) [role=toolbar], "
                              ".qc-bos__field:has(#qc-bos-investmentBrief) [contenteditable=true]").count()
    assert tag != "TEXTAREA" or toolbar, ("Investment Brief is a plain <textarea> with no rich-text toolbar: the "
                                          "case's bold phrase cannot be entered (PBI: Rich Text)")


@case("143341", title="Investment Brief caps at 5000 characters and rejects whitespace-only", story="Opportunity Details", prio=2)
def test_investment_brief_cap_and_whitespace(page, fx):
    sp = guarded_form(page)
    _cap_then_whitespace(sp, "investment_brief_en", "A", 5000, 15)


@case("143342", title="Key Highlights accepts a valid value within 500 characters", story="Opportunity Details", prio=2)
def test_key_highlights_accepts(page, fx):
    sp = guarded_form(page)
    value = "High ROI, government-backed PPP structure, and a 3-year payback period."
    sp.fill_field("key_highlights", value)
    sp.blur()
    assert sp.field_value("key_highlights") == value and sp.field_error_text("key_highlights") == ""


@case("143343", title="Key Highlights caps at 500 characters and rejects whitespace-only", story="Opportunity Details", prio=2)
def test_key_highlights_cap_and_whitespace(page, fx):
    _cap_then_whitespace(guarded_form(page), "key_highlights", "A", 500, 8)


@case("143344", title="Investment Amount accepts a valid positive number", story="Opportunity Details", prio=2)
def test_investment_amount_accepts(page, fx):
    sp = guarded_form(page)
    sp.type_field("investment_amount", "5000000")
    sp.blur()
    assert sp.field_value("investment_amount").replace(",", "") == "5000000"
    sp.fill_valid(valid_values(fx, investment_amount="5000000")).click_submit()
    assert sp.field_error_text("investment_amount") == ""


@case("143345", title="Investment Amount rejects zero, negative and non-numeric values", story="Opportunity Details", prio=2)
def test_investment_amount_rejects_bad_values(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx))
    results = {}
    for bad in ("0", "-5000", "abc"):
        sp.type_field("investment_amount", bad)
        sp.click_submit()
        results[bad] = sp.field_error_text("investment_amount")
    attach_json("Investment Amount results", results)
    accepted = [v for v, msg in results.items() if not msg]
    assert not accepted, f"Investment Amount accepted {accepted} (PBI: positive numeric); results={results}"


def _lookup_selection(page, key: str, value: str, label: str, expected_options: list | None = None):
    sp = guarded_form(page)
    assert sp.placeholder(key) == "Select"
    options = sp.option_labels(key)[1:]
    sp.fill_field(key, value)
    assert sp.selected_label(key) == label and sp.field_error_text(key) == ""
    if expected_options is not None:
        assert options == expected_options, f"{key} options {options}"
    return sp, options


@case("143346", title="Currency dropdown accepts a valid selection from the Currency lookup", story="Opportunity Details", prio=2)
def test_currency_selection(page, fx):
    sp = guarded_form(page)
    if not sp.page.locator("#qc-bos-currency").is_visible():
        sp.fill_field("currency", "QAR")
        assert sp.field_value("currency") == "QAR"
        pytest.skip("BLOCKED — the Currency CMS lookup is empty on qcdev, so the form renders a free-text input "
                    "(placeholder 'e.g. QAR') instead of the dropdown; 'QAR' typed is accepted.")
    assert "QAR" in sp.page.locator("#qc-bos-currency option").all_inner_texts()


@case("143347", title="Submission is blocked when Currency is left empty", story="Opportunity Details", prio=2)
def test_currency_required(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("currency",)).click_submit()
    assert_blocked(sp, "currency", MSG["en"]["required"])


@case("143348", title="Investment Type dropdown lists the lookup values and accepts Joint Venture", story="Opportunity Details", prio=2)
def test_investment_type_selection(page, fx):
    _, options = _lookup_selection(page, "investment_type", "jointVenture", "Joint Venture")
    attach_json("Investment Type options", options)
    # Case: Equity, Debt, Joint Venture, PPP, Grant, Other — live labels PPP as "Public-Private Partnership".
    assert options == ["Equity", "Debt", "Joint Venture", "Public-Private Partnership", "Grant", "Other"]


@case("143349", title="Submission is blocked when Investment Type is left unselected", story="Opportunity Details", prio=2)
def test_investment_type_required(page, fx):
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("investment_type",)).click_submit()
    assert_blocked(sp, "investment_type", MSG["en"]["required"])


@case("143350", title="Timeline dropdown accepts a valid selection and blocks submission when unselected", story="Opportunity Details", prio=2)
def test_timeline_selection_and_required(page, fx):
    _lookup_selection(page, "timeline", "sixToTwelveMonths", "6–12 months",
                      ["Immediate", "1–3 months", "3–6 months", "6–12 months", "12+ months"])
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("timeline",)).click_submit()
    assert_blocked(sp, "timeline", MSG["en"]["required"])


@case("143351", title="Risk Profile dropdown accepts a valid selection and blocks submission when unselected", story="Opportunity Details", prio=2)
def test_risk_profile_selection_and_required(page, fx):
    _lookup_selection(page, "risk_profile", "medium", "Medium", ["Low", "Medium", "High"])
    sp = guarded_form(page)
    sp.fill_valid(valid_values(fx), skip=("risk_profile",)).click_submit()
    assert_blocked(sp, "risk_profile", MSG["en"]["required"])


@case("143352", title="Industry Pool multi-select accepts several values and blocks submission when none is selected",
      story="Opportunity Details", prio=2)
def test_industry_pool_multi_select(page, fx):
    sp = guarded_form(page)
    options = sp.option_labels("industry_pool")[1:]
    assert options == ["Technology", "Energy", "Infrastructure", "Finance", "Trade"], options
    sp.fill_valid(valid_values(fx), skip=("industry_pool",)).click_submit()
    assert_blocked(sp, "industry_pool", MSG["en"]["required"])
    assert sp.is_multi_select("industry_pool"), (
        "Industry Pool is a single-value <select> (no 'multiple'): 'Energy' AND 'Infrastructure' cannot both be "
        "selected (PBI: Multi-select)")


# ===========================================================================
# Media & Documents — 143360-143367
# ===========================================================================
def _upload_accepted(sp, key: str, files: list) -> dict:
    sp.fill_field(key, files)
    state = {"error": sp.field_error_text(key), "file_label": sp.uploaded_file_label(key),
             "selected": sp.selected_file_names(key), "image_preview": sp.upload_has_image_preview(key)}
    attach_json(f"{key} upload state", state)
    return state


def _upload_rejected(sp, key: str, file_path: str, expected_suffix: str) -> None:
    name = os.path.basename(file_path)
    sp.fill_field(key, file_path)
    err = sp.field_error_text(key)
    assert err == f"{name} — {expected_suffix}", f"{key} / {name}: {err!r}"
    assert sp.selected_file_names(key) == [] and sp.uploaded_file_label(key) == "", f"{name} kept after rejection"


@case("143360", title="Banner Image accepts a 1.5MB JPG and shows a thumbnail preview", story="Media & Documents", prio=2)
def test_banner_accepts_valid(page, fx):
    sp = guarded_form(page)
    st = _upload_accepted(sp, "banner_image", fx["banner.jpg"])
    assert st["error"] == "" and st["selected"] == ["banner.jpg"] and st["file_label"] == "banner.jpg"
    evidence(page, "w1_143360_banner_uploaded")
    assert st["image_preview"], "no thumbnail preview — only the file name 'banner.jpg' is shown"


@case("143361", title="Banner Image rejects a GIF and a 3.2MB JPG", story="Media & Documents", prio=2)
def test_banner_rejects_type_and_size(page, fx):
    sp = guarded_form(page)
    _upload_rejected(sp, "banner_image", fx["banner.gif"], MSG["en"]["bad_type"])
    _upload_rejected(sp, "banner_image", fx["banner-large.jpg"], MSG["en"]["too_large"])


@case("143362", title="Opportunity Logo accepts an 800KB PNG and shows a thumbnail preview", story="Media & Documents", prio=2)
def test_logo_accepts_valid(page, fx):
    sp = guarded_form(page)
    st = _upload_accepted(sp, "opportunity_logo", fx["logo.png"])
    assert st["error"] == "" and st["selected"] == ["logo.png"] and st["file_label"] == "logo.png"
    assert st["image_preview"], "no thumbnail preview — only the file name 'logo.png' is shown"


@case("143363", title="Opportunity Logo rejects a BMP and a 2.8MB PNG", story="Media & Documents", prio=2)
def test_logo_rejects_type_and_size(page, fx):
    sp = guarded_form(page)
    _upload_rejected(sp, "opportunity_logo", fx["logo.bmp"], MSG["en"]["bad_type"])
    _upload_rejected(sp, "opportunity_logo", fx["logo-large.png"], MSG["en"]["too_large"])


@case("143364", title="Gallery Images accepts 2MB and 3MB JPGs together (5MB per image)", story="Media & Documents", prio=2)
def test_gallery_accepts_multiple(page, fx):
    sp = guarded_form(page)
    st = _upload_accepted(sp, "gallery_images", [fx["gallery1.jpg"], fx["gallery2.jpg"]])
    evidence(page, "w1_143364_gallery_2mb_3mb")
    assert st["error"] == "", f"gallery rejected a file within the PBI's 5 MB per image: {st['error']!r}"
    assert st["selected"] == ["gallery1.jpg", "gallery2.jpg"]
    assert st["image_preview"], "no thumbnail previews"


@case("143365", title="Gallery Images rejects a WEBP and a 6.4MB JPG", story="Media & Documents", prio=2)
def test_gallery_rejects_type_and_size(page, fx):
    sp = guarded_form(page)
    _upload_rejected(sp, "gallery_images", fx["gallery.webp"], MSG["en"]["bad_type"])
    _upload_rejected(sp, "gallery_images", fx["gallery-large.jpg"], MSG["en"]["too_large"])


@case("143366", title="Supporting Documents accepts a 3MB PDF as an attached file row", story="Media & Documents", prio=2)
def test_supporting_document_accepts(page, fx):
    sp = guarded_form(page)
    st = _upload_accepted(sp, "supporting_documents", fx["investment-brief.pdf"])
    assert st["error"] == "" and st["file_label"] == "investment-brief.pdf"


@case("143367", title="Supporting Documents rejects a DOCX and a 6MB PDF", story="Media & Documents", prio=2)
def test_supporting_document_rejects(page, fx):
    sp = guarded_form(page)
    _upload_rejected(sp, "supporting_documents", fx["investment-brief.docx"], MSG["en"]["bad_type"])
    _upload_rejected(sp, "supporting_documents", fx["investment-brief-large.pdf"], MSG["en"]["too_large"])


# ===========================================================================
# UI vs Figma — 143260 (EN, light + dark, desktop + mobile), 143261 (AR RTL)
# ===========================================================================
INK, WHITE = "rgb(29, 29, 27)", "rgb(255, 255, 255)"
FIGMA = {
    "light": {
        "page_bg": WHITE, "title_color": INK, "sub_color": "rgb(124, 123, 123)", "icon_bg": "rgb(246, 246, 246)",
        "label_color": INK, "req_color": "rgb(225, 29, 72)", "input_border": "rgb(237, 237, 237)",
        "placeholder": "rgb(168, 168, 167)", "rule": "rgb(246, 240, 236)", "drop_border": "rgb(208, 208, 208)",
        "drop_icon_bg": "rgb(244, 231, 234)", "drop_strong": "rgb(145, 23, 49)", "drop_rest": "rgb(52, 52, 50)",
        "dial": "rgb(52, 52, 50)",
    },
    "dark": {
        "page_bg": INK, "title_color": WHITE, "sub_color": "rgb(208, 208, 208)", "icon_bg": "rgb(52, 52, 50)",
        "label_color": WHITE, "req_color": "rgb(253, 164, 175)", "input_border": "rgb(74, 74, 73)",
        "placeholder": "rgb(168, 168, 167)", "rule": "rgb(66, 44, 27)", "drop_border": "rgb(124, 123, 123)",
        "drop_icon_bg": "rgb(54, 7, 17)", "drop_strong": "rgb(196, 69, 97)", "drop_rest": "rgb(246, 246, 246)",
        "dial": "rgb(246, 246, 246)",
    },
}
COPY = {
    "en": {"title": "Submit a Business Opportunity",
           "sub": "Share your investment or collaboration opportunity with global investors through Qatar Chamber.",
           "groups": ["Basic Information", "Opportunity Details", "Media & Documents", "Contact Information"],
           "hints": ["PNG or JPG · max 2 MB", "PNG or JPG · max 2 MB",
                     "Upload one completed images, maximum 10 images.", "Upload one completed PDF, maximum 5 MB."]},
    "ar": {"title": "تقديم فرصة استثمارية",
           "sub": "شارك فرصتك الاستثمارية أو التعاونية مع المستثمرين العالميين عبر غرفة قطر.",
           "groups": ["المعلومات الأساسية", "تفاصيل الفرصة", "الوسائط والمستندات", "معلومات التواصل"],
           "hints": ["PNG أو JPG · الحد الأقصى 2 ميجابايت", "PNG أو JPG · الحد الأقصى 2 ميجابايت",
                     "قم بتحميل الصور المكتملة، بحد أقصى 10 صور.", "قم بتحميل ملف PDF مكتمل، بحد أقصى 5 ميجابايت."]},
}
GROUP_FIELDS_EN = [
    ["Project / Opportunity Name (EN)", "Project / Opportunity Name (AR)", "Sector", "Sub-Sector", "Country",
     "Company / Organization Name"],
    ["Investment Brief (EN)", "Investment Brief (AR)", "Key Highlights", "Investment Amount", "Currency",
     "Investment Type", "Timeline", "Risk Profile", "Industry Pool"],
    ["Banner Image", "Opportunity Logo", "Gallery Images", "Supporting Documents"],
    ["Contact Information", "Contact Email", "Mobile Number", "Website"],
]


def _design_diffs(sp: SubmitBusinessOpportunityPage, mode: str, locale: str, viewport: str) -> list:
    """Live vs Figma, Rule 1 tolerances: text/colour exact, layout ±2, images ±5."""
    fig, copy, diffs = FIGMA[mode], COPY[locale], []

    def chk(name, live, exp, tol=None):
        ok = (abs(float(live) - float(exp)) <= tol) if tol is not None else live == exp
        if not ok:
            diffs.append(f"[{locale}/{mode}/{viewport}] {name}: Figma {exp!r} vs live {live!r}")

    s = sp.style
    title, sub, icon = s(sp.PAGEHEAD_TITLE), s(sp.PAGEHEAD_SUB), s(sp.PAGEHEAD_ICON)
    chk("page background", s(".qc-bos__body")["background"], fig["page_bg"])
    chk("form title copy", title["text"], copy["title"])
    chk("form title font", (title["fontSize"], title["fontWeight"], title["lineHeight"]), ("18px", "600", "28px"))
    chk("form title colour", title["color"], fig["title_color"])
    chk("subtitle copy", sub["text"], copy["sub"])
    chk("subtitle font", (sub["fontSize"], sub["fontWeight"], sub["lineHeight"]), ("12px", "400", "18px"))
    chk("subtitle colour", sub["color"], fig["sub_color"])
    chk("title icon width", icon["width"], 44, 5)
    chk("title icon background", icon["background"], fig["icon_bg"])
    chk("group headers", sp.group_header_texts(), copy["groups"])
    grp = s(sp.GROUP_HEADER)
    chk("group header font", (grp["fontSize"], grp["fontWeight"], grp["lineHeight"], grp["color"]),
        ("16px", "700", "24px", "rgb(166, 111, 67)"))
    chk("group divider colour", s(sp.GROUP_RULE)["background"], fig["rule"])
    label, req = s(sp.LABEL), s(sp.REQUIRED_MARK)
    chk("field label font", (label["fontSize"], label["fontWeight"], label["lineHeight"]), ("14px", "600", "22px"))
    chk("field label colour", label["color"], fig["label_color"])
    chk("required asterisk", (req["color"], req["fontWeight"]), (fig["req_color"], "700"))
    inp = s(sp.field("name_en"))
    chk("input height", inp["height"], 46, 2)
    chk("input radius", inp["radius"], "8px")
    chk("input border", (inp["borderWidth"], inp["borderColor"]), ("1px", fig["input_border"]))
    chk("placeholder colour", s(sp.field("name_en"), "::placeholder")["color"], fig["placeholder"])
    chk("textarea height", s(sp.field("investment_brief_en"))["height"], 72, 2)
    drop, dicon = s(sp.DROP_ZONE), s(sp.DROP_ICON)
    chk("upload zone border", (drop["borderStyle"], drop["borderColor"], drop["radius"]),
        ("dashed", fig["drop_border"], "12px"))
    chk("upload icon size", dicon["width"], 40, 5)
    chk("upload icon background", dicon["background"], fig["drop_icon_bg"])
    strong, rest, hint = s(sp.DROP_STRONG), s(sp.DROP_REST), s(sp.DROP_HINT)
    chk("'Click to upload'", (strong["fontSize"], strong["fontWeight"], strong["lineHeight"], strong["color"]),
        ("14px", "600", "22px", fig["drop_strong"]))
    chk("'or drag and drop'", (rest["fontSize"], rest["fontWeight"], rest["color"]), ("14px", "400", fig["drop_rest"]))
    chk("upload hint font", (hint["fontSize"], hint["fontWeight"], hint["lineHeight"], hint["color"]),
        ("12px", "400", "18px", "rgb(168, 168, 167)"))
    chk("upload hint copy", sp.drop_hints(), copy["hints"])
    dial = s(sp.DIAL_CODE)
    chk("+974 text", (dial["fontSize"], dial["fontWeight"], dial["color"]), ("14px", "400", fig["dial"]))
    btn = s(sp.SUBMIT_BUTTON)
    chk("Submit background", btn["background"], "rgb(145, 23, 49)")
    chk("Submit pill radius (>= height/2)", float(btn["radius"].rstrip("px")) >= btn["height"] / 2 - 1, True)
    chk("Submit label font", (btn["fontSize"], btn["fontWeight"], btn["lineHeight"]), ("16px", "600", "24px"))
    chk("Submit full form width", btn["width"], s(sp.FORM)["width"], 2)
    hero = s(sp.HERO_TITLE)
    chk("hero title font", (hero["fontSize"], hero["fontWeight"], hero["lineHeight"]),
        ("30px", "700", "38px") if viewport == "desktop" else ("20px", "700", "30px"))
    if viewport == "mobile":
        chk("mobile side gutter", s(sp.FORM)["x"], 20, 2)
        chk("no horizontal scroll", sp.has_horizontal_scroll(), False)
    return diffs


def _render_matrix(sp, page, locale: str) -> list:
    from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

    diffs = []
    for viewport, size in (("desktop", (1920, 1080)), ("mobile", (390, 844))):
        page.set_viewport_size({"width": size[0], "height": size[1]})
        for mode in ("light", "dark"):
            sp.open_submit_form(locale=locale)
            if mode == "dark":
                AccessibilityToolsComponent(page).enable_dark_mode()
                page.wait_for_timeout(500)
            diffs += _design_diffs(sp, mode, locale, viewport)
            evidence(page, f"w1_{locale}_{viewport}_{mode}_form")
            if mode == "dark":  # back to light for the next pass
                AccessibilityToolsComponent(page).open_panel().switch_to_dark_mode().close_panel()
    return diffs


@case("143260", title="The webform renders its 4 field groups (EN) as designed", story="Layout", prio=3, cats=("ui",))
def test_four_field_groups_match_figma(page, fx):
    sp = guarded_form(page)
    assert sp.group_header_texts() == COPY["en"]["groups"]  # case says "Basic Info"; Figma/live "Basic Information"
    assert sp.group_labels() == GROUP_FIELDS_EN, sp.group_labels()
    assert sp.page.locator(sp.SUBMIT_BUTTON).is_visible() and sp.text(sp.SUBMIT_LABEL).strip() == "Submit"
    allure.dynamic.description(f"Figma frames: {FIG_EN_D} / {FIG_EN_D_DARK} (desktop), {FIG_EN_M} (mobile 390).")
    diffs = _render_matrix(sp, page, "en")
    attach_json("EN design differences", diffs)
    assert not sp.is_captcha_visible(), "captcha unexpectedly visible"
    assert not diffs, "Design differs from Figma:\n" + "\n".join(diffs)


@case("143261", title="The webform renders correctly in Arabic RTL", story="Layout", prio=3, cats=("ui", "bilingual", "rtl"))
def test_arabic_rtl_rendering(page, fx):
    sp = guarded_form(page, locale="ar")
    assert sp.document_direction() == "rtl"
    assert sp.group_header_texts() == COPY["ar"]["groups"]
    label, field = sp.style("label[for=qc-bos-projectOpportunityName]"), sp.style(sp.field("name_en"))
    assert label["direction"] == "rtl"
    assert abs((label["x"] + label["width"]) - (field["x"] + field["width"])) <= 2, "label not right-aligned to its field"
    sp.fill_field("name_ar", "توسعة مجمع الطاقة الشمسية")
    sp.fill_field("investment_brief_ar", "ملخص استثماري باللغة العربية")
    assert sp.style(sp.field("name_ar"))["direction"] == "rtl"
    assert sp.style(sp.field("investment_brief_ar"))["direction"] == "rtl"
    sector_options = sp.option_labels("sector")
    attach_json("AR sector options", sector_options)
    allure.dynamic.description(f"Figma frames: {FIG_AR_D} / {FIG_AR_D_DARK} (desktop), {FIG_AR_M} (mobile 390). "
                               "Lookup labels '... (AR)' are known bug 149514.")
    diffs = _render_matrix(sp, page, "ar")
    if any(o.endswith("(AR)") for o in sector_options):
        diffs.append("[ar] Sector options are placeholder labels like 'Energy (AR)' (known bug 149514)")
    attach_json("AR design differences", diffs)
    assert not diffs, "Arabic rendering differs from Figma:\n" + "\n".join(diffs)

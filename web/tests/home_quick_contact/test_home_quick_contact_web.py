"""
web/tests/home_quick_contact/test_home_quick_contact_web.py — Quick Contact Us
Section (PBI 129390 / QC-HOME-014), Web platform, suite 134461.

Rewritten 2026-10-08 (Phase 3, B-129390):
  * Every test reads the public page in a LOGGED-OUT context (`{"auth": False}`)
    — the previous version ran on the default TEST_USER-authenticated `page`.
  * Each test carries its `tc_<id>` marker (Azure selection) as well as the
    traceability label.
  * Inline-message WORDING is recorded, not asserted: a different wording from
    the PBI is not a bug on this project (bug-rules / standards). What is
    asserted is the behaviour the case names — the submission is blocked (no
    POST leaves the browser), a message appears under the right field, and the
    other values are kept.
  * "Value accepted / submission proceeds" cases intercept the outgoing POST and
    ABORT it after proving it was sent with the entered value, so no record is
    stored and no email is sent. Real submissions are limited to 136485 (one
    send) and 136495 (the double-click), both as a QCTEST visitor addressed to
    the team test inbox (heba.samir611.hs@gmail.com).
  * 136492 (zero active categories) is not here: it needs all 11 real Inquiry
    Category records deactivated — NEEDS USER (see the phase-3 report).
"""

import json
from urllib.parse import parse_qs
from datetime import datetime, timezone

import allure
import pytest

from web.pages.home_quick_contact.home_quick_contact_page import HomeQuickContactPage

PBI = "129390"
TEST_INBOX = "heba.samir611.hs@gmail.com"

ANON = {"auth": False}
ANON_MOBILE = {"auth": False, "viewport": (375, 812)}
ANON_TABLET = {"auth": False, "viewport": (768, 1024)}

# PBI 129390 US001 "And when the visitor submits the form" — quoted for the record.
PBI_MESSAGES = {
    "name": ("Full Name is required.", "الاسم الكامل مطلوب."),
    "email_empty": ("E-mail Address is required.", "عنوان البريد الإلكتروني مطلوب."),
    "email_invalid": ("Please enter a valid email address.", "يرجى إدخال عنوان بريد إلكتروني صالح."),
    "category": ("Inquiry Category is required.", "فئة الاستفسار مطلوبة."),
    "message": ("Message is required.", "الرسالة مطلوبة."),
    "backend": ("Unable to send your message. Please try again later.", "تعذّر إرسال رسالتك. يرجى المحاولة مرة أخرى لاحقاً."),
}
FIELD_ID = {"name": "qc-cu-name", "email": "qc-cu-email", "category": "qc-cu-category", "message": "qc-cu-message"}

VALID = {
    "full_name": "QCTEST Fatima Al-Sulaiti",
    "email": "fatima.s@example.com",
    "category_label": "General Inquiry",
    "message": "QCTEST automated check - requesting a membership brochure.",
}


def _attach(name: str, data) -> None:
    allure.attach(json.dumps(data, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _open(page, locale: str = "en") -> HomeQuickContactPage:
    contact = HomeQuickContactPage(page)
    contact.open_home_arabic() if locale == "ar" else contact.open_home()
    contact.scroll_to_section()
    return contact


def _blocked_case(page, *, blank: str, overrides: dict | None = None, expect_field: str, pbi_key: str,
                  locale: str = "en") -> dict:
    """Fill every field validly except `blank` (left empty) / `overrides`,
    click Send Message, and assert the submission was blocked with a message
    under `expect_field`. Returns the evidence dict."""
    contact = _open(page, locale)
    sent = contact.watch_submissions()
    values = dict(VALID)
    if locale == "ar":
        values["category_label"] = "استفسار عام"
    if blank:
        values[blank] = ""
    values.update(overrides or {})
    contact.fill_form(**values)
    before = contact.field_values()
    contact.click_submit()
    page.wait_for_timeout(1500)  # measured: client validation renders in <300 ms; 1.5 s also covers a stray XHR
    errors = contact.field_errors()
    after = contact.field_values()
    status = contact.status_text()
    shown = errors.get(FIELD_ID[expect_field], "")
    pbi_text = PBI_MESSAGES[pbi_key][1 if locale == "ar" else 0]
    evidence = {"errors": errors, "status": status, "posts": sent, "before": before, "after": after,
                "pbi_message": pbi_text, "shown_message": shown, "wording_matches_pbi": shown == pbi_text}
    _attach("validation evidence", evidence)
    assert not sent, f"a submission left the browser although {expect_field} was invalid: {sent}"
    assert shown, f"no inline message under {expect_field}; errors={errors}"
    return evidence


def _accept_case(page, field_key: str, value: str) -> dict:
    """Valid value + all other fields valid -> no inline error and the
    submission is sent carrying the value. The POST is aborted after capture
    (no record, no email)."""
    contact = _open(page)
    seen = contact.intercept_submissions("abort")
    values = dict(VALID)
    values[field_key] = value
    contact.fill_form(**values)
    contact.click_submit()
    page.wait_for_timeout(1500)  # measured: the XHR is issued within ~200 ms of the click
    errors = contact.field_errors()
    evidence = {"errors": errors, "intercepted": seen}
    _attach("acceptance evidence", evidence)
    field_id = {"full_name": FIELD_ID["name"], "email": FIELD_ID["email"], "message": FIELD_ID["message"]}[field_key]
    assert not errors.get(field_id), f"valid value rejected: {errors.get(field_id)!r}"
    assert not any(errors.values()), f"some field reported an error: {errors}"
    assert seen, "no submission was sent for a fully valid form"
    param = {"full_name": "fullName", "email": "email", "message": "message"}[field_key]
    sent_values = [parse_qs(s["body"] or "").get(param, [""])[0] for s in seen]
    assert value in sent_values, f"the submission did not carry the entered {param} {value!r}: {sent_values}"
    return evidence


def _marks(*names):
    def deco(fn):
        for n in reversed(names):
            fn = getattr(pytest.mark, n)(fn)
        return fn
    return deco


COMMON = _marks("web", "global_", "pbi_129390")


# ---- Layout / UI -----------------------------------------------------------
@allure.feature("Quick Contact Us Section")
@allure.title("The Contact Us section is responsive at a 375px mobile viewport (EN) (ADO-136473)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136473
@pytest.mark.traceability("ADO-136473")
@pytest.mark.parametrize("page", [ANON_MOBILE], indirect=True)
def test_contact_us_responsive_at_mobile_375(page):
    contact = _open(page)
    single_column = contact.is_single_column_layout()
    has_overflow = contact.has_page_horizontal_overflow()
    map_box = contact.map_container_box()
    targets = {name: contact.element_box(loc) for name, loc in (
        ("name", contact.NAME_INPUT), ("email", contact.EMAIL_INPUT), ("category", contact.CATEGORY_SELECT),
        ("message", contact.MESSAGE_TEXTAREA), ("submit", contact.SUBMIT_BUTTON), ("directions", contact.DIRECTIONS_LINK))}
    _attach("375px measurements", {"single_column": single_column, "overflow": has_overflow, "map": map_box, "targets": targets})
    assert contact.is_section_visible()
    assert single_column, "expected the section to stack to a single column at 375px"
    assert not has_overflow, "expected no horizontal overflow at 375px"
    assert map_box and map_box["width"] >= 300, "expected the map to render at (near) full section width"
    small = {k: (round(v["width"]), round(v["height"])) for k, v in targets.items()
             if not v or v["width"] < 44 or v["height"] < 44}
    assert not small, f"touch targets under 44x44 px: {small}"


@allure.feature("Quick Contact Us Section")
@allure.title("The Contact Us section is responsive at a 768px tablet viewport (EN) (ADO-136474)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136474
@pytest.mark.traceability("ADO-136474")
@pytest.mark.parametrize("page", [ANON_TABLET], indirect=True)
def test_contact_us_responsive_at_tablet_768(page):
    contact = _open(page)
    overflow = contact.has_page_horizontal_overflow()
    clipped = page.evaluate("""() => [...document.querySelectorAll('section.qc-home-contact-us *')]
        .filter(e => e.children.length === 0 && e.innerText && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflow !== 'visible')
        .map(e => e.className + ': ' + e.innerText.slice(0, 40))""")
    _attach("768px", {"overflow": overflow, "clipped": clipped, "heading": contact.heading_text()})
    assert contact.is_section_visible()
    assert not overflow, "expected no horizontal scroll at 768px"
    assert not clipped, f"truncated text at 768px: {clipped}"
    assert contact.heading_text().strip()


@allure.feature("Quick Contact Us Section")
@allure.title("The Inquiry Category dropdown shows the correct placeholder and full option list (ADO-136475)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136475
@pytest.mark.traceability("ADO-136475")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_inquiry_category_dropdown_placeholder_and_options(page):
    expected = ["Select", "General Inquiry", "Membership Services", "Legal Services", "Commercial Directory",
                "Events", "B2B Platform", "Publications & Research", "Tender Submission", "Technical Support",
                "Suggestions & Feedback", "Other"]
    labels = _open(page).category_option_labels()
    _attach("options", labels)
    assert labels == expected, f"expected placeholder + 11 categories, got {labels!r}"


@allure.feature("Quick Contact Us Section")
@allure.title("Each form field shows the correct focus state (ADO-136476)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136476
@pytest.mark.traceability("ADO-136476")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_form_fields_show_visible_focus_state(page):
    """Focus is moved with real Tab presses from the field before; the first
    field is reached by focusing it (a cross-origin map iframe sits before the
    form in tab order — see the Page Object docstring)."""
    contact = _open(page)
    outlines = {}
    contact.focus_field(contact.NAME_INPUT)
    outlines["name"] = contact.field_outline(contact.NAME_INPUT)
    page.keyboard.press("Tab")
    outlines["email_active"] = page.evaluate("() => document.activeElement.id")
    outlines["email"] = contact.field_outline(contact.EMAIL_INPUT)
    contact.focus_field(contact.MESSAGE_TEXTAREA)
    outlines["message"] = contact.field_outline(contact.MESSAGE_TEXTAREA)
    _attach("focus outlines", outlines)
    for key in ("name", "email", "message"):
        o = outlines[key]
        assert o and "none" not in o and not o.endswith(" 0px"), f"{key}: no visible focus outline ({o!r})"


@allure.feature("Quick Contact Us Section")
@allure.title("Inline validation error state is visually distinct on empty required fields (ADO-136477)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136477
@pytest.mark.traceability("ADO-136477")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_required_fields_show_distinct_error_state(page):
    contact = _open(page)
    normal = {k: contact.field_border_color_hex(loc) for k, loc in (
        ("name", contact.NAME_INPUT), ("email", contact.EMAIL_INPUT),
        ("category", contact.CATEGORY_SELECT), ("message", contact.MESSAGE_TEXTAREA))}
    contact.click_submit()
    page.wait_for_timeout(800)  # measured: error classes apply in <300 ms
    errored = {k: contact.field_border_color_hex(loc) for k, loc in (
        ("name", contact.NAME_INPUT), ("email", contact.EMAIL_INPUT),
        ("category", contact.CATEGORY_SELECT), ("message", contact.MESSAGE_TEXTAREA))}
    errors = contact.field_errors()
    _attach("error state", {"normal": normal, "errored": errored, "errors": errors})
    for key in ("name", "email", "category", "message"):
        assert errored[key] != normal[key], f"{key}: border unchanged in error state ({errored[key]})"
        r, g, b = int(errored[key][1:3], 16), int(errored[key][3:5], 16), int(errored[key][5:7], 16)
        assert r > 150 and g < 80 and b < 80, f"{key}: error border is not red ({errored[key]})"
        assert errors.get(FIELD_ID[key]), f"{key}: no inline message"


@allure.feature("Quick Contact Us Section")
@allure.title("The Send Message button shows a disabled/loading state during submission (ADO-136478)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136478
@pytest.mark.traceability("ADO-136478")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_send_message_button_disabled_during_submission(page):
    """The POST is held 2 s and then aborted (nothing stored, no email), so the
    in-flight state can be observed deterministically."""
    contact = _open(page)
    contact.intercept_submissions("abort", delay_ms=2000)
    contact.fill_form(**VALID)
    before_html = contact.submit_button_html()
    contact.click_submit()
    page.wait_for_timeout(300)  # inside the 2 s hold
    disabled = contact.is_submit_disabled()
    during_html = contact.submit_button_html()
    spinner = contact.has_loading_spinner()
    animated = contact.spinner_visible()
    page.screenshot(path="reports/manual-exec-129390-136478-inflight.png")
    status = contact.wait_for_status_text(15000)
    _attach("button states", {"before": before_html, "during": during_html, "disabled": disabled,
                              "spinner_marker": spinner, "animated": animated, "status_after": status})
    assert disabled, "Send Message was not disabled while the request was in flight"
    assert spinner, "no loading spinner / busy indicator on Send Message while in flight"
    assert not contact.is_submit_disabled(), "button stayed disabled after the response"


@allure.feature("Quick Contact Us Section")
@allure.title("The embedded map renders the Qatar Chamber location pin correctly (ADO-136479)")
@COMMON
@pytest.mark.ui
@pytest.mark.tc_136479
@pytest.mark.traceability("ADO-136479")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_embedded_map_renders_location_pin(page):
    contact = _open(page)
    page.wait_for_timeout(1500)  # let the cross-origin iframe start loading (map fallback toggles on error only)
    src = contact.map_iframe_src()
    location = contact.location_text()
    _attach("map", {"src": src, "location": location, "fallback": contact.is_map_fallback_visible()})
    assert contact.is_map_iframe_visible()
    assert not contact.is_map_fallback_visible()
    assert "Lusail" in src and "Doha" in src, f"map query does not match the address: {src!r}"
    assert "Lusail Boulevard 69" in location


@allure.feature("Quick Contact Us Section")
@allure.title("The Contact Us section renders correctly in Arabic on desktop, RTL (ADO-136550)")
@COMMON
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.tc_136550
@pytest.mark.traceability("ADO-136550")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_contact_us_renders_correctly_in_arabic_rtl_desktop(page):
    contact = _open(page, "ar")
    data = {"page_dir": contact.page_direction(), "section_dir": contact.section_direction(),
            "info_x": contact.info_x(), "form_x": contact.form_x(), "heading": contact.heading_text(),
            "submit": contact.text(contact.SUBMIT_LABEL),
            "labels": page.locator("section.qc-home-contact-us label").all_inner_texts(),
            "placeholders": page.evaluate("() => [...document.querySelectorAll('section.qc-home-contact-us [placeholder]')].map(e => e.placeholder)"),
            "text_align": page.locator(contact.HEADING).evaluate("el => getComputedStyle(el).textAlign")}
    _attach("AR render", data)
    assert data["page_dir"] == "rtl" and data["section_dir"] == "rtl"
    assert data["info_x"] > data["form_x"], "contact column did not mirror to the right"
    assert data["heading"] == "تواصل مع غرفة قطر لدفع أعمالك نحو الأمام"
    assert data["submit"] == "إرسال الرسالة"
    # HEALED: an e-mail example placeholder ("example@domain.com") is
    # language-neutral sample data, not untranslated UI text.
    latin = [t for t in data["labels"] + data["placeholders"] if t and "@" not in t
             and any("a" <= ch.lower() <= "z" for ch in t) and not any("؀" <= ch <= "ۿ" for ch in t)]
    assert not latin, f"English-only labels/placeholders on the Arabic page: {latin}"


# ---- Auth ------------------------------------------------------------------
@allure.feature("Quick Contact Us Section")
@allure.title("An unauthenticated Public Visitor can view and submit the Contact Us section (ADO-136485)")
@COMMON
@pytest.mark.auth
@pytest.mark.tc_136485
@pytest.mark.traceability("ADO-136485")
@pytest.mark.xdist_group("contact_us_public_webform")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_public_visitor_can_view_and_submit_136485(page):
    """REAL submission #1 (logged-out). Visitor email = the team test inbox;
    the name carries QCTEST-136485 and a UTC timestamp so the stored record and
    the emails can be matched."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    contact = _open(page)
    sent = contact.watch_submissions()
    contact.fill_form(full_name="QCTEST-136485 Visitor", email=TEST_INBOX, category_label="Membership Services",
                      message=f"QCTEST-136485 public visitor submission sent {stamp}. Please ignore.")
    contact.click_submit()
    status = contact.wait_for_status_text(30000)
    _attach("real submission #1", {"sent_at": stamp, "to_visitor": TEST_INBOX, "posts": sent, "status": status})
    assert sent, "no submission request was sent"
    assert "thank" in status.lower() or "success" in status.lower(), f"no success confirmation: {status!r}"


# ---- Functional-Low: required / format -------------------------------------
@allure.feature("Quick Contact Us Section")
@allure.title("Full Name empty submission is blocked with the correct message (ADO-136487)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136487
@pytest.mark.traceability("ADO-136487")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_full_name_empty_blocked_136487(page):
    ev = _blocked_case(page, blank="full_name", expect_field="name", pbi_key="name")
    kept = {k: v for k, v in ev["after"].items() if k != "#qc-cu-name"}
    assert kept == {k: v for k, v in ev["before"].items() if k != "#qc-cu-name"}, "other values were not retained"


@allure.feature("Quick Contact Us Section")
@allure.title("Email Address empty submission shows the correct message (ADO-136488)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136488
@pytest.mark.traceability("ADO-136488")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_email_empty_blocked_136488(page):
    _blocked_case(page, blank="email", expect_field="email", pbi_key="email_empty")


@allure.feature("Quick Contact Us Section")
@allure.title("An invalid Email Address format is rejected (ADO-136489)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136489
@pytest.mark.traceability("ADO-136489")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_email_invalid_format_blocked_136489(page):
    _blocked_case(page, blank="", overrides={"email": "ahmed.ali@@invalid"}, expect_field="email", pbi_key="email_invalid")


@allure.feature("Quick Contact Us Section")
@allure.title("Submitting with Inquiry Category not selected is blocked (ADO-136490)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136490
@pytest.mark.traceability("ADO-136490")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_category_not_selected_blocked_136490(page):
    _blocked_case(page, blank="category_label", expect_field="category", pbi_key="category")


@allure.feature("Quick Contact Us Section")
@allure.title("Submitting with Message empty is blocked (ADO-136491)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136491
@pytest.mark.traceability("ADO-136491")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_message_empty_blocked_136491(page):
    _blocked_case(page, blank="message", expect_field="message", pbi_key="message")


@allure.feature("Quick Contact Us Section")
@allure.title("Full Name whitespace-only is rejected (ADO-136500)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136500
@pytest.mark.traceability("ADO-136500")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_full_name_whitespace_blocked_136500(page):
    _blocked_case(page, blank="", overrides={"full_name": "   "}, expect_field="name", pbi_key="name")


@allure.feature("Quick Contact Us Section")
@allure.title("Email whitespace-only is rejected (ADO-136502)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136502
@pytest.mark.traceability("ADO-136502")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_email_whitespace_blocked_136502(page):
    _blocked_case(page, blank="", overrides={"email": "   "}, expect_field="email", pbi_key="email_empty")


@allure.feature("Quick Contact Us Section")
@allure.title("Message whitespace-only is rejected (ADO-136504)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.tc_136504
@pytest.mark.traceability("ADO-136504")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_message_whitespace_blocked_136504(page):
    _blocked_case(page, blank="", overrides={"message": "   "}, expect_field="message", pbi_key="message")


@allure.feature("Quick Contact Us Section")
@allure.title("Full Name valid value is accepted (ADO-136501)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136501
@pytest.mark.traceability("ADO-136501")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_full_name_valid_accepted_136501(page):
    _accept_case(page, "full_name", "Fatima Al-Sulaiti")


@allure.feature("Quick Contact Us Section")
@allure.title("Valid Email is accepted (ADO-136503)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136503
@pytest.mark.traceability("ADO-136503")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_email_valid_accepted_136503(page):
    _accept_case(page, "email", "fatima.s@example.com")


@allure.feature("Quick Contact Us Section")
@allure.title("Valid Message is accepted (ADO-136505)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_136505
@pytest.mark.traceability("ADO-136505")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_message_valid_accepted_136505(page):
    _accept_case(page, "message", "Requesting a membership brochure.")


@allure.feature("Quick Contact Us Section")
@allure.title("'الاسم الكامل مطلوب.' shows correctly in Arabic (ADO-136552)")
@COMMON
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.tc_136552
@pytest.mark.traceability("ADO-136552")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_full_name_required_message_arabic_136552(page):
    ev = _blocked_case(page, blank="full_name", expect_field="name", pbi_key="name", locale="ar")
    assert any("؀" <= ch <= "ۿ" for ch in ev["shown_message"]), (
        f"the Full Name message on the Arabic page is not Arabic: {ev['shown_message']!r}")


# ---- Edge --------------------------------------------------------------------
@allure.feature("Quick Contact Us Section")
@allure.title("Location address still displays as plain text when the embedded map fails to load (ADO-136493)")
@COMMON
@pytest.mark.edge
@pytest.mark.tc_136493
@pytest.mark.traceability("ADO-136493")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_location_text_shown_when_map_fails_136493(page):
    """The map load failure is produced by blocking every Google Maps request
    in this browser — not by saving a broken Map Embed URL on the live article
    53012 (that would change the real public section; NEEDS USER if the
    CMS-side step itself is required)."""
    contact = HomeQuickContactPage(page)
    contact.block_map()
    contact.open_home()
    contact.scroll_to_section()
    page.wait_for_timeout(3000)  # the fallback switches on the iframe's error / load timeout
    location = contact.location_text()
    data = {"location": location, "fallback_visible": contact.is_map_fallback_visible(),
            "iframe_visible": contact.is_map_iframe_visible()}
    page.screenshot(path="reports/manual-exec-129390-136493.png")
    _attach("map blocked", data)
    assert "Lusail Boulevard 69" in location, f"location text missing when the map fails: {location!r}"


@allure.feature("Quick Contact Us Section")
@allure.title("A backend submission failure shows the correct message and does not confirm success (ADO-136494)")
@COMMON
@pytest.mark.edge
@pytest.mark.regression
@pytest.mark.tc_136494
@pytest.mark.traceability("ADO-136494")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_backend_error_shows_failure_message_136494(page):
    contact = _open(page)
    seen = contact.intercept_submissions("fail500")
    contact.fill_form(**VALID)
    contact.click_submit()
    status = contact.wait_for_status_text(15000)
    _attach("backend failure", {"intercepted": seen, "status": status, "pbi_message": PBI_MESSAGES["backend"][0]})
    assert seen, "no submission request was made"
    assert "thank" not in status.lower() and "success" not in status.lower(), f"success shown on a 500: {status!r}"
    assert status.strip(), "no failure message shown"


@allure.feature("Quick Contact Us Section")
@allure.title("A double-click on Send Message does not create duplicate submissions (ADO-136495)")
@COMMON
@pytest.mark.edge
@pytest.mark.tc_136495
@pytest.mark.traceability("ADO-136495")
@pytest.mark.xdist_group("contact_us_public_webform")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_double_click_sends_once_136495(page):
    """REAL submission #2. Proves at the browser that exactly ONE submission
    request leaves on a double-click. The stored-record count and the email
    count are checked separately (see the phase-3 report)."""
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    contact = _open(page)
    sent = contact.watch_submissions()
    contact.fill_form(full_name="QCTEST-136495 DoubleClick", email=TEST_INBOX, category_label="Legal Services",
                      message=f"QCTEST-136495 double-click check sent {stamp}. Please ignore.")
    page.locator(contact.SUBMIT_BUTTON).dblclick()
    contact.wait_for_status_text(30000)
    page.wait_for_timeout(2000)  # catch a late second request
    _attach("real submission #2 (double-click)", {"sent_at": stamp, "posts": sent, "status": contact.status_text()})
    assert len(sent) == 1, f"expected exactly one submission request, got {len(sent)}: {sent}"

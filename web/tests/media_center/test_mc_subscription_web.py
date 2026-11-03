"""
web/tests/media_center/test_mc_subscription_web.py — FE-SUBS (PBI 130709 Media
Center Home Page, Azure plan 137724 / suite 140368, batch 3 FRONTEND).

Public subscription band (subscribe valid / empty / already-subscribed /
reactivation / letter case / double-click / keyboard), the unsubscribe-link
page (confirmation, used link, invalid link EN/AR), responsive + RTL + Figma
rendering of the band.

Disclosed adaptations (rules p3_rules_130709.md, batch 3 + the FE-SUBS brief):
- Every public step runs in a FRESH logged-out context.
- Case addresses (qctest.mchub+NN@example.com / qa.mchub+NN@<QA_MAILBOX_DOMAIN>)
  are replaced by FE-SUBS's own qctest.mchub.fe+<azureId>-<stamp>@example.com.
  The subscribe endpoint is rate-limited ("Too many attempts", HTTP 429), so
  ONE address (A, created by 149138) is reused along the chain the cases allow:
  149138 new -> 149141/149143 already-active (one shared resubmission) ->
  149170 upper-case -> 149166/149167 tampered link -> 149146 real link ->
  149169 reopened link -> 149144 reactivation. Throttled attempts are retried
  (anti-abuse limit, not a finding).
- Record checks: the cases name the QC Site Content Editor, whose login is locked
  out on qcdev since 2026-10-18; the read-only checks run as TEST_USER
  (Administrator, rules 2026-10-07) on the same list + its REST read.
- Unsubscribe-link cases: no inbox. The link the email carries
  (/web/qatar-chamber/newsletter-unsubscribe?token=<record's unsubscribeToken>)
  is opened logged out; the token is read from the record. Mailbox steps are
  out of scope.
- Subscriber rows cannot be deleted: every address is left Unsubscribed (module
  teardown) and logged to reports/mc130709/FE-SUBS/addresses.jsonl.
"""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import datetime, timedelta

import allure
import pytest

from core.web.browser import new_context
from web.pages.media_center.mc_search_page import McHeroSearch
from web.pages.media_center.mc_subscription_page import (
    EVIDENCE_DIR,
    McSubscriberRecords,
    McSubscriptionBand,
    McUnsubscribeLinkPage,
    own_address,
    parse_iso,
    utc_now,
)
from web.pages.media_center.mc_ui_page import MediaCenterUiPage
# Pure comparison helpers already used by the FE-UI Figma cases (same tolerances).
from web.tests.media_center.test_mc_ui_web import (  # noqa: E402
    DURATION,
    PHOTO_BADGE,
    Checks,
    _columns,
    _is_arabic,
    _norm_quotes,
    _overlap,
    _pill_cta,
    _right_aligned,
)

pytestmark = [pytest.mark.web, pytest.mark.media, pytest.mark.pbi_130709,
              pytest.mark.xdist_group("mc_fesubs_130709")]

EPIC = "Media Center Home Page (PBI 130709)"
FEATURE = "FE-SUBS — subscription band & unsubscribe link"
P = MediaCenterUiPage

DESKTOP = {"auth": False, "viewport": (1920, 1080)}
TABLET = {"auth": False, "viewport": (768, 1024)}
MOBILE_375 = {"auth": False, "viewport": (375, 812)}
MOBILE_390 = {"auth": False, "viewport": (390, 844)}

# FE_SUBS_STAMP lets a resumed run reuse the same address chain (rate-limited endpoint).
STAMP = os.environ.get("FE_SUBS_STAMP") or datetime.now().strftime("%m%d%H%M")
LEDGER = os.path.join(EVIDENCE_DIR, "addresses.jsonl")
TIME_TOLERANCE = timedelta(minutes=5)

HEADING_EN = "Stay connected to Qatar's business story"
DESCRIPTION_EN = "Receive selected news, publications, and media updates from Qatar Chamber."
PLACEHOLDER_EN = "Enter Your E-mail Address"
MSG_SUCCESS_EN = ("You have successfully subscribed to Media Center updates. "
                  "Thank you for staying connected with Qatar Chamber.")
MSG_SUCCESS_AR = "لقد اشتركت بنجاح في تحديثات المركز الإعلامي. شكرًا لتواصلك مع غرفة قطر."
MSG_DUPLICATE_EN = "This email address is already subscribed."
MSG_REQUIRED_EN = "This field is required."
MSG_REQUIRED_AR = "هذا الحقل مطلوب."
MSG_LINK_INVALID_EN = "This unsubscribe link is no longer valid."
MSG_LINK_INVALID_AR = "رابط إلغاء الاشتراك لم يعد صالحاً."

# Module chain state (see docstring): address A and what the chain learnt about it.
STATE: dict = {"created": []}


def _labels(tc: str, qa: str, title: str) -> None:
    allure.dynamic.epic(EPIC)
    allure.dynamic.feature(FEATURE)
    allure.dynamic.title(f"TC {tc} — {title}")
    allure.dynamic.label("testcase", tc)
    allure.dynamic.label("qa_id", qa)


def _attach(name: str, data) -> None:
    allure.attach(json.dumps(data, ensure_ascii=False, indent=1, default=str), name=name,
                  attachment_type=allure.attachment_type.JSON)


def _log(record: dict) -> None:
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(LEDGER, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"at": datetime.now().isoformat(timespec="seconds"), **record},
                                ensure_ascii=False, default=str) + "\n")


def _remember(email: str, tc: str, result: dict) -> None:
    if result.get("api_status") in ("success", "duplicate") and email.lower() not in STATE["created"]:
        STATE["created"].append(email.lower())
    _log({"tc": tc, "email": email, "api_status": result.get("api_status"), "message": result.get("text"),
          "attempts": result.get("attempts")})


@contextmanager
def _anon(browser, viewport=None):
    ctx = new_context(browser, use_auth_state=False, viewport=viewport)
    try:
        yield ctx.new_page()
    finally:
        ctx.close()


# ===========================================================================
# Fixtures
# ===========================================================================
@pytest.fixture(scope="module")
def records(browser):
    """READ-ONLY record-check session (QC Site Content Editor since 2026-10-20; TEST_USER earlier)."""
    ctx = new_context(browser, use_auth_state=False)
    rec = McSubscriberRecords(ctx.new_page())
    assert rec.sign_in() == "ok", "PRECONDITION: subscriber-list reader could not sign in"
    rec.open_list()
    yield rec
    ctx.close()


def _read(records: McSubscriberRecords, needle: str, exact: bool = True) -> list[dict]:
    """Record read with one re-login if the long-running admin session dropped."""
    for attempt in range(2):
        try:
            return records.record(needle) if exact else records.api_records(needle)
        except Exception:  # noqa: BLE001 — re-login once, then let it raise
            if attempt:
                raise
            records.sign_in()
            records.open_list()
    return []


def _subscribe_fresh(browser, email: str, tc: str, locale: str = "en", via: str = "click") -> dict:
    with _anon(browser) as pg:
        band = McSubscriptionBand(pg).open_hub(locale)
        result = band.subscribe_with_backoff(email, via=via)
        band.evidence(f"tc{tc}_precondition_subscribe", locator=band.SECTION)
    _remember(email, tc, result)
    return result


def _unsubscribe_via_link(browser, token: str, tc: str) -> dict:
    with _anon(browser) as pg:
        unsub = McUnsubscribeLinkPage(pg)
        unsub.open_link(token)
        first = unsub.state()
        final = unsub.confirm() if first["name"] == "confirm" else first
        unsub.evidence(f"tc{tc}_precondition_unsubscribe", full_page=True)
    return {"first": first, "final": final}


def _address_a() -> str:
    return STATE.setdefault("A", own_address("149138", STAMP))


def _ensure_a(browser, records, active: bool, tc: str) -> dict:
    """Brings A to the state a case's precondition needs (Active / Unsubscribed)
    and returns its one record; creates A when 149138 did not run."""
    email = _address_a()
    rows = _read(records, email)
    if not rows:
        result = _subscribe_fresh(browser, email, tc)
        assert result.get("api_status") == "success", f"PRECONDITION: could not create {email}: {result}"
        rows = _read(records, email)
    assert len(rows) == 1, f"PRECONDITION: expected one record for {email}, found {rows}"
    if bool(rows[0]["active"]) != active:
        if active:
            result = _subscribe_fresh(browser, email, tc)
            assert result.get("api_status") == "success", f"PRECONDITION: could not reactivate {email}: {result}"
        else:
            out = _unsubscribe_via_link(browser, rows[0]["unsubscribeToken"], tc)
            assert out["final"]["name"] in ("success", "already"), f"PRECONDITION: unsubscribe failed: {out}"
        rows = _read(records, email)
    assert len(rows) == 1 and bool(rows[0]["active"]) == active, f"PRECONDITION: {email} not in state: {rows}"
    return rows[0]


def _close_to(at, value, tolerance=TIME_TOLERANCE) -> bool:
    stamp = parse_iso(value)
    return stamp is not None and abs(stamp - at) <= tolerance


@pytest.fixture(scope="module", autouse=True)
def _leave_unsubscribed(browser, records):
    """Teardown: subscriber rows cannot be deleted — every FE-SUBS address still
    Active is unsubscribed through its own token link (logged out) and listed."""
    yield
    left = []
    for email in STATE["created"]:
        try:
            rows = _read(records, email)
            for _ in range(10):   # a just-created record can lag the API by a few seconds
                if rows:
                    break
                records.page.wait_for_timeout(3000)
                rows = _read(records, email)
            for row in rows:
                if row["active"]:
                    _unsubscribe_via_link(browser, row["unsubscribeToken"], "teardown")
            rows = _read(records, email)
            left.append({"code": email, "active": [r["active"] for r in rows],
                         "reason": "Newsletter subscriber rows are not deleted; unsubscribed via its own token link, "
                                   "left as Unsubscribed"})
        except Exception as exc:  # noqa: BLE001 — teardown reports, never masks
            left.append({"code": email, "reason": f"teardown error {exc!r}"})
    _log({"tc": "teardown", "left": left})
    with open(os.path.join(EVIDENCE_DIR, "leftovers.json"), "w", encoding="utf-8") as handle:
        json.dump(left, handle, ensure_ascii=False, indent=1)


# ===========================================================================
#  Read-only rendering cases
# ===========================================================================
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.tc_149055
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149055_hub_renders_all_sections_logged_out(page):
    """MEDIA-MCHUB-TC-001 — all hub sections incl. the band above the footer (logged out, EN desktop)."""
    _labels("149055", "MEDIA-MCHUB-TC-001", "hub renders every section for a logged-out visitor")
    band = McSubscriptionBand(page)
    status = band.http_status_of_hub("en")
    hub = MediaCenterUiPage(page).wait_until_rendered()
    c = Checks("TC 149055")
    c.eq(1, "HTTP status", status, 200)
    c.ok(1, "tab title contains 'Media Center'", "Media Center" in band.title(), band.title(), "contains 'Media Center'")
    c.ok(1, "logged-out visitor", not band.is_signed_in(), band.is_signed_in(), False)
    for loc, name in ((P.HERO_PAGE_LABEL, "page label"), (P.HERO_CRUMBS, "breadcrumb"), (P.HERO_HEADLINE, "headline"),
                      (P.HERO_DESCRIPTION, "description"), (P.HERO_SEARCH_FORM, "search bar")):
        c.ok(2, f"hero {name} displayed", hub.is_visible(loc), hub.is_visible(loc), True)
    c.eq(3, "count widgets displayed", hub.visible_count(P.COUNT_CARD), 5)
    c.eq(4, "'Explore the hub' eyebrow", hub.texts(P.QA_EYEBROW), ["Explore the hub"])
    c.eq(4, "quick-access cards displayed", hub.visible_count(P.QA_CARD), 6)
    c.eq(5, "feed section headings", hub.texts(P.NF_HEADING) + hub.texts(P.PF_HEADING) + hub.texts(P.VF_HEADING),
         ["News & press releases", "Photo Gallery", "Video Gallery"])
    band.scroll_to_band()
    copy = band.copy()
    c.ok(6, "band envelope icon displayed + loaded", copy["icon_visible"] and copy["icon"]["loaded"], copy["icon"], "visible")
    c.ok(6, "band heading displayed", bool(copy["heading"]), copy["heading"], "non-empty")
    c.ok(6, "band email field displayed", band.is_visible(band.INPUT), band.is_visible(band.INPUT), True)
    c.eq(6, "band button label", copy["button_label"], "Subscribe")
    pos = band.band_above_footer()
    c.ok(6, "band sits above the global footer", pos["band_bottom"] <= pos["footer_top"] + 1, pos, "band bottom <= footer top")
    band.evidence("tc149055_hub_full", full_page=True)
    c.done()


@pytest.mark.ui
@pytest.mark.tc_149062
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149062_band_copy_en(page):
    """MEDIA-MCHUB-TC-008 — band icon, heading, description, placeholder, Subscribe button (EN)."""
    _labels("149062", "MEDIA-MCHUB-TC-008", "band copy, field and button (EN)")
    band = McSubscriptionBand(page).open_hub("en").scroll_to_band()
    copy = band.copy()
    band.evidence("tc149062_band_en", locator=band.SECTION)
    _attach("band copy", copy)
    c = Checks("TC 149062")
    c.ok(1, "envelope icon displayed and loaded", copy["icon_visible"] and copy["icon"]["loaded"], copy["icon"], "visible")
    c.eq(2, "heading", copy["heading"], HEADING_EN)
    c.eq(2, "description", copy["description"], DESCRIPTION_EN)
    c.eq(3, "placeholder", copy["placeholder"], PLACEHOLDER_EN)
    c.eq(3, "button label", copy["button_label"], "Subscribe")
    c.ok(3, "button enabled", copy["button_enabled"], copy["button_enabled"], True)
    c.done()


@pytest.mark.ui
@pytest.mark.tc_149067
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149067_band_rtl_arabic_typed_email_ltr(page):
    """MEDIA-MCHUB-TC-013 — AR band RTL; a typed address stays an intact LTR run (no submit)."""
    _labels("149067", "MEDIA-MCHUB-TC-013", "Arabic band RTL; typed email stays LTR")
    band = McSubscriptionBand(page).open_hub("ar").scroll_to_band()
    copy, lay = band.copy(), band.layout()
    c = Checks("TC 149067")
    for key in ("heading", "description", "placeholder", "button_label"):
        c.ok(1, f"{key} in Arabic", _is_arabic(copy[key]), copy[key], "Arabic text")
    c.eq(1, "band direction", copy["section_dir"], "rtl")
    for key in ("heading", "description"):
        c.ok(1, f"{key} right-aligned", _right_aligned(lay[key]), f"{lay[key]['textAlign']}/{lay[key]['direction']}", "right")
    c.ok(1, "placeholder right-aligned (input)", _right_aligned(lay["input"]),
         f"{lay['input']['textAlign']}/{lay['input']['direction']}", "right")
    c.ok(1, "envelope icon on the right side", lay["icon"]["x"] >= lay["heading"]["right"] - 1,
         (lay["icon"]["x"], lay["heading"]["right"]), "icon right of the heading")
    typed = "qctest.mchub.fe+149067-" + STAMP + "@example.com"   # typed only, never submitted
    band.type_email(typed)
    order = band.typed_text_visual_order()
    band.evidence("tc149067_band_ar_typed", locator=band.SECTION)
    _attach("typed value layout", order)
    c.eq(2, "typed value kept intact", order["value"], typed)
    c.ok(2, "address renders as an LTR run (first char left of '@', '@' left of last char)",
         order["x_first"] < order["x_at"] < order["x_last"], order, "x_first < x_at < x_last")
    c.eq(2, "nothing was submitted", band.requests_sent(), [])
    c.done()


def _responsive_band(page, tc: str, check_stack_fit: bool) -> None:
    band = McSubscriptionBand(page).open_hub("en").scroll_to_band()
    doc, lay = band.document_state(), band.layout()
    band.evidence(f"tc{tc}_band_{doc['viewport'][0]}", locator=band.SECTION)
    _attach("layout", {"doc": doc, "layout": lay})
    c = Checks(f"TC {tc}")
    c.ok(1, "no horizontal scrollbar", doc["scroll_width"] <= doc["client_width"],
         f"scrollWidth {doc['scroll_width']} > clientWidth {doc['client_width']}", "scrollWidth <= clientWidth")
    parts = ("icon", "heading", "description", "input", "button")
    for name in parts:
        box = lay[name]
        c.ok(2, f"{name} visible", box["visible"], box, "visible")
        c.ok(2, f"{name} inside the viewport width", box["vx"] >= -0.5 and box["vright"] <= doc["client_width"] + 0.5,
             (box["vx"], box["vright"]), f"0..{doc['client_width']}")
        c.ok(2, f"{name} inside the band", box["x"] >= lay["band"]["x"] - 0.5 and box["right"] <= lay["band"]["right"] + 0.5,
             (box["x"], box["right"]), (lay["band"]["x"], lay["band"]["right"]))
    for i, a in enumerate(parts):
        for b in parts[i + 1:]:
            c.ok(2, f"{a} / {b} do not overlap", not _overlap(lay[a], lay[b]), (lay[a], lay[b]), "no overlap")
    if check_stack_fit:
        for name, loc in (("email field", band.INPUT), ("Subscribe button", band.BUTTON)):
            c.ok(2, f"{name} tappable (nothing covers its centre)", band.element_at_centre_is(loc),
                 False, True)
    c.done()


@pytest.mark.compatibility
@pytest.mark.tc_149079
@pytest.mark.parametrize("page", [TABLET], indirect=True)
def test_tc_149079_band_responsive_tablet(page):
    """MEDIA-MCHUB-TC-025 — band at 768x1024."""
    _labels("149079", "MEDIA-MCHUB-TC-025", "band responsive at 768x1024")
    _responsive_band(page, "149079", check_stack_fit=False)


@pytest.mark.compatibility
@pytest.mark.tc_149080
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_tc_149080_band_responsive_mobile(page):
    """MEDIA-MCHUB-TC-026 — band at 375x812; field + button fit and are tappable."""
    _labels("149080", "MEDIA-MCHUB-TC-026", "band responsive at 375x812")
    _responsive_band(page, "149080", check_stack_fit=True)


@pytest.mark.auth
@pytest.mark.tc_149085
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149085_anonymous_hub_search_and_subscribe_field(page):
    """MEDIA-MCHUB-TC-031 — logged-out: hub, hero search, subscription field without sign-in."""
    _labels("149085", "MEDIA-MCHUB-TC-031", "anonymous visitor: hub, search, subscription field")
    c = Checks("TC 149085")
    band = McSubscriptionBand(page)
    status = band.http_status_of_hub("en")
    MediaCenterUiPage(page).wait_until_rendered()
    c.eq(1, "hub HTTP status", status, 200)
    c.ok(1, "no sign-in redirect", "/login" not in page.url and "/c/portal/login" not in page.url, page.url, "hub URL")
    c.ok(1, "not signed in, no login form", not band.is_signed_in() and page.locator("input[type=password]").count() == 0,
         band.is_signed_in(), "anonymous")
    results = McHeroSearch(page).search("news")
    state = results.state()
    results.evidence("tc149085_search_results")
    c.ok(2, "search results page opened", "/media-search" in state["url"], state["url"], "/media-search")
    c.ok(2, "no login prompt on results", page.locator("input[type=password]").count() == 0 and "login" not in page.url,
         page.url, "no login")
    band.open_hub("en").scroll_to_band().focus_email_field()
    copy = band.copy()
    band.evidence("tc149085_field_focused", locator=band.SECTION)
    c.ok(3, "email field focused", band.input_is_focused(), False, True)
    c.ok(3, "email field editable", copy["input_editable"], copy["input_editable"], True)
    c.ok(3, "Subscribe button enabled", copy["button_enabled"], copy["button_enabled"], True)
    c.done()


@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_149159
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149159_empty_email_blocked_en(page):
    """MEDIA-MCHUB-TC-105 — empty field -> 'This field is required.', nothing sent."""
    _labels("149159", "MEDIA-MCHUB-TC-105", "empty email blocked (EN)")
    band = McSubscriptionBand(page).open_hub("en").scroll_to_band()
    c = Checks("TC 149159")
    c.eq(1, "field empty", band.input_value(), "")
    out = band.submit_without_request("click")
    band.evidence("tc149159_empty_en", locator=band.SECTION)
    _attach("outcome", out)
    c.eq(2, "inline error text", out["text"], MSG_REQUIRED_EN)
    c.ok(2, "rendered as an error (not success)", out["error"] and not out["ok"], out, "error state")
    c.eq(2, "no subscribe request sent", out["requests"], [])
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149160
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149160_empty_email_blocked_ar(page):
    """MEDIA-MCHUB-TC-106 — AR empty field -> 'هذا الحقل مطلوب.' RTL."""
    _labels("149160", "MEDIA-MCHUB-TC-106", "empty email blocked (AR)")
    band = McSubscriptionBand(page).open_hub("ar").scroll_to_band()
    c = Checks("TC 149160")
    c.eq(1, "field empty", band.input_value(), "")
    out = band.submit_without_request("click")
    band.evidence("tc149160_empty_ar", locator=band.SECTION)
    _attach("outcome", out)
    c.eq(2, "inline error text", out["text"], MSG_REQUIRED_AR)
    c.eq(2, "message rendered RTL", out["direction"], "rtl")
    c.eq(2, "no subscribe request sent", out["requests"], [])
    c.done()


MSG_INVALID_EN = "Please enter a valid email address."
MSG_INVALID_AR = "يرجى إدخال بريد إلكتروني صحيح."
MSG_DUPLICATE_AR = "هذا البريد الإلكتروني مشترك بالفعل"


@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.tc_149157
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149157_invalid_format_blocked_en(page, records):
    """MEDIA-MCHUB-TC-103 — 'qctest.mchub.example.com' (no @) -> 'Please enter a valid email address.', no record."""
    _labels("149157", "MEDIA-MCHUB-TC-103", "invalid email format blocked (EN), no record")
    value = "qctest.mchub.example.com"
    band = McSubscriptionBand(page).open_hub("en").type_email(value)
    c = Checks("TC 149157")
    c.eq(1, "value entered", band.input_value(), value)
    out = band.submit_without_request("click")
    band.evidence("tc149157_invalid_en", locator=band.SECTION)
    rows = _read(records, value, exact=False)
    _attach("outcome", {"out": out, "rows": rows})
    c.eq(2, "inline error text", out["text"], MSG_INVALID_EN)
    c.ok(2, "no success message", out["error"] and not out["ok"], out, "error state")
    c.eq(2, "no subscribe request sent", out["requests"], [])
    c.eq(3, "no subscriber record", rows, [])
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149158
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149158_invalid_format_blocked_ar(page):
    """MEDIA-MCHUB-TC-104 — AR 'qctest.mchub@' -> Arabic invalid-format message RTL, blocked."""
    _labels("149158", "MEDIA-MCHUB-TC-104", "invalid email format blocked (AR)")
    value = "qctest.mchub@"
    band = McSubscriptionBand(page).open_hub("ar").type_email(value)
    c = Checks("TC 149158")
    c.eq(1, "value entered", band.input_value(), value)
    out = band.submit_without_request("click")
    band.evidence("tc149158_invalid_ar", locator=band.SECTION)
    _attach("outcome", out)
    c.eq(2, "inline error text", out["text"], MSG_INVALID_AR)
    c.eq(2, "rendered RTL", out["direction"], "rtl")
    c.eq(2, "subscription blocked (no request)", out["requests"], [])
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149161
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149161_whitespace_only_is_empty(page):
    """MEDIA-MCHUB-TC-107 — three spaces -> 'This field is required.', nothing sent."""
    _labels("149161", "MEDIA-MCHUB-TC-107", "whitespace-only email treated as empty")
    band = McSubscriptionBand(page).open_hub("en").scroll_to_band()
    band.focus_email_field()
    page.keyboard.type("   ")
    c = Checks("TC 149161")
    c.ok(1, "field holds whitespace only", band.input_value().strip() == "", repr(band.input_value()), "whitespace")
    out = band.submit_without_request("click")
    band.evidence("tc149161_whitespace", locator=band.SECTION)
    _attach("outcome", out)
    c.eq(2, "inline error text", out["text"], MSG_REQUIRED_EN)
    c.ok(2, "no success message", not out["ok"], out, "no success")
    c.eq(2, "no subscribe request (no record can be stored)", out["requests"], [])
    c.done()


@pytest.mark.edge
@pytest.mark.tc_149179
def test_tc_149179_band_arabic_fallback():
    """MEDIA-MCHUB-TC-125 — NEEDS-DECISION (no disposable band entry possible)."""
    _labels("149179", "MEDIA-MCHUB-TC-125", "band falls back when Arabic content is missing")
    pytest.skip("NEEDS-DECISION: the band copy is read from the hero singleton QCDEMO-130709-HERO-MAIN "
                "(/o/c/mediacenterheros: subscriptionHeading/Description/...); a disposable QCTEST-130709-BAND-01 "
                "cannot exist and the case forbids editing real band content; the case also names the QC Site "
                "Content Editor, locked out since 2026-10-18.")


# ===========================================================================
#  Figma cases
# ===========================================================================
@pytest.mark.ui
@pytest.mark.tc_149346
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149346_figma_band_desktop_en(page):
    """MEDIA-MCHUB-TC-408 — band vs Figma 5461:196212 (Light, EN, 1920)."""
    _labels("149346", "MEDIA-MCHUB-TC-408", "band matches Figma (Light, EN, desktop)")
    hub = MediaCenterUiPage(page).open_hub("en")
    hub.scroll_into_view(P.SUB)
    hub.save_evidence("tc149346_band_desktop_en", full_page=False, folder="reports/mc130709/FE-SUBS")
    B = McSubscriptionBand
    c = Checks("TC 149346")
    band, grad, inner = hub.style(B.BAND), hub.style(B.GRADIENT), hub.style(B.INNER)
    tex, decor = hub.style(B.TEXTURE), hub.style(B.DECOR)
    c.px(1, "band width", band["box"]["w"], 1320)
    c.radius(1, "band", band, 20)
    c.pad(1, "band", band, 40, 40, 40, 40)
    c.gradient(1, "band", grad["backgroundImage"], 90, [("rgba(145,23,49,1)", 16), ("rgba(66,44,27,1)", 84)])
    c.ok(1, "decorative pattern layer", tex["backgroundImage"] != "none" or decor["backgroundImage"] != "none",
         (tex["backgroundImage"][:60], decor["backgroundImage"][:60]), "pattern present")
    c.eq(1, "content in one row", inner["flexDirection"], "row")
    c.px(1, "row gap", inner["gap"], 24, 0.5)
    icon, heading, desc = hub.style(B.ICON_CIRCLE), hub.style(B.HEADING), hub.style(B.DESCRIPTION)
    c.size(2, "icon circle", icon, 64, 64, 0.5)
    c.radius(2, "icon circle", icon, 9999)
    c.color(2, "icon circle fill", icon["backgroundColor"], "rgba(255,255,255,0.1)")
    c.ok(2, "icon on the left", icon["box"]["right"] <= heading["box"]["x"], (icon["box"]["right"], heading["box"]["x"]),
         "left of the heading")
    c.eq(2, "heading text (apostrophe style normalised)", _norm_quotes(heading["text"]), HEADING_EN)
    c.typo(2, "heading", heading, 24, 32, 700, "#FFFFFF")
    c.eq(2, "description text", desc["text"], DESCRIPTION_EN)
    c.typo(2, "description", desc, 16, 24, 400, "#F6F6F6")
    form, inp, btn = hub.style(B.FORM), hub.style(B.INPUT), hub.style(B.BUTTON)
    c.px(3, "form width", form["box"]["w"], 440)
    c.px(3, "form at the right end", inner["box"]["right"] - form["box"]["right"], 0)
    c.color(3, "input background", inp["backgroundColor"], "#FFFFFF")
    c.border(3, "input", inp, 1, "#EDEDED")
    c.radius(3, "input", inp, 8)
    c.pad(3, "input", inp, 11, 12, 11, 12)
    ph = hub.placeholder_style(B.INPUT)
    c.eq(3, "placeholder text", hub.placeholder(B.INPUT), PLACEHOLDER_EN)
    c.typo(3, "placeholder", {**ph, "lineHeight": inp["lineHeight"]}, 14, 22, 400, "#A8A8A7")
    c.px(3, "input-to-button gap", btn["box"]["x"] - inp["box"]["right"], 16)
    label, ico = hub.style(B.BUTTON_LABEL), hub.style(B.BUTTON_ICON)
    c.color(4, "button background", btn["backgroundColor"], "#FFFFFF")
    c.border(4, "button", btn, 1, "#911731")
    c.radius(4, "button", btn, 9999)
    c.pad(4, "button", btn, 10, 16, 10, 16)
    c.eq(4, "button label", label["text"], "Subscribe")
    c.typo(4, "button label", label, 16, 24, 600, "#911731")
    c.size(4, "send icon", ico, 20, 20, 0.5)
    c.ok(4, "send icon right of the label", ico["box"]["x"] >= label["box"]["right"], (ico["box"]["x"], label["box"]["right"]),
         "icon after label")
    c.done()


QA_AR = ["معرض الصور", "معرض الفيديو", "المنشورات", "مجلة الملتقى", "دليل الأعضاء", "طلبات الإعلاميين"]
FEEDS_AR = [  # (eyebrow, heading, CTA, eyebrow sel, heading sel, CTA sel)
    ("آخر التحديثات", "الأخبار والبيانات الصحفية", "كافة المقالات", P.NF_EYEBROW, P.NF_HEADING, P.NF_CTA_HEAD),
    ("بالصور", "معرض الصور", "كافة الألبومات", P.PF_EYEBROW, P.PF_HEADING, P.PF_CTA_HEAD),
    ("شاهد الآن", "معرض الفيديو", "شاهد الآن", P.VF_EYEBROW, P.VF_HEADING, P.VF_CTA_HEAD),
]


@pytest.mark.ui
@pytest.mark.tc_149350
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149350_figma_ar_cards_feeds_band(page):
    """MEDIA-MCHUB-TC-412 — explore cards, feeds and band mirrored RTL with the Arabic copy (Figma 5461:196214)."""
    _labels("149350", "MEDIA-MCHUB-TC-412", "AR explore-hub, feeds and band mirrored (Light, desktop)")
    hub = MediaCenterUiPage(page).open_hub("ar")
    hub.save_evidence("tc149350_ar_desktop", full_page=True, folder="reports/mc130709/FE-SUBS")
    c = Checks("TC 149350")
    # 1 — explore the hub
    eb, hd = hub.style(P.QA_EYEBROW), hub.style(P.QA_HEADING)
    c.eq(1, "eyebrow text", eb["text"], "استكشف المركز")
    c.color(1, "eyebrow colour", eb["color"], "#911731")
    c.ok(1, "header right-aligned", _right_aligned(eb) and _right_aligned(hd), (eb["textAlign"], hd["textAlign"]), "right")
    c.eq(1, "heading text", hd["text"], "كل شيء في مكان واحد")
    c.typo(1, "heading", hd, 24, None, 700, "#1D1D1B")
    cards, titles = hub.styles_all(P.QA_CARD), hub.texts(P.QA_TITLE)
    order = sorted(range(len(cards)), key=lambda i: (round(cards[i]["box"]["y"]), -cards[i]["box"]["x"]))
    c.eq(1, "3x2 grid read right-to-left", [titles[i] for i in order], QA_AR)
    for i in range(len(cards)):
        tile, title, arrow = hub.style(P.QA_ICON_TILE, i), hub.style(P.QA_TITLE, i), hub.style(P.QA_ARROW, i)
        c.color(1, f"card {i + 1} icon tile fill", tile["backgroundColor"], "#911731")
        c.ok(1, f"card {i + 1} icon tile on the RIGHT", tile["box"]["x"] >= title["box"]["right"] - 1,
             (tile["box"]["x"], title["box"]["right"]), "tile right of the text")
        c.ok(1, f"card {i + 1} text right-aligned", _right_aligned(title), f"{title['textAlign']}/{title['direction']}", "right")
        c.ok(1, f"card {i + 1} arrow at the LEFT end", arrow["box"]["right"] <= title["box"]["x"] + 1,
             (arrow["box"]["right"], title["box"]["x"]), "arrow left of the text")
        c.eq(1, f"card {i + 1} arrow points left", hub.icon_direction(P.QA_ARROW, i), "left")
    # 2 — feed headers + CTAs
    for eyebrow, heading, cta_text, s_eb, s_hd, s_cta in FEEDS_AR:
        e, h, cta = hub.style(s_eb), hub.style(s_hd), hub.style(s_cta)
        c.eq(2, f"'{heading}' eyebrow", e["text"], eyebrow)
        c.eq(2, f"'{heading}' heading", h["text"], heading)
        c.ok(2, f"'{heading}' eyebrow/heading right-aligned", _right_aligned(e) and _right_aligned(h),
             (e["textAlign"], h["textAlign"]), "right")
        c.ok(2, f"'{heading}' CTA on the left", cta["box"]["right"] <= h["box"]["x"] + 1, (cta["box"]["right"], h["box"]["x"]),
             "CTA left of the heading")
        _pill_cta(c, 2, f"'{heading}' CTA", cta, "#FFFFFF", "#DEDEDD", "#4A4A49", cta_text)
    # 3 — lead article + cards
    media, body = hub.style(P.NF_LEAD_MEDIA), hub.style(P.NF_LEAD_BODY)
    c.ok(3, "lead image on the RIGHT, text on the left", media["box"]["x"] >= body["box"]["right"] - 1,
         (media["box"]["x"], body["box"]["right"]), "image right of text")
    lead_title = hub.style(P.NF_LEAD_TITLE)
    c.ok(3, "lead text right-aligned", _right_aligned(lead_title), lead_title["textAlign"], "right")
    chips = hub.texts(P.NF_LEAD_CHIP)
    c.ok(3, "chips 'مميز' + category", len(chips) == 2 and chips[0] == "مميز", chips, "['مميز', <category>]")
    more = hub.style(P.NF_READ_MORE)
    c.eq(3, "Read more text", more["text"], "اقرأ المزيد")
    c.color(3, "Read more colour", more["color"], "#911731")
    c.eq(3, "Read more arrow points left", hub.icon_direction(P.NF_READ_MORE_ICON), "left")
    for sel, name in ((P.NF_CARD, "news"), (P.PF_CARD, "photo"), (P.VF_CARD, "video")):
        xs = [s["box"]["x"] for s in hub.styles_all(sel) if s["box"]["w"] > 0][:3]
        c.ok(3, f"{name} cards ordered newest at the right", xs == sorted(xs, reverse=True), xs, "x decreasing in DOM order")
    for media_sel, badge_sel, name in ((P.PF_CARD_MEDIA, P.PF_BADGE, "photo-count badge"),
                                       (P.VF_CARD_MEDIA, P.VF_DURATION, "duration badge")):
        m, b = hub.style(media_sel), hub.style(badge_sel)
        c.px(3, f"{name} pinned bottom-RIGHT (right inset)", m["box"]["right"] - b["box"]["right"], 16)
        c.px(3, f"{name} pinned bottom-RIGHT (bottom inset)", m["box"]["bottom"] - b["box"]["bottom"], 16)
    badge = hub.texts(P.PF_BADGE_TEXT)
    c.ok(3, "photo badge in Arabic ('<n> صورة')", bool(badge) and "صور" in badge[0], badge[:1], "'<n> صورة'")
    # 4 — band
    B = McSubscriptionBand
    hub.scroll_into_view(P.SUB)
    grad, icon, heading, desc = hub.style(B.GRADIENT), hub.style(B.ICON_CIRCLE), hub.style(B.HEADING), hub.style(B.DESCRIPTION)
    form, inp, btn, label = hub.style(B.FORM), hub.style(B.INPUT), hub.style(B.BUTTON), hub.style(B.BUTTON_LABEL)
    c.gradient(4, "band (mirrored)", grad["backgroundImage"], 90, [("rgba(66,44,27,1)", 16), ("rgba(145,23,49,1)", 84)])
    c.ok(4, "icon circle on the right", icon["box"]["x"] >= heading["box"]["right"] - 1, (icon["box"]["x"], heading["box"]["right"]),
         "icon right of the heading")
    c.eq(4, "band heading", heading["text"], "ابقَ على تواصل مع مشهد الأعمال في قطر")
    c.typo(4, "band heading", heading, 24, None, 700, "#FFFFFF")
    c.color(4, "band description colour", desc["color"], "#F6F6F6")
    c.ok(4, "heading/description right-aligned", _right_aligned(heading) and _right_aligned(desc),
         (heading["textAlign"], desc["textAlign"]), "right")
    c.ok(4, "form on the left", form["box"]["right"] <= heading["box"]["x"] + 1, (form["box"]["right"], heading["box"]["x"]),
         "form left of the text")
    c.eq(4, "button label", label["text"], "اشترك")
    c.ok(4, "'اشترك' button LEFT of the input", btn["box"]["right"] <= inp["box"]["x"] + 1, (btn["box"]["right"], inp["box"]["x"]),
         "button left of input")
    c.color(4, "button background", btn["backgroundColor"], "#FFFFFF")
    c.border(4, "button", btn, 1, "#911731")
    c.color(4, "button text", label["color"], "#911731")
    c.eq(4, "placeholder", hub.placeholder(B.INPUT), "ادخل البريد الالكتروني")
    c.ok(4, "placeholder right-aligned", _right_aligned(inp), f"{inp['textAlign']}/{inp['direction']}", "right")
    c.color(4, "placeholder colour", hub.placeholder_style(B.INPUT)["color"], "#A8A8A7")
    c.done()


def _one_column(c: Checks, step, name, styles, gap=24):
    styles = [s for s in styles if s["box"]["w"] > 0]
    c.eq(step, f"{name} stack in one column", _columns(styles), 1)
    for a, b in zip(styles, styles[1:]):
        c.px(step, f"{name} vertical gap", b["box"]["y"] - a["box"]["bottom"], gap)
    return styles


@pytest.mark.ui
@pytest.mark.tc_149352
@pytest.mark.parametrize("page", [MOBILE_390], indirect=True)
def test_tc_149352_figma_mobile_feeds_and_band(page):
    """MEDIA-MCHUB-TC-414 — mobile feeds + band vs Figma 5461:196278 (Light, EN, 390)."""
    _labels("149352", "MEDIA-MCHUB-TC-414", "mobile feeds and band stack per Figma")
    hub = MediaCenterUiPage(page).open_hub("en")
    hub.save_evidence("tc149352_mobile_en", full_page=True, folder="reports/mc130709/FE-SUBS")
    c = Checks("TC 149352")
    # 1 — news
    c.eq(1, "header CTA hidden (eyebrow + heading only)", hub.visible_count(P.NF_CTA_HEAD), 0)
    lead, media, body = hub.style(P.NF_LEAD), hub.style(P.NF_LEAD_MEDIA), hub.style(P.NF_LEAD_BODY)
    c.px(1, "lead image full width", media["box"]["w"], lead["box"]["w"])
    c.px(1, "lead image height", media["box"]["h"], 200, 5)
    c.radius(1, "lead image", media, 12)
    c.px(1, "lead image above the text (16px gap)", body["box"]["y"] - media["box"]["bottom"], 16)
    c.typo(1, "lead title", hub.style(P.NF_LEAD_TITLE), 18, 28, 700, "#343432")
    cards = _one_column(c, 1, "article cards", hub.styles_all(P.NF_CARD))
    for i in range(len(cards)):
        c.px(1, f"article card {i + 1} image height", hub.style(P.NF_CARD_MEDIA, i)["box"]["h"], 200, 5)
        c.typo(1, f"article card {i + 1} title", hub.style(P.NF_CARD_TITLE, i), 16, 24, 700, "#1D1D1B")
    foot = hub.style("a.qc-mc-nf-cta--foot")
    c.ok(1, "'View All Articles' BELOW the cards", hub.visible_count("a.qc-mc-nf-cta--foot") == 1 and cards
         and foot["box"]["y"] >= cards[-1]["box"]["bottom"], foot["box"], "below last card")
    # 2 — photos
    albums = _one_column(c, 2, "album cards", hub.styles_all(P.PF_CARD))
    for i in range(len(albums)):
        c.px(2, f"album {i + 1} cover height", hub.style(P.PF_CARD_MEDIA, i)["box"]["h"], 200, 5)
        c.typo(2, f"album {i + 1} title", hub.style(P.PF_CARD_TITLE, i), 16, 24, 700, None)
    badges = hub.texts(P.PF_BADGE_TEXT)
    c.ok(2, "'{n} photos' badge", bool(badges) and all(PHOTO_BADGE.match(b) for b in badges if b), badges, "'<n> photos'")
    pfoot = hub.style("a.qc-mc-pf-cta--foot")
    c.ok(2, "'View all albums' BELOW the cards", hub.visible_count("a.qc-mc-pf-cta--foot") == 1 and albums
         and pfoot["box"]["y"] >= albums[-1]["box"]["bottom"], pfoot["box"], "below last card")
    # 3 — videos
    videos = _one_column(c, 3, "video cards", hub.styles_all(P.VF_CARD))
    for i in range(len(videos)):
        c.px(3, f"video {i + 1} thumbnail height", hub.style(P.VF_CARD_MEDIA, i)["box"]["h"], 200, 5)
        c.typo(3, f"video {i + 1} title", hub.style(P.VF_CARD_TITLE, i), 16, 24, 700, None)
    c.color(3, "thumbnail overlay", hub.style(P.VF_SCRIM)["backgroundColor"], "rgba(29,29,27,0.3)")
    play = hub.style(P.VF_PLAY)
    c.size(3, "play button (~53px)", play, 53, 53, 2)
    c.radius(3, "play button", play, 9999)
    dur = hub.texts(P.VF_DURATION)
    c.ok(3, "duration badge", bool(dur) and DURATION.match(dur[0]) is not None, dur[:1], "'mm:ss'")
    head_cta, vhead = hub.style(P.VF_CTA_HEAD), hub.style(".qc-mc-vf-head")
    c.ok(3, "'Watch now' CTA shown in the header row", hub.visible_count(P.VF_CTA_HEAD) == 1
         and head_cta["box"]["y"] >= vhead["box"]["y"] - 1 and head_cta["box"]["bottom"] <= vhead["box"]["bottom"] + 1,
         {"head_cta_visible": hub.visible_count(P.VF_CTA_HEAD), "foot_cta_visible": hub.visible_count("a.qc-mc-vf-cta--foot")},
         "CTA in header row")
    # 4 — band
    B = McSubscriptionBand
    hub.scroll_into_view(P.SUB)
    band, icon, heading, desc = hub.style(B.BAND), hub.style(B.ICON_CIRCLE), hub.style(B.HEADING), hub.style(B.DESCRIPTION)
    inner, inp, btn, label = hub.style(B.INNER), hub.style(B.INPUT), hub.style(B.BUTTON), hub.style(B.BUTTON_LABEL)
    c.pad(4, "band", band, 24, 24, 24, 24)
    c.radius(4, "band", band, 20)
    c.size(4, "icon circle", icon, 48, 48, 0.5)
    c.color(4, "icon circle fill", icon["backgroundColor"], "rgba(255,255,255,0.1)")
    c.ok(4, "icon circle beside the heading (same row)", abs(icon["box"]["y"] - heading["box"]["y"]) <= 16
         and icon["box"]["right"] <= heading["box"]["x"], (icon["box"], heading["box"]), "icon left of heading, same row")
    c.px(4, "icon-heading gap", heading["box"]["x"] - icon["box"]["right"], 12)
    c.typo(4, "heading", heading, 18, 28, 700, "#FFFFFF")
    c.typo(4, "description", desc, 12, 18, 400, "#F6F6F6")
    c.px(4, "email input full width", inp["box"]["w"], inner["box"]["w"])
    c.px(4, "button stacked below the input (16px)", btn["box"]["y"] - inp["box"]["bottom"], 16)
    c.color(4, "button background", btn["backgroundColor"], "#FFFFFF")
    c.border(4, "button", btn, 1, "#911731")
    c.color(4, "button label", label["color"], "#911731")
    c.done()


# ===========================================================================
#  Subscription chain (rate-limited endpoint; address A reused — see docstring)
# ===========================================================================
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.tc_149138
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149138_new_email_subscribes_active_record(page, records):
    """MEDIA-MCHUB-TC-084 — new valid email -> EN confirmation + one Active record."""
    _labels("149138", "MEDIA-MCHUB-TC-084", "new valid email stores an Active record + EN confirmation")
    email = _address_a()
    assert not _read(records, email), f"PRECONDITION: {email} already has a record"
    band = McSubscriptionBand(page).open_hub("en")
    band.type_email(email)
    c = Checks("TC 149138")
    c.eq(1, "email entered", band.input_value(), email)
    result = band.subscribe_with_backoff(email)
    _remember(email, "149138", result)
    band.evidence("tc149138_step2_message", locator=band.SECTION)
    _attach("subscribe outcome", result)
    assert not result["throttled"], f"PRECONDITION: endpoint still throttled after {result['attempts']} attempts"
    c.eq(2, "confirmation text", result["text"], MSG_SUCCESS_EN)
    c.ok(2, "rendered as success", result["ok"], result["ok"], True)
    rows = _read(records, email)
    records.list_rows(email)
    records.evidence_rows("tc149138_step3_record")
    _attach("record", rows)
    c.eq(3, "exactly one record", len(rows), 1)
    if rows:
        r = rows[0]
        c.eq(3, "stored email", r["email"], email)
        c.eq(3, "status Active (active = true)", r["active"], True)
        c.ok(3, "subscription date = now", _close_to(result["at"], r["lastSubscribedOn"]), r["lastSubscribedOn"], result["at"])
        c.ok(3, "no un-subscription date", not r["lastUnsubscribedOn"], r["lastUnsubscribedOn"], "empty")
    c.done()


@pytest.fixture(scope="module")
def duplicate_round(browser, records):
    """ONE resubmission of the already-active address A, shared by 149141 and
    149143 (identical step: subscribe an already-active address again)."""
    before = _ensure_a(browser, records, active=True, tc="149141")
    with _anon(browser, viewport=(1920, 1080)) as pg:
        band = McSubscriptionBand(pg).open_hub("en")
        band.type_email(_address_a())
        entered = band.input_value()
        result = band.subscribe_with_backoff(_address_a())
        shot = band.evidence("tc149141_149143_resubmit", locator=band.SECTION)
    _remember(_address_a(), "149141/149143", result)
    after = _read(records, _address_a())
    records.list_rows(_address_a())
    records.evidence_rows("tc149143_step3_record")
    return {"before": before, "entered": entered, "result": result, "after": after, "shot": shot}


@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_149141
def test_tc_149141_already_subscribed_message_en(duplicate_round):
    """MEDIA-MCHUB-TC-087 — already-active email -> 'This email address is already subscribed.'"""
    _labels("149141", "MEDIA-MCHUB-TC-087", "already-active email shows the already-subscribed message")
    d = duplicate_round
    _attach("resubmission", d)
    assert not d["result"]["throttled"], "PRECONDITION: endpoint still throttled"
    c = Checks("TC 149141")
    c.eq(1, "email entered", d["entered"], _address_a())
    c.eq(2, "message text", d["result"]["text"], MSG_DUPLICATE_EN)
    c.ok(2, "no success confirmation", not d["result"]["ok"] and MSG_SUCCESS_EN not in d["result"]["text"],
         d["result"]["text"], "no success message")
    c.done()


@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.tc_149143
def test_tc_149143_already_subscribed_no_duplicate_record(duplicate_round):
    """MEDIA-MCHUB-TC-089 — resubmitting an active email keeps exactly one record, date unchanged."""
    _labels("149143", "MEDIA-MCHUB-TC-089", "already-active email creates no duplicate record")
    d = duplicate_round
    _attach("resubmission", d)
    assert not d["result"]["throttled"], "PRECONDITION: endpoint still throttled"
    c = Checks("TC 149143")
    c.ok(1, "one record before; date noted", bool(d["before"]["lastSubscribedOn"]), d["before"], "one record")
    c.eq(2, "already-subscribed message", d["result"]["text"], MSG_DUPLICATE_EN)
    c.eq(3, "still exactly one record", len(d["after"]), 1)
    if d["after"]:
        a = d["after"][0]
        c.eq(3, "same record id", a["id"], d["before"]["id"])
        c.eq(3, "status Active", a["active"], True)
        c.eq(3, "subscription date unchanged", a["lastSubscribedOn"], d["before"]["lastSubscribedOn"])
    c.done()


@pytest.mark.edge
@pytest.mark.tc_149170
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149170_upper_case_address_is_already_subscribed(page, browser, records):
    """MEDIA-MCHUB-TC-116 — same address in upper case -> already subscribed, no duplicate."""
    _labels("149170", "MEDIA-MCHUB-TC-116", "upper-case address treated as already subscribed")
    before = _ensure_a(browser, records, active=True, tc="149170")
    upper = _address_a().upper()
    band = McSubscriptionBand(page).open_hub("en")
    result = band.subscribe_with_backoff(upper)
    _remember(_address_a(), "149170", result)
    band.evidence("tc149170_step1_message", locator=band.SECTION)
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    local = _address_a().split("@")[0]
    rows = _read(records, local, exact=False)
    records.list_rows(local)
    records.evidence_rows("tc149170_step2_record")
    _attach("outcome", {"typed": upper, "result": result, "rows": rows})
    c = Checks("TC 149170")
    c.eq(1, "message", result["text"], MSG_DUPLICATE_EN)
    c.eq(2, "exactly one record", len(rows), 1)
    if rows:
        c.eq(2, "stored in lower case", rows[0]["email"], _address_a())
        c.eq(2, "status Active", rows[0]["active"], True)
        c.eq(2, "same record", rows[0]["id"], before["id"])
    c.done()


def _tampered(token: str) -> str:
    return token[:-4] + "ZZZZ"


@pytest.mark.functional_low
@pytest.mark.tc_149166
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149166_invalid_unsubscribe_link_en(page, browser, records):
    """MEDIA-MCHUB-TC-112 — tampered token (EN) -> 'This unsubscribe link is no longer valid.', record unchanged."""
    _labels("149166", "MEDIA-MCHUB-TC-112", "invalid unsubscribe link (EN)")
    rec = _ensure_a(browser, records, active=True, tc="149166")
    unsub = McUnsubscribeLinkPage(page)
    status = unsub.open_link(_tampered(rec["unsubscribeToken"]), "en")
    state, facts = unsub.state(), unsub.page_facts()
    unsub.evidence("tc149166_invalid_link_en", full_page=True)
    after = _read(records, _address_a())
    _attach("page", {"status": status, "state": state, "facts": facts, "after": after})
    c = Checks("TC 149166")
    c.eq(1, "site page opens (HTTP)", status, 200)
    c.ok(1, "no error page / stack trace", not facts["trace_like"] and state["name"] != "error", state, "site page")
    c.eq(2, "message", state["text"], MSG_LINK_INVALID_EN)
    c.ok(3, "record unchanged — still Active", len(after) == 1 and after[0]["active"] is True
         and after[0]["lastUnsubscribedOn"] == rec["lastUnsubscribedOn"], after, "Active, unchanged")
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149167
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149167_invalid_unsubscribe_link_ar(page, browser, records):
    """MEDIA-MCHUB-TC-113 — tampered token under /ar -> RTL page + Arabic invalid-link message."""
    _labels("149167", "MEDIA-MCHUB-TC-113", "invalid unsubscribe link (AR)")
    rec = _ensure_a(browser, records, active=True, tc="149167")
    unsub = McUnsubscribeLinkPage(page)
    status = unsub.open_link(_tampered(rec["unsubscribeToken"]), "ar")
    state, facts = unsub.state(), unsub.page_facts()
    unsub.evidence("tc149167_invalid_link_ar", full_page=True)
    _attach("page", {"status": status, "state": state, "facts": facts})
    c = Checks("TC 149167")
    c.eq(1, "page opens RTL", facts["html_dir"], "rtl")
    c.eq(2, "message", state["text"], MSG_LINK_INVALID_AR)
    c.done()


@pytest.mark.functional_high
@pytest.mark.tc_149146
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149146_unsubscribe_link_shows_confirmation(page, browser, records):
    """MEDIA-MCHUB-TC-092 — following the unsubscribe link shows the unsubscribe confirmation."""
    _labels("149146", "MEDIA-MCHUB-TC-092", "unsubscribe link shows the confirmation page")
    rec = _ensure_a(browser, records, active=True, tc="149146")
    unsub = McUnsubscribeLinkPage(page)
    status = unsub.open_link(rec["unsubscribeToken"], "en")
    opened, facts = unsub.state(), unsub.page_facts()
    unsub.evidence("tc149146_step1_link_opened", full_page=True)
    c = Checks("TC 149146")
    c.eq(1, "site page opens (HTTP)", status, 200)
    c.ok(1, "no error", opened["name"] != "error" and not facts["trace_like"], opened, "no error")
    c.eq(2, "following the link shows the unsubscribe confirmation (no further action)", opened["name"], "success")
    final = opened
    if opened["name"] == "confirm":
        # The link only asks for confirmation; completed with its own button so the
        # confirmation message (and the chain's Unsubscribed precondition) can be read.
        final = unsub.confirm()
        unsub.evidence("tc149146_step2_after_confirm", full_page=True)
    after = _read(records, _address_a())
    STATE["A_unsubscribed_on"] = after[0]["lastUnsubscribedOn"] if after else None
    STATE["A_token"] = rec["unsubscribeToken"]
    _attach("page", {"status": status, "opened": opened, "final": final, "facts": facts, "after": after})
    c.eq(2, "confirmation shown after the flow", final["name"], "success")
    c.ok(2, "message states the address was unsubscribed from Media Center updates",
         "unsubscribed" in final["text"].lower() and "Media Center" in final["text"], final["text"],
         "'... unsubscribed from Media Center updates'")
    c.ok(2, "record now Unsubscribed", len(after) == 1 and after[0]["active"] is False and bool(after[0]["lastUnsubscribedOn"]),
         after, "active=false + un-subscription date")
    c.done()


@pytest.mark.edge
@pytest.mark.tc_149169
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149169_reopened_used_link_no_second_unsubscription(page, browser, records):
    """MEDIA-MCHUB-TC-115 — reopening a used link: no error page, record/date unchanged (mailbox step out of scope)."""
    _labels("149169", "MEDIA-MCHUB-TC-115", "reopening a used unsubscribe link")
    rec = _ensure_a(browser, records, active=False, tc="149169")
    unsubscribed_on = rec["lastUnsubscribedOn"]
    unsub = McUnsubscribeLinkPage(page)
    status = unsub.open_link(rec["unsubscribeToken"], "en")
    state, facts = unsub.state(), unsub.page_facts()
    if state["name"] == "confirm":   # a second confirm would be the 'second un-subscription' the case guards
        state["confirm_offered_again"] = True
    unsub.evidence("tc149169_step1_reopened", full_page=True)
    after = _read(records, _address_a())
    records.list_rows(_address_a())
    records.evidence_rows("tc149169_step2_record")
    _attach("page", {"status": status, "state": state, "facts": facts, "before": rec, "after": after})
    c = Checks("TC 149169")
    c.eq(1, "HTTP", status, 200)
    c.ok(1, "unsubscribe confirmation or 'no longer valid' — no error page",
         state["name"] in ("success", "already", "invalid") and not facts["trace_like"], state,
         "confirmation / invalid message")
    c.eq(2, "one record", len(after), 1)
    if after:
        c.eq(2, "status Unsubscribed", after[0]["active"], False)
        c.eq(2, "original un-subscription date unchanged", after[0]["lastUnsubscribedOn"], unsubscribed_on)
    c.done()


@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.regression
@pytest.mark.tc_149144
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149144_resubscribe_reactivates_record(page, browser, records):
    """MEDIA-MCHUB-TC-090 — unsubscribed email subscribes again -> same record Active, date updated."""
    _labels("149144", "MEDIA-MCHUB-TC-090", "re-subscription reactivates the existing record")
    before = _ensure_a(browser, records, active=False, tc="149144")
    d1 = parse_iso(before["lastSubscribedOn"])
    band = McSubscriptionBand(page).open_hub("en")
    result = band.subscribe_with_backoff(_address_a())
    _remember(_address_a(), "149144", result)
    band.evidence("tc149144_step2_message", locator=band.SECTION)
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    after = _read(records, _address_a())
    records.list_rows(_address_a())
    records.evidence_rows("tc149144_step3_record")
    _attach("outcome", {"before": before, "result": result, "after": after})
    c = Checks("TC 149144")
    c.eq(1, "one record, Unsubscribed before", before["active"], False)
    c.eq(2, "English success confirmation", result["text"], MSG_SUCCESS_EN)
    c.eq(3, "still exactly one record", len(after), 1)
    if after:
        a = after[0]
        c.eq(3, "same record", a["id"], before["id"])
        c.eq(3, "status Active", a["active"], True)
        d2 = parse_iso(a["lastSubscribedOn"])
        c.ok(3, "subscription date updated to now (> D1)", d1 is not None and d2 is not None and d2 > d1
             and _close_to(result["at"], a["lastSubscribedOn"]), (d1, d2), "> D1, = now")
    c.done()


@pytest.mark.edge
@pytest.mark.tc_149168
def test_tc_149168_expired_unsubscribe_link():
    """MEDIA-MCHUB-TC-114 — NEEDS-DECISION (no link validity period exists to expire)."""
    _labels("149168", "MEDIA-MCHUB-TC-114", "expired unsubscribe link")
    pytest.skip("NEEDS-DECISION: the unsubscribe link carries the record's permanent unsubscribeToken (UUID); the "
                "page/lookup has no age check and the case's validity period is 'to be confirmed by development' — "
                "an expired link cannot be produced.")


@pytest.mark.ui
@pytest.mark.tc_149073
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149073_keyboard_enter_submits(page, records):
    """MEDIA-MCHUB-TC-019 — keyboard-only: Tab to the field (visible focus), type, Enter -> success."""
    _labels("149073", "MEDIA-MCHUB-TC-019", "keyboard-only subscription with Enter")
    email = own_address("149073", STAMP)
    assert not _read(records, email), f"PRECONDITION: {email} already has a record"
    band = McSubscriptionBand(page).open_hub("en")
    c = Checks("TC 149073")
    reached = band.tab_to_email_field()
    focus = band.email_focus_style()
    band.evidence("tc149073_step1_focus", locator=band.SECTION)
    c.ok(1, "email field reached with Tab", reached, reached, True)
    c.ok(1, "visible focus outline", (focus["outline_style"] not in ("none", "") and focus["outline_width"] != "0px")
         or focus["box_shadow"] not in ("none", ""), focus, "outline or focus ring")
    result = band.subscribe_with_backoff(email, via="enter", before_each=lambda b: b.tab_to_email_field())
    _remember(email, "149073", result)
    band.evidence("tc149073_step2_message", locator=band.SECTION)
    _attach("outcome", {"focus": focus, "result": result})
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    c.eq(2, "success confirmation", result["text"], MSG_SUCCESS_EN)
    c.ok(2, "submitted once", len(result["requests"]) == 1, result["requests"], "one request")
    c.done()


@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.tc_149139
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149139_arabic_confirmation(page, records):
    """MEDIA-MCHUB-TC-085 — subscribing from /ar shows the Arabic confirmation, RTL."""
    _labels("149139", "MEDIA-MCHUB-TC-085", "Arabic confirmation message")
    email = own_address("149139", STAMP)
    assert not _read(records, email), f"PRECONDITION: {email} already has a record"
    band = McSubscriptionBand(page).open_hub("ar")
    band.type_email(email)
    c = Checks("TC 149139")
    c.eq(1, "email entered", band.input_value(), email)
    result = band.subscribe_with_backoff(email)
    _remember(email, "149139", result)
    band.evidence("tc149139_step2_message_ar", locator=band.SECTION)
    _attach("outcome", result)
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    c.eq(2, "Arabic confirmation", result["text"], MSG_SUCCESS_AR)
    c.eq(2, "rendered RTL", result["direction"], "rtl")
    c.done()


@pytest.mark.edge
@pytest.mark.tc_149171
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149171_double_click_creates_one_record(page, records):
    """MEDIA-MCHUB-TC-117 — double-click Subscribe -> one success, one Active record (mailbox step out of scope)."""
    _labels("149171", "MEDIA-MCHUB-TC-117", "double-click Subscribe creates one record")
    email = own_address("149171", STAMP)
    assert not _read(records, email), f"PRECONDITION: {email} already has a record"
    band = McSubscriptionBand(page).open_hub("en")
    result = band.subscribe_with_backoff(email, via="dblclick")
    _remember(email, "149171", result)
    band.evidence("tc149171_step1_message", locator=band.SECTION)
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    rows = _read(records, email)
    records.list_rows(email)
    records.evidence_rows("tc149171_step2_record")
    _attach("outcome", {"result": result, "rows": rows})
    c = Checks("TC 149171")
    c.eq(1, "one success confirmation (no error)", (result["text"], result["ok"]), (MSG_SUCCESS_EN, True))
    c.eq(1, "subscribe requests sent", len(result["requests"]), 1)
    c.eq(2, "exactly one record", len(rows), 1)
    if rows:
        c.eq(2, "record Active", rows[0]["active"], True)
    c.done()


# ===========================================================================
#  FE-HUB subscription cases handed to FE-SUBS (2026-10-19)
# ===========================================================================
def _sized_address(tc: str, length: int) -> str:
    """Own-namespace address of exactly `length` chars on a long example.com sub-domain."""
    local = f"qctest.mchub.fe+{tc}-{STAMP}"
    room = length - len(local) - 1 - len(".example.com") - 1
    a = room // 2 + room % 2
    return f"{local}@{'a' * a}.{'b' * (room - a)}.example.com"


def _subscribe_case(page, records, tc: str, typed: str, stored: str, locale: str = "en") -> tuple:
    assert not _read(records, stored), f"PRECONDITION: {stored} already has a record"
    band = McSubscriptionBand(page).open_hub(locale)
    band.type_email(typed)
    entered = band.input_value()
    band.evidence(f"tc{tc}_step1_entered", locator=band.SECTION)
    result = band.subscribe_with_backoff(typed)
    _remember(stored, tc, result)
    band.evidence(f"tc{tc}_step2_message", locator=band.SECTION)
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    return band, entered, result


@pytest.mark.functional_low
@pytest.mark.tc_149162
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149162_spaces_trimmed_before_storing(page, records):
    """MEDIA-MCHUB-TC-108 — '   <addr>   ' -> success; stored trimmed, Active."""
    _labels("149162", "MEDIA-MCHUB-TC-108", "leading/trailing spaces trimmed before storing")
    email = own_address("149162", STAMP)
    STATE["T"] = email
    band, entered, result = _subscribe_case(page, records, "149162", f"   {email}   ", email)
    rows = _read(records, email, exact=False)
    records.list_rows(email)
    records.evidence_rows("tc149162_step3_record")
    _attach("outcome", {"entered": repr(entered), "result": result, "rows": rows})
    c = Checks("TC 149162")
    c.ok(1, "value entered (a type=email field exposes its value without the outer spaces)",
         entered.strip() == email, repr(entered), "address (+ spaces)")
    c.eq(2, "English success confirmation", result["text"], MSG_SUCCESS_EN)
    c.eq(2, "request carried the trimmed address", [r["email"] for r in result["requests"]][:1], [email])
    c.eq(3, "exactly one record", len(rows), 1)
    if rows:
        c.eq(3, "stored exactly, no spaces", rows[0]["email"], email)
        c.eq(3, "status Active", rows[0]["active"], True)
    c.done()


@pytest.mark.functional_high
@pytest.mark.tc_149142
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149142_already_subscribed_message_ar(page, browser, records):
    """MEDIA-MCHUB-TC-088 — AR resubmission of an active address -> Arabic already-subscribed message, RTL."""
    _labels("149142", "MEDIA-MCHUB-TC-088", "already-active email shows the Arabic already-subscribed message")
    email = STATE.get("T") or own_address("149162", STAMP)
    rows = _read(records, email)
    if not (rows and rows[0]["active"]):
        email = _address_a()
        _ensure_a(browser, records, active=True, tc="149142")
    band = McSubscriptionBand(page).open_hub("ar")
    band.type_email(email)
    c = Checks("TC 149142")
    c.eq(1, "email entered", band.input_value(), email)
    result = band.subscribe_with_backoff(email)
    _remember(email, "149142", result)
    band.evidence("tc149142_step2_message_ar", locator=band.SECTION)
    _attach("outcome", result)
    assert not result["throttled"], "PRECONDITION: endpoint still throttled"
    c.eq(2, "Arabic already-subscribed message", result["text"], MSG_DUPLICATE_AR)
    c.eq(2, "rendered RTL", result["direction"], "rtl")
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149163
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149163_stored_lower_case(page, records):
    """MEDIA-MCHUB-TC-109 — mixed-case input -> success; stored all lower case, Active."""
    _labels("149163", "MEDIA-MCHUB-TC-109", "email stored in lower case")
    email = own_address("149163", STAMP)
    typed = f"QCTest.MCHub.FE+149163-{STAMP}@Example.COM"
    band, entered, result = _subscribe_case(page, records, "149163", typed, email)
    local = email.split("@")[0]
    rows = _read(records, local, exact=False)
    records.list_rows(local)
    records.evidence_rows("tc149163_step3_record")
    _attach("outcome", {"typed": typed, "result": result, "rows": rows})
    c = Checks("TC 149163")
    c.eq(1, "value entered", entered, typed)
    c.eq(2, "English success confirmation", result["text"], MSG_SUCCESS_EN)
    c.eq(3, "exactly one record", len(rows), 1)
    if rows:
        c.eq(3, "stored all lower case", rows[0]["email"], email)
        c.eq(3, "status Active", rows[0]["active"], True)
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149164
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149164_150_char_email_accepted(page, records):
    """MEDIA-MCHUB-TC-110 — 150-character address accepted and stored in full."""
    _labels("149164", "MEDIA-MCHUB-TC-110", "150-character email accepted and stored in full")
    email = _sized_address("149164", 150)
    assert len(email) == 150
    band, entered, result = _subscribe_case(page, records, "149164", email, email)
    rows = _read(records, email.split("@")[0], exact=False)
    records.list_rows(email.split("@")[0])
    records.evidence_rows("tc149164_step3_record")
    _attach("outcome", {"email": email, "maxlength": page.locator(band.INPUT).get_attribute("maxlength"),
                        "result": result, "rows": rows})
    c = Checks("TC 149164")
    c.eq(1, "all 150 characters entered", len(entered), 150)
    c.eq(2, "English success confirmation", result["text"], MSG_SUCCESS_EN)
    c.eq(3, "one record", len(rows), 1)
    if rows:
        c.eq(3, "full 150-character address stored", (rows[0]["email"], len(rows[0]["email"] or "")), (email, 150))
        c.eq(3, "status Active", rows[0]["active"], True)
    c.done()


@pytest.mark.functional_low
@pytest.mark.tc_149165
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tc_149165_151_char_email_not_accepted(page, records):
    """MEDIA-MCHUB-TC-111 — 151-character address: truncated at 150 or blocked; never stored at 151."""
    _labels("149165", "MEDIA-MCHUB-TC-111", "151-character email is not accepted")
    email = _sized_address("149165", 151)
    assert len(email) == 151
    band = McSubscriptionBand(page).open_hub("en")
    maxlength = page.locator(band.INPUT).get_attribute("maxlength")
    band.type_email(email)
    entered = band.input_value()
    band.evidence("tc149165_step1_entered", locator=band.SECTION)
    c = Checks("TC 149165")
    c.ok(1, "field truncates to 150 or holds 151", len(entered) in (150, 151), len(entered), "150 or 151")
    if len(entered) == 151:
        result = band.subscribe_with_backoff(email)
        _remember(email, "149165", result)
    else:
        result = band.submit_without_request("click")
    band.evidence("tc149165_step2_message", locator=band.SECTION)
    rows = _read(records, email.split("@")[0], exact=False)
    records.list_rows(email.split("@")[0])
    records.evidence_rows("tc149165_step3_record")
    _attach("outcome", {"maxlength": maxlength, "entered_len": len(entered), "result": result, "rows": rows})
    assert not result.get("throttled"), "PRECONDITION: endpoint still throttled"
    c.ok(2, "no record with the 151-character address", not any(len(r["email"] or "") == 151 for r in rows),
         [(r["email"], r["active"]) for r in rows], "not stored at 151 (truncated or blocked)")
    c.ok(2, "blocked with a validation message (when not truncated)", len(entered) == 150 or not result.get("ok"),
         result.get("text"), "validation message")
    c.done()

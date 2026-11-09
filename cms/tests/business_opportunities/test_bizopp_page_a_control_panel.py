"""
cms/tests/business_opportunities/test_bizopp_page_a_control_panel.py —
listing-page Hero/CTA authoring cases 143371 / 143372 for PBI 130697 (Agent A).

The listing page content lives in ONE shared record,
`manage-business-opportunity-page?editEntry=QC-BIZOPP-130697-PAGE` (no "+ Add
New", no Delete — a QCTEST copy cannot be created). Brief rule 2 therefore
applies: every field is snapshotted first, the edit is made and asserted, then
the snapshot is written back, the record is re-opened and diffed to prove
restoration. Only one agent touches this record (A -> E -> now Agent G). Account:
Site Content Editor.

Safety protocol (OpportunityListingPageAdminPage.snapshot / restore): the
snapshot waits for the editor to load fully and is refused unless complete
(non-empty title, eyebrow, CTA URL, description; every declared key); the
restore writes only the fields that differ, never '' over a non-empty snapshot
value, saves with the ORIGINAL status (Publish only if it was Published),
retries once, and raises naming every field that still differs.

Hero Image is NOT replaced: the record's current file (bo-hero-illustration.png)
reads "The stored file content is missing" in the form, so a replaced image
could not be put back exactly — the Hero Image check runs against the image the
page currently renders (open question in the Agent A report).
"""

from __future__ import annotations

from urllib.parse import urlparse

import allure
import pytest

from cms.pages.business_opportunities.opportunity_admin_page import (
    LISTING_PAGE_SLUG,
    MSG_SAVED_AND_PUBLISHED,
    P_CTA_BEHAVIOR,
    P_CTA_LABEL,
    P_CTA_URL,
    P_DESCRIPTION,
    P_EYEBROW,
    P_TITLE,
    ROLE_EDITOR,
    BizOppPublicView,
    BizOppPublicViewE,
    OpportunityListingPageAdminPage,
)
from cms.tests.business_opportunities.e_support import (  # noqa: F401 — fixtures
    AUTH_FREE_PAGE,
    EPIC,
    anon_pages,
    has,
    pinned,
)
from cms.tests.business_opportunities.e_support import e_login as login
from config.settings import web_url
from core.utils.waits import WaitTimeoutError, wait_until

FEATURE = "Business Opportunities — Control Panel (listing page Hero/CTA)"
PAGE_GROUP = pytest.mark.xdist_group("bizopp_listing_page_record")

# 180 characters of visible text incl. one bullet list and one link (case data).
HERO_HTML_EN = (
    '<p>Explore vetted investment opportunities across Qatar, the wider GCC region and partner markets abroad.</p>'
    '<ul><li>Energy and infrastructure projects</li><li>Technology ventures.</li></ul>'
    '<p>Read the <a href="https://qatarchamber.com/business-opportunities">investor guide</a>.</p>'
)
HERO_HTML_AR = (
    '<p>اكتشف فرص الاستثمار المعتمدة في قطر والأسواق الشريكة.</p>'
    '<ul><li>مشاريع الطاقة والبنية التحتية</li><li>المشاريع التقنية</li></ul>'
    '<p>اقرأ <a href="https://qatarchamber.com/business-opportunities">دليل المستثمر</a>.</p>'
)
CASE_VALUES = {
    P_EYEBROW: "Business Gateway", f"{P_EYEBROW}_ar": "بوابة الأعمال",
    P_TITLE: "Business Opportunities", f"{P_TITLE}_ar": "فرص الأعمال",
    P_CTA_LABEL: "Submit Opportunity", f"{P_CTA_LABEL}_ar": "تقديم فرصة",
    P_CTA_URL: "https://qatarchamber.com/business-opportunities/submit",
    P_CTA_BEHAVIOR: "New Tab",
    f"{P_DESCRIPTION}_html": HERO_HTML_EN, f"{P_DESCRIPTION}_html_ar": HERO_HTML_AR,
}
EXTERNAL_CTA_URLS = ("https://example.com/qctest-cta", "https://www.iana.org/qctest-cta-2")


def _markers(*tcs, regression=False):
    def deco(fn):
        marks = [pytest.mark.control_panel, pytest.mark.web, pytest.mark.invest, pytest.mark.pbi_130697,
                 pytest.mark.functional_low, PAGE_GROUP]
        if regression:
            marks.append(pytest.mark.regression)
        for m in marks:
            fn = m(fn)
        for tc in tcs:
            fn = getattr(pytest.mark, f"tc_{tc}")(fn)
        return fn
    return deco


def _restore(admin: OpportunityListingPageAdminPage, snapshot: dict) -> dict:
    """The guarded restore of the page object (complete snapshot only, only the
    differing fields, never '' over a non-empty value, ORIGINAL status, one
    retry). Returns {} or raises PageRecordSafetyError naming every differing field."""
    try:
        diff = admin.restore(snapshot, before_save=lambda: pinned(admin, ROLE_EDITOR))
    finally:
        allure.attach("\n".join(getattr(admin, "last_restore_attempts", [])) or "(no attempt recorded)",
                      name="restore attempts")
    allure.attach(repr(diff) if diff else "{} (identical)", name="restore diff (snapshot vs re-opened record)")
    return diff


def _publish_cta(admin: OpportunityListingPageAdminPage, anon_pages, url: str) -> dict:
    """Sets ONLY the CTA Redirect URL on the shared record, publishes, then reads
    the logged-out page API and the public CTA href (EN)."""
    admin.open_page_record()
    admin.wait_editor_loaded(strict=False)
    admin.fill_en(P_CTA_URL, url)
    pinned(admin, ROLE_EDITOR)
    admin.click_publish()
    out = {"entered": url, "went_through": admin.save_went_through(), "messages": admin.all_messages_text()}
    admin.evidence(f"143371 CTA url {url}")
    if out["went_through"]:
        out.update(_cta_public(anon_pages, url))
    allure.attach(repr(out), name=f"CTA probe {url}")
    return out


def _cta_public(anon_pages, url: str, timeout: float = 60.0) -> dict:
    """Polls the logged-out page API until it reports `url` as ctaRedirectUrl,
    then reads the public hero CTA href."""
    view = BizOppPublicViewE(anon_pages())
    seen = {"api": {}}

    def _api_has_it() -> bool:
        seen["api"] = view.page_api("en")
        return seen["api"].get("ctaRedirectUrl") == url

    try:
        wait_until(_api_has_it, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    view.open_listing("en")
    hero = view.hero()
    view.screenshot(f"143371 public CTA for {url}")
    api = seen["api"]
    return {"api_ctaRedirectUrl": api.get("ctaRedirectUrl"), "api_ctaRedirectPath": api.get("ctaRedirectPath"),
            "api_ctaOpenBehavior": api.get("ctaOpenBehavior"), "public_cta_href": hero.get("cta_href"),
            "public_cta_target": hero.get("cta_target")}


def _public_hero(anon_pages, locale: str, expect: dict, timeout: float = 45.0) -> dict:
    view = BizOppPublicViewE(anon_pages())
    seen = {"hero": {}}

    def _ok() -> bool:
        view.open_listing(locale)
        seen["hero"] = view.hero()
        return all(seen["hero"].get(k) == v for k, v in expect.items())

    try:
        wait_until(_ok, timeout=timeout, poll=3.0)
    except WaitTimeoutError:
        pass
    view.screenshot(f"public listing hero {locale}")
    allure.attach(repr(seen["hero"]), name=f"public hero ({locale})")
    return seen["hero"]


# ===========================================================================
# 143371 — fully authored Hero/CTA publishes and renders EN + AR
# ===========================================================================
@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Hero / CTA")
@allure.title("A fully authored Hero/CTA content set publishes and renders on the public listing page")
@_markers("143371", regression=True)
def test_hero_cta_publishes_and_renders(page, anon_pages):
    # Azure TC 143371 | Site Content Editor | shared record QC-BIZOPP-130697-PAGE (snapshot / restore).
    # Extra (review finding): the CTA Redirect URL is also published with two clearly EXTERNAL
    # hosts, to tell same-site normalisation of the case's qatarchamber.com URL from host stripping.
    admin = login(page, ROLE_EDITOR, LISTING_PAGE_SLUG)
    admin.open_page_record()
    snapshot = admin.snapshot()  # raises unless complete -> nothing is edited
    allure.attach(repr(snapshot), name="snapshot BEFORE edit")
    results: dict = {"external": []}
    try:
        admin.fill_page(CASE_VALUES)
        entered = {k: admin.text_value(k) for k in (P_EYEBROW, P_TITLE, P_CTA_LABEL, P_CTA_URL)}
        entered["cta_behavior"] = admin.picklist_value(P_CTA_BEHAVIOR)
        results["entered"] = entered
        pinned(admin, ROLE_EDITOR)
        admin.click_publish()
        results["went_through"] = admin.save_went_through()
        results["banners"] = admin.success_messages(MSG_SAVED_AND_PUBLISHED) if results["went_through"] \
            else admin.editbar_texts()
        results["outcome"] = admin.save_outcome()
        admin.evidence("143371 hero published")
        admin.open_page_record()
        results["status"] = admin.current_status()
        results["active"] = admin.active_status_stored()
        if results["went_through"]:
            results["case_cta"] = _cta_public(anon_pages, CASE_VALUES[P_CTA_URL])
            results["en"] = _public_hero(anon_pages, "en", {"eyebrow": "Business Gateway",
                                                             "title": "Business Opportunities"})
            results["ar"] = _public_hero(anon_pages, "ar", {"eyebrow": "بوابة الأعمال", "title": "فرص الأعمال"})
            for url in EXTERNAL_CTA_URLS:
                results["external"].append(_publish_cta(admin, anon_pages, url))
    finally:
        results["restore_diff"] = _restore(admin, snapshot)
    allure.attach(repr(results), name="143371 results")

    assert not results["restore_diff"], f"RESTORE INCOMPLETE on QC-BIZOPP-130697-PAGE: {results['restore_diff']}"
    assert results["went_through"], f"Publish of the Hero/CTA content did not go through: {results['outcome']}"
    assert has(results["banners"], MSG_SAVED_AND_PUBLISHED), f"no success message: {results['banners']}"
    assert results["status"] == "Published", f"record status after Publish: {results['status']!r}"

    # CTA host handling: external hosts must be kept verbatim (API + public href).
    stripped = [e for e in results["external"]
                if not e.get("went_through") or e.get("public_cta_href") != e["entered"]
                or e.get("api_ctaRedirectUrl") != e["entered"]]
    external_kept = bool(results["external"]) and not stripped
    case_url = CASE_VALUES[P_CTA_URL]
    case_href = (results.get("case_cta") or {}).get("public_cta_href") or ""
    # The case's own URL is on the site's production host: rewritten to a same-site path
    # (host replaced by the current site, path kept) = normalisation, accepted as such
    # ONLY when external hosts are kept verbatim.
    same_site_ok = (urlparse(case_href).path == urlparse(case_url).path
                    and urlparse(case_href).netloc == urlparse(web_url("/")).netloc)
    allure.attach(f"external hosts kept: {external_kept} ({results['external']})\n"
                  f"case URL {case_url} -> public href {case_href!r} (same-site normalisation: {same_site_ok})\n"
                  f"case API {results.get('case_cta')}", name="CTA host handling verdict")

    problems = []
    if stripped:
        problems.append(f"EXTERNAL CTA host stripped/altered: {stripped}")
    for locale, label in (("en", "Submit Opportunity"), ("ar", "تقديم فرصة")):
        hero = results[locale]
        exp_title = "Business Opportunities" if locale == "en" else "فرص الأعمال"
        exp_eyebrow = "Business Gateway" if locale == "en" else "بوابة الأعمال"
        if hero.get("eyebrow") != exp_eyebrow:
            problems.append(f"{locale}: eyebrow {hero.get('eyebrow')!r}")
        if hero.get("title") != exp_title:
            problems.append(f"{locale}: title {hero.get('title')!r}")
        if hero.get("description_lists", 0) < 2:
            problems.append(f"{locale}: description bullet list not rendered ({hero.get('description_html', '')[:200]!r})")
        if "https://qatarchamber.com/business-opportunities" not in hero.get("description_links", []):
            problems.append(f"{locale}: description link not rendered/clickable ({hero.get('description_links')})")
        if hero.get("cta_label") != label:
            problems.append(f"{locale}: CTA label {hero.get('cta_label')!r}")
        href = hero.get("cta_href") or ""
        normalised = (external_kept and urlparse(href).path == urlparse(case_url).path
                      and urlparse(href).netloc == urlparse(web_url("/")).netloc)
        if href != case_url and not normalised:
            problems.append(f"{locale}: CTA href {href!r} (entered {case_url!r})")
        if hero.get("cta_target") != "_blank":
            problems.append(f"{locale}: CTA does not open in a new tab (target={hero.get('cta_target')!r})")
        if not hero.get("image_loaded"):
            problems.append(f"{locale}: hero image not loaded ({hero.get('image_src')!r})")
    assert not problems, "PRODUCT: the published Hero/CTA does not render as authored: " + "; ".join(problems)


# ===========================================================================
# 143372 — Publish blocked: empty Page Title, 61-char Eyebrow, invalid CTA URL
#           + brief rule 7: Eyebrow is a PLAIN field -> implemented limit read
#             live, then the max-length value published and checked publicly
#             (EN + AR, 1920 + 390). Shared record: snapshot / restore / diff.
# ===========================================================================
EYEBROW_60_EN = ("QCTEST-130697-G eyebrow at the sixty character limit" + "x" * 60)[:60]
EYEBROW_60_AR = ("بوابة الأعمال اختبار الحد الأقصى لعدد الأحرف ستون حرفا" + "ب" * 60)[:60]
WIDTHS = (1920, 390)


def _attempt(admin, label: str, fill) -> dict:
    """Opens the record fresh, applies `fill`, clicks Publish, returns the outcome."""
    admin.open_page_record()
    fill(admin)
    typed = {"eyebrow_len": len(admin.text_value(P_EYEBROW)), "eyebrow_ar_len": len(admin.ar_value(P_EYEBROW)),
             "title": admin.text_value(P_TITLE), "cta_url": admin.text_value(P_CTA_URL),
             "eyebrow_maxlength": admin._en(P_EYEBROW).get_attribute("maxlength")}
    pinned(admin, ROLE_EDITOR)
    admin.click_publish()
    out = {"typed": typed, "went_through": admin.save_went_through(), "evidence": admin.refusal_evidence(),
           "messages": admin.all_messages_text()}
    admin.evidence(f"143372 {label}")
    allure.attach(repr(out), name=f"143372 attempt: {label}")
    return out


def _public_layout(anon_pages, locale: str, width: int) -> dict:
    view = BizOppPublicViewE(anon_pages())
    view.at_width(width).open_listing(locale)
    out = {"hero": view.hero(), "layout": view.hero_layout()}
    view.screenshot(f"143372 public hero {locale} {width}")
    allure.attach(repr(out), name=f"public hero layout {locale} @{width}")
    return out


def _layout_problems(locale: str, width: int, seen: dict, expected: str) -> list[str]:
    problems, lay = [], seen.get("layout") or {}
    eyebrow = lay.get("eyebrow") or {}
    if (seen.get("hero") or {}).get("eyebrow") != expected:
        problems.append(f"{locale}@{width}: eyebrow renders {(seen.get('hero') or {}).get('eyebrow')!r}, "
                        f"not the 60-char value")
    if lay and lay["page_scroll_w"] > lay["viewport"] + 1:
        problems.append(f"{locale}@{width}: horizontal page scroll ({lay['page_scroll_w']} > {lay['viewport']})")
    if eyebrow and eyebrow["scroll_w"] > eyebrow["client_w"] + 1:
        problems.append(f"{locale}@{width}: eyebrow text overflows/clips ({eyebrow['scroll_w']} > {eyebrow['client_w']})")
    if eyebrow and (eyebrow["left"] < -1 or eyebrow["right"] > lay["viewport"] + 1):
        problems.append(f"{locale}@{width}: eyebrow box outside the viewport ({eyebrow['left']}..{eyebrow['right']})")
    return problems


@AUTH_FREE_PAGE
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Hero / CTA validation")
@allure.title("The Hero/CTA content set blocks publish when a mandatory field is empty or exceeds its max length")
@_markers("143372")
def test_hero_cta_publish_blocked_on_invalid_values(page, anon_pages):
    # Azure TC 143372 | Site Content Editor | shared record QC-BIZOPP-130697-PAGE (snapshot / restore).
    admin = login(page, ROLE_EDITOR, LISTING_PAGE_SLUG)
    admin.open_page_record()
    snapshot = admin.snapshot()
    allure.attach(repr(snapshot), name="snapshot BEFORE edit")
    live_before = BizOppPublicView(anon_pages()).open_listing("en").hero()
    eyebrow_61 = EYEBROW_60_EN + "Z"
    eyebrow_61_ar = EYEBROW_60_AR + "ز"
    r: dict = {"public_max": {}}
    try:
        # Steps 1-3 — the case as written.
        def _case(a):
            a.fill_en(P_TITLE, "")
            a.fill_en(P_EYEBROW, eyebrow_61)
            a.fill_en(P_CTA_URL, "not-a-url")
        r["case"] = _attempt(admin, "case values (empty title, 61 eyebrow, not-a-url)", _case)
        r["public_after_case"] = BizOppPublicView(anon_pages()).open_listing("en").hero()
        # Rule 7 — the implemented Eyebrow limit, EN and AR, each on its own (other fields untouched).
        r["en61"] = _attempt(admin, "eyebrow EN 61 only", lambda a: a.fill_en(P_EYEBROW, eyebrow_61))
        r["ar61"] = _attempt(admin, "eyebrow AR 61 only", lambda a: a.fill_ar(P_EYEBROW, eyebrow_61_ar))

        # Rule 7 — publish the max-length value (60 EN + 60 AR) and check the public page.
        def _max(a):
            a.fill_en(P_EYEBROW, EYEBROW_60_EN)
            a.fill_ar(P_EYEBROW, EYEBROW_60_AR)
        r["max60"] = _attempt(admin, "eyebrow EN+AR at 60", _max)
        if r["max60"]["went_through"]:
            for locale, expected in (("en", EYEBROW_60_EN), ("ar", EYEBROW_60_AR)):
                for width in WIDTHS:
                    seen: dict = {}

                    def _shown(loc=locale, w=width, exp=expected, box=seen):
                        box.update(_public_layout(anon_pages, loc, w))
                        return box["hero"].get("eyebrow") == exp
                    try:
                        wait_until(_shown, timeout=45.0, poll=3.0)
                    except WaitTimeoutError:
                        pass
                    r["public_max"][(locale, width)] = seen
    finally:
        r["restore_diff"] = _restore(admin, snapshot)
    allure.attach(repr(r), name="143372 results")

    assert not r["restore_diff"], f"RESTORE INCOMPLETE on QC-BIZOPP-130697-PAGE: {r['restore_diff']}"
    case = r["case"]
    assert case["typed"]["eyebrow_len"] == 61, f"Eyebrow was truncated client-side: {case['typed']}"
    problems = []
    if case["went_through"]:
        problems.append(f"Publish was ACCEPTED with an empty Page Title, a 61-char Eyebrow and CTA URL 'not-a-url' "
                        f"(public hero then {r['public_after_case']})")
    else:
        msgs = case["messages"] + " " + repr(case["evidence"])
        for name, ok in (("Page Title required", "Page Title" in msgs or "pageTitle" in msgs),
                         ("Eyebrow max 60", "Eyebrow" in msgs or "eyebrowLabel" in msgs),
                         ("CTA URL format", "URL" in msgs or "ctaRedirectUrl" in msgs)):
            if not ok:
                problems.append(f"no validation message for {name}")
        for k in ("eyebrow", "title", "cta_href"):
            if r["public_after_case"].get(k) != live_before.get(k):
                problems.append(f"public {k} changed after the blocked attempt: {r['public_after_case'].get(k)!r}")
    if r["en61"]["went_through"]:
        problems.append("Eyebrow EN 61 characters alone was ACCEPTED (60-char limit not enforced)")
    if r["ar61"]["went_through"]:
        problems.append("Eyebrow AR 61 characters alone was ACCEPTED (60-char limit not enforced on Arabic)")
    if not r["max60"]["went_through"]:
        problems.append(f"Eyebrow at exactly 60 (EN+AR) was REFUSED: {r['max60']['messages']!r}")
    for (locale, width), seen in r["public_max"].items():
        expected = EYEBROW_60_EN if locale == "en" else EYEBROW_60_AR
        problems += _layout_problems(locale, width, seen, expected)
    assert not problems, "PRODUCT: " + "; ".join(problems) + f" | case messages: {case['messages']!r}"

"""
web/tests/business_opportunities/test_business_opportunities_detail_web.py
— Web cases for PBI 130697 (INVEST — Business Opportunities), the public
Opportunity Detail page: header + breadcrumb, sticky section index, 01 Overview,
02 Investment Details, 03 Gallery & Supporting Documents, downloads and the
Submit Inquiry CTA state (Azure plan 137724, suite 140361).

Cases: 143213, 143214, 143217, 143218, 143235, 143237, 143253, 143254, 143255,
143256, 143264, 143266, 143288, 143308. (143257 is Manual — checked visually
against Figma, no script.)

Run rules (Phase-3 web brief, 2026-10-12):
- Every test runs in a fresh UNAUTHENTICATED context (`"auth": False`): the
  cached CMS storageState carries an ar_SA cookie and a logged-in session.
- Read-only on qcdev. Real Published records only: QC-BIZOPP-130697-01
  (Active, "Qatar Smart City Infrastructure Fund") and -05 (Archived).
- Figma (file J3e1thav8NIu6a3XhC6Wcl, page 3963:142821) detail frames, identified
  by content: 4964:222947 desktop EN light, 4964:229742 desktop EN dark,
  4964:222993 desktop AR light, 4964:223038 mobile (390) EN light. Colours,
  font size/weight/line-height and copy compare exactly; layout ±2 px; images
  ±5 px (bug-rules Rule 1). Every UI test collects ALL token mismatches and
  fails once with the full list, so one run shows every finding.
- Breadcrumb: the PBI and every Figma frame say "Home › Business Gateway" (no
  "Business Opportunities" / title crumb). Figma wins over the case wording of
  143253, so the script asserts the Figma breadcrumb.
"""

import re

import allure
import pytest

from web.pages.business_opportunities.detail_page import (
    ACTIVE_ERC,
    ACTIVE_TITLE,
    ARCHIVED_ERC,
    BusinessOpportunityDetailPage,
)
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from config.settings import web_url

EPIC = "Business Opportunities"
FEATURE = "Detail Page"

DESKTOP = {"viewport": (1920, 1080), "auth": False}
MOBILE_375 = {"viewport": (375, 812), "auth": False}

LISTING_PATH = "/web/qatar-chamber/business-opportunities"
LISTING_CARD = "a.qc-bol-card"
LISTING_TAB = "button.qc-bol-tab"


def _sev(priority: int):
    return {
        1: allure.severity_level.BLOCKER,
        2: allure.severity_level.CRITICAL,
        3: allure.severity_level.NORMAL,
        4: allure.severity_level.MINOR,
    }[priority]


# ---------------------------------------------------------------------------
# Design-token helpers (Rule 1)
# ---------------------------------------------------------------------------
def rgb(hex_colour: str) -> str:
    h = hex_colour.lstrip("#")
    return f"rgb({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})"


def _px(value) -> float:
    return float(str(value).replace("px", "")) if value not in (None, "", "normal") else -1.0


class Tokens:
    """Soft-assert collector: every mismatch is recorded, then fail() raises
    once with the full list (and attaches it to Allure)."""

    def __init__(self, scope: str):
        self.scope = scope
        self.mismatches = []

    def eq(self, label, actual, expected):
        if actual != expected:
            self.mismatches.append(f"{label}: expected {expected!r}, got {actual!r}")

    def near(self, label, actual, expected, tol):
        if abs(_px(actual) - expected) > tol:
            self.mismatches.append(f"{label}: expected {expected}px (±{tol}), got {actual}")

    def text_style(self, dp, label, locator, size, line, weight, colour, index=0):
        s = dp.style(locator, "fontSize", "lineHeight", "fontWeight", "color", "fontFamily", index=index)
        self.eq(f"{label} font-size", s["fontSize"], f"{size}px")
        self.eq(f"{label} line-height", s["lineHeight"], f"{line}px")
        self.eq(f"{label} font-weight", s["fontWeight"], str(weight))
        self.eq(f"{label} colour", s["color"], rgb(colour))
        if not s["fontFamily"].startswith("Cairo"):
            self.mismatches.append(f"{label} font-family: expected Cairo, got {s['fontFamily']!r}")

    def fail(self):
        if self.mismatches:
            allure.attach("\n".join(self.mismatches), name=f"{self.scope} — Figma mismatches",
                          attachment_type=allure.attachment_type.TEXT)
            pytest.fail(f"{self.scope}: {len(self.mismatches)} Figma mismatch(es):\n  - "
                        + "\n  - ".join(self.mismatches), pytrace=False)


def _ring(dp, locator, index=0):
    """1px borders on this widget are drawn as `box-shadow: inset 0 0 0 1px <c>`."""
    shadow = dp.style(locator, "boxShadow", index=index)["boxShadow"]
    m = re.match(r"(rgba?\([^)]*\)) 0px 0px 0px ([\d.]+)px inset", shadow)
    return (m.group(1), float(m.group(2))) if m else (None, 0.0)


@pytest.fixture(autouse=True)
def _slow_qcdev(request):
    """qcdev is shared by 4 parallel agents: allow slow navigations."""
    if "page" in request.fixturenames:
        pg = request.getfixturevalue("page")
        pg.set_default_navigation_timeout(120000)
        pg.set_default_timeout(45000)


def _open_listing(page, locale="en"):
    page.goto(web_url(LISTING_PATH, locale=locale), wait_until="domcontentloaded")
    page.wait_for_selector(LISTING_CARD, timeout=60000)


def _open_from_listing(page, title, tab=None):
    _open_listing(page)
    if tab:
        page.locator(f"{LISTING_TAB}:has-text('{tab}')").click()
        page.wait_for_timeout(2500)
    card = page.locator(LISTING_CARD).filter(has_text=title).first
    card.locator("text=View Details").click()
    return BusinessOpportunityDetailPage(page).wait_loaded()


def _enable_dark(page):
    AccessibilityToolsComponent(page).enable_dark_mode()
    page.wait_for_timeout(800)


# ===========================================================================
# 143213 — View Details from the Active tab opens the correct detail page
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Navigation")
@allure.severity(_sev(2))
@allure.title("Clicking View Details from the Active tab opens the correct opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143213
@pytest.mark.traceability("143213")
@allure.label("pbi", "130697")
@allure.label("testcase", "143213")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_view_details_from_active_tab_opens_correct_page(page):
    dp = _open_from_listing(page, ACTIVE_TITLE)
    assert f"opportunity={ACTIVE_ERC}" in page.url, page.url
    assert dp.title_text() == ACTIVE_TITLE
    assert dp.is_submit_inquiry_cta_enabled(), "'Submit Inquiry' CTA is not visible+enabled on the Active record"


# ===========================================================================
# 143214 / 143235 — Archived record: read-only detail page, CTA hidden
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Navigation")
@allure.severity(_sev(3))
@allure.title("Clicking View Details from the Archive tab opens the opportunity's detail page in a read-only state")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143214
@pytest.mark.tc_143235
@pytest.mark.traceability("143214")
@allure.label("pbi", "130697")
@allure.label("testcase", "143214")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_view_details_from_archive_tab_opens_read_only(page):
    dp = _open_from_listing(page, "Agricultural Technology Hub", tab="Archive")
    assert f"opportunity={ARCHIVED_ERC}" in page.url, page.url
    assert dp.title_text() == "Agricultural Technology Hub"
    assert dp.section_ids() == ["qc-bod-overview", "qc-bod-investment", "qc-bod-gallery", "qc-bod-docs"]
    assert dp.overview_body_text() and dp.investment_structure() and dp.resources()
    assert not dp.is_submit_inquiry_cta_visible(), "'Submit Inquiry' is visible on an Archived record"
    assert not dp.is_submit_inquiry_cta_enabled()
    assert dp.archived_note_text() == "This opportunity is archived and is no longer accepting inquiries."


# ===========================================================================
# 143217 — index link scrolls to its section (and the indicator updates)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sticky section index")
@allure.severity(_sev(4))
@allure.title("Clicking a section index link scrolls the Detail page to the corresponding section")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143217
@pytest.mark.traceability("143217")
@allure.label("pbi", "130697")
@allure.label("testcase", "143217")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_section_index_click_scrolls_to_section(page):
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    assert dp.is_section_index_visible()
    dp.click_section_index_item("Investment Details")
    top = dp.section_viewport_top(dp.SECTION_INVESTMENT_DETAILS)
    assert -2 <= top <= 120, f"'02 Investment Details' section top is {top}px from the viewport top after the click"
    assert page.url.endswith("#qc-bod-investment")
    active = dp.active_section_index_label()
    assert active == "Investment Details", (
        f"section index indicator did not update after the click (marked row: {active!r}) — "
        "no row gets an active class/aria-current/distinct style"
    )


# ===========================================================================
# 143218 — Download returns the exact uploaded file
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Downloadable resources")
@allure.severity(_sev(2))
@allure.title("Clicking Download on a Downloadable Resource downloads the correct file")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143218
@pytest.mark.traceability("143218")
@allure.label("pbi", "130697")
@allure.label("testcase", "143218")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_download_resource_downloads_correct_file(page):
    """The real record's 'Investment Memorandum' PDF is 1,982 bytes, shown as
    '2 KB' (the case's '200 KB' is example data, not this record's file)."""
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    row = dp.resources()[0]
    assert row["title"] == "Investment Memorandum" and row["type"] == "PDF"
    served = page.request.get(web_url(row["href"]))
    assert served.status == 200
    assert 'filename="investment-memorandum.pdf"' in (served.headers.get("content-disposition") or "")
    download = dp.click_download_resource(0)
    assert download.failure() is None
    assert download.suggested_filename == "investment-memorandum.pdf"
    body = open(download.path(), "rb").read()
    assert body[:5] == b"%PDF-", "downloaded file is not a PDF"
    assert body == served.body(), "downloaded bytes differ from the uploaded attachment"
    assert row["size"] == f"{round(len(body) / 1024)} KB", f"size label {row['size']!r} vs {len(body)} bytes"


# ===========================================================================
# 143308 / 143375(web part) — Active record: CTA visible + enabled (+ opens modal)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Submit Inquiry CTA")
@allure.severity(_sev(2))
@allure.title("The Submit Inquiry CTA is visible and enabled on an Active opportunity's detail page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143308
@pytest.mark.tc_143375
@pytest.mark.traceability("143308")
@allure.label("pbi", "130697")
@allure.label("testcase", "143308")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_submit_inquiry_cta_visible_on_active(page):
    """143375's CMS step (record is Published/Active) was confirmed in the CMS
    phase; QC-BIZOPP-130697-01 is in the public Active tab."""
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    assert dp.section_ids() == ["qc-bod-overview", "qc-bod-investment", "qc-bod-gallery", "qc-bod-docs"]
    assert dp.is_submit_inquiry_cta_visible()
    assert dp.is_submit_inquiry_cta_enabled()
    assert dp.text(dp.SUBMIT_INQUIRY_CTA).strip() == "Submit Inquiry"
    dp.click_submit_inquiry()
    assert dp.is_modal_panel_visible()
    assert dp.text(".qc-bod-modal-title").strip() == "Express Your Interest"


# ===========================================================================
# 143237 — Download after the file was removed mid-visit (Edge) — BLOCKED
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Downloadable resources")
@allure.severity(_sev(2))
@allure.title("Clicking Download on a resource whose file was deactivated after the detail page rendered fails gracefully")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143237
@pytest.mark.traceability("143237")
@allure.label("pbi", "130697")
@allure.label("testcase", "143237")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_download_deactivated_resource_fails_gracefully(page):
    """BLOCKED: the precondition is deleting/deactivating a real record's
    Downloadable Resource File in the CMS mid-visit, and the CMS phase is closed
    (read-only on real records). As supporting evidence only, the test points
    the loaded row at an attachment id that does not exist (what the endpoint
    serves once a file is gone: HTTP 404, empty body) and records what the
    visitor sees."""
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    gone = "/o/qc-business-opportunities-api/attachment?id=999999999"
    status = page.request.get(web_url(gone)).status
    page.locator(dp.RESOURCE_DOWNLOAD_BUTTON).first.evaluate("(a, h) => a.setAttribute('href', h)", gone)
    observed = "no download event"
    try:
        with page.expect_download(timeout=8000) as info:
            page.locator(dp.RESOURCE_DOWNLOAD_BUTTON).first.click()
        observed = f"download event, failure={info.value.failure()!r}"
    except Exception as exc:  # noqa: BLE001
        observed = f"{observed} ({type(exc).__name__})"
    page.wait_for_timeout(1500)
    message_shown = page.locator("text=/no longer available|not available|unavailable/i").filter(visible=True).count() > 0
    allure.attach(page.screenshot(full_page=False), name="after Download on removed file",
                  attachment_type=allure.attachment_type.PNG)
    pytest.skip(
        "BLOCKED — needs a CMS deactivation of a real resource file (CMS phase closed, read-only). "
        f"Simulated removed file: endpoint HTTP {status}; click -> {observed}; "
        f"graceful message shown: {message_shown}; page stayed on {page.url}"
    )


# ===========================================================================
# 143253 — Header: title, hero summary, breadcrumb (+ Figma tokens)
# ===========================================================================
HEADER_VARIANTS = {
    # frame 4964:222947 / 4964:229742 / 4964:222993
    "en-light": dict(locale="en", dark=False, crumbs=["Home", "Business Gateway"], cta="Submit Inquiry",
                     title="#1D1D1B", desc="#6C6C6B", crumb="#6C6C6B", chip="#911731",
                     chip_bg="#F4E7EA", chip_border="#CD96A2"),
    "en-dark": dict(locale="en", dark=True, crumbs=["Home", "Business Gateway"], cta="Submit Inquiry",
                    title="#FFFFFF", desc="#DEDEDD", crumb="#DEDEDD", chip="#C44561",
                    chip_bg="#360711", chip_border="#711126"),
    "ar-light": dict(locale="ar", dark=False, crumbs=["الرئيسية", "بوابة الأعمال"], cta="إرسال استفسار",
                     title="#1D1D1B", desc="#6C6C6B", crumb="#6C6C6B", chip="#911731",
                     chip_bg="#F4E7EA", chip_border="#CD96A2"),
}


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Header")
@allure.severity(_sev(3))
@allure.title("The Opportunity Detail page header renders title, hero summary and breadcrumb")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143253
@pytest.mark.traceability("143253")
@allure.label("pbi", "130697")
@allure.label("testcase", "143253")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
@pytest.mark.parametrize("variant", list(HEADER_VARIANTS))
def test_detail_header_renders_title_summary_breadcrumb(page, variant):
    v = HEADER_VARIANTS[variant]
    if v["locale"] == "en":
        dp = _open_from_listing(page, ACTIVE_TITLE)
    else:
        dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC, locale="ar")
    if v["dark"]:
        _enable_dark(page)
    assert f"opportunity={ACTIVE_ERC}" in page.url

    # Functional: full title + summary, no truncation.
    title_box = page.locator(dp.HEADER_TITLE).evaluate(
        "e => [e.scrollWidth <= e.clientWidth + 1, getComputedStyle(e).textOverflow, getComputedStyle(e).webkitLineClamp]")
    assert dp.title_text() and title_box[0] and title_box[1] != "ellipsis" and title_box[2] in ("none", None, ""), title_box
    assert dp.summary_text(), "hero summary is empty"
    clipped = page.locator(dp.HEADER_SUMMARY).evaluate(
        "e => { const c = getComputedStyle(e); return c.webkitLineClamp !== 'none' || "
        "(c.overflowY !== 'visible' && e.scrollHeight > e.clientHeight + 4); }")
    assert not clipped, "hero summary is clamped/clipped"
    assert dp.is_hero_image_loaded()
    assert dp.document_direction() == ("rtl" if v["locale"] == "ar" else "ltr")

    t = Tokens(f"143253 header [{variant}] vs Figma")
    t.eq("breadcrumb items", dp.breadcrumb_texts(), v["crumbs"])
    t.eq("CTA copy", dp.text(dp.SUBMIT_INQUIRY_CTA).strip(), v["cta"])
    t.text_style(dp, "title", dp.HEADER_TITLE, 48, 60, 700, v["title"])
    t.text_style(dp, "hero summary", dp.HEADER_SUMMARY + " p", 16, 24, 400, v["desc"])
    t.near("hero summary width", dp.box(dp.HEADER_SUMMARY)["width"], 648, 2)
    for i, label in enumerate(("breadcrumb 'Home'", "breadcrumb current item")):
        t.text_style(dp, label, f"{dp.BREADCRUMB_LINK} span", 14, 22, 400, v["crumb"], index=i)
    t.text_style(dp, "sector chip", dp.CHIP, 12, 18, 400, v["chip"])
    t.eq("chip background", dp.style(dp.CHIP, "backgroundColor")["backgroundColor"], rgb(v["chip_bg"]))
    ring_colour, ring_width = _ring(dp, dp.CHIP)
    t.eq("chip border colour", ring_colour, rgb(v["chip_border"]))
    t.eq("chip border width", ring_width, 0.5)
    cta = dp.style(dp.SUBMIT_INQUIRY_CTA, "backgroundColor", "borderTopLeftRadius", "paddingTop", "paddingLeft")
    t.eq("CTA background", cta["backgroundColor"], rgb("#911731"))
    t.near("CTA height", dp.box(dp.SUBMIT_INQUIRY_CTA)["height"], 44, 2)
    t.near("CTA padding-top", cta["paddingTop"], 10, 2)
    t.near("CTA padding-inline", cta["paddingLeft"], 16, 2)
    t.text_style(dp, "CTA label", f"{dp.SUBMIT_INQUIRY_CTA} span", 16, 24, 600, "#FFFFFF")
    img = dp.box(dp.HERO_IMAGE)
    t.near("hero image width", img["width"], 424, 5)
    t.near("hero image height", img["height"], 240, 5)
    t.near("hero image radius", dp.style(dp.HERO_IMAGE, "borderTopLeftRadius")["borderTopLeftRadius"], 12, 2)
    if v["locale"] == "ar":
        t.near("RTL title right edge", dp.box(dp.HEADER_TITLE)["x"] + dp.box(dp.HEADER_TITLE)["width"], 1620, 2)

    # Breadcrumb navigation: the parent crumb is "Business Gateway" (PBI/Figma).
    hrefs = dp.breadcrumb_hrefs()
    assert hrefs[-1].endswith("/business-gateway"), hrefs
    dp.click_breadcrumb(v["crumbs"][-1])
    page.wait_for_url("**/business-gateway", timeout=30000)
    t.fail()


# ===========================================================================
# 143254 — sticky index stays fixed and highlights the visible section
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Sticky section index")
@allure.severity(_sev(3))
@allure.title("The Detail page sticky section index highlights the active section while scrolling")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143254
@pytest.mark.traceability("143254")
@allure.label("pbi", "130697")
@allure.label("testcase", "143254")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_section_index_highlights_active_section(page):
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    assert dp.section_index_entries() == [
        ("01", "Overview", "#qc-bod-overview"),
        ("02", "Investment Details", "#qc-bod-investment"),
        ("03", "Gallery & Supporting Documents", "#qc-bod-gallery"),
    ]
    assert dp.style(dp.SECTION_INDEX, "position")["position"] == "sticky"

    t = Tokens("143254 sticky index (Figma 4964:222947)")
    card = dp.box(dp.SECTION_INDEX_CARD)
    t.near("index card width", card["width"], 312, 2)
    t.near("index card height", card["height"], 144, 2)
    t.eq("index card background", dp.style(dp.SECTION_INDEX_CARD, "backgroundColor")["backgroundColor"], rgb("#F6F6F6"))
    t.eq("index card border", _ring(dp, dp.SECTION_INDEX_CARD), (rgb("#EDEDED"), 1.0))
    t.near("index row height", dp.box(dp.SECTION_INDEX_ITEM)["height"], 48, 2)
    t.text_style(dp, "index number", dp.SECTION_INDEX_NUM, 14, 22, 700, "#A8A8A7")
    t.eq("index number tile", dp.style(dp.SECTION_INDEX_NUM, "backgroundColor")["backgroundColor"], rgb("#EDEDED"))
    t.text_style(dp, "index label", dp.SECTION_INDEX_LABEL, 14, 22, 600, "#6C6C6B")

    t.eq("highlighted row on load", dp.active_section_index_label(), "Overview")
    tops = []
    for section, expected in ((dp.SECTION_INVESTMENT_DETAILS, "Investment Details"),
                              (dp.SECTION_GALLERY, "Gallery & Supporting Documents")):
        y = page.locator(section).evaluate("e => e.getBoundingClientRect().top + scrollY") - 200
        dp.scroll_to_y(y)
        tops.append(round(dp.section_index_viewport_top()))
        t.eq(f"highlighted row while '{expected}' is in view", dp.active_section_index_label(), expected)
    assert all(top == tops[0] for top in tops) and 0 <= tops[0] <= 120, f"index not pinned while scrolling: tops={tops}"
    dp.click_section_index_item("Overview")
    assert -2 <= dp.section_viewport_top(dp.SECTION_OVERVIEW) <= 120
    t.eq("highlighted row after clicking 'Overview'", dp.active_section_index_label(), "Overview")
    t.fail()


# ===========================================================================
# 143255 — 01 Overview: body, Investment Brief, Key Highlights (+ tokens)
# ===========================================================================
OVERVIEW_VARIANTS = {
    # frame 4964:222947 (light) / 4964:229742 (dark)
    "light": dict(body="#4A4A49", brief="#6C6C6B", heading="#1D1D1B", eyebrow="#911731", tile="#F6F6F6",
                  tile_border="#EDEDED", card="#FFFFFF", card_border="#EDEDED", stat_label="#4A4A49",
                  stat_value="#911731", hl_text="#343432", divider="#F6F6F6"),
    "dark": dict(body="#EDEDED", brief="#DEDEDD", heading="#FFFFFF", eyebrow="#C44561", tile="#343432",
                 tile_border="#4A4A49", card="#1D1D1B", card_border="#4A4A49", stat_label="#EDEDED",
                 stat_value="#C44561", hl_text="#F6F6F6", divider="#343432"),
}


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("01 Overview")
@allure.severity(_sev(3))
@allure.title("The Detail page Overview section renders body text and key highlights correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143255
@pytest.mark.traceability("143255")
@allure.label("pbi", "130697")
@allure.label("testcase", "143255")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
@pytest.mark.parametrize("theme", list(OVERVIEW_VARIANTS))
def test_detail_overview_section_renders_body_and_highlights(page, theme):
    """Known bug 149515 (Overview Body not rendered from its own CMS field) is
    referenced, not re-reported."""
    v = OVERVIEW_VARIANTS[theme]
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    if theme == "dark":
        _enable_dark(page)
    sec = dp.SECTION_OVERVIEW
    assert dp.text(f"{sec} {dp.SECTION_TITLE}").strip() == "Overview"
    assert dp.text(f"{sec} {dp.SECTION_EYEBROW}").strip() == "About the Opportunities"
    assert dp.overview_body_text(), "Overview body is empty"
    assert dp.subhead_texts()[0] == "Investment Brief" and dp.investment_brief_text()
    assert dp.stats() == {"Investment": "USD 25M–50M", "Type": "Joint Venture",
                          "Timeline": "3–6 months", "Risk profile": "Medium"}
    assert dp.text(".qc-bod-highlights-title").strip() == "Key Highlights"
    assert dp.key_highlight_texts() == ["Government-backed strategic programme",
                                        "Access to major smart-city development zones",
                                        "Structured partnership and knowledge-transfer model"]
    assert page.locator(dp.KEY_HIGHLIGHT_ITEM).evaluate_all(
        "li => li.every(e => e.scrollWidth <= e.clientWidth + 1)"), "a Key Highlight is truncated"

    t = Tokens(f"143255 Overview [{theme}] vs Figma")
    t.text_style(dp, "section eyebrow", f"{sec} {dp.SECTION_EYEBROW}", 12, 18, 400, v["eyebrow"])
    t.text_style(dp, "section title", f"{sec} {dp.SECTION_TITLE}", 24, 32, 600, v["heading"])
    tile = dp.box(f"{sec} {dp.SECTION_ICON_TILE}")
    t.near("section icon tile width", tile["width"], 44, 2)
    t.near("section icon tile height", tile["height"], 44, 2)
    t.eq("section icon tile fill", dp.style(f"{sec} {dp.SECTION_ICON_TILE}", "backgroundColor")["backgroundColor"], rgb(v["tile"]))
    t.eq("section icon tile border", _ring(dp, f"{sec} {dp.SECTION_ICON_TILE}")[0], rgb(v["tile_border"]))
    t.text_style(dp, "Overview body", f"{dp.OVERVIEW_PROSE} p", 16, 24, 400, v["body"], index=0)
    t.text_style(dp, "Investment Brief heading", dp.SUBHEAD, 18, 28, 700, v["heading"])
    t.text_style(dp, "Investment Brief text", f"{dp.OVERVIEW_PROSE} p", 16, 24, 400, v["brief"], index=1)
    t.eq("stats card fill", dp.style(".qc-bod-stats", "backgroundColor")["backgroundColor"], rgb(v["card"]))
    t.eq("stats card border", _ring(dp, ".qc-bod-stats"), (rgb(v["card_border"]), 1.0))
    t.near("stats card height", dp.box(".qc-bod-stats")["height"], 102, 2)
    t.text_style(dp, "stat label", dp.STAT_LABEL, 14, 22, 400, v["stat_label"])
    t.text_style(dp, "stat value", dp.STAT_VALUE, 18, 28, 700, v["stat_value"])
    t.eq("highlights card fill", dp.style(dp.KEY_HIGHLIGHTS, "backgroundColor")["backgroundColor"], rgb(v["card"]))
    t.text_style(dp, "Key Highlights title", ".qc-bod-highlights-title", 14, 22, 700, "#A66F43")
    t.text_style(dp, "highlight text", ".qc-bod-highlight-text p", 14, 22, 400, v["hl_text"])
    t.eq("highlight dot", dp.style(".qc-bod-highlight-dot", "backgroundColor")["backgroundColor"], rgb("#A66F43"))
    t.eq("section divider colour", dp.style(dp.DIVIDER, "backgroundColor")["backgroundColor"], rgb(v["divider"]))
    t.fail()


# ===========================================================================
# 143256 — 02 Investment Details: Submitted By, amount, ticket, co-investment
# ===========================================================================
INVEST_VARIANTS = {
    "light": dict(heading="#1D1D1B", sub_bg="#F6F0EC", sub_name="#1D1D1B", sub_meta="#7C7B7B", defs_bg="#FFFFFF",
                  defs_border="#DEDEDD", term="#855936", value="#343432"),
    "dark": dict(heading="#FFFFFF", sub_bg="#422C1B", sub_name="#FFFFFF", sub_meta="#D0D0D0", defs_bg="#1D1D1B",
                 defs_border="#6C6C6B", term="#B3845F", value="#F6F6F6"),
}


@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("02 Investment Details")
@allure.severity(_sev(3))
@allure.title("The Detail page Investment Details section renders the Investment Structure fields correctly")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143256
@pytest.mark.traceability("143256")
@allure.label("pbi", "130697")
@allure.label("testcase", "143256")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
@pytest.mark.parametrize("theme", list(INVEST_VARIANTS))
def test_detail_investment_details_section_renders_structure_fields(page, theme):
    """Record -01 has 3 Co-Investment items (the case's '2' is example data)."""
    v = INVEST_VARIANTS[theme]
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    if theme == "dark":
        _enable_dark(page)
    sec = dp.SECTION_INVESTMENT_DETAILS
    assert dp.text(f"{sec} {dp.SECTION_EYEBROW}").strip() == "Investment Details"
    assert dp.text(f"{sec} {dp.SECTION_TITLE}").strip() == "Investment Structure"
    sub = dp.submitted_by()
    assert sub == {"name": "Qatar Foundation for Technology", "entity_type": "Government Entity",
                   "location": "Doha, Qatar", "logo_loaded": True}, sub
    structure = dp.investment_structure()
    assert structure == {"Investment amount": "USD 25M–50M", "Minimum Ticket": "$5,000,000",
                         "Government Co-Investment": "40% ($20M)",
                         "Strategic Technology Partner": "35% ($17.5M)",
                         "Financial Investors": "25% ($12.5M)"}, structure

    t = Tokens(f"143256 Investment Details [{theme}] vs Figma")
    t.text_style(dp, "section title", f"{sec} {dp.SECTION_TITLE}", 24, 32, 600, v["heading"])
    t.eq("Submitted By card fill", dp.style(dp.SUBMITTER, "backgroundColor")["backgroundColor"], rgb(v["sub_bg"]))
    t.near("Submitted By card radius", dp.style(dp.SUBMITTER, "borderTopLeftRadius")["borderTopLeftRadius"], 12, 2)
    t.near("Submitted By card padding", dp.style(dp.SUBMITTER, "paddingTop")["paddingTop"], 20, 2)
    logo = dp.box(".qc-bod-submitter-logo")
    t.near("submitter logo width", logo["width"], 44, 5)
    t.near("submitter logo height", logo["height"], 44, 5)
    t.text_style(dp, "submitter name", dp.SUBMITTED_BY_NAME, 18, 28, 600, v["sub_name"])
    t.text_style(dp, "submitter meta", ".qc-bod-submitter-meta", 12, 18, 400, v["sub_meta"])
    t.eq("structure card fill", dp.style(dp.DEFS, "backgroundColor")["backgroundColor"], rgb(v["defs_bg"]))
    t.eq("structure card border", _ring(dp, dp.DEFS), (rgb(v["defs_border"]), 1.0))
    t.near("structure card radius", dp.style(dp.DEFS, "borderTopLeftRadius")["borderTopLeftRadius"], 12, 2)
    t.near("structure card height", dp.box(dp.DEFS)["height"], 178, 2)
    t.text_style(dp, "structure term", dp.DEF_TERM, 12, 18, 400, v["term"])
    t.text_style(dp, "structure value", dp.DEF_VALUE, 14, 22, 600, v["value"])
    t.fail()


# ===========================================================================
# 143264 — sections stack on a 375px viewport
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Responsive")
@allure.severity(_sev(3))
@allure.title("The Detail page sections stack correctly on a 375px mobile viewport")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143264
@pytest.mark.traceability("143264")
@allure.label("pbi", "130697")
@allure.label("testcase", "143264")
@pytest.mark.parametrize("page", [MOBILE_375], indirect=True)
def test_detail_layout_at_375px_mobile_viewport(page):
    """Figma mobile frame 4964:223038 (390 wide) has NO section index, so the
    index being hidden on mobile matches the design; the case's 'tab strip or
    condensed sticky bar' wording needs correction."""
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    page.wait_for_timeout(1500)
    assert not dp.has_horizontal_overflow(), f"horizontal overflow: {dp.overflowing_elements()}"
    assert dp.overflowing_elements() == []
    title, desc, cta, img = (dp.box(s) for s in (dp.HEADER_TITLE, dp.HEADER_SUMMARY, dp.SUBMIT_INQUIRY_CTA, dp.HERO_IMAGE))
    for name, b in (("title", title), ("summary", desc), ("CTA", cta), ("hero image", img)):
        assert abs(b["x"] - 20) <= 2 and abs(b["width"] - 335) <= 2, f"{name} not full-width: {b}"
    assert title["y"] < desc["y"] < cta["y"] < img["y"], "header blocks are not stacked vertically"
    assert not dp.is_section_index_visible(), "section index shown on mobile (Figma mobile frame has none)"
    tops = []
    for sid in dp.section_ids():
        b = dp.box(f"#{sid}")
        assert abs(b["x"] - 20) <= 2 and abs(b["width"] - 335) <= 2, f"#{sid} not full-width: {b}"
        tops.append(b["y"])
    assert tops == sorted(tops) and len(tops) == 4
    t = Tokens("143264 mobile header vs Figma 4964:223038")
    t.text_style(dp, "mobile title", dp.HEADER_TITLE, 30, 38, 700, "#1D1D1B")
    t.near("mobile CTA height", cta["height"], 44, 2)
    t.fail()


# ===========================================================================
# 143266 — High-Contrast mode
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Accessibility")
@allure.severity(_sev(4))
@allure.title("The Detail page renders correctly in High-Contrast mode")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143266
@pytest.mark.traceability("143266")
@allure.label("pbi", "130697")
@allure.label("testcase", "143266")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_renders_in_high_contrast_mode(page):
    dp = BusinessOpportunityDetailPage(page).open_detail(ACTIVE_ERC)
    probes = (("body", "backgroundColor"), (dp.HEADER_TITLE, "color"), (dp.SUBMIT_INQUIRY_CTA, "backgroundColor"),
              (dp.SECTION_INDEX_CARD, "backgroundColor"), (dp.SECTION_INDEX_LABEL, "color"))
    before = [dp.style(sel, prop)[prop] for sel, prop in probes]
    a11y = AccessibilityToolsComponent(page)
    a11y.enable_high_contrast()
    page.wait_for_timeout(800)
    assert a11y.is_high_contrast_active()
    after = [dp.style(sel, prop)[prop] for sel, prop in probes]
    changed = [sel for (sel, _), b, a in zip(probes, before, after) if a == b]
    assert not changed, f"no high-contrast palette on: {changed} (before={before}, after={after})"
    assert after[0] != after[1], "text colour equals the page background in High-Contrast"
    # (axe-playwright-python is not installed in this framework; contrast is checked by palette change + focus rings.)

    # Keyboard: Tab from the page top through the detail widget; every focused
    # element must show a visible focus ring.
    page.locator("body").click(position={"x": 5, "y": 300})
    page.evaluate("window.scrollTo(0, 0)")
    seen, missing_ring = [], []
    for _ in range(60):
        page.keyboard.press("Tab")
        info = page.evaluate(
            """() => { const e = document.activeElement; if (!e || !e.closest('.qc-bod')) return null;
                 const c = getComputedStyle(e);
                 return {el: e.tagName + '.' + e.className.toString().split(' ')[0], text: (e.innerText || '').trim().slice(0, 30),
                         ring: (c.outlineStyle !== 'none' && parseFloat(c.outlineWidth) > 0)
                               ? c.outlineStyle + ' ' + c.outlineWidth + ' ' + c.outlineColor : null,
                         shadow: c.boxShadow.slice(0, 80)}; }""")
        if info is None:
            if seen:
                break
            continue
        seen.append(info)
        if not info["ring"]:
            missing_ring.append(info)
    assert seen, "keyboard Tab never reached the detail widget"
    allure.attach("\n".join(str(s) for s in seen), name="focus order", attachment_type=allure.attachment_type.TEXT)
    assert not missing_ring, f"no visible focus outline in High-Contrast on: {missing_ring}"


# ===========================================================================
# 143288 — Archive Date transition (observed on the real archived record)
# ===========================================================================
@allure.epic(EPIC)
@allure.feature(FEATURE)
@allure.story("Archive transition")
@allure.severity(_sev(2))
@allure.title(
    "A Business Opportunity auto-moves to the Archive tab and its inquiry CTA becomes disabled "
    "when its Archive Date is reached"
)
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.invest
@pytest.mark.pbi_130697
@pytest.mark.tc_143288
@pytest.mark.traceability("143288")
@allure.label("pbi", "130697")
@allure.label("testcase", "143288")
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_detail_cta_disabled_after_archive_date_reached(page):
    """The scheduled transition itself (step 1) needs a CMS Archive Date edit
    and waiting for the scheduler — not possible read-only. This checks the
    public end state on the real archived record QC-BIZOPP-130697-05."""
    _open_listing(page)
    active_hrefs = page.locator(LISTING_CARD).evaluate_all("a => a.map(x => x.getAttribute('href'))")
    assert not any(ARCHIVED_ERC in h for h in active_hrefs), "archived record still listed in the Active tab"
    page.locator(f"{LISTING_TAB}:has-text('Archive')").click()
    page.wait_for_timeout(2500)
    archive_hrefs = page.locator(LISTING_CARD).evaluate_all("a => a.map(x => x.getAttribute('href'))")
    assert any(ARCHIVED_ERC in h for h in archive_hrefs), "archived record missing from the Archive tab"
    dp = BusinessOpportunityDetailPage(page).open_detail(ARCHIVED_ERC)
    assert not dp.is_submit_inquiry_cta_enabled()
    assert dp.archived_note_text()

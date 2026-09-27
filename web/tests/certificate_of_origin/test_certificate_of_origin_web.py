"""
web/tests/certificate_of_origin/test_certificate_of_origin_web.py — the Web
(public-site) cases for PBI 130947 (QC-SVC-005 — Certificate of Origin
Online), sourced from the injected Azure DevOps suite handed off by the QA
Manager. All 17 cases in the batch carry Platform = Web, so this is the only
module for this page.

SCRIPTED HERE (all 17): 140969, 140970, 140971, 140972, 140973, 140974,
140975, 140976, 140977, 140978, 140979, 140980, 140981, 140982, 140983,
140984, 140985 — of which 16 are delivered on the Web surface and 140981 is
scripted and complete but BLOCKED (below), so it counts as blocked, not as
delivered coverage.

140981 — scripted, complete, and NOT VERIFIABLE IN THIS ENVIRONMENT
("an Inactive section leaves no visible layout gap and drops its sticky index
entry"). Its step 1 is a Control_Panel write ("set the Documents Required
section Active Status to Inactive and publish"). This environment has no CMS
access at all: `CONTROL_PANEL_URL` is unset in `.env` and no CMS credentials
are configured, so the precondition cannot be created, and the section is
Active on the live build. The test below carries the case's FULL, unweakened
assertions behind a precondition gate that fires on the MISSING CMS ACCESS —
not on what the page renders, which would make the case's own first expected
result unfalsifiable — and skips with a concrete, actionable reason naming
exactly what is missing (see automation-standards.md -> Result integrity: an
unavailable precondition is the one legitimate use of `skip`; narrowing the
assertion to make it pass is not). It uses only Page-Object methods that
already existed (`section_exists()`, `gap_between_sections()`,
`index_entries()`), so the moment Control Panel access is configured and the
section is set Inactive and published, it runs as-is with no edit. Its index
assertion is an exact list, per the case's step-2 EXPECTED; on the current
build that will fail because a fourth, out-of-scope section renders — the
same scope conflict 140972 catches from the other direction, and an honest
red rather than a softened check.

URL NOTE — every case step says `/en/e-services/certificate-of-origin-online`.
That path returns HTTP 404 on qcdev. The canonical, redirect-free live page
(HTTP 200) is `/our-services/certificate-of-origin-online`, Arabic
`/ar/our-services/certificate-of-origin-online`; the shorter
`/certificate-of-origin-online` answers HTTP 302 to it. This module navigates
via `config.settings.web_url()` to the canonical path. Reported as a case-text
defect for the QA Manager; not corrected in Azure by this batch.

DESIGN TOKENS — these cases assert the Figma-verified values written into
each case's own EXPECTED text (Figma frames 2871:107628 EN-light,
2871:109904 EN-dark, 2871:107680 AR). They are asserted as stated; where the
live build renders a different value the test fails honestly and the delta is
reported to the QA Manager for Phase-3b triage. No expected value has been
relaxed to match the current build.
"""

import re

import allure
import pytest

from config.settings import CMS_ROLE_CREDENTIALS, settings
from core.web.design_tokens import (
    effective_color,
    font_family_contains,
    hex_to_rgb,
    px_close,
)
from web.pages.certificate_of_origin.certificate_of_origin_page import (
    SECTION_APPLY,
    SECTION_DOCUMENTS,
    SECTION_OVERVIEW,
    CertificateOfOriginPage,
)

# --------------------------------------------------------------------------
# Token-assertion helpers (test layer — the assertion intent lives here, not
# in the Page Object, which only exposes computed style dictionaries).
#
# The "#FFFFFF at 50% opacity" form these cases state repeatedly is resolved
# by `core.web.design_tokens.effective_color`, which folds an rgba() alpha
# channel and the element's own CSS `opacity` into one effective alpha.
# --------------------------------------------------------------------------
STYLE_PROPS = ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "opacity"]


def assert_type_tokens(coo, selector, *, weight, size, line_height, color,
                       alpha=1.0, index=0, label="", family="Cairo"):
    """Asserts one element's typography tokens against the case's values."""
    styles = coo.computed_style(selector, STYLE_PROPS, index=index)
    what = label or f"{selector}[{index}]"
    assert font_family_contains(styles["fontFamily"], family), (
        f"{what}: expected font family {family}, got {styles['fontFamily']!r}"
    )
    assert str(styles["fontWeight"]) == str(weight), (
        f"{what}: expected font-weight {weight}, got {styles['fontWeight']!r}"
    )
    assert px_close(styles["fontSize"], size), (
        f"{what}: expected font-size {size}, got {styles['fontSize']!r}"
    )
    assert px_close(styles["lineHeight"], line_height), (
        f"{what}: expected line-height {line_height}, got {styles['lineHeight']!r}"
    )
    actual_rgb, actual_alpha = effective_color(styles)
    assert actual_rgb == hex_to_rgb(color), (
        f"{what}: expected colour {color} ({hex_to_rgb(color)}), got {actual_rgb}"
    )
    assert abs(actual_alpha - alpha) <= 0.01, (
        f"{what}: expected {int(alpha * 100)}% opacity, got {int(actual_alpha * 100)}%"
    )


def assert_color(coo, selector, expected_hex, *, index=0, label=""):
    """Colour-only assertion — used by the dark-theme palette case, whose
    EXPECTED text names colours and nothing else."""
    styles = coo.computed_style(selector, ["color", "opacity"], index=index)
    actual_rgb, _ = effective_color(styles)
    what = label or f"{selector}[{index}]"
    assert actual_rgb == hex_to_rgb(expected_hex), (
        f"{what}: expected {expected_hex} ({hex_to_rgb(expected_hex)}), got {actual_rgb}"
    )


def _missing_control_panel_config() -> list:
    """The `.env` keys that still have to be filled before a Control_Panel
    precondition can be created on this machine. Empty list = CMS access is
    configured. Used by 140981, whose step 1 is an authoring write."""
    missing = []
    if not settings.control_panel_url:
        missing.append("CONTROL_PANEL_URL is not set in .env")
    if not any(email and password for email, password in CMS_ROLE_CREDENTIALS.values()):
        missing.append(
            "no CMS role credentials are configured (CMS_SITE_CONTENT_EDITOR_EMAIL / "
            "_PASSWORD, or another role pair)"
        )
    return missing


# --------------------------------------------------------------------------
# Concrete data mirrored from the approved cases (never re-authored here).
# --------------------------------------------------------------------------
HERO_EYEBROW_EN = "Export Documentation Service"
HERO_TITLE_EN = "Certificate of Origin Online"
HERO_DESC_EN = (
    "Apply for a Certificate of Origin, verify an issued certificate, or "
    "identify the documents required for your export scenario."
)
CTA_LABELS_EN = ["Login to COO", "Verify Certificate"]
QUICK_FACTS_EN = [
    ("Service Channel", "Online Portal"),
    ("Certificate Types", "8 Available Types"),
    ("Verification", "Secure QR Code"),
    ("Coverage", "National & Re-export"),
]
INDEX_ENTRIES_EN = ["01 Overview", "02 Documents Required", "03 How to Apply"]
# 140981 — the Inactive section under test, the index entry it must drop, and
# the exact surviving list the case's step-2 EXPECTED states ("the sticky
# index lists only '01 Overview' and '03 How to Apply'"). The numerals are NOT
# re-flowed: How to Apply keeps 03 with 02 removed, as the case writes it.
DOCUMENTS_INDEX_LABEL = "Documents Required"
INDEX_ENTRIES_DOCUMENTS_INACTIVE = ["01 Overview", "03 How to Apply"]
# The page stacks its sections flush and gets its rhythm from each section's
# own 40px padding, so a removed section must leave a 0px gap between its
# surviving neighbours, not a blank band. Measured live 2026-09-17 at
# 1920x1080: overview->documents, documents->apply and apply->finder all
# report exactly 0.00px. The tolerance absorbs sub-pixel rounding only.
SECTION_STACK_GAP_PX = 0.0
SECTION_STACK_TOLERANCE_PX = 1.0
OVERVIEW_BODY_PREFIX = (
    "The Certificate of Origin (COO) is an official trade document that "
    "certifies goods have been wholly produced, manufactured, or sufficiently "
    "processed in the Sta"
)
CARD_TITLES_EN = [
    "Apply for a Certificate",
    "Certificate Verification",
    "Application Requirements",
]
CARD_DESCS_EN = [
    "Submit your Certificate of Origin application through the electronic "
    "portal for eligible export transactions.",
    "Verify the authenticity of issued Certificates of Origin using the "
    "official online verification service.",
    "Review the required documents, certificate types, and eligibility "
    "criteria before submitting your application.",
]
DOCUMENTS_INTRO_EN = (
    "Detailed regulatory requirements for issuing Certificate of Origin "
    "across national exports, GCC corridors, trade agreements, and re-exports."
)
ACCORDION_ITEM_TITLE = "Certificate of Origin for Personal Effects"
ACCORDION_ITEM_SUBTITLE = "Personal items list, NOC, ID, and computer card"
ACCORDION_ANSWER_PREFIX = (
    "Provide a list of personal items including full description , number of "
    "packages , Country of Origin , importing country, shipping means and "
    "signature of the ow"
)
APPLY_INTRO_EN = (
    "Follow the steps below to submit your Certificate of Origin application "
    "through Qatar Chamber's electronic Certificate of Origin system."
)
STEP_NUMERALS = ["01", "02", "03", "04", "05", "06"]
STEP_TITLES_EN = [
    "Download and Complete the Application",
    "Receive Your Login Credentials",
    "Access the Online System",
    "Review the Requirements",
    "Comply with the Rules of Origin",
    "Share Your Feedback",
]
BANNER_BODY_EN = (
    "Access the online Certificate of Origin portal to submit and manage "
    "applications, or verify issued certificates through the official "
    "verification service."
)

HERO_EYEBROW_AR = "خدمة وثائق التصدير"
HERO_TITLE_AR = "شهادة المنشأ الإلكترونية"
HERO_DESC_AR = (
    "قدّم طلبًا للحصول على شهادة منشأ، أو تحقّق من صحة شهادة منشأ صادرة، أو "
    "اطّلع على المستندات المطلوبة وفقًا لنوع التصدير الخاص بك."
)
CTA_LABELS_AR = ["تسجيل الدخول", "التحقق من الشهادة"]
QUICK_FACTS_AR = [
    ("قناة الخدمة", "البوابة الإلكترونية"),
    ("أنواع الشهادات", "8 أنواع من الشهادات"),
    ("التحقق", "التحقق عبر رمز QR"),
    ("نطاق الخدمة", "التصدير وإعادة التصدير"),
]
INDEX_ENTRIES_AR = ["01 نظرة عامة", "02 المستندات المطلوبة", "03 كيفية التقديم"]
BANNER_EYEBROW_AR = "هل أنت مستعد للمتابعة؟"
BANNER_TITLE_AR = "اختر الخدمة التي تحتاجها"


# ---------------------------------------------------------------------------
# 140969 / ESERV-COO-TC-001 — hero eyebrow, title and description tokens
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Hero")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Hero renders the eyebrow, page title and description with the verified English design tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140969
@pytest.mark.traceability("ESERV-COO-TC-001")
@allure.label("pbi", "130947")
@allure.label("testcase", "140969")
def test_coo_hero_text_tokens_en(page):
    """ESERV-COO-TC-001 — Azure TC 140969."""
    coo = CertificateOfOriginPage(page)

    with allure.step("Open the published English page logged out at 1920x1080"):
        coo.start_console_capture()
        coo.open_coo(locale="en")

    assert coo.document_direction() == "ltr"
    assert coo.console_errors() == []
    assert not coo.has_horizontal_scrollbar()

    with allure.step("Inspect the hero eyebrow, title and description"):
        assert coo.hero_eyebrow_text() == HERO_EYEBROW_EN
        assert coo.hero_title_text() == HERO_TITLE_EN
        assert coo.hero_description_text() == HERO_DESC_EN

    assert_type_tokens(coo, coo.HERO_EYEBROW, weight=400, size="12px",
                       line_height="18px", color="#FFFFFF", alpha=0.5,
                       label="hero eyebrow")
    assert coo.effective_text_align(coo.HERO_EYEBROW) == "left"
    assert_type_tokens(coo, coo.HERO_TITLE, weight=700, size="48px",
                       line_height="60px", color="#FFFFFF", label="hero title")
    assert_type_tokens(coo, coo.HERO_DESC, weight=400, size="16px",
                       line_height="24px", color="#FFFFFF", alpha=0.7,
                       label="hero description")


# ---------------------------------------------------------------------------
# 140970 / ESERV-COO-TC-002 — hero shared CTA buttons
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Hero")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Hero renders both shared CTA buttons with the verified labels and tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140970
@pytest.mark.traceability("ESERV-COO-TC-002")
@allure.label("pbi", "130947")
@allure.label("testcase", "140970")
def test_coo_hero_shared_ctas_en(page):
    """ESERV-COO-TC-002 — Azure TC 140970."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm the CTA row renders below the hero description"):
        desc_box = coo.element_box(coo.HERO_DESC)
        ctas_box = coo.element_box(coo.HERO_CTAS)
        assert desc_box is not None and ctas_box is not None
        assert ctas_box["y"] >= desc_box["y"] + desc_box["height"] - 1

    with allure.step("Inspect the two hero buttons and their computed styles"):
        # Exactly two, in order, with no third button and no placeholder label.
        assert coo.hero_cta_count() == 2
        assert coo.hero_cta_labels() == CTA_LABELS_EN

        # Side by side: same row, left to right.
        first = coo.element_box(coo.HERO_CTA, index=0)
        second = coo.element_box(coo.HERO_CTA, index=1)
        assert abs(first["y"] - second["y"]) <= 2
        assert first["x"] < second["x"]

    for i, label in enumerate(CTA_LABELS_EN):
        assert_type_tokens(coo, coo.HERO_CTA, weight=600, size="16px",
                           line_height="24px", color="#4A4A49", index=i,
                           label=f"hero CTA '{label}'")
        assert coo.effective_text_align(coo.HERO_CTA, index=i) == "center"
        background = coo.computed_style(coo.HERO_CTA, ["backgroundColor"], index=i)
        assert background["backgroundColor"] == hex_to_rgb("#FFFFFF"), (
            f"hero CTA '{label}': expected a white pill, got "
            f"{background['backgroundColor']}"
        )


# ---------------------------------------------------------------------------
# 140971 / ESERV-COO-TC-003 — quick-facts tiles
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The four quick-facts tiles render the verified label and value pairs in order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140971
@pytest.mark.traceability("ESERV-COO-TC-003")
@allure.label("pbi", "130947")
@allure.label("testcase", "140971")
def test_coo_quick_facts_tiles_en(page):
    """ESERV-COO-TC-003 — Azure TC 140971."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm the quick-facts strip renders beneath the hero CTAs"):
        ctas_box = coo.element_box(coo.HERO_CTAS)
        facts_box = coo.element_box(coo.FACTS)
        assert facts_box["y"] >= ctas_box["y"] + ctas_box["height"] - 1

    with allure.step("Read the four tiles left to right"):
        assert coo.fact_count() == 4
        assert coo.fact_pairs() == QUICK_FACTS_EN

    for i, (label, value) in enumerate(QUICK_FACTS_EN):
        assert_type_tokens(coo, coo.FACT_LABEL, weight=400, size="12px",
                           line_height="18px", color="#FFFFFF", alpha=0.5,
                           index=i, label=f"quick-fact label '{label}'")
        assert_type_tokens(coo, coo.FACT_VALUE, weight=700, size="14px",
                           line_height="22px", color="#FFFFFF",
                           index=i, label=f"quick-fact value '{value}'")


# ---------------------------------------------------------------------------
# 140972 / ESERV-COO-TC-004 — sticky section index
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The sticky section index renders only the three PBI-defined entries and highlights the active one on scroll")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_140972
@pytest.mark.traceability("ESERV-COO-TC-004")
@allure.label("pbi", "130947")
@allure.label("testcase", "140972")
def test_coo_sticky_index_entries_and_active_state(page):
    """ESERV-COO-TC-004 — Azure TC 140972."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm the sticky index renders to the left of the content column"):
        assert coo.is_index_visible()
        index_box = coo.element_box(coo.INDEX_COL)
        content_box = coo.element_box(coo.CONTENT)
        assert index_box["x"] < content_box["x"]

    with allure.step("Read the index entries and their computed styles"):
        # The PBI defines exactly three sections; entries 04-07 exist in Figma
        # but are explicitly out of scope (A-2).
        assert coo.index_count() == 3
        assert coo.index_entries() == INDEX_ENTRIES_EN

    for i in range(3):
        assert_type_tokens(coo, coo.INDEX_NUM, weight=700, size="14px",
                           line_height="22px", color="#A8A8A7", index=i,
                           label=f"index numeral {i + 1}")
        assert_type_tokens(coo, coo.INDEX_LABEL, weight=600, size="14px",
                           line_height="22px", color="#6C6C6B", index=i,
                           label=f"index label {i + 1}")

    with allure.step("Scroll until Documents Required reaches the top of the viewport"):
        top_before_scroll = coo.index_top()
        coo.scroll_section_to_viewport_top(SECTION_DOCUMENTS)

    assert coo.index_column_position() == "sticky"
    assert coo.index_top() < top_before_scroll, "index did not stay pinned while scrolling"
    assert coo.is_index_visible()
    assert coo.active_index_label() == "Documents Required"


# ---------------------------------------------------------------------------
# 140973 / ESERV-COO-TC-005 — Overview section badge, heading and body
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Overview section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Overview section renders the verified badge, heading and body copy tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140973
@pytest.mark.traceability("ESERV-COO-TC-005")
@allure.label("pbi", "130947")
@allure.label("testcase", "140973")
def test_coo_overview_section_tokens(page):
    """ESERV-COO-TC-005 — Azure TC 140973."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Scroll to section 01 and inspect the badge, heading and body"):
        coo.scroll_section_into_view(SECTION_OVERVIEW)

        assert coo.section_badge_text(SECTION_OVERVIEW) == "About the service"
        assert coo.section_title_text(SECTION_OVERVIEW) == "Overview"
        assert coo.section_intro_text(SECTION_OVERVIEW).startswith(OVERVIEW_BODY_PREFIX)

    assert_type_tokens(coo, coo.section_badge_selector(SECTION_OVERVIEW), weight=400,
                       size="12px", line_height="18px", color="#911731",
                       label="Overview badge")
    assert_type_tokens(coo, coo.section_title_selector(SECTION_OVERVIEW), weight=600,
                       size="24px", line_height="32px", color="#1D1D1B",
                       label="Overview heading")
    assert_type_tokens(coo, coo.section_intro_selector(SECTION_OVERVIEW), weight=400,
                       size="16px", line_height="24px", color="#4A4A49",
                       label="Overview body")


# ---------------------------------------------------------------------------
# 140974 / ESERV-COO-TC-006 — three Overview info cards
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Overview section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The three Overview info cards render the verified titles and descriptions in display order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140974
@pytest.mark.traceability("ESERV-COO-TC-006")
@allure.label("pbi", "130947")
@allure.label("testcase", "140974")
def test_coo_overview_info_cards(page):
    """ESERV-COO-TC-006 — Azure TC 140974."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm three cards render side by side"):
        coo.scroll_section_into_view(SECTION_OVERVIEW)
        assert coo.card_count() == 3
        boxes = coo.card_boxes()
        assert abs(boxes[0]["y"] - boxes[1]["y"]) <= 2
        assert abs(boxes[1]["y"] - boxes[2]["y"]) <= 2
        assert boxes[0]["x"] < boxes[1]["x"] < boxes[2]["x"]

    with allure.step("Read the three card titles and bodies"):
        assert coo.card_titles() == CARD_TITLES_EN
        assert coo.card_descriptions() == CARD_DESCS_EN

    for i, title in enumerate(CARD_TITLES_EN):
        assert_type_tokens(coo, coo.CARD_TITLE, weight=600, size="16px",
                           line_height="24px", color="#343432", index=i,
                           label=f"info-card title '{title}'")
        assert_type_tokens(coo, coo.CARD_DESC, weight=400, size="14px",
                           line_height="22px", color="#7C7B7B", index=i,
                           label=f"info-card description {i + 1}")


# ---------------------------------------------------------------------------
# 140975 / ESERV-COO-TC-007 — Documents Required header block + PDF button
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Documents Required section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Documents Required section renders its badge, heading, intro and the Certificate of Origin (PDF) action button")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140975
@pytest.mark.traceability("ESERV-COO-TC-007")
@allure.label("pbi", "130947")
@allure.label("testcase", "140975")
def test_coo_documents_required_header_and_pdf_button(page):
    """ESERV-COO-TC-007 — Azure TC 140975."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Scroll to section 02 and inspect the badge, heading, intro and action button"):
        coo.scroll_section_into_view(SECTION_DOCUMENTS)

        assert coo.section_badge_text(SECTION_DOCUMENTS) == "Official Compliance Guide"
        assert coo.section_title_text(SECTION_DOCUMENTS) == "Documents Required"
        assert coo.section_intro_text(SECTION_DOCUMENTS) == DOCUMENTS_INTRO_EN
        assert coo.is_pdf_button_visible()
        assert coo.pdf_button_label() == "Certificate of Origin (PDF)"

    assert_type_tokens(coo, coo.section_badge_selector(SECTION_DOCUMENTS), weight=400,
                       size="12px", line_height="18px", color="#911731",
                       label="Documents Required badge")
    assert_type_tokens(coo, coo.section_title_selector(SECTION_DOCUMENTS), weight=600,
                       size="24px", line_height="32px", color="#1D1D1B",
                       label="Documents Required heading")
    assert_type_tokens(coo, coo.section_intro_selector(SECTION_DOCUMENTS), weight=400,
                       size="16px", line_height="24px", color="#4A4A49",
                       label="Documents Required intro")
    assert_type_tokens(coo, coo.PDF_BUTTON, weight=600, size="14px",
                       line_height="22px", color="#FFFFFF",
                       label="Certificate of Origin (PDF) button")
    assert coo.effective_text_align(coo.PDF_BUTTON) == "center"


# ---------------------------------------------------------------------------
# 140976 / ESERV-COO-TC-008 — document-requirement accordion item
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Documents Required section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A document-requirement accordion item renders its title, subtitle and content with the verified tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_140976
@pytest.mark.traceability("ESERV-COO-TC-008")
@allure.label("pbi", "130947")
@allure.label("testcase", "140976")
def test_coo_document_requirement_accordion_item(page):
    """ESERV-COO-TC-008 — Azure TC 140976."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm the accordion list renders under the Documents Required intro"):
        coo.scroll_section_into_view(SECTION_DOCUMENTS)
        assert coo.is_accordion_visible()
        intro_box = coo.element_box(coo.section_intro_selector(SECTION_DOCUMENTS))
        accordion_box = coo.element_box(coo.ACCORDION)
        assert accordion_box["y"] >= intro_box["y"] + intro_box["height"] - 1

    with allure.step(f"Expand '{ACCORDION_ITEM_TITLE}' and inspect its title, subtitle and content"):
        coo.expand_accordion_item(ACCORDION_ITEM_TITLE)
        assert coo.is_accordion_item_expanded(ACCORDION_ITEM_TITLE)

        assert coo.accordion_item_title_text(ACCORDION_ITEM_TITLE) == ACCORDION_ITEM_TITLE
        assert coo.accordion_item_subtitle_text(ACCORDION_ITEM_TITLE) == ACCORDION_ITEM_SUBTITLE
        assert coo.accordion_item_answer_text(ACCORDION_ITEM_TITLE).startswith(
            ACCORDION_ANSWER_PREFIX
        )

    assert_type_tokens(coo, coo.accordion_item_title_selector(ACCORDION_ITEM_TITLE),
                       weight=700, size="14px", line_height="22px", color="#343432",
                       label="accordion item title")
    assert_type_tokens(coo, coo.accordion_item_subtitle_selector(ACCORDION_ITEM_TITLE),
                       weight=400, size="14px", line_height="22px", color="#A8A8A7",
                       label="accordion item subtitle")
    assert_type_tokens(coo, coo.accordion_item_answer_selector(ACCORDION_ITEM_TITLE),
                       weight=400, size="14px", line_height="22px", color="#6C6C6B",
                       label="accordion item content")


# ---------------------------------------------------------------------------
# 140977 / ESERV-COO-TC-009 — How to Apply header block
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("How to Apply section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The How to Apply section renders its badge, heading and intro with the verified tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140977
@pytest.mark.traceability("ESERV-COO-TC-009")
@allure.label("pbi", "130947")
@allure.label("testcase", "140977")
def test_coo_how_to_apply_header(page):
    """ESERV-COO-TC-009 — Azure TC 140977."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Scroll to section 03 and inspect the badge, heading and intro"):
        coo.scroll_section_into_view(SECTION_APPLY)

        assert coo.section_badge_text(SECTION_APPLY) == "How to Apply"
        assert coo.section_title_text(SECTION_APPLY) == "Apply for a Certificate of Origin Online"
        assert coo.section_intro_text(SECTION_APPLY) == APPLY_INTRO_EN

    assert_type_tokens(coo, coo.section_badge_selector(SECTION_APPLY), weight=400,
                       size="12px", line_height="18px", color="#911731",
                       label="How to Apply badge")
    assert_type_tokens(coo, coo.section_title_selector(SECTION_APPLY), weight=600,
                       size="24px", line_height="32px", color="#1D1D1B",
                       label="How to Apply heading")
    assert_type_tokens(coo, coo.section_intro_selector(SECTION_APPLY), weight=400,
                       size="16px", line_height="24px", color="#4A4A49",
                       label="How to Apply intro")


# ---------------------------------------------------------------------------
# 140978 / ESERV-COO-TC-010 — the six How to Apply steps
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("How to Apply section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The six How to Apply steps render with numerals 01-06 and the verified step titles in order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140978
@pytest.mark.traceability("ESERV-COO-TC-010")
@allure.label("pbi", "130947")
@allure.label("testcase", "140978")
def test_coo_how_to_apply_steps(page):
    """ESERV-COO-TC-010 — Azure TC 140978."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm six steps render in a vertical sequence"):
        coo.scroll_section_into_view(SECTION_APPLY)
        assert coo.step_count() == 6
        boxes = coo.step_boxes()
        for earlier, later in zip(boxes, boxes[1:]):
            assert later["y"] > earlier["y"], "steps are not stacked vertically"

    with allure.step("Read the six step numerals and titles top to bottom"):
        assert coo.step_numerals() == STEP_NUMERALS
        assert coo.step_titles() == STEP_TITLES_EN
        assert all(desc.strip() != "" for desc in coo.step_descriptions())

    for i, title in enumerate(STEP_TITLES_EN):
        assert_type_tokens(coo, coo.STEP_NUM, weight=500, size="18px",
                           line_height="28px", color="#911731", index=i,
                           label=f"step numeral {STEP_NUMERALS[i]}")
        assert coo.effective_text_align(coo.STEP_NUM, index=i) == "center"
        assert_type_tokens(coo, coo.STEP_TITLE, weight=600, size="16px",
                           line_height="24px", color="#343432", index=i,
                           label=f"step title '{title}'")
        assert_type_tokens(coo, coo.STEP_DESC, weight=400, size="14px",
                           line_height="22px", color="#7C7B7B", index=i,
                           label=f"step description {STEP_NUMERALS[i]}")


# ---------------------------------------------------------------------------
# 140979 / ESERV-COO-TC-011 — Download the Application Form card
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("How to Apply section")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Download the Application Form card renders its title, subtitle and Download button with the verified tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140979
@pytest.mark.traceability("ESERV-COO-TC-011")
@allure.label("pbi", "130947")
@allure.label("testcase", "140979")
def test_coo_download_application_form_card(page):
    """ESERV-COO-TC-011 — Azure TC 140979."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Confirm the download card renders after the sixth step"):
        coo.scroll_section_into_view(SECTION_APPLY)
        assert coo.is_download_card_visible()
        assert coo.download_card_top() >= coo.last_step_bottom() - 1

    with allure.step("Inspect the download card title, subtitle and button"):
        assert coo.download_card_title() == "Download the Application Form"
        assert coo.download_card_subtitle() == (
            "Download the official application form to begin your registration."
        )
        assert coo.download_button_label() == "Download"

    assert_type_tokens(coo, coo.DOWNLOAD_TITLE, weight=600, size="16px",
                       line_height="24px", color="#343432",
                       label="download card title")
    assert_type_tokens(coo, coo.DOWNLOAD_SUBTITLE, weight=400, size="14px",
                       line_height="22px", color="#A8A8A7",
                       label="download card subtitle")
    assert_type_tokens(coo, coo.DOWNLOAD_BUTTON, weight=600, size="14px",
                       line_height="22px", color="#FFFFFF",
                       label="Download button")
    assert coo.effective_text_align(coo.DOWNLOAD_BUTTON) == "center"


# ---------------------------------------------------------------------------
# 140980 / ESERV-COO-TC-012 — next-step banner
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Next-step banner")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The next-step banner renders its eyebrow, heading, body and both shared CTAs with the verified tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140980
@pytest.mark.traceability("ESERV-COO-TC-012")
@allure.label("pbi", "130947")
@allure.label("testcase", "140980")
def test_coo_next_step_banner(page):
    """ESERV-COO-TC-012 — Azure TC 140980."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Scroll to the 'Ready to continue?' banner"):
        coo.scroll_to_banner()
        assert coo.is_banner_visible()

    with allure.step("Confirm the banner sits on a dark surface"):
        # "Dark surface" is measured, not eyeballed: every opaque colour the
        # banner actually paints (the live build uses a linear-gradient, so
        # background-color alone reads as transparent — see
        # banner_surface_colors()) must have a low relative luminance.
        surface_colors = coo.banner_surface_colors()
        assert surface_colors, "the banner paints no opaque surface colour at all"
        for color in surface_colors:
            r, g, b = (int(float(v)) for v in re.findall(r"[\d.]+", color)[:3])
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            assert luminance < 128, (
                f"banner surface colour {color} is not a dark surface"
            )

    with allure.step("Inspect the banner text and buttons"):
        assert coo.banner_eyebrow_text() == "Ready to continue?"
        assert coo.banner_title_text() == "Choose the service you need"
        assert coo.banner_body_text() == BANNER_BODY_EN
        assert coo.banner_cta_labels() == CTA_LABELS_EN

    assert_type_tokens(coo, coo.BANNER_EYEBROW, weight=700, size="14px",
                       line_height="22px", color="#FFFFFF", alpha=0.4,
                       label="banner eyebrow")
    assert_type_tokens(coo, coo.BANNER_TITLE, weight=700, size="18px",
                       line_height="28px", color="#FFFFFF",
                       label="banner heading")
    assert_type_tokens(coo, coo.BANNER_BODY, weight=400, size="14px",
                       line_height="22px", color="#FFFFFF", alpha=0.6,
                       label="banner body")
    for i, label in enumerate(CTA_LABELS_EN):
        assert_type_tokens(coo, coo.BANNER_CTA, weight=600, size="16px",
                           line_height="24px", color="#4A4A49", index=i,
                           label=f"banner CTA '{label}'")


# ---------------------------------------------------------------------------
# 140981 / ESERV-COO-TC-013 — an Inactive section leaves no gap and no entry
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Section visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Inactive section leaves no visible layout gap and drops its sticky index entry")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_140981
@pytest.mark.traceability("ESERV-COO-TC-013")
@allure.label("pbi", "130947")
@allure.label("testcase", "140981")
def test_coo_inactive_section_leaves_no_gap_and_no_index_entry(page):
    """ESERV-COO-TC-013 — Azure TC 140981.

    Step 1 of this case is a Control_Panel write: set the Documents Required
    section's Active Status to Inactive on the Certificate of Origin page
    record and publish. That is deferred Control_Panel work and this
    environment cannot perform it at all — `CONTROL_PANEL_URL` is unset in
    `.env` and no CMS role credentials are configured — so the precondition
    cannot be created here and the section is Active on the live build.

    The gate below therefore fires on the MISSING CMS ACCESS, not on what the
    page happens to render: gating on "the section still renders" would make
    the case's own first expected result unfalsifiable. The assertions are
    written in full and unweakened — once Control Panel access exists and the
    section has been set Inactive and published, the skip stops firing and
    they run as-is, with no edit to this test.
    """
    missing = _missing_control_panel_config()
    if missing:
        pytest.skip(
            "PRECONDITION UNAVAILABLE — step 1 of this case is a Control_Panel write "
            "(open the Certificate of Origin page record in the Control Panel, set the "
            "Documents Required section's Active Status to Inactive, and publish). That "
            "write belongs to the deferred Control_Panel batch and cannot be performed "
            f"from this environment: {'; '.join(missing)}. The section is "
            "Active on the live build, so the state this case describes does not exist to "
            "be observed. Configure Control Panel access, set Documents Required to "
            "Inactive and publish, then this skip stops firing and the assertions below "
            "run unchanged."
        )

    coo = CertificateOfOriginPage(page)

    with allure.step("Open the published English page logged out at 1920x1080"):
        coo.open_coo(locale="en")

    with allure.step("Confirm the Inactive section does not render at all"):
        assert not coo.section_exists(SECTION_DOCUMENTS), (
            "the Documents Required section still renders on the public page while its "
            "Active Status is Inactive"
        )

    with allure.step("Confirm no blank band is left where the section was"):
        gap = coo.gap_between_sections(SECTION_OVERVIEW, SECTION_APPLY)
        assert abs(gap) <= SECTION_STACK_TOLERANCE_PX, (
            f"removing the Inactive section left a {gap:.1f}px band between Overview and "
            f"How to Apply; the page stacks its sections flush "
            f"({SECTION_STACK_GAP_PX:.0f}px, each section carrying its own 40px padding)"
        )

    with allure.step("Confirm the sticky index lists only the two Active sections"):
        entries = coo.index_entries()
        assert not any(DOCUMENTS_INDEX_LABEL in entry for entry in entries), (
            f"the sticky index still lists the Inactive section: {entries}"
        )
        # The case states the surviving list exactly — "only '01 Overview' and
        # '03 How to Apply'" — so this is an equality, not a membership check.
        # Note the numerals do NOT re-flow: How to Apply stays 03 with 02
        # removed, exactly as the case writes it.
        assert entries == INDEX_ENTRIES_DOCUMENTS_INACTIVE, (
            f"the sticky index should list only "
            f"{INDEX_ENTRIES_DOCUMENTS_INACTIVE}, got {entries}"
        )


# ---------------------------------------------------------------------------
# 140982 / ESERV-COO-TC-014 — dark-theme palette
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Theming")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The page renders the verified dark-theme palette when Dark mode is active")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.accessibility
@pytest.mark.pbi_130947
@pytest.mark.tc_140982
@pytest.mark.traceability("ESERV-COO-TC-014")
@allure.label("pbi", "130947")
@allure.label("testcase", "140982")
def test_coo_dark_theme_palette(page):
    """ESERV-COO-TC-014 — Azure TC 140982."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    with allure.step("Switch the site theme to Dark via the accessibility widget"):
        coo.enable_dark_mode()
        assert coo.theme() == "dark"

    with allure.step("Inspect the section badges, headings and body copy"):
        for section_id, badge in (
            (SECTION_OVERVIEW, "About the service"),
            (SECTION_DOCUMENTS, "Official Compliance Guide"),
            (SECTION_APPLY, "How to Apply"),
        ):
            assert_color(coo, coo.section_badge_selector(section_id), "#C44561",
                         label=f"dark badge '{badge}'")
            assert_color(coo, coo.section_title_selector(section_id), "#FFFFFF",
                         label=f"dark heading of {section_id}")
            assert_color(coo, coo.section_intro_selector(section_id), "#EDEDED",
                         label=f"dark body copy of {section_id}")

    with allure.step("Inspect the sticky index, info cards and step numerals"):
        for i in range(coo.index_count()):
            assert_color(coo, coo.INDEX_LABEL, "#DEDEDD", index=i,
                         label=f"dark index label {i + 1}")
            assert_color(coo, coo.INDEX_NUM, "#A8A8A7", index=i,
                         label=f"dark index numeral {i + 1}")
        for i in range(coo.card_count()):
            assert_color(coo, coo.CARD_TITLE, "#F6F6F6", index=i,
                         label=f"dark info-card title {i + 1}")
            assert_color(coo, coo.CARD_DESC, "#D0D0D0", index=i,
                         label=f"dark info-card description {i + 1}")
        for i in range(coo.step_count()):
            assert_color(coo, coo.STEP_NUM, "#C44561", index=i,
                         label=f"dark step numeral {STEP_NUMERALS[i]}")


# ---------------------------------------------------------------------------
# 140983 / ESERV-COO-TC-015 — English page renders left-to-right end to end
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Bilingual / direction")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The English page renders left-to-right end to end")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.bilingual
@pytest.mark.pbi_130947
@pytest.mark.tc_140983
@pytest.mark.traceability("ESERV-COO-TC-015")
@allure.label("pbi", "130947")
@allure.label("testcase", "140983")
def test_coo_english_page_is_ltr_end_to_end(page):
    """ESERV-COO-TC-015 — Azure TC 140983."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")

    assert coo.document_direction() == "ltr"

    left_aligned = [
        (coo.HERO_EYEBROW, "hero eyebrow"),
        (coo.HERO_TITLE, "hero title"),
        (coo.HERO_DESC, "hero description"),
        (coo.section_badge_selector(SECTION_OVERVIEW), "Overview badge"),
        (coo.section_title_selector(SECTION_OVERVIEW), "Overview heading"),
        (coo.section_intro_selector(SECTION_OVERVIEW), "Overview body"),
        (coo.section_badge_selector(SECTION_DOCUMENTS), "Documents Required badge"),
        (coo.section_title_selector(SECTION_DOCUMENTS), "Documents Required heading"),
        (coo.section_badge_selector(SECTION_APPLY), "How to Apply badge"),
        (coo.section_title_selector(SECTION_APPLY), "How to Apply heading"),
        (coo.STEP_TITLE, "first step title"),
        (coo.BANNER_TITLE, "banner heading"),
    ]
    with allure.step("Inspect the alignment of the hero, sections, steps and banner"):
        for selector, label in left_aligned:
            assert coo.effective_text_align(selector) == "left", (
                f"{label} is not left-aligned"
            )
            assert not coo.is_text_clipped(selector), f"{label} is clipped"

    with allure.step("Confirm the sticky index sits to the left of the content column"):
        assert coo.element_box(coo.INDEX_COL)["x"] < coo.element_box(coo.CONTENT)["x"]

    assert not coo.has_horizontal_scrollbar()


# ---------------------------------------------------------------------------
# 140984 / ESERV-COO-TC-016 — Arabic page renders RTL with the verified copy
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Bilingual / direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Arabic page renders right-to-left with the verified Arabic copy")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.pbi_130947
@pytest.mark.tc_140984
@pytest.mark.traceability("ESERV-COO-TC-016")
@allure.label("pbi", "130947")
@allure.label("testcase", "140984")
def test_coo_arabic_page_is_rtl_with_arabic_copy(page):
    """ESERV-COO-TC-016 — Azure TC 140984."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="ar")

    with allure.step("Confirm the document is RTL and the layout is mirrored"):
        assert coo.document_direction() == "rtl"
        assert coo.element_box(coo.INDEX_COL)["x"] > coo.element_box(coo.CONTENT)["x"]

    with allure.step("Read the hero, quick facts, sticky index and banner copy"):
        assert coo.hero_eyebrow_text() == HERO_EYEBROW_AR
        assert coo.hero_title_text() == HERO_TITLE_AR
        assert coo.hero_description_text() == HERO_DESC_AR
        assert coo.hero_cta_labels() == CTA_LABELS_AR
        assert coo.fact_pairs() == QUICK_FACTS_AR
        # This case enumerates the three in-scope index entries (unlike 140972,
        # which additionally asserts "exactly three" — that exactness belongs to
        # 140972 and is not duplicated here).
        assert coo.index_entries()[:3] == INDEX_ENTRIES_AR
        assert coo.banner_eyebrow_text() == BANNER_EYEBROW_AR
        assert coo.banner_title_text() == BANNER_TITLE_AR

    with allure.step("Confirm all text is right-aligned and none is clipped"):
        for selector, label in (
            (coo.HERO_EYEBROW, "hero eyebrow"),
            (coo.HERO_TITLE, "hero title"),
            (coo.HERO_DESC, "hero description"),
            (coo.INDEX_LABEL, "first index label"),
            (coo.BANNER_TITLE, "banner heading"),
        ):
            assert coo.effective_text_align(selector) == "right", (
                f"{label} is not right-aligned"
            )
            assert not coo.is_text_clipped(selector), f"{label} is clipped"


# ---------------------------------------------------------------------------
# 140985 / ESERV-COO-TC-017 — Arabic hero title uses the Arabic type scale
# ---------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Bilingual / direction")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic hero title uses the Arabic type scale rather than the English one")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.bilingual
@pytest.mark.pbi_130947
@pytest.mark.tc_140985
@pytest.mark.traceability("ESERV-COO-TC-017")
@allure.label("pbi", "130947")
@allure.label("testcase", "140985")
def test_coo_arabic_hero_title_type_scale(page):
    """ESERV-COO-TC-017 — Azure TC 140985."""
    coo = CertificateOfOriginPage(page)

    with allure.step("Read the English hero title's computed type scale"):
        coo.open_coo(locale="en")
        assert coo.hero_title_text() == HERO_TITLE_EN
        assert_type_tokens(coo, coo.HERO_TITLE, weight=700, size="48px",
                           line_height="60px", color="#FFFFFF",
                           label="English hero title")

    with allure.step("Switch to the Arabic page and read the same computed values"):
        coo.open_coo(locale="ar")
        assert coo.hero_title_text() == HERO_TITLE_AR
        assert_type_tokens(coo, coo.HERO_TITLE, weight=700, size="40px",
                           line_height="64px", color="#FFFFFF",
                           label="Arabic hero title")
        assert coo.effective_text_align(coo.HERO_TITLE) == "right"
        assert not coo.hero_overflows_container()

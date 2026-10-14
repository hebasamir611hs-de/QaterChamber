"""
web/tests/certificate_of_origin/test_certificate_of_origin_web.py — the Web
(public-site) cases for PBI 130947 (QC-SVC-005 — Certificate of Origin
Online), sourced from the injected Azure DevOps suite handed off by the QA
Manager. All 17 cases in the batch carry Platform = Web, so this is the only
module for this page.

SCRIPTED HERE (all 17): 140969, 140970, 140971, 140972, 140973, 140974,
140975, 140976, 140977, 140978, 140979, 140980, 140981, 140982, 140983,
140984, 140985 (2026-10-07 batch: +21 more at the end of this module,
logged-out, scripted offline) — of which 16 are delivered on the Web surface and 140981 is
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


# ===========================================================================
# 2026-10-07 batch (OFFLINE scripted, not executed) — the 21 remaining Web
# Automation cases of suite 140380: 140986-140991, 140997, 140999, 141002,
# 141005, 141006, 141119-141127, 141144.
# Every one runs in a fresh LOGGED-OUT context (`"auth": False`), unlike the
# earlier tests above that use the default auth-state page. URLs: the cases'
# /en/e-services/... path is a 404 (see the module docstring); the canonical
# page is reached through web_url().
# ===========================================================================
E1920 = {"viewport": (1920, 1080), "auth": False}
T768 = {"viewport": (768, 1024), "auth": False}
M390 = {"viewport": (390, 844), "auth": False}
DARK_PALETTE = {hex_to_rgb(h) for h in ("#1D1D1B", "#343432", "#4A4A49")}
WHITE = hex_to_rgb("#FFFFFF")
PDF_LABEL = "Certificate of Origin (PDF)"
DOWNLOAD_TITLE_EN = "Download the Application Form"
BANNER_EYEBROW_EN = "Ready to continue?"
BANNER_TITLE_EN = "Choose the service you need"
APPLY_HEADING_EN = "Apply for a Certificate of Origin Online"
SECOND_REQUIREMENT = "QCTEST-130947 Second Requirement"
FORM_FILE = "QCTEST-130947-application-form.pdf"
LOGIN_URL = "https://coo.qatarchamber.com/login"
VERIFY_URL = "https://coo.qatarchamber.com/verify"
DEAD_URL = "https://coo.qatarchamber.com/qctest-130947-nonexistent"
FACT_LABELS_AR = ["قناة الخدمة", "أنواع الشهادات", "التحقق", "نطاق الخدمة"]
SECTION_HEADINGS_AR = ["نظرة عامة", "المستندات المطلوبة", "التقديم على شهادة المنشأ إلكترونيًا"]
CARD_TITLES_AR = ["التقديم على شهادة المنشأ", "التحقق من شهادة المنشأ", "متطلبات التقديم"]
ACCORDION_ITEM_AR = "شهادة المنشأ للأمتعة الشخصية"
STEP_TITLES_AR = ["تنزيل واستكمال نموذج الطلب", "استلام بيانات الدخول", "الدخول إلى النظام الإلكتروني",
                  "مراجعة المتطلبات", "الالتزام بقواعد المنشأ", "شاركنا ملاحظاتك"]
DOWNLOAD_TITLE_AR = "تنزيل نموذج الطلب"
DOWNLOAD_BUTTON_AR = "تحميل"
# The content column's top once a section is scrolled to (scroll-margin-top 96px,
# sticky header); "at the top of the content column" = within this band.
SECTION_TOP_BAND = (0.0, 160.0)


def _px(value: str) -> float:
    return float(str(value).replace("px", "") or 0)


def _rgb_of(css: str):
    m = re.findall(r"[\d.]+", css or "")
    return tuple(int(float(v)) for v in m[:3]) if len(m) >= 3 else None


def _no_overlap(boxes) -> bool:
    bs = [b for b in boxes if b]
    for i, a in enumerate(bs):
        for b in bs[i + 1:]:
            if (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
                    and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1):
                return False
    return True


def _stacked(boxes) -> bool:
    return all(boxes[k]["y"] + boxes[k]["height"] <= boxes[k + 1]["y"] + 1 for k in range(len(boxes) - 1))


def _type(coo, selector, weight, size, line, index=0):
    s = coo.computed_style(selector, ["fontFamily", "fontWeight", "fontSize", "lineHeight"], index=index)
    assert font_family_contains(s["fontFamily"], "Cairo"), f"{selector}: font {s['fontFamily']!r}"
    assert (str(s["fontWeight"]), px_close(s["fontSize"], size), px_close(s["lineHeight"], line)) == (str(weight), True, True), (
        f"{selector}: expected {weight} {size}/{line}, got {s['fontWeight']} {s['fontSize']}/{s['lineHeight']}")


def _nav_requests(page) -> list:
    """Records every navigation-request URL in the context (new tabs included)."""
    seen = []
    page.context.on("request", lambda r: seen.append(r.url) if r.is_navigation_request() else None)
    return seen


# --------------------------------------------------------------------------
# Compatibility (140986-140991)
# --------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Compatibility")
@allure.title("The page renders correctly at 1920px in English Light theme")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140986
@pytest.mark.traceability("ESERV-COO-TC-018")
@allure.label("pbi", "130947")
@allure.label("testcase", "140986")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_desktop_1920_en_light(page):
    """ESERV-COO-TC-018 — Azure TC 140986. Hero padding 40/300/0 on linear-gradient(118deg,#46071E,#601430 48%,
    #911731); body 64/300 with a 24px gap; 312px #F6F6F6 index rail left of the 944px content column (40px
    left padding); footer 80/300/32 on 90deg #422C1B 16% -> #911731 84%; no h-scroll/clipping; title Cairo
    700 48/60."""
    coo = CertificateOfOriginPage(page)
    coo.start_console_capture()
    coo.open_coo(locale="en")
    assert coo.http_status(page.url) == 200
    assert coo.document_direction() == "ltr"
    assert coo.console_errors() == []
    with allure.step("Hero, body, index rail, content column and footer layout tokens"):
        hero = coo.computed_style(coo.HERO, ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "backgroundImage"])
        assert [_px(hero[k]) for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft")] == [40, 300, 0, 300], hero
        g = hero["backgroundImage"].replace(" ", "")
        assert "linear-gradient(118deg,rgb(70,7,30)" in g and "rgb(96,20,48)48%" in g and "rgb(145,23,49)" in g, hero["backgroundImage"]
        body = coo.computed_style(coo.BODY, ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft"])
        assert [_px(body["paddingTop"]), _px(body["paddingRight"]), _px(body["paddingLeft"])] == [64, 300, 300], body
        assert _px(coo.computed_style(coo.LAYOUT, ["columnGap"])["columnGap"]) == 24
        rail, content = coo.element_box(coo.INDEX_COL), coo.element_box(coo.CONTENT)
        assert abs(rail["width"] - 312) <= 1 and rail["x"] < content["x"], (rail, content)
        assert _rgb_of(coo.computed_style(coo.INDEX, ["backgroundColor"])["backgroundColor"]) == hex_to_rgb("#F6F6F6")
        assert abs(content["width"] - 944) <= 1, content
        assert _px(coo.computed_style(coo.CONTENT, ["paddingLeft"])["paddingLeft"]) == 40
        foot = coo.computed_style(coo.FOOTER, ["paddingTop", "paddingRight", "paddingBottom", "paddingLeft", "backgroundImage"])
        assert [_px(foot[k]) for k in ("paddingTop", "paddingRight", "paddingBottom", "paddingLeft")] == [80, 300, 32, 300], foot
        fg = foot["backgroundImage"].replace(" ", "")
        assert "linear-gradient(90deg,rgb(66,44,27)16%,rgb(145,23,49)84%)" in fg, foot["backgroundImage"]
    with allure.step("Scroll top to bottom"):
        assert not coo.has_horizontal_scrollbar()
        assert coo.clipped_text_in() == []
        _type(coo, coo.HERO_TITLE, 700, "48px", "60px")
        assert coo.hero_title_text() == HERO_TITLE_EN


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Compatibility")
@allure.title("The page renders correctly at 1920px in Arabic Light theme")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140987
@pytest.mark.traceability("ESERV-COO-TC-019")
@allure.label("pbi", "130947")
@allure.label("testcase", "140987")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_desktop_1920_ar_light(page):
    """ESERV-COO-TC-019 — Azure TC 140987. dir=rtl; 312px rail on the RIGHT of the 944px column; title right-aligned
    Cairo 700 40/64; quick facts read right to left; footer mirrored; no h-scroll/clipping; height <= 3073."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="ar")
    assert coo.http_status(page.url) == 200 and coo.document_direction() == "rtl"
    rail, content = coo.element_box(coo.INDEX_COL), coo.element_box(coo.CONTENT)
    assert rail["x"] > content["x"] and abs(rail["width"] - 312) <= 1 and abs(content["width"] - 944) <= 1, (rail, content)
    assert coo.hero_title_text() == HERO_TITLE_AR
    assert coo.effective_text_align(coo.HERO_TITLE) == "right"
    _type(coo, coo.HERO_TITLE, 700, "40px", "64px")
    facts = coo.boxes(coo.FACT)
    assert [lbl for lbl, _ in coo.fact_pairs()] == FACT_LABELS_AR
    assert all(facts[k]["x"] > facts[k + 1]["x"] for k in range(len(facts) - 1)), "quick facts do not read right to left"
    assert coo.computed_style(coo.FOOTER, ["direction"])["direction"] == "rtl", "footer is not mirrored"
    assert not coo.has_horizontal_scrollbar()
    assert coo.clipped_text_in() == []
    assert coo.page_height() <= 3073, f"page height {coo.page_height()} exceeds the 3073px reference"


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Compatibility")
@allure.title("The page renders correctly at 1920px in Dark theme")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_140988
@pytest.mark.traceability("ESERV-COO-TC-020")
@allure.label("pbi", "130947")
@allure.label("testcase", "140988")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_desktop_1920_dark(page):
    """ESERV-COO-TC-020 — Azure TC 140988. Dark persists across reload; surfaces from #1D1D1B/#343432/#4A4A49;
    accent #C44561; rail not #F6F6F6; legible contrast; no white cards; no h-scroll."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en").enable_dark_mode()
    coo.reload_coo()
    assert coo.theme() == "dark", "Dark theme did not persist across a reload"
    for sel in (coo.BODY, coo.INDEX):
        rgb = _rgb_of(coo.computed_style(sel, ["backgroundColor"])["backgroundColor"])
        assert rgb in DARK_PALETTE, f"{sel} surface {rgb} is not in the dark palette"
    assert_color(coo, coo.section_badge_selector(SECTION_OVERVIEW), "#C44561", label="accent (Overview badge)")
    assert _rgb_of(coo.computed_style(coo.INDEX, ["backgroundColor"])["backgroundColor"]) != hex_to_rgb("#F6F6F6")
    whites = [sel for sel in (coo.CARD, coo.ACC_ITEM, coo.DOWNLOAD_CARD)
              if any(_rgb_of(s["backgroundColor"]) == WHITE for s in coo.computed_styles_all(sel, ["backgroundColor"]))]
    assert whites == [], f"light-theme white backgrounds kept in dark mode: {whites!r}"
    assert coo.low_contrast_text() == []
    assert not coo.has_horizontal_scrollbar()


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Compatibility")
@allure.title("The page reflows to a single column at 390px in English")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140989
@pytest.mark.traceability("ESERV-COO-TC-021")
@allure.label("pbi", "130947")
@allure.label("testcase", "140989")
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_coo_mobile_390_en(page):
    """ESERV-COO-TC-021 — Azure TC 140989. Title Cairo 700 30/38; facts and the three info cards stack; headings
    600 18/28; no index side column; both hero CTAs full width, unclipped; no overflow."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    assert not coo.has_horizontal_scrollbar()
    _type(coo, coo.HERO_TITLE, 700, "30px", "38px")
    assert _stacked(coo.boxes(coo.FACT)), "quick facts are not one per row"
    assert coo.card_titles() == CARD_TITLES_EN and _stacked(coo.card_boxes()), "info cards do not stack in order"
    for i in range(coo.page.locator(coo.SECTION_TITLE).count()):
        _type(coo, coo.SECTION_TITLE, 600, "18px", "28px", index=i)
    assert not coo.is_visible(coo.INDEX_COL), "the index rail is still rendered as a side column"
    ctas, row = coo.boxes(coo.HERO_CTA), coo.element_box(coo.HERO_CTAS)
    assert len(ctas) == 2 and all(abs(c["width"] - row["width"]) <= 1 for c in ctas), (ctas, row)
    assert coo.hero_cta_labels() == CTA_LABELS_EN and not any(coo.is_text_clipped(coo.HERO_CTA, i) for i in range(2))
    assert coo.clipped_text_in() == []


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Compatibility")
@allure.title("The page reflows to a single mirrored column at 390px in Arabic")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140990
@pytest.mark.traceability("ESERV-COO-TC-022")
@allure.label("pbi", "130947")
@allure.label("testcase", "140990")
@pytest.mark.parametrize("page", [M390], indirect=True)
def test_coo_mobile_390_ar(page):
    """ESERV-COO-TC-022 — Azure TC 140990. rtl; title 700 30/38 right-aligned; facts and cards stack right-aligned;
    accordion chevrons on the left edge; AR CTA labels in full; no overlapping blocks."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="ar")
    assert coo.document_direction() == "rtl" and not coo.has_horizontal_scrollbar()
    assert coo.hero_title_text() == HERO_TITLE_AR
    _type(coo, coo.HERO_TITLE, 700, "30px", "38px")
    assert coo.effective_text_align(coo.HERO_TITLE) == "right"
    assert _stacked(coo.boxes(coo.FACT)) and _stacked(coo.card_boxes())
    assert all(coo.effective_text_align(coo.FACT_LABEL, i) == "right" for i in range(coo.fact_count()))
    assert all(coo.effective_text_align(coo.CARD_TITLE, i) == "right" for i in range(coo.card_count()))
    marks, rows = coo.boxes(f"{coo.ACC_ITEM} {coo.ACC_MARK}"), coo.boxes(coo.ACC_QUESTION)
    assert marks and all(m["x"] + m["width"] / 2 < r["x"] + r["width"] / 2 for m, r in zip(marks, rows)), (
        "accordion chevrons are not on the left edge")
    assert coo.hero_cta_labels() == CTA_LABELS_AR and not any(coo.is_text_clipped(coo.HERO_CTA, i) for i in range(2))
    assert coo.clipped_text_in() == []
    # Sibling blocks only (the banner sits inside .qc-coo-body, so body/banner would overlap by containment).
    blocks = [coo.element_box(coo.HERO)] + coo.boxes(coo.SECTION) + [coo.element_box(coo.BANNER), coo.element_box(coo.FOOTER)]
    assert _no_overlap(blocks), "a block overlaps the next"


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Compatibility")
@allure.title("The page reflows legibly at 768px in English")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_140991
@pytest.mark.traceability("ESERV-COO-TC-023")
@allure.label("pbi", "130947")
@allure.label("testcase", "140991")
@pytest.mark.parametrize("page", [T768], indirect=True)
def test_coo_tablet_768_en(page):
    """ESERV-COO-TC-023 — Azure TC 140991. Reflow + legibility (no Figma frame, A-6): facts unclipped; <= 2 cards
    per row; rail hidden or not overlapping; banner CTAs side by side or stacked cleanly; headers clickable;
    index anchors scroll."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    assert not coo.has_horizontal_scrollbar()
    assert not any(coo.is_text_clipped(coo.FACT_LABEL, i) or coo.is_text_clipped(coo.FACT_VALUE, i)
                   for i in range(coo.fact_count()))
    rows = {}
    for b in coo.card_boxes():
        rows[round(b["y"])] = rows.get(round(b["y"]), 0) + 1
    assert max(rows.values()) <= 2, f"info cards per row {rows!r}"
    if coo.is_visible(coo.INDEX_COL):
        assert _no_overlap([coo.element_box(coo.INDEX_COL), coo.element_box(coo.CONTENT)])
    assert _no_overlap(coo.boxes(coo.BANNER_CTA))
    assert coo.clipped_text_in() == []
    coo.scroll_section_into_view(SECTION_DOCUMENTS)
    coo.expand_accordion_item(ACCORDION_ITEM_TITLE)
    assert coo.is_accordion_item_expanded(ACCORDION_ITEM_TITLE)
    if coo.is_visible(coo.INDEX_COL):
        coo.click_index_entry("How to Apply")
        top = coo.section_top(SECTION_APPLY)
        assert SECTION_TOP_BAND[0] <= top <= SECTION_TOP_BAND[1], f"How to Apply section top at {top}px after the anchor"


# --------------------------------------------------------------------------
# Acceptance journeys (140997, 140999, 141002)
# --------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Journey")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A public visitor sees the complete published page with every active component in display order")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140997
@pytest.mark.traceability("ESERV-COO-TC-029")
@allure.label("pbi", "130947")
@allure.label("testcase", "140997")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_public_full_page_en(page):
    """ESERV-COO-TC-029 — Azure TC 140997."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    assert coo.http_status(page.url) == 200 and coo.page.locator("input[type='password']").count() == 0
    with allure.step("Hero, quick facts and sticky index"):
        assert (coo.hero_eyebrow_text(), coo.hero_title_text(), coo.hero_description_text()) == (
            HERO_EYEBROW_EN, HERO_TITLE_EN, HERO_DESC_EN)
        assert coo.hero_cta_labels() == CTA_LABELS_EN
        assert coo.fact_pairs() == QUICK_FACTS_EN
        assert coo.index_entries() == INDEX_ENTRIES_EN
    with allure.step("Sections 01, 02, 03"):
        assert coo.section_intro_text(SECTION_OVERVIEW).startswith(OVERVIEW_BODY_PREFIX)
        assert coo.card_titles() == CARD_TITLES_EN
        assert coo.section_intro_text(SECTION_DOCUMENTS) == DOCUMENTS_INTRO_EN
        assert coo.pdf_button_label() == PDF_LABEL
        assert coo.accordion_item_count() > 0 and not any(
            coo.is_accordion_item_expanded(t) for t in coo.accordion_titles()), "accordion is not collapsed on load"
        assert coo.step_numerals() == STEP_NUMERALS and coo.step_titles() == STEP_TITLES_EN
        assert coo.download_card_title() == DOWNLOAD_TITLE_EN
    with allure.step("Next-step banner; nothing Inactive or draft-only rendered"):
        coo.scroll_to_banner()
        assert (coo.banner_eyebrow_text(), coo.banner_title_text(), coo.banner_body_text()) == (
            BANNER_EYEBROW_EN, BANNER_TITLE_EN, BANNER_BODY_EN)
        assert coo.banner_cta_labels() == CTA_LABELS_EN
        assert coo.page.locator(coo.SECTION).count() == 3, "a section beyond the three active ones is rendered"


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Journey")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Arabic published page delivers the full authored Arabic content set end to end")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_140999
@pytest.mark.traceability("ESERV-COO-TC-031")
@allure.label("pbi", "130947")
@allure.label("testcase", "140999")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_public_full_page_ar(page):
    """ESERV-COO-TC-031 — Azure TC 140999. No English fallback in any named position."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="ar")
    assert coo.http_status(page.url) == 200 and coo.document_direction() == "rtl"
    assert (coo.hero_eyebrow_text(), coo.hero_title_text()) == (HERO_EYEBROW_AR, HERO_TITLE_AR)
    assert coo.hero_cta_labels() == CTA_LABELS_AR
    assert coo.fact_pairs() == QUICK_FACTS_AR
    assert coo.index_entries() == INDEX_ENTRIES_AR
    assert [coo.section_title_text(s) for s in (SECTION_OVERVIEW, SECTION_DOCUMENTS, SECTION_APPLY)] == SECTION_HEADINGS_AR
    assert coo.card_titles() == CARD_TITLES_AR
    assert ACCORDION_ITEM_AR in coo.accordion_titles()
    assert coo.step_titles() == STEP_TITLES_AR
    assert (coo.download_card_title(), coo.download_button_label()) == (DOWNLOAD_TITLE_AR, DOWNLOAD_BUTTON_AR)
    coo.scroll_to_banner()
    assert (coo.banner_eyebrow_text(), coo.banner_title_text()) == (BANNER_EYEBROW_AR, BANNER_TITLE_AR)


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Journey")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Document discovery: sticky index -> expanded requirement -> PDF guide in a new tab")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_141002
@pytest.mark.traceability("ESERV-COO-TC-034")
@allure.label("pbi", "130947")
@allure.label("testcase", "141002")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_document_discovery_journey(page):
    """ESERV-COO-TC-034 — Azure TC 141002."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    with allure.step("Click '02 Documents Required'"):
        coo.click_index_entry(DOCUMENTS_INDEX_LABEL)
        assert coo.active_index_label() == DOCUMENTS_INDEX_LABEL
        top = coo.section_top(SECTION_DOCUMENTS)
        assert SECTION_TOP_BAND[0] <= top <= SECTION_TOP_BAND[1], f"Documents Required section top at {top}px"
    with allure.step(f"Expand '{ACCORDION_ITEM_TITLE}'"):
        coo.expand_accordion_item(ACCORDION_ITEM_TITLE)
        assert coo.accordion_item_answer_text(ACCORDION_ITEM_TITLE).startswith(ACCORDION_ANSWER_PREFIX)
        others = [t for t in coo.accordion_titles() if t != ACCORDION_ITEM_TITLE]
        assert not any(coo.is_accordion_item_expanded(t) for t in others)
    with allure.step(f"Click '{PDF_LABEL}'"):
        url, title = page.url, coo.hero_title_text()
        popup = coo.click_expect_popup(coo.PDF_BUTTON)
        assert popup is not page and popup.url not in ("", "about:blank")
        assert (page.url, coo.hero_title_text()) == (url, title), "the original tab did not stay on the COO page"


# --------------------------------------------------------------------------
# Hero CTAs (141005, 141006, 141144)
# --------------------------------------------------------------------------
def _cta_new_tab(page, index, expected):
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    assert coo.hero_cta_labels()[index] == CTA_LABELS_EN[index]
    assert coo.href_of(coo.HERO_CTA, index) == expected, f"href {coo.href_of(coo.HERO_CTA, index)!r} != {expected!r}"
    navs = _nav_requests(page)
    url = page.url
    popup = coo.click_expect_popup(coo.HERO_CTA, index)
    assert popup is not page, "the CTA did not open a new tab"
    assert any(u.rstrip("/") == expected.rstrip("/") for u in navs), f"the new tab never requested {expected}: {navs!r}"
    assert page.url == url and coo.is_hero_visible(), "the Certificate of Origin page did not stay loaded"


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Hero")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Login to COO call to action opens the configured portal URL in a new tab")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_141005
@pytest.mark.traceability("ESERV-COO-TC-037")
@allure.label("pbi", "130947")
@allure.label("testcase", "141005")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_login_cta_redirect(page):
    """ESERV-COO-TC-037 — Azure TC 141005. href exactly https://coo.qatarchamber.com/login; New Tab."""
    _cta_new_tab(page, 0, LOGIN_URL)


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Hero")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Verify Certificate call to action opens the configured verification URL in a new tab")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.eserv
@pytest.mark.uat
@pytest.mark.pbi_130947
@pytest.mark.tc_141006
@pytest.mark.traceability("ESERV-COO-TC-038")
@allure.label("pbi", "130947")
@allure.label("testcase", "141006")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_verify_cta_redirect(page):
    """ESERV-COO-TC-038 — Azure TC 141006. href exactly https://coo.qatarchamber.com/verify; New Tab."""
    _cta_new_tab(page, 1, VERIFY_URL)


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Hero")
@allure.title("The page degrades gracefully when a CTA Redirect URL is well-formed but its destination returns 404")
@pytest.mark.web
@pytest.mark.edge
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141144
@pytest.mark.traceability("ESERV-COO-TC-184")
@allure.label("pbi", "130947")
@allure.label("testcase", "141144")
@pytest.mark.skip(reason="CONDITIONAL: step 1 rewrites the Redirect URL of the shared 'Login to COO' CTA that the live "
                         "COO page renders. That record is real shared content, it is not in the approved live-restore "
                         "set (reports/live-restore/live_restore.py), and no QCTEST copy of the CTA can be rendered on "
                         "the page. Needs an explicit, ID-named go-ahead before it may run.")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_dead_cta_destination_degrades(page):
    """ESERV-COO-TC-184 — Azure TC 141144. Precondition (CMS, not automated here): the shared 'Login to COO' CTA's
    Redirect URL set to https://coo.qatarchamber.com/qctest-130947-nonexistent and published. The public half
    below runs as written once that precondition exists."""
    coo = CertificateOfOriginPage(page)
    coo.start_console_capture()
    coo.open_coo(locale="en")
    assert coo.href_of(coo.HERO_CTA, 0) == DEAD_URL and coo.href_of(coo.BANNER_CTA, 0) == DEAD_URL
    assert coo.is_enabled_link(coo.HERO_CTA, 0) and coo.is_enabled_link(coo.BANNER_CTA, 0)
    popup = coo.click_expect_popup(coo.HERO_CTA, 0)
    assert coo.http_status(DEAD_URL) == 404
    assert popup is not page and coo.is_hero_visible() and coo.console_errors() == []
    coo.reload_coo()
    assert coo.hero_title_text() == HERO_TITLE_EN and coo.card_count() and coo.step_count() and coo.is_banner_visible()


# --------------------------------------------------------------------------
# Controls (141119-141123)
# --------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Documents Required")
@allure.title("The Certificate of Origin (PDF) action button is an activatable control, including by keyboard")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141119
@pytest.mark.traceability("ESERV-COO-TC-159")
@allure.label("pbi", "130947")
@allure.label("testcase", "141119")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_pdf_button_activatable(page):
    """ESERV-COO-TC-159 — Azure TC 141119."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    coo.scroll_section_into_view(SECTION_DOCUMENTS)
    assert coo.is_enabled_link(coo.PDF_BUTTON), "the PDF button is not an enabled control with a non-empty href"
    assert coo.tab_to(coo.PDF_BUTTON), "the PDF button is not reachable in the keyboard tab order"
    ring = coo.focus_indicator(coo.PDF_BUTTON)
    assert ring["visible"] and (ring["outline"] != "none" or ring["shadow"] != "none"), f"no visible focus indicator: {ring!r}"
    popup = coo.press_enter_expect_popup()
    assert popup is not page and popup.url not in ("", "about:blank")


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Documents Required")
@allure.title("Clicking a document-requirement accordion header expands its content panel")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141120
@pytest.mark.traceability("ESERV-COO-TC-160")
@allure.label("pbi", "130947")
@allure.label("testcase", "141120")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_accordion_expands(page):
    """ESERV-COO-TC-160 — Azure TC 141120. PRECONDITION: a second active item 'QCTEST-130947 Second Requirement';
    the last assertion is gated on its presence."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    coo.scroll_section_into_view(SECTION_DOCUMENTS)
    titles = coo.accordion_titles()
    assert not any(coo.is_accordion_item_expanded(t) or coo.is_accordion_answer_visible(t) for t in titles)
    before = coo.accordion_chevron_transform(ACCORDION_ITEM_TITLE)
    coo.expand_accordion_item(ACCORDION_ITEM_TITLE)
    assert coo.is_accordion_answer_visible(ACCORDION_ITEM_TITLE)
    assert coo.accordion_item_answer_text(ACCORDION_ITEM_TITLE).startswith(ACCORDION_ANSWER_PREFIX)
    assert coo.accordion_chevron_transform(ACCORDION_ITEM_TITLE) != before, "the chevron did not rotate"
    if SECOND_REQUIREMENT not in titles:
        pytest.skip(f"PRECONDITION UNAVAILABLE: no active accordion item {SECOND_REQUIREMENT!r} on the page "
                    f"(items: {titles!r}). The expansion half ran for real above.")
    assert not coo.is_accordion_item_expanded(SECOND_REQUIREMENT)


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Documents Required")
@allure.title("Clicking an expanded accordion header collapses it again")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141121
@pytest.mark.traceability("ESERV-COO-TC-161")
@allure.label("pbi", "130947")
@allure.label("testcase", "141121")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_accordion_collapses(page):
    """ESERV-COO-TC-161 — Azure TC 141121."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    coo.scroll_section_into_view(SECTION_DOCUMENTS)
    chevron, height = coo.accordion_chevron_transform(ACCORDION_ITEM_TITLE), coo.section_height(SECTION_DOCUMENTS)
    next_top = coo.section_top(SECTION_APPLY) + coo.scroll_y()  # document-relative
    coo.expand_accordion_item(ACCORDION_ITEM_TITLE)
    assert coo.is_accordion_answer_visible(ACCORDION_ITEM_TITLE)
    coo.collapse_accordion_item(ACCORDION_ITEM_TITLE)
    assert not coo.is_accordion_item_expanded(ACCORDION_ITEM_TITLE)
    assert not coo.is_accordion_answer_visible(ACCORDION_ITEM_TITLE)
    assert coo.accordion_chevron_transform(ACCORDION_ITEM_TITLE) == chevron
    assert abs(coo.section_height(SECTION_DOCUMENTS) - height) <= 1
    assert abs(coo.section_top(SECTION_APPLY) + coo.scroll_y() - next_top) <= 1


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("How to Apply")
@allure.title("Clicking the Download button downloads the configured application form file")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141122
@pytest.mark.traceability("ESERV-COO-TC-162")
@allure.label("pbi", "130947")
@allure.label("testcase", "141122")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_download_application_form(page):
    """ESERV-COO-TC-162 — Azure TC 141122. PRECONDITION: QCTEST-130947-application-form.pdf configured on the card;
    gated on the card's href naming that file."""
    import os

    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    assert coo.is_download_card_visible() and coo.is_enabled_link(coo.DOWNLOAD_BUTTON)
    href = coo.href_of(coo.DOWNLOAD_BUTTON)
    if FORM_FILE.rsplit(".", 1)[0] not in href:
        pytest.skip(f"PRECONDITION UNAVAILABLE: the download card is not configured with {FORM_FILE} (href {href!r}).")
    from urllib.parse import urljoin
    assert coo.http_status(urljoin(page.url, href)) == 200
    dl = coo.download_via_button()
    assert dl.suggested_filename == FORM_FILE
    assert os.path.getsize(dl.path()) > 0


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Sticky index")
@allure.title("Clicking a sticky section index entry scrolls to the matching section")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141123
@pytest.mark.traceability("ESERV-COO-TC-163")
@allure.label("pbi", "130947")
@allure.label("testcase", "141123")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_index_scrolls_to_section(page):
    """ESERV-COO-TC-163 — Azure TC 141123."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    coo.click_index_entry("How to Apply")
    assert coo.active_index_label() == "How to Apply"
    assert coo.section_title_text(SECTION_APPLY) == APPLY_HEADING_EN
    top = coo.section_top(SECTION_APPLY)
    assert SECTION_TOP_BAND[0] <= top <= SECTION_TOP_BAND[1], f"How to Apply section top at {top}px"
    pinned = coo.index_viewport_top()
    coo.click_index_entry("Overview")
    assert coo.active_index_label() == "Overview"
    assert coo.section_title_text(SECTION_OVERVIEW) == "Overview"
    top = coo.section_top(SECTION_OVERVIEW)
    assert SECTION_TOP_BAND[0] <= top <= SECTION_TOP_BAND[1], f"Overview section top at {top}px"
    assert abs(coo.index_viewport_top() - pinned) <= 1, "the index did not stay pinned"


# --------------------------------------------------------------------------
# Language and theme switches (141124-141127)
# --------------------------------------------------------------------------
@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Bilingual / direction")
@allure.title("Switching EN -> AR loads the Arabic Certificate of Origin page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141124
@pytest.mark.traceability("ESERV-COO-TC-164")
@allure.label("pbi", "130947")
@allure.label("testcase", "141124")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_switch_en_to_ar(page):
    """ESERV-COO-TC-164 — Azure TC 141124."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en")
    assert coo.document_direction() == "ltr" and coo.language_switcher_label() == "AR"
    coo.switch_language("ar")
    assert coo.document_direction() == "rtl" and coo.hero_title_text() == HERO_TITLE_AR


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Bilingual / direction")
@allure.title("Switching AR -> EN loads the English Certificate of Origin page at the top")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141125
@pytest.mark.traceability("ESERV-COO-TC-165")
@allure.label("pbi", "130947")
@allure.label("testcase", "141125")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_switch_ar_to_en(page):
    """ESERV-COO-TC-165 — Azure TC 141125."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="ar")
    assert coo.document_direction() == "rtl" and coo.language_switcher_label() == "EN"
    coo.switch_language("en")
    assert coo.document_direction() == "ltr" and coo.hero_title_text() == HERO_TITLE_EN
    assert coo.scroll_y() == 0


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Theming")
@allure.title("Switching Light -> Dark applies the dark palette")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141126
@pytest.mark.traceability("ESERV-COO-TC-166")
@allure.label("pbi", "130947")
@allure.label("testcase", "141126")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_theme_light_to_dark(page):
    """ESERV-COO-TC-166 — Azure TC 141126. 'About the service' badge #911731 -> #C44561; surfaces
    #1D1D1B/#343432/#4A4A49; no error, no clipping layout shift."""
    coo = CertificateOfOriginPage(page)
    coo.start_console_capture()
    coo.open_coo(locale="en")
    badge = coo.section_badge_selector(SECTION_OVERVIEW)
    assert coo.theme() != "dark"
    assert_color(coo, badge, "#911731", label="light badge")
    assert _rgb_of(coo.computed_style(coo.BODY, ["backgroundColor"])["backgroundColor"]) not in DARK_PALETTE
    coo.enable_dark_mode()
    assert_color(coo, badge, "#C44561", label="dark badge")
    for sel in (coo.BODY, coo.INDEX):
        assert _rgb_of(coo.computed_style(sel, ["backgroundColor"])["backgroundColor"]) in DARK_PALETTE, sel
    assert coo.console_errors() == [] and coo.clipped_text_in() == [] and not coo.has_horizontal_scrollbar()


@allure.epic("E-Services")
@allure.feature("Certificate of Origin Online")
@allure.story("Theming")
@allure.title("Switching Dark -> Light restores the light palette")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.eserv
@pytest.mark.pbi_130947
@pytest.mark.tc_141127
@pytest.mark.traceability("ESERV-COO-TC-167")
@allure.label("pbi", "130947")
@allure.label("testcase", "141127")
@pytest.mark.parametrize("page", [E1920], indirect=True)
def test_coo_theme_dark_to_light(page):
    """ESERV-COO-TC-167 — Azure TC 141127. Badge back to #911731; rail #F6F6F6 with #EDEDED stroke; no element
    left on a dark-theme colour."""
    coo = CertificateOfOriginPage(page)
    coo.open_coo(locale="en").enable_dark_mode()
    badge = coo.section_badge_selector(SECTION_OVERVIEW)
    assert_color(coo, badge, "#C44561", label="dark badge")
    coo.disable_dark_mode()
    assert coo.theme() != "dark"
    assert_color(coo, badge, "#911731", label="light badge")
    rail = coo.computed_style(coo.INDEX, ["backgroundColor", "borderTopColor", "borderTopWidth", "boxShadow"])
    assert _rgb_of(rail["backgroundColor"]) == hex_to_rgb("#F6F6F6"), rail
    edge = hex_to_rgb("#EDEDED")
    assert (_rgb_of(rail["borderTopColor"]) == edge and _px(rail["borderTopWidth"]) > 0) or str(edge) in (
        str(_rgb_of(rail["boxShadow"]))), f"rail stroke is not #EDEDED: {rail!r}"
    stuck = [c for c in coo.surface_colors() if _rgb_of(c) in DARK_PALETTE]
    assert stuck == [], f"surfaces still on dark-theme colours: {stuck!r}"

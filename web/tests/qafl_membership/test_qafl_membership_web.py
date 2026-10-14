"""
web/tests/qafl_membership/test_qafl_membership_web.py — Web cases for PBI 130718
(QAFL Membership Registration): page layout / Figma tokens, step rendering,
acknowledgement, compatibility, accessibility, wizard navigation and edge cases.

Field-level cases live in test_qafl_membership_step1_web.py and
test_qafl_membership_steps2_5_web.py. Shared data and AAA bodies: qafl_data.py.

SCRIPTED OFFLINE 2026-10-07, NOT EXECUTED. Locators come from an anonymous
GET of the public page (see the Page Object docstring); anything the static
HTML could not confirm is marked `# UNVERIFIED` in the Page Object.

Every test runs in a fresh logged-out context (`anon()`), as a public visitor.
Tests that submit use a `QCTEST-<tc_id>-<uuid8>` company name and the QA inbox.
Cases whose oracle has a Control_Panel / mailbox half run their Web half and
then end in an explicit `pytest.skip(...)`, so they are never reported Passed
on half their expected result. 146809 is skipped up front (its precondition
is a Form Manager rejection). 146806/146807 (61/59-minute idle) run only with
QAFL_RUN_IDLE_TESTS=1. 146532 emulates 200% zoom as a 960x540 CSS-px viewport.
"""

import os

import allure
import pytest

from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from web.pages.components.header_component import HeaderComponent
from web.pages.qafl_membership.qafl_membership_page import QaflMembershipPage
from web.tests.qafl_membership.qafl_data import (
    AR_ACK,
    EN_ACK,
    EN_SUBTITLE,
    FONT_PROPS,
    IMAGE_TOL,
    KB,
    LAYOUT_TOL,
    STEP1_MANDATORY,
    FileMaker,
    current_matches,
    anon,
    box_mismatches,
    build,
    effective_color,
    fill_all_and_submit,
    font_mismatches,
    has_latin,
    ltr_readable,
    normalise,
    open_page,
    px_close,
    qctest_name,
    reach_step,
    rgb,
)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the breadcrumb and hero banner render per Figma in English desktop light')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146498
@pytest.mark.traceability("146498")
@allure.label("pbi", "130718")
@allure.label("testcase", "146498")
@anon(viewport=(1920, 1080))
def test_146498_breadcrumb_and_hero_banner_render_per_figma_in_english_deskt(page, tmp_path):
    """Verify that the breadcrumb and hero banner render per Figma in English desktop light

    Steps (case is the oracle):
    1. Open the QAFL Membership Registration page in English at 1920x1080 light theme -> Page loads;
       hero band is 1920x242 with content width 1320 px
    2. Inspect the breadcrumb row -> Breadcrumb shows 'Home' then 'Councils, Committees & Partnerships'
       in Cairo 14/400 white with 4x8 chevron separator (Figma shows no third current-page crumb - see
       A-11)
    3. Inspect the hero title and subtitle -> Title 'QAFL Membership Registration' Cairo 48/700 line-
       height 60 white; subtitle 'Register your company for QAFL membership by providing verified
       company information, authorized contacts, and the required supporting documents.' Cairo 16/400
       white at 70% opacity
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "en")
    with allure.step("Hero band is 1920x242 with content width 1320 px"):
        issues = box_mismatches(qp.box(qp.HERO), 1920, 242) + box_mismatches(qp.box(qp.HERO_INNER), 1320)
        assert not issues, issues
    with allure.step("Breadcrumb: 'Home' then 'Councils, Committees & Partnerships', Cairo 14/400 white, 4x8 chevron, no third crumb"):
        assert qp.text_of(qp.BREADCRUMB_HOME_TEXT) == "Home"
        assert qp.text_of(qp.BREADCRUMB_CURRENT) == "Councils, Committees & Partnerships"
        assert qp.count(qp.BREADCRUMB_SEP) == 1, "a third crumb / extra separator is rendered"
        for sel in (qp.BREADCRUMB_HOME_TEXT, qp.BREADCRUMB_CURRENT):
            issues = font_mismatches(qp.style(sel, FONT_PROPS), size=14, weight=400, color="#FFFFFF")
            assert not issues, (sel, issues)
        issues = box_mismatches(qp.box(qp.BREADCRUMB_SEP), 4, 8, tol=IMAGE_TOL)
        assert not issues, ("chevron", issues)
    with allure.step("Title Cairo 48/700 lh 60 white; subtitle Cairo 16/400 white at 70% opacity"):
        assert qp.text_of(qp.HERO_TITLE) == "QAFL Membership Registration"
        issues = font_mismatches(qp.style(qp.HERO_TITLE, FONT_PROPS), size=48, weight=700, line_height=60, color="#FFFFFF")
        assert not issues, issues
        assert qp.text_of(qp.HERO_SUBTITLE) == EN_SUBTITLE
        st = qp.style(qp.HERO_SUBTITLE, FONT_PROPS)
        assert not font_mismatches(st, size=16, weight=400), font_mismatches(st, size=16, weight=400)
        assert effective_color(st) == (rgb("#FFFFFF"), 0.7), effective_color(st)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the breadcrumb and hero banner render mirrored per Figma in Arabic desktop light')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146499
@pytest.mark.traceability("146499")
@allure.label("pbi", "130718")
@allure.label("testcase", "146499")
@anon(viewport=(1920, 1080))
def test_146499_breadcrumb_and_hero_banner_render_mirrored_per_figma_in_arab(page, tmp_path):
    """Verify that the breadcrumb and hero banner render mirrored per Figma in Arabic desktop light

    Steps (case is the oracle):
    1. Open the page in Arabic at 1920x1080 light theme -> Page loads with dir=rtl; hero band 1920x246
    2. Inspect the breadcrumb row -> Breadcrumb reads right-to-left: 'الرئيسية' rightmost then 'المجالس
       واللجان والشراكات', chevron mirrored
    3. Inspect hero title and subtitle -> Title 'تسجيل عضوية QAFL' Cairo 40/700 line-height 64 white (AR
       title is 40 px vs 48 px EN - confirm intended, A-11); subtitle starts 'سجّل شركتك لعضوية QAFL من
       خلال تقديم بيانات الشركة الموثقة' right-aligned
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "ar")
    with allure.step("Page loads with dir=rtl; hero band 1920x246"):
        assert qp.document_direction() == "rtl"
        issues = box_mismatches(qp.box(qp.HERO), 1920, 246)
        assert not issues, issues
    with allure.step("Breadcrumb reads right-to-left with the chevron between the crumbs"):
        assert qp.text_of(qp.BREADCRUMB_HOME_TEXT) == "الرئيسية"
        assert qp.text_of(qp.BREADCRUMB_CURRENT) == "المجالس واللجان والشراكات"
        home, sep, cur = qp.box(qp.BREADCRUMB_HOME), qp.box(qp.BREADCRUMB_SEP), qp.box(qp.BREADCRUMB_CURRENT)
        assert home["x"] > sep["x"] > cur["x"], "breadcrumb is not mirrored (Home must be rightmost)"
    with allure.step("Title 'تسجيل عضوية QAFL' Cairo 40/700 lh 64 white; subtitle right-aligned"):
        assert qp.text_of(qp.HERO_TITLE) == "تسجيل عضوية QAFL"
        issues = font_mismatches(qp.style(qp.HERO_TITLE, FONT_PROPS), size=40, weight=700, line_height=64, color="#FFFFFF")
        assert not issues, issues
        assert qp.text_of(qp.HERO_SUBTITLE).startswith("سجّل شركتك لعضوية QAFL من خلال تقديم بيانات الشركة الموثقة")
        st = qp.style(qp.HERO_SUBTITLE, ["textAlign", "direction"])
        assert st["direction"] == "rtl" and st["textAlign"] in ("right", "start"), st


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the association overview section renders per Figma in English')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146500
@pytest.mark.traceability("146500")
@allure.label("pbi", "130718")
@allure.label("testcase", "146500")
@anon(viewport=(1920, 1080))
def test_146500_association_overview_section_renders_per_figma_in_english(page, tmp_path):
    """Verify that the association overview section renders per Figma in English

    Steps (case is the oracle):
    1. Open the page in English light theme -> Section sits left of the card in the 1320 px container
    2. Inspect eyebrow and heading -> Eyebrow 'About the association' Cairo 14/400 #911731; heading 'An
       overview of the Qatar Association for Freight Forwarding and Logistics' Cairo 36/700 line-height
       44 #1D1D1B
    3. Inspect intro paragraph and bullet list -> Intro paragraph starts 'The Qatar Association for
       Freight Forwarding and Logistics (' Cairo 16/400 #6C6C6B; exactly 5 bullets covering QAFL role,
       FIATA affiliation and chairmanship, first bullet starts 'Represents the sector's interests and
       supports its growth'
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "en")
    with allure.step("Section sits left of the card"):
        assert qp.box(qp.OVERVIEW_TEXT)["x"] < qp.box(qp.CARD)["x"]
    with allure.step("Eyebrow and heading tokens"):
        assert qp.text_of(qp.OVERVIEW_EYEBROW) == "About the association"
        issues = font_mismatches(qp.style(qp.OVERVIEW_EYEBROW, FONT_PROPS), size=14, weight=400, color="#911731")
        assert not issues, issues
        assert qp.text_of(qp.OVERVIEW_HEADING) == "An overview of the Qatar Association for Freight Forwarding and Logistics"
        issues = font_mismatches(qp.style(qp.OVERVIEW_HEADING, FONT_PROPS), size=36, weight=700, line_height=44, color="#1D1D1B")
        assert not issues, issues
    with allure.step("Intro paragraph and exactly 5 bullets"):
        assert qp.text_of(qp.OVERVIEW_INTRO).startswith("The Qatar Association for Freight Forwarding and Logistics (")
        issues = font_mismatches(qp.style(qp.OVERVIEW_INTRO, FONT_PROPS), size=16, weight=400, color="#6C6C6B")
        assert not issues, issues
        bullets = [normalise(b) for b in qp.texts(qp.OVERVIEW_BULLETS)]
        assert len(bullets) == 5, bullets
        assert bullets[0].startswith("Represents the sector's interests and supports its growth"), bullets[0]
        joined = " ".join(bullets)
        assert "FIATA" in joined and "chaired" in joined, "bullets do not cover FIATA affiliation and chairmanship"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the association overview section renders RTL in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146501
@pytest.mark.traceability("146501")
@allure.label("pbi", "130718")
@allure.label("testcase", "146501")
@anon(viewport=(1920, 1080))
def test_146501_association_overview_section_renders_rtl_in_arabic(page, tmp_path):
    """Verify that the association overview section renders RTL in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic light theme -> Section is on the right side of the card, text right-
       aligned
    2. Inspect eyebrow and heading -> Eyebrow 'عن الجمعية' #911731 14/400; heading 'نبذة عن جمعية قطر
       للشحن والخدمات اللوجستية' Cairo 36/700 #1D1D1B
    3. Inspect paragraph and bullets -> Paragraph starts 'جمعية قطر للشحن والخدمات اللوجستية هي لجنة'; 5
       bullets, markers on the right, no clipping or English fallback text
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "ar")
    with allure.step("Section is on the right side of the card, text right-aligned"):
        assert qp.box(qp.OVERVIEW_TEXT)["x"] > qp.box(qp.CARD)["x"]
        st = qp.style(qp.OVERVIEW_TEXT, ["textAlign", "direction"])
        assert st["direction"] == "rtl" and st["textAlign"] in ("right", "start"), st
    with allure.step("Eyebrow and heading"):
        assert qp.text_of(qp.OVERVIEW_EYEBROW) == "عن الجمعية"
        issues = font_mismatches(qp.style(qp.OVERVIEW_EYEBROW, FONT_PROPS), size=14, weight=400, color="#911731")
        assert not issues, issues
        assert qp.text_of(qp.OVERVIEW_HEADING) == "نبذة عن جمعية قطر للشحن والخدمات اللوجستية"
        issues = font_mismatches(qp.style(qp.OVERVIEW_HEADING, FONT_PROPS), size=36, weight=700, color="#1D1D1B")
        assert not issues, issues
    with allure.step("Paragraph and 5 bullets: markers on the right, no clipping, no English fallback"):
        assert qp.text_of(qp.OVERVIEW_INTRO).startswith("جمعية قطر للشحن والخدمات اللوجستية هي لجنة")
        bullets = qp.texts(qp.OVERVIEW_BULLETS)
        assert len(bullets) == 5, bullets
        assert not any(has_latin(b) for b in bullets), "English fallback text in the Arabic bullets"
        assert qp.style(qp.OVERVIEW_BULLETS, ["direction"])["direction"] == "rtl"
        assert qp.page.locator(qp.OVERVIEW_BODY).evaluate("e => e.scrollWidth <= e.clientWidth + 1"), "overview body clipped"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the Required template card renders per Figma in English')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146502
@pytest.mark.traceability("146502")
@allure.label("pbi", "130718")
@allure.label("testcase", "146502")
@anon(viewport=(1920, 1080))
def test_146502_required_template_card_renders_per_figma_in_english(page, tmp_path):
    """Verify that the Required template card renders per Figma in English

    Steps (case is the oracle):
    1. Open the page in English light theme -> Card 424 px wide, 1 px #E9DBD0 border, radius 10, padding
       24, vertical gap 20; icon tile 64x64 #911731 radius 8 with white document icon
    2. Inspect the card frame and icon tile -> Eyebrow 'Required template' Cairo 12/400 #911731; title
       'QAFL Membership Authorization Letter' Cairo 20/700 #1D1D1B
    3. Inspect eyebrow, title, description and button -> Description Cairo 14/400 #4A4A49 (download,
       complete, sign, upload instructions); button 376x40 pill #911731 label 'Download Authorization
       Letter' Cairo 14/600 white with 14x17 icon
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "en")
    with allure.step("Card 424 px wide, 1 px #E9DBD0 border, radius 10, padding 24, gap 20; icon tile 64x64 #911731 radius 8"):
        issues = box_mismatches(qp.box(qp.CARD), 424)
        st = qp.style(qp.CARD, ["borderTopWidth", "borderTopColor", "borderTopLeftRadius", "paddingTop", "rowGap"])
        assert not issues, issues
        assert st["borderTopWidth"] == "1px" and st["borderTopColor"] == rgb("#E9DBD0"), st
        assert px_close(st["borderTopLeftRadius"], "10px", LAYOUT_TOL) and px_close(st["paddingTop"], "24px", LAYOUT_TOL), st
        assert px_close(st["rowGap"], "20px", LAYOUT_TOL), st
        issues = box_mismatches(qp.box(qp.CARD_ICON), 64, 64, tol=IMAGE_TOL)
        ist = qp.style(qp.CARD_ICON, ["backgroundColor", "borderTopLeftRadius", "color"])
        assert not issues, issues
        assert ist["backgroundColor"] == rgb("#911731") and ist["color"] == rgb("#FFFFFF"), ist
        assert px_close(ist["borderTopLeftRadius"], "8px", LAYOUT_TOL), ist
    with allure.step("Eyebrow 'Required template' Cairo 12/400 #911731; title Cairo 20/700 #1D1D1B"):
        assert qp.text_of(qp.CARD_EYEBROW) == "Required template"
        assert not font_mismatches(qp.style(qp.CARD_EYEBROW, FONT_PROPS), size=12, weight=400, color="#911731")
        assert qp.text_of(qp.CARD_TITLE) == "QAFL Membership Authorization Letter"
        assert not font_mismatches(qp.style(qp.CARD_TITLE, FONT_PROPS), size=20, weight=700, color="#1D1D1B")
    with allure.step("Description Cairo 14/400 #4A4A49; button 376x40 pill #911731 'Download Authorization Letter' 14/600 white, 14x17 icon"):
        desc = qp.text_of(qp.CARD_DESC).lower()
        assert all(w in desc for w in ("download", "complete", "sign", "upload")), desc
        assert not font_mismatches(qp.style(qp.CARD_DESC, FONT_PROPS), size=14, weight=400, color="#4A4A49")
        issues = box_mismatches(qp.box(qp.DOWNLOAD_BUTTON), 376, 40)
        assert not issues, ("button", issues)
        bst = qp.style(qp.DOWNLOAD_BUTTON, FONT_PROPS + ["backgroundColor", "borderTopLeftRadius"])
        assert qp.text_of(qp.DOWNLOAD_BUTTON) == "Download Authorization Letter"
        assert bst["backgroundColor"] == rgb("#911731"), bst
        assert float(bst["borderTopLeftRadius"].rstrip("px") or 0) >= 18, "button is not a pill"
        assert not font_mismatches(bst, size=14, weight=600, color="#FFFFFF"), font_mismatches(bst, size=14, weight=600, color="#FFFFFF")
        issues = box_mismatches(qp.box(qp.DOWNLOAD_ICON), 14, 17, tol=IMAGE_TOL)
        assert not issues, ("icon", issues)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the Required template card renders RTL in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146503
@pytest.mark.traceability("146503")
@allure.label("pbi", "130718")
@allure.label("testcase", "146503")
@anon(viewport=(1920, 1080))
def test_146503_required_template_card_renders_rtl_in_arabic(page, tmp_path):
    """Verify that the Required template card renders RTL in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic light theme -> Card mirrored, same border/radius/padding, icon tile on
       the right
    2. Inspect eyebrow and title -> Eyebrow 'النموذج المطلوب' and title 'خطاب تفويض عضوية QAFL' rendered
       right-aligned
    3. Inspect description and button -> Description starts 'قم بتحميل النموذج الحالي'; button label
       'تحميل خطاب التفويض' with icon on the mirrored side
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "ar")
    with allure.step("Card mirrored, icon tile on the right"):
        card, icon = qp.box(qp.CARD), qp.box(qp.CARD_ICON)
        assert icon["x"] + icon["width"] / 2 > card["x"] + card["width"] / 2, "icon tile is not on the right"
        st = qp.style(qp.CARD, ["borderTopWidth", "borderTopColor", "borderTopLeftRadius", "paddingTop"])
        assert st["borderTopColor"] == rgb("#E9DBD0") and px_close(st["paddingTop"], "24px", LAYOUT_TOL), st
    with allure.step("Eyebrow and title right-aligned"):
        assert qp.text_of(qp.CARD_EYEBROW) == "النموذج المطلوب"
        assert qp.text_of(qp.CARD_TITLE) == "خطاب تفويض عضوية QAFL"
        for sel in (qp.CARD_EYEBROW, qp.CARD_TITLE):
            s = qp.style(sel, ["direction", "textAlign"])
            assert s["direction"] == "rtl" and s["textAlign"] in ("right", "start"), (sel, s)
    with allure.step("Description and button label; icon on the mirrored side"):
        assert qp.text_of(qp.CARD_DESC).startswith("قم بتحميل النموذج الحالي")
        assert qp.text_of(qp.DOWNLOAD_BUTTON) == "تحميل خطاب التفويض"
        btn_label = qp.box(qp.DOWNLOAD_BUTTON + " > span")
        assert qp.box(qp.DOWNLOAD_ICON)["x"] > btn_label["x"], "download icon is not on the mirrored (right) side"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the 5-step progress indicator renders per Figma in English with step 01 active')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146504
@pytest.mark.traceability("146504")
@allure.label("pbi", "130718")
@allure.label("testcase", "146504")
@anon(viewport=(1920, 1080))
def test_146504_5_step_progress_indicator_renders_per_figma_in_english_with(page, tmp_path):
    """Verify that the 5-step progress indicator renders per Figma in English with step 01 active

    Steps (case is the oracle):
    1. Open the page in English light theme -> Five 36x36 circles labelled 01..05 left to right
    2. Inspect the five step circles and labels -> 01 filled #911731 with white numeral, label 'Company
       Identity' #911731; 02-05 filled #F6F6F6 numeral #911731, labels 'Senior Executive','Responsible
       Manager','Company Location','Supporting Documents' Cairo 14/400 #343432
    3. Inspect the connector line -> Connector line 2 px #DEDEDD behind the circles
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "en")
    with allure.step("Five 36x36 circles labelled 01..05 left to right"):
        assert [qp.text_of(qp.STEP_NUM_N.format(n=n)) for n in range(1, 6)] == ["01", "02", "03", "04", "05"]
        xs = [qp.box(qp.STEP_NUM_N.format(n=n))["x"] for n in range(1, 6)]
        assert xs == sorted(xs), f"circles not left-to-right: {xs}"
        for n in range(1, 6):
            assert not box_mismatches(qp.box(qp.STEP_NUM_N.format(n=n)), 36, 36), n
    with allure.step("01 active #911731/white, label #911731; 02-05 #F6F6F6 numeral #911731, labels Cairo 14/400 #343432"):
        s1 = qp.style(qp.STEP_NUM_N.format(n=1), ["backgroundColor", "color"])
        assert s1 == {"backgroundColor": rgb("#911731"), "color": rgb("#FFFFFF")}, s1
        assert qp.text_of(qp.STEP_LABEL_N.format(n=1)) == "Company Identity"
        assert qp.style(qp.STEP_LABEL_N.format(n=1), ["color"])["color"] == rgb("#911731")
        labels = [qp.text_of(qp.STEP_LABEL_N.format(n=n)) for n in range(2, 6)]
        assert labels == ["Senior Executive", "Responsible Manager", "Company Location", "Supporting Documents"], labels
        for n in range(2, 6):
            s = qp.style(qp.STEP_NUM_N.format(n=n), ["backgroundColor", "color"])
            assert s == {"backgroundColor": rgb("#F6F6F6"), "color": rgb("#911731")}, (n, s)
            issues = font_mismatches(qp.style(qp.STEP_LABEL_N.format(n=n), FONT_PROPS), size=14, weight=400, color="#343432")
            assert not issues, (n, issues)
    with allure.step("Connector line 2 px #DEDEDD behind the circles"):
        c = qp.connector_style(1)
        assert c["borderTopWidth"] == "2px" and c["borderTopColor"] == rgb("#DEDEDD"), c


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Page layout")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the progress indicator renders RTL in Arabic with 01 on the right')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146505
@pytest.mark.traceability("146505")
@allure.label("pbi", "130718")
@allure.label("testcase", "146505")
@anon(viewport=(1920, 1080))
def test_146505_progress_indicator_renders_rtl_in_arabic_with_01_on_the_righ(page, tmp_path):
    """Verify that the progress indicator renders RTL in Arabic with 01 on the right

    Steps (case is the oracle):
    1. Open the page in Arabic light theme -> Circles ordered 01 (rightmost, active #911731) to 05
       (leftmost)
    2. Inspect circle order and labels -> Labels 'هوية الشركة','المسؤول التنفيذي','المدير المسؤول','موقع
       الشركة','المستندات الداعمة' under circles 01..05 respectively; inactive circles #F6F6F6
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "ar")
    with allure.step("Circles ordered 01 (rightmost, active #911731) to 05 (leftmost)"):
        xs = [qp.box(qp.STEP_NUM_N.format(n=n))["x"] for n in range(1, 6)]
        assert xs == sorted(xs, reverse=True), f"circles not right-to-left: {xs}"
        assert qp.style(qp.STEP_NUM_N.format(n=1), ["backgroundColor"])["backgroundColor"] == rgb("#911731")
    with allure.step("Arabic labels under 01..05; inactive circles #F6F6F6"):
        labels = [qp.text_of(qp.STEP_LABEL_N.format(n=n)) for n in range(1, 6)]
        assert labels == ["هوية الشركة", "المسؤول التنفيذي", "المدير المسؤول", "موقع الشركة", "المستندات الداعمة"], labels
        for n in range(2, 6):
            assert qp.style(qp.STEP_NUM_N.format(n=n), ["backgroundColor"])["backgroundColor"] == rgb("#F6F6F6"), n


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Step 1 Company Identity renders per Figma in English')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146506
@pytest.mark.traceability("146506")
@allure.label("pbi", "130718")
@allure.label("testcase", "146506")
@anon(viewport=(1920, 1080))
def test_146506_step_1_company_identity_renders_per_figma_in_english(page, tmp_path):
    """Verify that Step 1 Company Identity renders per Figma in English

    Steps (case is the oracle):
    1. Open the page in English light theme at Step 1 -> Step 1 is displayed
    2. Inspect the step header -> Header tile 44x44 #F6F6F6 border #EDEDED radius 8; title 'Company
       Identity' Cairo 18/600 #1D1D1B; subtitle 'Enter the company's registered legal information.'
       Cairo 12/400 #7C7B7B
    3. Inspect field labels, placeholders and required asterisks -> Labels Cairo 14/600 #1D1D1B with red
       asterisk #E11D48; 'Company English Name' and 'Company Arabic Name' inputs 312x44 side by side
       with placeholders 'Registered company name in English' / 'Registered company name in Arabic'
       (#A8A8A7); 'Company Registered Under' and 'Company Type' dropdowns 648x44 with placeholders
       'Select registration authority' / 'Select company type' and 10x5 chevron
    4. Inspect Company Size, Market Presence and Next button -> Company Size cards 153x64 (Small 1-50
       employees, Medium 51-500 employees, Large 501+ employees, Other 'Enter count'); Market Presence
       cards 153x46 (Local, Regional, International, Other); Next button 648x48 pill #911731 label
       'Next' Cairo 16/600 white with 8x8 arrow
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "en")
    assert qp.wait_for_step(1)
    with allure.step("Step header tile 44x44 #F6F6F6 border #EDEDED radius 8; title and subtitle tokens"):
        icon = qp.STEP_HEAD_ICON_N.format(n=1)
        assert not box_mismatches(qp.box(icon), 44, 44, tol=IMAGE_TOL), box_mismatches(qp.box(icon), 44, 44, tol=IMAGE_TOL)
        st = qp.style(icon, ["backgroundColor", "borderTopColor", "borderTopLeftRadius"])
        assert st["backgroundColor"] == rgb("#F6F6F6") and st["borderTopColor"] == rgb("#EDEDED"), st
        assert px_close(st["borderTopLeftRadius"], "8px", LAYOUT_TOL), st
        assert qp.text_of(qp.STEP_HEAD_TITLE_N.format(n=1)) == "Company Identity"
        assert not font_mismatches(qp.style(qp.STEP_HEAD_TITLE_N.format(n=1), FONT_PROPS), size=18, weight=600, color="#1D1D1B")
        assert qp.text_of(qp.STEP_HEAD_SUB_N.format(n=1)) == "Enter the company's registered legal information."
        assert not font_mismatches(qp.style(qp.STEP_HEAD_SUB_N.format(n=1), FONT_PROPS), size=12, weight=400, color="#7C7B7B")
    with allure.step("Labels Cairo 14/600 #1D1D1B with red #E11D48 asterisk; inputs, placeholders, dropdowns"):
        for n in STEP1_MANDATORY:
            issues = font_mismatches(qp.style(qp.FIELD_LABEL.format(name=n), FONT_PROPS), size=14, weight=600, color="#1D1D1B")
            assert not issues, (n, issues)
            star = qp.pseudo_style(qp.FIELD_LABEL.format(name=n), "::after", ["content", "color"])
            assert "*" in star["content"] and star["color"] == rgb("#E11D48"), (n, star)
        en, ar = qp.box(qp.CONTROL.format(name="companyEnglishName")), qp.box(qp.CONTROL.format(name="companyArabicName"))
        assert not box_mismatches(en, 312, 44) and not box_mismatches(ar, 312, 44), (en, ar)
        assert abs(en["y"] - ar["y"]) <= LAYOUT_TOL and en["x"] < ar["x"], "name inputs not side by side, English first"
        assert qp.placeholder("companyEnglishName") == "Registered company name in English"
        assert qp.placeholder("companyArabicName") == "Registered company name in Arabic"
        ph = qp.pseudo_style(qp.CONTROL.format(name="companyEnglishName"), "::placeholder", ["color"])
        assert ph["color"] == rgb("#A8A8A7"), ph
        for n, text in (("companyRegisteredUnder", "Select registration authority"), ("companyType", "Select company type")):
            assert not box_mismatches(qp.box(qp.CONTROL.format(name=n)), 648, 44), n
            qp.wait_for_options_loaded(n)
            assert qp.selected_option_text(n) == text, n
    with allure.step("Company Size cards 153x64; Market Presence cards 153x46; Next 648x48 pill #911731"):
        mains = [normalise(t) for t in qp.texts(qp.RADIO_CARD_MAIN.format(name="companySize"))]
        subs = [normalise(t) for t in qp.texts(qp.RADIO_CARD_SUB.format(name="companySize"))]
        assert mains == ["Small", "Medium", "Large", "Other"], mains
        assert subs == ["1-50 employees", "51-500 employees", "501+ employees", "Enter count"], subs
        for i in range(4):
            assert not box_mismatches(qp.box(qp.RADIO_CARD_ANY.format(name="companySize"), i), 153, 64), ("size", i)
            assert not box_mismatches(qp.box(qp.RADIO_CARD_ANY.format(name="marketPresence"), i), 153, 46), ("mp", i)
        assert qp.texts(qp.RADIO_CARD_MAIN.format(name="marketPresence")) == ["Local", "Regional", "International", "Other"]
        assert not box_mismatches(qp.box(qp.NEXT_BUTTON), 648, 48), box_mismatches(qp.box(qp.NEXT_BUTTON), 648, 48)
        nst = qp.style(qp.NEXT_BUTTON, FONT_PROPS + ["backgroundColor", "borderTopLeftRadius"])
        assert nst["backgroundColor"] == rgb("#911731"), nst
        assert float(nst["borderTopLeftRadius"].rstrip("px") or 0) >= 20, "Next is not a pill"
        assert qp.text_of(qp.NEXT_BUTTON) == "Next"
        assert not font_mismatches(nst, size=16, weight=600, color="#FFFFFF"), font_mismatches(nst, size=16, weight=600, color="#FFFFFF")
        assert not box_mismatches(qp.box(qp.NEXT_ARROW), 8, 8, tol=IMAGE_TOL), box_mismatches(qp.box(qp.NEXT_ARROW), 8, 8, tol=IMAGE_TOL)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Step 1 Company Identity renders RTL per Figma in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.figmaverified
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146507
@pytest.mark.traceability("146507")
@allure.label("pbi", "130718")
@allure.label("testcase", "146507")
@anon(viewport=(1920, 1080))
def test_146507_step_1_company_identity_renders_rtl_per_figma_in_arabic(page, tmp_path):
    """Verify that Step 1 Company Identity renders RTL per Figma in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic light theme at Step 1 -> Step 1 displayed RTL; title 'هوية الشركة' Cairo
       18/600, subtitle 'أدخل المعلومات القانونية المسجلة للشركة.'
    2. Inspect header, labels and placeholders -> Labels 'اسم الشركة بالعربية', 'اسم الشركة
       بالإنجليزية', 'الشركة مسجلة لدى ', 'نوع الشركة', 'حجم الشركة', 'التواجد في السوق' with asterisks;
       placeholders 'اسم الشركة المسجل بالعربية', 'اسم الشركة المسجل بالإنجليزية', 'اختر جهة التسجيل',
       'اختر نوع الشركة'; Arabic Name field appears first (right) - EN frame has English first, confirm
       mirrored order intended (A-11)
    3. Inspect option cards and Next button -> Company Size cards show 'صغيرة 1-50 موظف','متوسطة 51-500
       موظف','كبيرة 501+ موظف','أخرى أدخل العدد'; MP cards 'محلي','إقليمي','دولي','أخرى'; Next button
       label 'التالي' with arrow mirrored
    """
    qp = QaflMembershipPage(page)
    open_page(qp, "ar")
    with allure.step("Step 1 RTL; title 'هوية الشركة' Cairo 18/600 and subtitle"):
        assert qp.document_direction() == "rtl"
        assert qp.text_of(qp.STEP_HEAD_TITLE_N.format(n=1)) == "هوية الشركة"
        assert not font_mismatches(qp.style(qp.STEP_HEAD_TITLE_N.format(n=1), FONT_PROPS), size=18, weight=600)
        assert qp.text_of(qp.STEP_HEAD_SUB_N.format(n=1)) == "أدخل المعلومات القانونية المسجلة للشركة."
    with allure.step("Labels with asterisks, placeholders, Arabic Name first (right)"):
        expected = {"companyArabicName": "اسم الشركة بالعربية", "companyEnglishName": "اسم الشركة بالإنجليزية",
                    "companyRegisteredUnder": "الشركة مسجلة لدى", "companyType": "نوع الشركة",
                    "companySize": "حجم الشركة", "marketPresence": "التواجد في السوق"}
        for n, label in expected.items():
            assert qp.label_text(n) == label, (n, qp.label_text(n))
            assert qp.has_required_marker(n), n
        assert qp.placeholder("companyArabicName") == "اسم الشركة المسجل بالعربية"
        assert qp.placeholder("companyEnglishName") == "اسم الشركة المسجل بالإنجليزية"
        for n, text in (("companyRegisteredUnder", "اختر جهة التسجيل"), ("companyType", "اختر نوع الشركة")):
            qp.wait_for_options_loaded(n)
            assert qp.selected_option_text(n) == text, n
        ar_box, en_box = qp.box(qp.CONTROL.format(name="companyArabicName")), qp.box(qp.CONTROL.format(name="companyEnglishName"))
        assert ar_box["x"] > en_box["x"], "Arabic Name field is not first (rightmost) in RTL"
    with allure.step("Option cards and Next 'التالي' with mirrored arrow"):
        cards = [normalise(" ".join(t.split())) for t in qp.page.locator(qp.RADIO_CARD_ANY.format(name="companySize")).all_inner_texts()]
        assert cards == ["صغيرة 1-50 موظف", "متوسطة 51-500 موظف", "كبيرة 501+ موظف", "أخرى أدخل العدد"], cards
        assert qp.texts(qp.RADIO_CARD_MAIN.format(name="marketPresence")) == ["محلي", "إقليمي", "دولي", "أخرى"]
        assert qp.text_of(qp.NEXT_BUTTON) == "التالي"
        assert qp.style(qp.NEXT_ARROW, ["transform"])["transform"] != "none", "Next arrow is not mirrored"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 2 Senior Executive renders its 7 fields with required markers in English')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146508
@pytest.mark.traceability("146508")
@allure.label("pbi", "130718")
@allure.label("testcase", "146508")
@anon()
def test_146508_step_2_senior_executive_renders_its_7_fields_with_required_m(page, tmp_path):
    """Verify that Step 2 Senior Executive renders its 7 fields with required markers in English

    Steps (case is the oracle):
    1. Complete Step 1 with baseline data (A-2) and click Next -> Step 2 shown, progress 02 active, 01
       completed
    2. Inspect Step 2 heading and field list -> Fields in order: CEO / Chairman / Manager Name,
       Designation, Email, Confirm Email Address, Phone, Extension Number, Mobile Number, all with
       required asterisk
    3. Inspect the Previous and Next buttons -> Previous and Next buttons present; styling consistent
       with Step 1 tokens
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146508, 2, locale='en')
    with allure.step("Step 2 shown; progress 02 active, earlier steps completed"):
        assert qp.active_badge() == 2
        for d in range(1, 2):
            assert qp.step_badge_state(d)["done"], d
    with allure.step("Field labels, order and required markers"):
        names = qp.visible_field_names(2)
        got = [normalise(qp.label_text(n)) for n in names]
        assert got == ['CEO / Chairman / Manager Name', 'Designation', 'Email', 'Confirm Email Address', 'Phone', 'Extension Number', 'Mobile Number'], got
        for n in ['seniorExecutiveName', 'seniorExecutiveDesignation', 'seniorExecutiveEmail', 'seniorExecutiveConfirmEmail', 'seniorExecutivePhone', 'seniorExecutiveExtension', 'seniorExecutiveMobile']:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for n in []:
            assert not qp.has_required_marker(n), f"{n} is marked required"

    with allure.step("Previous and Next present; styling consistent with Step 1 tokens"):
        assert qp.is_shown(qp.PREV_BUTTON) and qp.is_shown(qp.NEXT_BUTTON)
        assert qp.style(qp.NEXT_BUTTON, ["backgroundColor"])["backgroundColor"] == rgb("#911731")
        assert not font_mismatches(qp.style(qp.FIELD_LABEL.format(name="seniorExecutiveName"), FONT_PROPS), size=14, weight=600, color="#1D1D1B")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 2 Senior Executive renders RTL in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146509
@pytest.mark.traceability("146509")
@allure.label("pbi", "130718")
@allure.label("testcase", "146509")
@anon()
def test_146509_step_2_senior_executive_renders_rtl_in_arabic(page, tmp_path):
    """Verify that Step 2 Senior Executive renders RTL in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic and complete Step 1 with baseline data -> Step 2 shown RTL; progress 02
       active
    2. Inspect Step 2 labels and alignment -> All 7 labels Arabic with asterisks, right-aligned, no
       English fallback; Previous/Next arrows mirrored
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146509, 2, locale="ar")
    with allure.step("Step 2 RTL; progress 02 active"):
        assert qp.document_direction() == "rtl" and qp.active_badge() == 2
    with allure.step("All 7 labels Arabic with asterisks, right-aligned, no English fallback; arrows mirrored"):
        for n in ['seniorExecutiveName', 'seniorExecutiveDesignation', 'seniorExecutiveEmail', 'seniorExecutiveConfirmEmail', 'seniorExecutivePhone', 'seniorExecutiveExtension', 'seniorExecutiveMobile']:
            label = qp.label_text(n)
            assert label and not has_latin(label), (n, label)
            assert qp.has_required_marker(n), n
            s = qp.style(qp.FIELD_LABEL.format(name=n), ["direction", "textAlign"])
            assert s["direction"] == "rtl" and s["textAlign"] in ("right", "start"), (n, s)
        assert qp.style(qp.NEXT_ARROW, ["transform"])["transform"] != "none", "Next arrow not mirrored"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 3 Responsible Manager renders the same 7-field set in English')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146510
@pytest.mark.traceability("146510")
@allure.label("pbi", "130718")
@allure.label("testcase", "146510")
@anon()
def test_146510_step_3_responsible_manager_renders_the_same_7_field_set_in_e(page, tmp_path):
    """Verify that Step 3 Responsible Manager renders the same 7-field set in English

    Steps (case is the oracle):
    1. Complete Steps 1-2 with baseline data and click Next -> Step 3 shown, progress 03 active, 01-02
       completed
    2. Inspect Step 3 heading and fields -> Fields: Responsible Manager Name, Designation, Email,
       Confirm Email Address, Phone, Extension Number, Mobile Number, all required-marked; Previous and
       Next present
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146510, 3, locale='en')
    with allure.step("Step 3 shown; progress 03 active, earlier steps completed"):
        assert qp.active_badge() == 3
        for d in range(1, 3):
            assert qp.step_badge_state(d)["done"], d
    with allure.step("Field labels, order and required markers"):
        names = qp.visible_field_names(3)
        got = [normalise(qp.label_text(n)) for n in names]
        assert got == ['Responsible Manager Name', 'Designation', 'Email', 'Confirm Email Address', 'Phone', 'Extension Number', 'Mobile Number'], got
        for n in ['responsibleManagerName', 'responsibleManagerDesignation', 'responsibleManagerEmail', 'responsibleManagerConfirmEmail', 'responsibleManagerPhone', 'responsibleManagerExtension', 'responsibleManagerMobile']:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for n in []:
            assert not qp.has_required_marker(n), f"{n} is marked required"

    with allure.step("Previous and Next present"):
        assert qp.is_shown(qp.PREV_BUTTON) and qp.is_shown(qp.NEXT_BUTTON)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 3 Responsible Manager renders RTL in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146511
@pytest.mark.traceability("146511")
@allure.label("pbi", "130718")
@allure.label("testcase", "146511")
@anon()
def test_146511_step_3_responsible_manager_renders_rtl_in_arabic(page, tmp_path):
    """Verify that Step 3 Responsible Manager renders RTL in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic and complete Steps 1-2 -> Step 3 shown RTL, progress 03 active
    2. Inspect Step 3 -> 7 Arabic labels right-aligned with asterisks; no truncation
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146511, 3, locale="ar")
    with allure.step("Step 3 RTL, progress 03 active"):
        assert qp.document_direction() == "rtl" and qp.active_badge() == 3
    with allure.step("7 Arabic labels right-aligned with asterisks; no truncation"):
        for n in ['responsibleManagerName', 'responsibleManagerDesignation', 'responsibleManagerEmail', 'responsibleManagerConfirmEmail', 'responsibleManagerPhone', 'responsibleManagerExtension', 'responsibleManagerMobile']:
            label = qp.label_text(n)
            assert label and not has_latin(label), (n, label)
            assert qp.has_required_marker(n), n
            assert qp.style(qp.FIELD_LABEL.format(name=n), ["textAlign"])["textAlign"] in ("right", "start"), n
            assert qp.page.locator(qp.FIELD_LABEL.format(name=n)).evaluate("e => e.scrollWidth <= e.clientWidth + 1"), f"{n} label truncated"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 4 Company Location renders 5 fields with Website marked optional in English')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146512
@pytest.mark.traceability("146512")
@allure.label("pbi", "130718")
@allure.label("testcase", "146512")
@anon()
def test_146512_step_4_company_location_renders_5_fields_with_website_marked(page, tmp_path):
    """Verify that Step 4 Company Location renders 5 fields with Website marked optional in English

    Steps (case is the oracle):
    1. Complete Steps 1-3 with baseline data and click Next -> Step 4 shown, progress 04 active
    2. Inspect Step 4 fields -> Fields: Website (no asterisk), Location Name, Building Number, Zone
       Number, Street Number (asterisk on the last four); Previous and Next present
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146512, 4, locale='en')
    with allure.step("Step 4 shown; progress 04 active, earlier steps completed"):
        assert qp.active_badge() == 4
        for d in range(1, 4):
            assert qp.step_badge_state(d)["done"], d
    with allure.step("Field labels, order and required markers"):
        names = qp.visible_field_names(4)
        got = [normalise(qp.label_text(n)) for n in names]
        assert got == ['Website', 'Location Name', 'Building Number', 'Zone Number', 'Street Number'], got
        for n in ['locationName', 'buildingNumber', 'zoneNumber', 'streetNumber']:
            assert qp.has_required_marker(n), f"{n} has no required marker"
        for n in ['website']:
            assert not qp.has_required_marker(n), f"{n} is marked required"

    with allure.step("Previous and Next present"):
        assert qp.is_shown(qp.PREV_BUTTON) and qp.is_shown(qp.NEXT_BUTTON)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 4 Company Location renders RTL in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146513
@pytest.mark.traceability("146513")
@allure.label("pbi", "130718")
@allure.label("testcase", "146513")
@anon()
def test_146513_step_4_company_location_renders_rtl_in_arabic(page, tmp_path):
    """Verify that Step 4 Company Location renders RTL in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic and complete Steps 1-3 -> Step 4 RTL, progress 04 active
    2. Inspect Step 4 -> Five Arabic labels right-aligned; Website has no asterisk; the URL input
       content stays LTR-readable
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146513, 4, locale="ar")
    with allure.step("Step 4 RTL, progress 04 active"):
        assert qp.document_direction() == "rtl" and qp.active_badge() == 4
    with allure.step("Five Arabic labels right-aligned; Website has no asterisk; URL stays LTR-readable"):
        names = qp.visible_field_names(4)
        assert len(names) == 5, names
        for n in names:
            label = qp.label_text(n)
            assert label and not has_latin(label), (n, label)
            assert qp.style(qp.FIELD_LABEL.format(name=n), ["textAlign"])["textAlign"] in ("right", "start"), n
        assert not qp.has_required_marker("website")
        qp.type_into("website", "https://www.gulffreight.qa")
        assert qp.field_value("website") == "https://www.gulffreight.qa"
        assert ltr_readable(qp, "website"), "URL input renders RTL"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 5 Supporting Documents renders 3 uploads, CAPTCHA and Submit in English')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146514
@pytest.mark.traceability("146514")
@allure.label("pbi", "130718")
@allure.label("testcase", "146514")
@anon()
def test_146514_step_5_supporting_documents_renders_3_uploads_captcha_and_su(page, tmp_path):
    """Verify that Step 5 Supporting Documents renders 3 uploads, CAPTCHA and Submit in English

    Steps (case is the oracle):
    1. Complete Steps 1-4 with baseline data and click Next -> Step 5 shown, progress 05 active
    2. Inspect the upload controls -> Three required uploads: QAFL Membership Authorization Letter,
       Authorized Person Qatar ID - Front, Authorized Person Qatar ID - Back, each showing allowed
       formats/size hint
    3. Inspect CAPTCHA and Submit button -> CAPTCHA widget above Submit; button labelled 'Submit';
       Previous present
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146514, 5)
    with allure.step("Step 5 shown, progress 05 active"):
        assert qp.active_badge() == 5
    with allure.step("Three required uploads, each with allowed formats/size hint"):
        names = qp.visible_field_names(5)
        labels = [normalise(qp.label_text(n)) for n in names]
        assert labels == ["QAFL Membership Authorization Letter", "Authorized Person Qatar ID - Front",
                          "Authorized Person Qatar ID - Back"], labels
        for n in names:
            assert qp.has_required_marker(n), n
            assert qp.dropzone_hint(n), f"{n} has no format/size hint"
    with allure.step("CAPTCHA above Submit; Submit labelled 'Submit'; Previous present"):
        assert qp.count(qp.CAPTCHA_WIDGET) == 1, "CAPTCHA mount missing"
        cap = qp.box(qp.CAPTCHA)
        if cap:  # score-mode reCAPTCHA renders no visible widget (see module docstring)
            assert cap["y"] < qp.box(qp.SUBMIT_BUTTON)["y"], "CAPTCHA is not above Submit"
        assert qp.text_of(qp.SUBMIT_BUTTON) == "Submit"
        assert qp.is_shown(qp.PREV_BUTTON)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that Step 5 Supporting Documents renders RTL in Arabic')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146515
@pytest.mark.traceability("146515")
@allure.label("pbi", "130718")
@allure.label("testcase", "146515")
@anon()
def test_146515_step_5_supporting_documents_renders_rtl_in_arabic(page, tmp_path):
    """Verify that Step 5 Supporting Documents renders RTL in Arabic

    Steps (case is the oracle):
    1. Open the page in Arabic and complete Steps 1-4 -> Step 5 RTL, progress 05 active
    2. Inspect Step 5 -> Arabic upload labels and format hints right-aligned; CAPTCHA and Arabic Submit
       button present, no overlap
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146515, 5, locale="ar")
    with allure.step("Step 5 RTL, progress 05 active"):
        assert qp.document_direction() == "rtl" and qp.active_badge() == 5
    with allure.step("Arabic labels and hints right-aligned; CAPTCHA and Arabic Submit; no overlap"):
        names = qp.visible_field_names(5)
        boxes = []
        for n in names:
            assert qp.label_text(n) and qp.dropzone_hint(n), n
            assert qp.style(qp.FIELD_LABEL.format(name=n), ["textAlign"])["textAlign"] in ("right", "start"), n
            assert qp.style(qp.DROPZONE_HINT.format(name=n), ["direction"])["direction"] == "rtl", n
            boxes.append(qp.box(qp.FIELD.format(name=n)))
        for i, a in enumerate(boxes):
            for b in boxes[i + 1:]:
                overlap = not (a["x"] + a["width"] <= b["x"] or b["x"] + b["width"] <= a["x"]
                               or a["y"] + a["height"] <= b["y"] or b["y"] + b["height"] <= a["y"])
                assert not overlap, "upload fields overlap"
        assert qp.count(qp.CAPTCHA_WIDGET) == 1
        assert qp.text_of(qp.SUBMIT_BUTTON) == "إرسال"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that the English on-screen acknowledgement is shown verbatim after a valid submission')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146516
@pytest.mark.traceability("146516")
@allure.label("pbi", "130718")
@allure.label("testcase", "146516")
@anon()
def test_146516_english_on_screen_acknowledgement_is_shown_verbatim_after_a(page, tmp_path):
    """Verify that the English on-screen acknowledgement is shown verbatim after a valid submission

    Steps (case is the oracle):
    1. Complete all 5 steps with baseline data in English and pass CAPTCHA -> Submission accepted
    2. Click Submit -> Success screen displayed replacing the form
    3. Read the success message -> Message reads exactly 'Your QAFL Membership Registration has been
       submitted successfully. Your application is currently under review. You will be contacted once
       the review is completed.'
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    fill_all_and_submit(qp, files, 146516, locale="en")
    with allure.step("Success screen replaces the form"):
        assert qp.has_submission_succeeded(), f"not accepted; toast={qp.toast_text(2000)!r} captcha={qp.captcha_error_text()!r}"
        assert not qp.is_shown(qp.FORM)
    with allure.step("Message verbatim"):
        assert qp.ack_text() == EN_ACK, qp.ack_text()


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Form steps rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that the Arabic on-screen acknowledgement is shown verbatim after a valid submission')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146517
@pytest.mark.traceability("146517")
@allure.label("pbi", "130718")
@allure.label("testcase", "146517")
@anon()
def test_146517_arabic_on_screen_acknowledgement_is_shown_verbatim_after_a_v(page, tmp_path):
    """Verify that the Arabic on-screen acknowledgement is shown verbatim after a valid submission

    Steps (case is the oracle):
    1. Open the page in Arabic, complete all 5 steps with baseline data and pass CAPTCHA -> Submission
       accepted
    2. Click 'إرسال' (Submit) -> Success screen displayed RTL
    3. Read the success message -> Message reads exactly 'تم إرسال طلب عضوية QAFL بنجاح. طلبكم الآن قيد
       المراجعة. سيتم التواصل معكم بعد الانتهاء من مراجعة الطلب.'
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    fill_all_and_submit(qp, files, 146517, locale="ar")
    with allure.step("Success screen displayed RTL"):
        assert qp.has_submission_succeeded(), f"not accepted; toast={qp.toast_text(2000)!r} captcha={qp.captcha_error_text()!r}"
        assert qp.document_direction() == "rtl"
    with allure.step("Message verbatim"):
        assert qp.ack_text() == AR_ACK, qp.ack_text()


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that an input shows the focus state when focused by click and by Tab')
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146518
@pytest.mark.traceability("146518")
@allure.label("pbi", "130718")
@allure.label("testcase", "146518")
@anon()
def test_146518_an_input_shows_the_focus_state_when_focused_by_click_and_by(page, tmp_path):
    """Verify that an input shows the focus state when focused by click and by Tab

    Steps (case is the oracle):
    1. Open Step 1 -> Input default: 312x44, border #EDEDED 1 px, radius 8, placeholder #A8A8A7
    2. Click the Company English Name input -> Focused input shows a visible focus indicator distinct
       from the default border; caret visible
    3. Tab to Company Arabic Name then Shift+Tab back -> Focus indicator is shown on keyboard focus and
       is not clipped
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    name = "companyEnglishName"
    with allure.step("Default input: 312x44, border #EDEDED 1 px, radius 8, placeholder #A8A8A7"):
        assert not box_mismatches(qp.box(qp.CONTROL.format(name=name)), 312, 44)
        st = qp.style(qp.CONTROL.format(name=name), ["borderTopColor", "borderTopWidth", "borderTopLeftRadius"])
        assert st["borderTopColor"] == rgb("#EDEDED") and st["borderTopWidth"] == "1px", st
        assert px_close(st["borderTopLeftRadius"], "8px", LAYOUT_TOL), st
        assert qp.pseudo_style(qp.CONTROL.format(name=name), "::placeholder", ["color"])["color"] == rgb("#A8A8A7")
        default = qp.control_focus_style(name)
    with allure.step("Click: visible focus indicator distinct from the default border"):
        qp.click_control(name)
        assert qp.focused_control_name() == name
        assert qp.control_focus_style(name) != default, "no visible focus change on click"
    with allure.step("Tab to Arabic Name then Shift+Tab back: indicator shown on keyboard focus"):
        qp.press_key("Tab")
        assert qp.focused_control_name() == "companyArabicName"
        qp.press_key("Shift+Tab")
        assert qp.focused_control_name() == name
        assert qp.control_focus_style(name) != default, "no visible focus change on keyboard focus"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that an invalid input shows the inline error state under the field')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146519
@pytest.mark.traceability("146519")
@allure.label("pbi", "130718")
@allure.label("testcase", "146519")
@anon()
def test_146519_an_invalid_input_shows_the_inline_error_state_under_the_fiel(page, tmp_path):
    """Verify that an invalid input shows the inline error state under the field

    Steps (case is the oracle):
    1. Open Step 1 and focus Company English Name then leave it empty and Tab out -> Field flagged
       invalid on blur
    2. Inspect the field and the message area -> Inline error text appears directly under the field in
       the error colour, with the border changed from #EDEDED; other fields unaffected
    3. Type 'Gulf Freight Logistics WLL' into the field -> Error clears in real time once a valid value
       is typed
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    name = "companyEnglishName"
    with allure.step("Focus Company English Name, leave it empty, Tab out: flagged invalid on blur"):
        qp.blur(name)
        assert qp.has_field_error(name), "no inline error on blur"
    with allure.step("Inline error directly under the field; border changed from #EDEDED; other fields unaffected"):
        assert qp.field_error_below_control(name), "error is not under the field"
        assert qp.style(qp.CONTROL.format(name=name), ["borderTopColor"])["borderTopColor"] != rgb("#EDEDED")
        allure.attach(str(qp.field_error_style(name)), "error colour (case assumes #E11D48, derived)", allure.attachment_type.TEXT)
        assert qp.has_no_field_error("companyArabicName"), "another field was flagged"
    with allure.step("Type a valid value: the error clears in real time"):
        qp.type_into(name, "Gulf Freight Logistics WLL")
        assert qp.has_no_field_error(name), "error did not clear"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that LTR values (email, phone, URL) stay readable inside Arabic RTL fields')
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.comm
@pytest.mark.ui
@pytest.mark.pbi_130718
@pytest.mark.tc_146520
@pytest.mark.traceability("146520")
@allure.label("pbi", "130718")
@allure.label("testcase", "146520")
@anon()
def test_146520_ltr_values_email_phone_url_stay_readable_inside_arabic_rtl_f(page, tmp_path):
    """Verify that LTR values (email, phone, URL) stay readable inside Arabic RTL fields

    Steps (case is the oracle):
    1. Open the page in Arabic and reach Step 2 -> Step 2 shown
    2. Type the email and the phone value -> Email and phone display left-to-right without reordering of
       '+' or digits, field itself right-aligned
    3. Reach Step 4 and type the website URL -> URL displays left-to-right unmangled
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146520, 2, locale="ar")
    with allure.step("Type the email and the phone value: displayed LTR, field right-aligned"):
        qp.type_into("seniorExecutiveEmail", "khalid.almarri@gulffreight.qa")
        qp.type_into("seniorExecutivePhone", "+974 4412 3456")
        assert qp.field_value("seniorExecutiveEmail") == "khalid.almarri@gulffreight.qa"
        assert qp.field_value("seniorExecutivePhone") == "+974 4412 3456"
        for n in ("seniorExecutiveEmail", "seniorExecutivePhone"):
            assert ltr_readable(qp, n), f"{n} renders the LTR value RTL"
    with allure.step("Reach Step 4 and type the website URL: LTR, unmangled"):
        qp.fill(build(2, files, 146520))
        qp.click_next()
        assert qp.wait_for_step(3)
        qp.fill(build(3, files, 146520))
        qp.click_next()
        assert qp.wait_for_step(4)
        qp.type_into("website", "https://www.gulffreight.qa")
        assert qp.field_value("website") == "https://www.gulffreight.qa"
        assert ltr_readable(qp, "website"), "URL renders RTL"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the registration page and Step 1 to Step 2 flow work in Chrome (latest)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146521
@pytest.mark.traceability("146521")
@allure.label("pbi", "130718")
@allure.label("testcase", "146521")
@anon(engine="chromium")
def test_146521_registration_page_and_step_1_to_step_2_flow_work_in_chrome_l(page, tmp_path):
    """Verify that the registration page and Step 1 to Step 2 flow work in Chrome (latest)

    Steps (case is the oracle):
    1. Open the page in Chrome latest -> Page renders hero, overview, card and Step 1 without layout
       defects
    2. Complete Step 1 with baseline data -> Inputs, dropdowns, radio cards and file inputs work
    3. Click Next -> Step 2 opens with progress 02 active
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Page renders hero, overview, card and Step 1 without layout defects"):
        for sel in (qp.HERO_TITLE, qp.OVERVIEW_HEADING, qp.CARD, qp.STEP_FIELDSET_N.format(n=1)):
            assert qp.is_shown(sel), sel
        assert not qp.has_horizontal_overflow(), "horizontal overflow"
    with allure.step("Complete Step 1 (inputs, dropdowns, radio cards, file input)"):
        qp.fill(build(1, files, 146521))
    with allure.step("Click Next: Step 2 opens with progress 02 active"):
        qp.click_next()
        assert qp.wait_for_step(2) and qp.active_badge() == 2


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the registration page and Step 1 to Step 2 flow work in Firefox (latest)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146522
@pytest.mark.traceability("146522")
@allure.label("pbi", "130718")
@allure.label("testcase", "146522")
@anon(engine="firefox")
def test_146522_registration_page_and_step_1_to_step_2_flow_work_in_firefox(page, tmp_path):
    """Verify that the registration page and Step 1 to Step 2 flow work in Firefox (latest)

    Steps (case is the oracle):
    1. Open the page in Firefox latest -> Page renders without layout defects
    2. Complete Step 1 with baseline data -> Form controls incl. file input work
    3. Click Next -> Step 2 opens with progress 02 active
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Page renders hero, overview, card and Step 1 without layout defects"):
        for sel in (qp.HERO_TITLE, qp.OVERVIEW_HEADING, qp.CARD, qp.STEP_FIELDSET_N.format(n=1)):
            assert qp.is_shown(sel), sel
        assert not qp.has_horizontal_overflow(), "horizontal overflow"
    with allure.step("Complete Step 1 (inputs, dropdowns, radio cards, file input)"):
        qp.fill(build(1, files, 146522))
    with allure.step("Click Next: Step 2 opens with progress 02 active"):
        qp.click_next()
        assert qp.wait_for_step(2) and qp.active_badge() == 2


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the registration page and Step 1 to Step 2 flow work in Safari (latest)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146523
@pytest.mark.traceability("146523")
@allure.label("pbi", "130718")
@allure.label("testcase", "146523")
@anon(engine="webkit")
def test_146523_registration_page_and_step_1_to_step_2_flow_work_in_safari_l(page, tmp_path):
    """Verify that the registration page and Step 1 to Step 2 flow work in Safari (latest)

    Steps (case is the oracle):
    1. Open the page in Safari latest -> Page renders without layout defects
    2. Complete Step 1 with baseline data -> Form controls and file input work
    3. Click Next -> Step 2 opens with progress 02 active
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Page renders hero, overview, card and Step 1 without layout defects"):
        for sel in (qp.HERO_TITLE, qp.OVERVIEW_HEADING, qp.CARD, qp.STEP_FIELDSET_N.format(n=1)):
            assert qp.is_shown(sel), sel
        assert not qp.has_horizontal_overflow(), "horizontal overflow"
    with allure.step("Complete Step 1 (inputs, dropdowns, radio cards, file input)"):
        qp.fill(build(1, files, 146523))
    with allure.step("Click Next: Step 2 opens with progress 02 active"):
        qp.click_next()
        assert qp.wait_for_step(2) and qp.active_badge() == 2


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the registration page and Step 1 to Step 2 flow work in Edge (latest)')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146524
@pytest.mark.traceability("146524")
@allure.label("pbi", "130718")
@allure.label("testcase", "146524")
@anon(engine="msedge")
def test_146524_registration_page_and_step_1_to_step_2_flow_work_in_edge_lat(page, tmp_path):
    """Verify that the registration page and Step 1 to Step 2 flow work in Edge (latest)

    Steps (case is the oracle):
    1. Open the page in Edge latest -> Page renders without layout defects
    2. Complete Step 1 with baseline data -> Form controls and file input work
    3. Click Next -> Step 2 opens with progress 02 active
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Page renders hero, overview, card and Step 1 without layout defects"):
        for sel in (qp.HERO_TITLE, qp.OVERVIEW_HEADING, qp.CARD, qp.STEP_FIELDSET_N.format(n=1)):
            assert qp.is_shown(sel), sel
        assert not qp.has_horizontal_overflow(), "horizontal overflow"
    with allure.step("Complete Step 1 (inputs, dropdowns, radio cards, file input)"):
        qp.fill(build(1, files, 146524))
    with allure.step("Click Next: Step 2 opens with progress 02 active"):
        qp.click_next()
        assert qp.wait_for_step(2) and qp.active_badge() == 2


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the page lays out per Figma at the 1920 px desktop viewport')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.figmaverified
@pytest.mark.pbi_130718
@pytest.mark.tc_146525
@pytest.mark.traceability("146525")
@allure.label("pbi", "130718")
@allure.label("testcase", "146525")
@anon(viewport=(1920, 1080))
def test_146525_page_lays_out_per_figma_at_the_1920_px_desktop_viewport(page, tmp_path):
    """Verify that the page lays out per Figma at the 1920 px desktop viewport

    Steps (case is the oracle):
    1. Open the page at 1920x1080 -> Content container 1320 px wide with 300 px side padding
    2. Inspect the content container and column split -> Overview + card row on top, form column 872 px
       wide below with 648 px wide controls, no horizontal scrollbar
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Content container 1320 px wide with 300 px side padding"):
        body = qp.box(qp.OVERVIEW)
        assert not box_mismatches(body, 1320), box_mismatches(body, 1320)
        assert abs(body["x"] - 300) <= LAYOUT_TOL, f"left offset {body['x']}"
    with allure.step("Overview + card row on top; form column 872 px with 648 px controls; no horizontal scroll"):
        assert qp.box(qp.OVERVIEW)["y"] < qp.box(qp.FORM)["y"]
        assert not box_mismatches(qp.box(qp.FORM), 872), box_mismatches(qp.box(qp.FORM), 872)
        assert not box_mismatches(qp.box(qp.CONTROL.format(name="companyRegisteredUnder")), 648)
        assert not qp.has_horizontal_overflow()


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the page reflows without overflow at the 768 px tablet viewport')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146526
@pytest.mark.traceability("146526")
@allure.label("pbi", "130718")
@allure.label("testcase", "146526")
@anon(viewport=(768, 1024))
def test_146526_page_reflows_without_overflow_at_the_768_px_tablet_viewport(page, tmp_path):
    """Verify that the page reflows without overflow at the 768 px tablet viewport

    Steps (case is the oracle):
    1. Resize the browser to 768x1024 -> Layout reflows to fewer columns, no horizontal scroll or
       clipped text
    2. Scroll from hero to Next button -> Card, progress indicator and inputs fit the width; touch
       targets at least 44 px high
    3. Tap Next after completing Step 1 -> Step 2 opens normally
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Layout reflows, no horizontal scroll"):
        assert not qp.has_horizontal_overflow()
    with allure.step("Card, progress indicator and inputs fit the width; touch targets >= 44 px"):
        vw = qp.viewport_width()
        for sel in (qp.CARD, qp.STEPS, qp.CONTROL.format(name="companyEnglishName"), qp.NEXT_BUTTON):
            b = qp.box(sel)
            assert b and b["x"] >= 0 and b["x"] + b["width"] <= vw + 1, (sel, b)
        for sel in (qp.CONTROL.format(name="companyEnglishName"), qp.CONTROL.format(name="companyType"), qp.NEXT_BUTTON):
            assert qp.box(sel)["height"] >= 44, sel
    with allure.step("Complete Step 1 and tap Next: Step 2 opens"):
        qp.fill(build(1, files, 146526))
        qp.click_next()
        assert qp.wait_for_step(2)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the page lays out per Figma at the 390 px mobile viewport')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.figmaverified
@pytest.mark.pbi_130718
@pytest.mark.tc_146527
@pytest.mark.traceability("146527")
@allure.label("pbi", "130718")
@allure.label("testcase", "146527")
@anon(viewport=(390, 844))
def test_146527_page_lays_out_per_figma_at_the_390_px_mobile_viewport(page, tmp_path):
    """Verify that the page lays out per Figma at the 390 px mobile viewport

    Steps (case is the oracle):
    1. Open the page at 390x844 -> Hero title Cairo 24/700 line-height 32 white, page side padding 20
       px, no horizontal scroll
    2. Inspect hero and overview -> Card 350 px wide with 302 px button; overview heading Cairo 24/700
       line-height 32
    3. Inspect card, inputs, option cards and Next button -> Inputs 310x44, option cards stacked 310x46,
       Next button 310x48 full width
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Hero title Cairo 24/700 lh 32 white; side padding 20 px; no horizontal scroll"):
        assert not font_mismatches(qp.style(qp.HERO_TITLE, FONT_PROPS), size=24, weight=700, line_height=32, color="#FFFFFF")
        assert abs(qp.box(qp.HERO_TITLE)["x"] - 20) <= LAYOUT_TOL, qp.box(qp.HERO_TITLE)
        assert not qp.has_horizontal_overflow()
    with allure.step("Card 350 px with 302 px button; overview heading Cairo 24/700 lh 32"):
        assert not box_mismatches(qp.box(qp.CARD), 350), box_mismatches(qp.box(qp.CARD), 350)
        assert not box_mismatches(qp.box(qp.DOWNLOAD_BUTTON), 302), box_mismatches(qp.box(qp.DOWNLOAD_BUTTON), 302)
        assert not font_mismatches(qp.style(qp.OVERVIEW_HEADING, FONT_PROPS), size=24, weight=700, line_height=32)
    with allure.step("Inputs 310x44, option cards stacked 310x46, Next 310x48"):
        assert not box_mismatches(qp.box(qp.CONTROL.format(name="companyEnglishName")), 310, 44)
        cards = [qp.box(qp.RADIO_CARD_ANY.format(name="marketPresence"), i) for i in range(4)]
        for c in cards:
            assert not box_mismatches(c, 310, 46), c
        assert [c["y"] for c in cards] == sorted(c["y"] for c in cards) and len({round(c["x"]) for c in cards}) == 1
        assert not box_mismatches(qp.box(qp.NEXT_BUTTON), 310, 48), box_mismatches(qp.box(qp.NEXT_BUTTON), 310, 48)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the page renders with light theme tokens per Figma')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.figmaverified
@pytest.mark.pbi_130718
@pytest.mark.tc_146528
@pytest.mark.traceability("146528")
@allure.label("pbi", "130718")
@allure.label("testcase", "146528")
@anon()
def test_146528_page_renders_with_light_theme_tokens_per_figma(page, tmp_path):
    """Verify that the page renders with light theme tokens per Figma

    Steps (case is the oracle):
    1. Set the theme toggle to Light -> Theme is Light
    2. Load the page -> Page background #FFFFFF, primary text #1D1D1B, brand accent #911731
    3. Inspect page background and primary button -> Primary buttons filled #911731 with white label;
       contrast of body text on background readable
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    a11y = AccessibilityToolsComponent(page)
    with allure.step("Theme is Light"):
        assert qp.page.evaluate("() => document.documentElement.getAttribute('data-theme')") != "dark"
    with allure.step("Background #FFFFFF, primary text #1D1D1B, accent #911731"):
        assert a11y.page_background_color() == rgb("#FFFFFF")
        assert qp.style(qp.OVERVIEW_HEADING, ["color"])["color"] == rgb("#1D1D1B")
        assert qp.style(qp.OVERVIEW_EYEBROW, ["color"])["color"] == rgb("#911731")
    with allure.step("Primary button #911731 with white label"):
        st = qp.style(qp.NEXT_BUTTON, ["backgroundColor", "color"])
        assert st == {"backgroundColor": rgb("#911731"), "color": rgb("#FFFFFF")}, st


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the page renders with dark theme tokens per Figma')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.figmaverified
@pytest.mark.pbi_130718
@pytest.mark.tc_146529
@pytest.mark.traceability("146529")
@allure.label("pbi", "130718")
@allure.label("testcase", "146529")
@anon()
def test_146529_page_renders_with_dark_theme_tokens_per_figma(page, tmp_path):
    """Verify that the page renders with dark theme tokens per Figma

    Steps (case is the oracle):
    1. Set the theme toggle to Dark -> Theme is Dark
    2. Load the page -> Page and header background #1D1D1B; header text white; icon buttons #4A4A49 with
       #DEDEDD icons
    3. Inspect header, background and accent -> Accent buttons/logo accent #C44561 instead of #911731;
       no light-theme artefacts remain (form-body dark tokens not extracted - derived, A-1)
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    a11y = AccessibilityToolsComponent(page)
    header = HeaderComponent(page)
    with allure.step("Set the theme toggle to Dark"):
        a11y.enable_dark_mode()
    with allure.step("Page and header background #1D1D1B; header text white; icon buttons #4A4A49 with #DEDEDD icons"):
        assert a11y.page_background_color() == rgb("#1D1D1B")
        hs = header.container_style()
        assert hs["backgroundColor"] == rgb("#1D1D1B"), hs
        nav = qp.style(header.NAV_TOP_LEVEL_ITEMS, ["color"])
        assert nav["color"] == rgb("#FFFFFF"), nav
        btn = qp.style(header.ACCESSIBILITY_BUTTON, ["backgroundColor", "color"])
        assert btn == {"backgroundColor": rgb("#4A4A49"), "color": rgb("#DEDEDD")}, btn
    with allure.step("Accent buttons #C44561; no light-theme artefacts"):
        assert qp.style(qp.NEXT_BUTTON, ["backgroundColor"])["backgroundColor"] == rgb("#C44561")
        assert qp.style(qp.OVERVIEW_HEADING, ["color"])["color"] != rgb("#1D1D1B"), "heading kept the light-theme ink"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the page renders with the Normal contrast baseline')
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146530
@pytest.mark.traceability("146530")
@allure.label("pbi", "130718")
@allure.label("testcase", "146530")
@anon()
def test_146530_page_renders_with_the_normal_contrast_baseline(page, tmp_path):
    """Verify that the page renders with the Normal contrast baseline

    Steps (case is the oracle):
    1. Set the contrast toggle to Normal -> Contrast mode Normal active
    2. Load the page and view the form -> Standard colour tokens used on hero, form and buttons
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    a11y = AccessibilityToolsComponent(page)
    with allure.step("Contrast mode Normal active"):
        assert not a11y.is_high_contrast_active()
    with allure.step("Standard colour tokens on hero, form and buttons"):
        assert qp.style(qp.HERO_TITLE, ["color"])["color"] == rgb("#FFFFFF")
        assert qp.style(qp.OVERVIEW_HEADING, ["color"])["color"] == rgb("#1D1D1B")
        assert qp.style(qp.NEXT_BUTTON, ["backgroundColor"])["backgroundColor"] == rgb("#911731")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the form stays usable at 200% browser zoom')
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146532
@pytest.mark.traceability("146532")
@allure.label("pbi", "130718")
@allure.label("testcase", "146532")
@anon(viewport=(960, 540))
def test_146532_form_stays_usable_at_200_browser_zoom(page, tmp_path):
    """Verify that the form stays usable at 200% browser zoom

    Steps (case is the oracle):
    1. Set browser zoom to 200% -> No content is lost or overlapped; layout reflows
    2. Scroll the page and Step 1 -> All fields and buttons reachable without horizontal scrolling of
       the form
    3. Complete Step 1 and click Next -> Step 2 opens
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("200% zoom (960x540 CSS px): layout reflows, nothing overlapped"):
        assert not qp.has_horizontal_overflow(), "horizontal scroll at 200% zoom"
    with allure.step("All Step 1 fields and buttons reachable without horizontal scrolling"):
        vw = qp.viewport_width()
        for n in STEP1_MANDATORY:
            b = qp.box(qp.FIELD.format(name=n))
            assert b and b["x"] >= 0 and b["x"] + b["width"] <= vw + 1, (n, b)
        nb = qp.box(qp.NEXT_BUTTON)
        assert nb["x"] + nb["width"] <= vw + 1
    with allure.step("Complete Step 1 and click Next: Step 2 opens"):
        qp.fill(build(1, files, 146532))
        qp.click_next()
        assert qp.wait_for_step(2)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that the whole form can be completed using the keyboard only')
@pytest.mark.web
@pytest.mark.accessibility
@pytest.mark.comm
@pytest.mark.compatibility
@pytest.mark.pbi_130718
@pytest.mark.tc_146533
@pytest.mark.traceability("146533")
@allure.label("pbi", "130718")
@allure.label("testcase", "146533")
@anon()
def test_146533_whole_form_can_be_completed_using_the_keyboard_only(page, tmp_path):
    """Verify that the whole form can be completed using the keyboard only

    Steps (case is the oracle):
    1. Press Tab from the page top through the download button and Step 1 fields -> Tab order follows
       visual order (download button, then fields top to bottom); focus visible on each
    2. Select dropdown, radio and Next using Enter/Space/Arrow keys -> Dropdown options and radio cards
       selectable by keyboard
    3. Confirm focus after moving to Step 2 -> Next activates with Enter and focus lands on the first
       Step 2 field
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    values = build(1, files, 146533)
    with allure.step("Tab from the top through the download button and Step 1 fields: visual order"):
        assert qp.press_tab_until_focused(qp.DOWNLOAD_BUTTON, max_presses=80), "download button never takes focus"
        order = []
        for _ in range(3):
            qp.press_key("Tab")
            order.append(qp.focused_control_name())
        assert order == ["companyEnglishName", "companyArabicName", "companyRegisteredUnder"], order
    with allure.step("Type names, pick dropdowns, radio cards by keyboard"):
        qp.focus("companyEnglishName")
        qp.page.keyboard.type(values["companyEnglishName"])
        qp.press_key("Tab")
        qp.page.keyboard.type(values["companyArabicName"])
        qp.wait_for_options_loaded("companyRegisteredUnder")
        qp.focus("companyRegisteredUnder")
        for _ in range(6):
            if qp.field_value("companyRegisteredUnder") == "qfc":
                break
            qp.press_key("ArrowDown")
        assert qp.field_value("companyRegisteredUnder") == "qfc", "dropdown not selectable by keyboard"
        qp.focus("qfcNumber")
        qp.page.keyboard.type("QFC-00123")
        # A native file chooser cannot be driven by keyboard in automation: set the file directly (disclosed).
        qp.attach("qfcMembershipCopy", values["qfcMembershipCopy"])
        qp.page.locator(qp.RADIO.format(name="companySize", value="small")).focus()
        qp.press_key("Space")
        qp.press_key("ArrowRight")
        assert qp.field_value("companySize") == "medium", "radio cards not selectable by Arrow keys"
        qp.wait_for_options_loaded("companyType")
        qp.focus("companyType")
        for _ in range(8):
            if qp.selected_option_text("companyType") == "LLC":
                break
            qp.press_key("ArrowDown")
        assert qp.selected_option_text("companyType") == "LLC"
        qp.page.locator(qp.RADIO.format(name="marketPresence", value="local")).focus()
        qp.press_key("Space")
        assert qp.field_value("marketPresence") == "local"
    with allure.step("Next activates with Enter; focus lands on the first Step 2 field"):
        qp.page.locator(qp.NEXT_BUTTON).focus()
        qp.press_key("Enter")
        assert qp.wait_for_step(2)
        assert qp.focused_control_name() == "seniorExecutiveName", f"focus is on {qp.focused_control_name()!r}"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Compatibility & accessibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('Verify that a Public Visitor can view the page, download the template and submit the form without logging in')
@pytest.mark.web
@pytest.mark.auth
@pytest.mark.comm
@pytest.mark.pbi_130718
@pytest.mark.tc_146534
@pytest.mark.traceability("146534")
@allure.label("pbi", "130718")
@allure.label("testcase", "146534")
@anon()
def test_146534_a_public_visitor_can_view_the_page_download_the_template_and(page, tmp_path):
    """Verify that a Public Visitor can view the page, download the template and submit the form without logging in

    Steps (case is the oracle):
    1. Open the page in a fresh anonymous browser context -> Page loads with no login prompt
    2. Click 'Download Authorization Letter' -> Template file download starts
    3. Start the form and reach Step 1 Next -> Form is usable with no authentication requirement
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Page loads in a fresh anonymous context with no login prompt"):
        assert "login" not in qp.page.url.lower()
        assert qp.is_shown(qp.HERO_TITLE)
    with allure.step("Click 'Download Authorization Letter': download starts"):
        download = qp.download_template()
        assert download.suggested_filename, "no file downloaded"
    with allure.step("Form is usable with no authentication: Step 1 -> Next"):
        qp.fill(build(1, files, 146534))
        qp.click_next()
        assert qp.wait_for_step(2)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Step 1 - Company Identity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that the visitor reaches the registration page via Main Menu > Councils, Committees & Partnerships')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.pbi_130718
@pytest.mark.tc_146543
@pytest.mark.traceability("146543")
@allure.label("pbi", "130718")
@allure.label("testcase", "146543")
@anon()
def test_146543_visitor_reaches_the_registration_page_via_main_menu_councils(page, tmp_path):
    """Verify that the visitor reaches the registration page via Main Menu > Councils, Committees & Partnerships

    Steps (case is the oracle):
    1. Open the home page -> Home page loads
    2. Open Main Menu 'Councils, Committees & Partnerships' -> Submenu lists 'QAFL Membership
       Registration'
    3. Click 'QAFL Membership Registration' -> Registration page loads showing hero title, overview,
       card and 5-step form at Step 1
    """
    qp = QaflMembershipPage(page)
    with allure.step("Open the home page"):
        qp.open_home()
    with allure.step("Open Main Menu 'Councils, Committees & Partnerships': submenu lists 'QAFL Membership Registration'"):
        qp.open_menu_section("Councils, Committees & Partnerships")
        assert qp.is_menu_qafl_link_visible(), "submenu has no QAFL Membership Registration link"
        assert normalise(qp.menu_qafl_link_text()) == "QAFL Membership Registration"
    with allure.step("Click it: hero, overview, card and the 5-step form at Step 1"):
        qp.click_menu_qafl_link()
        assert qp.text_of(qp.HERO_TITLE) == "QAFL Membership Registration"
        for sel in (qp.OVERVIEW, qp.CARD, qp.STEPS):
            assert qp.is_shown(sel), sel
        assert qp.count(qp.STEP_ITEM) == 5 and qp.current_step() == 1


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Wizard navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Download Authorization Letter downloads the current admin-managed template')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.uat
@pytest.mark.pbi_130718
@pytest.mark.tc_146744
@pytest.mark.traceability("146744")
@allure.label("pbi", "130718")
@allure.label("testcase", "146744")
@anon()
def test_146744_download_authorization_letter_downloads_the_current_admin_ma(page, tmp_path):
    """Verify that Download Authorization Letter downloads the current admin-managed template

    Steps (case is the oracle):
    1. Open the page in an anonymous context -> Page loads
    2. Click 'Download Authorization Letter' -> Download starts without login
    3. Open the downloaded file -> File name and content match the template uploaded in the CMS
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Click 'Download Authorization Letter': download starts without login"):
        download = qp.download_template()
    with allure.step("File name matches the admin-managed template"):
        assert download.suggested_filename == "QAFL-Authorization-Letter-v1.docx", download.suggested_filename
    pytest.skip("Web half PASSED (anonymous download + file name). Byte-for-byte content vs the file the Editor "
                "uploaded in the CMS needs a Control_Panel read; not verified here.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Wizard navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Next advances to the following step when the current step is valid')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146745
@pytest.mark.traceability("146745")
@allure.label("pbi", "130718")
@allure.label("testcase", "146745")
@anon()
def test_146745_next_advances_to_the_following_step_when_the_current_step_is(page, tmp_path):
    """Verify that Next advances to the following step when the current step is valid

    Steps (case is the oracle):
    1. Complete Step 1 with baseline data -> Step 1 accepted
    2. Click Next -> Step 2 displayed
    3. Observe progress indicator and page -> Progress shows 01 completed and 02 active
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    with allure.step("Complete Step 1 with baseline data"):
        qp.fill(build(1, files, 146745))
    with allure.step("Click Next: Step 2 displayed"):
        qp.click_next()
        assert qp.wait_for_step(2)
    with allure.step("Progress shows 01 completed and 02 active"):
        assert qp.step_badge_state(1) == {"active": False, "done": True}, qp.step_badge_state(1)
        assert qp.step_badge_state(2) == {"active": True, "done": False}, qp.step_badge_state(2)


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Wizard navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Next is blocked and errors are shown when mandatory fields on the step are empty')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146746
@pytest.mark.traceability("146746")
@allure.label("pbi", "130718")
@allure.label("testcase", "146746")
@anon()
def test_146746_next_is_blocked_and_errors_are_shown_when_mandatory_fields_o(page, tmp_path):
    """Verify that Next is blocked and errors are shown when mandatory fields on the step are empty

    Steps (case is the oracle):
    1. Open Step 1 and click Next without entering anything -> Step 1 displayed
    2. Read the errors -> User stays on Step 1; inline required errors appear on Company English Name,
       Company Arabic Name, Company Registered Under, Company Size, Company Type and Market Presence;
       progress remains 01
    """
    qp = QaflMembershipPage(page)
    open_page(qp)
    with allure.step("Click Next without entering anything"):
        qp.wait_for_options_loaded("companyRegisteredUnder")
        qp.click_next()
    with allure.step("Stays on Step 1 with inline required errors on the six mandatory fields; progress 01"):
        assert qp.current_step() == 1
        for n in ("companyEnglishName", "companyArabicName", "companyRegisteredUnder", "companySize",
                  "companyType", "marketPresence"):
            assert qp.has_field_error(n), f"no inline required error on {n}"
        assert qp.active_badge() == 1


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Wizard navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that Previous returns to the prior step with entered values retained')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146747
@pytest.mark.traceability("146747")
@allure.label("pbi", "130718")
@allure.label("testcase", "146747")
@anon()
def test_146747_previous_returns_to_the_prior_step_with_entered_values_retai(page, tmp_path):
    """Verify that Previous returns to the prior step with entered values retained

    Steps (case is the oracle):
    1. Complete Step 1 and fill Step 2 with baseline data -> Step 2 filled
    2. Click Previous -> Step 1 shown with all values intact and progress 01 active
    3. Compare Step 1 and re-open Step 2 values -> No values lost
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    s1 = reach_step(qp, files, 146747, 2)[1]
    s2 = build(2, files, 146747)
    with allure.step("Fill Step 2 with baseline data"):
        qp.fill(s2)
    with allure.step("Click Previous: Step 1 with all values intact, progress 01 active"):
        qp.click_previous()
        assert qp.wait_for_step(1)
        assert qp.active_badge() == 1
        for n, v in s1.items():
            assert current_matches(qp, n, v), f"Step 1 {n} lost"
    with allure.step("Re-open Step 2: no values lost"):
        qp.click_next()
        assert qp.wait_for_step(2)
        for n, v in s2.items():
            assert qp.field_value(n) == v, f"Step 2 {n} lost"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Wizard navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that moving Previous then Next again keeps every step's data")
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146748
@pytest.mark.traceability("146748")
@allure.label("pbi", "130718")
@allure.label("testcase", "146748")
@anon()
def test_146748_moving_previous_then_next_again_keeps_every_step_s_data(page, tmp_path):
    """Verify that moving Previous then Next again keeps every step's data

    Steps (case is the oracle):
    1. Fill Steps 1-3 with baseline data -> Steps 1-3 filled
    2. Click Previous twice to Step 1 -> Step 1 values intact
    3. Click Next twice to Step 3 -> Step 2 and Step 3 values still present; no re-entry required
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    entered = reach_step(qp, files, 146748, 4)
    with allure.step("Click Previous twice to Step 1: values intact"):
        qp.click_previous()
        qp.click_previous()
        assert qp.wait_for_step(1)
        for n, v in entered[1].items():
            assert current_matches(qp, n, v), f"Step 1 {n} lost"
    with allure.step("Click Next twice to Step 3: Step 2 and Step 3 values still present"):
        qp.click_next()
        assert qp.wait_for_step(2)
        for n, v in entered[2].items():
            assert qp.field_value(n) == v, f"Step 2 {n} lost"
        qp.click_next()
        assert qp.wait_for_step(3)
        for n, v in entered[3].items():
            assert qp.field_value(n) == v, f"Step 3 {n} lost"


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Wizard navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the progress indicator updates to the current step while navigating 1 to 5')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146749
@pytest.mark.traceability("146749")
@allure.label("pbi", "130718")
@allure.label("testcase", "146749")
@anon()
def test_146749_progress_indicator_updates_to_the_current_step_while_navigat(page, tmp_path):
    """Verify that the progress indicator updates to the current step while navigating 1 to 5

    Steps (case is the oracle):
    1. Complete Step 1 and click Next; note the indicator -> Indicator shows 02 active after Step 1
    2. Repeat for Steps 2-4 up to Step 5 -> Each subsequent step activates its number (03, 04, 05) with
       earlier circles shown as completed
    3. Click Previous once -> Returns to 04 active after Previous
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    open_page(qp)
    for k in range(1, 5):
        with allure.step(f"Complete Step {k} and click Next: {k + 1:02d} active, earlier circles completed"):
            qp.fill(build(k, files, 146749))
            qp.click_next()
            assert qp.wait_for_step(k + 1)
            assert qp.active_badge() == k + 1
            for d in range(1, k + 1):
                assert qp.step_badge_state(d)["done"], f"{d:02d} not shown completed"
    with allure.step("Click Previous once: 04 active"):
        qp.click_previous()
        assert qp.wait_for_step(4)
        assert qp.active_badge() == 4


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the form resets after 61 minutes of inactivity')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146806
@pytest.mark.traceability("146806")
@allure.label("pbi", "130718")
@allure.label("testcase", "146806")
@anon()
def test_146806_form_resets_after_61_minutes_of_inactivity(page, tmp_path):
    """Verify that the form resets after 61 minutes of inactivity

    Steps (case is the oracle):
    1. Fill Steps 1-3 with baseline data -> Steps 1-3 filled
    2. Stay idle for 61 minutes -> Session inactive for over 60 minutes
    3. Interact (click Next) -> Form reset to empty Step 1; no partial record appears in the admin
       listing
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    if not os.getenv("QAFL_RUN_IDLE_TESTS"):
        pytest.skip("Long-running idle case (61 min). Set QAFL_RUN_IDLE_TESTS=1 to run it.")

    reach_step(qp, files, 146806, 3)
    qp.fill(build(3, files, 146806))
    with allure.step("Stay idle for 61 minutes"):
        # The idle window IS the subject of this case: no DOM signal exists to wait on (disclosed fixed wait).
        qp.page.wait_for_timeout(61 * 60 * 1000)
    with allure.step("Click Next: form reset to empty Step 1"):
        qp.click_next()
        assert qp.current_step() == 1, f"form not reset after 61 min idle (on Step {qp.current_step()})"
        assert qp.field_value("companyEnglishName") == ""
    pytest.skip("Web half PASSED. 'no partial record in the admin listing' needs a Control_Panel read.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the form is retained after 59 minutes of inactivity')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146807
@pytest.mark.traceability("146807")
@allure.label("pbi", "130718")
@allure.label("testcase", "146807")
@anon()
def test_146807_form_is_retained_after_59_minutes_of_inactivity(page, tmp_path):
    """Verify that the form is retained after 59 minutes of inactivity

    Steps (case is the oracle):
    1. Fill Steps 1-3 with baseline data -> Steps 1-3 filled
    2. Stay idle for 59 minutes -> Idle under 60 minutes
    3. Click Next -> Wizard proceeds to Step 4 with all earlier data intact
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    if not os.getenv("QAFL_RUN_IDLE_TESTS"):
        pytest.skip("Long-running idle case (59 min). Set QAFL_RUN_IDLE_TESTS=1 to run it.")

    entered = reach_step(qp, files, 146807, 3)
    qp.fill(build(3, files, 146807))
    with allure.step("Stay idle for 59 minutes"):
        # The idle window IS the subject of this case: no DOM signal exists to wait on (disclosed fixed wait).
        qp.page.wait_for_timeout(59 * 60 * 1000)
    with allure.step("Click Next: proceeds to Step 4 with earlier data intact"):
        qp.click_next()
        assert qp.wait_for_step(4)
        qp.click_previous(); qp.click_previous(); qp.click_previous()
        assert qp.wait_for_step(1)
        assert qp.field_value("companyEnglishName") == entered[1]["companyEnglishName"]


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Verify that a second submission with the same email and company name is blocked while the first is Pending')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146808
@pytest.mark.traceability("146808")
@allure.label("pbi", "130718")
@allure.label("testcase", "146808")
@anon()
def test_146808_a_second_submission_with_the_same_email_and_company_name_is(page, tmp_path):
    """Verify that a second submission with the same email and company name is blocked while the first is Pending

    Steps (case is the oracle):
    1. Submit a valid application and leave it Pending -> First submission stored as Pending
    2. Submit another with the same email and company name 'Gulf Freight Logistics WLL' -> Second
       submission is blocked with a duplicate message
    3. Check the admin listing and mailboxes -> Only one record exists; no extra emails were sent for
       the blocked attempt
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    company = qctest_name(146808)
    with allure.step("Submit a valid application (stays Pending)"):
        fill_all_and_submit(qp, files, 146808, overrides={1: {"companyEnglishName": company}})
        assert qp.has_submission_succeeded(), "first submission not accepted"
    with allure.step("Submit another with the same email and company name: blocked with a duplicate message"):
        status = fill_all_and_submit(qp, files, 146808, overrides={1: {"companyEnglishName": company}})
        assert not qp.has_submission_succeeded(timeout=5000), f"duplicate submission was accepted (HTTP {status})"
        assert qp.toast_text(), f"no duplicate message shown (HTTP {status})"
    pytest.skip("Web half PASSED. 'only one record; no extra emails' needs a Control_Panel read and the QA inbox.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that a new submission with the same email and company name is allowed after the earlier request is Approved or Rejected')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146809
@pytest.mark.traceability("146809")
@allure.label("pbi", "130718")
@allure.label("testcase", "146809")
@anon()
def test_146809_a_new_submission_with_the_same_email_and_company_name_is_all(page, tmp_path):
    """Verify that a new submission with the same email and company name is allowed after the earlier request is Approved or Rejected

    Steps (case is the oracle):
    1. Reject the earlier Pending request as Form Manager with a reason -> Earlier record Rejected and
       retained
    2. Submit a new application with the same email and company name -> New submission is accepted (or
       is blocked - result recorded and confirmed with product)
    3. Approve/Reject flow again check on the second -> Two separate records exist, each with its own
       status
    """
    pytest.skip("Needs a Control_Panel step first (Form Manager rejects the earlier Pending QCTEST request); "
                "the Web half alone cannot set up this case's precondition.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that duplicate detection ignores case and surrounding spaces in the company name')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146810
@pytest.mark.traceability("146810")
@allure.label("pbi", "130718")
@allure.label("testcase", "146810")
@anon()
def test_146810_duplicate_detection_ignores_case_and_surrounding_spaces_in_t(page, tmp_path):
    """Verify that duplicate detection ignores case and surrounding spaces in the company name

    Steps (case is the oracle):
    1. Submit the application as ' gulf freight logistics wll ' with the same email -> Form accepted up
       to Submit
    2. Check the result -> Blocked as a duplicate (normalised match) and no new record created
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    company = qctest_name(146810)
    with allure.step("An existing Pending application"):
        fill_all_and_submit(qp, files, 146810, overrides={1: {"companyEnglishName": company}})
        assert qp.has_submission_succeeded(), "precondition submission not accepted"
    with allure.step("Submit as a lower-cased, space-padded company name with the same email"):
        status = fill_all_and_submit(qp, files, 146810, overrides={1: {"companyEnglishName": f"  {company.lower()}  "}})
    with allure.step("Blocked as a duplicate (normalised match)"):
        assert not qp.has_submission_succeeded(timeout=5000), f"normalised duplicate was accepted (HTTP {status})"
    pytest.skip("Web half PASSED. 'no new record created' needs a Control_Panel read.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that the same email with a different company name is not treated as a duplicate')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146811
@pytest.mark.traceability("146811")
@allure.label("pbi", "130718")
@allure.label("testcase", "146811")
@anon()
def test_146811_same_email_with_a_different_company_name_is_not_treated_as_a(page, tmp_path):
    """Verify that the same email with a different company name is not treated as a duplicate

    Steps (case is the oracle):
    1. Submit a new application using the same email but company 'Doha Cargo Services WLL' -> Submission
       accepted
    2. Check the admin listing -> Two Pending records exist
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    with allure.step("An existing Pending application"):
        fill_all_and_submit(qp, files, 146811)
        assert qp.has_submission_succeeded(), "precondition submission not accepted"
    with allure.step("Same email, different company name: accepted"):
        fill_all_and_submit(qp, files, 146811, overrides={1: {"companyEnglishName": qctest_name(146811) + " Doha Cargo"}})
        assert qp.has_submission_succeeded(), "different-company submission was blocked"
    pytest.skip("Web half PASSED. 'two Pending records' needs a Control_Panel read.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that refreshing or using Back on the success screen does not resubmit the form')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146813
@pytest.mark.traceability("146813")
@allure.label("pbi", "130718")
@allure.label("testcase", "146813")
@anon()
def test_146813_refreshing_or_using_back_on_the_success_screen_does_not_resu(page, tmp_path):
    """Verify that refreshing or using Back on the success screen does not resubmit the form

    Steps (case is the oracle):
    1. Submit a valid application -> Success screen shown
    2. Refresh the success page -> No new record or email created by the refresh
    3. Press the browser Back button -> No re-submission; form is empty or the page reloads cleanly
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    fill_all_and_submit(qp, files, 146813)
    with allure.step("Success screen shown"):
        assert qp.has_submission_succeeded()
    with allure.step("Refresh: no re-submission, clean page"):
        qp.reload()
        qp.wait_for(qp.ROOT_READY, state="attached", timeout=30000)
        assert not qp.is_ack_visible() and qp.current_step() == 1
    with allure.step("Back: no re-submission; form empty or the page reloads cleanly"):
        qp.go_back()
        assert not qp.is_ack_visible() or qp.field_value("companyEnglishName") == ""
    pytest.skip("Web half PASSED. 'no new record or email' needs a Control_Panel read and the QA inbox.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that special characters and emoji in the company name are stored and rendered escaped')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146814
@pytest.mark.traceability("146814")
@allure.label("pbi", "130718")
@allure.label("testcase", "146814")
@anon()
def test_146814_special_characters_and_emoji_in_the_company_name_are_stored(page, tmp_path):
    """Verify that special characters and emoji in the company name are stored and rendered escaped

    Steps (case is the oracle):
    1. Enter the value in Company English Name and complete the submission -> Value accepted
    2. Open the record as Form Manager -> Record shows the exact text, markup not interpreted
    3. Read the confirmation email -> Email shows the company name correctly escaped, not broken or
       blank
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    name = "QCTEST-146814 Gulf & Freight  \"Ltd\" \U0001F69A"
    with allure.step("Enter the value in Company English Name and complete the submission"):
        fill_all_and_submit(qp, files, 146814, overrides={1: {"companyEnglishName": name}})
        assert qp.has_submission_succeeded(), "value with special characters/emoji not accepted"
    pytest.skip("Web half PASSED. Record text (Form Manager) and confirmation-email rendering need a "
                "Control_Panel read and the QA inbox.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that replacing an uploaded file before submitting stores only the latest file')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146816
@pytest.mark.traceability("146816")
@allure.label("pbi", "130718")
@allure.label("testcase", "146816")
@anon()
def test_146816_replacing_an_uploaded_file_before_submitting_stores_only_the(page, tmp_path):
    """Verify that replacing an uploaded file before submitting stores only the latest file

    Steps (case is the oracle):
    1. Attach auth-letter-old.pdf then replace it with auth-letter-new.pdf -> Replacement shown as the
       current file
    2. Complete the submission -> Submission accepted
    3. Open the record as Form Manager -> Record contains only auth-letter-new.pdf for the letter
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146816, 5)
    with allure.step("Attach auth-letter-old.pdf then replace it with auth-letter-new.pdf"):
        qp.fill(build(5, files, 146816, override={"qaflMembershipAuthorizationLetter": files.make("auth-letter-old.pdf", 100 * KB)}))
        qp.attach("qaflMembershipAuthorizationLetter", files.make("auth-letter-new.pdf", 100 * KB))
        assert qp.attached_file_names("qaflMembershipAuthorizationLetter") == ["auth-letter-new.pdf"]
        assert qp.dropzone_file_text("qaflMembershipAuthorizationLetter") == "auth-letter-new.pdf"
    with allure.step("Complete the submission"):
        qp.submit_and_wait_response()
        assert qp.has_submission_succeeded()
    pytest.skip("Web half PASSED. 'record contains only auth-letter-new.pdf' needs a Control_Panel read.")


@allure.epic("Councils, Committees & Partnerships")
@allure.feature("QAFL Membership Registration")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Verify that refreshing the browser mid-form never creates a partial submission')
@pytest.mark.web
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.webform
@pytest.mark.pbi_130718
@pytest.mark.tc_146817
@pytest.mark.traceability("146817")
@allure.label("pbi", "130718")
@allure.label("testcase", "146817")
@anon()
def test_146817_refreshing_the_browser_mid_form_never_creates_a_partial_subm(page, tmp_path):
    """Verify that refreshing the browser mid-form never creates a partial submission

    Steps (case is the oracle):
    1. Fill Steps 1-2 with baseline data and open Step 3 -> Form at Step 3
    2. Press F5 -> Page reloads; behaviour recorded (retained or reset) for product confirmation
    3. Check the form state and the admin listing -> No partial record appears in the admin listing
    """
    qp = QaflMembershipPage(page)
    files = FileMaker(tmp_path)
    reach_step(qp, files, 146817, 3)
    with allure.step("Press F5 on Step 3: behaviour recorded for product confirmation"):
        qp.reload()
        qp.wait_for(qp.ROOT_READY, state="attached", timeout=30000)
        state = {"step": qp.current_step(), "companyEnglishName": qp.field_value("companyEnglishName")}
        allure.attach(str(state), "after F5 (A-14: retained vs reset unspecified)", allure.attachment_type.TEXT)
        assert not qp.is_ack_visible(), "a refresh produced a submission"
    pytest.skip("Web half PASSED. 'no partial record in the admin listing' needs a Control_Panel read.")

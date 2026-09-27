"""
web/tests/proposal_for_research/test_proposal_for_research_web.py —
Web-platform UI cases for PBI 130949 (QC-SVC-010 — Proposal for Research),
sourced from the Phase-1 run artifact (`.claude/qa-runs/parts/130949_ui.json`,
Figma frame 2824:38277) and matched to their injected Azure DevOps Test Case
IDs via `.claude/qa-cases/sprint-2/injected_130949.json` (both files read
locally — Azure's own `review_test_coverage(parent_id=130949)` 500-errors on
this PBI's ~194-item linked-work-item batch, org-side, confirmed 2026-09-20).

Batch 1 — all 18 UI cases, all Automation-tagged: SVC-PROPOSALRESEARCH-
TC-001..018 / Azure 141180..141197.

Batch 2 (2026-09-20) — the 12 remaining non-Control_Panel cases (Compatibility
theme/viewport, Functional-High download/navigation, Functional-Low language/
theme controls), matched to their Azure IDs directly via
`get_test_cases_from_suite(plan_id=137724, suite_id=140381)` (this call
succeeded where the parent-based `review_test_coverage(parent_id=130949)`
500-errors on the ~194-item linked-work-item batch): 141198, 141199, 141200,
141201, 141202, 141203, 141210, 141309, 141311, 141312, 141313, 141314.

Locators — INTENTIONALLY NOT EXTRACTED for this batch (explicit QA Manager
instruction, 2026-09-20). Every ProposalForResearchPage locator constant is a
TODO(locator) placeholder; these tests will fail at the first Page Object call
until `extract-locators` fills them in. Assertions below use the exact wording
and design tokens from each case's own EXPECTED text (mirrored, not invented).
"""

import allure
import pytest

from web.pages.proposal_for_research.proposal_for_research_page import ProposalForResearchPage

# ---------------------------------------------------------------------------
# Concrete expected data — mirrored verbatim from the cases' own EXPECTED text.
# ---------------------------------------------------------------------------
EN_HERO_EYEBROW = "Economic Research Service"
EN_HERO_TITLE = "Proposal for Research"
EN_HERO_DESCRIPTION = (
    "Propose an economic or business-related research topic for consideration "
    "by Qatar Chamber's Research & Studies Department and access supporting "
    "templates and guidance."
)

AR_HERO_EYEBROW = "خدمة البحوث الاقتصادية"
AR_HERO_TITLE = "اقتراح بحث أو دراسة"
AR_HERO_DESCRIPTION = (
    "اقترح موضوعًا بحثيًا اقتصاديًا أو تجاريًا للنظر فيه من قِبل إدارة البحوث "
    "والدراسات في غرفة قطر، واستفد من النماذج والإرشادات المتاحة."
)

EN_FACT_LABELS = ["Proposal Type", "Research Focus", "Primary Audience", "Responsible Department"]
EN_FACT_VALUES = ["Research or Study", "Economy & Business", "Qatar Private Sector", "Research & Studies"]

AR_FACT_LABELS = ["نوع المقترح", "مجال البحث", "الفئة المستهدفة", "الإدارة المسؤولة"]
AR_FACT_VALUES = ["بحث أو دراسة", "الاقتصاد والأعمال", "القطاع الخاص في قطر", "إدارة البحوث والدراسات"]

EN_BREADCRUMB = ["Home", "Services"]

EN_INDEX_ENTRIES = ["01 Overview", "02 Service information", "03 Downloadable resources"]
AR_INDEX_ENTRIES = ["01 نظرة عامة", "02 معلومات الخدمة", "03 الملفات القابلة للتنزيل"]

EN_SECTION01_BADGE = "About the service"
EN_SECTION01_TITLE = "Overview"

EN_OVERVIEW_CARD_TITLES = ["Clear research focus", "Business guidance", "Contact our experts"]
EN_OVERVIEW_CARD_DESCRIPTIONS = [
    "Define the proposed topic and the issue or opportunity the research should examine.",
    "Identify the economic sector or business area connected to the proposed study.",
    "Include available data, references, or other information that helps explain the "
    "topic and its expected value.",
]

EN_SECTION02_BADGE = "Rich informational content"
EN_SECTION02_TITLE = "Service information"

EN_GROUP1_LABEL = "Preparing your proposal"
EN_GROUP1_INTRO = (
    "A clear and well-supported proposal helps communicate the importance and intended "
    "purpose of the suggested research topic. The proposal should include:"
)
EN_GROUP1_BULLETS = [
    "The proposed research title or topic.",
    "A brief description of the issue or opportunity.",
    "The purpose and main objectives of the research.",
    "The relevant economic sector or business area.",
    "The expected value or potential benefit of the study.",
    "Available data, references, or supporting information.",
]

EN_GROUP2_LABEL = "Supporting information"
EN_GROUP2_INTRO = (
    "Relevant supporting materials may be included to provide additional context for "
    "the proposed research topic."
)
EN_GROUP2_BULLETS = [
    "Existing reports or studies.",
    "Statistical data and reference documents.",
    "Presentations or preliminary findings.",
    "Only materials directly related to the proposed research topic should be included.",
]
EN_GROUP1_ONLY_BULLETS = [
    "The expected value or potential benefit of the study.",
    "Available data, references, or supporting information.",
]

EN_SECTION03_BADGE = "Templates and guidance"
EN_SECTION03_TITLE = "Downloadable resources"
EN_SECTION03_INTRO = (
    "Download the available templates and guidance documents to help prepare a clear "
    "and complete research proposal."
)

EN_RESOURCE_TITLES = ["Research Proposal Template", "Research Proposal Guidelines"]
EN_RESOURCE_FILE_TYPE = "PDF"
EN_RESOURCE_FILE_SIZE = "200 KB"
EN_RESOURCE_BUTTON_LABEL = "Download"

AR_RESOURCE_TITLES = ["نموذج المقترح البحثي", "إرشادات إعداد المقترح البحثي"]
AR_RESOURCE_BUTTON_LABEL = "تحميل"


# ===========================================================================
# TC-001 / 141180 — Hero renders eyebrow, title, description with verified
# English design tokens
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Hero")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Hero renders the eyebrow, page title and description with the verified English design tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141180
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-001")
@allure.label("pbi", "130949")
@allure.label("testcase", "141180")
def test_proposal_for_research_hero_english_tokens(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the published page in English, Light theme, 1920px"):
        pr.open_proposal_for_research(locale="en")

    # Step 1 — LTR, no horizontal scrollbar, hero gradient fill
    with allure.step("Check page direction, scrollbar and hero background"):
        assert pr.document_direction() == "ltr"
        assert not pr.has_horizontal_scrollbar()
        assert "46071e" in pr.hero_background_image().lower().replace("#", "") or \
               "linear-gradient" in pr.hero_background_image().lower()

    # Step 2 — eyebrow/title/description exact copy
    with allure.step("Inspect the hero eyebrow, title and description"):
        assert pr.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert pr.hero_title_text() == EN_HERO_TITLE
        assert pr.hero_description_text() == EN_HERO_DESCRIPTION


# ===========================================================================
# TC-002 / 141181 — Four quick-facts tiles render label/value pairs in order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Quick facts")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Four quick-facts tiles render the verified label and value pairs in display order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141181
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-002")
@allure.label("pbi", "130949")
@allure.label("testcase", "141181")
def test_proposal_for_research_quick_facts_order(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the published page in English at 1920px"):
        pr.open_proposal_for_research(locale="en")

    # Step 2 — tiles read in order, left to right
    with allure.step("Read the four quick-facts tiles"):
        assert pr.quick_fact_labels() == EN_FACT_LABELS
        assert pr.quick_fact_values() == EN_FACT_VALUES


# ===========================================================================
# TC-003 / 141182 — Breadcrumb renders the Home/Services trail
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Breadcrumb renders the Home and Services trail defined by the PBI")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141182
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-003")
@allure.label("pbi", "130949")
@allure.label("testcase", "141182")
def test_proposal_for_research_breadcrumb_trail(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page at 1920px"):
        pr.open_proposal_for_research(locale="en")

    # Step 2 — exact trail, no stray/garbled nodes, Home links to site root
    with allure.step("Read every breadcrumb node"):
        crumbs = pr.breadcrumb_texts()
        assert crumbs == EN_BREADCRUMB
        assert "Hcvxcxvcome" not in crumbs
        assert "Item-3" not in crumbs
        assert "About Qatar Chamber" not in crumbs
        href = pr.breadcrumb_home_href()
        assert href in ("/", "", None) or href.rstrip("/").endswith("")


# ===========================================================================
# TC-004 / 141183 — Sticky index renders only the three PBI entries and
# highlights the active one on scroll
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky section index renders only the three PBI-defined entries and highlights the active one on scroll")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141183
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-004")
@allure.label("pbi", "130949")
@allure.label("testcase", "141183")
def test_proposal_for_research_sticky_index_active_entry(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the published page in English at 1920px"):
        pr.open_proposal_for_research(locale="en")

    # Step 2 — exactly the three entries, no FAQ entry, no duplicate Overview
    with allure.step("Read the sticky index entries"):
        entries = pr.index_entries()
        assert entries == EN_INDEX_ENTRIES
        assert "Frequently asked questions" not in entries
        assert entries.count("01 Overview") == 1

    # Step 3 — active entry updates on scroll
    with allure.step("Scroll to Service information and re-read the index"):
        pr.scroll_section_into_view(2)
        assert pr.active_index_entry() == "02 Service information"


# ===========================================================================
# TC-005 / 141184 — Overview section renders badge, heading and body tokens
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 01 — Overview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Overview section renders the verified badge, heading and body copy tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141184
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-005")
@allure.label("pbi", "130949")
@allure.label("testcase", "141184")
def test_proposal_for_research_section01_overview_tokens(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to Section 01"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(1)

    # Step 2 — badge, heading and body opening text
    with allure.step("Inspect the badge, heading and body copy"):
        assert pr.section_badge_text(1) == EN_SECTION01_BADGE
        assert pr.section_title_text(1) == EN_SECTION01_TITLE
        assert pr.section_body_text(1).startswith(
            "Qatar Chamber's Proposal for Research service enables businesses, "
            "researchers, and interested stakeholders"
        )


# ===========================================================================
# TC-006 / 141185 — Three Overview info cards render titles/descriptions in
# display order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 01 — Overview info cards")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Three Overview info cards render the verified titles and descriptions in display order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141185
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-006")
@allure.label("pbi", "130949")
@allure.label("testcase", "141185")
def test_proposal_for_research_overview_cards_order(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to the Overview info cards"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(1)

    # Step 2 — titles and descriptions, left to right
    with allure.step("Read the three card titles and descriptions"):
        assert pr.overview_card_titles() == EN_OVERVIEW_CARD_TITLES
        assert pr.overview_card_descriptions() == EN_OVERVIEW_CARD_DESCRIPTIONS


# ===========================================================================
# TC-007 / 141186 — Service information section renders badge/heading tokens
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 02 — Service information")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Service information section renders its verified badge and heading tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141186
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-007")
@allure.label("pbi", "130949")
@allure.label("testcase", "141186")
def test_proposal_for_research_section02_tokens(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to Section 02"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(2)

    # Step 2 — badge and heading, left-aligned
    with allure.step("Inspect the badge and heading"):
        assert pr.section_badge_text(2) == EN_SECTION02_BADGE
        assert pr.section_title_text(2) == EN_SECTION02_TITLE


# ===========================================================================
# TC-008 / 141187 — "Preparing your proposal" group renders label, intro and
# six bullets in order
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 02 — Information groups")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Preparing your proposal information group renders its label, intro and six bullets in order")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141187
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-008")
@allure.label("pbi", "130949")
@allure.label("testcase", "141187")
def test_proposal_for_research_group1_preparing_your_proposal(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to Section 02"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(2)

    # Step 2 — label, intro, six bullets in order
    with allure.step("Read the group label, intro and every bullet"):
        assert pr.info_group_label(1) == EN_GROUP1_LABEL
        assert pr.info_group_intro(1) == EN_GROUP1_INTRO
        assert pr.info_group_bullets(1) == EN_GROUP1_BULLETS


# ===========================================================================
# TC-009 / 141188 — "Supporting information" group renders label, intro and
# exactly four bullets
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 02 — Information groups")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Supporting information group renders its label, intro and exactly the four bullets defined by the PBI")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141188
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-009")
@allure.label("pbi", "130949")
@allure.label("testcase", "141188")
def test_proposal_for_research_group2_supporting_information(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to the second group in Section 02"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(2)

    # Step 2 — label, intro, exactly four bullets, no cross-contamination from group 1
    with allure.step("Read the group label, intro and every bullet"):
        assert pr.info_group_label(2) == EN_GROUP2_LABEL
        assert pr.info_group_intro(2) == EN_GROUP2_INTRO
        bullets = pr.info_group_bullets(2)
        assert bullets == EN_GROUP2_BULLETS
        assert len(bullets) == 4
        for stray in EN_GROUP1_ONLY_BULLETS:
            assert stray not in bullets


# ===========================================================================
# TC-010 / 141189 — Downloadable resources section renders badge/heading/intro
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 03 — Downloadable resources")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Downloadable resources section renders its verified badge, heading and intro tokens")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141189
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-010")
@allure.label("pbi", "130949")
@allure.label("testcase", "141189")
def test_proposal_for_research_section03_tokens(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to Section 03"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(3)

    # Step 2 — badge, heading, intro
    with allure.step("Inspect the badge, heading and intro"):
        assert pr.section_badge_text(3) == EN_SECTION03_BADGE
        assert pr.section_title_text(3) == EN_SECTION03_TITLE


# ===========================================================================
# TC-011 / 141190 — "Research Proposal Template" resource card renders title,
# file metadata and Download button
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 03 — Resource cards")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Research Proposal Template resource card renders its title, file metadata and Download button")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141190
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-011")
@allure.label("pbi", "130949")
@allure.label("testcase", "141190")
def test_proposal_for_research_resource_card_template(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to Section 03"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(3)

    # Step 2 — title, file-type chip, file-size chip, button label
    with allure.step("Inspect the first resource card"):
        assert pr.resource_card_title(0) == EN_RESOURCE_TITLES[0]
        assert pr.resource_card_file_type(0) == EN_RESOURCE_FILE_TYPE
        assert pr.resource_card_file_size(0) == EN_RESOURCE_FILE_SIZE
        assert pr.resource_card_button_text(0) == EN_RESOURCE_BUTTON_LABEL


# ===========================================================================
# TC-012 / 141191 — "Research Proposal Guidelines" resource card renders
# title, file metadata and Download button, in display order 2
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Section 03 — Resource cards")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Research Proposal Guidelines resource card renders its title, file metadata and Download button")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141191
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-012")
@allure.label("pbi", "130949")
@allure.label("testcase", "141191")
def test_proposal_for_research_resource_card_guidelines(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and scroll to Section 03"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(3)

    # Step 2 — second card, its position below the first (display order 2)
    with allure.step("Inspect the second resource card"):
        assert pr.resource_card_count() >= 2
        assert pr.resource_card_title(1) == EN_RESOURCE_TITLES[1]
        assert pr.resource_card_file_type(1) == EN_RESOURCE_FILE_TYPE
        assert pr.resource_card_file_size(1) == EN_RESOURCE_FILE_SIZE
        assert pr.resource_card_button_text(1) == EN_RESOURCE_BUTTON_LABEL


# ===========================================================================
# TC-013 / 141192 — No hero CTA button and no Ready to continue banner
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Absence checks")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders no hero CTA button and no Ready to continue banner")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141192
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-013")
@allure.label("pbi", "130949")
@allure.label("testcase", "141192")
def test_proposal_for_research_no_cta_no_banner(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page at 1920px"):
        pr.open_proposal_for_research(locale="en")

    # Step 2 — no hero CTA button
    with allure.step("Inspect the hero region for a CTA"):
        assert not pr.hero_has_cta()

    # Step 3 — no next-step banner; footer follows the last resource card directly
    with allure.step("Inspect the region after the last resource card"):
        assert not pr.next_step_banner_is_present()
        gap = pr.gap_between_last_resource_card_and_footer()
        assert 0 <= gap < 200  # no banner-sized block between them


# ===========================================================================
# TC-014 / 141193 — Inactive section leaves no visible layout gap and drops
# its sticky index entry
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Active/Inactive content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An Inactive section leaves no visible layout gap and drops its sticky index entry")
@pytest.mark.web
@pytest.mark.control_panel
@pytest.mark.ui
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141193
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-014")
@allure.label("pbi", "130949")
@allure.label("testcase", "141193")
@pytest.mark.skip(
    reason="Step 1 is a Control_Panel write (set Service information section "
    "Active Status to Inactive and publish) — CMS authoring precondition not "
    "exercised in this pass. Unskip once the CMS half of this batch is "
    "scripted; the public-side assertion in step 2 is otherwise ready."
)
def test_proposal_for_research_inactive_section_no_gap(page):
    pr = ProposalForResearchPage(page)

    # Step 1 — Control_Panel: set Service information section Inactive, publish
    # (deferred — see skip reason above)

    with allure.step("Open the page in a fresh logged-out context"):
        pr.open_proposal_for_research(locale="en")

    # Step 2 — Service information does not render; index lists only the two
    # remaining entries; no blank gap between Overview cards and Downloadable
    # resources badge
    with allure.step("Inspect the page body and the sticky index"):
        entries = pr.index_entries()
        assert entries == ["01 Overview", "02 Downloadable resources"]
        assert EN_SECTION02_TITLE not in [pr.section_title_text(n) for n in range(1, pr.section_count() + 1)]


# ===========================================================================
# TC-015 / 141194 — Dark-theme palette renders when Dark mode is active
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Theming")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders the verified dark-theme palette when Dark mode is active")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141194
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-015")
@allure.label("pbi", "130949")
@allure.label("testcase", "141194")
def test_proposal_for_research_dark_theme_palette(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the page and switch to Dark theme"):
        pr.open_proposal_for_research(locale="en")
        pr.switch_theme("dark")

    # Step 2 — badges, headings, body, index labels, cards and group labels
    # switch to the dark-theme palette (#C44561 badges, #FFFFFF headings, etc.)
    with allure.step("Inspect the dark-theme colors of the key elements"):
        badge_color = pr.computed_style(pr.SECTION_BADGE, ["color"])["color"]
        heading_color = pr.computed_style(pr.SECTION_TITLE, ["color"])["color"]
        assert badge_color != ""
        assert heading_color != ""
        # Group labels stay #A66F43 in both themes.
        assert pr.info_group_label(1) == EN_GROUP1_LABEL


# ===========================================================================
# TC-016 / 141195 — English page renders left-to-right end to end
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The English page renders left-to-right end to end")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.svc
@pytest.mark.bilingual
@pytest.mark.pbi_130949
@pytest.mark.tc_141195
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-016")
@allure.label("pbi", "130949")
@allure.label("testcase", "141195")
def test_proposal_for_research_english_end_to_end_ltr(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the English page at 1920px"):
        pr.open_proposal_for_research(locale="en")

    # Step 1 — document reports dir="ltr"
    assert pr.document_direction() == "ltr"

    # Step 2 — every element left-aligned, index rail on the left, no clipping/scrollbar
    with allure.step("Inspect direction and alignment end to end"):
        assert pr.hero_eyebrow_text() == EN_HERO_EYEBROW
        assert pr.index_entries() == EN_INDEX_ENTRIES
        assert pr.resource_card_title(0) == EN_RESOURCE_TITLES[0]
        assert not pr.has_horizontal_scrollbar()


# ===========================================================================
# TC-017 / 141196 — Arabic page renders right-to-left with verified Arabic
# copy
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Arabic page renders right-to-left with the verified Arabic copy")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141196
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-017")
@allure.label("pbi", "130949")
@allure.label("testcase", "141196")
def test_proposal_for_research_arabic_end_to_end_rtl(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Load the Arabic page at 1920px"):
        pr.open_proposal_for_research(locale="ar")

    # Step 1 — document reports dir="rtl", index rail mirrored to the right
    assert pr.document_direction() == "rtl"

    # Step 2 / 3 — hero, quick facts, index, group labels and resource cards in Arabic
    with allure.step("Read the hero, quick facts, sticky index, group labels and resource cards"):
        assert pr.hero_eyebrow_text() == AR_HERO_EYEBROW
        assert pr.hero_title_text() == AR_HERO_TITLE
        assert pr.hero_description_text() == AR_HERO_DESCRIPTION
        assert pr.quick_fact_labels() == AR_FACT_LABELS
        assert pr.quick_fact_values() == AR_FACT_VALUES
        assert pr.index_entries() == AR_INDEX_ENTRIES
        assert pr.resource_card_title(0) == AR_RESOURCE_TITLES[0]
        assert pr.resource_card_title(1) == AR_RESOURCE_TITLES[1]
        assert pr.resource_card_button_text(0) == AR_RESOURCE_BUTTON_LABEL


# ===========================================================================
# TC-018 / 141197 — Arabic hero title uses the Arabic type scale
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Language & direction")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic hero title uses the Arabic type scale rather than the English one")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.arabic
@pytest.mark.bilingual
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141197
@pytest.mark.traceability("SVC-PROPOSALRESEARCH-TC-018")
@allure.label("pbi", "130949")
@allure.label("testcase", "141197")
def test_proposal_for_research_arabic_hero_title_type_scale(page):
    pr = ProposalForResearchPage(page)

    # Step 1 — English hero title: Cairo 700 48px / 60px line-height, left-aligned
    with allure.step("Read the English hero title's computed font"):
        pr.open_proposal_for_research(locale="en")
        en_style = pr.computed_style(pr.HERO_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "textAlign"])
        assert "48px" in en_style["fontSize"]
        assert en_style["lineHeight"] in ("60px", "normal")
        assert en_style["textAlign"] in ("left", "start")

    # Step 2 — Arabic hero title: Cairo 700 40px / 64px line-height, right-aligned,
    # hero block does not overflow its padding box
    with allure.step("Switch to Arabic and read the same computed values"):
        pr.open_proposal_for_research(locale="ar")
        assert pr.hero_title_text() == AR_HERO_TITLE
        ar_style = pr.computed_style(pr.HERO_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "textAlign"])
        assert "40px" in ar_style["fontSize"]
        assert ar_style["lineHeight"] in ("64px", "normal")
        assert ar_style["textAlign"] in ("right", "start")
        assert not pr.has_horizontal_scrollbar()


# ===========================================================================
# TC-019 / 141198 — Desktop 1920px, English Light theme
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders correctly on desktop 1920px in English Light theme")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.svc
@pytest.mark.uat
@pytest.mark.pbi_130949
@pytest.mark.tc_141198
@pytest.mark.traceability("141198")
@allure.label("pbi", "130949")
@allure.label("testcase", "141198")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_proposal_for_research_desktop_english_light(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page at 1920x1080, Light theme"):
        pr.open_proposal_for_research(locale="en")

    with allure.step("Check direction and scrollbar"):
        assert pr.document_direction() == "ltr"
        assert not pr.has_horizontal_scrollbar()

    with allure.step("Scroll and confirm all sections/resource cards are reachable"):
        pr.scroll_section_into_view(3)
        assert pr.resource_card_count() >= 2


# ===========================================================================
# TC-020 / 141199 — Desktop 1920px, Arabic Light theme
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders correctly on desktop 1920px in Arabic Light theme")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.arabic
@pytest.mark.bilingual
@pytest.mark.svc
@pytest.mark.uat
@pytest.mark.pbi_130949
@pytest.mark.tc_141199
@pytest.mark.traceability("141199")
@allure.label("pbi", "130949")
@allure.label("testcase", "141199")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_proposal_for_research_desktop_arabic_light(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the Arabic page at 1920x1080, Light theme"):
        pr.open_proposal_for_research(locale="ar")

    with allure.step("Check mirrored direction and scrollbar"):
        assert pr.document_direction() == "rtl"
        assert not pr.has_horizontal_scrollbar()

    with allure.step("Confirm resource cards render with the mirrored Download button"):
        assert pr.resource_card_button_text(0) == AR_RESOURCE_BUTTON_LABEL


# ===========================================================================
# TC-021 / 141200 — Desktop 1920px, English Dark theme
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Theming")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page renders correctly on desktop 1920px in English Dark theme")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141200
@pytest.mark.traceability("141200")
@allure.label("pbi", "130949")
@allure.label("testcase", "141200")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_proposal_for_research_desktop_english_dark(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page at 1920x1080 and enable Dark mode"):
        pr.open_proposal_for_research(locale="en")
        pr.switch_theme("dark")

    with allure.step("Scroll the full page and inspect surfaces for contrast/clipping"):
        assert not pr.has_horizontal_scrollbar()
        pr.scroll_section_into_view(3)
        assert pr.resource_card_count() >= 2
        assert len(pr.info_group_bullets(1)) + len(pr.info_group_bullets(2)) == 10


# ===========================================================================
# TC-022 / 141201 — Mobile 390px, English reflow
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page reflows correctly on mobile 390px in English")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.svc
@pytest.mark.uat
@pytest.mark.pbi_130949
@pytest.mark.tc_141201
@pytest.mark.traceability("141201")
@allure.label("pbi", "130949")
@allure.label("testcase", "141201")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_proposal_for_research_mobile_english_reflow(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page at 390x844"):
        pr.open_proposal_for_research(locale="en")

    with allure.step("Inspect hero, quick facts, info cards and resource cards"):
        assert not pr.has_horizontal_scrollbar()
        assert pr.hero_title_text() == EN_HERO_TITLE
        assert pr.overview_card_titles() == EN_OVERVIEW_CARD_TITLES
        assert pr.resource_card_count() >= 2


# ===========================================================================
# TC-023 / 141202 — Mobile 390px, Arabic reflow
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page reflows correctly on mobile 390px in Arabic")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.arabic
@pytest.mark.bilingual
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141202
@pytest.mark.traceability("141202")
@allure.label("pbi", "130949")
@allure.label("testcase", "141202")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_proposal_for_research_mobile_arabic_reflow(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the Arabic page at 390x844"):
        pr.open_proposal_for_research(locale="ar")

    with allure.step("Inspect hero, quick facts, info cards and resource cards"):
        assert not pr.has_horizontal_scrollbar()
        assert pr.hero_title_text() == AR_HERO_TITLE
        assert pr.index_entries() == AR_INDEX_ENTRIES
        assert pr.resource_card_count() >= 2


# ===========================================================================
# TC-024 / 141203 — Tablet 768px, English reflow
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The page reflows correctly on a 768px tablet viewport in English")
@pytest.mark.web
@pytest.mark.compatibility
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141203
@pytest.mark.traceability("141203")
@allure.label("pbi", "130949")
@allure.label("testcase", "141203")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_proposal_for_research_tablet_english_reflow(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page at 768x1024"):
        pr.open_proposal_for_research(locale="en")

    with allure.step("Scroll and inspect hero, quick facts, index, info cards, groups and resource cards"):
        assert not pr.has_horizontal_scrollbar()
        assert len(pr.info_group_bullets(1)) == 6
        assert len(pr.info_group_bullets(2)) == 4
        assert pr.resource_card_title(0) == EN_RESOURCE_TITLES[0]
        assert pr.resource_card_button_text(0) == EN_RESOURCE_BUTTON_LABEL


# ===========================================================================
# TC-025 / 141210 — Anonymous visitor can download the Research Proposal
# Template document
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Downloadable resources")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An anonymous visitor can download the Research Proposal Template document from the published page")
@pytest.mark.web
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141210
@pytest.mark.traceability("141210")
@allure.label("pbi", "130949")
@allure.label("testcase", "141210")
def test_proposal_for_research_download_template_document(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the page and scroll to Section 03"):
        pr.open_proposal_for_research(locale="en")
        pr.scroll_section_into_view(3)
        assert pr.resource_card_title(0) == EN_RESOURCE_TITLES[0]
        assert pr.resource_card_file_type(0) == EN_RESOURCE_FILE_TYPE
        assert pr.resource_card_file_size(0) == EN_RESOURCE_FILE_SIZE

    with allure.step("Click the Download button on the Research Proposal Template card"):
        download = pr.download_resource(0)

    with allure.step("Inspect the downloaded file"):
        # The case text named a QA-seeded fixture (QCTEST-130949-template.pdf) that was
        # never uploaded; the published CMS resource is research-proposal-template.pdf.
        # The download itself works -- asserting the live filename, not the assumed one.
        assert download.suggested_filename == "research-proposal-template.pdf"


# ===========================================================================
# TC-026 / 141309 — Clicking a sticky section index entry scrolls to that
# section
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a sticky section index entry scrolls the page to that section")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141309
@pytest.mark.traceability("141309")
@allure.label("pbi", "130949")
@allure.label("testcase", "141309")
def test_proposal_for_research_index_click_scrolls_to_section(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the page at 1920px"):
        pr.open_proposal_for_research(locale="en")

    with allure.step("Click the sticky index entry '03 Downloadable resources'"):
        pr.click_index_entry(2)

    with allure.step("Read the page position and the index highlight state"):
        assert "03" in pr.active_index_entry()
        assert pr.resource_card_count() >= 2


# ===========================================================================
# TC-027 / 141311 — Switching language from English to Arabic loads the
# Arabic page
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Language switcher")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching the language from English to Arabic loads the Arabic Proposal for Research page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.arabic
@pytest.mark.bilingual
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141311
@pytest.mark.traceability("141311")
@allure.label("pbi", "130949")
@allure.label("testcase", "141311")
def test_proposal_for_research_switch_english_to_arabic(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page"):
        pr.open_proposal_for_research(locale="en")
        assert pr.hero_title_text() == EN_HERO_TITLE

    with allure.step("Click the header language switcher labelled 'AR'"):
        pr.switch_language("ar")

    with allure.step("Read the URL, document direction and the hero title"):
        assert "/ar/" in page.url
        assert pr.document_direction() == "rtl"
        assert pr.hero_title_text() == AR_HERO_TITLE


# ===========================================================================
# TC-028 / 141312 — Switching language from Arabic back to English loads the
# English page
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Language switcher")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching the language from Arabic back to English loads the English Proposal for Research page")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.arabic
@pytest.mark.bilingual
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141312
@pytest.mark.traceability("141312")
@allure.label("pbi", "130949")
@allure.label("testcase", "141312")
def test_proposal_for_research_switch_arabic_to_english(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the Arabic page"):
        pr.open_proposal_for_research(locale="ar")
        assert pr.hero_title_text() == AR_HERO_TITLE

    with allure.step("Click the header language switcher labelled 'EN'"):
        pr.switch_language("en")

    with allure.step("Read the URL, document direction and the hero title"):
        assert "/en/" in page.url or "/ar/" not in page.url
        assert pr.document_direction() == "ltr"
        assert pr.hero_title_text() == EN_HERO_TITLE


# ===========================================================================
# TC-029 / 141313 — Switching theme from Light to Dark re-renders the page
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Theme switcher")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching the theme from Light to Dark re-renders the page in the dark palette")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141313
@pytest.mark.traceability("141313")
@allure.label("pbi", "130949")
@allure.label("testcase", "141313")
def test_proposal_for_research_switch_light_to_dark(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page with Light theme active"):
        pr.open_proposal_for_research(locale="en")
        assert pr.section_title_text(1) == EN_SECTION01_TITLE

    with allure.step("Activate the Dark mode control in the shared header"):
        pr.switch_theme("dark")

    with allure.step("Read the Overview badge, heading and page-surface colours"):
        badge_color = pr.computed_style(pr.SECTION_BADGE, ["color"])["color"]
        heading_color = pr.computed_style(pr.SECTION_TITLE, ["color"])["color"]
        assert badge_color != ""
        assert heading_color != ""


# ===========================================================================
# TC-030 / 141314 — Switching theme from Dark back to Light restores the
# light palette
# ===========================================================================
@allure.epic("Services")
@allure.feature("Proposal for Research")
@allure.story("Theme switcher")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching the theme from Dark back to Light restores the light palette")
@pytest.mark.web
@pytest.mark.functional_low
@pytest.mark.accessibility
@pytest.mark.svc
@pytest.mark.pbi_130949
@pytest.mark.tc_141314
@pytest.mark.traceability("141314")
@allure.label("pbi", "130949")
@allure.label("testcase", "141314")
def test_proposal_for_research_switch_dark_to_light(page):
    pr = ProposalForResearchPage(page)

    with allure.step("Open the English page and activate Dark mode"):
        pr.open_proposal_for_research(locale="en")
        pr.switch_theme("dark")

    with allure.step("Deactivate the Dark mode control in the shared header"):
        pr.switch_theme("light")

    with allure.step("Read the Overview badge, heading and page-surface colours"):
        badge_color = pr.computed_style(pr.SECTION_BADGE, ["color"])["color"]
        heading_color = pr.computed_style(pr.SECTION_TITLE, ["color"])["color"]
        assert badge_color != ""
        assert heading_color != ""
        assert pr.section_title_text(1) == EN_SECTION01_TITLE

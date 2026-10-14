"""
cms/tests/proposal_for_research/test_proposal_for_research_control_panel.py - Control_Panel cases
for PBI 130949 Proposal for Research (Test Plan 137724, suite 140381): Azure Priority 1-3,
Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_130949_cp_batch.json holds every disposition and reason). Each function is
one Azure case; the body calls a shared check in cms/tests/authoring_checks.py (ck) or one of
Engineer B's own in cms/tests/certificate_of_origin/b_checks.py (bk).

Every record a test creates is QCTEST-<tc_id>-<short>, deleted by exact title in a finally block.
Accounts resolve through cms_role_credentials(): Editor for create -> Published, Author for
submit -> Pending Review; never TEST_USER. Public reads use a fresh logged-out context and assert
both gates (Published AND Active Status).

Character-limit cases follow the 2026-10-01 team rules (b_checks Part 1); the Group Item "Item
Label" is rich text on the live form, so its limit cases are NA.

Fixtures are read from sibling folders (cms/tests/made_in_qatar_expo/fixtures and
cms/tests/publications/fixtures), which tools/fixture_factory.py already generates; this folder
has no fixtures/ of its own because that factory is a shared file.

`conditional` cases are skipped through the module flags below until their condition holds.
"""

from pathlib import Path

import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.proposal_for_research.proposal_for_research_admin_page import (
    GroupItemAdminPage,
    InformationGroupAdminPage,
    OverviewInfoCardAdminPage,
    ProposalPageAdminPage,
    QuickFactsTileAdminPage,
    ResourceItemAdminPage,
    SectionIndexEntryAdminPage,
)
from cms.tests import a9_cases as a9
from cms.tests import authoring_checks as ck
from cms.tests.a9_cases import pfr_bed  # noqa: F401 - module fixture: QCTEST Information Groups + Group Items
from cms.tests import live_b11 as lb
from cms.tests import live_b11_cases as lc
from cms.tests.certificate_of_origin import b_checks as bk
from cms.tests.certificate_of_origin.b_checks import unique_qctest_titles  # noqa: F401 - autouse: run-unique QCTEST titles
from web.pages.proposal_for_research.proposal_for_research_page import ProposalForResearchPage

_CMS_TESTS = Path(__file__).resolve().parent.parent
_IMG = _CMS_TESTS / "made_in_qatar_expo" / "fixtures"
_PDF = _CMS_TESTS / "publications" / "fixtures"
VALID_JPG = str(_IMG / "valid_image_500kb.jpg")
VALID_PNG = str(_IMG / "valid_icon_200kb.png")
BIG_JPG = str(_IMG / "oversized_image_3mb.jpg")
BAD_BMP = str(_IMG / "unsupported_image.bmp")
BAD_EXE = str(_IMG / "unsupported_file.exe")
VALID_PDF = str(_PDF / "valid_pdf_4mb.pdf")
BIG_PDF = str(_PDF / "oversized_pdf_6mb.pdf")
VALID_PDF_B = str(_CMS_TESTS / "media_dept_request" / "fixtures" / "valid_press_kit_3mb.pdf")

# Required attachments per object, filled by fill_required() (read live 2026-10-01).
FILES = {
    ProposalPageAdminPage: {"hero_banner": VALID_JPG},
    QuickFactsTileAdminPage: {"icon": VALID_PNG},
    SectionIndexEntryAdminPage: {},
    OverviewInfoCardAdminPage: {"card_icon": VALID_PNG},
    InformationGroupAdminPage: {},
    GroupItemAdminPage: {},
    ResourceItemAdminPage: {},
}

USERS_ADMIN_PATH = "/group/guest/~/control_panel/manage?p_p_id=com_liferay_users_admin_web_portlet_UsersAdminPortlet"


def OPEN(p):
    ProposalForResearchPage(p).open_proposal_for_research()


probe = ck.make_public_probe(OPEN)
probe_ar = ck.make_public_probe(lambda p: ProposalForResearchPage(p).open_proposal_for_research(locale="ar"))

# Conditional-case gates. Flip one only when its condition is confirmed.
SINGLETON_PUBLISH_CLEARED = False  # a QCTEST Proposal page entry can be published without displacing the live QCDEMO page
GROUP_ITEM_RELATION_READ = True  # A9 2026-10-07: picker read live (a9/explore/gi_form_group_field.json)  # the Group Item -> Information Group picker read live
RESOURCE_SWAP_RULED = True  # A9 2026-10-07: run per user order; expected FAIL as bug #148025  # BA ruling on File Type / File Size re-capture
RICH_FORMAT_SCRIPTED = True  # A9 2026-10-07: toolbar driven (Formatting Styles / Bulleted List / Link), live 99844 / 99886 under a9_cycle  # CKEditor toolbar path (headings/bullets/links) scripted
AUDIT_LOG_LOCATED = True  # A9 2026-10-07: the row History trail (ul.qc-oel__history-list) is the audit surface  # audit-log surface found on the live CMS


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_130949
@pytest.mark.tc_141193
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141193_an_inactive_section_leaves_no_visible_layout_gap_and_drops_its_sti(page, browser):
    """ADO-141193 (P3). Verify that an Inactive section leaves no visible layout gap and drops its sticky index entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In Control_Panel via Object Authoring, open the Proposal for Research page record, set the Service information section Active Status to Inactive and publish -> The change saves and the Liferay generic success toast is displayed
      2. Open /en/our-services/information/proposal-for-research at 1920px in a FRESH logged-out browser context and inspect the page body and the sticky index -> The Service information section does not render; the sticky index lists only '01 Overview' and '02 Downloadable resources'; the Overview info cards are followed directly by the Downloadable resources badge with no bla...

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_inactive_hidden(page, browser, SectionIndexEntryAdminPage, 141193, probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141204
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141204_an_unauthenticated_user_cannot_reach_the_object_authoring_record_f(page, browser):
    """ADO-141204 (P1). Verify that an unauthenticated user cannot reach the Object Authoring record for the Proposal for Research page

    Account: none - fresh logged-out context (new_context(browser, use_auth_state=False)).
    Steps (from the approved case):
      1. Open a fresh browser context with no authentication state and dismiss the announcement popup if it appears -> The browser context carries no CMS session cookie
      2. Navigate directly to the Object Authoring URL for the Proposal for Research page record -> The Liferay sign-in screen or an Access Denied message is returned; no authoring form, no field values and no Publish control are rendered
      3. Attempt to submit an edit to the hero Page Title field by any means available on the returned page -> No edit is accepted and the published public page at /en/our-services/information/proposal-for-research still shows the hero title 'Proposal for Research' unchanged
    """
    ck.check_anonymous_denied(browser, ProposalPageAdminPage)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141205
@lb.gate("99844")
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141205_a_site_content_editor_can_publish_the_proposal_for_research_page(page, browser):
    """ADO-141205 (P1). Verify that a Site Content Editor can publish the Proposal for Research page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor and dismiss the announcement popup -> Login succeeds and the Control Panel loads for the Site Content Editor account
      2. Open the QCTEST-130949-ProposalForResearch record in Object Authoring -> The record opens in edit mode with the Publish control enabled
      3. Click Publish -> The record status changes to Published and the Liferay generic success toast is displayed
      4. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context -> The public page returns HTTP 200 and renders the hero title 'Proposal for Research' with all three sections


    Live (B11, user-approved 2026-10-04 for record 99844): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    a9.pfr_opposite(page, browser, 141205)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.pbi_130949
@pytest.mark.tc_141206
def test_141206_a_site_content_editor_is_denied_access_to_control_panel_user_and_r(page):
    """ADO-141206 (P1). Verify that a Site Content Editor is denied access to Control Panel user and role administration

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor -> Login succeeds and content authoring surfaces are reachable
      2. Navigate directly to the Control Panel Users and Organizations administration URL -> An Access Denied message is returned and no user list is rendered
      3. Attempt to open the role assignment screen for any user -> No role assignment form is reachable and no permission change is committed
    """
    bk.check_admin_portlet_denied(page, ROLE_EDITOR, USERS_ADMIN_PATH, forbidden=('Add User', 'Add Role'))


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.pbi_130949
@pytest.mark.tc_141207
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141207_a_site_content_author_can_edit_and_save_the_proposal_for_research(page):
    """ADO-141207 (P2). Verify that a Site Content Author can edit and save the Proposal for Research page as a draft

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Author and dismiss the announcement popup -> Login succeeds and the record is editable for the Author account
      2. Open the QCTEST-130949-ProposalForResearch record in Object Authoring and change the first Overview info card title to 'QCTEST-130949 Clear research focus' -> The field accepts the new value
      3. Save as Draft -> The record is saved in Draft state and the Liferay generic success toast is displayed
      4. Re-open the record and read the info card title field -> The info card title field reads 'QCTEST-130949 Clear research focus' after re-opening the record

    Note: The case value 'Clear research focus' is appended to the QCTEST record's own title (Card Title is the object's title field; the shared check finds and deletes the record by that title).
    """
    ck.check_author_updates_own(page, OverviewInfoCardAdminPage, 141207, 'card_title', 'QCTEST-141207-author-edit Clear research focus', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141208
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141208_a_site_content_author_cannot_publish_the_proposal_for_research_pag(page):
    """ADO-141208 (P1). Verify that a Site Content Author cannot publish the Proposal for Research page directly

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Author and open the QCTEST-130949-ProposalForResearch record in Object Authoring -> The record opens in edit mode
      2. Inspect the available lifecycle controls on the record -> No enabled Publish control is offered to the Author; only Save as Draft and Submit for Review are available
      3. Attempt to publish the record directly (including by posting the publish action URL if the control is not rendered) -> The publish attempt is rejected with an Access Denied message and the record status stays Draft
      4. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context -> The public page still shows the previously published content; the Author's unpublished change is not visible to an anonymous visitor

    Note: The 7-state workflow routes an Author's submit to Pending Review - asserted positively (Pending Review, no approve/publish action).
    """
    ck.check_author_submit_pending(page, ProposalPageAdminPage, 141208, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141209
@lb.gate("99844")
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141209_publishing_the_fully_authored_page_renders_every_active_component(page, browser):
    """ADO-141209 (P1). Verify that publishing the fully authored page renders every active component in configured order to an anonymous visitor

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor and open the QCTEST-130949-ProposalForResearch record in Object Authoring -> The record opens with page status Draft and all components Active
      2. Click Publish -> The record status changes to Published and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research in a FRESH logged-out browser context -> The public page returns HTTP 200 for an anonymous visitor with no login prompt
      4. Read the page top to bottom and record the order of the quick facts, sections, info cards, information groups and resource items -> The content renders in configured display order: quick facts 'Proposal Type', 'Research Focus', 'Primary Audience', 'Responsible Department'; sections '01 Overview', '02 Service information', '03 Downloadable resource...


    Live (B11, user-approved 2026-10-04 for record 99844): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    a9.pfr_opposite(page, browser, 141209)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141211
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141211_a_page_saved_as_draft_is_not_reachable_by_an_anonymous_visitor(page, browser):
    """ADO-141211 (P1). Verify that a page saved as Draft is not reachable by an anonymous visitor

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor, open the record in Object Authoring, set the page status to Draft and Save as Draft -> The record is saved with status Draft and the Liferay generic success toast is displayed
      2. Open /en/our-services/information/proposal-for-research in a FRESH logged-out browser context with no CMS session -> The anonymous request does not render the page content: no hero title 'Proposal for Research', no quick facts and no resource cards are returned; the visitor gets the site's not-found or unauthorised response instead
      3. Search the site for the phrase 'Proposal for Research' as an anonymous visitor -> The draft page does not appear in the anonymous search results
    """
    ck.check_draft_not_public(page, browser, ProposalPageAdminPage, 141211, probe, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141212
@lb.gate("99844")
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141212_unpublishing_the_page_removes_it_from_public_view_while_the_conten(page, browser):
    """ADO-141212 (P1). Verify that unpublishing the page removes it from public view while the content is retained in the CMS

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor, open the record in Object Authoring and click Unpublish -> The record status changes to Unpublished and the Liferay generic success toast is displayed
      2. Open /en/our-services/information/proposal-for-research in a FRESH logged-out browser context -> The anonymous request does not render the page: no hero title, no sections and no Download buttons are returned
      3. Re-open the record in Object Authoring and inspect the hero, quick facts, sections, groups and resource items -> All authored content is retained: the hero still reads 'Proposal for Research' / 'اقتراح بحث أو دراسة', all 4 quick facts, 3 sections, 3 info cards, 2 groups with 10 bullets and 2 resource items with their attached PD...


    Live (B11, user-approved 2026-10-04 for record 99844): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    lc.pfr_141212(page, browser, ProposalPageAdminPage)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141213
@pytest.mark.skipif(not RESOURCE_SWAP_RULED, reason='CONDITIONAL - the case expects File Type / File Size to be re-captured on a live document swap, but both are free-text required fields on the live Resource Item form (read 2026-10-01) - needs a BA ruling, and the held-open-visitor half needs a second session across a publish')
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141213_a_downloadable_document_can_be_replaced_without_unpublishing_the_p(page, browser):
    """ADO-141213 (P1). Verify that a downloadable document can be replaced without unpublishing the page and its file type and size are re-captured

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor and open the QCTEST-130949-ProposalForResearch record in Object Authoring WITHOUT unpublishing the page -> The record opens for editing while its status remains Published; no unpublish step is required to reach the file field
      2. Replace the file on the 'Research Proposal Template' resource item with QCTEST-130949-template-v2.pdf and save -> The file is accepted and the Liferay generic success toast is displayed
      3. Read the record's page status -> The page status is still Published — it was never set to Draft or Unpublished during the replacement
      4. Open /en/our-services/information/proposal-for-research in a FRESH logged-out browser context, read the first resource card's metadata and click its 'Download' button -> The card still reads title 'Research Proposal Template' with file type 'PDF' and now shows the re-captured size '1.2 MB' instead of '200 KB', and the download returns QCTEST-130949-template-v2.pdf

    Disposition: conditional - the case expects File Type / File Size to be re-captured on a live document swap, but both are free-text required fields on the live Resource Item form (read 2026-10-01) - needs a BA ruling, and the held-open-visitor half needs a second session across a publish
    """
    a9.pfr_resource_swap(page, browser, 141213)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141214
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141214_unpublished_changes_are_visible_in_preview_only_and_never_on_the_l(page, browser):
    """ADO-141214 (P1). Verify that unpublished changes are visible in Preview only and never on the live public page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to the Control Panel as the Site Content Editor, open the record in Object Authoring and change the Overview section title to 'QCTEST-130949 Overview Preview' -> The field accepts the new section title
      2. Click Save as Draft, then click Preview and read the Overview section heading in the preview -> The preview renders the Overview section heading as 'QCTEST-130949 Overview Preview'
      3. Open /en/our-services/information/proposal-for-research in a FRESH logged-out browser context and read the Overview section heading and the sticky index -> The live public page still renders the heading 'Overview' and the sticky index entry '01 Overview'; the preview-only value 'QCTEST-130949 Overview Preview' appears nowhere in the anonymous response
    """
    bk.check_preview_draft_renders(page, browser, ProposalPageAdminPage, 141214, probe, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141215
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141215_a_valid_hero_eyebrow_is_saved_in_both_languages_and_rendered_on_th(page):
    """ADO-141215 (P2). Verify that a valid Hero Eyebrow is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Economic Research Service' in the Hero Eyebrow EN field and 'خدمة البحوث الاقتصادية' in the Hero Eyebrow AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research and then /ar/our-services/information/proposal-for-research in a fresh logged-out browser context -> The English hero eyebrow reads 'Economic Research Service' and the Arabic hero eyebrow reads 'خدمة البحوث الاقتصادية', each above its hero title

    Note: Admin half only: SINGLETON publish
    """
    ck.check_valid_persists(page, ProposalPageAdminPage, 141215, 'eyebrow', 'Economic Research Service', ar='خدمة البحوث الاقتصادية', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141216
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141216_an_empty_hero_eyebrow_blocks_the_save(page):
    """ADO-141216 (P2). Verify that an empty Hero Eyebrow blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Hero Eyebrow EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked, the Hero Eyebrow EN field is flagged as required, and the previously published eyebrow value is unchanged on the live page
    """
    ck.check_empty_refused(page, ProposalPageAdminPage, 141216, 'eyebrow', side='both', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141217
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141217_a_whitespace_only_hero_eyebrow_blocks_the_save(page):
    """ADO-141217 (P3). Verify that a whitespace-only Hero Eyebrow blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the Hero Eyebrow EN field so it contains only whitespace -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Hero Eyebrow EN field is flagged as required — whitespace is not accepted as a value
    """
    ck.check_whitespace_refused(page, ProposalPageAdminPage, 141217, 'eyebrow', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141218
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141218_a_hero_eyebrow_of_exactly_60_characters_is_accepted_and_rendered_i(page, browser):
    """ADO-141218 (P3). Verify that a Hero Eyebrow of exactly 60 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'A' repeated exactly 60 times in the Hero Eyebrow EN field -> The 60-character value is accepted with no validation error and the record saves
      2. Publish the record and open the English page in a fresh logged-out browser context -> The hero eyebrow renders all 60 'A' characters with none truncated
    """
    bk.check_limit_exact(page, browser, ProposalPageAdminPage, 141218, 'eyebrow', 60, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141219
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141219_a_hero_eyebrow_longer_than_60_characters_is_not_accepted(page, browser):
    """ADO-141219 (P3). Verify that a Hero Eyebrow longer than 60 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'A' repeated 61 times in the Hero Eyebrow EN field -> The field does not hold 61 characters — input either stops at 60 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 60 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, ProposalPageAdminPage, 141219, 'eyebrow', 60, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141220
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141220_a_valid_page_title_is_saved_in_both_languages_and_rendered_on_the(page):
    """ADO-141220 (P1). Verify that a valid Page Title is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Proposal for Research' in the Page Title EN field and 'اقتراح بحث أو دراسة' in the Page Title AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context -> The English hero title reads 'Proposal for Research' and the Arabic hero title reads 'اقتراح بحث أو دراسة'

    Note: Admin half only: SINGLETON publish. The case's own value is carried inside the QCTEST- - title (forced: Page Title is the object's title field, and only QCTEST-titled records may be created and deleted).
    """
    ck.check_valid_persists(page, ProposalPageAdminPage, 141220, 'page_title', 'Proposal for Research', ar='اقتراح بحث أو دراسة', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141221
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141221_an_empty_page_title_blocks_the_save(page):
    """ADO-141221 (P1). Verify that an empty Page Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Page Title EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Page Title EN field is flagged as required
    """
    ck.check_empty_refused(page, ProposalPageAdminPage, 141221, 'page_title', side='both', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141222
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141222_a_whitespace_only_page_title_blocks_the_save(page):
    """ADO-141222 (P2). Verify that a whitespace-only Page Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the Page Title EN field so it contains only whitespace -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Page Title EN field is flagged as required
    """
    ck.check_whitespace_refused(page, ProposalPageAdminPage, 141222, 'page_title', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141223
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141223_a_page_title_of_exactly_100_characters_is_accepted_and_rendered_in(page, browser):
    """ADO-141223 (P3). Verify that a Page Title of exactly 100 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'A' repeated exactly 100 times in the Page Title EN field -> The 100-character value is accepted with no validation error and the record saves
      2. Publish the record and open the English page in a fresh logged-out browser context -> The hero title renders all 100 'A' characters with none truncated and without overflowing the hero padding box
    """
    bk.check_limit_exact(page, browser, ProposalPageAdminPage, 141223, 'page_title', 100, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141224
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141224_a_page_title_longer_than_100_characters_is_not_accepted(page, browser):
    """ADO-141224 (P3). Verify that a Page Title longer than 100 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'A' repeated 101 times in the Page Title EN field -> The field does not hold 101 characters — input either stops at 100 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 100 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, ProposalPageAdminPage, 141224, 'page_title', 100, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141225
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141225_a_valid_quick_fact_label_is_saved_in_both_languages_and_rendered_o(page, browser):
    """ADO-141225 (P2). Verify that a valid quick-fact Label is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Proposal Type' in the quick-fact 1 Label EN field and 'نوع المقترح' in the Label AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first quick-fact tile -> The first quick-fact label reads 'Proposal Type' in English and 'نوع المقترح' in Arabic, above its value
    """
    bk.check_valid_renders(page, browser, QuickFactsTileAdminPage, 141225, 'label', 'Turnaround', ar='مدة', probe=probe, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141226
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141226_an_empty_quick_fact_label_blocks_the_save(page):
    """ADO-141226 (P2). Verify that an empty quick-fact Label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the quick-fact 1 Label EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the quick-fact Label EN field is flagged as required
    """
    ck.check_empty_refused(page, QuickFactsTileAdminPage, 141226, 'label', side='both', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141227
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141227_a_whitespace_only_quick_fact_label_blocks_the_save(page):
    """ADO-141227 (P3). Verify that a whitespace-only quick-fact Label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the quick-fact 1 Label EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the quick-fact Label EN field is flagged as required
    """
    ck.check_whitespace_refused(page, QuickFactsTileAdminPage, 141227, 'label', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141228
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141228_a_quick_fact_label_of_exactly_60_characters_is_accepted_and_render(page, browser):
    """ADO-141228 (P3). Verify that a quick-fact Label of exactly 60 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'B' repeated exactly 60 times in the quick-fact 1 Label EN field -> The 60-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first quick-fact tile on the English page in a fresh logged-out browser context -> The first quick-fact label renders all 60 'B' characters with none truncated
    """
    bk.check_limit_exact(page, browser, QuickFactsTileAdminPage, 141228, 'label', 60, files=FILES[QuickFactsTileAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141229
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141229_a_quick_fact_label_longer_than_60_characters_is_not_accepted(page, browser):
    """ADO-141229 (P3). Verify that a quick-fact Label longer than 60 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'B' repeated 61 times in the quick-fact 1 Label EN field -> The field does not hold 61 characters — input either stops at 60 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 60 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, QuickFactsTileAdminPage, 141229, 'label', 60, files=FILES[QuickFactsTileAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141230
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141230_a_valid_quick_fact_value_is_saved_in_both_languages_and_rendered_o(page, browser):
    """ADO-141230 (P2). Verify that a valid quick-fact Value is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Research or Study' in the quick-fact 1 Value EN field and 'بحث أو دراسة' in the Value AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first quick-fact tile -> The first quick-fact value reads 'Research or Study' in English and 'بحث أو دراسة' in Arabic, below its label
    """
    bk.check_valid_renders(page, browser, QuickFactsTileAdminPage, 141230, 'value', 'QCTEST-141230 Ten Working Days', ar='عشرة أيام', probe=probe, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141231
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141231_an_empty_quick_fact_value_blocks_the_save(page):
    """ADO-141231 (P2). Verify that an empty quick-fact Value blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the quick-fact 1 Value EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the quick-fact Value EN field is flagged as required
    """
    ck.check_empty_refused(page, QuickFactsTileAdminPage, 141231, 'value', side='both', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141232
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141232_a_whitespace_only_quick_fact_value_blocks_the_save(page):
    """ADO-141232 (P3). Verify that a whitespace-only quick-fact Value blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the quick-fact 1 Value EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the quick-fact Value EN field is flagged as required
    """
    ck.check_whitespace_refused(page, QuickFactsTileAdminPage, 141232, 'value', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141233
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141233_a_quick_fact_value_of_exactly_120_characters_is_accepted_and_rende(page, browser):
    """ADO-141233 (P3). Verify that a quick-fact Value of exactly 120 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'C' repeated exactly 120 times in the quick-fact 1 Value EN field -> The 120-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first quick-fact tile on the English page in a fresh logged-out browser context -> The first quick-fact value renders all 120 'C' characters with none truncated and the tile wraps within the quick-facts container
    """
    bk.check_limit_exact(page, browser, QuickFactsTileAdminPage, 141233, 'value', 120, files=FILES[QuickFactsTileAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141234
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141234_a_quick_fact_value_longer_than_120_characters_is_not_accepted(page, browser):
    """ADO-141234 (P3). Verify that a quick-fact Value longer than 120 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'C' repeated 121 times in the quick-fact 1 Value EN field -> The field does not hold 121 characters — input either stops at 120 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 120 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, QuickFactsTileAdminPage, 141234, 'value', 120, files=FILES[QuickFactsTileAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141235
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141235_a_valid_section_title_is_saved_in_both_languages_and_drives_both_t(page, browser):
    """ADO-141235 (P2). Verify that a valid Section Title is saved in both languages and drives both the heading and the index entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Service information' in the Section 2 Title EN field and 'معلومات الخدمة' in the Title AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read both the section heading and the sticky index entry -> The English page shows the section heading 'Service information' and the index entry '02 Service information'; the Arabic page shows 'معلومات الخدمة' in both places
    """
    bk.check_valid_renders(page, browser, SectionIndexEntryAdminPage, 141235, 'section_title', 'Overview', ar='نظرة عامة', probe=probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141236
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141236_an_empty_section_title_blocks_the_save(page):
    """ADO-141236 (P2). Verify that an empty Section Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Section 2 Title EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Section Title EN field is flagged as required
    """
    ck.check_empty_refused(page, SectionIndexEntryAdminPage, 141236, 'section_title', side='both', files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141237
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141237_a_whitespace_only_section_title_blocks_the_save(page):
    """ADO-141237 (P3). Verify that a whitespace-only Section Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the Section 2 Title EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Section Title EN field is flagged as required
    """
    ck.check_whitespace_refused(page, SectionIndexEntryAdminPage, 141237, 'section_title', files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141238
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141238_a_section_title_of_exactly_100_characters_is_accepted_and_rendered(page, browser):
    """ADO-141238 (P3). Verify that a Section Title of exactly 100 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'D' repeated exactly 100 times in the Section 2 Title EN field -> The 100-character value is accepted with no validation error and the record saves
      2. Publish the record and read the section heading and the sticky index entry on the English page in a fresh logged-out browser context -> Both the section heading and the '02' index entry render all 100 'D' characters with none truncated
    """
    bk.check_limit_exact(page, browser, SectionIndexEntryAdminPage, 141238, 'section_title', 100, files=FILES[SectionIndexEntryAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141239
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141239_a_section_title_longer_than_100_characters_is_not_accepted(page, browser):
    """ADO-141239 (P3). Verify that a Section Title longer than 100 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'D' repeated 101 times in the Section 2 Title EN field -> The field does not hold 101 characters — input either stops at 100 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 100 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, SectionIndexEntryAdminPage, 141239, 'section_title', 100, files=FILES[SectionIndexEntryAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141240
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141240_a_valid_info_card_title_is_saved_in_both_languages_and_rendered_on(page, browser):
    """ADO-141240 (P2). Verify that a valid Info Card Title is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Clear research focus' in the info card 1 Title EN field and 'موضوع بحثي واضح' in the Title AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first Overview info card -> The first info card title reads 'Clear research focus' in English and 'موضوع بحثي واضح' in Arabic
    """
    bk.check_valid_renders(page, browser, OverviewInfoCardAdminPage, 141240, 'card_title', 'Research Scope', ar='نطاق البحث', probe=probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141241
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141241_an_empty_info_card_title_blocks_the_save(page):
    """ADO-141241 (P2). Verify that an empty Info Card Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the info card 1 Title EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Info Card Title EN field is flagged as required
    """
    ck.check_empty_refused(page, OverviewInfoCardAdminPage, 141241, 'card_title', side='both', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141242
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141242_a_whitespace_only_info_card_title_blocks_the_save(page):
    """ADO-141242 (P3). Verify that a whitespace-only Info Card Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the info card 1 Title EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Info Card Title EN field is flagged as required
    """
    ck.check_whitespace_refused(page, OverviewInfoCardAdminPage, 141242, 'card_title', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141243
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141243_an_info_card_title_of_exactly_100_characters_is_accepted_and_rende(page, browser):
    """ADO-141243 (P3). Verify that an Info Card Title of exactly 100 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'E' repeated exactly 100 times in the info card 1 Title EN field -> The 100-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first info card on the English page in a fresh logged-out browser context -> The first info card title renders all 100 'E' characters wrapped inside the 256px card with none truncated
    """
    bk.check_limit_exact(page, browser, OverviewInfoCardAdminPage, 141243, 'card_title', 100, files=FILES[OverviewInfoCardAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141244
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141244_an_info_card_title_longer_than_100_characters_is_not_accepted(page, browser):
    """ADO-141244 (P3). Verify that an Info Card Title longer than 100 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'E' repeated 101 times in the info card 1 Title EN field -> The field does not hold 101 characters — input either stops at 100 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 100 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, OverviewInfoCardAdminPage, 141244, 'card_title', 100, files=FILES[OverviewInfoCardAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141245
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141245_a_valid_information_group_label_is_saved_in_both_languages_and_ren(page, browser):
    """ADO-141245 (P2). Verify that a valid Information Group Label is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Preparing your proposal' in the group 1 Label EN field and 'إعداد المقترح البحثي' in the Label AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first information group label in section 02 -> The first group label reads 'Preparing your proposal' in English and 'إعداد المقترح البحثي' in Arabic, rendered in Cairo 700 14px/22px #A66F43
    """
    bk.check_valid_renders(page, browser, InformationGroupAdminPage, 141245, 'group_label', 'Eligibility', ar='الأهلية', probe=probe, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141246
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141246_an_empty_information_group_label_blocks_the_save(page):
    """ADO-141246 (P2). Verify that an empty Information Group Label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the group 1 Label EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Information Group Label EN field is flagged as required
    """
    ck.check_empty_refused(page, InformationGroupAdminPage, 141246, 'group_label', side='both', files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141247
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141247_a_whitespace_only_information_group_label_blocks_the_save(page):
    """ADO-141247 (P3). Verify that a whitespace-only Information Group Label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the group 1 Label EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Information Group Label EN field is flagged as required
    """
    ck.check_whitespace_refused(page, InformationGroupAdminPage, 141247, 'group_label', files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141248
@pytest.mark.xdist_group("pfr_service-information-group")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141248_an_information_group_label_of_exactly_120_characters_is_accepted_a(page, browser):
    """ADO-141248 (P3). Verify that an Information Group Label of exactly 120 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'F' repeated exactly 120 times in the group 1 Label EN field -> The 120-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first group label on the English page in a fresh logged-out browser context -> The group label renders all 120 'F' characters in Cairo 700 14px/22px #A66F43 with none truncated
    """
    bk.check_limit_exact(page, browser, InformationGroupAdminPage, 141248, 'group_label', 120, files=FILES[InformationGroupAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141249
@pytest.mark.xdist_group("pfr_service-information-group")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141249_an_information_group_label_longer_than_120_characters_is_not_accep(page, browser):
    """ADO-141249 (P3). Verify that an Information Group Label longer than 120 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'F' repeated 121 times in the group 1 Label EN field -> The field does not hold 121 characters — input either stops at 120 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 120 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, InformationGroupAdminPage, 141249, 'group_label', 120, files=FILES[InformationGroupAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141250
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141250_a_valid_group_item_bullet_label_is_saved_in_both_languages_and_ren(pfr_bed, browser, page):
    """ADO-141250 (P2). Verify that a valid Group Item bullet label is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'The proposed research title or topic.' in the group 1 bullet 1 Label EN rich-text field and 'عنوان البحث أو الموضوع المقترح.' in the Label AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first bullet of the first information group -> The first bullet reads 'The proposed research title or topic.' in English and 'عنوان البحث أو الموضوع المقترح.' in Arabic, in Cairo 400 14px/22px #343432

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141250(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141251
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141251_an_empty_group_item_bullet_label_blocks_the_save(page):
    """ADO-141251 (P2). Verify that an empty Group Item bullet label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the group 1 bullet 1 Label EN rich-text field so it contains no content -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Group Item Label EN field is flagged as required
    """
    ck.check_empty_refused(page, GroupItemAdminPage, 141251, 'item_label', side='both', files=FILES[GroupItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141252
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141252_a_whitespace_only_group_item_bullet_label_blocks_the_save(page):
    """ADO-141252 (P3). Verify that a whitespace-only Group Item bullet label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the group 1 bullet 1 Label EN rich-text field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Group Item Label EN field is flagged as required
    """
    ck.check_whitespace_refused(page, GroupItemAdminPage, 141252, 'item_label', files=FILES[GroupItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141253
@pytest.mark.skip(reason='N/A: no character limit is applied to rich-text fields (team decision 2026-10-01)')
def test_141253_a_group_item_bullet_label_of_exactly_300_characters_is_accepted_an(page):
    """ADO-141253 (P3). Verify that a Group Item bullet label of exactly 300 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'G' repeated exactly 300 times in the group 1 bullet 1 Label EN field -> The 300-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first bullet on the English page in a fresh logged-out browser context -> The bullet renders all 300 'G' characters wrapped inside the 884px content width with none truncated

    Disposition: skip - N/A: no character limit is applied to rich-text fields (team decision 2026-10-01)
    """
    pass


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141254
@pytest.mark.skip(reason='N/A: no character limit is applied to rich-text fields (team decision 2026-10-01)')
def test_141254_a_group_item_bullet_label_longer_than_300_characters_is_not_accept(page):
    """ADO-141254 (P3). Verify that a Group Item bullet label longer than 300 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'G' repeated 301 times in the group 1 bullet 1 Label EN field -> The field does not hold 301 characters — input either stops at 300 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 300 characters is persisted to the record

    Disposition: skip - N/A: no character limit is applied to rich-text fields (team decision 2026-10-01)
    """
    pass


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141255
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141255_a_valid_resource_title_is_saved_in_both_languages_and_rendered_on(page, browser):
    """ADO-141255 (P2). Verify that a valid Resource Title is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Research Proposal Template' in the resource 1 Title EN field and 'نموذج المقترح البحثي' in the Title AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first resource card -> The first resource card title reads 'Research Proposal Template' in English and 'نموذج المقترح البحثي' in Arabic, in Cairo 600 16px/24px #343432
    """
    bk.check_valid_renders(page, browser, ResourceItemAdminPage, 141255, 'resource_title', 'Research Proposal Template', ar='نموذج المقترح', probe=probe, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141256
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141256_an_empty_resource_title_blocks_the_save(page):
    """ADO-141256 (P2). Verify that an empty Resource Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the resource 1 Title EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Resource Title EN field is flagged as required
    """
    ck.check_empty_refused(page, ResourceItemAdminPage, 141256, 'resource_title', side='both', files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141257
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141257_a_whitespace_only_resource_title_blocks_the_save(page):
    """ADO-141257 (P3). Verify that a whitespace-only Resource Title blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the resource 1 Title EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Resource Title EN field is flagged as required
    """
    ck.check_whitespace_refused(page, ResourceItemAdminPage, 141257, 'resource_title', files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141258
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141258_a_resource_title_of_exactly_200_characters_is_accepted_and_rendere(page, browser):
    """ADO-141258 (P3). Verify that a Resource Title of exactly 200 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'H' repeated exactly 200 times in the resource 1 Title EN field -> The 200-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first resource card on the English page in a fresh logged-out browser context -> The resource card title renders all 200 'H' characters wrapped inside the 740px card title area with none truncated, and the 'Download' button stays visible
    """
    bk.check_limit_exact(page, browser, ResourceItemAdminPage, 141258, 'resource_title', 200, files=FILES[ResourceItemAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141259
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141259_a_resource_title_longer_than_200_characters_is_not_accepted(page, browser):
    """ADO-141259 (P3). Verify that a Resource Title longer than 200 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'H' repeated 201 times in the resource 1 Title EN field -> The field does not hold 201 characters — input either stops at 200 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 200 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, ResourceItemAdminPage, 141259, 'resource_title', 200, files=FILES[ResourceItemAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141260
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141260_a_valid_resource_download_label_is_saved_in_both_languages_and_ren(page, browser):
    """ADO-141260 (P2). Verify that a valid resource Download Label is saved in both languages and rendered on the button

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Download' in the resource 1 Download Label EN field and 'تحميل' in the Download Label AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first resource card's button label -> The button on the first resource card reads 'Download' in English and 'تحميل' in Arabic, in Cairo 600 14px/22px #4A4A49 centre-aligned
    """
    bk.check_valid_renders(page, browser, ResourceItemAdminPage, 141260, 'download_label', 'Download PDF', ar='تنزيل', probe=probe, files=FILES[ResourceItemAdminPage],
                           # b9: the label IS the download button, which renders only for a resource holding a file
                           extra={'resource_file': VALID_PDF})


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141261
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141261_an_empty_resource_download_label_blocks_the_save(page):
    """ADO-141261 (P2). Verify that an empty resource Download Label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the resource 1 Download Label EN field so it contains no characters -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Download Label EN field is flagged as required
    """
    ck.check_empty_refused(page, ResourceItemAdminPage, 141261, 'download_label', side='both', files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141262
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141262_a_whitespace_only_resource_download_label_blocks_the_save(page):
    """ADO-141262 (P3). Verify that a whitespace-only resource Download Label blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the resource 1 Download Label EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Download Label EN field is flagged as required
    """
    ck.check_whitespace_refused(page, ResourceItemAdminPage, 141262, 'download_label', files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141263
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141263_a_resource_download_label_of_exactly_40_characters_is_accepted_and(page, browser):
    """ADO-141263 (P3). Verify that a resource Download Label of exactly 40 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the character 'J' repeated exactly 40 times in the resource 1 Download Label EN field -> The 40-character value is accepted with no validation error and the record saves
      2. Publish the record and read the first resource card's button on the English page in a fresh logged-out browser context -> The button label renders all 40 'J' characters with none truncated and the button remains clickable
    """
    bk.check_limit_exact(page, browser, ResourceItemAdminPage, 141263, 'download_label', 40, files=FILES[ResourceItemAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141264
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141264_a_resource_download_label_longer_than_40_characters_is_not_accepte(page, browser):
    """ADO-141264 (P3). Verify that a resource Download Label longer than 40 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to enter the character 'J' repeated 41 times in the resource 1 Download Label EN field -> The field does not hold 41 characters — input either stops at 40 characters or the value is flagged as exceeding the limit
      2. Attempt to save the record -> No value longer than 40 characters is persisted to the record
    """
    bk.check_limit_over(page, browser, ResourceItemAdminPage, 141264, 'download_label', 40, files=FILES[ResourceItemAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141265
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141265_a_valid_hero_description_is_saved_in_both_languages_and_rendered_o(page):
    """ADO-141265 (P2). Verify that a valid Hero Description is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Propose an economic or business-related research topic for consideration by Qatar Chamber's Research & Studies Department and access supporting templates and guidance.' in the Hero Description EN rich-text fiel... -> Both rich-text values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the hero description -> The English hero description renders the full authored sentence in Cairo 400 16px/24px #FFFFFF at 70% opacity and the Arabic hero description renders the full Arabic sentence right-aligned

    Note: Admin half only: SINGLETON publish
    """
    ck.check_valid_persists(page, ProposalPageAdminPage, 141265, 'hero_description', 'QCTEST-141265 hero description', ar='وصف اختبار', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141266
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141266_an_empty_hero_description_blocks_the_save(page):
    """ADO-141266 (P2). Verify that an empty Hero Description blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Hero Description EN rich-text field so it contains no content -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Hero Description EN field is flagged as required
    """
    ck.check_empty_refused(page, ProposalPageAdminPage, 141266, 'hero_description', side='both', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141267
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141267_a_whitespace_only_hero_description_blocks_the_save(page):
    """ADO-141267 (P3). Verify that a whitespace-only Hero Description blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the Hero Description EN rich-text field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Hero Description EN field is flagged as required
    """
    ck.check_whitespace_refused(page, ProposalPageAdminPage, 141267, 'hero_description', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141268
@lb.gate("99886")
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141268_a_valid_section_body_is_saved_in_both_languages_and_rendered_on_th(page, browser):
    """ADO-141268 (P2). Verify that a valid Section Body is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the authored Overview body text in the Section 1 Body EN rich-text field and 'تمكّن خدمة مقترح بحث في غرفة قطر الشركات والباحثين والجهات المهتمة من تقديم مقترحات لموضوعات بحثية اقتصادية وتجارية ليتم دراستها من ق... -> Both rich-text values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the Overview body -> The English Overview body opens with 'Qatar Chamber's Proposal for Research service enables businesses, researchers, and interested stakeholders to propose economic and business-related topics for c' in Cairo 400 16px...

    Live (B11, user-approved 2026-10-04 for record 99886): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    lc.pfr_141268(page, browser, OverviewInfoCardAdminPage)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141269
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141269_an_empty_section_body_blocks_the_save(page):
    """ADO-141269 (P2). Verify that an empty Section Body blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Section 1 Body EN rich-text field so it contains no content -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Section Body EN field is flagged as required
    """
    ck.check_empty_refused(page, OverviewInfoCardAdminPage, 141269, 'overview_body', side='both', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141270
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141270_a_whitespace_only_section_body_blocks_the_save(page):
    """ADO-141270 (P3). Verify that a whitespace-only Section Body blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the Section 1 Body EN rich-text field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Section Body EN field is flagged as required
    """
    ck.check_whitespace_refused(page, OverviewInfoCardAdminPage, 141270, 'overview_body', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141271
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141271_a_valid_info_card_description_is_saved_in_both_languages_and_rende(page, browser):
    """ADO-141271 (P2). Verify that a valid Info Card Description is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Define the proposed topic and the issue or opportunity the research should examine.' in the info card 1 Description EN field and 'حدّد الموضوع المقترح والقضية أو الفرصة التي ينبغي أن يتناولها البحث.' in the AR ... -> Both rich-text values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first info card description -> The first info card description reads 'Define the proposed topic and the issue or opportunity the research should examine.' in Cairo 400 14px/22px #7C7B7B in English and the Arabic sentence right-aligned in Arabic
    """
    bk.check_valid_renders(page, browser, OverviewInfoCardAdminPage, 141271, 'card_description', 'QCTEST-141271 card description', ar='وصف اختبار', probe=probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141272
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141272_an_empty_info_card_description_blocks_the_save(page):
    """ADO-141272 (P2). Verify that an empty Info Card Description blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the info card 1 Description EN rich-text field so it contains no content -> The field is left empty
      2. Attempt to save the record -> The save is blocked and the Info Card Description EN field is flagged as required
    """
    ck.check_empty_refused(page, OverviewInfoCardAdminPage, 141272, 'card_description', side='both', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141273
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141273_a_whitespace_only_info_card_description_blocks_the_save(page):
    """ADO-141273 (P3). Verify that a whitespace-only Info Card Description blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the info card 1 Description EN rich-text field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Info Card Description EN field is flagged as required
    """
    ck.check_whitespace_refused(page, OverviewInfoCardAdminPage, 141273, 'card_description', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141274
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141274_a_valid_information_group_intro_is_saved_in_both_languages_and_ren(page, browser):
    """ADO-141274 (P2). Verify that a valid Information Group Intro is saved in both languages and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'A clear and well-supported proposal helps communicate the importance and intended purpose of the suggested research topic. The proposal should include:' in the group 1 Intro EN field and 'يساعد المقترح الواضح و... -> Both rich-text values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the first group intro -> The English group intro renders the full sentence in Cairo 400 14px/22px #343432 above the six bullets, and the Arabic intro renders right-aligned above its bullets
    """
    bk.check_valid_renders(page, browser, InformationGroupAdminPage, 141274, 'group_intro', 'QCTEST-141274 group intro', ar='مقدمة اختبار', probe=probe, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141275
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141275_a_valid_hero_banner_image_under_2_mb_is_accepted_and_rendered_on_t(page):
    """ADO-141275 (P2). Verify that a valid hero banner image under 2 MB is accepted and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload QCTEST-130949-hero.jpg (850 KB JPG) into the Hero Banner Image field -> The file is accepted with no validation error and a thumbnail of QCTEST-130949-hero.jpg is shown in the field
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context and inspect the hero background -> The hero renders QCTEST-130949-hero.jpg behind the gradient overlay, the image request returns HTTP 200, and the hero eyebrow, title and description stay legible over it

    Note: Admin half only: SINGLETON publish
    """
    ck.check_file_accepted(page, ProposalPageAdminPage, 141275, 'hero_banner', VALID_JPG, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141276
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141276_a_hero_banner_image_of_a_disallowed_file_type_is_rejected(page):
    """ADO-141276 (P2). Verify that a hero banner image of a disallowed file type is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload QCTEST-130949-hero.bmp (400 KB BMP) into the Hero Banner Image field -> The upload is rejected with a file-type validation error and no thumbnail is attached
      2. Attempt to save the record -> The Hero Banner Image field still holds the previously attached image and no BMP is persisted
      3. Open the published English page in a fresh logged-out browser context -> The live hero still renders the previously published banner image
    """
    ck.check_file_refused(page, ProposalPageAdminPage, 141276, 'hero_banner', BAD_BMP, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141277
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141277_a_hero_banner_image_of_2_mb_or_more_is_rejected(page):
    """ADO-141277 (P2). Verify that a hero banner image of 2 MB or more is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload QCTEST-130949-hero-large.jpg (3 MB JPG) into the Hero Banner Image field -> The upload is rejected with a file-size validation error and no thumbnail is attached
      2. Attempt to save the record -> The Hero Banner Image field still holds the previously attached image and no 3 MB file is persisted
    """
    ck.check_file_refused(page, ProposalPageAdminPage, 141277, 'hero_banner', BIG_JPG, files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141278
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141278_a_valid_pdf_of_5_mb_or_less_is_accepted_on_a_resource_item_and_ser(page):
    """ADO-141278 (P1). Verify that a valid PDF of 5 MB or less is accepted on a resource item and served from the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload QCTEST-130949-template.pdf (200 KB PDF) into the resource 1 File field -> The file is accepted with no validation error and QCTEST-130949-template.pdf is attached to the resource item
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and click the first resource card's 'Download' button -> The download returns QCTEST-130949-template.pdf with HTTP 200 and the file opens as a valid PDF

    Note: Admin half: the PDF is attached and persists.
    """
    ck.check_file_accepted(page, ResourceItemAdminPage, 141278, 'resource_file', VALID_PDF, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141279
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141279_a_resource_file_of_a_disallowed_type_is_rejected(page):
    """ADO-141279 (P2). Verify that a resource file of a disallowed type is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload QCTEST-130949-template.docx (150 KB DOCX) into the resource 1 File field -> The upload is rejected with a file-type validation error stating that only PDF files are allowed, and the DOCX is not attached
      2. Attempt to save the record -> The resource item still holds its previously attached PDF and no DOCX is persisted
      3. Open the published English page in a fresh logged-out browser context and click the first resource card's 'Download' button -> The download still returns the previously published PDF, not a DOCX
    """
    ck.check_file_refused(page, ResourceItemAdminPage, 141279, 'resource_file', BAD_EXE, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141280
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141280_a_resource_file_larger_than_5_mb_is_rejected(page):
    """ADO-141280 (P2). Verify that a resource file larger than 5 MB is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload QCTEST-130949-template-6mb.pdf (6 MB PDF) into the resource 1 File field -> The upload is rejected with a file-size validation error and the 6 MB file is not attached
      2. Attempt to save the record -> The resource item still holds its previously attached 200 KB PDF and the card metadata still reads '200 KB'
    """
    bk.check_oversize_refused(page, ResourceItemAdminPage, 141280, 'resource_file', BIG_PDF, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141281
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141281_the_resource_file_type_is_auto_captured_from_the_uploaded_file_and(page):
    """ADO-141281 (P2). Verify that the resource File Type is auto-captured from the uploaded file and is not editable

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload QCTEST-130949-template.pdf into the resource 1 File field and read the File Type field without typing into it -> The File Type field is populated automatically with 'PDF' without any manual entry
      2. Attempt to type the value 'DOCX' into the File Type field -> The field does not accept keyboard input — it stays 'PDF'
      3. Publish the record and read the first resource card on the published English page in a fresh logged-out browser context -> The resource card renders the file type 'PDF' in Cairo 400 14px/22px #A8A8A7
    """
    bk.check_autocaptured(page, ResourceItemAdminPage, 141281, 'file_type', files=FILES[ResourceItemAdminPage], upload=('resource_file', VALID_PDF))


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141282
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141282_the_resource_file_size_is_auto_captured_from_the_uploaded_file_and(page):
    """ADO-141282 (P2). Verify that the resource File Size is auto-captured from the uploaded file and is not editable

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload QCTEST-130949-template.pdf (200 KB) into the resource 1 File field and read the File Size field without typing into it -> The File Size field is populated automatically with '200 KB' without any manual entry
      2. Attempt to type the value '10 MB' into the File Size field -> The field does not accept keyboard input — it stays '200 KB'
      3. Publish the record and read the first resource card on the published English page in a fresh logged-out browser context -> The resource card renders the file size '200 KB' in Cairo 400 14px/22px #A8A8A7, matching the size of the actual downloaded file
    """
    bk.check_autocaptured(page, ResourceItemAdminPage, 141282, 'file_size', files=FILES[ResourceItemAdminPage], upload=('resource_file', VALID_PDF))


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141283
@lb.gate("99844")
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141283_setting_the_page_status_to_published_makes_the_page_publicly_reach(page, browser):
    """ADO-141283 (P1). Verify that setting the Page Status to Published makes the page publicly reachable

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Page Status dropdown on the record and select 'Published' -> The dropdown offers Draft, Published and Unpublished and accepts the 'Published' selection
      2. Save the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context -> The anonymous request returns HTTP 200 and renders the hero title 'Proposal for Research'


    Live (B11, user-approved 2026-10-04 for record 99844): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    a9.pfr_opposite(page, browser, 141283)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141284
@lb.gate("99844")
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141284_setting_the_page_status_back_to_draft_removes_the_page_from_public(page, browser):
    """ADO-141284 (P1). Verify that setting the Page Status back to Draft removes the page from public view

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Page Status dropdown on the record and select 'Draft' -> The dropdown accepts the 'Draft' selection
      2. Save the record -> The record is saved with status Draft and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context -> The anonymous request no longer renders the page content — no hero title, sections or resource cards are returned


    Live (B11, user-approved 2026-10-04 for record 99844): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    lc.pfr_141284(page, browser, ProposalPageAdminPage)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141285
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141285_an_active_quick_fact_tile_renders_on_the_published_page(page, browser):
    """ADO-141285 (P2). Verify that an Active quick-fact tile renders on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of quick-fact tile 3 to Active and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the quick-facts strip -> Four quick-fact tiles render and the third reads 'Primary Audience' / 'Qatar Private Sector' in its configured order position

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, QuickFactsTileAdminPage, 141285, probe, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141286
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141286_an_inactive_quick_fact_tile_is_hidden_on_the_published_page(page, browser):
    """ADO-141286 (P2). Verify that an Inactive quick-fact tile is hidden on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of quick-fact tile 3 to Inactive and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the quick-facts strip -> Only three quick-fact tiles render — 'Proposal Type', 'Research Focus' and 'Responsible Department' — with no 'Primary Audience' tile and no empty slot left in the strip

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_inactive_hidden(page, browser, QuickFactsTileAdminPage, 141286, probe, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141287
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141287_an_active_section_renders_on_the_published_page_with_its_index_ent(page, browser):
    """ADO-141287 (P2). Verify that an Active section renders on the published page with its index entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of section 3 to Active and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the page body and the sticky index -> The Downloadable resources section renders with its badge, heading, intro and both resource cards, and the sticky index shows the entry '03 Downloadable resources'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, SectionIndexEntryAdminPage, 141287, probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141288
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141288_an_inactive_section_is_hidden_on_the_published_page_together_with(page, browser):
    """ADO-141288 (P2). Verify that an Inactive section is hidden on the published page together with its index entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of section 3 to Inactive and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the page body and the sticky index -> The Downloadable resources section does not render and no resource card or 'Download' button is present; the sticky index lists only '01 Overview' and '02 Service information'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_inactive_hidden(page, browser, SectionIndexEntryAdminPage, 141288, probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141289
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141289_an_active_overview_info_card_renders_on_the_published_page(page, browser):
    """ADO-141289 (P2). Verify that an Active Overview info card renders on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of info card 2 to Active and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the Overview info cards -> Three info cards render and the second reads 'Business guidance' with the description 'Identify the economic sector or business area connected to the proposed study.'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, OverviewInfoCardAdminPage, 141289, probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141290
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141290_an_inactive_overview_info_card_is_hidden_on_the_published_page(page, browser):
    """ADO-141290 (P2). Verify that an Inactive Overview info card is hidden on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of info card 2 to Inactive and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the Overview info cards -> Only two info cards render — 'Clear research focus' and 'Contact our experts' — side by side with no gap where the 'Business guidance' card used to be

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_inactive_hidden(page, browser, OverviewInfoCardAdminPage, 141290, probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141291
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141291_an_active_information_group_renders_on_the_published_page(page, browser):
    """ADO-141291 (P2). Verify that an Active information group renders on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of information group 2 to Active and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 02 -> Both groups render: 'Preparing your proposal' with its six bullets, followed by 'Supporting information' with its intro and four bullets

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, InformationGroupAdminPage, 141291, probe, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141292
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141292_an_inactive_information_group_is_hidden_on_the_published_page(page, browser):
    """ADO-141292 (P2). Verify that an Inactive information group is hidden on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of information group 2 to Inactive and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 02 -> Only 'Preparing your proposal' and its six bullets render; the label 'Supporting information' and its four bullets are absent, and the Downloadable resources section follows the last bullet with no blank gap

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_inactive_hidden(page, browser, InformationGroupAdminPage, 141292, probe, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141293
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141293_an_active_information_group_item_renders_as_a_bullet_on_the_publis(pfr_bed, browser, page):
    """ADO-141293 (P2). Verify that an Active information group item renders as a bullet on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of group 1 bullet 5 to Active and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the bullets of 'Preparing your proposal' -> Six bullets render and the fifth reads 'The expected value or potential benefit of the study.' in Cairo 400 14px/22px #343432

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141293(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141294
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141294_an_inactive_information_group_item_is_hidden_on_the_published_page(pfr_bed, browser, page):
    """ADO-141294 (P2). Verify that an Inactive information group item is hidden on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of group 1 bullet 5 to Inactive and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the bullets of 'Preparing your proposal' -> Five bullets render, the text 'The expected value or potential benefit of the study.' is absent from the group, and the remaining bullets stay in their configured order with no empty list row

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141294(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141295
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141295_an_active_downloadable_resource_item_renders_with_a_working_downlo(page, browser):
    """ADO-141295 (P2). Verify that an Active downloadable resource item renders with a working Download button

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of resource item 2 to Active and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 03 -> Two resource cards render and the second reads 'Research Proposal Guidelines' with 'PDF' and '200 KB'
      3. Click the 'Download' button on the 'Research Proposal Guidelines' card -> The download returns QCTEST-130949-guidelines.pdf with HTTP 200

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, ResourceItemAdminPage, 141295, probe, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141296
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141296_an_inactive_downloadable_resource_item_is_hidden_on_the_published(page, browser):
    """ADO-141296 (P2). Verify that an Inactive downloadable resource item is hidden on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of resource item 2 to Inactive and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 03 -> Only the 'Research Proposal Template' card renders; no card titled 'Research Proposal Guidelines' and no second 'Download' button is present, and the section closes directly after the first card

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_inactive_hidden(page, browser, ResourceItemAdminPage, 141296, probe, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141297
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141297_quick_fact_tiles_render_in_the_order_set_by_their_display_order_va(page, browser):
    """ADO-141297 (P3). Verify that quick-fact tiles render in the order set by their Display Order values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the quick-fact Display Order values to 1, 2, 3 and 4 as listed and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the quick-facts strip left to right -> The tiles render in the order 'Proposal Type', 'Research Focus', 'Primary Audience', 'Responsible Department', matching the configured display order exactly

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, QuickFactsTileAdminPage, 141297, OPEN, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141298
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141298_a_zero_or_negative_quick_fact_display_order_is_rejected(page):
    """ADO-141298 (P3). Verify that a zero or negative quick-fact Display Order is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0 in the quick-fact 1 Display Order field and attempt to save the record -> The save is blocked and the Display Order field is flagged as requiring a positive integer; 0 is not persisted
      2. Enter -1 in the same field and attempt to save the record -> The save is blocked again and -1 is not persisted; the field retains its previous valid value
    """
    ck.check_value_refused(page, QuickFactsTileAdminPage, 141298, 'display_order', '0', short='zero', files=FILES[QuickFactsTileAdminPage])
    ck.check_value_refused(page, QuickFactsTileAdminPage, 141298, 'display_order', '-1', short='neg', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141299
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141299_sections_render_in_the_order_set_by_their_display_order_values(page, browser):
    """ADO-141299 (P2). Verify that sections render in the order set by their Display Order values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the section Display Order values to 1, 2 and 3 as listed and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the sticky index and the section order down the page -> The sections render top to bottom as Overview, Service information, Downloadable resources and the sticky index numerals read 01, 02, 03 against those same titles

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, SectionIndexEntryAdminPage, 141299, OPEN, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141300
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141300_a_zero_or_negative_section_display_order_is_rejected(page):
    """ADO-141300 (P3). Verify that a zero or negative section Display Order is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0 in the section 2 Display Order field and attempt to save the record -> The save is blocked and the Display Order field is flagged as requiring a positive integer; 0 is not persisted
      2. Enter -2 in the same field and attempt to save the record -> The save is blocked again and -2 is not persisted; the section keeps its previous order value
    """
    ck.check_value_refused(page, SectionIndexEntryAdminPage, 141300, 'display_order', '0', short='zero', files=FILES[SectionIndexEntryAdminPage])
    ck.check_value_refused(page, SectionIndexEntryAdminPage, 141300, 'display_order', '-1', short='neg', files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141301
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141301_overview_info_cards_render_in_the_order_set_by_their_display_order(page, browser):
    """ADO-141301 (P3). Verify that Overview info cards render in the order set by their Display Order values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the info card Display Order values to 1, 2 and 3 as listed and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the three info cards left to right -> The cards render in the order 'Clear research focus', 'Business guidance', 'Contact our experts', matching the configured display order exactly

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, OverviewInfoCardAdminPage, 141301, OPEN, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141302
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141302_a_zero_or_negative_info_card_display_order_is_rejected(page):
    """ADO-141302 (P3). Verify that a zero or negative info card Display Order is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0 in the info card 1 Display Order field and attempt to save the record -> The save is blocked and the Display Order field is flagged as requiring a positive integer; 0 is not persisted
      2. Enter -3 in the same field and attempt to save the record -> The save is blocked again and -3 is not persisted; the card keeps its previous order value
    """
    ck.check_value_refused(page, OverviewInfoCardAdminPage, 141302, 'display_order', '0', short='zero', files=FILES[OverviewInfoCardAdminPage])
    ck.check_value_refused(page, OverviewInfoCardAdminPage, 141302, 'display_order', '-1', short='neg', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141303
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141303_information_groups_render_in_the_order_set_by_their_display_order(page, browser):
    """ADO-141303 (P3). Verify that information groups render in the order set by their Display Order values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the information group Display Order values to 1 and 2 as listed and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 02 top to bottom -> 'Preparing your proposal' renders first with its six bullets and 'Supporting information' renders second with its four bullets, matching the configured display order

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, InformationGroupAdminPage, 141303, OPEN, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141304
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141304_a_zero_or_negative_information_group_display_order_is_rejected(page):
    """ADO-141304 (P3). Verify that a zero or negative information group Display Order is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0 in the information group 2 Display Order field and attempt to save the record -> The save is blocked and the Display Order field is flagged as requiring a positive integer; 0 is not persisted
      2. Enter -1 in the same field and attempt to save the record -> The save is blocked again and -1 is not persisted; the group keeps its previous order value
    """
    ck.check_value_refused(page, InformationGroupAdminPage, 141304, 'display_order', '0', short='zero', files=FILES[InformationGroupAdminPage])
    ck.check_value_refused(page, InformationGroupAdminPage, 141304, 'display_order', '-1', short='neg', files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141305
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141305_information_group_items_render_as_bullets_in_the_order_set_by_thei(pfr_bed, browser, page):
    """ADO-141305 (P3). Verify that information group items render as bullets in the order set by their Display Order values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the group 1 bullet Display Order values to 1, 2, 3, 4, 5 and 6 in the authored sequence and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the bullets of 'Preparing your proposal' top to bottom -> The bullets render in the order 'The proposed research title or topic.', 'A brief description of the issue or opportunity.', 'The purpose and main objectives of the research.', 'The relevant economic sector or busines...

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141305(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141306
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141306_a_zero_or_negative_group_item_display_order_is_rejected(page):
    """ADO-141306 (P3). Verify that a zero or negative group item Display Order is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0 in the group 1 bullet 2 Display Order field and attempt to save the record -> The save is blocked and the Display Order field is flagged as requiring a positive integer; 0 is not persisted
      2. Enter -4 in the same field and attempt to save the record -> The save is blocked again and -4 is not persisted; the bullet keeps its previous order value
    """
    ck.check_value_refused(page, GroupItemAdminPage, 141306, 'display_order', '0', short='zero', files=FILES[GroupItemAdminPage])
    ck.check_value_refused(page, GroupItemAdminPage, 141306, 'display_order', '-1', short='neg', files=FILES[GroupItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141307
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141307_downloadable_resource_items_render_in_the_order_set_by_their_displ(page, browser):
    """ADO-141307 (P3). Verify that downloadable resource items render in the order set by their Display Order values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the resource Display Order values to 1 and 2 as listed and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the resource cards top to bottom -> The 'Research Proposal Template' card renders first and the 'Research Proposal Guidelines' card second, matching the configured display order

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, ResourceItemAdminPage, 141307, OPEN, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141308
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141308_a_zero_or_negative_resource_display_order_is_rejected(page):
    """ADO-141308 (P3). Verify that a zero or negative resource Display Order is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0 in the resource 2 Display Order field and attempt to save the record -> The save is blocked and the Display Order field is flagged as requiring a positive integer; 0 is not persisted
      2. Enter -1 in the same field and attempt to save the record -> The save is blocked again and -1 is not persisted; the resource item keeps its previous order value
    """
    ck.check_value_refused(page, ResourceItemAdminPage, 141308, 'display_order', '0', short='zero', files=FILES[ResourceItemAdminPage])
    ck.check_value_refused(page, ResourceItemAdminPage, 141308, 'display_order', '-1', short='neg', files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141310
@lb.gate("99844")
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141310_the_hero_banner_image_can_be_replaced_on_a_published_page_and_the(page, browser):
    """ADO-141310 (P2). Verify that the hero banner image can be replaced on a published page and the new image is served

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the record in Object Authoring while its status is Published and replace the Hero Banner Image with QCTEST-130949-hero-v2.png -> The PNG is accepted with no validation error and the field thumbnail updates to QCTEST-130949-hero-v2.png
      2. Save the record and read its page status -> The record is saved, the Liferay generic success toast is displayed, and the page status is still Published
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context and inspect the hero background image request -> The hero background request resolves to QCTEST-130949-hero-v2.png with HTTP 200 and the previous QCTEST-130949-hero.jpg is no longer requested


    Live (B11, user-approved 2026-10-04 for record 99844): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    lc.pfr_141310(page, browser, ProposalPageAdminPage, VALID_PNG)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141315
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141315_a_new_quick_fact_tile_can_be_added_and_appears_on_the_published_pa(page, browser):
    """ADO-141315 (P2). Verify that a new quick-fact tile can be added and appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new quick-fact tile with label 'QCTEST Turnaround' / 'مدة الإنجاز', value '10 working days' / '10 أيام عمل', display order 5 and Active status -> The new tile is created and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the quick-facts strip -> Five quick-fact tiles render and the fifth reads 'QCTEST Turnaround' / '10 working days' after 'Responsible Department'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, QuickFactsTileAdminPage, 141315, probe, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141316
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141316_an_existing_quick_fact_tile_can_be_edited_and_the_change_appears_o(page, browser):
    """ADO-141316 (P2). Verify that an existing quick-fact tile can be edited and the change appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open quick-fact tile 2 and change its Value EN from 'Economy & Business' to 'QCTEST Economy and Trade' -> The edit is accepted and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the second quick-fact tile -> The second quick-fact tile reads label 'Research Focus' with value 'QCTEST Economy and Trade' and the old value 'Economy & Business' is no longer present

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_edit_published_updates(page, browser, QuickFactsTileAdminPage, 141316, probe, 'value', 'QCTEST-141316-edited', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141317
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141317_a_quick_fact_tile_can_be_deleted_and_disappears_from_the_published(page, browser):
    """ADO-141317 (P2). Verify that a quick-fact tile can be deleted and disappears from the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Locate the quick-fact tile whose Label EN is exactly 'QCTEST Turnaround' and confirm its label before deleting -> The tile with label 'QCTEST Turnaround' is positively identified by title, not by row position
      2. Delete that tile and publish the record -> The tile is removed and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and read the quick-facts strip -> Four quick-fact tiles render — 'Proposal Type', 'Research Focus', 'Primary Audience', 'Responsible Department' — and no tile labelled 'QCTEST Turnaround' remains

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_delete_removes(page, browser, QuickFactsTileAdminPage, 141317, probe, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141318
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141318_reordering_quick_fact_tiles_changes_their_order_on_the_published_p(page, browser):
    """ADO-141318 (P3). Verify that reordering quick-fact tiles changes their order on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of 'Responsible Department' to 1 and of 'Proposal Type' to 4 and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the quick-facts strip left to right -> The tiles render in the order 'Responsible Department', 'Research Focus', 'Primary Audience', 'Proposal Type' — reflecting the swapped display order

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, QuickFactsTileAdminPage, 141318, OPEN, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141319
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141319_a_new_section_can_be_added_and_appears_with_its_own_sticky_index_e(page, browser):
    """ADO-141319 (P2). Verify that a new section can be added and appears with its own sticky index entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new section titled 'QCTEST Additional guidance' / 'إرشادات إضافية' with body 'QCTEST body copy for the additional guidance section.', display order 4 and Active status -> The new section is created and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the sticky index and the page body -> The sticky index lists four entries ending with '04 QCTEST Additional guidance' and the new section renders after Downloadable resources with the body 'QCTEST body copy for the additional guidance section.'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, SectionIndexEntryAdminPage, 141319, probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141320
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141320_an_existing_section_can_be_edited_and_the_change_appears_in_both_t(page, browser):
    """ADO-141320 (P2). Verify that an existing section can be edited and the change appears in both the heading and the index

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open section 1 and change its Title EN from 'Overview' to 'QCTEST Overview' -> The edit is accepted and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the section heading and the sticky index -> The section heading reads 'QCTEST Overview' and the index entry reads '01 QCTEST Overview'; the old label 'Overview' appears in neither place

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_edit_published_updates(page, browser, SectionIndexEntryAdminPage, 141320, probe, 'section_numbering', 'QCTEST-141320-edited', files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141321
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141321_a_section_can_be_deleted_and_disappears_with_its_sticky_index_entr(page, browser):
    """ADO-141321 (P2). Verify that a section can be deleted and disappears with its sticky index entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Locate the section whose Title EN is exactly 'QCTEST Additional guidance' and confirm its title before deleting -> The section is positively identified by title, not by row position
      2. Delete that section and publish the record -> The section is removed and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and read the sticky index and the page body -> The sticky index lists exactly three entries again and no section titled 'QCTEST Additional guidance' renders anywhere on the page

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_delete_removes(page, browser, SectionIndexEntryAdminPage, 141321, probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141322
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141322_reordering_sections_changes_the_rendered_section_sequence_while_ea(page, browser):
    """ADO-141322 (P3). Verify that reordering sections changes the rendered section sequence while each section keeps its authored numbering

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of 'Downloadable resources' to 1 and of 'Overview' to 3 and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the sticky index and the section order down the page -> The sticky index lists 'Downloadable resources' first, 'Service information' second and 'Overview' third and the sections render down the page in that same sequence; each entry still displays its own authored Section ...

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, SectionIndexEntryAdminPage, 141322, OPEN, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141323
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141323_a_new_overview_info_card_can_be_added_and_appears_on_the_published(page, browser):
    """ADO-141323 (P2). Verify that a new Overview info card can be added and appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new Overview info card titled 'QCTEST Submission channel' / 'قناة التقديم' with the description 'QCTEST description for the submission channel card.', display order 4 and Active status -> The new card is created and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the Overview info cards -> Four info cards render and the fourth reads 'QCTEST Submission channel' with the description 'QCTEST description for the submission channel card.'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, OverviewInfoCardAdminPage, 141323, probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141324
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141324_an_existing_overview_info_card_can_be_edited_and_the_change_appear(page, browser):
    """ADO-141324 (P2). Verify that an existing Overview info card can be edited and the change appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open info card 3 and change its Title EN from 'Contact our experts' to 'QCTEST Contact our experts' -> The edit is accepted and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the third Overview info card -> The third info card title reads 'QCTEST Contact our experts' and the old title 'Contact our experts' is no longer rendered

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_edit_published_updates(page, browser, OverviewInfoCardAdminPage, 141324, probe, 'card_title', 'QCTEST Contact our experts', files=FILES[OverviewInfoCardAdminPage])  # b9: the case edits the card Title EN, not the section badge


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141325
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141325_an_overview_info_card_can_be_deleted_and_disappears_from_the_publi(page, browser):
    """ADO-141325 (P2). Verify that an Overview info card can be deleted and disappears from the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Locate the info card whose Title EN is exactly 'QCTEST Submission channel' and confirm its title before deleting -> The card is positively identified by title, not by row position
      2. Delete that card and publish the record -> The card is removed and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and read the Overview info cards -> Three info cards render — 'Clear research focus', 'Business guidance', 'Contact our experts' — and no card titled 'QCTEST Submission channel' remains

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_delete_removes(page, browser, OverviewInfoCardAdminPage, 141325, probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141326
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141326_reordering_overview_info_cards_changes_their_order_on_the_publishe(page, browser):
    """ADO-141326 (P3). Verify that reordering Overview info cards changes their order on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of 'Contact our experts' to 1 and of 'Clear research focus' to 3 and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the three info cards left to right -> The cards render in the order 'Contact our experts', 'Business guidance', 'Clear research focus'

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, OverviewInfoCardAdminPage, 141326, OPEN, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141327
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141327_a_new_information_group_can_be_added_and_appears_in_the_service_in(page, browser):
    """ADO-141327 (P2). Verify that a new information group can be added and appears in the Service information section

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new information group labelled 'QCTEST Review process' / 'آلية المراجعة' with the intro 'QCTEST intro copy for the review process group.', display order 3 and Active status -> The new group is created and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read section 02 -> Three groups render and the third label reads 'QCTEST Review process' in Cairo 700 14px/22px #A66F43 with the intro 'QCTEST intro copy for the review process group.' beneath it

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, InformationGroupAdminPage, 141327, probe, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141328
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141328_an_existing_information_group_can_be_edited_and_the_change_appears(page, browser):
    """ADO-141328 (P2). Verify that an existing information group can be edited and the change appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open information group 2 and change its Label EN from 'Supporting information' to 'QCTEST Supporting information' -> The edit is accepted and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the second group label in section 02 -> The second group label reads 'QCTEST Supporting information' and the old label 'Supporting information' is no longer rendered

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_edit_published_updates(page, browser, InformationGroupAdminPage, 141328, probe, 'group_label', 'QCTEST Supporting information', files=FILES[InformationGroupAdminPage])  # b9: the case edits the group Label EN, not the section badge


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141329
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141329_an_information_group_can_be_deleted_and_disappears_with_all_of_its(page, browser):
    """ADO-141329 (P2). Verify that an information group can be deleted and disappears with all of its bullets

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Locate the information group whose Label EN is exactly 'QCTEST Review process' and confirm its label before deleting -> The group is positively identified by label, not by row position
      2. Delete that group and publish the record -> The group is removed and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and read section 02 -> Two groups render — 'Preparing your proposal' and 'Supporting information' — and neither the label 'QCTEST Review process' nor its intro appears anywhere in the section

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_delete_removes(page, browser, InformationGroupAdminPage, 141329, probe, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141330
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141330_reordering_information_groups_changes_their_order_on_the_published(page, browser):
    """ADO-141330 (P3). Verify that reordering information groups changes their order on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of 'Supporting information' to 1 and of 'Preparing your proposal' to 2 and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 02 top to bottom -> 'Supporting information' renders first with its four bullets and 'Preparing your proposal' renders second with its six bullets

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, InformationGroupAdminPage, 141330, OPEN, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141331
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141331_a_new_bullet_can_be_added_to_an_information_group_and_appears_on_t(pfr_bed, browser, page):
    """ADO-141331 (P2). Verify that a new bullet can be added to an information group and appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new bullet to the 'Preparing your proposal' group with the label 'QCTEST The proposed timeline for the study.' / 'الجدول الزمني المقترح للدراسة.', display order 7 and Active status -> The new bullet is created and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the bullets of 'Preparing your proposal' -> Seven bullets render and the seventh reads 'QCTEST The proposed timeline for the study.' in Cairo 400 14px/22px #343432

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141331(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141332
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141332_an_existing_bullet_can_be_edited_and_the_change_appears_on_the_pub(pfr_bed, browser, page):
    """ADO-141332 (P2). Verify that an existing bullet can be edited and the change appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open bullet 1 of the 'Supporting information' group and change its Label EN to 'QCTEST Existing reports or studies.' -> The edit is accepted and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the bullets of 'Supporting information' -> The first bullet of the group reads 'QCTEST Existing reports or studies.' and the old text 'Existing reports or studies.' is no longer rendered

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141332(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141333
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141333_a_bullet_can_be_deleted_and_disappears_from_the_published_page(pfr_bed, browser, page):
    """ADO-141333 (P2). Verify that a bullet can be deleted and disappears from the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Locate the bullet whose Label EN is exactly 'QCTEST The proposed timeline for the study.' and confirm its text before deleting -> The bullet is positively identified by its text, not by row position
      2. Delete that bullet and publish the record -> The bullet is removed and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and read the bullets of 'Preparing your proposal' -> Six bullets render and the text 'QCTEST The proposed timeline for the study.' appears nowhere on the page

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141333(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141334
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141334_reordering_bullets_within_an_information_group_changes_their_order(pfr_bed, browser, page):
    """ADO-141334 (P3). Verify that reordering bullets within an information group changes their order on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of 'Available data, references, or supporting information.' to 1 and of 'The proposed research title or topic.' to 6 and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the bullets of 'Preparing your proposal' top to bottom -> The first bullet reads 'Available data, references, or supporting information.' and the sixth reads 'The proposed research title or topic.', with the middle four bullets unchanged

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141334(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141335
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141335_a_new_downloadable_resource_item_can_be_added_and_appears_with_a_w(page, browser):
    """ADO-141335 (P2). Verify that a new downloadable resource item can be added and appears with a working Download button

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new resource item titled 'QCTEST Research Proposal Checklist' / 'قائمة تحقق المقترح البحثي' with QCTEST-130949-checklist.pdf attached, download label 'Download' / 'تحميل', display order 3 and Active status -> The new resource item is created with the PDF attached and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context, read section 03 and click the new card's 'Download' button -> Three resource cards render, the third reads 'QCTEST Research Proposal Checklist' with 'PDF' and '300 KB', and its download returns QCTEST-130949-checklist.pdf with HTTP 200

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, ResourceItemAdminPage, 141335, probe, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141336
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141336_an_existing_downloadable_resource_item_can_be_edited_and_the_chang(page, browser):
    """ADO-141336 (P2). Verify that an existing downloadable resource item can be edited and the change appears on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open resource item 2 and change its Title EN to 'QCTEST Research Proposal Guidelines' -> The edit is accepted and the Liferay generic success toast is displayed
      2. Publish the record -> The record saves with status Published
      3. Open the published English page in a fresh logged-out browser context and read the second resource card -> The second resource card title reads 'QCTEST Research Proposal Guidelines', its metadata still reads 'PDF' and '200 KB', and the old title is no longer rendered

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_edit_published_updates(page, browser, ResourceItemAdminPage, 141336, probe, 'resource_title', 'QCTEST Research Proposal Guidelines', files=FILES[ResourceItemAdminPage],
                                     extra={'resource_file': VALID_PDF})  # b9: the case edits the resource Title EN, on a card holding a file


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141337
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141337_a_downloadable_resource_item_can_be_deleted_and_disappears_from_th(page, browser):
    """ADO-141337 (P2). Verify that a downloadable resource item can be deleted and disappears from the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Locate the resource item whose Title EN is exactly 'QCTEST Research Proposal Checklist' and confirm its title before deleting -> The resource item is positively identified by title, not by row position
      2. Delete that resource item and publish the record -> The item is removed and the Liferay generic success toast is displayed
      3. Open the published English page in a fresh logged-out browser context and read section 03 -> Two resource cards render and no card titled 'QCTEST Research Proposal Checklist' and no third 'Download' button is present

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_delete_removes(page, browser, ResourceItemAdminPage, 141337, probe, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141338
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141338_reordering_downloadable_resource_items_changes_their_order_on_the(page, browser):
    """ADO-141338 (P3). Verify that reordering downloadable resource items changes their order on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of 'Research Proposal Guidelines' to 1 and of 'Research Proposal Template' to 2 and publish the record -> The record saves with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read the resource cards top to bottom -> The 'Research Proposal Guidelines' card renders first and the 'Research Proposal Template' card second, each still showing its own 'PDF' and '200 KB' metadata and its own file on download

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_order_follows(page, browser, ResourceItemAdminPage, 141338, OPEN, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141339
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141339_a_missing_arabic_translation_on_a_non_mandatory_field_falls_back_t(page, browser):
    """ADO-141339 (P2). Verify that a missing Arabic translation on a non-mandatory field falls back to the default language

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave the Arabic description of Overview info card 3 empty while its English description reads 'Include available data, references, or other information that helps explain the topic and its expected value.' and publis... -> The record is published and the Liferay generic success toast is displayed
      2. Open /ar/our-services/information/proposal-for-research in a fresh logged-out browser context -> The Arabic page renders with dir="rtl" and all other Arabic content intact
      3. Read the third Overview info card -> The third info card renders the English description 'Include available data, references, or other information that helps explain the topic and its expected value.' as the fallback value; the card is not blank and no r...

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_ar_fallback(page, browser, InformationGroupAdminPage, 141339, 'group_intro', 'QCTEST-141339 group intro', probe_ar, files=FILES[InformationGroupAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130949
@pytest.mark.tc_141340
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141340_publishing_is_blocked_when_a_mandatory_arabic_value_is_missing_whi(page):
    """ADO-141340 (P1). Verify that publishing is blocked when a mandatory Arabic value is missing while Arabic is enabled

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Page Title AR field so it contains no characters, leaving the Page Title EN as 'Proposal for Research' -> The Arabic field is empty while the English field still holds its value
      2. Click Publish -> The publish is blocked with a validation message identifying the missing mandatory Arabic value, and the record status does not change to Published
      3. Open /ar/our-services/information/proposal-for-research in a fresh logged-out browser context -> The Arabic page still shows the previously published title 'اقتراح بحث أو دراسة'; no page with a blank Arabic title is served
    """
    bk.check_ar_required_refused(page, ProposalPageAdminPage, 141340, 'page_title', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141341
@pytest.mark.skipif(not AUDIT_LOG_LOCATED, reason='CONDITIONAL - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141341_an_audit_log_record_is_written_for_a_content_change_on_the_proposa(page, browser):
    """ADO-141341 (P2). Verify that an audit-log record is written for a content change on the Proposal for Research page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as the Site Content Editor, change the Overview section Body EN to 'QCTEST-130949 audit trail check.' and publish the record, noting the local time of the publish -> The change is saved, the record is published and the Liferay generic success toast is displayed
      2. Open the Control Panel audit log and filter for the Proposal for Research page record -> The audit log returns entries for the Proposal for Research page record
      3. Read the most recent audit entry -> The most recent entry records the publish action against the Proposal for Research record, attributed to the Site Content Editor account, with a timestamp matching the publish time

    Disposition: conditional - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)
    """
    a9.pfr_141341(page, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.edge
@pytest.mark.pbi_130949
@pytest.mark.tc_141342
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141342_the_rendered_resource_order_stays_deterministic_when_two_downloada(page, browser):
    """ADO-141342 (P3). Verify that the rendered resource order stays deterministic when two downloadable resource items share the same Display Order value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Display Order of both 'Research Proposal Template' and 'Research Proposal Guidelines' to 1 and attempt to save the record -> The system behaves deterministically: either the duplicate value is rejected with a validation message identifying the conflict, or both items are accepted
      2. If the save is accepted, publish the record and open the published English page in a fresh logged-out browser context -> If accepted and published, both cards render — neither item is silently dropped and no card renders twice
      3. Reload the page three times and record the order of the two resource cards on each load -> The two cards appear in the same relative order on all three reloads; the order does not vary between renders

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    bk.check_duplicate_order_stable(page, browser, ResourceItemAdminPage, 141342, OPEN, files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.edge
@pytest.mark.pbi_130949
@pytest.mark.tc_141343
@pytest.mark.skipif(not GROUP_ITEM_RELATION_READ, reason="CONDITIONAL - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)")
@pytest.mark.xdist_group("pfr_service-information-group-item")
def test_141343_an_active_information_group_renders_without_an_empty_bullet_list_w(pfr_bed, browser, page):
    """ADO-141343 (P3). Verify that an Active information group renders without an empty bullet list when every one of its bullets is Inactive

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the Active Status of all four bullets in the 'Supporting information' group to Inactive while leaving the group itself Active, and publish the record -> The record saves and publishes with the Liferay generic success toast
      2. Open the published English page in a fresh logged-out browser context and read section 02 -> The group label 'Supporting information' and its intro 'Relevant supporting materials may be included to provide additional context for the proposed research topic.' render with no bullet list beneath them
      3. Inspect the vertical space between the group intro and the start of the Downloadable resources section -> No empty bullet markers, placeholder rows or blank vertical gap are left where the four bullets used to be; the Downloadable resources section follows the group intro directly

    Disposition: conditional - a Group Item (bullet) renders only inside an Information Group; the relationship field on the live Group Item form ('Group Items') has not been read live yet, so a QCTEST bullet cannot be attached to a QCTEST group - automate once that picker is read (read only)
    """
    a9.pfr_141343(pfr_bed, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.edge
@pytest.mark.pbi_130949
@pytest.mark.tc_141344
def test_141344_the_published_page_reports_a_broken_download_when_a_resource_pdf_i(page, browser):
    """ADO-141344 (P2). Verify that the published page reports a broken download when a resource PDF is deleted from Documents and Media after publishing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Publish the page with the 'Research Proposal Template' card pointing at QCTEST-130949-template.pdf and confirm the download works in a logged-out context -> The download returns QCTEST-130949-template.pdf with HTTP 200 before the deletion
      2. Delete QCTEST-130949-template.pdf from Liferay Documents & Media, confirming the target by its exact file name before deleting -> The file is positively identified by name and removed from Documents & Media
      3. Reload the published English page in a fresh logged-out browser context and click the 'Download' button on the 'Research Proposal Template' card -> The visitor is not left with a silent failure: either the card no longer offers a download, or the click returns a handled not-found response rather than an unhandled server error; the rest of the page, including the ...

    Disposition: skip - needs a real shared record mutated: the case deletes a file from Documents & Media, and Documents & Media deletion is off-limits to automation (engineer brief Step 2)
    """
    a9.pfr_141344(page, browser)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.edge
@pytest.mark.pbi_130949
@pytest.mark.tc_141345
@pytest.mark.skipif(not RESOURCE_SWAP_RULED, reason='CONDITIONAL - the case expects File Type / File Size to be re-captured on a live document swap, but both are free-text required fields on the live Resource Item form (read 2026-10-01) - needs a BA ruling, and the held-open-visitor half needs a second session across a publish')
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141345_a_visitor_holding_the_page_open_receives_the_replacement_document(page, browser):
    """ADO-141345 (P2). Verify that a visitor holding the page open receives the replacement document and its updated size after a live document swap

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In a logged-out browser context, load the published English page and leave it open on section 03 without reloading -> The visitor context shows the first resource card with 'PDF' and '200 KB'
      2. In a separate Control Panel session, replace the file on the 'Research Proposal Template' item with QCTEST-130949-template-v2.pdf and save, keeping the page status Published -> The replacement saves with the Liferay generic success toast and the page status remains Published throughout
      3. Without reloading, click the 'Download' button in the still-open visitor context -> The click from the stale page does not produce an unhandled error — it returns either the new QCTEST-130949-template-v2.pdf or a handled not-found response, never a broken or truncated file
      4. Reload the visitor page and read the first resource card's metadata, then click 'Download' again -> After reload the card reads 'PDF' and '1.2 MB' and the download returns QCTEST-130949-template-v2.pdf; the file type and file size shown match the file actually served

    Disposition: conditional - the case expects File Type / File Size to be re-captured on a live document swap, but both are free-text required fields on the live Resource Item form (read 2026-10-01) - needs a BA ruling, and the held-open-visitor half needs a second session across a publish
    """
    a9.pfr_resource_swap(page, browser, 141345, hold_open=True)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141346
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141346_a_valid_quick_fact_tile_icon_is_saved_and_rendered_on_the_publishe(page):
    """ADO-141346 (P2). Verify that a valid quick-fact tile Icon is saved and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log into https://qcdev.ihorizons.com/object-authoring as the Site Content Editor and open the QCTEST-130949-ProposalForResearch record, then open quick-fact tile 1 'Research Focus' -> Quick-fact tile 1 opens with the Icon field visible and marked as required
      2. Open the Icon picker, select the allowed-set icon 'search' and save the record -> The icon 'search' is accepted with no validation error and the record saves with the Liferay generic success toast
      3. Publish the record and open /en/our-services/information/proposal-for-research in a fresh logged-out browser context -> The 'Research Focus' quick-fact tile renders the 'search' icon above its label, and the icon element is present in the DOM with a non-empty source
    """
    ck.check_file_accepted(page, QuickFactsTileAdminPage, 141346, 'icon', VALID_PNG, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141347
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141347_a_quick_fact_tile_with_no_icon_selected_blocks_the_save(page):
    """ADO-141347 (P3). Verify that a quick-fact tile with no Icon selected blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open quick-fact tile 1 'Research Focus' in the QCTEST-130949-ProposalForResearch record and clear the selected Icon so the field is empty -> The Icon field shows no selected icon
      2. Attempt to save the record -> The save is blocked and the Icon field is flagged as required; no success toast is shown
    """
    ck.check_empty_refused(page, QuickFactsTileAdminPage, 141347, 'icon', side='both', files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141348
@pytest.mark.xdist_group("pfr_proposal-research-quick-facts-tile")
def test_141348_a_quick_fact_tile_icon_outside_the_allowed_icon_set_is_rejected(page):
    """ADO-141348 (P3). Verify that a quick-fact tile Icon outside the allowed icon set is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open quick-fact tile 1 'Research Focus' and attempt to supply the icon by uploading the file QCTEST-130949-icon.bmp instead of choosing from the allowed icon set -> The upload is rejected with a validation error stating the icon is not an allowed type, or the picker offers no way to supply a file outside the allowed icon set
      2. Attempt to save the record -> The tile retains its previously saved allowed-set icon and QCTEST-130949-icon.bmp is never stored against the tile

    Note: 'Outside the allowed icon set' is an upload of a type the Icon attachment does not accept (jpg/jpeg/png/svg, read live).
    """
    ck.check_file_refused(page, QuickFactsTileAdminPage, 141348, 'icon', BAD_BMP, files=FILES[QuickFactsTileAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141349
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141349_a_valid_overview_info_card_icon_is_saved_and_rendered_on_the_publi(page):
    """ADO-141349 (P2). Verify that a valid Overview info card Icon is saved and rendered on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the QCTEST-130949-ProposalForResearch record in Object Authoring as the Site Content Editor and open Overview info card 1 'Clear research focus' -> Info card 1 opens with the Card Icon field visible and marked as required
      2. Open the Card Icon picker, select the allowed-set icon 'target' and save the record -> The icon 'target' is accepted with no validation error and the record saves with the Liferay generic success toast
      3. Publish the record and open /en/our-services/information/proposal-for-research in a fresh logged-out browser context, then scroll to the Overview info cards -> The 'Clear research focus' card renders the 'target' icon above its title, followed by the title and the description, in that order
    """
    ck.check_file_accepted(page, OverviewInfoCardAdminPage, 141349, 'card_icon', VALID_PNG, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141350
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141350_an_overview_info_card_with_no_card_icon_selected_blocks_the_save(page):
    """ADO-141350 (P3). Verify that an Overview info card with no Card Icon selected blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Overview info card 1 'Clear research focus' in the QCTEST-130949-ProposalForResearch record and clear the selected Card Icon -> The Card Icon field shows no selected icon
      2. Attempt to save the record -> The save is blocked and the Card Icon field is flagged as required; no success toast is shown
    """
    ck.check_empty_refused(page, OverviewInfoCardAdminPage, 141350, 'card_icon', side='both', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141351
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141351_an_overview_info_card_icon_outside_the_allowed_icon_set_is_rejecte(page):
    """ADO-141351 (P3). Verify that an Overview info card Icon outside the allowed icon set is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Overview info card 1 'Clear research focus' and attempt to supply the Card Icon by uploading QCTEST-130949-icon.bmp instead of choosing from the allowed icon set -> The upload is rejected with a validation error stating the icon is not an allowed type, or the picker offers no way to supply a file outside the allowed icon set
      2. Attempt to save the record -> The card retains its previously saved allowed-set icon and QCTEST-130949-icon.bmp is never stored against the card

    Note: 'Outside the allowed icon set' is an upload of a type the Card Icon attachment does not accept (jpg/jpeg/png/svg, read live).
    """
    ck.check_file_refused(page, OverviewInfoCardAdminPage, 141351, 'card_icon', BAD_BMP, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141352
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141352_a_valid_section_badge_is_saved_in_both_languages_and_rendered_abov(page, browser):
    """ADO-141352 (P2). Verify that a valid Section Badge is saved in both languages and rendered above the section heading

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'About the service' in the Overview Section Badge EN field and 'عن الخدمة' in the Section Badge AR field -> Both values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English and Arabic published pages in a fresh logged-out browser context and read the badge above the Overview heading -> The English page renders 'About the service' in Cairo 400 12px/18px #911731 directly above the 'Overview' heading, and the Arabic page renders 'عن الخدمة' right-aligned above 'نظرة عامة'
    """
    bk.check_valid_renders(page, browser, OverviewInfoCardAdminPage, 141352, 'section_badge', 'Overview', ar='نظرة عامة', probe=probe, files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141353
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141353_an_empty_section_badge_blocks_the_save(page):
    """ADO-141353 (P3). Verify that an empty Section Badge blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Overview Section Badge EN field so it contains no characters -> The field is empty
      2. Attempt to save the record -> The save is blocked and the Section Badge EN field is flagged as required
    """
    ck.check_empty_refused(page, OverviewInfoCardAdminPage, 141353, 'section_badge', side='both', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141354
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141354_a_whitespace_only_section_badge_blocks_the_save(page):
    """ADO-141354 (P3). Verify that a whitespace-only Section Badge blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Type three space characters into the Overview Section Badge EN field -> The field contains only whitespace
      2. Attempt to save the record -> The save is blocked and the Section Badge EN field is flagged as required
    """
    ck.check_whitespace_refused(page, OverviewInfoCardAdminPage, 141354, 'section_badge', files=FILES[OverviewInfoCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141355
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141355_a_section_badge_of_exactly_100_characters_is_accepted_and_rendered(page, browser):
    """ADO-141355 (P3). Verify that a Section Badge of exactly 100 characters is accepted and rendered in full

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a string of exactly 100 'B' characters in the Overview Section Badge EN field and save the record -> The field accepts all 100 characters and the record saves with the Liferay generic success toast
      2. Publish the record and read the badge above the Overview heading on the English page in a fresh logged-out browser context -> The badge renders all 100 'B' characters above the Overview heading with none truncated
    """
    bk.check_limit_exact(page, browser, OverviewInfoCardAdminPage, 141355, 'section_badge', 100, files=FILES[OverviewInfoCardAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141356
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
def test_141356_a_section_badge_longer_than_100_characters_is_not_accepted(page, browser):
    """ADO-141356 (P3). Verify that a Section Badge longer than 100 characters is not accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Paste a string of 101 'B' characters into the Overview Section Badge EN field -> Either the field stops accepting input at 100 characters or the 101-character value is held pending validation
      2. Attempt to save the record and re-read the stored value -> The field does not accept a value longer than 100 characters: the save is blocked with the Section Badge EN field flagged as over the limit, or the stored value is exactly 100 characters
    """
    bk.check_limit_over(page, browser, OverviewInfoCardAdminPage, 141356, 'section_badge', 100, files=FILES[OverviewInfoCardAdminPage], probe=probe)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141357
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141357_a_valid_section_numbering_value_is_saved_and_rendered_as_the_stick(page, browser):
    """ADO-141357 (P2). Verify that a valid Section Numbering value is saved and rendered as the sticky index numeral

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open section 2 'Service information' in the QCTEST-130949-ProposalForResearch record and enter '02' in the Section Numbering field -> The value '02' is accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context and read the sticky index entry for Service information -> The sticky index entry reads '02 Service information', with the numeral matching the authored Section Numbering value exactly
    """
    bk.check_valid_renders(page, browser, SectionIndexEntryAdminPage, 141357, 'section_numbering', '77', ar='77', probe=probe, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141358
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141358_an_empty_section_numbering_blocks_the_save(page):
    """ADO-141358 (P3). Verify that an empty Section Numbering blocks the save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Section Numbering field of section 2 'Service information' so it contains no characters -> The field is empty
      2. Attempt to save the record -> The save is blocked and the Section Numbering field is flagged as required
    """
    ck.check_empty_refused(page, SectionIndexEntryAdminPage, 141358, 'section_numbering', side='both', files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141359
@pytest.mark.xdist_group("pfr_proposal-research-section-index-entry")
def test_141359_the_authored_section_numbering_is_preserved_when_sections_are_reor(page, browser):
    """ADO-141359 (P3). Verify that the authored Section Numbering is preserved when sections are reordered

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the QCTEST-130949-ProposalForResearch record and change the Display Order of 'Downloadable resources' to 2 and of 'Service information' to 3, leaving both Section Numbering values as authored ('03' and '02') -> Both Display Order values are accepted with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English published page in a fresh logged-out browser context and read the sticky index entries top to bottom together with their numerals -> The sections and index entries now render in the sequence Overview, Downloadable resources, Service information, and each entry still carries its AUTHORED numeral: '01 Overview', '03 Downloadable resources', '02 Servi...

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object. Each QCTEST section keeps its authored Section Numbering while the order changes.
    """
    bk.check_order_follows(page, browser, SectionIndexEntryAdminPage, 141359, OPEN, files=FILES[SectionIndexEntryAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141360
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141360_the_page_created_date_is_auto_captured_at_creation_and_is_not_edit(page):
    """ADO-141360 (P3). Verify that the page Created Date is auto-captured at creation and is not editable

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log into Object Authoring as the Site Content Editor, create the record QCTEST-130949-CreatedDate and note the wall-clock time at the moment of the first save -> The record is created and saved with the Liferay generic success toast; no Created Date was entered by the author
      2. Reopen the saved record and inspect the Created Date field -> The Created Date is populated automatically and matches the wall-clock time of the first save to the minute
      3. Attempt to type a different date into the Created Date field, then edit the Page Title to 'QCTEST-130949-CreatedDate v2', save, and re-read the Created Date -> The Created Date field is read-only and rejects the typed value, and after the title edit is saved the Created Date still shows the original creation timestamp unchanged
    """
    bk.check_autocaptured(page, ProposalPageAdminPage, 141360, 'created_date', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141361
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141361_the_page_last_modified_date_is_auto_updated_on_every_save_and_is_n(page):
    """ADO-141361 (P3). Verify that the page Last Modified Date is auto-updated on every save and is not editable

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the QCTEST-130949-ProposalForResearch record in Object Authoring as the Site Content Editor and record the current Last Modified Date value -> The current Last Modified Date is displayed on the record
      2. Attempt to type a different date into the Last Modified Date field -> The Last Modified Date field is read-only and rejects the typed value
      3. Change the Hero Eyebrow EN to 'QCTEST Economic Research Service', save the record and re-read the Last Modified Date -> The save succeeds with the Liferay generic success toast and the Last Modified Date has advanced to the time of this save, matching the wall-clock time to the minute and no longer equal to the previously recorded value
    """
    ck.check_modified_updates(page, ProposalPageAdminPage, 141361, 'eyebrow', 'QCTEST-141361 edited', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141362
@a9.a9_gate("99844")
@pytest.mark.skipif(not RICH_FORMAT_SCRIPTED, reason='CONDITIONAL - headings / bullets / inline hyperlinks are entered through the CKEditor toolbar, which this suite does not drive yet - automate once the toolbar path is scripted')
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141362_the_hero_description_rich_text_supports_headings_bullets_and_inlin(page, browser):
    """ADO-141362 (P2). Verify that the Hero Description rich text supports headings, bullets and inline hyperlinks on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Hero Description EN rich-text field, author a heading 'QCTEST Research scope', a bullet list with the items 'Economic topics' and 'Business topics', and a paragraph containing the inline hyperlink 'Research & S... -> The editor accepts the heading, the bullet list and the hyperlink with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context and inspect the hero description markup -> The hero description renders 'QCTEST Research scope' as a heading element, 'Economic topics' and 'Business topics' as two list items of a bullet list, and 'Research & Studies' as an anchor element whose href is https:...
      4. Click the 'Research & Studies' link in the hero description -> The browser navigates to https://qcdev.ihorizons.com/en/about

    Disposition: conditional - headings / bullets / inline hyperlinks are entered through the CKEditor toolbar, which this suite does not drive yet - automate once the toolbar path is scripted
    """
    a9.pfr_rich(page, browser, 141362)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141363
@a9.a9_gate("99886")
@pytest.mark.skipif(not RICH_FORMAT_SCRIPTED, reason='CONDITIONAL - headings / bullets / inline hyperlinks are entered through the CKEditor toolbar, which this suite does not drive yet - automate once the toolbar path is scripted')
@pytest.mark.xdist_group("pfr_overview-section-and-info-card")
def test_141363_the_overview_body_rich_text_supports_headings_paragraphs_bullets_a(page, browser):
    """ADO-141363 (P2). Verify that the Overview Body rich text supports headings, paragraphs, bullets and inline hyperlinks on the published page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Section 1 Body EN rich-text field, author a heading 'QCTEST How proposals are reviewed', two paragraphs, a bullet list with the items 'Submission', 'Review' and 'Feedback', and a paragraph containing the inline... -> The editor accepts the heading, both paragraphs, the bullet list and the hyperlink with no validation error
      2. Publish the record -> The record is saved with status Published and the Liferay generic success toast is displayed
      3. Open the English published page in a fresh logged-out browser context and inspect the Overview body markup -> The Overview body renders 'QCTEST How proposals are reviewed' as a heading element, the two paragraphs as separate paragraph elements, 'Submission', 'Review' and 'Feedback' as three list items of a bullet list, and 'c...
      4. Click the 'contact the department' link inside the Overview body -> The browser navigates to https://qcdev.ihorizons.com/en/contact-us

    Disposition: conditional - headings / bullets / inline hyperlinks are entered through the CKEditor toolbar, which this suite does not drive yet - automate once the toolbar path is scripted
    """
    a9.pfr_rich(page, browser, 141363)


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141365
@pytest.mark.xdist_group("pfr_proposal-for-research-page")
def test_141365_saving_the_page_with_no_hero_banner_attached_is_blocked(page):
    """ADO-141365 (P2). Verify that saving the page with no Hero Banner attached is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the QCTEST-130949-ProposalForResearch record in Object Authoring as the Site Content Editor and remove the attached hero banner image so the Hero Banner field is empty -> The Hero Banner field shows no attached image
      2. Attempt to save and publish the record -> The save/publish is blocked and the Hero Banner field is flagged as required; no success toast is shown and the previously published page continues to serve its existing hero banner
    """
    ck.check_empty_refused(page, ProposalPageAdminPage, 141365, 'hero_banner', side='both', files=FILES[ProposalPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141366
@pytest.mark.xdist_group("pfr_downloadable-resource-item")
def test_141366_saving_a_downloadable_resource_item_with_no_file_attached_is_block(page):
    """ADO-141366 (P2). Verify that saving a downloadable resource item with no file attached is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new downloadable resource item to the QCTEST-130949-ProposalForResearch record, set Resource Title EN to 'QCTEST-130949-NoFile', set Display Order 3 and Active Status Active, and leave the Resource File field empty -> The item is created in the editor with no file attached
      2. Attempt to save the record -> The save is blocked and the Resource File field is flagged as required; no resource card titled 'QCTEST-130949-NoFile' is created and none appears on the published page
    """
    ck.check_empty_refused(page, ResourceItemAdminPage, 141366, 'resource_file', side='both', files=FILES[ResourceItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_130949
@pytest.mark.tc_141367
@pytest.mark.xdist_group("pfr_service-information-group")
def test_141367_an_information_group_with_no_group_intro_is_saved_and_rendered_wit(page, browser):
    """ADO-141367 (P2). Verify that an information group with no Group Intro is saved and rendered with its label and bullets only

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open information group 2 'Supporting information' in the QCTEST-130949-ProposalForResearch record and clear both the Group Intro EN and the Group Intro AR rich-text fields -> Both Group Intro fields are empty and neither is flagged as required
      2. Save and publish the record -> The record saves and publishes successfully with the Liferay generic success toast
      3. Open /en/our-services/information/proposal-for-research in a fresh logged-out browser context and read the second information group in section 02 -> The group renders its label 'Supporting information' followed directly by its four bullets, with no intro paragraph and no empty intro block or extra vertical gap between the label and the first bullet

    Note: Re-expressed on disposable QCTEST records: the case's named live entries are QCDEMO content, which may only be read; the same behaviour is asserted on a QCTEST entry of the same object.
    """
    ck.check_editor_publish_public(page, browser, InformationGroupAdminPage, 141367, probe, files=FILES[InformationGroupAdminPage])

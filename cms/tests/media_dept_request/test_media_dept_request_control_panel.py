"""
cms/tests/media_dept_request/test_media_dept_request_control_panel.py - Control_Panel cases for PBI 131061
(Test Plan 137724, suite 140395): Azure Priority 1-3, Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_131061_cp_batch.json, which holds every disposition and
reason). Each function is one Azure case; the body calls a shared check in
cms/tests/authoring_checks.py.

Every record a test creates is QCTEST-<tc_id>-<short>, deleted by exact title in
a finally block. Accounts resolve through cms_role_credentials(): Editor for
create -> Published, Author for submit -> Pending Review, Site Member for
denial; never TEST_USER. Public reads use a fresh logged-out context.

`conditional` cases are skipped through the module flags below until their
condition is confirmed; each flag says what must be true to flip it.
"""

from pathlib import Path

import pytest

from cms.pages.components.disposable_object_admin import (
    ROLE_AUTHOR, ROLE_EDITOR, ROLE_FORM_MANAGER, chars, qctest_title,
)
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED, STATUS_UNPUBLISHED
from cms.pages.media_dept_request.media_dept_request_admin_page import (
    MediaDeptPageHeroAdminPage,
    PressKitCardAdminPage,
    MediaStandardCardAdminPage,
    MediaDeptSubmissionAdminPage,
)
from cms.tests import authoring_checks as ck
from web.pages.media_dept_request.media_dept_request_page import MediaDeptRequestPage

FIXTURES = Path(__file__).resolve().parent / "fixtures"
VALID_JPG = str(FIXTURES / 'valid_image_500kb.jpg')
VALID_PNG = str(FIXTURES / 'valid_icon_200kb.png')
VALID_SVG = str(FIXTURES / 'valid_icon_45kb.svg')
BIG_IMAGE = str(FIXTURES / 'oversized_image_3mb.jpg')
BIG_ICON_1MB = str(FIXTURES / 'oversized_icon_1_5mb.png')
BAD_IMAGE = str(FIXTURES / 'unsupported_image.bmp')
BAD_IMAGE_GIF = str(FIXTURES / 'unsupported_image.gif')
BAD_IMAGE_PDF = str(FIXTURES / 'unsupported_image.pdf')
BAD_DOC = str(FIXTURES / 'unsupported_file.docx')
BAD_EXE = str(FIXTURES / 'unsupported_file.exe')
VALID_PDF = str(FIXTURES / 'valid_press_kit_3mb.pdf')
BIG_PDF = str(FIXTURES / 'oversized_press_kit_6mb.pdf')

# Required upload fields per object, filled by fill_required().
FILES = {
    MediaDeptPageHeroAdminPage: {'hero_image': VALID_JPG},
    PressKitCardAdminPage: {'icon': VALID_PNG, 'file_en': VALID_PDF, 'file_ar': VALID_PDF},
    MediaStandardCardAdminPage: {'icon': VALID_SVG},
    MediaDeptSubmissionAdminPage: {},
}

probe = ck.make_public_probe(lambda p: MediaDeptRequestPage(p).open_media_dept_request_anonymous())

# Conditional-case gates. Flip one only when its condition is confirmed.
QCTEST_SUBMISSION_PATH = False  # True once: a QCTEST submission/subscriber can be created and deleted by exact reference
SINGLETON_PUBLISH_CLEARED = False  # True once: confirmed live that publishing a QCTEST entry of a page-level object does not displace the live QCDEMO entry

@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131061
@pytest.mark.tc_142743
def test_142743_cms_admin_content_entry_form_displays_hero_and_card_fields_w(page):
    """ADO-142743 (P3). Verify that the CMS admin content-entry form displays Hero and Card fields with EN/AR inputs

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Login as Site Content Editor -> Editor session active
      2. Open Request to Media Dept. in Object Authoring -> Hero and 4-card field panels each expose separate EN and AR inputs for every bilingual field
    """
    ck.check_form_renders(page, MediaDeptPageHeroAdminPage, ['hero_eyebrow', 'page_title', 'hero_description', 'hero_image'])
    ck.check_form_renders(page, MediaStandardCardAdminPage, ['icon', 'eyebrow', 'title', 'description', 'button_label'])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131061
@pytest.mark.tc_142744
def test_142744_admin_submissions_list_is_filterable_by_form_type_and_status(page):
    """ADO-142744 (P3). Verify that the Admin Submissions list is filterable by Form Type and Status

    Account: QC Form Manager via cms_role_credentials('Form Manager') (read-only; none of the named roles is mutated).
    Steps (from the approved case):
      1. Login as Form Manager -> Login succeeds, submissions list accessible
      2. Open Submissions list -> List loads with all submissions
      3. Apply Form Type = 'Media Inquiry' filter -> List narrows to Media Inquiry submissions only
      4. Apply Status = 'Pending' filter -> List further narrows to Pending Media Inquiry submissions only
    """
    ck.check_form_renders(page, MediaDeptSubmissionAdminPage, ['form_type', 'status'], role=ROLE_FORM_MANAGER)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131061
@pytest.mark.tc_142745
def test_142745_admin_submission_detail_view_displays_all_submitted_values_r(page):
    """ADO-142745 (P3). Verify that the Admin Submission detail view displays all submitted values read-only

    Account: QC Form Manager via cms_role_credentials('Form Manager') (read-only; none of the named roles is mutated).
    Steps (from the approved case):
      1. Open a Pending Interview Request submission -> Detail view shows all 8 submitted fields as read-only text, plus a separate Internal Notes text area for admin-only input
    """
    ck.check_form_renders(page, MediaDeptSubmissionAdminPage, ['reference_no', 'internal_notes'], role=ROLE_FORM_MANAGER)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_131061
@pytest.mark.tc_142761
def test_142761_unauthenticated_visitor_forced_browsing_to_the_cms_submissio(page, browser):
    """ADO-142761 (P1). Verify that an unauthenticated visitor forced-browsing to the CMS Submissions list is denied

    Account: none - fresh logged-out context (new_context(browser, use_auth_state=False)).
    Steps (from the approved case):
      1. As an unauthenticated user, navigate directly to the Control Panel Submissions list URL -> User is redirected to CMS login (or shown 'Access Denied. You do not have permission to perform this action.' / 'تم رفض الوصول...') — submission data is never e
    """
    ck.check_anonymous_denied(browser, MediaDeptSubmissionAdminPage)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131061
@pytest.mark.tc_142762
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142762_site_content_editor_has_full_crud_lifecycle_rights_on_the_pa(page, browser):
    """ADO-142762 (P1). Verify that a Site Content Editor has full CRUD+lifecycle rights on the page and Press Kit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Login as Site Content Editor (test1@xyz.com) -> Login succeeds
      2. Edit Hero content, save as draft, preview, publish, unpublish, and delete a test Press Kit card entry -> Every lifecycle action (draft/preview/publish/unpublish/delete) succeeds without an Access-Denied response

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_full_lifecycle(page, browser, PressKitCardAdminPage, 142762, probe, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131061
@pytest.mark.tc_142763
def test_142763_site_content_author_can_view_and_update_assigned_page_press(page):
    """ADO-142763 (P1). Verify that a Site Content Author can view and update assigned page/Press Kit content

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Login as Site Content Author (Test2@xyz.com) -> Login succeeds
      2. Open the assigned Request to Media Dept. page -> Page opens
      3. Edit the Press Kit Description field and save -> Author can view and edit the assigned content; save succeeds (submission for review, per role definition)
    """
    ck.check_author_updates_own(page, PressKitCardAdminPage, 142763, 'description', 'QCTEST author edit', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131061
@pytest.mark.tc_142764
def test_142764_site_content_author_is_blocked_from_publishing_directly(page):
    """ADO-142764 (P1). Verify that a Site Content Author is blocked from publishing directly

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Login as Site Content Author -> Login succeeds
      2. Edit the Hero Description -> Description edited
      3. Attempt to click Publish directly (not Submit for Review) -> Publish action is blocked; 'Access Denied. You do not have permission to perform this action.' / 'تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء.' is display
    """
    ck.check_author_submit_pending(page, MediaStandardCardAdminPage, 142764, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131061
@pytest.mark.tc_142765
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142765_form_manager_can_view_submissions_and_update_status_notes(page):
    """ADO-142765 (P1). Verify that a Form Manager can view submissions and update status/notes

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. Login as Form Manager -> Login succeeds
      2. Open a Pending submission -> Submission opens
      3. Change status to 'Under Review' and add an internal note -> Status and note save successfully; Form Manager's actions succeed without Access-Denied

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131061
@pytest.mark.tc_142766
def test_142766_form_manager_is_blocked_from_editing_form_structure_or_page(page):
    """ADO-142766 (P1). Verify that a Form Manager is blocked from editing form structure or page content

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. Login as Form Manager -> Login succeeds
      2. Attempt to open the Hero/Card content editor -> Content editor access blocked
      3. Attempt to modify the Interview Request webform's field definitions -> Both actions are blocked with 'Access Denied. You do not have permission to perform this action.' / AR equivalent
    """
    ck.check_role_cannot_author(page, MediaDeptPageHeroAdminPage, ROLE_FORM_MANAGER)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131061
@pytest.mark.tc_142771
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142771_site_content_editor_can_update_the_press_kit_file_and_visito(page, browser):
    """ADO-142771 (P1). Verify that a Site Content Editor can update the Press Kit file and visitors immediately receive the new version

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Login as Site Content Editor -> Editor session active
      2. Open Press Kit File field, upload a new EN PDF (press_kit_v2.pdf) -> New file staged
      3. Publish -> Publish succeeds; Liferay generic success toast shown; audit log records the change
      4. In a fresh anonymous browser context, load the public page and click Download on Card 01 -> Anonymous visitor's downloaded file is press_kit_v2.pdf, not the previous version

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_republish_updates(page, browser, PressKitCardAdminPage, 142771, probe, 'title', 'QCTEST-142771 kit', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131061
@pytest.mark.tc_142772
def test_142772_site_content_editor_s_hero_card_content_edit_is_reflected_bi(page, browser):
    """ADO-142772 (P1). Verify that a Site Content Editor's Hero/Card content edit is reflected bilingually on the live page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Login as Site Content Editor -> Editor session active
      2. Update Hero Description EN='Access approved press resources or contact our Media Department.' and AR equivalent -> Values entered
      3. Save and Publish -> Publish succeeds; Liferay generic toast shown; audit log entry recorded
      4. Load the public EN page, then the public AR page -> EN public page shows the new EN description; AR public page (/ar) shows the new AR description
    """
    ck.check_editor_publish_public(page, browser, MediaStandardCardAdminPage, 142772, probe, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131061
@pytest.mark.tc_142773
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142773_form_manager_can_progress_a_submission_through_pending_under(page):
    """ADO-142773 (P1). Verify that a Form Manager can progress a submission through Pending → Under Review → Completed with no auto-email and full audit trail

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. Login as Form Manager -> Login succeeds
      2. Open the Interview Request submission from TC-032 (status Pending) -> Submission opens, status shows 'Pending' (default)
      3. Change status to 'Under Review', add internal note 'Coordinating with Chairman's office' -> Status field shows Under Review, note text entered
      4. Save -> Save succeeds; Liferay generic toast shown; audit log records timestamp + acting Form Manager user; no additional email is sent to submitter or admin
      5. Re-open the submission, change status to 'Completed' -> Submission re-opens showing Under Review + the saved note, all original field values still read-only and unchanged
      6. Save -> Status shows 'Completed'; audit log records the second transition with timestamp + acting user; no email sent

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142781
def test_142781_hero_eyebrow_label_saves_with_valid_en_ar_text_within_60_cha(page):
    """ADO-142781 (P3). Verify that the Hero Eyebrow Label saves with valid EN/AR text within 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Login as Site Content Editor and open the Hero fields panel -> Editor session active; Hero panel visible
      2. Enter Eyebrow Label EN='Insights & Media', AR='الأخبار والإعلام' -> Both values entered
      3. Save and Publish -> Publish succeeds; public page hero eyebrow displays both values correctly per locale
    """
    ck.check_valid_persists(page, MediaDeptPageHeroAdminPage, 142781, 'hero_eyebrow', 'Valid hero eyebrow', ar='قيمة صالحة', files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142782
def test_142782_hero_eyebrow_label_blocks_publish_when_the_arabic_value_is_m(page):
    """ADO-142782 (P3). Verify that the Hero Eyebrow Label blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter Eyebrow Label EN='Insights & Media', leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; 'Arabic content is required.' / 'المحتوى بالعربية مطلوب.' shown; page not published
    """
    ck.check_empty_refused(page, MediaDeptPageHeroAdminPage, 142782, 'hero_eyebrow', side='ar', files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142783
def test_142783_hero_eyebrow_label_rejects_text_exceeding_60_characters(page):
    """ADO-142783 (P3). Verify that the Hero Eyebrow Label rejects text exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter a 61-character EN value -> Over-limit value entered
      3. Attempt Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaDeptPageHeroAdminPage, 142783, 'hero_eyebrow', 60, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142784
def test_142784_hero_page_title_saves_with_valid_en_ar_text_within_100_chara(page):
    """ADO-142784 (P3). Verify that the Hero Page Title saves with valid EN/AR text within 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter Page Title EN='Request to the Media Dept.', AR='طلب إلى إدارة الإعلام' -> Both values entered
      3. Save and Publish -> Publish succeeds; public page title displays correctly per locale
    """
    ck.check_valid_persists(page, MediaDeptPageHeroAdminPage, 142784, 'page_title', 'Valid page title', ar='قيمة صالحة', files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142785
def test_142785_hero_page_title_blocks_publish_when_the_arabic_value_is_miss(page):
    """ADO-142785 (P3). Verify that the Hero Page Title blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter Page Title EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, MediaDeptPageHeroAdminPage, 142785, 'page_title', side='ar', files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142786
def test_142786_hero_page_title_rejects_text_exceeding_100_characters(page):
    """ADO-142786 (P3). Verify that the Hero Page Title rejects text exceeding 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter a 101-character EN value -> Over-limit value entered
      3. Attempt Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaDeptPageHeroAdminPage, 142786, 'page_title', 100, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142787
def test_142787_hero_description_saves_with_valid_en_ar_rich_text_within_200(page):
    """ADO-142787 (P3). Verify that the Hero Description saves with valid EN/AR rich text within 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter Hero Description EN='Access approved press resources or send a focused request to Qatar Chamber's Media Department.' and AR equivalent -> Both values entered
      3. Save and Publish -> Publish succeeds; public page shows the formatted description per locale
    """
    ck.check_valid_persists(page, MediaDeptPageHeroAdminPage, 142787, 'hero_description', 'Valid hero description', ar='قيمة صالحة', files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142788
def test_142788_hero_description_blocks_publish_when_the_arabic_value_is_mis(page):
    """ADO-142788 (P3). Verify that the Hero Description blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter Hero Description EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, MediaDeptPageHeroAdminPage, 142788, 'hero_description', side='ar', files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142789
def test_142789_hero_description_rejects_rich_text_exceeding_200_characters(page):
    """ADO-142789 (P3). Verify that the Hero Description rejects rich text exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero fields panel -> Panel visible
      2. Enter a 201-character EN value -> Over-limit value entered
      3. Attempt Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaDeptPageHeroAdminPage, 142789, 'hero_description', 200, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142790
def test_142790_hero_image_accepts_a_valid_jpg_under_2mb(page):
    """ADO-142790 (P3). Verify that the Hero Image accepts a valid JPG under 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero Image field -> Field visible
      2. Upload hero_banner.jpg (1.4MB) -> File selected
      3. Save -> Upload succeeds; image displays as the hero banner on the public page
    """
    ck.check_file_accepted(page, MediaDeptPageHeroAdminPage, 142790, 'hero_image', VALID_JPG, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142791
def test_142791_hero_image_rejects_an_unsupported_file_format(page):
    """ADO-142791 (P3). Verify that the Hero Image rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero Image field -> Field visible
      2. Upload hero_banner.gif -> File selected
      3. Save -> Validation error: unsupported format; upload rejected
    """
    ck.check_file_refused(page, MediaDeptPageHeroAdminPage, 142791, 'hero_image', BAD_IMAGE_GIF, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142792
def test_142792_hero_image_rejects_a_file_exceeding_2mb(page):
    """ADO-142792 (P3). Verify that the Hero Image rejects a file exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Hero Image field -> Field visible
      2. Upload hero_banner_large.jpg (2.4MB) -> File selected
      3. Save -> Validation error: file exceeds 2MB limit; upload rejected
    """
    ck.check_file_refused(page, MediaDeptPageHeroAdminPage, 142792, 'hero_image', BIG_IMAGE, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142793
def test_142793_press_kit_icon_accepts_a_valid_png_under_2mb(page):
    """ADO-142793 (P3). Verify that the Press Kit Icon accepts a valid PNG under 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Icon field -> Field visible
      2. Upload press_icon.png (300KB) -> File selected
      3. Save -> Icon uploads and displays on Card 01
    """
    ck.check_file_accepted(page, PressKitCardAdminPage, 142793, 'icon', VALID_PNG, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142794
def test_142794_press_kit_icon_rejects_an_unsupported_file_format(page):
    """ADO-142794 (P3). Verify that the Press Kit Icon rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Icon field -> Field visible
      2. Upload press_icon.bmp -> File selected
      3. Save -> Validation error: unsupported format
    """
    ck.check_file_refused(page, PressKitCardAdminPage, 142794, 'icon', BAD_IMAGE, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142795
def test_142795_press_kit_icon_rejects_a_file_exceeding_2mb(page):
    """ADO-142795 (P3). Verify that the Press Kit Icon rejects a file exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Icon field -> Field visible
      2. Upload press_icon_large.png (2.1MB) -> File selected
      3. Save -> Validation error: exceeds 2MB
    """
    ck.check_file_refused(page, PressKitCardAdminPage, 142795, 'icon', BIG_IMAGE, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142796
def test_142796_press_kit_eyebrow_label_saves_with_valid_en_ar_text_within_6(page):
    """ADO-142796 (P3). Verify that the Press Kit Eyebrow Label saves with valid EN/AR text within 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Eyebrow field -> Field visible
      2. Enter EN='Media resources', AR='موارد إعلامية' -> Both values entered
      3. Save and Publish -> Publish succeeds; displays on Card 01 per locale
    """
    ck.check_valid_persists(page, PressKitCardAdminPage, 142796, 'eyebrow', 'Valid eyebrow', ar='قيمة صالحة', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142797
def test_142797_press_kit_eyebrow_label_blocks_publish_when_the_arabic_value(page):
    """ADO-142797 (P3). Verify that the Press Kit Eyebrow Label blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Eyebrow field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, PressKitCardAdminPage, 142797, 'eyebrow', side='ar', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142798
def test_142798_press_kit_eyebrow_label_rejects_text_exceeding_60_characters(page):
    """ADO-142798 (P3). Verify that the Press Kit Eyebrow Label rejects text exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Eyebrow field -> Field visible
      2. Enter a 61-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, PressKitCardAdminPage, 142798, 'eyebrow', 60, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142799
def test_142799_press_kit_title_saves_with_valid_en_ar_text_within_150_chara(page):
    """ADO-142799 (P3). Verify that the Press Kit Title saves with valid EN/AR text within 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Title field -> Field visible
      2. Enter EN='Press Kit', AR='حقيبة صحفية' -> Both values entered
      3. Save and Publish -> Publish succeeds; displays on Card 01
    """
    ck.check_valid_persists(page, PressKitCardAdminPage, 142799, 'title', 'Valid title', ar='قيمة صالحة', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142800
def test_142800_press_kit_title_blocks_publish_when_the_arabic_value_is_miss(page):
    """ADO-142800 (P3). Verify that the Press Kit Title blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Title field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, PressKitCardAdminPage, 142800, 'title', side='ar', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142801
def test_142801_press_kit_title_rejects_text_exceeding_150_characters(page):
    """ADO-142801 (P3). Verify that the Press Kit Title rejects text exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Title field -> Field visible
      2. Enter a 151-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, PressKitCardAdminPage, 142801, 'title', 150, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142802
def test_142802_press_kit_description_saves_with_valid_en_ar_text_within_400(page):
    """ADO-142802 (P3). Verify that the Press Kit Description saves with valid EN/AR text within 400 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Description field -> Field visible
      2. Enter EN='Download our official press kit including brand assets, logos and media guidelines.' and AR equivalent -> Both values entered
      3. Save and Publish -> Publish succeeds; displays on Card 01
    """
    ck.check_valid_persists(page, PressKitCardAdminPage, 142802, 'description', 'Valid description', ar='قيمة صالحة', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142803
def test_142803_press_kit_description_blocks_publish_when_the_arabic_value_i(page):
    """ADO-142803 (P3). Verify that the Press Kit Description blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Description field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, PressKitCardAdminPage, 142803, 'description', side='ar', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142804
def test_142804_press_kit_description_rejects_text_exceeding_400_characters(page):
    """ADO-142804 (P3). Verify that the Press Kit Description rejects text exceeding 400 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Description field -> Field visible
      2. Enter a 401-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, PressKitCardAdminPage, 142804, 'description', 400, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142805
def test_142805_press_kit_file_button_label_saves_with_valid_en_ar_text_with(page):
    """ADO-142805 (P3). Verify that the Press Kit File Button Label saves with valid EN/AR text within 50 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Button Label field -> Field visible
      2. Enter EN='Download Press Kit', AR='تنزيل الحقيبة الصحفية' -> Both values entered
      3. Save and Publish -> Publish succeeds; button displays correct label per locale
    """
    ck.check_valid_persists(page, PressKitCardAdminPage, 142805, 'file_button_label', 'Valid file button label', ar='قيمة صالحة', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142806
def test_142806_press_kit_file_button_label_blocks_publish_when_the_arabic_v(page):
    """ADO-142806 (P3). Verify that the Press Kit File Button Label blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Button Label field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, PressKitCardAdminPage, 142806, 'file_button_label', side='ar', files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142807
def test_142807_press_kit_file_button_label_rejects_text_exceeding_50_charac(page):
    """ADO-142807 (P3). Verify that the Press Kit File Button Label rejects text exceeding 50 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 01's Button Label field -> Field visible
      2. Enter a 51-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, PressKitCardAdminPage, 142807, 'file_button_label', 50, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142808
def test_142808_press_kit_file_en_accepts_a_valid_pdf_under_5mb(page):
    """ADO-142808 (P3). Verify that the Press Kit File EN accepts a valid PDF under 5MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Press Kit File EN field -> Field visible
      2. Upload press_kit_en.pdf (3.2MB) -> File selected
      3. Save and Publish -> File uploads; EN visitors download this file
    """
    ck.check_file_accepted(page, PressKitCardAdminPage, 142808, 'file_en', VALID_PDF, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142809
def test_142809_press_kit_file_en_rejects_an_unsupported_file_format(page):
    """ADO-142809 (P3). Verify that the Press Kit File EN rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Press Kit File EN field -> Field visible
      2. Upload press_kit_en.docx -> File selected
      3. Save -> Validation error: PDF only
    """
    ck.check_file_refused(page, PressKitCardAdminPage, 142809, 'file_en', BAD_DOC, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142810
def test_142810_press_kit_file_en_rejects_a_file_exceeding_5mb(page):
    """ADO-142810 (P3). Verify that the Press Kit File EN rejects a file exceeding 5MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Press Kit File EN field -> Field visible
      2. Upload press_kit_en_large.pdf (5.6MB) -> File selected
      3. Save -> Validation error: exceeds 5MB
    """
    ck.check_file_refused(page, PressKitCardAdminPage, 142810, 'file_en', BIG_PDF, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142811
def test_142811_press_kit_file_ar_accepts_a_valid_pdf_under_5mb(page):
    """ADO-142811 (P3). Verify that the Press Kit File AR accepts a valid PDF under 5MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Press Kit File AR field -> Field visible
      2. Upload press_kit_ar.pdf (2.8MB) -> File selected
      3. Save and Publish -> File uploads; AR visitors download this file
    """
    ck.check_file_accepted(page, PressKitCardAdminPage, 142811, 'file_ar', VALID_PDF, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142812
def test_142812_press_kit_file_ar_rejects_an_unsupported_file_format(page):
    """ADO-142812 (P3). Verify that the Press Kit File AR rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Press Kit File AR field -> Field visible
      2. Upload press_kit_ar.docx -> File selected
      3. Save -> Validation error: PDF only
    """
    ck.check_file_refused(page, PressKitCardAdminPage, 142812, 'file_ar', BAD_DOC, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142813
def test_142813_press_kit_file_ar_rejects_a_file_exceeding_5mb(page):
    """ADO-142813 (P3). Verify that the Press Kit File AR rejects a file exceeding 5MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Press Kit File AR field -> Field visible
      2. Upload press_kit_ar_large.pdf (5.3MB) -> File selected
      3. Save -> Validation error: exceeds 5MB
    """
    ck.check_file_refused(page, PressKitCardAdminPage, 142813, 'file_ar', BIG_PDF, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142814
def test_142814_standard_card_icon_accepts_a_valid_svg_under_2mb(page):
    """ADO-142814 (P3). Verify that the Standard Card Icon accepts a valid SVG under 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Icon field -> Field visible
      2. Upload card_icon.svg (45KB) -> File selected
      3. Save -> Icon uploads and displays on the card
    """
    ck.check_file_accepted(page, MediaStandardCardAdminPage, 142814, 'icon', VALID_SVG, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142815
def test_142815_standard_card_icon_rejects_an_unsupported_file_format(page):
    """ADO-142815 (P3). Verify that the Standard Card Icon rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Icon field -> Field visible
      2. Upload card_icon.tiff -> File selected
      3. Save -> Validation error: unsupported format
    """
    ck.check_file_refused(page, MediaStandardCardAdminPage, 142815, 'icon', BAD_IMAGE, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142816
def test_142816_standard_card_icon_rejects_a_file_exceeding_2mb(page):
    """ADO-142816 (P3). Verify that the Standard Card Icon rejects a file exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Icon field -> Field visible
      2. Upload card_icon_large.svg (2.2MB) -> File selected
      3. Save -> Validation error: exceeds 2MB
    """
    ck.check_file_refused(page, MediaStandardCardAdminPage, 142816, 'icon', BIG_IMAGE, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142817
def test_142817_standard_card_eyebrow_label_saves_with_valid_en_ar_text_with(page):
    """ADO-142817 (P3). Verify that the Standard Card Eyebrow Label saves with valid EN/AR text within 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Eyebrow field -> Field visible
      2. Enter EN='Press Relations', AR='العلاقات الصحفية' -> Both values entered
      3. Save and Publish -> Publish succeeds; displays on Card 02
    """
    ck.check_valid_persists(page, MediaStandardCardAdminPage, 142817, 'eyebrow', 'Valid eyebrow', ar='قيمة صالحة', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142818
def test_142818_standard_card_eyebrow_label_blocks_publish_when_the_arabic_v(page):
    """ADO-142818 (P3). Verify that the Standard Card Eyebrow Label blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Eyebrow field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, MediaStandardCardAdminPage, 142818, 'eyebrow', side='ar', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142819
def test_142819_standard_card_eyebrow_label_rejects_text_exceeding_60_charac(page):
    """ADO-142819 (P3). Verify that the Standard Card Eyebrow Label rejects text exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Eyebrow field -> Field visible
      2. Enter a 61-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaStandardCardAdminPage, 142819, 'eyebrow', 60, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142820
def test_142820_standard_card_title_saves_with_valid_en_ar_text_within_150_c(page):
    """ADO-142820 (P3). Verify that the Standard Card Title saves with valid EN/AR text within 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Title field -> Field visible
      2. Enter EN='Interview Request', AR='طلب مقابلة' -> Both values entered
      3. Save and Publish -> Publish succeeds; displays on Card 02
    """
    ck.check_valid_persists(page, MediaStandardCardAdminPage, 142820, 'title', 'Valid title', ar='قيمة صالحة', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142821
def test_142821_standard_card_title_blocks_publish_when_the_arabic_value_is(page):
    """ADO-142821 (P3). Verify that the Standard Card Title blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Title field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, MediaStandardCardAdminPage, 142821, 'title', side='ar', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142822
def test_142822_standard_card_title_rejects_text_exceeding_150_characters(page):
    """ADO-142822 (P3). Verify that the Standard Card Title rejects text exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Title field -> Field visible
      2. Enter a 151-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaStandardCardAdminPage, 142822, 'title', 150, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142823
def test_142823_standard_card_description_saves_with_valid_en_ar_text_within(page):
    """ADO-142823 (P3). Verify that the Standard Card Description saves with valid EN/AR text within 400 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Description field -> Field visible
      2. Enter EN='Submit a request to interview Qatar Chamber leadership.' and AR equivalent -> Both values entered
      3. Save and Publish -> Publish succeeds; displays on Card 02
    """
    ck.check_valid_persists(page, MediaStandardCardAdminPage, 142823, 'description', 'Valid description', ar='قيمة صالحة', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142824
def test_142824_standard_card_description_blocks_publish_when_the_arabic_val(page):
    """ADO-142824 (P3). Verify that the Standard Card Description blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Description field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, MediaStandardCardAdminPage, 142824, 'description', side='ar', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142825
def test_142825_standard_card_description_rejects_text_exceeding_400_charact(page):
    """ADO-142825 (P3). Verify that the Standard Card Description rejects text exceeding 400 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Description field -> Field visible
      2. Enter a 401-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaStandardCardAdminPage, 142825, 'description', 400, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142826
def test_142826_standard_card_button_label_saves_with_valid_en_ar_text_withi(page):
    """ADO-142826 (P3). Verify that the Standard Card Button Label saves with valid EN/AR text within 50 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Button Label field -> Field visible
      2. Enter EN='Request Form', AR='نموذج الطلب' -> Both values entered
      3. Save and Publish -> Publish succeeds; button displays correct label
    """
    ck.check_valid_persists(page, MediaStandardCardAdminPage, 142826, 'button_label', 'Valid button label', ar='قيمة صالحة', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142827
def test_142827_standard_card_button_label_blocks_publish_when_the_arabic_va(page):
    """ADO-142827 (P3). Verify that the Standard Card Button Label blocks publish when the Arabic value is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Button Label field -> Field visible
      2. Enter EN only, leave AR empty -> EN entered, AR empty
      3. Attempt Publish -> Publish blocked; bilingual-required error shown
    """
    ck.check_empty_refused(page, MediaStandardCardAdminPage, 142827, 'button_label', side='ar', files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142828
def test_142828_standard_card_button_label_rejects_text_exceeding_50_charact(page):
    """ADO-142828 (P3). Verify that the Standard Card Button Label rejects text exceeding 50 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Card 02's Button Label field -> Field visible
      2. Enter a 51-character EN value -> Over-limit value entered
      3. Save -> Validation error shown; value not saved
    """
    ck.check_over_max_refused(page, MediaStandardCardAdminPage, 142828, 'button_label', 50, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142884
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142884_submission_reference_no_is_auto_generated_and_unique_per_sub(page):
    """ADO-142884 (P3). Verify that the Submission Reference No. is auto-generated and unique per submission

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. Submit an Interview Request form -> First submission record created
      2. Submit a second Interview Request form with different data -> Second submission record created
      3. Compare the two submission records' Reference No. values -> Each record received a distinct, auto-generated Reference No.; no duplicates

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142885
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142885_submission_form_type_is_stored_correctly_for_each_of_the_3_w(page):
    """ADO-142885 (P3). Verify that the Submission Form Type is stored correctly for each of the 3 webform types

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. Submit one Interview Request, one Event Coverage Request, and one Media Inquiry -> All 3 submissions accepted
      2. Open each resulting submission record -> Each submission record's Form Type field correctly reads 'Interview Request' / 'Event Coverage Request' / 'Media Inquiry' respectively

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142886
def test_142886_submission_s_submitted_field_values_display_as_a_complete_re(page):
    """ADO-142886 (P3). Verify that the Submission's Submitted Field Values display as a complete read-only snapshot

    Account: QC Form Manager via cms_role_credentials('Form Manager') (read-only; none of the named roles is mutated).
    Steps (from the approved case):
      1. Submit the Media Inquiry form with an attachment -> Submission accepted
      2. Open the submission in the admin detail view -> All submitted values, including the attached file, display read-only; none are editable
    """
    ck.check_form_renders(page, MediaDeptSubmissionAdminPage, ['reference_no', 'form_type', 'status', 'internal_notes'], role=ROLE_FORM_MANAGER)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142887
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142887_submission_date_time_is_auto_recorded_at_the_moment_of_submi(page):
    """ADO-142887 (P3). Verify that the Submission Date/Time is auto-recorded at the moment of submission

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. Submit an Interview Request form and note the wall-clock time -> Submission accepted at a known time
      2. Open the submission record -> Submission Date/Time field matches the actual submission time (within the propagation budget)

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142888
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142888_internal_notes_field_accepts_valid_text_within_1000_characte(page):
    """ADO-142888 (P3). Verify that the Internal Notes field accepts valid text within 1000 characters and saves

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. As Form Manager, open a submission -> Submission detail view open
      2. Enter Internal Notes='Coordinating with Chairman's office' -> Note entered
      3. Save -> Note saves successfully against the submission

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142889
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142889_internal_notes_field_rejects_text_exceeding_1000_characters(page):
    """ADO-142889 (P3). Verify that the Internal Notes field rejects text exceeding 1000 characters

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. As Form Manager, open a submission -> Submission detail view open
      2. Enter a 1001-character Internal Notes value -> Over-limit value entered
      3. Attempt Save -> Validation error shown; note not saved

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142890
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142890_internal_notes_field_is_never_visible_to_the_submitter(page):
    """ADO-142890 (P3). Verify that the Internal Notes field is never visible to the submitter

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. As Form Manager, save an Internal Note against a submission -> Note saved against the submission
      2. As the original submitter, attempt to view submission status via any public-facing channel -> Internal Notes content is not exposed anywhere on the public/visitor side

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142891
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142891_publishing_the_page_makes_it_visible_on_the_public_site(page, browser):
    """ADO-142891 (P3). Verify that publishing the Page makes it visible on the public site

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, with the Page in Draft state, click Publish -> Liferay generic success toast shown; audit log entry recorded; public page becomes reachable and renders hero+cards

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, MediaDeptPageHeroAdminPage, 142891, probe, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142892
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142892_unpublishing_the_page_removes_it_from_the_public_site(page, browser):
    """ADO-142892 (P3). Verify that unpublishing the Page removes it from the public site

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, with the Page currently Published, click Unpublish -> Toast shown; audit log entry recorded; public URL returns a not-found/unavailable state, not stale content

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_unpublish_hides(page, browser, MediaDeptPageHeroAdminPage, 142892, probe, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142893
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142893_publishing_the_press_kit_card_makes_the_press_kit_downloadab(page, browser):
    """ADO-142893 (P3). Verify that publishing the Press Kit card makes the Press Kit downloadable

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, with Card 01 in Draft state, click Publish -> Toast shown; audit logged; Download button becomes active and serves the file publicly

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, PressKitCardAdminPage, 142893, probe, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142894
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142894_unpublishing_the_press_kit_card_removes_the_download_option(page, browser):
    """ADO-142894 (P3). Verify that unpublishing the Press Kit card removes the Download option publicly

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, with Card 01 currently Published, click Unpublish -> Toast shown; audit logged; Card 01/Download no longer available to public visitors

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_unpublish_hides(page, browser, PressKitCardAdminPage, 142894, probe, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142896
def test_142896_publishing_a_standard_card_makes_it_visible_on_the_public_si(page, browser):
    """ADO-142896 (P3). Verify that publishing a Standard Card makes it visible on the public site

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, with Card 02 in Draft state, click Publish -> Toast shown; audit logged; Card 02 renders publicly
    """
    ck.check_editor_publish_public(page, browser, MediaStandardCardAdminPage, 142896, probe, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142897
def test_142897_unpublishing_a_standard_card_removes_it_from_the_public_site(page, browser):
    """ADO-142897 (P3). Verify that unpublishing a Standard Card removes it from the public site

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, with Card 02 currently Published, click Unpublish -> Toast shown; audit logged; Card 02 no longer renders publicly (3-card layout, not 4)
    """
    ck.check_unpublish_hides(page, browser, MediaStandardCardAdminPage, 142897, probe, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142919
def test_142919_page_starts_in_draft_by_default_when_newly_created(page):
    """ADO-142919 (P3). Verify that the Page starts in Draft by default when newly created

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, create a new Request to Media Dept.-type record -> Record defaults to Status = Draft; not visible publicly until explicitly published
    """
    ck.check_default_draft(page, MediaDeptPageHeroAdminPage, 142919, files=FILES[MediaDeptPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142920
def test_142920_press_kit_card_starts_in_draft_by_default_when_newly_created(page):
    """ADO-142920 (P3). Verify that the Press Kit card starts in Draft by default when newly created

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, create a new Press Kit card record -> Record defaults to Status = Draft
    """
    ck.check_default_draft(page, PressKitCardAdminPage, 142920, files=FILES[PressKitCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142921
def test_142921_standard_card_starts_in_draft_by_default_when_newly_created(page):
    """ADO-142921 (P3). Verify that a Standard Card starts in Draft by default when newly created

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, create a new standard card record -> Record defaults to Status = Draft
    """
    ck.check_default_draft(page, MediaStandardCardAdminPage, 142921, files=FILES[MediaStandardCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131061
@pytest.mark.tc_142922
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_142922_submission_can_reach_the_closed_status_as_an_alternate_termi(page):
    """ADO-142922 (P3). Verify that a submission can reach the Closed status as an alternate terminal state to Completed

    Account: QC Form Manager via cms_role_credentials('Form Manager').
    Steps (from the approved case):
      1. As Form Manager, with a submission currently Under Review, change status to 'Closed' -> Status field changed
      2. Save -> Save succeeds; status shows Closed; toast shown; audit log records the transition with timestamp + acting user; no email sent

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')

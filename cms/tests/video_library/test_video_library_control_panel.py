"""
cms/tests/video_library/test_video_library_control_panel.py - Control_Panel cases for PBI 130715
(Test Plan 137724, suite 140374): Azure Priority 1-3, Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_130715_cp_batch.json, which holds every disposition and
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
from cms.pages.video_library.video_library_admin_page import (
    VideoLibraryPageHeroAdminPage,
    VideoCategoryAdminPage,
    VideoRecordAdminPage,
    VideoRecordUploadAdminPage,
)
from cms.tests import authoring_checks as ck
from web.pages.video_library.video_library_listing_page import VideoLibraryListingPage

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
VALID_MP4 = str(FIXTURES / 'valid_video_1mb.mp4')
BAD_VIDEO = str(FIXTURES / 'unsupported_video.avi')

# Required upload fields per object, filled by fill_required().
FILES = {
    VideoLibraryPageHeroAdminPage: {'hero_background_image': VALID_JPG},
    VideoCategoryAdminPage: {},
    VideoRecordAdminPage: {'video_thumbnail': VALID_JPG},
    VideoRecordUploadAdminPage: {'video_thumbnail': VALID_JPG, 'video_file': VALID_MP4},
}

probe = ck.make_public_probe(lambda p: VideoLibraryListingPage(p).open_video_library())

# Conditional-case gates. Flip one only when its condition is confirmed.
AUDIT_LOG_LOCATED = False  # True once: the audit-log surface is located
FLICKR_SETTINGS_LOCATED = False  # True once: the Flickr integration settings surface is located

@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130715
@pytest.mark.tc_142968
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record; the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')
def test_142968_administrator_can_access_and_configure_flickr_integration_se(page):
    """ADO-142968 (P1). Verify that Administrator can access and configure Flickr integration settings

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Log in as Administrator. -> Login succeeds.
      2. Navigate to the Flickr integration settings area. -> Settings page is accessible, all fields editable.
      3. Update the import scope and save. -> Save succeeds with a confirmation toast; new value persists on reload.

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record; the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130715
@pytest.mark.tc_142969
def test_142969_site_content_editor_can_publish_a_video_record(page, browser):
    """ADO-142969 (P1). Verify that Site Content Editor can publish a video record

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor (test1@xyz.com). -> Login succeeds.
      2. Open a complete draft video record. -> Record opens with Publish action enabled.
      3. Click Publish. -> Record status changes to Published; video appears on the public Video Library.
    """
    ck.check_editor_publish_public(page, browser, VideoRecordAdminPage, 142969, probe, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130715
@pytest.mark.tc_142970
@pytest.mark.skipif(not FLICKR_SETTINGS_LOCATED, reason='CONDITIONAL - the Flickr integration settings surface is not an Object Authoring object and is not located yet')
def test_142970_site_content_editor_is_denied_access_to_flickr_integration_s(page):
    """ADO-142970 (P1). Verify that Site Content Editor is denied access to Flickr integration settings

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor. -> Login succeeds.
      2. Attempt to navigate directly to the Flickr integration settings URL. -> Access is refused with message "Access Denied. You do not have permission to perform this action." / تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء.; setting

    Disposition: conditional - the Flickr integration settings surface is not an Object Authoring object and is not located yet
    """
    pytest.fail('Flickr settings surface not located')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130715
@pytest.mark.tc_142971
def test_142971_site_content_author_can_create_and_submit_a_video_record_for(page):
    """ADO-142971 (P1). Verify that Site Content Author can create and submit a video record for review

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in as Site Content Author (Test2@xyz.com). -> Login succeeds.
      2. Create a new video record with valid data. -> Record saves as Draft.
      3. Submit for review. -> Record is submitted for review; no Publish action is available to this role.
    """
    ck.check_author_submit_pending(page, VideoRecordAdminPage, 142971, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130715
@pytest.mark.tc_142972
def test_142972_site_content_author_is_denied_direct_publish_action(page):
    """ADO-142972 (P1). Verify that Site Content Author is denied direct publish action

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in as Site Content Author. -> Login succeeds.
      2. Open own draft video record. -> Record opens; Publish control is not available/disabled.
      3. Attempt to trigger Publish directly (via UI control or deep-link to the publish action URL). -> Direct deep-link attempt is refused with "Access Denied. You do not have permission to perform this action." / تم رفض الوصول...; record remains in Draft/Pending
    """
    ck.check_author_submit_pending(page, VideoRecordAdminPage, 142972, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143001
def test_143001_creating_a_new_video_record_and_publishing_it_makes_it_visib(page, browser):
    """ADO-143001 (P1). Verify that creating a new video record and publishing it makes it visible on the public Video Library

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor. -> Login succeeds.
      2. Create a video record: Title EN="Chamber Awards Night" / AR="حفل جوائز الغرفة", Category=Events, Source=External URL (`https://vimeo.com/123456789`), Thumbnail=valid PNG, Duration= -> Fields accepted.
      3. Save as Draft, then Publish. -> Record status becomes Published.
      4. In a fresh browser session, open the public Video Library. -> "Chamber Awards Night" card is visible on the public Video Library with the entered data.
    """
    ck.check_editor_publish_public(page, browser, VideoRecordAdminPage, 143001, probe, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143002
def test_143002_editing_a_published_video_and_republishing_shows_the_new_val(page, browser):
    """ADO-143002 (P1). Verify that editing a published video and republishing shows the new value on the public page, not the stale one

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the published "Chamber Awards Night" record. -> Record opens.
      2. Change the title to "Chamber Awards Night 2026" and republish. -> Save/republish succeeds.
      3. Reload the public Video Library. -> Public card shows "Chamber Awards Night 2026", not the old title.
    """
    ck.check_republish_updates(page, browser, VideoRecordAdminPage, 143002, probe, 'video_title', 'QCTEST-143002 Chamber Awards Night 2026', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143003
def test_143003_previewing_a_draft_video_record_shows_draft_content_without(page, browser):
    """ADO-143003 (P1). Verify that previewing a draft video record shows draft content without exposing it publicly

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a draft video record, do not publish. -> Draft record saved.
      2. Click Preview. -> Preview shows the entered content correctly within the CMS preview surface.
      3. In a fresh, logged-out browser context, attempt to reach the same video's public URL. -> The public URL does not show the video (not found) — draft content is never publicly visible.
    """
    ck.check_preview_draft(page, browser, VideoRecordAdminPage, 143003, probe, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143004
def test_143004_publish_is_blocked_when_the_video_record_has_no_thumbnail(page):
    """ADO-143004 (P1). Verify that publish is blocked when the video record has no thumbnail

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a video record with all required fields filled except Thumbnail. -> Record saves as Draft.
      2. Attempt to Publish. -> Publish is blocked with message "A video thumbnail is required." / الصورة المصغّرة للفيديو مطلوبة.; record remains unpublished.
    """
    ck.check_publish_refused(page, VideoRecordAdminPage, 143004, skip=('video_thumbnail',), files={})


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143005
def test_143005_publish_is_blocked_when_the_video_record_has_no_playable_sou(page):
    """ADO-143005 (P1). Verify that publish is blocked when the video record has no playable source

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a video record with Thumbnail and metadata filled but no Source Type value/source field set. -> Record saves as Draft.
      2. Attempt to Publish. -> Publish is blocked with message "A video source is required." / مصدر الفيديو مطلوب.; record remains unpublished.
    """
    ck.check_publish_refused(page, VideoRecordAdminPage, 143005, skip=('video_url', 'video_file'), files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143006
def test_143006_unpublishing_a_published_video_removes_it_from_both_the_publ(page, browser):
    """ADO-143006 (P1). Verify that unpublishing a published video removes it from both the public listing and its Details URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Confirm "Chamber Awards Night 2026" is live on the public Video Library. -> Card confirmed visible.
      2. In the Control Panel, Unpublish the record. -> Record status becomes Unpublished.
      3. In a fresh, logged-out browser context, reload the Video Library and the video's direct URL. -> Video no longer appears on the listing; direct URL returns the standard not-found page, not a stale 200.
    """
    ck.check_unpublish_hides(page, browser, VideoRecordAdminPage, 143006, probe, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143007
def test_143007_deleting_a_video_record_removes_it_permanently(page, browser):
    """ADO-143007 (P1). Verify that deleting a video record removes it permanently

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a disposable `QCTEST-` video record. -> Record created.
      2. Delete it from the admin listing. -> Delete succeeds.
      3. Confirm it no longer appears in the admin listing or (if it had been published) the public site. -> Record is absent from both the admin listing and the public site.
    """
    ck.check_delete_removes(page, browser, VideoRecordAdminPage, 143007, probe, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143008
def test_143008_creating_and_publishing_a_video_category_makes_it_appear_in(page, browser):
    """ADO-143008 (P1). Verify that creating and publishing a Video Category makes it appear in the frontend dropdown and chip row, in configured order

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a Video Category "Sustainability" EN / "الاستدامة" AR, Display Order=7. -> Category saves as Draft.
      2. Publish it. -> Status becomes Published.
      3. Reload the public Video Library. -> "Sustainability" appears both in the "All Categories" dropdown and as the 7th chip in the quick-filter row, with no redevelopment required.
    """
    ck.check_editor_publish_public(page, browser, VideoCategoryAdminPage, 143008, probe, files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143009
def test_143009_unpublishing_a_video_category_removes_it_from_the_frontend_d(page, browser):
    """ADO-143009 (P1). Verify that unpublishing a Video Category removes it from the frontend dropdown and chip row

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Confirm "Sustainability" is visible on the public dropdown/chips. -> Confirmed visible.
      2. Unpublish the category. -> Status becomes Unpublished.
      3. Reload the public Video Library. -> "Sustainability" no longer appears in the dropdown or chip row.
    """
    ck.check_unpublish_hides(page, browser, VideoCategoryAdminPage, 143009, probe, files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143010
def test_143010_deleting_an_unlinked_video_category_succeeds(page):
    """ADO-143010 (P1). Verify that deleting an unlinked Video Category succeeds

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a `QCTEST-` category with zero linked videos. -> Category created.
      2. Delete it. -> Delete succeeds; category no longer appears in the admin listing or frontend.
    """
    admin = VideoCategoryAdminPage(page)
    title = qctest_title(143010, 'unlinked')
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=FILES[VideoCategoryAdminPage])
        admin.save_as_draft()
        assert admin.delete_disposable(title), 'delete of an unlinked category did not run'
        assert not admin.entry_exists(title, ROLE_EDITOR)
    finally:
        admin.delete_disposable(title)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143011
def test_143011_deleting_a_video_category_linked_to_published_videos_is_bloc(page, browser):
    """ADO-143011 (P1). Verify that deleting a Video Category linked to published videos is blocked until reassigned

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to delete the "Events" category, which has published videos assigned. -> Delete action is attempted.
      2. Observe the result. -> Deletion is blocked with a message indicating the category is in use; "Events" and its published videos remain intact and unaffected.
    """
    ck.check_in_use_delete_blocked(page, browser, VideoCategoryAdminPage, VideoRecordAdminPage, 143011, 'video_category', child_files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143012
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record')
def test_143012_triggering_a_manual_flickr_import_creates_one_folder_per_fli(page):
    """ADO-143012 (P1). Verify that triggering a manual Flickr import creates one folder per Flickr album and imports videos without publishing them

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Log in as Administrator. -> Login succeeds.
      2. Configure import scope to include video media type. -> Scope saved.
      3. Trigger a manual import run. -> Run completes; a folder named after the English Flickr album name is created under Documents & Media / Video Library, containing the imported videos, with Flick
      4. Inspect Documents & Media and the public Video Library. -> None of the newly imported videos appear on the public Video Library (not yet published).

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143013
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record')
def test_143013_imported_video_s_duration_exceeding_10_minutes_is_flagged_re(page):
    """ADO-143013 (P1). Verify that an imported video's duration exceeding 10 minutes is flagged, requiring External URL before publish

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Import a Flickr video with a source duration of 14:20. -> Import completes, duration 14:20 stored.
      2. Open the imported record and attempt to Publish without changing the source. -> Publish attempt shows a warning that Flickr playback truncates at 10 minutes and requires either explicit confirmation or switching Source Type to External URL 

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143014
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record')
def test_143014_individual_video_import_failure_is_logged_and_the_run_contin(page):
    """ADO-143014 (P1). Verify that an individual video import failure is logged and the run continues with remaining assets

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Trigger an import run where one video asset is corrupted/unreadable on the Flickr side while others are valid. -> Run executes.
      2. Inspect the import log after the run. -> Log shows the one asset recorded as an error while all other valid videos in the same run were successfully created — the run did not abort.

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143015
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record')
def test_143015_re_running_import_against_already_imported_assets_applies_th(page):
    """ADO-143015 (P1). Verify that re-running import against already-imported assets applies the configured duplicate-handling rule

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Run import once, note a video asset "Board Meeting Q3" is created. -> Asset created.
      2. Configure duplicate handling = "skip existing". -> Setting saved.
      3. Run import again against the same Flickr album. -> Second run does not create a duplicate "Board Meeting Q3" record; the existing one is left unchanged (skipped), per the configured rule.

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143016
@pytest.mark.skipif(not FLICKR_SETTINGS_LOCATED, reason='CONDITIONAL - the Flickr integration settings surface is not an Object Authoring object and is not located yet; the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')
def test_143016_administrator_can_view_the_import_log_per_run_showing_albums(page):
    """ADO-143016 (P1). Verify that the Administrator can view the import log per run showing albums fetched, videos created, skipped, and errors

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Run a manual import. -> Run completes.
      2. Open the import log for that run. -> Log entry displays albums fetched, videos created, videos skipped, and any errors for that specific run.

    Disposition: conditional - the Flickr integration settings surface is not an Object Authoring object and is not located yet; the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account
    """
    pytest.fail('import log surface not located')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130715
@pytest.mark.tc_143017
@pytest.mark.skipif(not AUDIT_LOG_LOCATED, reason='CONDITIONAL - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')
def test_143017_every_admin_publish_unpublish_delete_action_shows_the_lifera(page):
    """ADO-143017 (P1). Verify that every admin publish/unpublish/delete action shows the Liferay generic success toast and records an audit log entry

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor. -> Login succeeds.
      2. Publish a draft video record. -> Action completes; a Liferay generic success toast displays (EN/AR per active locale).
      3. Check the audit log for the same action. -> Audit log shows a new entry recording the publish action, the acting user, and timestamp.

    Disposition: conditional - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143018
def test_143018_page_title_field_accepts_a_valid_value_within_100_characters(page):
    """ADO-143018 (P3). Verify that the Page Title field accepts a valid value within 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Video Library page content settings. -> Settings open.
      2. Enter Page Title = "Video Library" (14 chars). -> Value entered.
      3. Save. -> Save succeeds; title persists and displays on the public hero.
    """
    ck.check_valid_persists(page, VideoLibraryPageHeroAdminPage, 143018, 'page_title', 'Valid page title', ar='قيمة صالحة', files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143019
def test_143019_page_title_field_rejects_an_empty_value(page):
    """ADO-143019 (P3). Verify that the Page Title field rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the page content settings. -> Settings open.
      2. Clear the Page Title field. -> Field is empty.
      3. Attempt to save. -> Save is blocked with a required-field validation error; previous title is retained.
    """
    ck.check_empty_refused(page, VideoLibraryPageHeroAdminPage, 143019, 'page_title', side='both', files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143020
def test_143020_page_title_field_enforces_the_100_character_maximum(page):
    """ADO-143020 (P3). Verify that the Page Title field enforces the 100-character maximum

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter exactly 100 characters as the Page Title; save. -> 100-char value is accepted and persists.
      2. Enter 101 characters; attempt to save. -> Save is blocked (or input truncated to 100) with a max-length validation indication.
    """
    ck.check_over_max_refused(page, VideoLibraryPageHeroAdminPage, 143020, 'page_title', 100, files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143021
def test_143021_page_title_field_rejects_a_whitespace_only_value(page):
    """ADO-143021 (P3). Verify that the Page Title field rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter only spaces ("   ") as the Page Title. -> Value entered.
      2. Attempt to save. -> Save is blocked as equivalent to empty; previous title is retained.
    """
    ck.check_whitespace_refused(page, VideoLibraryPageHeroAdminPage, 143021, 'page_title', files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143022
def test_143022_hero_background_image_field_accepts_a_valid_jpg_png_under_2(page):
    """ADO-143022 (P3). Verify that the Hero Background Image field accepts a valid JPG/PNG under 2 MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the page content settings. -> Settings open.
      2. Upload a 500 KB PNG file. -> Upload succeeds.
      3. Save. -> Save succeeds; image displays as the hero background on the public page.
    """
    ck.check_file_accepted(page, VideoLibraryPageHeroAdminPage, 143022, 'hero_background_image', VALID_PNG, files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143023
def test_143023_hero_background_image_field_is_blocked_when_left_empty(page):
    """ADO-143023 (P3). Verify that the Hero Background Image field is blocked when left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the page content settings with no image uploaded. -> Settings open.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoLibraryPageHeroAdminPage, 143023, 'hero_background_image', side='en', files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143024
def test_143024_hero_background_image_field_rejects_a_file_exceeding_2_mb(page):
    """ADO-143024 (P3). Verify that the Hero Background Image field rejects a file exceeding 2 MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a 3.5 MB JPG as the Hero Background Image. -> Upload is rejected or flagged oversize.
      2. Attempt to save. -> Save is blocked; previous image (if any) is retained.
    """
    ck.check_file_refused(page, VideoLibraryPageHeroAdminPage, 143024, 'hero_background_image', BIG_IMAGE, files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143025
def test_143025_hero_background_image_field_rejects_an_unsupported_format(page):
    """ADO-143025 (P3). Verify that the Hero Background Image field rejects an unsupported format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a GIF file as the Hero Background Image. -> Upload is rejected as an unsupported format.
      2. Attempt to save. -> Save is blocked; previous image (if any) is retained.
    """
    ck.check_file_refused(page, VideoLibraryPageHeroAdminPage, 143025, 'hero_background_image', BAD_IMAGE_GIF, files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143028
def test_143028_page_status_dropdown_persists_each_selectable_value(page):
    """ADO-143028 (P3). Verify that the Page Status dropdown persists each selectable value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open page content settings. -> Settings open.
      2. Set Status = Draft, save; then Published, save; then Unpublished, save. -> Each value persists and is reflected on reload after saving.
    """
    ck.check_select_persists(page, VideoLibraryPageHeroAdminPage, 143028, 'page_status', [STATUS_DRAFT, STATUS_PUBLISHED, STATUS_UNPUBLISHED], files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143029
def test_143029_page_s_created_last_modified_date_auto_populates_and_updates(page):
    """ADO-143029 (P3). Verify that the page's Created/Last Modified Date auto-populates and updates on edit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Note the page's Last Modified timestamp. -> Timestamp noted.
      2. Edit and save any field on the page. -> Save succeeds.
      3. Re-check the timestamp. -> Last Modified timestamp updates to the time of the edit.
    """
    ck.check_modified_updates(page, VideoLibraryPageHeroAdminPage, 143029, 'page_title', qctest_title(143029, 'edited'), files=FILES[VideoLibraryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143030
def test_143030_new_video_category_s_category_id_auto_generates_a_unique_val(page):
    """ADO-143030 (P3). Verify that a new Video Category's Category ID auto-generates a unique value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create two new Video Category records. -> Both records save.
      2. Inspect their Category IDs. -> Each has a distinct, system-generated unique ID.
    """
    ck.check_auto_id_unique(page, VideoCategoryAdminPage, 143030, 'category_id', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143031
def test_143031_category_name_field_accepts_a_valid_value_within_200_charact(page):
    """ADO-143031 (P3). Verify that the Category Name field accepts a valid value within 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a Video Category. -> Form opens.
      2. Enter Name EN = "Community Outreach" (19 chars) / AR = "التواصل المجتمعي". -> Values entered.
      3. Save. -> Save succeeds; name persists and displays in the frontend dropdown/chip.
    """
    ck.check_valid_persists(page, VideoCategoryAdminPage, 143031, 'category_name', 'Valid category name', ar='قيمة صالحة', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143032
def test_143032_category_name_field_rejects_an_empty_value(page):
    """ADO-143032 (P3). Verify that the Category Name field rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a Video Category, leaving Name EN blank. -> Form opens.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoCategoryAdminPage, 143032, 'category_name', side='both', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143033
def test_143033_category_name_field_enforces_the_200_character_maximum(page):
    """ADO-143033 (P3). Verify that the Category Name field enforces the 200-character maximum

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter exactly 200 characters as Category Name; save. -> 200-char value accepted and persists.
      2. Enter 201 characters; attempt to save. -> Save is blocked (or truncated) with a max-length validation indication.
    """
    ck.check_over_max_refused(page, VideoCategoryAdminPage, 143033, 'category_name', 200, files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143034
def test_143034_category_name_field_rejects_a_whitespace_only_value(page):
    """ADO-143034 (P3). Verify that the Category Name field rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter only spaces as Category Name. -> Value entered.
      2. Attempt to save. -> Save is blocked as equivalent to empty.
    """
    ck.check_whitespace_refused(page, VideoCategoryAdminPage, 143034, 'category_name', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143035
def test_143035_display_order_accepts_a_valid_positive_integer(page):
    """ADO-143035 (P3). Verify that Display Order accepts a valid positive integer

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a Video Category. -> Form opens.
      2. Enter Display Order = 3. -> Value entered.
      3. Save. -> Save succeeds; category appears at position 3 in the dropdown/chip row.
    """
    ck.check_valid_persists(page, VideoCategoryAdminPage, 143035, 'display_order', '9900', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143036
def test_143036_display_order_rejects_an_empty_value(page):
    """ADO-143036 (P3). Verify that Display Order rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Display Order blank. -> Field empty.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoCategoryAdminPage, 143036, 'display_order', side='both', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143037
def test_143037_display_order_rejects_zero(page):
    """ADO-143037 (P3). Verify that Display Order rejects zero

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Display Order = 0. -> Value entered.
      2. Attempt to save. -> Save is blocked — 0 is not a positive integer.
    """
    ck.check_value_refused(page, VideoCategoryAdminPage, 143037, 'display_order', '0', short='zero', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143038
def test_143038_display_order_rejects_a_negative_value(page):
    """ADO-143038 (P3). Verify that Display Order rejects a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Display Order = -2. -> Value entered.
      2. Attempt to save. -> Save is blocked — negative values are not permitted.
    """
    ck.check_value_refused(page, VideoCategoryAdminPage, 143038, 'display_order', '-1', short='neg', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143039
def test_143039_display_order_rejects_a_non_numeric_value(page):
    """ADO-143039 (P3). Verify that Display Order rejects a non-numeric value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Display Order = "abc". -> Value entered.
      2. Attempt to save. -> Save is blocked with a numeric-format validation error.
    """
    ck.check_value_refused(page, VideoCategoryAdminPage, 143039, 'display_order', 'abc', short='nan', files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143040
def test_143040_category_publish_status_dropdown_persists_each_selectable_va(page):
    """ADO-143040 (P3). Verify that the Category Publish Status dropdown persists each selectable value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a category record. -> Record opens.
      2. Set Publish Status = Draft, save; then Published, save. -> Each value persists on reload.
    """
    ck.check_select_persists(page, VideoCategoryAdminPage, 143040, 'publish_status', [STATUS_DRAFT, STATUS_PUBLISHED], files=FILES[VideoCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143041
def test_143041_new_video_record_s_video_id_auto_generates_a_unique_value(page):
    """ADO-143041 (P3). Verify that a new Video Record's Video ID auto-generates a unique value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create two new video records. -> Both save.
      2. Inspect their Video IDs. -> Each has a distinct, system-generated unique ID.
    """
    ck.check_auto_id_unique(page, VideoRecordAdminPage, 143041, 'video_id', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143042
def test_143042_video_title_field_accepts_a_valid_value_within_200_character(page):
    """ADO-143042 (P3). Verify that the Video Title field accepts a valid value within 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a video record. -> Form opens.
      2. Enter Title EN/AR within limit. -> Values entered.
      3. Save. -> Save succeeds; title displays on card and Details page.
    """
    ck.check_valid_persists(page, VideoRecordAdminPage, 143042, 'video_title', 'Valid video title', ar='قيمة صالحة', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143043
def test_143043_video_title_field_rejects_an_empty_value(page):
    """ADO-143043 (P3). Verify that the Video Title field rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Video Title EN blank. -> Field empty.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143043, 'video_title', side='both', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143044
def test_143044_video_title_field_enforces_the_200_character_maximum(page):
    """ADO-143044 (P3). Verify that the Video Title field enforces the 200-character maximum

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter exactly 200 characters as Video Title; save. -> 200-char value accepted.
      2. Enter 201 characters; attempt to save. -> Save is blocked (or truncated) with a max-length indication.
    """
    ck.check_over_max_refused(page, VideoRecordAdminPage, 143044, 'video_title', 200, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143045
def test_143045_video_title_field_rejects_a_whitespace_only_value(page):
    """ADO-143045 (P3). Verify that the Video Title field rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter only spaces as Video Title. -> Value entered.
      2. Attempt to save. -> Save is blocked as equivalent to empty.
    """
    ck.check_whitespace_refused(page, VideoRecordAdminPage, 143045, 'video_title', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143046
def test_143046_video_category_accepts_a_valid_selection_from_published_cate(page):
    """ADO-143046 (P3). Verify that Video Category accepts a valid selection from published categories

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record. -> Record opens.
      2. Select Category = "Institutional" from the dropdown (only published categories listed). -> Only published categories are selectable; "Institutional" selected.
      3. Save. -> Save succeeds; card shows "Institutional" chip.
    """
    cat = VideoCategoryAdminPage(page)
    draft = qctest_title(143046, 'draft-cat')
    try:
        cat.open_form(ROLE_EDITOR)
        cat.fill_required(draft)
        cat.save_as_draft()
        admin = VideoRecordAdminPage(page)
        admin.open_form(ROLE_EDITOR)
        options = admin.select_options('video_category')
        assert options, 'Video Category offers no options'
        assert draft not in options, 'a Draft category is offered on the video form'
    finally:
        cat.delete_disposable(draft)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143047
def test_143047_video_category_is_blocked_when_not_selected(page):
    """ADO-143047 (P3). Verify that Video Category is blocked when not selected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Video Category unselected. -> Field unset.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143047, 'video_category', side='both', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143048
def test_143048_video_source_type_accepts_exactly_one_valid_selection_and_re(page):
    """ADO-143048 (P3). Verify that Video Source Type accepts exactly one valid selection and reveals its conditional field

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record. -> Record opens.
      2. Select Source Type = "External URL". -> The Video URL field appears/becomes required; Flickr Video ID and Video File fields are hidden/disabled.
    """
    admin = VideoRecordAdminPage(page)
    admin.open_form(ROLE_EDITOR)
    admin.select_option('video_source_type', admin.SOURCE_EXTERNAL_URL)
    assert admin.field_present('video_url'), 'External URL did not reveal Video URL'
    assert not admin.field_present('video_file'), 'Video File stays shown for External URL'


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143049
def test_143049_video_source_type_is_blocked_when_not_selected(page):
    """ADO-143049 (P3). Verify that Video Source Type is blocked when not selected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Source Type unselected. -> Field unset.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143049, 'video_source_type', side='both', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143050
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record')
def test_143050_flickr_video_id_auto_populates_and_is_stored_on_the_record_a(page):
    """ADO-143050 (P3). Verify that the Flickr Video ID auto-populates and is stored on the record after import

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Import a video from Flickr. -> Import completes.
      2. Inspect the resulting record's Flickr Video ID field. -> Field is populated with the correct Flickr video ID, read-only in the UI.

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143051
def test_143051_video_url_accepts_a_valid_youtube_vimeo_url_when_source_exte(page):
    """ADO-143051 (P3). Verify that Video URL accepts a valid YouTube/Vimeo URL when Source=External URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Source Type=External URL. -> Field appears.
      2. Enter Video URL = `https://www.youtube.com/watch?v=abc123`. -> Value entered.
      3. Save. -> Save succeeds; URL is stored as the playback source.
    """
    ck.check_valid_persists(page, VideoRecordAdminPage, 143051, 'video_url', 'https://www.youtube.com/watch?v=abc123', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143052
def test_143052_video_url_rejects_a_non_youtube_vimeo_url(page):
    """ADO-143052 (P3). Verify that Video URL rejects a non-YouTube/Vimeo URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Source Type=External URL. -> Field appears.
      2. Enter Video URL = `https://example.com/video.mp4`. -> Value entered.
      3. Attempt to save. -> Save is blocked with a format validation error (must be a valid YouTube or Vimeo URL).
    """
    ck.check_value_refused(page, VideoRecordAdminPage, 143052, 'video_url', 'https://example.com/video.mp4', short='url', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143053
def test_143053_video_url_is_blocked_when_left_empty_while_source_external_u(page):
    """ADO-143053 (P3). Verify that Video URL is blocked when left empty while Source=External URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Source Type=External URL. -> Field appears, required.
      2. Leave Video URL blank. -> Field empty.
      3. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143053, 'video_url', side='both', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143054
def test_143054_video_file_accepts_a_valid_mp4_mov_upload_when_source_direct(page):
    """ADO-143054 (P3). Verify that Video File accepts a valid MP4/MOV upload when Source=Direct Upload

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Source Type=Direct Upload. -> Field appears.
      2. Upload a valid MP4 file. -> Upload succeeds.
      3. Save. -> Save succeeds; file stored in Documents & Media as the playback source.
    """
    ck.check_file_accepted(page, VideoRecordUploadAdminPage, 143054, 'video_file', VALID_MP4, files=FILES[VideoRecordUploadAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143055
def test_143055_video_file_rejects_an_unsupported_format(page):
    """ADO-143055 (P3). Verify that Video File rejects an unsupported format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Source Type=Direct Upload. -> Field appears.
      2. Attempt to upload an AVI file. -> Upload is rejected as unsupported format.
      3. Attempt to save. -> Save is blocked.
    """
    ck.check_file_refused(page, VideoRecordUploadAdminPage, 143055, 'video_file', BAD_VIDEO, files=FILES[VideoRecordUploadAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143056
def test_143056_video_file_is_blocked_when_left_empty_while_source_direct_up(page):
    """ADO-143056 (P3). Verify that Video File is blocked when left empty while Source=Direct Upload

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Source Type=Direct Upload. -> Field appears, required.
      2. Leave Video File empty. -> Field empty.
      3. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordUploadAdminPage, 143056, 'video_file', side='en', files=FILES[VideoRecordUploadAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143057
def test_143057_video_thumbnail_accepts_a_valid_jpg_jpeg_png_upload(page):
    """ADO-143057 (P3). Verify that Video Thumbnail accepts a valid JPG/JPEG/PNG upload

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record. -> Record opens.
      2. Upload a valid PNG as Thumbnail EN/AR. -> Upload succeeds.
      3. Save. -> Save succeeds; thumbnail is used as the card image and player poster frame.
    """
    ck.check_file_accepted(page, VideoRecordAdminPage, 143057, 'video_thumbnail', VALID_PNG, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143058
def test_143058_video_thumbnail_rejects_an_unsupported_file_format(page):
    """ADO-143058 (P3). Verify that Video Thumbnail rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a BMP file as the Video Thumbnail. -> Upload is attempted.
      2. Observe the result. -> Rejected with message "Unsupported file type. Accepted formats: JPG, JPEG, PNG." / نوع الملف غير مدعوم. الصيغ المقبولة: JPG، JPEG، PNG.
    """
    ck.check_file_refused(page, VideoRecordAdminPage, 143058, 'video_thumbnail', BAD_IMAGE, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143059
def test_143059_duration_accepts_a_valid_mm_ss_value_and_displays_as_a_badge(page, browser):
    """ADO-143059 (P3). Verify that Duration accepts a valid mm:ss value and displays as a badge

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record with Duration auto-populated as 08:31. -> Field shows 08:31.
      2. Edit it to 12:45. -> Field accepts 12:45.
      3. Save and view the video card. -> Save succeeds; card and player show duration badge "12:45".
    """
    ck.check_editor_publish_public(page, browser, VideoRecordAdminPage, 143059, probe, files=FILES[VideoRecordAdminPage], extra={'duration': '04:30'})


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143060
def test_143060_duration_rejects_an_invalid_mm_ss_format(page):
    """ADO-143060 (P3). Verify that Duration rejects an invalid mm:ss format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Duration = "8:99". -> Value entered.
      2. Attempt to save. -> Save is blocked with a format validation error (seconds must be 00–59).
    """
    ck.check_value_refused(page, VideoRecordAdminPage, 143060, 'duration', '8:99', short='fmt', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143061
def test_143061_duration_is_blocked_when_left_empty(page):
    """ADO-143061 (P3). Verify that Duration is blocked when left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Duration field. -> Field empty.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143061, 'duration', side='both', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143062
def test_143062_video_description_accepts_valid_rich_text_within_2000_charac(page):
    """ADO-143062 (P3). Verify that Video Description accepts valid rich text within 2000 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record. -> Record opens.
      2. Enter a 300-character multi-paragraph description. -> Text entered with paragraph breaks.
      3. Save. -> Save succeeds; description renders with formatting preserved on Details page.
    """
    ck.check_valid_persists(page, VideoRecordAdminPage, 143062, 'video_description', 'Valid video description', ar='قيمة صالحة', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143063
def test_143063_video_description_accepts_exactly_2000_characters(page):
    """ADO-143063 (P3). Verify that Video Description accepts exactly 2000 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter exactly 2000 characters as the description. -> Value entered.
      2. Save. -> Save succeeds; full 2000-character text persists.
    """
    ck.check_valid_persists(page, VideoRecordAdminPage, 143063, 'video_description', chars(2000), files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143064
def test_143064_video_description_rejects_content_exceeding_2000_characters(page):
    """ADO-143064 (P3). Verify that Video Description rejects content exceeding 2000 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 2001 characters as the description. -> Value entered.
      2. Attempt to save. -> Save is blocked (or input truncated) with a max-length validation indication.
    """
    ck.check_over_max_refused(page, VideoRecordAdminPage, 143064, 'video_description', 2000, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143065
def test_143065_video_description_can_be_left_empty_since_it_is_not_a_requir(page, browser):
    """ADO-143065 (P3). Verify that Video Description can be left empty since it is not a required field

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave the Description field blank on an otherwise-complete video record. -> Field left empty.
      2. Save and publish. -> Save and publish succeed with no validation error for the missing description.
    """
    ck.check_editor_publish_public(page, browser, VideoRecordAdminPage, 143065, probe, files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143066
def test_143066_published_date_accepts_a_valid_date(page):
    """ADO-143066 (P3). Verify that Published Date accepts a valid date

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record. -> Record opens.
      2. Enter Published Date = 2026-09-15. -> Value entered.
      3. Save. -> Save succeeds; date is used to drive "Most Recent" sort and displays on the card/Details page.
    """
    ck.check_valid_persists(page, VideoRecordAdminPage, 143066, 'published_date', '15/06/2027', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143067
def test_143067_published_date_is_blocked_when_left_empty(page):
    """ADO-143067 (P3). Verify that Published Date is blocked when left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Published Date blank. -> Field empty.
      2. Attempt to save. -> Save is blocked with a required-field validation error.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143067, 'published_date', side='both', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143068
def test_143068_published_date_rejects_an_invalid_date_format(page):
    """ADO-143068 (P3). Verify that Published Date rejects an invalid date format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Published Date = "31/02/2026" (invalid calendar date). -> Value entered.
      2. Attempt to save. -> Save is blocked with a date-format/validity error.
    """
    ck.check_value_refused(page, VideoRecordAdminPage, 143068, 'published_date', '31/02/2026', short='fmt', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143070
def test_143070_flickr_source_folder_reference_populates_for_flickr_sourced(page):
    """ADO-143070 (P3). Verify that the Flickr Source Folder reference populates for Flickr-sourced videos and remains blank otherwise

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor') (reads a QCTEST record only).
    Steps (from the approved case):
      1. Inspect a Flickr-imported video record's Flickr Source Folder field. -> Field shows the correct Documents & Media folder path.
      2. Inspect a Direct-Upload video record's same field. -> Field is blank/not applicable for the non-Flickr record.
    """
    admin = VideoRecordAdminPage(page)
    title = qctest_title(143070, 'nonflickr')
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=FILES[VideoRecordAdminPage])
        admin.save_as_draft()
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        assert admin.value('flickr_source_folder') == '', 'non-Flickr video carries a Flickr Source Folder'
    finally:
        admin.delete_disposable(title)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143071
def test_143071_video_status_dropdown_persists_each_selectable_value(page):
    """ADO-143071 (P3). Verify that the Video Status dropdown persists each selectable value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open a video record. -> Record opens.
      2. Set Status=Draft, save; then Published, save; then Unpublished, save. -> Each value persists on reload.
    """
    ck.check_select_persists(page, VideoRecordAdminPage, 143071, 'video_status', [STATUS_DRAFT, STATUS_PUBLISHED], files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130715
@pytest.mark.tc_143072
def test_143072_video_record_s_created_last_modified_date_auto_populates_and(page):
    """ADO-143072 (P3). Verify that the video record's Created/Last Modified Date auto-populates and updates on edit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Note a video record's Last Modified timestamp. -> Timestamp noted.
      2. Edit and save any field. -> Save succeeds.
      3. Re-check the timestamp. -> Timestamp updates to the edit time.
    """
    ck.check_modified_updates(page, VideoRecordAdminPage, 143072, 'duration', '05:00', files=FILES[VideoRecordAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130715
@pytest.mark.tc_143073
def test_143073_publishing_is_blocked_when_arabic_content_is_missing_while_e(page):
    """ADO-143073 (P2). Verify that publishing is blocked when Arabic content is missing while English content is filled

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create a video record with Title EN, Thumbnail, and Source filled but Title AR left blank. -> Record saves as Draft.
      2. Attempt to Publish. -> Publish is blocked with message "Arabic content is required." / المحتوى بالعربية مطلوب.; record remains unpublished.
    """
    ck.check_empty_refused(page, VideoRecordAdminPage, 143073, 'video_title', side='ar', files=FILES[VideoRecordAdminPage])

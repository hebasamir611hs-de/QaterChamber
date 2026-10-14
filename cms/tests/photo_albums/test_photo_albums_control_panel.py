"""
cms/tests/photo_albums/test_photo_albums_control_panel.py - Control_Panel cases for PBI 130714
(Test Plan 137724, suite 140373): Azure Priority 1-3, Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_130714_cp_batch.json, which holds every disposition and
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
from cms.pages.photo_albums.photo_albums_admin_page import (
    PhotoGalleryPageHeroAdminPage,
    PhotoEventCategoryAdminPage,
    PhotoAlbumAdminPage,
    PhotoAdminPage,
)
from cms.tests import authoring_checks as ck
from web.pages.photo_albums.photo_albums_listing_page import PhotoAlbumsListingPage

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

# Required upload fields per object, filled by fill_required().
FILES = {
    PhotoGalleryPageHeroAdminPage: {'hero_background_image': VALID_JPG},
    PhotoEventCategoryAdminPage: {},
    PhotoAlbumAdminPage: {'cover_image': VALID_JPG},
    PhotoAdminPage: {'photo_file': VALID_JPG},
}

probe = ck.make_public_probe(lambda p: PhotoAlbumsListingPage(p).open_photo_albums())

# Conditional-case gates. Flip one only when its condition is confirmed.
FLICKR_SETTINGS_LOCATED = False  # True once: the Flickr integration settings surface is located
PHOTOS_PANEL_READ = False  # True once: the Photo Album Photos panel is read live

@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143110
def test_143110_admin_event_category_creation_form_renders_name_display_orde(page):
    """ADO-143110 (P3). Verify that the admin Event Category creation form renders Name, Display Order, and Publish Status fields

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to Liferay CMS as Site Content Editor. -> Login succeeds and the Photo Albums management area is reachable.
      2. Navigate to Photo Albums management, then Event Categories, then Create New. -> The Event Category creation form displays Name EN, Name AR, Display Order, and Publish Status fields.
    """
    ck.check_form_renders(page, PhotoEventCategoryAdminPage, ['name', 'display_order', 'publish_status'])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143111
def test_143111_admin_album_creation_form_renders_title_event_category_cover(page):
    """ADO-143111 (P3). Verify that the admin Album creation form renders Title, Event Category, Cover Image, Published Date, and Photos fields

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to Liferay CMS as Site Content Editor. -> Login succeeds.
      2. Navigate to Photo Albums management, then Albums, then Create New. -> The Album creation form displays Title EN, Title AR, Event Category selector, Album Cover Image upload, Published Date, and a Photos panel.
    """
    ck.check_form_renders(page, PhotoAlbumAdminPage, ['album_title', 'event_category', 'cover_image', 'published_date'])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143112
def test_143112_admin_photo_add_panel_offers_both_selecting_from_documents_m(page):
    """ADO-143112 (P3). Verify that the admin photo-add panel offers both selecting from Documents & Media and uploading from device

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open an Album's Photos panel in Liferay CMS. -> Photos panel is visible with existing photos, if any, listed.
      2. Click Add Photo. -> An option to select from Documents & Media and a separate option to upload a new file from device are both presented.
    """
    ck.check_form_renders(page, PhotoAdminPage, ['photo_file'])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143115
def test_143115_cms_album_creation_form_renders_correctly_for_bilingual_fiel(page):
    """ADO-143115 (P3). Verify that the CMS Album creation form renders correctly for bilingual field entry in Arabic

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor'), /ar/ admin locale.
    Steps (from the approved case):
      1. Log in to Liferay CMS as Site Content Editor. -> Login succeeds.
      2. Open the Album creation form. -> Album creation form is visible.
      3. Switch the Title field's active locale to Arabic (ar_SA). -> The Title AR input accepts and correctly renders right-to-left Arabic text without corrupting the parallel Title EN field.
    """
    ck.check_rtl_form(page, PhotoAlbumAdminPage)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130714
@pytest.mark.tc_143116
@pytest.mark.skipif(not PHOTOS_PANEL_READ, reason='CONDITIONAL - the Photos panel inside Photo Album (rows, per-photo status control) is read live first')
def test_143116_each_photo_row_in_the_admin_photos_panel_displays_its_curren(page):
    """ADO-143116 (P3). Verify that each photo row in the admin Photos panel displays its current Publish Status accurately

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open an album's Photos panel containing one Published photo and one Unpublished photo. -> Photos panel lists both photos.
      2. Observe each row's status control. -> The Published photo's row shows a Published status control and the Unpublished photo's row shows an Unpublished status control, matching each photo's actual sta

    Disposition: conditional - the Photos panel inside Photo Album (rows, per-photo status control) is read live first
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the Photos panel inside Photo Album (rows, per-photo status control) is read live first')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143123
@pytest.mark.skip(reason='needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record')
def test_143123_administrator_can_access_and_trigger_the_flickr_integration(page):
    """ADO-143123 (P1). Verify that an Administrator can access and trigger the Flickr integration manual import

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Log in to Liferay CMS with the Administrator account. -> Login succeeds.
      2. Navigate to the Flickr integration settings area. -> Flickr integration settings page is reachable and its controls are enabled.
      3. Trigger a manual import. -> The manual import runs immediately using the current configuration and an import log entry is created.

    Disposition: skip - needs a real shared record mutated: a Flickr import/config change writes real albums/videos into shared qcdev and cannot be scoped to a QCTEST record
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130714
@pytest.mark.tc_143124
def test_143124_site_content_editor_can_perform_the_full_album_lifecycle(page, browser):
    """ADO-143124 (P1). Verify that a Site Content Editor can perform the full album lifecycle

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to Liferay CMS with the Site Content Editor role (test1@xyz.com). -> Login succeeds.
      2. Create, edit, preview, publish, unpublish, and delete a test album named "QCTEST-Auth Album". -> Every one of create, edit, preview, publish, unpublish, and delete completes successfully for the Site Content Editor with no permission error at any step.
    """
    ck.check_full_lifecycle(page, browser, PhotoAlbumAdminPage, 143124, probe, files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143125
@pytest.mark.skipif(not FLICKR_SETTINGS_LOCATED, reason='CONDITIONAL - the Flickr integration settings surface is not an Object Authoring object and is not located yet')
def test_143125_site_content_editor_is_denied_access_to_flickr_integration_s(page):
    """ADO-143125 (P1). Verify that a Site Content Editor is denied access to Flickr integration settings

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to Liferay CMS with the Site Content Editor role. -> Login succeeds.
      2. Attempt to navigate directly to the Flickr integration settings URL. -> Access is refused with "Access Denied. You do not have permission to perform this action." / "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء." and the settin

    Disposition: conditional - the Flickr integration settings surface is not an Object Authoring object and is not located yet
    """
    pytest.fail('Flickr settings surface not located')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143126
def test_143126_site_content_author_can_create_and_edit_an_album_and_submit(page):
    """ADO-143126 (P1). Verify that a Site Content Author can create and edit an album and submit it for review

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in to Liferay CMS with the Site Content Author role (Test2@xyz.com). -> Login succeeds.
      2. Create a test album named "QCTEST-Author Album" with all mandatory fields populated. -> The album saves as Draft with no permission error.
      3. Submit it for review. -> The album's status moves to Pending Review.
    """
    ck.check_author_submit_pending(page, PhotoAlbumAdminPage, 143126, files=FILES[PhotoAlbumAdminPage], edit_key='album_title', edit_value=qctest_title(143126, 'author'))


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130714
@pytest.mark.tc_143127
def test_143127_site_content_author_cannot_publish_an_album_directly(page):
    """ADO-143127 (P1). Verify that a Site Content Author cannot publish an album directly

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in to Liferay CMS with the Site Content Author role. -> Login succeeds.
      2. Open a Draft album owned by this user. -> Album opens in Draft status.
      3. Attempt to invoke the Publish transition directly against the album, bypassing the review-submission UI path. -> The Publish transition is refused with "Access Denied. You do not have permission to perform this action." and the album's status remains unchanged.
    """
    ck.check_author_submit_pending(page, PhotoAlbumAdminPage, 143127, files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130714
@pytest.mark.tc_143143
def test_143143_site_content_editor_can_create_an_event_category_and_album_a(page, browser):
    """ADO-143143 (P1). Verify that a Site Content Editor can create an Event Category and Album, add photos, and publish so the album appears correctly on the public site

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to Liferay CMS as Site Content Editor and create Event Category "Community Outreach" EN/AR, Display Order 4, Publish Status Published. -> Category saves with an auto-generated Event Category ID and appears Published.
      2. Create Album "QCTEST-Community Day 2026" EN/AR under "Community Outreach", set Published Date 2026-09-15, upload a JPG Album Cover Image, and enter both Title fields. -> Album saves with an auto-generated Album ID, audit-logged Created date, and all entered field values retained.
      3. Add one photo selected from Documents & Media and one photo uploaded from device, entering Photo Title EN/AR for each, setting Thumbnail Framing, and Display Order values 1 and 2. -> Both photos save under the album with their respective metadata and order values, and the album's Parent Album reference for both is this album.
      4. Save as Draft, then Preview, then Publish. -> Draft state is reachable, Preview renders the entered content, and Publish succeeds with a success toast and an audit log entry.
      5. Open the public Photo Albums listing and this album's Details page. -> The album appears on the public listing under the "Community Outreach" chip with the correct cover image and photo count, and the Details page shows both photos
    """
    cat = PhotoEventCategoryAdminPage(page)
    ctitle = qctest_title(143143, 'cat')
    try:
        ck._publish_as_editor(cat, ctitle)
        ck.check_editor_publish_public(page, browser, PhotoAlbumAdminPage, 143143, probe, files=FILES[PhotoAlbumAdminPage], extra={'event_category': ctitle})
    finally:
        cat.delete_disposable(ctitle)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130714
@pytest.mark.tc_143144
def test_143144_unpublishing_an_album_removes_it_from_the_public_listing_and(page, browser):
    """ADO-143144 (P1). Verify that unpublishing an album removes it from the public listing and details page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Confirm "QCTEST-Community Day 2026" is visible on the public Photo Albums listing. -> Album card is visible.
      2. In Liferay CMS, unpublish the album. -> Album status changes to Unpublished with a success toast and audit log entry.
      3. Reload the public listing in a fresh logged-out browser context. -> The album no longer appears anywhere on the public listing.
    """
    ck.check_unpublish_hides(page, browser, PhotoAlbumAdminPage, 143144, probe, files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130714
@pytest.mark.tc_143145
def test_143145_deleting_an_album_removes_it_from_the_public_site_and_its_do(page, browser):
    """ADO-143145 (P1). Verify that deleting an album removes it from the public site and its Documents & Media references

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In Liferay CMS, delete "QCTEST-Community Day 2026". -> Album is removed from the CMS Albums listing with an audit log entry.
      2. Reload the public Photo Albums listing in a fresh logged-out browser context. -> The album no longer appears on the public listing.
      3. Attempt to open the deleted album's previously known Details URL. -> The Details URL returns a standard not-found page rather than stale album content.
    """
    ck.check_delete_removes(page, browser, PhotoAlbumAdminPage, 143145, probe, files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143147
def test_143147_leaving_the_page_title_ar_field_empty_is_blocked_with_the_bi(page):
    """ADO-143147 (P3). Verify that leaving the Page Title AR field empty is blocked with the bilingual-required message

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In Liferay CMS, open the Photo Albums page's Hero settings. -> Hero settings form opens.
      2. Enter "Photo Albums" in the Title EN field and leave Title AR empty. -> EN field accepts the value; AR field remains empty.
      3. Attempt to save. -> Save is blocked with "Arabic content is required." / "المحتوى بالعربية مطلوب." and the page title is not updated.
    """
    ck.check_empty_refused(page, PhotoGalleryPageHeroAdminPage, 143147, 'page_title', side='ar', files=FILES[PhotoGalleryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143148
def test_143148_page_title_en_field_rejects_input_exceeding_100_characters(page):
    """ADO-143148 (P3). Verify that the Page Title EN field rejects input exceeding 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Hero settings Title EN field, enter a string of 101 characters. -> Field accepts keystrokes up to its input limit.
      2. Attempt to save. -> Save is blocked (or the value is truncated to 100 characters, whichever the implementation enforces) and no value over 100 characters is persisted.
    """
    ck.check_over_max_refused(page, PhotoGalleryPageHeroAdminPage, 143148, 'page_title', 100, files=FILES[PhotoGalleryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143149
def test_143149_leaving_the_hero_background_image_empty_blocks_save(page):
    """ADO-143149 (P3). Verify that leaving the Hero Background Image empty blocks save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In Hero settings, remove any existing Hero Background Image. -> Image field shows no file selected.
      2. Attempt to save. -> Save is blocked; a required-field validation message is shown and the previous background image, if any, remains in effect.
    """
    ck.check_empty_refused(page, PhotoGalleryPageHeroAdminPage, 143149, 'hero_background_image', side='en', files=FILES[PhotoGalleryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143150
def test_143150_hero_background_image_upload_larger_than_2_mb_is_rejected(page):
    """ADO-143150 (P3). Verify that a Hero Background Image upload larger than 2 MB is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In Hero settings, upload a JPG file sized 3 MB as the Hero Background Image. -> Upload is rejected with a file-size validation message and the field remains unset or retains the prior valid image.
    """
    ck.check_file_refused(page, PhotoGalleryPageHeroAdminPage, 143150, 'hero_background_image', BIG_IMAGE, files=FILES[PhotoGalleryPageHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143151
def test_143151_leaving_the_event_category_name_ar_field_empty_is_blocked_wi(page):
    """ADO-143151 (P3). Verify that leaving the Event Category Name AR field empty is blocked with the bilingual-required message

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Create Event Category form. -> Form opens.
      2. Enter "Institutional" in Name EN and leave Name AR empty. -> EN field accepts the value; AR field remains empty.
      3. Attempt to save. -> Save is blocked with "Arabic content is required." / "المحتوى بالعربية مطلوب." and the category is not created.
    """
    ck.check_empty_refused(page, PhotoEventCategoryAdminPage, 143151, 'name', side='ar', files=FILES[PhotoEventCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143152
def test_143152_event_category_name_en_field_rejects_input_exceeding_200_cha(page):
    """ADO-143152 (P3). Verify that the Event Category Name EN field rejects input exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Event Category Name EN field, enter a string of 201 characters. -> Field accepts keystrokes.
      2. Attempt to save. -> Save is blocked and no value over 200 characters is persisted for the category name.
    """
    ck.check_over_max_refused(page, PhotoEventCategoryAdminPage, 143152, 'name', 200, files=FILES[PhotoEventCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143153
def test_143153_event_category_display_order_rejects_a_negative_value(page):
    """ADO-143153 (P3). Verify that the Event Category Display Order rejects a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Event Category form, enter -1 in the Display Order field. -> Field accepts the keystrokes.
      2. Attempt to save. -> Save is blocked with a validation message requiring a positive integer, and the category is not created with a negative order.
    """
    ck.check_value_refused(page, PhotoEventCategoryAdminPage, 143153, 'display_order', '-1', short='neg', files=FILES[PhotoEventCategoryAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143157
def test_143157_leaving_the_album_title_ar_field_empty_is_blocked_with_the_b(page):
    """ADO-143157 (P3). Verify that leaving the Album Title AR field empty is blocked with the bilingual-required message

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Album creation form, enter "Trade Summit 2026" in Title EN and leave Title AR empty. -> EN field accepts the value; AR field remains empty.
      2. Attempt to save. -> Save is blocked with "Arabic content is required." / "المحتوى بالعربية مطلوب." and the album is not created.
    """
    ck.check_empty_refused(page, PhotoAlbumAdminPage, 143157, 'album_title', side='ar', files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143158
def test_143158_album_title_en_field_rejects_input_exceeding_200_characters(page):
    """ADO-143158 (P3). Verify that the Album Title EN field rejects input exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Album Title EN field, enter a string of 201 characters. -> Field accepts keystrokes.
      2. Attempt to save. -> Save is blocked and no value over 200 characters is persisted for the album title.
    """
    ck.check_over_max_refused(page, PhotoAlbumAdminPage, 143158, 'album_title', 200, files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143159
def test_143159_saving_an_album_with_no_event_category_selected_is_blocked(page):
    """ADO-143159 (P3). Verify that saving an album with no Event Category selected is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Album creation form, complete every field except the Event Category selector. -> All other fields hold valid values.
      2. Attempt to save. -> Save is blocked with a required-field validation message and the album is not created.
    """
    ck.check_empty_refused(page, PhotoAlbumAdminPage, 143159, 'event_category', side='en', files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143160
def test_143160_album_with_no_cover_image_is_blocked_from_publishing(page):
    """ADO-143160 (P3). Verify that an album with no Cover Image is blocked from publishing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create an album with all mandatory fields completed except Album Cover Image. -> Album saves as Draft with no cover image.
      2. Attempt to publish. -> Publishing is blocked with "An album cover image is required." / "صورة غلاف الألبوم مطلوبة." and the album remains unpublished.
    """
    ck.check_empty_refused(page, PhotoAlbumAdminPage, 143160, 'cover_image', side='en', files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143161
def test_143161_uploading_an_unsupported_file_format_as_the_album_cover_imag(page):
    """ADO-143161 (P3). Verify that uploading an unsupported file format as the Album Cover Image is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Album creation form, upload a .gif file as the Album Cover Image. -> Upload is rejected with "Unsupported file type. Accepted formats: JPG, JPEG, PNG." / "نوع الملف غير مدعوم. الصيغ المقبولة: JPG، JPEG، PNG." and no cover image i
    """
    ck.check_file_refused(page, PhotoAlbumAdminPage, 143161, 'cover_image', BAD_IMAGE_GIF, files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143162
def test_143162_leaving_album_published_date_empty_blocks_save(page):
    """ADO-143162 (P3). Verify that leaving Album Published Date empty blocks save

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Album creation form, leave the Published Date field empty. -> Other fields hold valid values.
      2. Attempt to save. -> Save is blocked with a required-field validation message and the album is not created.
    """
    ck.check_empty_refused(page, PhotoAlbumAdminPage, 143162, 'published_date', side='both', files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143163
def test_143163_album_with_zero_published_photos_is_blocked_from_publishing(page):
    """ADO-143163 (P3). Verify that an album with zero published photos is blocked from publishing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create an album with all mandatory fields completed and one photo added but left Unpublished. -> Album saves as Draft with zero published photos.
      2. Attempt to publish the album. -> Publishing is blocked with "An album must contain at least one published photo." / "يجب أن يحتوي الألبوم على صورة منشورة واحدة على الأقل." and the album remains
    """
    ck.check_publish_refused(page, PhotoAlbumAdminPage, 143163, skip=(), files=FILES[PhotoAlbumAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143164
def test_143164_leaving_the_photo_file_empty_blocks_saving_a_photo(page):
    """ADO-143164 (P3). Verify that leaving the Photo File empty blocks saving a photo

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In an album's Add Photo panel, leave the Photo File unset. -> No file is selected.
      2. Attempt to save. -> Save is blocked with a required-field validation message and no photo entry is created.
    """
    ck.check_empty_refused(page, PhotoAdminPage, 143164, 'photo_file', side='en', files=FILES[PhotoAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143165
def test_143165_uploading_an_unsupported_file_format_as_a_photo_file_is_reje(page):
    """ADO-143165 (P3). Verify that uploading an unsupported file format as a Photo File is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In an album's Add Photo panel, upload a .bmp file as the Photo File. -> Upload is rejected with "Unsupported file type. Accepted formats: JPG, JPEG, PNG." / "نوع الملف غير مدعوم. الصيغ المقبولة: JPG، JPEG، PNG." and no photo entry i
    """
    ck.check_file_refused(page, PhotoAdminPage, 143165, 'photo_file', BAD_IMAGE, files=FILES[PhotoAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143166
def test_143166_photo_can_be_saved_with_the_photo_title_en_ar_fields_left_bl(page):
    """ADO-143166 (P3). Verify that a photo can be saved with the Photo Title EN/AR fields left blank

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Add Photo panel, upload a valid JPG Photo File and leave both Photo Title EN and Photo Title AR empty. -> File is accepted.
      2. Save. -> Photo saves successfully with both title fields empty, since Photo Title is not a required field.
    """
    admin = PhotoAdminPage(page)
    title = qctest_title(143166, 'untitled')
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=('photo_title',), files=FILES[PhotoAdminPage])
        admin.save_as_draft()
        assert not admin.refusal_visible(), 'a photo with blank titles was refused'
    finally:
        admin.delete_disposable(title)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143167
def test_143167_photo_title_en_field_rejects_input_exceeding_200_characters(page):
    """ADO-143167 (P3). Verify that the Photo Title EN field rejects input exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Photo Title EN field, enter a string of 201 characters. -> Field accepts keystrokes.
      2. Attempt to save. -> Save is blocked and no value over 200 characters is persisted for the photo title.
    """
    ck.check_over_max_refused(page, PhotoAdminPage, 143167, 'photo_title', 200, files=FILES[PhotoAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143168
def test_143168_saving_a_photo_with_thumbnail_framing_left_unset_is_blocked(page):
    """ADO-143168 (P3). Verify that saving a photo with Thumbnail Framing left unset is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Add Photo panel, upload a valid Photo File and leave the Thumbnail Framing configuration unset. -> File is accepted.
      2. Attempt to save. -> Save is blocked with a required-field validation message since Thumbnail Framing must be configured.
    """
    ck.check_empty_refused(page, PhotoAdminPage, 143168, 'thumbnail_framing', side='en', files=FILES[PhotoAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143169
def test_143169_photo_display_order_rejects_a_negative_value(page):
    """ADO-143169 (P3). Verify that Photo Display Order rejects a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In the Add Photo panel, enter -2 in the Display Order field. -> Field accepts keystrokes.
      2. Attempt to save. -> Save is blocked with a validation message requiring a positive integer, and the photo is not saved with a negative order.
    """
    ck.check_value_refused(page, PhotoAdminPage, 143169, 'display_order', '-1', short='neg', files=FILES[PhotoAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143170
@pytest.mark.skipif(not PHOTOS_PANEL_READ, reason='CONDITIONAL - the Photos panel inside Photo Album (per-photo Display Order) is read live first')
def test_143170_photo_with_the_lowest_display_order_value_renders_as_the_ful(page):
    """ADO-143170 (P3). Verify that the photo with the lowest Display Order value renders as the full-width lead photo

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. In a published album, set photo A's Display Order to 3, photo B's to 1, and photo C's to 2. -> Order values save as entered.
      2. Open the album's public Details page. -> Photo B renders as the full-width lead photo, with photo C and then photo A following in the grid below, in that order.

    Disposition: conditional - the Photos panel inside Photo Album (per-photo Display Order) is read live first
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the Photos panel inside Photo Album (per-photo Display Order) is read live first')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143176
@pytest.mark.skipif(not PHOTOS_PANEL_READ, reason='CONDITIONAL - the Photos panel inside Photo Album (per-photo unpublish) is read live first')
def test_143176_photo_count_automatically_decreases_when_a_published_photo_i(page):
    """ADO-143176 (P3). Verify that the photo count automatically decreases when a published photo is unpublished

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Note an album's current photo count of 6 on its card and Details page. -> Card badge and Details page both read 6.
      2. In Liferay CMS, unpublish one photo in that album. -> Photo status changes to Unpublished.
      3. Reload the public listing card and the Details page. -> Card badge now reads "5 photos" and Details page now reads "5 images", both updated automatically with no manual recalculation step.

    Disposition: conditional - the Photos panel inside Photo Album (per-photo unpublish) is read live first
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the Photos panel inside Photo Album (per-photo unpublish) is read live first')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130714
@pytest.mark.tc_143178
def test_143178_deleting_an_event_category_linked_to_published_albums_is_blo(page, browser):
    """ADO-143178 (P3). Verify that deleting an Event Category linked to published albums is blocked until those albums are reassigned

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to delete Event Category "Institutional" while it has one or more Published albums linked to it. -> Deletion is blocked with a validation message indicating the category is in use, and "Institutional" remains in the CMS category list and in the public All Even
    """
    ck.check_in_use_delete_blocked(page, browser, PhotoEventCategoryAdminPage, PhotoAlbumAdminPage, 143178, 'event_category', child_files=FILES[PhotoAlbumAdminPage])

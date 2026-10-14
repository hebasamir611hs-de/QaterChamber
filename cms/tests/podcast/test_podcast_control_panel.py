"""
cms/tests/podcast/test_podcast_control_panel.py - Control_Panel cases for PBI 130713
(Test Plan 137724, suite 140372): Azure Priority 1-3, Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_130713_cp_batch.json, which holds every disposition and
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
from cms.pages.podcast.podcast_admin_page import (
    PodcastShowConfigurationAdminPage,
    PodcastPlatformLinkAdminPage,
    PodcastEpisodeAdminPage,
    PodcastEpisodeAudioAdminPage,
    PodcastSubscriberAdminPage,
)
from cms.tests import authoring_checks as ck
from web.pages.podcast.podcast_page import PodcastPage

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
VALID_MP3 = str(FIXTURES / 'valid_episode_audio.mp3')
BAD_AUDIO = str(FIXTURES / 'unsupported_episode_audio.wma')

# Required upload fields per object, filled by fill_required().
FILES = {
    PodcastShowConfigurationAdminPage: {'hero_background_image': VALID_JPG, 'hero_illustration': VALID_PNG, 'host_image': VALID_JPG},
    PodcastPlatformLinkAdminPage: {'platform_icon': VALID_PNG},
    PodcastEpisodeAdminPage: {'episode_artwork': VALID_JPG},
    PodcastEpisodeAudioAdminPage: {'episode_artwork': VALID_JPG, 'audio_file': VALID_MP3},
    PodcastSubscriberAdminPage: {},
}

probe = ck.make_public_probe(lambda p: PodcastPage(p).open_podcast())

# Conditional-case gates. Flip one only when its condition is confirmed.
ADMINISTRATOR_ACCOUNT_RULED = False  # True once: QA Manager ruled which account stands for 'Administrator'
AUDIT_LOG_LOCATED = False  # True once: the audit-log surface is located
EPISODE_PUBLISH_EMAIL_CLEARED = False  # True once: QA Manager confirmed publishing a QCTEST episode may email qcdev's subscriber list
QCTEST_SUBMISSION_PATH = False  # True once: a QCTEST submission/subscriber can be created and deleted by exact reference
SINGLETON_PUBLISH_CLEARED = False  # True once: confirmed live that publishing a QCTEST entry of a page-level object does not displace the live QCDEMO entry
WORKFLOW_ENDPOINT_LOCATED = False  # True once: the direct workflow-transition request is located

@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_130713
@pytest.mark.tc_143523
def test_143523_control_panel_podcast_admin_forms_render_correctly_in_arabic(page):
    """ADO-143523 (P3). Verify that Control Panel Podcast admin forms render correctly in Arabic (RTL)

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor'), /ar/ admin locale for that request only.
    Steps (from the approved case):
      1. Open Podcast Episode admin form in AR UI locale. -> AR field labels/inputs render RTL, EN fields remain LTR within the form.
      2. Save a change. -> Liferay generic success toast displays in Arabic, RTL.
    """
    ck.check_rtl_form(page, PodcastEpisodeAdminPage)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143535
@pytest.mark.skipif(not ADMINISTRATOR_ACCOUNT_RULED, reason='CONDITIONAL - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account; the unsubscribe step also needs a QCTEST subscriber')
def test_143535_administrator_can_view_filter_export_and_manually_unsubscrib(page):
    """ADO-143535 (P2). Verify that Administrator can view, filter, export and manually unsubscribe Podcast subscribers

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Log in as Administrator, open Podcast Subscribers panel. -> list loads with email/status/subscription date/unsubscription date columns.
      2. Apply a status filter, then export CSV, then manually unsubscribe one record. -> all three actions succeed, no permission error.

    Disposition: conditional - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account; the unsubscribe step also needs a QCTEST subscriber
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account; the unsubscribe step also needs a QCTEST subscriber')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143536
def test_143536_unauthenticated_request_to_the_podcast_subscribers_admin_pan(page, browser):
    """ADO-143536 (P1). Verify that an unauthenticated request to the Podcast Subscribers admin panel is denied

    Account: none - fresh logged-out context (new_context(browser, use_auth_state=False)).
    Steps (from the approved case):
      1. Without logging in, navigate directly to the Subscribers panel admin URL. -> redirected to CMS login, panel content not rendered.
    """
    ck.check_anonymous_denied(browser, PodcastSubscriberAdminPage)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143537
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only')
def test_143537_site_content_editor_can_publish_an_episode_directly(page, browser):
    """ADO-143537 (P2). Verify that Site Content Editor can publish an episode directly

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as `test1@xyz.com` (Site Content Editor); Create episode `QCTEST-EP-201`, fill all mandatory fields, click Publish. -> episode status = Published immediately, no review step required.

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only
    """
    ck.check_editor_publish_public(page, browser, PodcastEpisodeAdminPage, 143537, probe, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143538
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated (subscription-band half); the platform-link half alone is safe')
def test_143538_site_content_editor_can_manage_platform_follow_links_and_the(page, browser):
    """ADO-143538 (P3). Verify that Site Content Editor can manage Platform Follow Links and the subscription band

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Editor, edit an existing Platform Follow Link's Display Order and Active Status, save. -> change applied without an "Access Denied" message.
      2. Edit Subscription Band heading text, publish. -> change applied.

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated (subscription-band half); the platform-link half alone is safe
    """
    ck.check_editor_publish_public(page, browser, PodcastPlatformLinkAdminPage, 143538, probe, files=FILES[PodcastPlatformLinkAdminPage])
    ck.check_editor_publish_public(page, browser, PodcastShowConfigurationAdminPage, 143538, probe, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143539
def test_143539_site_content_author_can_create_and_edit_an_assigned_episode(page):
    """ADO-143539 (P2). Verify that Site Content Author can create and edit an assigned episode with bilingual metadata but cannot publish it directly

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in as `Test2@xyz.com` (Site Content Author); Create episode `QCTEST-EP-202`, fill EN+AR Title/Description → saved as Draft successfully; Attempt to click Publish. -> action blocked / routed to "submit for review" instead of direct publish, status remains not-Published.
    """
    ck.check_author_submit_pending(page, PodcastEpisodeAdminPage, 143539, files=FILES[PodcastEpisodeAdminPage], edit_key='brief_description', edit_value='QCTEST author description')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143540
def test_143540_site_content_author_cannot_manage_podcast_subscribers(page):
    """ADO-143540 (P2). Verify that Site Content Author cannot manage Podcast subscribers

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in as Site Content Author, attempt to open the Podcast Subscribers panel. -> "Access Denied. You do not have permission to perform this action." (MSG-10) shown, panel content not rendered.
    """
    ck.check_role_cannot_author(page, PodcastSubscriberAdminPage, ROLE_AUTHOR)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130713
@pytest.mark.tc_143541
@pytest.mark.skipif(not WORKFLOW_ENDPOINT_LOCATED, reason='CONDITIONAL - the direct workflow-transition endpoint is not documented - automate once located (read the request the UI sends)')
def test_143541_site_content_author_cannot_bypass_the_publish_restriction_vi(page):
    """ADO-143541 (P1). Verify that Site Content Author cannot bypass the publish restriction via a direct workflow-transition request

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. As Site Content Author, attempt to force the episode's status to Published via a direct workflow-transition action (not the disabled UI button). -> transition rejected, status remains Draft/Pending Review, action logged as denied.

    Disposition: conditional - the direct workflow-transition endpoint is not documented - automate once located (read the request the UI sends)
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the direct workflow-transition endpoint is not documented - automate once located (read the request the UI sends)')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143604
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only; the inbox check also needs a mailbox the suite can read')
def test_143604_publishing_a_new_episode_sends_the_new_episode_notification(page, browser):
    """ADO-143604 (P1). Verify that publishing a new episode sends the New Episode notification email to all active subscribers

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. With ≥2 Active subscribers seeded, publish a new episode "Episode 25" from the CMS. -> Confirm both active subscribers receive the New Episode notification email containing `{{episode_title}}`, `{{episode_number}}`, `{{episode_description}}`, `{{p

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only; the inbox check also needs a mailbox the suite can read
    """
    ck.check_editor_publish_public(page, browser, PodcastEpisodeAdminPage, 143604, probe, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143613
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_143613_publishing_the_podcast_page_draft_published_makes_content_vi(page, browser):
    """ADO-143613 (P1). Verify that publishing the Podcast page (Draft → Published) makes content visible on the public site

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Site Content Editor, edit Podcast page fields, click Publish; Open `/podcast` in a fresh logged-out browser context. -> the newly published Show Title/Description/host/links are visible.

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, PodcastShowConfigurationAdminPage, 143613, probe, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143615
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_143615_re_publishing_an_edited_podcast_page_shows_the_new_value_not(page, browser):
    """ADO-143615 (P2). Verify that re-publishing an edited Podcast page shows the new value, not a stale cached one

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Edit the already-published Show Description to a new value, Publish; Reload `/podcast` in a fresh logged-out context. -> the new description text is shown, the old text is gone (no stale cache).

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_republish_updates(page, browser, PodcastShowConfigurationAdminPage, 143615, probe, 'host_name', 'QCTEST-143615 Host', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143617
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_143617_unpublishing_the_podcast_page_removes_it_from_public_visibil(page, browser):
    """ADO-143617 (P1). Verify that unpublishing the Podcast page removes it from public visibility

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. As Site Content Editor, Unpublish the Podcast page; In a fresh logged-out browser context, navigate to `/podcast`. -> page is not visible to the visitor (no stale 200 with old content).

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_unpublish_hides(page, browser, PodcastShowConfigurationAdminPage, 143617, probe, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143618
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only')
def test_143618_publishing_a_new_episode_draft_published_makes_it_visible_on(page, browser):
    """ADO-143618 (P1). Verify that publishing a new episode (Draft → Published) makes it visible on the public episode list

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create+publish episode `QCTEST-EP-210`; Open `/podcast` in a fresh logged-out context. -> episode appears in the Latest Episodes list with its artwork/title/description.

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only
    """
    ck.check_editor_publish_public(page, browser, PodcastEpisodeAdminPage, 143618, probe, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143619
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only')
def test_143619_re_publishing_an_edited_episode_shows_the_updated_fields_on(page, browser):
    """ADO-143619 (P2). Verify that re-publishing an edited episode shows the updated fields on the public listing, not stale ones

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Edit `QCTEST-EP-210`'s title, re-publish; Reload `/podcast` logged-out. -> the updated title displays, old title is gone.

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only
    """
    ck.check_republish_updates(page, browser, PodcastEpisodeAdminPage, 143619, probe, 'brief_description', 'QCTEST-143619 updated', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143620
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only')
def test_143620_unpublishing_an_episode_removes_it_from_the_public_listing(page, browser):
    """ADO-143620 (P1). Verify that unpublishing an episode removes it from the public listing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Unpublish `QCTEST-EP-210`; Reload `/podcast` in a fresh logged-out context. -> the episode row is gone from the Latest Episodes list.

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only
    """
    ck.check_unpublish_hides(page, browser, PodcastEpisodeAdminPage, 143620, probe, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143621
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only')
def test_143621_deleting_an_episode_removes_it_from_both_the_public_listing(page, browser):
    """ADO-143621 (P2). Verify that deleting an episode removes it from both the public listing and the admin list with no broken reference

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Delete `QCTEST-EP-210` from the admin episode list; Confirm it no longer appears in the admin grid; Reload `/podcast` logged-out. -> episode is absent, no broken image/link/placeholder left in its place.

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only
    """
    ck.check_delete_removes(page, browser, PodcastEpisodeAdminPage, 143621, probe, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143629
def test_143629_episode_without_a_playable_source_cannot_be_published(page):
    """ADO-143629 (P2). Verify that an episode without a playable source cannot be published

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create an episode with no Audio File and no Embed Link; Attempt to Publish. -> publish is blocked, status remains Draft.
    """
    ck.check_publish_refused(page, PodcastEpisodeAdminPage, 143629, skip=('audio_file', 'embed_link'), files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_130713
@pytest.mark.tc_143630
def test_143630_setting_both_an_uploaded_audio_file_and_an_embed_link_on_the(page):
    """ADO-143630 (P2). Verify that setting both an uploaded audio file and an embed link on the same episode is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. On an episode, upload an audio file AND enter an embed link; Attempt to save. -> save is rejected, the two options remain mutually exclusive, no episode record is created/updated with both set.
    """
    ck.check_publish_refused(page, PodcastEpisodeAdminPage, 143630, skip=(), files=FILES[PodcastEpisodeAdminPage], extra={'audio_file': VALID_MP3})


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143631
def test_143631_publishing_without_required_arabic_content_is_blocked(page):
    """ADO-143631 (P1). Verify that publishing without required Arabic content is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create an episode with the English Title/Description filled but the Arabic fields left empty; Attempt to Publish. -> "Arabic content is required." / "المحتوى بالعربية مطلوب." (MSG-7) shown, publish blocked.
    """
    admin = PodcastEpisodeAdminPage(page)
    title = qctest_title(143631, 'no-ar')
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=True, files=FILES[PodcastEpisodeAdminPage])
        admin.fill('episode_title', '', locale='ar')
        admin.fill('brief_description', '', locale='ar')
        admin.submit_for_review()
        assert admin.refusal_visible(), 'publish without Arabic content raised no refusal'
        assert admin.status_of(title, ROLE_EDITOR) != STATUS_PUBLISHED
    finally:
        admin.delete_disposable(title)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143632
@pytest.mark.skip(reason='needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see')
def test_143632_toggling_featured_on_home_page_on_one_episode_unsets_any_pre(page):
    """ADO-143632 (P2). Verify that toggling Featured on Home Page on one episode unsets any previously featured episode

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Confirm Episode A is currently Featured; Toggle Featured = true on Episode B, save → Episode B becomes Featured; Reopen Episode A's record. -> its Featured toggle is now false; only one episode is Featured across the whole set.

    Disposition: skip - needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143634
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_143634_newly_subscribed_record_appears_in_the_admin_subscriber_list(page):
    """ADO-143634 (P2). Verify that a newly subscribed record appears in the admin subscriber list with status Active and its subscription date

    Account: none - fresh logged-out context (new_context(browser, use_auth_state=False)) then Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Subscribe `list.check@example.com` on the public page; Open the admin Podcast Subscribers panel. -> the record appears with status Active and today's subscription date.

    Disposition: conditional - needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143635
@pytest.mark.skipif(not ADMINISTRATOR_ACCOUNT_RULED, reason='CONDITIONAL - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')
def test_143635_filtering_the_subscriber_list_by_status_returns_only_matchin(page):
    """ADO-143635 (P3). Verify that filtering the subscriber list by status returns only matching subscribers

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Seed 2 Active and 1 Unsubscribed subscriber; Apply filter Status=Unsubscribed. -> only the 1 Unsubscribed record is shown, the 2 Active records are excluded.

    Disposition: conditional - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143636
@pytest.mark.skipif(not ADMINISTRATOR_ACCOUNT_RULED, reason='CONDITIONAL - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')
def test_143636_filtering_the_subscriber_list_by_date_range_returns_only_mat(page):
    """ADO-143636 (P3). Verify that filtering the subscriber list by date range returns only matching subscribers

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Seed subscribers with different subscription dates; Apply a date-range filter covering only one subscriber's date. -> only that subscriber displays.

    Disposition: conditional - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143637
@pytest.mark.skipif(not ADMINISTRATOR_ACCOUNT_RULED, reason='CONDITIONAL - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')
def test_143637_searching_the_subscriber_list_by_email_address_returns_only(page):
    """ADO-143637 (P3). Verify that searching the subscriber list by email address returns only the matching subscriber

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Search `list.check@example.com`. -> Only that record is returned; other subscribers are excluded.

    Disposition: conditional - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143638
@pytest.mark.skipif(not ADMINISTRATOR_ACCOUNT_RULED, reason='CONDITIONAL - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')
def test_143638_exporting_the_filtered_subscriber_list_produces_a_csv_with_a(page):
    """ADO-143638 (P2). Verify that exporting the filtered subscriber list produces a CSV with all required columns

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Apply a status filter; Click Export. -> a CSV file downloads containing exactly the filtered subscribers with columns email address, status, subscription date, unsubscription date.

    Disposition: conditional - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143639
@pytest.mark.skipif(not QCTEST_SUBMISSION_PATH, reason='CONDITIONAL - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')
def test_143639_admin_can_manually_set_a_subscriber_to_unsubscribed(page):
    """ADO-143639 (P2). Verify that an admin can manually set a subscriber to Unsubscribed

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. In the admin panel, select an Active subscriber and choose "Unsubscribe". -> Status is set to Unsubscribed, un-subscription date recorded, Unsubscribe Confirmation email sent to that address, and the address stops receiving future Podcas

    Disposition: conditional - the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the case names Administrator; the eight provisioned roles have no Administrator and the brief bars TEST_USER for lifecycle/permission cases - needs a QA Manager ruling on the account; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143640
@pytest.mark.skipif(not AUDIT_LOG_LOCATED, reason='CONDITIONAL - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')
def test_143640_any_subscriber_record_change_is_audit_logged_with_a_timestam(page):
    """ADO-143640 (P3). Verify that any subscriber record change is audit-logged with a timestamp and the acting admin

    Account: Administrator (named by the case; no provisioned role - TEST_USER is barred by the brief).
    Steps (from the approved case):
      1. Perform a manual unsubscribe action as a named admin user; Open the audit log. -> an entry exists recording the action, timestamp, and the acting user's identity.

    Disposition: conditional - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143671
def test_143671_save_as_draft_on_the_podcast_page_stores_changes_without_pub(page, browser):
    """ADO-143671 (P2). Verify that Save as Draft on the Podcast page stores changes without publishing them

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Edit Show Description, click "Save as Draft"; Reload `/podcast` logged-out. -> old published description still shows (draft not visible publicly); reopening the admin form shows the draft change retained.
    """
    ck.check_draft_not_public(page, browser, PodcastShowConfigurationAdminPage, 143671, probe, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143672
def test_143672_preview_on_the_podcast_page_shows_draft_changes_without_affe(page, browser):
    """ADO-143672 (P2). Verify that Preview on the Podcast page shows draft changes without affecting the live public page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Save Show Description as Draft, click Preview → preview view shows the new draft text. -> In a separate logged-out context, `/podcast` still shows the old published text.
    """
    ck.check_preview_draft(page, browser, PodcastShowConfigurationAdminPage, 143672, probe, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143673
def test_143673_creating_a_new_episode_via_create_episode_stores_it_as_draft(page):
    """ADO-143673 (P3). Verify that creating a new episode via Create Episode stores it as Draft by default

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Click "Create Episode", fill mandatory fields, click Save (not Publish). -> Episode status = Draft; not visible on the public listing.
    """
    ck.check_default_draft(page, PodcastEpisodeAdminPage, 143673, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130713
@pytest.mark.tc_143675
def test_143675_adding_a_new_active_platform_follow_link_appears_in_the_hero(page, browser):
    """ADO-143675 (P2). Verify that adding a new active Platform Follow Link appears in the hero in its configured display order

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add a new platform link (e.g. "YouTube"), Display Order = 1, Active = true, publish; Open `/podcast`. -> the new button appears first among the platform buttons, per Display Order.
    """
    ck.check_editor_publish_public(page, browser, PodcastPlatformLinkAdminPage, 143675, probe, files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143676
def test_143676_setting_a_platform_follow_link_s_active_status_to_false_remo(page, browser):
    """ADO-143676 (P2). Verify that setting a Platform Follow Link's Active Status to false removes it from the public hero

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set an existing active platform link's Active Status = false, publish; Open `/podcast` logged-out. -> that button no longer displays.
    """
    admin = PodcastPlatformLinkAdminPage(page)
    ctx, anon = ck._anon_page(browser)
    title = qctest_title(143676, 'pub')
    try:
        ck._publish_as_editor(admin, title, files=FILES[PodcastPlatformLinkAdminPage])
        assert probe(anon, title)
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        admin.unpublish_to_edit_as_draft()
        admin.set_flag('active_status', False)
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert not probe(anon, title, False), 'Active Status off but the link is still on the public hero'
    finally:
        admin.delete_disposable(title)
        ck._close(ctx)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143677
def test_143677_re_activating_a_platform_follow_link_restores_its_button_on(page, browser):
    """ADO-143677 (P3). Verify that re-activating a Platform Follow Link restores its button on the public hero

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set the same link's Active Status back to true, publish; Reload `/podcast`. -> the button reappears in its configured Display Order position.
    """
    admin = PodcastPlatformLinkAdminPage(page)
    ctx, anon = ck._anon_page(browser)
    title = qctest_title(143677, 'pub')
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=False, files=FILES[PodcastPlatformLinkAdminPage])
        admin.submit_for_review()
        assert admin.status_of(title, ROLE_EDITOR) == STATUS_PUBLISHED
        assert not probe(anon, title, False)
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        admin.unpublish_to_edit_as_draft()
        admin.set_flag('active_status', True)
        admin.submit_for_review()
        assert probe(anon, title), 're-activated link did not return to the public hero'
    finally:
        admin.delete_disposable(title)
        ck._close(ctx)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130713
@pytest.mark.tc_143680
@pytest.mark.skipif(not EPISODE_PUBLISH_EMAIL_CLEARED, reason='CONDITIONAL - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only')
def test_143680_editing_a_published_episode_s_brief_description_and_re_publi(page, browser):
    """ADO-143680 (P2). Verify that editing a published episode's Brief Description and re-publishing updates the value visitors see, confirmed on both EN and AR locales

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Edit the EN Brief Description of a published episode, re-publish; Reload `/podcast` (EN) logged-out → new EN text shows; Reload `/ar/podcast` logged-out. -> AR text (previously unaffected by the EN-only edit) still renders correctly, no cross-locale corruption.

    Disposition: conditional - publishing a QCTEST episode may fire the New Episode email to every Active subscriber on qcdev - automate only once the QA Manager confirms that list holds test addresses only
    """
    ck.check_republish_updates(page, browser, PodcastEpisodeAdminPage, 143680, probe, 'brief_description', 'QCTEST-143680 updated', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143681
def test_143681_show_title_accepts_a_valid_value_within_150_characters(page):
    """ADO-143681 (P3). Verify that Show Title accepts a valid value within 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Qatar Chamber Podcast"` (22 chars) in Show Title. -> Save → field accepts the value; saves successfully and displays on the public hero.
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143681, 'show_title', 'Qatar Chamber Podcast', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143682
def test_143682_show_title_rejects_an_empty_value(page):
    """ADO-143682 (P2). Verify that Show Title rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Show Title field. -> Save → "This field is required." (MSG-5) shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143682, 'show_title', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143683
def test_143683_show_title_rejects_a_value_exceeding_150_characters(page):
    """ADO-143683 (P3). Verify that Show Title rejects a value exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 151-character string in Show Title. -> Save → validation error shown; save blocked; value not persisted.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143683, 'show_title', 150, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143684
def test_143684_show_title_rejects_whitespace_only_input(page):
    """ADO-143684 (P3). Verify that Show Title rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"     "` (spaces only) in Show Title. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143684, 'show_title', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143685
def test_143685_show_description_accepts_a_valid_rich_text_value_within_1000(page):
    """ADO-143685 (P3). Verify that Show Description accepts a valid rich-text value within 1000 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid rich-text value ≤1000 characters in Show Description. -> Save → saved successfully; renders on the public hero.
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143685, 'show_description', 'Valid show description', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143686
def test_143686_show_description_rejects_an_empty_value(page):
    """ADO-143686 (P2). Verify that Show Description rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Show Description field. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143686, 'show_description', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143687
def test_143687_show_description_rejects_a_value_exceeding_1000_characters(page):
    """ADO-143687 (P3). Verify that Show Description rejects a value exceeding 1000 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 1001-character value in Show Description. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143687, 'show_description', 1000, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143688
def test_143688_show_description_rejects_whitespace_only_input(page):
    """ADO-143688 (P3). Verify that Show Description rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Show Description. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143688, 'show_description', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143689
def test_143689_hero_background_image_accepts_a_valid_file_within_the_size_t(page):
    """ADO-143689 (P2). Verify that Hero Background Image accepts a valid file within the size/type limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid 1.5MB JPG as Hero Background Image. -> Save → saved; renders as the hero background on the public page.
    """
    ck.check_file_accepted(page, PodcastShowConfigurationAdminPage, 143689, 'hero_background_image', VALID_JPG, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143690
def test_143690_hero_background_image_rejects_an_unsupported_file_type(page):
    """ADO-143690 (P2). Verify that Hero Background Image rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a `.pdf` file as Hero Background Image. -> Save → "Unsupported file type or size." (MSG-9) shown; rejected.
    """
    ck.check_file_refused(page, PodcastShowConfigurationAdminPage, 143690, 'hero_background_image', BAD_IMAGE_PDF, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143691
def test_143691_hero_background_image_rejects_a_file_exceeding_the_2mb_size(page):
    """ADO-143691 (P2). Verify that Hero Background Image rejects a file exceeding the 2MB size limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload an oversized 2.5MB JPG as Hero Background Image. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastShowConfigurationAdminPage, 143691, 'hero_background_image', BIG_IMAGE, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143692
def test_143692_hero_background_image_is_required_before_publish(page):
    """ADO-143692 (P2). Verify that Hero Background Image is required before publish

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Hero Background Image empty, attempt Save/Publish. -> "This field is required." shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143692, 'hero_background_image', side='en', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143693
def test_143693_hero_illustration_accepts_a_valid_file_within_the_size_type(page):
    """ADO-143693 (P3). Verify that Hero Illustration accepts a valid file within the size/type limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid 1MB SVG as Hero Illustration. -> Save → saved; renders in the hero.
    """
    ck.check_file_accepted(page, PodcastShowConfigurationAdminPage, 143693, 'hero_illustration', VALID_JPG, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143694
def test_143694_hero_illustration_rejects_an_unsupported_file_type(page):
    """ADO-143694 (P3). Verify that Hero Illustration rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a `.gif` file as Hero Illustration. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastShowConfigurationAdminPage, 143694, 'hero_illustration', BAD_IMAGE_GIF, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143695
def test_143695_hero_illustration_rejects_a_file_exceeding_the_2mb_size_limi(page):
    """ADO-143695 (P3). Verify that Hero Illustration rejects a file exceeding the 2MB size limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload an oversized 2.2MB PNG as Hero Illustration. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastShowConfigurationAdminPage, 143695, 'hero_illustration', BIG_IMAGE, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143696
def test_143696_hero_illustration_is_required_before_publish(page):
    """ADO-143696 (P3). Verify that Hero Illustration is required before publish

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Hero Illustration empty, attempt Save/Publish. -> required-field error shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143696, 'hero_illustration', side='en', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143697
def test_143697_cadence_badge_label_accepts_a_valid_value_within_30_characte(page):
    """ADO-143697 (P3). Verify that Cadence Badge Label accepts a valid value within 30 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Weekly"` in Cadence Badge Label. -> Save → saved; badge shows "Weekly".
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143697, 'cadence_badge_label', 'Weekly', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143698
def test_143698_cadence_badge_label_rejects_an_empty_value(page):
    """ADO-143698 (P2). Verify that Cadence Badge Label rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Cadence Badge Label. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143698, 'cadence_badge_label', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143699
def test_143699_cadence_badge_label_rejects_a_value_exceeding_30_characters(page):
    """ADO-143699 (P3). Verify that Cadence Badge Label rejects a value exceeding 30 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 31-character value in Cadence Badge Label. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143699, 'cadence_badge_label', 30, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143700
def test_143700_cadence_badge_label_rejects_whitespace_only_input(page):
    """ADO-143700 (P3). Verify that Cadence Badge Label rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Cadence Badge Label. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143700, 'cadence_badge_label', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143701
def test_143701_host_name_accepts_a_valid_value_within_150_characters(page):
    """ADO-143701 (P3). Verify that Host Name accepts a valid value within 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Ahmed Al-Kuwari"` in Host Name. -> Save → saved; shows in the host block.
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143701, 'host_name', 'Ahmed Al-Kuwari', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143702
def test_143702_host_name_rejects_an_empty_value(page):
    """ADO-143702 (P2). Verify that Host Name rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Host Name. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143702, 'host_name', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143703
def test_143703_host_name_rejects_a_value_exceeding_150_characters(page):
    """ADO-143703 (P3). Verify that Host Name rejects a value exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 151-character value in Host Name. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143703, 'host_name', 150, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143704
def test_143704_host_name_rejects_whitespace_only_input(page):
    """ADO-143704 (P3). Verify that Host Name rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Host Name. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143704, 'host_name', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143705
def test_143705_host_title_accepts_a_valid_value_within_150_characters(page):
    """ADO-143705 (P3). Verify that Host Title accepts a valid value within 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Director of Communications"` in Host Title. -> Save → saved; shows under the host name.
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143705, 'host_title', 'Director of Communications', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143706
def test_143706_host_title_rejects_an_empty_value(page):
    """ADO-143706 (P2). Verify that Host Title rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Host Title. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143706, 'host_title', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143707
def test_143707_host_title_rejects_a_value_exceeding_150_characters(page):
    """ADO-143707 (P3). Verify that Host Title rejects a value exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 151-character value in Host Title. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143707, 'host_title', 150, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143708
def test_143708_host_title_rejects_whitespace_only_input(page):
    """ADO-143708 (P3). Verify that Host Title rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Host Title. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143708, 'host_title', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143709
def test_143709_host_image_accepts_a_valid_supported_file_type(page):
    """ADO-143709 (P3). Verify that Host Image accepts a valid supported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid PNG as Host Image. -> Save → saved; renders as the host photo.
    """
    ck.check_file_accepted(page, PodcastShowConfigurationAdminPage, 143709, 'host_image', VALID_JPG, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143710
def test_143710_host_image_rejects_an_unsupported_file_type(page):
    """ADO-143710 (P3). Verify that Host Image rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a `.bmp` file as Host Image. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastShowConfigurationAdminPage, 143710, 'host_image', BAD_IMAGE, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143741
def test_143741_host_image_is_required_before_publish(page):
    """ADO-143741 (P3). Verify that Host Image is required before publish

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Host Image empty, attempt Save/Publish. -> required-field error shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143741, 'host_image', side='en', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143742
def test_143742_platform_name_accepts_a_valid_value_within_60_characters(page):
    """ADO-143742 (P3). Verify that Platform Name accepts a valid value within 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Apple Music"` in Platform Name. -> Save → saved; renders as the button label.
    """
    ck.check_valid_persists(page, PodcastPlatformLinkAdminPage, 143742, 'platform_name', 'Apple Music', ar='قيمة صالحة', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143743
def test_143743_platform_name_rejects_an_empty_value(page):
    """ADO-143743 (P2). Verify that Platform Name rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Platform Name. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastPlatformLinkAdminPage, 143743, 'platform_name', side='both', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143744
def test_143744_platform_name_rejects_a_value_exceeding_60_characters(page):
    """ADO-143744 (P3). Verify that Platform Name rejects a value exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 61-character value in Platform Name. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastPlatformLinkAdminPage, 143744, 'platform_name', 60, files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143745
def test_143745_platform_name_rejects_whitespace_only_input(page):
    """ADO-143745 (P3). Verify that Platform Name rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Platform Name. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastPlatformLinkAdminPage, 143745, 'platform_name', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143746
def test_143746_platform_icon_accepts_a_valid_file_within_the_size_type_limi(page):
    """ADO-143746 (P3). Verify that Platform Icon accepts a valid file within the size/type limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid 400KB SVG as Platform Icon. -> Save → saved; renders on the button.
    """
    ck.check_file_accepted(page, PodcastPlatformLinkAdminPage, 143746, 'platform_icon', VALID_PNG, files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143747
def test_143747_platform_icon_rejects_an_unsupported_file_type(page):
    """ADO-143747 (P3). Verify that Platform Icon rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a `.jpg` file as Platform Icon. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastPlatformLinkAdminPage, 143747, 'platform_icon', BAD_IMAGE, files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143748
def test_143748_platform_icon_rejects_a_file_exceeding_the_1mb_size_limit(page):
    """ADO-143748 (P3). Verify that Platform Icon rejects a file exceeding the 1MB size limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload an oversized 1.2MB file as Platform Icon. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastPlatformLinkAdminPage, 143748, 'platform_icon', BIG_ICON_1MB, files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143749
def test_143749_platform_icon_is_required_before_publish(page):
    """ADO-143749 (P3). Verify that Platform Icon is required before publish

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Platform Icon empty, attempt Save/Publish. -> required-field error shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastPlatformLinkAdminPage, 143749, 'platform_icon', side='en', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143750
def test_143750_platform_url_accepts_a_valid_url(page):
    """ADO-143750 (P2). Verify that Platform URL accepts a valid URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `https://music.apple.com/qc-podcast` in Platform URL. -> Save → saved; the button opens this URL.
    """
    ck.check_valid_persists(page, PodcastPlatformLinkAdminPage, 143750, 'platform_url', 'https://music.apple.com/qc-podcast', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143751
def test_143751_platform_url_rejects_an_invalid_url_format(page):
    """ADO-143751 (P2). Verify that Platform URL rejects an invalid URL format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"not a url"` in Platform URL. -> Save → "A valid platform URL is required." (MSG-8) shown; rejected.
    """
    ck.check_value_refused(page, PodcastPlatformLinkAdminPage, 143751, 'platform_url', 'not a url', short='url', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143752
def test_143752_platform_url_rejects_an_empty_value(page):
    """ADO-143752 (P2). Verify that Platform URL rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Platform URL. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastPlatformLinkAdminPage, 143752, 'platform_url', side='both', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143753
def test_143753_display_order_accepts_a_valid_positive_integer(page):
    """ADO-143753 (P3). Verify that Display Order accepts a valid positive integer

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `1` in Display Order. -> Save → saved; link ordered first.
    """
    ck.check_valid_persists(page, PodcastPlatformLinkAdminPage, 143753, 'display_order', '1', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143754
def test_143754_display_order_rejects_zero(page):
    """ADO-143754 (P3). Verify that Display Order rejects zero

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `0` in Display Order. -> Save → validation error shown (must be positive); save blocked.
    """
    ck.check_value_refused(page, PodcastPlatformLinkAdminPage, 143754, 'display_order', '0', short='zero', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143755
def test_143755_display_order_rejects_non_numeric_input(page):
    """ADO-143755 (P3). Verify that Display Order rejects non-numeric input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"abc"` in Display Order. -> Save → validation error shown; save blocked.
    """
    ck.check_value_refused(page, PodcastPlatformLinkAdminPage, 143755, 'display_order', 'abc', short='nan', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143756
def test_143756_display_order_rejects_an_empty_value(page):
    """ADO-143756 (P3). Verify that Display Order rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Display Order. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastPlatformLinkAdminPage, 143756, 'display_order', side='both', files=FILES[PodcastPlatformLinkAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143757
def test_143757_episode_title_accepts_a_valid_value_within_200_characters(page):
    """ADO-143757 (P2). Verify that Episode Title accepts a valid value within 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Trade Corridors of Tomorrow"` in Episode Title. -> Save → saved; shows on the episode row.
    """
    ck.check_valid_persists(page, PodcastEpisodeAdminPage, 143757, 'episode_title', 'Trade Corridors of Tomorrow', ar='قيمة صالحة', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143758
def test_143758_episode_title_rejects_an_empty_value(page):
    """ADO-143758 (P2). Verify that Episode Title rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Episode Title. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAdminPage, 143758, 'episode_title', side='both', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143759
def test_143759_episode_title_rejects_a_value_exceeding_200_characters(page):
    """ADO-143759 (P3). Verify that Episode Title rejects a value exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 201-character value in Episode Title. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastEpisodeAdminPage, 143759, 'episode_title', 200, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143760
def test_143760_episode_title_rejects_whitespace_only_input(page):
    """ADO-143760 (P3). Verify that Episode Title rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Episode Title. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastEpisodeAdminPage, 143760, 'episode_title', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143761
def test_143761_episode_number_accepts_a_valid_unique_value(page):
    """ADO-143761 (P2). Verify that Episode Number accepts a valid unique value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid unique value `25` in Episode Number. -> Save → saved successfully.
    """
    ck.check_valid_persists(page, PodcastEpisodeAdminPage, 143761, 'episode_number', '9925', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143762
def test_143762_episode_number_rejects_a_value_already_in_use_by_another_epi(page):
    """ADO-143762 (P2). Verify that Episode Number rejects a value already in use by another episode

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `24` (already in use by an existing episode) in Episode Number. -> Save → "This episode number is already in use." (MSG-11) shown; blocked.
    """
    admin = PodcastEpisodeAdminPage(page)
    first, second = qctest_title(143762, 'a'), qctest_title(143762, 'b')
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(first, files=FILES[PodcastEpisodeAdminPage])
        admin.fill('episode_number', '9924')
        admin.save_as_draft()
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(second, files=FILES[PodcastEpisodeAdminPage])
        admin.fill('episode_number', '9924')
        admin.submit_for_review()
        assert admin.refusal_visible(), 'a duplicate Episode Number raised no refusal'
        assert admin.status_of(second, ROLE_EDITOR) != STATUS_PUBLISHED
    finally:
        admin.delete_disposable(second)
        admin.delete_disposable(first)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143763
def test_143763_episode_number_rejects_zero_or_a_negative_value(page):
    """ADO-143763 (P3). Verify that Episode Number rejects zero or a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `-1` in Episode Number. -> Save → validation error shown; save blocked.
    """
    ck.check_value_refused(page, PodcastEpisodeAdminPage, 143763, 'episode_number', '0', short='zero', files=FILES[PodcastEpisodeAdminPage])
    ck.check_value_refused(page, PodcastEpisodeAdminPage, 143763, 'episode_number', '-500', short='neg', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143764
def test_143764_episode_number_rejects_non_numeric_input(page):
    """ADO-143764 (P3). Verify that Episode Number rejects non-numeric input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"twenty-four"` in Episode Number. -> Save → validation error shown; save blocked.
    """
    ck.check_value_refused(page, PodcastEpisodeAdminPage, 143764, 'episode_number', 'abc', short='nan', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143765
def test_143765_episode_artwork_accepts_a_valid_supported_file_type(page):
    """ADO-143765 (P2). Verify that Episode Artwork accepts a valid supported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid JPG as Episode Artwork. -> Save → saved; renders as the episode thumbnail on the public row.
    """
    ck.check_file_accepted(page, PodcastEpisodeAdminPage, 143765, 'episode_artwork', VALID_JPG, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143766
def test_143766_episode_artwork_rejects_an_unsupported_file_type(page):
    """ADO-143766 (P2). Verify that Episode Artwork rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a `.tiff` file as Episode Artwork. -> Save → MSG-9 shown; rejected.
    """
    ck.check_file_refused(page, PodcastEpisodeAdminPage, 143766, 'episode_artwork', BAD_IMAGE, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143767
def test_143767_episode_artwork_is_required_before_publish(page):
    """ADO-143767 (P2). Verify that Episode Artwork is required before publish

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Episode Artwork empty, attempt Publish. -> "Episode artwork is required." (MSG-12) shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAdminPage, 143767, 'episode_artwork', side='en', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143768
def test_143768_brief_description_accepts_a_valid_value_within_300_character(page):
    """ADO-143768 (P2). Verify that Brief Description accepts a valid value within 300 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid description ≤300 characters in Brief Description. -> Save → saved; shows on the episode row.
    """
    ck.check_valid_persists(page, PodcastEpisodeAdminPage, 143768, 'brief_description', 'Valid brief description', ar='قيمة صالحة', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143769
def test_143769_brief_description_rejects_an_empty_value(page):
    """ADO-143769 (P2). Verify that Brief Description rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Brief Description. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAdminPage, 143769, 'brief_description', side='both', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143770
def test_143770_brief_description_rejects_a_value_exceeding_300_characters(page):
    """ADO-143770 (P3). Verify that Brief Description rejects a value exceeding 300 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 301-character value in Brief Description. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastEpisodeAdminPage, 143770, 'brief_description', 300, files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143771
def test_143771_brief_description_rejects_whitespace_only_input(page):
    """ADO-143771 (P3). Verify that Brief Description rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Brief Description. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastEpisodeAdminPage, 143771, 'brief_description', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143772
def test_143772_episode_audio_file_accepts_a_valid_supported_format_when_opt(page):
    """ADO-143772 (P2). Verify that Episode Audio File accepts a valid supported format when Option A is selected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Select Audio Source Type = Option A, upload a valid MP3 as Episode Audio File. -> Save → saved; playable and downloadable on the public row.
    """
    ck.check_file_accepted(page, PodcastEpisodeAudioAdminPage, 143772, 'audio_file', VALID_MP3, files=FILES[PodcastEpisodeAudioAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143773
def test_143773_episode_audio_file_rejects_an_unsupported_audio_format(page):
    """ADO-143773 (P2). Verify that Episode Audio File rejects an unsupported audio format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a `.wma` file as Episode Audio File. -> Save → "Unsupported audio format. Accepted formats: MP3, WAV, M4A." (MSG-14) shown; rejected.
    """
    ck.check_file_refused(page, PodcastEpisodeAudioAdminPage, 143773, 'audio_file', BAD_AUDIO, files=FILES[PodcastEpisodeAudioAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143774
def test_143774_episode_audio_file_is_required_before_publish_when_option_a(page):
    """ADO-143774 (P2). Verify that Episode Audio File is required before publish when Option A is selected and no file is uploaded

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Select Audio Source Type = Option A, leave Episode Audio File empty, attempt Publish. -> "An audio file or an embed link is required." (MSG-13) shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAudioAdminPage, 143774, 'audio_file', side='en', files=FILES[PodcastEpisodeAudioAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143775
def test_143775_episode_embed_link_accepts_a_valid_embed_url_when_option_b_i(page):
    """ADO-143775 (P2). Verify that Episode Embed Link accepts a valid embed URL when Option B is selected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Select Audio Source Type = Option B, enter a valid embed URL in Episode Embed Link. -> Save → saved; the episode plays via the embed on the public page.
    """
    ck.check_valid_persists(page, PodcastEpisodeAdminPage, 143775, 'embed_link', 'https://example.com/qctest-valid', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143776
def test_143776_episode_embed_link_is_required_before_publish_when_option_b(page):
    """ADO-143776 (P2). Verify that Episode Embed Link is required before publish when Option B is selected and left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Select Audio Source Type = Option B, leave Episode Embed Link empty, attempt Publish. -> MSG-13 shown; publish blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAdminPage, 143776, 'embed_link', side='both', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143777
def test_143777_published_date_accepts_a_valid_date(page):
    """ADO-143777 (P3). Verify that Published Date accepts a valid date

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `2026-09-21` in Published Date. -> Save → saved; episode sorts correctly by this date.
    """
    ck.check_valid_persists(page, PodcastEpisodeAdminPage, 143777, 'published_date', '15/06/2027', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143778
def test_143778_published_date_rejects_an_empty_value(page):
    """ADO-143778 (P3). Verify that Published Date rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Published Date. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAdminPage, 143778, 'published_date', side='both', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143779
def test_143779_duration_accepts_a_valid_hh_mm_ss_value(page):
    """ADO-143779 (P3). Verify that Duration accepts a valid HH:MM:SS value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `00:42:15` in Duration. -> Save → saved; displays "42 MIN" on the public row.
    """
    ck.check_valid_persists(page, PodcastEpisodeAdminPage, 143779, 'duration', '00:42:15', ar='قيمة صالحة', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143780
def test_143780_duration_rejects_an_invalid_format(page):
    """ADO-143780 (P3). Verify that Duration rejects an invalid format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"42 minutes"` in Duration. -> Save → validation error shown; save blocked.
    """
    ck.check_value_refused(page, PodcastEpisodeAdminPage, 143780, 'duration', '42 minutes', short='fmt', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143799
def test_143799_duration_rejects_an_empty_value(page):
    """ADO-143799 (P3). Verify that Duration rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Duration. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastEpisodeAdminPage, 143799, 'duration', side='both', files=FILES[PodcastEpisodeAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143804
def test_143804_subscription_heading_accepts_a_valid_value_within_150_charac(page):
    """ADO-143804 (P3). Verify that Subscription Heading accepts a valid value within 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `"Never miss a new episode"` in Subscription Heading. -> Save → saved successfully.
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143804, 'subscription_heading', 'Never miss a new episode', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143805
def test_143805_subscription_heading_rejects_an_empty_value(page):
    """ADO-143805 (P2). Verify that Subscription Heading rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Subscription Heading. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143805, 'subscription_heading', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143806
def test_143806_subscription_heading_rejects_a_value_exceeding_150_character(page):
    """ADO-143806 (P3). Verify that Subscription Heading rejects a value exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 151-character value in Subscription Heading. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143806, 'subscription_heading', 150, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143807
def test_143807_subscription_heading_rejects_whitespace_only_input(page):
    """ADO-143807 (P3). Verify that Subscription Heading rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Subscription Heading. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143807, 'subscription_heading', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143808
def test_143808_subscription_description_accepts_a_valid_value_within_300_ch(page):
    """ADO-143808 (P3). Verify that Subscription Description accepts a valid value within 300 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid description ≤300 characters in Subscription Description. -> Save → saved; shows under the heading.
    """
    ck.check_valid_persists(page, PodcastShowConfigurationAdminPage, 143808, 'subscription_description', 'Valid subscription description', ar='قيمة صالحة', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143809
def test_143809_subscription_description_rejects_an_empty_value(page):
    """ADO-143809 (P2). Verify that Subscription Description rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Subscription Description. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143809, 'subscription_description', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143810
def test_143810_subscription_description_rejects_a_value_exceeding_300_chara(page):
    """ADO-143810 (P3). Verify that Subscription Description rejects a value exceeding 300 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 301-character value in Subscription Description. -> Save → validation error shown; save blocked.
    """
    ck.check_over_max_refused(page, PodcastShowConfigurationAdminPage, 143810, 'subscription_description', 300, files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143811
def test_143811_subscription_description_rejects_whitespace_only_input(page):
    """ADO-143811 (P3). Verify that Subscription Description rejects whitespace-only input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter whitespace-only content in Subscription Description. -> Save → treated as empty; MSG-5 shown; save blocked.
    """
    ck.check_whitespace_refused(page, PodcastShowConfigurationAdminPage, 143811, 'subscription_description', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143813
def test_143813_email_field_placeholder_rejects_an_empty_value(page):
    """ADO-143813 (P3). Verify that Email Field Placeholder rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Email Field Placeholder. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143813, 'email_placeholder', side='both', files=FILES[PodcastShowConfigurationAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130713
@pytest.mark.tc_143817
def test_143817_subscribe_button_label_rejects_an_empty_value(page):
    """ADO-143817 (P3). Verify that Subscribe Button Label rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Subscribe Button Label. -> Save → MSG-5 shown; save blocked.
    """
    ck.check_empty_refused(page, PodcastShowConfigurationAdminPage, 143817, 'subscribe_button_label', side='both', files=FILES[PodcastShowConfigurationAdminPage])

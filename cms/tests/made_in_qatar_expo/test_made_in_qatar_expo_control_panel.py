"""
cms/tests/made_in_qatar_expo/test_made_in_qatar_expo_control_panel.py - Control_Panel cases for PBI 130708
(Test Plan 137724, suite 140367): Azure Priority 1-3, Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_130708_cp_batch.json, which holds every disposition and
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
from cms.pages.made_in_qatar_expo.made_in_qatar_expo_admin_page import (
    MadeInQatarExpoHeroAdminPage,
    MadeInQatarExpoAboutAdminPage,
    MadeInQatarExpoCtaCardAdminPage,
)
from cms.tests import authoring_checks as ck
from web.pages.made_in_qatar_expo.made_in_qatar_expo_page import MadeInQatarExpoPage

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
    MadeInQatarExpoHeroAdminPage: {'hero_banner': VALID_JPG},
    MadeInQatarExpoAboutAdminPage: {},
    MadeInQatarExpoCtaCardAdminPage: {'logo': VALID_PNG},
}

probe = ck.make_public_probe(lambda p: MadeInQatarExpoPage(p).open_page())

# Conditional-case gates. Flip one only when its condition is confirmed.
SINGLETON_PUBLISH_CLEARED = False  # True once: confirmed live that publishing a QCTEST entry of a page-level object does not displace the live QCDEMO entry

@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142642
def test_142642_site_content_author_can_view_and_update_assigned_made_in_qat(page):
    """ADO-142642 (P2). Verify that a Site Content Author can view and update assigned Made in Qatar Expo content

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in as Site Content Author -> Login succeeds
      2. Open Made in Qatar Expo in Object Authoring -> Page opens in edit mode
      3. Update About section body text and save -> Save succeeds; updated value persists on reload
    """
    ck.check_author_updates_own(page, MadeInQatarExpoAboutAdminPage, 142642, 'section_body', 'QCTEST author edit', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.pbi_130708
@pytest.mark.tc_142643
def test_142643_site_content_author_cannot_publish_the_made_in_qatar_expo_pa(page):
    """ADO-142643 (P1). Verify that a Site Content Author cannot publish the Made in Qatar Expo page

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in as Site Content Author, open the page -> Page opens
      2. Attempt Publish (via UI action and, if the environment exposes it, direct action endpoint) -> "Access Denied. You do not have permission to perform this action." / "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء." is shown; page status unchanged
    """
    ck.check_author_submit_pending(page, MadeInQatarExpoHeroAdminPage, 142643, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.pbi_130708
@pytest.mark.tc_142644
def test_142644_public_visitor_cannot_access_the_made_in_qatar_expo_admin_ed(page, browser):
    """ADO-142644 (P1). Verify that a Public Visitor cannot access the Made in Qatar Expo admin/edit page

    Account: none - fresh logged-out context (new_context(browser, use_auth_state=False)).
    Steps (from the approved case):
      1. In a logged-out browser context, navigate directly to the Object Authoring edit URL for the page -> Redirected to CMS login, or "Access Denied" shown; no page content/fields exposed
    """
    ck.check_anonymous_denied(browser, MadeInQatarExpoHeroAdminPage)


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142646
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142646_site_content_editor_can_fully_author_and_publish_the_made_in(page, browser):
    """ADO-142646 (P2). Verify that a Site Content Editor can fully author and publish the Made in Qatar Expo page end-to-end

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Object Authoring, set Hero Eyebrow/Title/Description/Banner (EN/AR) -> Fields accept values
      2. Set About Eyebrow/Title/Body (EN/AR) -> Fields accept values
      3. Set Card Logo/Eyebrow/Heading/Description/Button/URL/Open Behavior (EN/AR) -> Fields accept values
      4. Save as Draft, then Preview -> Draft saved; preview renders configured content
      5. Publish -> Liferay generic success toast shown; audit log records the publish action
      6. Reload the public Web page (anonymous context) -> All configured EN/AR content is visible live, matching what was authored

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    for cls in (MadeInQatarExpoHeroAdminPage, MadeInQatarExpoAboutAdminPage, MadeInQatarExpoCtaCardAdminPage):
        ck.check_editor_publish_public(page, browser, cls, 142646, probe, files=FILES[cls])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142649
def test_142649_hero_eyebrow_label_saves_correctly_with_valid_en_ar_values(page):
    """ADO-142649 (P3). Verify that the Hero Eyebrow Label saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR values, Save -> Values accepted, no validation error
      2. Reload the edit form -> Both values persist exactly as entered
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142649, 'eyebrow', 'Valid eyebrow', ar='قيمة صالحة', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142650
def test_142650_hero_eyebrow_label_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142650 (P2). Verify that the Hero Eyebrow Label is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Eyebrow EN empty (AR filled), attempt Save -> Save blocked; "This field is required." shown under EN field
      2. Fill EN, clear AR, attempt Save -> Save blocked; "هذا الحقل مطلوب." shown under AR field
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142650, 'eyebrow', side='each', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142651
def test_142651_hero_eyebrow_label_rejects_input_exceeding_60_characters(page):
    """ADO-142651 (P3). Verify that the Hero Eyebrow Label rejects input exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 61-character value in Eyebrow EN, attempt Save -> Save blocked (or input truncated at 60, per field behavior); validation message shown / character count exceeded indicator displayed
      2. Enter exactly 60 characters -> Value accepted and saved
    """
    ck.check_over_max_refused(page, MadeInQatarExpoHeroAdminPage, 142651, 'eyebrow', 60, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142652
def test_142652_page_title_saves_correctly_with_valid_en_ar_values(page):
    """ADO-142652 (P3). Verify that the Page Title saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted, no error
      2. Reload -> Values persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142652, 'page_title', 'Valid page title', ar='قيمة صالحة', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142653
def test_142653_page_title_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142653 (P2). Verify that the Page Title is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Title EN, attempt Save -> Blocked; "This field is required." shown
      2. Restore EN, clear Title AR, attempt Save -> Blocked; "هذا الحقل مطلوب." shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142653, 'page_title', side='each', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142654
def test_142654_page_title_rejects_input_exceeding_120_characters(page):
    """ADO-142654 (P3). Verify that the Page Title rejects input exceeding 120 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 121 characters in Title EN, attempt Save -> Save blocked/truncated; boundary validation triggers
      2. Enter exactly 120 characters -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoHeroAdminPage, 142654, 'page_title', 120, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142655
def test_142655_hero_description_saves_correctly_with_valid_en_ar_rich_text(page):
    """ADO-142655 (P3). Verify that the Hero Description saves correctly with valid EN/AR rich text

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR rich text, Save -> Accepted
      2. Reload -> Formatting and text persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142655, 'hero_description', 'Valid hero description', ar='قيمة صالحة', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142656
def test_142656_hero_description_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142656 (P2). Verify that the Hero Description is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Description EN, attempt Save -> Blocked; "This field is required." shown
      2. Restore EN, clear AR, attempt Save -> Blocked; "هذا الحقل مطلوب." shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142656, 'hero_description', side='each', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142657
def test_142657_hero_description_rejects_content_exceeding_200_characters(page):
    """ADO-142657 (P3). Verify that the Hero Description rejects content exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 201 characters, attempt Save -> Blocked/truncated at boundary
      2. Enter exactly 200 characters -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoHeroAdminPage, 142657, 'hero_description', 200, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142658
def test_142658_hero_banner_accepts_a_valid_image_upload_with_alt_text(page):
    """ADO-142658 (P2). Verify that the Hero Banner accepts a valid image upload with alt text

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload `hero-banner.jpg` (500KB), enter alt text EN/AR, Save -> Upload succeeds, image preview shown
      2. Reload -> Image and alt text persist; image renders on public Web page
    """
    ck.check_file_accepted(page, MadeInQatarExpoHeroAdminPage, 142658, 'hero_banner', VALID_JPG, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142659
def test_142659_hero_banner_rejects_an_unsupported_file_format(page):
    """ADO-142659 (P3). Verify that the Hero Banner rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a `.pdf` file as Hero Banner -> Upload rejected; format-not-supported message shown; no file saved
    """
    ck.check_file_refused(page, MadeInQatarExpoHeroAdminPage, 142659, 'hero_banner', BAD_IMAGE_PDF, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142660
def test_142660_hero_banner_rejects_an_image_exceeding_2mb(page):
    """ADO-142660 (P2). Verify that the Hero Banner rejects an image exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a 3MB `.jpg` as Hero Banner -> Upload rejected; "Image size must not exceed 2 MB." / "يجب ألا يتجاوز حجم الصورة 2 ميغابايت." shown
    """
    ck.check_file_refused(page, MadeInQatarExpoHeroAdminPage, 142660, 'hero_banner', BIG_IMAGE, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142661
def test_142661_publish_is_blocked_when_the_hero_banner_is_missing(page):
    """ADO-142661 (P2). Verify that Publish is blocked when the Hero Banner is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Hero Banner unset, attempt Publish -> Blocked; "This field is required." shown; page not published
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142661, 'hero_banner', side='en', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142662
def test_142662_hero_cta_button_label_saves_correctly_with_valid_en_ar_value(page):
    """ADO-142662 (P3). Verify that the Hero CTA Button Label saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist and render on the CTA button
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142662, 'button_label', 'Valid button label', ar='قيمة صالحة', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142663
def test_142663_hero_cta_button_label_is_rejected_when_en_or_ar_is_left_empt(page):
    """ADO-142663 (P2). Verify that the Hero CTA Button Label is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Button Label EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR, attempt Save -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142663, 'button_label', side='each', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142664
def test_142664_hero_cta_button_label_rejects_input_exceeding_60_characters(page):
    """ADO-142664 (P3). Verify that the Hero CTA Button Label rejects input exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 61 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 60 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoHeroAdminPage, 142664, 'button_label', 60, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142665
def test_142665_hero_cta_redirect_url_saves_correctly_with_a_valid_url(page):
    """ADO-142665 (P2). Verify that the Hero CTA Redirect URL saves correctly with a valid URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the URL, Save -> Accepted, no error
      2. Reload -> URL persists
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142665, 'redirect_url', 'https://example.com/qctest-valid', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142666
def test_142666_hero_cta_redirect_url_rejects_an_invalid_url_format(page):
    """ADO-142666 (P2). Verify that the Hero CTA Redirect URL rejects an invalid URL format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `not-a-valid-url`, attempt Save -> Blocked; "Please enter a valid URL." / "يرجى إدخال رابط صالح." shown
    """
    ck.check_value_refused(page, MadeInQatarExpoHeroAdminPage, 142666, 'redirect_url', 'not-a-valid-url', short='url', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142667
def test_142667_publish_is_blocked_when_the_hero_cta_redirect_url_is_empty(page):
    """ADO-142667 (P2). Verify that Publish is blocked when the Hero CTA Redirect URL is empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Redirect URL empty (label filled), attempt Publish -> Blocked; "This field is required." shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142667, 'redirect_url', side='both', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142668
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated (the Events-menu ordering half needs the page published)')
def test_142668_page_display_order_saves_correctly_with_a_valid_value(page):
    """ADO-142668 (P3). Verify that Page Display Order saves correctly with a valid value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 3, Save -> Accepted
      2. Check Events menu ordering -> Item positioned per the value

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated (the Events-menu ordering half needs the page published)
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142668, 'display_order', '300', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142669
def test_142669_page_display_order_rejects_an_empty_value(page):
    """ADO-142669 (P3). Verify that Page Display Order rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear Display Order, attempt Save -> Blocked; "This field is required." shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoHeroAdminPage, 142669, 'display_order', side='both', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142670
def test_142670_page_display_order_rejects_a_negative_value(page):
    """ADO-142670 (P3). Verify that Page Display Order rejects a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter -1, attempt Save -> Blocked; validation error shown; value not saved
    """
    ck.check_value_refused(page, MadeInQatarExpoHeroAdminPage, 142670, 'display_order', '-1', short='neg', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142671
def test_142671_page_display_order_rejects_non_numeric_input(page):
    """ADO-142671 (P3). Verify that Page Display Order rejects non-numeric input

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter "abc" into Display Order -> Field rejects non-numeric characters, or Save is blocked with a validation error; value not saved
    """
    ck.check_value_refused(page, MadeInQatarExpoHeroAdminPage, 142671, 'display_order', 'abc', short='nan', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142673
def test_142673_section_eyebrow_saves_correctly_with_valid_en_ar_values(page):
    """ADO-142673 (P3). Verify that the Section Eyebrow saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoAboutAdminPage, 142673, 'section_eyebrow', 'Valid section eyebrow', ar='قيمة صالحة', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142674
def test_142674_section_eyebrow_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142674 (P2). Verify that the Section Eyebrow is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR, attempt Save -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoAboutAdminPage, 142674, 'section_eyebrow', side='each', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142675
def test_142675_section_eyebrow_rejects_input_exceeding_100_characters(page):
    """ADO-142675 (P3). Verify that the Section Eyebrow rejects input exceeding 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 101 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 100 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoAboutAdminPage, 142675, 'section_eyebrow', 100, files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142676
def test_142676_section_title_saves_correctly_with_valid_en_ar_values(page):
    """ADO-142676 (P3). Verify that the Section Title saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoAboutAdminPage, 142676, 'section_title', 'Valid section title', ar='قيمة صالحة', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142677
def test_142677_section_title_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142677 (P2). Verify that the Section Title is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR, attempt Save -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoAboutAdminPage, 142677, 'section_title', side='each', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142678
def test_142678_section_title_rejects_input_exceeding_120_characters(page):
    """ADO-142678 (P3). Verify that the Section Title rejects input exceeding 120 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 121 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 120 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoAboutAdminPage, 142678, 'section_title', 120, files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142679
def test_142679_section_body_saves_correctly_with_valid_en_ar_rich_text(page):
    """ADO-142679 (P3). Verify that the Section Body saves correctly with valid EN/AR rich text

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR body content with basic formatting (bold/paragraph), Save -> Accepted
      2. Reload -> Content and formatting persist; renders correctly on Web
    """
    ck.check_valid_persists(page, MadeInQatarExpoAboutAdminPage, 142679, 'section_body', 'Valid section body', ar='قيمة صالحة', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142680
def test_142680_section_body_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142680 (P2). Verify that the Section Body is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN body, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR body, attempt Save -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoAboutAdminPage, 142680, 'section_body', side='each', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142681
def test_142681_section_body_rejects_content_exceeding_10000_characters(page):
    """ADO-142681 (P3). Verify that the Section Body rejects content exceeding 10000 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 10,001 characters, attempt Save -> Blocked/truncated at boundary
      2. Enter exactly 10,000 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoAboutAdminPage, 142681, 'section_body', 10000, files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142682
def test_142682_cta_card_logo_accepts_a_valid_image_upload_with_alt_text(page):
    """ADO-142682 (P2). Verify that the CTA Card Logo accepts a valid image upload with alt text

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload logo, enter alt text, Save -> Upload succeeds
      2. Reload -> Logo and alt text persist; renders on the public card
    """
    ck.check_file_accepted(page, MadeInQatarExpoCtaCardAdminPage, 142682, 'logo', VALID_PNG, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142683
def test_142683_cta_card_logo_rejects_an_unsupported_file_format(page):
    """ADO-142683 (P3). Verify that the CTA Card Logo rejects an unsupported file format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a `.docx` file as the card logo -> Upload rejected; format-not-supported message shown
    """
    ck.check_file_refused(page, MadeInQatarExpoCtaCardAdminPage, 142683, 'logo', BAD_DOC, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142684
def test_142684_cta_card_logo_rejects_an_image_exceeding_2mb(page):
    """ADO-142684 (P2). Verify that the CTA Card Logo rejects an image exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a 2.5MB `.png` as the logo -> Upload rejected; "Image size must not exceed 2 MB." shown
    """
    ck.check_file_refused(page, MadeInQatarExpoCtaCardAdminPage, 142684, 'logo', BIG_IMAGE, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142685
def test_142685_publish_is_blocked_when_the_cta_card_logo_is_missing(page):
    """ADO-142685 (P2). Verify that Publish is blocked when the CTA Card Logo is missing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Card Logo unset, attempt Publish -> Blocked; "This field is required." shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoCtaCardAdminPage, 142685, 'logo', side='en', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142686
def test_142686_cta_card_eyebrow_saves_correctly_with_valid_en_ar_values(page):
    """ADO-142686 (P3). Verify that the CTA Card Eyebrow saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoCtaCardAdminPage, 142686, 'eyebrow', 'Valid eyebrow', ar='قيمة صالحة', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142687
def test_142687_cta_card_eyebrow_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142687 (P2). Verify that the CTA Card Eyebrow is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoCtaCardAdminPage, 142687, 'eyebrow', side='each', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142688
def test_142688_cta_card_eyebrow_rejects_input_exceeding_100_characters(page):
    """ADO-142688 (P3). Verify that the CTA Card Eyebrow rejects input exceeding 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 101 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 100 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoCtaCardAdminPage, 142688, 'eyebrow', 100, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142689
def test_142689_cta_card_heading_saves_correctly_with_valid_en_ar_values(page):
    """ADO-142689 (P3). Verify that the CTA Card Heading saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoCtaCardAdminPage, 142689, 'heading', 'Valid heading', ar='قيمة صالحة', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142690
def test_142690_cta_card_heading_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142690 (P2). Verify that the CTA Card Heading is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoCtaCardAdminPage, 142690, 'heading', side='each', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142691
def test_142691_cta_card_heading_rejects_input_exceeding_120_characters(page):
    """ADO-142691 (P3). Verify that the CTA Card Heading rejects input exceeding 120 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 121 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 120 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoCtaCardAdminPage, 142691, 'heading', 120, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142692
def test_142692_cta_card_description_saves_correctly_with_valid_en_ar_rich_t(page):
    """ADO-142692 (P3). Verify that the CTA Card Description saves correctly with valid EN/AR rich text

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist
    """
    ck.check_valid_persists(page, MadeInQatarExpoCtaCardAdminPage, 142692, 'description', 'Valid description', ar='قيمة صالحة', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142693
def test_142693_cta_card_description_is_rejected_when_en_or_ar_is_left_empty(page):
    """ADO-142693 (P2). Verify that the CTA Card Description is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoCtaCardAdminPage, 142693, 'description', side='each', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142694
def test_142694_cta_card_description_rejects_content_exceeding_200_character(page):
    """ADO-142694 (P3). Verify that the CTA Card Description rejects content exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 201 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 200 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoCtaCardAdminPage, 142694, 'description', 200, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142695
def test_142695_cta_card_button_label_saves_correctly_with_valid_en_ar_value(page):
    """ADO-142695 (P3). Verify that the CTA Card Button Label saves correctly with valid EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter EN + AR, Save -> Accepted
      2. Reload -> Values persist and render on the card's CTA button
    """
    ck.check_valid_persists(page, MadeInQatarExpoCtaCardAdminPage, 142695, 'button_label', 'Valid button label', ar='قيمة صالحة', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142696
def test_142696_cta_card_button_label_is_rejected_when_en_or_ar_is_left_empt(page):
    """ADO-142696 (P2). Verify that the CTA Card Button Label is rejected when EN or AR is left empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear EN, attempt Save -> Blocked; EN message shown
      2. Restore EN, clear AR -> Blocked; AR message shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoCtaCardAdminPage, 142696, 'button_label', side='each', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142697
def test_142697_cta_card_button_label_rejects_input_exceeding_60_characters(page):
    """ADO-142697 (P3). Verify that the CTA Card Button Label rejects input exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 61 characters, attempt Save -> Blocked/truncated
      2. Enter exactly 60 -> Accepted
    """
    ck.check_over_max_refused(page, MadeInQatarExpoCtaCardAdminPage, 142697, 'button_label', 60, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142698
def test_142698_cta_card_redirect_url_saves_correctly_with_a_valid_url(page):
    """ADO-142698 (P2). Verify that the CTA Card Redirect URL saves correctly with a valid URL

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter the URL, Save -> Accepted
      2. Reload -> URL persists
    """
    ck.check_valid_persists(page, MadeInQatarExpoCtaCardAdminPage, 142698, 'redirect_url', 'https://example.com/qctest-valid', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142699
def test_142699_cta_card_redirect_url_rejects_an_invalid_url_format(page):
    """ADO-142699 (P2). Verify that the CTA Card Redirect URL rejects an invalid URL format

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter `htp:/badurl`, attempt Save -> Blocked; "Please enter a valid URL." / "يرجى إدخال رابط صالح." shown
    """
    ck.check_value_refused(page, MadeInQatarExpoCtaCardAdminPage, 142699, 'redirect_url', 'htp:/badurl', short='url', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142700
def test_142700_publish_is_blocked_when_the_cta_card_redirect_url_is_empty(page):
    """ADO-142700 (P2). Verify that Publish is blocked when the CTA Card Redirect URL is empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Card Redirect URL empty (other card fields filled), attempt Publish -> Blocked; "This field is required." shown
    """
    ck.check_empty_refused(page, MadeInQatarExpoCtaCardAdminPage, 142700, 'redirect_url', side='both', files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142701
def test_142701_site_content_editor_can_save_the_made_in_qatar_expo_page_as(page):
    """ADO-142701 (P3). Verify that a Site Content Editor can save the Made in Qatar Expo page as Draft

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Fill all mandatory fields, click "Save as Draft" -> Liferay generic success toast shown (EN/AR per locale); Page Status = Draft; audit log records the save
      2. Reopen the page -> All entered values persist
    """
    ck.check_default_draft(page, MadeInQatarExpoHeroAdminPage, 142701, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142702
def test_142702_site_content_editor_can_preview_the_made_in_qatar_expo_page(page, browser):
    """ADO-142702 (P3). Verify that a Site Content Editor can preview the Made in Qatar Expo page before publishing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. With the page in Draft, click Preview -> Preview renders hero/About/card exactly as configured
      2. Confirm the page is NOT live on the public site while only previewed -> Anonymous context still shows the page as unavailable
    """
    ck.check_preview_draft(page, browser, MadeInQatarExpoHeroAdminPage, 142702, probe, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142703
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142703_site_content_editor_can_publish_the_made_in_qatar_expo_page(page, browser):
    """ADO-142703 (P2). Verify that a Site Content Editor can publish the Made in Qatar Expo page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Click Publish on a valid Draft -> Liferay generic success toast shown; Page Status = Published; audit log records the publish
      2. Load the page anonymously on Web -> Page is live with the published content

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, MadeInQatarExpoHeroAdminPage, 142703, probe, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130708
@pytest.mark.tc_142704
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142704_site_content_editor_can_unpublish_the_made_in_qatar_expo_pag(page, browser):
    """ADO-142704 (P2). Verify that a Site Content Editor can unpublish the Made in Qatar Expo page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. On a Published page, click Unpublish -> Success toast shown; Page Status = Unpublished; audit log records the action
      2. Load the page anonymously on Web -> Page returns not-found; menu item no longer visible

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_unpublish_hides(page, browser, MadeInQatarExpoHeroAdminPage, 142704, probe, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142705
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142705_previously_unpublished_made_in_qatar_expo_page_can_be_republ(page, browser):
    """ADO-142705 (P3). Verify that a previously Unpublished Made in Qatar Expo page can be republished and reappears live

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. On the Unpublished page, click Publish again -> Success toast shown; Status = Published
      2. Load the page anonymously -> Page is live again with its content intact

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_republish_updates(page, browser, MadeInQatarExpoHeroAdminPage, 142705, probe, 'eyebrow', 'QCTEST-142705 again', files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142711
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142711_setting_page_active_status_on_makes_the_page_appear_in_the_e(page, browser):
    """ADO-142711 (P3). Verify that setting Page Active Status = On makes the page appear in the Events menu

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. On a Published page, set Active Status = On, save -> Success toast shown
      2. Check the public Events menu -> "Made in Qatar Expo" item visible

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, MadeInQatarExpoHeroAdminPage, 142711, probe, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142712
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142712_setting_page_active_status_off_hides_the_page_from_the_event(page, browser):
    """ADO-142712 (P3). Verify that setting Page Active Status = Off hides the page from the Events menu

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. On a Published page, set Active Status = Off, save -> Success toast shown
      2. Check the public Events menu -> "Made in Qatar Expo" item no longer visible

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_unpublish_hides(page, browser, MadeInQatarExpoHeroAdminPage, 142712, probe, files=FILES[MadeInQatarExpoHeroAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142713
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142713_setting_the_side_cta_card_active_status_on_displays_the_card(page, browser):
    """ADO-142713 (P3). Verify that setting the Side CTA Card Active Status = On displays the card on the public page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Card Active Status = On, save/publish -> Success toast shown
      2. Load the public page -> Side CTA Card is visible

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, MadeInQatarExpoCtaCardAdminPage, 142713, probe, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130708
@pytest.mark.tc_142714
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142714_setting_the_side_cta_card_active_status_off_hides_the_card_f(page, browser):
    """ADO-142714 (P3). Verify that setting the Side CTA Card Active Status = Off hides the card from the public page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Card Active Status = Off, save/publish -> Success toast shown
      2. Load the public page -> Side CTA Card is not rendered; hero and About remain visible

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_unpublish_hides(page, browser, MadeInQatarExpoCtaCardAdminPage, 142714, probe, files=FILES[MadeInQatarExpoCtaCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.edge
@pytest.mark.pbi_130708
@pytest.mark.tc_142722
def test_142722_system_handles_two_site_content_editors_editing_the_made_in(page, browser):
    """ADO-142722 (P3). Verify that the system handles two Site Content Editors editing the Made in Qatar Expo page concurrently without data corruption

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor') in two sessions.
    Steps (from the approved case):
      1. Editor A opens the page for editing -> Edit form loaded
      2. Editor B opens the same page and saves a change to the About Title -> Editor B's save succeeds
      3. Editor A saves a different change without refreshing -> System either blocks with a conflict warning or silently overwrites Editor B's change (record actual observed behavior); no data corruption or partial/blank rec
    """
    ck.check_two_editors(page, browser, MadeInQatarExpoAboutAdminPage, 142722, 'section_title', files=FILES[MadeInQatarExpoAboutAdminPage])


@pytest.mark.control_panel
@pytest.mark.expo
@pytest.mark.edge
@pytest.mark.pbi_130708
@pytest.mark.tc_142726
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated (the redirect half needs both entries published)')
def test_142726_hero_cta_and_side_card_cta_can_be_configured_to_different_ex(page):
    """ADO-142726 (P3). Verify that the Hero CTA and Side Card CTA can be configured to different external destinations without a blocking validation error

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Hero CTA URL = `https://www.madeinqatar.qa`, Card CTA URL = `https://www.qatarchamber.com` (different domain), attempt Save -> Save is allowed (no blocking validation observed) — record actual behavior for the Manager to confirm whether a warning should be added
      2. Load the public page and click each CTA -> Each CTA redirects to its own independently configured URL

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated (the redirect half needs both entries published)
    """
    ck.check_valid_persists(page, MadeInQatarExpoHeroAdminPage, 142726, 'redirect_url', 'https://www.madeinqatar.qa', files=FILES[MadeInQatarExpoHeroAdminPage])
    ck.check_valid_persists(page, MadeInQatarExpoCtaCardAdminPage, 142726, 'redirect_url', 'https://www.qatarchamber.com', files=FILES[MadeInQatarExpoCtaCardAdminPage])

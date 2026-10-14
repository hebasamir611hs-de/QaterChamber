"""
cms/tests/advertisements/test_advertisements_control_panel.py - Control_Panel cases for PBI 131062
(Test Plan 137724, suite 140396): Azure Priority 1-3, Automation-tagged.

Generated 2026-10-01 from the approved cases (batch file
.claude/qa-runs/phase3_131062_cp_batch.json, which holds every disposition and
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
from cms.pages.advertisements.advertisements_admin_page import (
    AdvertisementsPageAdminPage,
    AdvertisementRateCardAdminPage,
    AdvertisementChecklistItemAdminPage,
    AdvertisementBookingRequestAdminPage,
)
from cms.tests import authoring_checks as ck
from web.pages.advertisements.advertisements_page import AdvertisementsPage

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
    AdvertisementsPageAdminPage: {'hero_image': VALID_JPG},
    AdvertisementRateCardAdminPage: {'card_icon': VALID_PNG},
    AdvertisementChecklistItemAdminPage: {},
    AdvertisementBookingRequestAdminPage: {},
}

probe = ck.make_public_probe(lambda p: AdvertisementsPage(p).open_advertisements_anonymous())

# Conditional-case gates. Flip one only when its condition is confirmed.
ADS_TYPE_OBJECT_READ = False  # True once: the Ads Type object is read live
AUDIT_LOG_LOCATED = False  # True once: the audit-log surface is located
CHECKLIST_STRUCTURE_READ = False  # True once: the rate-card Feature Checklist structure is read live
EMAIL_TEMPLATE_LOCATED = False  # True once: the email-template preview surface is located
REVIEWER_ROLE_AVAILABLE = False  # True once: a 'QC Admin Reviewer' account is provisioned in .env
SINGLETON_PUBLISH_CLEARED = False  # True once: confirmed live that publishing a QCTEST entry of a page-level object does not displace the live QCDEMO entry

@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131062
@pytest.mark.tc_142409
def test_142409_cms_advertisements_management_area_renders_correctly_in_arab(page):
    """ADO-142409 (P3). Verify that the CMS Advertisements management area renders correctly in Arabic admin locale

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor'), /ar/ admin locale.
    Steps (from the approved case):
      1. Log in as Site Content Editor -> Login succeeds
      2. Switch admin locale to AR -> Admin locale switched
      3. Open Advertisements management -> Admin screens render RTL where the CMS UI itself is localized; AR-authored field values display correctly in the AR fields regardless of admin chrome locale
    """
    ck.check_rtl_form(page, AdvertisementRateCardAdminPage)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131062
@pytest.mark.tc_142417
def test_142417_cms_rate_card_authoring_form_renders_all_field_groups(page):
    """ADO-142417 (P3). Verify that the CMS rate card authoring form renders all field groups

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open 'Create Rate Card' -> Form opens
      2. Inspect form -> All listed fields/groups present and correctly labelled, EN and AR sub-fields shown for bilingual fields
    """
    ck.check_form_renders(page, AdvertisementRateCardAdminPage, ['card_icon', 'category_label', 'ad_title', 'price', 'currency', 'pricing_unit', 'short_description', 'featured', 'book_now_label', 'mapped_ads_type', 'display_order'])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142418
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142418_cms_booking_requests_panel_lists_booking_reference_company_n(page):
    """ADO-142418 (P2). Verify that the CMS Booking Requests panel lists Booking Reference, Company Name, Contact Person, Email, Ads Type, Preferred Date, Submission Date and Status columns

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Log in as QC Admin Reviewer -> Login succeeds
      2. Open Advertisement Booking Requests panel -> Grid displays all 8 named columns with correct values for the seeded request

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131062
@pytest.mark.tc_142419
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142419_booking_request_detail_view_renders_all_submitted_field_valu(page):
    """ADO-142419 (P2). Verify that the Booking Request detail view renders all submitted field values as read-only

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Click a row to open detail view -> All submitted values (Company Name, Contact Person, Email, Mobile, Ads Type, Preferred Date, Additional Notes) render read-only, not editable

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131062
@pytest.mark.tc_142426
@pytest.mark.skipif(not EMAIL_TEMPLATE_LOCATED, reason='CONDITIONAL - the email-template preview surface is not located yet in the CMS')
def test_142426_acknowledgement_email_template_preview_in_the_cms_renders_th(page):
    """ADO-142426 (P3). Verify that the Acknowledgement Email template preview in the CMS renders the correct EN and AR subject/body with placeholder merge fields visible

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Acknowledgement Email template in CMS -> Template opens
      2. Inspect EN and AR tabs -> Both EN and AR subject/body render with {{full_name}}, {{booking_reference}}, {{advertising_type}}, {{submission_date}} shown as merge tokens, no raw braces bro

    Disposition: conditional - the email-template preview surface is not located yet in the CMS
    """
    pytest.fail('email template surface not located')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.ui
@pytest.mark.pbi_131062
@pytest.mark.tc_142427
@pytest.mark.skipif(not EMAIL_TEMPLATE_LOCATED, reason='CONDITIONAL - the email-template preview surface is not located yet in the CMS')
def test_142427_new_request_to_reviewer_email_template_preview_renders_corre(page):
    """ADO-142427 (P3). Verify that the New-Request-to-Reviewer Email template preview renders correctly with its named merge fields

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open template -> Template opens
      2. Inspect EN/AR -> Subject/body render with {{company_name}}, {{contact_person}}, {{email}}, {{mobile_number}}, {{ads_type}}, {{preferred_date}}, {{additional_notes}}, {{booking_r

    Disposition: conditional - the email-template preview surface is not located yet in the CMS
    """
    pytest.fail('email template surface not located')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142431
def test_142431_site_content_editor_can_perform_full_crud_and_lifecycle_acti(page, browser):
    """ADO-142431 (P2). Verify that a Site Content Editor can perform full CRUD and lifecycle actions on a rate card

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create, edit, preview, publish, unpublish, delete a QCTEST- rate card -> Every action succeeds; each state change reflected in the CMS grid and, where published, on the live page
    """
    ck.check_full_lifecycle(page, browser, AdvertisementRateCardAdminPage, 142431, probe, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131062
@pytest.mark.tc_142432
def test_142432_site_content_author_can_view_and_update_assigned_advertiseme(page):
    """ADO-142432 (P1). Verify that a Site Content Author can view and update assigned advertisement content but cannot publish

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Open an assigned rate card -> Card opens
      2. Edit a field, save -> Edit/save succeeds (Draft)
      3. Attempt to Publish -> Publish action is blocked/unavailable, 'Access Denied. You do not have permission to perform this action.' shown if attempted directly
    """
    ck.check_author_submit_pending(page, AdvertisementRateCardAdminPage, 142432, files=FILES[AdvertisementRateCardAdminPage], edit_key='short_description', edit_value='QCTEST author edit')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131062
@pytest.mark.tc_142433
def test_142433_site_content_author_cannot_access_the_booking_requests_revie(page):
    """ADO-142433 (P1). Verify that a Site Content Author cannot access the Booking Requests review panel

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Attempt to navigate to Advertisement Booking Requests panel URL directly -> Access Denied message shown; panel content not rendered
    """
    ck.check_role_cannot_author(page, AdvertisementBookingRequestAdminPage, ROLE_AUTHOR)


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142434
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142434_qc_admin_reviewer_can_review_approve_and_reject_booking_requ(page):
    """ADO-142434 (P1). Verify that a QC Admin Reviewer can review, approve and reject Booking Requests

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Open a submitted request -> Request opens
      2. Approve it -> Approve sets status Approved + Approval Email sent
      3. Open another, Reject it -> Reject sets status Rejected + no email sent, both actions audit-logged

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_131062
@pytest.mark.tc_142435
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142435_qc_admin_reviewer_cannot_edit_rate_card_content_or_publish_t(page):
    """ADO-142435 (P1). Verify that a QC Admin Reviewer cannot edit rate card content or publish the Advertisements page

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Attempt to open the rate card authoring form and edit a field -> Access Denied message shown; no field-level edit access granted

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142443
def test_142443_site_content_editor_can_create_save_as_draft_preview_and_pub(page, browser):
    """ADO-142443 (P1). Verify that a Site Content Editor can create, save as draft, preview and publish a new rate card, and it appears correctly on the live Advertisements page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Create rate card (title='Print Feature', category='Directory', price=3000, currency=QAR, unit='/issue', ≥1 checklist item, mapped Ads Type='Directory Listing') -> Card created
      2. Save as Draft -> Draft saved, not visible publicly
      3. Preview -> Preview shows the card as it will render, still not public
      4. Publish -> After Publish, card appears live on the Advertisements page with all authored values, in the configured display order
    """
    ck.check_full_lifecycle(page, browser, AdvertisementRateCardAdminPage, 142443, probe, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142448
@pytest.mark.skip(reason='needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see')
def test_142448_flagging_a_card_as_featured_while_another_card_is_already_fe(page):
    """ADO-142448 (P2). Verify that flagging a card as Featured while another card is already Featured is blocked at publish time

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Edit Card B, toggle Featured=true -> Toggle set
      2. Attempt to Publish/Save -> System blocks the change and displays a validation message; Card A remains the only featured card, Card B's Featured flag is not persisted as true

    Disposition: skip - needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142449
def test_142449_publishing_a_rate_card_without_price_currency_or_pricing_uni(page):
    """ADO-142449 (P2). Verify that publishing a rate card without price, currency or pricing unit is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Fill title/category/description/checklist only -> Fields filled
      2. Attempt Publish -> Publish blocked; 'Price, currency and pricing unit are required.' (EN) shown; card remains unpublished
    """
    ck.check_publish_refused(page, AdvertisementRateCardAdminPage, 142449, skip=('price', 'pricing_unit'), files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142450
@pytest.mark.skipif(not CHECKLIST_STRUCTURE_READ, reason="CONDITIONAL - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")
def test_142450_publishing_a_rate_card_without_at_least_one_feature_checklis(page):
    """ADO-142450 (P2). Verify that publishing a rate card without at least one feature checklist item is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave checklist empty -> Checklist left empty
      2. Attempt Publish -> Publish blocked; 'At least one specification is required.' (EN) shown

    Disposition: conditional - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142451
def test_142451_publishing_a_rate_card_without_required_arabic_content_is_bl(page):
    """ADO-142451 (P2). Verify that publishing a rate card without required Arabic content is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Fill only EN title/description -> EN fields filled, AR fields left blank
      2. Attempt Publish -> Publish blocked; 'Arabic content is required.' shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142451, 'ad_title', side='ar', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142454
@pytest.mark.skipif(not AUDIT_LOG_LOCATED, reason='CONDITIONAL - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')
def test_142454_every_admin_change_to_a_rate_card_is_recorded_in_the_audit_l(page):
    """ADO-142454 (P3). Verify that every admin change to a rate card is recorded in the audit log with a generic success toast

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Edit a card field, Save -> Liferay generic success toast shown on save
      2. Open audit log -> Audit log records the change with actor and timestamp

    Disposition: conditional - the audit-log surface is not located yet - automate once it is found on the live CMS (read only)
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the audit-log surface is not located yet - automate once it is found on the live CMS (read only)')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142455
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142455_qc_admin_reviewer_can_filter_booking_requests_by_ads_type(page):
    """ADO-142455 (P3). Verify that a QC Admin Reviewer can filter Booking Requests by Ads Type

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Open Booking Requests panel -> Panel opens
      2. Filter by Ads Type = 'Website Banner' -> Only requests with Ads Type='Website Banner' listed

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142456
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142456_qc_admin_reviewer_can_filter_booking_requests_by_status(page):
    """ADO-142456 (P3). Verify that a QC Admin Reviewer can filter Booking Requests by Status

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Filter by Status='Submitted' -> Only Submitted requests listed

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142457
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142457_qc_admin_reviewer_can_filter_booking_requests_by_date_range(page):
    """ADO-142457 (P3). Verify that a QC Admin Reviewer can filter Booking Requests by date range

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Apply a date range filter covering only one request's submission date -> Only the matching request listed

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142458
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference")
def test_142458_approving_a_booking_request_updates_status_to_approved_and_s(page):
    """ADO-142458 (P1). Verify that approving a Booking Request updates status to Approved and sends the Approval Email

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Open the request -> Request opens
      2. Click Approve -> Status changes to 'Approved'; Approval Date auto-stamped; Approval Email sent to requester with {{full_name}}, {{booking_reference}}, {{approval_date}} resolved

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142459
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference")
def test_142459_rejecting_a_booking_request_updates_status_to_rejected_and_s(page):
    """ADO-142459 (P1). Verify that rejecting a Booking Request updates status to Rejected and sends no email to the requester

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Open the request -> Request opens
      2. Click Reject, optionally add a reason -> Status changes to 'Rejected'; no rejection email sent to the requester's mailbox; record remains stored/queryable (not deleted); audit log entry recorded

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142460
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142460_booking_request_cannot_be_moved_to_any_status_other_than_app(page):
    """ADO-142460 (P2). Verify that a Booking Request cannot be moved to any status other than Approved or Rejected

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Attempt to set status directly to an arbitrary value via any exposed status control -> Only Approved/Rejected are selectable transitions; no other status reachable, no auto-progression occurs without reviewer action

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_131062
@pytest.mark.tc_142461
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142461_internal_notes_added_by_the_reviewer_are_stored_against_the(page):
    """ADO-142461 (P2). Verify that internal notes added by the reviewer are stored against the request and not visible to the requester

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Add Internal Notes='Verified CR, approved for Q4 slot' -> Notes entered
      2. Save -> Notes stored and visible only within the CMS to QC staff
      3. Check the requester's Acknowledgement/Approval email content -> Notes text does not appear anywhere in requester-facing emails or any public surface

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142462
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142462_hero_eyebrow_accepts_a_valid_value_up_to_60_characters_and_r(page, browser):
    """ADO-142462 (P3). Verify that Hero Eyebrow accepts a valid value up to 60 characters and renders on the live page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter value 'Insights & Media Hub' (21 chars) -> Value entered
      2. Publish -> Published
      3. View live page -> Live hero shows the exact eyebrow text

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, AdvertisementsPageAdminPage, 142462, probe, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142463
def test_142463_hero_eyebrow_rejects_an_empty_value(page):
    """ADO-142463 (P2). Verify that Hero Eyebrow rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Attempt Save/Publish -> 'This field is required.' shown; save blocked
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142463, 'hero_eyebrow', side='both', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142464
def test_142464_hero_eyebrow_rejects_a_value_exceeding_60_characters(page):
    """ADO-142464 (P3). Verify that Hero Eyebrow rejects a value exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 61-character string -> Value entered
      2. Attempt Save -> Validation error shown (max-length exceeded); save blocked or value truncated per configured behavior — record actual behavior
    """
    ck.check_over_max_refused(page, AdvertisementsPageAdminPage, 142464, 'hero_eyebrow', 60, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142465
def test_142465_hero_eyebrow_rejects_a_whitespace_only_value(page):
    """ADO-142465 (P3). Verify that Hero Eyebrow rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter only spaces ('   ') -> Spaces entered
      2. Attempt Save -> Treated as empty; 'This field is required.' shown
    """
    ck.check_whitespace_refused(page, AdvertisementsPageAdminPage, 142465, 'hero_eyebrow', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142466
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142466_page_title_accepts_a_valid_value_up_to_100_characters_and_re(page, browser):
    """ADO-142466 (P3). Verify that Page Title accepts a valid value up to 100 characters and renders on the live page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Advertisements' (15 chars) -> Value entered
      2. Publish -> Live hero title renders exactly

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, AdvertisementsPageAdminPage, 142466, probe, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142467
def test_142467_page_title_rejects_an_empty_value(page):
    """ADO-142467 (P2). Verify that Page Title rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142467, 'page_title', side='both', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142468
def test_142468_page_title_rejects_a_value_exceeding_100_characters(page):
    """ADO-142468 (P3). Verify that Page Title rejects a value exceeding 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 101-character string -> Value entered
      2. Save -> Max-length validation error shown
    """
    ck.check_over_max_refused(page, AdvertisementsPageAdminPage, 142468, 'page_title', 100, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142469
def test_142469_page_title_rejects_a_whitespace_only_value(page):
    """ADO-142469 (P3). Verify that Page Title rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementsPageAdminPage, 142469, 'page_title', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142470
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142470_hero_description_accepts_a_valid_value_up_to_200_characters(page, browser):
    """ADO-142470 (P3). Verify that Hero Description accepts a valid value up to 200 characters and renders on the live page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 150-character description -> Value entered
      2. Publish -> Live hero description renders exactly, rich-text formatting intact

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_republish_updates(page, browser, AdvertisementsPageAdminPage, 142470, probe, 'hero_description', 'QCTEST-142470 hero', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142471
def test_142471_hero_description_rejects_an_empty_value(page):
    """ADO-142471 (P2). Verify that Hero Description rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142471, 'hero_description', side='both', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142472
def test_142472_hero_description_rejects_a_value_exceeding_200_characters(page):
    """ADO-142472 (P3). Verify that Hero Description rejects a value exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 201-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementsPageAdminPage, 142472, 'hero_description', 200, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142473
def test_142473_hero_description_rejects_a_whitespace_only_value(page):
    """ADO-142473 (P3). Verify that Hero Description rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementsPageAdminPage, 142473, 'hero_description', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142474
@pytest.mark.skipif(not SINGLETON_PUBLISH_CLEARED, reason='CONDITIONAL - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated')
def test_142474_hero_image_accepts_a_valid_jpg_under_2mb_and_renders_on_the(page, browser):
    """ADO-142474 (P3). Verify that Hero Image accepts a valid JPG under 2MB and renders on the live page

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload hero.jpg (800KB) -> File uploaded
      2. Publish -> Live hero illustration renders the uploaded image

    Disposition: conditional - publishing/unpublishing an entry of a page-level configuration object (SINGLETON) may displace or hide the live QCDEMO entry every visitor sees - automate only once it is confirmed live that a QCTEST entry renders without replacing it; otherwise skip: needs a real shared record mutated
    """
    ck.check_editor_publish_public(page, browser, AdvertisementsPageAdminPage, 142474, probe, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142475
def test_142475_hero_image_rejects_an_unsupported_file_type(page):
    """ADO-142475 (P3). Verify that Hero Image rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload hero.gif -> File uploaded
      2. Attempt Save -> Error shown: unsupported file type; upload rejected
    """
    ck.check_file_refused(page, AdvertisementsPageAdminPage, 142475, 'hero_image', BAD_IMAGE_GIF, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142476
def test_142476_hero_image_rejects_a_file_exceeding_2mb(page):
    """ADO-142476 (P3). Verify that Hero Image rejects a file exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload hero.png (3.5MB) -> File uploaded
      2. Attempt Save -> Error shown: file exceeds 2MB limit; upload rejected
    """
    ck.check_file_refused(page, AdvertisementsPageAdminPage, 142476, 'hero_image', BIG_IMAGE, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142477
def test_142477_hero_image_is_enforced_as_mandatory(page):
    """ADO-142477 (P2). Verify that Hero Image is enforced as mandatory

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave field empty -> Field left empty
      2. Attempt Publish -> Required error shown; publish blocked
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142477, 'hero_image', side='en', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142478
def test_142478_section_eyebrow_accepts_a_valid_value_up_to_60_characters(page):
    """ADO-142478 (P3). Verify that Section Eyebrow accepts a valid value up to 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Advertising rate cards' (23 chars) -> Value entered
      2. Publish -> Live section eyebrow renders exactly
    """
    ck.check_valid_persists(page, AdvertisementsPageAdminPage, 142478, 'section_eyebrow', 'Valid section eyebrow', ar='قيمة صالحة', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142479
def test_142479_section_eyebrow_rejects_an_empty_value(page):
    """ADO-142479 (P2). Verify that Section Eyebrow rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142479, 'section_eyebrow', side='both', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142480
def test_142480_section_eyebrow_rejects_a_value_exceeding_60_characters(page):
    """ADO-142480 (P3). Verify that Section Eyebrow rejects a value exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 61-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementsPageAdminPage, 142480, 'section_eyebrow', 60, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142481
def test_142481_section_eyebrow_rejects_a_whitespace_only_value(page):
    """ADO-142481 (P3). Verify that Section Eyebrow rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementsPageAdminPage, 142481, 'section_eyebrow', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142482
def test_142482_section_title_accepts_a_valid_value_up_to_150_characters(page):
    """ADO-142482 (P3). Verify that Section Title accepts a valid value up to 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Choose the right placement' (27 chars) -> Value entered
      2. Publish -> Live heading renders exactly
    """
    ck.check_valid_persists(page, AdvertisementsPageAdminPage, 142482, 'section_title', 'Valid section title', ar='قيمة صالحة', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142483
def test_142483_section_title_rejects_an_empty_value(page):
    """ADO-142483 (P2). Verify that Section Title rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142483, 'section_title', side='both', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142484
def test_142484_section_title_rejects_a_value_exceeding_150_characters(page):
    """ADO-142484 (P3). Verify that Section Title rejects a value exceeding 150 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 151-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementsPageAdminPage, 142484, 'section_title', 150, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142485
def test_142485_section_title_rejects_a_whitespace_only_value(page):
    """ADO-142485 (P3). Verify that Section Title rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementsPageAdminPage, 142485, 'section_title', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142486
def test_142486_section_description_accepts_a_valid_value_up_to_300_characte(page):
    """ADO-142486 (P3). Verify that Section Description accepts a valid value up to 300 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 200-character description -> Value entered
      2. Publish -> Live description renders exactly
    """
    ck.check_valid_persists(page, AdvertisementsPageAdminPage, 142486, 'section_description', 'Valid section description', ar='قيمة صالحة', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142487
def test_142487_section_description_rejects_an_empty_value(page):
    """ADO-142487 (P2). Verify that Section Description rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementsPageAdminPage, 142487, 'section_description', side='both', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142488
def test_142488_section_description_rejects_a_value_exceeding_300_characters(page):
    """ADO-142488 (P3). Verify that Section Description rejects a value exceeding 300 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 301-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementsPageAdminPage, 142488, 'section_description', 300, files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142489
def test_142489_section_description_rejects_a_whitespace_only_value(page):
    """ADO-142489 (P3). Verify that Section Description rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementsPageAdminPage, 142489, 'section_description', files=FILES[AdvertisementsPageAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142490
def test_142490_card_icon_accepts_a_valid_png_under_2mb_and_renders_on_the_l(page, browser):
    """ADO-142490 (P3). Verify that Card Icon accepts a valid PNG under 2MB and renders on the live card

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload icon.png (500KB) -> File uploaded
      2. Publish -> Live card icon renders the uploaded image
    """
    ck.check_editor_publish_public(page, browser, AdvertisementRateCardAdminPage, 142490, probe, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142491
def test_142491_card_icon_rejects_an_unsupported_file_type(page):
    """ADO-142491 (P3). Verify that Card Icon rejects an unsupported file type

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload icon.bmp -> File uploaded
      2. Attempt Save -> Unsupported-type error shown
    """
    ck.check_file_refused(page, AdvertisementRateCardAdminPage, 142491, 'card_icon', BAD_IMAGE, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142492
def test_142492_card_icon_rejects_a_file_exceeding_2mb(page):
    """ADO-142492 (P3). Verify that Card Icon rejects a file exceeding 2MB

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload icon.svg (4MB) -> File uploaded
      2. Attempt Save -> File-size error shown
    """
    ck.check_file_refused(page, AdvertisementRateCardAdminPage, 142492, 'card_icon', BIG_IMAGE, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142493
def test_142493_card_icon_is_enforced_as_mandatory(page):
    """ADO-142493 (P2). Verify that Card Icon is enforced as mandatory

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt Publish without icon -> Required error shown, publish blocked
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142493, 'card_icon', side='en', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142494
def test_142494_category_eyebrow_label_accepts_a_valid_value_up_to_60_charac(page):
    """ADO-142494 (P3). Verify that Category/Eyebrow Label accepts a valid value up to 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Website' (7 chars) -> Value entered
      2. Publish -> Live card category tag renders 'Website'
    """
    ck.check_valid_persists(page, AdvertisementRateCardAdminPage, 142494, 'category_label', 'Valid category label', ar='قيمة صالحة', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142495
def test_142495_category_eyebrow_label_rejects_an_empty_value(page):
    """ADO-142495 (P2). Verify that Category/Eyebrow Label rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142495, 'category_label', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142496
def test_142496_category_eyebrow_label_rejects_a_value_exceeding_60_characte(page):
    """ADO-142496 (P3). Verify that Category/Eyebrow Label rejects a value exceeding 60 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 61-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementRateCardAdminPage, 142496, 'category_label', 60, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142497
def test_142497_category_eyebrow_label_rejects_a_whitespace_only_value(page):
    """ADO-142497 (P3). Verify that Category/Eyebrow Label rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementRateCardAdminPage, 142497, 'category_label', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142498
def test_142498_advertisement_title_accepts_a_valid_value_up_to_200_characte(page):
    """ADO-142498 (P3). Verify that Advertisement Title accepts a valid value up to 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Digital Banner' (14 chars) -> Value entered
      2. Publish -> Live card title renders 'Digital Banner'
    """
    ck.check_valid_persists(page, AdvertisementRateCardAdminPage, 142498, 'ad_title', 'Valid ad title', ar='قيمة صالحة', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142499
def test_142499_advertisement_title_rejects_an_empty_value(page):
    """ADO-142499 (P2). Verify that Advertisement Title rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142499, 'ad_title', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142500
def test_142500_advertisement_title_rejects_a_value_exceeding_200_characters(page):
    """ADO-142500 (P3). Verify that Advertisement Title rejects a value exceeding 200 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 201-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementRateCardAdminPage, 142500, 'ad_title', 200, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142501
def test_142501_advertisement_title_rejects_a_whitespace_only_value(page):
    """ADO-142501 (P3). Verify that Advertisement Title rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementRateCardAdminPage, 142501, 'ad_title', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142502
def test_142502_price_accepts_a_valid_positive_value_with_up_to_2_decimals_a(page, browser):
    """ADO-142502 (P2). Verify that Price accepts a valid positive value with up to 2 decimals and renders combined with currency and unit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Price=5000.00 (Currency=QAR, Unit='/month') -> Value entered
      2. Publish -> Live card shows 'QAR 5,000.00 /month' (or configured formatting) together as one unit
    """
    ck.check_editor_publish_public(page, browser, AdvertisementRateCardAdminPage, 142502, probe, files=FILES[AdvertisementRateCardAdminPage], extra={'price': '5000.00', 'pricing_unit': '/month'})


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142503
def test_142503_price_rejects_an_empty_value(page):
    """ADO-142503 (P2). Verify that Price rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> 'Price, currency and pricing unit are required.' shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142503, 'price', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142504
def test_142504_price_rejects_zero_and_negative_values(page):
    """ADO-142504 (P2). Verify that Price rejects zero and negative values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0, Save -> Validation error shown
      2. Enter -500, Save -> Validation error shown; positive-only enforced on both attempts
    """
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142504, 'price', '0', short='zero', files=FILES[AdvertisementRateCardAdminPage])
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142504, 'price', '-500', short='neg', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142505
def test_142505_price_rejects_a_non_numeric_value(page):
    """ADO-142505 (P3). Verify that Price rejects a non-numeric value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'five thousand' -> Value entered
      2. Save -> Validation error: numeric value required
    """
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142505, 'price', 'abc', short='nan', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142506
def test_142506_price_rejects_a_value_with_more_than_2_decimal_places(page):
    """ADO-142506 (P3). Verify that Price rejects a value with more than 2 decimal places

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 5000.999 -> Value entered
      2. Save -> Validation error: max 2 decimal places exceeded
    """
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142506, 'price', '5000.999', short='dec', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142507
def test_142507_currency_accepts_a_valid_selection_and_defaults_to_qar(page):
    """ADO-142507 (P3). Verify that Currency accepts a valid selection and defaults to QAR

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open new card form, inspect Currency -> Dropdown pre-populated with QAR as default; selecting another valid currency (e.g. USD) persists correctly
    """
    admin = AdvertisementRateCardAdminPage(page)
    admin.open_form(ROLE_EDITOR)
    assert admin.value('currency') == admin.DEFAULT_CURRENCY, f"Currency defaults to {admin.value('currency')!r}, not QAR"


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142508
def test_142508_currency_rejects_being_left_unselected_on_a_form_where_the_d(page):
    """ADO-142508 (P3). Verify that Currency rejects being left unselected on a form where the default was cleared

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Clear the Currency selection -> Selection cleared
      2. Attempt Save -> 'Price, currency and pricing unit are required.' shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142508, 'currency', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142509
def test_142509_pricing_unit_accepts_a_valid_value_up_to_30_characters_and_r(page, browser):
    """ADO-142509 (P3). Verify that Pricing Unit accepts a valid value up to 30 characters and renders combined with price

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter '/month' (6 chars) -> Value entered
      2. Publish -> Live card shows unit appended to price exactly as 'QAR 5,000 /month'
    """
    ck.check_editor_publish_public(page, browser, AdvertisementRateCardAdminPage, 142509, probe, files=FILES[AdvertisementRateCardAdminPage], extra={'pricing_unit': '/issue'})


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142510
def test_142510_pricing_unit_rejects_an_empty_value(page):
    """ADO-142510 (P2). Verify that Pricing Unit rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> 'Price, currency and pricing unit are required.' shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142510, 'pricing_unit', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142511
def test_142511_pricing_unit_rejects_a_value_exceeding_30_characters(page):
    """ADO-142511 (P3). Verify that Pricing Unit rejects a value exceeding 30 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 31-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementRateCardAdminPage, 142511, 'pricing_unit', 30, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142512
def test_142512_pricing_unit_rejects_a_whitespace_only_value(page):
    """ADO-142512 (P3). Verify that Pricing Unit rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementRateCardAdminPage, 142512, 'pricing_unit', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142513
def test_142513_short_description_accepts_a_valid_value_up_to_500_characters(page):
    """ADO-142513 (P3). Verify that Short Description accepts a valid value up to 500 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 300-character description -> Value entered
      2. Publish -> Live card description renders exactly
    """
    ck.check_valid_persists(page, AdvertisementRateCardAdminPage, 142513, 'short_description', 'Valid short description', ar='قيمة صالحة', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142514
def test_142514_short_description_rejects_an_empty_value(page):
    """ADO-142514 (P2). Verify that Short Description rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142514, 'short_description', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142515
def test_142515_short_description_rejects_a_value_exceeding_500_characters(page):
    """ADO-142515 (P3). Verify that Short Description rejects a value exceeding 500 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 501-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementRateCardAdminPage, 142515, 'short_description', 500, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142516
def test_142516_short_description_rejects_a_whitespace_only_value(page):
    """ADO-142516 (P3). Verify that Short Description rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementRateCardAdminPage, 142516, 'short_description', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142517
@pytest.mark.skipif(not CHECKLIST_STRUCTURE_READ, reason="CONDITIONAL - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")
def test_142517_feature_checklist_accepts_the_minimum_of_1_item_and_renders(page):
    """ADO-142517 (P3). Verify that the Feature Checklist accepts the minimum of 1 item and renders it beneath the description with a check icon

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add 1 item ('24/7 visibility') -> Item added
      2. Publish -> Live card shows exactly 1 checklist line with a check icon beneath the description

    Disposition: conditional - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142518
@pytest.mark.skipif(not CHECKLIST_STRUCTURE_READ, reason="CONDITIONAL - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")
def test_142518_feature_checklist_accepts_the_maximum_of_5_items_and_renders(page):
    """ADO-142518 (P3). Verify that the Feature Checklist accepts the maximum of 5 items and renders all 5 in configured order

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Add 5 distinct items in a specific order -> Items added
      2. Publish -> Live card shows all 5 items, each with a check icon, in the configured order

    Disposition: conditional - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142519
@pytest.mark.skipif(not CHECKLIST_STRUCTURE_READ, reason="CONDITIONAL - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")
def test_142519_publishing_with_0_checklist_items_is_blocked(page):
    """ADO-142519 (P2). Verify that publishing with 0 checklist items is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave checklist empty -> Checklist left empty
      2. Attempt Publish -> 'At least one specification is required.' shown

    Disposition: conditional - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142520
def test_142520_checklist_item_exceeding_100_characters_per_line_is_rejected(page):
    """ADO-142520 (P3). Verify that a checklist item exceeding 100 characters per line is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 101-character checklist item -> Item entered
      2. Save -> Max-length (100 chars/line) validation error shown
    """
    ck.check_over_max_refused(page, AdvertisementChecklistItemAdminPage, 142520, 'item_text', 100, files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_131062
@pytest.mark.tc_142521
@pytest.mark.skip(reason='needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see')
def test_142521_featured_toggle_can_be_set_on_a_single_card_and_persists_on(page):
    """ADO-142521 (P2). Verify that the Featured toggle can be set on a single card and persists on publish

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Toggle Featured on -> Toggle set
      2. Publish -> Card publishes as featured; live page shows it in the highlighted style

    Disposition: skip - needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142522
@pytest.mark.skip(reason='needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see')
def test_142522_setting_a_second_card_s_featured_toggle_while_one_is_already(page):
    """ADO-142522 (P2). Verify that setting a second card's Featured toggle while one is already featured is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Toggle Card B Featured=true -> Toggle set
      2. Attempt Publish -> Validation message blocks the change; only Card A remains featured

    Disposition: skip - needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142523
def test_142523_book_now_button_label_accepts_a_valid_custom_value_up_to_50(page):
    """ADO-142523 (P3). Verify that Book Now Button Label accepts a valid custom value up to 50 characters and overrides the default

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter custom label 'Reserve This Slot' (18 chars) -> Label entered
      2. Publish -> Live card's action button shows 'Reserve This Slot' instead of the default
    """
    ck.check_valid_persists(page, AdvertisementRateCardAdminPage, 142523, 'book_now_label', 'Valid book now label', ar='قيمة صالحة', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142524
def test_142524_book_now_button_label_defaults_to_book_now_when_left_unset(page, browser):
    """ADO-142524 (P3). Verify that Book Now Button Label defaults to 'Book Now' when left unset

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave label field at default -> Field left at default
      2. Publish -> Live card button shows 'Book Now'
    """
    ck.check_editor_publish_public(page, browser, AdvertisementRateCardAdminPage, 142524, probe, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142525
def test_142525_book_now_button_label_rejects_a_value_exceeding_50_character(page):
    """ADO-142525 (P3). Verify that Book Now Button Label rejects a value exceeding 50 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 51-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementRateCardAdminPage, 142525, 'book_now_label', 50, files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142526
def test_142526_book_now_button_label_rejects_a_whitespace_only_value(page):
    """ADO-142526 (P3). Verify that Book Now Button Label rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Falls back to required/default handling — required error or default re-applied (verify actual behavior); does not save as blank
    """
    ck.check_whitespace_refused(page, AdvertisementRateCardAdminPage, 142526, 'book_now_label', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142527
@pytest.mark.skipif(not ADS_TYPE_OBJECT_READ, reason='CONDITIONAL - the Ads Type object (Published vs Draft types) is read live first')
def test_142527_mapped_ads_type_dropdown_lists_only_published_ads_type_recor(page):
    """ADO-142527 (P2). Verify that Mapped Ads Type dropdown lists only Published Ads Type records and persists the selection

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Mapped Ads Type dropdown -> Only the 2 Published types listed (Draft type absent)
      2. Select a Published type, Save -> Selection persists and correctly pre-selects on the frontend modal

    Disposition: conditional - the Ads Type object (Published vs Draft types) is read live first
    """
    pytest.fail('body not scripted until the condition is resolved: ' + 'the Ads Type object (Published vs Draft types) is read live first')


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142528
def test_142528_mapped_ads_type_rejects_being_left_unselected(page):
    """ADO-142528 (P2). Verify that Mapped Ads Type rejects being left unselected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave unselected -> Left unselected
      2. Attempt Publish -> Required error shown, publish blocked
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142528, 'mapped_ads_type', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142529
def test_142529_display_order_accepts_a_valid_positive_integer_and_controls(page, browser):
    """ADO-142529 (P3). Verify that Display Order accepts a valid positive integer and controls the card's rendering position

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set Display Order=1 -> Order set
      2. Publish -> Card renders first among published cards
    """
    ck.check_editor_publish_public(page, browser, AdvertisementRateCardAdminPage, 142529, probe, files=FILES[AdvertisementRateCardAdminPage], extra={'display_order': '9900'})


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142530
def test_142530_display_order_rejects_an_empty_value(page):
    """ADO-142530 (P3). Verify that Display Order rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementRateCardAdminPage, 142530, 'display_order', side='both', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142531
def test_142531_display_order_rejects_zero_or_a_negative_value(page):
    """ADO-142531 (P3). Verify that Display Order rejects zero or a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0, Save -> Validation error shown
      2. Enter -1, Save -> Validation error shown on both; positive-integer-only enforced
    """
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142531, 'display_order', '0', short='zero', files=FILES[AdvertisementRateCardAdminPage])
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142531, 'display_order', '-500', short='neg', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142532
def test_142532_display_order_rejects_a_non_numeric_value(page):
    """ADO-142532 (P3). Verify that Display Order rejects a non-numeric value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'first' -> Value entered
      2. Save -> Validation error: numeric value required
    """
    ck.check_value_refused(page, AdvertisementRateCardAdminPage, 142532, 'display_order', 'abc', short='nan', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142533
def test_142533_checklist_item_text_accepts_a_valid_value_up_to_100_characte(page):
    """ADO-142533 (P3). Verify that Checklist Item Text accepts a valid value up to 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'Premium placement' (18 chars) -> Value entered
      2. Publish -> Live card checklist line renders exactly
    """
    ck.check_valid_persists(page, AdvertisementChecklistItemAdminPage, 142533, 'item_text', 'Valid item text', ar='قيمة صالحة', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142534
def test_142534_checklist_item_text_rejects_an_empty_value_when_the_item_row(page):
    """ADO-142534 (P3). Verify that Checklist Item Text rejects an empty value when the item row is kept

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave item text blank, row not removed -> Text left blank
      2. Attempt Save -> Required error shown for that row
    """
    ck.check_empty_refused(page, AdvertisementChecklistItemAdminPage, 142534, 'item_text', side='both', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142535
def test_142535_checklist_item_text_rejects_a_value_exceeding_100_characters(page):
    """ADO-142535 (P3). Verify that Checklist Item Text rejects a value exceeding 100 characters

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a 101-character string -> Value entered
      2. Save -> Max-length error shown
    """
    ck.check_over_max_refused(page, AdvertisementChecklistItemAdminPage, 142535, 'item_text', 100, files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142536
def test_142536_checklist_item_text_rejects_a_whitespace_only_value(page):
    """ADO-142536 (P3). Verify that Checklist Item Text rejects a whitespace-only value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces -> Spaces entered
      2. Save -> Required error shown
    """
    ck.check_whitespace_refused(page, AdvertisementChecklistItemAdminPage, 142536, 'item_text', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142537
def test_142537_checklist_item_display_order_accepts_a_valid_positive_intege(page):
    """ADO-142537 (P3). Verify that Checklist Item Display Order accepts a valid positive integer and controls item rendering order

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Set order=1 for first item -> Order set
      2. Publish -> Item renders in the corresponding position on the live card
    """
    ck.check_valid_persists(page, AdvertisementChecklistItemAdminPage, 142537, 'item_display_order', '9900', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142538
def test_142538_checklist_item_display_order_rejects_an_empty_value(page):
    """ADO-142538 (P3). Verify that Checklist Item Display Order rejects an empty value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save -> Required error shown
    """
    ck.check_empty_refused(page, AdvertisementChecklistItemAdminPage, 142538, 'item_display_order', side='both', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142539
def test_142539_checklist_item_display_order_rejects_zero_or_a_negative_valu(page):
    """ADO-142539 (P3). Verify that Checklist Item Display Order rejects zero or a negative value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 0, Save -> Validation error shown
      2. Enter -1, Save -> Validation error shown on both
    """
    ck.check_value_refused(page, AdvertisementChecklistItemAdminPage, 142539, 'item_display_order', '0', short='zero', files=FILES[AdvertisementChecklistItemAdminPage])
    ck.check_value_refused(page, AdvertisementChecklistItemAdminPage, 142539, 'item_display_order', '-500', short='neg', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142540
def test_142540_checklist_item_display_order_rejects_a_non_numeric_value(page):
    """ADO-142540 (P3). Verify that Checklist Item Display Order rejects a non-numeric value

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 'one' -> Value entered
      2. Save -> Validation error shown
    """
    ck.check_value_refused(page, AdvertisementChecklistItemAdminPage, 142540, 'item_display_order', 'abc', short='nan', files=FILES[AdvertisementChecklistItemAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142572
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142572_internal_notes_accepts_a_valid_filled_value_up_to_1000_chara(page):
    """ADO-142572 (P3). Verify that Internal Notes accepts a valid filled value up to 1000 characters

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Enter a 500-character note -> Note entered
      2. Save -> Value accepted and stored against the Booking Request

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142573
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142573_internal_notes_is_accepted_when_left_empty_being_optional(page):
    """ADO-142573 (P3). Verify that Internal Notes is accepted when left empty, being optional

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Leave blank -> Left blank
      2. Save the reviewer action -> No validation error; request processed normally

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142574
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142574_internal_notes_rejects_a_value_exceeding_1000_characters(page):
    """ADO-142574 (P3). Verify that Internal Notes rejects a value exceeding 1000 characters

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Enter a 1001-character string -> Value entered
      2. Attempt Save -> Max-length validation error shown

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_131062
@pytest.mark.tc_142577
def test_142577_saved_rate_card_s_field_values_persist_correctly_after_save(page):
    """ADO-142577 (P3). Verify that a saved rate card's field values persist correctly after Save → reload

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Save as Draft (all fields filled) -> Saved
      2. Reload the CMS edit form -> All previously entered field values (icon, category, title, price, currency, unit, description, checklist, display order) are retained exactly
    """
    ck.check_valid_persists(page, AdvertisementRateCardAdminPage, 142577, 'short_description', 'QCTEST persisted description', ar='وصف محفوظ', files=FILES[AdvertisementRateCardAdminPage])


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_131062
@pytest.mark.tc_142580
@pytest.mark.skip(reason='needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see')
def test_142580_second_admin_cannot_publish_a_card_as_featured_while_a_first(page):
    """ADO-142580 (P3). Verify that a second admin cannot publish a card as Featured while a first admin's Featured card publish is already in flight

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Publish Card A as Featured -> Card A published Featured
      2. Immediately attempt to publish Card B as Featured -> Card B's publish is blocked with the featured-conflict validation message regardless of timing

    Disposition: skip - needs a real shared record mutated: setting Featured on a QCTEST record unsets the live featured record visitors see
    """
    raise AssertionError("not reached - skipped, see reason")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_131062
@pytest.mark.tc_142581
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")
def test_142581_rejecting_an_already_rejected_booking_request_is_not_possibl(page):
    """ADO-142581 (P3). Verify that rejecting an already-Rejected Booking Request is not possible

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Reopen the Rejected request -> Request reopened
      2. Attempt Reject again -> Reject action is unavailable/disabled for a terminal Rejected record, or is rejected with a state-conflict message — no duplicate audit entries or emails fire

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_131062
@pytest.mark.tc_142582
@pytest.mark.skipif(not REVIEWER_ROLE_AVAILABLE, reason="CONDITIONAL - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference")
def test_142582_approving_an_already_approved_booking_request_does_not_re_tr(page):
    """ADO-142582 (P3). Verify that approving an already-Approved Booking Request does not re-trigger a duplicate Approval Email

    Account: QC Admin Reviewer (named by the case; not one of the eight provisioned roles).
    Steps (from the approved case):
      1. Reopen the Approved request -> Request reopened
      2. Attempt Approve again -> Action is unavailable/disabled for a terminal Approved record, or is blocked with a state-conflict message — no second Approval Email sent

    Disposition: conditional - the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the case names a 'QC Admin Reviewer' account, which is not one of the eight provisioned roles (standards.md, Named CMS User Roles) - needs the account or a ruling; needs a QCTEST submission/subscriber to mutate; real visitor records may only be read - automate only once a QCTEST record can be created (public form without a CAPTCHA wall, or an authoring add) and deleted by exact reference")


@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_131062
@pytest.mark.tc_142584
@pytest.mark.skipif(not CHECKLIST_STRUCTURE_READ, reason="CONDITIONAL - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")
def test_142584_feature_checklist_s_maximum_of_5_items_is_enforced_a_6th_ite(page):
    """ADO-142584 (P3). Verify that the Feature Checklist's maximum of 5 items is enforced — a 6th item cannot be added

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to add a 6th checklist item (5 already present) -> Add-item control is disabled at 5, or the 6th add attempt is rejected with a max-items message

    Disposition: conditional - the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed
    """
    pytest.fail('body not scripted until the condition is resolved: ' + "the Feature Checklist's structure (own object vs repeater) is read live first; automate once confirmed")

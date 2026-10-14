"""
cms/tests/partners_offers/test_partners_offers_control_panel.py - Control_Panel cases for PBI 130720
Partners & Offers (Test Plan 137724, suite 140379): Azure Priority 1-3, Automation-tagged.

Scripted 2026-10-04 (Engineer A) from the approved cases in
.claude/qa-runs/phase3_130720_cp_batch.json, after the 2026-10-01 block lifted (the Site Content
Editor now gets the four authoring forms). Field labels / refs / required flags were read live the
same day (cms/pages/partners_offers/partners_offers_admin_page.py). Ordered P1, P2, then P3.

Each function is one Azure case; the body calls a shared check in cms/tests/authoring_checks.py
(ck), one of Engineer B's in cms/tests/certificate_of_origin/b_checks.py (bk, imported, not
copied), or this PBI's own in cms/tests/partners_offers/po_checks.py (po). Form mechanics come from
B's FragmentFormMixin: network-watched save with the record ID taken from the write, a refusal
that needs a POSITIVE signal, status / History / delete BY ID, cached role sessions verified
against my-user-account, and the Editor Pending->Published settle.

Data rules:
  - every record is QCTEST-<tc_id>-<short>-<run token> (bk.unique_qctest_titles, autouse), deleted
    BY ID in a finally block every run; real QCDEMO offers / categories / tiers are read only;
  - cases naming a real record ('Medical Centers', 'Restaurants', 'Elite') either only LINK a
    QCTEST offer to it by name (the field is free text), or are re-expressed on a QCTEST record;
  - Partner Offer has no Active Status field: its public gate is Published + an in-window
    validity (default 2026-09-21..2026-12-31). Category / Tier carry Active Status (ticked for
    public checks);
  - public reads use a fresh logged-out context; Load More is paged through.

Accounts via cms_role_credentials(): Editor (create -> Published), Author (Pending Review),
Content Contributor (named by 144366), never TEST_USER.

Character-limit cases are skipped as N/A (user decision 2026-10-03). Partners Offers Page publish
cases are skip CONDITIONAL (the singleton's one entry IS the live page).
"""

import tempfile
from pathlib import Path

import pytest

from cms.pages.partners_offers.partners_offers_admin_page import (
    MembershipTierAdminPage,
    PartnerCategoryAdminPage,
    PartnerOfferAdminPage,
    PartnersOffersPageAdminPage,
)
from cms.tests import authoring_checks as ck
from cms.tests import live_b11 as lb
from cms.tests import live_b11_cases as lc
from cms.tests.certificate_of_origin import b_checks as bk
from cms.tests.certificate_of_origin.b_checks import unique_qctest_titles  # noqa: F401 - autouse: run-unique QCTEST titles
from cms.tests.partners_offers import po_checks as po

_FX = Path(__file__).resolve().parent / "fixtures"
VALID_JPG = str(_FX / "valid_image_500kb.jpg")
VALID_PNG = str(_FX / "valid_icon_200kb.png")
BAD_EXE = str(_FX / "unsupported_file.exe")
VALID_DOCX = str(_FX / "valid_form.docx")
VALID_PDF = str(_FX / "valid_pdf_3mb.pdf")

# A valid logo on every offer: Partner Logo is required on the live form.
OFFER_FILES = {"partner_logo": VALID_PNG}
# Every required field valid on a page-singleton refusal, so only the case's own field is missing.
PAGE_FILES = {"hero_illustration": VALID_JPG}

PROBE = po.card_probe()

# 144368: a real, published QCDEMO offer read live 2026-10-04 (id 167093) - only deep-linked, never changed.
REAL_OFFER_ERC = "QCDEMO-130720-OFFER-01"
REAL_OFFER_LEAK = "Namaa Health Network"

CONTRACT_URL = "https://qcdev.ihorizons.com/documents/QCTEST-contract.pdf"  # the case's own example
AR_NAME_144422 = f"QCTEST-واحة سبا {bk.RUN_TOKEN}"


def _text(prefix: str, n: int, word: str) -> str:
    return (prefix + " " + " ".join([word] * n))[:n].rstrip()


DESC_250 = _text("QCTEST-144431 description", 250, "benefit")
DESC_250_AR = _text("QCTEST-144431 وصف", 250, "ميزة")
TERMS_500 = _text("QCTEST-144606 terms", 500, "condition")
TERMS_500_AR = _text("QCTEST-144606 شروط", 500, "شرط")


def big_png_15mb() -> str:
    """The case's 15 MB PNG, generated at run time in the temp dir (no committed fixture edited)."""
    from tools.fixture_factory import make_png

    dest = Path(tempfile.gettempdir()) / "qctest_partner_logo_15mb.png"
    if not dest.exists() or dest.stat().st_size < 15 * 1024 * 1024:
        dest.write_bytes(make_png(15 * 1024 * 1024))
    return str(dest)


# Conditional-case gate. Flip only when it is confirmed live that a QCTEST Partners Offers Page
# entry can be published without replacing QCDEMO-130720-PO-PAGE-01 (id 167087, "Partners & Offers").
PAGE_PUBLISH_CLEARED = False
SINGLETON_REASON = (
    "CONDITIONAL - publishing a Partners Offers Page entry (page-level singleton) may displace the live "
    "page entry QCDEMO-130720-PO-PAGE-01 (id 167087, 'Partners & Offers') that every visitor sees; the "
    "object has no Active Status to keep a QCTEST entry hidden. Automate once it is confirmed that a "
    "QCTEST entry renders without replacing it; otherwise it needs that real shared record mutated."
)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144363
@pytest.mark.xdist_group("po_partner-offer")
def test_144363_a_site_content_editor_can_perform_the_full_crud_lifecycle_on_a_par(page, browser):
    """ADO-144363 (P1). Verify that a Site Content Editor can perform the full CRUD lifecycle on a Partner Offer

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in to Control_Panel as Site Content Editor -> Login succeeds; Partner Offer management area is accessible
      2. Open Object Authoring for Partner Offer and create/edit/preview/publish/unpublish/delete a QCTEST- offer -> Every lifecycle action (create as Draft, edit, preview, publish, unpublish, delete) completes successfully with the Liferay success toast

    Note: Lifecycle on a disposable QCTEST offer: Draft -> Preview link -> edit -> Submit (Editor lands on Published, by ID) -> public card -> Unpublish -> hidden -> Delete. Toast text is not asserted (a missing toast is not a bug, user rule).
    """
    ck.check_full_lifecycle(page, browser, PartnerOfferAdminPage, 144363, PROBE, files=OFFER_FILES,
                          edit_key='partner_location', edit_value='QCTEST-144363 edited location')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144365
@pytest.mark.xdist_group("po_partner-offer")
def test_144365_a_public_visitor_cannot_access_the_control_panel_offer_category_ma(page, browser):
    """ADO-144365 (P1). Verify that a Public Visitor cannot access the Control Panel offer/category management area

    Account: none - fresh logged-out context (new_context(browser, use_auth_state=False)).
    Steps (from the approved case):
      1. While logged out, navigate directly to the Control_Panel Partner Offer management URL -> Access is denied / visitor is redirected to login — no offer management UI is exposed to an unauthenticated user
    """
    ck.check_anonymous_denied(browser, PartnerOfferAdminPage)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144366
@pytest.mark.xdist_group("po_partner-offer")
def test_144366_a_role_without_partner_offer_permission_sees_access_denied_when_at(page):
    """ADO-144366 (P1). Verify that a role without Partner Offer permission sees 'Access Denied' when attempting to publish an offer

    Account: QC Site Content Contributor via cms_role_credentials('Content Contributor'); teardown as Editor.
    Steps (from the approved case):
      1. Log in to Control_Panel as Content Contributor -> Login succeeds
      2. Attempt to publish a QCTEST- offer via Object Authoring -> Action is blocked with 'Access Denied. You do not have permission to perform this action.' (EN) / 'تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء' (AR) shown per active language

    Note: Asserts the behaviour: the Contributor's QCTEST offer never reaches Published (status read BY ID) and no Publish/Approve row action is offered. The exact 'Access Denied' wording is recorded, not asserted (different wording is not a bug, user rule).
    """
    po.check_role_cannot_publish(page, PartnerOfferAdminPage, 144366, 'Content Contributor', files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144368
@pytest.mark.xdist_group("po_partner-offer")
def test_144368_deep_linking_to_the_admin_offer_edit_url_while_logged_out_redirect(page, browser):
    """ADO-144368 (P1). Verify that deep-linking to the admin offer-edit URL while logged out redirects to login rather than exposing content

    Account: none - fresh logged-out context; deep link to a real QCDEMO offer's edit URL (read-only).
    Steps (from the approved case):
      1. While logged out, paste the direct Control_Panel edit URL for a known offer entry ID into the browser -> Request is redirected to the Control_Panel login page; no offer edit form or field data is exposed
    """
    po.check_anonymous_edit_link_denied(browser, PartnerOfferAdminPage, REAL_OFFER_ERC, REAL_OFFER_LEAK)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144404
@pytest.mark.xdist_group("po_partner-offer")
def test_144404_a_site_content_editor_can_create_a_full_partner_offer_record_end_t(page, browser):
    """ADO-144404 (P1). Verify that a Site Content Editor can create a full Partner Offer record end-to-end and it becomes visible on the public listing

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor and open Object Authoring for Partner Offer -> Form loads with all required fields
      2. Fill Partner Name EN/AR, Category, Location, Description EN/AR, Terms EN/AR, Validity Start=2026-09-21/End=2026-12-31, Tier=General, Logo -> All fields accept the entered values
      3. Click Publish -> Offer is published; Liferay success toast shown in the active language
      4. Open the public Partners & Offers page (fresh, logged-out browser context) -> 'QCTEST-Al Waha Spa' appears as a card with all entered details, under 'Beauty and Fitness'

    Note: The case's 'QCTEST-Al Waha Spa' is carried as the run-unique QCTEST title. Card is checked under the 'Beauty and Fitness' filter in a fresh logged-out context.
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144404, 'full', OFFER_FILES,
                        extra={'partner_category': 'Beauty and Fitness', 'membership_tier': 'General',
                               'partner_location': 'Doha QCTEST-144404', 'validity_start': '2026-09-21', 'validity_end': '2026-12-31'},
                        ar_extra={'partner_location': 'الدوحة QCTEST-144404'},
                        category='Beauty and Fitness', card_expect=['Beauty and Fitness', 'Doha QCTEST-144404', 'General'], check_logo=True)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.auth
@pytest.mark.pbi_130720
@pytest.mark.tc_144364
@pytest.mark.xdist_group("po_partner-offer")
def test_144364_a_site_content_author_can_view_and_update_only_assigned_partner_of(page):
    """ADO-144364 (P2). Verify that a Site Content Author can view and update only assigned Partner Offer records, without direct publish rights

    Account: QC Site Content Author via cms_role_credentials('Site Content Author'); teardown as Editor.
    Steps (from the approved case):
      1. Log in to Control_Panel as Site Content Author -> Login succeeds; assigned offer is accessible and editable
      2. Open an assigned QCTEST- offer and edit a field -> Field edit is accepted and saved
      3. Attempt to publish directly -> Direct Publish action is not available/blocked — the record can only be submitted for review, per the role's rights

    Note: 'Assigned' record = the Author's own QCTEST offer (Owner permission). Asserts: edit accepted, Submit lands on Pending Review (never Published), no Publish/Approve row action.
    """
    ck.check_author_submit_pending(page, PartnerOfferAdminPage, 144364, files=OFFER_FILES,
                                  edit_key='partner_location', edit_value='QCTEST-144364 author edit')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144405
@pytest.mark.xdist_group("po_partner-category")
def test_144405_a_newly_added_active_partner_category_auto_appears_in_the_public_f(page, browser):
    """ADO-144405 (P2). Verify that a newly-added active Partner Category auto-appears in the public filter dropdown without redevelopment

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor and open the Partner Category lookup management screen -> Category creation form accepts the new entry
      2. Add category 'QCTEST-Wellness Centers', set Active = true, save -> Category saves; Liferay success toast shown
      3. Open the public Partners & Offers page and open the category dropdown -> 'QCTEST-Wellness Centers' appears in the dropdown's option list with no code deployment needed

    Note: 'QCTEST-Wellness Centers' is carried as the run-unique QCTEST category title; the public dropdown is read logged-out.
    """
    po.check_category_public(page, browser, PartnerCategoryAdminPage, 144405)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.pbi_130720
@pytest.mark.tc_144406
@pytest.mark.xdist_group("po_partner-category+partner-offer")
def test_144406_deactivating_a_category_with_published_offers_still_assigned_is_bl(page, browser):
    """ADO-144406 (P2). Verify that deactivating a Category with published offers still assigned is blocked with a reassignment warning

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor and open the Partner Category lookup for 'Medical Centers' -> Lookup form loads current Active=true state
      2. Attempt to set Active Status = false and save -> Save is blocked with a warning that published offers must be reassigned first; category remains Active

    Note: Re-expressed on disposable data: the real 'Medical Centers' category is never touched; a QCTEST category with a Published QCTEST offer assigned is deactivated instead.
    """
    po.check_category_deactivate_blocked(page, browser, PartnerCategoryAdminPage, PartnerOfferAdminPage, 144406, OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144408
@pytest.mark.xdist_group("po_partner-offer")
def test_144408_unpublishing_a_partner_offer_removes_it_from_the_public_listing_an(page, browser):
    """ADO-144408 (P2). Verify that unpublishing a Partner Offer removes it from the public listing and its modal

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor and unpublish a QCTEST- offer -> Offer status changes to Unpublished; success toast shown
      2. Load the public Partners & Offers page (fresh logged-out context) -> Offer no longer appears in the grid
      3. Attempt to reach the offer's details via a previously-bookmarked deep interaction (re-click the category it was under) -> No 'Offer details' entry point exists for it anywhere on the public page

    Note: No card = no 'Offer details' entry point for the offer anywhere on the public page.
    """
    ck.check_unpublish_hides(page, browser, PartnerOfferAdminPage, 144408, PROBE, files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_high
@pytest.mark.pbi_130720
@pytest.mark.tc_144409
@pytest.mark.xdist_group("po_partner-offer")
def test_144409_deleting_a_partner_offer_removes_it_from_the_listing_and_the_modal(page, browser):
    """ADO-144409 (P2). Verify that deleting a Partner Offer removes it from the listing and the modal never opens for it

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Log in as Site Content Editor and delete a QCTEST- offer via Object Authoring -> Offer is removed from Object Authoring; success toast shown
      2. Load the public Partners & Offers page (fresh logged-out context) -> Offer no longer appears anywhere on the public listing; no residual card or modal entry point remains
    """
    ck.check_delete_removes(page, browser, PartnerOfferAdminPage, 144409, PROBE, files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144411
@pytest.mark.xdist_group("po_partners-offers-page")
def test_144411_publishing_hero_content_with_a_missing_arabic_hero_title_is_blocke(page):
    """ADO-144411 (P2). Verify that publishing hero content with a missing Arabic Hero Title is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter an English value for Hero Title, leave the Arabic field empty -> English value is entered; Arabic field remains empty
      2. Attempt to publish -> Publish is blocked with 'Arabic content is required.' / 'المحتوى بالعربية مطلوب'

    Note: Refusal on the page singleton, run with Active Status unticked (as the COO refusals): nothing reaches visitors even if the refusal fails.
    """
    bk.check_required_by_case(bk.check_ar_required_refused, PartnersOffersPageAdminPage, 'page_title',
                             page, PartnersOffersPageAdminPage, 144411, 'page_title', files=PAGE_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144415
@pytest.mark.xdist_group("po_partner-category")
def test_144415_saving_a_partner_category_with_missing_arabic_name_is_blocked(page):
    """ADO-144415 (P2). Verify that saving a Partner Category with missing Arabic name is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter English name 'QCTEST-Shops' only, leave Arabic blank -> English name is entered; Arabic name remains empty
      2. Save -> Save is blocked with 'Arabic content is required.' / 'المحتوى بالعربية مطلوب'
    """
    bk.check_required_by_case(bk.check_ar_required_refused, PartnerCategoryAdminPage, 'category_name',
                             page, PartnerCategoryAdminPage, 144415, 'category_name')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144419
@pytest.mark.xdist_group("po_membership-tier")
def test_144419_saving_a_membership_tier_with_missing_arabic_name_is_blocked(page):
    """ADO-144419 (P2). Verify that saving a Membership Tier with missing Arabic name is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter English name 'QCTEST-Platinum' only, leave Arabic blank -> English name is entered; Arabic name remains empty
      2. Save -> Save is blocked with 'Arabic content is required.' / 'المحتوى بالعربية مطلوب'
    """
    bk.check_required_by_case(bk.check_ar_required_refused, MembershipTierAdminPage, 'tier_name',
                             page, MembershipTierAdminPage, 144419, 'tier_name')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144423
@pytest.mark.xdist_group("po_partner-offer")
def test_144423_publishing_an_offer_with_a_missing_partner_name_in_arabic_is_block(page):
    """ADO-144423 (P2). Verify that publishing an offer with a missing Partner Name in Arabic is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Fill Partner Name EN only, leave AR blank -> English name is entered; Arabic name remains empty
      2. Attempt to publish -> Publish is blocked with 'Arabic content is required.' / 'المحتوى بالعربية مطلوب'
    """
    bk.check_required_by_case(bk.check_ar_required_refused, PartnerOfferAdminPage, 'partner_name',
                             page, PartnerOfferAdminPage, 144423, 'partner_name', files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144425
@pytest.mark.xdist_group("po_partner-offer")
def test_144425_an_unsupported_partner_logo_file_type_is_rejected(page):
    """ADO-144425 (P2). Verify that an unsupported Partner Logo file type is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a non-image file as the Partner Logo -> Upload attempt is made with the invalid file
      2. Save -> Upload/save is blocked with 'Unsupported file type or size.' / 'نوع الملف أو حجمه غير مدعوم'
    """
    ck.check_file_refused(page, PartnerOfferAdminPage, 144425, 'partner_logo', BAD_EXE, files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144426
@pytest.mark.xdist_group("po_partner-offer")
def test_144426_an_oversized_partner_logo_file_is_rejected(page):
    """ADO-144426 (P2). Verify that an oversized Partner Logo file is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a 15MB PNG as the Partner Logo -> Upload attempt is made with the oversized file
      2. Save -> Upload/save is blocked with 'Unsupported file type or size.' / 'نوع الملف أو حجمه غير مدعوم'

    Note: Both steps: the upload attempt, then the Save must be blocked (the stored record is checked BY ID). 15 MB PNG generated at run time in the temp dir by tools/fixture_factory.make_png (no committed fixture edited).
    """
    po.check_file_save_refused(page, PartnerOfferAdminPage, 144426, 'partner_logo', big_png_15mb(), files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144427
@pytest.mark.xdist_group("po_partner-offer")
def test_144427_assigning_a_valid_active_partner_category_to_an_offer_saves_and_th(page, browser):
    """ADO-144427 (P2). Verify that assigning a valid active Partner Category to an offer saves and the offer files correctly under it

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Select 'Restaurants' in the Partner Category field -> Selection saves
      2. Save/publish -> Offer publishes
      3. Filter the public listing by 'Restaurants' -> Offer appears under the 'Restaurants' filter

    Note: Links the QCTEST offer to the existing 'Restaurants' category (a link only; the category is not changed).
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144427, 'cat', OFFER_FILES,
                        extra={'partner_category': 'Restaurants'}, category='Restaurants', card_expect=['Restaurants'])


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144428
@pytest.mark.xdist_group("po_partner-offer")
def test_144428_publishing_an_offer_with_no_partner_category_selected_is_blocked(page):
    """ADO-144428 (P2). Verify that publishing an offer with no Partner Category selected is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Partner Category unselected -> Category field remains unselected
      2. Attempt to publish -> Publish is blocked; validation indicates Category is required
    """
    bk.check_required_by_case(ck.check_publish_refused, PartnerOfferAdminPage, 'partner_category',
                             page, PartnerOfferAdminPage, 144428, ('partner_category',), files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144431
@pytest.mark.xdist_group("po_partner-offer")
def test_144431_offer_description_en_ar_saves_and_displays_correctly_within_the_10(page, browser):
    """ADO-144431 (P2). Verify that Offer Description EN/AR saves and displays correctly within the 1000-char limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid 250-character description EN/AR -> Field accepts the text
      2. Save/publish -> Offer saves
      3. Load the public card and modal -> Description renders identically in the card's description panel and the modal

    Note: 250-character value: a render case, not a character-limit case.
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144431, 'desc', OFFER_FILES,
                        extra={'offer_description': DESC_250}, ar_extra={'offer_description': DESC_250_AR},
                        card_expect=[DESC_250], modal_expect=[DESC_250])


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144432
@pytest.mark.xdist_group("po_partner-offer")
def test_144432_publishing_an_offer_with_an_empty_offer_description_is_blocked(page):
    """ADO-144432 (P2). Verify that publishing an offer with an empty Offer Description is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Offer Description EN blank -> Description field remains empty
      2. Attempt to publish -> Publish is blocked; validation indicates Offer Description is required
    """
    bk.check_required_by_case(ck.check_empty_refused, PartnerOfferAdminPage, 'offer_description',
                             page, PartnerOfferAdminPage, 144432, 'offer_description', side='en', files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144606
@pytest.mark.xdist_group("po_partner-offer")
def test_144606_offer_terms_en_ar_saves_and_displays_correctly_in_the_modal_within(page, browser):
    """ADO-144606 (P2). Verify that Offer Terms EN/AR saves and displays correctly in the modal within the 2000-char limit

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid 500-character Offer Terms EN/AR -> Field accepts the text
      2. Save/publish -> Offer saves
      3. Open the public card, then the modal -> Card does NOT show terms text; the modal's 'Offer terms' section shows the full text correctly

    Note: 500-character value: a render case, not a character-limit case.
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144606, 'terms', OFFER_FILES,
                        extra={'offer_terms': TERMS_500}, ar_extra={'offer_terms': TERMS_500_AR},
                        card_absent=[TERMS_500[:60]], modal_expect=[TERMS_500])


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144607
@pytest.mark.xdist_group("po_partner-offer")
def test_144607_publishing_an_offer_with_empty_offer_terms_is_blocked(page):
    """ADO-144607 (P2). Verify that publishing an offer with empty Offer Terms is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Offer Terms EN blank -> Terms field remains empty
      2. Attempt to publish -> Publish is blocked; validation indicates Offer Terms is required
    """
    bk.check_required_by_case(ck.check_empty_refused, PartnerOfferAdminPage, 'offer_terms',
                             page, PartnerOfferAdminPage, 144607, 'offer_terms', side='en', files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144611
@pytest.mark.xdist_group("po_partner-offer")
def test_144611_a_validity_start_date_before_a_later_end_date_saves_successfully(page):
    """ADO-144611 (P2). Verify that a Validity Start Date before a later End Date saves successfully

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Start=2026-10-01 and End=2026-12-31 -> Both dates are entered in their fields
      2. Save/publish -> Save succeeds and the offer's validity window is stored as entered
    """
    po.check_dates_persist(page, PartnerOfferAdminPage, 144611, 'validity_start', 'validity_end',
                           '2026-10-01', '2026-12-31', OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144612
@pytest.mark.xdist_group("po_partner-offer")
def test_144612_an_end_date_before_the_start_date_is_blocked(page):
    """ADO-144612 (P2). Verify that an End Date before the Start Date is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter Start=2026-12-31 and End=2026-10-01 -> Both dates are entered in their fields
      2. Attempt to save -> Save is blocked with 'The end date must be after the start date.' / 'يجب أن يكون تاريخ الانتهاء بعد تاريخ البدء'
    """
    po.check_dates_refused(page, PartnerOfferAdminPage, 144612, 'validity_start', 'validity_end',
                           '2026-12-31', '2026-10-01', OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144613
@pytest.mark.xdist_group("po_partner-offer")
def test_144613_publishing_an_offer_with_empty_validity_dates_is_blocked(page):
    """ADO-144613 (P2). Verify that publishing an offer with empty validity dates is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Validity Start and End Date blank -> Both date fields remain empty
      2. Attempt to publish -> Publish is blocked; validation indicates both validity dates are required
    """
    bk.check_required_by_case(po.check_dates_refused, PartnerOfferAdminPage, 'validity_start',
                             page, PartnerOfferAdminPage, 144613, 'validity_start', 'validity_end', '', '', OFFER_FILES, short='dates-empty')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144615
@pytest.mark.xdist_group("po_partner-offer")
def test_144615_publishing_an_offer_with_no_membership_tier_selected_is_blocked(page):
    """ADO-144615 (P2). Verify that publishing an offer with no Membership Tier selected is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Membership Tier unselected -> Tier field remains unselected
      2. Attempt to publish -> Publish is blocked; validation indicates Membership Tier is required
    """
    bk.check_required_by_case(ck.check_publish_refused, PartnerOfferAdminPage, 'membership_tier',
                             page, PartnerOfferAdminPage, 144615, ('membership_tier',), files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144616
@pytest.mark.xdist_group("po_partner-offer")
def test_144616_a_valid_pdf_contract_document_uploads_and_opens_correctly_from_bot(page, browser):
    """ADO-144616 (P2). Verify that a valid PDF Contract Document uploads and opens correctly from both the card and the modal

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid PDF (2MB) as the Contract Document -> Upload succeeds
      2. Save/publish -> Offer publishes
      3. Click 'Contract' on the public card, then 'Open contract' in the modal -> Both actions open the same PDF in a new browser tab

    Note: Fixture valid_pdf_3mb.pdf (the case's 2MB PDF is not a generated fixture; the PBI sets no size limit for the contract).
    """
    po.check_contract_opens(page, browser, PartnerOfferAdminPage, 144616, {**OFFER_FILES, 'contract_file': VALID_PDF})


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144617
@pytest.mark.xdist_group("po_partner-offer")
def test_144617_a_valid_contract_url_saves_and_opens_correctly_instead_of_an_uploa(page, browser):
    """ADO-144617 (P2). Verify that a valid contract URL saves and opens correctly instead of an uploaded PDF

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter a valid contract URL (e.g. https://qcdev.ihorizons.com/documents/QCTEST-contract.pdf) -> URL field accepts a valid link
      2. Save/publish -> Offer publishes
      3. Click 'Contract' on the public card -> Clicking 'Contract' opens the linked document in a new tab
    """
    po.check_contract_opens(page, browser, PartnerOfferAdminPage, 144617, OFFER_FILES,
                           extra={'contract_url': CONTRACT_URL}, expect_href=CONTRACT_URL, modal=False)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.pbi_130720
@pytest.mark.tc_144618
@pytest.mark.xdist_group("po_partner-offer")
def test_144618_uploading_a_non_pdf_file_as_the_contract_document_is_rejected(page):
    """ADO-144618 (P2). Verify that uploading a non-PDF file as the Contract Document is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Attempt to upload a .docx file as the Contract Document -> Upload attempt is made with the .docx file
      2. Save -> Upload/save is blocked with 'Unsupported file type. Only PDF is accepted.' / 'نوع الملف غير مدعوم. يُقبل ملف PDF فقط'
    """
    ck.check_file_refused(page, PartnerOfferAdminPage, 144618, 'contract_file', VALID_DOCX, files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.edge
@pytest.mark.pbi_130720
@pytest.mark.tc_144627
@pytest.mark.xdist_group("po_partner-category+partner-offer")
def test_144627_attempting_to_deactivate_a_category_that_still_has_published_offer(page, browser):
    """ADO-144627 (P2). Verify that attempting to deactivate a Category that still has Published offers assigned is blocked with a reassignment warning

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Partner Category lookup for 'Medical Centers' (3 published offers assigned) -> Lookup opens showing Active=true and the 3 assigned published offers
      2. Set Active Status = false and attempt to save -> A warning is shown that offers must be reassigned to another category before deactivation; save is blocked and the category remains Active

    Note: Re-expressed on disposable data (one Published QCTEST offer instead of 'Medical Centers' with 3 real offers).
    """
    po.check_category_deactivate_blocked(page, browser, PartnerCategoryAdminPage, PartnerOfferAdminPage, 144627, OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144410
@lb.gate("167087")
@pytest.mark.xdist_group("po_partners-offers-page")
def test_144410_the_hero_and_offers_section_content_fields_save_and_render_correct(page, browser):
    """ADO-144410 (P3). Verify that the hero and Offers-section content fields save and render correctly with valid bilingual EN/AR values

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open the Offers page/hero content editor -> Editor form loads all 7 fields
      2. Enter valid EN and AR text in all 7 content fields and save -> Save succeeds with a success toast
      3. Load the public page in both languages -> Each field renders the correct language's text on the corresponding locale


    Live (B11, user-approved 2026-10-04 for record 167087): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    lc.po_144410(page, browser, PartnersOffersPageAdminPage)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144412
@lb.gate("167087")
@pytest.mark.xdist_group("po_partners-offers-page")
def test_144412_a_valid_hero_illustration_image_uploads_and_displays_on_the_public(page, browser):
    """ADO-144412 (P3). Verify that a valid Hero Illustration image uploads and displays on the public hero

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid hero illustration image and save -> Upload succeeds; save toast shown
      2. Load the public Offers page -> Illustration displays correctly in the hero background area


    Live (B11, user-approved 2026-10-04 for record 167087): acts on the live record itself, run only by
    reports/live-restore/b11_cycle.py (snapshot -> this test alone -n 0 -> restore + verify). Account: QC Site
    Content Editor via cms_role_credentials('Site Content Editor'); public reads in a fresh logged-out context.
    """
    lc.po_144412(page, browser, PartnersOffersPageAdminPage, VALID_PNG)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144413
@pytest.mark.xdist_group("po_partners-offers-page")
def test_144413_publishing_the_hero_with_no_illustration_selected_is_blocked(page):
    """ADO-144413 (P3). Verify that publishing the hero with no illustration selected is blocked

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Hero Illustration empty -> Hero Illustration field remains empty
      2. Attempt to publish -> Publish is blocked; validation indicates Hero Illustration is required

    Note: Refusal on the page singleton, run with Active Status unticked.
    """
    bk.check_required_by_case(ck.check_empty_refused, PartnersOffersPageAdminPage, 'hero_illustration',
                             page, PartnersOffersPageAdminPage, 144413, 'hero_illustration', side='en', files=PAGE_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144414
@pytest.mark.xdist_group("po_partner-category")
def test_144414_a_partner_category_saves_successfully_with_valid_en_ar_names(page):
    """ADO-144414 (P3). Verify that a Partner Category saves successfully with valid EN/AR names

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Partner Category lookup management, add a new entry -> Add form loads
      2. Enter valid EN and AR names and save -> Category saves; appears in the lookup list with both names correct

    Note: Drafts are turned off for this record type (live tooltip), so 'save' = Submit, with Active Status unticked so nothing reaches the public dropdown. The EN value is carried inside the run-unique QCTEST title.
    """
    po.check_lookup_saves(page, PartnerCategoryAdminPage, 144414, 'Shops', 'متاجر')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144418
@pytest.mark.xdist_group("po_membership-tier")
def test_144418_a_membership_tier_saves_successfully_with_valid_en_ar_names(page):
    """ADO-144418 (P3). Verify that a Membership Tier saves successfully with valid EN/AR names

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Open Membership Tier lookup management, add a new entry -> Add form loads
      2. Enter valid EN and AR names and save -> Tier saves; appears in the lookup list with both names correct

    Note: Drafts are turned off for this record type (live tooltip), so 'save' = Submit, Active Status unticked.
    """
    po.check_lookup_saves(page, MembershipTierAdminPage, 144418, 'Platinum', 'بلاتيني')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144422
@pytest.mark.xdist_group("po_partner-offer")
def test_144422_partner_name_en_ar_saves_and_displays_correctly_on_the_card(page, browser):
    """ADO-144422 (P3). Verify that Partner Name EN/AR saves and displays correctly on the card

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter valid EN/AR partner name on a new offer -> Fields accept the values
      2. Save/publish -> Offer saves
      3. Load the public listing in both languages -> Card shows 'QCTEST-Al Waha Spa' on EN, 'QCTEST-واحة سبا' on AR

    Note: EN name = the run-unique QCTEST title (case: 'QCTEST-Al Waha Spa'); AR name 'QCTEST-واحة سبا' + run token, read on the Arabic listing.
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144422, 'name', OFFER_FILES,
                        ar_extra={'partner_name': AR_NAME_144422}, ar_expect=[AR_NAME_144422])


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144424
@pytest.mark.xdist_group("po_partner-offer")
def test_144424_a_valid_png_jpg_partner_logo_uploads_successfully(page, browser):
    """ADO-144424 (P3). Verify that a valid PNG/JPG Partner Logo uploads successfully

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Upload a valid PNG logo (300x300px, 120KB) to the Partner Logo field -> Upload completes without error
      2. Save -> Save succeeds and the logo renders in the tile on the public card

    Note: Fixture valid_icon_200kb.png (the case's 300x300 / 120KB PNG is not a generated fixture; any valid PNG under the limit exercises the same path).
    """
    po.check_logo_on_card(page, browser, PartnerOfferAdminPage, 144424, {**OFFER_FILES, 'partner_logo': VALID_PNG})


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144429
@pytest.mark.xdist_group("po_partner-offer")
def test_144429_partner_location_en_ar_saves_and_displays_correctly_on_the_card(page, browser):
    """ADO-144429 (P3). Verify that Partner Location EN/AR saves and displays correctly on the card

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter valid EN/AR location text -> Field accepts the values
      2. Save/publish -> Offer saves
      3. Load the public card -> Card shows the location text with the marker icon in the active language
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144429, 'loc', OFFER_FILES,
                        extra={'partner_location': 'Doha QCTEST-144429'}, ar_extra={'partner_location': 'الدوحة QCTEST-144429'},
                        card_expect=['Doha QCTEST-144429'], ar_expect=['الدوحة QCTEST-144429'])


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144430
@pytest.mark.xdist_group("po_partner-offer")
def test_144430_an_offer_publishes_successfully_when_partner_location_is_left_empt(page, browser):
    """ADO-144430 (P3). Verify that an offer publishes successfully when Partner Location is left empty (optional field)

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Leave Partner Location EN/AR blank on an otherwise-complete offer -> Location fields remain blank
      2. Publish -> Publish succeeds; the offer card renders without a location line rather than an error or empty placeholder
    """
    po.check_card_without_location(page, browser, PartnerOfferAdminPage, 144430, OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144433
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
@pytest.mark.xdist_group("po_partner-offer")
def test_144433_an_offer_description_of_exactly_1000_characters_is_accepted(page):
    """ADO-144433 (P3). Verify that an Offer Description of exactly 1000 characters is accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter exactly 1000 characters in Offer Description EN -> Full 1000-character value is entered in the field
      2. Save -> Save succeeds; the full text is stored and renders without truncation on the card panel/modal

    Disposition: skip - N/A: no character limit on this project (user decision 2026-10-03)
    """
    pass


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144604
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
@pytest.mark.xdist_group("po_partner-offer")
def test_144604_an_offer_description_exceeding_1000_characters_is_rejected(page):
    """ADO-144604 (P3). Verify that an Offer Description exceeding 1000 characters is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 1001 characters in Offer Description EN -> 1001-character value is entered in the field
      2. Attempt to save -> Save is blocked with a max-length validation error; the value is not stored

    Disposition: skip - N/A: no character limit on this project (user decision 2026-10-03)
    """
    pass


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144605
@pytest.mark.xdist_group("po_partner-offer")
def test_144605_a_whitespace_only_offer_description_is_rejected_as_effectively_emp(page):
    """ADO-144605 (P3). Verify that a whitespace-only Offer Description is rejected as effectively empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter ' ' (spaces only) in Offer Description EN -> Whitespace-only value is entered in the field
      2. Attempt to publish -> Publish is blocked; the field is treated as empty, same as the blank-field validation
    """
    bk.check_required_by_case(ck.check_whitespace_refused, PartnerOfferAdminPage, 'offer_description',
                             page, PartnerOfferAdminPage, 144605, 'offer_description', files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144608
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
@pytest.mark.xdist_group("po_partner-offer")
def test_144608_offer_terms_of_exactly_2000_characters_is_accepted(page):
    """ADO-144608 (P3). Verify that Offer Terms of exactly 2000 characters is accepted

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter exactly 2000 characters in Offer Terms EN -> Full 2000-character value is entered in the field
      2. Save -> Save succeeds; the full text is stored and renders in full in the modal's 'Offer terms' section

    Disposition: skip - N/A: no character limit on this project (user decision 2026-10-03)
    """
    pass


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144609
@pytest.mark.skip(reason="N/A: no character limit on this project (user decision 2026-10-03)")
@pytest.mark.xdist_group("po_partner-offer")
def test_144609_offer_terms_exceeding_2000_characters_is_rejected(page):
    """ADO-144609 (P3). Verify that Offer Terms exceeding 2000 characters is rejected

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter 2001 characters in Offer Terms EN -> 2001-character value is entered in the field
      2. Attempt to save -> Save is blocked with a max-length validation error; the value is not stored

    Disposition: skip - N/A: no character limit on this project (user decision 2026-10-03)
    """
    pass


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144610
@pytest.mark.xdist_group("po_partner-offer")
def test_144610_whitespace_only_offer_terms_is_rejected_as_effectively_empty(page):
    """ADO-144610 (P3). Verify that whitespace-only Offer Terms is rejected as effectively empty

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Enter spaces only in Offer Terms EN -> Whitespace-only value is entered in the field
      2. Attempt to publish -> Publish is blocked; the field is treated as empty
    """
    bk.check_required_by_case(ck.check_whitespace_refused, PartnerOfferAdminPage, 'offer_terms',
                             page, PartnerOfferAdminPage, 144610, 'offer_terms', files=OFFER_FILES)


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144614
@pytest.mark.xdist_group("po_partner-offer")
def test_144614_assigning_a_valid_membership_tier_to_an_offer_saves_and_the_correc(page, browser):
    """ADO-144614 (P3). Verify that assigning a valid Membership Tier to an offer saves and the correct badge renders

    Account: QC Site Content Editor via cms_role_credentials('Site Content Editor').
    Steps (from the approved case):
      1. Select 'Elite' in the Membership Tier field -> Selection saves
      2. Save/publish -> Offer publishes
      3. Load the public card -> Card shows the 'Elite' tier badge
    """
    po.check_offer_card(page, browser, PartnerOfferAdminPage, 144614, 'tier', OFFER_FILES,
                        extra={'membership_tier': 'Elite'}, card_expect=['Elite'])


from cms.tests.partners_offers import ne_checks as ne  # noqa: E402 - 2026-10-07 batch helpers

# ===========================================================================
# 2026-10-07 batch (OFFLINE scripted, not executed): the 4 remaining Automation
# cases, all Priority 4 (Display Order on the two lookups).
# ===========================================================================

@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144416
def test_144416_partner_category_s_display_order_accepts_a_valid_numeric_value_and_reo(page, browser):
    """ADO-144416 (P4). Verify that a Partner Category's Display Order accepts a valid numeric value and reorders the dropdown

    Steps (from the approved case):
      1. Set Display Order = 3 and save -> Save succeeds
      2. Open the public filter dropdown -> Category appears at the corresponding position in the dropdown option order

    Note: Account: Site Content Editor. QCTEST-144416 category (Active ticked) with Display Order 3; its expected dropdown position is derived at run time from the live categories' orders (100-grid). Deleted by ID.
    """
    ne.check_category_order_public(page, browser, 144416, '3')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144417
def test_144417_non_numeric_display_order_value_is_rejected(page):
    """ADO-144417 (P4). Verify that a non-numeric Display Order value is rejected

    Steps (from the approved case):
      1. Enter 'abc' in Display Order -> Value 'abc' is entered in the field
      2. Attempt to save -> Save is blocked; field-level validation error indicates a numeric value is required

    Note: Account: Site Content Editor. Sibling precedent (advertisements 142532): a spinbutton that will not hold the text counts as the refusal; otherwise Submit must be refused.
    """
    ck.check_value_refused(page, PartnerCategoryAdminPage, 144417, 'display_order', 'abc', short='nan')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144420
def test_144420_membership_tier_s_display_order_accepts_a_valid_numeric_value_and_reor(page):
    """ADO-144420 (P4). Verify that a Membership Tier's Display Order accepts a valid numeric value and reorders badges consistently

    Steps (from the approved case):
      1. Set Display Order = 2 and save -> Save succeeds; tier list reorders accordingly in the lookup management screen

    Note: Account: Site Content Editor. QCTEST-144420 tier (Active unticked) with Display Order 2; its row position in the Membership Tier list is compared with the position its order implies. Deleted by ID.
    """
    ne.check_tier_order_admin(page, 144420, '2')


@pytest.mark.control_panel
@pytest.mark.comm
@pytest.mark.functional_low
@pytest.mark.pbi_130720
@pytest.mark.tc_144421
def test_144421_non_numeric_membership_tier_display_order_value_is_rejected(page):
    """ADO-144421 (P4). Verify that a non-numeric Membership Tier Display Order value is rejected

    Steps (from the approved case):
      1. Enter '--' in Display Order -> Value '--' is entered in the field
      2. Attempt to save -> Save is blocked; field-level validation error indicates a numeric value is required

    Note: Account: Site Content Editor. Same refusal oracle as 144417.
    """
    ck.check_value_refused(page, MembershipTierAdminPage, 144421, 'display_order', '--', short='nan')

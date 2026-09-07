"""
cms/tests/home_services/test_home_services_control_panel.py — Control_Panel-
tagged cases for PBI 129371 (QC-HOME-005 — Our Services Section, Home
Page). Cases sourced verbatim from the injected/approved Azure DevOps set
handed off for this batch (Case 1: ADO 135346, Case 2: ADO 135351) — full
step text quoted in each test's own docstring below.

SOURCE / LIVE VERIFICATION (2026-09-02, headed Chromium via Playwright MCP
against qcdev, existing authenticated admin session — no locators guessed):
  - Content & Data > "Service Cards" is confirmed live to be the Object
    Definition backing the Home Page's "Our Services" section
    (objectDefinitionId=47976, externalReferenceCode
    QCDEMO-129371-SERVICE_CARD on every existing row — matches PBI 129371).
  - The public Home Page's "Services We Provide" section
    (`section.qc-home-our-services`) renders a real tab strip
    (`.qc-os-tabs [role="tab"]`, confirmed-live text: "All Services",
    "Membership", "Legal", "E-Services", "Information") and, per tab, a
    server-rendered card list keyed off each Service Card's own "Assigned
    Tab" field.

SURFACE FINDING — CONFIRMED, blocks ADO Test Case 135346 (case-vs-product
mismatch, not an automation gap):

135346's own Step 1 names the fields "Tag/Heading/Description". The live
section header of `section.qc-home-our-services` renders exactly that
trio (`<span class="qc-os-tag" data-qc-os-tag>Our Services</span>`,
`<h2 class="qc-os-heading" data-qc-os-heading>Services We Provide</h2>`,
`<p class="qc-os-desc" data-qc-os-desc>...</p>` — confirmed live this
session) — this is the section header/intro text, NOT a Service Card
(Service Cards has no Tag or Heading field; its fields are
title/shortDescription/redirectUrl/icon/imageThumbnail/assignedTab/
displayOrder/activeStatus — confirmed live and enumerated in
home_services_admin_page.py). The `data-qc-os-*` attributes are plain data
attributes, not Liferay's `data-lfr-editable-id` in-context-editing markers
and not tied to any Object Definition entry — confirmed live via a full,
un-truncated enumeration of every Content & Data menu item on this site
(140+ entries checked this session): no "Our Services Section"/"Service
Section Header" (or equivalent) Object Definition exists. This trio is
therefore Liferay Page Builder **fragment configuration** on the Home page
itself (edited via Design > Site Builder > Pages, not Content & Data) —
confirmed by elimination, not by opening the fragment editor directly (out
of scope for this pass; see below).

This blocks 135346 as literally worded for two independent reasons: (1) no
disposable, namespaced fixture path exists for a Page Builder fragment
config value the way `QCTEST-`-prefixed Object Definition entries exist
elsewhere in this suite — editing it would mean editing the live Home
page's real section header, which cms-testing.md's "never mutate
pre-existing content the suite did not create" rule (and §9's "no authoring
environment the suite may write to freely" escalation trigger) forbids; and
(2) whether that Page Builder surface even exposes a Save-as-Draft/Publish
pair with a "Draft" status (Liferay Pages do carry their own Draft/
Published version state, separate from Object Definition workflow) was
not independently verified this session — opening the Home page in Page
Builder to author-scope this precisely is exploratory work belonging to a
dedicated PBI-129371-scoped fragment investigation, not this batch's
Object-Definition-pattern automation pass. Per automation-standards.md's
Result Integrity section this is scripted as `@pytest.mark.skip` with a
concrete reason below — NOT force-fit onto Service Cards' unrelated
Save/Cancel-only form (which was probed and ruled out, not assumed).
Flagged back to the QA Manager: confirm whether Page Builder fragment
authoring for this section is in scope, and if so, whether a disposable
authoring surface (e.g. a scratch page) can host it for safe automation.

TAB NAMING NOTE (135351): the case names the target tab "Information
Services". The confirmed-live Assigned Tab option / public tab label is
"Information" (no tab literally reads "Information Services" on this
environment). Treated as the case's own shorthand for the live
"Information" tab — see home_services_admin_page.py's TAB NAMING NOTE.

CONCRETE DATA NOTE (135351): the case names a specific real editorial card,
"Halls Reservation" — that card does not exist among the confirmed-live
rows (New Membership, Membership Renewal, Signatory Editing, Signature
Attestation, Certificate of Origin, Document Attestation, Business
Directory, Economic Reports — the full, confirmed-single-page Service
Cards list: 8 rows total, list pagination control shows page "1" only, no
second page, so this is not a pagination artifact), and per
cms-testing.md's never-mutate-pre-existing-content rule this suite may not
create or rename a real editorial card to match. The test instead creates
its own `QCTEST-`-prefixed Service Card, assigns it to the Information tab,
and verifies it appears there on the live Home Page — mirroring the case's
INTENT (assigning a card to a tab makes it appear under that tab) rather
than the literal card name. Disclosed here, not silently substituted.

"Publish" WORDING NOTE (135351): the Service Cards form has no separate
Publish action (see WORKFLOW FINDING above) — Save is the only commit
action and every entry auto-approves. The test's Step 2 exercises Save,
which is this object's full equivalent of the case's "Publish" step.

TEST-DATA POLICY (cms-profile.md): DISPOSABLE. Every test creates its own
`QCTEST-`-prefixed card (via Title) and deletes it via the admin row's own
Actions kebab -> Delete -> confirm in a `finally` block. Never touches any
pre-existing editorial row.

PREVIEW SURFACE FINDING (ADO 135347, live-probed 2026-09-02, headed-equivalent
Chromium via a scripted Playwright probe against qcdev, existing
authenticated admin session, no locators guessed): Case 135347's Step 1
("click Preview on the section") does NOT correspond to any control on the
Service Cards Object Definition surface this module otherwise automates.
Confirmed live by three independent, exhaustive sweeps this session:
  1. Every `role=button` on the Service Cards LIST screen, matched against
     both its visible text AND its `aria-label`/`title` attributes (to catch
     icon-only controls, not just labelled ones) — no "Preview" anywhere
     (only New/Actions/sort/column-visibility/etc., all already documented
     in home_services_admin_page.py).
  2. Every `role=button` on the Add/Edit form — Save/Cancel only (matches
     the WORKFLOW FINDING already on record for this object).
  3. The first list row's own Actions kebab menu (`[role="menuitem"]`,
     confirmed to be the correct control — it renders View / Delete /
     Permissions, the same primitives `delete_row_by_title()` already
     drives) — no "Preview" item.
  A fourth check followed the case's own framing (Preview implies a
  section/page-level render — "Tag, heading, description, tabs, AND
  cards" together, which only a page-level surface could show, not a
  single Service Card): Product Menu > Design > Site Builder > Pages >
  "Home" was opened via the same confirmed-live navigation pattern used
  elsewhere in this file. Its "Home" row link opened the LIVE public Home
  page directly (`/en`), not an editor/preview mode, and no per-row Actions
  kebab was reachable on that Pages list this session to check for a
  separate Edit/Preview entry point. Whether Liferay's Page Builder exposes
  a genuine draft-vs-live Preview render for this page (reachable via a
  different Pages-list control, e.g. an Edit action distinct from the row
  link) was not established this session — that is unexplored, not
  contradicted. Scripted as `@pytest.mark.skip` with this concrete finding,
  not force-fit onto the unrelated Service Cards Save/Cancel form. Flagged
  back to the QA Manager: confirm which CMS surface actually owns "Preview"
  for this section (Page Builder Pages editor vs. the Service Cards object)
  before this case can be retargeted.
"""

import allure
import pytest

from cms.pages.home_services.home_services_admin_page import HomeServicesAdminPage
from core.utils.logger import get_logger
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from web.pages.home_services.home_services_page import HomeServicesPage

logger = get_logger("test_home_services_control_panel")

IMAGE_FIXTURE = "cms/tests/home_services/fixtures/service_card.png"


_SECTION_HEADER_SKIP_REASON = (
    "CONFIRMED case-vs-product mismatch, not an automation gap — live-"
    "verified 2026-09-02: the case's own Tag/Heading/Description fields "
    "match the Home Page 'Our Services' section HEADER "
    "(`section.qc-home-our-services .qc-os-head-text` — Tag/Heading/Desc "
    "spans, confirmed live), not a Service Card (Service Cards has no Tag "
    "or Heading field — confirmed live, see this module's SURFACE FINDING). "
    "That header is Liferay Page Builder fragment configuration on the live "
    "Home page, not an Object Definition entry (confirmed by an exhaustive, "
    "un-truncated Content & Data menu enumeration this session — no "
    "matching object exists). No disposable, namespaced fixture path exists "
    "for a Page Builder fragment config value the way QCTEST-prefixed "
    "Object Definition entries exist elsewhere in this suite; editing it "
    "would mean editing the live Home page's real section header, which "
    "cms-testing.md's never-mutate-pre-existing-content rule forbids. "
    "Whether that Page Builder surface exposes a Save-as-Draft/Publish pair "
    "at all was not verified this session (out of scope for this "
    "Object-Definition-pattern automation pass). See this module's "
    "docstring for the full finding. Flagged back to the QA Manager to "
    "confirm scope and, if in scope, a safe disposable authoring surface."
)


@allure.epic("Home Page")
@allure.feature("Our Services")
@allure.story("Content workflow — draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("BLOCKED — saving the section as Draft keeps it hidden from the live Home Page (Page Builder fragment, no safe disposable authoring surface)")
@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129371
@pytest.mark.tc_135346
@pytest.mark.skip(reason=_SECTION_HEADER_SKIP_REASON)
def test_saving_section_as_draft_keeps_it_hidden_from_live_home_page():
    """ADO-135346. Steps (quoted verbatim):
      1. In CMS, enter valid Tag/Heading/Description -> Fields populated
      2. Click Save as Draft -> Liferay generic success toast shown;
         section status = Draft
      3. Open the live Home Page in a new tab -> Live Home Page does not
         show the drafted changes

    Left deliberately unautomated/skipped — see module docstring's SURFACE
    FINDING and _SECTION_HEADER_SKIP_REASON. The Tag/Heading/Description
    trio is the live Home page's own Page Builder section-header fragment
    config, not a Service Card and not any other Object Definition entry —
    no safe, disposable authoring surface for it was found this session.
    """
    pytest.fail("Not reached — see the skip reason.")


@allure.epic("Home Page")
@allure.feature("Our Services")
@allure.story("CMS authoring workflow — filter-tab assignment")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Assigning a service card to a filter tab makes it appear under that tab")
@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135351
def test_assign_service_card_to_filter_tab_shows_under_tab(page):
    """ADO-135351. Steps (quoted verbatim):
      1. In CMS, assign card "Halls Reservation" to tab "Information
         Services" -> Assignment saved
      2. Publish -> Success toast shown
      3. On live Home Page, click Information Services tab -> Halls
         Reservation card appears under Information Services tab

    Adapted per this module's CONCRETE DATA NOTE and TAB NAMING NOTE: card
    name -> a QCTEST-prefixed fixture card this test creates and owns; tab
    name -> the live "Information" tab. "Publish" -> Save (this object's
    only commit action; see "Publish" WORDING NOTE). Intent preserved:
    assigning a service card to a filter tab makes it appear under that
    tab on the live Home Page.
    """
    admin = HomeServicesAdminPage(page)
    home = HomeServicesPage(page)
    title = "QCTEST-135351 Halls Reservation"

    try:
        with allure.step('Confirm the fixture card is not yet visible under the Information tab'):
            home.open_home().open_tab("Information")
            hidden_before = not home.card_visible(title)
        assert hidden_before, (
            f"Fixture card {title!r} unexpectedly visible under the Information "
            "tab before it was ever created"
        )

        with allure.step('In CMS, create a card and assign it to the "Information" tab'):
            admin.open_new_service_card_form()
            admin.set_title(title)
            admin.set_short_description("QCTEST fixture card for ADO-135351.")
            admin.set_redirect_url("/web/qatar-chamber/services/qctest-135351")
            admin.set_display_order("900")
            admin.set_assigned_tab("Information")
            # Confirmed live 2026-09-02: activeStatus defaults UNCHECKED on a
            # new Service Card. Must be set explicitly — an inactive card
            # would save cleanly but never render on the delivery surface,
            # producing a false red on the live-visibility assertion below
            # that looks like a propagation defect rather than a fixture gap.
            admin.set_active(True)
            admin.upload_icon(IMAGE_FIXTURE)
            assert admin.uploaded_icon_filename() != "", (
                "Icon upload did not populate the field before Save"
            )
            admin.upload_image_thumbnail(IMAGE_FIXTURE)
            assert admin.uploaded_image_thumbnail_filename() != "", (
                "Image Thumbnail upload did not populate the field before Save"
            )

        with allure.step("Save (this object's Publish-equivalent commit action)"):
            admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error creating card {title!r}: {admin.save_error_text()!r}"
        )
        assert admin.wait_for_row_visible(title), (
            f"new card {title!r} not visible in the admin list after Save"
        )

        with allure.step('On the live Home Page, click the Information tab and assert the card appears'):
            visible_after = home.reload_until_card_visible_under_tab(
                "Information", title, expected_visible=True
            )
        assert visible_after, (
            f"Card {title!r} did not appear under the Information tab on the "
            f"live Home Page within {home.RELOAD_POLL_TIMEOUT_MS}ms of "
            "Save (budget borrowed from cms-profile.md's Board Members "
            "measurement, unverified for this content type)"
        )
    finally:
        admin.open_service_cards_list()
        admin.delete_row_by_title(title)


@allure.epic("Home Page")
@allure.feature("Our Services")
@allure.story("CMS authoring workflow — filter-tab reassignment")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Reassigning a service card to a different tab moves it out of the original tab")
@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.functional_high
@pytest.mark.pbi_129371
@pytest.mark.tc_135352
def test_reassign_service_card_to_different_tab_moves_it_out_of_original_tab(page):
    """ADO-135352. Steps (quoted verbatim):
      1. In CMS, reassign card to tab Membership -> Reassignment saved,
         success toast shown
      2. Publish -> Card no longer appears under Information Services
      3. On live Home Page, click Information Services then Membership ->
         Card appears under Membership

    Adapted per this module's TAB NAMING NOTE (the live tab is "Information",
    not "Information Services") and "Publish" WORDING NOTE (Save is this
    object's only commit action). The fixture card is created directly under
    the "Information" tab first (this test owns its own precondition rather
    than depending on ADO-135351's card), then reassigned to "Membership" —
    preserving the case's intent: reassigning a card out of one tab removes
    it from that tab's card list and moves it into the newly assigned tab's
    list on the live Home Page.
    """
    admin = HomeServicesAdminPage(page)
    home = HomeServicesPage(page)
    title = "QCTEST-135352 Reassign Card"

    try:
        with allure.step('In CMS, create a fixture card assigned to the "Information" tab'):
            admin.open_new_service_card_form()
            admin.set_title(title)
            admin.set_short_description("QCTEST fixture card for ADO-135352.")
            admin.set_redirect_url("/web/qatar-chamber/services/qctest-135352")
            admin.set_display_order("900")
            admin.set_assigned_tab("Information")
            # See ADO-135351's own note: activeStatus defaults UNCHECKED on a
            # new Service Card and must be set explicitly.
            admin.set_active(True)
            admin.upload_icon(IMAGE_FIXTURE)
            assert admin.uploaded_icon_filename() != "", (
                "Icon upload did not populate the field before Save"
            )
            admin.upload_image_thumbnail(IMAGE_FIXTURE)
            assert admin.uploaded_image_thumbnail_filename() != "", (
                "Image Thumbnail upload did not populate the field before Save"
            )
            admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error creating card {title!r}: {admin.save_error_text()!r}"
        )
        assert admin.wait_for_row_visible(title), (
            f"new card {title!r} not visible in the admin list after Save"
        )

        with allure.step('Confirm the fixture card appears under the Information tab before reassignment'):
            visible_before = home.reload_until_card_visible_under_tab(
                "Information", title, expected_visible=True
            )
        assert visible_before, (
            f"Fixture card {title!r} did not appear under the Information tab "
            f"before reassignment within {home.RELOAD_POLL_TIMEOUT_MS}ms of Save"
        )

        with allure.step('In CMS, reassign the card to the "Membership" tab'):
            admin.open_service_card_edit_form_by_title(title)
            admin.set_assigned_tab("Membership")
            admin.save()
        assert not admin.is_save_error_shown(), (
            f"unexpected validation error reassigning card {title!r}: {admin.save_error_text()!r}"
        )

        with allure.step('On live Home Page, click Information then Membership and assert the card moved'):
            no_longer_under_information = home.reload_until_card_visible_under_tab(
                "Information", title, expected_visible=False
            )
            assert no_longer_under_information, (
                f"Card {title!r} still appears under the Information tab "
                f"after reassignment within {home.RELOAD_POLL_TIMEOUT_MS}ms "
                "of Save (budget borrowed from cms-profile.md's Board Members "
                "measurement, unverified for this content type)"
            )

            now_under_membership = home.reload_until_card_visible_under_tab(
                "Membership", title, expected_visible=True
            )
            assert now_under_membership, (
                f"Card {title!r} did not appear under the Membership tab "
                f"after reassignment within {home.RELOAD_POLL_TIMEOUT_MS}ms of Save"
            )
    finally:
        admin.open_service_cards_list()
        admin.delete_row_by_title(title)


# _PREVIEW_SKIP_REASON is kept below for history (that raw-admin finding is
# still accurate: the Service Cards OBJECT DEFINITION surface genuinely has
# no Preview control). It no longer gates 135347 — see the dated finding
# right below it.
_PREVIEW_SKIP_REASON = (
    "CONFIRMED live 2026-09-02: no Preview control exists on the Service "
    "Cards Object Definition surface — exhaustively checked via three "
    "sweeps (list-screen role=button incl. aria-label/title for icon-only "
    "controls, Add/Edit form buttons, and the row-level Actions kebab menu "
    "[View/Delete/Permissions only]). The case's own expected result "
    "(Tag/heading/description/tabs/cards rendered together) implies a "
    "section- or page-level render, not a single Service Card entry; "
    "Design > Site Builder > Pages > 'Home' was also probed live this "
    "session and its row link opens the LIVE public Home page directly, "
    "not an editor/preview mode, with no reachable per-row Actions kebab "
    "this session to check for a separate Edit/Preview entry point. "
    "Whether Liferay Page Builder exposes a genuine Preview for this page "
    "via a different control was not established this session (unexplored, "
    "not contradicted) — see this module's PREVIEW SURFACE FINDING. "
    "Flagged back to the QA Manager to confirm which CMS surface owns "
    "'Preview' for this section before retargeting."
)

# UNBLOCKED 2026-09-03: the object-authoring surface (manage-service-card)
# DOES have a Preview — confirmed live this session, both the row-level
# "Preview" link and the list page's own right-hand Preview pane. Its
# target URL is `/web/qatar-chamber/home?qcPreview=servicecards%3A<id>` —
# a real navigation to the LIVE Home page with that Service Card entry
# pinned, NOT a same-card-only render. Confirmed live by opening that exact
# URL and finding `section.qc-home-our-services`'s Tag ("Our Services"),
# Heading ("Services We Provide"), Description paragraph, the full
# `tablist "Service categories"` (All Services/Membership/Legal/
# E-Services/Information), AND the card grid all rendered together on the
# same page, with the PREVIEW status banner ("PREVIEW — showing a
# published servicecards record, exactly as visitors see it.") injected at
# the top. This genuinely satisfies 135347's own expected result
# (Tag/heading/description/tabs/cards rendered together) — the case is
# retargeted onto object-authoring's Preview rather than left blocked.
_PREVIEW_UNBLOCK_FINDING_2026_09_03 = (
    "Superseded by object-authoring's own Preview (manage-service-card) — "
    "see the comment immediately above. Retargeted, not force-fit: the raw "
    "Object Definition surface still has no Preview control (that part of "
    "the original finding stands), but 135347 is not scoped to that raw "
    "surface specifically — it is scoped to whatever CMS surface owns "
    "authoring for this section, and object-authoring is the confirmed, "
    "intended editor workflow per .claude/context/active/standards.md's "
    "Object Authoring lifecycle section."
)


@allure.epic("Home Page")
@allure.feature("Our Services")
@allure.story("CMS authoring workflow — preview before publish")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Preview shows the section (Tag/heading/description/tabs/cards) before publishing")
@pytest.mark.control_panel
@pytest.mark.svc
@pytest.mark.pbi_129371
@pytest.mark.tc_135347
def test_preview_shows_section_before_publishing(page):
    """ADO-135347. Steps (quoted verbatim):
      1. In CMS, click Preview on the section -> A preview render opens
         showing Tag, heading, description, tabs, and cards as configured,
         without affecting the live page.

    UNBLOCKED 2026-09-03 via the object-authoring surface's own Preview —
    see _PREVIEW_UNBLOCK_FINDING_2026_09_03 above. A fixture Service Card
    is created and saved via manage-service-card, then its own row-level
    Preview link is followed and asserted to render the Tag, Heading,
    Description, the tab strip, AND the card grid all together (not just
    the one card) — matching the case's own expected result — plus the
    PREVIEW status banner confirming this is a preview render, not the
    live page.
    """
    admin = HomeServicesAdminPage(page)
    authoring = ObjectAuthoringPage(page, slug="service-card")
    title = "QCTEST-135347 Preview Card"

    try:
        with allure.step("In CMS, create a fixture Service Card and save it"):
            admin.open_service_cards_list()
            authoring.open_new_entry_form()
            authoring.fill_text("Title", title)
            authoring.fill_text("Short Description", "QCTEST fixture card for ADO-135347.")
            authoring.fill_text("Redirect URL", "/web/qatar-chamber/services/qctest-135347")
            authoring.fill_number("Display Order", "901")
            authoring.select_combobox_option("Assigned Tab", "Information")
            authoring.set_checkbox("Active Status", True)
            authoring.upload_file("Icon", IMAGE_FIXTURE)
            assert authoring.uploaded_filename("Icon") != "", (
                "Icon upload did not populate the field before Save"
            )
            authoring.upload_file("Image Thumbnail", IMAGE_FIXTURE)
            assert authoring.uploaded_filename("Image Thumbnail") != "", (
                "Image Thumbnail upload did not populate the field before Save"
            )
            authoring.save_as_draft()

        with allure.step("Click Preview on the fixture card's row"):
            # Same class of bug already root-caused in the Promo Banner
            # object-authoring tests: admin.open_service_cards_list()
            # navigates the RAW admin surface, which has no Preview link
            # at all (View/Delete/Permissions only) — row_preview_url()
            # needs manage-service-card's own entries list instead.
            authoring.open_entries_list()
            preview_url = authoring.row_preview_url(title)
        assert preview_url, f"no Preview link found for fixture card {title!r}"

        with allure.step("Assert the preview render shows Tag, Heading, Description, tabs, and cards together"):
            # Draft-specific banner text (the fixture is saved as Draft,
            # never published) — asserting the exact draft wording, not
            # just "PREVIEW"/"showing" (both appear in the draft AND the
            # published banner, so that alone would not prove this is
            # rendering the UNPUBLISHED state "without affecting the live
            # page", which is the actual point of the case's expected
            # result).
            banner_text = authoring.preview_banner_text(preview_url)
            assert "unpublished (draft)" in banner_text, (
                f"expected the draft-specific PREVIEW banner, got: {banner_text!r}"
            )
            # Scoped to the real Our Services section container (confirmed
            # live in this module's SURFACE FINDING) rather than bare
            # text=/role= locators that also match the main-nav "Our
            # Services" link or unrelated `article` elements elsewhere on
            # the Home page (e.g. Business Events, Publications).
            section = authoring.page.locator("section.qc-home-our-services")
            assert section.locator("[data-qc-os-tag]").is_visible(), "section Tag not rendered in preview"
            assert section.locator("[data-qc-os-heading]").is_visible(), "section Heading not rendered in preview"
            assert section.locator("[data-qc-os-desc]").is_visible(), "section Description not rendered in preview"
            assert section.get_by_role("tablist").is_visible(), "section tab strip not rendered in preview"
            assert section.locator("article").first.is_visible(), "no cards rendered in preview"
    finally:
        # Teardown must land on manage-service-card's own entries list
        # (authoring.open_entries_list()), NOT admin.open_service_cards_list()
        # — the raw admin's list has no `data-qc-oel-delete` rows (confirmed
        # live 2026-09-03, same finding as the other two object-authoring
        # test modules in this batch).
        try:
            authoring.open_entries_list()
            authoring.delete_entry_by_title(title)
        except Exception:
            logger.warning("teardown for %r did not complete — leftover QCTEST data may remain", title)

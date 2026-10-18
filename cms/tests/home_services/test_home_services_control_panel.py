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
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED

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


# ---------------------------------------------------------------------------
# ADO 135348 / 135350 -- added 2026-09-10
#
# THESE TWO ARE NOT News Article cases. They were handed over in a batch
# labelled "News Articles", but their own ADO tags say **SVC** and their
# expected results name "Tag/heading/description/tabs/cards" and "Our
# Services section" -- i.e. this module's subject, PBI 129371. Recorded
# here rather than silently retargeting, so the mismatch is visible.
#
# OBJECT NAMES (cms/Content-Admin-Guide.docx section 8 "Home - Our
# Services"): **ServiceCard** (`manage-service-card`) and **FilterTab**.
# The guide lists NO third object for this section -- so the section's own
# Tag / Heading / Description trio is NOT object-authorable content. It is
# the Page Builder section-header fragment already documented in this
# module's SURFACE FINDING, which is exactly why TC 135346 above is
# skipped. That constraint is what shapes both cases below.
# ---------------------------------------------------------------------------

_TC_135350_SKIP_REASON = (
    "ADO-135350 requires the WHOLE 'Our Services' section to disappear from "
    "the live Home Page ('Our Services section no longer appears'). On this "
    "build there is no object-level way to reach that state: the section is a "
    "Page Builder fragment (see this module's SURFACE FINDING and TC 135346), "
    "and standards.md puts fragments and page layout absolutely off-limits to "
    "automation. The only object-level approximation -- unpublishing or "
    "deactivating EVERY real ServiceCard until the section renders its empty "
    "state -- would take the live Our Services section down for the duration "
    "of a run on a SHARED environment and would mutate real editorial rows, "
    "which standards.md forbids outright. Deliberately NOT force-fit onto "
    "unpublishing a single fixture card: that removes one CARD, not the "
    "SECTION, and asserting it would silently rewrite the case. Referred to "
    "the QA Manager/BA: either the case belongs on a disposable environment "
    "where the fragment can be unpublished, or it should be reworded to the "
    "card-level behaviour that TC 135352 and the Promotional Banner unpublish "
    "cases already cover."
)


"""
cms/pages/home_community_partners/home_community_partners_admin_page.py —
CommunityPartnersAdminPage.

MIGRATED 2026-09-07 (PBI 129385, Object Authoring broadening) — per
.claude/context/active/standards.md's "Object Authoring Is the Only Path for
Content Operations — Not Content & Data" section (superseded/broadened
2026-09-07: Content & Data is now retired for EVERY operation on an
Object-Definition-backed record, not just lifecycle actions). Community
Partner IS Object-Definition-backed (objectDefinitionId=45665, real
Draft/Approved workflow states) and this session confirmed LIVE that the
Object Authoring surface for it is reachable — contrary to the 2026-08-31/
2026-09-03 sessions' finding, which is now known to have probed the WRONG
slug.

SLUG CORRECTION (confirmed live this session): the 2026-09-03 session
probed `manage-community-partners` (plural) and got a real "Coming Soon"
404 — but the actual registered slug on `/object-authoring`'s own object
list is `manage-community-partner` (SINGULAR). Confirmed live:
`https://qcdev.ihorizons.com/web/qatar-chamber/manage-community-partner`
renders the real "Manage: Community Partner" Object Authoring surface, with
a genuine Save as Draft / Submit for Publishing lifecycle (buttons
confirmed live via `document.querySelectorAll`) — the 2026-08-31 finding
("no separate Preview/Draft/Publish lifecycle exists on this form") was
true only for the Content & Data raw editor, which this class no longer
uses at all.

This class now composes `ObjectAuthoringPage` (slug "community-partner")
for the generic Draft/Preview/Publish/Unpublish state machine and adds only
this object's own field labels — no locators are duplicated from that
shared class.

CONFIRMED LIVE THIS SESSION (field-level, via the real Object Authoring
form, `get_by_role` accessible-name lookups, not inherited from the retired
Content & Data page):
  - Six fields, none bilingual-paired-under-one-label (each tooltip reads
    "<Field> field cannot be localized." — confirmed via
    `[role="tooltip"][aria-label$="cannot be localized."]`): "Partner Name
    (EN)" (textbox), "Partner Name (AR)" (textbox), "Partner URL" (textbox),
    "Display Order" (spinbutton), "Active" (checkbox), "Partner Logo
    (Color, hover state)" (file upload via the shared
    ObjectAuthoringPage.upload_file() flow).
  - Entries table row list confirmed live: QatarEnergy (id 45744),
    Qatar Airways (id 45776), QNB (id 45808) — all Status APPROVED — plus
    one pre-existing leftover Draft row from a 2026-09-03 session
    ("partner test name 1", id 180959, never published, no public-visibility
    risk) that this session found but could not clean up (a
    `browser_handle_dialog` permission denial blocked the delete
    confirmation mid-click) — flagged here as a known, disposable, harmless
    leftover for a future session to remove, not a shared/real record.
  - **ID-45776-NAMING QUESTION RESOLVED LIVE THIS SESSION**: the entries
    table's own row-to-id mapping was read directly off each row's
    `data-qc-oel-delete` attribute (never inferred): id 45776's title is
    exactly "Qatar Airways". NO record named/coded "Qatar Development Bank"
    exists anywhere in this object's entries list (4 total rows enumerated:
    QatarEnergy/Qatar Airways/QNB/the leftover Draft). TC 135832's own case
    text naming "Qatar Development Bank" is therefore a STALE/WRONG case
    reference, not a hint that a same-ID rename occurred — standards.md's
    Safe-Parallelism table (`xdist_group("qatar_airways_45776")` tied to
    "Qatar Airways partner, ID 45776") is the CORRECT mapping and is used
    as-is below; TC 135832 is scripted against the real Qatar Airways
    record, per this project's established disclosed-substitution
    precedent for a case-vs-product/case-vs-reality mismatch.
  - **Required-field validation differs genuinely from the retired Content
    & Data surface — re-verified live, not carried over** (per
    standards.md's own warning that the path change "may change previously
    observed behavior"): on THIS surface, "Save as Draft" does **not**
    enforce Partner Name (EN) as required — live-verified by creating a
    real draft with it empty (Save as Draft succeeded, a new Draft row
    appeared keyed by its own UUID entry code since no title existed) and
    immediately deleting that probe entry afterward, confirmed via a fresh
    reopen of the list. "Submit for Publishing" WITH Partner Name (EN)
    empty was independently tried twice (once with `.click()`, once
    force-equivalent via a direct CSS locator to rule out an overlay
    swallowing the click) — in both cases NO entry was created (confirmed
    via a before/after diff of the entries list, and confirmed via the
    Network tab that neither attempt fired a POST/create request at all —
    this is a real client-side block, not a silently-dropped click) — but
    **no visible error text/alert renders anywhere on the page** (no
    `[role="alert"]` content, no banner). This is a genuine case-vs-product
    discrepancy from TC 135830's literal "Error message ... displayed"
    expectation: the BLOCKING behavior is real and confirmed (no entry is
    ever created, matching the case's core intent — no unpublished record
    leaks to the frontend), but there is no message text to assert against.
    TC 135830 below asserts the confirmed-real outcome (Submit for
    Publishing produces no new/newly-visible entry) and documents the
    missing-error-text gap rather than asserting unverified literal text.
  - **Editing an already-Approved entry requires Unpublish first** —
    confirmed live opening Qatar Airways' edit form: banner reads exactly
    'Editing "Qatar Airways" (approved). It is published, so Save as Draft
    is unavailable until you unpublish it.' with only "Unpublish to edit as
    draft" (and "Cancel and add a new entry instead") available — no direct
    field-edit-then-resave path exists for an Approved entry on this
    surface, unlike the retired Content & Data editor (which allowed direct
    Save on an Approved row). TC 135832's deactivate/restore cycle therefore
    goes: open the Approved entry -> Unpublish to edit as draft -> edit
    Active -> Submit for Publishing (republishes as Approved with the new
    Active value) -> restore is the same cycle run again with Active
    reverted. The public carousel's own query
    (`/o/c/communitypartners/scopes/<groupId>?filter=activeStatus eq true`,
    confirmed live via Network capture) filters purely on `activeStatus`,
    independent of the CMS workflow Status column — so an Approved entry
    with Active=False is correctly excluded from the carousel while
    remaining "Approved" in the admin list, which is exactly the case's own
    precondition/expected-result shape.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage

SLUG = "community-partner"

PARTNER_NAME_EN_LABEL = "Partner Name (EN)"
PARTNER_NAME_AR_LABEL = "Partner Name (AR)"
PARTNER_URL_LABEL = "Partner URL"
DISPLAY_ORDER_LABEL = "Display Order"
ACTIVE_LABEL = "Active"
LOGO_LABEL = "Partner Logo (Color, hover state)"

# Confirmed live this session — the 3 real, shared records (see module
# docstring's ID-45776 resolution). Names only, matching the Entry column's
# own rendered title text (title-based lookup IS correct for this object —
# unlike manage-strategic-pillar-card's confirmed externalReferenceCode
# exception documented in ObjectAuthoringPage's own module docstring).
QATAR_ENERGY_NAME = "QatarEnergy"
QATAR_AIRWAYS_NAME = "Qatar Airways"
QNB_NAME = "QNB"


class CommunityPartnersAdminPage(ObjectAuthoringPage):
    """Community Partner's own field-level actions, composed on top of the
    generic Object Authoring Draft/Preview/Publish/Unpublish state machine.
    Every navigation/lifecycle/list method (open_new_entry_form,
    open_entries_list, open_entry_by_edit_link, save_as_draft,
    submit_for_publishing, unpublish_to_edit_as_draft, row_status_text,
    row_visible, delete_entry_by_title, row_preview_url, preview_banner_text,
    current_status, ...) is inherited AS-IS from ObjectAuthoringPage — do not
    re-declare them here."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Field actions — this object's own labels only --------------------
    def set_partner_name_en(self, value: str) -> "CommunityPartnersAdminPage":
        self.fill_text(PARTNER_NAME_EN_LABEL, value)
        return self

    def set_partner_name_ar(self, value: str) -> "CommunityPartnersAdminPage":
        self.fill_text(PARTNER_NAME_AR_LABEL, value)
        return self

    def set_partner_url(self, value: str) -> "CommunityPartnersAdminPage":
        self.fill_text(PARTNER_URL_LABEL, value)
        return self

    def set_display_order(self, value: str) -> "CommunityPartnersAdminPage":
        self.fill_number(DISPLAY_ORDER_LABEL, value)
        return self

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=DISPLAY_ORDER_LABEL, exact=True).input_value()

    def set_active(self, active: bool) -> "CommunityPartnersAdminPage":
        self.set_checkbox(ACTIVE_LABEL, active)
        return self

    def is_active(self) -> bool:
        return self.page.get_by_role("checkbox", name=ACTIVE_LABEL, exact=True).is_checked()

    def upload_partner_logo(self, file_path: str) -> "CommunityPartnersAdminPage":
        self.upload_file(LOGO_LABEL, file_path)
        return self

    def uploaded_logo_filename(self) -> str:
        return self.uploaded_filename(LOGO_LABEL)

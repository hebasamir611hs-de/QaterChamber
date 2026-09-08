"""
cms/pages/home_hero_banner/home_hero_banner_admin_page.py —
HomeHeroBannerAdminPage.

Control_Panel Page Object for PBI 129367 (QC-HOME-001 — Hero Banner, Home
Page section), backing the Object Authoring surface's `manage-hero-banner-
slide` entry list/create/edit form. Per
.claude/context/active/standards.md's "Object Authoring Is the Only Path for
Content Operations" rule, this class composes `ObjectAuthoringPage`
(cms/pages/components/object_authoring_page.py) for ALL navigation/lifecycle
behaviour — the same thin-holder pattern already established by
`ChambersLawAdminPage`/`ChairmanMessageAdminPage`/`GmMessageAdminPage`: this
class holds only the object's slug + its field-label constants, never
duplicates the generic Draft/Preview/Publish/Unpublish state machine.

CONFIRMED LIVE 2026-09-08 (headless Chromium against qcdev, authenticated via
a freshly re-captured `.auth/state.json` / `tools/save_auth.py`; locators
harvested CLI-first via `tools/extract_locators.py` against the live
`/web/qatar-chamber/object-authoring` listing and the
`manage-hero-banner-slide` add form, with a small scoped Playwright script —
still CLI, never the Playwright MCP — filling the gap the static harvester
has for accessible-name resolution and `required` attribute reads, same
disclosed pattern `ChairmanMessageAdminPage`/`ChambersLawAdminPage` used):

  - **Object identity**: the `/object-authoring` listing (filtered live for
    "hero") shows a "Hero Banner Slide" entry whose own link resolves to
    `/web/qatar-chamber/manage-hero-banner-slide` — confirmed slug
    `hero-banner-slide`. (`"About Hero Banner"` is a DIFFERENT, unrelated
    object also present in that listing — not this one.)
  - **Freely-creatable list, NOT a singleton** — confirmed live:
    `manage-hero-banner-slide`'s own entries table showed 6 existing rows
    (2 real `QCDEMO-129367-HERO_BANNER_SLIDE-0x` entries plus 4
    auto-generated-externalReferenceCode rows, one already sitting in
    DRAFT status from an earlier, unrelated session) at discovery time —
    multiple entries coexist, so `open_new_entry_form()` genuinely creates
    an ADDITIONAL slide, never edits/overwrites an existing one. This was
    verified live BEFORE any write, per this task's explicit precondition
    check.
  - **Mandatory fields — confirmed live via a DOM `required` attribute
    read** (not guessed from visible asterisks; this project's Object
    Authoring forms render no visible "*" marker at all — NOTE 2026-09-08:
    `.claude/context/active/OBJECT-AUTHORING-GUIDE.md` §3 says required
    fields ARE marked with `*`. That is not a contradiction of this
    finding: the asterisks documented in
    `cms/pages/org_structure/org_structure_admin_page.py` belong to the
    **native Control-Panel "New" form**, a different surface from the
    Object Authoring form this class drives. Before "correcting" either
    docstring, confirm WHICH surface is in front of you. The DOM
    `required` read below is the surface-independent check and stays the
    preferred mechanism either way): Banner Image
    (file upload), Banner Title (EN), Banner Title (AR), Button 1 Label
    (EN), Button 1 Label (AR), Button 1 Link, Button 2 Label (EN), Button 2
    Label (AR), Button 2 Link, Display Order. Banner Subtitle (Description)
    (EN)/(AR) (rich textareas) and the two checkboxes (Active Status,
    Counters Active Status) confirmed live NOT required.
  - **Field accessible names** — every text/number field resolves uniquely
    via `page.get_by_role(<role>, name=<label>, exact=True)` with no
    locale-toggle click needed (same confirmed-live shape as
    ObjectAuthoringPage.fill_text()/fill_number() already document for
    sibling objects): "Banner Title (EN)", "Banner Title (AR)", "Banner
    Subtitle (Description) (EN)", "Banner Subtitle (Description) (AR)",
    "Button 1 Label (EN)", "Button 1 Label (AR)", "Button 1 Link", "Button
    2 Label (EN)", "Button 2 Label (AR)", "Button 2 Link", "Display Order"
    (spinbutton), "Active Status" (checkbox), "Counters Active Status"
    (checkbox). The single image field's accessible name is plain "Banner
    Image" (NOT "Banner Image (EN)"/"(AR)" — confirmed live only ONE image
    field exists on this object, unlike Promotional Banner's separate
    EN/AR images) — its own hidden filename textbox
    ("Banner Image Select File") and sibling "Select File" button are
    confirmed live present, so `ObjectAuthoringPage.upload_file("Banner
    Image", <path>)` / `.uploaded_filename("Banner Image")` apply directly,
    no new upload mechanism needed.
  - This surface exposes only "Save as Draft" / "Submit for Publishing" —
    confirmed live, no separate generic "Save" button (same shape every
    other object-authoring form on this project already documents). ADO-135009's
    own Step 3 wording ("Click Save") does not distinguish Draft vs
    Publish — disclosed adaptation: the calling test uses "Submit for
    Publishing" (not "Save as Draft") since the case's own intent is
    creating a real, usable Hero Banner slide, not exercising the separate
    Draft-state case family this project already covers elsewhere (see
    home_promo_banners' TC 135122/135123 precedent for that distinct
    workflow-status axis).
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

# ---- Object Authoring identity — confirmed live 2026-09-08 (see module
# docstring) -----------------------------------------------------------
HERO_BANNER_SLIDE_SLUG = "hero-banner-slide"


class HomeHeroBannerAdminPage(BasePage):
    """Thin holder of this object's identity + field-label constants. All
    navigation/state/lifecycle behaviour is delegated to
    `ObjectAuthoringPage` — this class does not duplicate that state
    machine (see module docstring)."""

    # ---- Field labels — confirmed live (see module docstring) --------------
    BANNER_IMAGE_LABEL = "Banner Image"
    BANNER_TITLE_EN_LABEL = "Banner Title (EN)"
    BANNER_TITLE_AR_LABEL = "Banner Title (AR)"
    BANNER_SUBTITLE_EN_LABEL = "Banner Subtitle (Description) (EN)"
    BANNER_SUBTITLE_AR_LABEL = "Banner Subtitle (Description) (AR)"
    BUTTON1_LABEL_EN_LABEL = "Button 1 Label (EN)"
    BUTTON1_LABEL_AR_LABEL = "Button 1 Label (AR)"
    BUTTON1_LINK_LABEL = "Button 1 Link"
    BUTTON2_LABEL_EN_LABEL = "Button 2 Label (EN)"
    BUTTON2_LABEL_AR_LABEL = "Button 2 Label (AR)"
    BUTTON2_LINK_LABEL = "Button 2 Link"
    DISPLAY_ORDER_LABEL = "Display Order"
    ACTIVE_STATUS_LABEL = "Active Status"
    COUNTERS_ACTIVE_STATUS_LABEL = "Counters Active Status"

    def __init__(self, page):
        super().__init__(page)

    # ---- Navigation ---------------------------------------------------------
    def open_new_slide_form(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLIDE_SLUG)
        authoring.open_new_entry_form()
        return authoring

    def open_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLIDE_SLUG)
        authoring.open_entries_list()
        return authoring

    def open_slide_by_code(self, entry_code: str) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLIDE_SLUG)
        authoring.open_entry_by_code(entry_code)
        return authoring

    def open_slide_by_title(self, title: str) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLIDE_SLUG)
        authoring.open_entry_by_edit_link(title)
        return authoring

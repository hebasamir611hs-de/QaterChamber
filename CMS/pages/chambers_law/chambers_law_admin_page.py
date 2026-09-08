"""
cms/pages/chambers_law/chambers_law_admin_page.py — ChambersLawAdminPage.

PBI 129394 (QC-ABOUT-003 — Chamber's Law), Control_Panel-tagged cases 134871,
134873, 134874, 134875, 134877, 134882, 134883, 134884, 134885, 134886,
134887, 134888. Composes `ObjectAuthoringPage`
(cms/pages/components/object_authoring_page.py) for navigation/lifecycle —
this class holds only field-label constants + this feature's two known
object identities, mirroring `ChairmanMessageAdminPage`'s established
convention (see that file's own docstring for the identical pattern on a
sibling object).

CONFIRMED LIVE 2026-09-07 (headless Chromium against qcdev, authenticated
via `.auth/state.json`; a disclosed, scoped Playwright script — still CLI,
never the Playwright MCP — since `tools/extract_locators.py`'s static
harvester does not resolve accessible names the way `get_by_role(...,
name=...)` does, same disclosed pattern `ChairmanMessageAdminPage` used):

**TWO separate Object Authoring objects back this feature** (confirmed via
the `/object-authoring` listing filtered for "law" — never guessed):

  - **Chamber Laws Page** (the page-level singleton record) — slug
    `chamber-laws-page` (`manage-chamber-laws-page`), singleton entry code
    `QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY` (status APPROVED at discovery).
    Fields confirmed live, in on-screen order: Page Title, Intro Heading,
    Intro Content (rich text, 2 CKEditor instances EN/AR — DOM id
    `ObjectField_introContent`, confirmed live via the same ancestor-walk
    `ChairmanMessageAdminPage.MESSAGE_CONTENT_FIELD_NAME` documents),
    Content Image (upload), Content Image Alt Text, References Heading,
    Status (redundant combobox, not used — same as every other object on
    this surface).
  - **Law Entry** (the repeating law-record list, NOT nested under the page
    record — its own top-level object) — slug `law-entry`
    (`manage-law-entry`). Fields confirmed live, in on-screen order: Law
    Number, Law Title, Law Description (plain textbox, NOT rich text — a
    real, confirmed-live difference from what a "Description" field is on
    other objects), External Link URL (NOT bilingual — confirmed live, no
    "— العربية" counterpart, same pattern as Chairman's Message's Hyperlink
    URL), Law Icon (upload), Display Order (spinbutton), Active Status
    (checkbox). 4 real entries exist live at discovery:
      - `QCDEMO-129394-law-11-1990` — Law Number "Law No. 11 of 1990", Law
        Title "Establishment of the Qatar Chamber of Commerce and
        Industry", Display Order 100, Active True, External Link URL
        `https://www.almeezan.qa/` — this is the public page's FIRST card.
      - `QCDEMO-129394-law-11-1996` — Law Number "Law No. 11 of 1996", Law
        Title "Amending Certain Provisions of Law No. 11 of 1990", Display
        Order 200, Active True, External Link URL `https://www.almeezan.qa/`
        — the public page's SECOND card. **This entry already exists as
        real, pre-existing content** — it is NOT created by this batch's
        134884 (see that test's own docstring for why the case's literal
        "create Law No. 11 of 1996" precondition no longer holds and how
        this is handled without colliding with this real record).
      - a stray non-publishing-relevant `test samy` entry (Active **False**
        — confirmed live via its own edit form, which is why it never
        renders publicly) and a stray `44444`/Law Number "455" entry
        (Active True, Display Order 300 — the public page's THIRD/last
        card, `https://www.google.com` destination) — both pre-existing,
        NOT created or touched by this batch; left alone throughout.

  - **File-upload restore path — CONFIRMED BETTER than Chairman's Message's
    same-shaped fields**: both Content Image and Law Icon on THIS surface
    render a real `Current file: <name> (<size>) Preview · Download ...
    Remove file` block once a file is set (confirmed live via a full-page
    screenshot + DOM probe) — a genuine Download link, unlike the Chairman
    Portrait/Hero Banner fields' Select-File/Remove-file-only variant that
    left TC 134783/134784 as disclosed skips last batch. See
    `ObjectAuthoringPage.current_file_download_url()` /
    `.download_current_file()` / `.remove_current_file()` — the generic
    mechanism this finding was added to, since it is confirmed live across
    BOTH objects in this feature (Content Image AND Law Icon), not
    idiosyncratic to one field.
  - **Content Image was confirmed LIVE, ALREADY SET** on the singleton
    record (`chamber-laws-content.png`, 173 KB) — the OPPOSITE precondition
    134882 ("a record with no Content Image set") literally asks for. See
    that test's own docstring for how the Download-based restore path
    changes the outcome here versus Chairman's Message's disclosed-skip
    134784 (no Download there at all).
  - **Preview** — same row-level `Preview` link mechanism `ObjectAuthoringPage`
    already documents generically; confirmed live present on both objects'
    entries tables.

Every CMS-mutating test in the sibling test module is TEST_OWNED (this
project's Test-Data Policy): it reads the record's/entry's current value
immediately before mutating and restores that SAME captured value in a
`finally` block, never a hardcoded assumed "original" — this class exposes
no state of its own; every baseline capture happens in the test.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

# ---- Object Authoring identities — confirmed live 2026-09-07 (see module
# docstring) -----------------------------------------------------------
CHAMBERS_LAW_PAGE_SLUG = "chamber-laws-page"
CHAMBERS_LAW_PAGE_ENTRY_CODE = "QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY"
LAW_ENTRY_SLUG = "law-entry"
LAW_1990_ENTRY_CODE = "QCDEMO-129394-law-11-1990"
LAW_1996_ENTRY_CODE = "QCDEMO-129394-law-11-1996"
# The Law Entry object's own Entry column renders the entry's real Law
# Title text (confirmed live — unlike e.g. manage-strategic-pillar-card,
# whose Entry column renders an externalReferenceCode instead, per
# ObjectAuthoringPage's own class-level note), so row_visible()/
# row_status_text() (title-keyed) are the correct lookup here, not the
# `_by_code` variants (code-keyed, for objects whose Entry column doesn't
# show the title).
LAW_1990_TITLE = "Establishment of the Qatar Chamber of Commerce and Industry"
LAW_1996_TITLE = "Amending Certain Provisions of Law No. 11 of 1990"


class ChambersLawAdminPage(BasePage):
    """Thin holder of this feature's TWO object identities + field-label
    constants. All navigation/state/lifecycle behaviour is delegated to
    `ObjectAuthoringPage` — this class does not duplicate that state
    machine (see module docstring)."""

    # ---- Chamber Laws Page (singleton) field labels — confirmed live -----
    PAGE_TITLE_LABEL = "Page Title"
    INTRO_HEADING_LABEL = "Intro Heading"
    REFERENCES_HEADING_LABEL = "References Heading"
    CONTENT_IMAGE_UPLOAD_LABEL = "Content Image"
    CONTENT_IMAGE_ALT_TEXT_LABEL = "Content Image Alt Text"
    INTRO_CONTENT_FIELD_NAME = "introContent"  # rich-text DOM-id-safe field name
    ARABIC_SUFFIX = " — العربية"

    # ---- Law Entry field labels — confirmed live --------------------------
    LAW_NUMBER_LABEL = "Law Number"
    LAW_TITLE_LABEL = "Law Title"
    LAW_DESCRIPTION_LABEL = "Law Description"
    EXTERNAL_LINK_URL_LABEL = "External Link URL"  # not bilingual — confirmed live
    LAW_ICON_UPLOAD_LABEL = "Law Icon"
    DISPLAY_ORDER_LABEL = "Display Order"
    ACTIVE_STATUS_LABEL = "Active Status"

    def __init__(self, page):
        super().__init__(page)

    # ---- Chamber Laws Page (singleton) navigation --------------------------
    def open_page_record(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=CHAMBERS_LAW_PAGE_SLUG)
        authoring.open_entry_by_code(CHAMBERS_LAW_PAGE_ENTRY_CODE)
        return authoring

    def open_page_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=CHAMBERS_LAW_PAGE_SLUG)
        authoring.open_entries_list()
        return authoring

    # ---- Law Entry navigation ----------------------------------------------
    def open_law_entry(self, entry_code: str) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=LAW_ENTRY_SLUG)
        authoring.open_entry_by_code(entry_code)
        return authoring

    def open_law_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=LAW_ENTRY_SLUG)
        authoring.open_entries_list()
        return authoring

    def open_new_law_entry_form(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=LAW_ENTRY_SLUG)
        authoring.open_new_entry_form()
        return authoring

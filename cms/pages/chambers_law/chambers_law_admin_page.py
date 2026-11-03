"""
cms/pages/chambers_law/chambers_law_admin_page.py — ChambersLawAdminPage.

PBI 129394 (QC-ABOUT-003 — Chamber's Law), Control_Panel-tagged cases 134871,
134873, 134874, 134875, 134877, 134882, 134883, 134884, 134885, 134886,
134887, 134888. Composes `ObjectAuthoringPage`
(cms/pages/components/object_authoring_page.py) for navigation/lifecycle —
this class holds only field-label constants + this feature's object
identities, mirroring `ChairmanMessageAdminPage`'s established convention
(see that file's own docstring for the identical pattern on a sibling
object).

═══════════════════════════════════════════════════════════════════════
THIS FEATURE IS BACKED BY **TWO** OBJECT AUTHORING OBJECTS
  1. **Chamber Laws Page** — slug `chamber-laws-page`
     (`/web/qatar-chamber/manage-chamber-laws-page`). A SINGLETON: exactly
     one record, `QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`. Owns the
     PAGE-level content.
  2. **Law Entry** — slug `law-entry` (`manage-law-entry`). One record per
     law/reference CARD in the Official Legal References section.

`Content Image` (on the Page record, rendered as the intro figure) and
`Law Icon` (on each Law Entry, rendered as a card's icon) are TWO DIFFERENT
images on TWO DIFFERENT objects. Do not conflate them.
═══════════════════════════════════════════════════════════════════════

⚠ CORRECTION OF A FALSE, DATED "LIVE-VERIFIED FACT" (this file and its
sibling test module both carried it; it is now removed).
Between 2026-09-09 and 2026-09-15 this module asserted, as a live-verified
fact, that "there is no page-level Chamber's Law object", that
`manage-chamber-laws-page` returned HTTP 404, and that Page Title / Intro
Heading / References Heading "exist NOWHERE in Object Authoring" and were
unauthorable static fragment content. **Every part of that is wrong.**

RE-VERIFIED LIVE 2026-09-15 (authenticated headless Chromium against qcdev
via `.auth/state.json` + a scoped CLI Playwright probe — disclosed, still
CLI, never the Playwright MCP; `tools/extract_locators.py` was run first and
confirmed the page renders the real Object Authoring shell, but its static
harvester does not resolve accessible names the way `get_by_role(name=...)`
does, hence the scoped probe for the field names below):

  - `/web/qatar-chamber/object-authoring` returns HTTP 200 and its index
    links **"Chamber Laws Page" -> /web/qatar-chamber/manage-chamber-laws-page**.
  - `manage-chamber-laws-page` returns **HTTP 200**, title
    "Manage: Chamber Laws Page", and lists ONE entry:
    `QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`, status APPROVED / ON THE
    WEBSITE.
  - Its editing banner reads: 'Editing
    QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY (approved). It is published. Use
    Unpublish to edit as draft ...'.
  - Its fields, with the EXACT accessible names read off the live form
    (uniqueness count == 1 for every one of them):

        'Page Title'                  'Page Title — العربية *'
        'Intro Heading'               'Intro Heading — العربية *'
        'Intro Content'  (rich text)  'Intro Content — العربية'  (rich text)
        'Content Image'  (Select File / Remove file / Preview · Download)
        'Content Image Alt Text'      'Content Image Alt Text — العربية *'
        'References Heading'          'References Heading — العربية *'

  - PROOF the record drives the public page — the CMS values match the
    anonymous, logged-out render character-for-character (the live data is
    polluted by earlier runs, which makes the match all the more decisive):

        CMS `Page Title`         = "Chamber’s Law--1"
            -> public `h1.qc-cl-hero-title`
        CMS `Intro Heading`      = "Chamber Legal Framework Framework"
            -> public `h2.qc-cl-intro-heading`
        CMS `References Heading` = "Official Official Legal References"
            -> public `h2.qc-cl-refs-heading`
        CMS `Content Image`      = chamber-laws-content.png (173 KB)
            -> public `img.qc-cl-intro-img` whose `src` carries
               `objectEntryExternalReferenceCode=
                QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`

    That last one is the strongest single signal: the delivered image URL
    names this object entry as its owner.

  - Corroborating evidence that the object existed all along: this repo's
    own `ObjectAuthoringPage.current_file_name()` / `download_current_file()`
    helpers carry a "CONFIRMED LIVE 2026-09-07 against manage-chamber-laws-
    page (Content Image)" note. The 2026-09-09 "it does not exist" claim
    contradicted a finding already recorded in the same codebase.

  - The `cms/Content-Admin-Guide.docx` §26 reading that produced the false
    claim was an ARGUMENT FROM SILENCE: the guide describes `LawEntry`, and
    the absence of a page-level object in that section was treated as proof
    of non-existence. The guide is the source of truth for object NAMING; it
    is not an exhaustive inventory, and a live HTTP 200 on the object's own
    manage page outranks its silence.

The practical cost of the false claim: five cases (134871, 134873, 134874,
134875, 134882) were retargeted onto Law Entry, where they tested something
the case did not ask about, and 134883 was retargeted onto `Law Icon`
instead of `Content Image`. All six are retargeted back by this batch.

── Law Entry (`manage-law-entry`) — re-verified live 2026-09-15 ──────────
Fields, in on-screen order, accessible names exactly as rendered:

    'Law Number'        'Law Number — العربية *'
    'Law Title'         'Law Title — العربية *'
    'Law Description'   'Law Description — العربية *'   (plain textbox, NOT
                        rich text — a real, confirmed-live difference from
                        what a "Description" field is on other objects)
    'External Link URL'                (NOT bilingual — no AR counterpart)
    'Law Icon'                         (Select File picker)
    'Display Order'                    (spinbutton)
    'Active Status'                    (checkbox)

Live records at re-verification: `QCDEMO-129394-law-11-1990` (Approved,
active) and `QCDEMO-129394-law-11-1996` (Approved, active) — the public
page's first and second cards — plus two pre-existing strays (`test samy`,
inactive; a `455`/`44444` entry) this batch never touches.

── REQUIRED-FIELD ASTERISKS ARE PART OF THE ACCESSIBLE NAME ─────────────
On BOTH objects, the ENGLISH half of each bilingual pair is NOT required
(no asterisk) while the ARABIC half IS (trailing " *"), e.g. the live
accessible name is `Law Number — العربية *`, never `Law Number — العربية`.
`ARABIC_SUFFIX` below therefore stays asterisk-free and the tolerance lives
in the lookup instead: `ObjectAuthoringPage.label_pattern()` matches an
anchored label with an OPTIONAL trailing ` *`, and every `fill_text` /
`field_value` / `fill_number` / `set_checkbox` / `is_checked` call on that
class now uses it. A blanket `ARABIC_SUFFIX = " — العربية *"` would be
wrong: it would break the non-required shapes (`Intro Content — العربية`
carries no asterisk at all).

── Entry-column identity differs PER OBJECT on this feature ─────────────
  - **Chamber Laws Page**: the Entry column renders the entry CODE
    (`QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`) -> use the `*_by_code`
    lookups (`row_status_text_by_code`, `row_preview_url_by_code`).
  - **Law Entry**: the Entry column renders the real Law TITLE -> use the
    title-keyed lookups (`row_visible`, `row_preview_url`).
Mixing them up is how two tests timed out on 2026-09-09.

── Attachment fields ────────────────────────────────────────────────────
Both `Content Image` (Page record) and `Law Icon` (Law Entry) render the
richer upload widget variant: a real `Current file: <name> (<size>) /
Preview · Download / Remove file` block once a file is set — re-confirmed
live 2026-09-15 for Content Image (`chamber-laws-content.png`, 173 KB, with
a working Download link). That gives a genuine byte-for-byte TEST_OWNED
restore path (`download_current_file()` before mutating ->
`upload_file()` in `finally`), which the Chairman Portrait / Hero Banner
fields on other objects do not have.

── Measured lifecycle timings (live, 3/3 iterations, 2026-09-15) ────────
  - "Unpublish to edit as draft" button visible:      0.02–0.05 s
  - status reads `Draft` after clicking Unpublish:    1.20–1.38 s
  - status reads `Approved` after Submit for Publishing: **27–30 s**
Publishing is an order of magnitude slower than unpublishing. Any wait
budget gated behind a publish must be sized for ~30 s plus the public
cache refresh — see the test module's own timeout constants.

Every CMS-mutating test in the sibling test module is TEST_OWNED (this
project's Test-Data Policy): it reads the record's/entry's current value
immediately before mutating and restores that SAME captured value in a
`finally` block, never a hardcoded assumed "original" — this class exposes
no state of its own; every baseline capture happens in the test.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

# ---- Object Authoring identities — all re-verified live 2026-09-15 -------
# The page-level singleton. Re-instated after the false 2026-09-09 "this
# object does not exist" claim (see the module docstring for the evidence).
CHAMBERS_LAW_PAGE_SLUG = "chamber-laws-page"
CHAMBERS_LAW_PAGE_ENTRY_CODE = "QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY"

# The per-law card records.
LAW_ENTRY_SLUG = "law-entry"
LAW_1990_ENTRY_CODE = "QCDEMO-129394-law-11-1990"
LAW_1996_ENTRY_CODE = "QCDEMO-129394-law-11-1996"
# Law Entry's Entry column renders the entry's real Law Title text
# (confirmed live), so row_visible()/row_status_text()/row_preview_url()
# (title-keyed) are the correct lookups for THAT object. The Chamber Laws
# Page object is the opposite — its Entry column renders the entry CODE, so
# the `_by_code` variants are the correct lookups there.
LAW_1990_TITLE = "Establishment of the Qatar Chamber of Commerce and Industry"
LAW_1996_TITLE = "Amending Certain Provisions of Law No. 11 of 1990"
LAW_1990_NUMBER = "Law No. 11 of 1990"
LAW_1996_NUMBER = "Law No. 11 of 1996"


class ChambersLawAdminPage(BasePage):
    """Thin holder of this feature's TWO object identities + both objects'
    field-label constants. All navigation/state/lifecycle behaviour is
    delegated to `ObjectAuthoringPage` — this class does not duplicate that
    state machine (see module docstring)."""

    # ---- Chamber Laws Page (singleton) field labels — confirmed live ------
    # Accessible names exactly as rendered; the Arabic counterpart of each
    # bilingual field is `<label> + ARABIC_SUFFIX` and additionally carries a
    # required-field " *" that ObjectAuthoringPage.label_pattern() tolerates
    # (see the module docstring).
    PAGE_TITLE_LABEL = "Page Title"
    INTRO_HEADING_LABEL = "Intro Heading"
    INTRO_CONTENT_LABEL = "Intro Content"
    # Liferay object-field name for the Intro Content rich-text field — pass
    # this to ObjectAuthoringPage.fill_rich_text()/rich_text_value() so the
    # EN (default-locale) CKEditor instance is targeted deterministically
    # instead of by mount order. Confirmed live 2026-09-15:
    # `div[id*="ObjectField_introContent"] iframe[title="editor"]` resolves
    # to exactly ONE iframe while a bare `iframe[title="editor"]` matches TWO
    # (EN + AR).
    INTRO_CONTENT_FIELD_NAME = "introContent"
    CONTENT_IMAGE_UPLOAD_LABEL = "Content Image"
    CONTENT_IMAGE_ALT_TEXT_LABEL = "Content Image Alt Text"
    REFERENCES_HEADING_LABEL = "References Heading"
    ARABIC_SUFFIX = " — العربية"

    # ---- Law Entry field labels — confirmed live --------------------------
    LAW_NUMBER_LABEL = "Law Number"
    LAW_TITLE_LABEL = "Law Title"
    LAW_DESCRIPTION_LABEL = "Law Description"
    # NOT BILINGUAL -- re-confirmed live 2026-09-15 three independent ways:
    # the manage form renders exactly ONE control named
    # `ObjectField_externalLinkUrl`; the form carries Arabic twins for
    # `lawNumber`/`lawTitle`/`lawDescription` ONLY (`#qc-ar-*`, three of
    # them, no `#qc-ar-externalLinkUrl`); and the Object definition itself
    # reports `localized: false` for this field while the page's own
    # `configuration.localizedFields` reads exactly
    # "lawNumber,lawTitle,lawDescription". So the Arabic-control defect
    # (#141969 / #141991 -- a `name`-less twin missing from the `/validate`
    # payload) CANNOT apply here: there is no twin to be missing.
    EXTERNAL_LINK_URL_LABEL = "External Link URL"
    # The SAME control's accessible name when the form renders in Arabic.
    # It is the Object's own `label.ar_SA`, and unlike the three localized
    # text fields -- whose Arabic labels are the ASCII strings "Law Number
    # (AR)" / "Law Title (AR)" / "Law Description (AR)" -- this one is
    # genuinely Arabic, so an English-label lookup resolves ZERO controls on
    # an Arabic render. Read live off the settled form, count == 1.
    EXTERNAL_LINK_URL_LABEL_AR = "رابط النص القانوني الخارجي"
    LAW_ICON_UPLOAD_LABEL = "Law Icon"
    DISPLAY_ORDER_LABEL = "Display Order"
    ACTIVE_STATUS_LABEL = "Active Status"

    def __init__(self, page):
        super().__init__(page)

    # ---- Chamber Laws Page (singleton) navigation -------------------------
    def open_page_record(self) -> "ObjectAuthoringPage":
        """Opens the ONE Chamber Laws Page record for edit. Returns the
        `ObjectAuthoringPage` driving `manage-chamber-laws-page`, with its
        entry code already tracked (so `reopen()`/`wait_for_status()` work)."""
        authoring = ObjectAuthoringPage(self.page, slug=CHAMBERS_LAW_PAGE_SLUG)
        authoring.open_entry_by_code(CHAMBERS_LAW_PAGE_ENTRY_CODE)
        return authoring

    def open_page_entries_list(self) -> "ObjectAuthoringPage":
        """Opens `manage-chamber-laws-page`'s own entries list (one row).
        Remember: this object's Entry column renders the CODE, so use the
        `*_by_code` lookups on the returned object."""
        authoring = ObjectAuthoringPage(self.page, slug=CHAMBERS_LAW_PAGE_SLUG)
        authoring.open_entries_list()
        return authoring

    # ---- Law Entry navigation ----------------------------------------------
    def open_law_entry(
        self, entry_code: str, locale: str | None = None
    ) -> "ObjectAuthoringPage":
        """`locale="en"` / `locale="ar"` PINS the CMS interface language of
        the authoring form (see ObjectAuthoringPage._manage_url()'s
        locale-pinning note). It matters on this object more than on most:
        the shared qcdev authoring account's own Liferay language is
        `ar_SA`, so an unpinned open renders Arabic field labels
        ("Law Number (AR)", "رابط النص القانوني الخارجي", "ترتيب العرض") --
        against which every English `label_pattern()` lookup resolves ZERO
        controls -- and serves every client-side validation message in
        Arabic. `locale=None` keeps the historic session-inherited
        behaviour."""
        authoring = ObjectAuthoringPage(self.page, slug=LAW_ENTRY_SLUG)
        authoring.open_entry_by_code(entry_code, locale=locale)
        return authoring

    def open_law_entries_list(self, locale: str | None = None) -> "ObjectAuthoringPage":
        """Opens `manage-law-entry`'s entries list. This object's Entry
        column renders the real Law Title, so use the title-keyed lookups.

        `locale` pins the interface language exactly as `open_law_entry()`
        does, and for the same live-measured reason: an Edit link clicked
        out of an UNPINNED list inherits whatever locale the session drifted
        to (`ar_SA` for the shared qcdev authoring account), against which
        every English `label_pattern()` lookup on the form that opens
        resolves ZERO controls."""
        authoring = ObjectAuthoringPage(self.page, slug=LAW_ENTRY_SLUG)
        authoring.open_entries_list(locale=locale)
        return authoring

    def open_new_law_entry_form(self, locale: str | None = None) -> "ObjectAuthoringPage":
        """`locale` pins the interface language — see `open_law_entry()`."""
        authoring = ObjectAuthoringPage(self.page, slug=LAW_ENTRY_SLUG)
        authoring.open_new_entry_form(locale=locale)
        return authoring

"""
cms/pages/home_hero_banner/home_hero_banner_admin_page.py — HeroBannerSlideAdminPage,
AchievementCounterAdminPage.

Control_Panel Page Objects for PBI 129367 (QC-HOME-001 — Hero Banner),
backing the homepage Hero Banner carousel and its "Achievement Counters" row
embedded IN the hero overlay (public counterpart: web/pages/home_hero_banner/
home_hero_banner_page.py).

CONFIRMED LIVE (2026-09-08, Playwright MCP against qcdev, TEST_USER session —
disclosed fallback: this session had no prior extraction for this page, and
both objects sit behind an authenticated Object Authoring surface the
stateless CLI extractor would need the same live/authenticated browser
context to reach anyway):

  - The Hero Banner is backed by TWO separate Liferay Object Definitions,
    both reachable via Object Authoring (`/web/qatar-chamber/manage-<slug>`)
    per standards.md's "Object Authoring Is the Only Path for Content
    Operations" rule — Content & Data is never used for either:

    1. "Hero Banner Slide" -> manage-hero-banner-slide. 6 entries this
       session: QCDEMO-129367-HERO_BANNER_SLIDE-01 / -02 (both Approved,
       QCDEMO/TEST_OWNED seed rows — the "129367" embedded in their own
       externalReferenceCode is the live-confirmed source of this PBI
       number, the same seed-naming convention already relied on
       project-wide, e.g. pbi_129389/pbi_129397) plus 4 further UUID-coded
       real-content rows (3 Approved + 1 Draft) that this suite never
       touches. Confirmed field set (via `get_by_role` accessible names,
       the confirmed-working locator strategy for this DDM-less Object
       Authoring surface — see ObjectAuthoringPage's own module docstring):
       Banner Image (upload), Banner Title (EN/AR), Banner Subtitle
       (Description) (EN/AR), Button 1 Label (EN/AR), Button 1 Link,
       Button 2 Label (EN/AR), Button 2 Link, Display Order, Active Status
       (checkbox), Counters Active Status (checkbox — whether THIS slide's
       own overlay also renders the counters row). Save as Draft / Submit
       for Publishing, same lifecycle as every other Object Authoring
       surface on this project (see ObjectAuthoringPage).

    2. "Achievement Counter" -> manage-achievement-counter. 4 entries this
       session: QCDEMO-129367-ACHIEVEMENT_COUNTER-01 / -02 / -03 (Approved,
       QCDEMO/TEST_OWNED seed rows) plus 1 further UUID-coded row (also
       Approved, renders as the 4th "statistics" counter) — all 4 are
       currently live on the Home Page. Confirmed live field-to-frontend
       mapping (each counter's own Home Page `<img>` src embeds its
       `objectEntryExternalReferenceCode`, confirmed by reading the DOM):
         -01  Display Order=100, Active=True — "Active Members" / "50K +"
         -02  Display Order=200, Active=True — "Countries Served" / "100 +"
         -03  Display Order=300, Active=True — "Service Support" / "24/7"
              <- this is "counter 3" in every ADO case this module covers
         (UUID row) Display Order=400 — "statistics" / "5001+"
       Confirmed field set: Counter Title (EN/AR), Counter Value, Counter
       Icon (upload), Counter Display Order (spinbutton), Counter Active
       Status (checkbox).

       THIS IS A DIFFERENT OBJECT DEFINITION from "About Us Counter"
       (manage-about-us-counter, PBI 129389's "Last Year Achievements"
       widget lower on the Home Page — see
       cms/pages/home_about_summary/home_about_summary_admin_page.py). Do
       not conflate the two: they are separate Object Definitions
       rendering in two different Home Page sections with two different
       field sets (About Us Counter's fields are Counter Active Status/
       Display Order/Title/Value too, but on a visually distinct section
       with "0 +"-style live values, confirmed live to be unrelated data).

  - The counters row only renders inside whichever Hero Banner Slide is
    currently the carousel's active overlay AND has its own "Counters
    Active Status"=true. HERO_BANNER_SLIDE-01 (Display Order=100 — the
    lowest, confirmed live twice to be the slide shown on a fresh,
    un-clicked page load) has Counters Active Status=true — every counter
    test in this module's paired test file relies on -01 staying untouched
    (this module's own tests never mutate it).

  - HERO_BANNER_SLIDE-01 and -02 share the IDENTICAL default seed Banner
    Title (EN) ("Qatar Chamber is among the oldest chambers of commerce in
    the GCC.") — confirmed live by reading both edit forms directly. Title
    text alone therefore cannot distinguish -02 on the public carousel;
    see the paired test module's tc_135024 docstring for how this is
    handled (a temporary QCTEST- fingerprint, captured/restored).

  - Editing an already-Approved entry on EITHER object requires "Unpublish
    to edit as draft" first — same confirmed-live shape as every other
    Object Authoring object on this project (e.g.
    home_community_partners_admin_page.py) — there is no direct
    edit-then-resave path for an Approved row.

CONFIRMED LIVE (2026-09-08, Playwright MCP against qcdev, TEST_USER session
— this batch's tc_135010/135014/135015/135018/135019 investigation):

  - "Hero Banner Slide"'s own Entry-column list rows show a UUID/
    externalReferenceCode for every row EXCEPT the two QCDEMO seed rows
    (-01/-02, which show their own real externalReferenceCode by design) —
    a freshly created row's Entry column NEVER renders its Banner Title,
    same class of exception as manage-strategic-pillar-card documented in
    ObjectAuthoringPage's own module docstring. Any test creating its own
    disposable QCTEST- slide MUST resolve that row's real entry code via
    `find_entry_code_by_field(BANNER_TITLE_EN_LABEL, title)` before acting
    on it (open/status/delete) — never a title-based `row_status_text`/
    `delete_entry_by_title`/`row_visible` call, which will never match.

  - Confirmed field-label -> accessible-name mapping (via
    `get_by_role(..., name=<label>, exact=True)`, this surface's
    established working pattern): "Banner Image" (upload field — no
    "(upload)" suffix in the real accessible name), "Display Order"
    (spinbutton — distinct label text from Achievement Counter's own
    "Counter Display Order", no collision), "Active Status" (checkbox —
    distinct from Achievement Counter's "Counter Active Status").

  - REVISED 2026-09-08 (see the CORRECTED note above — supersedes this
    paragraph's original "raw upload" framing): "Banner Image" is a MEDIA
    PICKER, not a raw upload field. `select_banner_image_from_library()`
    (via `ObjectAuthoringPage.select_existing_file_from_library()`) opens
    the same item-selector modal, navigates into the confirmed-live
    "Flickr" library folder, and single-clicks the confirmed-live existing
    file "download.png" — selecting it immediately, no drag-drop, no "Add"
    button. The field's own filename readout
    (`uploaded_filename("Banner Image")`) correctly shows "download.png"
    immediately after selection — confirmed live end-to-end. Because this
    is a SELECT of an already-existing library file (not a new upload),
    there is no repeat-upload auto-rename behavior to work around (that
    concern only applied to the old, now-removed raw-upload flow) — every
    run selects the exact same stable "download.png", so
    `uploaded_filename()` can be asserted by exact match, not prefix. NO
    separate visual `<img>` thumbnail element renders anywhere on this
    form after selection (searched live for any `<img src>` referencing
    the file or a `/documents/` path — zero matches, both immediately
    after selection and after Save as Draft) — this Object Authoring
    surface's only observable "selection succeeded" signal is the
    filename readout, same mechanism `uploaded_filename()` was already
    built for elsewhere on this project (see ObjectAuthoringPage's own
    docstring). ADO 135010's literal "thumbnail preview shown" expected
    result is therefore asserted via this filename-readout signal, a
    disclosed mechanism substitution, not a dropped case — the
    selection's real success/failure IS observably verifiable this way,
    just not via a visual thumbnail. Separately, ADO 135010's own literal
    steps ("Click upload control" / "Select banner1.jpg (1.2MB)") describe
    the raw-upload mechanism the case's author assumed — reinterpreted
    here as "click the image picker control" / "select an existing image
    from the library", the real mechanism, disclosed on that test's own
    docstring (same disclosed-mechanism-substitution precedent as
    tc_135024's own docstring elsewhere in this suite) — the case's
    asserted intent (a Banner Image selection succeeds and is observably
    confirmed) is unchanged, only how that intent is reached.
    ON REOPEN: unlike a raw upload (which this project's Object Authoring
    surface does NOT support for this field), a picker-selected EXISTING
    file's association DOES persist correctly — confirmed live on a
    disposable probe entry: the field's hidden "Select File" control's own
    placeholder attribute reads "Current file: download.png — pick a file
    to replace it" on a fresh `editEntry` reopen (the `<strong>` filename-
    readout element itself is empty on reopen — a real, different-signal
    quirk of reopen vs. immediately-after-select, not a persistence
    failure; the placeholder is the correct reopen-state signal).

  - New entries default Active Status=False AND Counters Active
    Status=False (confirmed live, unchecked checkboxes on a fresh
    create-new form) — a disposable QCTEST- entry saved with no explicit
    Active Status change never appears on the live carousel regardless of
    Draft/Approved status, which is exactly the safe default for
    tc_135010 (upload-only, no publish needed) but means tc_135018/135019
    must EXPLICITLY check Active Status=True themselves to produce a real,
    meaningful publish/draft-visibility assertion rather than a vacuous one.

  - The carousel AUTOPLAYS: `section.qc-home-hero-banner[data-autoplay-
    interval="6000"]` (confirmed live) — the initially-active slide on a
    fresh page load silently advances to the next one after ~6s. This is
    why HomeHeroBannerPage.active_slide_entry_code() (used by
    tc_135014/135015) must be read IMMEDIATELY after open_home() returns,
    never after any extra wait/settle — reload_until_active_slide_matches()
    does exactly that on every poll iteration (fresh open_home() -> read,
    no intervening delay).

  - **CORRECTED 2026-09-08 (was: "LIVE-CONFIRMED PRODUCT DEFECT" — that
    finding was WRONG, caused by this automation using the wrong control,
    not a real product defect; corrected honestly here rather than
    silently walked back)**: an earlier pass of this suite concluded there
    was no working UI path to Approve a brand-new Hero Banner Slide,
    because (a) "Banner Image" appeared to silently fail to persist across
    a reopen, and (b) Submit for Publishing appeared to fire zero API
    calls / silently no-op. Both observations were real, but both had a
    different, mundane cause than a product defect:
      1. "Banner Image" is NOT a raw file-upload field on this project —
         it is a MEDIA PICKER that selects an EXISTING image already in
         Liferay's Documents & Media library (this project's library is
         populated by a one-way Flickr import — see cms-profile.md's
         "Flickr Pro API" note and `.claude/context/active/background.md`).
         The earlier pass drove the field via `upload_file()`'s drag-drop-
         a-NEW-file flow instead of clicking an existing file's own card —
         confirmed live (2026-09-08, Playwright MCP) that a single click on
         an existing file (e.g. a file directly under the "Flickr" library
         folder) selects it immediately (no "Add" button, no upload-
         progress wait) and — unlike the raw-upload path — this selection
         DOES persist correctly across a reopen: the field's hidden
         "Select File" control's own placeholder reads "Current file:
         <name> — pick a file to replace it" on a fresh `editEntry`
         reopen, confirmed live end-to-end on a disposable probe entry.
         See `ObjectAuthoringPage.select_existing_file_from_library()` and
         this class's `select_banner_image_from_library()`, now used
         instead of the old `upload_banner_image()` (removed — see below).
      2. Submit for Publishing does NOT silently no-op — it is blocked by
         ordinary native HTML5 "Please fill out this field" validation
         whenever any of this form's OTHER required fields are left empty
         (Banner Subtitle (Description) EN/AR, Button 1 Label EN/AR,
         Button 1 Link, Button 2 Label EN/AR, Button 2 Link — all marked
         required `*` on this form, confirmed live by screenshot: a
         validation tooltip appears on the first empty required field and
         the click never reaches the network layer at all, hence "zero API
         calls"). The earlier pass filled only Banner Title EN/AR + Active
         Status before Submit — never these other required fields — and
         read the resulting zero network calls as a silent product no-op.
         CONFIRMED LIVE 2026-09-08: filling EVERY required field (Banner
         Image via the picker above, Banner Title EN/AR, Banner Subtitle
         EN/AR, both Button Labels EN/AR, both Button Links, Display Order)
         and clicking Submit for Publishing on a brand-new create form
         fires a real `POST .../herobannerslides/scopes/<id>/validate`,
         creates a real entry, and that entry's own status reads
         "(approved)" on the very next `editEntry` reopen — reproduced
         live end-to-end on a disposable probe entry (created, confirmed
         Approved, then deleted as part of this correction's own cleanup).
      Net effect: there IS a working UI path to Approve a brand-new Hero
      Banner Slide with an image — create -> pick an EXISTING library
      image -> fill every other required field -> Submit for Publishing.
      No Bug should be filed against PBI 129367 from the earlier pass's
      finding; that finding is retracted here. tc_135018 below is now
      scripted to reach a real Approved status and exercise the actual
      delete assertion, not an expected-failure placeholder.

  - Display Order swap round-trip for the -01/-02 pair, live-confirmed
    end-to-end 2026-09-08 (see test module's tc_135014 docstring for the
    full evidence): unlike the Achievement Counter object, this object's
    Display Order values do NOT need an out-of-convention substitute — the
    case's own literal "1"/"2" values produce a clean swap with no tie,
    because the only OTHER currently-Active real slide
    (bbdc6974-fb89-6d9f-96ba-a7273a2122a3, "please visit our website") sits
    at Display Order 300 (well outside 1-2), and this object's remaining 2
    real rows (a85dddfc-..., fb725894-...) are both Active Status=False
    (Display Order 0 each, confirmed live) and therefore never render on
    the carousel regardless of their own Display Order value — a tie with
    an inactive row is a non-event. -01/-02's TRUE baseline (100/200) was
    restored and re-verified live before this batch's tests were written.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url, settings

HERO_BANNER_SLIDE_SLUG = "hero-banner-slide"
ACHIEVEMENT_COUNTER_SLUG = "achievement-counter"

# ---- Session/auth (HEALED 2026-09-14, triage of tc_135009/135013/135016/
# 135017/135022/135023/135025 — see module docstring's own investigation
# notes for the rest of this batch): mirrors
# OrgStructureAdminPage._ensure_logged_in() / HomeBusinessEventsAdminPage.
# _ensure_logged_in()'s already-confirmed-live pattern exactly — a
# stale/absent session hitting `manage-hero-banner-slide`/
# `manage-achievement-counter` directly renders the public "Coming Soon"
# placeholder with no login redirect for either class to react to. Both
# classes below were the confirmed-live gap in that shared pattern (they
# compose ObjectAuthoringPage directly, with no override), unlike their
# sibling admin Page Objects that already carry this guard. Routing through
# `/en/home` first, which DOES surface a real login form when logged out,
# closes that gap the same way it already does for those siblings.
ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'

# ---- Hero Banner Slide (confirmed-live entry codes) ------------------------
HERO_SLIDE_01_ERC = "QCDEMO-129367-HERO_BANNER_SLIDE-01"  # Display Order 100 — the counters-active slide, NOT touched by these tests
HERO_SLIDE_02_ERC = "QCDEMO-129367-HERO_BANNER_SLIDE-02"  # Display Order 200 — this module's publish/unpublish test target

BANNER_TITLE_EN_LABEL = "Banner Title (EN)"
BANNER_TITLE_AR_LABEL = "Banner Title (AR)"
BANNER_IMAGE_LABEL = "Banner Image"
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

# Confirmed-live-populated Documents & Media library location this project's
# Flickr import lands content in (see cms-profile.md's "Flickr Pro API"
# note) — used by select_banner_image_from_library() below as the real,
# working mechanism for the "Banner Image" media-picker field (see module
# docstring's CORRECTED note). "download.png" sits directly under the
# "Flickr" folder itself (no sub-album navigation needed), confirmed live
# 2026-09-08 and re-verified idempotent across repeat selection (unlike a
# raw upload, selecting an existing library file has no repeat-run
# auto-rename side effect to work around).
BANNER_IMAGE_LIBRARY_FOLDER = "Flickr"
BANNER_IMAGE_LIBRARY_FILE = "download.png"

# ---- Achievement Counter (confirmed-live entry codes) -----------------------
ACHIEVEMENT_COUNTER_01_ERC = "QCDEMO-129367-ACHIEVEMENT_COUNTER-01"
ACHIEVEMENT_COUNTER_02_ERC = "QCDEMO-129367-ACHIEVEMENT_COUNTER-02"
ACHIEVEMENT_COUNTER_03_ERC = "QCDEMO-129367-ACHIEVEMENT_COUNTER-03"  # "counter 3" in every ADO case this module covers

COUNTER_TITLE_EN_LABEL = "Counter Title (EN)"
COUNTER_TITLE_AR_LABEL = "Counter Title (AR)"
COUNTER_VALUE_LABEL = "Counter Value"
COUNTER_DISPLAY_ORDER_LABEL = "Counter Display Order"
COUNTER_ACTIVE_STATUS_LABEL = "Counter Active Status"


class HeroBannerSlideAdminPage(ObjectAuthoringPage):
    """Hero Banner Slide's own field-level actions, composed on top of the
    generic Object Authoring Draft/Preview/Publish/Unpublish state machine
    (open_entry_by_code, unpublish_to_edit_as_draft, submit_for_publishing,
    current_status, row_status_text_by_code, ... all inherited as-is from
    ObjectAuthoringPage — do not re-declare them here)."""

    def __init__(self, page):
        super().__init__(page, HERO_BANNER_SLIDE_SLUG)

    def _ensure_logged_in(self) -> None:
        """See module-level constants' docstring note above — HEALED
        2026-09-14. Called at the top of every navigation entry point this
        module's tests use as their FIRST admin action
        (open_new_entry_form/open_entry_by_code), mirroring exactly where
        OrgStructureAdminPage/HomeBusinessEventsAdminPage call their own
        copy of this same check (not on every subsequent navigation)."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_new_entry_form(self) -> "HeroBannerSlideAdminPage":
        self._ensure_logged_in()
        return super().open_new_entry_form()

    def open_entry_by_code(self, entry_code: str) -> "HeroBannerSlideAdminPage":
        self._ensure_logged_in()
        return super().open_entry_by_code(entry_code)

    def set_banner_title_en(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BANNER_TITLE_EN_LABEL, value)
        return self

    def banner_title_en_value(self) -> str:
        return self.field_value(BANNER_TITLE_EN_LABEL)

    def set_banner_title_ar(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BANNER_TITLE_AR_LABEL, value)
        return self

    def banner_title_ar_value(self) -> str:
        # ADDED for tc_135009/tc_135013 (batch1, 2026-09-13) — symmetry
        # getter for banner_title_en_value() above; ObjectAuthoringPage's
        # generic field_value() already supports any field label, this is
        # just a named wrapper so callers read at this class's own
        # vocabulary rather than passing BANNER_TITLE_AR_LABEL directly.
        return self.field_value(BANNER_TITLE_AR_LABEL)

    def select_banner_image_from_library(
        self,
        folder_name: str = BANNER_IMAGE_LIBRARY_FOLDER,
        file_name: str = BANNER_IMAGE_LIBRARY_FILE,
    ) -> "HeroBannerSlideAdminPage":
        """The REAL, working mechanism for "Banner Image" — a media-library
        picker, NOT a raw file upload (see module docstring's CORRECTED
        note). Replaces the old, wrongly-mechanized `upload_banner_image()`
        (removed 2026-09-08)."""
        self.select_existing_file_from_library(BANNER_IMAGE_LABEL, folder_name, file_name)
        return self

    def uploaded_banner_image_filename(self) -> str:
        return self.uploaded_filename(BANNER_IMAGE_LABEL)

    def set_banner_subtitle_en(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BANNER_SUBTITLE_EN_LABEL, value)
        return self

    def set_banner_subtitle_ar(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BANNER_SUBTITLE_AR_LABEL, value)
        return self

    def set_button1_label_en(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BUTTON1_LABEL_EN_LABEL, value)
        return self

    def set_button1_label_ar(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BUTTON1_LABEL_AR_LABEL, value)
        return self

    def set_button1_link(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BUTTON1_LINK_LABEL, value)
        return self

    def set_button2_label_en(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BUTTON2_LABEL_EN_LABEL, value)
        return self

    def set_button2_label_ar(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BUTTON2_LABEL_AR_LABEL, value)
        return self

    def set_button2_link(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_text(BUTTON2_LINK_LABEL, value)
        return self

    def fill_remaining_required_fields_for_publishing(
        self,
        subtitle_en: str,
        subtitle_ar: str,
        button1_label_en: str,
        button1_label_ar: str,
        button1_link: str,
        button2_label_en: str,
        button2_label_ar: str,
        button2_link: str,
    ) -> "HeroBannerSlideAdminPage":
        """Convenience batch-fill for every OTHER required (`*`) field on
        this form besides Banner Title/Image/Display Order — CONFIRMED LIVE
        2026-09-08 that Submit for Publishing is blocked by ordinary native
        HTML5 required-field validation (not a product defect — see module
        docstring's CORRECTED note) unless Banner Subtitle (Description)
        EN/AR, Button 1/2 Label EN/AR, and Button 1/2 Link are all filled.
        Save as Draft does NOT require these — only needed by a caller that
        will call `submit_for_publishing()` on a brand-new entry."""
        self.set_banner_subtitle_en(subtitle_en)
        self.set_banner_subtitle_ar(subtitle_ar)
        self.set_button1_label_en(button1_label_en)
        self.set_button1_label_ar(button1_label_ar)
        self.set_button1_link(button1_link)
        self.set_button2_label_en(button2_label_en)
        self.set_button2_label_ar(button2_label_ar)
        self.set_button2_link(button2_link)
        return self

    def set_display_order(self, value: str) -> "HeroBannerSlideAdminPage":
        self.fill_number(DISPLAY_ORDER_LABEL, value)
        return self

    def display_order_value(self) -> str:
        return self.page.get_by_role(
            "spinbutton", name=DISPLAY_ORDER_LABEL, exact=True
        ).input_value()

    def set_slide_active(self, active: bool) -> "HeroBannerSlideAdminPage":
        self.set_checkbox(ACTIVE_STATUS_LABEL, active)
        return self

    def is_slide_active(self) -> bool:
        return self.page.get_by_role(
            "checkbox", name=ACTIVE_STATUS_LABEL, exact=True
        ).is_checked()


class AchievementCounterAdminPage(ObjectAuthoringPage):
    """Achievement Counter's own field-level actions, same composition
    pattern as HeroBannerSlideAdminPage above."""

    def __init__(self, page):
        super().__init__(page, ACHIEVEMENT_COUNTER_SLUG)

    def _ensure_logged_in(self) -> None:
        """Same guard, same rationale as HeroBannerSlideAdminPage's own
        copy above (HEALED 2026-09-14) — this class independently composes
        ObjectAuthoringPage and shares the same confirmed-live gap."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (self.is_visible(CONTENT_DATA_MENU_ITEM) or self.is_visible(PRODUCT_MENU_TOGGLE)):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_new_entry_form(self) -> "AchievementCounterAdminPage":
        self._ensure_logged_in()
        return super().open_new_entry_form()

    def open_entry_by_code(self, entry_code: str) -> "AchievementCounterAdminPage":
        self._ensure_logged_in()
        return super().open_entry_by_code(entry_code)

    def set_counter_active(self, active: bool) -> "AchievementCounterAdminPage":
        self.set_checkbox(COUNTER_ACTIVE_STATUS_LABEL, active)
        return self

    def is_counter_active(self) -> bool:
        return self.page.get_by_role(
            "checkbox", name=COUNTER_ACTIVE_STATUS_LABEL, exact=True
        ).is_checked()

    def set_counter_display_order(self, value: str) -> "AchievementCounterAdminPage":
        self.fill_number(COUNTER_DISPLAY_ORDER_LABEL, value)
        return self

    def counter_display_order_value(self) -> str:
        return self.page.get_by_role(
            "spinbutton", name=COUNTER_DISPLAY_ORDER_LABEL, exact=True
        ).input_value()

    def counter_title_en_value(self) -> str:
        return self.field_value(COUNTER_TITLE_EN_LABEL)

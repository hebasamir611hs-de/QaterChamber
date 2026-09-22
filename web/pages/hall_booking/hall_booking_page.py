"""
web/pages/hall_booking/hall_booking_page.py — HallBookingPage.

Public-frontend Page Object for PBI 129411 (QC-SVC-014 — Hall Booking),
`/web/qatar-chamber/halls-booking` (SVC service — see standards.md's Service/
Module Codes: Halls Reservation is under "Our Services"). This is the pure
public-facing (Platform=Web) surface only — no admin/CMS steps here.

Locators extracted CLI-first via tools/extract_locators.py against the live
page (WEB_BASE_URL=https://qcdev.ihorizons.com) at the framework default
viewport, plus a disclosed scripted DOM probe (still CLI — a plain Playwright
script, not the Playwright MCP) for the component's own custom `data-qc-hb-*`
(page) / `data-qc-hbf-*` (reservation-form modal) attributes, which
`extract_locators.py`'s harvester does not surface (its SEL list matches
`data-testid`/`data-test`, not this project's own `data-qc-hb*` convention —
the same class of gap `org_structure_page.py`'s module docstring already
documents for that page's `qc-org-*` custom classes):

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/halls-booking

    -> role=button[name="Start Your Reservation"] / "Prepare Your Information"
       / "Check Availability & Timing" / "Review the Reservation Policy"
       / "Complete Your Submission"  (the 5 accordion headers, Section 02)
    -> role=button[name="View photo album: Sheikh Nasser Bin Khaled Hall"] /
       "Grand Hall" / "Training Hall"
    -> role=button[name="Reserve a Hall"]  uniq=2 (hero CTA + bottom banner CTA)
    -> role=button[name="Select for reservation"]  uniq=3 (one per hall card)
    -> role=link[name="01Overview"] / "02Reservation Guidelines" /
       "03Available Halls" / "04Media Gallery"  (sticky section index)

DOM probe (plain Playwright script, `page.evaluate` over
`document.querySelectorAll('*')` filtered to attributes starting with
`data-qc-hb-`/`data-qc-hbf-`) confirmed the component's own stable
custom-attribute scheme — used below as the highest-tier locator, exactly
the same precedence `org_structure_page.py` gives its own `qc-org-*` custom
classes over generic CSS:

    section.qc-hb[data-qc-hb-home-url][data-qc-hb-services-url]...
      nav.qc-hb-crumbs[data-qc-hb-crumbs]                  (Home > Services)
      p.qc-hb-eyebrow[data-qc-hb-eyebrow]                  "Facilities Reservation Service"
      h1.qc-hb-title[data-qc-hb-title]                     "Halls Booking"
      p.qc-hb-hero-desc[data-qc-hb-desc]
      button.qc-hb-pill[data-qc-hb-hero-cta]                hero "Reserve a Hall"
      div.qc-hb-facts[data-qc-hb-facts] > .qc-hb-fact > .qc-hb-fact-label/-value
      aside.qc-hb-index-col > nav.qc-hb-index[data-qc-hb-index]
        a.qc-hb-index-item[data-qc-hb-index-key="01".."04"][href="#qc-hb-sec-0N"]
        (gets `.is-active` appended by a real scroll-driven scroll-spy —
        CONFIRMED LIVE: a synthetic `window.scrollTo()` jump does NOT update
        it, but real `page.mouse.wheel()` scroll events do — see
        scroll_by_wheel() below, and use it, never window.scrollTo, for any
        "scroll and observe the active section index" assertion)
      section#qc-hb-sec-01..04.qc-hb-section[data-qc-hb-section-key]
        sec-02: div.qc-hb-acc > div.qc-hb-acc-item
          button.qc-hb-acc-head[aria-expanded][aria-controls="qc-hb-acc-panel-N"]
          div.qc-hb-acc-body#qc-hb-acc-panel-N[hidden]      (5 items, N=0..4)
        sec-03: div.qc-hb-halls > div.qc-hb-hall
          h3.qc-hb-hall-name / button.qc-hb-hall-btn "Select for reservation"
          (live order confirmed: Sheikh Nasser Bin Khaled Hall, Grand Hall,
          Training Hall — "Grand Hall" is the 2nd hall used by tc_140024)
      div.qc-hb-banner[data-qc-hb-banner]                   "Ready to reserve a hall?" + its own "Reserve a Hall" CTA
      a.qc-lang-switcher (header)                            AR/EN toggle, href=/c/portal/update_language?...languageId=ar_SA|en_US

    Reservation Request Form modal (already mounted in the DOM at page load,
    `display:none` until the root class gains `qc-hall-booking-form--open` —
    CONFIRMED LIVE via computed-style probe, not a guess):
      div.qc-hall-booking-form[data-qc-hbf-root]
        div[data-qc-hbf-overlay] > div[data-qc-hbf-dialog]
          div[data-qc-hbf-view="form"]
            h2[data-qc-hbf-title]                            "Reservation Request Form" (AR: "نموذج طلب الحجز")
            button[data-qc-hbf-close]                         the "x" icon in the corner
            form[data-qc-hbf-form] > div[data-qc-hbf-grid]
              input[data-qc-hbf-field="companyEnglishName"]   *required
              input[data-qc-hbf-field="companyArabicName"]    *required
              input[data-qc-hbf-field="commercialRegistrationNumber"]  *required
              input[data-qc-hbf-field="emailAddress"]         *required, type=email
              input[data-qc-hbf-field="mobileNumber"]         *required, type=tel
              input[data-qc-hbf-field="telephone"]            (optional)
              input[data-qc-hbf-field="reservationFromDate"]  *required — DISPLAY input;
                the field a user actually TYPES/reads is a separate
                input[data-qc-hbf-native="reservationFromDate"] (type=date,
                visually hidden, feeds the display field/datepicker) — fill
                THIS one with an ISO "YYYY-MM-DD" string, confirmed live.
              input[data-qc-hbf-field="reservationToDate"]    *required (same native/display split)
              select[data-qc-hbf-field="selectedHall"]        *required — options:
                "" (the "Select" placeholder, default) / "Sheikh Nasser Bin
                Khaled Hall" / "Grand Hall" / "Training Hall"
              p[data-qc-hbf-error="<fieldName>"]              inline validation error, per field
              div[data-qc-hbf-captcha-row] > div[data-qc-hbf-captcha]  — see
                "CAPTCHA" note below
              input[data-qc-hbf-field="website"]              a honeypot field, not a real UI field — never fill it
            button[data-qc-hbf-cancel] "Cancel"                CONFIRMED LIVE: closes the modal correctly
            button[data-qc-hbf-close]  "×" (corner icon)       CONFIRMED LIVE BUG: clicking it does NOT close the
                modal (root keeps its `--open` modifier; no console error).
                close_modal() below therefore uses Cancel, the one control
                confirmed to actually work — do not switch it to the "x"
                icon without first re-confirming the icon button live again.
            button[data-qc-hbf-submit] "Submit Request"
          div[data-qc-hbf-view="success"]
            h2[data-qc-hbf-success-title]                     "Reservation Request Received"
            span[data-qc-hbf-reference]                       e.g. "HBR-00000001"
            button[data-qc-hbf-done] "Done"

    CAPTCHA (tc_140016 / tc_140019 / tc_140045's "Pass the CAPTCHA" step):
    CONFIRMED LIVE via captured network requests — this form's
    `div[data-qc-hbf-captcha]` renders **Google reCAPTCHA Enterprise in
    INVISIBLE mode** (`.../recaptcha/enterprise/anchor?...size=invisible...`,
    site key `6Lcfo3ctAAAAAODkvzP48AMiKKxOwt5hXpscaQ1c`) — there is no
    checkbox/challenge UI to click at all; it silently
    executes (`grecaptcha.enterprise.execute()`) as an implicit part of the
    Submit action, never as a separate user-visible step. No other
    already-automated webform test in this repo (`web/` or `cms/`) has an
    established CAPTCHA-handling pattern to follow (grepped both trees —
    none exists), so nothing is being overridden here; this is the first
    one. Two things were verified live, not assumed:
      1. Submitting with a missing mandatory field (tc_140016/tc_140019) is
         blocked by the form's own CLIENT-SIDE validation BEFORE the
         invisible widget ever executes — confirmed by reproducing the exact
         "leave Email Address blank" flow: the inline error appeared with no
         CAPTCHA-related network calls, prior data intact.
      2. A fully-valid submission (tc_140045's flow) DOES pass this
         environment's invisible widget from this scripted, headless
         Playwright session with no interaction at all — confirmed by
         actually completing a submission and receiving a real reference
         number back.
    submit_request() therefore just clicks Submit — there is no separate
    "solve the CAPTCHA" method to call, and none should be invented.

VISUAL/RENDERING BATCH (2026-09-16) — extends this Page Object for 15
Web-only visual-rendering cases (17 originally-CMS-write-then-verify-on-Web
cases scoped down to "verify what is CURRENTLY published" per the task; 2 of
the 17 — 139946/139997 — could not be scoped down at all, since they need a
CMS-created EMPTY-value precondition that has no live counterpart, and were
therefore never automated here). Every locator below came from a disclosed,
scripted DOM probe (still CLI — a plain Playwright script run in the shell,
not the Playwright MCP; `tools/extract_locators.py` does not harvest
non-interactive elements like `<img>`/mask-icon `<span>`s at all, the same
class of gap this file's own module docstring already documents for its
`data-qc-hb-*` custom-attribute harvest), confirmed live against
qcdev at the framework's default 1920x1080 viewport:

    Hero banner image (tc_139859):
      img.qc-hb-hero-img[src][alt]  — a REAL photo, naturalWidth=1448,
      naturalHeight=1086 confirmed live. Sibling decorative arrow SVGs on
      the pill CTA are NOT this image — scoped by class, not by tag.

    Hero Description (tc_139856 — DROPPED, see below):
      p.qc-hb-hero-desc[data-qc-hb-desc] is CONFIRMED LIVE to be a PLAIN
      text field, not a rich-text field — unlike every other body-copy
      field on this page, it carries NO `qc-hb-rt` wrapper class (compare
      Section 01's `.qc-hb-rt.qc-hb-prose`, hall cards' `.qc-hb-rt
      .qc-hb-hall-desc`, the banner's `.qc-hb-rt.qc-hb-banner-body`, and
      Section 03's `.qc-hb-rt.qc-hb-intro` — all four DO carry it). Its
      current live text is a single unformatted sentence — no bold/italic/
      list/link markup exists to verify rendering of, and the field is not
      architecturally rich-text-backed in the first place. tc_139856 is
      therefore SKIPPED (live-data/architecture gap), not scripted as a
      pass — see the test's own skip reason.

    Rich-text fields that ARE genuinely `.qc-hb-rt`-wrapped (tc_139901,
    139930, 139945, 139954, 139996) all confirmed live to currently render
    ONLY plain `<p>` paragraphs (no live bold/italic/list/link instance
    exists on this page today) — this is enough to test "renders its
    markup correctly, not raw tags leaking through" (real parsed <p>
    element(s), non-empty text, no literal "<"/"&lt;" leaking into the
    rendered text) even though a bold/italic/list/link-specific assertion
    is not exercisable against today's content. tc_139930 (Guideline
    Content) is a special case: ALL FIVE accordion bodies currently render
    the identical literal placeholder copy "[Content pending] No body copy
    for this guideline exists in the approved Figma design... To be
    supplied by the Product Owner." — confirmed live via DOM probe. This is
    real, clean rich-text rendering (the placeholder text itself renders
    correctly, no tag leakage) even though the copy is a content
    placeholder rather than final guideline text; the test asserts on the
    rendering mechanism, not on the copy being final, and discloses this in
    its own docstring.

    Quick-Fact icons (tc_139869) and Checklist-Card icons (tc_139904) are
    BOTH the same CSS mask-icon pattern — `span.qc-hb-fact-icon >
    span.qc-hb-mask` / `span.qc-hb-card-icon > span.qc-hb-mask` — a
    `mask-image: url(...)` CSS custom-property icon, not an `<img>`/`<svg>`
    tag. CONFIRMED LIVE for all 4 quick facts and both Section 01 checklist
    cards: each `.qc-hb-mask` node has a real, non-"none" computed
    `mask-image` (resolving to a real `.svg` Documents & Media URL) and a
    non-zero bounding box (24x24 / 22x22). "Broken icon" for this pattern
    means `mask-image: none` or a zero-size box, not a broken `<img>` (there
    is no `src` attribute to break here at all).

    Section-index numbering badges (tc_139887): `.qc-hb-index-item
    .qc-hb-index-num` — CONFIRMED LIVE for all 4 entries: "01"/"02"/"03"/
    "04", already zero-padded two-digit strings, matching
    `data-qc-hb-index-key` 1:1.

    Section 03 "Available Halls" — CONFIRMED LIVE additions beyond what the
    original docstring above documented:
      div.qc-hb-rt.qc-hb-intro > p                    (tc_139945 — a real
        intro paragraph DOES exist: "Review hall specs, capacity, and
        select the ideal hall for your event")
      .qc-hb-hall > .qc-hb-hall-photo > img[src][alt] (tc_139951 — each of
        the 3 hall cards has a real, loaded photo; naturalWidth/Height
        confirmed >0 for all 3: Sheikh Nasser 1200x801, Grand Hall 800x533,
        Training Hall 800x533)
      .qc-hb-hall > .qc-hb-hall-text > div.qc-hb-rt.qc-hb-hall-desc > p
        (tc_139954 — each hall's own description, plain-paragraph rich
        text, same pattern as Overview Body)
      .qc-hb-hall > .qc-hb-hall-meta > span.qc-hb-cap (icon + "N Persons"
        text) (tc_139957 — a dedicated, visually-distinct badge element
        with its own icon, NOT bare inline text — confirmed for all 3
        halls, live text is "140 Persons" for each, not the task
        description's illustrative "up to N guests" wording, which is
        fine: the case is about the badge being a distinct visual element,
        not the exact copy)

    Section 04 Media Gallery + its lightbox (tc_139983, tc_140033,
    tc_140035) — a SEPARATE component (`qc-hall-gallery`, its own
    `data-qc-hg-*` attribute family) mounted inside `#qc-hb-sec-04`, not
    part of the `qc-hb-*` component the rest of the page uses:
      ul[data-qc-hg-grid] > li.qc-hall-gallery__cell
        button.qc-hall-gallery__tile[aria-label="View photo album: <Hall>"]
          img.qc-hall-gallery__img[src][alt]            (the tile's own
            thumbnail — tc_139983, CONFIRMED LIVE loaded/non-broken for
            all 3 tiles)
          span.qc-hall-gallery__tag[aria-label="Photo album: N photos"]
            (the visible photo-count badge — tc_140033)
      Clicking a tile opens a REAL lightbox (`div.qc-hall-gallery__lb-dialog
      [role="dialog"]`), confirmed live to be a genuinely separate overlay
      from the Reservation Request Form modal (both can be found by a
      broad `[role="dialog"]` query — do not conflate them):
        p.qc-hall-gallery__lb-count                     "1 / 3" style
          1-based position/total text
        figure.qc-hall-gallery__lb-figure
          img.qc-hall-gallery__lb-img[src]               (shown for a
            photo item; `display:none` for a video item)
          video.qc-hall-gallery__lb-video[controls]      (shown for a
            video item; `display:none` for a photo item — native browser
            controls, no bespoke play/seek UI, per an inline code comment
            confirmed live in the DOM)
        button.qc-hall-gallery__lb-nav--next / --prev    step through items
        button.qc-hall-gallery__lb-close[aria-label="Close image viewer"]

      CONFIRMED LIVE by stepping every item of all 3 albums (disclosed
      scripted probe, not a guess): Sheikh Nasser Bin Khaled Hall = 3 items
      (2 photos + 1 REAL playable video,
      .../hall-01-placeholder-clip.webm, confirmed `display` toggles to
      visible with a resolvable `currentSrc` on item 3/3); Grand Hall = 2
      items (2 photos, 0 videos); Training Hall = 3 items (2 photos + 1
      REAL playable video, .../hall-03-placeholder-clip.webm on item 3/3).
      Each tile's own "N photos" badge counts PHOTOS ONLY, not total media
      items — and for all 3 albums that photo-only count IS accurate (2
      photos each, badge says "2 photos" each) — tc_140033 is therefore a
      real, confirmed-live PASS, not a mismatch/bug. tc_140035 uses the
      Sheikh Nasser Bin Khaled Hall album (position 0) specifically,
      since it is one of the two albums confirmed to actually contain a
      video item.
"""

from config.settings import web_url
from core.web.base_page import BasePage

HALLS_BOOKING_PATH = "/web/qatar-chamber/halls-booking"
HOME_PATH = "/web/qatar-chamber"

# Live-confirmed hall names/order (Section 03 — see module docstring).
HALL_NAME_SHEIKH_NASSER = "Sheikh Nasser Bin Khaled Hall"
HALL_NAME_GRAND = "Grand Hall"          # the 2nd hall — used by tc_140024
HALL_NAME_TRAINING = "Training Hall"

# The reservation modal's mandatory text/select fields (excludes the
# optional "telephone" and the honeypot "website" field), keyed the same way
# the DOM's own data-qc-hbf-field values are.
MANDATORY_FIELD_NAMES = (
    "companyEnglishName",
    "companyArabicName",
    "commercialRegistrationNumber",
    "emailAddress",
    "mobileNumber",
    "reservationFromDate",
    "reservationToDate",
    "selectedHall",
)


class HallBookingPage(BasePage):
    # ---- Page chrome / hero -------------------------------------------
    BREADCRUMB_NAV = ".qc-hb-crumbs"
    BREADCRUMB_HOME_LINK = ".qc-hb-crumbs a.qc-hb-crumb:not(.is-current)"
    BREADCRUMB_SERVICES_LINK = ".qc-hb-crumbs a.qc-hb-crumb.is-current"
    EYEBROW = ".qc-hb-eyebrow"
    PAGE_TITLE = ".qc-hb-title"
    HERO_DESC = ".qc-hb-hero-desc"
    HERO_CTA = "[data-qc-hb-hero-cta]"
    QUICK_FACTS = ".qc-hb-facts"

    # ---- Sticky section index ------------------------------------------
    SECTION_INDEX = ".qc-hb-index"
    SECTION_INDEX_ITEM = ".qc-hb-index-item"
    SECTION_INDEX_ACTIVE_ITEM = ".qc-hb-index-item.is-active"

    # ---- Sections --------------------------------------------------------
    SECTION_01_OVERVIEW = "#qc-hb-sec-01"
    SECTION_02_GUIDELINES = "#qc-hb-sec-02"
    SECTION_03_HALLS = "#qc-hb-sec-03"
    SECTION_04_GALLERY = "#qc-hb-sec-04"
    BANNER = ".qc-hb-banner"

    # ---- Section 02 — Reservation Guidelines accordion ------------------
    ACC_ITEM = ".qc-hb-acc-item"
    ACC_HEAD = ".qc-hb-acc-head"
    ACC_BODY = ".qc-hb-acc-body"

    # ---- Section 03 — Available Halls -----------------------------------
    HALL_CARD = ".qc-hb-hall"
    HALL_NAME = ".qc-hb-hall-name"
    HALL_SELECT_BTN = ".qc-hb-hall-btn"

    # ---- Hero banner image (tc_139859) -----------------------------------
    HERO_IMAGE = ".qc-hb-hero-img"

    # ---- Quick facts (tc_139869) -------------------------------------------
    FACT_ITEM = ".qc-hb-facts .qc-hb-fact"
    ICON_MASK = ".qc-hb-mask"  # shared mask-icon pattern, scoped per-container below

    # ---- Section 01 — Overview body + checklist cards (tc_139901/139904) ---
    OVERVIEW_BODY = "#qc-hb-sec-01 .qc-hb-prose"
    CHECKLIST_CARD = "#qc-hb-sec-01 .qc-hb-card"

    # ---- Section 03 — intro / hall image / description / capacity ----------
    # (tc_139945 / tc_139951 / tc_139954 / tc_139957)
    HALLS_INTRO = "#qc-hb-sec-03 .qc-hb-intro"
    HALL_IMAGE = ".qc-hb-hall-photo img"      # scoped within HALL_CARD.nth(i)
    HALL_DESC = ".qc-hb-hall-desc"            # scoped within HALL_CARD.nth(i)
    HALL_CAP = ".qc-hb-cap"                   # scoped within HALL_CARD.nth(i)

    # ---- Bottom banner body (tc_139996) -------------------------------------
    BANNER_BODY = ".qc-hb-banner .qc-hb-banner-body"

    # ---- Section 04 — Media Gallery + lightbox (tc_139983/140033/140035) ---
    # A separate `qc-hall-gallery` component, its own data-qc-hg-* family —
    # see module docstring's VISUAL/RENDERING BATCH note.
    GALLERY_TILE = "#qc-hb-sec-04 .qc-hall-gallery__tile"
    GALLERY_TILE_IMG = ".qc-hall-gallery__img"   # scoped within GALLERY_TILE.nth(i)
    GALLERY_TILE_TAG = ".qc-hall-gallery__tag"   # scoped within GALLERY_TILE.nth(i)
    LIGHTBOX_DIALOG = ".qc-hall-gallery__lb-dialog"
    LIGHTBOX_COUNT = ".qc-hall-gallery__lb-count"
    LIGHTBOX_IMG = ".qc-hall-gallery__lb-img"
    LIGHTBOX_VIDEO = ".qc-hall-gallery__lb-video"
    LIGHTBOX_NEXT = ".qc-hall-gallery__lb-nav--next"
    LIGHTBOX_CLOSE = ".qc-hall-gallery__lb-close"

    # Real, parsed rich-text formatting elements a genuine WYSIWYG-authored
    # field can render — used to confirm a `qc-hb-rt` container rendered as
    # actual structured HTML (not an inert/escaped text blob). Content-
    # dependent: today's live content only ever exercises <p>; the others
    # are included so a future richer edit is picked up without code changes.
    RICH_TEXT_TAGS_SELECTOR = "p, h1, h2, h3, h4, h5, h6, ul, ol, li, strong, b, em, i, a"

    # ---- Header language toggle ------------------------------------------
    LANGUAGE_TOGGLE = "a.qc-lang-switcher"

    # ---- Reservation Request Form modal -----------------------------------
    MODAL_ROOT = "[data-qc-hbf-root]"
    MODAL_OVERLAY = "[data-qc-hbf-overlay]"
    MODAL_DIALOG = "[data-qc-hbf-dialog]"
    MODAL_TITLE = "[data-qc-hbf-title]"
    MODAL_CLOSE_X = "[data-qc-hbf-close]"  # confirmed live NOT to work — see module docstring
    MODAL_CANCEL = "[data-qc-hbf-cancel]"
    MODAL_SUBMIT = "[data-qc-hbf-submit]"
    MODAL_DONE = "[data-qc-hbf-done]"
    VIEW_FORM = '[data-qc-hbf-view="form"]'
    VIEW_SUCCESS = '[data-qc-hbf-view="success"]'
    SUCCESS_TITLE = "[data-qc-hbf-success-title]"
    SUCCESS_REFERENCE = "[data-qc-hbf-reference]"
    SELECTED_HALL_SELECT = 'select[data-qc-hbf-field="selectedHall"]'

    # ---- Navigation -------------------------------------------------------
    def _wait_for_hero_content_mounted(self, timeout: int = 8000) -> None:
        """CONFIRMED LIVE (tc_140037/tc_140040 first-run failures): this
        fragment's hero text (`.qc-hb-title` etc.) is populated by CLIENT JS
        after the document's own `domcontentloaded`/`load` event — the exact
        same class of async-mount gap `core/web/overlays.py`'s module
        docstring already documents for the announcement popup (66-98ms
        after `page.goto()` returns). A navigation reached via
        `expect_navigation(wait_until="domcontentloaded")` (menu hover-click,
        breadcrumb click, language toggle — all of which trigger a real
        top-level navigation, not an in-place SPA update) can return control
        before that mount finishes, so `page_title_text()` etc. can read an
        empty string. Poll for real content instead of a blind sleep."""
        self.page.wait_for_function(
            "() => { const el = document.querySelector('.qc-hb-title'); "
            "return !!el && el.textContent.trim().length > 0; }",
            timeout=timeout,
        )

    def open_halls_booking(self, locale: str = "en") -> "HallBookingPage":
        self.open(web_url(HALLS_BOOKING_PATH, locale=locale))
        self._wait_for_hero_content_mounted()
        return self

    def navigate_via_main_menu(self) -> "HallBookingPage":
        """Home -> "Our Services" (hover-revealed mega menu) -> "Halls
        Booking" — the literal menu path tc_140037 exercises. CONFIRMED LIVE:
        a plain `.click()` on the "Our Services" top-level item navigates
        straight to the Our Services landing page (it is itself a real link,
        not a dropdown-only trigger) instead of revealing the submenu, so
        the submenu must be reached by HOVER, not click. A raw hover+click on
        the revealed "Halls Booking" item was also observed to occasionally
        not navigate in this headless environment (no exception, just no
        navigation) unless the target item is hovered immediately before the
        click and the click is wrapped in an explicit navigation wait — both
        done below."""
        self.open(web_url(HOME_PATH))
        services_link = self.page.get_by_role("link", name="Our Services", exact=True).first
        services_link.hover()
        self.page.wait_for_timeout(500)
        hb_link = self.page.get_by_role("link", name="Halls Booking", exact=True).first
        hb_link.wait_for(state="visible")
        hb_link.hover()
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            hb_link.click()
        self._wait_for_hero_content_mounted()
        return self

    # ---- Page chrome / hero state queries ---------------------------------
    def is_hero_cta_visible(self) -> bool:
        return self.is_visible(self.HERO_CTA)

    def click_hero_cta(self) -> "HallBookingPage":
        self.click(self.HERO_CTA)
        return self

    def page_title_text(self) -> str:
        return self.text(self.PAGE_TITLE)

    def eyebrow_text(self) -> str:
        return self.text(self.EYEBROW)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB_NAV)

    def breadcrumb_text(self) -> str:
        return self.text(self.BREADCRUMB_NAV)

    def click_breadcrumb_home(self) -> None:
        # CONFIRMED LIVE: a plain click() followed by a separate
        # wait_for_load_state("domcontentloaded") call can resolve against
        # the OLD page (the click's own navigation hadn't started yet),
        # silently leaving the caller on the same URL. Wrap the click in
        # expect_navigation so it genuinely waits for the new document.
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.BREADCRUMB_HOME_LINK)

    def click_breadcrumb_services(self) -> None:
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.BREADCRUMB_SERVICES_LINK)

    def quick_facts_text(self) -> str:
        return self.text(self.QUICK_FACTS)

    def banner_text(self) -> str:
        return self.text(self.BANNER)

    def banner_reserve_button(self):
        """The bottom banner's own "Reserve a Hall" CTA — a DIFFERENT DOM
        node from HERO_CTA (there are 2 on the page; scope to the banner
        container so a click can't ambiguously hit the hero one)."""
        return self.page.locator(self.BANNER).get_by_role("button", name="Reserve a Hall")

    # ---- Sticky section index ----------------------------------------------
    def is_section_index_visible(self) -> bool:
        return self.is_visible(self.SECTION_INDEX)

    def index_item_labels(self) -> list:
        return self.page.locator(self.SECTION_INDEX_ITEM).all_inner_texts()

    def click_index_item(self, position: int, timeout: int = 6000) -> "HallBookingPage":
        """0-based position among the 4 sticky index entries (0="01
        Overview" .. 3="04 Media Gallery"). CONFIRMED LIVE (tc_140038 first
        run): the click triggers a smooth `scrollIntoView`, and the
        scroll-spy transiently marks an IN-BETWEEN section active while the
        scroll animation is still in flight (e.g. "02" on the way to "03") —
        a fixed short sleep can sample it mid-transition. Poll for the
        TARGET item to actually carry `is-active` instead of a blind sleep."""
        self.page.locator(self.SECTION_INDEX_ITEM).nth(position).click()
        self.page.wait_for_function(
            "pos => { const items = document.querySelectorAll('.qc-hb-index-item'); "
            "const el = items[pos]; return !!el && el.classList.contains('is-active'); }",
            arg=position,
            timeout=timeout,
        )
        return self

    def active_index_text(self) -> str:
        active = self.page.locator(self.SECTION_INDEX_ACTIVE_ITEM)
        return active.first.inner_text() if active.count() else ""

    def is_index_item_active(self, position: int) -> bool:
        item = self.page.locator(self.SECTION_INDEX_ITEM).nth(position)
        classes = item.get_attribute("class") or ""
        return "is-active" in classes

    def scroll_by_wheel(self, delta_y: int, steps: int = 10, step_pause_ms: int = 250) -> None:
        """Real, incremental mouse-wheel scroll — CONFIRMED LIVE (see module
        docstring) that this section index's active-item scroll-spy tracks
        genuine scroll/wheel events but does NOT react to a synthetic
        `window.scrollTo()` jump. `delta_y` is applied per step (negative
        scrolls up); never replace this with a raw JS scroll for a
        scroll-spy assertion."""
        for _ in range(steps):
            self.page.mouse.wheel(0, delta_y)
            self.page.wait_for_timeout(step_pause_ms)

    # ---- Sections / content -------------------------------------------------
    def is_section_visible(self, locator: str) -> bool:
        return self.is_visible(locator)

    # ---- Section 02 — accordion --------------------------------------------
    def accordion_item_count(self) -> int:
        return self.page.locator(self.ACC_ITEM).count()

    def click_accordion_item(self, position: int) -> "HallBookingPage":
        self.page.locator(self.ACC_ITEM).nth(position).locator(self.ACC_HEAD).click()
        return self

    def is_accordion_expanded(self, position: int) -> bool:
        head = self.page.locator(self.ACC_ITEM).nth(position).locator(self.ACC_HEAD)
        return head.get_attribute("aria-expanded") == "true"

    def is_accordion_body_hidden(self, position: int) -> bool:
        body = self.page.locator(self.ACC_ITEM).nth(position).locator(self.ACC_BODY)
        return body.get_attribute("hidden") is not None

    def accordion_body_text(self, position: int) -> str:
        return self.page.locator(self.ACC_ITEM).nth(position).locator(self.ACC_BODY).inner_text()

    def accordion_title_text(self, position: int) -> str:
        return self.page.locator(self.ACC_ITEM).nth(position).locator(self.ACC_HEAD).inner_text()

    # ---- Section 03 — hall cards --------------------------------------------
    def hall_card_count(self) -> int:
        return self.page.locator(self.HALL_CARD).count()

    def hall_name_at(self, position: int) -> str:
        return self.page.locator(self.HALL_NAME).nth(position).inner_text()

    def click_select_for_reservation(self, position: int) -> "HallBookingPage":
        """Click the Nth hall card's own "Select for reservation" button
        (0-based; position 1 = the 2nd hall, "Grand Hall" — tc_140024)."""
        self.page.locator(self.HALL_CARD).nth(position).locator(self.HALL_SELECT_BTN).click()
        return self

    # ---- Language toggle ------------------------------------------------------
    def language_toggle_label(self) -> str:
        return self.text(self.LANGUAGE_TOGGLE)

    def click_language_toggle(self) -> "HallBookingPage":
        # Same expect_navigation requirement as the breadcrumb links above —
        # this is a full-page `/c/portal/update_language?...` redirect, not
        # an SPA-style in-place update. Also re-waits for the client-JS hero
        # content to remount post-navigation (see
        # _wait_for_hero_content_mounted's own docstring — CONFIRMED LIVE to
        # matter here specifically, tc_140040's first run read an empty
        # page_title_text() right after this same click).
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.LANGUAGE_TOGGLE)
        self._wait_for_hero_content_mounted()
        return self

    def html_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ---- Reservation modal — open/close state ------------------------------
    def is_modal_open(self) -> bool:
        return self.is_visible(self.MODAL_OVERLAY)

    def wait_for_modal_open(self, timeout: int = 5000) -> None:
        self.wait_for(self.MODAL_OVERLAY, state="visible", timeout=timeout)

    def wait_for_modal_closed(self, timeout: int = 5000) -> None:
        self.wait_for(self.MODAL_OVERLAY, state="hidden", timeout=timeout)

    def close_modal(self) -> "HallBookingPage":
        """Closes the modal via Cancel — the one control CONFIRMED LIVE to
        actually work (see module docstring; the "x" icon button does not)."""
        self.click(self.MODAL_CANCEL)
        self.wait_for_modal_closed()
        return self

    def modal_title_text(self) -> str:
        return self.text(self.MODAL_TITLE)

    def modal_dialog_direction(self) -> str:
        return self.page.locator(self.MODAL_DIALOG).evaluate(
            "el => getComputedStyle(el).direction"
        )

    def is_form_view_visible(self) -> bool:
        return self.is_visible(self.VIEW_FORM)

    def is_success_view_visible(self) -> bool:
        return self.is_visible(self.VIEW_SUCCESS)

    def success_title_text(self) -> str:
        return self.text(self.SUCCESS_TITLE)

    def success_reference_text(self) -> str:
        return self.text(self.SUCCESS_REFERENCE)

    def click_done(self) -> "HallBookingPage":
        self.click(self.MODAL_DONE)
        return self

    # ---- Reservation modal — field access ------------------------------------
    def _field_locator(self, field_name: str) -> str:
        if field_name == "selectedHall":
            return f'select[data-qc-hbf-field="{field_name}"]'
        return f'input[data-qc-hbf-field="{field_name}"]'

    def _native_date_locator(self, field_name: str) -> str:
        return f'input[data-qc-hbf-native="{field_name}"]'

    def _error_locator(self, field_name: str) -> str:
        return f'p[data-qc-hbf-error="{field_name}"]'

    def selected_hall_value(self) -> str:
        return self.page.locator(self.SELECTED_HALL_SELECT).input_value()

    def selected_hall_label(self) -> str:
        return self.page.locator(f"{self.SELECTED_HALL_SELECT} option:checked").inner_text()

    def field_value(self, field_name: str) -> str:
        return self.page.locator(self._field_locator(field_name)).input_value()

    def fill_text_field(self, field_name: str, value: str) -> "HallBookingPage":
        self.type(self._field_locator(field_name), value)
        return self

    def fill_date_field(self, field_name: str, iso_date: str) -> "HallBookingPage":
        """`iso_date` in `YYYY-MM-DD` — fills the NATIVE date input, the one
        that actually drives the field (see module docstring)."""
        self.page.locator(self._native_date_locator(field_name)).fill(iso_date)
        return self

    def select_hall(self, hall_name: str) -> "HallBookingPage":
        self.select_option(self.SELECTED_HALL_SELECT, label=hall_name)
        return self

    def field_error_text(self, field_name: str) -> str:
        return self.text(self._error_locator(field_name))

    def is_field_error_visible(self, field_name: str) -> bool:
        return self.is_visible(self._error_locator(field_name))

    def wait_for_field_error(self, field_name: str, timeout: int = 5000) -> None:
        """Condition-based wait for a field's inline validation error to
        render after Submit — used instead of a blind `wait_for_timeout()`
        for the two mandatory-field-missing cases."""
        self.wait_for(self._error_locator(field_name), state="visible", timeout=timeout)

    def wait_for_success_view(self, timeout: int = 35000) -> None:
        """Condition-based wait for the success view to render after a
        valid Submit — the invisible reCAPTCHA execution time is NOT fixed:
        CONFIRMED LIVE via captured network requests that Enterprise
        sometimes completes on the first `anchor` call, and sometimes runs
        an extra `reload`/`clr` round-trip (a real additional verification
        pass) before the site's own `/o/qc-hall-booking/submit` call fires.
        Both an 8s AND a 20s timeout were observed live to time out on one
        run and then pass cleanly (well under either bound) on the very next
        identical run — genuine third-party latency variance, not a
        scripting defect. 35s gives headroom over reCAPTCHA's own widget
        budget (`execute-ms=30000`, seen in the anchor request's own query
        string) while still being a real DOM-state wait, never a blind
        sleep."""
        self.wait_for(self.VIEW_SUCCESS, state="visible", timeout=timeout)

    def fill_all_mandatory_fields(self, overrides: dict = None, exclude: tuple = ()) -> dict:
        """Fills every MANDATORY_FIELD_NAMES entry with a disposable
        `QCTEST-` value (per this project's disposable-test-data
        convention), except any field named in `exclude`. `overrides`
        replaces the default value for a named field (e.g. a real email
        address, since `emailAddress` is `type=email` and a bare
        `QCTEST-...` string is not a valid email).

        CONFIRMED LIVE (tc_140045 investigation): this form has SERVER-SIDE
        duplicate-submission detection — resubmitting the same (or very
        similar) company/email/CR-number data in a short window is silently
        delayed/blocked well past a generous wait, while an otherwise
        IDENTICAL flow with genuinely unique data reaches the success view
        in well under 15s every time. A UNIQUE per-call suffix is therefore
        baked into every default value below (not just the email) so this
        method is safe to call repeatedly across test runs/reruns without
        colliding with a prior run's disposable record — mirrors this
        project's own documented duplicate-submission handling rule
        (standards.md's Webform/Approval-Workflow Rules).

        Returns the dict of values ACTUALLY filled (post-override, minus any
        `exclude`d field) so a caller can assert against the real values
        used instead of hard-coding a literal that would go stale the next
        time this method's defaults change."""
        import time

        overrides = overrides or {}
        suffix = str(int(time.time() * 1000))[-9:]
        defaults = {
            "companyEnglishName": f"QCTEST-Hall Booking Co {suffix}",
            "companyArabicName": f"QCTEST-شركة حجز القاعات {suffix}",
            "commercialRegistrationNumber": f"QCTEST-{suffix}",
            "emailAddress": f"qctest.hallbooking.{suffix}@example.com",
            "mobileNumber": f"555{suffix[-6:]}",
            "reservationFromDate": "2027-03-10",
            "reservationToDate": "2027-03-11",
            "selectedHall": HALL_NAME_TRAINING,
        }
        filled = {}
        for field_name in MANDATORY_FIELD_NAMES:
            if field_name in exclude:
                continue
            value = overrides.get(field_name, defaults[field_name])
            if field_name == "selectedHall":
                self.select_hall(value)
            elif field_name in ("reservationFromDate", "reservationToDate"):
                self.fill_date_field(field_name, value)
            else:
                self.fill_text_field(field_name, value)
            filled[field_name] = value
        return filled

    def submit_request(self) -> "HallBookingPage":
        """Clicks Submit — no separate CAPTCHA-solve step exists to call for
        this form (invisible reCAPTCHA Enterprise; see module docstring)."""
        self.click(self.MODAL_SUBMIT)
        return self

    # =========================================================================
    # VISUAL/RENDERING BATCH (2026-09-16) — state-query helpers only, no
    # asserts (Page Objects expose state; tests assert). See module docstring's
    # "VISUAL/RENDERING BATCH" section for the live-confirmed DOM evidence.
    # =========================================================================

    # ---- Hero banner image (tc_139859) -------------------------------------
    def hero_image_state(self) -> dict:
        img = self.page.locator(self.HERO_IMAGE)
        return self._image_state(img)

    # ---- Quick-fact icons (tc_139869) ---------------------------------------
    def fact_count(self) -> int:
        return self.page.locator(self.FACT_ITEM).count()

    def fact_icon_state(self, position: int) -> dict:
        mask = self.page.locator(self.FACT_ITEM).nth(position).locator(self.ICON_MASK)
        return self._mask_icon_state(mask)

    # ---- Section 01 — Overview body (tc_139901) -----------------------------
    def overview_body_state(self) -> dict:
        return self._rich_text_state(self.page.locator(self.OVERVIEW_BODY))

    # ---- Section 01 — Checklist card icons (tc_139904) ----------------------
    def checklist_card_count(self) -> int:
        return self.page.locator(self.CHECKLIST_CARD).count()

    def checklist_card_icon_state(self, position: int) -> dict:
        mask = self.page.locator(self.CHECKLIST_CARD).nth(position).locator(self.ICON_MASK)
        return self._mask_icon_state(mask)

    # ---- Section-index numbering badges (tc_139887) -------------------------
    def index_item_number_text(self, position: int) -> str:
        return self.page.locator(self.SECTION_INDEX_ITEM).nth(position).locator(".qc-hb-index-num").inner_text()

    # ---- Section 02 — Guideline (accordion) content rich text (tc_139930) --
    def accordion_body_state(self, position: int) -> dict:
        body = self.page.locator(self.ACC_ITEM).nth(position).locator(self.ACC_BODY)
        return self._rich_text_state(body)

    # ---- Section 03 — Halls intro rich text (tc_139945) ---------------------
    def halls_intro_state(self) -> dict:
        return self._rich_text_state(self.page.locator(self.HALLS_INTRO))

    # ---- Section 03 — Hall image (tc_139951) --------------------------------
    def hall_image_state(self, position: int) -> dict:
        img = self.page.locator(self.HALL_CARD).nth(position).locator(self.HALL_IMAGE)
        return self._image_state(img)

    # ---- Section 03 — Hall description rich text (tc_139954) ----------------
    def hall_description_state(self, position: int) -> dict:
        desc = self.page.locator(self.HALL_CARD).nth(position).locator(self.HALL_DESC)
        return self._rich_text_state(desc)

    # ---- Section 03 — Capacity badge (tc_139957) -----------------------------
    def hall_capacity_badge_text(self, position: int) -> str:
        return self.page.locator(self.HALL_CARD).nth(position).locator(self.HALL_CAP).inner_text()

    def is_hall_capacity_badge_distinct(self, position: int) -> bool:
        """True when the capacity indicator is its own visually-distinct
        badge element (a dedicated `.qc-hb-cap` span carrying its own icon
        child), not bare inline text indistinguishable from surrounding
        copy — the adapted assertion for tc_139957."""
        badge = self.page.locator(self.HALL_CARD).nth(position).locator(self.HALL_CAP)
        has_icon = badge.locator(".qc-hb-cap-icon").count() > 0
        return badge.is_visible() and has_icon

    # ---- Bottom banner body rich text (tc_139996) ---------------------------
    def banner_body_state(self) -> dict:
        return self._rich_text_state(self.page.locator(self.BANNER_BODY))

    # ---- Section 04 — Media Gallery tiles (tc_139983 / tc_140033) ----------
    def gallery_tile_count(self) -> int:
        return self.page.locator(self.GALLERY_TILE).count()

    def gallery_tile_thumbnail_state(self, position: int) -> dict:
        img = self.page.locator(self.GALLERY_TILE).nth(position).locator(self.GALLERY_TILE_IMG)
        return self._image_state(img)

    def gallery_tile_photo_count_label(self, position: int) -> str:
        """The tile's visible photo-count badge text/aria-label, e.g.
        "Photo album: 2 photos" — tc_140033's displayed indicator."""
        tag = self.page.locator(self.GALLERY_TILE).nth(position).locator(self.GALLERY_TILE_TAG)
        return tag.get_attribute("aria-label") or tag.inner_text()

    # ---- Section 04 — Lightbox (tc_140033 / tc_140035) -----------------------
    def open_gallery_tile(self, position: int) -> "HallBookingPage":
        self.page.locator(self.GALLERY_TILE).nth(position).scroll_into_view_if_needed()
        self.click_gallery_tile(position)
        self.wait_for(self.LIGHTBOX_DIALOG, state="visible")
        return self

    def click_gallery_tile(self, position: int) -> None:
        self.page.locator(self.GALLERY_TILE).nth(position).click()

    def close_lightbox(self) -> "HallBookingPage":
        self.click(self.LIGHTBOX_CLOSE)
        self.wait_for(self.LIGHTBOX_DIALOG, state="hidden")
        return self

    def lightbox_total_count(self) -> int:
        """Parses the lightbox's own "N / TOTAL" position text and returns
        TOTAL — the real number of media items in the open album, used to
        independently verify a tile's displayed photo-count badge rather
        than trusting it."""
        text = self.text(self.LIGHTBOX_COUNT)
        return int(text.split("/")[-1].strip())

    def current_lightbox_item(self) -> tuple:
        """(kind, src) for whichever of the image/video figure elements is
        CURRENTLY the visible one — the two share one figure slot, toggled
        by `display` (see module docstring). `kind` is "photo", "video", or
        "unknown" if neither resolves (a genuine rendering defect)."""
        return self.page.evaluate(
            "() => {"
            "  const img = document.querySelector('" + self.LIGHTBOX_IMG + "');"
            "  const vid = document.querySelector('" + self.LIGHTBOX_VIDEO + "');"
            "  const imgVisible = img && getComputedStyle(img).display !== 'none';"
            "  const vidVisible = vid && getComputedStyle(vid).display !== 'none';"
            "  if (vidVisible) return ['video', vid.currentSrc || vid.getAttribute('src') || ''];"
            "  if (imgVisible) return ['photo', img.getAttribute('src') || ''];"
            "  return ['unknown', ''];"
            "}"
        )

    def advance_lightbox(self) -> None:
        """Clicks Next and waits for the position counter to actually
        advance before returning — condition-based, never a blind sleep."""
        current = self.text(self.LIGHTBOX_COUNT)
        current_position = int(current.split("/")[0].strip())
        self.click(self.LIGHTBOX_NEXT)
        expected_prefix = f"{current_position + 1} /"
        self.page.wait_for_function(
            "expected => { const el = document.querySelector('" + self.LIGHTBOX_COUNT + "'); "
            "return !!el && el.textContent.trim().startsWith(expected); }",
            arg=expected_prefix,
            timeout=5000,
        )

    def find_and_show_video_item(self, position: int) -> bool:
        """Opens the Nth gallery tile's lightbox and steps through its
        items until a video item is shown, LEAVING the lightbox open and
        positioned on it (does not close). Returns True if a video item
        was found, False if the album contains no video (a genuine,
        reportable live-data gap, not a broken test)."""
        self.open_gallery_tile(position)
        total = self.lightbox_total_count()
        for i in range(total):
            kind, _ = self.current_lightbox_item()
            if kind == "video":
                return True
            if i < total - 1:
                self.advance_lightbox()
        return False

    def collect_album_media(self, position: int) -> list:
        """Opens the Nth gallery tile's lightbox, steps through EVERY item
        via Next, records a `(kind, src)` tuple per item in display order,
        closes the lightbox, and returns the list — the real, live media
        breakdown of that album. Used to verify a tile's displayed
        photo-count badge is accurate (tc_140033) and to reach a real video
        item for a playability check (tc_140035) without hard-coding a
        position that could go stale if the album's content changes."""
        self.open_gallery_tile(position)
        total = self.lightbox_total_count()
        items = []
        for i in range(total):
            items.append(self.current_lightbox_item())
            if i < total - 1:
                self.advance_lightbox()
        self.close_lightbox()
        return items

    def is_lightbox_video_playable(self) -> bool:
        """True when the CURRENTLY-shown lightbox item is a real, loadable
        video — a resolvable `currentSrc`/`src` and enough buffered
        metadata (`readyState >= HAVE_METADATA` with a real `duration`) to
        prove the source is genuinely playable, without requiring an actual
        user-gesture-gated `.play()` call in a headless session. Adapted
        assertion for tc_140035 ("capable of playing... not broken")."""
        video = self.page.locator(self.LIGHTBOX_VIDEO)
        if not video.is_visible():
            return False
        video.evaluate("v => v.load ? v.load() : null")
        try:
            self.page.wait_for_function(
                "() => { const v = document.querySelector('" + self.LIGHTBOX_VIDEO + "'); "
                "return !!v && v.readyState >= 1 && !isNaN(v.duration) && v.duration > 0; }",
                timeout=10000,
            )
        except Exception:
            return False
        state = video.evaluate(
            "v => ({ src: v.currentSrc || v.getAttribute('src') || '', "
            "readyState: v.readyState, duration: v.duration, networkState: v.networkState })"
        )
        return bool(state["src"]) and state["readyState"] >= 1 and state["duration"] > 0 and state["networkState"] != 3

    # ---- Shared visual-check primitives --------------------------------------
    def _image_state(self, img_locator) -> dict:
        """Common `<img>` rendering-health snapshot: real `src`, browser-
        confirmed `complete`+non-zero natural dimensions (a proper load, not
        a broken/placeholder icon), and the rendered bounding box."""
        if img_locator.count() == 0:
            return {"exists": False, "src": "", "loaded": False, "width": 0, "height": 0}
        src = img_locator.get_attribute("src") or ""
        loaded = img_locator.evaluate("el => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0")
        box = img_locator.bounding_box()
        return {
            "exists": True,
            "src": src,
            "loaded": bool(loaded),
            "width": box["width"] if box else 0,
            "height": box["height"] if box else 0,
        }

    def _mask_icon_state(self, mask_locator) -> dict:
        """Common CSS mask-icon rendering-health snapshot (the
        `.qc-hb-mask` pattern — see module docstring): a real, non-"none"
        computed `mask-image` and a non-zero rendered box, the equivalent
        of "not a broken image" for an icon with no `src` attribute."""
        if mask_locator.count() == 0:
            return {"exists": False, "mask_image": "none", "width": 0, "height": 0}
        box = mask_locator.bounding_box()
        mask_image = mask_locator.evaluate(
            "el => getComputedStyle(el).maskImage || getComputedStyle(el).webkitMaskImage || 'none'"
        )
        return {
            "exists": True,
            "mask_image": mask_image,
            "width": box["width"] if box else 0,
            "height": box["height"] if box else 0,
        }

    def _rich_text_state(self, rt_locator) -> dict:
        """Common rich-text-container rendering-health snapshot: visible,
        non-empty rendered text, no literal raw-tag leakage into that text
        (a CMS field that stored escaped HTML would show literal "<p>"/
        "&lt;" characters to a visitor instead of a real paragraph), and at
        least one genuinely PARSED formatting element (see
        RICH_TEXT_TAGS_SELECTOR) proving the browser rendered real HTML."""
        if rt_locator.count() == 0:
            return {"exists": False, "visible": False, "inner_text": "", "formatted_element_count": 0, "has_raw_tag_leak": True}
        inner_text = rt_locator.inner_text()
        return {
            "exists": True,
            "visible": rt_locator.is_visible(),
            "inner_text": inner_text,
            "formatted_element_count": rt_locator.locator(self.RICH_TEXT_TAGS_SELECTOR).count(),
            "has_raw_tag_leak": ("<" in inner_text) or ("&lt;" in inner_text),
        }

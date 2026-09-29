"""
web/pages/advertisements/advertisements_page.py — AdvertisementsPage +
AdvertisementRequestModal, for PBI 131062 ("QC - Insights & Media - 009 -
Advertisements"), single public page at
`/web/qatar-chamber/advertisements` (AR: `/ar/web/qatar-chamber/advertisements`)
— hero + "Advertising rate cards" section (3 published rate cards) + one
shared "Book Now" Request modal (one field set — unlike media_dept_request's
3 differently-shaped forms, this page has exactly one modal shape).

Locators — CLI-first extraction log, confirmed live 2026-09-22 against
https://qcdev.ihorizons.com/web/qatar-chamber/advertisements at the
framework's default 1920x1080 viewport:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/advertisements
    -> returns only the shared header/footer nav candidates (role-based).
       The page body (hero/cards/modal) is composed of plain divs/buttons
       with no accessible-name/role surface — same class of gap already
       documented on podcast_page.py / media_dept_request_page.py. Resolved
       the same way: `page.eval_on_selector_all('[class*=qc-]', ...)` to
       harvest the real class tree, then targeted `inner_html()`/attribute
       reads to confirm field ids, maxlengths, and error copy.

    The real URL was NOT guessed — confirmed by a scripted <a> harvest of
    the live header's "Media Center" flyout against /web/home: the flyout's
    "Advertisements" link resolves to
    https://qcdev.ihorizons.com/web/qatar-chamber/advertisements (same
    technique already used for media_dept_request_page.py's URL discovery).

Real DOM structure confirmed live (2026-09-22):

    header.qc-adv-hero (shell qc-adv qc-adv-shell qc-adv-hero-shell)
        nav.qc-adv-crumbs
            a.qc-adv-crumb (Home) / span.qc-adv-crumb-sep /
            span.qc-adv-crumb.is-current ("Insights & Media" — CONFIRMED
                LIVE: same "middle/only crumb reads the PARENT hub label,
                not the page's own title" quirk already documented on
                podcast_page.py and media_dept_request_page.py's crumbs;
                only 2 crumb items render total, matching case 142398's own
                stated 'Home › Insights & Media')
        .qc-adv-hero-grid > .qc-adv-hero-copy (p.qc-adv-hero-eyebrow
            "Insights & Media" / h1.qc-adv-hero-title "Advertisements" /
            p.qc-adv-hero-desc) + .qc-adv-hero-art > img.qc-adv-hero-img

    section.qc-adv-body
        .qc-adv-section-head (p.qc-adv-section-eyebrow "Advertising rate
            cards" / h2.qc-adv-section-title "Choose the right placement" /
            p.qc-adv-section-desc)
        div.qc-adv-cards > article.qc-adv-card (x3, CONFIRMED LIVE):
            0: category "Website", title "Digital Banner", price
               "QAR 5,000 /month", cta "Book Now" (outlined — no
               `is-solid`/`is-featured` class)
            1: class "qc-adv-card is-featured" — CONFIRMED LIVE the
               `.qc-adv-card-category` element for THIS card renders the
               literal text "Most Popular" IN PLACE OF a category label
               (no separate promo-label element exists alongside it) —
               title "Magazine Full Page", price "QAR 12,000 /issue", cta
               "Book Now" carries `is-solid` (filled/primary), matching
               case 142401's expectations exactly (highlighted style +
               'Most Popular' label + filled button), just implemented as
               one shared slot rather than two elements.
            2: category "Directory", title "Directory Listing", price
               "QAR 3,000 /year", cta "Book Now" (outlined)
            Each card: .qc-adv-card-iconbox > img.qc-adv-card-icon,
            .qc-adv-card-desc, ul.qc-adv-card-features >
            li.qc-adv-card-feature > span.qc-adv-card-check (svg check) +
            text, button.qc-adv-card-cta ("Book Now").
        .qc-adv-empty (empty-grid-state message — NOT exercised this batch,
            see test module docstring's skip list: the real live page
            always has 3 published cards and no Control_Panel access this
            batch to temporarily unpublish them all).

    Request modal (`.qc-adv-modal`), mounted on-demand by a card's "Book
    Now" click:
        .qc-adv-modal-backdrop / .qc-adv-modal-panel[role=dialog]
            button.qc-adv-modal-close[data-qc-adv-modal-close] (X, aria-label
                "Close" — CONFIRMED LIVE clicking it closes the modal
                IMMEDIATELY with no confirmation prompt, even with unsaved
                data already entered — see "Confirmed mismatches" below)
            .qc-adv-modal-head (icon + .qc-adv-modal-eyebrow "Advertisement
                request" / .qc-adv-modal-title "Tell us what you need")
            .qc-adv-modal-lead ("Submit your preferred format and date.
                Qatar Chamber will review the request and coordinate the
                next steps offline.")
            form.qc-adv-form > .qc-adv-form-grid: one .qc-adv-field per
                field (label[for=qc-adv-<fieldId>] with a trailing
                span.qc-adv-req="*" on every MANDATORY field only — CONFIRMED
                LIVE Additional Notes carries no asterisk, matching case
                142413 exactly) + control (id=qc-adv-<fieldId>) + error
                <p id=qc-adv-<fieldId>-error class="qc-adv-field-error">
                (CONFIRMED LIVE: on a real validation failure the field's
                wrapping `.qc-adv-field` gains a `has-error` class and the
                control gets `aria-invalid="true"` alongside the error text
                rendering directly beneath the field, inside the SAME
                `.qc-adv-field` wrapper — satisfies case 142414's "not only
                a global banner" ask; a second, generic
                `[data-qc-adv-form-error]` banner ALSO renders, reading
                "Please check the highlighted fields.")
            .qc-adv-captcha[data-qc-adv-captcha-field] > div[data-qc-recaptcha]
                (real Google reCAPTCHA ENTERPRISE, size=invisible — same
                widget class already documented on media_dept_request_page.py.
                Live-probed 2026-09-22: a real headless-Chromium submit with
                fully valid data completed end-to-end — `.qc-adv-done`
                un-hid with a real reference "ADV-00000001" within ~10s of
                clicking Submit, no bypass/env flag needed. See test module
                docstring for the CAPTCHA-skip accounting.)
            input.qc-adv-hp[name=_hp] (honeypot, never filled by real tests)
            [data-qc-adv-form-error] (generic submit-failure banner)
            .qc-adv-form-actions > button.qc-adv-btn-ghost[data-qc-adv-form-cancel]
                ("Cancel"), button.qc-adv-btn-solid[data-qc-adv-form-submit]
                ("Submit Request", type=submit, never `disabled` —
                confirmed live per case 142407)
        .qc-adv-done[data-qc-adv-done][hidden] (success state) >
            .qc-adv-done-title ("Request received"), .qc-adv-done-body
            ("Qatar Chamber will review your request and coordinate the
            next steps with you offline." — CONFIRMED LIVE MISMATCH vs.
            case 142436's own stated bilingual wording, see below),
            .qc-adv-done-ref > .qc-adv-done-ref-value (real stored
            bookingReference, format "ADV-00000001"),
            button.qc-adv-btn-solid[data-qc-adv-done-close] ("Done")

    Field map (id suffix after "qc-adv-", label, type, real live
    maxlength/attrs — confirmed via inner_html()/JS-property reads):
        company_name -> companyName (text, maxlength=200, label "Company Name*")
        contact_person -> contactPerson (text, maxlength=150, label "Contact Person*")
        email -> email (email, maxlength=150, label "Email*")
        mobile_number -> mobileNumber (tel, maxlength=20, "+974" fixed prefix
            span alongside the input, placeholder "+974 xxxx xxxx" — the
            input itself holds only the national number, label "Mobile Number*")
        ads_type -> adsType (select, the ONLY field with a native HTML
            `required` attribute — CONFIRMED LIVE; options
            ["", "Select ads Type"], ["websiteBanner", "Digital Banner"],
            ["magazinePage", "Magazine Full Page"],
            ["directoryListing", "Directory Listing"] — see "Confirmed
            mismatches" below for the option-LABEL vs. case-text gap.
            Pre-selected per the launching card: card 0 -> "websiteBanner",
            card 1 -> "magazinePage", card 2 -> "directoryListing". Label
            "Ads Type*")
        preferred_date -> preferredDate (date, `min` CONFIRMED LIVE set to
            the CURRENT date server-side each day — "past date"/"today" are
            computed at test run time via `datetime.date.today()`, never a
            hardcoded literal, label "Preferred Date*")
        additional_notes -> additionalNotes (textarea, maxlength=2000,
            OPTIONAL — no asterisk on its label, confirmed live both by the
            DOM and by a real no-notes submission succeeding)
        upload_artwork -> uploadArtwork (button.qc-adv-drop +
            hidden .qc-adv-file-input[accept=".pdf,application/pdf"],
            MANDATORY — carries the `*` indicator; drop zone shows
            instructional text + "(max.10MB)" copy, filename echoed in
            .qc-adv-drop-file once a file is attached)

    Live validation error strings (confirmed via real reject/invalid probes):
        required (every mandatory field): "This field is required."
        invalid email: "Enter a valid email address."
        past date: "Choose today’s date or a later one." (curly apostrophe
            as shipped, used exactly as observed)
        unsupported attachment type: "Attach a PDF file."
        oversized attachment: "The file must be 10 MB or smaller."
        generic submit-blocked banner: "Please check the highlighted fields."

    All 4 length-limited fields' real live `maxlength` EXACTLY matches this
    batch's own case-stated limits (Company Name 200, Contact Person 150,
    Mobile Number 20, Additional Notes 2000) — CONFIRMED LIVE via a real
    over-length `fill()` on each: the typed value is truncated to the exact
    cap before it ever reaches the DOM (a 250-char fill into Company Name's
    maxlength=200 control reads back at exactly 200 chars). This differs
    from PBI 131061's batch (where several fields' live maxlength was
    LOOSER than the case's stated limit) — here the "exceeds limit" state
    is UNREACHABLE via the real UI for all 4 fields, so those 4 cases
    (142543/142547/142556/142565) assert the real, observed truncation
    enforcement mechanism, not a submit-time validation error — see the
    test module docstring's "Field length-limit findings" section.

    CONFIRMED LIVE PRODUCT GAPS (disclosed, not silently normalized — see
    the corresponding tests, which are scripted to assert the QA case's own
    real expected result and are EXPECTED TO FAIL, per
    automation-standards.md's Result-integrity section):
      - Contact Person's "letters only" rule (case 142549) is NOT enforced
        live: submitting "Ahmed123!" produces no field error and the
        request submits successfully end-to-end (probed with a full valid
        submission carrying this value — reference ADV-00000002 was
        issued).
      - Mobile Number's format rule (case 142555) is NOT enforced live:
        submitting "ABCDEFGH" produces no field error and the same probe
        above submitted successfully with this value too.
      - The Ads Type dropdown's real option LABELS read "Digital Banner" /
        "Magazine Full Page" / "Directory Listing" — cases 142403/142436
        (and 142557's own option-list wording "Website Banner, Magazine
        page and Directory Listing") state different label text
        ("Website Banner" / "Magazine page"). The underlying VALUE/mapping
        is correct (card 0 -> the option now labelled "Digital Banner" is
        still the one pre-selected for the Digital Banner card), only the
        visible label text differs from the case's own wording.
      - Closing/cancelling the modal with unsaved data (case 142442) shows
        NO confirmation prompt live — both the (X) close icon and the
        Cancel button close the modal immediately, discarding any entered
        data with no "are you sure" step. Probed directly: filling Company
        Name then clicking either control leaves the modal not-visible with
        no intervening dialog.
      - The real success-state copy ("Request received" /
        "Qatar Chamber will review your request and coordinate the next
        steps with you offline.") does not match case 142436's own stated
        bilingual confirmation text ("Thank you for your interest in
        advertising with Qatar Chamber. Your booking request has been
        received and our team will contact you shortly.") — the booking
        itself still succeeds and issues a real reference number.
"""

from config.settings import web_url
from core.web.base_page import BasePage

ADVERTISEMENTS_PATH = "/web/qatar-chamber/advertisements"

# 0-based card index -> its mapped Ads Type <option value>, for readability
# at call sites (open_request_form(CARD_DIGITAL_BANNER) reads better than a
# bare 0).
CARD_DIGITAL_BANNER = 0
CARD_MAGAZINE_FULL_PAGE = 1
CARD_DIRECTORY_LISTING = 2

# field-key -> real DOM id suffix (after "qc-adv-").
FIELD_MAP = {
    "company_name": "companyName",
    "contact_person": "contactPerson",
    "email": "email",
    "mobile_number": "mobileNumber",
    "ads_type": "adsType",
    "preferred_date": "preferredDate",
    "additional_notes": "additionalNotes",
    "upload_artwork": "uploadArtwork",
}

# field-keys that are <select> controls (select_option, not type()).
SELECT_FIELDS = {"ads_type"}
# field-keys that are <textarea> controls.
TEXTAREA_FIELDS = {"additional_notes"}
# field-keys that are <input type=date> controls.
DATE_FIELDS = {"preferred_date"}
# field-key -> its confirmed-live maxlength (matches every case's own stated
# limit EXACTLY on this batch — see module docstring). The over-length state
# is unreachable via the real UI; these are asserted as truncation-
# enforcement, not a submit-time validation error.
EXACT_MAXLENGTH_FIELDS = {
    "company_name": 200,
    "contact_person": 150,
    "mobile_number": 20,
    "additional_notes": 2000,
}

REQUIRED_ERROR = "This field is required."
INVALID_EMAIL_ERROR = "Enter a valid email address."
PAST_DATE_ERROR = "Choose today’s date or a later one."
UNSUPPORTED_FILE_ERROR = "Attach a PDF file."
OVERSIZED_FILE_ERROR = "The file must be 10 MB or smaller."
GENERIC_FORM_ERROR = "Please check the highlighted fields."

# Real live Ads Type <option> labels (see module docstring's "Confirmed
# mismatches" — several cases state different label wording).
ADS_TYPE_OPTIONS_LIVE = {
    "websiteBanner": "Digital Banner",
    "magazinePage": "Magazine Full Page",
    "directoryListing": "Directory Listing",
}


class AdvertisementsPage(BasePage):
    HERO = ".qc-adv-hero"
    HERO_EYEBROW = ".qc-adv-hero-eyebrow"
    HERO_TITLE = ".qc-adv-hero-title"
    HERO_DESC = ".qc-adv-hero-desc"
    HERO_IMG = ".qc-adv-hero-img"
    CRUMB = ".qc-adv-crumb"
    CRUMB_CURRENT = ".qc-adv-crumb.is-current"
    CRUMB_HOME_LINK = "a.qc-adv-crumb"

    SECTION_EYEBROW = ".qc-adv-section-eyebrow"
    SECTION_TITLE = ".qc-adv-section-title"
    SECTION_DESC = ".qc-adv-section-desc"

    CARD = ".qc-adv-card"
    CARD_FEATURED = ".qc-adv-card.is-featured"
    CARD_ICON = ".qc-adv-card-icon"
    CARD_CATEGORY = ".qc-adv-card-category"
    CARD_TITLE = ".qc-adv-card-title"
    CARD_PRICE = ".qc-adv-card-price"
    CARD_DESC = ".qc-adv-card-desc"
    CARD_FEATURE = ".qc-adv-card-feature"
    CARD_CTA = ".qc-adv-card-cta"
    EMPTY = ".qc-adv-empty"

    MODAL_PANEL = ".qc-adv-modal-panel"

    # ---- Navigation ---------------------------------------------------
    def open_advertisements(self, locale: str = "en") -> "AdvertisementsPage":
        self.open(web_url(ADVERTISEMENTS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_advertisements_anonymous(self, locale: str = "en") -> "AdvertisementsPage":
        self.open_anonymous(web_url(ADVERTISEMENTS_PATH, locale=locale))
        return self

    # ---- Hero / crumbs --------------------------------------------------
    def hero_eyebrow(self) -> str:
        return self.text(self.HERO_EYEBROW)

    def hero_title(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_desc(self) -> str:
        return self.text(self.HERO_DESC)

    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def is_hero_image_visible(self) -> bool:
        return self.is_visible(self.HERO_IMG)

    def crumb_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.CRUMB).all_inner_texts()]

    def click_crumb_home(self) -> None:
        self.click(self.CRUMB_HOME_LINK)

    # ---- Section header --------------------------------------------------
    def section_eyebrow(self) -> str:
        return self.text(self.SECTION_EYEBROW)

    def section_title(self) -> str:
        return self.text(self.SECTION_TITLE)

    def section_desc(self) -> str:
        return self.text(self.SECTION_DESC)

    # ---- Cards ----------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def featured_card_count(self) -> int:
        return self.page.locator(self.CARD_FEATURED).count()

    def card_category(self, index: int) -> str:
        return self.page.locator(self.CARD_CATEGORY).nth(index).inner_text()

    def card_title(self, index: int) -> str:
        return self.page.locator(self.CARD_TITLE).nth(index).inner_text()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_text_contents()

    def card_price(self, index: int) -> str:
        return self.page.locator(self.CARD_PRICE).nth(index).inner_text()

    def card_desc(self, index: int) -> str:
        return self.page.locator(self.CARD_DESC).nth(index).inner_text()

    def card_feature_count(self, index: int) -> int:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_FEATURE).count()

    def is_card_featured(self, index: int) -> bool:
        cls = self.page.locator(self.CARD).nth(index).get_attribute("class") or ""
        return "is-featured" in cls

    def card_cta_classes(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_CTA).get_attribute("class") or ""

    def is_card_icon_visible(self, index: int) -> bool:
        return self.page.locator(self.CARD_ICON).nth(index).is_visible()

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def empty_state_text(self) -> str:
        return self.text(self.EMPTY)

    def book_now_button(self, index: int):
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_CTA)

    def book_now_outline_style(self, index: int) -> str:
        return self.book_now_button(index).evaluate(
            "el => { const s = getComputedStyle(el); "
            "return s.outlineStyle + '|' + s.outlineWidth; }"
        )

    def focus_book_now_via_tab(self, index: int, max_presses: int = 60) -> bool:
        target_handle = self.book_now_button(index)
        for _ in range(max_presses):
            if target_handle.evaluate("el => el === document.activeElement"):
                return True
            self.press_key("Tab")
        return target_handle.evaluate("el => el === document.activeElement")

    def open_request_form(self, card_index: int) -> "AdvertisementRequestModal":
        self.book_now_button(card_index).click()
        self.wait_for(self.MODAL_PANEL)
        return AdvertisementRequestModal(self.page)


class AdvertisementRequestModal(BasePage):
    """One modal component for the Advertisement Request form. Unlike
    media_dept_request_page.py's 3-form-shapes-per-shell design, this page
    has exactly one field set regardless of which card's Book Now opened
    it — only the Ads Type pre-selection differs per launching card."""

    MODAL_PANEL = ".qc-adv-modal-panel"
    MODAL_EYEBROW = ".qc-adv-modal-eyebrow"
    MODAL_TITLE = ".qc-adv-modal-title"
    MODAL_LEAD = ".qc-adv-modal-lead"
    MODAL_CLOSE = "[data-qc-adv-modal-close]"
    FORM = ".qc-adv-form"
    CAPTCHA_WIDGET = "[data-qc-recaptcha]"
    FORM_ERROR = "[data-qc-adv-form-error]"
    SUBMIT_BTN = "[data-qc-adv-form-submit]"
    CANCEL_BTN = "[data-qc-adv-form-cancel]"

    DONE_PANEL = "[data-qc-adv-done]"
    DONE_TITLE = ".qc-adv-done-title"
    DONE_BODY = ".qc-adv-done-body"
    DONE_REF = "[data-qc-adv-done-ref]"
    DONE_CLOSE_BTN = "[data-qc-adv-done-close]"

    ATTACHMENT_DROP_BTN = "#qc-adv-uploadArtwork"
    ATTACHMENT_FILE_INPUT = ".qc-adv-file-input"
    ATTACHMENT_FILENAME = ".qc-adv-drop-file"

    REQUIRED_LABEL_MARK = ".qc-adv-req"

    def _control_locator(self, field_key: str) -> str:
        return f"#qc-adv-{FIELD_MAP[field_key]}"

    def _error_locator(self, field_key: str) -> str:
        return f"#qc-adv-{FIELD_MAP[field_key]}-error"

    # ---- Fill / read ----------------------------------------------------
    def fill_field(self, field_key: str, value: str) -> "AdvertisementRequestModal":
        if field_key in SELECT_FIELDS:
            self.select_option(self._control_locator(field_key), value=value)
        else:
            self.type(self._control_locator(field_key), value)
        return self

    def fill_form(self, data: dict) -> "AdvertisementRequestModal":
        for key, value in data.items():
            if key == "upload_artwork":
                self.upload_attachment(value)
            else:
                self.fill_field(key, value)
        return self

    def field_value(self, field_key: str) -> str:
        return self.page.locator(self._control_locator(field_key)).input_value()

    def field_error_text(self, field_key: str) -> str:
        return self.text(self._error_locator(field_key))

    def is_field_error_visible(self, field_key: str) -> bool:
        return self.is_visible(self._error_locator(field_key))

    def is_field_marked_invalid(self, field_key: str) -> bool:
        wrapper_classes = self.page.locator(self._control_locator(field_key)).evaluate(
            "el => el.closest('.qc-adv-field').className"
        )
        return "has-error" in wrapper_classes

    def is_field_label_mandatory(self, field_key: str) -> bool:
        control_id = f"qc-adv-{FIELD_MAP[field_key]}"
        label = self.page.locator(f"label[for='{control_id}']")
        return label.locator(self.REQUIRED_LABEL_MARK).count() > 0

    def ads_type_option_values(self) -> list:
        return self.page.eval_on_selector_all(
            f"{self._control_locator('ads_type')} option",
            "els => els.map(e => e.value).filter(v => v)",
        )

    def ads_type_option_labels(self) -> list:
        return self.page.eval_on_selector_all(
            f"{self._control_locator('ads_type')} option",
            "els => els.map(e => e.innerText).filter(v => v)",
        )

    def upload_attachment(self, file_path: str) -> "AdvertisementRequestModal":
        self.upload_file(self.ATTACHMENT_FILE_INPUT, file_path)
        return self

    def attachment_filename(self) -> str:
        return self.text(self.ATTACHMENT_FILENAME)

    # ---- Modal chrome -----------------------------------------------------
    def is_open(self) -> bool:
        return self.is_visible(self.MODAL_PANEL)

    def eyebrow(self) -> str:
        return self.text(self.MODAL_EYEBROW)

    def title(self) -> str:
        return self.text(self.MODAL_TITLE)

    def lead_text(self) -> str:
        return self.text(self.MODAL_LEAD)

    def is_captcha_widget_visible(self) -> bool:
        """Checks DOM presence (`count() > 0`), not Playwright visibility —
        this is a real Google reCAPTCHA Enterprise widget with size=invisible
        by design (auto-executes on Submit, no visible checkbox ever
        renders), confirmed live 2026-09-23 and consistent with this same
        module's tc_142571, which is correctly SKIPPED for exactly this
        reason. A strict visibility check would always be False for a
        correctly-configured invisible widget; presence in the DOM is the
        correct, honest signal that the widget is wired up (HEALED
        2026-09-23)."""
        return self.page.locator(self.CAPTCHA_WIDGET).count() > 0

    def is_submit_enabled(self) -> bool:
        return self.page.locator(self.SUBMIT_BTN).is_enabled()

    def form_error_text(self) -> str:
        return self.text(self.FORM_ERROR)

    def close(self) -> "AdvertisementRequestModal":
        self.click(self.MODAL_CLOSE)
        return self

    def submit(self) -> "AdvertisementRequestModal":
        self.click(self.SUBMIT_BTN)
        return self

    def cancel(self) -> "AdvertisementRequestModal":
        self.click(self.CANCEL_BTN)
        return self

    # ---- Success state ----------------------------------------------------
    def wait_for_done(self, timeout: int = 20000) -> "AdvertisementRequestModal":
        self.wait_for(self.DONE_PANEL, timeout=timeout)
        return self

    def is_done_visible(self) -> bool:
        return self.is_visible(self.DONE_PANEL)

    def done_title(self) -> str:
        return self.text(self.DONE_TITLE)

    def done_body(self) -> str:
        return self.text(self.DONE_BODY)

    def reference_number(self) -> str:
        return self.text(self.DONE_REF)

    def close_done(self) -> "AdvertisementRequestModal":
        self.click(self.DONE_CLOSE_BTN)
        return self

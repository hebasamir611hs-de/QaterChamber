"""
web/pages/media_dept_request/media_dept_request_page.py — MediaDeptRequestPage
+ MediaDeptRequestModal, for PBI 131061 ("QC - Insights & Media - 008 -
Request to the Media Dept."), single page at
`/web/qatar-chamber/request-to-media-dept` (AR:
`/ar/web/qatar-chamber/request-to-media-dept`) — hero + 4 numbered cards
(01 Press Kit download, 02 Interview Request, 03 Event Coverage Request,
04 Media Inquiry with attachment). Cards 02/03/04 open the SAME modal shell
(`.qc-mdr-modal`) with a different field set per card — one modal component
class handles all three (field-id maps below), not three separate classes.

Locators — CLI-first extraction log, confirmed live 2026-09-22 against
https://qcdev.ihorizons.com/web/qatar-chamber/request-to-media-dept at the
framework's default 1920x1080 viewport:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/for-media-professionals
    -> 404 (qc-error page) — that URL guess is WRONG; the real slug was found
       by walking the live header's "Media Center" flyout, which links
       "Request to the Media Dept." -> /web/qatar-chamber/request-to-media-dept
       (confirmed via a scripted <a> harvest against /web/qatar-chamber/media-center,
       not guessed).

    Extractor run against the REAL url found no page-body candidates either
    (cards/modal are composed divs/buttons, same class of gap already
    documented for podcast_page.py/photo_albums/video_library) — resolved the
    same way, via `page.eval_on_selector_all('[class*=qc-]', ...)` and
    targeted `inner_html()` reads.

Real DOM structure confirmed live (2026-09-22):

    header.qc-mdr-hero (shell class qc-mdr-shell qc-mdr-hero-shell)
        nav.qc-mdr-crumbs
            a.qc-mdr-crumb (Home, href=/web/qatar-chamber)
            span.qc-mdr-crumb-sep
            span.qc-mdr-crumb.is-current[aria-current=page] ("Insights & Media"
                — CONFIRMED LIVE: the current crumb reads the PARENT hub label,
                NOT "Request to the Media Dept." itself; only 2 crumb items
                render total. Same "middle/only crumb is plain, not the page's
                own title" quirk already flagged on podcast_page.py's crumbs —
                used as-is, not invented, not asserted as wrong)
        p.qc-mdr-hero-eyebrow / h1.qc-mdr-hero-title ("Request to the Media
            Dept.") / p.qc-mdr-hero-desc

    section.qc-mdr-body
        h2.qc-mdr-section-title ("Choose the support you need")
        div.qc-mdr-cards
            article.qc-mdr-card.is-featured (card 01 — Press Kit)
                span.qc-mdr-card-number ("01")
                p.qc-mdr-card-eyebrow ("Media resources")
                h3.qc-mdr-card-title ("Press Kit")
                a.qc-mdr-card-cta.is-download (href=/o/qc-media-dept-requests/press-kit?lang=en,
                    text "Download press kit" — CONFIRMED LIVE via a real
                    Playwright download: suggested_filename resolves to
                    "qatar-chamber-press-kit-en.pdf", NOT the case's own
                    literal "press_kit_en.pdf" — used as observed, disclosed
                    at the specific test)
            article.qc-mdr-card (card 02 — Interview Request)
                eyebrow "Media access", title "Interview Request"
                button.qc-mdr-card-cta.is-solid ("Request Form")
            article.qc-mdr-card (card 03 — Event Coverage Request)
                eyebrow "Event access" (CONFIRMED LIVE: lowercase "access" —
                    TC 142750's own title states 'Event Access' capitalized;
                    asserted against the real observed string, not the case's
                    capitalization, per result-integrity)
                button.qc-mdr-card-cta.is-solid ("Request Form")
            article.qc-mdr-card (card 04 — Media Inquiry)
                eyebrow "Press support", title "Media Inquiry"
                button.qc-mdr-card-cta.is-solid ("Request Form")

    Modal shell (`.qc-mdr-modal`), mounted on-demand by a card's "Request
    Form" click — same "state the script can't reach deterministically at
    first harvest" class already documented elsewhere in this project:
        .qc-mdr-modal-backdrop / .qc-mdr-modal-panel[role=dialog]
            .qc-mdr-modal-eyebrow / .qc-mdr-modal-title / [data-qc-mdr-modal-close]
            .qc-mdr-modal-lead
            form.qc-mdr-form[novalidate] > .qc-mdr-form-grid
                one .qc-mdr-field per field: <label for=qc-mdr-<fieldId>> +
                text/email/tel/select/textarea/date control
                id=qc-mdr-<fieldId>, error <p id=qc-mdr-<fieldId>-error>
            .qc-mdr-captcha[data-qc-recaptcha-field] > div[data-qc-recaptcha]
                (real Google reCAPTCHA ENTERPRISE, size=invisible — CONFIRMED
                LIVE via the anchor iframe's own src query string. No
                checkbox/challenge exists to solve; it auto-executes on
                Submit and returns a token in the background. Live-probed
                2026-09-22: a real headless Chromium submit against all 3
                forms (Interview/Event Coverage/Media Inquiry) completed
                successfully end-to-end — `.qc-mdr-done` un-hid with a real
                reference number (MDR-INT-00000001 / MDR-EVT-00000001 / a
                Media Inquiry equivalent) within ~10s of clicking Submit, no
                bypass/env flag needed, no widget defeated. This means the
                bulk of this batch's "valid input -> Submit succeeds" cases
                ARE genuinely automatable — see test module docstring for the
                full accounting of what stays skipped and why.)
            input.qc-mdr-hp[name=_hp] (honeypot, never filled by real tests)
            [data-qc-mdr-form-error] (generic submit-failure message)
            .qc-mdr-form-actions > [data-qc-mdr-form-cancel] ("Cancel"),
                [data-qc-mdr-form-submit] ("Submit Request")
        .qc-mdr-done[hidden] (success state) > .qc-mdr-done-title,
            .qc-mdr-done-body, .qc-mdr-done-ref > .qc-mdr-done-ref-value,
            [data-qc-mdr-done-close]
        .qc-mdr-confirm (close-confirmation popup) > .qc-mdr-confirm-text
            (CONFIRMED LIVE EN text: "Are you sure want to close?" — verbatim
            grammar as shipped, not corrected), [data-qc-mdr-confirm-yes]
            ("Yes"), [data-qc-mdr-confirm-no] ("No")

    Per-form field maps (id suffix after "qc-mdr-", label, type, real live
    maxlength/attrs — confirmed via inner_html() reads, NOT the case's own
    stated limits, several of which differ from the live control — see the
    "Field length-limit mismatch" table in the test module docstring):
        INTERVIEW (card 02): mediaOrganization(text,maxlength=200),
            journalistName(text,maxlength=150,letters-only enforced
            server/script-side — confirmed live via a live reject probe),
            email(email,maxlength=150), phoneNumber(tel,maxlength=20,
            +974 fixed prefix span alongside the input — the input itself
            holds only the national number, no literal "+" is typeable in it),
            requestedInterviewee(select: chairman/boardMembers/departmentHead),
            format(select: inPerson/onlineVideoCall/phone),
            interviewSubject(textarea,maxlength=1000),
            proposedDate(date,min=today — CONFIRMED LIVE the `min` attribute
            is set to the CURRENT date server-side each day, so "past date"
            and "today" must be computed at test run time, never hardcoded)
        EVENT COVERAGE (card 03): mediaOrganization, reporterName(maxlength=150),
            email, phoneNumber, eventName(select: tradeForum2026/gccSubmit/other),
            coverageType(select: press/photo/video/all),
            equipmentAndAccessNeeds(textarea,maxlength=1000)
        MEDIA INQUIRY (card 04): fullName(text,maxlength=150),
            mediaOrganization, workEmail(email,maxlength=150),
            inquiryType(select: informationRequest/dataRequest/generalInquiry),
            message(textarea,maxlength=1000),
            attachment(file button + hidden .qc-mdr-file-input,
            accept=".pdf,.doc,.docx,.jpg,.jpeg,.png", OPTIONAL — no `*` marker
            on its label, confirmed live both by the DOM and by a real
            no-attachment submission succeeding)

    Live validation error strings (confirmed via real reject/invalid probes,
    all forms share the same generic messages):
        required: "This field is required."
        invalid email: "Enter a valid email address."
        invalid phone: "Enter a valid mobile number."
        non-letter name: "Use letters only."
        past date: "Choose today's date or a later one." (the site copy
            actually renders a curly apostrophe; used exactly as observed)
        unsupported attachment type: "Attach a PDF, DOC, DOCX, JPG or PNG file."
        oversized attachment: "The file must be 10 MB or smaller."
"""

from config.settings import web_url
from core.web.base_page import BasePage

MEDIA_DEPT_REQUEST_PATH = "/web/qatar-chamber/request-to-media-dept"

# form_type keys used throughout this batch's Page Object + tests.
INTERVIEW = "interview"
EVENT_COVERAGE = "event_coverage"
MEDIA_INQUIRY = "media_inquiry"

# field-key -> real DOM id suffix (after "qc-mdr-"), per form.
FIELD_MAPS = {
    INTERVIEW: {
        "media_organization": "mediaOrganization",
        "journalist_name": "journalistName",
        "email": "email",
        "phone_number": "phoneNumber",
        "requested_interviewee": "requestedInterviewee",
        "format": "format",
        "interview_subject": "interviewSubject",
        "proposed_date": "proposedDate",
    },
    EVENT_COVERAGE: {
        "media_organization": "mediaOrganization",
        "reporter_name": "reporterName",
        "email": "email",
        "phone_number": "phoneNumber",
        "event_name": "eventName",
        "coverage_type": "coverageType",
        "equipment_and_access_needs": "equipmentAndAccessNeeds",
    },
    MEDIA_INQUIRY: {
        "full_name": "fullName",
        "media_organization": "mediaOrganization",
        "work_email": "workEmail",
        "inquiry_type": "inquiryType",
        "message": "message",
        "attachment": "attachment",
    },
}

# field-keys that are <select> controls (select_option, not type()).
SELECT_FIELDS = {
    "requested_interviewee", "format", "event_name", "coverage_type", "inquiry_type",
}
# field-keys that are <textarea> controls (still typed via .type(), listed
# separately only for the maxlength/rich-text framing in the docstring above).
TEXTAREA_FIELDS = {"interview_subject", "equipment_and_access_needs", "message"}
# field-keys that are <input type=date> controls.
DATE_FIELDS = {"proposed_date"}
# field-keys with a real live maxlength that is LOOSER than the case's own
# stated limit — see the module docstring's mismatch table. Over-the-case
# over-limit values are NOT truncated by the control (still fit under the
# real cap), so the test must assert the CASE's real expected result (a
# validation error) and is expected to genuinely fail, not be narrowed.
LOOSE_MAXLENGTH_FIELDS = {
    "media_organization": 200,   # cases state 150
    "journalist_name": 150,      # case states 100
    "reporter_name": 150,        # case states 100
    "full_name": 150,            # case states 100
}
# field-keys whose real live maxlength EXACTLY matches the case's stated
# limit — the "exceeds limit" state is unreachable via the UI (the control
# truncates on fill()); these are asserted as truncation-enforcement instead.
EXACT_MAXLENGTH_FIELDS = {
    "interview_subject": 1000,
    "equipment_and_access_needs": 1000,
    "message": 1000,
    "phone_number": 20,
}

REQUIRED_ERROR = "This field is required."
INVALID_EMAIL_ERROR = "Enter a valid email address."
INVALID_PHONE_ERROR = "Enter a valid mobile number."
LETTERS_ONLY_ERROR = "Use letters only."
PAST_DATE_ERROR = "Choose today’s date or a later one."
UNSUPPORTED_FILE_ERROR = "Attach a PDF, DOC, DOCX, JPG or PNG file."
OVERSIZED_FILE_ERROR = "The file must be 10 MB or smaller."


class MediaDeptRequestPage(BasePage):
    HERO = ".qc-mdr-hero"
    HERO_TITLE = ".qc-mdr-hero-title"
    HERO_DESC = ".qc-mdr-hero-desc"
    CRUMB = ".qc-mdr-crumb"
    CRUMB_CURRENT = ".qc-mdr-crumb.is-current"
    SECTION_TITLE = ".qc-mdr-section-title"

    CARD = ".qc-mdr-card"
    CARD_NUMBER = ".qc-mdr-card-number"
    CARD_EYEBROW = ".qc-mdr-card-eyebrow"
    CARD_TITLE = ".qc-mdr-card-title"
    CARD_DESC = ".qc-mdr-card-desc"
    CARD_CTA_DOWNLOAD = ".qc-mdr-card-cta.is-download"
    CARD_CTA_SOLID = ".qc-mdr-card-cta.is-solid"
    EMPTY = ".qc-mdr-empty"

    MODAL_PANEL = ".qc-mdr-modal-panel"

    # ---- Navigation ---------------------------------------------------
    def open_media_dept_request(self, locale: str = "en") -> "MediaDeptRequestPage":
        self.open(web_url(MEDIA_DEPT_REQUEST_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_media_dept_request_anonymous(self, locale: str = "en") -> "MediaDeptRequestPage":
        self.open_anonymous(web_url(MEDIA_DEPT_REQUEST_PATH, locale=locale))
        return self

    # ---- Hero / crumbs --------------------------------------------------
    def hero_title(self) -> str:
        return self.text(self.HERO_TITLE)

    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def crumb_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.CRUMB).all_inner_texts()]

    # ---- Cards ----------------------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_number(self, index: int) -> str:
        return self.page.locator(self.CARD_NUMBER).nth(index).inner_text()

    def card_eyebrow(self, index: int) -> str:
        return self.page.locator(self.CARD_EYEBROW).nth(index).inner_text()

    def card_title(self, index: int) -> str:
        return self.page.locator(self.CARD_TITLE).nth(index).inner_text()

    def card_desc(self, index: int) -> str:
        return self.page.locator(self.CARD_DESC).nth(index).inner_text()

    def is_download_cta_visible(self) -> bool:
        return self.is_visible(self.CARD_CTA_DOWNLOAD)

    def download_press_kit(self):
        """Real download via the CTA's own href — Page Object still owns the
        wait/click via self.page (BasePage's own driver handle), matching this
        project's existing convention (podcast_page.py's viewport reads) for
        a Playwright capability BasePage does not itself wrap 1:1."""
        with self.page.expect_download() as dl_info:
            self.click(self.CARD_CTA_DOWNLOAD)
        return dl_info.value

    def open_request_form(self, card_index: int) -> "MediaDeptRequestModal":
        """card_index is 0-based among the 3 solid-CTA cards: 0=Interview
        (card 02), 1=Event Coverage (card 03), 2=Media Inquiry (card 04)."""
        form_types = [INTERVIEW, EVENT_COVERAGE, MEDIA_INQUIRY]
        self.page.locator(self.CARD_CTA_SOLID).nth(card_index).click()
        self.wait_for(self.MODAL_PANEL)
        return MediaDeptRequestModal(self.page, form_types[card_index])


class MediaDeptRequestModal(BasePage):
    """One modal component for all 3 request forms — the modal SHELL
    (`.qc-mdr-modal`) is identical across Interview/Event Coverage/Media
    Inquiry; only the field-id set differs (FIELD_MAPS above). Constructed
    with the `form_type` the caller opened (MediaDeptRequestPage.open_request_form)."""

    MODAL_PANEL = ".qc-mdr-modal-panel"
    MODAL_TITLE = ".qc-mdr-modal-title"
    MODAL_EYEBROW = ".qc-mdr-modal-eyebrow"
    MODAL_CLOSE = "[data-qc-mdr-modal-close]"
    FORM = ".qc-mdr-form"
    CAPTCHA_WIDGET = "[data-qc-recaptcha]"
    CAPTCHA_ERROR = "[data-qc-mdr-captcha-error]"
    FORM_ERROR = "[data-qc-mdr-form-error]"
    SUBMIT_BTN = "[data-qc-mdr-form-submit]"
    CANCEL_BTN = "[data-qc-mdr-form-cancel]"

    DONE_PANEL = ".qc-mdr-done"
    DONE_TITLE = ".qc-mdr-done-title"
    DONE_REF = ".qc-mdr-done-ref-value"
    DONE_CLOSE_BTN = "[data-qc-mdr-done-close]"

    CONFIRM_PANEL = ".qc-mdr-confirm"
    CONFIRM_TEXT = ".qc-mdr-confirm-text"
    CONFIRM_YES_BTN = "[data-qc-mdr-confirm-yes]"
    CONFIRM_NO_BTN = "[data-qc-mdr-confirm-no]"

    ATTACHMENT_DROP_BTN = "#qc-mdr-attachment"
    ATTACHMENT_FILE_INPUT = ".qc-mdr-file-input"
    ATTACHMENT_FILENAME = ".qc-mdr-drop-file"

    def __init__(self, page, form_type: str):
        super().__init__(page)
        self.form_type = form_type
        self.fields = FIELD_MAPS[form_type]

    def _control_locator(self, field_key: str) -> str:
        return f"#qc-mdr-{self.fields[field_key]}"

    def _error_locator(self, field_key: str) -> str:
        return f"#qc-mdr-{self.fields[field_key]}-error"

    # ---- Fill / read ----------------------------------------------------
    def fill_field(self, field_key: str, value: str) -> "MediaDeptRequestModal":
        if field_key in SELECT_FIELDS:
            self.select_option(self._control_locator(field_key), value=value)
        else:
            self.type(self._control_locator(field_key), value)
        return self

    def fill_form(self, data: dict) -> "MediaDeptRequestModal":
        for key, value in data.items():
            if key == "attachment":
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

    def upload_attachment(self, file_path: str) -> "MediaDeptRequestModal":
        self.upload_file(self.ATTACHMENT_FILE_INPUT, file_path)
        return self

    def attachment_filename(self) -> str:
        return self.text(self.ATTACHMENT_FILENAME)

    # ---- Modal chrome -----------------------------------------------------
    def is_open(self) -> bool:
        return self.is_visible(self.MODAL_PANEL)

    def title(self) -> str:
        return self.text(self.MODAL_TITLE)

    def is_captcha_widget_visible(self) -> bool:
        """Checks DOM presence (`count() > 0`), not Playwright visibility —
        this is a real Google reCAPTCHA Enterprise widget with size=invisible
        by design (auto-executes on Submit, no visible checkbox ever
        renders), confirmed live 2026-09-23. A strict visibility check would
        always be False for a correctly-configured invisible widget; presence
        in the DOM is the correct, honest signal that the widget is wired up
        (HEALED 2026-09-23 — same fix as advertisements_page.py's identical
        method, and consistent with this module's own tc_142571-class
        precedent for invisible-reCAPTCHA handling)."""
        return self.page.locator(self.CAPTCHA_WIDGET).count() > 0

    def close(self) -> "MediaDeptRequestModal":
        self.click(self.MODAL_CLOSE)
        return self

    def submit(self) -> "MediaDeptRequestModal":
        self.click(self.SUBMIT_BTN)
        return self

    def cancel(self) -> "MediaDeptRequestModal":
        self.click(self.CANCEL_BTN)
        return self

    # ---- Success state ----------------------------------------------------
    def wait_for_done(self, timeout: int = 20000) -> "MediaDeptRequestModal":
        self.wait_for(self.DONE_PANEL, timeout=timeout)
        return self

    def is_done_visible(self) -> bool:
        return self.is_visible(self.DONE_PANEL)

    def reference_number(self) -> str:
        return self.text(self.DONE_REF)

    def close_done(self) -> "MediaDeptRequestModal":
        self.click(self.DONE_CLOSE_BTN)
        return self

    # ---- Close-confirmation popup ------------------------------------------
    def is_confirm_visible(self) -> bool:
        return self.is_visible(self.CONFIRM_PANEL)

    def confirm_text(self) -> str:
        return self.text(self.CONFIRM_TEXT)

    def confirm_yes(self) -> "MediaDeptRequestModal":
        self.click(self.CONFIRM_YES_BTN)
        return self

    def confirm_no(self) -> "MediaDeptRequestModal":
        self.click(self.CONFIRM_NO_BTN)
        return self

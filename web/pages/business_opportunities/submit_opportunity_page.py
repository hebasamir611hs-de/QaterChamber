"""
web/pages/business_opportunities/submit_opportunity_page.py —
SubmitBusinessOpportunityPage.

Public "Submit a Business Opportunity" webform of PBI 130697 (INVEST —
Business Opportunities): 4 field groups (Basic Information, Opportunity
Details, Media & Documents, Contact Information), a privacy-consent checkbox,
a reCAPTCHA slot and a Submit button, plus the inline success screen.

RE-VERIFIED LIVE 2026-10-12 (qcdev, unauthenticated context, EN + AR, Agent W1)
-----------------------------------------------------------------------------
* Path /web/qatar-chamber/submit-business-opportunity (AR: /ar/...). Every
  field has a stable id `#qc-bos-<field>` and its inline error is
  `span.qc-bos__error[data-qc-e="<field>"]` (exact per-field hook).
* Options come from GET /o/qc-business-opportunities-api/lookups; the page
  is only ready once `#qc-bos-sector` has more than its placeholder option.
* Country and Currency lookups are EMPTY on qcdev, so the fragment swaps the
  hidden <select> for a free-text input (`#qc-bos-country-text`,
  `#qc-bos-currency-text`). Sub-Sector is a DISABLED select ("Not yet
  configured"). Industry Pool is a single <select> (no `multiple`).
* Uploads are plain <input type=file> inside a drop zone; a valid file shows
  only its file NAME (`[data-qc-file-name=<field>]`) — no thumbnail, no
  progress bar. An invalid file is rejected on change (error "<name> — This
  file type is not accepted." / "... larger than the allowed size.") and the
  input is cleared. Image limit 2 MB (banner, logo AND each gallery image),
  PDF 5 MB, at most 10 files per multi field; jpg/jpeg/png/svg accepted.
* Messages: "This field is required." for every empty mandatory field
  (whitespace is trimmed), "Please enter a valid email address.", "Please
  enter a valid mobile number." (6-15 digits), "Please enter a full address
  starting with http:// or https://.", "Please enter a valid amount of zero or
  more." (0 is ACCEPTED), status banner "Please correct the highlighted
  fields." (`div.qc-bos__status`).
* Submit: the button is disabled and relabelled "Submitting..." while the
  multipart POST /o/qc-business-opportunities-api/submissions runs; success
  hides the form and shows `div.qc-bos__done` with the story's copy and the
  reference number inline (`strong.qc-bos__ref-inline`,
  QC-BO-SUB-yyyyMMdd-XXXXXX). reCAPTCHA is disabled on qcdev, so the
  "Security Check" field stays hidden.
* The site keeps the last language in the session: open EN and AR in
  SEPARATE fresh contexts (an EN URL opened after an AR one renders Arabic).
"""

from config.settings import web_url
from core.web.base_page import BasePage

PATH = "/web/qatar-chamber/submit-business-opportunity"
SUBMIT_API = "/o/qc-business-opportunities-api/submissions"

# field key -> DOM field name (data-qc-f / data-qc-e / #qc-bos-<name>)
FIELD_NAMES = {
    "name_en": "projectOpportunityName",
    "name_ar": "projectOpportunityNameAr",
    "sector": "sector",
    "sub_sector": "subSector",
    "country": "country",
    "company_name": "companyOrganizationName",
    "investment_brief_en": "investmentBrief",
    "investment_brief_ar": "investmentBriefAr",
    "key_highlights": "keyHighlights",
    "investment_amount": "investmentAmount",
    "currency": "currency",
    "investment_type": "investmentType",
    "timeline": "timeline",
    "risk_profile": "riskProfile",
    "industry_pool": "industryPool",
    "banner_image": "bannerImage",
    "opportunity_logo": "opportunityLogo",
    "gallery_images": "galleryImages",
    "supporting_documents": "supportingDocuments",
    "contact_full_name": "contactInformation",
    "contact_email": "contactEmail",
    "contact_mobile": "mobileNumber",
    "contact_website": "website",
    "consent": "privacyPolicyConsent",
}
TEXT_FIELD_KEYS = ("name_en", "name_ar", "company_name", "investment_brief_en", "investment_brief_ar",
                   "key_highlights", "investment_amount", "contact_full_name", "contact_email",
                   "contact_mobile", "contact_website")
# Country / Currency: free-text fallback while their lookups are empty.
LOOKUP_TEXT_KEYS = ("country", "currency")
SELECT_FIELD_KEYS = ("sector", "sub_sector", "investment_type", "timeline", "risk_profile", "industry_pool")
UPLOAD_FIELD_KEYS = ("banner_image", "opportunity_logo", "gallery_images", "supporting_documents")
MANDATORY_FIELD_KEYS = tuple(k for k in FIELD_NAMES if k not in ("sub_sector", "contact_website"))

# Select values (option value attribute, language-independent).
SAMPLE_SELECT_VALUES = {
    "sector": "energy",
    "investment_type": "jointVenture",
    "timeline": "sixToTwelveMonths",
    "risk_profile": "medium",
    "industry_pool": "energy",
}

MSG = {
    "en": {
        "required": "This field is required.",
        "invalid_email": "Please enter a valid email address.",
        "invalid_phone": "Please enter a valid mobile number.",
        "invalid_url": "Please enter a full address starting with http:// or https://.",
        "invalid_amount": "Please enter a valid amount of zero or more.",
        "bad_type": "This file type is not accepted.",
        "too_large": "This file is larger than the allowed size.",
        "fix_errors": "Please correct the highlighted fields.",
        "generic_error": "Something went wrong. Nothing was saved. Please review your entries and try again.",
        "done_title": "Submission received",
        "done_text": ("Thank you. Your business opportunity has been submitted successfully. Your Reference "
                      "Number is {ref}. The Qatar Chamber team will review your submission and notify you of "
                      "the outcome."),
    },
    "ar": {
        "required": "هذا الحقل مطلوب.",
        "fix_errors": "يرجى تصحيح الحقول المحددة.",
        "done_title": "تم استلام الطلب",
        "done_text": ("شكرًا لك. تم تقديم فرصتك التجارية بنجاح. رقمك المرجعي هو {ref}. سيقوم فريق غرفة "
                      "قطر بمراجعة طلبك وإبلاغك بالنتيجة."),
    },
}

_STYLE_JS = r"""(sel) => { const e = document.querySelector(sel); if (!e) return null;
  const s = getComputedStyle(e); const r = e.getBoundingClientRect();
  return {text: (e.innerText || '').trim(), fontFamily: s.fontFamily.split(',')[0].replace(/["']/g, '').trim(),
          fontSize: s.fontSize, fontWeight: s.fontWeight, lineHeight: s.lineHeight, color: s.color,
          background: s.backgroundColor, borderColor: s.borderTopColor, borderWidth: s.borderTopWidth,
          borderStyle: s.borderTopStyle, radius: s.borderTopLeftRadius, width: r.width, height: r.height,
          x: r.x, textAlign: s.textAlign, direction: s.direction}; }"""


class SubmitBusinessOpportunityPage(BasePage):
    ROOT = "section.qc-bos"
    HERO_TITLE = "h1.qc-bos__hero-title"
    PAGEHEAD_TITLE = "[data-qc-bos-pagehead-title]"
    PAGEHEAD_SUB = "[data-qc-bos-pagehead-sub]"
    PAGEHEAD_ICON = "[data-qc-bos-pagehead-icon]"
    GROUP = "section.qc-bos__group"
    GROUP_HEADER = "span.qc-bos__grouphead-label"
    GROUP_RULE = "span.qc-bos__grouphead-rule"
    LABEL = "label.qc-bos__label"
    REQUIRED_MARK = "span.qc-bos__req"
    DROP_ZONE = "div.qc-bos__drop"
    DROP_ICON = "span.qc-bos__drop-icon"
    DROP_STRONG = "span.qc-bos__drop-strong"
    DROP_REST = "span.qc-bos__drop-rest"
    DROP_HINT = "span.qc-bos__drop-hint"
    COUNTER = "span.qc-bos__counter"
    DIAL_CODE = "span.qc-bos__dial-code"
    FLAG = "span.qc-bos__flag"
    CONSENT = "#qc-bos-privacyPolicyConsent"
    CAPTCHA_FIELD = "div.qc-bos__captcha-field"
    SUBMIT_BUTTON = "button.qc-bos__submit"
    SUBMIT_LABEL = "[data-qc-bos-submit-label]"
    STATUS = "div.qc-bos__status"
    FORM = "form.qc-bos__form"
    DONE = "div.qc-bos__done"
    DONE_TITLE = "[data-qc-bos-done-title]"
    DONE_TEXT = "[data-qc-bos-done-text]"
    DONE_REF = "strong.qc-bos__ref-inline"
    DONE_LINK = "[data-qc-bos-done-link]"
    LANGUAGE_SWITCHER = "header.qc-global-site-header a.qc-lang-switcher"

    def __init__(self, page):
        super().__init__(page)
        self.posts: list[str] = []
        self._blocking = False

    # ---- locators ---------------------------------------------------------
    @staticmethod
    def field(key: str) -> str:
        name = FIELD_NAMES[key]
        if key in LOOKUP_TEXT_KEYS:
            return f"#qc-bos-{name}-text"
        return f"#qc-bos-{name}"

    @staticmethod
    def error(key: str) -> str:
        return f"span.qc-bos__error[data-qc-e='{FIELD_NAMES[key]}']"

    @staticmethod
    def file_name_label(key: str) -> str:
        return f"[data-qc-file-name='{FIELD_NAMES[key]}']"

    # ---- navigation / safety ------------------------------------------------
    def open_submit_form(self, locale: str = "en") -> "SubmitBusinessOpportunityPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for(self.SUBMIT_BUTTON, state="visible", timeout=60000)
        self.page.wait_for_function(
            "() => { const s = document.querySelector('#qc-bos-sector'); return s && s.options.length > 1; }",
            timeout=30000)
        return self

    def block_submissions(self) -> "SubmitBusinessOpportunityPage":
        """Validation cases: any POST to the intake endpoint is recorded and
        aborted, so a validation case can never create a record, and
        `self.posts` proves whether the form tried to submit at all."""
        def _abort(route):
            self.posts.append(route.request.url)
            route.abort()
        self.page.route(f"**{SUBMIT_API}**", _abort)
        self._blocking = True
        return self

    def unblock_submissions(self) -> None:
        if self._blocking:
            self.page.unroute(f"**{SUBMIT_API}**")
            self._blocking = False

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ---- fill ---------------------------------------------------------------
    def fill_field(self, key: str, value) -> None:
        loc = self.field(key)
        if key in UPLOAD_FIELD_KEYS:
            self.page.set_input_files(loc, value)
            self.page.wait_for_timeout(300)
        elif key == "consent":
            self.page.locator(loc).set_checked(bool(value))
        elif key in SELECT_FIELD_KEYS:
            self.page.select_option(loc, value=value)
        else:
            self.page.fill(loc, value)

    def type_field(self, key: str, value: str) -> None:
        """Real key presses (honours maxlength / input masks)."""
        self.page.fill(self.field(key), "")
        self.page.locator(self.field(key)).press_sequentially(value, delay=0)

    def fill_valid(self, values: dict, skip: tuple = ()) -> "SubmitBusinessOpportunityPage":
        for key, value in values.items():
            if key not in skip:
                self.fill_field(key, value)
        return self

    def blur(self) -> None:
        self.page.locator(self.PAGEHEAD_TITLE).click()

    # ---- read ---------------------------------------------------------------
    def field_value(self, key: str) -> str:
        return self.page.input_value(self.field(key))

    def errors(self) -> dict:
        """Every visible inline error, keyed by DOM field name."""
        return self.page.evaluate(
            "() => Object.fromEntries([...document.querySelectorAll('span.qc-bos__error')]"
            ".filter(e => !e.hidden && e.textContent.trim()).map(e => [e.dataset.qcE, e.textContent.trim()]))")

    def field_error_text(self, key: str) -> str:
        return self.errors().get(FIELD_NAMES[key], "")

    def is_field_invalid(self, key: str) -> bool:
        cls = self.page.locator(self.field(key)).get_attribute("class") or ""
        return "qc-bos__input--invalid" in cls or self.page.locator(self.field(key)).get_attribute("aria-invalid") == "true"

    def status_text(self) -> str:
        loc = self.page.locator(self.STATUS)
        return loc.inner_text().strip() if loc.is_visible() else ""

    def option_labels(self, key: str) -> list:
        return [t.strip() for t in self.page.locator(f"{self.field(key)} option").all_inner_texts()]

    def selected_label(self, key: str) -> str:
        return self.page.locator(self.field(key)).locator("option:checked").inner_text().strip()

    def is_multi_select(self, key: str) -> bool:
        return self.page.evaluate("(s) => document.querySelector(s).multiple", self.field(key))

    def is_disabled(self, key: str) -> bool:
        return self.page.locator(self.field(key)).is_disabled()

    def maxlength(self, key: str) -> int:
        return int(self.page.locator(self.field(key)).get_attribute("maxlength") or -1)

    def placeholder(self, key: str) -> str:
        if key in SELECT_FIELD_KEYS:
            return self.option_labels(key)[0]
        return self.page.locator(self.field(key)).get_attribute("placeholder") or ""

    def uploaded_file_label(self, key: str) -> str:
        loc = self.page.locator(self.file_name_label(key))
        return loc.inner_text().strip() if loc.is_visible() else ""

    def upload_has_image_preview(self, key: str) -> bool:
        return self.page.locator(f"[data-qc-drop='{FIELD_NAMES[key]}'] img").count() > 0

    def selected_file_names(self, key: str) -> list:
        return self.page.evaluate("(s) => [...document.querySelector(s).files].map(f => f.name)", self.field(key))

    def group_header_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.GROUP_HEADER).all_inner_texts()]

    def group_labels(self) -> list:
        """Per group: the visible label texts (asterisk stripped)."""
        return self.page.evaluate(
            "() => [...document.querySelectorAll('section.qc-bos__group')].map(g => [...g.querySelectorAll('.qc-bos__label')]"
            ".filter(l => l.offsetParent).map(l => l.innerText.replace('*', '').trim()))")

    def drop_hints(self) -> list:
        return [t.strip() for t in self.page.locator(self.DROP_HINT).all_inner_texts()]

    def style(self, selector: str, pseudo: str | None = None) -> dict | None:
        if pseudo:
            return self.page.evaluate(
                "([s, p]) => { const e = document.querySelector(s); if (!e) return null; const c = getComputedStyle(e, p);"
                " return {color: c.color, fontSize: c.fontSize, fontWeight: c.fontWeight}; }", [selector, pseudo])
        return self.page.evaluate(_STYLE_JS, selector)

    def has_horizontal_scroll(self) -> bool:
        return self.page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")

    def is_captcha_visible(self) -> bool:
        return self.page.locator(self.CAPTCHA_FIELD).is_visible()

    def contact_mobile_country_code_text(self) -> str:
        return self.text(self.DIAL_CODE).strip()

    # ---- submit -------------------------------------------------------------
    def click_submit(self) -> "SubmitBusinessOpportunityPage":
        self.page.locator(self.SUBMIT_BUTTON).click()
        self.page.wait_for_timeout(600)
        return self

    def submit_and_wait(self, timeout_ms: int = 90000) -> dict:
        """Real submission: clicks Submit, samples the button state while the
        POST is in flight, and returns the HTTP status + JSON body + UI state."""
        with self.page.expect_response(
                lambda r: SUBMIT_API in r.url and r.request.method == "POST", timeout=timeout_ms) as info:
            self.page.locator(self.SUBMIT_BUTTON).click()
            busy = self.page.evaluate(
                "(s) => { const b = document.querySelector(s); return {disabled: b.disabled,"
                " label: (document.querySelector('[data-qc-bos-submit-label]') || {}).textContent}; }",
                self.SUBMIT_BUTTON)
        response = info.value
        body = {}
        try:
            body = response.json()
        except Exception:  # noqa: BLE001 — body read below from the UI anyway
            pass
        try:
            self.page.locator(f"{self.DONE}:visible, {self.STATUS}:visible").first.wait_for(timeout=30000)
        except Exception:  # noqa: BLE001
            pass
        return {"http": response.status, "body": body, "busy_state": busy, **self.outcome()}

    def outcome(self) -> dict:
        done = self.page.locator(self.DONE).is_visible()
        return {
            "success": done,
            "form_hidden": not self.page.locator(self.FORM).is_visible(),
            "done_title": self.text(self.DONE_TITLE).strip() if done else "",
            "done_text": self.text(self.DONE_TEXT).strip() if done else "",
            "reference": self.text(self.DONE_REF).strip() if done and self.page.locator(self.DONE_REF).count() else "",
            "status": self.status_text(),
            "button_disabled": self.page.locator(self.SUBMIT_BUTTON).is_disabled(),
        }

    def is_success_visible(self) -> bool:
        return self.page.locator(self.DONE).is_visible()

    def click_language_switcher(self) -> None:
        self.page.locator(self.LANGUAGE_SWITCHER).first.click()
        self.page.wait_for_load_state("domcontentloaded")

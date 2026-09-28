"""
web/pages/suggestions_complaints/suggestions_complaints_page.py —
SuggestionsComplaintsPage.

Public-frontend Page Object for PBI 131030 (QC - Councils, Committees &
Partnerships - 006 - Suggestions & Complaints), scripted from the 88
Automation-tagged, Web-platform cases handed off for Phase 3 (already
filtered to exclude Control_Panel-tagged and non-automated cases).

LOCATORS — CLI-first, verified live 2026-09-22 (qcdev)
------------------------------------------------------------------
Real path resolved via the Liferay nav-items REST API
(`/o/c/navitems/scopes/37246?...`):
`/web/qatar-chamber/suggestions-and-complaints` (the actual live path,
replacing the originally-guessed `/our-services/suggestions-and-complaints`
— see PATH below). An ad-hoc structural dump (scripted
`document.querySelectorAll` class/id walk, not MCP) confirmed the real CSS
namespace is `qc-sc-*` / shared `qc-field__*` (same field-chrome family
already confirmed for join_committee_page.py and
business_council_membership_page.py), replacing the originally-guessed
`data-qc-sc-field`/`data-qc-sc-error` attribute contract below:

    <section class="qc-sc"> ... hero / intro / form-card markup ... </section>
    <div class="qc-field">
      <label class="qc-field__label">...<span class="qc-field__req">*</span></label>
      <input|select|textarea id="qc-sc-<camelCaseId>" class="qc-field__input">
      <span class="qc-field__error">...</span>
    </div>

Every field carries a stable, unique `id` (`#qc-sc-*`) — the framework's
highest confirmed tier — so `field_control_locator()`/`field_error_locator()`
/`field_wrapper_locator()` below now resolve by id/`:has(#id)` rather than
the originally-guessed `[name='<key>']`/`[data-qc-sc-error]`/
`[data-qc-sc-field]` attributes, none of which exist on the live DOM.

The 3-group structure (Applicant Details / Company Details / Submission
Details) and all 19 fields, their requiredness, and their conditional
"Other" reveals (Applicant Position -> "Please specify your position",
Sector -> "Please specify the sector") ARE confirmed live and match this
module's FIELD_TABLE exactly.

CAPTCHA: the field row (label "Verification") IS confirmed and unique
(`div.qc-sc-captcha`), but its widget mount (`div.qc-sc-captcha__widget`)
renders EMPTY — consistent with the invisible/score-based reCAPTCHA pattern
already confirmed on this project's other service-page forms, matching
this module's own pre-existing disclosure below.

Post-submit confirmation: a toast container (`div.qc-sc-toast`) exists at
the end of the fragment (also empty until triggered) — CONFIRMATION now
points there instead of the originally-guessed `.qc-sc-confirmation`.

Field model (19 fields across 3 groups) — derived from the 88 cases' own
field names, requiredness, formats and max-lengths; not invented beyond what
the cases state:
------------------------------------------------------------------
Group 1 — Applicant Details:
    applicant_name            text     required   max 200
    applicant_position        select   required   reveals applicant_position_other when "Other"
    applicant_position_other  text     required*  max 100  (*only when revealed)
    applicant_email           email    required
    applicant_mobile          phone    required   +974 format

Group 2 — Company Details:
    company_name              text     required
    cr_number                 text     required
    activity_as_in_cr         text     optional
    primary_business_activity text     optional
    type_of_ownership         select   required
    company_telephone         phone    optional   +974 format
    company_mobile            phone    required   +974 format
    company_email             email    required   max 150
    sector                    select   required   reveals sector_other when "Other"
    sector_other              text     required*  max 100  (*only when revealed)

Group 3 — Submission Details:
    authority                 text     optional
    department                text     optional
    complaint_brief           textarea required   max 2000
    proposal_solution         textarea required   max 2000

CAPTCHA — assumed present, unverified
------------------------------------------------------------------
Case 144402 ("submitting without completing CAPTCHA blocks submission with a
CAPTCHA error") and 144393/144400 describe a CAPTCHA challenge gating
submission, matching the pattern already confirmed live on this project's
other service-page forms (Legal Consultation's invisible reCAPTCHA
Enterprise — see legal_consultation_page.py). No agreed CAPTCHA bypass exists
on this project (no test key, no env flag). Any test whose case requires an
ACTUAL successful submission (a stored Reference Number) is gated behind
`captcha_state()` the same way `test_legal_consultation_web.py` gates
138477/138490 — the reachable steps run for real and fail red if the product
is wrong; only the final submit-and-observe-the-result step is skipped, with
a concrete reason, when no bypass is configured.
"""

from core.web.base_page import BasePage
from config.settings import web_url

PATH = "/web/qatar-chamber/suggestions-and-complaints"

# Logical field key -> confirmed live `id` suffix (`#qc-sc-<value>`).
FIELD_IDS = {
    "applicant_name": "applicantName",
    "applicant_position": "applicantPosition",
    "applicant_position_other": "applicantPositionOther",
    "applicant_email": "applicantEmail",
    "applicant_mobile": "applicantMobile",
    "company_name": "companyName",
    "cr_number": "crNumber",
    "activity_as_in_cr": "activityInCR",
    "primary_business_activity": "primaryBusinessActivity",
    "type_of_ownership": "typeOfOwnership",
    "company_telephone": "telephone",
    "company_mobile": "companyMobile",
    "company_email": "companyEmail",
    "sector": "sector",
    "sector_other": "sectorOther",
    "authority": "authority",
    "department": "department",
    "complaint_brief": "complaintBrief",
    "proposal_solution": "proposalForSolution",
}

# key -> (label, required, max_length, control_type, reveals_key)
# control_type in {"text", "email", "phone", "select", "textarea"}
FIELD_TABLE = [
    ("applicant_name", "Applicant Name", True, 200, "text", None),
    ("applicant_position", "Applicant Position", True, None, "select", "applicant_position_other"),
    ("applicant_position_other", "Please specify (Applicant Position)", True, 100, "text", None),
    ("applicant_email", "Applicant Email", True, None, "email", None),
    ("applicant_mobile", "Applicant Mobile Number", True, None, "phone", None),
    ("company_name", "Company name", True, None, "text", None),
    ("cr_number", "CR Number", True, None, "text", None),
    ("activity_as_in_cr", "Activity as in CR", False, None, "text", None),
    ("primary_business_activity", "Primary Business Activity", False, None, "text", None),
    ("type_of_ownership", "Type of Ownership", True, None, "select", None),
    ("company_telephone", "Telephone (Direct Line)", False, None, "phone", None),
    ("company_mobile", "Mobile Number", True, None, "phone", None),
    ("company_email", "Company Email", True, 150, "email", None),
    ("sector", "Select the Sector", True, None, "select", "sector_other"),
    ("sector_other", "Please specify (Sector)", True, 100, "text", None),
    ("authority", "Authority", False, None, "text", None),
    ("department", "Department", False, None, "text", None),
    ("complaint_brief", "Complaint/Proposal in Brief", True, 2000, "textarea", None),
    ("proposal_solution", "Proposal for Solution", True, 2000, "textarea", None),
]
FIELD_BY_KEY = {row[0]: row for row in FIELD_TABLE}

# Sample valid values used to fill every OTHER field while a test leaves the
# field under test empty/whitespace/invalid — mirrors each case's own
# "complete remaining mandatory fields with valid data" step. Never asserted
# on except where a case's own EXPECTED text names the stored value.
SAMPLE_VALID_VALUES = {
    "applicant_name": "Ahmed Al-Sayed",
    # Select fields: these are STATIC FALLBACKS only. `sample_value()` resolves
    # the real option label live from the product's own lookups endpoint
    # (see SELECT_LOOKUP_GROUP below) so an option-label change upstream can
    # never again take out 35 tests at once — the previous value here was
    # "Manager", which has never existed in the live applicantPosition list.
    "applicant_position": "General Manager",
    "applicant_position_other": "Regional Compliance Lead",
    "applicant_email": "ahmed.alsayed@example.com",
    # Confirmed live (trace 2026-09-22, TC-144443): the two mobile inputs are
    # <input type="tel" inputmode="numeric" maxlength="8"
    #  autocomplete="tel-national" placeholder="XXXXXXXX"> — the "+974" is
    # STATIC CHROME rendered beside the box, not part of the value. A
    # "+974 5512 3456" sample is 14 chars into a maxlength=8 national field
    # and is rejected. Bare 8-digit national numbers only.
    "applicant_mobile": "55123456",
    "company_name": "Al Rayyan Trading LLC",
    "cr_number": "123456",
    "activity_as_in_cr": "General Trading",
    "primary_business_activity": "Import and distribution of consumer goods",
    "type_of_ownership": "Sole Proprietorship",
    # Telephone (Direct Line) is a DIFFERENT control: maxlength="40", no
    # inputmode/national-format chrome — the full international form is valid.
    "company_telephone": "+974 4444 5555",
    "company_mobile": "33445566",
    "company_email": "info@alrayyantrading.com",
    "sector": "Trade",
    "sector_other": "Custom sector description",
    "authority": "Ministry of Commerce and Industry",
    "department": "Consumer Protection Department",
    "complaint_brief": "Delayed customs clearance at Hamad Port affecting our shipment schedule.",
    "proposal_solution": "Request expedited clearance lane coordination with Customs Authority.",
}

# key -> the value that reveals its conditional counterpart.
OTHER_TRIGGER_VALUE = {"applicant_position": "Other", "sector": "Other"}

# ---------------------------------------------------------------------------
# Select options come from the PRODUCT, not from this module
# ---------------------------------------------------------------------------
# The fragment root carries `data-lookups-endpoint="/o/qc-suggestions-complaints
# /lookups"` and populates all three selects from it. Hardcoding option labels
# here is what made a single stale label ("Manager") fail 35 tests, so
# `sample_value()` reads the live list and picks a stable OPTION KEY — the
# machine-readable side of the payload, which does not churn when the
# human-readable label is reworded or re-translated.
#
# Payload shape (confirmed live 2026-09-22):
#   {"applicantPosition":[{"key":"generalManager","en":"General Manager",
#                          "ar":"..."} , ...], "typeOfOwnership":[...],
#    "sector":[...]}
DEFAULT_LOOKUPS_ENDPOINT = "/o/qc-suggestions-complaints/lookups"

# logical field key -> lookups payload group name
SELECT_LOOKUP_GROUP = {
    "applicant_position": "applicantPosition",
    "type_of_ownership": "typeOfOwnership",
    "sector": "sector",
}

# logical field key -> the lookup OPTION KEY this suite fills selects with.
# "other" is deliberately never chosen here: it reveals a conditional field.
SELECT_SAMPLE_OPTION_KEY = {
    "applicant_position": "generalManager",
    "type_of_ownership": "soleProprietorship",
    "sector": "trade",
}


class SuggestionsComplaintsPage(BasePage):
    # ---- Root / breadcrumb / hero ------------------------------------------
    ROOT = "section.qc-sc"
    CRUMBS = "nav.qc-sc-crumbs"
    CRUMB = ".qc-sc-crumbs__item"
    # The trail's LAST segment is the current page: main.js builds it as a
    # <span aria-current="page"> with no href (only segments carrying a
    # `part.href` become <a>). Confirmed live in the fragment JS, trace
    # 2026-09-22 TC-144443.
    CRUMB_CURRENT = '.qc-sc-crumbs__item[aria-current="page"]'
    HERO = "header.qc-sc-hero"
    HERO_TITLE = "h1.qc-sc-hero__title"
    HERO_DESC = "p.qc-sc-hero__subtitle"

    # ---- Informational section ---------------------------------------------
    INFO_SECTION = ".qc-sc-intro"
    INFO_EYEBROW = "p.qc-sc-intro__eyebrow"
    INFO_HEADING = "h2.qc-sc-intro__heading"
    INFO_PARAGRAPHS = ".qc-sc-intro__body p"

    # ---- Form card -----------------------------------------------------
    FORM_CARD = ".qc-sc-card"
    FORM_CARD_ICON = "span.qc-sc-card__icon"
    FORM_CARD_TITLE = "h3.qc-sc-card__title"
    FORM_DISCLAIMER = "p.qc-sc-card__helper"
    FORM = "form.qc-sc-form"
    GROUP_HEADER = "span.qc-sc-section__title"
    FIELD = ".qc-field"
    FIELD_LABEL = "label.qc-field__label"
    FIELD_REQUIRED_MARK = "span.qc-field__req"
    # TODO(locator): the "Verification" field row IS confirmed
    # (div.qc-field.qc-sc-captcha), but its widget mount
    # (div.qc-sc-captcha__widget) renders EMPTY at load time — no checkbox,
    # no iframe — consistent with an invisible/score-based reCAPTCHA (same
    # pattern already confirmed on this project's other service-page forms,
    # matching this module's own pre-existing disclosure). RECAPTCHA_IFRAME
    # therefore has no live element to confirm; left as its original
    # best-guess selector.
    CAPTCHA_MOUNT = "div.qc-sc-captcha"
    RECAPTCHA_IFRAME = 'iframe[src*="recaptcha"]'
    SUBMIT_BUTTON = "button.qc-sc-submit"
    CONFIRMATION = "div.qc-sc-toast"  # post-submit toast container (empty until triggered)
    PRIVACY_POLICY_LINK = "a.qc-sc-consent__link"

    # ---- Navigation ----------------------------------------------------
    def open_suggestions_complaints(self, locale: str = "en") -> "SuggestionsComplaintsPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for(self.HERO_TITLE, state="visible", timeout=30000)
        self.wait_for(self.FORM, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_language(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    def theme(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    # ---- Generic measurement helpers (mirrors legal_consultation_page.py) --
    def box(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).bounding_box()

    def computed_style(self, locator: str, props: list, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

    # ---- Breadcrumb ------------------------------------------------------
    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.CRUMB).all_inner_texts()]

    def breadcrumb_count(self) -> int:
        return self.page.locator(self.CRUMB).count()

    def breadcrumb_hrefs(self) -> list:
        """href of every crumb segment, in order; None for a non-linked one."""
        return self.page.locator(self.CRUMB).evaluate_all(
            "nodes => nodes.map((n) => n.getAttribute('href'))"
        )

    def current_breadcrumb_text(self) -> str:
        return self.text(self.CRUMB_CURRENT).strip()

    def is_current_breadcrumb_linked(self) -> bool:
        """True when the aria-current segment is itself a hyperlink. It must
        NOT be: the current page has no parent to link to."""
        return bool(
            self.page.locator(self.CRUMB_CURRENT).evaluate(
                "n => n.tagName.toLowerCase() === 'a' && !!n.getAttribute('href')"
            )
        )

    # ---- Hero --------------------------------------------------------------
    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESC).strip()

    # ---- Informational section ----------------------------------------
    def info_eyebrow_text(self) -> str:
        return self.text(self.INFO_EYEBROW).strip()

    def info_heading_text(self) -> str:
        return self.text(self.INFO_HEADING).strip()

    def info_paragraph_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.INFO_PARAGRAPHS).all_inner_texts()]

    # ---- Form card ----------------------------------------------------
    def form_card_title_text(self) -> str:
        return self.text(self.FORM_CARD_TITLE).strip()

    def form_disclaimer_text(self) -> str:
        return self.text(self.FORM_DISCLAIMER).strip()

    def group_header_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.GROUP_HEADER).all_inner_texts()]

    def submit_button_text(self) -> str:
        return self.text(self.SUBMIT_BUTTON).strip()

    def privacy_policy_href(self) -> str | None:
        return self.get_attribute(self.PRIVACY_POLICY_LINK, "href")

    def click_privacy_policy_link(self) -> None:
        self.click(self.PRIVACY_POLICY_LINK)

    # ---- Field-level generic helpers ------------------------------------
    # Confirmed live: every field resolves by its stable `#qc-sc-<id>` id
    # (FIELD_IDS), not a `name` attribute or `data-qc-sc-*` attribute — both
    # of the originally-guessed contracts do not exist on the live DOM.
    def field_control_locator(self, key: str) -> str:
        return f"#qc-sc-{FIELD_IDS[key]}"

    def field_error_locator(self, key: str) -> str:
        return f"{self.field_wrapper_locator(key)} span.qc-field__error"

    def field_wrapper_locator(self, key: str) -> str:
        return f"div.qc-field:has(#qc-sc-{FIELD_IDS[key]})"

    def field_label_text(self, key: str) -> str:
        return self.text(f"{self.field_wrapper_locator(key)} {self.FIELD_LABEL}").strip()

    def is_field_visible(self, key: str) -> bool:
        return self.is_visible(self.field_wrapper_locator(key))

    def is_field_required_marked(self, key: str) -> bool:
        return self.is_visible(f"{self.field_wrapper_locator(key)} {self.FIELD_REQUIRED_MARK}")

    def field_border_color(self, key: str) -> str:
        return self.computed_style(self.field_control_locator(key), ["borderColor"])["borderColor"]

    def field_border_style(self, key: str) -> dict:
        return self.computed_style(
            self.field_control_locator(key), ["borderColor", "borderWidth", "borderRadius", "padding"]
        )

    def field_error_text(self, key: str) -> str:
        return self.text(self.field_error_locator(key)).strip()

    def is_field_error_visible(self, key: str) -> bool:
        return self.is_visible(self.field_error_locator(key))

    def field_value(self, key: str) -> str:
        return self.page.locator(self.field_control_locator(key)).input_value()

    def field_max_length_attribute(self, key: str) -> str | None:
        return self.get_attribute(self.field_control_locator(key), "maxlength")

    # ---- Live select options (lookups endpoint) --------------------------
    def lookups_endpoint(self) -> str:
        """The product's own lookups URL, read off the fragment root's
        `data-lookups-endpoint` attribute so a path change is picked up
        automatically; falls back to the confirmed default."""
        value = self.get_attribute(self.ROOT, "data-lookups-endpoint")
        return (value or DEFAULT_LOOKUPS_ENDPOINT).strip() or DEFAULT_LOOKUPS_ENDPOINT

    def lookups(self) -> dict:
        """Fetches (once per Page Object instance) the live select-option
        payload through the browser context's own request API, so it carries
        the same session/cookies as the page under test."""
        cached = getattr(self, "_lookups_cache", None)
        if cached is not None:
            return cached
        response = self.page.request.get(web_url(self.lookups_endpoint()))
        payload = response.json()
        self._lookups_cache = payload
        return payload

    def lookup_option_labels(self, key: str) -> list:
        """Every option LABEL the product offers for a select field, in the
        page's current language."""
        lang = "ar" if (self.document_language() or "en").lower().startswith("ar") else "en"
        return [entry[lang] for entry in self.lookups()[SELECT_LOOKUP_GROUP[key]]]

    def lookup_label_for(self, key: str, option_key: str) -> str | None:
        lang = "ar" if (self.document_language() or "en").lower().startswith("ar") else "en"
        for entry in self.lookups()[SELECT_LOOKUP_GROUP[key]]:
            if entry.get("key") == option_key:
                return entry[lang]
        return None

    def sample_value(self, key: str) -> str:
        """The valid value this suite fills `key` with.

        For the three SELECT fields the label is resolved LIVE from the
        lookups endpoint by stable option key, so a reworded or re-translated
        label can't invalidate the sample data (a stale hardcoded "Manager"
        previously failed 35 tests). Falls back to SAMPLE_VALID_VALUES if the
        endpoint is unreachable or the option key has genuinely gone."""
        if key not in SELECT_LOOKUP_GROUP:
            return SAMPLE_VALID_VALUES[key]
        try:
            label = self.lookup_label_for(key, SELECT_SAMPLE_OPTION_KEY[key])
        except Exception:  # noqa: BLE001 — never let lookup I/O mask the real assertion
            label = None
        return label or SAMPLE_VALID_VALUES[key]

    def fill_field(self, key: str, value: str) -> "SuggestionsComplaintsPage":
        _, _, _, _, control_type, _ = FIELD_BY_KEY[key]
        locator = self.field_control_locator(key)
        if control_type == "select":
            self.select_option(locator, label=value)
        else:
            self.type(locator, value)
        return self

    def blur_field(self, key: str) -> None:
        """Click outside the field to trigger on-blur validation."""
        self.click(self.ROOT)

    def paste_into_field(self, key: str, value: str) -> "SuggestionsComplaintsPage":
        """Simulates a paste (Ctrl+A then insert_text) rather than a typed
        entry — Playwright has no headless-safe native OS-clipboard paste, so
        `keyboard.insert_text` (its own documented paste-equivalent
        primitive) is used, exercising the field's real input handling
        rather than a scripted DOM value assignment."""
        self.click(self.field_control_locator(key))
        self.press_key("Control+A")
        self.page.keyboard.insert_text(value)
        return self

    def fill_mandatory_fields(self, overrides: dict | None = None, skip: set | None = None) -> None:
        """Fill every mandatory (and currently-visible) field with its sample
        valid value, honouring `overrides` (value per key) and `skip` (keys
        left untouched, e.g. the field a case is deliberately testing)."""
        overrides = overrides or {}
        skip = skip or set()
        for key, _, required, _, _, reveals in FIELD_TABLE:
            if key in skip:
                continue
            if not required:
                continue
            if not self.is_field_visible(key):
                continue
            value = overrides.get(key, self.sample_value(key))
            self.fill_field(key, value)
            if reveals and value == OTHER_TRIGGER_VALUE.get(key):
                # Conditional field just became visible this same pass —
                # fill it too, unless the caller explicitly wants it skipped.
                if reveals not in skip:
                    self.fill_field(reveals, overrides.get(reveals, self.sample_value(reveals)))

    # ---- CAPTCHA / submission -------------------------------------------
    def captcha_state(self) -> dict:
        return self.page.evaluate(
            """
            () => {
                const mount = document.querySelector('.qc-sc-captcha');
                const frames = Array.from(document.querySelectorAll('iframe[src*="recaptcha"]'));
                return {
                    mountPresent: !!mount,
                    recaptchaFrames: frames.length,
                    recaptchaLoaded: frames.some((f) => f.getBoundingClientRect().width > 0),
                };
            }
            """
        )

    def click_submit(self) -> "SuggestionsComplaintsPage":
        self.click(self.SUBMIT_BUTTON)
        return self

    def is_submit_button_disabled(self) -> bool:
        return bool(self.get_attribute(self.SUBMIT_BUTTON, "disabled"))

    def confirmation_state(self) -> dict:
        return self.page.evaluate(
            """
            () => {
                const el = document.querySelector('.qc-sc-toast');
                if (!el) return null;
                return {
                    text: el.textContent.trim(),
                    visible: el.offsetParent !== null,
                };
            }
            """
        )

    def reference_number(self) -> str | None:
        """Extracts the Reference Number token out of the confirmation
        banner text — TODO(locator): confirm the real DOM node once the
        confirmation banner markup is extracted; this falls back to a
        regex scrape of the whole confirmation text so the page-object
        contract does not change once a dedicated node is confirmed."""
        import re

        state = self.confirmation_state()
        if not state:
            return None
        match = re.search(r"([A-Z0-9-]{6,})", state["text"])
        return match.group(1) if match else None

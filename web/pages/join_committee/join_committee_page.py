"""
web/pages/join_committee/join_committee_page.py — JoinCommitteePage.

Public-frontend Page Object for PBI 130717 ("QC - Councils, Committees &
Partnerships - 002 - Request to Join a Committee"), sourced from the
approved/injected Azure DevOps test suite (81 Web-tagged, Automation-tagged
cases; Control_Panel-tagged and Manual cases already excluded from the batch
handed off by the QA Manager for this Phase 3 scripting pass).

Locators — CLI-first, verified live 2026-09-22 (qcdev)
------------------------------------------------------------------
Real path resolved via the Liferay nav-items REST API
(`/o/c/navitems/scopes/37246?...`):
`/web/qatar-chamber/request-to-join-a-committee`. An ad-hoc structural dump
(scripted `document.querySelectorAll` class/id walk, not MCP) then confirmed
the real CSS namespace is `qc-cj-*` / `qc-field__*` (Committee Join), not the
guessed `qc-jcr-*`. Every form field carries a stable, unique `id`
(`#qc-cj-*`) — the framework's highest confirmed tier.

The three group headers ("Committee Selection", "Company Information",
"Contact & Classification") and their field membership/order ARE confirmed
live and match this module's pre-existing disclosed-inference grouping
exactly — no changes needed to FIELD_TABLE/GROUP_FIELD_KEYS/GROUP_HEADERS.
The 13-value-dropdown cases (143443/143444) remain out of scope for literal
value assertions per the original disclosure below.

CAPTCHA: reCAPTCHA Enterprise in invisible score mode, confirmed live
2026-09-22 (`/o/qc-recaptcha-api/config` returns mode "score", enabled
true; `recaptcha/enterprise.js?render=<siteKey>` loads). There is no visible
mount node, so presence is asserted via the server-rendered script tags
(RECAPTCHA_SCRIPT), which is also what makes the submission gate
deterministic.

SUBMISSIONS_REVIEW_PATH (Control Panel deep-link) remains an unconfirmed
guess — out of scope for this pass (public-frontend extraction only; the
Control Panel admin surface was not reached).

Dropdowns: fill_all_valid() selects by option `value` (SAMPLE_OPTION_VALUES),
which is identical on the EN and AR pages; the "valid value accepted" family
still selects by the English label its case names. The 13 Sector/Committee
values are stated verbatim in TC-038 (FLD-1) and asserted literally in
143443 (SECTOR_COMMITTEE_VALUES_EN); 143444 asserts 13 Arabic values. The
"Select a committee" placeholder (value="") is excluded from both.
"""

import time

from config.settings import control_panel_url, web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import (
    AccessibilityToolsComponent,
)

JOIN_COMMITTEE_PATH = "/web/qatar-chamber/request-to-join-a-committee"

# TODO(locator): guessed Control Panel path for the admin-only submissions
# review surface (143427's deep-link denial target) — the Object Definition
# portlet's real p_p_id/objectDefinitionId is unconfirmed; this is a
# plausible Liferay "manage" URL shape mirrored from
# cms/pages/org_structure/org_structure_admin_page.py's LIST_URL pattern,
# not a verified selector.
SUBMISSIONS_REVIEW_PATH = (
    "/group/qatar-chamber/~/control_panel/manage"
    "?p_p_id=com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet"
    "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_mvcRenderCommandName="
    "%2Fedit_object_definition"
    "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_objectDefinitionExternalReferenceCode="
    "QCDEMO-130717-COMMITTEE-JOINING-REQUEST"
)

# Field key -> (English label, required?) — labels verbatim from the spec's
# FLD-n rows (.claude/qa-runs/130717.json), in the PBI's field order; also used as the
# structural "field order" assertion the group-order cases (143412/143413)
# compare against (see the module docstring's grouping disclosure).
FIELD_TABLE = [
    ("sector_committee", "Select the Sector / Committee", True),
    ("applicant_name", "Applicant Name", True),
    ("company_name", "Company name", True),
    ("cr_number", "CR Number", True),
    ("established_since", "Established Since", True),
    ("owner_name", "Owner Name", True),
    ("gm_ceo", "General Manager / CEO", True),
    ("activity", "Activity", False),
    ("email", "Email", True),
    ("mobile_number", "Mobile Number", True),
    ("telephone", "Telephone/Direct Line", False),
    ("fax", "Fax", False),
    ("website", "Website", False),
    ("type_of_ownership", "Type of Ownership", True),
    ("size_of_company", "Size of Company", True),
    ("number_of_employees", "Number of Employees", True),
]

# See the module docstring's disclosed-inference note.
GROUP_HEADERS = ["Committee Selection", "Company Information", "Contact & Classification"]
GROUP_FIELD_KEYS = {
    "Committee Selection": ["sector_committee"],
    "Company Information": [
        "applicant_name", "company_name", "cr_number", "established_since",
        "owner_name", "gm_ceo", "activity",
    ],
    "Contact & Classification": [
        "email", "mobile_number", "telephone", "fax", "website",
        "type_of_ownership", "size_of_company", "number_of_employees",
    ],
}

# Dropdown fields are driven via select_option(); every other text/number
# field via type().
SELECT_FIELDS = {"sector_committee", "established_since", "type_of_ownership", "size_of_company"}

# Fields the "counter" family (increment/decrement/boundary cases) targets.
STEPPER_FIELDS = {"number_of_employees"}

# Sample valid values used to fill every OTHER field while leaving the field
# under test empty/invalid — mirrors each case's own "fill remaining
# mandatory fields validly" step. Arbitrary but realistic; never asserted on
# except where a case names its own literal (mirrored verbatim below).
SAMPLE_VALUES = {
    "sector_committee": "Education",
    "applicant_name": "Ahmed Al-Thani",
    "company_name": "Qatar Trading Co.",
    "cr_number": "12345678901234567890",
    "established_since": "From 5-10 years",
    "owner_name": "Mohammed Al-Thani",
    "gm_ceo": "Sara Al-Kaabi",
    "activity": "Import/Export",
    "email": "info@qatartrading.qa",
    "mobile_number": "+974 5512 3456",
    "telephone": "+974 4444 5555",
    "fax": "+974 4444 5556",
    "website": "https://www.qatartrading.qa",
    "type_of_ownership": "Qatari",
    "size_of_company": "Small",
    "number_of_employees": "25",
}

# Option `value` attributes for the four dropdowns — confirmed live
# 2026-09-22 and identical on the EN and AR pages, unlike the visible labels.
# fill_all_valid() selects by these so the same data works in both locales.
SAMPLE_OPTION_VALUES = {
    "sector_committee": "education",
    "established_since": "from5To10Years",
    "type_of_ownership": "qatari",
    "size_of_company": "small",
}

# The 13 Sector/Committee values, verbatim from TC-038 (FLD-1), in order.
SECTOR_COMMITTEE_VALUES_EN = [
    "Insurance", "Education", "Registration & Membership", "Tourism & Exhibitions",
    "Services", "Banks", "Commerce", "Food Security and Environment", "Industry",
    "Arbitration", "Contracting", "Health", "Real Estate",
]


class JoinCommitteePage(BasePage):
    # ---- Root / breadcrumb / hero -------------------------------------------
    ROOT = "section.qc-cj"
    BREADCRUMB = "nav.qc-cj-crumbs"
    BREADCRUMB_ITEM = ".qc-cj-crumbs__item"
    HERO = "header.qc-cj-hero"
    HERO_TITLE = "h1.qc-cj-hero__title"
    HERO_SUBTITLE = "p.qc-cj-hero__subtitle"

    # ---- Informational section (eyebrow/heading/body) -----------------------
    INFO_SECTION = ".qc-cj-intro"
    INFO_EYEBROW = "p.qc-cj-intro__eyebrow"
    INFO_HEADING = "h2.qc-cj-intro__heading"
    INFO_BODY = "div.qc-cj-intro__body"

    # ---- Form card header (icon/title/disclaimer) ---------------------------
    FORM_CARD = ".qc-cj-card"
    FORM_CARD_ICON = "span.qc-cj-card__icon"
    FORM_CARD_TITLE = "h3.qc-cj-card__title"
    FORM_CARD_DISCLAIMER = "p.qc-cj-card__helper"

    # ---- Field groups ---------------------------------------------------------
    FORM = "form.qc-cj-form"
    GROUP = ".qc-cj-section"
    GROUP_HEADER = "span.qc-cj-section__title"
    GROUP_FIELD_LABEL = ".qc-field label.qc-field__label"
    FIELD = ".qc-field"
    FIELD_LABEL = "label.qc-field__label"
    FIELD_REQUIRED_MARK = "span.qc-field__req"

    # ---- Consent / CAPTCHA / Submit -----------------------------------------
    CONSENT_LINE = "p.qc-cj-consent"
    PRIVACY_POLICY_LINK = "a.qc-cj-consent__link"
    # reCAPTCHA Enterprise in invisible score mode (confirmed live
    # 2026-09-22: `/o/qc-recaptcha-api/config` -> mode "score", enabled true).
    # There is no visible mount node; presence is proven by the scripts, which
    # are in the server-rendered DOM, so the check does not depend on timing.
    RECAPTCHA_SCRIPT = 'script[src*="recaptcha/enterprise.js"], script[src*="qc-recaptcha.js"]'
    RECAPTCHA_IFRAME = 'iframe[src*="recaptcha"]'
    SUBMIT_BUTTON = "button.qc-cj-submit"

    # ---- Post-submit acknowledgement ----------------------------------------
    # Both nodes are in the DOM from page load with `hidden` set; only the
    # un-hidden one is a real result.
    SUCCESS_MESSAGE = "div.qc-cj-success"
    STATUS_BANNER = "div.qc-cj-status"

    # ---- Inline validation ----------------------------------------------------
    # No per-field data attribute on the error span — it is the field
    # wrapper's own last child, so `:has()` scopes by this field's confirmed
    # input id (see FIELD_NAMES / _field_locator below).
    ERROR_BY_FIELD = "div.qc-field:has(#qc-cj-{name}) span.qc-field__error"
    INVALID_INPUT_CLASS = "is-invalid"  # TODO(locator): not independently observed; mirrors this project's other forms' pattern — re-verify once a field is actually driven invalid

    # Field key -> the confirmed `id` suffix the live form uses
    # (`#qc-cj-<value>`). Drives both the field locators and the error
    # locators.
    FIELD_NAMES = {
        "sector_committee": "sectorCommittee",
        "applicant_name": "applicantName",
        "company_name": "companyName",
        "cr_number": "crNumber",
        "established_since": "establishedSince",
        "owner_name": "ownerName",
        "gm_ceo": "generalManagerCeo",
        "activity": "activity",
        "email": "email",
        "mobile_number": "mobileNumber",
        "telephone": "telephoneNumber",
        "fax": "fax",
        "website": "website",
        "type_of_ownership": "typeOfOwnership",
        "size_of_company": "sizeOfCompany",
        "number_of_employees": "numberOfEmployees",
    }

    # Number-of-Employees stepper: a custom counter (+/- buttons around a
    # numeric input), confirmed live — matches 143489/143491's
    # "increment/decrement control" wording.
    EMPLOYEES_INCREMENT = "div.qc-field__counter button.qc-field__counter-btn:last-of-type"  # "+" button
    EMPLOYEES_DECREMENT = "div.qc-field__counter button.qc-field__counter-btn:first-of-type"  # "−" button
    EMPLOYEES_VALUE = "#qc-cj-numberOfEmployees"  # counter's own numeric input (value read via input_value(), not text)

    def __init__(self, page):
        super().__init__(page)
        self.accessibility_tools = AccessibilityToolsComponent(page)

    # ---- Field locator helper -------------------------------------------------
    def _field_locator(self, field_key: str) -> str:
        # Confirmed live: every field carries a stable, unique `#qc-cj-<name>`
        # id — no `name` attribute confirmed, so this now resolves by id
        # rather than the originally-guessed `[name=...]` CSS attribute
        # selector. FORM prefix kept for scoping consistency.
        name = self.FIELD_NAMES[field_key]
        return f"{self.FORM} #qc-cj-{name}"

    # ---- Navigation --------------------------------------------------------
    def open_join_committee(self, locale: str = "en") -> "JoinCommitteePage":
        self.open(web_url(JOIN_COMMITTEE_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    # ---- Breadcrumb / hero ---------------------------------------------------
    def breadcrumb_text(self) -> str:
        return " / ".join(t.strip() for t in self.page.locator(self.BREADCRUMB_ITEM).all_inner_texts())

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_subtitle_text(self) -> str:
        return self.text(self.HERO_SUBTITLE).strip()

    # ---- Informational section -----------------------------------------------
    def info_eyebrow_text(self) -> str:
        return self.text(self.INFO_EYEBROW).strip()

    def info_heading_text(self) -> str:
        return self.text(self.INFO_HEADING).strip()

    def info_body_text(self) -> str:
        return self.text(self.INFO_BODY).strip()

    # ---- Form card header ------------------------------------------------------
    def form_card_icon_is_visible(self) -> bool:
        return self.is_visible(self.FORM_CARD_ICON)

    def form_card_title_text(self) -> str:
        return self.text(self.FORM_CARD_TITLE).strip()

    def form_card_disclaimer_text(self) -> str:
        return self.text(self.FORM_CARD_DISCLAIMER).strip()

    # ---- Field groups -----------------------------------------------------------
    def group_header_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.GROUP_HEADER).all_inner_texts()]

    def group_field_labels(self, group_index: int) -> list:
        """Field label texts within the nth group (0-based), in render
        order — compared against GROUP_FIELD_KEYS' declared order."""
        group = self.page.locator(self.GROUP).nth(group_index)
        return [t.strip() for t in group.locator(self.FIELD_LABEL).all_inner_texts()]

    # ---- Consent / Privacy Policy -----------------------------------------------
    def consent_text(self) -> str:
        return self.text(self.CONSENT_LINE).strip()

    def privacy_policy_link_text(self) -> str:
        return self.text(self.PRIVACY_POLICY_LINK).strip()

    def privacy_policy_link_style(self) -> dict:
        return self.page.locator(self.PRIVACY_POLICY_LINK).evaluate(
            """
            (a) => {
                const s = getComputedStyle(a);
                return { fontWeight: s.fontWeight, tagName: a.tagName.toLowerCase(),
                         href: a.getAttribute('href'), target: a.getAttribute('target') };
            }
            """
        )

    def click_privacy_policy_link(self):
        """Clicks the inline Privacy Policy link and returns the page showing
        the Privacy Policy: the new tab when the link has target=_blank, else
        this page after same-tab navigation (the live link has no target)."""
        target = self.get_attribute(self.PRIVACY_POLICY_LINK, "target")
        if target == "_blank":
            with self.page.context.expect_page(timeout=10000) as new_page_info:
                self.click(self.PRIVACY_POLICY_LINK)
            return new_page_info.value
        self.click(self.PRIVACY_POLICY_LINK)
        self.page.wait_for_url("**/privacy-policy**", timeout=30000)
        return self.page

    # ---- Submit button / CAPTCHA -----------------------------------------------
    def submit_button_text(self) -> str:
        return self.text(self.SUBMIT_BUTTON).strip()

    def submit_button_is_enabled(self) -> bool:
        return self.page.locator(self.SUBMIT_BUTTON).is_enabled()

    def captcha_state(self) -> dict:
        return self.page.evaluate(
            """
            () => {
                const scripts = document.querySelectorAll(
                    'script[src*="recaptcha/enterprise.js"], script[src*="qc-recaptcha.js"]');
                const frames = Array.from(document.querySelectorAll('iframe[src*="recaptcha"]'));
                return {
                    scriptPresent: scripts.length > 0,
                    enterpriseScript: !!document.querySelector('script[src*="recaptcha/enterprise.js"]'),
                    recaptchaFrames: frames.length,
                    recaptchaLoaded: frames.some((f) => f.getBoundingClientRect().width > 0),
                };
            }
            """
        )

    def submit_form(self) -> "JoinCommitteePage":
        self.click(self.SUBMIT_BUTTON)
        return self

    def submit_and_wait_result(self, timeout: int = 30000) -> "JoinCommitteePage":
        """Submits and waits for a VISIBLE result: the success box, the
        status/error banner, or an inline field error. The success and status
        nodes exist hidden from page load, so presence alone proves nothing."""
        self.click(self.SUBMIT_BUTTON)
        self.page.wait_for_function(
            """() => document.querySelector('.qc-cj-success:not([hidden])') ||
                     document.querySelector('.qc-cj-status:not([hidden])') ||
                     document.querySelector('.qc-field .is-invalid')""",
            timeout=timeout,
        )
        return self

    # ---- Fields ------------------------------------------------------------------
    def fill_field(self, field_key: str, value: str) -> None:
        locator = self._field_locator(field_key)
        if field_key in SELECT_FIELDS:
            self.select_option(locator, label=value)
        else:
            self.type(locator, value)

    def field_value(self, field_key: str) -> str:
        return self.page.locator(self._field_locator(field_key)).input_value()

    def field_error_text(self, field_key: str) -> str:
        locator = self.ERROR_BY_FIELD.format(name=self.FIELD_NAMES[field_key])
        return self.text(locator).strip()

    def field_is_marked_invalid(self, field_key: str) -> bool:
        classes = self.page.locator(self._field_locator(field_key)).get_attribute("class") or ""
        return self.INVALID_INPUT_CLASS in classes.split()

    def fill_all_valid(self, overrides: dict | None = None, skip: str | None = None) -> "JoinCommitteePage":
        """Fills every field from SAMPLE_VALUES, optionally skipping one
        field key (left empty) and/or overriding others — mirrors each
        case's own 'fill remaining mandatory fields validly' step."""
        # The server refuses a repeat of the same request within a few minutes
        # (409 "duplicate"), which would masquerade as a rejection in any
        # later test — so CR Number and Email are unique per fill.
        stamp = f"{time.time_ns() // 1000:020d}"[-20:]
        unique = {"cr_number": stamp, "email": f"qa.auto.{stamp}@qatartrading.qa"}
        values = {**SAMPLE_VALUES, **unique, **(overrides or {})}
        for key, _label, _required in FIELD_TABLE:
            if key == skip:
                continue
            value = values.get(key)
            if value is None:
                continue
            if key in STEPPER_FIELDS:
                self.set_number_of_employees(int(value))
            elif key in SELECT_FIELDS and key not in (overrides or {}):
                self.select_option(self._field_locator(key), value=SAMPLE_OPTION_VALUES[key])
            else:
                self.fill_field(key, value)
        return self

    def dropdown_options(self, field_key: str) -> list:
        locator = self._field_locator(field_key)
        # Options load asynchronously after the placeholder; the placeholder
        # itself (value="") is not one of the selectable values.
        self.page.wait_for_function(
            "(sel) => document.querySelector(sel).options.length > 1",
            arg=locator, timeout=30000,
        )
        options = self.page.locator(f'{locator} option:not([value=""])').all_inner_texts()
        return [t.strip() for t in options if t.strip()]

    # ---- Number of Employees stepper -------------------------------------------
    def employees_value(self) -> int:
        # The counter <input> has no `value` attribute; the live value is only
        # readable through input_value().
        raw = self.page.locator(self.EMPLOYEES_VALUE).input_value().strip()
        return int(raw) if raw.isdigit() else 0

    def increment_employees(self, times: int = 1) -> "JoinCommitteePage":
        for _ in range(times):
            self.click(self.EMPLOYEES_INCREMENT)
        return self

    def decrement_employees(self, times: int = 1) -> "JoinCommitteePage":
        for _ in range(times):
            self.click(self.EMPLOYEES_DECREMENT)
        return self

    def set_number_of_employees(self, value: int) -> "JoinCommitteePage":
        current = self.employees_value()
        if value > current:
            self.increment_employees(value - current)
        elif value < current:
            self.decrement_employees(current - value)
        return self

    def employees_decrement_is_disabled(self) -> bool:
        return not self.page.locator(self.EMPLOYEES_DECREMENT).is_enabled()

    # ---- Success screen ------------------------------------------------------
    def success_message_text(self) -> str:
        return self.text(self.SUCCESS_MESSAGE).strip()

    def success_message_is_visible(self) -> bool:
        return self.is_visible(self.SUCCESS_MESSAGE)

    def status_banner_text(self) -> str:
        banner = self.page.locator(self.STATUS_BANNER)
        return banner.inner_text().strip() if banner.is_visible() else ""

    def success_message_direction(self) -> str:
        return self.page.locator(self.SUCCESS_MESSAGE).evaluate(
            "(el) => getComputedStyle(el).direction"
        )

    # ---- Theme / contrast (via the shared accessibility widget) -----------------
    def enable_dark_mode(self) -> "JoinCommitteePage":
        self.accessibility_tools.enable_dark_mode()
        return self

    def is_dark_mode_active(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('data-theme') === 'dark'"
        )

    def enable_high_contrast(self) -> "JoinCommitteePage":
        self.accessibility_tools.enable_high_contrast()
        return self

    def is_high_contrast_active(self) -> bool:
        return self.accessibility_tools.is_high_contrast_active()

    # ---- Compatibility measurement helpers --------------------------------------
    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def layout_boxes(self) -> dict:
        """Bounding boxes of the hero, info section and form card — used by
        the desktop/tablet/mobile breakpoint cases to assert no overlap."""
        return self.page.evaluate(
            """
            () => {
                const b = (s) => {
                    const el = document.querySelector(s);
                    return el ? el.getBoundingClientRect() : null;
                };
                const rect = (r) => r && ({ x: r.x, y: r.y, right: r.right, bottom: r.bottom,
                                             width: r.width, height: r.height });
                return {
                    hero: rect(b('.qc-cj-hero')),
                    info: rect(b('.qc-cj-intro')),
                    card: rect(b('.qc-cj-card')),
                };
            }
            """
        )

    # ---- Deep-link / access-control -----------------------------------------
    def open_submissions_review_as_visitor(self) -> "JoinCommitteePage":
        """Navigates directly to the admin-only submissions-review URL. Used
        by 143427 with an unauthenticated `page` fixture
        (`@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)`)."""
        self.page.goto(control_panel_url(SUBMISSIONS_REVIEW_PATH))
        return self

    def is_on_login_or_denied(self) -> bool:
        url = self.page.url.lower()
        if "login" in url or "sign-in" in url:
            return True
        # TODO(locator): confirmed "access denied" indicator once the real
        # admin surface responds — falls back to a plain URL/login check.
        return self.is_visible("text=Access Denied") or self.is_visible("text=403")

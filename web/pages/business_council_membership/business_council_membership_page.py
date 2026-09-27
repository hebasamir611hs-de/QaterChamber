"""
web/pages/business_council_membership/business_council_membership_page.py —
BusinessCouncilMembershipPage.

Public-frontend Page Object for PBI 130719 (QC - Councils, Committees &
Partnerships - 004 - Business Council Membership Request), scripted from the
75 `Automation`-tagged, `Web`-platform cases in the injected Azure DevOps
suite handed off by the QA Manager (Control_Panel-tagged and non-automated
cases already excluded from that hand-off).

LOCATORS — CLI-first, verified live 2026-09-22 (qcdev)
------------------------------------------------------------------
Real path resolved via the Liferay nav-items REST API
(`/o/c/navitems/scopes/37246?...`):
`/web/qatar-chamber/business-council-membership-request`. An ad-hoc
structural dump (scripted `document.querySelectorAll` class/id walk, not
MCP) confirmed the CSS namespace guessed originally (`qc-bcm-*`) IS the real
one, in BEM form (`qc-bcm-hero__title`, `qc-bcm-crumbs__item`, etc.) — and
the shared `qc-field__*` field-chrome classes already confirmed for
`join_committee_page.py` are reused here too. Every field carries a stable,
unique `id` (`#qc-bcm-*`) — the framework's highest confirmed tier — so the
per-field templates below now resolve by `:has(#qc-bcm-<id>)` rather than
the originally-guessed `[data-field='<key>']` attribute (which does not
exist on the live DOM). See `FIELD_IDS` and `_locator_for()`.

The 3-group structure (Country Priorities / Applicant & Company / Contact &
Activity) IS confirmed live and matches the docstring's original structural
assumption exactly.

CAPTCHA — RESOLVED 2026-09-22 (was the single biggest source of broken
tests in this module). `div.qc-bcm-captcha` is a confirmed, unique mount
(count == 1) that renders **empty and zero-sized** — `innerHTML == ""`,
zero child iframes, `is_visible() == False`. The page loads
`https://www.google.com/recaptcha/enterprise.js?render=<site-key>` and
exposes a `window.grecaptcha` global: this is **reCAPTCHA Enterprise v3,
invisible / score-based**. There is no checkbox, no image challenge, and no
user-facing "solved" state — the token is minted by `grecaptcha.execute()`
when the form is submitted. The old `CAPTCHA_CHECKBOX` constant (a prose
`TODO(locator):` string) has been REMOVED: it was being fed straight into
`Locator.click()` and died in Playwright's CSS parser, taking 37 tests with
it. Anything that needs to reason about the widget now uses
`is_captcha_mounted()`; there is deliberately no `solve_captcha()` /
`fail_captcha_challenge()`, because neither action exists on this form.

Field validation is INDEPENDENT of the CAPTCHA — verified live: submitting
an empty form with zero CAPTCHA interaction renders
`span.qc-field__error` ("This field is required.") under every invalid
field plus a `div.qc-bcm-status` banner ("Please correct the highlighted
fields."), while `div.qc-bcm-success` stays hidden. Validation tests must
therefore never touch the CAPTCHA.
"""

from config.settings import web_url
from core.web.base_page import BasePage

BUSINESS_COUNCIL_MEMBERSHIP_PATH = "/web/qatar-chamber/business-council-membership-request"

# Logical field keys used throughout the page object and the test module —
# stable regardless of the real DOM id, which FIELD_IDS below maps to.
COUNTRY_FIELDS = ("country_1", "country_2", "country_3", "country_4")
REQUIRED_TEXT_FIELDS = ("applicant_name", "company_name", "email", "mobile_number", "company_activity")
OPTIONAL_TEXT_FIELDS = ("cr_number", "owner_name", "telephone", "fax", "website")
ALL_FIELDS = COUNTRY_FIELDS + REQUIRED_TEXT_FIELDS + OPTIONAL_TEXT_FIELDS

GROUP_APPLICANT_COMPANY_FIELDS = ("applicant_name", "company_name", "cr_number", "owner_name")
GROUP_CONTACT_ACTIVITY_FIELDS = ("email", "mobile_number", "telephone", "fax", "website", "company_activity")

# Logical field key -> confirmed live `id` suffix (`#qc-bcm-<value>`).
FIELD_IDS = {
    "country_1": "country1",
    "country_2": "country2",
    "country_3": "country3",
    "country_4": "country4",
    "applicant_name": "applicantName",
    "company_name": "companyName",
    "cr_number": "crNumber",
    "owner_name": "ownerName",
    "email": "email",
    "mobile_number": "mobileNumber",
    "telephone": "telephoneDirectLine",
    "fax": "fax",
    "website": "website",
    "company_activity": "companyActivity",
}


class BusinessCouncilMembershipPage(BasePage):
    # ---- Root / hero -------------------------------------------------------
    ROOT = "section.qc-bcm"
    HERO = "header.qc-bcm-hero"
    HERO_HEADING = "h1.qc-bcm-hero__title"
    HERO_SUBTITLE = "p.qc-bcm-hero__subtitle"

    # ---- Breadcrumb ---------------------------------------------------------
    BREADCRUMB = "nav.qc-bcm-crumbs"
    BREADCRUMB_ITEM = ".qc-bcm-crumbs__item"

    # ---- Informational section ----------------------------------------------
    INFO_SECTION = ".qc-bcm-intro"
    INFO_EYEBROW = "p.qc-bcm-intro__eyebrow"
    INFO_HEADING = "h2.qc-bcm-intro__heading"
    INFO_BODY = "div.qc-bcm-intro__body"
    # The container above is a plain wrapper and reports the INHERITED base
    # colour (rgb(29,29,27)); the Figma grey #6C6C6B is set on its <p>
    # children (3 of them, all identical — verified live 2026-09-22). Style
    # probes must therefore read the paragraph, not the wrapper.
    INFO_BODY_PARAGRAPH = "div.qc-bcm-intro__body p"

    # ---- Form card ------------------------------------------------------------
    FORM_CARD = ".qc-bcm-card"
    FORM_ICON_BOX = "span.qc-bcm-card__icon"
    FORM_TITLE = "h3.qc-bcm-card__title"
    FORM_HELPER_TEXT = "p.qc-bcm-card__helper"
    FORM = "form.qc-bcm-form"

    # ---- Sub-headers (one per field group) -----------------------------------
    # TODO(locator): no separate divider element observed alongside the
    # section title on the live form (styling likely comes from the section
    # border itself, not a distinct child node) — SUB_HEADER_DIVIDER left
    # pointing at the section title's own selector so it resolves rather than
    # silently matching nothing; flag to devs if a dedicated divider node is
    # expected.
    SUB_HEADER = "span.qc-bcm-section__title"
    SUB_HEADER_DIVIDER = "span.qc-bcm-section__title"
    FIELD_GROUP = ".qc-bcm-section"

    # ---- Generic field row (label + control), by logical field key ----------
    # {field} is substituted with FIELD_IDS[field_key] (the real `id` suffix)
    # at call time via _locator_for() — NOT the field_key itself, since the
    # live DOM has no `data-field` attribute.
    FIELD_ROW_TEMPLATE = "div.qc-field:has(#qc-bcm-{field})"
    FIELD_LABEL_TEMPLATE = "div.qc-field:has(#qc-bcm-{field}) label.qc-field__label"
    FIELD_REQUIRED_MARK_TEMPLATE = "div.qc-field:has(#qc-bcm-{field}) span.qc-field__req"
    FIELD_CONTROL_TEMPLATE = "#qc-bcm-{field}"
    FIELD_ERROR_TEMPLATE = "div.qc-field:has(#qc-bcm-{field}) span.qc-field__error"

    # ---- Mobile Number field (+974 prefix chip) ------------------------------
    MOBILE_PREFIX_CHIP = "span.qc-field__phone-code"  # "+974" chip, scoped uniquely under the Mobile Number field
    MOBILE_DIGITS_INPUT = "#qc-bcm-mobileNumber"

    # ---- Company Activity textarea -------------------------------------------
    COMPANY_ACTIVITY_TEXTAREA = "#qc-bcm-companyActivity"

    # ---- Consent line + Submit -----------------------------------------------
    CONSENT_LINE = "p.qc-bcm-consent"
    SUBMIT_BUTTON = "button.qc-bcm-submit"
    SUBMIT_ICON = "button.qc-bcm-submit svg, button.qc-bcm-submit img"

    # ---- CAPTCHA (invisible reCAPTCHA Enterprise v3 — see module docstring) --
    # There is NO CAPTCHA_CHECKBOX. The mount below is present exactly once
    # but renders empty and zero-sized, so it is queried by COUNT, never by
    # visibility, and never clicked.
    CAPTCHA_MOUNT = "div.qc-bcm-captcha"
    CAPTCHA_REQUIRED_MESSAGE = "div.qc-field:has(.qc-bcm-captcha) span.qc-field__error"

    # ---- Post-submit feedback -------------------------------------------------
    CONFIRMATION_MESSAGE = "div.qc-bcm-success"
    DUPLICATE_MESSAGE = "div.qc-bcm-status"  # TODO(locator): a generic top-of-form status banner is confirmed to exist, but no dedicated "duplicate" variant/class was observed live — re-verify once a duplicate submission is actually triggered

    # ---- Field -> locator constant name map (for computed-style/box probes) -
    _FIELD_LOCATOR_TEMPLATES = {
        "row": FIELD_ROW_TEMPLATE,
        "label": FIELD_LABEL_TEMPLATE,
        "required_mark": FIELD_REQUIRED_MARK_TEMPLATE,
        "control": FIELD_CONTROL_TEMPLATE,
        "error": FIELD_ERROR_TEMPLATE,
    }

    # ---- Navigation -----------------------------------------------------------
    def open_membership_request(self, locale: str = "en") -> "BusinessCouncilMembershipPage":
        """Open the public Business Council Membership Request page."""
        self.open(web_url(BUSINESS_COUNCIL_MEMBERSHIP_PATH, locale=locale))
        self.wait_for(self.HERO_HEADING, state="visible", timeout=30000)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_language(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    def page_title(self) -> str:
        return self.page.title()

    # ---- Generic measurement helpers (mirrors legal_consultation_page.py) ----
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

    # ---- Hero -------------------------------------------------------------
    def hero_heading_text(self) -> str:
        return self.text(self.HERO_HEADING).strip()

    def hero_heading_style(self) -> dict:
        return self.computed_style(
            self.HERO_HEADING,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
        )

    def hero_subtitle_text(self) -> str:
        return self.text(self.HERO_SUBTITLE).strip()

    def hero_subtitle_style(self) -> dict:
        return self.computed_style(
            self.HERO_SUBTITLE,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "width"],
        )

    # ---- Breadcrumb ---------------------------------------------------------
    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.BREADCRUMB_ITEM).all_inner_texts()]

    def click_breadcrumb_segment(self, text: str) -> None:
        self.page.locator(self.BREADCRUMB_ITEM, has_text=text).click()

    # ---- Informational section ----------------------------------------------
    def info_eyebrow_text(self) -> str:
        return self.text(self.INFO_EYEBROW).strip()

    def info_eyebrow_style(self) -> dict:
        return self.computed_style(self.INFO_EYEBROW, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"])

    def info_heading_text(self) -> str:
        return self.text(self.INFO_HEADING).strip()

    def info_heading_style(self) -> dict:
        return self.computed_style(self.INFO_HEADING, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"])

    def info_body_text(self) -> str:
        return self.text(self.INFO_BODY).strip()

    def info_body_style(self) -> dict:
        # Reads the <p>, not the wrapper — see INFO_BODY_PARAGRAPH's note.
        return self.computed_style(
            self.INFO_BODY_PARAGRAPH,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
        )

    # ---- Form card ------------------------------------------------------------
    def form_title_text(self) -> str:
        return self.text(self.FORM_TITLE).strip()

    def form_title_style(self) -> dict:
        return self.computed_style(self.FORM_TITLE, ["fontFamily", "fontWeight", "fontSize", "color"])

    def form_helper_text(self) -> str:
        return self.text(self.FORM_HELPER_TEXT).strip()

    def form_helper_style(self) -> dict:
        return self.computed_style(self.FORM_HELPER_TEXT, ["fontFamily", "fontWeight", "fontSize", "color"])

    def icon_box_metrics(self) -> dict:
        box = self.box(self.FORM_ICON_BOX)
        style = self.computed_style(self.FORM_ICON_BOX, ["border", "borderRadius", "backgroundColor"])
        return {**box, **style}

    def form_card_style(self) -> dict:
        return self.computed_style(
            self.FORM_CARD,
            ["padding", "backgroundColor", "border", "borderRadius", "boxShadow"],
        )

    # ---- Sub-headers ----------------------------------------------------------
    def sub_header_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.SUB_HEADER).all_inner_texts()]

    def sub_header_style(self, index: int) -> dict:
        return self.computed_style(self.SUB_HEADER, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"], index=index)

    def sub_header_divider_visible(self, index: int) -> bool:
        return self.page.locator(self.SUB_HEADER_DIVIDER).nth(index).is_visible()

    # ---- Generic field queries ------------------------------------------------
    def _locator_for(self, kind: str, field_key: str) -> str:
        # Substitutes the confirmed live `id` suffix (FIELD_IDS), not the
        # logical field_key itself — the DOM has no `data-field` attribute.
        return self._FIELD_LOCATOR_TEMPLATES[kind].format(field=FIELD_IDS[field_key])

    def field_label_text(self, field_key: str) -> str:
        return self.text(self._locator_for("label", field_key)).strip()

    def field_required_mark_style(self, field_key: str) -> dict:
        return self.computed_style(self._locator_for("required_mark", field_key), ["fontFamily", "fontWeight", "color"])

    def field_row_box(self, field_key: str) -> dict:
        return self.box(self._locator_for("row", field_key))

    def field_control_box_style(self, field_key: str) -> dict:
        """Padding/gap of the CONTROL itself (`#qc-bcm-<id>`), which is what
        the Figma field spec describes.

        Not the `div.qc-field` row: that wrapper only stacks label over input
        (`display:flex; flex-direction:column`) and correctly computes
        `padding: 0px`, which is why measuring it reported "0px" against an
        expected "11px 12px". The control carries the real 11px/12px inner
        padding (verified live 2026-09-22).
        """
        return self.computed_style(self._locator_for("control", field_key), ["padding", "gap"])

    def field_error_text(self, field_key: str) -> str:
        locator = self._locator_for("error", field_key)
        if not self.is_visible(locator):
            return ""
        return self.text(locator).strip()

    def is_field_error_visible(self, field_key: str) -> bool:
        return self.is_visible(self._locator_for("error", field_key))

    def field_value(self, field_key: str) -> str:
        """The control's LIVE value (`input_value()`), i.e. what the user
        typed. Not `get_attribute("value")`: typing does not update the HTML
        attribute, so that read returns None for a filled field."""
        return self.page.locator(self._locator_for("control", field_key)).input_value()

    def control_placeholder(self, field_key: str) -> str | None:
        return self.get_attribute(self._locator_for("control", field_key), "placeholder")

    def control_style(self, field_key: str) -> dict:
        return self.computed_style(self._locator_for("control", field_key), ["fontFamily", "fontWeight", "fontSize", "color"])

    def blur_field(self, field_key: str) -> None:
        """Focus then blur a field with no value entered — used by the
        real-time inline-validation cases (e.g. 144504)."""
        control = self.page.locator(self._locator_for("control", field_key))
        control.click()
        self.page.keyboard.press("Tab")

    # ---- Country dropdowns -----------------------------------------------------
    def select_country(self, index: int, country_code: str) -> None:
        """Select Country 1..4 by its ISO 3166-1 alpha-2 option VALUE.

        `index` is 1-4. `country_code` is the option's `value` ("GB", "DE",
        ...), never its visible label — verified live 2026-09-22: both
        locales serve the same 250 options with identical ISO `value`s, but
        the labels are localised ("United Kingdom" vs "المملكة المتحدة"), so
        selecting by label times out on the AR page with "did not find some
        options". Selecting by value is locale-independent and is the only
        correct strategy for this bilingual form.
        """
        self.select_option(self._locator_for("control", f"country_{index}"), value=country_code)

    def country_dropdown_options(self, index: int) -> list:
        locator = self._locator_for("control", f"country_{index}")
        return [t.strip() for t in self.page.locator(f"{locator} option").all_inner_texts()]

    def is_country_dropdown_empty(self, index: int) -> bool:
        return len(self.country_dropdown_options(index)) == 0

    # ---- Text/select field fill -------------------------------------------------
    def fill_field(self, field_key: str, value: str) -> None:
        if field_key in COUNTRY_FIELDS:
            self.select_country(int(field_key.rsplit("_", 1)[1]), value)
        elif field_key == "mobile_number":
            self.type(self.MOBILE_DIGITS_INPUT, value)
        elif field_key == "company_activity":
            self.type(self.COMPANY_ACTIVITY_TEXTAREA, value)
        else:
            self.type(self._locator_for("control", field_key), value)

    def fill_form(self, data: dict) -> "BusinessCouncilMembershipPage":
        """Fill every field present in `data` (field_key -> value). Fields
        not present are left untouched — used by every negative case to
        fill everything EXCEPT the one field under test."""
        for field_key, value in data.items():
            self.fill_field(field_key, value)
        return self

    # ---- Mobile Number prefix chip --------------------------------------------
    def mobile_prefix_text(self) -> str:
        return self.text(self.MOBILE_PREFIX_CHIP).strip()

    def mobile_prefix_style(self) -> dict:
        return self.computed_style(self.MOBILE_PREFIX_CHIP, ["color", "borderColor"])

    def is_mobile_prefix_editable(self) -> bool:
        return not (self.get_attribute(self.MOBILE_PREFIX_CHIP, "contenteditable") in (None, "false"))

    # ---- Company Activity textarea --------------------------------------------
    def textarea_metrics(self) -> dict:
        """Bounding box (numeric px) merged with the computed style.

        "height" is deliberately NOT in the computed-style list: the two dicts
        are merged, so a CSS string ("140px") would overwrite the bounding
        box's numeric height and break any arithmetic a caller does on it
        (`round(metrics["height"])` raised TypeError: type str doesn't define
        __round__). Numeric geometry comes from the box, strings from the
        style — no key may appear in both.
        """
        box = self.box(self.COMPANY_ACTIVITY_TEXTAREA)
        style = self.computed_style(self.COMPANY_ACTIVITY_TEXTAREA, ["padding", "border", "borderRadius"])
        return {**box, **style}

    # ---- Field groups (order + membership) -------------------------------------
    def group_header_positions(self) -> list:
        return self.page.evaluate(
            f"""
            () => Array.from(document.querySelectorAll({self.SUB_HEADER!r}))
                .map((el) => ({{ text: el.textContent.trim(), y: el.getBoundingClientRect().y }}))
            """
        )

    # ---- Consent line -----------------------------------------------------------
    def consent_text(self) -> str:
        return self.text(self.CONSENT_LINE).strip()

    def consent_style(self) -> dict:
        return self.computed_style(self.CONSENT_LINE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "textAlign"])

    # ---- Submit button ------------------------------------------------------------
    def submit_button_text(self) -> str:
        return self.text(self.SUBMIT_BUTTON).strip()

    def is_submit_icon_visible(self) -> bool:
        return self.is_visible(self.SUBMIT_ICON)

    def submit_icon_box(self) -> dict:
        return self.box(self.SUBMIT_ICON)

    # ---- CAPTCHA (invisible / score-based — see module docstring) ---------------
    def is_captcha_mounted(self) -> bool:
        """True when the invisible reCAPTCHA Enterprise mount is present on
        the form.

        Deliberately a COUNT check, not a visibility check: the mount renders
        empty and zero-sized by design, so `is_visible()` is correctly False
        and would be the wrong question to ask. This is the only state this
        widget exposes to a UI test — there is no checkbox to click, no
        challenge to answer, and no "solved" flag; `grecaptcha.execute()`
        mints the score token during submit. Callers assert on the
        POST-SUBMIT outcome (confirmation vs. error), never on a CAPTCHA
        interaction.
        """
        return self.page.locator(self.CAPTCHA_MOUNT).count() == 1

    def captcha_required_message(self) -> str:
        if not self.is_visible(self.CAPTCHA_REQUIRED_MESSAGE):
            return ""
        return self.text(self.CAPTCHA_REQUIRED_MESSAGE).strip()

    # ---- Submit + feedback ----------------------------------------------------------
    def submit(self) -> "BusinessCouncilMembershipPage":
        self.click(self.SUBMIT_BUTTON)
        return self

    def confirmation_text(self) -> str:
        self.wait_for(self.CONFIRMATION_MESSAGE, state="visible", timeout=30000)
        return self.text(self.CONFIRMATION_MESSAGE).strip()

    def is_confirmation_visible(self) -> bool:
        """INSTANT read, no waiting. Use it only to assert that the success
        message must NOT appear (e.g. right after a client-side validation
        block). For a positive check use `has_submission_succeeded()`: after
        Submit the button shows "Submitting…" while reCAPTCHA and the request
        run, so an instant read comes back False on a submit that is about to
        succeed."""
        return self.is_visible(self.CONFIRMATION_MESSAGE)

    # Any of these being visible means the submit has finished: the success
    # message, the status banner (duplicate / "Please correct the highlighted
    # fields."), or an inline field error.
    _SUBMIT_OUTCOME = (
        "div.qc-bcm-success:visible, div.qc-bcm-status:visible, span.qc-field__error:visible"
    )

    def wait_for_submit_outcome(self, timeout: int = 30000) -> bool:
        """Wait until the submit has an outcome (success, status banner, or a
        field error). Returns False if none appears within `timeout`; never
        raises, so the caller's assertion reports the failure."""
        try:
            self.page.locator(self._SUBMIT_OUTCOME).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001 — timeout is reported by the caller's assert
            return False

    def has_submission_succeeded(self, timeout: int = 30000) -> bool:
        """Positive success check: waits for the submit outcome first, then
        reports whether that outcome is the success message."""
        self.wait_for_submit_outcome(timeout)
        return self.is_visible(self.CONFIRMATION_MESSAGE)

    def duplicate_message_text(self) -> str:
        return self.text(self.DUPLICATE_MESSAGE).strip()

    def is_duplicate_message_visible(self) -> bool:
        """Positive check, so it waits for the submit outcome first (same
        reason as `has_submission_succeeded()`)."""
        self.wait_for_submit_outcome()
        return self.is_visible(self.DUPLICATE_MESSAGE)

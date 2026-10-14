"""
web/pages/qafl_membership/qafl_membership_page.py — QaflMembershipPage.

Public-frontend Page Object for PBI 130718 (QC - Councils, Committees &
Partnerships - 003 - QAFL Membership Registration): hero + breadcrumb,
association overview, "Required template" card, 5-step progress indicator
and the 5-step wizard form (Company Identity / Senior Executive /
Responsible Manager / Company Location / Supporting Documents).

LOCATOR PROVENANCE — OFFLINE, 2026-10-07
----------------------------------------
No browser was run (another live session owned qcdev). Every constant below
was read off an ANONYMOUS read-only HTTP GET of the public page, saved as
  reports/locators/qafl_membership/qafl_membership_en.html
  reports/locators/qafl_membership/qafl_membership_ar.html
The fragment is server-rendered markup plus an inline script, so the class
names, `name=` attributes, `data-role` hooks, the validator, the step
switcher and the submit handler are all present in that HTML verbatim.
What a static GET cannot show (JS-rendered menu, list-fed <select> option
VALUES, the Liferay toast container) is marked `# UNVERIFIED`.

Facts read off the fragment script (they shape the wrappers below):
  * Steps are `fieldset.qc-qafl-step[data-step=N]`; the inactive ones carry
    the `hidden` attribute. Progress badges `li.qc-qafl-steps__item` get
    `is-active` / `is-done`. Next/Prev/Submit are `[data-role=...]` buttons.
  * Every field is a `.qc-qafl-field` wrapper with ONE control (`[name=X]`)
    and ONE `em[data-role=err]`. The em is always in the DOM (empty when the
    field is valid), so an error is "wrapper has `is-invalid` AND em text is
    non-empty" — never `is_visible(em)`.
  * The required asterisk is CSS `::after { content: " *" }` on the label
    span (`[data-required]`, `[data-cond-required]`, `.is-required-now`),
    so it is read via getComputedStyle(span, '::after').
  * Validation runs on `input`, `change`, `blur` and Next/Submit, all
    synchronously; a rejected file is reverted to the last accepted file.
  * Success = `div.qc-qafl-ack[data-role=ack]` un-hidden (form hidden).
    Duplicate / generic failure = Liferay.Util.openToast (no fragment DOM).
"""

from config.settings import web_url
from core.web.base_page import BasePage

QAFL_MEMBERSHIP_PATH = "/web/qatar-chamber/qafl-membership"
HOME_PATH = "/web/qatar-chamber"

# Control `name` -> kind. Drives set_field()'s dispatch. Every name below is
# confirmed verbatim in the saved HTML.
FIELD_KINDS = {
    # Step 1
    "companyEnglishName": "text",
    "companyArabicName": "text",
    "companyRegisteredUnder": "select",
    "verifiedOnQatarCommercialDirectory": "radio",
    "crNumber": "text",
    "uploadCrCopy": "file",
    "qatarChamberMembershipNumber": "text",
    "uploadQatarChamberMembershipCopy": "file",
    "qfcNumber": "text",
    "qfcMembershipCopy": "file",
    "qfzNumber": "text",
    "qfzMembershipCopy": "file",
    "companyRegisteredUnderOther": "text",
    "companyRegisteredUnderOtherMembershipCopy": "file",
    "companySize": "radio",
    "companySizeOther": "text",
    "companyType": "select",
    "companyTypeOther": "text",
    "marketPresence": "radio",
    "regionalMarkets": "text",
    "internationalMarkets": "text",
    "marketPresenceOther": "text",
    # Step 2
    "seniorExecutiveName": "text",
    "seniorExecutiveDesignation": "text",
    "seniorExecutiveEmail": "text",
    "seniorExecutiveConfirmEmail": "text",
    "seniorExecutivePhone": "text",
    "seniorExecutiveExtension": "text",
    "seniorExecutiveMobile": "text",
    # Step 3
    "responsibleManagerName": "text",
    "responsibleManagerDesignation": "text",
    "responsibleManagerEmail": "text",
    "responsibleManagerConfirmEmail": "text",
    "responsibleManagerPhone": "text",
    "responsibleManagerExtension": "text",
    "responsibleManagerMobile": "text",
    # Step 4
    "website": "text",
    "locationName": "text",
    "buildingNumber": "text",
    "zoneNumber": "text",
    "streetNumber": "text",
    # Step 5
    "qaflMembershipAuthorizationLetter": "file",
    "authorizedPersonQatarIdFront": "file",
    "authorizedPersonQatarIdBack": "file",
}

# Company Registered Under option VALUE -> `data-cond-group` it reveals. The
# fragment's applyCru() compares the <select> value to data-cond-group, so the
# list-fed option keys must equal these. The options themselves load async
# from /o/qc-qafl-membership/options and are NOT in the static HTML.
CRU_VALUES = ("moci", "qfc", "qfz", "other")  # UNVERIFIED (inferred from applyCru)

# Ordered field names per conditional group, as they appear in the DOM.
COND_GROUP_FIELDS = {
    "moci": ("crNumber", "uploadCrCopy", "qatarChamberMembershipNumber", "uploadQatarChamberMembershipCopy"),
    "qfc": ("qfcNumber", "qfcMembershipCopy"),
    "qfz": ("qfzNumber", "qfzMembershipCopy"),
    "other": ("companyRegisteredUnderOther", "companyRegisteredUnderOtherMembershipCopy"),
}

STEP_FIELDS = {
    1: ("companyEnglishName", "companyArabicName", "companyRegisteredUnder", "companySize", "companyType", "marketPresence"),
    2: ("seniorExecutiveName", "seniorExecutiveDesignation", "seniorExecutiveEmail", "seniorExecutiveConfirmEmail",
        "seniorExecutivePhone", "seniorExecutiveExtension", "seniorExecutiveMobile"),
    3: ("responsibleManagerName", "responsibleManagerDesignation", "responsibleManagerEmail",
        "responsibleManagerConfirmEmail", "responsibleManagerPhone", "responsibleManagerExtension",
        "responsibleManagerMobile"),
    4: ("website", "locationName", "buildingNumber", "zoneNumber", "streetNumber"),
    5: ("qaflMembershipAuthorizationLetter", "authorizedPersonQatarIdFront", "authorizedPersonQatarIdBack"),
}


class QaflMembershipPage(BasePage):
    # ---- Root (fragment) -----------------------------------------------------
    ROOT = "div.qc-qafl-membership"
    ROOT_READY = 'div.qc-qafl-membership[data-qc-init="1"]'  # set by the fragment script on init

    # ---- Hero + breadcrumb ----------------------------------------------------
    HERO = "section.qc-qafl-hero"
    HERO_INNER = "div.qc-qafl-hero__inner"
    HERO_TITLE = "h1.qc-qafl-hero__title"
    HERO_SUBTITLE = "p.qc-qafl-hero__subtitle"
    BREADCRUMB = "nav.qc-qafl-breadcrumb"
    BREADCRUMB_HOME = "a.qc-qafl-breadcrumb__home"
    BREADCRUMB_HOME_TEXT = "a.qc-qafl-breadcrumb__home > span"
    BREADCRUMB_SEP = "span.qc-qafl-breadcrumb__sep"
    BREADCRUMB_CURRENT = "span.qc-qafl-breadcrumb__current"

    # ---- Overview ---------------------------------------------------------------
    BODY_WRAP = "div.qc-qafl-body"
    OVERVIEW = "section.qc-qafl-overview"
    OVERVIEW_TEXT = "div.qc-qafl-overview__text"
    OVERVIEW_EYEBROW = "span.qc-qafl-overview__eyebrow"
    OVERVIEW_HEADING = "h2.qc-qafl-overview__heading"
    OVERVIEW_BODY = "div.qc-qafl-overview__body"
    OVERVIEW_INTRO = "div.qc-qafl-overview__body p"  # built by the script (DEFAULT_BODY) or CMS rich text
    OVERVIEW_BULLETS = "div.qc-qafl-overview__body li"

    # ---- Required-template card ------------------------------------------------------
    CARD = "aside.qc-qafl-card"
    CARD_ICON = "span.qc-qafl-card__icon"
    CARD_ICON_SVG = "span.qc-qafl-card__icon svg"
    CARD_EYEBROW = "span.qc-qafl-card__eyebrow"
    CARD_TITLE = "h3.qc-qafl-card__title"
    CARD_DESC = "p.qc-qafl-card__desc"
    DOWNLOAD_BUTTON = "a.qc-qafl-card__download"  # hidden until a published record supplies templateFile
    DOWNLOAD_ICON = "svg.qc-qafl-card__download-ic"

    # ---- Progress indicator ----------------------------------------------------------------
    STEPS = "ol.qc-qafl-steps"
    STEP_ITEM = "li.qc-qafl-steps__item"
    STEP_ITEM_N = 'li.qc-qafl-steps__item[data-step="{n}"]'
    STEP_NUM_N = 'li.qc-qafl-steps__item[data-step="{n}"] span.qc-qafl-steps__num'
    STEP_LABEL_N = 'li.qc-qafl-steps__item[data-step="{n}"] span.qc-qafl-steps__label'

    # ---- Form + step fieldsets ------------------------------------------------------------
    FORM = "form.qc-qafl-form"
    STEP_FIELDSET_N = 'fieldset.qc-qafl-step[data-step="{n}"]'
    STEP_HEAD_ICON_N = 'fieldset.qc-qafl-step[data-step="{n}"] span.qc-qafl-step-head__icon'
    STEP_HEAD_TITLE_N = 'fieldset.qc-qafl-step[data-step="{n}"] span.qc-qafl-step-head__title'
    STEP_HEAD_SUB_N = 'fieldset.qc-qafl-step[data-step="{n}"] span.qc-qafl-step-head__sub'
    COND_GROUP_N = 'div.qc-qafl-cond[data-cond-group="{group}"]'

    # ---- Generic field (by control name) -----------------------------------------------------
    FIELD = '.qc-qafl-field:has([name="{name}"])'
    FIELD_INVALID = '.qc-qafl-field.is-invalid:has([name="{name}"])'
    FIELD_LABEL = '.qc-qafl-field:has([name="{name}"]) > span:first-child'
    FIELD_ERROR = '.qc-qafl-field:has([name="{name}"]) > em[data-role="err"]'
    CONTROL = '[name="{name}"]'
    RADIO = 'input[type="radio"][name="{name}"][value="{value}"]'
    RADIO_CARD = 'label.qc-qafl-card-opt:has(input[name="{name}"][value="{value}"])'
    RADIO_CARD_ANY = 'label.qc-qafl-card-opt:has(input[name="{name}"])'
    RADIO_CARD_MAIN = 'label.qc-qafl-card-opt:has(input[name="{name}"]) span.qc-qafl-card-opt__main'
    RADIO_CARD_SUB = 'label.qc-qafl-card-opt:has(input[name="{name}"]) span.qc-qafl-card-opt__sub'
    SELECT_OPTION_VALUE = 'select[name="{name}"] option[value="{value}"]'
    SELECT_OPTIONS = 'select[name="{name}"] option'
    DROPZONE_HINT = '.qc-qafl-field:has([name="{name}"]) span.qc-qafl-dz__hint'
    DROPZONE_FILE = '.qc-qafl-field:has([name="{name}"]) span[data-role="dzfile"]'
    VERIFIED_FIELD = "div.qc-qafl-verified[data-verified]"
    MOBILE_CC = '.qc-qafl-field:has([name="{name}"]) span.qc-qafl-phone__cc'

    # ---- CAPTCHA (shared QC.recaptcha mount) ------------------------------------------------
    CAPTCHA = "div.qc-qafl-captcha[data-qc-recaptcha-field]"
    CAPTCHA_WIDGET = "div.qc-qafl-captcha__widget[data-qc-recaptcha]"
    CAPTCHA_ERROR = "em[data-role-captcha]"

    # ---- Navigation buttons -----------------------------------------------------------------
    PREV_BUTTON = 'button[data-role="prev"]'
    NEXT_BUTTON = 'button[data-role="next"]'
    SUBMIT_BUTTON = 'button[data-role="submit"]'
    NEXT_ARROW = 'button[data-role="next"] svg.qc-qafl-btn__arrow'

    # ---- Outcome ---------------------------------------------------------------------------
    ACK = 'div.qc-qafl-ack[data-role="ack"]'
    ACK_MESSAGE = 'div.qc-qafl-ack[data-role="ack"] p.qc-qafl-ack__msg'
    TOAST = ".alert"  # UNVERIFIED — Liferay.Util.openToast container; not in static HTML

    # ---- Site header (JS-rendered; not in static HTML) ----------------------------------------
    HEADER = "header.qc-global-site-header"
    HEADER_NAV_ITEM = 'header.qc-global-site-header nav.qc-nav li.qc-has-children:has(> a:has-text("{text}"))'  # UNVERIFIED
    HEADER_QAFL_LINK = 'header.qc-global-site-header nav.qc-nav a[href*="qafl-membership"]'  # UNVERIFIED

    # ------------------------------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------------------------------
    def open_registration(self, locale: str = "en") -> "QaflMembershipPage":
        self.open(web_url(QAFL_MEMBERSHIP_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE, state="visible", timeout=30000)
        # The fragment script flags its root once listeners are bound; filling
        # before that would bypass the validators.
        self.wait_for(self.ROOT_READY, state="attached", timeout=30000)
        return self

    def open_home(self, locale: str = "en") -> "QaflMembershipPage":
        self.open(web_url(HOME_PATH, locale=locale))
        self.wait_for(self.HEADER, state="visible", timeout=30000)
        return self

    def open_menu_section(self, section_text: str) -> None:
        self.page.locator(self.HEADER_NAV_ITEM.format(text=section_text)).first.hover()

    def is_menu_qafl_link_visible(self, timeout: int = 5000) -> bool:
        try:
            self.page.locator(self.HEADER_QAFL_LINK).first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001 — reported by the caller's assert
            return False

    def menu_qafl_link_text(self) -> str:
        return self.page.locator(self.HEADER_QAFL_LINK).first.inner_text().strip()

    def click_menu_qafl_link(self) -> "QaflMembershipPage":
        self.page.locator(self.HEADER_QAFL_LINK).first.click()
        self.wait_for(self.HERO_TITLE, state="visible", timeout=30000)
        self.wait_for(self.ROOT_READY, state="attached", timeout=30000)
        return self

    def reload(self) -> None:
        self.page.reload(wait_until="domcontentloaded")

    def go_back(self) -> None:
        self.page.go_back(wait_until="domcontentloaded")

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')") or ""

    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth + 1"
        )

    def viewport_width(self) -> int:
        return self.page.evaluate("() => document.documentElement.clientWidth")

    # ------------------------------------------------------------------------------------------
    # Generic measurement
    # ------------------------------------------------------------------------------------------
    def box(self, locator: str, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).bounding_box() or {}

    def style(self, locator: str, props: list, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            "(el, props) => { const s = getComputedStyle(el); const o = {}; props.forEach(p => o[p] = s[p]); return o; }",
            props,
        )

    def pseudo_style(self, locator: str, pseudo: str, props: list, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            "(el, a) => { const s = getComputedStyle(el, a[0]); const o = {}; a[1].forEach(p => o[p] = s[p]); return o; }",
            [pseudo, props],
        )

    def texts(self, locator: str) -> list:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def text_of(self, locator: str) -> str:
        return self.text(locator).strip()

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def is_shown(self, locator: str) -> bool:
        return self.is_visible(locator)

    # ------------------------------------------------------------------------------------------
    # Steps / progress
    # ------------------------------------------------------------------------------------------
    def current_step(self) -> int:
        return self.page.evaluate(
            "() => { const s = Array.from(document.querySelectorAll('fieldset.qc-qafl-step'))"
            ".find(f => !f.hidden); return s ? Number(s.dataset.step) : 0; }"
        )

    def wait_for_step(self, n: int, timeout: int = 5000) -> bool:
        try:
            self.page.locator(self.STEP_FIELDSET_N.format(n=n)).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    def step_badge_state(self, n: int) -> dict:
        classes = self.get_attribute(self.STEP_ITEM_N.format(n=n), "class") or ""
        return {"active": "is-active" in classes.split(), "done": "is-done" in classes.split()}

    def active_badge(self) -> int:
        return self.page.evaluate(
            "() => { const b = document.querySelector('li.qc-qafl-steps__item.is-active');"
            " return b ? Number(b.dataset.step) : 0; }"
        )

    def connector_style(self, n: int = 1) -> dict:
        """The dashed connector is `li.qc-qafl-steps__item::after` with a
        2px border-block-start (confirmed in the saved CSS)."""
        return self.pseudo_style(
            self.STEP_ITEM_N.format(n=n), "::after", ["borderTopWidth", "borderTopColor", "borderTopStyle", "display"]
        )

    def badge_positions(self) -> list:
        return [self.box(self.STEP_ITEM_N.format(n=n)).get("x", 0) for n in range(1, 6)]

    def click_next(self) -> None:
        self.click(self.NEXT_BUTTON)

    def click_previous(self) -> None:
        self.click(self.PREV_BUTTON)

    def click_submit(self) -> None:
        self.click(self.SUBMIT_BUTTON)

    # ------------------------------------------------------------------------------------------
    # Field interaction
    # ------------------------------------------------------------------------------------------
    def wait_for_select_option(self, name: str, value: str = None, label: str = None, timeout: int = 15000) -> None:
        """List-fed <select>s fill asynchronously after page init."""
        if value is not None:
            sel = self.SELECT_OPTION_VALUE.format(name=name, value=value)
        else:
            sel = f'select[name="{name}"] option:text-is("{label}")'
        self.page.locator(sel).first.wait_for(state="attached", timeout=timeout)

    def select(self, name: str, value: str = None, label: str = None) -> None:
        self.wait_for_select_option(name, value=value, label=label)
        self.select_option(self.CONTROL.format(name=name), label=label, value=value)

    def choose(self, name: str, value: str) -> None:
        self.page.locator(self.RADIO.format(name=name, value=value)).check()

    def type_into(self, name: str, value: str) -> None:
        self.type(self.CONTROL.format(name=name), value)

    def press_sequentially(self, name: str, value: str) -> None:
        loc = self.page.locator(self.CONTROL.format(name=name))
        loc.click()
        loc.press_sequentially(value)

    def attach(self, name: str, path: str) -> None:
        self.upload_file(self.CONTROL.format(name=name), path)

    def set_field(self, name: str, value) -> None:
        """Dispatch on FIELD_KINDS. Select values are option VALUES unless
        passed as {"label": "..."}."""
        kind = FIELD_KINDS[name]
        if kind == "select":
            if isinstance(value, dict):
                self.select(name, label=value["label"])
            else:
                self.select(name, value=value)
        elif kind == "radio":
            self.choose(name, value)
        elif kind == "file":
            self.attach(name, value)
        else:
            self.type_into(name, value)

    def fill(self, values: dict) -> None:
        for name, value in values.items():
            self.set_field(name, value)

    def blur(self, name: str) -> None:
        self.page.locator(self.CONTROL.format(name=name)).first.focus()
        self.page.keyboard.press("Tab")

    def focus(self, name: str) -> None:
        self.page.locator(self.CONTROL.format(name=name)).first.focus()

    def click_control(self, name: str) -> None:
        self.page.locator(self.CONTROL.format(name=name)).first.click()

    # ------------------------------------------------------------------------------------------
    # Field state
    # ------------------------------------------------------------------------------------------
    def field_value(self, name: str) -> str:
        kind = FIELD_KINDS[name]
        if kind == "radio":
            return self.page.evaluate(
                "(n) => { const c = Array.from(document.querySelectorAll(`input[type=radio][name=\"${n}\"]`))"
                ".find(r => r.checked); return c ? c.value : ''; }",
                name,
            )
        if kind == "file":
            return ",".join(self.attached_file_names(name))
        return self.page.locator(self.CONTROL.format(name=name)).first.input_value()

    def selected_option_text(self, name: str) -> str:
        return self.page.locator(self.CONTROL.format(name=name)).evaluate(
            "s => s.selectedIndex >= 0 ? s.options[s.selectedIndex].textContent.trim() : ''"
        )

    def option_texts(self, name: str, include_placeholder: bool = False) -> list:
        return self.page.locator(self.CONTROL.format(name=name)).evaluate(
            "(s, ph) => Array.from(s.options).filter(o => ph || o.value !== '').map(o => o.textContent.trim())",
            include_placeholder,
        )

    def wait_for_options_loaded(self, name: str, timeout: int = 15000) -> None:
        self.page.locator(f'select[name="{name}"] option:not([value=""])').first.wait_for(
            state="attached", timeout=timeout
        )

    def attached_file_names(self, name: str) -> list:
        return self.page.locator(self.CONTROL.format(name=name)).evaluate(
            "el => Array.from(el.files || []).map(f => f.name)"
        )

    def has_field_error(self, name: str, timeout: int = 5000) -> bool:
        """True once the field wrapper carries `is-invalid` AND its error em
        has text. Waits up to `timeout` because validation is event-driven."""
        try:
            self.page.locator(self.FIELD_INVALID.format(name=name)).first.wait_for(state="attached", timeout=timeout)
        except Exception:  # noqa: BLE001
            return False
        return bool(self.field_error_text(name))

    def has_no_field_error(self, name: str) -> bool:
        invalid = self.page.locator(self.FIELD_INVALID.format(name=name)).count() > 0
        return not invalid and not self.field_error_text(name)

    def field_error_text(self, name: str) -> str:
        loc = self.page.locator(self.FIELD_ERROR.format(name=name)).first
        return (loc.text_content() or "").strip() if loc.count() else ""

    def field_error_style(self, name: str) -> dict:
        return self.style(self.FIELD_ERROR.format(name=name), ["color"])

    def field_error_below_control(self, name: str) -> bool:
        ctrl = self.box(self.CONTROL.format(name=name))
        err = self.box(self.FIELD_ERROR.format(name=name))
        return bool(ctrl and err) and err["y"] >= ctrl["y"] + ctrl["height"] - 1

    def is_field_visible(self, name: str) -> bool:
        return self.page.locator(self.FIELD.format(name=name)).first.is_visible()

    def is_control_required(self, name: str) -> bool:
        return self.page.evaluate(
            "(n) => Array.from(document.querySelectorAll(`[name=\"${n}\"]`)).some(e => e.required)", name
        )

    def label_text(self, name: str) -> str:
        return (self.page.locator(self.FIELD_LABEL.format(name=name)).first.text_content() or "").strip()

    def required_marker(self, name: str) -> str:
        """The label span's ::after content ('" *"' when marked required,
        'none'/'normal' otherwise) — the asterisk is CSS-generated."""
        return self.pseudo_style(self.FIELD_LABEL.format(name=name), "::after", ["content"])["content"]

    def has_required_marker(self, name: str) -> bool:
        return "*" in (self.required_marker(name) or "")

    def placeholder(self, name: str) -> str:
        return self.get_attribute(self.CONTROL.format(name=name), "placeholder") or ""

    def visible_field_names(self, step: int) -> list:
        """Control names of every currently visible field in the step, DOM order."""
        return self.page.locator(self.STEP_FIELDSET_N.format(n=step)).evaluate(
            "fs => { const seen = []; fs.querySelectorAll('.qc-qafl-field').forEach(f => {"
            " if (f.hidden || f.closest('[hidden]')) return;"
            " const c = f.querySelector('[name]'); if (c && !seen.includes(c.name)) seen.push(c.name); });"
            " return seen; }"
        )

    def visible_cond_field_names(self) -> list:
        """Names of fields inside the currently un-hidden Company Registered
        Under group (`div.qc-qafl-cond`), DOM order."""
        return self.page.evaluate(
            "() => { const out = []; document.querySelectorAll('div.qc-qafl-cond').forEach(g => {"
            " if (g.hidden) return; g.querySelectorAll('[name]').forEach(c => out.push(c.name)); });"
            " return out; }"
        )

    def focused_control_name(self) -> str:
        return self.page.evaluate("() => (document.activeElement && document.activeElement.name) || ''")

    def focused_selector_matches(self, locator: str) -> bool:
        return self.is_focused(locator)

    def control_focus_style(self, name: str) -> dict:
        return self.style(
            self.CONTROL.format(name=name),
            ["borderTopColor", "borderTopWidth", "outlineStyle", "outlineWidth", "outlineColor", "boxShadow"],
        )

    def dropzone_hint(self, name: str) -> str:
        return (self.page.locator(self.DROPZONE_HINT.format(name=name)).first.text_content() or "").strip()

    def dropzone_file_text(self, name: str) -> str:
        loc = self.page.locator(self.DROPZONE_FILE.format(name=name)).first
        return (loc.text_content() or "").strip() if loc.count() else ""

    # ------------------------------------------------------------------------------------------
    # Template download
    # ------------------------------------------------------------------------------------------
    def download_template(self, timeout: int = 30000):
        """Click Download Authorization Letter and return the Playwright
        Download object."""
        with self.page.expect_download(timeout=timeout) as info:
            self.click(self.DOWNLOAD_BUTTON)
        return info.value

    # ------------------------------------------------------------------------------------------
    # Submit outcome
    # ------------------------------------------------------------------------------------------
    _OUTCOME = (
        'div.qc-qafl-ack[data-role="ack"]:visible, em[data-role-captcha]:not(:empty), '
        ".qc-qafl-field.is-invalid, .alert:visible"  # UNVERIFIED (.alert = Liferay toast)
    )

    def wait_for_submit_outcome(self, timeout: int = 45000) -> bool:
        try:
            self.page.locator(self._OUTCOME).first.wait_for(state="attached", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    SUBMIT_ENDPOINT = "/o/qc-qafl-membership/submit"  # data-qc-submit-endpoint on the fragment root

    def submit_and_wait_response(self, timeout: int = 60000) -> int | None:
        """Click Submit and wait for the POST to the submit endpoint — the
        definitive signal that the submit finished. Returns the HTTP status,
        or None when no request was sent (client-side validation blocked it,
        or the CAPTCHA blocked it locally)."""
        try:
            with self.page.expect_response(
                lambda r: self.SUBMIT_ENDPOINT in r.url and r.request.method == "POST", timeout=timeout
            ) as info:
                self.click_submit()
            return info.value.status
        except Exception:  # noqa: BLE001 — caller asserts on the outcome
            return None

    def has_submission_succeeded(self, timeout: int = 15000) -> bool:
        """Waits on the acknowledgement block itself (not on a generic
        outcome), so a stray toast can never short-circuit the check."""
        try:
            self.page.locator(self.ACK).wait_for(state="visible", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    def is_ack_visible(self) -> bool:
        return self.is_visible(self.ACK)

    def ack_text(self) -> str:
        return self.text_of(self.ACK_MESSAGE)

    def toast_text(self, timeout: int = 15000) -> str:
        try:
            loc = self.page.locator(self.TOAST).last
            loc.wait_for(state="visible", timeout=timeout)
            return loc.inner_text().strip()
        except Exception:  # noqa: BLE001
            return ""

    def captcha_error_text(self) -> str:
        return (self.page.locator(self.CAPTCHA_ERROR).first.text_content() or "").strip()

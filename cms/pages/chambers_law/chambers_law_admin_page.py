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

import re

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

    # ---- Chamber Laws Page: LOCALE-INDEPENDENT locators (live 2026-10-12) --
    # The accessible names above only resolve on an /en render; on /ar every
    # label is Arabic ("عنوان الصفحة", ...). These name/id selectors were read
    # off the live form in BOTH renders and are the same in each: the English
    # half is the Liferay field `ObjectField_<name>`, its Arabic twin the
    # page's own `#qc-ar-<name>` control. Every one is `required` natively,
    # has NO `maxlength`, and carries a live "<n> / 280" counter.
    PAGE_TEXT_FIELDS = {
        "page_title": ('input[name="ObjectField_pageTitle"]', "#qc-ar-pageTitle"),
        "intro_heading": ('input[name="ObjectField_introHeading"]', "#qc-ar-introHeading"),
        "alt_text": ('input[name="ObjectField_contentImageAltText"]', "#qc-ar-contentImageAltText"),
        "refs_heading": ('input[name="ObjectField_referencesHeading"]', "#qc-ar-referencesHeading"),
    }
    # Intro Content: two CKEditor 4 instances. Their instance names END with
    # these tokens (EN: "fragment-<uuid>-ObjectField_introContent", AR:
    # "qc-ar-introContent"); CKEditor wraps each in `#cke_<instance name>`.
    INTRO_EDITOR_TOKENS = {"en": "ObjectField_introContent", "ar": "qc-ar-introContent"}
    # The object's own "Status" PICKLIST field (`pageStatus`) -- NOT the
    # workflow status. Options read live: Draft / Published / Unpublished.
    PAGE_STATUS_COMBOBOX = "input[data-qc-oel-picklist]"
    PAGE_STATUS_LABEL_INPUT = 'input[name="ObjectField_pageStatus-label"]'
    ACTIVE_STATUS_CHECKBOX = 'input[name="ObjectField_activeStatus"]'
    # Form submit buttons by their Liferay `status` value: 0 = Publish (EN
    # "Publish"/"Submit for Review", AR "نشر"), 2 = Save as Draft.
    PUBLISH_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    SAVE_DRAFT_SUBMIT = 'button[type="submit"][name="status"][value="2"]'
    CHAR_COUNTER_RE = re.compile(r"(\d+)\s*/\s*(\d+)")
    BANNER_DATES_RE = re.compile(
        r"Created ([0-9/]+, [0-9:]+), last modified ([0-9/]+, [0-9:]+)"
    )
    SINGLETON_NOTE = "This page holds this one record only"
    ACCESS_DENIED_EN = "Access Denied. You do not have permission to perform this action."
    ACCESS_DENIED_AR = "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء."

    # ---- AboutHeroBanner (the object that renders this page's hero) ------
    # One row per page, keyed by Page Key; the chamber-laws row is REAL
    # content (`QCDEMO-ABOUT-HERO-chamber-laws`) and is never written by
    # automation -- hero-field cases run on disposable QCTEST rows.
    HERO_BANNER_SLUG = "about-hero-banner"
    HERO_BANNER_CHAMBER_LAWS_CODE = "QCDEMO-ABOUT-HERO-chamber-laws"
    HERO_PAGE_KEY_LABEL = "Page Key"
    HERO_IMAGE_UPLOAD_LABEL = "Banner Image"
    HERO_ALT_TEXT_LABEL = "Banner Image Alt Text"
    HERO_PAGE_KEY_INPUT = 'input[name="ObjectField_pageKey"]'
    HERO_ALT_TEXT_INPUT = 'input[name="ObjectField_bannerImageAltText"]'

    # Walks up from a control to the nearest ancestor carrying a "<n> / <m>"
    # counter and returns that ancestor's text.
    _COUNTER_JS = (
        "el => { let n = el; for (let i = 0; i < 4 && n; i++) { n = n.parentElement;"
        " if (n && /\\d+\\s*\\/\\s*\\d+/.test(n.innerText)) return n.innerText; } return ''; }"
    )

    def __init__(self, page):
        super().__init__(page)

    # ---- Chamber Laws Page (singleton) navigation -------------------------
    def open_page_record(self, locale: str | None = None) -> "ObjectAuthoringPage":
        """Opens the ONE Chamber Laws Page record for edit. Returns the
        `ObjectAuthoringPage` driving `manage-chamber-laws-page`, with its
        entry code already tracked (so `reopen()`/`wait_for_status()` work).
        `locale` pins the CMS interface language ("en"/"ar")."""
        authoring = ObjectAuthoringPage(self.page, slug=CHAMBERS_LAW_PAGE_SLUG)
        if locale == "ar":
            return self._open_arabic(authoring, CHAMBERS_LAW_PAGE_ENTRY_CODE,
                                     self.PAGE_TEXT_FIELDS["page_title"][0])
        authoring.open_entry_by_code(CHAMBERS_LAW_PAGE_ENTRY_CODE, locale=locale)
        return authoring

    def _open_arabic(self, authoring, entry_code: str, settle_selector: str):
        """`/ar` render of an entry's edit form. The editing banner -- which
        `open_entry_by_code()` settles on -- is Arabic there, so the settle
        signal is the form's own (locale-independent) field control."""
        authoring.open(authoring._manage_url(edit_entry=entry_code, locale="ar"))
        authoring._entry_code = entry_code
        authoring._locale = "ar"
        self.page.locator(settle_selector).first.wait_for(state="visible", timeout=60000)
        return authoring

    # ---- Attachment picker, addressed by FIELD NAME (locale-independent) ---
    UPLOAD_PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'

    def open_file_picker(self, field_name: str):
        """Clicks the "Select File" control of the attachment field whose
        hidden input is `input[name=<field_name>]` -- its button id is the
        input id + "-button-label" (read live, both objects) -- and returns
        the picker's frame locator."""
        hidden = self.page.locator(f'input[name="{field_name}"]').first
        button_id = hidden.get_attribute("id") + "-button-label"
        self.page.locator(f'[id="{button_id}"]').click()
        return self.page.frame_locator(self.UPLOAD_PICKER_IFRAME)

    @staticmethod
    def picker_set_file(frame, file_path: str) -> None:
        frame.locator('input[type="file"]').set_input_files(file_path)

    @staticmethod
    def picker_reports_uploaded(frame) -> bool:
        # "1 of 1" (EN) / "1 من 1" (AR) -- the picker's uploaded-count line.
        return frame.get_by_text(re.compile(r"^\s*1 (of|من) 1\s*$")).count() > 0

    def attachment_validation_message(self, field_name: str) -> str:
        """Constraint message of an attachment field's hidden input, "" if valid."""
        return self.page.locator(f'input[name="{field_name}"]').first.evaluate(
            "el => el.validity && !el.validity.valid ? (el.validationMessage || 'invalid') : ''"
        )

    def attachment_value(self, field_name: str) -> str:
        """Value of an attachment field's hidden input (the attached file's
        id once a file is added on the open form; "" otherwise)."""
        return self.page.locator(f'input[name="{field_name}"]').first.input_value()

    def current_user_id(self) -> str:
        return str(self.page.evaluate("() => Liferay.ThemeDisplay.getUserId()"))

    # ---- Liferay Audit (Control Panel) ------------------------------------
    AUDIT_PORTLET_PATH = (
        "/en/group/guest/~/control_panel/manage?p_p_id="
        "com_liferay_portal_security_audit_web_portlet_AuditPortlet"
        "&_com_liferay_portal_security_audit_web_portlet_AuditPortlet_delta=200"
    )

    def audit_rows_for(self, resource_id: str) -> list:
        """Audit-log rows whose Resource ID cell equals `resource_id`, newest
        first, each as its list of cell texts: [User ID, User Name, Resource
        ID, Resource Name, Resource Action, Client IP, Create Date]. Needs
        an account allowed to read the audit portlet."""
        from config.settings import control_panel_url
        self.open(control_panel_url(self.AUDIT_PORTLET_PATH))
        self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=60000)
        rows = self.page.evaluate(
            "() => Array.from(document.querySelectorAll('table tbody tr')).map(r =>"
            " Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim()))"
        )
        return [r for r in rows if len(r) >= 5 and r[2] == str(resource_id)]

    # ---- Chamber Laws Page: field access (locale-independent) -------------
    def _text_control(self, key: str, locale: str = "en"):
        en, ar = self.PAGE_TEXT_FIELDS[key]
        return self.page.locator(ar if locale == "ar" else en).first

    def page_text(self, key: str, locale: str = "en") -> str:
        return self._text_control(key, locale).input_value()

    def fill_page_text(self, key: str, value: str, locale: str = "en") -> None:
        self._text_control(key, locale).fill(value)

    def page_text_validation_message(self, key: str, locale: str = "en") -> str:
        """The browser's own constraint message for the control, "" if valid."""
        return self._text_control(key, locale).evaluate(
            "el => el.validity && !el.validity.valid ? (el.validationMessage || 'invalid') : ''"
        )

    def page_text_counter(self, key: str, locale: str = "en") -> tuple:
        """(current, limit) from the field's own live "<n> / <max>" counter --
        the IMPLEMENTED limit (no `maxlength` attribute exists). (-1, -1)
        when no counter renders."""
        text = self._text_control(key, locale).evaluate(self._COUNTER_JS)
        match = self.CHAR_COUNTER_RE.search(text or "")
        return (int(match.group(1)), int(match.group(2))) if match else (-1, -1)

    def _intro_instance_js(self, locale: str) -> str:
        token = self.INTRO_EDITOR_TOKENS[locale]
        return (
            "(() => { const k = Object.keys(CKEDITOR.instances).find(n => n.endsWith("
            f"'{token}')); return CKEDITOR.instances[k]; }})()"
        )

    def intro_html(self, locale: str = "en") -> str:
        return self.page.evaluate(f"() => {self._intro_instance_js(locale)}.getData()")

    def set_intro_html(self, html: str, locale: str = "en") -> None:
        """Sets the editor's HTML through CKEditor's own `setData()` and
        syncs it to the form (`updateElement()` + a change event). Used for
        byte-exact baseline restores and for the 5000-character cases, where
        typing cannot reproduce `&amp;`, curly quotes or `<p>` boundaries
        exactly (live finding: typing doubles paragraph breaks)."""
        self.page.evaluate(
            "([html]) => new Promise(resolve => { const ed = "
            f"{self._intro_instance_js(locale)}; ed.setData(html, {{ callback: () => {{"
            " ed.updateElement(); ed.fire('change'); resolve(true); } }); })",
            [html],
        )

    def _intro_iframe(self, locale: str) -> str:
        token = self.INTRO_EDITOR_TOKENS[locale]
        return f'[id^="cke_"][id$="{token}"] iframe'

    def type_into_intro(self, text: str, locale: str = "en") -> None:
        """Replaces the editor's content by REAL typing (select-all + type);
        every newline is an Enter, i.e. a new paragraph."""
        self.fill_iframe_editor(self._intro_iframe(locale), text)

    def intro_text(self, locale: str = "en") -> str:
        return self.iframe_editor_text(self._intro_iframe(locale))

    def intro_direction(self, locale: str = "en") -> str:
        return self.page.frame_locator(self._intro_iframe(locale)).locator("body").evaluate(
            "b => (getComputedStyle(b).direction || b.getAttribute('dir') || '').toLowerCase()"
        )

    def page_status_value(self) -> str:
        """Current label of the object's own Status picklist field. Fails
        fast, naming the rendered fields, when the form has none."""
        from cms.pages.components.status_picklist import require_status_picklist

        require_status_picklist(self.page, self.PAGE_STATUS_LABEL_INPUT, self.PAGE_STATUS_COMBOBOX)
        return self.page.locator(self.PAGE_STATUS_LABEL_INPUT).first.input_value()

    def _open_page_status_list(self):
        combo = self.page.locator(self.PAGE_STATUS_COMBOBOX).first
        combo.click()
        listbox = self.page.locator(f"#{combo.get_attribute('aria-controls')}")
        listbox.locator("[role=option]").first.wait_for(state="visible", timeout=10000)
        return listbox

    def page_status_options(self) -> list:
        listbox = self._open_page_status_list()
        options = [t.strip() for t in listbox.locator("[role=option]").all_inner_texts()]
        self.page.keyboard.press("Escape")
        return options

    def pick_page_status(self, option: str) -> list:
        """Opens the Status picklist ONCE, returns every option it offered,
        selects `option` and verifies it by read-back (one re-pick). See
        cms/pages/components/status_picklist.py for why it is one action."""
        from cms.pages.components.status_picklist import pick_status_option

        return pick_status_option(self.page, self.PAGE_STATUS_COMBOBOX, option, self.page_status_value)

    def choose_page_status(self, option: str) -> None:
        listbox = self._open_page_status_list()
        listbox.locator("[role=option]").filter(
            has_text=re.compile(rf"^\s*{re.escape(option)}\s*$")
        ).first.click()

    def active_status_checked(self) -> bool:
        return self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first.is_checked()

    def set_active_status(self, checked: bool) -> None:
        box = self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first
        if checked:
            box.check()
        else:
            box.uncheck()

    def publish_control_state(self) -> dict:
        """{"publish": (present, enabled, label), "draft": (...)} for the
        form's two submit controls, read by their status value."""
        out = {}
        for key, sel in (("publish", self.PUBLISH_SUBMIT), ("draft", self.SAVE_DRAFT_SUBMIT)):
            loc = self.page.locator(sel)
            if loc.count() == 0:
                out[key] = (False, False, "")
            else:
                out[key] = (True, loc.first.is_enabled(), loc.first.inner_text().strip())
        return out

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def banner_dates(self) -> tuple:
        """(created, last_modified) as rendered in the editing banner."""
        match = self.BANNER_DATES_RE.search(self.body_text())
        return (match.group(1), match.group(2)) if match else ("", "")

    def _page_row(self):
        return self.page.locator(
            f'table tbody tr:has-text("{CHAMBERS_LAW_PAGE_ENTRY_CODE}")'
        ).first

    def page_row_last_modified(self) -> str:
        """The entries list's LAST MODIFIED cell (second resolution) for the
        page record. Call on the open manage page."""
        return self._page_row().locator("td").nth(2).inner_text().strip()

    def page_row_entry_id(self) -> str:
        """Numeric entry id, read off the row's own History control
        (`data-qc-oel-history="<entryId>"`) -- the singleton row has no
        Delete control to read it from."""
        return (
            self._page_row().locator("[data-qc-oel-history]").first
            .get_attribute("data-qc-oel-history") or ""
        )

    def page_row_actions(self) -> list:
        return [t.strip() for t in self._page_row().locator("a, button").all_inner_texts() if t.strip()]

    def page_row_action_attrs(self) -> list:
        return self._page_row().evaluate(
            "r => Array.from(r.querySelectorAll('*')).flatMap(e => Array.from(e.attributes)"
            ".map(a => a.name)).filter(n => n.startsWith('data-qc-oel-'))"
        )

    def editable_system_field_controls(self) -> list:
        """Every ENABLED, non-readonly form control whose label or name names
        an identifier or a created/modified date. Empty = none is editable."""
        return self.page.evaluate(
            "() => Array.from(document.querySelectorAll('form input, form textarea, form select'))"
            ".filter(e => e.type !== 'hidden' && !e.disabled && !e.readOnly)"
            ".map(e => [e.name || e.id, (e.labels && e.labels[0] ? e.labels[0].innerText : '')])"
            ".filter(([n, l]) => /\\b(page id|entry id|id|created|modified|create date|modified date)\\b/i.test(l)"
            " || /(^|_)(id|pageId|createDate|modifiedDate)$/.test(n))"
        )

    def click_publish_control(self) -> None:
        """Raw click on the form's Publish/Submit control (status value 0),
        for permission cases that ATTEMPT a publish without assuming it
        will settle like a successful save."""
        self.page.locator(self.PUBLISH_SUBMIT).first.click()
        self.page.wait_for_load_state("load")

    def open_manage_entry(self, slug: str, entry_code: str, locale: str | None = None) -> None:
        """Navigates to `manage-<slug>?editEntry=<code>` WITHOUT waiting for
        an edit form -- for access-denied cases, where none must render."""
        authoring = ObjectAuthoringPage(self.page, slug=slug)
        self.open(authoring._manage_url(edit_entry=entry_code, locale=locale))
        self.page.wait_for_load_state("load")

    def open_page_record_as_viewer(self, locale: str = "en") -> None:
        """Opens the page record's edit URL for a role that may NOT edit it
        (live 2026-10-12, Site Content Author: no "Editing ..." banner -- an
        "Access Denied ... Only a Content Editor can change a record once it
        has reached the website" note and DISABLED submit controls instead).
        Settles on the form's submit control or that note, whichever renders."""
        self.open_manage_entry(CHAMBERS_LAW_PAGE_SLUG, CHAMBERS_LAW_PAGE_ENTRY_CODE, locale)
        self.page.locator(self.PUBLISH_SUBMIT).or_(
            self.page.get_by_text(self.ACCESS_DENIED_EN)
        ).first.wait_for(state="attached", timeout=60000)

    def has_object_form(self) -> bool:
        """True when any Object-field control (`ObjectField_*`) rendered."""
        return self.page.locator('input[name^="ObjectField_"]').count() > 0

    def list_offers_row_link(self, text: str) -> bool:
        return self.page.locator("table tbody tr a", has_text=text).count() > 0

    def form_has_control(self, role: str, label: str) -> bool:
        return self.page.get_by_role(role, name=ObjectAuthoringPage.label_pattern(label)).count() > 0

    def page_has_edit_form(self) -> bool:
        return self.page.locator(self.PAGE_TEXT_FIELDS["page_title"][0]).count() > 0

    # ---- AboutHeroBanner navigation ---------------------------------------
    def open_hero_record(self, entry_code: str = HERO_BANNER_CHAMBER_LAWS_CODE,
                         locale: str | None = "en") -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=self.HERO_BANNER_SLUG)
        if locale == "ar":
            return self._open_arabic(authoring, entry_code, self.HERO_PAGE_KEY_INPUT)
        authoring.open_entry_by_code(entry_code, locale=locale)
        return authoring

    def hero_entry_code(self, page_key: str) -> str:
        """editEntry code of the hero row whose Entry column is `page_key`,
        read off that row's own Edit link; "" when no such row. Call on the
        open entries list."""
        row = self.page.locator(f'table tbody tr:has-text("{page_key}")').first
        if row.count() == 0:
            return ""
        href = row.locator('a[href*="editEntry="]').first.get_attribute("href") or ""
        match = re.search(r"editEntry=([^&]+)", href)
        return match.group(1) if match else ""

    def open_new_hero_form(self, locale: str | None = "en") -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=self.HERO_BANNER_SLUG)
        authoring.open_new_entry_form(locale=locale)
        return authoring

    def open_hero_entries_list(self, locale: str | None = "en") -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=self.HERO_BANNER_SLUG)
        authoring.open_entries_list(locale=locale)
        return authoring

    def hero_banner_file_name(self) -> str:
        """`Current file:` name of the open hero row's Banner Image, or ""."""
        return ObjectAuthoringPage(self.page, slug=self.HERO_BANNER_SLUG).current_file_name(
            self.HERO_IMAGE_UPLOAD_LABEL
        )

    def hero_banner_required_message(self) -> str:
        """The form's own constraint message on the Banner Image control
        (`input[name=ObjectField_bannerImage]`), "" when it currently passes
        -- i.e. what would stop a Publish submit with the field empty."""
        return self.page.locator('input[name="ObjectField_bannerImage"]').first.evaluate(
            "el => el.validity && !el.validity.valid ? (el.validationMessage || 'invalid') : ''"
        )

    def fill_hero_page_key(self, value: str) -> None:
        self.page.locator(self.HERO_PAGE_KEY_INPUT).first.fill(value)

    def hero_alt_text(self) -> str:
        return self.page.locator(self.HERO_ALT_TEXT_INPUT).first.input_value()

    def fill_hero_alt_text(self, value: str) -> None:
        self.page.locator(self.HERO_ALT_TEXT_INPUT).first.fill(value)

    def hero_alt_validation_message(self) -> str:
        return self.page.locator(self.HERO_ALT_TEXT_INPUT).first.evaluate(
            "el => el.validity && !el.validity.valid ? (el.validationMessage || 'invalid') : ''"
        )

    def hero_alt_counter(self) -> tuple:
        text = self.page.locator(self.HERO_ALT_TEXT_INPUT).first.evaluate(self._COUNTER_JS)
        match = self.CHAR_COUNTER_RE.search(text or "")
        return (int(match.group(1)), int(match.group(2))) if match else (-1, -1)

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

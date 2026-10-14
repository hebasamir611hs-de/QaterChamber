"""
cms/pages/about_qatar_chamber/about_qatar_chamber_admin_page.py --
AboutQatarChamberObjectAuthoringPage.

PBI 129392 (QC-ABOUT 001 -- Qatar Chamber / the About Us page).

═══════════════════════════════════════════════════════════════════════
OBJECT NAMES FOR THIS FEATURE (from cms/Content-Admin-Guide.docx)
═══════════════════════════════════════════════════════════════════════
Source of truth is the team's Content Admin Guide, per standards.md ->
*"Object Names Come From cms/Content-Admin-Guide.docx -- Never Guessed,
Never Probed First"*. Guide section 23 + section 22 give TWO objects:

  - **AboutQatarChamberPage** (guide section 23, "one entry") -> slug
    `about-qatar-chamber-page` (`manage-about-qatar-chamber-page`).
    Singleton entry code `QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY`.
    Guide fields: pageTitle, pageContent, contentImage,
    contentImageAltText, hyperlinkTitle + hyperlinkUrl, pageStatus.

  - **AboutHeroBanner** (guide section 22) -> slug `about-hero-banner`
    (`manage-about-hero-banner`). ONE ROW PER PAGE, selected by `pageKey`;
    the About Us row is `QCDEMO-ABOUT-HERO-about-us`. Fields: pageKey,
    bannerImage, bannerImageAltText. Four rows exist live (about-us,
    chairman-message, vision-mission-objectives, chamber-laws).

**THE HERO BANNER IS NOT ON THE PAGE OBJECT -- THIS IS A REAL TRAP.**
The guide warns: *"the About Us and Chairman objects (sections 23, 24)
also contain an old heroBannerImage field -- it is no longer used for the
banner. Set the banner in AboutHeroBanner."* Confirmed live 2026-09-09,
with the exact mechanism:

  - `manage-about-qatar-chamber-page` DOES still render a `Hero Banner
    Image` attachment field, and it DOES hold a file
    (`about-hero-banner.png`, doc `4561f252-...`).
  - The public About Us page carries that file only as a DATA ATTRIBUTE
    (`data-qc-ap-hero-img` on `div.qc-about-page`) and never renders it.
  - What actually renders is `div.qc-ap-hero-media`'s inline
    `background-image: url(.../about-us-hero.png/7d50e4ad-...)` -- the
    **AboutHeroBanner** row's `Banner Image`.

So a test that writes the page object's own `Hero Banner Image` will save
happily and change NOTHING on the site. Any hero-banner case must drive
`open_hero_banner_record()`. `HERO_BANNER_IMAGE_LABEL_LEGACY` below is
kept only to name the trap explicitly, never to be written by a test.
═══════════════════════════════════════════════════════════════════════

Field labels below were read off the real edit forms live 2026-09-09
(authenticated headless Chromium, scoped CLI probe -- never the Playwright
MCP), in on-screen order. Composes `ObjectAuthoringPage`
(cms/pages/components/object_authoring_page.py) for all navigation and
lifecycle, mirroring `ChambersLawAdminPage`'s established convention --
this class holds only object identities + field-label constants.

Entry-column note (matters for which lookup helper is correct): BOTH of
these objects render a CODE in their Entry column -- the page object shows
its `QCDEMO-129392-...` external reference code, and AboutHeroBanner shows
the `pageKey` (`about-us`, `chairman-message`, ...). Neither renders a
title, so the `_by_code` lookups are the RIGHT ones here. (Contrast
`LawEntry`, whose Entry column renders the Law Title, where title-keyed
lookups are required -- getting that backwards cost two failed runs on
PBI 129394.)
"""

import re

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage

# ---- Object Authoring identities (guide sections 23 + 22) ---------------
ABOUT_PAGE_SLUG = "about-qatar-chamber-page"
ABOUT_PAGE_ENTRY_CODE = "QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY"

HERO_BANNER_SLUG = "about-hero-banner"
HERO_BANNER_ABOUT_US_ENTRY_CODE = "QCDEMO-ABOUT-HERO-about-us"
HERO_BANNER_ABOUT_US_PAGE_KEY = "about-us"


class AboutQatarChamberAdminPage(BasePage):
    """Drives PBI 129392's two Object Authoring objects. Every navigation
    and lifecycle action goes through `ObjectAuthoringPage` -- `Content &
    Data` is retired project-wide for Object-Definition-backed records
    (standards.md)."""

    ARABIC_SUFFIX = " — العربية"

    # ---- AboutQatarChamberPage fields (confirmed live, on-screen order) --
    PAGE_TITLE_LABEL = "Page Title"
    # The rich-text body. Its rendered LABEL is "Page Content Required"
    # (the required marker is concatenated into the accessible name), but
    # rich text is addressed by DOM field NAME, not label -- see
    # ObjectAuthoringPage.fill_rich_text()/rich_text_value().
    PAGE_CONTENT_FIELD_NAME = "pageContent"
    PAGE_CONTENT_LABEL = "Page Content Required"
    CONTENT_IMAGE_UPLOAD_LABEL = "Content Image"
    CONTENT_IMAGE_ALT_TEXT_LABEL = "Content Image Alt Text"
    HYPERLINK_TITLE_LABEL = "Hyperlink Title"
    HYPERLINK_URL_LABEL = "Hyperlink URL"
    # DO NOT WRITE THIS FIELD -- see the module docstring's trap note. It
    # exists on the form and saves cleanly, but the public page ignores it.
    HERO_BANNER_IMAGE_LABEL_LEGACY = "Hero Banner Image"
    HERO_BANNER_ALT_TEXT_LABEL_LEGACY = "Hero Banner Alt Text"

    # ---- AboutHeroBanner fields (the REAL hero banner) -------------------
    PAGE_KEY_LABEL = "Page Key"
    BANNER_IMAGE_UPLOAD_LABEL = "Banner Image"
    BANNER_IMAGE_ALT_TEXT_LABEL = "Banner Image Alt Text"

    def __init__(self, page):
        super().__init__(page)

    # ---- Navigation ------------------------------------------------------
    def open_page_record(self) -> "ObjectAuthoringPage":
        """The AboutQatarChamberPage singleton (guide section 23)."""
        authoring = ObjectAuthoringPage(self.page, slug=ABOUT_PAGE_SLUG)
        authoring.open_entry_by_code(ABOUT_PAGE_ENTRY_CODE)
        return authoring

    def open_page_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=ABOUT_PAGE_SLUG)
        authoring.open_entries_list()
        return authoring

    def open_hero_banner_record(self, locale: str | None = None) -> "ObjectAuthoringPage":
        """The AboutHeroBanner row whose pageKey is `about-us` (guide
        section 22) -- the object that ACTUALLY renders the hero banner.
        `locale` pins the interface language ("en"/"ar"); the settle is
        locale-independent (EDIT_BAR)."""
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        authoring.open_entry_by_code(HERO_BANNER_ABOUT_US_ENTRY_CODE, locale=locale)
        return authoring

    def open_hero_banner_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        authoring.open_entries_list()
        return authoring

    # =====================================================================
    # Added 2026-10-12 (PBI 129392 batch 2 -- 29 cases, scripted OFFLINE).
    # Locale-independent locators, mirroring ChambersLawAdminPage's
    # live-read 2026-10-12 convention on the sibling object
    # (`ObjectField_<name>` for the EN control, `#qc-ar-<name>` for its
    # Arabic twin). NOT read live on THIS object -- no browser session was
    # available while scripting. Names follow the guide's field keys (s.23).
    # =====================================================================
    # VERIFY-LIVE: field names on manage-about-qatar-chamber-page.
    PAGE_TEXT_FIELDS = {
        "page_title": ('input[name="ObjectField_pageTitle"]', "#qc-ar-pageTitle"),
        "alt_text": ('input[name="ObjectField_contentImageAltText"]', "#qc-ar-contentImageAltText"),
        "hyperlink_title": ('input[name="ObjectField_hyperlinkTitle"]', "#qc-ar-hyperlinkTitle"),
        "hyperlink_url": ('input[name="ObjectField_hyperlinkUrl"]', "#qc-ar-hyperlinkUrl"),
    }
    # VERIFY-LIVE: CKEditor instance-name suffixes for Page Content EN/AR.
    CONTENT_EDITOR_TOKENS = {"en": "ObjectField_pageContent", "ar": "qc-ar-pageContent"}
    # VERIFY-LIVE: hidden input name of the Content Image attachment field.
    CONTENT_IMAGE_FIELD_NAME = "ObjectField_contentImage"
    # Form submit buttons by Liferay `status` value: 0 = Publish / Submit
    # for Review (AR "نشر"), 2 = Save as Draft. Same on every object.
    PUBLISH_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    SAVE_DRAFT_SUBMIT = 'button[type="submit"][name="status"][value="2"]'
    ACCESS_DENIED_EN = "Access Denied. You do not have permission to perform this action."
    ACCESS_DENIED_AR = "تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا الإجراء."

    # ---- AboutHeroBanner (disposable QCTEST rows) -- same object and the
    # selectors ChambersLawAdminPage read live 2026-10-12. Method names
    # match that class so the shared hero-row helpers work on either.
    HERO_IMAGE_UPLOAD_LABEL = "Banner Image"
    HERO_IMAGE_FIELD_NAME = "ObjectField_bannerImage"
    HERO_PAGE_KEY_INPUT = 'input[name="ObjectField_pageKey"]'
    HERO_ALT_TEXT_INPUT = 'input[name="ObjectField_bannerImageAltText"]'
    UPLOAD_PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'

    # ---- Locale-aware navigation -------------------------------------------
    def open_page_record_in(self, locale: str = "en") -> "ObjectAuthoringPage":
        """Opens the singleton pinned to an interface language. The `/ar`
        render's banner is Arabic, so it settles on the title control."""
        authoring = ObjectAuthoringPage(self.page, slug=ABOUT_PAGE_SLUG)
        if locale == "ar":
            authoring.open(authoring._manage_url(edit_entry=ABOUT_PAGE_ENTRY_CODE, locale="ar"))
            authoring._entry_code = ABOUT_PAGE_ENTRY_CODE
            authoring._locale = "ar"
            self.page.locator(self.PAGE_TEXT_FIELDS["page_title"][0]).first.wait_for(
                state="visible", timeout=60000
            )
            return authoring
        authoring.open_entry_by_code(ABOUT_PAGE_ENTRY_CODE, locale="en")
        return authoring

    def open_manage_entry(self, slug: str, entry_code: str, locale: str | None = None) -> None:
        """Navigates to an edit URL WITHOUT waiting for a form (access-denied
        cases, where none must render)."""
        authoring = ObjectAuthoringPage(self.page, slug=slug)
        self.open(authoring._manage_url(edit_entry=entry_code, locale=locale))
        self.page.wait_for_load_state("load")

    # ---- Plain text fields (one helper for every text field) ---------------
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

    def page_has_edit_form(self) -> bool:
        return self.page.locator(self.PAGE_TEXT_FIELDS["page_title"][0]).count() > 0

    def has_object_form(self) -> bool:
        return self.page.locator('input[name^="ObjectField_"]').count() > 0

    # ---- Page Content rich text, as HTML (one helper for rich text) --------
    def _content_instance_js(self, locale: str) -> str:
        token = self.CONTENT_EDITOR_TOKENS[locale]
        return (
            "(() => { const k = Object.keys(CKEDITOR.instances).find(n => n.endsWith("
            f"'{token}')); return CKEDITOR.instances[k]; }})()"
        )

    def page_content_html(self, locale: str = "en") -> str:
        return self.page.evaluate(f"() => {self._content_instance_js(locale)}.getData()")

    def set_page_content_html(self, html: str, locale: str = "en") -> None:
        """CKEditor `setData()` + `updateElement()` + change event -- the
        byte-exact write used for baselines (typing doubles paragraphs)."""
        self.page.evaluate(
            "([html]) => new Promise(resolve => { const ed = "
            f"{self._content_instance_js(locale)}; ed.setData(html, {{ callback: () => {{"
            " ed.updateElement(); ed.fire('change'); resolve(true); } }); })",
            [html],
        )

    def page_content_direction(self, locale: str = "ar") -> str:
        token = self.CONTENT_EDITOR_TOKENS[locale]
        return self.page.frame_locator(f'[id^="cke_"][id$="{token}"] iframe').locator("body").evaluate(
            "b => (getComputedStyle(b).direction || b.getAttribute('dir') || '').toLowerCase()"
        )

    # ---- Attachment picker, by FIELD NAME (locale-independent) -------------
    def open_file_picker(self, field_name: str):
        hidden = self.page.locator(f'input[name="{field_name}"]').first
        button_id = hidden.get_attribute("id") + "-button-label"
        self.page.locator(f'[id="{button_id}"]').click()
        return self.page.frame_locator(self.UPLOAD_PICKER_IFRAME)

    @staticmethod
    def picker_set_file(frame, file_path: str) -> None:
        frame.locator('input[type="file"]').set_input_files(file_path)

    @staticmethod
    def picker_reports_uploaded(frame) -> bool:
        return frame.get_by_text("1 of 1").count() > 0

    # ---- Form controls / page state ----------------------------------------
    def publish_control_state(self) -> dict:
        """{"publish": (present, enabled, label), "draft": (...)}."""
        out = {}
        for key, sel in (("publish", self.PUBLISH_SUBMIT), ("draft", self.SAVE_DRAFT_SUBMIT)):
            loc = self.page.locator(sel)
            if loc.count() == 0:
                out[key] = (False, False, "")
            else:
                out[key] = (True, loc.first.is_enabled(), loc.first.inner_text().strip())
        return out

    def click_publish_control(self) -> None:
        self.page.locator(self.PUBLISH_SUBMIT).first.click()
        self.page.wait_for_load_state("load")

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def current_user_id(self) -> str:
        return str(self.page.evaluate("() => Liferay.ThemeDisplay.getUserId()"))

    def _page_row(self):
        return self.page.locator(f'table tbody tr:has-text("{ABOUT_PAGE_ENTRY_CODE}")').first

    def page_row_entry_id(self) -> str:
        """Numeric entry id off the singleton row's History control. Call on
        the open entries list."""
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

    # ---- Liferay Audit (Control Panel) -------------------------------------
    AUDIT_PORTLET_PATH = (
        "/group/guest/~/control_panel/manage?p_p_id="
        "com_liferay_portal_security_audit_web_portlet_AuditPortlet"
        "&_com_liferay_portal_security_audit_web_portlet_AuditPortlet_delta=200"
    )

    def audit_rows_for(self, resource_id: str) -> list:
        """Audit rows whose Resource ID equals `resource_id`, newest first:
        [User ID, User Name, Resource ID, Resource Name, Action, IP, Date]."""
        from config.settings import control_panel_url
        self.open(control_panel_url(self.AUDIT_PORTLET_PATH))
        self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=60000)
        rows = self.page.evaluate(
            "() => Array.from(document.querySelectorAll('table tbody tr')).map(r =>"
            " Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim()))"
        )
        return [r for r in rows if len(r) >= 5 and r[2] == str(resource_id)]

    # ---- Active Status (the second public-visibility gate) -- added
    # 2026-10-12 for the module-level singleton snapshot. VERIFY-LIVE: the
    # control name mirrors `ObjectField_activeStatus`, read live on
    # manage-chamber-laws-page; None when this form renders no such box.
    ACTIVE_STATUS_CHECKBOX = 'input[name="ObjectField_activeStatus"]'

    def active_status_or_none(self):
        box = self.page.locator(self.ACTIVE_STATUS_CHECKBOX)
        return box.first.is_checked() if box.count() else None

    def set_active_status(self, checked: bool) -> None:
        box = self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first
        box.check() if checked else box.uncheck()

    # ---- The object's own Status PICKLIST field (`pageStatus`) -- NOT the
    # workflow status. Added 2026-10-13 (P3/P4 batch, OFFLINE), mirroring
    # ChambersLawAdminPage's live-read picklist (`input[data-qc-oel-picklist]`
    # + `ObjectField_<ref>-label`). VERIFY-LIVE on this object: the form is
    # expected to render exactly one picklist.
    STATUS_PICKLIST_REF = "pageStatus"
    STATUS_PICKLIST_COMBOBOX = "input[data-qc-oel-picklist]"
    STATUS_PICKLIST_LABEL_INPUT = 'input[name="ObjectField_pageStatus-label"]'

    def page_status_value(self) -> str:
        """Current label of the record's Status picklist ("" if unset).
        Fails fast, naming the rendered fields, when the form has none."""
        from cms.pages.components.status_picklist import require_status_picklist

        require_status_picklist(self.page, self.STATUS_PICKLIST_LABEL_INPUT, self.STATUS_PICKLIST_COMBOBOX)
        box = self.page.locator(self.STATUS_PICKLIST_LABEL_INPUT)
        if box.count():
            return box.first.input_value().strip()
        return self.page.locator(self.STATUS_PICKLIST_COMBOBOX).first.input_value().strip()

    def _open_page_status_list(self):
        combo = self.page.locator(self.STATUS_PICKLIST_COMBOBOX).first
        combo.click()
        listbox = self.page.locator(f"#{combo.get_attribute('aria-controls')}")
        listbox.locator("[role=option]").first.wait_for(state="visible", timeout=10000)
        return listbox

    def page_status_options(self) -> list:
        """Every option the Status picklist offers, in order."""
        listbox = self._open_page_status_list()
        options = [t.strip() for t in listbox.locator("[role=option]").all_inner_texts()]
        self.page.keyboard.press("Escape")
        return options

    def pick_page_status(self, option: str) -> list:
        """Opens the Status picklist ONCE, returns every option it offered,
        selects `option` and verifies it by read-back (one re-pick). See
        cms/pages/components/status_picklist.py for why it is one action."""
        from cms.pages.components.status_picklist import pick_status_option

        return pick_status_option(self.page, self.STATUS_PICKLIST_COMBOBOX, option, self.page_status_value)

    def choose_page_status(self, option: str) -> None:
        listbox = self._open_page_status_list()
        listbox.locator("[role=option]").filter(
            has_text=re.compile(rf"^\s*{re.escape(option)}\s*$")
        ).first.click()

    # ---- AboutHeroBanner disposable rows ------------------------------------
    def open_hero_record(self, entry_code: str = HERO_BANNER_ABOUT_US_ENTRY_CODE,
                         locale: str | None = "en") -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        if locale == "ar":
            authoring.open(authoring._manage_url(edit_entry=entry_code, locale="ar"))
            authoring._entry_code = entry_code
            authoring._locale = "ar"
            self.page.locator(self.HERO_PAGE_KEY_INPUT).first.wait_for(state="visible", timeout=60000)
            return authoring
        authoring.open_entry_by_code(entry_code, locale=locale)
        return authoring

    def hero_entry_code(self, page_key: str) -> str:
        row = self.page.locator(f'table tbody tr:has-text("{page_key}")').first
        if row.count() == 0:
            return ""
        href = row.locator('a[href*="editEntry="]').first.get_attribute("href") or ""
        match = re.search(r"editEntry=([^&]+)", href)
        return match.group(1) if match else ""

    def hero_entry_code_exact(self, page_key: str) -> str:
        """editEntry code of the row whose Entry cell is EXACTLY `page_key`
        (call on the open hero list); "" when absent. Unlike
        hero_entry_code(), a key that merely CONTAINS `page_key` never
        matches -- the resolver for disposable QCTEST rows (2026-10-12)."""
        rows = self.page.locator("table tbody tr")
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = [c.strip() for c in row.locator("td").all_inner_texts()]
            if page_key in cells:
                href = row.locator('a[href*="editEntry="]').first.get_attribute("href") or ""
                match = re.search(r"editEntry=([^&]+)", href)
                return match.group(1) if match else ""
        return ""

    def hero_create_form_usable(self) -> bool:
        """True only on a genuine, EMPTY create form: no `editEntry` in the
        URL, no "Editing <x> (<status>)" banner, and a visible, editable,
        empty Page Key. Guards the singleton manage-page trap -- a manage
        page with no create form opens a live record instead (2026-10-04)."""
        if "editEntry=" in (self.page.url or ""):
            return False
        if self.page.get_by_text(re.compile(r"^Editing .+\(", re.I)).count():
            return False
        key = self.page.locator(self.HERO_PAGE_KEY_INPUT).first
        try:
            return key.is_visible() and key.is_editable() and key.input_value() == ""
        except Exception:  # noqa: BLE001 -- no such control
            return False

    def open_new_hero_form(self, locale: str | None = "en") -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        authoring.open_new_entry_form(locale=locale)
        return authoring

    def open_hero_entries_list(self, locale: str | None = "en") -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        authoring.open_entries_list(locale=locale)
        return authoring

    def fill_hero_page_key(self, value: str) -> None:
        self.page.locator(self.HERO_PAGE_KEY_INPUT).first.fill(value)

    def hero_alt_text(self) -> str:
        return self.page.locator(self.HERO_ALT_TEXT_INPUT).first.input_value()

    def fill_hero_alt_text(self, value: str) -> None:
        self.page.locator(self.HERO_ALT_TEXT_INPUT).first.fill(value)

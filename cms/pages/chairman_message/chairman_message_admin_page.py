"""
cms/pages/chairman_message/chairman_message_admin_page.py — Control_Panel Page
Objects for PBI 129393 (QC-ABOUT-002, Chairman's Message).

Two Object Authoring objects back this page (cms/Content-Admin-Guide.docx §22,
§24):

  1. **Chairman Message Page** (`ChairmanMessagePage`) — slug
     `chairman-message-page`, a SINGLETON. Its one live record is
     `QCDEMO-129393-chairmans-message` (row id 78261). Slug, entry code and the
     EN field labels were read live 2026-09-07 (see the retired
     web/pages/about_chairman_message/chairman_message_admin_page.py). Every
     write to it is TEST_OWNED: capture → mutate → restore → verify by re-read
     (done in the test module).
  2. **About Hero Banner** (`AboutHeroBanner`) — slug `about-hero-banner`, one
     row per page selected by `Page Key` (`chairman-message` for this page).
     Guide §24 / ¶142: the TOP BANNER of this page is set there; the
     `heroBannerImage` field still present on the Chairman object is "no
     longer used for the banner — leave that old field alone". Hero-banner
     FIELD cases therefore run on disposable `QCTEST-<tc>-HERO` rows (a page
     key no page renders), exactly as cms/pages/chambers_law does.

Field access is label-driven for the English interface
(`ObjectAuthoringPage.label_pattern()` tolerates the required " *"; the Arabic
twin is "<Label> — العربية"). Arabic-interface steps use the locale-independent
`ObjectField_<name>` / `#qc-ar-<name>` controls.
"""

from __future__ import annotations

import re

from cms.pages.components.disposable_object_admin import (
    DisposableObjectAdminPage,
    FieldSpec as F,
)
from config.settings import control_panel_url

CHAIRMAN_MESSAGE_SLUG = "chairman-message-page"
CHAIRMAN_MESSAGE_ENTRY_CODE = "QCDEMO-129393-chairmans-message"
CHAIRMAN_MESSAGE_ROW_ID = "78261"

HERO_BANNER_SLUG = "about-hero-banner"
HERO_PAGE_KEY = "chairman-message"


class ChairmanMessageAdminPage(DisposableObjectAdminPage):
    """The singleton Chairman Message Page record. Inherits role sign-in,
    the declarative `FIELDS` fill/read path and `refusal_visible()` from
    DisposableObjectAdminPage; never creates or deletes a record."""

    SIDEBAR_LABEL = "Chairman Message Page"
    SLUG = CHAIRMAN_MESSAGE_SLUG
    SLUG_CONFIRMED_LIVE = True  # read live 2026-09-07 (/object-authoring sidebar)
    SINGLETON = True
    TITLE_FIELD = "page_title"
    ACTIVE_FIELD = None  # VERIFY-LIVE: this object shows no Active Status checkbox in the 2026-09-07 inventory
    FIELDS = {
        "page_title": F("Page Title", bilingual=True, required=True, confirmed_live=True),
        "hero_alt": F("Hero Banner Alt Text", bilingual=True, required=True, confirmed_live=True),
        "portrait": F("Chairman Portrait", kind="file", required=True, confirmed_live=True),
        "portrait_alt": F("Chairman Portrait Alt Text", bilingual=True, required=True, confirmed_live=True),
        "name": F("Chairman Name", bilingual=True, required=True, confirmed_live=True),
        "designation": F("Chairman Designation", bilingual=True, required=True, confirmed_live=True),
        "message": F("Message Content", kind="rich", bilingual=True, required=True,
                     ref="messageContent", confirmed_live=True),
        "hyperlink_title": F("Hyperlink Title", confirmed_live=True),
        "hyperlink_url": F("Hyperlink URL", kind="url", confirmed_live=True),
    }
    TEXT_KEYS = ("page_title", "hero_alt", "portrait_alt", "name", "designation")

    # Locale-independent controls (pattern read live on chamber-laws-page
    # 2026-10-12, same qc-oel form). VERIFY-LIVE on this object.
    TEXT_CONTROLS = {
        "page_title": ('input[name="ObjectField_pageTitle"]', "#qc-ar-pageTitle"),
        "hero_alt": ('input[name="ObjectField_heroBannerAltText"]', "#qc-ar-heroBannerAltText"),
        "portrait_alt": ('input[name="ObjectField_chairmanPortraitAltText"]', "#qc-ar-chairmanPortraitAltText"),
        "name": ('input[name="ObjectField_chairmanName"]', "#qc-ar-chairmanName"),
        "designation": ('input[name="ObjectField_chairmanDesignation"]', "#qc-ar-chairmanDesignation"),
    }
    # CKEditor 4 instance-name suffixes for Message Content. VERIFY-LIVE: the
    # EN token was read live 2026-09-07; the AR token follows chamber-laws-page.
    MESSAGE_EDITOR_TOKENS = {"en": "ObjectField_messageContent", "ar": "qc-ar-messageContent"}
    PUBLISH_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    ROW_HISTORY_ATTR = "data-qc-oel-history"

    # ---- navigation -----------------------------------------------------
    def open_record(self, locale: str | None = "en") -> "ChairmanMessageAdminPage":
        """Opens the ONE live record by its code — never by position."""
        if locale == "ar":
            self.open(self._manage_url(edit_entry=CHAIRMAN_MESSAGE_ENTRY_CODE, locale="ar"))
            self._entry_code = CHAIRMAN_MESSAGE_ENTRY_CODE
            self._locale = "ar"
            self.page.locator(self.TEXT_CONTROLS["page_title"][0]).first.wait_for(
                state="visible", timeout=60000)
            return self
        self.open_entry_by_code(CHAIRMAN_MESSAGE_ENTRY_CODE, locale=locale)
        return self

    def open_record_raw(self, locale: str | None = None) -> int | None:
        """Navigates to the record's edit URL WITHOUT waiting for a form —
        for access-denied cases. Returns the HTTP status."""
        resp = self.page.goto(
            self._manage_url(edit_entry=CHAIRMAN_MESSAGE_ENTRY_CODE, locale=locale),
            wait_until="domcontentloaded")
        self.page.wait_for_load_state("load")
        return resp.status if resp else None

    def has_object_form(self) -> bool:
        return self.page.locator('input[name^="ObjectField_"]').count() > 0

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    # ---- text fields (locale-independent) -------------------------------
    def _control(self, key: str, locale: str):
        en, ar = self.TEXT_CONTROLS[key]
        return self.page.locator(ar if locale == "ar" else en).first

    def text_of(self, key: str, locale: str = "en") -> str:
        return self._control(key, locale).input_value()

    def set_text(self, key: str, value: str, locale: str = "en") -> None:
        self._control(key, locale).fill(value)

    # ---- Message Content (CKEditor, HTML-exact) --------------------------
    def _editor_js(self, locale: str) -> str:
        token = self.MESSAGE_EDITOR_TOKENS[locale]
        return ("(() => { const k = Object.keys(CKEDITOR.instances).find(n => n.endsWith("
                f"'{token}')); return CKEDITOR.instances[k]; }})()")

    def message_html(self, locale: str = "en") -> str:
        return self.page.evaluate(f"() => {self._editor_js(locale)}.getData()")

    def set_message_html(self, html: str, locale: str = "en") -> None:
        """CKEditor `setData()` + `updateElement()` — byte-exact, so a captured
        baseline (headings, lists, links) is restored without the flattening
        that re-typing plain text would cause."""
        self.page.evaluate(
            "([html]) => new Promise(resolve => { const ed = "
            f"{self._editor_js(locale)}; ed.setData(html, {{ callback: () => {{"
            " ed.updateElement(); ed.fire('change'); resolve(true); } }); })",
            [html],
        )

    def message_direction(self, locale: str = "ar") -> str:
        token = self.MESSAGE_EDITOR_TOKENS[locale]
        return self.page.frame_locator(f'[id^="cke_"][id$="{token}"] iframe').locator("body").evaluate(
            "b => (getComputedStyle(b).direction || b.getAttribute('dir') || '').toLowerCase()")

    # ---- attachments -------------------------------------------------------
    def portrait_name(self) -> str:
        return self.current_file_name(self.spec("portrait").label)

    def restore_existing_file(self, key: str, file_name: str) -> None:
        """Re-selects the captured baseline Documents & Media file.
        VERIFY-LIVE: the folder holding the live portrait is unknown; root is
        tried first, then `qatar-chamber-website`."""
        label = self.spec(key).label
        last = None
        for folder in (None, "qatar-chamber-website"):
            try:
                self.select_existing_file(label, file_name, folder=folder)
                return
            except Exception as exc:  # noqa: BLE001 — try the next folder
                last = exc
                self.page.keyboard.press("Escape")
        raise AssertionError(f"could not re-select baseline file {file_name!r}: {last!r}")

    def existing_file_findable(self, key: str, file_name: str) -> bool:
        """Pre-flight for a TEST_OWNED file restore: opens the field's picker,
        looks for `file_name` in the root and in `qatar-chamber-website`
        WITHOUT selecting it, then closes the picker. VERIFY-LIVE (folder)."""
        label = self.spec(key).label
        box = self.page.get_by_role("textbox", name=f"{label} Select File")
        box.locator("xpath=..").get_by_role("button", name="Select File").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        found = False
        try:
            target = frame.get_by_text(file_name, exact=True).first
            try:
                target.wait_for(state="visible", timeout=10000)
                found = True
            except Exception:  # noqa: BLE001 — not in the root; try the folder
                frame.get_by_role("link", name="qatar-chamber-website").first.click()
                target.wait_for(state="visible", timeout=10000)
                found = True
        except Exception:  # noqa: BLE001 — not found anywhere
            found = False
        self.page.keyboard.press("Escape")
        return found

    # ---- Active Status (the second public-visibility gate) -- added
    # 2026-10-12 for the module-level singleton snapshot. ACTIVE_FIELD is None
    # (no checkbox seen in the 2026-09-07 inventory), so this reads None unless
    # one renders. VERIFY-LIVE: name mirrors chamber-laws-page.
    ACTIVE_STATUS_CHECKBOX = 'input[name="ObjectField_activeStatus"]'

    def active_status_or_none(self):
        box = self.page.locator(self.ACTIVE_STATUS_CHECKBOX)
        return box.first.is_checked() if box.count() else None

    def set_active_status(self, checked: bool) -> None:
        box = self.page.locator(self.ACTIVE_STATUS_CHECKBOX).first
        box.check() if checked else box.uncheck()

    # ---- The object's own Status PICKLIST field (`publishStatus`) -- NOT the
    # workflow status. Added 2026-10-13 (P3/P4 batch, OFFLINE), mirroring
    # ChambersLawAdminPage's live-read picklist (`input[data-qc-oel-picklist]`
    # + `ObjectField_<ref>-label`). VERIFY-LIVE on this object: the form is
    # expected to render exactly one picklist.
    STATUS_PICKLIST_REF = "publishStatus"
    STATUS_PICKLIST_COMBOBOX = "input[data-qc-oel-picklist]"
    STATUS_PICKLIST_LABEL_INPUT = 'input[name="ObjectField_publishStatus-label"]'

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

    # ---- controls / permissions --------------------------------------------
    def control_state(self) -> dict:
        """{name: (present, enabled)} for the form's lifecycle controls."""
        out = {}
        for name, sel in (("save_draft", self.SAVE_AS_DRAFT_BUTTON),
                          ("submit", self.SUBMIT_FOR_REVIEW_BUTTON),
                          ("unpublish", self.UNPUBLISH_BUTTON)):
            loc = self.page.locator(sel)
            out[name] = (loc.count() > 0, loc.count() > 0 and loc.first.is_enabled())
        return out

    def row_actions_for_record(self) -> list[str]:
        """data-qc-oel-* action attributes on the record's own list row."""
        row = self.page.locator(f'table tbody tr:has-text("{CHAIRMAN_MESSAGE_ENTRY_CODE}")').first
        if row.count() == 0:
            return []
        return row.evaluate(
            "r => Array.from(r.querySelectorAll('*')).flatMap(e => Array.from(e.attributes)"
            ".map(a => a.name)).filter(n => n.startsWith('data-qc-oel-'))")

    def record_entry_id(self) -> str:
        """Numeric entry id off the row's History control (call on the list)."""
        row = self.page.locator(f'table tbody tr:has-text("{CHAIRMAN_MESSAGE_ENTRY_CODE}")').first
        return row.locator(f"[{self.ROW_HISTORY_ATTR}]").first.get_attribute(self.ROW_HISTORY_ATTR) or ""

    # ---- Liferay audit log (TC 134779) -------------------------------------
    AUDIT_PORTLET_PATH = (
        "/group/guest/~/control_panel/manage?p_p_id="
        "com_liferay_portal_security_audit_web_portlet_AuditPortlet"
        "&_com_liferay_portal_security_audit_web_portlet_AuditPortlet_delta=200"
    )

    def audit_rows_for(self, resource_id: str) -> list:
        """Audit rows whose Resource ID equals `resource_id`, each as cell
        texts [User ID, User Name, Resource ID, Resource Name, Action, IP,
        Create Date]. Same portlet path as chambers_law (read live there)."""
        self.open(control_panel_url(self.AUDIT_PORTLET_PATH))
        self.page.locator("table tbody tr").first.wait_for(state="visible", timeout=60000)
        rows = self.page.evaluate(
            "() => Array.from(document.querySelectorAll('table tbody tr')).map(r =>"
            " Array.from(r.querySelectorAll('td')).map(td => td.innerText.trim()))")
        return [r for r in rows if len(r) >= 5 and r[2] == str(resource_id)]


class ChairmanHeroBannerAdminPage(DisposableObjectAdminPage):
    """About Hero Banner rows (one per page, keyed by Page Key). Inputs read
    live on this object 2026-10-12 (cms/pages/chambers_law). The Entry column
    shows the Page Key, so a row is resolved by its EXACT page key — never by
    position — and only `QCTEST-*` rows can be deleted (base-class guard)."""

    SIDEBAR_LABEL = "About Hero Banner"
    SLUG = HERO_BANNER_SLUG
    SLUG_CONFIRMED_LIVE = True  # read live 2026-09-09 / 2026-10-12
    TITLE_FIELD = "page_key"
    ACTIVE_FIELD = None
    FIELDS = {
        "page_key": F("Page Key", required=True, confirmed_live=True),
        "banner_image": F("Banner Image", kind="file", required=True, confirmed_live=True),
        "alt": F("Banner Image Alt Text", required=True, confirmed_live=True),
    }
    PAGE_KEY_INPUT = 'input[name="ObjectField_pageKey"]'
    ALT_TEXT_INPUT = 'input[name="ObjectField_bannerImageAltText"]'
    IMAGE_LABEL = "Banner Image"
    PUBLISH_SUBMIT = 'button[type="submit"][name="status"][value="0"]'
    UPLOAD_PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'
    PICKER_UPLOADED_TEXT = "1 of 1"
    PICKER_DECISION_TIMEOUT_MS = 20000

    def open_new(self) -> "ChairmanHeroBannerAdminPage":
        self.open_new_entry_form(locale="en")
        return self

    def entry_code_for_key(self, page_key: str) -> str:
        """editEntry code of the row whose Entry column is exactly
        `page_key` (call on the open list); "" when absent."""
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        for i in range(rows.count()):
            row = rows.nth(i)
            cells = [c.strip() for c in row.locator("td").all_inner_texts()]
            if page_key in cells:
                href = row.locator('a[href*="editEntry="]').first.get_attribute("href") or ""
                m = re.search(r"editEntry=([^&]+)", href)
                return m.group(1) if m else ""
        return ""

    def open_by_key(self, page_key: str, locale: str = "en") -> "ChairmanHeroBannerAdminPage":
        self.open_entries_list(locale="en")
        self.filter_entries(page_key)
        code = self.entry_code_for_key(page_key)
        if not code:
            raise AssertionError(f"no About Hero Banner row with Page Key {page_key!r}")
        if locale == "ar":
            self.open(self._manage_url(edit_entry=code, locale="ar"))
            self._entry_code, self._locale = code, "ar"
            self.page.locator(self.PAGE_KEY_INPUT).first.wait_for(state="visible", timeout=60000)
            return self
        self.open_entry_by_code(code, locale="en")
        return self

    def fill_page_key(self, value: str) -> None:
        self.page.locator(self.PAGE_KEY_INPUT).first.fill(value)

    def alt_text(self) -> str:
        return self.page.locator(self.ALT_TEXT_INPUT).first.input_value()

    def fill_alt_text(self, value: str) -> None:
        self.page.locator(self.ALT_TEXT_INPUT).first.fill(value)

    def image_name(self) -> str:
        return self.current_file_name(self.IMAGE_LABEL)

    def publish(self) -> None:
        self.submit_via(self.PUBLISH_SUBMIT)

    def attempt_upload_by_field(self, field_name: str, file_path: str) -> bool:
        """Opens the attachment picker by FIELD NAME (works in both interface
        languages), sets the file, and reports whether the picker accepted it
        ("1 of 1" uploaded). Never clicks Add, so a rejected file can never
        half-attach. VERIFY-LIVE: acceptance signal read on chamber-laws."""
        hidden = self.page.locator(f'input[name="{field_name}"]').first
        button_id = (hidden.get_attribute("id") or "") + "-button-label"
        self.page.locator(f'[id="{button_id}"]').click()
        frame = self.page.frame_locator(self.UPLOAD_PICKER_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        try:
            frame.get_by_text(self.PICKER_UPLOADED_TEXT).first.wait_for(
                state="visible", timeout=self.PICKER_DECISION_TIMEOUT_MS)
            accepted = True
        except Exception:  # noqa: BLE001 — no acceptance within budget = rejected
            accepted = False
        try:
            self.last_picker_text = frame.locator("body").inner_text()[:500]
        except Exception:  # noqa: BLE001
            self.last_picker_text = ""
        self.page.keyboard.press("Escape")
        return accepted

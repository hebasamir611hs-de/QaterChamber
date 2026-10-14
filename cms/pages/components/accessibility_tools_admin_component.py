"""
cms/pages/components/accessibility_tools_admin_component.py — AccessibilitySettingsPage.

The Azure cases call this surface "Global Components -> Header Management ->
Accessibility Settings". On the current build it is the Object Authoring
manage page of the `AccessibilityHeaderConfiguration` Object
(cms/Content-Admin-Guide.docx §3), which is the only content path
(standards.md -> "Object Authoring Is the Only Path"):

    /web/qatar-chamber/manage-accessibility-header-configuration

Backs PBI 129364 (QC-GBL-003 Accessibility Tools) Control_Panel cases, and
the older NO-PBI RBAC test `test_restricted_role_denied_accessibility_settings`
(ADO 134658).

READ LIVE 2026-09-30 (read-only, TEST_USER storageState — the role accounts
in .env could not sign in, see below):
  - ONE entry (a singleton, per the guide): Entry code
    8f47e8e3-fcc8-a55f-845a-87b59c92c88f, entryId 45370, badge PUBLISHED.
  - Opened for edit, `Accessibility Tools Enabled` was TICKED and
    `Active Status` was ticked. The create form (no ?editEntry) renders the
    same checkbox UNTICKED — that is the new-entry default, not the stored
    value, so a "saved state" read must come off the edit form.
  - The checkbox's accessible name is "Accessibility Tools Enabled"; its
    `name` attribute is `ObjectField_accessibilityToolsEnabled`. Its `id` is
    regenerated on every render and is not used.
  - Signed out, the manage URL answers 404 with the site's "Coming Soon" page
    (h1.qc-error-title), EN and /ar alike — the guide's documented behaviour.

NOT READ LIVE — the Site Member's view. `CMS_SITE_MEMBER_*` is unset in .env
and the Editor/Author keys still hold the retired `*@xyz.com` logins
("Authentication failed ... account lockout"). So ACCESS_DENIED_MESSAGE_EN/_AR
stay placeholders; the denial tests in the test module assert the case's
wording off the rendered body text instead, so they can fail on whatever the
member really sees.

THIS PAGE OBJECT HAS NO SAVE PATH, ON PURPOSE. The live entry is the real
site-wide setting; saving, submitting, publishing or unpublishing it changes
qcdev for every visitor (engineer brief 2026-09-30, hard rule 1). The only
write available here is ticking/unticking the checkbox in the browser and
then leaving without saving. Do not add a save/submit method to this class.
"""

from cms.pages.components.header_admin_component import _TrackedFormMixin
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url
from core.utils.waits import wait_until
from core.web.base_page import BasePage
from core.web.license_gate import clear_license_gate

_UNVERIFIED = "TODO: run tools/extract_locators.py against the live page and paste the confirmed selector here"


class AccessibilityConfigWriter(_TrackedFormMixin, ObjectAuthoringPage):
    """Writes to the ONE live AccessibilityHeaderConfiguration entry (id 45370)
    — approved by the user 2026-10-01, ID-named, with snapshot -> restore ->
    verify (`a11y_config_guard` in the test module). Uses Submit on the
    Published record only: Submit updates the record in place (proven live by
    134273 on HeaderConfiguration), whereas Unpublish + Save as Draft was seen
    live to create a SECOND entry (bug-verify-20261001-1432). Never unpublish,
    save-as-draft or delete this entry."""

    LIVE_ENTRY_ID = "45370"
    LIVE_ENTRY_CODE = "8f47e8e3-fcc8-a55f-845a-87b59c92c88f"

    def __init__(self, page):
        super().__init__(page, AccessibilitySettingsPage.SLUG)

    save_draft = None  # deliberately unavailable on this singleton


class AccessibilitySettingsPage(BasePage):
    SLUG = "accessibility-header-configuration"
    SETTINGS_PATH = "/web/qatar-chamber/manage-accessibility-header-configuration"
    OBJECT_AUTHORING_INDEX_PATH = "/web/qatar-chamber/object-authoring"

    # Denial wording the Site Member sees has not been observed (see module
    # docstring). Kept as placeholders so the legacy test's blocker gate still
    # names them.
    ACCESS_DENIED_MESSAGE_EN = _UNVERIFIED
    ACCESS_DENIED_MESSAGE_AR = _UNVERIFIED

    TOGGLE_LABEL = "Accessibility Tools Enabled"
    ACCESSIBILITY_TOOLS_TOGGLE = 'input[type="checkbox"][name="ObjectField_accessibilityToolsEnabled"]'
    # Presence = the authoring form for this Object actually rendered.
    SETTINGS_FORM = 'form:has(input[name="ObjectField_accessibilityToolsEnabled"])'
    ENTRIES_TABLE = "table[data-qc-oel-table]"
    ENTRY_ROW = "table[data-qc-oel-table] tbody tr"
    ENTRY_CODE_ATTR = "data-qc-oel-label"

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, self.SLUG)

    # ---- helpers ---------------------------------------------------------
    def _require_verified(self, value: str, name: str) -> None:
        if value == _UNVERIFIED:
            raise RuntimeError(
                f"AccessibilitySettingsPage.{name} is an unverified placeholder — run "
                f"tools/extract_locators.py against the live page (as an account that "
                f"sees it) and replace it before running this test."
            )

    def settings_url(self, locale: str | None = None) -> str:
        prefix = f"/{locale}" if locale and locale != "en" else ""
        return control_panel_url(f"{prefix}{self.SETTINGS_PATH}")

    # ---- navigation ------------------------------------------------------
    def open_settings(self, locale: str | None = None) -> "AccessibilitySettingsPage":
        """Plain navigation, no wait for the form. This is the denial path's
        entry point: a refused account must not be made to wait on a form it
        should never get. `locale="ar"` requests the /ar-prefixed URL.

        Deliberately NOT BasePage.open(). That wrapper runs
        session_guard.reauthenticate(), which treats a manage-URL page without
        `body.signed-in` as a dropped session and signs in as TEST_USER. That
        would silently swap the Site Member for the admin mid-denial-check.
        Only the license-gate guard is kept."""
        url = self.settings_url(locale)
        self.page.goto(url, wait_until="domcontentloaded")
        clear_license_gate(self.page, url)
        return self

    def _open_entries_table(self) -> None:
        """Opens the entries list and waits on the row's own entry-code link
        (`a[data-qc-oel-label]`, seen live on the row). It does not use
        ObjectAuthoringPage.open_entries_list(), which waits on the Delete
        link: that link was only observed as TEST_USER, and the role sheet
        does not give the Editor Delete."""
        self.open(control_panel_url(f"/en{self.SETTINGS_PATH}"))  # pinned EN, as ObjectAuthoringPage does
        self.wait_for(f"{self.ENTRY_ROW} a[{self.ENTRY_CODE_ATTR}]", first=True, timeout=35000)

    def open_stored_entry(self) -> str:
        """Opens the ONE stored entry for edit and returns its entry code.

        Resolved off the entries table, never positionally: the table must
        hold exactly one row (the guide's singleton), otherwise this raises
        rather than guess which row is the live setting."""
        self._open_entries_table()
        rows = self.page.locator(self.ENTRY_ROW)
        count = rows.count()
        if count != 1:
            raise AssertionError(
                f"manage-{self.SLUG} lists {count} entries; the guide defines ONE "
                "AccessibilityHeaderConfiguration entry. Refusing to pick one."
            )
        code = rows.first.locator(f"a[{self.ENTRY_CODE_ATTR}]").first.get_attribute(self.ENTRY_CODE_ATTR) or ""
        if not code:
            raise AssertionError(f"could not read the entry code from the single manage-{self.SLUG} row")
        self.authoring.open_entry_by_code(code, locale="en")
        self.wait_for(self.ACCESSIBILITY_TOOLS_TOGGLE, state="attached", timeout=15000)
        return code

    def reopen_stored_entry(self) -> "AccessibilitySettingsPage":
        """Fresh navigation back to the entry last opened — never go_back(),
        which could restore the browser's unsaved form state."""
        self.authoring.reopen()
        self.wait_for(self.ACCESSIBILITY_TOOLS_TOGGLE, state="attached", timeout=15000)
        return self

    def leave_without_saving(self) -> "AccessibilitySettingsPage":
        """Navigates to the Object Authoring index without clicking anything
        on the form. A `beforeunload` prompt (if the form raises one) is
        accepted so the navigation completes; ANY other dialog is dismissed —
        on the live singleton a stray confirm() must never be accepted."""

        def _on_dialog(dialog):
            if dialog.type == "beforeunload":
                dialog.accept()
            else:
                dialog.dismiss()

        self.page.on("dialog", _on_dialog)
        try:
            self.open(control_panel_url(self.OBJECT_AUTHORING_INDEX_PATH))
            self.page.wait_for_url("**/object-authoring**", timeout=20000)
        finally:
            self.page.remove_listener("dialog", _on_dialog)
        return self

    # ---- checkbox (browser-side only; never saved) -----------------------
    def toggle_visible(self) -> bool:
        return self.is_visible(self.ACCESSIBILITY_TOOLS_TOGGLE)

    def toggle_checked(self) -> bool:
        return self.authoring.is_checked(self.TOGGLE_LABEL)

    def set_toggle_unsaved(self, checked: bool) -> "AccessibilitySettingsPage":
        """Ticks/unticks the checkbox in the browser only. Nothing here
        submits — see the module docstring."""
        self.authoring.set_checkbox(self.TOGGLE_LABEL, checked)
        return self

    # ---- stored-record reads (off a fresh entries list) -------------------
    def row_status(self, entry_code: str) -> str:
        """The row's workflow badge, normalized (e.g. STATUS_PUBLISHED). Read
        off the list, where the PUBLISHED badge was seen live. The edit
        banner's wording has not been checked on this Object."""
        self._open_entries_table()
        return self.authoring.row_status_text_by_code(entry_code)

    def row_last_modified(self, entry_code: str) -> str:
        """The entry row's Last-modified cell, from a fresh entries list."""
        self._open_entries_table()
        row = self.page.locator(f'{self.ENTRY_ROW}:has-text("{entry_code}")')
        return row.locator("td").nth(2).inner_text().strip()

    # ---- denial-state reads ----------------------------------------------
    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def wait_for_body_text(self, expected: str, timeout: float = 20.0) -> bool:
        """True once `expected` appears in the rendered body, False if it
        never does within `timeout`. Text is compared, not used as a
        locator, so no Arabic selector is ever built."""
        try:
            wait_until(lambda: expected in self.body_text(), timeout=timeout, poll=0.5,
                       message=f"{expected!r} never rendered")
            return True
        except Exception:  # noqa: BLE001 — caller asserts with the page state in the message
            return False

    def page_heading(self) -> str:
        """Title + first h1 text, for failure messages only."""
        h1 = self.page.locator("h1:visible")
        first = h1.first.inner_text().strip() if h1.count() else ""
        return f"{self.page.title()!r} / h1={first!r} / url={self.page.url}"

    def settings_form_loaded(self) -> bool:
        return self.is_visible(self.SETTINGS_FORM)

    def entries_table_visible(self) -> bool:
        return self.page.locator(self.ENTRIES_TABLE).count() > 0

    def submit_control_present(self) -> bool:
        """Any submit button inside the authoring form, whatever its label.
        The label varies by account and build: "Submit for Review" / "Publish"
        per the shared constant, and a different label read live as TEST_USER
        on 2026-09-30. So this matches structurally, not by text."""
        return self.page.locator(f"{self.SETTINGS_FORM} button[type=\"submit\"]").count() > 0

    # ---- legacy API used by test_restricted_role_denied_accessibility_settings
    def _denial_locator(self, locale: str = "en") -> str:
        name = "ACCESS_DENIED_MESSAGE_AR" if locale == "ar" else "ACCESS_DENIED_MESSAGE_EN"
        locator = getattr(self, name)
        self._require_verified(locator, name)
        return locator

    def wait_for_denial(self, locale: str = "en", timeout: int = 10000) -> None:
        """Positive ANCHOR for the denial state — call this BEFORE any negative
        assertion (form absent / toggle absent). BasePage.is_visible() is
        zero-wait by design, so asserting `not settings_form_loaded()` straight
        after navigation is a race: it can pass simply because nothing has
        rendered yet."""
        self.wait_for(self._denial_locator(locale), timeout=timeout)

    def access_denied_shown(self, locale: str = "en") -> bool:
        return self.is_visible(self._denial_locator(locale))

    def denial_text(self, locale: str = "en") -> str:
        return self.text(self._denial_locator(locale))

    def accessibility_toggle_visible(self) -> bool:
        return self.toggle_visible()

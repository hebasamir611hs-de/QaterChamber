"""
cms/pages/components/header_admin_component.py — Site Header (PBI 129363, QC-GBL-001).

Control_Panel Page Objects for the two Object-Definition-backed header objects
named in `cms/Content-Admin-Guide.docx` §3, both driven through Object
Authoring and composing `ObjectAuthoringPage`:

  - `HeaderConfigurationAdminPage` — `manage-header-configuration`. ONE entry,
    `QCDEMO-129363-HEADER-CONFIG-DEFAULT`, which IS the real live site header
    (user-confirmed). Since 2026-10-01 (brief v2, user's ID-named approval) it
    exposes the approved writes plus snapshot()/restore()/diff_from() for the
    tests' snapshot-restore-verify fixture; delete/archive still raise.
  - `NavItemAdminPage` — `manage-nav-item`. Tests operate ONLY on disposable
    `QCTEST-<tc_id>-*` items; every destructive helper refuses anything else.

Plus `PublicHeaderNavProbe`, a thin subclass of the public-site
`HeaderComponent` (web/pages/components/header_component.py) adding href-based
presence/position reads for one QCTEST nav item. It lives here, not in the
web file, only because this batch may not edit other files — see the report.

LOCATORS — extracted live 2026-09-30 (eng-header) with scoped Playwright CLI
scripts through the framework's own BasePage/CmsLoginPage, 1920x1080, signed
in as TEST_USER for read-only extraction (the `.env` role credentials were not
usable — see "ENVIRONMENT BLOCKERS" below). One disposable NavItem,
`QCTEST-PROBE-HDR-nav` (id 277406), was created and deleted during extraction.

Confirmed live on `manage-nav-item` (page title "Manage: Navigation Item"):
  - Form fields, accessible names (label `for=`/`aria-labelledby` wiring works,
    so `get_by_role(..., name=label_pattern(...))` resolves each uniquely):
      Nav Item Label EN *   textbox   name=ObjectField_navItemLabelEn  required
      Nav Item Label AR *   textbox   name=ObjectField_navItemLabelAr  required
      Nav Item URL          textbox   name=ObjectField_navItemUrl
      Display Order *       spinbutton type=number min=-2147483648  required
      Active Status         checkbox  (unticked by default)
      Nav Item Level        combobox  options "1" / "2" / "3" (level1..3)
      Parent Menu           textbox   (free text)
      Parent Item           combobox  relationship r_navItemParent_c_navItemId
    The guide says depth is derived from Parent Item with "no level to set";
    the live form DOES carry `Nav Item Level` and a free-text `Parent Menu` —
    reported as a guide-vs-UI contradiction, not acted on.
  - The two form buttons are `button[type=submit][name=status]`: "Save as
    Draft" and — for TEST_USER on this object — "Submit for Publishing". The
    shared `ObjectAuthoringPage.SUBMIT_FOR_REVIEW_BUTTON` matches only
    "Submit for Review" / "Publish", so it resolves NOTHING here. This class
    therefore uses a label-agnostic structural locator (`SUBMIT_BUTTON`): the
    status-submit button that is not Save as Draft. It matches whichever label
    the signed-in account is shown, and carries no legacy literal.
  - Entry column shows `navItemLabelEn` (the object's configured titleField).
    Row actions carry `data-qc-oel-<action>="<entryId>"` plus
    `data-qc-oel-label="<label>"`. The Edit link's href carries the entry's
    externalReferenceCode (`?editEntry=<uuid>`).
  - The entries list is PAGINATED client-side, 10 per page by default
    ("Showing 1–10 of 64", sorted oldest first, so a new QCTEST item lands on
    the LAST page). `[data-qc-oel-page-size]` offers 10/25/50/100/All("0").
    Every row lookup here first switches to All — otherwise the shared
    title-based helpers simply do not find a new item, and a teardown that
    cannot see its row silently leaves a live menu item behind.
  - The list's client-side search box (`[data-qc-oel-q]`) is deliberately NOT
    used: after filtering, the row's Delete and Edit links did nothing (no
    confirm(), no request) — reproduced twice on 2026-09-30. Without the
    filter the same Delete link fired its confirm() and a
    `POST /o/qc-object-status/trash/<id>` immediately.
  - Delete now reads: 'Delete "<label>"? It is moved to the Recycle Bin under
    this list, where it can be restored.' — a Recycle Bin, contradicting the
    Object Authoring guide's "no undo, no recycle bin". Reported, not acted on.
    A trashed row is gone from the page DOM (re-checked live) and the count
    drops, so exact-label lookups never see it.
  - Page size "All" (`value="0"`) renders every row ("Showing 1–64 of 64").
  - Deleting as the Site Content Editor is UNVERIFIED (extraction ran as
    TEST_USER); the teardown fixture fails loudly if a row survives.
  - Validation, observed on a create-form submit (nothing was saved):
      * empty AR label -> native HTML5 `required`: "Please fill out this
        field." (browser validationMessage; no app message).
      * URL "not a url" -> app field error, `[role=alert]` inside the field's
        form-group: "Nav Item URL is not a valid URL — start it with https://
        for another site, or with / for a page on this one."
      * Display Order "-1" passes native validation (min is -2^31); whether the
        server refuses it was not observed (the URL error fired first).
      * Typing letters into the number input is impossible (`fill("abc")`
        raises "Cannot type text into input[type=number]"); keyboard typing is
        dropped by the browser and leaves the field empty.
  - The AR label box computes `direction: ltr` and carries no `dir` attribute.
  - A reopened Draft (`?editEntry=<code>`) shows the banner "Editing <label>
    (Draft). Save as Draft or Submit for Publishing updates this record.
    Cancel and add a new entry instead".

Confirmed live on `manage-header-configuration` (read-only, never saved):
  - One row, `QCDEMO-129363-HEADER-CONFIG-DEFAULT`, PUBLISHED, entry id 44788.
  - Fields: Workflow Status (combobox, required), Logo Image (attachment,
    help text "Upload a .png,.svg no larger than 2 MB."), Logo Alt Text (EN) /
    (AR) (150 max), Logo Redirect URL (500 max), Active Status. On the
    published entry "Save as Draft" is disabled.
  - Its preview frame is `?qcPreview=headerconfigurations%3A44788` — keyed to
    the STORED record id.

Public header (anonymous, /home): every nav link — top-level and dropdown
child alike — is `header.qc-global-site-header nav.qc-nav a.qc-nav-link` whose
href is the NavItem URL; top level is `nav.qc-nav > ul.qc-nav-list > li`.
Children render inside the parent's `li.qc-has-children` (hidden until hover),
so presence is read from the DOM by href, never by hovering.

ENVIRONMENT NOTES:
  - (2026-09-30) `.env` role credentials were retired; fixed by 2026-10-01
    (coordinator: every role signs in).
  - Public render latency for NavItem changes was NOT measured (the probe's
    publish step was lost to the search-filter wiring defect above).
    cms-profile.md's 5s budget was measured for Board Members only, so the
    public polls here use a disclosed 60s upper bound with a fresh reload
    every 3s — a bound, never a sleep.
"""

import re
import time

from config.settings import web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.license_gate import clear_license_gate
from core.web.overlays import dismiss_overlays
from cms.pages.components.object_authoring_page import (
    STATUS_PUBLISHED,
    ObjectAuthoringPage,
    normalize_status,
)
from web.pages.components.header_component import HeaderComponent

logger = get_logger("header_admin_component")

QCTEST_PREFIX = "QCTEST-"

# Public-render poll bound for NavItem changes — UNMEASURED for this object
# (see module docstring). An upper bound on a condition poll, not a sleep.
PUBLIC_RENDER_TIMEOUT_S = 60.0
PUBLIC_RENDER_POLL_S = 3.0
# How long a clicked Save/Submit may take to actually SEND the form. The form
# page loads invisible reCAPTCHA and qc-form-guard.js, either of which can
# hold the submission back; no send inside this bound = the form refused it.
SUBMIT_SEND_TIMEOUT_MS = 20000
# Form action every NavItem Save as Draft / Submit posts to (probe 2 read).
FORM_ACTION_FRAGMENT = "/c/portal/edit_info_item"


class ReadOnlyViolation(AssertionError):
    """Raised when code tries to mutate the live HeaderConfiguration entry."""


# Write requests a Save as Draft / Submit can produce (probe 2026-10-01):
#   create form   -> POST /o/c/navitems/scopes/<id>/validate (fetch, a CHECK,
#                    not a write), POST document /c/portal/edit_info_item,
#                    then PUT /o/c/navitems/<id> (fetch)
#   ?editEntry=   -> ONLY PUT /o/c/<objects>/<id> (fetch), then a navigation
#                    to ?previewEntry=<code>. NO edit_info_item POST at all —
#                    which is why the v1 tracker reported "the form was not
#                    sent" for 134303/134308 although the server had saved
#                    ("Saved and submitted for publishing." in the evidence).
def _is_form_write(request) -> bool:
    if request.method not in ("POST", "PUT", "PATCH"):
        return False
    url = request.url
    if url.split("?")[0].rstrip("/").endswith("/validate"):
        return False
    return FORM_ACTION_FRAGMENT in url or "/o/c/" in url


# Success notices the form page shows after a write. "Saved and submitted for
# publishing." is confirmed in the 2026-10-01 evidence; the other two are the
# guide's / standards' wording for the Draft and Author paths.
SUCCESS_NOTICE_RE = re.compile(
    r"Draft saved\.|Saved and submitted for (?:publishing|review)\.", re.I
)


class _TrackedFormMixin:
    """Save/Submit with a POSITIVE send signal, select-from-list pickers, the
    editing banner's raw status, and form feedback — shared by both header
    objects."""

    SAVE_AS_DRAFT_BUTTON = 'form button[type="submit"][name="status"]:has-text("Save as Draft")'
    # Label-agnostic status-submit button (see module docstring).
    SUBMIT_BUTTON = 'form button[type="submit"][name="status"]:not(:has-text("Save as Draft"))'
    LIST_LOADING = "[data-qc-oel-status]"
    FORM_ERROR_ALERTS = 'form [role="alert"], .qc-oel [role="alert"], .alert-danger'

    def _combobox(self, label: str):
        return self.page.get_by_role("combobox", name=self.label_pattern(label))

    def _pick_from_list(self, label: str, option_text: str, type_to_search: bool):
        combo = self._combobox(label)
        listbox_id = combo.get_attribute("aria-controls")
        combo.click()
        if type_to_search:
            combo.fill(option_text)
        option = self.page.locator(f'[id="{listbox_id}"] [role="option"]').filter(
            has_text=re.compile(r"^\s*" + re.escape(option_text) + r"\s*$")
        )
        option.first.wait_for(state="visible", timeout=15000)
        option.first.click()
        return self

    def save_draft(self) -> bool:
        """Click Save as Draft; True if the form was actually sent."""
        return self._press_and_track(self.SAVE_AS_DRAFT_BUTTON)

    def submit(self) -> bool:
        """Click the status-submit button, whatever the account sees it
        labelled. True if the form was actually sent, False if it refused to
        send (native or client-side validation). The landing state depends on
        the account (Editor -> Published, Author -> Pending Review)."""
        return self._press_and_track(self.SUBMIT_BUTTON)

    def _press_and_track(self, selector: str) -> bool:
        """Positive-signal submit (HEALED 2026-10-01, see `_is_form_write`):
          1. wait for a WRITE request (document POST to the form action, or a
             PUT/PATCH/POST to the headless `/o/c/` API, never `/validate`);
             none within SUBMIT_SEND_TIMEOUT_MS -> the form refused -> False,
             page left as-is so `validation_feedback()` can read it;
          2. wait for its response, then for the NEXT document (a marker set
             on the old window must be gone) and its entries list to load."""
        self.wait_for(selector, timeout=10000)
        self.page.evaluate("() => { window.__qcHeaderSubmitMarker = true; }")
        try:
            with self.page.expect_request(_is_form_write, timeout=SUBMIT_SEND_TIMEOUT_MS) as sent:
                self.click(selector)
        except Exception as exc:  # noqa: BLE001 — only "nothing was sent" is expected here
            if type(exc).__name__ != "TimeoutError":
                raise
            logger.info("%s: form was not sent within %sms", selector, SUBMIT_SEND_TIMEOUT_MS)
            return False
        sent.value.response()
        try:
            self.page.wait_for_function("() => !window.__qcHeaderSubmitMarker", timeout=35000)
        except Exception:  # noqa: BLE001 — no document swap observed; fall back, disclosed
            logger.warning("%s: write sent but no new document loaded; using the generic settle", selector)
            self._wait_for_settle()
            return True
        self.wait_for(f"{self.LIST_LOADING}[hidden]", state="attached", timeout=35000)
        return True

    AUTHORING_CONTROLS = 'form button[type="submit"][name="status"]'

    def authoring_control_count(self) -> int:
        """Save as Draft / Submit controls rendered for the signed-in account."""
        return self.page.locator(self.AUTHORING_CONTROLS).count()

    def wait_for_banner_status(self, entry_code: str, *expected: str, timeout: float = 90.0):
        """Reopen `entry_code` until its banner state is one of `expected`
        (case-insensitive, raw — so "Inactive" is matchable). Raises
        WaitTimeoutError: a transition that did not commit fails loudly."""
        wanted = {e.casefold() for e in expected}

        def _reached() -> bool:
            self.open_entry_by_code(entry_code, locale="en")
            return self.banner_status_raw().casefold() in wanted

        wait_until(_reached, timeout=timeout, poll=3.0,
                   message=f"{entry_code} never reached banner status {sorted(expected)}")
        return self

    def success_notice(self) -> str:
        """The post-write success notice on the current page, or ""."""
        match = SUCCESS_NOTICE_RE.search(self.page.locator("body").inner_text())
        return match.group(0) if match else ""

    def banner_status_raw(self) -> str:
        """The state word in the editing banner, verbatim — "Editing <title>
        (<State>)." Unlike `current_status()`, keeps states the shared
        vocabulary does not know: a Published record with Active Status off
        reads "(Inactive)" (confirmed live 2026-10-01). "" when no banner."""
        match = re.search(r"Editing .+? \(([^()]+)\)\.", self.page.locator("body").inner_text())
        return match.group(1).strip() if match else ""

    def validation_feedback(self) -> str:
        """Everything the form is telling the user about why it will not save:
        native `validationMessage` of invalid ObjectField inputs/textareas,
        non-empty inline field alerts, any red bar. Joined with " | "."""
        native = self.page.evaluate(
            """() => [...document.querySelectorAll('form [name^="ObjectField_"]:not([type=hidden])')]
                .filter(e => e.willValidate && !e.checkValidity())
                .map(e => e.validationMessage)"""
        )
        alerts = []
        loc = self.page.locator(self.FORM_ERROR_ALERTS)
        for i in range(loc.count()):
            try:
                text = loc.nth(i).inner_text().strip()
            except Exception:  # noqa: BLE001 — node may be re-rendering
                continue
            if text and "activation key" not in text:  # site-wide licence banner
                alerts.append(text)
        return " | ".join([m for m in native if m] + alerts)


class HeaderConfigurationAdminPage(_TrackedFormMixin, ObjectAuthoringPage):
    """`manage-header-configuration` — the ONE live entry.

    Writes are approved ONLY under the user's ID-named approval of 2026-10-01
    (engineer brief v2: logo, alt text EN/AR, logo redirect URL, save as draft,
    submit for review, update, unpublish), and ONLY through tests holding the
    snapshot -> restore -> verify fixture. Delete and the other row
    transitions stay refused.

    Live read 2026-10-01 (Editor, read-only): banner "Editing
    QCDEMO-129363-HEADER-CONFIG-DEFAULT (Published). It is published. Use
    Unpublish to edit as draft below…"; Save as Draft DISABLED, Submit for
    Publishing enabled; Workflow Status = "Published" (options Draft /
    Submitted for Review / Published / Unpublished); alt EN "Qatar Chamber",
    alt AR "غرفة قطر", redirect "/web/qatar-chamber/home", Active ticked, logo
    "qc-logo (2) (9).png"; Editor row actions: unpublish, delete. Restore
    mechanics (approve / publish row actions, re-pointing the logo at the D&M
    file) are NOT yet exercised live."""

    SLUG = "header-configuration"
    LIVE_ENTRY_CODE = "QCDEMO-129363-HEADER-CONFIG-DEFAULT"
    LIVE_ENTRY_ID = "44788"

    FIELD_LOGO_IMAGE = "Logo Image"
    FIELD_LOGO_ALT_TEXT_EN = "Logo Alt Text (EN)"
    FIELD_LOGO_ALT_TEXT_AR = "Logo Alt Text (AR)"
    FIELD_LOGO_REDIRECT_URL = "Logo Redirect URL"
    FIELD_ACTIVE_STATUS = "Active Status"
    FIELD_WORKFLOW_STATUS = "Workflow Status"

    ACCESS_DENIED_TEXT = "Access Denied. You do not have permission to perform this action."
    PAGE_SETTLED_ANCHOR = "header.qc-global-site-header"
    PREVIEW_LOGO_IMG = "header.qc-global-site-header a.qc-logo img"
    ROW = 'table.qc-oel__table tbody tr:has-text("QCDEMO-129363-HEADER-CONFIG-DEFAULT")'
    _CURRENT_FILE_RE = re.compile(r"^Current file:\s*(.+?)\s+—\s+pick a file", re.S)

    # Fields a snapshot holds; restore writes back exactly these.
    SNAPSHOT_KEYS = ("alt_en", "alt_ar", "redirect_url", "active", "workflow_field", "logo")

    def __init__(self, page):
        super().__init__(page, self.SLUG)

    # ---- Navigation ------------------------------------------------------------
    def open_manage_page_for_any_role(self) -> "HeaderConfigurationAdminPage":
        """Navigate to the manage URL WITHOUT waiting for the admin table —
        used by the access-denial case, where the table must not appear.
        Bypasses BasePage.open()'s reauthenticate() hook on purpose: if the
        denied response were a login form, that hook would sign the page in
        as TEST_USER and turn the no-role check into a super-admin one."""
        url = self._manage_url(locale="en")
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page)
        self.wait_for(self.PAGE_SETTLED_ANCHOR, state="attached", timeout=35000)
        return self

    def open_live_entry(self) -> "HeaderConfigurationAdminPage":
        self.open_entry_by_code(self.LIVE_ENTRY_CODE, locale="en")
        self.wait_for(f"{self.LIST_LOADING}[hidden]", state="attached", timeout=35000)
        return self

    def open_list(self) -> "HeaderConfigurationAdminPage":
        """Entries list (one row). No page-size switch: with a single entry
        the pager control is not interactable (select_option timed out live)."""
        self.open(self._manage_url(locale="en"))
        self.wait_for(f"{self.LIST_LOADING}[hidden]", state="attached", timeout=35000)
        return self

    # ---- State queries -----------------------------------------------------------
    def access_denied_shown(self) -> bool:
        return self.ACCESS_DENIED_TEXT in self.page.locator("body").inner_text()

    def entries_table_rendered(self) -> bool:
        return self.page.locator("a[data-qc-oel-delete]").count() > 0

    def _textbox(self, label: str):
        return self.page.get_by_role("textbox", name=self.label_pattern(label))

    def alt_en(self) -> str:
        return self._textbox(self.FIELD_LOGO_ALT_TEXT_EN).input_value()

    def alt_ar(self) -> str:
        return self._textbox(self.FIELD_LOGO_ALT_TEXT_AR).input_value()

    def redirect_url(self) -> str:
        return self._textbox(self.FIELD_LOGO_REDIRECT_URL).input_value()

    def alt_ar_direction(self) -> str:
        return self._textbox(self.FIELD_LOGO_ALT_TEXT_AR).evaluate("e => getComputedStyle(e).direction")

    def active(self) -> bool:
        return self.page.get_by_role("checkbox", name=self.label_pattern(self.FIELD_ACTIVE_STATUS)).is_checked()

    def workflow_field(self) -> str:
        return self._combobox(self.FIELD_WORKFLOW_STATUS).input_value()

    def logo_file_name(self) -> str:
        """Stored logo file name, from the hidden picker textbox's placeholder
        ("Current file: <name> — pick a file to replace it", confirmed live)."""
        placeholder = self.current_file_placeholder(self.FIELD_LOGO_IMAGE)
        match = self._CURRENT_FILE_RE.match(placeholder or "")
        return match.group(1).strip() if match else ""

    def row_status_raw(self) -> str:
        self.open_list()
        row = self.page.locator(self.ROW)
        return row.locator("td").nth(1).inner_text().strip() if row.count() else ""

    def preview_url(self) -> str:
        self.open_list()
        return self.row_preview_url_by_code(self.LIVE_ENTRY_CODE)

    def snapshot(self) -> dict:
        """Every restorable field, the workflow state and Active Status, read
        from a freshly reopened edit form (brief v2 rule 1)."""
        self.open_live_entry()
        snap = {
            "alt_en": self.alt_en(),
            "alt_ar": self.alt_ar(),
            "redirect_url": self.redirect_url(),
            "active": self.active(),
            "workflow_field": self.workflow_field(),
            "logo": self.logo_file_name(),
            "banner_status": self.banner_status_raw(),
        }
        snap["row_status"] = normalize_status(self.row_status_raw())
        return snap

    def diff_from(self, snap: dict) -> dict:
        """{key: (expected, actual)} for every snapshot field that differs now,
        plus the workflow state, which must be Published. {} = identical."""
        now = self.snapshot()
        diff = {k: (snap[k], now[k]) for k in self.SNAPSHOT_KEYS if snap[k] != now[k]}
        if now["row_status"] != STATUS_PUBLISHED:
            diff["row_status"] = (STATUS_PUBLISHED, now["row_status"])
        return diff

    # ---- Approved writes (fixture-guarded) -------------------------------------
    def set_alt_en(self, value: str):
        self._textbox(self.FIELD_LOGO_ALT_TEXT_EN).fill(value)
        return self

    def set_alt_ar(self, value: str):
        self._textbox(self.FIELD_LOGO_ALT_TEXT_AR).fill(value)
        return self

    def set_redirect_url(self, value: str):
        self._textbox(self.FIELD_LOGO_REDIRECT_URL).fill(value)
        return self

    def set_active(self, value: bool):
        box = self.page.get_by_role("checkbox", name=self.label_pattern(self.FIELD_ACTIVE_STATUS))
        if value:
            box.check()
        else:
            box.uncheck()
        return self

    def select_workflow_field(self, label: str):
        return self._pick_from_list(self.FIELD_WORKFLOW_STATUS, label, type_to_search=False)

    def selected_logo_name(self) -> str:
        """Newly picked (not yet saved) file name readout."""
        return self.uploaded_filename(self.FIELD_LOGO_IMAGE)

    # ---- Logo picker (Liferay item selector) -----------------------------------
    # Live read 2026-10-03 (Editor, read-only, nothing selected or saved): the
    # picker root shows folders (Flickr, qatar-chamber-website, …) then 20
    # documents per page, 51 pages — so a name is found with the picker's own
    # "Search for" box (input[name$="_keywords"]), never by browsing the root.
    # Results render each document's TITLE, which drops the extension
    # ("qc-logo (2) (8)", not "qc-logo (2) (8).png"). The picker URL carries
    # extensions [".png", ".svg"] and maxFileSize "2".
    PICKER_KEYWORDS = 'input[name$="_keywords"]'
    PICKER_CARD_TITLE = ".card-title"
    PICKER_FILE_INPUT = 'input[type="file"]'
    PICKER_ADD_BUTTON = "button.btn-primary:not(.dropdown-toggle):visible"
    PICKER_ERROR = '.alert-danger, .text-danger, [role="alert"], .form-feedback-item, .lfr-alert-wrapper'
    PICKER_BUDGET_MS = 60000
    PICKER_MAX_RESULT_PAGES = 5

    @staticmethod
    def unique_upload_name(prefix: str, ext: str) -> str:
        """Fresh Documents & Media file name per upload. Since 2026-10-03 D&M
        rejects a repeated upload name with "An unexpected error occurred while
        uploading your file." while a new name uploads fine (same fix as
        image_alt_text_admin_component.py)."""
        return f"{prefix}-{time.strftime('%Y%m%d%H%M%S')}-{time.time_ns() % 100000}{ext}"

    def _open_logo_picker(self):
        """Click the Logo Image field's own Select File button (retried: the
        click can land before the form's upload script is wired) and wait for
        the picker's file input — the readiness signal, the iframe itself
        reports visible late."""
        hidden = self.page.get_by_role("textbox", name=f"{self.FIELD_LOGO_IMAGE} Select File")
        button = hidden.locator("xpath=..").get_by_role("button", name="Select File")
        iframe = self.page.locator(self.UPLOAD_MODAL_IFRAME).first
        for attempt in range(3):
            button.click()
            try:
                iframe.wait_for(state="attached", timeout=20000)
                break
            except Exception:  # noqa: BLE001 — retry; the last attempt re-raises
                if attempt == 2:
                    raise
                dismiss_overlays(self.page)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME).first
        frame.locator(self.PICKER_FILE_INPUT).wait_for(state="attached", timeout=self.PICKER_BUDGET_MS)
        return frame

    def _close_logo_picker(self) -> None:
        close = self.page.locator(
            '.modal-dialog button.close, .modal-dialog [aria-label="close"], .modal-dialog [aria-label="Close"]'
        )
        if close.count():
            close.first.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=10000)

    def _find_in_picker(self, frame, file_name: str):
        """Search the picker for `file_name` and return the matching result's
        title locator (title == name or name without extension), scanning up
        to PICKER_MAX_RESULT_PAGES result pages. None when absent."""
        stem = file_name.rsplit(".", 1)[0] if "." in file_name else file_name
        box = frame.locator(self.PICKER_KEYWORDS).first
        box.fill(stem)
        box.press("Enter")
        # The search reloads the iframe; the reloaded box carries the keywords.
        frame.locator(f'{self.PICKER_KEYWORDS}[value="{stem}"]').first.wait_for(
            state="attached", timeout=self.PICKER_BUDGET_MS)
        wanted = re.compile(r"^\s*(" + re.escape(stem) + "|" + re.escape(file_name) + r")\s*$")
        for page_no in range(1, self.PICKER_MAX_RESULT_PAGES + 1):
            if page_no > 1:
                link = frame.locator(f'a[aria-label="Page {page_no}"]')
                if link.count() == 0:
                    break
                link.first.click()
                frame.locator(f'a[aria-label="Page {page_no}"][aria-current], '
                              f'li.active a[aria-label="Page {page_no}"]').first.wait_for(
                    state="attached", timeout=self.PICKER_BUDGET_MS)
            hit = frame.locator(self.PICKER_CARD_TITLE).filter(has_text=wanted)
            if hit.count():
                return hit.first
        return None

    def library_has_logo(self, file_name: str) -> bool:
        """READ-ONLY: open the logo picker, search for `file_name`, report
        whether it is selectable, close WITHOUT selecting. Run before any logo
        write so the restore path is proven first.

        Live 2026-10-03: searching "qc-logo" lists "qc-logo", "qc-logo (1)",
        "qc-logo (2)" … "qc-logo (2) (8)" and "qc-logo.png" — but NOT the
        stored "qc-logo (2) (9)". The live logo's file is not in the site
        library the picker browses, so this returns False and 134270 stops
        before writing."""
        frame = self._open_logo_picker()
        try:
            found = self._find_in_picker(frame, file_name) is not None
        finally:
            self._close_logo_picker()
        return found

    def select_logo_from_library(self, file_name: str):
        """Re-point the logo at an EXISTING Documents & Media file found by
        name. Raises if it is not found or the picker does not close."""
        frame = self._open_logo_picker()
        hit = self._find_in_picker(frame, file_name)
        if hit is None:
            self._close_logo_picker()
            raise AssertionError(f"logo {file_name!r} not found in the picker")
        hit.click()
        if not self._picker_closed(4000):
            try:
                hit.dblclick()
            except Exception:  # noqa: BLE001 — the closed-check below is the gate
                pass
        if not self._picker_closed(8000):
            raise AssertionError(f"picker stayed open after selecting {file_name!r}")
        return self

    def upload_logo_named(self, file_path: str, upload_name: str, mime_type: str):
        """Upload the fixture's bytes under `upload_name` (in-memory payload)
        and commit it with the picker's Add button."""
        frame = self._open_logo_picker()
        with open(file_path, "rb") as handle:
            payload = handle.read()
        frame.locator(self.PICKER_FILE_INPUT).set_input_files(
            {"name": upload_name, "mimeType": mime_type, "buffer": payload})
        add = frame.locator(self.PICKER_ADD_BUTTON)
        add.first.wait_for(state="visible", timeout=self.PICKER_BUDGET_MS)
        wait_until(lambda: add.first.is_enabled(), timeout=30.0, poll=0.3,
                   message="picker Add button never became enabled after the upload")
        add.first.click()
        self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=30000)
        return self

    def upload_logo_expect_rejected(self, file_path: str, upload_name: str, mime_type: str) -> dict:
        """Offer a file the field should refuse, WITHOUT ever clicking Add.
        Returns {"rejected": bool, "message": str}: rejected when the picker
        shows an error, False when it enables Add (accepted). The picker is
        closed either way, so nothing is committed to the record."""
        frame = self._open_logo_picker()
        with open(file_path, "rb") as handle:
            payload = handle.read()
        frame.locator(self.PICKER_FILE_INPUT).set_input_files(
            {"name": upload_name, "mimeType": mime_type, "buffer": payload})
        error = frame.locator(self.PICKER_ERROR).filter(has_text=re.compile(r"\S"))
        add = frame.locator(self.PICKER_ADD_BUTTON)
        outcome: dict = {}

        def _settled() -> bool:
            if error.count():
                outcome.update(rejected=True, message=error.first.inner_text().strip())
                return True
            if add.count() and add.first.is_enabled():
                outcome.update(rejected=False, message="")
                return True
            return False

        try:
            wait_until(_settled, timeout=30.0, poll=0.5, message="picker gave no verdict on the file")
        except WaitTimeoutError:
            outcome.update(rejected=False, message="no verdict within 30s")
        finally:
            self._close_logo_picker()
        return outcome

    def offers_row_action(self, action: str) -> bool:
        self.open_list()
        attr = self.ROW_ACTION_ATTRS[action]
        return self.page.locator(f"{self.ROW} [{attr}]").count() > 0

    def unpublish(self):
        """Row action Unpublish (confirm accepted) -> Unpublished."""
        self.open_list()
        self.unpublish_entry(self.LIVE_ENTRY_CODE)
        return self

    def publish(self):
        """Row action Publish (Unpublished -> Published). Unverified live
        (standards: "publish from Unpublished" not yet walked)."""
        self.open_list()
        self.publish_entry(self.LIVE_ENTRY_CODE)
        return self

    def approve(self):
        """Row action Approve (Pending Review -> Published), Editor only."""
        self.open_list()
        self.approve_entry(self.LIVE_ENTRY_CODE)
        return self

    def restore(self, snap: dict) -> dict:
        """Write `snap` back and bring the entry to Published (caller must be
        signed in as Site Content Editor), then re-read. Returns the remaining
        diff — {} means restored AND verified. Writes nothing when the entry
        already matches. Never raises; an exception comes back as a diff."""
        try:
            if not self.diff_from(snap):
                return {}
            if self.row_status_raw().casefold() == "pending review" and self.offers_row_action("approve"):
                self.approve()
            self.open_live_entry()
            self.set_alt_en(snap["alt_en"]).set_alt_ar(snap["alt_ar"]).set_redirect_url(snap["redirect_url"])
            self.set_active(snap["active"])
            if snap["workflow_field"] and self.workflow_field() != snap["workflow_field"]:
                self.select_workflow_field(snap["workflow_field"])
            if snap["logo"] and self.logo_file_name() != snap["logo"]:
                self.select_logo_from_library(snap["logo"])
            self.submit()
            if normalize_status(self.row_status_raw()) != STATUS_PUBLISHED and self.offers_row_action("publish"):
                self.publish()
            return self.diff_from(snap)
        except Exception as exc:  # noqa: BLE001 — surfaced to the fixture as a failed restore
            logger.error("restore of %s raised: %r", self.LIVE_ENTRY_CODE, exc)
            return {"exception": repr(exc)[:300]}

    def preview_shows_logo_alt(self, alt_text: str) -> bool:
        """On the record's preview page, is the header logo rendered with
        `alt_text`?"""
        return self.page.locator(f'{self.PREVIEW_LOGO_IMG}[alt="{alt_text}"]').count() > 0

    # Destructive / out-of-approval actions stay refused.
    def _refuse(self, *_args, **_kwargs):
        raise ReadOnlyViolation(
            f"{self.LIVE_ENTRY_CODE} is the real live header: delete, archive, "
            "restore-from-archive, return-to-author and file removal are not "
            "covered by the 2026-10-01 approval."
        )

    delete_entry_by_title = _refuse
    delete_entry_by_code = _refuse
    delete_all_entries_by_title = _refuse
    archive_entry = _refuse
    restore_entry = _refuse
    return_to_author = _refuse
    remove_current_file = _refuse
    field_length_rejected = _refuse


class NavItemAdminPage(_TrackedFormMixin, ObjectAuthoringPage):
    """`manage-nav-item` — disposable `QCTEST-*` navigation items only."""

    SLUG = "nav-item"

    FIELD_LABEL_EN = "Nav Item Label EN"
    FIELD_LABEL_AR = "Nav Item Label AR"
    FIELD_URL = "Nav Item URL"
    FIELD_DISPLAY_ORDER = "Display Order"
    FIELD_ACTIVE_STATUS = "Active Status"
    FIELD_LEVEL = "Nav Item Level"
    FIELD_PARENT_ITEM = "Parent Item"
    FIELD_PARENT_MENU = "Parent Menu"

    # Object field names (`ObjectField_<name>`) — used to scope a field's own
    # form-group for its inline error and native validity.
    NAME_LABEL_EN = "navItemLabelEn"
    NAME_LABEL_AR = "navItemLabelAr"
    NAME_URL = "navItemUrl"
    NAME_DISPLAY_ORDER = "displayOrder"
    NAME_LEVEL = "navItemLevel"
    NAME_PARENT_ITEM = "r_navItemParent_c_navItemId"

    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    PAGE_SIZE_ALL = "0"
    PAGER_COUNT = "[data-qc-oel-pager-count]"
    # The live entries table only (trashed rows were confirmed absent from
    # the page DOM, but scoping keeps any future trash/preview table out).
    ENTRY_ROW = "table.qc-oel__table tbody tr"

    def __init__(self, page):
        super().__init__(page, self.SLUG)

    # ---- Navigation --------------------------------------------------------
    def open_create_form(self) -> "NavItemAdminPage":
        self.open_new_entry_form(locale="en")
        return self

    def open_full_list(self) -> "NavItemAdminPage":
        """Entries list with every row rendered (page size = All, confirmed
        live to render all 64 rows). Role-independent readiness: the list's
        own loading indicator goes hidden and its pager count renders — never
        a row-action link, whose presence depends on the signed-in role."""
        self.open(self._manage_url(locale="en"))
        self._locale = "en"
        self.wait_for(f"{self.LIST_LOADING}[hidden]", state="attached", timeout=35000)
        self.wait_for(self.PAGE_SIZE_SELECT, state="attached", timeout=10000)
        self.page.locator(self.PAGE_SIZE_SELECT).select_option(self.PAGE_SIZE_ALL)
        self.wait_for(self.PAGER_COUNT, state="attached", timeout=10000)
        return self

    def open_by_code(self, entry_code: str) -> "NavItemAdminPage":
        self.open_entry_by_code(entry_code, locale="en")
        return self

    # ---- Form actions --------------------------------------------------------
    def _textbox(self, label: str):
        return self.page.get_by_role("textbox", name=self.label_pattern(label))

    def _display_order(self):
        return self.page.get_by_role("spinbutton", name=self.label_pattern(self.FIELD_DISPLAY_ORDER))

    def _active(self):
        return self.page.get_by_role("checkbox", name=self.label_pattern(self.FIELD_ACTIVE_STATUS))

    def fill_nav_item(
        self,
        label_en: str,
        label_ar: str,
        url: str,
        display_order: str | None,
        active: bool,
    ) -> "NavItemAdminPage":
        if not label_en.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to author a non-disposable nav item {label_en!r}")
        self._textbox(self.FIELD_LABEL_EN).fill(label_en)
        self._textbox(self.FIELD_LABEL_AR).fill(label_ar)
        self._textbox(self.FIELD_URL).fill(url)
        if display_order is not None:
            self._display_order().fill(display_order)
        if active:
            self._active().check()
        else:
            self._active().uncheck()
        return self

    def set_active(self, active: bool) -> "NavItemAdminPage":
        if active:
            self._active().check()
        else:
            self._active().uncheck()
        return self

    def type_display_order_keys(self, text: str) -> "NavItemAdminPage":
        """Types key-by-key into the number input, the way a user would.
        Needed for non-numeric input: `fill()` refuses letters on
        type=number outright (confirmed live)."""
        field = self._display_order()
        field.fill("")
        field.press_sequentially(text)
        return self

    def select_level(self, level: str) -> "NavItemAdminPage":
        """`Nav Item Level` select-from-list (options "1"/"2"/"3", confirmed
        live). Scoped to the field's own listbox via aria-controls, since the
        form has two identical "Open Options Menu" buttons."""
        return self._pick_from_list(self.FIELD_LEVEL, level, type_to_search=False)

    def select_parent_item(self, parent_label: str) -> "NavItemAdminPage":
        """`Parent Item` relationship picker. Options load asynchronously
        ("Loading" -> list) after typing, so the parent's own label is typed to
        filter, then the exact option is clicked. The option-list mechanics were
        read live but NOT clicked through during extraction — first real run
        is the confirmation."""
        if not parent_label.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to parent a test item under real item {parent_label!r}")
        return self._pick_from_list(self.FIELD_PARENT_ITEM, parent_label, type_to_search=True)

    def set_parent_menu(self, text: str) -> "NavItemAdminPage":
        """Free-text `Parent Menu` field (present on the live form, absent
        from the guide)."""
        self._textbox(self.FIELD_PARENT_MENU).fill(text)
        return self

    # ---- Read-backs ----------------------------------------------------------
    def label_en_value(self) -> str:
        return self._textbox(self.FIELD_LABEL_EN).input_value()

    def label_ar_value(self) -> str:
        return self._textbox(self.FIELD_LABEL_AR).input_value()

    def url_value(self) -> str:
        return self._textbox(self.FIELD_URL).input_value()

    def display_order_value(self) -> str:
        return self._display_order().input_value()

    def active_checked(self) -> bool:
        return self._active().is_checked()

    def label_ar_direction(self) -> str:
        """Computed CSS `direction` of the AR label box ("rtl"/"ltr")."""
        return self._textbox(self.FIELD_LABEL_AR).evaluate("e => getComputedStyle(e).direction")

    # ---- List lookups (exact label, never position, never substring) ------
    def entries_with_label(self, label: str) -> list[dict]:
        """Every row whose Entry cell equals `label` EXACTLY, as
        {"entry_id", "entry_code", "status"}. Exact equality (not the shared
        helpers' `:has-text`) because a child label can contain its parent's."""
        self.open_full_list()
        rows = self.page.evaluate(
            """([sel, label]) => [...document.querySelectorAll(sel)]
                .filter(tr => tr.querySelector('td') && tr.querySelector('td').innerText.trim() === label)
                .map(tr => {
                    const del = tr.querySelector('a[data-qc-oel-delete]');
                    const edit = [...tr.querySelectorAll('a')].find(a => /editEntry=/.test(a.getAttribute('href') || ''));
                    const code = edit ? new URL(edit.getAttribute('href'), location.origin).searchParams.get('editEntry') : '';
                    return {entry_id: del ? del.getAttribute('data-qc-oel-delete') : '',
                            entry_code: code || '',
                            status: tr.querySelectorAll('td')[1] ? tr.querySelectorAll('td')[1].innerText : ''};
                })""",
            [self.ENTRY_ROW, label],
        )
        for row in rows:
            row["status"] = normalize_status(row["status"])
        return rows

    def wait_for_single_entry(self, label: str, timeout: float = 45.0) -> dict:
        """Poll the fully expanded list until exactly one row carries `label`
        and return it. Raises WaitTimeoutError otherwise (0 = the save never
        landed; 2+ = a duplicate)."""
        found: dict = {}

        def _one() -> bool:
            rows = self.entries_with_label(label)
            if len(rows) == 1:
                found.update(rows[0])
                return True
            return False

        wait_until(_one, timeout=timeout, poll=3.0,
                   message=f"expected exactly one nav item {label!r}")
        return found

    def display_order_of(self, label: str) -> int:
        """READ-ONLY: Display Order of the one item whose Entry equals `label`
        (opens its edit form, never saves)."""
        rows = self.entries_with_label(label)
        if len(rows) != 1:
            raise AssertionError(f"expected exactly one nav item {label!r}, found {len(rows)}")
        self.open_by_code(rows[0]["entry_code"])
        return int(self.display_order_value())

    # ---- Teardown (QCTEST-only, by id, verified) -----------------------------
    def delete_by_id(self, entry_id: str, expected_label: str) -> bool:
        """Delete ONE row by its entry id, after confirming the row's own
        `data-qc-oel-label` equals `expected_label` and is disposable. Accepts
        the confirm() it raises. Returns True once the row's delete link has
        detached. Never raises (teardown contract)."""
        try:
            if not expected_label.startswith(QCTEST_PREFIX):
                raise ValueError(f"refusing to delete non-disposable {expected_label!r}")
            self.open_full_list()
            link = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
            if link.count() != 1 or link.get_attribute("data-qc-oel-label") != expected_label:
                logger.warning("delete_by_id(%s): row label does not match %r — not deleting", entry_id, expected_label)
                return False
            self.page.once("dialog", lambda d: d.accept())
            link.click()
            link.wait_for(state="detached", timeout=15000)
            return True
        except Exception:  # noqa: BLE001 — best-effort teardown, never raises
            logger.warning("delete_by_id(%s, %r) failed — QCTEST leftover may remain", entry_id, expected_label)
            return False

    def teardown_label(self, label: str) -> list[str]:
        """Delete every row carrying exactly `label` (QCTEST- only), then
        re-read the list and return the entry ids that SURVIVED (empty list =
        clean). Callers should fail loudly on survivors: a published+active
        leftover sits in the real public menu."""
        if not label.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to tear down non-disposable {label!r}")
        try:
            for row in self.entries_with_label(label):
                if row["entry_id"]:
                    self.delete_by_id(row["entry_id"], label)
            return [r["entry_id"] for r in self.entries_with_label(label)]
        except Exception:  # noqa: BLE001 — report as "unknown survivors"
            logger.warning("teardown_label(%r) could not re-read the list", label)
            return ["<unverified>"]


class PublicHeaderNavProbe(HeaderComponent):
    """Anonymous public-header reads for one disposable nav item, by href.
    Construct on a page from `new_context(browser, use_auth_state=False)`."""

    NAV_LINKS = "header.qc-global-site-header nav.qc-nav a.qc-nav-link"
    TOP_LEVEL_LI = "header.qc-global-site-header nav.qc-nav > ul.qc-nav-list > li"

    def open_home_anonymous(self) -> "PublicHeaderNavProbe":
        """Opens /home WITHOUT BasePage.open()'s reauthenticate() hook, which
        could otherwise sign an intentionally anonymous context back in."""
        url = web_url("/home")
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page)
        self.wait_for(self.NAV, state="attached", timeout=20000)
        self.wait_for(self.NAV_TOP_LEVEL_ITEMS, first=True, state="attached", timeout=20000)
        return self

    def is_signed_in(self) -> bool:
        return self.page.locator("body.signed-in").count() > 0

    def logo_src(self) -> str:
        return self.page.locator(self.LOGO_IMAGE).first.get_attribute("src") or ""

    def logo_alt(self) -> str:
        return self.page.locator(self.LOGO_IMAGE).first.get_attribute("alt") or ""

    def logo_href(self) -> str:
        return self.page.locator(self.LOGO).first.get_attribute("href") or ""

    def wait_until_ordered(self, first_frag: str, second_frag: str,
                           timeout: float = PUBLIC_RENDER_TIMEOUT_S) -> bool:
        """Reload /home until both top-level items render and `first_frag`'s
        slot is before `second_frag`'s."""
        def _reached() -> bool:
            self.open_home_anonymous()
            a, b = self.top_level_position_of(first_frag), self.top_level_position_of(second_frag)
            return 0 < a < b

        try:
            wait_until(_reached, timeout=timeout, poll=PUBLIC_RENDER_POLL_S,
                       message=f"public order {first_frag!r} before {second_frag!r}")
            return True
        except WaitTimeoutError:
            return False

    def wait_for_logo(self, predicate, timeout: float = PUBLIC_RENDER_TIMEOUT_S) -> bool:
        """Reload /home until `predicate(self)` holds for the public logo.
        Returns whether it did; the caller asserts."""
        def _reached() -> bool:
            self.open_home_anonymous()
            return bool(predicate(self))

        try:
            wait_until(_reached, timeout=timeout, poll=PUBLIC_RENDER_POLL_S,
                       message="public header logo condition")
            return True
        except WaitTimeoutError:
            return False

    def link_count_to(self, href_fragment: str) -> int:
        return self.page.locator(f'{self.NAV_LINKS}[href*="{href_fragment}"]').count()

    def top_level_labels(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.NAV_TOP_LEVEL_ITEMS).all_inner_texts()]

    def top_level_position_of(self, href_fragment: str) -> int:
        """1-based slot of the top-level item linking to `href_fragment`
        (0 when it is not a top-level item)."""
        return self.page.evaluate(
            """([sel, frag]) => {
                const lis = [...document.querySelectorAll(sel)];
                const i = lis.findIndex(li => {
                    const a = li.querySelector(':scope > a.qc-nav-link');
                    return a && (a.getAttribute('href') || '').includes(frag);
                });
                return i + 1;
            }""",
            [self.TOP_LEVEL_LI, href_fragment],
        )

    def wait_for_link(self, href_fragment: str, present: bool,
                      timeout: float = PUBLIC_RENDER_TIMEOUT_S) -> bool:
        """Reload /home until a nav link to `href_fragment` is present (or
        absent). Returns whether the condition was reached; the caller asserts."""
        def _reached() -> bool:
            self.open_home_anonymous()
            return (self.link_count_to(href_fragment) > 0) == present

        try:
            wait_until(_reached, timeout=timeout, poll=PUBLIC_RENDER_POLL_S,
                       message=f"public nav link {href_fragment!r} present={present}")
            return True
        except WaitTimeoutError:
            return False


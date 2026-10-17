"""
cms/pages/useful_links/useful_link_category_admin_page.py —
UsefulLinkCategoryAdminPage, the shared _UsefulLinksAuthoringBase, and the
UsefulLinksPublicView delivery-surface reader.

Control_Panel Page Objects for PBI 130702 ("QC - Business Gateway - 009 -
Useful Links"). The public page `/web/qatar-chamber/useful-links` is backed by
three Object Definitions, all listed on the live `object-authoring` index
(`object-authoring-index.md`): "Useful Link Category"
(`manage-useful-link-category`, this module), "Useful Link"
(`manage-useful-link`, see useful_link_admin_page.py) and "Useful Links Page"
(`manage-useful-links-page`, owned by a different batch — not touched here).
`cms/Content-Admin-Guide.docx` has no Useful Links section, so the object
names come from the live index, not from a guess.

CONFIRMED LIVE 2026-09-29 (throwaway Playwright probe scripts, TEST_USER,
1920x1080, run under the cross-agent qcdev browser mutex):

  Form — each control carries an exact accessible name:
    textbox   "Category Number"                    (required)
    textbox   "Category Eyebrow"                   (required, counter 0/100)
    textbox   "Category Eyebrow — العربية *"       (required)
    textbox   "Category Title"                     (required, counter 0/150)
    textbox   "Category Title — العربية *"         (required)
    spinbutton "Display Order"                     (required, type=number)
    checkbox  "Active Status"                      (UNCHECKED by default)
  Buttons: "Save as Draft" (name=status value=2) and "Publish" (name=status
  value=0). There is NO "Submit for Review" button on this object — the
  shared ObjectAuthoringPage.submit_for_review() matches nothing here, so
  publish() below targets the Publish button by its stable name/value pair.
  The form states "As an Editor, what you publish here goes live straight
  away."

  Validation — a refused Publish lists reasons in an alert bar and writes
  nothing. Messages observed verbatim:
    "Category Number cannot be only spaces."
    "Category Number must be a two-character zero-padded value from 01 to 09."
    "Category Eyebrow is 101 characters; the maximum is 100."
    "Display Order must be 100 or greater and follow the 100-grid
     (100, 200, 300, ...)."
  An empty required field is refused by native constraint validation
  ("Please fill out this field.") plus the page message "Please complete the
  required fields before proceeding with the workflow action for this new
  record. Nothing has been submitted."
  Display Order is an <input type=number>: typing "abc" leaves it empty.

  Success — Publish reloads the page onto `?previewEntry=<erc>`; the row shows
  PUBLISHED. The Entry column renders the Category Title (EN) verbatim, so
  title-based row lookup is safe for this object.

  Delete — row "Delete" raises ONE native confirm ("Delete "<title>"? It is
  moved to the Recycle Bin under this list, where it can be restored.") and
  POSTs /o/qc-object-status/trash/<id>. Deleting a category also removes its
  Link Items from the Useful Link list (observed: link count 47 -> 46).

  FINDING (candidate product defect, recorded not worked around silently):
  after typing into the entries list's own client-side "Search entries…"
  filter (`input[data-qc-oel-q]`), the filtered rows' Delete links stop
  responding — no confirm dialog, no request, reproduced 3x on
  QCTEST-ULCAT-PROBE-1790696132. Without the filter the same link works. Row
  lookup here therefore never uses that filter.

  Public page (anonymous context): every ACTIVE + PUBLISHED category renders
  as `.qc-ul-row` > `button.qc-ul-head` (aria-expanded) holding
  `.qc-ul-num` (the Category Number, verbatim — two categories with the same
  number both show it), `.qc-ul-head-eyebrow`, `.qc-ul-head-title`; its panel
  `.qc-ul-panel` holds `a.qc-ul-card` (href, target, `.qc-ul-org`,
  `.qc-ul-site`).

ROLE (updated 2026-09-30). Every authoring step runs as the role the case
names — "Site Content Editor" by default (`_UsefulLinksAuthoringBase.role`),
signed in with `cms_role_credentials()` in an auth-free context (the test
modules request `page` with {"auth": False}). `ensure_session()` re-logs in
as that role whenever the context is not signed in as its userId, and
`_submit()` re-reads `signed_in_user()` before AND after every Publish /
Save as Draft, raising if BasePage's session guard ever swapped in
TEST_USER — so no outcome is silently a super-admin one.

  BUG 1 (product defect, confirmed live 2026-09-30, read-only probe): on
  the Category create form rendered to the Site Content Editor (and the
  Author), the controls labelled "Display Order" / "Active Status" are
  `ObjectRelationship#C_UsefulLink#usefulLinkCategoryLinks_displayOrder`
  / `..._activeStatus`; there is NO `ObjectField_displayOrder` input at
  all, so Publish fails server-side ("No value was provided for required
  object field displayOrder"). The Link form binds correctly
  (`ObjectField_displayOrder`) for the same Editor. Tests keep this red —
  the step under test is never re-pointed at the admin account.
  `last_submit["display_order_control"]` records the bound control name.

  The admin (TEST_USER) session is used ONLY in teardown, in a separate
  context, to repair (valid Display Order) and delete the test's own
  exact-title QCTEST- record when the role session could not delete it.

TEST-DATA SAFETY (standards.md "Destructive Operations Against qcdev"):
delete_category() resolves the target by an EXACT Entry-column match, refuses
any title that does not start with "QCTEST-", and re-checks the Delete link's
own `data-qc-oel-label` against the title immediately before clicking.
"""

from __future__ import annotations

import re
import time
from contextlib import contextmanager

from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.useful_links.useful_links_page_admin_page import (
    ROLE_EDITOR,
    ROLE_USER_IDS,
)
from config.settings import cms_role_credentials, control_panel_url, settings, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.license_gate import clear_license_gate
from core.web.overlays import dismiss_overlays

logger = get_logger(__name__)

CATEGORY_SLUG = "useful-link-category"
PUBLIC_PAGE_PATH = "/web/qatar-chamber/useful-links"
DISPOSABLE_PREFIX = "QCTEST-"

ADMIN_HOME_EN_URL_PATH = "/en/home"
CONTROL_MENU_NAV = 'nav[aria-label="Control Menu"]'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'

# ---- Category form fields (exact accessible names, confirmed live) -------
FIELD_CATEGORY_NUMBER = "Category Number"
FIELD_CATEGORY_EYEBROW_EN = "Category Eyebrow"
FIELD_CATEGORY_EYEBROW_AR = "Category Eyebrow — العربية *"
FIELD_CATEGORY_TITLE_EN = "Category Title"
FIELD_CATEGORY_TITLE_AR = "Category Title — العربية *"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_ACTIVE_STATUS = "Active Status"

# ---- Validation messages (verbatim, confirmed live) ----------------------
MSG_REQUIRED_FIELDS = "Please complete the required fields before proceeding"
MSG_CATEGORY_NUMBER_SPACES = "Category Number cannot be only spaces."
MSG_CATEGORY_NUMBER_FORMAT = "Category Number must be a two-character zero-padded value from 01 to 09."
MSG_DISPLAY_ORDER_GRID = "Display Order must be 100 or greater and follow the 100-grid"
SUCCESS_NOTICE_PATTERN = re.compile(r"^\s*(Saved and published\.|Draft saved\.|Saved and submitted for review\.)\s*$")
ARABIC_NOTICE_PATTERN = re.compile(r"Arabic content (saved|could not|was not)", re.I)
ARABIC_FAILED_PATTERN = re.compile(r"Arabic content (could not|was not)", re.I)


class _UsefulLinksAuthoringBase(ObjectAuthoringPage):
    """Everything the two Useful Links authoring objects share: the session
    guard, the Publish/Save-as-Draft buttons (this object family has no
    "Submit for Review" button), post-submit settling, the validation-bar
    reader, and safe, exact-title row lookup + delete."""

    PUBLISH_BUTTON = 'button[name="status"][value="0"]'
    SAVE_DRAFT_BUTTON = 'button[name="status"][value="2"]'
    # The shared class waits on 'button:has-text("Save as Draft")' for a
    # mounted form; that button exists here too, so the inherited
    # open_new_entry_form() wait stays valid.
    ALERT_SELECTOR = ".alert, [role=alert]"
    LICENSE_BANNER_TEXT = "activation key"
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    PAGE_SIZE_ALL_VALUE = "0"
    ROW_TITLE_CELL = "td.qc-oel__cell-title"
    ROW_DELETE_LINK = "a[data-qc-oel-delete]"
    LIST_LOADING_STATUS = "[data-qc-oel-status]"
    FEEDBACK_BAR = "[data-qc-oel-editbar]"
    POST_SUBMIT_TIMEOUT_S = 60.0
    NATIVE_BLOCK_CONFIRM_S = 5.0

    # ---- Session ---------------------------------------------------------
    # The role every authoring step signs in as (see the module's ROLE note).
    # None = the admin TEST_USER session — used only by teardown twins.
    role: str | None = ROLE_EDITOR

    def open(self, url: str) -> None:
        """Role sessions navigate WITHOUT BasePage's session guard: that guard
        re-logs any session it cannot recognise in as TEST_USER, which would
        silently turn a role outcome into a super-admin one. A dropped role
        session is re-established by ensure_session() instead."""
        if not self.role:
            super().open(url)
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    def signed_in_user(self) -> tuple[str, str]:
        """(userId, userName) from Liferay's own ThemeDisplay; ('', '') when
        signed out or the page has no Liferay runtime."""
        try:
            info = self.page.evaluate(
                """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                    ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                    : ['', '']"""
            )
        except Exception:  # noqa: BLE001 — mid-navigation
            return "", ""
        return info[0], info[1]

    def assert_role(self, when: str = "") -> None:
        """Raises unless this context is signed in as `self.role`."""
        if not self.role:
            return
        expected = ROLE_USER_IDS[self.role]
        actual = self.signed_in_user()
        if actual[0] != expected:
            raise AssertionError(
                f"session is not the {self.role} (userId {expected}) {when}: signed in as {actual!r}"
            )

    def ensure_session(self) -> None:
        """Opens /en/home and makes sure the context is signed in as
        `self.role` (Site Content Editor by default): re-logs in as that
        role when the session is missing, dropped, or belongs to anyone
        else. The admin twin (role=None) keeps the sibling pattern."""
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not self.role:
            if self.is_visible(CONTROL_MENU_NAV) or self.is_visible(PRODUCT_MENU_TOGGLE):
                return
            CmsLoginPage(self.page).open_login().login(settings.test_user, settings.test_password)
            return
        if self.signed_in_user()[0] == ROLE_USER_IDS[self.role]:
            return
        if self.signed_in_user()[0]:
            self.page.goto(control_panel_url("/c/portal/logout"), wait_until="domcontentloaded", timeout=90000)
        email, password = cms_role_credentials(self.role)
        CmsLoginPage(self.page).open_login().login(email, password)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        self.assert_role("after signing in")

    @contextmanager
    def admin_twin(self):
        """TEARDOWN ONLY: the same Page Object in a separate context on the
        cached admin (TEST_USER) session, for repairing/deleting the test's
        own QCTEST- record when the role session could not."""
        from core.web.browser import new_context

        ctx = new_context(self.page.context.browser)
        try:
            # Same Page Object class and slug (subclasses add no init state).
            twin = type(self).__new__(type(self))
            _UsefulLinksAuthoringBase.__init__(twin, ctx.new_page(), self.slug)
            twin.role = None
            yield twin
        finally:
            try:
                ctx.close()
            except Exception:  # noqa: BLE001
                pass

    def open_new_form(self):
        self._last_fills = []
        return self._open_new_form()

    def _open_new_form(self):
        """Opens the create form and waits for the page's own client-side
        list/form bootstrap to finish (`[data-qc-oel-status]` hidden) —
        confirmed live 2026-09-29 that filling before it finishes can have
        every typed value wiped by the late form reset."""
        self.ensure_session()
        self.open_new_entry_form()
        self._wait_list_loaded()
        return self

    def _fill_verified(self, fills: list) -> None:
        """Applies (label, value, filler) triples, then reads each control
        back; any value a late client-side reset wiped is re-applied (at most
        twice). The read-back compares against what the browser would hold
        for that input, so a deliberately non-numeric Display Order (which a
        number input drops) is not "re-applied" forever."""
        self._last_fills = list(getattr(self, "_last_fills", [])) + list(fills)
        for _ in range(3):
            for _label, value, filler in fills:
                filler(value)
            stale = [(lbl, v, f) for lbl, v, f in fills if not self._holds(lbl, v)]
            if not stale:
                return
            logger.info("re-applying fields wiped by a late form reset: %s", [lbl for lbl, _, _ in stale])
            self._wait_list_loaded()
            fills = stale

    def _holds(self, label: str, value) -> bool:
        if label == FIELD_ACTIVE_STATUS:
            return self.is_active_status_checked() == value
        if label == FIELD_DISPLAY_ORDER:
            expected = str(value) if re.fullmatch(r"-?\d+", str(value)) else ""
            return self.display_order_value() == expected
        return self._textbox(label).input_value() == value

    # ---- Low-level field helpers ------------------------------------------
    def _textbox(self, label: str):
        return self.page.get_by_role("textbox", name=label, exact=True)

    def _spinbutton(self, label: str):
        return self.page.get_by_role("spinbutton", name=label, exact=True)

    def set_display_order(self, value: str):
        """Types `value` keystroke by keystroke so a non-numeric string
        ("abc", "two") behaves as it does for a real user on an
        <input type=number> — the browser drops the characters and the field
        stays empty — instead of Playwright's fill() raising on it."""
        box = self._spinbutton(FIELD_DISPLAY_ORDER)
        box.click()
        box.press("Control+a")
        box.press("Delete")
        self.page.keyboard.type(str(value), delay=15)
        return self

    def display_order_value(self) -> str:
        return self._spinbutton(FIELD_DISPLAY_ORDER).input_value()

    def set_active_status(self, active: bool):
        self.set_checkbox(FIELD_ACTIVE_STATUS, active)
        return self

    def is_active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    def native_validation_message(self, label: str, role: str = "textbox") -> str:
        return self.page.get_by_role(role, name=label, exact=True).evaluate("el => el.validationMessage")

    # ---- Submit ---------------------------------------------------------------
    def publish(self) -> bool:
        """Clicks Publish and waits until the page settles into either a
        saved state (URL carries previewEntry=/editEntry=) or a refused one
        (a validation alert, the required-fields message, or a native-invalid
        control). Returns True when the save committed."""
        return self._submit(self.PUBLISH_BUTTON)

    def save_as_draft_and_wait(self) -> bool:
        return self._submit(self.SAVE_DRAFT_BUTTON)

    def _submit(self, button_selector: str) -> bool:
        """Marks the current document, clicks, then waits until EITHER the
        document was replaced by the post-submit render (form POST ->
        reload; the marker is gone and the form is mounted again) OR the
        still-current document shows a refusal (alert bar, required-fields
        notice, or a native-invalid control that blocked the submit). The
        save counts as committed only when a reload happened and the new
        render carries no refusal."""
        # A late client-side form reset can wipe values after they were
        # verified; re-check everything this form was given right before the
        # click (cheap when nothing changed).
        pending = [f for f in getattr(self, "_last_fills", []) if not self._holds(f[0], f[1])]
        if pending:
            logger.info("re-applying %s before submit", [f[0] for f in pending])
            self._fill_verified(pending)
        submitted_fills = list(getattr(self, "_last_fills", []))
        self._last_fills = []
        # Role-dependent outcome: prove WHO clicks, and which control the
        # "Display Order" label is bound to (Bug 1 evidence).
        self.assert_role("before the submit click")
        user_before = self.signed_in_user()
        spin = self._spinbutton(FIELD_DISPLAY_ORDER)
        bound = (spin.first.get_attribute("name") or "") if spin.count() else ""
        before = self.page.url
        self.page.evaluate("() => { window.__qcUlSubmitMarker = true; }")
        self.page.locator(button_selector).click()
        state = {"reloaded": False}

        def _settled() -> bool:
            try:
                marker = self.page.evaluate("() => window.__qcUlSubmitMarker === true")
            except Exception:  # noqa: BLE001 — navigating right now
                return False
            if not marker:
                state["reloaded"] = True
                return self.page.locator(self.PUBLISH_BUTTON).count() > 0
            if self.page.url != before and "previewEntry=" in self.page.url:
                state["reloaded"] = True  # in-place (history) navigation to the saved record
                return True
            if self.validation_errors() or self.required_fields_message_shown():
                return True
            invalid = self.page.evaluate(
                "() => !!document.querySelector('form input:invalid:not([type=hidden])')"
            )
            if not invalid or not all(self._holds(f[0], f[1]) for f in submitted_fills):
                state.pop("blocked_since", None)
                return False
            # A native block leaves the page (URL + values) unchanged. The
            # post-save form reset can momentarily look identical before the
            # URL moves to previewEntry=, so the state must hold for a few
            # seconds before it counts as a refusal.
            since = state.setdefault("blocked_since", time.monotonic())
            return time.monotonic() - since >= self.NATIVE_BLOCK_CONFIRM_S

        try:
            wait_until(_settled, timeout=self.POST_SUBMIT_TIMEOUT_S, poll=0.5,
                       message="Publish/Save neither committed nor showed a refusal")
            settled = True
        except WaitTimeoutError:
            settled = False
            logger.warning("submit did not settle within %ss (url=%s)", self.POST_SUBMIT_TIMEOUT_S, self.page.url)
        # The success toast auto-dismisses: read it straight after the
        # reload, before the list bootstrap and the Arabic-save waits.
        notice = self._read_success_notice(timeout_ms=8000) if state["reloaded"] else ""
        if state["reloaded"]:
            self._wait_list_loaded()
        errors = self.validation_errors()
        required = self.required_fields_message_shown()
        invalid = self.page.evaluate(
            "() => [...document.querySelectorAll('form input:invalid:not([type=hidden])')]"
            ".map(e => (e.name || e.id) + ': ' + e.validationMessage)"
        )
        self.last_submit = {
            "settled": settled, "reloaded": state["reloaded"], "url": self.page.url,
            "errors": errors, "required_notice": required, "invalid_controls": invalid,
            "success_notice": notice, "display_order_control": bound, "user": user_before,
            "feedback": [t.strip() for t in self.page.locator(self.FEEDBACK_BAR).all_inner_texts() if t.strip()],
        }
        if state["reloaded"]:
            self.assert_role("after the submit reload")
        logger.info("submit outcome: %s", self.last_submit)
        if not state["reloaded"] or errors or required:
            return False
        self._wait_for_arabic_save()
        return True

    def _wait_for_arabic_save(self) -> None:
        """OBJECT-AUTHORING-GUIDE §5: on a new record the Arabic boxes are
        saved a moment AFTER the record. Waits (bounded) for the surface's own
        "Arabic content saved…" / "…Arabic content was not / could not…"
        notice so a caller never navigates away mid-write. Absent notice (an
        edit, or no Arabic typed) is fine — the wait simply times out."""
        notice = self.page.get_by_text(ARABIC_NOTICE_PATTERN).first
        try:
            notice.wait_for(state="visible", timeout=15000)
            self.last_submit["arabic_notice"] = notice.inner_text().strip()
        except Exception:  # noqa: BLE001 — notice not shown for this save
            self.last_submit["arabic_notice"] = ""

    def arabic_save_failed(self) -> bool:
        return self.page.get_by_text(ARABIC_FAILED_PATTERN).count() > 0

    last_submit: dict = {}

    SERVER_REFUSAL_TEXT = "This record was not saved"

    def validation_errors(self) -> list[str]:
        """Texts of the refusal bar(s), with the dev instance's own
        licence-expiry banner filtered out: the client-side alert bar AND the
        edit bar's server refusal ("This record was not saved: • …"). HEALED
        2026-09-30: for the Site Content Editor the client-side rule messages
        are not rendered and the refusal arrives only in the edit bar
        (observed: "Object entry value exceeds the maximum length of 100
        characters for object field "categoryEyebrow"")."""
        texts = self.page.locator(self.ALERT_SELECTOR).all_inner_texts()
        texts += [t for t in self.page.locator(self.FEEDBACK_BAR).all_inner_texts() if self.SERVER_REFUSAL_TEXT in t]
        out = []
        for t in (t.strip() for t in texts):
            if t and self.LICENSE_BANNER_TEXT not in t and t not in out:
                out.append(t)
        return out

    def _read_success_notice(self, timeout_ms: int = 8000) -> str:
        """Waits (bounded) for the post-save success notice — confirmed live
        2026-09-29 as "Saved and published." after a Publish ("Draft saved."
        for Save as Draft) — and returns its text, or "" if none showed."""
        notice = self.page.get_by_text(SUCCESS_NOTICE_PATTERN)
        try:
            notice.first.wait_for(state="visible", timeout=timeout_ms)
            return notice.first.inner_text().strip()
        except Exception:  # noqa: BLE001 — not shown
            return ""

    def success_notice(self) -> str:
        """The success notice of the LAST submit, captured inside _submit()
        right after the reload (it auto-dismisses); falls back to a short
        live read. "" when no notice appeared."""
        captured = (self.last_submit or {}).get("success_notice", "")
        return captured or self._read_success_notice(timeout_ms=2000)

    def required_fields_message_shown(self) -> bool:
        return self.page.get_by_text(MSG_REQUIRED_FIELDS).count() > 0

    def has_validation_error(self, fragment: str) -> bool:
        return any(fragment in t for t in self.validation_errors())

    # ---- Entries list ---------------------------------------------------------
    def open_list(self):
        self.ensure_session()
        self.open_entries_list()
        self._wait_list_loaded()
        self._show_all_rows()
        return self

    def _wait_list_loaded(self) -> None:
        try:
            self.page.locator(self.LIST_LOADING_STATUS).wait_for(state="hidden", timeout=20000)
        except Exception:  # noqa: BLE001 — status node absent on some renders
            pass

    def _show_all_rows(self) -> None:
        """Switches the list's page-size selector to "All" when the object
        paginates (Useful Link has 46+ rows at 10 per page)."""
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() == 0 or not select.first.is_visible():
            return
        if select.first.input_value() == self.PAGE_SIZE_ALL_VALUE:
            return
        select.first.select_option(self.PAGE_SIZE_ALL_VALUE)
        self._wait_list_loaded()
        self.page.locator(self.ROW_DELETE_LINK).first.wait_for(state="attached", timeout=15000)

    def _exact_row(self, title: str):
        """The single entries-table row whose Entry cell equals `title`
        exactly (never a substring match), or None."""
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        for i in range(rows.count()):
            row = rows.nth(i)
            cell = row.locator(self.ROW_TITLE_CELL)
            if cell.count() and cell.first.inner_text().strip() == title:
                return row
        return None

    def row_exists(self, title: str) -> bool:
        return self._exact_row(title) is not None

    def row_status(self, title: str) -> str:
        row = self._exact_row(title)
        if row is None:
            return ""
        return normalize_status(row.locator("td").nth(1).inner_text())

    def open_for_edit(self, title: str):
        """Opens the row's own Edit link (its href carries the real
        editEntry code) and waits for the editing banner."""
        self.open_list()
        row = self._exact_row(title)
        if row is None:
            raise AssertionError(f"No entries-list row titled exactly {title!r}")
        href = row.get_by_role("link", name="Edit").get_attribute("href") or ""
        match = re.search(r"[?&]editEntry=([^&]+)", href)
        if not match:
            raise AssertionError(f"Row {title!r} has no editEntry code in its Edit link ({href!r})")
        self.open_entry_by_code(match.group(1))
        self.wait_for(self.PUBLISH_BUTTON, timeout=20000)
        return self

    def delete_disposable(self, title: str) -> bool:
        """Deletes ONE row, identified by an exact Entry-cell match, and only
        when the title carries the QCTEST- prefix; re-verifies the Delete
        link's own data-qc-oel-label equals the title right before clicking.
        Returns True once the row is gone. Raises on a non-disposable title —
        that is a programming error, never something to swallow."""
        if not title.startswith(DISPOSABLE_PREFIX):
            raise ValueError(f"Refusing to delete non-disposable record {title!r}")
        self.open_list()
        row = self._exact_row(title)
        if row is None:
            return False
        link = row.locator(self.ROW_DELETE_LINK).first
        label = link.get_attribute("data-qc-oel-label") or ""
        entry_id = link.get_attribute("data-qc-oel-delete") or ""
        if label != title or not entry_id:
            raise AssertionError(
                f"Delete target re-check failed: row label {label!r} != {title!r} (id={entry_id!r})"
            )

        def _accept(dialog):
            try:
                dialog.accept()
            except Exception:  # noqa: BLE001 — already handled
                pass

        self.page.on("dialog", _accept)
        try:
            target = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
            target.click()
            try:
                target.wait_for(state="detached", timeout=20000)
            except Exception:  # noqa: BLE001 — refused delete; reported via the return value
                logger.warning("Delete of %s did not remove the row (server refused?)", title)
        finally:
            self.page.remove_listener("dialog", _accept)
        self.open_list()
        return not self.row_exists(title)

    # ---- Recycle Bin -----------------------------------------------------------
    RECYCLE_BIN = "details[data-qc-oel-trash]"
    RECYCLE_BIN_ITEM = "details[data-qc-oel-trash] li"
    RECYCLE_BIN_RESTORE = "a[data-qc-oel-untrash]"

    def _recycle_bin_item(self, title: str):
        details = self.page.locator(self.RECYCLE_BIN)
        if details.count() == 0:
            return None
        if details.first.get_attribute("open") is None:
            details.first.locator("summary").click()
        items = self.page.locator(self.RECYCLE_BIN_ITEM)
        for i in range(items.count()):
            item = items.nth(i)
            text = item.inner_text().split("·")[0].strip()
            if text == title:
                return item
        return None

    def in_recycle_bin(self, title: str) -> bool:
        self.open_list()
        return self._recycle_bin_item(title) is not None

    def restore_from_recycle_bin(self, title: str) -> bool:
        """Restores ONE recycled record (exact title, QCTEST- only). Used
        by teardown only: a category whose child Link Item sits in the
        Recycle Bin cannot itself be deleted (see useful_link_admin_page's
        FINDING note), so the recycled child is restored first and the
        category delete then takes both away together."""
        if not title.startswith(DISPOSABLE_PREFIX):
            raise ValueError(f"Refusing to restore non-disposable record {title!r}")
        self.open_list()
        item = self._recycle_bin_item(title)
        if item is None:
            return False
        link = item.locator(self.RECYCLE_BIN_RESTORE).first
        entry_id = link.get_attribute("data-qc-oel-untrash") or ""

        def _accept(dialog):
            try:
                dialog.accept()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _accept)
        try:
            link.click()
            self.page.locator(f'a[data-qc-oel-untrash="{entry_id}"]').wait_for(state="detached", timeout=20000)
        finally:
            self.page.remove_listener("dialog", _accept)
        return True

    # Form control that carries the Entry-column title (set per object).
    ENTRY_TITLE_FIELD: str | None = None

    def repair_display_order(self, title: str, value: str = "900") -> bool:
        """TEARDOWN ONLY, on the admin twin: gives the test's own QCTEST-
        record (exact Entry title, title re-read on the open form) a valid
        Display Order so the Recycle-Bin move — which re-runs the object's
        validation — is accepted. Returns True when a save committed."""
        if self.role:
            raise RuntimeError("repair_display_order is an admin-twin teardown helper only")
        if not title.startswith(DISPOSABLE_PREFIX):
            raise ValueError(f"Refusing to edit non-disposable record {title!r}")
        self.open_for_edit(title)
        if self.ENTRY_TITLE_FIELD and self._textbox(self.ENTRY_TITLE_FIELD).input_value() != title:
            raise AssertionError(f"STOP: the opened record is not {title!r}")
        spin = self._spinbutton(FIELD_DISPLAY_ORDER)
        if spin.count() != 1 or spin.get_attribute("name") != "ObjectField_displayOrder":
            return False
        self._last_fills = [(FIELD_DISPLAY_ORDER, value, self.set_display_order)]
        self.set_display_order(value)
        draft = self.page.locator(self.SAVE_DRAFT_BUTTON)
        if draft.count() and draft.first.is_enabled():
            return self.save_as_draft_and_wait()
        return self.publish()

    def delete_owned(self, title: str) -> bool:
        """Deletes the test's own QCTEST- record by exact title: first in the
        role session; if that session could not remove it, in the admin twin
        (repairing a missing Display Order first — Bug 1 leaves role-created
        records without one). A failed identity re-check raises (STOP)."""
        if self.delete_disposable(title):
            return True
        if not self.role:
            return False
        with self.admin_twin() as admin:
            if admin.delete_disposable(title):
                return True
            if admin.row_exists_fresh(title) and admin.repair_display_order(title):
                return admin.delete_disposable(title)
            return not admin.row_exists_fresh(title)

    def teardown_category(self, category_title: str, recycled_link_titles=()) -> None:
        """Teardown for a QCTEST category and everything under it. Deleting
        a category moves its Link Items to the Recycle Bin with it; but a
        category whose child is ALREADY recycled cannot be deleted (server
        answers 400 "Delete failed: null" — see the link module's FINDING),
        so any such child named in `recycled_link_titles` is restored first.
        Never raises."""
        try:
            if not self.row_exists_fresh(category_title):
                return
            links = _UsefulLinksAuthoringBase(self.page, "useful-link")
            links.role = self.role
            for link_title in recycled_link_titles:
                if links.in_recycle_bin(link_title):
                    links.restore_from_recycle_bin(link_title)
            if not self.delete_owned(category_title):
                logger.warning("LEFTOVER QCTEST category may remain: %s", category_title)
        except Exception as exc:  # noqa: BLE001 — teardown must not mask the test result
            logger.warning("teardown of %s failed: %s", category_title, exc)

    def safe_cleanup(self, title: str) -> None:
        """Teardown wrapper — never raises, logs a leftover instead."""
        try:
            if self.row_exists_fresh(title):
                if not self.delete_owned(title):
                    logger.warning("LEFTOVER QCTEST record may remain: %s", title)
        except Exception as exc:  # noqa: BLE001 — teardown must not mask the test result
            logger.warning("cleanup of %s failed: %s", title, exc)

    def saved_despite_ambiguous_submit(self, title: str) -> bool:
        """Setup-only fallback: when a submit settled without any refusal
        text (no alert, no required notice) the entries list is the arbiter
        of whether the record was written."""
        info = self.last_submit or {}
        if info.get("errors") or info.get("required_notice"):
            return False
        return self.row_exists_fresh(title)

    def row_exists_fresh(self, title: str) -> bool:
        self.open_list()
        return self.row_exists(title)


class UsefulLinkCategoryAdminPage(_UsefulLinksAuthoringBase):
    """manage-useful-link-category — one row per accordion category."""

    ENTRY_TITLE_FIELD = FIELD_CATEGORY_TITLE_EN

    def __init__(self, page):
        super().__init__(page, CATEGORY_SLUG)

    def fill_category(
        self,
        number: str | None = None,
        eyebrow_en: str | None = None,
        eyebrow_ar: str | None = None,
        title_en: str | None = None,
        title_ar: str | None = None,
        display_order: str | None = None,
        active: bool | None = None,
    ) -> "UsefulLinkCategoryAdminPage":
        """Fills only the arguments given; None leaves a field untouched."""
        text = lambda label: (lambda v: self._textbox(label).fill(v))  # noqa: E731
        fills = [
            (FIELD_CATEGORY_NUMBER, number, text(FIELD_CATEGORY_NUMBER)),
            (FIELD_CATEGORY_EYEBROW_EN, eyebrow_en, text(FIELD_CATEGORY_EYEBROW_EN)),
            (FIELD_CATEGORY_EYEBROW_AR, eyebrow_ar, text(FIELD_CATEGORY_EYEBROW_AR)),
            (FIELD_CATEGORY_TITLE_EN, title_en, text(FIELD_CATEGORY_TITLE_EN)),
            (FIELD_CATEGORY_TITLE_AR, title_ar, text(FIELD_CATEGORY_TITLE_AR)),
            (FIELD_DISPLAY_ORDER, display_order, self.set_display_order),
            (FIELD_ACTIVE_STATUS, active, self.set_active_status),
        ]
        self._fill_verified([f for f in fills if f[1] is not None])
        return self

    def field(self, label: str) -> str:
        return self._textbox(label).input_value()

    def create_category(
        self,
        title_en: str,
        number: str = "09",
        eyebrow_en: str = "QCTEST eyebrow",
        eyebrow_ar: str = "حاجب اختبار",
        title_ar: str = "فئة اختبار",
        display_order: str = "900",
        active: bool = True,
    ) -> bool:
        """Setup helper for tests whose subject is not the category form
        itself: opens a fresh form, fills a complete valid category and
        publishes it. Returns True when the save committed."""
        self.open_new_form()
        self.fill_category(number, eyebrow_en, eyebrow_ar, title_en, title_ar, display_order, active)
        return self.publish() or self.saved_despite_ambiguous_submit(title_en)


def qctest_title(tc_id: int | str, kind: str, suffix: str = "") -> str:
    """Unique disposable title, e.g. "QCTEST-140730-ULCAT-5123456". The
    QCTEST- prefix is what delete_disposable() insists on."""
    stamp = str(int(time.time() * 1000))[-8:]
    base = f"{DISPOSABLE_PREFIX}{tc_id}-{kind}-{stamp}"
    return f"{base} {suffix}".strip() if suffix else base


@contextmanager
def anonymous_public_view(browser, stub_hosts: str | None = None):
    """A FRESH, logged-out browser context (no storageState) opened on the
    public page reader — the mandatory path for every visitor-visibility
    assertion. `stub_hosts` (a regex) answers matching external URLs with a
    local stub page so redirect checks assert WHERE the card navigates
    without depending on third-party sites being reachable from the runner."""
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    try:
        if stub_hosts:
            ctx.route(
                re.compile(stub_hosts),
                lambda route: route.fulfill(
                    status=200, content_type="text/html",
                    body="<html><head><title>external stub</title></head><body>external stub</body></html>",
                ),
            )
        yield UsefulLinksPublicView(ctx.new_page())
    finally:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001 — teardown must not mask the result
            pass


class UsefulLinksPublicView(BasePage):
    """Read-only reader for the public /useful-links accordion. Always hand
    it a page from a FRESH, logged-out context (standards.md: public
    visibility checks must never reuse the CMS session)."""

    ACCORDION = "[data-qc-ul-accordion]"
    ROW = ".qc-ul-row"
    HEAD = "button.qc-ul-head"
    HEAD_NUM = ".qc-ul-num"
    HEAD_EYEBROW = ".qc-ul-head-eyebrow"
    HEAD_TITLE = ".qc-ul-head-title"
    CARD = "a.qc-ul-card"
    CARD_ORG = ".qc-ul-org"
    CARD_SITE = ".qc-ul-site"
    PROPAGATION_TIMEOUT_S = 20.0

    def open_page(self, locale: str = "en") -> "UsefulLinksPublicView":
        self.open(web_url(PUBLIC_PAGE_PATH, locale=locale))
        self.page.locator(self.HEAD).first.wait_for(state="visible", timeout=30000)
        return self

    def _row(self, title: str):
        return self.page.locator(self.ROW).filter(
            has=self.page.locator(self.HEAD_TITLE, has_text=re.compile(rf"^\s*{re.escape(title)}\s*$"))
        )

    def category_titles(self) -> list[str]:
        return [t.strip() for t in self.page.locator(f"{self.ROW} {self.HEAD_TITLE}").all_inner_texts()]

    def category_numbers(self) -> list[str]:
        return [t.strip() for t in self.page.locator(f"{self.ROW} {self.HEAD_NUM}").all_inner_texts()]

    def has_category(self, title: str) -> bool:
        return self._row(title).count() > 0

    def category_header(self, title: str) -> dict:
        row = self._row(title).first
        return {
            "number": row.locator(self.HEAD_NUM).inner_text().strip(),
            "eyebrow": row.locator(self.HEAD_EYEBROW).inner_text().strip(),
            "title": row.locator(self.HEAD_TITLE).inner_text().strip(),
        }

    def wait_for_category(self, title: str, present: bool = True) -> bool:
        """Publish-then-poll: reloads until the category's presence matches
        `present` or the budget runs out. Returns the final presence."""
        def _check() -> bool:
            self.open_page()
            return self.has_category(title) == present

        try:
            wait_until(_check, timeout=self.PROPAGATION_TIMEOUT_S, poll=1.0)
        except WaitTimeoutError:
            pass
        return self.has_category(title)

    def wait_for_order(self, ahead: str, behind: str, category_title: str | None = None) -> list[str]:
        """Publish-then-poll for a reorder: reloads until `ahead` renders
        before `behind` — among category titles, or among the cards of
        `category_title` when given. Returns the last observed order."""
        seen: list[str] = []

        def _check() -> bool:
            nonlocal seen
            self.open_page()
            if category_title is None:
                seen = self.category_titles()
            else:
                seen = self.card_orgs(category_title) if self.has_category(category_title) else []
            return ahead in seen and behind in seen and seen.index(ahead) < seen.index(behind)

        try:
            wait_until(_check, timeout=self.PROPAGATION_TIMEOUT_S, poll=1.0)
        except WaitTimeoutError:
            pass
        return seen

    def expand(self, title: str) -> "UsefulLinksPublicView":
        head = self._row(title).first.locator(self.HEAD)
        if head.get_attribute("aria-expanded") != "true":
            head.click()
            self.page.wait_for_function(
                "el => el.getAttribute('aria-expanded') === 'true'", arg=head.element_handle(), timeout=5000
            )
        return self

    def cards(self, category_title: str) -> list[dict]:
        self.expand(category_title)
        cards = self._row(category_title).first.locator(self.CARD)
        return cards.evaluate_all(
            """els => els.map(e => ({
                org: (e.querySelector('.qc-ul-org')||{}).innerText || '',
                site: (e.querySelector('.qc-ul-site')||{}).innerText || '',
                href: e.getAttribute('href') || '',
                target: e.getAttribute('target') || '',
                logo: (e.querySelector('img')||{}).src || ''
            }))"""
        )

    def card_orgs(self, category_title: str) -> list[str]:
        return [c["org"].strip() for c in self.cards(category_title)]

    def card(self, category_title: str, org: str) -> dict | None:
        for c in self.cards(category_title):
            if c["org"].strip() == org:
                return c
        return None

    def card_locator(self, category_title: str, org: str):
        self.expand(category_title)
        return self._row(category_title).first.locator(self.CARD).filter(
            has=self.page.locator(self.CARD_ORG, has_text=re.compile(rf"^\s*{re.escape(org)}\s*$"))
        ).first

    def wait_for_card(self, category_title: str, org: str, present: bool = True) -> bool:
        def _check() -> bool:
            self.open_page()
            if not self.has_category(category_title):
                return not present
            return (org in self.card_orgs(category_title)) == present

        try:
            wait_until(_check, timeout=self.PROPAGATION_TIMEOUT_S, poll=1.0)
        except WaitTimeoutError:
            seen = self.category_titles()
            cards = self.card_orgs(category_title) if self.has_category(category_title) else None
            logger.warning("wait_for_card(%r, %r, present=%s) timed out; categories=%s cards=%s",
                           category_title, org, present, seen, cards)
        return self.has_category(category_title) and org in self.card_orgs(category_title)

    # ---- Redirect behaviour ----------------------------------------------------
    def click_card_new_tab(self, category_title: str, org: str) -> tuple[str, str]:
        """Clicks the card and returns (popup_url, original_tab_url). Raises
        if no new tab opens."""
        card = self.card_locator(category_title, org)
        with self.page.context.expect_page(timeout=15000) as popup_info:
            card.click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded", timeout=15000)
        return popup.url, self.page.url

    def click_card_same_tab(self, category_title: str, org: str) -> tuple[str, int]:
        """Clicks the card and returns (this_tab_url_after_click,
        open_tab_count) — a Same Tab card must navigate THIS tab and open
        no other."""
        card = self.card_locator(category_title, org)
        start = self.page.url
        card.click()
        try:
            self.page.wait_for_url(lambda u: u != start, timeout=15000)
        except Exception:  # noqa: BLE001 — reported through the returned URL
            pass
        return self.page.url, len(self.page.context.pages)

    # ---- Whole-page reads ------------------------------------------------------
    def category_eyebrows(self) -> list[str]:
        return [t.strip() for t in self.page.locator(f"{self.ROW} {self.HEAD_EYEBROW}").all_inner_texts()]

    def all_card_orgs(self) -> list[str]:
        """Organization names of every card on the page, expanded or not
        (collapsed panels keep their cards in the DOM)."""
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_ORG}").all_text_contents()]

"""
cms/pages/useful_links/useful_links_page_admin_page.py —
UsefulLinksPageAdminPage / UsefulLinksPublicView.

PBI 130702 "QC - Business Gateway - 009 - Useful Links", Control_Panel
surface, the PAGE-LEVEL object only (hero + directory-intro copy, hero
banner, page status). The Category and Link objects belong to the sibling
admin pages in this folder; this module drives the Category object only
through the generic ObjectAuthoringPage state machine, for the three
category-shaped cases in this batch (140691, 140692/140693 and 140786), and
only ever on records its own test created.

═══════════════════════════════════════════════════════════════════════
THE OBJECT: confirmed live 2026-09-29 (TEST_USER session, qcdev, CLI probe)
  Object Authoring slug `useful-links-page`
    -> https://qcdev.ihorizons.com/web/qatar-chamber/manage-useful-links-page
  Listed on /object-authoring as "Useful Links Page" (object-authoring-index.md).
  Not documented in cms/Content-Admin-Guide.docx.
  SINGLETON: exactly ONE record, entry code `QCDEMO-130702-ULP-1`, entry id
  109803, title "Useful Links", PUBLISHED, Active. It is REAL shared
  content. Never deleted. Every test that edits it is TEST_OWNED: capture a
  full snapshot first, restore it in `finally`, and leave it Published.
  REST the public page reads: /o/c/usefullinkspages/scopes/37246?pageSize=1
  Public page: /web/qatar-chamber/useful-links  (AR: /ar/web/...)
═══════════════════════════════════════════════════════════════════════

FIELDS (read off the live `/en/` edit form; every control is addressed by its
own stable `name` / `id` attribute, never by fragment-generated ids or by
label text, so the same locator works in an Arabic interface too):

    key                 EN control                          AR control              counter
    eyebrow_label       [name=ObjectField_eyebrowLabel]      #qc-ar-eyebrowLabel      60
    page_title          [name=ObjectField_pageTitle]         #qc-ar-pageTitle        120
    directory_eyebrow   [name=ObjectField_directoryEyebrow]  #qc-ar-directoryEyebrow 100
    directory_heading   [name=ObjectField_directoryHeading]  #qc-ar-directoryHeading 120
    directory_subtext   [name=ObjectField_directorySubtext]  #qc-ar-directorySubtext 250
    hero description    rich text, CKEditor (EN textarea[name=ObjectField_heroDescription],
                        AR #qc-ar-heroDescription), "Hero Description Required"
    Hero Banner         attachment; picker declares extensions .jpg,.jpeg,.png,.svg and
                        maxFileSize "2"; help line "Upload a .jpg,.jpeg,.png,.svg no
                        larger than 2 MB."
    Status              picklist `pageStatus` — Draft / Published / Unpublished.
                        THE PUBLIC FRAGMENT RENDERS NOTHING unless pageStatus ==
                        "published" (its own shipped comment and main.js).
    Active Status       checkbox (defaults CHECKED on a new entry).

  Every EN and AR text control carries the HTML `required` attribute and a
  `data-qc-oel-counter` cap; there is NO `maxlength`, so an over-long value
  can be typed. Over the cap the page renders two notes:
    - live counter: "61 characters — the maximum is 60. Shorten it by 1 before saving."
    - Liferay fragment: "Maximum Number of Characters Exceeded: 61 / 60"

FORM ACTIONS (TEST_USER is treated as an Editor by this build: "As an Editor,
what you publish here goes live straight away."):
    button[type=submit][name=status][value="2"]  "Save as Draft" — DISABLED on a
                                                   published record; performs no
                                                   validation (repo-wide finding)
    button[type=submit][name=status][value="0"]  "Publish" (Editor) /
                                                   "Submit for Review" (Author)
  There is no button literally labelled "Save". A case that says "click Save"
  and expects validation can only mean the submit button — the one that
  validates, and the only one enabled on the published singleton.

REFUSAL SHAPE (observed live 2026-09-29, empty Page Title + Publish): the
browser's own required check fires ("Please fill out this field." on the
control), nothing is sent, and a bar reads "Please complete the required
fields before proceeding with the workflow action for Useful Links. Nothing
has been submitted." No "Page title is required." text was rendered.

The Arabic twins are populated a beat after the form renders; `open_singleton`
waits for them before anything is read or typed.

SESSION GUARD CAVEAT (same as LawsRegulationsAdminPage): BasePage.open() can
silently log a dropped session back in as TEST_USER. Role-pinned tests re-read
`signed_in_user()` before asserting.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from cms.pages.components.object_authoring_page import (
    STATUS_PUBLISHED,
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.license_gate import clear_license_gate
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays

logger = get_logger("useful_links_page_admin_page")

USEFUL_LINKS_PAGE_SLUG = "useful-links-page"
USEFUL_LINK_CATEGORY_SLUG = "useful-link-category"
SINGLETON_ENTRY_CODE = "QCDEMO-130702-ULP-1"
SINGLETON_ENTRY_ID = "109803"
SINGLETON_TITLE = "Useful Links"
PUBLIC_PATH = "/web/qatar-chamber/useful-links"
QCTEST_PREFIX = "QCTEST-130702-"

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# Save-feedback strings (English interface).
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_DRAFT_SAVED = "Draft saved."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_REQUIRED_FIELDS_BAR = "Please complete the required fields"
MSG_NOT_SAVED_BAR = "This record was not saved"


@dataclass(frozen=True)
class TextField:
    key: str
    label: str
    name: str
    limit: int

    @property
    def en_selector(self) -> str:
        return f'form [name="ObjectField_{self.name}"]'

    @property
    def ar_selector(self) -> str:
        return f"#qc-ar-{self.name}"


EYEBROW_LABEL = TextField("eyebrow_label", "Eyebrow Label", "eyebrowLabel", 60)
PAGE_TITLE = TextField("page_title", "Page Title", "pageTitle", 120)
DIRECTORY_EYEBROW = TextField("directory_eyebrow", "Directory Eyebrow", "directoryEyebrow", 100)
DIRECTORY_HEADING = TextField("directory_heading", "Directory Heading", "directoryHeading", 120)
DIRECTORY_SUBTEXT = TextField("directory_subtext", "Directory Subtext", "directorySubtext", 250)
TEXT_FIELDS = (EYEBROW_LABEL, PAGE_TITLE, DIRECTORY_EYEBROW, DIRECTORY_HEADING, DIRECTORY_SUBTEXT)

HERO_DESCRIPTION_NAME = "heroDescription"
HERO_BANNER_LABEL = "Hero Banner"


@dataclass(frozen=True)
class CreatedEntry:
    """Identity of a record the CURRENT test created — the only thing the
    delete path accepts. `entry_id` is the row's `data-qc-oel-delete` id."""

    title: str
    entry_id: str


class _AuthoringBase(ObjectAuthoringPage):
    """Save / refusal / row helpers shared by the page and category objects."""

    SUBMIT_BUTTON = 'form button[type="submit"][name="status"][value="0"]'
    DRAFT_BUTTON = 'form button[type="submit"][name="status"][value="2"]'
    FEEDBACK_BANNER = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    FRAGMENT_ERROR = 'p[id$="-error"].text-danger:not(.sr-only)'
    COUNTER_NOTE = 'form div[aria-live="polite"]:not([hidden])'
    # Any rendered row or the form's own submit button: an Author's list
    # carries NO Delete link on rows it does not own (observed live), so the
    # base class's delete-link signal never appears for that account.
    LIST_LOADED = 'table tbody tr, form button[type="submit"][name="status"]'
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    ROW_BY_ID = 'table tbody tr:has(a[data-qc-oel-delete="{entry_id}"])'
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    ROW_ACTION_NAMES = (
        "approve", "reject", "resubmit", "publish", "unpublish", "archive",
        "restore", "return", "schedule", "history", "delete",
    )
    _DOC_MARK = "__qcUsefulLinksBeforeSave"
    pinned_role: str | None = None

    def open(self, url: str) -> None:
        """Role-pinned sessions navigate WITHOUT BasePage's session guard:
        that guard re-logs any session it cannot recognise (no English
        Control Menu, e.g. Site Content Author or an Arabic interface) in
        as TEST_USER, which would silently turn a role assertion into a
        super-admin one. Unpinned sessions keep the normal guarded open."""
        if not self.pinned_role:
            super().open(url)
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    # ---- Session / identity -------------------------------------------------
    def login_as_role(self, role: str) -> str:
        """Real login as a named role in THIS (auth-free) context. Returns
        "ok", "auth_failed" (Liferay's credentials/lockout banner) or
        "unknown". Never falls back to another account."""
        email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            self.pinned_role = role
            return "ok"
        except Exception:  # noqa: BLE001 — classified below, never treated as success
            try:
                body = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                body = ""
            if AUTH_FAILED_BANNER_TEXT in body:
                return "auth_failed"
            # An account without Control Menu access (observed: Site Content
            # Author) signs in fine but never renders CmsLoginPage's success
            # indicator. Liferay's own ThemeDisplay is the arbiter; the
            # caller still checks the userId it expects.
            try:
                if self.signed_in_user()[0]:
                    self.pinned_role = role
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            return "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # ---- Buttons --------------------------------------------------------------
    def submit_button_label(self) -> str:
        button = self.page.locator(self.SUBMIT_BUTTON)
        return button.first.inner_text().strip() if button.count() else ""

    def is_submit_enabled(self) -> bool:
        button = self.page.locator(self.SUBMIT_BUTTON)
        return button.count() > 0 and button.first.is_enabled()

    def is_draft_enabled(self) -> bool:
        button = self.page.locator(self.DRAFT_BUTTON)
        return button.count() > 0 and button.first.is_enabled()

    # ---- Save ----------------------------------------------------------------
    def submit(self) -> "_AuthoringBase":
        """Clicks the role-dependent submit button (Publish / Submit for
        Review). Asserts nothing — the caller asserts the outcome."""
        self._mark_document()
        _dismiss_chatbot_launcher(self.page)
        self.page.locator(self.SUBMIT_BUTTON).first.click()
        self._wait_for_save_outcome()
        return self

    def save_draft(self) -> "_AuthoringBase":
        self._mark_document()
        _dismiss_chatbot_launcher(self.page)
        self.page.locator(self.DRAFT_BUTTON).first.click()
        self._wait_for_save_outcome()
        return self

    def _mark_document(self) -> None:
        self.page.evaluate(f"() => {{ window.{self._DOC_MARK} = true; }}")

    def _document_replaced(self) -> bool:
        try:
            return not self.page.evaluate(f"() => Boolean(window.{self._DOC_MARK})")
        except Exception:  # noqa: BLE001 — mid-navigation
            return False

    def _any_native_invalid(self) -> bool:
        try:
            return bool(self.page.evaluate(
                "() => [...document.querySelectorAll('form input, form textarea')]"
                ".some(i => i.willValidate && !i.checkValidity())"
            ))
        except Exception:  # noqa: BLE001 — navigation in flight
            return False

    def _wait_for_save_outcome(self, timeout: float = 45.0) -> None:
        """A successful save RELOADS the manage page; a refused one stays and
        shows a note, a bar or native validation. Waits for whichever real
        signal appears first — a reload is detected by a marker planted on
        the pre-save document disappearing, never by a fixed sleep."""

        # A refusal is only a NEW bar or a NEW under-the-box note: the live
        # character counter is already visible before the click on an
        # over-long value, so it cannot signal the outcome.
        def _settled() -> bool:
            if self._document_replaced():
                return self.page.locator(self.LIST_LOADED).count() > 0
            return bool(self.refusal_bar()) or bool(self._visible_texts(self.FIELD_ERROR))

        try:
            wait_until(_settled, timeout=timeout, poll=0.5,
                       message="save produced neither a reload nor a refusal")
        except WaitTimeoutError:
            logger.warning("save outcome did not settle; url=%s", self.page.url)
        self.last_save_reloaded = self._document_replaced()
        if self.last_save_reloaded:
            try:
                wait_until(lambda: bool(self.feedback_banners()), timeout=15.0, poll=0.5)
            except WaitTimeoutError:
                pass

    def save_reloaded(self) -> bool:
        """True when the last submit()/save_draft() reloaded the page — the
        surface's own "the save went through" signal."""
        return bool(getattr(self, "last_save_reloaded", False))

    # ---- Feedback / refusal readers ------------------------------------------
    def _visible_texts(self, selector: str) -> list[str]:
        found = self.page.locator(selector)
        out = []
        for i in range(found.count()):
            node = found.nth(i)
            try:
                if node.is_visible():
                    text = (node.inner_text() or "").strip()
                    if text:
                        out.append(text)
            except Exception:  # noqa: BLE001 — node vanished mid-read
                continue
        return out

    def feedback_banners(self) -> list[str]:
        return self._visible_texts(self.FEEDBACK_BANNER)

    def success_banner(self) -> str:
        for text in self.feedback_banners():
            if any(m in text for m in (MSG_SAVED_AND_PUBLISHED, MSG_DRAFT_SAVED, MSG_SUBMITTED_FOR_REVIEW)):
                return text
        return ""

    def refusal_bar(self) -> str:
        for text in self.feedback_banners():
            if MSG_REQUIRED_FIELDS_BAR in text or MSG_NOT_SAVED_BAR in text:
                return text
        return ""

    def native_invalid_messages(self) -> list[str]:
        """`name-or-id: validationMessage` for every form control currently
        failing the browser's own constraint check."""
        try:
            return self.page.evaluate(
                "() => [...document.querySelectorAll('form input, form textarea')]"
                ".filter(e => e.willValidate && !e.checkValidity())"
                ".map(e => (e.name || e.id) + ': ' + e.validationMessage)"
            )
        except Exception:  # noqa: BLE001
            return []

    def refusal_text(self) -> str:
        """EVERYTHING the page says about why a save did not go through, from
        all renderers (under-the-box notes, Liferay fragment notes, live
        counter notes, the red/refusal bar), joined with " | "."""
        parts = (
            self._visible_texts(self.FIELD_ERROR)
            + self._visible_texts(self.FRAGMENT_ERROR)
            + self._visible_texts(self.COUNTER_NOTE)
        )
        bar = self.refusal_bar()
        if bar:
            parts.append(bar)
        return " | ".join(parts)

    def message_report(self) -> str:
        return (
            f"reloaded={self.save_reloaded()}; refusal={self.refusal_text()!r}; "
            f"native={self.native_invalid_messages()!r}; banners={self.feedback_banners()!r}"
        )

    # ---- List (always all rows, scoped by entry id) -------------------------
    def open_list(self) -> "_AuthoringBase":
        self._locale = "en"
        self.open(self._manage_url(locale="en"))
        self.page.locator("table tbody tr").first.wait_for(state="attached", timeout=35000)
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.first.input_value() != "0":
            select.first.select_option("0")
            self.page.locator(self.LIST_LOADED).first.wait_for(state="attached", timeout=15000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def _row_by_id(self, entry_id: str):
        return self.page.locator(self.ROW_BY_ID.format(entry_id=entry_id))

    def row_status_by_id(self, entry_id: str) -> str:
        row = self._row_by_id(entry_id)
        if row.count() != 1:
            return ""
        return normalize_status(row.locator("td").nth(1).inner_text())

    def row_title_by_id(self, entry_id: str) -> str:
        row = self._row_by_id(entry_id)
        return row.locator("td").first.inner_text().strip() if row.count() == 1 else ""

    def row_modified_by_id(self, entry_id: str) -> str:
        row = self._row_by_id(entry_id)
        return row.locator("td").nth(2).inner_text().strip() if row.count() == 1 else ""

    def row_actions_by_id(self, entry_id: str) -> list[str]:
        row = self._row_by_id(entry_id)
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_preview_url_by_id(self, entry_id: str) -> str:
        row = self._row_by_id(entry_id)
        href = row.get_by_role("link", name="Preview").first.get_attribute("href") or ""
        return control_panel_url(href) if href else ""

    def run_row_action_by_id(self, entry_id: str, action: str, comment: str = "") -> "_AuthoringBase":
        """Clicks one id-scoped row action and accepts every native dialog it
        raises (answering prompts with `comment`)."""
        control = self._row_by_id(entry_id).locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(
                f"row {entry_id} offers no {action!r} action; offered: {self.row_actions_by_id(entry_id)}"
            )

        def _accept(dialog):
            try:
                dialog.accept(comment)
            except Exception:  # noqa: BLE001 — already handled
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        return self

    def history_by_id(self, entry_id: str) -> list[dict]:
        """Expands the row's History trail -> [{action, who, when, comment}]."""
        self.open_list()
        self._row_by_id(entry_id).locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row_by_id(entry_id).locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(),
                       timeout=15.0, poll=0.5, message="history did not load")
        except WaitTimeoutError:
            return []
        items = cell.locator("li")
        out = []
        for i in range(items.count()):
            item = items.nth(i)

            def _part(sel: str) -> str:
                node = item.locator(sel)
                return node.first.inner_text().strip() if node.count() else ""

            out.append({
                "action": _part(self.HISTORY_ACTION),
                "who": _part(self.HISTORY_WHO),
                "when": _part(self.HISTORY_WHEN),
                "comment": _part(self.HISTORY_COMMENT),
            })
        return out


class UsefulLinksPageAdminPage(_AuthoringBase):
    """The Useful Links Page singleton (see module docstring)."""

    ARABIC_HYDRATED_TIMEOUT_S = 20.0
    HERO_DESCRIPTION_EN_TEXTAREA = f'textarea[name="ObjectField_{HERO_DESCRIPTION_NAME}"]'
    HERO_DESCRIPTION_AR_TEXTAREA = f"#qc-ar-{HERO_DESCRIPTION_NAME}"
    HERO_DESCRIPTION_EN_EDITOR = f'div[id^="cke_"][id*="ObjectField_{HERO_DESCRIPTION_NAME}"]'
    HERO_DESCRIPTION_REQUIRED_MIRROR = 'form input[id$="-ckeditor-required"]'
    PAGE_STATUS_VALUE = 'form input[name="ObjectField_pageStatus"]'
    PAGE_STATUS_INPUT = 'form input[id$="-select-from-list-input"]'

    def __init__(self, page):
        super().__init__(page, USEFUL_LINKS_PAGE_SLUG)

    # ---- Navigation -----------------------------------------------------------
    def open_singleton(self, locale: str = "en") -> "UsefulLinksPageAdminPage":
        """Opens the singleton's edit form (interface language pinned) and
        waits until its Arabic twins are populated."""
        if locale == "en":
            self.open_entry_by_code(SINGLETON_ENTRY_CODE, locale=locale)
        else:
            # The Arabic interface renders the editing banner in Arabic, so
            # the base class's English "Cancel and add..." wait cannot be
            # used; wait for the record's own (language-neutral) control.
            # NOT BasePage.open(): its session guard looks for the ENGLISH
            # "Control Menu" nav label, finds none on an Arabic interface,
            # treats the session as dead and silently re-logs in as
            # TEST_USER (observed live 2026-09-30 on a role-pinned run).
            url = self._manage_url(edit_entry=SINGLETON_ENTRY_CODE, locale=locale)
            self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
            clear_license_gate(self.page, url)
            self._entry_code, self._locale = SINGLETON_ENTRY_CODE, locale
            self.page.locator(PAGE_TITLE.en_selector).first.wait_for(state="visible", timeout=35000)
        try:
            wait_until(
                lambda: bool(self.page.locator(PAGE_TITLE.ar_selector).input_value()),
                timeout=self.ARABIC_HYDRATED_TIMEOUT_S, poll=0.3,
                message="Arabic values never loaded into the edit form",
            )
        except WaitTimeoutError:
            logger.warning("Arabic twins still empty on the singleton edit form")
        _dismiss_chatbot_launcher(self.page)
        return self

    def singleton_row_status(self) -> str:
        self.open_list()
        return self.row_status_by_id(SINGLETON_ENTRY_ID)

    def singleton_row_modified(self) -> str:
        self.open_list()
        return self.row_modified_by_id(SINGLETON_ENTRY_ID)

    def singleton_history(self) -> list[dict]:
        return self.history_by_id(SINGLETON_ENTRY_ID)

    # ---- Text fields ----------------------------------------------------------
    def _control(self, field: TextField, arabic: bool = False):
        return self.page.locator(field.ar_selector if arabic else field.en_selector).first

    def fill_field(self, field: TextField, value: str, arabic: bool = False) -> "UsefulLinksPageAdminPage":
        self._control(field, arabic).fill(value)
        self._control(field, arabic).dispatch_event("change")
        return self

    def type_field(self, field: TextField, value: str, arabic: bool = False) -> "UsefulLinksPageAdminPage":
        """Clears the control, then TYPES `value` key by key (for max-length
        cases: a real keystroke stream, not a programmatic fill)."""
        control = self._control(field, arabic)
        control.fill("")
        control.press_sequentially(value, delay=2)
        return self

    def clear_field(self, field: TextField, arabic: bool = False) -> "UsefulLinksPageAdminPage":
        return self.fill_field(field, "", arabic)

    def field_text(self, field: TextField, arabic: bool = False) -> str:
        return self._control(field, arabic).input_value()

    def field_native_message(self, field: TextField, arabic: bool = False) -> str:
        return self._control(field, arabic).evaluate("el => el.validationMessage || ''")

    # ---- Hero Description (CKEditor) -----------------------------------------
    def _hero_editor_iframe(self) -> str:
        return self.description_editor_iframe(HERO_DESCRIPTION_NAME)

    def hero_description_html(self, arabic: bool = False) -> str:
        """The STORED value as loaded into the form (the textarea CKEditor was
        initialised from) — read after a fresh open to see what persisted."""
        sel = self.HERO_DESCRIPTION_AR_TEXTAREA if arabic else self.HERO_DESCRIPTION_EN_TEXTAREA
        return self.page.locator(sel).first.input_value()

    def hero_description_text(self) -> str:
        return self.rich_text_value(HERO_DESCRIPTION_NAME)

    def set_hero_description_source(self, html: str) -> "UsefulLinksPageAdminPage":
        """Enters `html` through the EN editor's own "Source" mode (toolbar
        button -> source textarea -> back to WYSIWYG) — real editor input,
        and the only exact way to put a heading/bullets/link, or restore a
        captured value, without depending on toolbar menus."""
        editor = self.page.locator(self.HERO_DESCRIPTION_EN_EDITOR).first
        editor.locator("a.cke_button__source").first.click()
        # Source mode (observed live 2026-09-30) is CodeMirror inside the
        # editor's own `cke_N_contents` box. Real keyboard input into it.
        # The source view is a CodeMirror instance: focus it by clicking its
        # rendered code lines (its input <textarea> sits under them).
        source = editor.locator('[id$="_contents"] .CodeMirror-lines').first
        source.wait_for(state="visible", timeout=10000)
        source.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Delete")
        self.page.keyboard.insert_text(html)
        editor.locator("a.cke_button__source").first.click()
        self.page.frame_locator(self._hero_editor_iframe()).locator("body").wait_for(state="visible", timeout=10000)
        return self

    def clear_hero_description(self) -> "UsefulLinksPageAdminPage":
        """Select-all + Backspace inside the EN editor (real keyboard)."""
        body = self.page.frame_locator(self._hero_editor_iframe()).locator("body")
        body.wait_for(state="visible", timeout=10000)
        body.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Delete")
        return self

    def type_into_hero_description(self, text: str) -> "UsefulLinksPageAdminPage":
        body = self.page.frame_locator(self._hero_editor_iframe()).locator("body")
        body.click()
        self.page.keyboard.type(text)
        return self

    def hero_description_required_mirror(self) -> str:
        """The hidden `required` mirror input CKEditor keeps in sync — what the
        browser's required check actually evaluates for the rich text."""
        node = self.page.locator(self.HERO_DESCRIPTION_REQUIRED_MIRROR).first
        return node.input_value() if node.count() else ""

    # ---- Hero Banner ------------------------------------------------------------
    def hero_banner_file(self) -> str:
        """Name of the file currently stored on the record ("" when none)."""
        return self.current_file_name(HERO_BANNER_LABEL)

    def hero_banner_help_text(self) -> str:
        container = self._file_upload_container(HERO_BANNER_LABEL)
        node = container.locator("p", has_text="no larger than")
        return node.first.inner_text().strip() if node.count() else ""

    def upload_hero_banner(self, file_path: str) -> "UsefulLinksPageAdminPage":
        self.upload_file(HERO_BANNER_LABEL, file_path)
        return self

    def hero_banner_pending_name(self) -> str:
        """Filename readout of a NEWLY selected (not yet saved) file."""
        try:
            return self.uploaded_filename(HERO_BANNER_LABEL)
        except Exception:  # noqa: BLE001
            return ""

    def try_hero_banner_upload(self, file_path: str, timeout: float = 25.0) -> dict:
        """Drives the Documents & Media picker for `file_path` and reports
        what the picker said: {"rejection": <visible feedback or "">,
        "accepted": <"1 of 1" shown>, "added": <Add clicked and the picker
        closed>, "picker_text": ...}. Clicks Add only when the picker itself
        accepted the file; always leaves the picker closed."""
        hidden = self.page.get_by_role("textbox", name=f"{HERO_BANNER_LABEL} Select File")
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        result = {"rejection": "", "accepted": False, "added": False, "picker_text": ""}

        def _resolved() -> bool:
            rejection = self._picker_feedback(frame)
            if rejection:
                result["rejection"] = rejection
                return True
            if frame.get_by_text("1 of 1").count():
                result["accepted"] = True
                return True
            return False

        try:
            wait_until(_resolved, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        try:
            result["picker_text"] = frame.locator("body").inner_text()
        except Exception:  # noqa: BLE001
            pass
        if result["accepted"]:
            frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click(timeout=15000)
            result["added"] = self._picker_closed(15000)
            if not result["added"]:
                result["rejection"] = self._picker_feedback(frame) or result["rejection"]
        self.close_picker()
        return result

    PICKER_FEEDBACK_RE = re.compile(
        r"(valid extension|valid file size|no larger than|exceeds|too large|not supported|maximum)", re.I
    )

    def _picker_feedback(self, frame) -> str:
        for scope in (frame, self.page):
            try:
                nodes = scope.get_by_text(self.PICKER_FEEDBACK_RE)
                for i in range(min(nodes.count(), 10)):
                    node = nodes.nth(i)
                    text = " ".join((node.inner_text() or "").split())
                    # the field's own help line is not a rejection
                    if node.is_visible() and text and not text.startswith("Upload a "):
                        return text
            except Exception:  # noqa: BLE001 — frame detached mid-read
                continue
        return ""

    def close_picker(self) -> None:
        if self._picker_closed(1500):
            return
        self.page.keyboard.press("Escape")
        if self._picker_closed(4000):
            return
        for name in ("Cancel", "Close"):
            button = self.page.get_by_role("button", name=name)
            if button.count():
                try:
                    button.first.click(timeout=5000)
                    break
                except Exception:  # noqa: BLE001 — try the next label
                    continue
        if not self._picker_closed(6000):
            raise AssertionError("the Documents & Media picker would not close")

    def download_hero_banner(self, dest_dir: str) -> str:
        """Saves the currently stored banner's bytes (TEST_OWNED baseline for
        a binary restore) under its own file name in `dest_dir`."""
        name = self.hero_banner_file()
        if not name:
            return ""
        return self.download_current_file(HERO_BANNER_LABEL, os.path.join(dest_dir, name))

    # ---- Page Status picklist / Active Status --------------------------------
    def page_status(self) -> str:
        """The `pageStatus` picklist key ("draft" / "published" / "unpublished")."""
        return self.page.locator(self.PAGE_STATUS_VALUE).first.input_value()

    def select_page_status(self, option_label: str) -> "UsefulLinksPageAdminPage":
        combobox = self.page.locator(self.PAGE_STATUS_INPUT).first
        listbox_id = combobox.get_attribute("aria-controls")
        self.page.locator(f'button[aria-controls="{listbox_id}"]').click()
        choice = self.page.locator(f'[id="{listbox_id}"] [role="option"]:text-is("{option_label}")')
        choice.wait_for(state="visible", timeout=5000)
        choice.click()
        wait_until(lambda: combobox.input_value() == option_label, timeout=5.0, poll=0.2,
                   message=f"Status picklist did not take {option_label!r}")
        return self

    def active_status(self) -> bool:
        return self.page.locator('form input[name="ObjectField_activeStatus"][type="checkbox"]').first.is_checked()

    # ---- Snapshot / restore (TEST_OWNED) --------------------------------------
    def snapshot(self) -> dict:
        """Every value this batch can touch, read off a FRESH open."""
        self.open_singleton()
        snap = {}
        for field in TEXT_FIELDS:
            snap[field.key] = self.field_text(field)
            snap[field.key + "_ar"] = self.field_text(field, arabic=True)
        snap["hero_description"] = self.hero_description_html()
        snap["hero_description_ar"] = self.hero_description_html(arabic=True)
        snap["hero_banner"] = self.hero_banner_file()
        snap["page_status"] = self.page_status()
        snap["active_status"] = self.active_status()
        snap["workflow_status"] = self.current_status()
        return snap

    def text_values(self) -> dict:
        """Text-field values off the currently open form (EN + AR)."""
        out = {}
        for field in TEXT_FIELDS:
            out[field.key] = self.field_text(field)
            out[field.key + "_ar"] = self.field_text(field, arabic=True)
        return out

    def differences(self, baseline: dict) -> list[str]:
        """Keys whose stored value (fresh open) differs from `baseline`,
        comparing text fields, hero description and banner file name."""
        current = self.snapshot()
        keys = [f.key for f in TEXT_FIELDS] + [f.key + "_ar" for f in TEXT_FIELDS] + [
            "hero_description", "hero_description_ar", "hero_banner", "page_status",
        ]
        return [k for k in keys if _norm(current.get(k)) != _norm(baseline.get(k))]

    def restore_text_and_description(self, baseline: dict) -> None:
        """Puts every text field + the EN hero description back to `baseline`
        and submits (publishes) — used by finally-blocks. Only fields that
        differ are rewritten. Raises when the record does not come back."""
        diffs = self.differences(baseline)  # leaves the singleton open
        text_diffs = [k for k in diffs if k not in ("hero_banner", "page_status")]
        if not text_diffs and "page_status" not in diffs:
            return
        for field in TEXT_FIELDS:
            if field.key in text_diffs:
                self.fill_field(field, baseline[field.key])
            if field.key + "_ar" in text_diffs:
                self.fill_field(field, baseline[field.key + "_ar"], arabic=True)
        if "hero_description" in text_diffs:
            self.set_hero_description_source(baseline["hero_description"])
        if "page_status" in diffs:
            label = {"published": "Published", "draft": "Draft", "unpublished": "Unpublished"}.get(
                baseline["page_status"], baseline["page_status"])
            self.select_page_status(label)
        self.submit()
        remaining = [k for k in self.differences(baseline) if k != "hero_banner"]
        if remaining:
            raise AssertionError(f"TEST_OWNED restore incomplete on {SINGLETON_ENTRY_CODE}: {remaining}")

    def ensure_published(self, timeout: float = 120.0) -> str:
        """Leaves the singleton Published: row Publish action when the row is
        Unpublished, form submit otherwise (Draft). Returns the final status."""
        status = self.singleton_row_status()
        if status == STATUS_PUBLISHED:
            return status
        actions = self.row_actions_by_id(SINGLETON_ENTRY_ID)
        if "publish" in actions:
            self.run_row_action_by_id(SINGLETON_ENTRY_ID, "publish", "QCTEST-130702 restore")
        else:
            self.open_singleton()
            self.submit()
        try:
            wait_until(lambda: self.singleton_row_status() == STATUS_PUBLISHED,
                       timeout=timeout, poll=3.0, message="singleton never returned to Published")
        except WaitTimeoutError:
            pass
        return self.singleton_row_status()

    def unpublish_singleton(self) -> str:
        self.open_list()
        self.run_row_action_by_id(SINGLETON_ENTRY_ID, "unpublish", "QCTEST-130702 unpublish")
        return self.singleton_row_status()


class UsefulLinkCategoryAuthoring(_AuthoringBase):
    """Minimal driver for the Useful Link Category object — ONLY for records
    the calling test creates itself (QCTEST-130702- titles). The full
    category surface is the sibling admin page's; this exists so the
    page-level batch's three category-shaped cases do not edit that file."""

    # Accessible names read off the live form's ARIA snapshot (2026-09-29).
    AR = " — العربية"
    NUMBER_LABEL = "Category Number"
    EYEBROW_LABEL = "Category Eyebrow"
    TITLE_LABEL = "Category Title"
    DISPLAY_ORDER_LABEL = "Display Order"
    ACTIVE_LABEL = "Active Status"

    def __init__(self, page):
        super().__init__(page, USEFUL_LINK_CATEGORY_SLUG)

    def _box(self, label: str, role: str = "textbox"):
        return self.page.get_by_role(role, name=self.label_pattern(label)).first

    # The page's client-side list/form bootstrap status node; filling before
    # it hides lets a late form reset wipe typed values (observed live).
    BOOTSTRAP_STATUS = "[data-qc-oel-status]"

    def _wait_bootstrapped(self) -> None:
        try:
            self.page.locator(self.BOOTSTRAP_STATUS).first.wait_for(state="hidden", timeout=20000)
        except Exception:  # noqa: BLE001 — node absent on some renders
            pass

    def open_new_form(self) -> "UsefulLinkCategoryAuthoring":
        self.open_new_entry_form(locale="en")
        self._wait_bootstrapped()
        _dismiss_chatbot_launcher(self.page)
        return self

    def form_is_editable(self) -> bool:
        title = self._box(self.TITLE_LABEL)
        return title.count() == 1 and title.is_editable() and self.is_submit_enabled()

    def fill_category(self, number: str, eyebrow: str, eyebrow_ar: str, title: str,
                      title_ar: str, display_order: str, active: bool = True) -> "UsefulLinkCategoryAuthoring":
        """Fills every control, then reads each back and re-applies any value
        a late client-side form reset wiped (observed live 2026-09-30: the
        Display Order was lost -> 'No value was provided for required object
        field "displayOrder"'). At most three passes; never a sleep."""
        fills = [
            (label, role, value) for label, role, value in (
                (self.NUMBER_LABEL, "textbox", number),
                (self.EYEBROW_LABEL, "textbox", eyebrow),
                (self.EYEBROW_LABEL + self.AR, "textbox", eyebrow_ar),
                (self.TITLE_LABEL, "textbox", title),
                (self.TITLE_LABEL + self.AR, "textbox", title_ar),
                (self.DISPLAY_ORDER_LABEL, "spinbutton", display_order),
            ) if value is not None
        ]
        self._last_fills = list(fills)
        self._last_active = active
        for _ in range(3):
            for label, role, value in fills:
                box = self._box(label, role)
                if role == "spinbutton":
                    # real keystrokes: fill() on <input type=number> did not
                    # register with the form's own change tracking
                    box.click()
                    box.press("Control+a")
                    box.press("Delete")
                    self.page.keyboard.type(str(value), delay=15)
                    box.dispatch_event("change")
                else:
                    box.fill(value)
            box = self._box(self.ACTIVE_LABEL, "checkbox")
            box.check() if active else box.uncheck()
            stale = [f for f in fills if self._box(f[0], f[1]).input_value() != f[2]]
            if not stale and box.is_checked() == active:
                return self
            logger.info("category form reset wiped %s; re-applying", [f[0] for f in stale])
            fills = stale or fills
        raise AssertionError(f"category form would not hold values: {[f[0] for f in fills]}")

    def _stale_fills(self) -> list:
        return [f for f in getattr(self, "_last_fills", []) if self._box(f[0], f[1]).input_value() != f[2]]

    def _reapply_before_click(self) -> None:
        """A late client-side reset can wipe values AFTER they were verified
        (observed live: 'No value was provided for required object field
        "displayOrder"'). Re-check everything this form was given right
        before the click and re-apply what was lost."""
        stale = self._stale_fills()
        if stale:
            logger.info("re-applying %s before submit", [f[0] for f in stale])
            self.fill_category(**{"number": None, "eyebrow": None, "eyebrow_ar": None, "title": None,
                                  "title_ar": None, "display_order": None,
                                  **{self._FILL_KEYS[f[0]]: f[2] for f in stale}},
                               active=getattr(self, "_last_active", True))
        self._last_fills = []

    @property
    def _FILL_KEYS(self) -> dict:
        return {self.NUMBER_LABEL: "number", self.EYEBROW_LABEL: "eyebrow",
                self.EYEBROW_LABEL + self.AR: "eyebrow_ar", self.TITLE_LABEL: "title",
                self.TITLE_LABEL + self.AR: "title_ar", self.DISPLAY_ORDER_LABEL: "display_order"}

    def submit(self) -> "UsefulLinkCategoryAuthoring":
        self._reapply_before_click()
        return super().submit()

    def save_draft(self) -> "UsefulLinkCategoryAuthoring":
        self._reapply_before_click()
        return super().save_draft()

    def fill_title(self, title: str) -> "UsefulLinkCategoryAuthoring":
        box = self._box(self.TITLE_LABEL)
        for _ in range(3):
            box.fill(title)
            try:
                wait_until(lambda: box.input_value() == title, timeout=3.0, poll=0.3)
                return self
            except WaitTimeoutError:
                logger.info("category title wiped by a late form reset; re-applying")
        raise AssertionError("category title field would not hold the new value")

    def title_value(self) -> str:
        return self._box(self.TITLE_LABEL).input_value()

    def title_ar_value(self) -> str:
        return self._box(self.TITLE_LABEL + self.AR).input_value()

    def rows_with_exact_title(self, title: str) -> list[dict]:
        return self.page.evaluate(
            """(t) => [...document.querySelectorAll('table tbody tr')]
                .filter(r => r.querySelector('a[data-qc-oel-delete]'))
                .filter(r => r.querySelector('td') && r.querySelector('td').innerText.trim() === t)
                .map(r => ({entry_id: r.querySelector('a[data-qc-oel-delete]').getAttribute('data-qc-oel-delete'),
                            status: (r.querySelectorAll('td')[1] || {innerText: ''}).innerText.trim()}))""",
            title,
        )

    def capture_created(self, title: str) -> CreatedEntry:
        self.open_list()
        rows = self.rows_with_exact_title(title)
        if len(rows) != 1:
            raise AssertionError(f"expected exactly one row titled {title!r}, found {len(rows)}: {rows}")
        return CreatedEntry(title=title, entry_id=rows[0]["entry_id"])

    def open_created(self, entry: CreatedEntry) -> "UsefulLinkCategoryAuthoring":
        self.open_list()
        row = self._row_by_id(entry.entry_id)
        if row.count() != 1:
            raise AssertionError(f"row for {entry} is not on the list")
        href = row.get_by_role("link", name="Edit").first.get_attribute("href") or ""
        match = re.search(r"editEntry=([^&#]+)", href)
        if not match:
            raise AssertionError(f"row for {entry} has no Edit link")
        self.open_entry_by_code(match.group(1), locale="en")
        self._wait_bootstrapped()
        _dismiss_chatbot_launcher(self.page)
        return self

    def display_order_control_name(self) -> str:
        """`name` of the control the "Display Order" label resolves to on the
        open form. On the category form this should be
        `ObjectField_displayOrder`; for the Site Content Editor / Author it
        was observed live (2026-09-30) to be the relationship field
        `ObjectRelationship#C_UsefulLink#usefulLinkCategoryLinks_displayOrder`
        — the value typed there never reaches the category."""
        box = self._box(self.DISPLAY_ORDER_LABEL, "spinbutton")
        return (box.get_attribute("name") or "") if box.count() else ""

    def repair_display_order(self, entry: CreatedEntry, display_order: str) -> bool:
        """Cleanup aid for a record THIS test created: a role-created draft
        stored without a Display Order cannot be moved to the Recycle Bin
        (the trash call re-runs the object's validation). Opens exactly the
        captured row (by entry id), re-verifies its title, sets the Display
        Order and saves it as a draft again. Only ever on QCTEST- records;
        must be driven from a session whose form binds ObjectField_displayOrder."""
        if not entry.title.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to edit {entry.title!r}: not a {QCTEST_PREFIX} record")
        self.open_created(entry)
        if self.title_value() != entry.title:
            raise AssertionError(f"STOP: entry {entry.entry_id} reads {self.title_value()!r}, not {entry.title!r}")
        if self.display_order_control_name() != "ObjectField_displayOrder":
            return False
        self.fill_category(number=None, eyebrow=None, eyebrow_ar=None, title=None, title_ar=None,
                           display_order=display_order, active=True)
        self.save_draft()
        return self.save_reloaded()

    def delete_disposable(self, entry: CreatedEntry) -> bool:
        """THE ONLY DELETE PATH. Deletes exactly the captured row after
        re-verifying — immediately before the click — that the row and its
        delete link still carry the captured QCTEST-130702- title. Returns
        False (never raises) when the row is already gone; raises on any
        identity mismatch (a mismatch means STOP)."""
        # Safety contract (2026-09-30 rewrite, after the qcdev data-loss
        # incident): the row is located by its EXACT QCTEST title (never by
        # position — no .first/.nth, no loop over delete links); exactly one
        # such row must exist; its own delete link must carry the entry id
        # captured at creation AND the same title label; the title cell is
        # re-read immediately before the click; the click is on that row's
        # own link; the confirm dialog is accepted only if it names the title.
        if not entry.title.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to delete {entry.title!r}: not a {QCTEST_PREFIX} record")
        self.open_list()
        matches = self.rows_with_exact_title(entry.title)
        if not matches:
            return False
        if len(matches) != 1 or matches[0]["entry_id"] != entry.entry_id:
            raise AssertionError(
                f"STOP: title {entry.title!r} resolves to {matches}, not exactly the captured "
                f"entry {entry.entry_id} — refusing to delete; resolve by hand"
            )
        # `has=` locators are evaluated RELATIVE to each candidate row.
        title_cell = self.page.locator("td:first-child").filter(
            has_text=re.compile(rf"^\s*{re.escape(entry.title)}\s*$"))
        row = self.page.locator("table tbody tr").filter(has=title_cell).filter(
            has=self.page.locator(f'a[data-qc-oel-delete="{entry.entry_id}"]'))
        if row.count() != 1:
            raise AssertionError(f"STOP: expected one row for {entry}, found {row.count()} — refusing to delete")
        link = row.locator(f'a[data-qc-oel-delete="{entry.entry_id}"]')
        live_title = row.locator("td:first-child").inner_text().strip()
        label = link.get_attribute("data-qc-oel-label") or ""
        if live_title != entry.title or label != entry.title:
            raise AssertionError(
                f"STOP: row {entry.entry_id} reads {live_title!r} / label {label!r}, "
                f"not the captured {entry.title!r} — refusing to delete"
            )

        dialogs: list[str] = []

        def _accept(dialog):
            dialogs.append(dialog.message)
            if entry.title in dialog.message:
                dialog.accept()
            else:
                dialog.dismiss()

        _dismiss_chatbot_launcher(self.page)
        self.page.on("dialog", _accept)
        try:
            link.scroll_into_view_if_needed()
            link.click()  # a real click on THIS row's own link (no force: nothing may intercept it)
            try:
                row.wait_for(state="detached", timeout=20000)
            except Exception as exc:  # noqa: BLE001 — reported with what the page said
                refused = self._visible_texts("[data-qc-oel-delete-refused]")
                raise AssertionError(
                    f"delete of {entry} did not remove the row; dialogs seen: {dialogs!r}; "
                    f"refused: {refused!r}; banners: {self.feedback_banners()!r}"
                ) from exc
        finally:
            self.page.remove_listener("dialog", _accept)
        self.open_list()
        return self.rows_with_exact_title(entry.title) == []


class UsefulLinksPublicView(BasePage):
    """What an ANONYMOUS visitor sees on /web/qatar-chamber/useful-links.
    Must be driven on a context created with `use_auth_state=False`. The
    content is client-rendered by the fragment's main.js from the Objects'
    REST collections, so every read waits for the render to finish (the
    fragment removes its loading status node, then either fills the hero or
    hides the whole section)."""

    ROOT = "section.qc-ul"
    EYEBROW = "[data-qc-ul-eyebrow]"
    TITLE = "[data-qc-ul-title]"
    DESCRIPTION = "[data-qc-ul-desc]"
    HERO_IMG = "img[data-qc-ul-hero-img]"
    INTRO_EYEBROW = "[data-qc-ul-intro-eyebrow]"
    INTRO_HEADING = "[data-qc-ul-intro-heading]"
    INTRO_SUBTEXT = "[data-qc-ul-intro-subtext]"
    CATEGORY_TITLE = ".qc-ul-row .qc-ul-head-title"

    def open_public(self, locale: str = "en") -> "UsefulLinksPublicView":
        self.last_response = self.page.goto(web_url(PUBLIC_PATH, locale=locale),
                                             wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, web_url(PUBLIC_PATH, locale=locale))
        dismiss_overlays(self.page, grace_ms=1500)
        try:
            wait_until(self._rendered_or_hidden, timeout=30.0, poll=0.5,
                       message="useful-links fragment never finished rendering")
        except WaitTimeoutError:
            logger.warning("public useful-links render did not settle")
        return self

    def _rendered_or_hidden(self) -> bool:
        root = self.page.locator(self.ROOT)
        if root.count() == 0:
            return True
        if root.first.get_attribute("hidden") is not None:
            return True
        return bool(self._text(self.TITLE))

    def http_status(self):
        return self.last_response.status if getattr(self, "last_response", None) else None

    def _text(self, selector: str) -> str:
        node = self.page.locator(selector)
        if node.count() == 0:
            return ""
        try:
            if not node.first.is_visible():
                return ""
            return (node.first.inner_text() or "").strip()
        except Exception:  # noqa: BLE001
            return ""

    def is_content_visible(self) -> bool:
        root = self.page.locator(self.ROOT)
        return root.count() > 0 and root.first.is_visible() and bool(self._text(self.TITLE))

    def eyebrow(self) -> str:
        return self._text(self.EYEBROW)

    def title(self) -> str:
        return self._text(self.TITLE)

    def description_text(self) -> str:
        return self._text(self.DESCRIPTION)

    def hero_image_src(self) -> str:
        node = self.page.locator(self.HERO_IMG)
        return (node.first.get_attribute("src") or "") if node.count() else ""

    def intro_eyebrow(self) -> str:
        return self._text(self.INTRO_EYEBROW)

    def intro_heading(self) -> str:
        return self._text(self.INTRO_HEADING)

    def intro_subtext(self) -> str:
        return self._text(self.INTRO_SUBTEXT)

    def category_titles(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.CATEGORY_TITLE).all_inner_texts()]

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()


def _norm(value) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())

"""
cms/pages/components/disposable_object_admin.py — DisposableObjectAdminPage.

Shared base for Object Authoring admin Page Objects whose tests work ONLY on
disposable `QCTEST-<tc_id>-<short>` records (standards.md, "Destructive-
Precondition Tests Must Use Disposable Test Data"). Added 2026-10-01 for the
Phase 3 CMS batch (PBIs 130708, 130713, 130714, 130715, 131061, 131062).

It extends ObjectAuthoringPage (not edited — that file is shared) with what
those six features need in common:

  - a declarative field table (`FIELDS`), so one generic fill/read path serves
    every object and a label correction after a live read touches one line;
  - role sign-in via `config.settings.cms_role_credentials()` — never a
    hard-coded account and never TEST_USER;
  - a search-before-lookup on the paged entries list (the Chamber Events
    finding of 2026-09-30: a fresh record can land on page 2);
  - a delete guard that refuses anything not titled `QCTEST-*`.

OBJECT NAMES. Per the 2026-10-01 engineer brief ("Object-name source,
user-authorized 2026-10-01"), the Content-Admin-Guide.docx does not yet list
these objects; their names and slugs come from the live Object Authoring
sidebar. A subclass sets `SIDEBAR_LABEL` (the exact sidebar text) and `SLUG`.
Until a slug has been read live, `SLUG_CONFIRMED_LIVE` stays False and the
page refuses to navigate, so a guessed slug can never reach qcdev.

Field labels in subclasses are taken from the approved test-case titles until
read live; each FieldSpec carries `confirmed_live` for that reason.
"""

from __future__ import annotations

import re
import shutil
import time
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.utils.waits import WaitTimeoutError, wait_until
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url

AR_SUFFIX = "العربية"
DISPOSABLE_PREFIX = "QCTEST-"

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_FORM_MANAGER = "Form Manager"
ROLE_SITE_MEMBER = "Site Member"

ADMIN_HOME_EN_URL_PATH = "/en/home"


def safe_file_tag(tag: str, max_len: int = 40) -> str:
    """`tag` reduced to [A-Za-z0-9._-], without a repeated QCTEST- prefix."""
    tag = re.sub(r"[^A-Za-z0-9._-]+", "-", tag or "").strip("-.")
    while tag.upper().startswith(DISPOSABLE_PREFIX):
        tag = tag[len(DISPOSABLE_PREFIX):]
    return tag[:max_len].strip("-.")


def qctest_title(tc_id: int | str, short: str) -> str:
    """`QCTEST-<tc_id>-<short>` — the only shape a test may create."""
    return f"{DISPOSABLE_PREFIX}{tc_id}-{short}"


@dataclass(frozen=True)
class FieldSpec:
    """One form field. `kind` is text | rich | number | date | file | select
    | checkbox | url. `ref` is the Liferay object-field name (the
    `ObjectField_<ref>` DOM id), needed for rich text and dates."""

    label: str
    kind: str = "text"
    bilingual: bool = False
    required: bool = False
    ref: str | None = None
    default: str = ""
    default_ar: str = ""
    max_len: int | None = None
    confirmed_live: bool = False

    def ar_label(self) -> str:
        return f"{self.label} — {AR_SUFFIX}"


class SlugNotConfirmed(RuntimeError):
    """Raised before any navigation to an object whose slug was not read live."""


class DisposableObjectAdminPage(ObjectAuthoringPage):
    SIDEBAR_LABEL: str = ""
    SLUG: str = ""
    SLUG_CONFIRMED_LIVE: bool = False
    # Page-level configuration objects whose one published entry IS the live
    # page. Publishing a second entry may displace it, so lifecycle cases on
    # these objects are dispositioned `conditional` in the batch file.
    SINGLETON: bool = False
    TITLE_FIELD: str = ""
    ACTIVE_FIELD: str | None = "active_status"
    FIELDS: dict[str, FieldSpec] = {}

    ENTRIES_SEARCH_INPUT = 'input[placeholder^="Search entries"]'
    ENTRIES_SEARCH_TIMEOUT_MS = 20000
    ENTRIES_SEARCH_RETRY_MS = 4000

    # The refused-submit bar (OBJECT-AUTHORING-GUIDE: "a red bar listing the
    # reasons in plain words, and nothing was saved"). TODO(live): confirm the
    # container selector; the message prefix is from standards.md.
    REFUSAL_BAR = '[role="alert"], .alert-danger'
    REQUIRED_REFUSAL_TEXT = "Please complete the required fields"

    def __init__(self, page):
        super().__init__(page, self.SLUG)

    # ---- guards --------------------------------------------------------
    def _manage_url(self, edit_entry: str | None = None, locale: str | None = None) -> str:
        if not self.SLUG_CONFIRMED_LIVE or not self.SLUG:
            raise SlugNotConfirmed(
                f"{type(self).__name__}: slug for sidebar object {self.SIDEBAR_LABEL!r} "
                "has not been read from the live Object Authoring sidebar yet."
            )
        return super()._manage_url(edit_entry, locale)

    def manage_url(self) -> str:
        return self._manage_url()

    # ---- sign-in -------------------------------------------------------
    def sign_in(self, role: str) -> "DisposableObjectAdminPage":
        email, password = cms_role_credentials(role)
        CmsLoginPage(self.page).ensure_signed_in_as(
            email, password, control_panel_url(ADMIN_HOME_EN_URL_PATH)
        )
        return self

    def has_admin_toolbar(self) -> bool:
        return CmsLoginPage(self.page).has_admin_toolbar()

    def open_form(self, role: str, locale: str | None = "en") -> "DisposableObjectAdminPage":
        self.sign_in(role)
        self.open_new_entry_form(locale=locale)
        return self

    def open_list(self, role: str, locale: str | None = "en") -> "DisposableObjectAdminPage":
        self.sign_in(role)
        self.open_entries_list(locale=locale)
        return self

    # ---- paged entries list -------------------------------------------
    def filter_entries(self, text: str) -> "DisposableObjectAdminPage":
        box = self.page.locator(self.ENTRIES_SEARCH_INPUT)
        if box.count() == 0:
            return self
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{text}")').first
        waited = 0
        while True:
            box.fill(text)
            box.press("Enter")
            try:
                row.wait_for(state="visible", timeout=self.ENTRIES_SEARCH_RETRY_MS)
                return self
            except Exception:  # noqa: BLE001 — not (yet) indexed; retry within budget
                waited += self.ENTRIES_SEARCH_RETRY_MS
                if waited >= self.ENTRIES_SEARCH_TIMEOUT_MS:
                    return self

    def row_status_text(self, title: str) -> str:
        self.filter_entries(title)
        return super().row_status_text(title)

    def row_visible(self, title: str) -> bool:
        self.filter_entries(title)
        return super().row_visible(title)

    def open_entry_by_edit_link(self, title: str) -> "DisposableObjectAdminPage":
        self.filter_entries(title)
        super().open_entry_by_edit_link(title)
        return self

    def _run_row_action(self, title_or_code: str, action: str, comment: str = ""):
        self.filter_entries(title_or_code)
        return super()._run_row_action(title_or_code, action, comment)

    def row_offers_action(self, title: str, action: str) -> bool:
        self.filter_entries(title)
        return self._row_locator(title).locator(f"[{self.ROW_ACTION_ATTRS[action]}]").count() > 0

    def any_row_action_rendered(self, action: str) -> bool:
        return self.page.locator(f"[{self.ROW_ACTION_ATTRS[action]}]").count() > 0

    def submit_button_label(self) -> str:
        return self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON).first.inner_text().strip()

    # ---- fields --------------------------------------------------------
    def spec(self, key: str) -> FieldSpec:
        return self.FIELDS[key]

    def _label(self, key: str, locale: str) -> str:
        spec = self.spec(key)
        return spec.ar_label() if locale == "ar" else spec.label

    def _rich_iframe(self, key: str, locale: str) -> str:
        spec = self.spec(key)
        base = self.description_editor_iframe(spec.ref)
        return f"{base} >> nth={1 if locale == 'ar' else 0}"

    def fill(self, key: str, value: str, locale: str = "en") -> "DisposableObjectAdminPage":
        spec = self.spec(key)
        label = self._label(key, locale)
        if spec.kind == "rich":
            self.fill_iframe_editor(self._rich_iframe(key, locale), value)
        elif spec.kind == "number":
            self.page.get_by_role("spinbutton", name=self.label_pattern(label)).fill(value)
        elif spec.kind == "date":
            self._fill_date(self.date_input(key, locale), value)
        elif spec.kind == "select":
            self.select_option(key, value)
        elif spec.kind == "checkbox":
            self.set_flag(key, value not in ("", "false", "False", "0"))
        elif spec.kind == "file":
            self.upload(key, value)
        else:  # text | url
            self.page.get_by_role("textbox", name=self.label_pattern(label)).fill(value)
        return self

    def value(self, key: str, locale: str = "en") -> str:
        spec = self.spec(key)
        label = self._label(key, locale)
        if spec.kind == "rich":
            return self.iframe_editor_text(self._rich_iframe(key, locale)).strip()
        if spec.kind == "number":
            return self.page.get_by_role("spinbutton", name=self.label_pattern(label)).input_value()
        if spec.kind == "checkbox":
            return str(self.flag(key))
        if spec.kind == "select":
            return self.combobox(key).input_value()
        if spec.kind == "date":
            return self.date_input(key, locale).input_value()
        if spec.kind == "file":
            # A newly SELECTED file shows in the <strong role=textbox> readout;
            # a SAVED file does not -- on a re-opened record that readout is
            # empty and the stored file is in the `Current file:` block (read
            # live 2026-10-13 on manage-media-item / manage-newsletter:
            # strong "" vs current "card1-video-digital-launch (1) (9).png").
            return self.uploaded_filename(label) or self.current_file_name(label)
        return self.page.get_by_role("textbox", name=self.label_pattern(label)).input_value()

    def set_flag(self, key: str, checked: bool) -> "DisposableObjectAdminPage":
        box = self.page.get_by_role("checkbox", name=self.label_pattern(self.spec(key).label))
        box.check() if checked else box.uncheck()
        return self

    def flag(self, key: str) -> bool:
        return self.page.get_by_role("checkbox", name=self.label_pattern(self.spec(key).label)).is_checked()

    # ---- field resolution (2026-10-13, PBI 129388 run) ------------------
    # Live: the date controls ("Publication Date" on manage-media-item,
    # "Published Date" on manage-photo-album) are not role=textbox by that
    # name, and manage-photo-album's comboboxes have NO accessible name (their
    # aria-label is a fragment-...-select-from-list-input id). Both are found
    # through the visible <label> element instead, with bounded fallbacks --
    # never a 30 s wait on a role lookup that cannot match.
    FIELD_RESOLVE_MS = 10000
    OPTIONS_VISIBLE_MS = 8000

    def _label_element(self, label: str):
        return self.page.locator("label").filter(has_text=self.label_pattern(label))

    def _labelled_control(self, label: str, css: str, xpath_test: str):
        """The control a <label> names: its `for=` target, else the nearest
        ancestor of the label holding a `css` element (`xpath_test` is the
        same element as an XPath step)."""
        lab = self._label_element(label)
        if lab.count() == 0:
            return None
        target = lab.first.get_attribute("for")
        if target:
            loc = self.page.locator(f'[id="{target}"]')
            # A hidden `for=` target (e.g. a date picker's hidden ISO input)
            # falls through to the visible control next to the label.
            if loc.count() and loc.first.is_visible():
                return loc.first
        near = lab.first.locator(f"xpath=ancestor::*[.//{xpath_test}][1]").locator(css)
        return near.first if near.count() else None

    def _resolve(self, candidates, what: str):
        """First candidate (a zero-arg factory) that resolves to a visible
        element, polled up to FIELD_RESOLVE_MS; raises LookupError naming
        `what`."""
        end = time.monotonic() + self.FIELD_RESOLVE_MS / 1000
        while True:
            for make in candidates:
                try:
                    loc = make()
                    if loc is not None and loc.count() and loc.first.is_visible():
                        return loc.first
                except Exception:  # noqa: BLE001 -- try the next shape
                    pass
            if time.monotonic() >= end:
                raise LookupError(f"{type(self).__name__}: could not locate {what} on {self.page.url}")
            self.page.wait_for_timeout(300)

    def date_input(self, key: str, locale: str = "en"):
        spec = self.spec(key)
        label = self._label(key, locale)
        candidates = [
            lambda: self._labelled_control(label, 'input:not([type="hidden"])', "input[not(@type='hidden')]"),
            lambda: self.page.get_by_role("textbox", name=self.label_pattern(label)),
        ]
        if spec.ref:
            candidates.insert(1, lambda: self.page.locator(
                f'input[name*="{spec.ref}"]:not([type="hidden"]), '
                f'input[id*="{spec.ref}"]:not([type="hidden"])'))
        return self._resolve(candidates, f"date field {label!r}")

    @staticmethod
    def _fill_date(box, value: str) -> None:
        if (box.get_attribute("type") or "").lower() == "date":
            # A native date input only takes ISO; the field defaults are MM/DD/YYYY.
            m = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", value.strip())
            box.fill(f"{m.group(3)}-{int(m.group(1)):02d}-{int(m.group(2)):02d}" if m else value)
            return
        box.click()
        box.fill("")
        box.press_sequentially(value)
        box.press("Tab")

    def combobox(self, key: str):
        label = self.spec(key).label
        return self._resolve(
            [
                lambda: self.page.get_by_role("combobox", name=self.label_pattern(label)),
                lambda: self._labelled_control(label, '[role="combobox"]', "*[@role='combobox']"),
            ],
            f"combobox {label!r}",
        )

    def _open_options(self, combobox):
        """Opens the list unless it is already open. Live 2026-10-13
        (manage-photo-album "Event Category"): Escape does NOT close this
        list, and the toggle button TOGGLES -- so a blind second click after
        select_options() closed it and the option click hit a hidden <li>
        for 30 s."""
        listbox_id = combobox.get_attribute("aria-controls")
        toggle = self.page.locator(f'button[aria-controls="{listbox_id}"]') if listbox_id else None
        if combobox.get_attribute("aria-expanded") == "true":
            pass
        elif toggle is not None and toggle.count():
            toggle.first.click()
        else:
            combobox.click()
        if listbox_id:
            opts = self.page.locator(f'[id="{listbox_id}"] [role="option"]')
        else:
            opts = self.page.locator('[role="listbox"]:visible [role="option"]')
        try:
            opts.first.wait_for(state="visible", timeout=self.OPTIONS_VISIBLE_MS)
        except Exception:  # noqa: BLE001 -- the caller reports what IS there
            pass
        return opts

    @staticmethod
    def _norm(text: str) -> str:
        return " ".join((text or "").split()).casefold()

    def select_option(self, key: str, option_label: str) -> "DisposableObjectAdminPage":
        """Exact match (whitespace-normalized, case-insensitive) first, then
        contains; a miss raises with the options that WERE listed."""
        opts = self._open_options(self.combobox(key))
        texts = [t.strip() for t in opts.all_inner_texts()]
        want = self._norm(option_label)
        pick = next((i for i, t in enumerate(texts) if self._norm(t) == want), None)
        if pick is None:
            pick = next((i for i, t in enumerate(texts) if want and want in self._norm(t)), None)
        if pick is None:
            self._close_options(self.combobox(key))
            raise LookupError(
                f"{self.spec(key).label!r}: no option matching {option_label!r}; available: {texts}"
            )
        chosen = texts[pick]
        opts.nth(pick).click(timeout=10000)
        # Live 2026-10-13 (manage-photo-album): the option click intermittently
        # leaves the combobox EMPTY. Verified by read-back, re-picked once.
        combobox = self.combobox(key)
        if self._norm(combobox.input_value()) != self._norm(chosen):
            self._open_options(combobox).nth(pick).click(timeout=10000)
            got = self.combobox(key).input_value()
            if self._norm(got) != self._norm(chosen):
                raise LookupError(f"{self.spec(key).label!r}: picked {chosen!r} but the field reads {got!r}")
        return self

    def select_options(self, key: str) -> list[str]:
        combobox = self.combobox(key)
        opts = self._open_options(combobox)
        texts = [t.strip() for t in opts.all_inner_texts()]
        self._close_options(combobox)
        return texts

    def _close_options(self, combobox) -> None:
        """Escape first; when the list is still expanded (this surface ignores
        Escape), its own toggle closes it."""
        self.page.keyboard.press("Escape")
        if combobox.get_attribute("aria-expanded") != "true":
            return
        listbox_id = combobox.get_attribute("aria-controls")
        toggle = self.page.locator(f'button[aria-controls="{listbox_id}"]') if listbox_id else None
        if toggle is not None and toggle.count():
            toggle.first.click()

    def upload(self, key: str, fixture_path: str, tag: str = "") -> "DisposableObjectAdminPage":
        """Uploads a uniquely named QCTEST copy: re-uploading an existing
        Documents & Media file name fails instead of versioning (Chamber
        Events, 2026-09-30), and D&M deletion is not approved, so every copy
        must be recognisable as test data."""
        self.upload_file(self.spec(key).label, self.disposable_copy(fixture_path, tag))
        return self

    def upload_rejected(self, key: str, fixture_path: str, tag: str = "") -> bool:
        return self.upload_file_expect_rejected(self.spec(key).label, self.disposable_copy(fixture_path, tag))

    @staticmethod
    def disposable_copy(fixture_path: str, tag: str = "") -> str:
        """The tag only names the FILE, so it is reduced to filename-safe
        characters (2026-10-13: an XSS-payload tag "<script>alert(1)</script>"
        was an invalid Windows path). A payload belongs in the field value."""
        src = Path(fixture_path)
        tag = safe_file_tag(tag)
        name = f"{DISPOSABLE_PREFIX}{tag + '-' if tag else ''}{uuid.uuid4().hex[:10]}{src.suffix}"
        dest = Path(tempfile.gettempdir()) / name
        shutil.copy(src, dest)
        return str(dest)

    def field_present(self, key: str) -> bool:
        spec = self.spec(key)
        if spec.kind == "rich":
            return self.page.locator(self._rich_iframe(key, "en")).count() > 0
        if spec.kind == "file":
            return self.page.get_by_role("textbox", name=f"{spec.label} Select File").count() > 0
        if spec.kind in ("date", "select"):
            try:
                self.date_input(key) if spec.kind == "date" else self.combobox(key)
                return True
            except LookupError:
                return False
        role = {"number": "spinbutton", "checkbox": "checkbox", "select": "combobox"}.get(spec.kind, "textbox")
        return self.page.get_by_role(role, name=self.label_pattern(spec.label)).count() > 0

    def max_length_attr(self, key: str, locale: str = "en") -> int | None:
        raw = self.page.get_by_role(
            "textbox", name=self.label_pattern(self._label(key, locale))
        ).get_attribute("maxlength")
        return int(raw) if raw and raw.isdigit() else None

    # ---- composite fills ---------------------------------------------
    def fill_required(
        self,
        title: str,
        skip: tuple[str, ...] = (),
        active: bool = False,
        files: dict[str, str] | None = None,
    ) -> "DisposableObjectAdminPage":
        """Fill every required field with its declared valid default, the
        title field with `title`, except the keys in `skip` — so a case about
        one field can isolate it. `files` maps file-field keys to fixtures.
        Ticks Active Status only when `active` (it defaults UNTICKED and is
        the second visibility gate)."""
        files = files or {}
        for key, spec in self.FIELDS.items():
            if key in skip or not spec.required:
                continue
            if key == self.TITLE_FIELD:
                self.fill(key, title)
                if spec.bilingual:
                    self.fill(key, f"{title} AR", locale="ar")
                continue
            if spec.kind == "file":
                if key in files:
                    self.upload(key, files[key], tag=title)
                continue
            if spec.kind == "select" and not spec.default:
                # No fixed value is known (e.g. a category list): take the first
                # option the form offers. Selecting an existing option only
                # links the QCTEST record to it; nothing on that option changes.
                options = self.select_options(key)
                if options:
                    self.select_option(key, options[0])
                continue
            self.fill(key, spec.default)
            if spec.bilingual:
                self.fill(key, spec.default_ar or spec.default, locale="ar")
        if self.ACTIVE_FIELD and self.ACTIVE_FIELD in self.FIELDS and self.ACTIVE_FIELD not in skip:
            self.set_flag(self.ACTIVE_FIELD, active)
        return self

    # ---- outcomes -------------------------------------------------------
    def _refusal_messages(self) -> list[str]:
        """Non-empty texts of the VISIBLE refusal elements.

        CORRECTED 2026-10-13 (live, manage-media-item): every fragment text /
        file input renders an always-present `<span role="alert">` error slot
        that is EMPTY until a validation message is written into it. Matching
        `[role="alert"]` by visibility alone read those blank slots as a
        refusal -- "validation refused a valid item: '   '" on a save that had
        succeeded. Only an element carrying text counts."""
        bar = self.page.locator(self.REFUSAL_BAR)
        out = []
        for i in range(bar.count()):
            el = bar.nth(i)
            try:
                text = " ".join((el.inner_text(timeout=2000) or "").split())
                if text and el.is_visible():
                    out.append(text)
            except Exception:  # noqa: BLE001 -- detached between count and read
                continue
        # Live 2026-10-13: a required-field refusal renders as the plain
        # "Please complete the required fields ... Nothing has been submitted."
        # message, which the bar selector above does not match.
        required = self.page.get_by_text(self.REQUIRED_REFUSAL_TEXT)
        for i in range(required.count()):
            try:
                if required.nth(i).is_visible():
                    out.append(" ".join(required.nth(i).inner_text(timeout=2000).split()))
            except Exception:  # noqa: BLE001
                continue
        return out

    def refusal_visible(self, timeout_ms: int = 5000) -> bool:
        def _seen() -> bool:
            return bool(self._refusal_messages())

        try:
            wait_until(_seen, timeout=timeout_ms / 1000, poll=0.3)
            return True
        except WaitTimeoutError:
            return False

    def refusal_text(self) -> str:
        return " | ".join(self._refusal_messages())

    def field_error_text(self, key: str, locale: str = "en") -> str:
        """Inline error under a field (e.g. "This field is required.").
        TODO(live): confirm the feedback element; Clay renders it as
        `.form-feedback-item` inside the field's `.form-group`."""
        label = self._label(key, locale)
        box = self.page.get_by_role("textbox", name=self.label_pattern(label))
        group = box.locator("xpath=ancestor::*[contains(@class,'form-group')][1]")
        fb = group.locator(".form-feedback-item, .form-feedback-group")
        return " ".join(t.strip() for t in fb.all_inner_texts()) if fb.count() else ""

    def status_of(self, title: str, role: str) -> str:
        self.open_list(role)
        return self.row_status_text(title)

    def entry_exists(self, title: str, role: str) -> bool:
        self.open_list(role)
        return self.row_visible(title)

    # ---- teardown ------------------------------------------------------
    def delete_disposable(self, title: str, role: str = ROLE_EDITOR) -> bool:
        """Delete by EXACT title, never by position, and only a QCTEST record.
        Never raises — teardown must not mask the test's own result."""
        if not title.startswith(DISPOSABLE_PREFIX):
            raise ValueError(f"refusing to delete non-disposable record {title!r}")
        try:
            self.open_list(role)
            self.filter_entries(title)
            row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
            if row.count() != 1:
                return False
            return self.delete_entry_by_title(title)
        except Exception:  # noqa: BLE001
            return False


def chars(n: int, seed: str = "Q") -> str:
    """A deterministic n-character string for boundary cases."""
    return (seed * n)[:n]


_WS = re.compile(r"\s+")


def squash(text: str) -> str:
    return _WS.sub(" ", text or "").strip()

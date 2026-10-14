"""
cms/tests/about_qatar_chamber/about_helpers.py -- the About Qatar Chamber
test module's own helpers (PBI 129392).

WHY THIS FILE EXISTS (2026-10-12)
---------------------------------
test_about_qatar_chamber_control_panel.py imported its helpers from the
Chamber's Law TEST modules (test_chambers_law_control_panel.py and its sibling).
That made About's collection depend on another feature's test file: when
`_create_hero` / `_hero_key` / `_hero_reset` / `_open_hero` were not there,
the whole About module failed to import (ImportError at collection). Those
four never existed in chambers_law at all, so they are written here; the
rest are copied from chambers_law and trimmed to what About calls.
No test module may import another test module.

Raw Playwright stays inside `_FormProbe` (a read-only probe of the form the
Page Object has open) -- the same contract BasePage / ObjectAuthoringPage hold.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import allure

from cms.pages.about_qatar_chamber.about_qatar_chamber_admin_page import HERO_BANNER_SLUG
from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.tests.live_write_guard import deletes_suppressed, refuse_hero_create
from config.settings import cms_role_credentials
from core.utils.waits import wait_until
from core.web.browser import new_context

DISPOSABLE_PREFIX = "QCTEST-"
HERO_LISTED_TIMEOUT = 30.0
FIXTURE_DIR = Path(tempfile.gettempdir()) / "qc_about_qatar_chamber_fixtures"


# ---- reporting / fixtures / sessions ---------------------------------------
def _attach(name: str, body) -> None:
    try:
        allure.attach(body if isinstance(body, str) else repr(body), name=name)
    except Exception:  # noqa: BLE001 -- reporting must never mask anything
        pass


def _fixture(name: str, maker, size: int) -> str:
    """A generated upload file of exactly `size` bytes (reused when present)."""
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    path = FIXTURE_DIR / name
    if not path.exists() or path.stat().st_size != size:
        path.write_bytes(maker(size))
    return str(path)


def _role_session(browser, role: str):
    """A FRESH context signed in as `role` -- never the TEST_USER page, and
    never a saved role storageState. Callers open it BEFORE any mutation, so
    a failed login can never strand a record mid-workflow."""
    context = new_context(browser, use_auth_state=False)
    role_page = context.new_page()
    email, password = cms_role_credentials(role)
    CmsLoginPage(role_page).open_login().login(email, password)
    return context, role_page


# ---- form probe (read-only) -------------------------------------------------
# The SIZE-feedback wording family (live literal: "Please enter a file with a
# valid file size no larger than 2 MB."). The field's always-visible help line
# does not contain "valid file size", so it can never read as a rejection.
SIZE_REJECTION_RE = re.compile(
    r"valid\s+file\s+size\s+no\s+larger\s+than\s*[0-9]+(?:[.,][0-9]+)?\s*MB",
    re.IGNORECASE,
)


class _FormProbe:
    """Reads what the Object Authoring form / D&M picker is SAYING. Copied
    from cms/tests/chambers_law/law_entry_form.py's `_LawEntryForm`, limited
    to the readers About uses. Never writes."""

    # The page's own `banner()` helper renders both the editing banner and
    # every save message as `[data-qc-oel-editbar]` -- matched on TEXT.
    EDIT_BAR = "[data-qc-oel-editbar]"
    FIELD_ERROR_NOTE = "[data-qc-oel-field-error]"
    FRAGMENT_ERROR_NOTE = 'p[id$="-error"].text-danger:not(.sr-only)'
    SAVE_REFUSED_PREFIXES = ("This record was not saved:", "لم يتم حفظ هذا السجل:")
    PUBLISHED_MESSAGES = (
        "Saved and submitted for review.",
        "Saved and submitted for publishing.",  # pre-2026-09-28 wording
        "تم الحفظ وإرساله للنشر.",
    )
    DRAFT_SAVED_MESSAGES = ("Draft saved.", "تم حفظ المسودة.")
    PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'
    SIZE_FEEDBACK_ATTR_TOKEN = "size"
    _COLLECT_FEEDBACK_JS = """
    (root) => {
      const doc = root.ownerDocument || root;
      const out = [];
      for (const el of doc.querySelectorAll('*')) {
        for (const attr of el.attributes) {
          if (!attr.name.endsWith('-feedback')) continue;
          const value = (attr.value || '').trim();
          if (value.length > 10) out.push([attr.name, value]);
        }
      }
      return out;
    }
    """

    def __init__(self, authoring):
        self._authoring = authoring
        self._page = authoring.page

    # ---- save messages ----------------------------------------------------
    def _visible_texts(self, selector: str) -> list:
        found = self._page.locator(selector)
        out = []
        for index in range(found.count()):
            element = found.nth(index)
            try:
                if not element.is_visible():
                    continue
                text = (element.inner_text() or "").strip()
            except Exception:  # noqa: BLE001 -- a node that vanished mid-read
                continue
            if text:
                out.append(text)
        return out

    def _bar_texts(self) -> list:
        bars = self._page.locator(self.EDIT_BAR)
        return [bars.nth(i).inner_text() for i in range(bars.count())]

    def field_error_texts(self) -> tuple:
        return tuple(self._visible_texts(self.FIELD_ERROR_NOTE))

    def fragment_error_texts(self) -> tuple:
        return tuple(self._visible_texts(self.FRAGMENT_ERROR_NOTE))

    def refusal_bar_text(self) -> str:
        for text in self._bar_texts():
            if any(prefix in text for prefix in self.SAVE_REFUSED_PREFIXES):
                return text
        return ""

    def save_refusal_text(self) -> str:
        """Everything the page says about why a save did not go through --
        under-the-box notes, fragment notes, then the red bar -- or ""."""
        parts = list(self.field_error_texts()) + list(self.fragment_error_texts())
        bar = self.refusal_bar_text()
        if bar:
            parts.append(bar)
        return " | ".join(parts)

    def success_message_text(self) -> str:
        wanted = self.PUBLISHED_MESSAGES + self.DRAFT_SAVED_MESSAGES
        for text in self._bar_texts():
            if any(message in text for message in wanted):
                return text
        return ""

    def attachment_validation_message(self, field_label: str) -> str:
        """The browser's own constraint message for an attachment field's
        hidden "<Field Label> Select File" control, "" when valid."""
        return self._page.get_by_role("textbox", name=f"{field_label} Select File").evaluate(
            "el => el.validity && !el.validity.valid ? (el.validationMessage || 'invalid') : ''"
        )

    # ---- upload rejection detectors ----------------------------------------
    def _scopes(self, frame=None):
        return [scope for scope in (frame, self._page) if scope is not None]

    def _declared_feedback(self, frame=None):
        pairs = []
        for scope in self._scopes(frame):
            try:
                pairs.extend(scope.locator("body").evaluate(self._COLLECT_FEEDBACK_JS))
            except Exception:  # noqa: BLE001 -- a detached frame reads as none
                continue
        return [(str(name), str(value)) for name, value in pairs]

    def declared_size_feedback(self, frame=None) -> str:
        for name, value in self._declared_feedback(frame):
            if self.SIZE_FEEDBACK_ATTR_TOKEN in name:
                return value
        return ""

    def _visible_text(self, scope, needle) -> str:
        try:
            nodes = scope.get_by_text(needle)
            count = min(nodes.count(), 10)
        except Exception:  # noqa: BLE001 -- the iframe can detach mid-read
            return ""
        for index in range(count):
            node = nodes.nth(index)
            try:
                if node.is_visible():
                    return " ".join(node.inner_text().split())
            except Exception:  # noqa: BLE001 -- try the next candidate
                continue
        return ""

    def size_rejection_text(self, frame=None) -> str:
        for scope in self._scopes(frame):
            text = self._visible_text(scope, SIZE_REJECTION_RE)
            if text:
                return text
        declared = self.declared_size_feedback(frame)
        if declared:
            for scope in self._scopes(frame):
                text = self._visible_text(scope, declared)
                if text:
                    return text
        return ""

    def declared_rejection_text(self, frame=None) -> str:
        for _name, value in self._declared_feedback(frame):
            for scope in self._scopes(frame):
                text = self._visible_text(scope, value)
                if text:
                    return text
        return ""

    def picker_body_text(self) -> str:
        """REPORT ONLY -- never a rejection signal."""
        try:
            return self._page.frame_locator(self.PICKER_IFRAME).locator("body").inner_text()
        except Exception:  # noqa: BLE001
            return ""

    def _picker_closed(self, timeout: int) -> bool:
        try:
            self._page.locator(self.PICKER_IFRAME).wait_for(state="detached", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001 -- caller decides what to do next
            return False

    def close_picker(self) -> None:
        if self._picker_closed(1500):
            return
        try:
            self._page.keyboard.press("Escape")
        except Exception:  # noqa: BLE001
            pass
        if self._picker_closed(4000):
            return
        for name in ("Cancel", "Close"):
            try:
                button = self._page.get_by_role("button", name=name)
                if button.count():
                    button.first.click(timeout=5000)
                    break
            except Exception:  # noqa: BLE001 -- try the next candidate label
                continue
        if not self._picker_closed(6000):
            raise AssertionError(
                "the Documents & Media picker would not close -- a still-open modal "
                "overlays the form's Save/Publish buttons"
            )


# ---- save / upload actions ---------------------------------------------------
def _publish_edit(admin, authoring) -> dict:
    """Clicks the record's Publish control (status=0) and captures what the
    page said, BEFORE anything navigates away."""
    probe = _FormProbe(authoring)
    authoring.submit_via(admin.PUBLISH_SUBMIT)
    return {
        "refusal": probe.save_refusal_text(),
        "success": probe.success_message_text(),
        "url": admin.page.url,
    }


_UPLOAD_COMPLAINT = re.compile(r"valid (file )?extension|valid file size|بملحق|ملحق|حجم", re.I)
_UPLOAD_SIZE_COMPLAINT = re.compile(r"valid file size|حجم", re.I)


def _attempt_upload(admin, authoring, field_name: str, file_path: str, size_only: bool = False) -> dict:
    """Drives the D&M picker with one file and reports what was said about it.
    Add is never clicked, so nothing can be attached or persisted."""
    probe = _FormProbe(authoring)
    frame = admin.open_file_picker(field_name)
    admin.picker_set_file(frame, file_path)
    reader = probe.size_rejection_text if size_only else probe.declared_rejection_text
    pattern = _UPLOAD_SIZE_COMPLAINT if size_only else _UPLOAD_COMPLAINT
    seen = {"rejection": "", "accepted": False, "form_rejection": ""}

    def _resolved() -> bool:
        seen["rejection"] = reader(frame) or probe._visible_text(frame, pattern) or seen["rejection"]
        if seen["rejection"]:
            return True
        if admin.picker_reports_uploaded(frame):
            seen["accepted"] = True
            return True
        return False

    try:
        wait_until(_resolved, timeout=25, poll=1.0)
    except Exception:  # noqa: BLE001 -- "neither" is itself the result
        pass
    seen["picker_text"] = probe.picker_body_text()
    probe.close_picker()
    seen["rejected"] = bool(seen["rejection"])
    return seen


# ---- disposable AboutHeroBanner rows (QCTEST-<tc>-HERO) -----------------------
def _hero_key(tc: str) -> str:
    return f"{DISPOSABLE_PREFIX}{tc}-HERO"


def _require_disposable(key: str) -> None:
    if not key.startswith(DISPOSABLE_PREFIX):
        raise ValueError(f"refusing to touch non-disposable About Hero Banner row {key!r}")


def _hero_listed(admin, key: str, timeout: float = HERO_LISTED_TIMEOUT) -> bool:
    """True once a row whose Entry cell is EXACTLY `key` is on the list."""
    def _present() -> bool:
        admin.open_hero_entries_list("en")
        return bool(admin.hero_entry_code_exact(key))

    try:
        wait_until(_present, timeout=timeout, poll=5)
        return True
    except Exception:  # noqa: BLE001 -- not listed is itself the result
        return False


def _hero_reset(admin, key: str, tc: str = "") -> int:
    """Deletes every row carrying the disposable `key` -- QCTEST namespace
    only, matched on the key itself, never by position. Never raises: a
    teardown must not mask the test's own result."""
    _require_disposable(key)
    if deletes_suppressed():
        # User decision 2026-10-13: nothing is deleted under the opt-in. No
        # QCTEST hero row can be created any more (_create_hero always stops
        # first -- refuse_hero_create), so there is nothing to keep or log.
        _attach(f"hero cleanup skipped ({tc or key})", "deletes suppressed (QC_ALLOW_LIVE_SINGLETON_WRITES=1)")
        return 0
    try:
        removed = ObjectAuthoringPage(admin.page, slug=HERO_BANNER_SLUG).delete_all_entries_by_title(
            key, max_rows=3)
    except Exception as exc:  # noqa: BLE001
        _attach(f"hero cleanup failed ({tc or key})", repr(exc))
        return 0
    if removed:
        _attach(f"hero cleanup ({tc or key})", f"deleted {removed} row(s) {key!r}")
    return removed


def _open_hero(admin, key: str, locale: str = "en"):
    """The disposable row `key`, opened for edit by its own editEntry code."""
    _require_disposable(key)
    admin.open_hero_entries_list("en")
    code = admin.hero_entry_code_exact(key)
    if not code:
        raise AssertionError(f"no About Hero Banner row with Page Key {key!r}")
    return admin.open_hero_record(code, locale=locale)


def _create_hero(admin, key: str, image_path: str | None, alt: str) -> dict:
    """Creates the disposable hero row `key` through the CREATE form and
    clicks Publish. Returns what the page said plus `listed` (row present).

    Singleton manage-page trap (incident 183176): a manage page that renders
    no create form opens a LIVE record instead. Nothing is typed unless the
    page is provably an empty create form -- no editEntry, no "Editing ..."
    banner, an empty visible Page Key."""
    _require_disposable(key)
    _hero_reset(admin, key, "sweep before create")  # leftover from a killed run
    # User decision 2026-10-13: AboutHeroBanner holds one row per page and
    # its create form is hidden, so the QCTEST create path is NOT APPLICABLE
    # whatever QC_ALLOW_LIVE_SINGLETON_WRITES says (refuse_hero_create never
    # opens -- carrying on would type into the LIVE row, incident 183176). A
    # case that needs a saved hero row runs on the REAL row instead. The
    # disposable path below runs only when a genuine, empty create form is there.
    hero_desc = "About Hero Banner (one row per page; no visible empty create form for a QCTEST row)"
    try:
        authoring = admin.open_new_hero_form(locale="en")
    except Exception as exc:  # noqa: BLE001
        refuse_hero_create(hero_desc, f"create form did not render: {exc!r}")
    if not admin.hero_create_form_usable():
        refuse_hero_create(hero_desc, f"url {admin.page.url} is not an EMPTY create form")
    admin.fill_hero_page_key(key)
    if image_path:
        authoring.upload_file(admin.HERO_IMAGE_UPLOAD_LABEL, image_path)
    admin.fill_hero_alt_text(alt)
    said = _publish_edit(admin, authoring)
    said["listed"] = _hero_listed(admin, key)
    return said

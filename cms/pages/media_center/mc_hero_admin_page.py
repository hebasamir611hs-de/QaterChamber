"""
cms/pages/media_center/mc_hero_admin_page.py — Media Center Hero (PBI 130709).

Control_Panel Page Object for the singleton Object Authoring page
`/web/qatar-chamber/manage-media-center-hero` plus a read-only view of the
public hero on `/web/qatar-chamber/media-center`.

LIVE RECON 2026-10-07 (QC Site Content Editor 156488, read-only; one Publish
click was intercepted and ABORTED at the network layer to read the payload —
nothing was saved):

  - The page holds ONE record: entry id 206354, ERC QCDEMO-130709-HERO-MAIN,
    ENTRY column "Media Center", badge PUBLISHED. The row carries NO delete
    link. The edit bar says "This page holds this one record only." The
    preview panel reads "Field view (no page renders this Object)".
  - Fields (EN `ObjectField_<key>`, AR twin `#qc-ar-<key>`):
      pageLabel* (counter "n / 60", AR required)
      heroHeadline* (counter "n / 150", AR required)
      heroDescription (rich text, label shows "Required"; CKEditor instances
        `fragment-…-ObjectField_heroDescription` and `qc-ar-heroDescription`)
      heroBackgroundImage (upload, help "Upload a .jpg,.jpeg,.png no larger
        than 2 MB.", block "Current file: media-center-hero-background.jpeg
        (544 KB) … Remove file")
      searchPlaceholder* (counter "n / 100", AR required)
      activeStatus (checkbox)
    No native `maxlength` on any text input (maxLength -1) — the limit is
    shown by the counter only.
  - Editor buttons on the published record: "Publish" ("As an Editor, what
    you publish here goes live straight away.") and "Unpublish to edit as
    draft" (never used here).
  - Publish sends ONE `PUT /o/c/mediacenterheros/206354` carrying the WHOLE
    record (JSON). The rich text is sent as CKEditor's getData() — i.e.
    wrapped in "<p>…</p>\\n" — while the stored seed value is plain text, so a
    UI save can never reproduce the seed bytes of heroDescription. That is why
    `restore_exact()` re-sends the snapshot body through the very same
    endpoint the authoring page itself calls (Editor session, lock held).
  - Read-only record state: `GET /o/c/mediacenterheros/scopes/37246/by-
    external-reference-code/QCDEMO-130709-HERO-MAIN?nestedFields=…` (Editor
    session; anonymous gets 403).
  - Public hero (fragment `qc-mc-hero`, data loaded client-side from
    /o/c/mediacenterheros): h1.qc-mc-hero-pagetitle (Page Label),
    p.qc-mc-hero-headline, .qc-mc-hero-desc, input#qc-mc-hero-q (placeholder),
    div.qc-mc-hero-bg (inline background-image url with the file name),
    section[data-qc-mch-ready="true"] once rendered.

SAFETY: every write requires the HERO lock (scratchpad lock file) to be held
by this process; delete / unpublish / bulk helpers inherited from the tender
Page Object are disabled.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import time
from datetime import datetime

from cms.pages.tenders.tender_admin_page import TenderWorkflowAdminPage
from config.settings import PROJECT_ROOT, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays

logger = get_logger("mc_hero_admin_page")

SLUG = "media-center-hero"
HERO_ERC = "QCDEMO-130709-HERO-MAIN"
HERO_ID = "206354"
SCOPE_ID = "37246"
HERO_API = f"/o/c/mediacenterheros/scopes/{SCOPE_ID}/by-external-reference-code/{HERO_ERC}?nestedFields=heroBackgroundImage"
HERO_PUT = f"/o/c/mediacenterheros/{HERO_ID}"

K_LABEL = "pageLabel"
K_HEADLINE = "heroHeadline"
K_DESC = "heroDescription"
K_IMAGE = "heroBackgroundImage"
K_SEARCH = "searchPlaceholder"
IMAGE_LABEL = "Hero Background Image"
TEXT_KEYS = (K_LABEL, K_HEADLINE, K_SEARCH)

ROLE_EDITOR = "Site Content Editor"
ROLE_MEMBER = "Site Member"
EDITOR_USER_ID = "156488"
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_REQUIRED_BLOCK = "Please complete the required fields"
MSG_ACCESS_DENIED = "Access Denied. You do not have permission to perform this action."
MSG_FILE_INVALID_EN = "Unsupported file type or size."
MSG_FILE_INVALID_AR = "نوع الملف أو حجمه غير مدعوم."
MSG_ARABIC_REQUIRED = "Arabic content is required."

PUBLIC_PATH = "/web/qatar-chamber/media-center"
EVIDENCE_ROOT = os.path.join(str(PROJECT_ROOT), "reports", "mc130709", "HERO")

# Keys of the API body that the authoring page itself sends on Publish (captured live).
_PUT_KEYS = ("defaultLanguageId", "externalReferenceCode", "friendlyUrlPath", "friendlyUrlPath_i18n", "id",
             "keywords", "objectEntryFolderExternalReferenceCode", "objectEntryFolderId", "scopeId", "scopeKey",
             "systemProperties", "taxonomyCategoryBriefs", "heroDescription", "searchPlaceholder", "pageStatus",
             "activeStatus", "heroHeadline", "pageLabel_i18n", "heroDescription_i18n", "heroBackgroundImage",
             "searchPlaceholder_i18n", "heroHeadline_i18n", "pageLabel")
# Volatile keys never compared (they change on any save by design).
VOLATILE_KEYS = ("dateModified", "actions", "creator", "dateCreated")

_LOCK_DIR = os.getenv(
    "QC_MC_HERO_SCRATCH_DIR",
    r"C:\Users\HP\AppData\Local\Temp\claude\d--Qatar-Chamber-QaterChamber-main"
    r"\de2eae66-6f02-4a22-8869-a22476b25d22\scratchpad",
)
HERO_LOCK = os.path.join(_LOCK_DIR, "locks", "mc_hero_206354.lock")


# ---------------------------------------------------------------------------
# Lock
# ---------------------------------------------------------------------------
class HeroLock:
    def __init__(self):
        self.token = f"HERO {datetime.now().isoformat(timespec='seconds')} pid={os.getpid()}"
        self.held = False

    def try_acquire(self) -> bool:
        os.makedirs(os.path.dirname(HERO_LOCK), exist_ok=True)
        try:
            fd = os.open(HERO_LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return False
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(self.token)
        self.held = True
        return True

    def still_mine(self) -> bool:
        try:
            with open(HERO_LOCK, encoding="utf-8") as handle:
                return self.held and handle.read().strip() == self.token
        except OSError:
            return False

    def release(self) -> None:
        if self.still_mine():
            os.remove(HERO_LOCK)
        self.held = False


@contextlib.contextmanager
def hero_lock(timeout_s: float = 900.0):
    lock = HeroLock()
    try:
        wait_until(lock.try_acquire, timeout=timeout_s, poll=3.0)
    except WaitTimeoutError:
        raise TimeoutError(f"{HERO_LOCK} still held after {timeout_s:.0f}s") from None
    try:
        yield lock
    finally:
        lock.release()


def comparable(record: dict) -> dict:
    """The record minus volatile keys (dateModified etc.)."""
    return {k: v for k, v in record.items() if k not in VOLATILE_KEYS}


def record_diff(before: dict, after: dict) -> list[str]:
    a, b = comparable(before), comparable(after)
    return [f"{k}: {json.dumps(a.get(k), ensure_ascii=False)} -> {json.dumps(b.get(k), ensure_ascii=False)}"
            for k in sorted(set(a) | set(b)) if a.get(k) != b.get(k)]


# ---------------------------------------------------------------------------
# Admin page
# ---------------------------------------------------------------------------
class MCHeroAdminPage(TenderWorkflowAdminPage):
    FORM = 'form:has([name^="ObjectField_"])'
    SAVE_REQUEST_PATTERN = re.compile(r"/o/c/mediacenterheros")
    REMOVE_FILE_BUTTON = re.compile(r"^\s*(Remove file|إزالة الملف)\s*$")
    # Live 2026-10-07: the Arabic admin UI labels the buttons نشر (Publish) and
    # إختر مجلّد (Select File); the picker's Add button is matched in both UIs.
    SUBMIT_NAME = re.compile(r"^\s*(Publish|Submit for Review|نشر)\s*$")
    UPLOAD_MODAL_ADD_BUTTON_TEXT = re.compile(r"^\s*(Add|إضافة|أضف)\s*$")
    _CKE_NAME_JS = """([key, arabic]) => {
        if (!window.CKEDITOR) return '';
        const names = Object.keys(CKEDITOR.instances);
        return names.find(n => arabic ? n === 'qc-ar-' + key : n.endsWith('-ObjectField_' + key)) || '';
    }"""

    def __init__(self, page, lock: HeroLock | None = None):
        super().__init__(page)
        self.slug = SLUG
        self.lock = lock
        self.EVIDENCE_DIR = EVIDENCE_ROOT

    # ---- guards -----------------------------------------------------------
    def _require_lock(self) -> None:
        if self.lock is None or not self.lock.still_mine():
            raise PermissionError("refusing to change the hero without holding the HERO lock")

    def _guard_form(self) -> None:
        self._require_lock()
        if self._entry_code != HERO_ERC:
            raise AssertionError("the open form is not QCDEMO-130709-HERO-MAIN")

    # ---- session ------------------------------------------------------------
    # qcdev drops sessions under load (core/web/session_guard.py). The shared
    # guard re-authenticates as the super-admin TEST_USER, which would silently
    # change WHO edits the hero (and invalidate a site-member access check).
    # This Page Object therefore re-logs in as ITS OWN role instead.
    def login_as_role(self, role: str) -> str:  # type: ignore[override]
        outcome = super().login_as_role(role)
        if outcome == "ok":
            self.role = role
            self.expected_uid = self._uid()
        return outcome

    def _uid(self) -> str:
        """Signed-in user id; tolerant of a late redirect still in flight."""
        for _ in range(6):
            try:
                self.page.wait_for_function("() => window.Liferay && Liferay.ThemeDisplay", timeout=20000)
                return self.signed_in_user()[0]
            except Exception as exc:  # noqa: BLE001 — navigation in flight; retried
                logger.info("uid read retried: %r", exc)
                try:
                    self.page.wait_for_load_state("domcontentloaded", timeout=10000)
                except Exception:  # noqa: BLE001
                    pass
        return ""

    def open(self, url: str) -> None:  # type: ignore[override]
        from core.web.license_gate import clear_license_gate, remember_target  # noqa: PLC0415
        role = getattr(self, "role", None)
        for attempt in range(1, 4):
            remember_target(self.page, url)
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            clear_license_gate(self.page, url)
            if not role or "/c/portal/" in url:
                break
            if self._uid() == self.expected_uid:
                break
            logger.warning("session lost (attempt %s) — re-login as %s", attempt, role)
            super().login_as_role(role)
        else:
            raise AssertionError(f"could not keep the {role} session on {url}")
        try:
            dismiss_overlays(self.page, grace_ms=1500)
        except Exception:  # noqa: BLE001
            pass

    # ---- navigation -------------------------------------------------------
    def open_list(self, locale: str = "en") -> "MCHeroAdminPage":
        last = None
        for attempt in range(1, 4):
            try:
                self.open(self._manage_url(locale=locale))
                self.page.locator(self.LIST_LOADED).first.wait_for(state="attached", timeout=45000)
                _dismiss_chatbot_launcher(self.page)
                return self
            except Exception as exc:  # noqa: BLE001 — retried (dropped session / slow render)
                last = exc
                self.evidence(f"open_list_retry_{attempt}")
                logger.warning("open_list attempt %s failed on %s: %r", attempt, self.page.url, exc)
        raise AssertionError(f"hero entries list never rendered: {last!r}")

    def open_hero(self, locale: str = "en") -> "MCHeroAdminPage":
        self.open(self._manage_url(edit_entry=HERO_ERC, locale=locale))
        self._entry_code = HERO_ERC
        self._locale = locale
        self.page.locator(f'{self.FORM} [name="ObjectField_{K_LABEL}"]').first.wait_for(
            state="attached", timeout=90000)
        try:
            wait_until(lambda: self.text_value(K_LABEL) != "" and bool(self.cke_name(K_DESC))
                       and self.rich_data(K_DESC) != "", timeout=20.0, poll=0.5)
        except WaitTimeoutError:
            logger.warning("hero form values / editor did not fully load in 20 s")
        _dismiss_chatbot_launcher(self.page)
        return self

    # ---- list -------------------------------------------------------------
    def hero_row(self) -> dict:
        rows = [r for r in self.list_rows() if r["entry_id"] == HERO_ID]
        return rows[0] if len(rows) == 1 else {}

    def row_count(self) -> int:
        return len(self.list_rows())

    def row_status(self, entry=None) -> str:  # type: ignore[override]
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        row = self.hero_row()
        return normalize_status(row.get("status", "")) if row else ""

    # ---- API (read; exact restore) ------------------------------------------
    def api_get(self) -> dict:
        """The stored record (Editor session, read-only GET). Retries when the
        page is mid-navigation (late redirect / license-gate reset)."""
        body = [0, ""]
        for attempt in range(1, 6):
            try:
                self.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=20000)
                body = self.page.evaluate(
                    """async (u) => { const r = await fetch(u, {headers: {'Accept': 'application/json',
                            'x-csrf-token': (window.Liferay && Liferay.authToken) || ''}});
                        return [r.status, await r.text()]; }""", HERO_API)
                if body[0] == 200:
                    break
            except Exception as exc:  # noqa: BLE001 — navigation in flight; retried
                logger.warning("api_get attempt %s: %r", attempt, exc)
            self.page.wait_for_timeout(2000)
            if body[0] in (401, 403) or attempt >= 3:
                self.open_list()
        if body[0] != 200:
            raise AssertionError(f"hero GET returned {body[0]}: {body[1][:200]}")
        data = json.loads(body[1])
        data.pop("actions", None)
        return data

    def restore_exact(self, snapshot: dict) -> int:
        """Re-sends the snapshot through the same PUT the authoring page uses
        on Publish (lock held, Editor session). Returns the HTTP status."""
        self._require_lock()
        if str(snapshot.get("id")) != HERO_ID or snapshot.get("externalReferenceCode") != HERO_ERC:
            raise AssertionError("snapshot is not QCDEMO-130709-HERO-MAIN")
        body = {k: snapshot[k] for k in _PUT_KEYS if k in snapshot}
        body["status"] = {"code": snapshot.get("status", {}).get("code", 0)}
        self.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=30000)
        result = self.page.evaluate(
            """async ([u, b]) => { const r = await fetch(u, {method: 'PUT', body: JSON.stringify(b),
                    headers: {'Content-Type': 'application/json', 'Accept': 'application/json',
                              'x-csrf-token': Liferay.authToken}});
                return [r.status, (await r.text()).slice(0, 300)]; }""", [HERO_PUT, body])
        logger.info("hero exact restore PUT -> %s", result[0])
        self.last_restore_response = result
        return int(result[0])

    # ---- plain fields -------------------------------------------------------
    def set_text(self, key: str, value: str, arabic: bool = False) -> "MCHeroAdminPage":
        self._guard_form()
        (self.fill_ar if arabic else self.fill_en)(key, value)
        return self

    def type_text(self, key: str, text: str, arabic: bool = False) -> "MCHeroAdminPage":
        """Select-all, Delete, then type key by key (counter handlers see keys)."""
        self._guard_form()
        box = self._ar(key) if arabic else self._en(key)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if text:
            self.page.keyboard.type(text)
        box.press("Tab")
        return self

    def value_of(self, key: str, arabic: bool = False) -> str:
        return (self._ar(key) if arabic else self._en(key)).input_value()

    def text_direction(self, key: str, arabic: bool = False) -> str:
        node = self._ar(key) if arabic else self._en(key)
        return node.evaluate("el => el.getAttribute('dir') || getComputedStyle(el).direction")

    def counter_reading(self, key: str, arabic: bool = False) -> tuple[int, int] | None:
        node = self._ar(key) if arabic else self._en(key)
        text = node.evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           const m = (c.innerText || '').match(/(\\d+)\\s*\\/\\s*(\\d+)/);
                           if (m) return m[1] + '/' + m[2]; }
                       return ''; }""")
        if not text:
            return None
        current, limit = text.split("/")
        return int(current), int(limit)

    def native_max_length(self, key: str, arabic: bool = False) -> int:
        node = self._ar(key) if arabic else self._en(key)
        return int(node.evaluate("el => el.maxLength"))

    def errors_for(self, key: str) -> list[str]:
        names = {f"ObjectField_{key}", f"qc-ar-{key}"}
        return [o["text"] for o in self.field_error_owners() if names & set(o["field"].split(","))]

    # ---- rich text (CKEditor 4) ---------------------------------------------
    def cke_name(self, key: str, arabic: bool = False) -> str:
        return self.page.evaluate(self._CKE_NAME_JS, [key, arabic])

    def rich_data(self, key: str, arabic: bool = False) -> str:
        name = self.cke_name(key, arabic)
        return self.page.evaluate("(n) => CKEDITOR.instances[n].getData()", name) if name else ""

    def _rich_body(self, key: str, arabic: bool):
        name = self.cke_name(key, arabic)
        return self.page.frame_locator(f'[id="cke_{name}"] iframe[title="editor"]').locator("body")

    def clear_rich(self, key: str, arabic: bool = False) -> "MCHeroAdminPage":
        self._guard_form()
        body = self._rich_body(key, arabic)
        body.wait_for(state="visible", timeout=20000)
        body.click()
        for combo in ("Delete", "Backspace"):
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press(combo)
        return self

    def type_rich(self, key: str, text: str, arabic: bool = False) -> "MCHeroAdminPage":
        """Replace the editor content with TYPED text ("\\n" = Enter)."""
        self.clear_rich(key, arabic)
        for i, part in enumerate(text.split("\n")):
            if i:
                self.page.keyboard.press("Enter")
            if part:
                self.page.keyboard.type(part)
        return self

    def bold_phrase(self, key: str, phrase: str, arabic: bool = False) -> "MCHeroAdminPage":
        """Selects `phrase` inside the editor and clicks the toolbar Bold button."""
        self._guard_form()
        name = self.cke_name(key, arabic)
        found = self.page.evaluate(
            """([n, phrase]) => { const ed = CKEDITOR.instances[n]; ed.focus();
                const doc = ed.document.$; const walker = doc.createTreeWalker(doc.body, NodeFilter.SHOW_TEXT);
                let node; while ((node = walker.nextNode())) { const i = node.data.indexOf(phrase);
                    if (i >= 0) { const r = doc.createRange(); r.setStart(node, i); r.setEnd(node, i + phrase.length);
                        const s = doc.getSelection(); s.removeAllRanges(); s.addRange(r);
                        ed.getSelection().reset && ed.getSelection().reset(); return true; } }
                return false; }""", [name, phrase])
        if not found:
            raise AssertionError(f"{phrase!r} not found in the {key} editor (arabic={arabic})")
        self.page.locator(f'[id="cke_{name}"] a.cke_button__bold').first.click()
        return self

    # ---- attachment -----------------------------------------------------------
    def upload_block_text(self, key: str = K_IMAGE) -> str:  # type: ignore[override]
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                return ((c ? c.innerText : '') + ' ' + (el.value || '') + ' ' + (el.placeholder || ''))
                    .replace(/\\s+/g, ' ').trim(); }""", IMAGE_LABEL)

    def _open_picker(self, key: str) -> None:  # type: ignore[override]
        """The field's own Select File button (locale-independent: the only
        button inside the hidden input's wrapper, live EN + AR)."""
        hidden = self._form().locator(f'input[name="ObjectField_{key}"]').first
        hidden.locator("xpath=..").locator("button").first.click()

    def current_image_name(self) -> str:
        match = re.search(r"Current file:\s*(.+?)\s*\(", self.upload_block_text())
        return match.group(1).strip() if match else ""

    def try_upload_image(self, file_path: str, stem: str) -> dict:
        self._guard_form()
        return self.attempt_upload(K_IMAGE, file_path, stem)

    def remove_image(self) -> dict:
        """Clicks "Remove file" in the image block; returns {clicked, block}."""
        self._guard_form()
        node = self._form().locator(f'input[name="ObjectField_{K_IMAGE}"]').first
        container = node.locator("xpath=ancestor::*[.//button[normalize-space()='Remove file']][1]")
        button = container.get_by_role("button", name=self.REMOVE_FILE_BUTTON)
        clicked = False
        if button.count():
            try:
                button.first.click(timeout=10000)
                clicked = True
            except Exception as exc:  # noqa: BLE001 — reported to the caller
                logger.warning("Remove file click failed: %r", exc)
        return {"clicked": clicked, "block": self.upload_block_text()}

    # ---- save ------------------------------------------------------------------
    def publish(self) -> dict:
        """Clicks Publish on the open hero form and returns the outcome evidence."""
        self._guard_form()
        self.click_publish()
        went = self.save_went_through()
        return {"went_through": went, "refused": self.save_was_refused(),
                "evidence": self.refusal_evidence(), "messages": self.all_messages_text(),
                "editbar": self.success_messages(MSG_SAVED_AND_PUBLISHED, 10.0) if went else self.editbar_texts(),
                "requests": list(getattr(self, "last_save_requests", [])),
                "responses": list(getattr(self, "last_save_responses", []))}

    def body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def has_hero_form(self) -> bool:
        return self.page.locator(f'[name="ObjectField_{K_LABEL}"]').count() > 0

    # ---- disabled inherited destructive helpers -----------------------------------
    def _disabled(self, *_a, **_k):
        raise NotImplementedError("disabled on the hero singleton")

    delete_entry_by_code = delete_entry_by_title = delete_all_entries_by_title = _disabled
    delete_disposable_entry = delete_own_entry = delete_own_entry_d = _disabled
    unpublish_entry = unpublish_to_edit_as_draft = archive_entry = _disabled


# ---------------------------------------------------------------------------
# Public hero (anonymous context)
# ---------------------------------------------------------------------------
_HERO_STATE_JS = """() => {
  const q = (s) => document.querySelector(s);
  const sec = q('section.qc-mc-hero');
  const m = (el) => { if (!el) return null; const r = el.getBoundingClientRect(); const cs = getComputedStyle(el);
      return {text: (el.innerText || '').trim(), html: el.innerHTML, left: r.left, right: r.right, width: r.width,
              height: r.height, scroll_width: el.scrollWidth, client_width: el.clientWidth,
              scroll_height: el.scrollHeight, client_height: el.clientHeight, overflow: cs.overflow,
              text_overflow: cs.textOverflow, white_space: cs.whiteSpace, direction: cs.direction,
              font_weight: cs.fontWeight}; };
  const input = q('#qc-mc-hero-q');
  const bg = q('.qc-mc-hero-bg');
  const desc = q('.qc-mc-hero-desc');
  const bolds = desc ? [...desc.querySelectorAll('b, strong')].map(e => e.innerText.trim()) : [];
  return {ready: sec ? sec.getAttribute('data-qc-mch-ready') : null, section_dir: sec ? sec.getAttribute('dir') : null,
          html_lang: document.documentElement.lang, label: m(q('.qc-mc-hero-pagetitle')),
          headline: m(q('.qc-mc-hero-headline')), desc: m(desc), desc_bold: bolds,
          placeholder: input ? input.placeholder : null, input: m(input),
          placeholder_text_width: input ? (() => { const cs = getComputedStyle(input);
              const c = document.createElement('canvas').getContext('2d');
              c.font = cs.fontWeight + ' ' + cs.fontSize + ' ' + cs.fontFamily;
              return c.measureText(input.placeholder || '').width + parseFloat(cs.paddingLeft || 0)
                     + parseFloat(cs.paddingRight || 0); })() : null,
          bg_style: bg ? (bg.style.backgroundImage || '') : null,
          viewport: window.innerWidth, doc_scroll_width: document.documentElement.scrollWidth,
          doc_client_width: document.documentElement.clientWidth};
}"""


class MCHeroPublicView(BasePage):
    READY = 'section.qc-mc-hero[data-qc-mch-ready="true"]'
    BG_SETTLED = '.qc-mc-hero-bg[data-qc-mch-bg-loaded]'

    def open_page(self, locale: str = "en") -> "MCHeroPublicView":
        self.open(web_url(PUBLIC_PATH, locale=locale))
        try:
            dismiss_overlays(self.page)
        except Exception:  # noqa: BLE001
            pass
        try:
            self.page.locator(self.READY).first.wait_for(state="attached", timeout=30000)
        except Exception:  # noqa: BLE001 — state() reports ready=None/false
            logger.warning("public hero did not report ready in 30 s (%s)", locale)
        try:
            # main.js sets the background asynchronously after "ready".
            self.page.locator(self.BG_SETTLED).first.wait_for(state="attached", timeout=15000)
        except Exception:  # noqa: BLE001 — state() reports bg_file=""
            logger.warning("public hero background did not settle in 15 s (%s)", locale)
        return self

    def state(self) -> dict:
        s = self.page.evaluate(_HERO_STATE_JS)
        s["url"] = self.page.url
        match = re.search(r"/([^/?\"]+\.(?:jpe?g|png|gif|svg))", s.get("bg_style") or "", re.I)
        s["bg_file"] = match.group(1) if match else ""
        return s

    def poll(self, predicate, locale: str, timeout: float = 60.0, poll: float = 3.0) -> tuple[dict, float, bool]:
        """Fresh reloads until predicate(state) holds. Returns (state, seconds, ok)."""
        started = time.monotonic()
        last: dict = {}
        while True:
            self.open_page(locale)
            last = self.state()
            if predicate(last):
                return last, time.monotonic() - started, True
            if time.monotonic() - started > timeout:
                return last, time.monotonic() - started, False
            self.page.wait_for_timeout(int(poll * 1000))

    def evidence(self, name: str) -> str:
        os.makedirs(EVIDENCE_ROOT, exist_ok=True)
        path = os.path.join(EVIDENCE_ROOT, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=False)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "media_center")
        except Exception as exc:  # noqa: BLE001 — evidence only
            logger.warning("evidence %s failed: %r", name, exc)
        return path

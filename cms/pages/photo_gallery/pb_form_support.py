"""
cms/pages/photo_gallery/pb_form_support.py — PBFieldsMixin /
PhotoGalleryPublicViewPB (Agent PB).

Agent PB's additions for PBI 130714 ("QC - Insights & Media - 006 - Photo
Gallery") Control_Panel field-validation cases. The core lifecycle / identity /
guarded-delete / save-probe layer is PA's `GalleryAdminPage`
(gallery_admin_base.py); this module only adds what PB's cases need on top of
it, as a mixin placed IN FRONT of PA's per-object classes:

    PBFieldsMixin + EventCategoryAdminPage  -> event_category_admin_page.py (# --- PB ---)
    PBFieldsMixin + PhotoAlbumAdminPage     -> photo_album_admin_page.py   (# --- PB ---)
    PBFieldsMixin + GalleryAdminPage        -> page_hero_admin_page.py     (PB-owned)

Read live 2026-10-05 off the `/en/` manage pages as the Site Content Editor
(156488), read-only, before any test wrote anything:
  - EN text controls `form [name="ObjectField_<key>"]`, Arabic twins
    `#qc-ar-<key>` (no `name`, `data-qc-ar-ready` set once hydrated). Both carry
    the HTML `required` attribute; NO `maxlength` anywhere.
  - Numbers are `input[type=number]` (min -2147483648: the browser does NOT
    stop a negative Display Order).
  - Attachments: text `input[name="ObjectField_<key>"]` with `accept`, a
    "Select File" button opening the Documents & Media picker iframe, help line
    "Upload a .jpg,.jpeg,.png no larger than N MB.", "Remove file" / "Undo
    remove" on a stored file, placeholder "Current file: <name> — pick a file
    to replace it".
  - Editor buttons: `button[name=status]` value 2 "Save as Draft" / value 0
    "Publish". Active Status is TICKED by default.

SESSION: role-pinned contexts navigate WITHOUT BasePage's session guard (it
re-logs a dropped session in as TEST_USER, which would silently turn an
Editor assertion into a super-admin one); tests re-read `signed_in_user()`
before every save.

Documents & Media files are never deleted by this framework; every upload is
a uniquely named QCTEST copy (see the final report for the names left).
"""

from __future__ import annotations

import json
import os
import re

from config.settings import PROJECT_ROOT, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.license_gate import clear_license_gate
from core.web.overlays import dismiss_overlays

logger = get_logger("photo_gallery_pb")

PB_QCTEST_PREFIX = "QCTEST-130714-PB-"
PB_ROLE_EDITOR = "Site Content Editor"
PB_ROLE_USER_IDS = {PB_ROLE_EDITOR: "156488"}

PB_MSG_DRAFT_SAVED = "Draft saved."
PB_MSG_SAVED_AND_PUBLISHED = "Saved and published."
PB_MSG_BLOCKED = "Please complete the required fields"
PB_MSG_ARABIC_REQUIRED_EN = "Arabic content is required."
PB_MSG_ARABIC_REQUIRED_AR = "المحتوى بالعربية مطلوب."
PB_MSG_UNSUPPORTED_EN = "Unsupported file type. Accepted formats: JPG, JPEG, PNG."
PB_MSG_UNSUPPORTED_AR = "نوع الملف غير مدعوم. الصيغ المقبولة: JPG، JPEG، PNG."
PB_MSG_COVER_REQUIRED_EN = "An album cover image is required."
PB_MSG_COVER_REQUIRED_AR = "صورة غلاف الألبوم مطلوبة."

PB_EVIDENCE_DIR = os.path.join(str(PROJECT_ROOT), "reports", "evidence", "130714_PB")


def _accept_beforeunload(dialog) -> None:
    """Leaving an edited-but-unsaved form must never hang on "leave site?"."""
    if dialog.type == "beforeunload":
        try:
            dialog.accept()
        except Exception:  # noqa: BLE001 — already handled
            pass


def norm(value) -> str:
    return "" if value is None else " ".join(str(value).split())


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, default=str)


def save_evidence(page, name: str, full_page: bool = True) -> str:
    """PNG under reports/evidence/130714_PB/ (also attached to Allure)."""
    os.makedirs(PB_EVIDENCE_DIR, exist_ok=True)
    path = os.path.join(PB_EVIDENCE_DIR, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "photo_gallery")
    except Exception as exc:  # noqa: BLE001 — evidence only
        logger.warning("evidence %s failed: %r", name, exc)
    return path


class PBFieldsMixin:
    """Agent PB's extra field-level readers, mixed IN FRONT of PA's per-object
    GalleryAdminPage subclasses (MRO: PB mixin -> PA object page -> PA core).
    Nothing here overrides a PA method except `open()` (role-pinned sessions
    navigate without BasePage's TEST_USER re-login guard)."""

    pinned_role: str | None = None
    PICKER_FEEDBACK_RE = re.compile(
        r"(valid extension|valid file size|no larger than|exceeds|too large|not supported|not allowed|"
        r"unsupported|maximum|invalid file|file type|غير مدعوم)", re.I)

    def pb_init(self) -> None:
        self.page.on("dialog", _accept_beforeunload)

    # ---- session ------------------------------------------------------------
    def open(self, url: str) -> None:
        if not self.pinned_role:
            super().open(url)
            return
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    def login_pinned(self, role: str = PB_ROLE_EDITOR) -> str:
        outcome = self.login_as_role(role)
        if outcome == "ok":
            self.pinned_role = role
        return outcome

    # ---- form readiness / readers ---------------------------------------------
    def wait_arabic_ready(self, timeout: float = 20.0) -> bool:
        """Every Arabic twin carries the script's own `data-qc-ar-ready` marker.
        Live 2026-10-05: the marker is only set on an EDIT form (stored value
        loaded); the create form never sets it, so it is only waited for there."""
        if "editEntry=" not in self.page.url:
            return True
        try:
            wait_until(lambda: self.page.evaluate(
                "() => { const t = [...document.querySelectorAll('[id^=\"qc-ar-\"]')];"
                " return t.length > 0 && t.every(e => e.hasAttribute('data-qc-ar-ready')); }"),
                timeout=timeout, poll=0.3)
            return True
        except WaitTimeoutError:
            logger.warning("Arabic twins did not report ready on %s", self.page.url)
            return False

    def control_info(self, key: str, arabic: bool = False) -> dict:
        """required / maxLength / min / accept / validationMessage of one control."""
        control = self._ar(key) if arabic else self._en(key)
        return control.evaluate(
            """e => ({required: e.required, maxLength: e.maxLength, min: e.min, max: e.max,
                      accept: e.accept || '', type: e.type, validationMessage: e.validationMessage})""")

    def fill_en_change(self, key: str, value: str):
        control = self._en(key)
        control.fill(value)
        control.dispatch_event("change")
        return self

    def fill_ar_change(self, key: str, value: str):
        control = self._ar(key)
        control.fill(value)
        control.dispatch_event("change")
        return self

    def field_error_owners(self) -> list[dict]:
        """[{field, text}] — each visible inline field error with the control it belongs to."""
        try:
            return self.page.evaluate(
                """(sel) => [...document.querySelectorAll(sel)].filter(e => e.innerText.trim()).map(e => {
                    let c = e.parentElement, owners = [];
                    for (let i = 0; i < 6 && c && !owners.length; i++, c = c.parentElement) {
                        owners = [...c.querySelectorAll('[name^="ObjectField_"]:not([type="hidden"]), [id^="qc-ar-"]')]
                            .map(n => n.name || n.id);
                    }
                    return {field: owners.join(','), text: e.innerText.trim()}; })""",
                self.FIELD_ERROR,
            )
        except Exception:  # noqa: BLE001
            return []

    def pb_refusal_evidence(self) -> dict:
        evidence = self.refusal_evidence()
        evidence["field_error_owners"] = self.field_error_owners()
        return evidence

    def visible_text(self) -> str:
        try:
            return " ".join(self.page.locator("body").inner_text().split())
        except Exception:  # noqa: BLE001
            return ""

    # ---- identity (long titles) -----------------------------------------------------
    @staticmethod
    def _title_matches(shown: str, title: str) -> bool:
        """Exact, or the Entry column / delete label shortened a LONG title with an
        ellipsis (the remaining text must still be a >=40-char prefix of it)."""
        shown, title = (shown or "").strip(), (title or "").strip()
        if shown == title:
            return True
        for mark in ("…", "..."):
            if shown.endswith(mark):
                head = shown[: -len(mark)].rstrip()
                if len(head) >= 40 and title.startswith(head):
                    return True
        return False

    def identify_created_pb(self, title: str, ids_before: set[str]):
        """PA's identify_created(), tolerant of an Entry column that shortens a long
        title: the ONE new row (id not in `ids_before`, not a seeded QCDEMO- code)
        whose OWN form reads exactly `title`."""
        from cms.pages.photo_gallery.gallery_admin_base import REAL_CODE_PREFIXES, GalleryEntry  # noqa: PLC0415
        if not title.startswith(self.prefix):
            raise ValueError(f"{title!r} is not in the {self.prefix} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not any(r["code"].startswith(p) for p in REAL_CODE_PREFIXES)]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(self.TITLE_KEY) == title:
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            logger.warning("identify_created_pb(%r): %s matches among new rows %s", title, len(matches), fresh)
            return None
        entry = GalleryEntry(title=title, entry_id=matches[0]["entry_id"], code=matches[0]["code"],
                             prefix=self.prefix, slug=self.slug)
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def _delete_preconditions(self, entry) -> str:
        """PA's checks unchanged, except the row title / delete label may be an
        ellipsis-shortened form of a long captured title (see _title_matches)."""
        from cms.pages.photo_gallery.gallery_admin_base import REAL_CODE_PREFIXES  # noqa: PLC0415
        if not self.is_list_fully_expanded():
            return f"list not fully expanded ({self.rendered_row_count()} of {self.total_entry_count()})"
        links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        if links.count() != 1:
            return f"{links.count()} delete links carry id {entry.entry_id}"
        rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code:
            return f"row {entry.entry_id} points at {row['code']!r}, not {entry.code!r}"
        if any(row["code"].startswith(p) for p in REAL_CODE_PREFIXES):
            return f"row {entry.entry_id} has a seeded code {row['code']!r}"
        if not (self._title_matches(row["title"], entry.title) and self._title_matches(row["label"], entry.title)):
            return f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, not {entry.title!r}"
        return ""

    # ---- attachments ------------------------------------------------------------
    def _file_input(self, key: str):
        return self._form().locator(f'input[name="ObjectField_{key}"]').first

    def file_field_value(self, key: str) -> str:
        """Current value of the attachment's own text input ("" = nothing selected)."""
        return self._file_input(key).input_value()

    def _picker_feedback(self, frame) -> str:
        for scope in (frame, self.page):
            try:
                nodes = scope.get_by_text(self.PICKER_FEEDBACK_RE)
                for i in range(min(nodes.count(), 10)):
                    node = nodes.nth(i)
                    text = " ".join((node.inner_text() or "").split())
                    if node.is_visible() and text and not text.startswith("Upload a "):
                        return text
            except Exception:  # noqa: BLE001 — frame detached mid-read
                continue
        return ""

    def attempt_upload_pb(self, key: str, file_path: str, stem: str | None = None,
                          response_timeout_ms: int = 30000) -> dict:
        """Like PA's attempt_upload(), but also records a CLIENT-side refusal (the
        picker refusing before any upload POST) and the picker's own feedback
        text. Returns {file, size, upload_posted, status, body, success, errors,
        feedback, picker_text, add_clicked, attached, field_text, field_value,
        field_errors, picker_evidence}. Always leaves the picker closed."""
        upload_path = self._unique_upload_copy(file_path, stem)
        result = {"file": os.path.basename(upload_path), "size": os.path.getsize(upload_path), "status": None,
                  "body": "", "success": None, "errors": [], "feedback": "", "add_clicked": False,
                  "attached": False, "picker_text": "", "upload_posted": False}
        self.last_uploaded_name = result["file"]
        self._open_picker(key)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').first.wait_for(state="attached", timeout=60000)
        try:
            with self.page.expect_response(
                lambda r: r.request.method == "POST" and bool(self.UPLOAD_REQUEST_PATTERN.search(r.url)),
                timeout=response_timeout_ms,
            ) as upload:
                frame.locator('input[type="file"]').first.set_input_files(upload_path)
            result["upload_posted"] = True
            result["status"] = upload.value.status
            try:
                result["body"] = upload.value.text()[:1000]
            except Exception:  # noqa: BLE001
                result["body"] = ""
            compact = result["body"].replace(" ", "")
            if '"success":false' in compact:
                result["success"] = False
            elif '"success":true' in compact or '"file":' in compact:
                result["success"] = True
        except Exception:  # noqa: BLE001 — no upload POST answered (client-side refusal?)
            pass
        finally:
            try:
                os.remove(upload_path)
            except OSError:
                pass
        errors = frame.locator(self.PICKER_ERROR)
        try:
            wait_until(lambda: bool(self._picker_feedback(frame)) or
                       (errors.count() > 0 and any(t.strip() for t in errors.all_inner_texts())),
                       timeout=6.0, poll=0.5)
        except WaitTimeoutError:
            pass
        try:
            result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
            result["feedback"] = self._picker_feedback(frame)
            result["picker_text"] = " ".join(frame.locator("body").inner_text(timeout=5000).split())[:800]
        except Exception:  # noqa: BLE001
            pass
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        result["picker_evidence"] = save_evidence(self.page, f"picker_{self.slug}_{key}_{result['file']}",
                                                  full_page=False)
        if result["success"] is True and not result["errors"] and not result["feedback"]:
            add = frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT)

            def _added() -> bool:
                if modal.count() == 0:
                    return True
                try:
                    add.click(timeout=3000)
                    result["add_clicked"] = True
                except Exception:  # noqa: BLE001
                    pass
                return modal.count() == 0

            try:
                wait_until(_added, timeout=30.0, poll=1.5)
            except WaitTimeoutError:
                result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
        if modal.count():
            self.page.keyboard.press("Escape")
            try:
                modal.wait_for(state="detached", timeout=8000)
            except Exception:  # noqa: BLE001
                for name in ("Cancel", "Close"):
                    button = self.page.get_by_role("button", name=name)
                    if button.count():
                        try:
                            button.first.click(timeout=5000)
                            break
                        except Exception:  # noqa: BLE001
                            continue
        result["field_text"] = self.field_block_text(key)
        result["field_value"] = self._file_input(key).input_value()
        result["field_errors"] = self._safe_field_errors()
        stem_name = os.path.splitext(result["file"])[0]
        # The size/format error quotes the file name, so field text alone is not proof of attachment.
        text_without_errors = result["field_text"]
        for error in result["field_errors"]:
            text_without_errors = text_without_errors.replace(error, " ")
        result["attached"] = stem_name in (text_without_errors + " " + result["field_value"])
        self.last_upload_attempt = result
        return result

    def upload_pb(self, key: str, file_path: str, stem: str | None = None):
        result = self.attempt_upload_pb(key, file_path, stem, response_timeout_ms=60000)
        if not result.get("attached"):
            raise AssertionError(f"upload of {file_path} into {key} was not attached: {result}")
        return self

    def stored_file_placeholder_name(self, key: str) -> str:
        """Persisted file per the input's "Current file: <name> — pick a file..." placeholder."""
        placeholder = self._file_input(key).get_attribute("placeholder") or ""
        match = re.match(r"Current file:\s*(.+?)\s+—", placeholder)
        return match.group(1) if match else ""

    def file_download_url(self, key: str) -> str:
        from config.settings import control_panel_url  # noqa: PLC0415
        href = self._file_input(key).evaluate(
            """el => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !c.querySelector('.qc-oel__current-file-meta'); i++) c = c.parentElement;
                const m = c ? c.querySelector('.qc-oel__current-file-meta') : null;
                const a = m ? [...m.querySelectorAll('a')].find(x => /download/i.test(x.innerText)) : null;
                return a ? a.getAttribute('href') : ''; }""")
        if not href:
            return ""
        return control_panel_url(href) if href.startswith("/") else href

    def file_bytes(self, key: str) -> bytes:
        url = self.file_download_url(key)
        if not url:
            return b""
        response = self.page.context.request.get(url)
        return response.body() if response.ok else b""

    def remove_file_button_state(self, key: str) -> dict:
        """{present, enabled} of the field's own "Remove file" button (read-only)."""
        return self._file_input(key).evaluate(
            """el => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && ![...c.querySelectorAll('button')].some(b => /Remove file/.test(b.innerText)); i++) c = c.parentElement;
                const b = c ? [...c.querySelectorAll('button')].find(x => /Remove file/.test(x.innerText)) : null;
                return {present: !!b, enabled: !!b && !b.disabled && !b.hidden && b.offsetParent !== null}; }""")


class PhotoGalleryPublicViewPB(BasePage):
    """Read-only, LOGGED-OUT reads of the public Photo Gallery (Agent PB). Drive
    it on a context created with `use_auth_state=False`; it navigates with a
    plain goto (BasePage.open's session guard would sign the context in).
    Selectors are the live `qc-pgl-*` / `qc-pgd-*` classes documented in
    web/pages/photo_albums/*.py (listing `/web/qatar-chamber/photo-gallery`,
    detail `/web/qatar-chamber/photo-album-details?erc=<code>`)."""

    LISTING_PATH = "/web/qatar-chamber/photo-gallery"
    DETAIL_PATH = "/web/qatar-chamber/photo-album-details"
    HERO_TITLE = ".qc-pgl-hero-title"
    HERO_BG = ".qc-pgl-hero-bg"
    CARD = "a.qc-pgl-card"
    CARD_TITLE = ".qc-pgl-card-title"
    CARD_CHIP = ".qc-pgl-chip"
    CAT_SELECT = "select[data-qc-pgl-cat]"
    MORE_BTN = ".qc-pgl-more"
    EMPTY = ".qc-pgl-empty"
    DETAIL_HERO_TITLE = ".qc-pgd-hero-title"
    DETAIL_TITLE = ".qc-pgd-title"
    DETAIL_CHIP = ".qc-pgd-chip"
    DETAIL_CRUMB_CURRENT = ".qc-pgd-crumb-current"
    LISTING_TEXT_SELECTORS = [HERO_TITLE, CARD_TITLE, CARD_CHIP, CAT_SELECT, ".qc-pgl-crumb-current"]
    DETAIL_TEXT_SELECTORS = [DETAIL_HERO_TITLE, DETAIL_TITLE, DETAIL_CHIP, DETAIL_CRUMB_CURRENT]

    def _goto(self, url: str) -> None:
        self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        clear_license_gate(self.page, url)
        dismiss_overlays(self.page, grace_ms=1500)

    def open_listing_all(self, locale: str = "en") -> "PhotoGalleryPublicViewPB":
        """Listing with every "Load More" page expanded."""
        self._goto(web_url(self.LISTING_PATH, locale=locale))
        try:
            self.page.locator(f"{self.CARD}, {self.EMPTY}").first.wait_for(state="visible", timeout=60000)
        except Exception:  # noqa: BLE001 — an empty grid is reported by the caller
            return self
        cards, button = self.page.locator(self.CARD), self.page.locator(self.MORE_BTN)
        for _ in range(40):
            if button.count() == 0 or not button.first.is_visible():
                break
            before = cards.count()
            button.first.click()
            try:
                wait_until(lambda: cards.count() > before, timeout=10.0, poll=0.25)
            except WaitTimeoutError:
                break
        return self

    def hero_title(self) -> str:
        node = self.page.locator(self.HERO_TITLE)
        return " ".join((node.first.text_content() or "").split()) if node.count() else ""

    def wait_hero_title(self, expected: str, locale: str = "en", timeout: float = 5.0) -> str:
        """Re-opens the listing until the hero title reads `expected` (cms-profile 5 s @ 0.5 s)."""
        seen = {"v": ""}

        def _ok() -> bool:
            self._goto(web_url(self.LISTING_PATH, locale=locale))
            try:
                self.page.locator(self.HERO_TITLE).first.wait_for(state="visible", timeout=30000)
            except Exception:  # noqa: BLE001
                return False
            seen["v"] = self.hero_title()
            return seen["v"] == expected

        try:
            wait_until(_ok, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return seen["v"]

    def cards(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('a.qc-pgl-card')].map(a => {
                const q = s => { const n = a.querySelector(s); return n ? n.textContent.replace(/\\s+/g, ' ').trim() : ''; };
                return {href: a.getAttribute('href') || '', title: q('.qc-pgl-card-title'), chip: q('.qc-pgl-chip')};
            })""")

    def card_index_by_code(self, code: str) -> int:
        for i, card in enumerate(self.cards()):
            if re.search(r"[?&]erc=" + re.escape(code) + r"(&|$)", card["href"]):
                return i
        return -1

    def wait_card(self, code: str, locale: str = "en", timeout: float = 5.0) -> int:
        """Re-opens the expanded listing until the card for `code` shows (5 s @ 0.5 s)."""
        state = {"i": -1}

        def _ok() -> bool:
            self.open_listing_all(locale)
            state["i"] = self.card_index_by_code(code)
            return state["i"] >= 0

        try:
            wait_until(_ok, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return state["i"]

    def category_options(self) -> list[str]:
        select = self.page.locator(self.CAT_SELECT)
        if select.count() == 0:
            return []
        return [" ".join(t.split()) for t in select.first.locator("option").all_text_contents()]

    def scroll_card_into_view(self, index: int) -> None:
        card = self.page.locator(self.CARD).nth(index)
        try:
            card.scroll_into_view_if_needed(timeout=5000)
        except Exception:  # noqa: BLE001
            pass

    def open_detail(self, code: str, locale: str = "en") -> "PhotoGalleryPublicViewPB":
        self._goto(web_url(f"{self.DETAIL_PATH}?erc={code}", locale=locale))
        try:
            self.page.locator(f"{self.DETAIL_TITLE}, {self.DETAIL_HERO_TITLE}").first.wait_for(
                state="visible", timeout=60000)
        except Exception:  # noqa: BLE001 — the caller asserts on what rendered
            logger.warning("album detail never rendered a title for %s", code)
        return self

    def detail_texts(self) -> dict:
        return self.page.evaluate(
            """(sels) => Object.fromEntries(sels.map(s => { const n = document.querySelector(s);
                return [s, n ? n.textContent.replace(/\\s+/g, ' ').trim() : null]; }))""",
            self.DETAIL_TEXT_SELECTORS)

    def overflow_report(self, selectors: list[str], only_text: str | None = None) -> list[dict]:
        """Per element of `selectors` (optionally only those containing `only_text`):
        clipping / ellipsis / line-clamp / beyond-viewport, plus page horizontal scroll."""
        return self.page.evaluate(
            """([sels, only]) => {
                const out = []; const vw = document.documentElement.clientWidth;
                for (const s of sels) document.querySelectorAll(s).forEach(el => {
                    const txt = (el.textContent || '').replace(/\\s+/g, ' ').trim();
                    if (only && !txt.includes(only)) return;
                    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
                    out.push({sel: s, text: txt.slice(0, 60), len: txt.length,
                              clipped: (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
                                       && (cs.overflow.includes('hidden') || cs.textOverflow === 'ellipsis'
                                           || cs.webkitLineClamp !== 'none'),
                              ellipsis: cs.textOverflow === 'ellipsis', line_clamp: cs.webkitLineClamp,
                              overflow: cs.overflow, white_space: cs.whiteSpace, word_break: cs.wordBreak,
                              overflow_wrap: cs.overflowWrap,
                              beyond_viewport: r.right > vw + 1 || r.left < -1,
                              width: Math.round(r.width), height: Math.round(r.height),
                              scroll_w: el.scrollWidth, client_w: el.clientWidth, vw: vw});
                });
                out.push({sel: 'document', page_hscroll: document.documentElement.scrollWidth > vw + 1,
                          scrollWidth: document.documentElement.scrollWidth, vw: vw});
                return out; }""",
            [selectors, only_text],
        )

    def evidence(self, name: str, full_page: bool = True) -> str:
        return save_evidence(self.page, name, full_page)


def overflow_problems(report: list[dict]) -> list[str]:
    """Human-readable layout problems from an overflow_report()."""
    problems = []
    for item in report:
        if item.get("sel") == "document":
            if item.get("page_hscroll"):
                problems.append(f"page scrolls horizontally (scrollWidth {item['scrollWidth']} > {item['vw']})")
            continue
        if item.get("beyond_viewport"):
            problems.append(f"{item['sel']} extends beyond the viewport (width {item['width']} / vw {item['vw']})")
        if item.get("clipped"):
            problems.append(f"{item['sel']} text is clipped (scroll {item['scroll_w']} > client {item['client_w']}, "
                            f"overflow {item['overflow']}, ellipsis {item['ellipsis']}, clamp {item['line_clamp']})")
    return problems

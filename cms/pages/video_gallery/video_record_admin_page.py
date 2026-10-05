"""
cms/pages/video_gallery/video_record_admin_page.py — Video Gallery CMS core.

Control_Panel Page Objects for PBI 130715 ("QC - Insights & Media - 007 -
Video Gallery"), Azure suite 140374 in plan 137724, on the Object Authoring
surface:

  - `/web/qatar-chamber/manage-video-record`   (slug "video-record")
  - `/web/qatar-chamber/manage-video-category` (slug "video-category",
    see video_category_admin_page.py — it subclasses VideoGalleryAdminPage)

CORE OWNER: Agent VA. Agents VB / VC subclass these classes in their own
sections (`# --- VB ---`, `# --- VC ---`) — nothing here is renamed lightly.

LIVE 2026-10-05 (read-only probes as Site Content Editor 156488 and Site
Content Author 156492, /en/ manage pages, 1920x1080):

  manage-video-record form fields (`ObjectField_<key>`; Arabic twins
  `#qc-ar-<key>`, no name):
    videoTitle* (+ qc-ar-videoTitle*), videoSourceType (picklist: Flickr |
    External URL | Direct Upload), r_flickrFolderVideoRecords_c_flickrAlbumId
    (relationship "Flickr Source Folder", options = Flickr Album records),
    r_flickrVideoRecords_c_flickrVideoId (relationship "Flickr Video", no
    options — manage-flickr-video has 0 entries), videoFile (upload, "Upload
    a .mp4,.mov no larger than 100 MB."), videoUrl, flickrVideoId,
    videoThumbnail* (upload, "Upload a .jpg,.jpeg,.png no larger than 2 MB."),
    duration*, videoDescription (+ qc-ar-videoDescription; stored as HTML),
    publishedDate* (date: visible `#qc-dtp-<hidden id>` dd/mm/yyyy box bound to
    the hidden `input[type=date]`), viewCount* (number), flickrSourceFolder
    (text), flickrDurationExceedsLimit (checkbox), videoStatus (picklist:
    Draft | Published | Unpublished — independent of the workflow badge),
    flickrLongVideoConfirmed (checkbox "Flickr 10-minute Limit Acknowledged"),
    r_videoRecords_c_videoCategoryId (relationship "Video Category": options =
    the six Video Category records by id), activeStatus (checkbox).
    (* = native `required`.)
  manage-video-category form fields: categoryName* (+ qc-ar-categoryName*),
    displayOrder* (number), activeStatus.
  Buttons: Editor "Save as Draft" / "Publish" ("As an Editor, what you
    publish here goes live straight away."); Author "Save as Draft" /
    "Submit for Review" ("Entries here are reviewed before they go live.").
  Entries list: Entry = title; Status = workflow badge; row actions carry
    `data-qc-oel-<action>="<entryId>"` + `data-qc-oel-label="<title>"`; Edit
    links `?editEntry=<externalReferenceCode>`; Preview links
    `/web/qatar-chamber/video-library?qcPreview=videorecords%3A<id>`
    (`videocategories%3A<id>` for categories). Page-size select
    `select[data-qc-oel-page-size]` with "0" = ALL.
  Real data (NEVER acted on): video records with codes QCDEMO-130715-VIDEO-NN
    plus "Youtube" (id 155179, uuid code); categories with codes
    QCDEMO-130715-VIDEOCAT-<slug> (Institutional 135063, Events 135067,
    Leadership 135071, Training 135075, Promotional 135208, Live Streams
    135212).
  Author rows on records it does not own: View / Preview / History only.

DELETE SAFETY (user's hard rule — 14 real records were once lost):
  `delete_disposable_entry()` deletes ONE record only when ALL hold —
    * its title starts with THIS page object's `owner_prefix`
      (QCTEST-130715-VA-/-VB-/-VC-) — another agent's prefix is refused;
    * its entry id was captured by `identify_created()` (diff of list ids
      before/after this test's own save) and adopted into `owned_entry_ids`;
    * its code is not a real QCDEMO-130715- code;
    * re-opened by code immediately before, the stored title equals the
      captured title;
    * the list is fully expanded (page size ALL), exactly one delete link
      carries the id, and that row's title + data-qc-oel-label equal the
      captured title (re-checked right before the click);
    * the native confirm() names the title (else it is dismissed).
  There is NO positional, looping, "first link" or substring delete here.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import uuid
from dataclasses import dataclass, replace
from time import monotonic

from cms.pages.components.object_authoring_page import ObjectAuthoringPage, normalize_status
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import PROJECT_ROOT, cms_role_credentials, control_panel_url, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.overlays import _dismiss_chatbot_launcher
from web.pages.video_library.video_details_page import VIDEO_DETAILS_PATH, VideoDetailsPage
from web.pages.video_library.video_library_listing_page import VideoLibraryListingPage

_logger = get_logger("video_gallery_admin_page")

VIDEO_RECORD_SLUG = "video-record"
VIDEO_CATEGORY_SLUG = "video-category"

QCTEST_PBI_PREFIX = "QCTEST-130715-"
REAL_CODE_PREFIX = "QCDEMO-130715-"
REAL_VIDEO_IDS = frozenset({"135228", "135246", "135252", "135258", "135264", "135270", "135276",
                            "135292", "135300", "155179"})
REAL_CATEGORY_IDS = frozenset({"135063", "135067", "135071", "135075", "135208", "135212"})

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_BLOCKED = "Please complete the required fields"
STATUS_INACTIVE = "Inactive"

THUMB_HELP = "Upload a .jpg,.jpeg,.png no larger than 2 MB."
VIDEO_FILE_HELP = "Upload a .mp4,.mov no larger than 100 MB."

# ---- Video Record field keys ----------------------------------------------
K_TITLE = "videoTitle"
K_SOURCE_TYPE = "videoSourceType"
K_FLICKR_FOLDER_REL = "r_flickrFolderVideoRecords_c_flickrAlbumId"
K_FLICKR_VIDEO_REL = "r_flickrVideoRecords_c_flickrVideoId"
K_VIDEO_FILE = "videoFile"
K_VIDEO_URL = "videoUrl"
K_FLICKR_VIDEO_ID = "flickrVideoId"
K_THUMBNAIL = "videoThumbnail"
K_DURATION = "duration"
K_DESCRIPTION = "videoDescription"
K_PUBLISHED_DATE = "publishedDate"
K_VIEW_COUNT = "viewCount"
K_FLICKR_SOURCE_FOLDER = "flickrSourceFolder"
K_FLICKR_EXCEEDS = "flickrDurationExceedsLimit"
K_VIDEO_STATUS = "videoStatus"
K_FLICKR_LONG_CONFIRMED = "flickrLongVideoConfirmed"
K_CATEGORY_REL = "r_videoRecords_c_videoCategoryId"
K_ACTIVE = "activeStatus"

SOURCE_FLICKR = "Flickr"
SOURCE_EXTERNAL_URL = "External URL"
SOURCE_DIRECT_UPLOAD = "Direct Upload"

UPLOAD_LABELS = {K_THUMBNAIL: "Video Thumbnail", K_VIDEO_FILE: "Video File"}

FIXTURES_DIR = os.path.join(str(PROJECT_ROOT), "cms", "tests", "video_gallery", "fixtures")
DEFAULT_THUMBNAIL = os.path.join(FIXTURES_DIR, "va_qctest_thumb.png")


@dataclass(frozen=True)
class VideoGalleryEntry:
    """Identity of a record THIS test created (title as stored, list id, code)."""

    title: str
    entry_id: str
    code: str
    prefix: str

    def in_namespace(self) -> bool:
        return (self.prefix.startswith(QCTEST_PBI_PREFIX) and self.prefix != QCTEST_PBI_PREFIX
                and self.title.strip().startswith(self.prefix))

    def is_real(self) -> bool:
        return (self.code.startswith(REAL_CODE_PREFIX) or self.entry_id in REAL_VIDEO_IDS
                or self.entry_id in REAL_CATEGORY_IDS)

    def with_title(self, title: str) -> "VideoGalleryEntry":
        return replace(self, title=title)


class VideoGalleryAdminPage(ObjectAuthoringPage):
    """Generic manage-<slug> driver shared by Video Record and Video Category.

    `owner_prefix` is the calling agent's data namespace (e.g.
    "QCTEST-130715-VA-"); every state-changing helper refuses records outside it.
    """

    TITLE_KEY = K_TITLE
    PREVIEW_TYPE = "videorecords"
    FORM_TEMPLATE = 'form:has([name="ObjectField_{key}"])'
    SUBMIT_NAME = re.compile(r"^\s*(Publish|Submit for Review|Submit for Publishing)\s*$")
    SAVE_AS_DRAFT_NAME = re.compile(r"^\s*Save as Draft\s*$")
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    ENTRY_COUNT = "[data-qc-oel-count]"
    EDITBAR = "[data-qc-oel-editbar]"
    FIELD_ERROR = "[data-qc-oel-field-error]"
    DELETE_LINK_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    ID_ATTRS = ("delete", "history", "view", "approve", "reject", "resubmit", "publish",
                "unpublish", "archive", "restore", "return", "schedule")
    ROW_ACTION_NAMES = ("view", "approve", "reject", "resubmit", "publish", "unpublish", "archive",
                        "restore", "return", "schedule", "history", "delete")
    DESTRUCTIVE_ROW_ACTIONS = frozenset({"delete", "trash", "untrash"})
    LIST_LOADED = ", ".join(f"[data-qc-oel-{n}]" for n in ID_ATTRS)
    EMPTY_LIST_TEXT = "No entries yet"
    SAVE_REQUEST_PATTERN = re.compile(r"edit_info_item|/o/c/")
    UPLOAD_REQUEST_PATTERN = re.compile(r"com_liferay_document_library_web_portlet_DLPortlet.*p_p_lifecycle=1")
    PICKER_ERROR = (".alert-danger, .alert-warning, [role='alert'], .text-danger, .invalid-feedback, "
                    ".form-feedback-item, .lfr-dropzone-error, .upload-error")
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    REFUSAL_QUIET_WINDOW_S = 6.0
    SAVE_OUTCOME_TIMEOUT_S = 90.0
    _DOC_MARK = "__qcVgBeforeSave"
    EVIDENCE_ROOT = os.path.join(str(PROJECT_ROOT), "reports", "evidence")

    def __init__(self, page, slug: str, owner_prefix: str, evidence_dir: str | None = None):
        if not (owner_prefix.startswith(QCTEST_PBI_PREFIX) and owner_prefix != QCTEST_PBI_PREFIX):
            raise ValueError(f"owner_prefix must be an agent namespace under {QCTEST_PBI_PREFIX}")
        super().__init__(page, slug)
        self.owner_prefix = owner_prefix
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""
        agent = owner_prefix[len(QCTEST_PBI_PREFIX):].strip("-").lower() or "x"
        self.evidence_dir = evidence_dir or os.path.join(self.EVIDENCE_ROOT, f"130715_{agent}")

    # ---- session ----------------------------------------------------------------
    def login_as_role(self, role: str) -> str:
        """Real login as `role` in an auth-free context: "ok" / "auth_failed" / "unknown"."""
        email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            return "ok"
        except Exception:  # noqa: BLE001 — classified below
            try:
                self.page.wait_for_load_state("load")
                if self.signed_in_user()[0]:
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            try:
                body = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                body = ""
            return "auth_failed" if AUTH_FAILED_BANNER_TEXT in body else "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    # ---- evidence -----------------------------------------------------------------
    def evidence(self, name: str, full_page: bool = True) -> str:
        """PNG under reports/evidence/130715_<agent>/ (also attached to Allure)."""
        os.makedirs(self.evidence_dir, exist_ok=True)
        path = os.path.join(self.evidence_dir, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "video_gallery")
        except Exception as exc:  # noqa: BLE001 — evidence only
            _logger.warning("evidence %s failed: %r", name, exc)
        return path

    # ---- navigation ---------------------------------------------------------------
    @property
    def FORM(self) -> str:  # noqa: N802 — selector constant per slug
        return self.FORM_TEMPLATE.format(key=self.TITLE_KEY)

    def open_create_form_en(self) -> "VideoGalleryAdminPage":
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self._locale = "en"
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "VideoGalleryAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} [name="ObjectField_{self.TITLE_KEY}"]').first.wait_for(timeout=90000)
        try:
            wait_until(lambda: self.text_value(self.TITLE_KEY) != "", timeout=15.0, poll=0.5)
        except WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_list_all(self) -> "VideoGalleryAdminPage":
        self.open(self._manage_url(locale="en"))
        try:
            self.page.locator(f"{self.LIST_LOADED}, :text(\"{self.EMPTY_LIST_TEXT}\")").first.wait_for(timeout=90000)
        except Exception:  # noqa: BLE001 — is_list_fully_expanded() reports it
            _logger.warning("entries list did not render on %s", self.slug)
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.first.input_value() != "0":
            select.first.select_option("0")
        total = self.total_entry_count()
        try:
            wait_until(lambda: total is None or self.rendered_row_count() >= total, timeout=15.0, poll=0.3)
        except WaitTimeoutError:
            _logger.warning("page-size ALL did not settle to %s rows", total)
        _dismiss_chatbot_launcher(self.page)
        return self

    def total_entry_count(self) -> int | None:
        counter = self.page.locator(self.ENTRY_COUNT)
        if counter.count() == 0:
            return None
        match = re.search(r"(\d+)\s*total", counter.first.inner_text())
        return int(match.group(1)) if match else None

    def rendered_row_count(self) -> int:
        return self.page.locator(f"{self.ENTRIES_TABLE_ROW}:has({self.LIST_LOADED})").count()

    def is_list_fully_expanded(self) -> bool:
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.first.input_value() != "0":
            return False
        total = self.total_entry_count()
        return total is not None and self.rendered_row_count() == total

    _ROWS_JS = """(attrs) => [...document.querySelectorAll('table tbody tr')].map(r => {
            const tds = r.querySelectorAll('td');
            let id = '';
            for (const a of attrs) { const n = r.querySelector('[data-qc-oel-' + a + ']');
                                     if (n) { id = n.getAttribute('data-qc-oel-' + a); break; } }
            const del = r.querySelector('a[data-qc-oel-delete]');
            const lab = r.querySelector('[data-qc-oel-label]');
            const link = [...r.querySelectorAll('a[href*="editEntry="]')][0];
            let code = '';
            if (link) { const m = link.getAttribute('href').match(/editEntry=([^&#]+)/); code = m ? decodeURIComponent(m[1]) : ''; }
            return {entry_id: id, title: tds[0] ? tds[0].innerText.trim() : '', code: code,
                    status: tds[1] ? tds[1].innerText.trim() : '',
                    delete_id: del ? del.getAttribute('data-qc-oel-delete') : '',
                    label: del ? (del.getAttribute('data-qc-oel-label') || '')
                               : (lab ? (lab.getAttribute('data-qc-oel-label') || '') : '')};
        }).filter(r => r.entry_id)"""

    def list_rows(self) -> list[dict]:
        return self.page.evaluate(self._ROWS_JS, list(self.ID_ATTRS))

    def snapshot_ids(self) -> set[str]:
        self.open_list_all()
        if not self.is_list_fully_expanded():
            raise AssertionError(f"the {self.slug} list did not expand to show every row; cannot snapshot ids")
        return {r["entry_id"] for r in self.list_rows()}

    def leftovers(self) -> list[dict]:
        """Read-only: rows whose title is in THIS page object's owner namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].startswith(self.owner_prefix)]

    # ---- identity -------------------------------------------------------------------
    def identify_created(self, title: str, ids_before: set[str]) -> VideoGalleryEntry | None:
        """The ONE new row (id not in `ids_before`, not real) whose Entry cell
        reads `title` and whose own form reads exactly `title`. None for zero
        or several matches. Read-only."""
        if not title.startswith(self.owner_prefix):
            raise ValueError(f"{title!r} is not in the {self.owner_prefix} namespace")
        for _ in range(3):
            self.open_list_all()
            if self.is_list_fully_expanded():
                break
        if not self.is_list_fully_expanded():
            _logger.warning("identify_created(%r): the list never expanded to every row", title)
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(REAL_CODE_PREFIX) and r["title"].strip() == title.strip()]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    if self.text_value(self.TITLE_KEY).strip() == title.strip():
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — unreadable row is not ours
                    _logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _logger.warning("identify_created(%r): %s matches among new rows %s", title, len(matches), fresh)
            return None
        entry = VideoGalleryEntry(title=title.strip(), entry_id=matches[0]["entry_id"],
                                  code=matches[0]["code"], prefix=self.owner_prefix)
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt(self, entry: VideoGalleryEntry) -> VideoGalleryEntry:
        """Lets a second page object (another role / the cleanup context) act on
        a record THIS test captured. Refuses anything outside the namespace."""
        if (not isinstance(entry, VideoGalleryEntry) or not entry.in_namespace() or entry.is_real()
                or entry.prefix != self.owner_prefix or not entry.entry_id or not entry.code):
            raise ValueError(f"refusing to adopt {entry}: not a captured {self.owner_prefix} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def _guard(self, entry: VideoGalleryEntry, what: str) -> None:
        if (not isinstance(entry, VideoGalleryEntry) or not entry.in_namespace() or entry.is_real()
                or entry.prefix != self.owner_prefix):
            raise ValueError(f"{what} refuses {entry}: not a {self.owner_prefix} record")
        if entry.entry_id not in self.owned_entry_ids:
            raise ValueError(f"{what} refuses {entry}: id not captured/adopted by this test")

    # ---- rows -----------------------------------------------------------------------
    def _row(self, entry: VideoGalleryEntry):
        return self.page.locator(", ".join(
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-{a}="{entry.entry_id}"])' for a in self.ID_ATTRS))

    def row_present(self, entry: VideoGalleryEntry) -> bool:
        return any(r["entry_id"] == entry.entry_id for r in self.list_rows())

    def row_present_by_title(self, title: str) -> bool:
        return any(r["title"].strip() == title.strip() for r in self.list_rows())

    def row_status(self, entry: VideoGalleryEntry) -> str:
        """Normalized workflow badge of the captured row ("" when the row is gone)."""
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        if len(rows) != 1:
            return ""
        raw = " ".join(rows[0]["status"].split())
        if raw.casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(raw)

    def row_status_raw(self, entry: VideoGalleryEntry) -> str:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0]["status"] if len(rows) == 1 else ""

    def row_actions(self, entry: VideoGalleryEntry) -> list[str]:
        row = self._row(entry).first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_link_labels(self, entry: VideoGalleryEntry) -> list[str]:
        return [t.strip() for t in self._row(entry).first.locator("td").last.locator("a, button")
                .all_inner_texts() if t.strip()]

    def row_has_edit_link(self, entry: VideoGalleryEntry) -> bool:
        return self._row(entry).first.locator('a[href*="editEntry="]').count() > 0

    def row_preview_href(self, entry: VideoGalleryEntry) -> str:
        link = self._row(entry).first.get_by_role("link", name="Preview")
        href = link.first.get_attribute("href") if link.count() else ""
        return (href if href.startswith("http") else control_panel_url(href)) if href else ""

    def run_row_action(self, entry: VideoGalleryEntry, action: str, comment: str = "") -> list[str]:
        """Clicks ONE id-scoped workflow action (`data-qc-oel-<action>`) on a
        captured record, accepting every confirm()/prompt() it chains (prompts
        get `comment`); returns the dialog messages. Destructive actions refused."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_disposable_entry()")
        if action != "history":
            self._guard(entry, "run_row_action")
            rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
            if len(rows) != 1 or rows[0]["title"].strip() != entry.title:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {rows}")
        control = self._row(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry.title!r} offers no {action!r} action; offered {self.row_actions(entry)}")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept(comment) if dialog.type == "prompt" else dialog.accept()
            except Exception:  # noqa: BLE001 — already handled
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        self.last_row_action_dialogs = messages
        return messages

    def history(self, entry: VideoGalleryEntry) -> list[dict]:
        """Expands the row's History (inside the table) -> [{action, who, when, comment, text}]."""
        self.open_list_all()
        self._row(entry).first.locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(), timeout=20.0, poll=0.5)
        except WaitTimeoutError:
            return []
        items = cell.locator("li")
        trail = []
        for i in range(items.count()):
            item = items.nth(i)

            def _part(sel: str, node=item) -> str:
                found = node.locator(sel)
                return found.first.inner_text().strip() if found.count() else ""

            trail.append({"action": _part(self.HISTORY_ACTION), "who": _part(self.HISTORY_WHO),
                          "when": _part(self.HISTORY_WHEN), "comment": _part(self.HISTORY_COMMENT),
                          "text": " ".join(item.inner_text().split())})
        return [h for h in trail if h["action"] or h["who"]]

    def history_cell_text(self, entry: VideoGalleryEntry) -> str:
        cell = self._row(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        return " ".join(cell.inner_text().split()) if cell.count() else ""

    def wait_status(self, entry: VideoGalleryEntry, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            self.open_list_all()
            seen["status"] = self.row_status(entry)
            return seen["status"] in expected

        try:
            wait_until(_reached, timeout=timeout, poll=3.0)
        except WaitTimeoutError:
            pass
        return seen["status"]

    # ---- guarded delete ---------------------------------------------------------------
    def _delete_preconditions(self, entry: VideoGalleryEntry) -> str:
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
        if row["code"].startswith(REAL_CODE_PREFIX):
            return f"row {entry.entry_id} has a REAL code {row['code']!r}"
        if row["title"].strip() != entry.title.strip() or row["label"].strip() != entry.title.strip():
            return (f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, "
                    f"not the captured {entry.title!r}")
        return ""

    def delete_disposable_entry(self, entry: VideoGalleryEntry) -> bool:
        """Deletes exactly the captured record or refuses (False, never raises).
        `self.last_delete_dialogs` / `self.last_delete_banners` keep the evidence."""
        self.last_delete_dialogs, self.last_delete_banners = [], []
        try:
            try:
                self._guard(entry, "delete")
            except ValueError as exc:
                _logger.error("DELETE REFUSED: %s", exc)
                return False
            self.open_entry_en(entry.code)
            live = self.text_value(self.TITLE_KEY).strip()
            if live != entry.title.strip():
                _logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry)
            if reason:
                _logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                _logger.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            names = [n for n in (entry.title.strip(), entry.code) if n]
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if any(n in dialog.message for n in names):
                    dialog.accept()
                else:
                    dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    link.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001 — verified below
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            self.last_delete_dialogs = dialogs
            try:
                self.last_delete_banners = self.editbar_texts() + self._alert_texts()
            except Exception:  # noqa: BLE001
                pass
            if not any(any(n in m for n in names) for m in dialogs):
                _logger.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not self.row_present(entry)
            if gone:
                _logger.info("deleted %r", entry)
            return gone
        except Exception as exc:  # noqa: BLE001
            _logger.error("delete of %r failed: %r", entry, exc)
            return False

    def _alert_texts(self) -> list[str]:
        return [t.strip() for t in self.page.locator(
            "[role='alert'], .alert, .qc-oel__message, .qc-oel__error").all_inner_texts() if t.strip()]

    # ---- field access -------------------------------------------------------------------
    def _form(self):
        return self.page.locator(self.FORM).first

    def _en(self, key: str):
        return self._form().locator(f'[name="ObjectField_{key}"]:not([type="hidden"])').first

    def _ar(self, key: str):
        return self._form().locator(f'[id="qc-ar-{key}"]').first

    def fill_en(self, key: str, value: str) -> "VideoGalleryAdminPage":
        self._en(key).fill(value)
        return self

    def fill_ar(self, key: str, value: str) -> "VideoGalleryAdminPage":
        self._ar(key).fill(value)
        return self

    def text_value(self, key: str) -> str:
        return self._en(key).input_value()

    def ar_value(self, key: str) -> str:
        return self._ar(key).input_value()

    def fill_number_key(self, key: str, value: str) -> "VideoGalleryAdminPage":
        self._en(key).fill(value)
        return self

    def _date_box(self, key: str):
        hidden_id = self._form().locator(f'input[type="date"][name="ObjectField_{key}"]').first.get_attribute("id")
        return self._form().locator(f'[id="qc-dtp-{hidden_id}"]').first

    def set_date(self, key: str, value: str) -> "VideoGalleryAdminPage":
        """`value` dd/mm/yyyy typed key by key ("" clears)."""
        box = self._date_box(key)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if value:
            self.page.keyboard.type(value, delay=20)
        box.press("Tab")
        return self

    def date_text(self, key: str) -> str:
        return self._date_box(key).input_value()

    def date_stored(self, key: str) -> str:
        return self._form().locator(f'input[type="date"][name="ObjectField_{key}"]').first.input_value()

    def _picklist_prefix(self, key: str) -> str:
        hidden_id = self._form().locator(
            f'input[type="hidden"][name="ObjectField_{key}"]').first.get_attribute("id")
        return re.sub(r"-value-input$", "", hidden_id or "")

    def picklist_options(self, key: str) -> list[str]:
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        toggle.click()
        options = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]')
        try:
            options.first.wait_for(state="visible", timeout=8000)
        except Exception:  # noqa: BLE001 — empty list
            pass
        labels = [options.nth(i).get_attribute("data-option-label") or "" for i in range(options.count())]
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        return labels

    def pick(self, key: str, option_label: str) -> "VideoGalleryAdminPage":
        """Picklist / relationship select by its visible option label."""
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        option = self.page.locator(
            f'li[role="option"][id^="{prefix}-option-"][data-option-label="{option_label}"]')
        toggle.click()
        option.first.wait_for(state="visible", timeout=10000)
        option.first.click()
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        try:
            wait_until(lambda: hidden.input_value() != "", timeout=5.0, poll=0.25)
        except WaitTimeoutError:
            raise AssertionError(f"picking {option_label!r} in {key} left ObjectField_{key} empty") from None
        if self.page.locator(f'li[role="option"][id^="{prefix}-option-"]:visible').count():
            toggle.click()
        return self

    def picklist_value(self, key: str) -> str:
        """Stored value (option key / related entry id) of a picklist or relationship."""
        return self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first.input_value()

    def picklist_label(self, key: str) -> str:
        return self._form().locator(f'input[type="hidden"][name="ObjectField_{key}-label"]').first.input_value()

    def set_checkbox_key(self, key: str, checked: bool) -> "VideoGalleryAdminPage":
        box = self._form().locator(f'input[type="checkbox"][name="ObjectField_{key}"]').first
        box.check() if checked else box.uncheck()
        if box.is_checked() != checked:
            raise AssertionError(f"checkbox {key} did not take the value {checked}")
        return self

    def checkbox_stored(self, key: str) -> str:
        box = self._form().locator(f'input[type="checkbox"][name="ObjectField_{key}"]')
        if box.count() == 0:
            return ""
        return "true" if box.first.is_checked() else "false"

    def set_active_status(self, active: bool) -> "VideoGalleryAdminPage":
        return self.set_checkbox_key(K_ACTIVE, active)

    def active_status_stored(self) -> str:
        return self.checkbox_stored(K_ACTIVE)

    # ---- uploads ------------------------------------------------------------------------
    @staticmethod
    def _unique_upload_copy(file_path: str, stem: str | None = None) -> str:
        base, ext = os.path.splitext(os.path.basename(file_path))
        folder = os.path.join(tempfile.gettempdir(), "qctest_uploads_130715")
        os.makedirs(folder, exist_ok=True)
        target = os.path.join(folder, f"{stem or base}-{uuid.uuid4().hex[:8]}{ext}")
        shutil.copyfile(file_path, target)
        return target

    def _open_picker(self, key: str) -> None:
        node = self._form().locator(f'[name="ObjectField_{key}"]').first
        node.evaluate("""el => { let c = el.parentElement;
            for (let i = 0; i < 6 && c && !c.querySelector('button'); i++) c = c.parentElement;
            if (c) c.setAttribute('data-qc-vg-upload-block', el.name); }""")
        self.page.locator(f'[data-qc-vg-upload-block="ObjectField_{key}"]').get_by_role(
            "button", name="Select File").first.click()

    def upload(self, key: str, file_path: str, stem: str | None = None) -> "VideoGalleryAdminPage":
        result = self.attempt_upload(key, file_path, stem)
        if not result.get("attached"):
            raise AssertionError(f"upload of {file_path} into {key} was not attached: {result}")
        return self

    def attempt_upload(self, key: str, file_path: str, stem: str | None = None,
                       response_timeout_ms: int = 60000) -> dict:
        """Tries an upload through the Documents & Media picker; returns evidence
        {file, status, body, success, errors, picker_text, add_clicked, attached, field_text}."""
        upload_path = self._unique_upload_copy(file_path, stem)
        result = {"file": os.path.basename(upload_path), "status": None, "body": "", "success": None,
                  "errors": [], "add_clicked": False, "attached": False, "picker_text": ""}
        self.last_uploaded_name = result["file"]
        self._open_picker(key)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        try:
            with self.page.expect_response(
                lambda r: r.request.method == "POST" and bool(self.UPLOAD_REQUEST_PATTERN.search(r.url)),
                timeout=response_timeout_ms,
            ) as upload:
                frame.locator('input[type="file"]').set_input_files(upload_path)
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
        except Exception:  # noqa: BLE001 — no upload POST answered
            pass
        finally:
            try:
                os.remove(upload_path)
            except OSError:
                pass
        errors = frame.locator(self.PICKER_ERROR)
        try:
            wait_until(lambda: errors.count() > 0 and any(t.strip() for t in errors.all_inner_texts()),
                       timeout=5.0, poll=0.5)
        except WaitTimeoutError:
            pass
        try:
            result["errors"] = [t.strip() for t in errors.all_inner_texts() if t.strip()]
            result["picker_text"] = " ".join(frame.locator("body").inner_text(timeout=5000).split())[:600]
        except Exception:  # noqa: BLE001
            pass
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        if result["success"] is True and not result["errors"]:
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
            result["picker_evidence"] = self.evidence(f"picker_{key}_{result['file']}", full_page=False)
            self.page.keyboard.press("Escape")
            try:
                modal.wait_for(state="detached", timeout=8000)
            except Exception:  # noqa: BLE001
                _logger.warning("upload picker did not close on Escape")
        result["field_text"] = self.upload_block_text(key)
        result["field_errors"] = self._safe_field_errors()
        result["attached"] = os.path.splitext(result["file"])[0] in result["field_text"]
        self.last_upload_attempt = result
        return result

    def upload_block_text(self, key: str) -> str:
        label = UPLOAD_LABELS.get(key, key)
        node = self._form().locator(f'[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                const v = el.value || el.placeholder || '';
                return ((c ? c.innerText : '') + ' ' + v).replace(/\\s+/g, ' ').trim(); }""",
            label,
        )

    def stored_file_name(self, key: str) -> str:
        match = re.search(r"Current file:\s*(.+?)\s*(\(|—)", self.upload_block_text(key))
        return match.group(1).strip() if match else ""

    # ---- save / publish with an outcome probe ----------------------------------------------
    def click_publish(self) -> "VideoGalleryAdminPage":
        """The role's submit button (Editor "Publish", Author "Submit for Review")."""
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def click_save_as_draft(self) -> "VideoGalleryAdminPage":
        self._arm_save_probe()
        self.page.get_by_role("button", name=self.SAVE_AS_DRAFT_NAME).first.click()
        self._wait_for_save_outcome()
        return self

    def _arm_save_probe(self) -> None:
        self._save_requests: list[str] = []
        self._save_responses: list[int] = []
        self._navigated = False
        self._errors_before = set(self._safe_field_errors())

        def _is_save(request) -> bool:
            return request.method != "GET" and bool(self.SAVE_REQUEST_PATTERN.search(request.url))

        def _on_request(request):
            try:
                if _is_save(request):
                    self._save_requests.append(f"{request.method} {request.url}")
            except Exception:  # noqa: BLE001
                pass

        def _on_response(response):
            try:
                if _is_save(response.request):
                    self._save_responses.append(response.status)
            except Exception:  # noqa: BLE001
                pass

        def _on_navigation(frame):
            if frame == self.page.main_frame:
                self._navigated = True

        self._probe_handlers = (_on_request, _on_navigation, _on_response)
        self.page.on("request", _on_request)
        self.page.on("framenavigated", _on_navigation)
        self.page.on("response", _on_response)
        self.page.evaluate(
            f"""() => {{
                window.{self._DOC_MARK} = true;
                window.__qcVgInvalid = []; window.__qcVgInvalidMsg = {{}};
                if (!window.__qcVgHooked) {{
                    window.__qcVgHooked = true;
                    document.addEventListener('invalid', (e) => {{
                        const t = e.target; const k = t.name || t.id || '';
                        window.__qcVgInvalid.push(k); window.__qcVgInvalidMsg[k] = t.validationMessage;
                    }}, true);
                }}
            }}"""
        )

    def _disarm_save_probe(self) -> None:
        on_request, on_navigation, on_response = getattr(self, "_probe_handlers", (None, None, None))
        for event, handler in (("request", on_request), ("framenavigated", on_navigation),
                               ("response", on_response)):
            if handler is not None:
                try:
                    self.page.remove_listener(event, handler)
                except Exception:  # noqa: BLE001
                    pass

    def _document_replaced(self) -> bool:
        try:
            return not self.page.evaluate(f"() => Boolean(window.{self._DOC_MARK})")
        except Exception:  # noqa: BLE001
            return False

    def _safe_field_errors(self) -> list[str]:
        try:
            return self.field_errors()
        except Exception:  # noqa: BLE001
            return []

    def _invalid_fields(self) -> list[str]:
        try:
            return list(self.page.evaluate("() => window.__qcVgInvalid || []"))
        except Exception:  # noqa: BLE001
            return []

    def _native_messages(self) -> dict:
        try:
            return dict(self.page.evaluate("() => window.__qcVgInvalidMsg || {}"))
        except Exception:  # noqa: BLE001
            return {}

    def _refusal_shown(self) -> bool:
        try:
            return (bool(self._invalid_fields()) or bool(self._safe_field_errors())
                    or any(MSG_BLOCKED in t or "not saved" in t or "Nothing has been" in t
                           for t in self.editbar_texts()))
        except Exception:  # noqa: BLE001
            return False

    def _wait_for_save_outcome(self) -> None:
        started = monotonic()
        state = {"value": ""}
        settled = f"{self.LIST_LOADED}, {self.SAVE_AS_DRAFT_BUTTON}"

        def _outcome() -> bool:
            if self._document_replaced():
                if self.page.locator(settled).count() > 0:
                    state["value"] = "reloaded"
                    return True
                return False
            answered = len(self._save_responses) >= len(self._save_requests)
            accepted = any(code < 400 for code in self._save_responses)
            quiet = answered and not self._navigated and monotonic() - started >= self.REFUSAL_QUIET_WINDOW_S
            if quiet and not accepted and self._refusal_shown():
                state["value"] = "refused"
                return True
            if quiet and accepted and any(t not in self._errors_before for t in self._safe_field_errors()):
                state["value"] = "refused"
                return True
            return False

        try:
            wait_until(_outcome, timeout=self.SAVE_OUTCOME_TIMEOUT_S, poll=0.5)
        except WaitTimeoutError:
            _logger.warning("save outcome did not settle; requests=%s responses=%s",
                            self._save_requests, self._save_responses)
        finally:
            self._disarm_save_probe()
        self.last_save_reloaded = state["value"] == "reloaded"
        self.last_save_refused = state["value"] == "refused"
        self.last_save_requests = list(self._save_requests)
        self.last_save_responses = list(self._save_responses)
        self.last_invalid_fields = [] if self.last_save_reloaded else self._invalid_fields()
        self.last_native_messages = {} if self.last_save_reloaded else self._native_messages()

    def save_went_through(self) -> bool:
        return bool(getattr(self, "last_save_reloaded", False))

    def save_was_refused(self) -> bool:
        return bool(getattr(self, "last_save_refused", False))

    def editbar_texts(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.EDITBAR).all_inner_texts() if t.strip()]

    def field_errors(self) -> list[str]:
        return [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]

    def refusal_evidence(self) -> dict:
        return {
            "invalid_fields": list(getattr(self, "last_invalid_fields", [])),
            "native_messages": dict(getattr(self, "last_native_messages", {})),
            "field_errors": self._safe_field_errors(),
            "editbar": self.editbar_texts(),
            "save_requests": list(getattr(self, "last_save_requests", [])),
            "save_responses": list(getattr(self, "last_save_responses", [])),
        }

    def all_messages_text(self) -> str:
        parts = self.editbar_texts() + self._safe_field_errors()
        parts += [m for m in getattr(self, "last_native_messages", {}).values() if m]
        return " | ".join(parts)

    def success_messages(self, expected: str, timeout: float = 15.0) -> list[str]:
        try:
            wait_until(lambda: any(expected in t for t in self.editbar_texts()), timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass
        return self.editbar_texts()

    def wait_arabic_saved(self, timeout: float = 25.0) -> str:
        """Guide §5: on a new record the Arabic is saved a moment after the
        record. Returns MSG_ARABIC_SAVED, a failure text, or ""."""
        seen = {"text": ""}

        def _done() -> bool:
            seen["text"] = self.rendered_body_text()
            return MSG_ARABIC_SAVED in seen["text"] or "Arabic content was not" in seen["text"]

        try:
            wait_until(_done, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            return ""
        return MSG_ARABIC_SAVED if MSG_ARABIC_SAVED in seen["text"] else "the Arabic content was NOT saved"

    # ---- form --------------------------------------------------------------------------------
    def submit_button_label(self) -> str:
        button = self.page.get_by_role("button", name=self.SUBMIT_NAME)
        return button.first.inner_text().strip() if button.count() else ""

    def form_buttons(self, enabled_only: bool = True) -> list[str]:
        names = []
        for button in self._form().locator("button").all():
            try:
                if button.is_visible() and (button.is_enabled() or not enabled_only):
                    label = button.inner_text().strip()
                    if label:
                        names.append(label)
            except Exception:  # noqa: BLE001 — detached node
                continue
        return names

    def editing_bar_text(self) -> str:
        for text in self.editbar_texts():
            if text.startswith("Editing"):
                return text
        return ""

    def click_unpublish_to_edit(self) -> list[str]:
        """Edit-bar "Unpublish to edit as draft" on the open captured record."""
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _accept)
        try:
            self.page.get_by_role("button", name="Unpublish to edit as draft").first.click()
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        return messages

    # ---- preview ------------------------------------------------------------------------------
    def open_listing_preview_expanded(self, preview_url: str, expected: str, timeout: float = 45.0) -> str:
        """Opens a row's Preview of the Video Library listing in THIS signed-in
        context, clicks Load More until `expected` shows or the button is gone;
        returns the body text."""
        self.open(preview_url)
        more = self.page.locator(VideoLibraryListingPage.MORE_BTN)
        cards = self.page.locator(VideoLibraryListingPage.CARD)
        state = {"text": ""}

        def _shown() -> bool:
            try:
                state["text"] = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                return False
            if expected in state["text"]:
                return True
            if more.count() and more.first.is_visible():
                before = cards.count()
                more.first.click()
                try:
                    wait_until(lambda: cards.count() > before, timeout=10.0, poll=0.25)
                except WaitTimeoutError:
                    pass
            return False

        try:
            wait_until(_shown, timeout=timeout, poll=1.0)
        except WaitTimeoutError:
            pass
        return state["text"]

    def open_preview(self, preview_url: str, expected: list[str], timeout: float = 45.0) -> str:
        """Opens a row's Preview (public page with `qcPreview=`) in THIS signed-in
        context, waits for every `expected` text; returns the body text."""
        self.open(preview_url)
        state = {"text": ""}

        def _shown() -> bool:
            try:
                state["text"] = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001
                return False
            return all(e in state["text"] for e in expected)

        try:
            wait_until(_shown, timeout=timeout, poll=1.0)
        except WaitTimeoutError:
            pass
        return state["text"]


class VideoRecordAdminPage(VideoGalleryAdminPage):
    """manage-video-record (slug "video-record")."""

    TITLE_KEY = K_TITLE
    PREVIEW_TYPE = "videorecords"

    def __init__(self, page, owner_prefix: str, evidence_dir: str | None = None):
        super().__init__(page, VIDEO_RECORD_SLUG, owner_prefix, evidence_dir)

    # ---- description (stored as HTML; CKEditor when mounted, else textarea) -----------
    def _desc_iframe(self, ar: bool = False) -> str:
        return (f'[id="cke_qc-ar-{K_DESCRIPTION}"] iframe[title="editor"]' if ar
                else f'div.cke[class*="-ObjectField_{K_DESCRIPTION}"] iframe[title="editor"]')

    def fill_description(self, text: str, ar: bool = False) -> "VideoRecordAdminPage":
        iframe = self._desc_iframe(ar)
        if self.page.locator(iframe).count():
            self.fill_iframe_editor(iframe, text)
        else:
            (self._ar(K_DESCRIPTION) if ar else self._en(K_DESCRIPTION)).fill(text)
        return self

    def description_value(self, ar: bool = False) -> str:
        iframe = self._desc_iframe(ar)
        if self.page.locator(iframe).count():
            return self.iframe_editor_text(iframe).strip()
        raw = (self._ar(K_DESCRIPTION) if ar else self._en(K_DESCRIPTION)).input_value()
        return re.sub(r"<[^>]+>", " ", raw).strip()

    # ---- whole record -------------------------------------------------------------------
    def fill_video(self, data: dict) -> "VideoRecordAdminPage":
        """Fills every key `data` carries (None / absent = left untouched).
        Keys: the K_* field keys, `<key>_ar` for Arabic twins, K_THUMBNAIL /
        K_VIDEO_FILE = local file paths (`<key>_stem` optional), "active_status"."""
        if data.get(K_TITLE) is not None:
            self.fill_en(K_TITLE, data[K_TITLE])
        if data.get(f"{K_TITLE}_ar") is not None:
            self.fill_ar(K_TITLE, data[f"{K_TITLE}_ar"])
        for key in (K_SOURCE_TYPE, K_CATEGORY_REL, K_VIDEO_STATUS, K_FLICKR_FOLDER_REL):
            if data.get(key):
                self.pick(key, data[key])
        for key in (K_VIDEO_URL, K_FLICKR_VIDEO_ID, K_DURATION, K_FLICKR_SOURCE_FOLDER):
            if data.get(key) is not None:
                self.fill_en(key, data[key])
        if data.get(K_VIEW_COUNT) is not None:
            self.fill_number_key(K_VIEW_COUNT, data[K_VIEW_COUNT])
        if data.get(K_PUBLISHED_DATE) is not None:
            self.set_date(K_PUBLISHED_DATE, data[K_PUBLISHED_DATE])
        if data.get(K_DESCRIPTION) is not None:
            self.fill_description(data[K_DESCRIPTION])
        if data.get(f"{K_DESCRIPTION}_ar") is not None:
            self.fill_description(data[f"{K_DESCRIPTION}_ar"], ar=True)
        for key in (K_FLICKR_EXCEEDS, K_FLICKR_LONG_CONFIRMED):
            if data.get(key) is not None:
                self.set_checkbox_key(key, bool(data[key]))
        for key in (K_THUMBNAIL, K_VIDEO_FILE):
            if data.get(key):
                self.upload(key, data[key], data.get(f"{key}_stem"))
                data[f"{key}_uploaded_as"] = self.last_uploaded_name
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    def read_video(self) -> dict:
        """Stored values of the open record, keyed like the fill data."""
        values = {K_TITLE: self.text_value(K_TITLE), f"{K_TITLE}_ar": self.ar_value(K_TITLE)}
        for key in (K_VIDEO_URL, K_FLICKR_VIDEO_ID, K_DURATION, K_VIEW_COUNT, K_FLICKR_SOURCE_FOLDER):
            values[key] = self.text_value(key)
        for key in (K_SOURCE_TYPE, K_VIDEO_STATUS, K_CATEGORY_REL, K_FLICKR_FOLDER_REL):
            values[key] = self.picklist_value(key)
            values[f"{key}-label"] = self.picklist_label(key)
        values[K_PUBLISHED_DATE] = self.date_stored(K_PUBLISHED_DATE)
        values[K_DESCRIPTION] = self.description_value()
        values[f"{K_DESCRIPTION}_ar"] = self.description_value(ar=True)
        for key in (K_THUMBNAIL, K_VIDEO_FILE):
            values[f"{key}_uploaded_as"] = self.stored_file_name(key)
        for key in (K_FLICKR_EXCEEDS, K_FLICKR_LONG_CONFIRMED):
            values[key] = self.checkbox_stored(key)
        values["active_status"] = self.active_status_stored()
        return values

    @staticmethod
    def default_video_data(title: str, **overrides) -> dict:
        """A complete, valid External-URL video (EN + AR, thumbnail, category
        Events, Status Published, Active Status ticked)."""
        if not title.startswith(QCTEST_PBI_PREFIX):
            raise ValueError(f"disposable videos must use a {QCTEST_PBI_PREFIX}<agent>- title")
        data = {
            K_TITLE: title,
            f"{K_TITLE}_ar": f"{title} فيديو تجريبي",
            K_SOURCE_TYPE: SOURCE_EXTERNAL_URL,
            K_VIDEO_URL: "https://vimeo.com/123456789",
            K_THUMBNAIL: DEFAULT_THUMBNAIL,
            f"{K_THUMBNAIL}_stem": "qctest-130715-thumb",
            K_DURATION: "05:12",
            K_DESCRIPTION: f"{title} — disposable automated-test video.",
            f"{K_DESCRIPTION}_ar": "فيديو اختبار آلي مؤقت.",
            K_PUBLISHED_DATE: "05/10/2026",
            K_VIEW_COUNT: "0",
            K_VIDEO_STATUS: "Published",
            K_CATEGORY_REL: "Events",
            "active_status": True,
        }
        data.update(overrides)
        return data

    @staticmethod
    def details_erc_url(code: str, locale: str = "en") -> str:
        return web_url(f"{VIDEO_DETAILS_PATH}?erc={code}", locale=locale)


class VideoLibraryPublicView(VideoLibraryListingPage):
    """Logged-out reads of the public Video Library (Load More expanded) —
    reuses web/pages/video_library/* locators. Always drive from a fresh
    context created WITHOUT the auth storageState."""

    def open_listing_all(self, locale: str = "en") -> "VideoLibraryPublicView":
        self.open_video_library(locale)
        cards, button = self.page.locator(self.CARD), self.page.locator(self.MORE_BTN)
        try:
            wait_until(lambda: cards.count() > 0 or self.is_empty_state_visible(), timeout=30.0, poll=0.5)
        except WaitTimeoutError:
            return self
        for _ in range(30):
            if button.count() == 0 or not button.first.is_visible():
                break
            before = cards.count()
            button.first.click()
            try:
                wait_until(lambda: cards.count() > before, timeout=10.0, poll=0.25)
            except WaitTimeoutError:
                break
        return self

    def cards(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('a.qc-vll-card')].map(a => {
                const q = s => { const n = a.querySelector(s); return n ? n.innerText.trim() : ''; };
                const img = a.querySelector('.qc-vll-thumb-img');
                return {href: a.getAttribute('href') || '', title: q('.qc-vll-card-title'),
                        tag: q('.qc-vll-tag'), duration: q('.qc-vll-duration'),
                        meta: [...a.querySelectorAll('.qc-vll-meta-item')].map(m => m.innerText.trim()),
                        thumb: img ? (img.getAttribute('src') || '') : '',
                        fallback: !!a.querySelector('.qc-vll-thumb-fallback')}; })"""
        )

    def card_for_code(self, code: str) -> dict:
        for card in self.cards():
            if re.search(rf"[?&]erc={re.escape(code)}(&|$)", card["href"]):
                return card
        return {}

    def card_for_title(self, title: str) -> dict:
        for card in self.cards():
            if card["title"].strip() == title.strip():
                return card
        return {}

    def chip_texts(self) -> list[str]:
        return [t.strip() for t in self.chip_labels()]

    def dropdown_texts(self) -> list[str]:
        return [t.strip() for t in self.category_options()]


class VideoDetailsPublicView(VideoDetailsPage):
    """Logged-out read of one video's Details URL (soft-404 aware)."""

    def details_state(self, code: str, locale: str = "en") -> dict:
        """{status, not_found, title, text} for `?erc=<code>` — never raises on a
        missing record (the route answers 200 with `.qc-vdt-notfound`)."""
        response = self.page.goto(VideoRecordAdminPage.details_erc_url(code, locale))
        self.page.wait_for_load_state("domcontentloaded")
        try:
            wait_until(lambda: self.page.locator(f"{self.NOT_FOUND}, {self.TITLE}").count() > 0
                       and (self.page.locator(self.NOT_FOUND).count() > 0
                            or bool(self.page.locator(self.TITLE).first.inner_text().strip())),
                       timeout=30.0, poll=0.5)
        except WaitTimeoutError:
            pass
        nf = self.page.locator(self.NOT_FOUND)
        title = self.page.locator(self.TITLE)
        return {"status": response.status if response else 0,
                "not_found": nf.count() > 0 and nf.first.is_visible(),
                "not_found_text": nf.first.inner_text().strip() if nf.count() else "",
                "title": title.first.inner_text().strip() if title.count() else "",
                "url": self.page.url}


# --- VC ---
# =============================================================================
# Agent VC (PBI 130715, suite 140374) — Video Record FIELD helpers for cases
# 143041-143073 (cms/tests/video_gallery/test_video_gallery_record_fields_control_panel.py).
# Subclasses the core VideoRecordAdminPage; adds only read helpers plus ONE
# extra guarded path for a record whose EN title is blank/whitespace (the
# "empty title is rejected" cases): such a record — if the product wrongly
# saves it — is identified by a QCTEST-130715-VC- marker in its ARABIC title,
# its captured entry id + code, and is deleted only after the same re-read /
# fully-expanded-list / single-link checks as the core delete.
# =============================================================================
VC_PREFIX = "QCTEST-130715-VC-"
VC_SOURCE_DEPENDENT_KEYS = (K_FLICKR_FOLDER_REL, K_FLICKR_VIDEO_REL, K_VIDEO_FILE, K_VIDEO_URL, K_FLICKR_VIDEO_ID)
VC_THUMBNAIL = os.path.join(FIXTURES_DIR, "vc_qctest_thumb.png")
VC_THUMBNAIL_BMP = os.path.join(FIXTURES_DIR, "vc_qctest_thumb.bmp")
VC_CLIP_MP4 = os.path.join(FIXTURES_DIR, "vc_qctest_clip.mp4")
VC_CLIP_MOV = os.path.join(FIXTURES_DIR, "vc_qctest_clip.mov")
VC_CLIP_AVI = os.path.join(FIXTURES_DIR, "vc_qctest_clip.avi")


@dataclass(frozen=True)
class VideoBlankTitleEntryVC:
    """A record THIS test created whose EN title is blank; identity = AR marker + id + code."""

    ar_title: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return self.ar_title.strip().startswith(VC_PREFIX)


class VideoRecordFieldsAdminPageVC(VideoRecordAdminPage):
    """manage-video-record field-level reads for Agent VC (namespace QCTEST-130715-VC-)."""

    def __init__(self, page):
        super().__init__(page, VC_PREFIX)

    def field_state(self, key: str) -> dict:
        """{present, visible, disabled, readonly, required, label} of field `key`'s user-facing control."""
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]')
        if hidden.count():
            node = self.page.locator(f'[id="{self._picklist_prefix(key)}-select-from-list-input"]')
        else:
            node = self._form().locator(f'[name="ObjectField_{key}"]:not([type="hidden"])')
        if node.count() == 0:
            return {"present": False, "visible": False, "disabled": None, "readonly": None, "required": None}
        return node.first.evaluate(
            """e => { let b = e; for (let i = 0; i < 6 && b && !b.querySelector('label'); i++) b = b.parentElement;
                      const shown = n => { for (let c = n; c; c = c.parentElement) {
                          const s = getComputedStyle(c); if (s.display === 'none' || s.visibility === 'hidden') return false; }
                          return true; };
                      const lab = b && b.querySelector('label') ? b.querySelector('label').innerText : '';
                      const btn = b ? b.querySelector('button') : null;
                      return {present: true, visible: shown(e) && (b ? shown(b) : true),
                              disabled: e.disabled || (btn ? btn.disabled : false),
                              readonly: e.readOnly, required: e.required || /\\*/.test(lab), label: lab.trim()}; }"""
        )

    def source_dependent_states(self) -> dict:
        return {key: self.field_state(key) for key in VC_SOURCE_DEPENDENT_KEYS}

    def form_field_labels(self) -> list[str]:
        return [t.strip() for t in self._form().locator("label").all_inner_texts() if t.strip()]

    def type_into(self, key: str, text: str) -> "VideoRecordFieldsAdminPageVC":
        """Types `text` key by key into an EN text field (a maxlength stops it the way a user is)."""
        box = self._en(key)
        box.fill("")
        box.press_sequentially(text, delay=0)
        return self

    def field_error_owners(self) -> list[dict]:
        """[{field, text}] — each inline field error with the field it belongs to."""
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
        except Exception:  # noqa: BLE001 — mid-navigation
            return []

    def refusal_evidence(self) -> dict:
        evidence = super().refusal_evidence()
        evidence["field_error_owners"] = self.field_error_owners()
        return evidence

    def raw_description(self, ar: bool = False) -> str:
        return (self._ar(K_DESCRIPTION) if ar else self._en(K_DESCRIPTION)).input_value()

    def row_modified_text(self, entry: VideoGalleryEntry) -> str:
        """LAST MODIFIED cell of exactly the captured row ("" unless exactly one)."""
        cells = self.page.evaluate(
            """(id) => [...document.querySelectorAll('table tbody tr')]
                 .filter(r => r.querySelector('[data-qc-oel-delete="' + id + '"], [data-qc-oel-history="' + id + '"]'))
                 .map(r => { const t = r.querySelectorAll('td'); return t[2] ? t[2].innerText.trim() : ''; })""",
            entry.entry_id,
        )
        return cells[0] if len(cells) == 1 else ""

    # ---- blank-EN-title records (only if the product wrongly saves one) --------------
    def identify_created_by_ar(self, ar_title: str, ids_before: set[str]) -> VideoBlankTitleEntryVC | None:
        if not ar_title.startswith(VC_PREFIX):
            raise ValueError(f"{ar_title!r} is not in the {VC_PREFIX} namespace")
        for _ in range(3):
            self.open_list_all()
            if self.is_list_fully_expanded():
                break
        if not self.is_list_fully_expanded():
            _logger.warning("identify_created(%r): the list never expanded to every row", ar_title)
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(REAL_CODE_PREFIX)]
        matches = []
        for row in fresh:
            try:
                self.open_entry_en(row["code"])
                if self.ar_value(K_TITLE).strip() == ar_title.strip() and not self.text_value(K_TITLE).strip():
                    matches.append(row)
            except Exception as exc:  # noqa: BLE001 — unreadable row is not ours
                _logger.warning("could not read new row %s: %r", row, exc)
        if len(matches) != 1:
            return None
        entry = VideoBlankTitleEntryVC(ar_title=ar_title.strip(), entry_id=matches[0]["entry_id"],
                                       code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def delete_blank_title_entry(self, entry: VideoBlankTitleEntryVC) -> bool:
        """Guarded delete of a captured blank-title VC record; False (never raises) on any doubt."""
        self.last_delete_dialogs = []
        try:
            if (not entry.in_namespace() or not entry.entry_id or not entry.code
                    or entry.code.startswith(REAL_CODE_PREFIX) or entry.entry_id in REAL_VIDEO_IDS
                    or entry.entry_id not in self.owned_entry_ids):
                _logger.error("DELETE REFUSED: %r is not a captured VC blank-title record", entry)
                return False
            self.open_entry_en(entry.code)
            if self.ar_value(K_TITLE).strip() != entry.ar_title or self.text_value(K_TITLE).strip():
                _logger.error("DELETE REFUSED for %r: the record no longer matches", entry)
                return False

            def _reason() -> str:
                if not self.is_list_fully_expanded():
                    return "list not fully expanded"
                rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
                links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id)).count()
                if len(rows) != 1 or links != 1:
                    return f"{len(rows)} rows / {links} links carry id {entry.entry_id}"
                if rows[0]["code"] != entry.code or rows[0]["title"].strip():
                    return f"row {rows[0]} does not match the captured blank-title {entry}"
                return ""

            self.open_list_all()
            for attempt in ("check", "re-check"):
                reason = _reason()
                if reason:
                    _logger.error("DELETE REFUSED for %r (%s): %s", entry, attempt, reason)
                    return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if entry.code in dialog.message or entry.ar_title in dialog.message:
                    dialog.accept()
                else:
                    dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.click(force=True)
                try:
                    link.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001 — verified below
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            self.last_delete_dialogs = dialogs
            self.open_list_all()
            return self.is_list_fully_expanded() and not any(
                r["entry_id"] == entry.entry_id for r in self.list_rows())
        except Exception as exc:  # noqa: BLE001
            _logger.error("blank-title delete of %r failed: %r", entry, exc)
            return False


class VideoPublicViewVC(VideoLibraryPublicView):
    """Logged-out listing + detail reads for Agent VC (char-limit layout checks included)."""

    LISTING_TEXT_SELECTORS = ["a.qc-vll-card", ".qc-vll-card-title", ".qc-vll-tag"]
    DETAIL_TEXT_SELECTORS = [".qc-vdt-hero-title", ".qc-vdt-crumb-current", ".qc-vdt-title", ".qc-vdt-desc"]

    def open_detail(self, code: str, locale: str = "en") -> "VideoPublicViewVC":
        self.open(VideoRecordAdminPage.details_erc_url(code, locale))
        self.page.locator(".qc-vdt-title, .qc-vdt-notfound").first.wait_for(state="attached", timeout=60000)
        try:
            wait_until(lambda: self.page.locator(".qc-vdt-notfound:visible").count() > 0
                       or bool(self.page.locator(".qc-vdt-title").first.inner_text().strip()),
                       timeout=20.0, poll=0.5)
        except WaitTimeoutError:
            pass
        return self

    def detail(self) -> dict:
        return self.page.evaluate(
            """() => { const q = s => { const n = document.querySelector(s); return n ? n.innerText.trim() : ''; };
                const desc = document.querySelector('.qc-vdt-desc');
                const poster = document.querySelector('.qc-vdt-poster-img');
                const nf = document.querySelector('.qc-vdt-notfound');
                return {not_found: !!(nf && nf.offsetParent !== null), title: q('.qc-vdt-title'),
                        hero_title: q('.qc-vdt-hero-title'), tag: q('.qc-vdt-tag'), duration: q('.qc-vdt-duration'),
                        meta: [...document.querySelectorAll('.qc-vdt-meta-item')].map(m => m.innerText.trim()),
                        desc_text: desc ? desc.innerText : '', desc_html: desc ? desc.innerHTML : '',
                        desc_paragraphs: desc ? desc.querySelectorAll('p').length : 0,
                        poster_src: poster ? (poster.getAttribute('src') || '') : '',
                        poster_loaded: poster ? (poster.complete && poster.naturalWidth > 0) : false}; }"""
        )

    def wait_images_settled(self, selector: str, timeout: float = 15.0) -> None:
        imgs = self.page.locator(selector)
        try:
            wait_until(lambda: all(imgs.nth(i).evaluate("i => i.complete") for i in range(imgs.count())),
                       timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass

    def card_thumb_loaded(self, code: str) -> bool:
        self.wait_images_settled("a.qc-vll-card .qc-vll-thumb-img")
        return bool(self.page.evaluate(
            """(code) => { const a = [...document.querySelectorAll('a.qc-vll-card')]
                    .find(x => (x.getAttribute('href') || '').endsWith('erc=' + code));
                const i = a ? a.querySelector('.qc-vll-thumb-img') : null;
                return !!(i && i.complete && i.naturalWidth > 0); }""", code))

    def play_and_read_source(self, timeout: float = 20.0) -> dict:
        """Clicks Play; returns what mounted in `.qc-vdt-embed` {iframe_src, video_src, error}."""
        self.page.locator(".qc-vdt-play").first.click()
        try:
            self.page.locator(".qc-vdt-embed iframe, .qc-vdt-embed video, .qc-vdt-player-error").first.wait_for(
                state="attached", timeout=timeout * 1000)
        except Exception:  # noqa: BLE001 — reported by the caller
            pass
        return self.page.evaluate(
            """() => { const f = document.querySelector('.qc-vdt-embed iframe');
                const v = document.querySelector('.qc-vdt-embed video');
                const s = v ? (v.currentSrc || v.getAttribute('src') || ((v.querySelector('source') || {}).src) || '') : '';
                const err = document.querySelector('.qc-vdt-player-error');
                return {iframe_src: f ? (f.getAttribute('src') || '') : '', video_src: s,
                        error: err && err.offsetParent !== null ? err.innerText.trim() : ''}; }"""
        )

    def overflow_report(self, selectors: list[str]) -> list[dict]:
        """Per element: clipping / ellipsis / beyond-viewport signals + page horizontal scroll."""
        return self.page.evaluate(
            """(sels) => {
                const out = []; const vw = document.documentElement.clientWidth;
                for (const s of sels) document.querySelectorAll(s).forEach(el => {
                    const cs = getComputedStyle(el); const r = el.getBoundingClientRect();
                    out.push({sel: s, text: el.innerText.slice(0, 60),
                              clipped: (el.scrollWidth > el.clientWidth + 1 || el.scrollHeight > el.clientHeight + 1)
                                       && (cs.overflow.includes('hidden') || cs.textOverflow === 'ellipsis'
                                           || cs.webkitLineClamp !== 'none'),
                              ellipsis: cs.textOverflow === 'ellipsis', line_clamp: cs.webkitLineClamp,
                              beyond_viewport: r.right > vw + 1 || r.left < -1,
                              width: Math.round(r.width), vw: vw}); });
                out.push({sel: 'document', page_hscroll: document.documentElement.scrollWidth > vw + 1,
                          scrollWidth: document.documentElement.scrollWidth, vw: vw});
                return out; }""",
            selectors,
        )

    def scroll_to(self, selector: str) -> None:
        node = self.page.locator(selector)
        if node.count():
            node.first.scroll_into_view_if_needed()

    def evidence(self, name: str, full_page: bool = True) -> str:
        folder = os.path.join(str(PROJECT_ROOT), "reports", "evidence", "130715_vc", "public")
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "video_gallery")
        except Exception as exc:  # noqa: BLE001 — evidence only
            _logger.warning("public evidence %s failed: %r", name, exc)
        return path
# --- end VC ---

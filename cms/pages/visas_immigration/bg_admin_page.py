"""
cms/pages/visas_immigration/bg_admin_page.py — Business Gateway (BG) Object
Authoring Page Object for PBI 130701 Visas & Immigration (suite 140362).

One class, `BGAdminPage`, drives any of the seven BG `manage-<slug>` pages
(`/web/qatar-chamber/manage-bg-*`). Construct it with the object slug and the
calling agent's data prefix; everything that is object-specific (field keys,
which field the list's ENTRY column shows) lives in the tables below.

LIVE RECON 2026-10-06 (Site Content Editor 156488, Author 156492, admin 20132;
read-only, nothing saved):

  Object (slug)               ENTRY column    Fields (EN key; * = required; AR twin `qc-ar-<key>`)
  BG Info Page (bg-info-page) pageTitle       pageKey* (text, cfg maxLength 280), eyebrowLabel* (60,
                                              AR*), pageTitle* (120, AR*), heroDescription* (rich),
                                              heroBanner* (upload .jpg/.jpeg/.png/.svg <= 2 MB),
                                              activeStatus. NO create form for ANY role (form is
                                              display:none) — the 3 page records can only be edited.
                                              NO Status / pageStatus field (removed, PBI 142267).
  BG Info Section             sectionTitle    pageKey*, sectionKey*, sectionEyebrow (100, optional),
  (bg-info-section)                           sectionTitle* (120, AR*), sectionBody (rich, optional),
                                              highlightCardEyebrow (100), highlightCardHeading (200),
                                              supportingImage (upload .jpg/.jpeg/.png <= 2 MB),
                                              supportingImageAltText (+AR), disclaimerBody (rich),
                                              displayOrder* (number), activeStatus.
  BG Checklist Item           sectionKey (!)  sectionKey*, itemText* (RICH TEXT, no counter),
  (bg-checklist-item)                         displayOrder*, activeStatus.
  BG Highlight Item           itemText        sectionKey*, itemText* (120, AR*), displayOrder*, activeStatus.
  BG Sub-topic Block          blockHeading    sectionKey*, blockHeading* (120, AR*), blockBody* (rich,
  (bg-sub-topic-block)                        no counter), blockStyle (picklist Paragraph=paragraph /
                                              Checklist=checklist, optional), displayOrder*, activeStatus.
  BG Official Source Link     linkTitle       sectionKey*, linkTitle* (200, AR*), linkDescription (250),
  (bg-official-source-link)                   url* (text), openBehavior (Same Tab=sameTab /
                                              New Tab=newTab), displayOrder*, activeStatus.
  BG Sector Tile              tileLabel       sectionKey*, tileIcon* (upload incl. svg), tileLabel* (120),
  (bg-sector-tile)                            tileUrl, openBehavior, displayOrder*, activeStatus.

  Relationships are plain TEXT KEYS, not Liferay relationships: page.pageKey
  <- section.pageKey; section.sectionKey <- item.sectionKey (items are NOT
  scoped to a page — a sectionKey must be unique site-wide).

  Buttons: Editor "Save as Draft" / "Publish" ("As an Editor, what you publish
  here goes live straight away."); Author "Save as Draft" / "Submit for
  Review" ("Entries here are reviewed before they go live."). Editor rows on a
  published record: Edit / Preview / Unpublish / History / Delete; Author: View
  / Preview / History. Row actions carry `data-qc-oel-<action>="<entryId>"`,
  the delete link also `data-qc-oel-label="<ENTRY text>"`. Status badges seen:
  PUBLISHED, DRAFT, PENDING REVIEW, INACTIVE.

  Public renderer (fragment on /web/qatar-chamber/visas-immigration, config
  pageKey="visas-immigration", nestedSectionKeys="official-sources"): reads all
  seven objects, takes the FIRST bginfopages row whose pageKey matches, hides
  everything unless that row is workflow-approved, then renders sections with
  the same pageKey (activeStatus true, ascending displayOrder) and joins items
  by sectionKey. Only the FIRST section (by order) with a disclaimerBody feeds
  the page-foot disclaimer. Signed-in staff also SEE drafts on the ordinary
  page (qc-object-preview.js) — public assertions must use a fresh anonymous
  context.

DELETE SAFETY (user's standing rule): `delete_disposable_entry()` deletes ONLY
a `BGEntry` this session captured (list-id diff + exact identity read back by
code), in the caller's own QCTEST-130701-<A|B|C|D>- namespace, never a QCDEMO-
record, re-checked immediately before the click, confirm() must name the
entry. No positional, looping or substring delete exists in this module.
"""

import os as _os
import re as _re
from dataclasses import dataclass as _dataclass

from cms.pages.tenders.tender_admin_page import TenderWorkflowAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import web_url
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.overlays import _dismiss_chatbot_launcher

_logger = _get_logger("bg_admin_page")

# ---- objects ----------------------------------------------------------------
SLUG_PAGE = "bg-info-page"
SLUG_SECTION = "bg-info-section"
SLUG_CHECKLIST = "bg-checklist-item"
SLUG_HIGHLIGHT = "bg-highlight-item"
SLUG_SUBTOPIC = "bg-sub-topic-block"
SLUG_LINK = "bg-official-source-link"
SLUG_TILE = "bg-sector-tile"

# Headless resource name (appears in save requests and in `qcPreview=`).
RESOURCE = {
    SLUG_PAGE: "bginfopages",
    SLUG_SECTION: "bginfosections",
    SLUG_CHECKLIST: "bgchecklistitems",
    SLUG_HIGHLIGHT: "bghighlightitems",
    SLUG_SUBTOPIC: "bgsubtopicblocks",
    SLUG_LINK: "bgofficialsourcelinks",
    SLUG_TILE: "bgsectortiles",
}

# The field the entries list shows in its ENTRY column (= the identity field).
ENTRY_FIELD = {
    SLUG_PAGE: "pageTitle",
    SLUG_SECTION: "sectionTitle",
    SLUG_CHECKLIST: "sectionKey",
    SLUG_HIGHLIGHT: "itemText",
    SLUG_SUBTOPIC: "blockHeading",
    SLUG_LINK: "linkTitle",
    SLUG_TILE: "tileLabel",
}

# Field keys per object (EN `ObjectField_<key>`; AR `qc-ar-<key>`).
TEXT_KEYS = {
    SLUG_PAGE: ("pageKey", "eyebrowLabel", "pageTitle"),
    SLUG_SECTION: ("pageKey", "sectionKey", "sectionEyebrow", "sectionTitle", "highlightCardEyebrow",
                   "highlightCardHeading", "supportingImageAltText"),
    SLUG_CHECKLIST: ("sectionKey",),
    SLUG_HIGHLIGHT: ("sectionKey", "itemText"),
    SLUG_SUBTOPIC: ("sectionKey", "blockHeading"),
    SLUG_LINK: ("sectionKey", "linkTitle", "linkDescription", "url"),
    SLUG_TILE: ("sectionKey", "tileLabel", "tileUrl"),
}
AR_TEXT_KEYS = {
    SLUG_PAGE: ("eyebrowLabel", "pageTitle"),
    SLUG_SECTION: ("sectionEyebrow", "sectionTitle", "highlightCardEyebrow", "highlightCardHeading",
                   "supportingImageAltText"),
    SLUG_CHECKLIST: (),
    SLUG_HIGHLIGHT: ("itemText",),
    SLUG_SUBTOPIC: ("blockHeading",),
    SLUG_LINK: ("linkTitle", "linkDescription"),
    SLUG_TILE: ("tileLabel",),
}
RICH_KEYS = {
    SLUG_PAGE: ("heroDescription",),
    SLUG_SECTION: ("sectionBody", "disclaimerBody"),
    SLUG_CHECKLIST: ("itemText",),
    SLUG_HIGHLIGHT: (),
    SLUG_SUBTOPIC: ("blockBody",),
    SLUG_LINK: (),
    SLUG_TILE: (),
}
PICKLIST_KEYS = {SLUG_SUBTOPIC: ("blockStyle",), SLUG_LINK: ("openBehavior",), SLUG_TILE: ("openBehavior",)}
UPLOAD_KEYS = {SLUG_PAGE: {"heroBanner": "Hero Banner"},
               SLUG_SECTION: {"supportingImage": "Supporting Image"},
               SLUG_TILE: {"tileIcon": "Tile Icon"}}
HAS_DISPLAY_ORDER = frozenset(set(RESOURCE) - {SLUG_PAGE})

# Character limits shown by the form's own counters ("0 / N"), live 2026-10-06.
# Rich-text fields (checklist itemText, blockBody, disclaimerBody,
# heroDescription, sectionBody) show NO counter.
COUNTER_LIMITS = {
    (SLUG_PAGE, "eyebrowLabel"): 60, (SLUG_PAGE, "pageTitle"): 120,
    (SLUG_SECTION, "sectionEyebrow"): 100, (SLUG_SECTION, "sectionTitle"): 120,
    (SLUG_SECTION, "highlightCardEyebrow"): 100, (SLUG_SECTION, "highlightCardHeading"): 200,
    (SLUG_HIGHLIGHT, "itemText"): 120, (SLUG_SUBTOPIC, "blockHeading"): 120,
    (SLUG_LINK, "linkTitle"): 200, (SLUG_LINK, "linkDescription"): 250, (SLUG_TILE, "tileLabel"): 120,
}

OPT_BLOCK_STYLE_PARAGRAPH = "Paragraph"
OPT_BLOCK_STYLE_CHECKLIST = "Checklist"
OPT_OPEN_SAME_TAB = "Same Tab"
OPT_OPEN_NEW_TAB = "New Tab"

# ---- real data (never acted on) ------------------------------------------------
VISAS_PAGE_KEY = "visas-immigration"
VISAS_PAGE_CODE = "QCDEMO-130701-PAGE-visas-immigration"
VISAS_PAGE_ID = "109104"
# Section 01..04 of the case wording = the real sections in displayOrder.
REAL_SECTIONS = {  # sectionKey: (displayOrder, entryId, title)
    "confirm-requirements": (100, "109110", "Confirm requirements before you travel"),
    "arrivals": (200, "109240", "Arriving at Hamad International Airport"),
    "departures": (300, "109115", "Departing from Hamad International Airport"),
    "official-sources": (400, "109119", "Official sources"),
}
REAL_CODE_PREFIX = "QCDEMO-"
VISAS_PUBLIC_PATH = "/web/qatar-chamber/visas-immigration"

# ---- namespaces / roles / messages ------------------------------------------------
QCTEST_PREFIXES = {a: f"QCTEST-130701-{a}-" for a in "ABCD"}
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}
MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_EDITOR_NOTE = "As an Editor, what you publish here goes live straight away."
MSG_AUTHOR_NOTE = "Entries here are reviewed before they go live."
MSG_AUTHOR_PUBLISHED_DENIED = "Only a Content Editor can change a record once it has reached the website"
STATUS_INACTIVE = "Inactive"


@_dataclass(frozen=True)
class BGEntry:
    """Identity of ONE BG record this session created.

    `entry_value` is the stored ENTRY-column field value (ENTRY_FIELD[slug]);
    `prefix` the creating agent's namespace (QCTEST-130701-<X>-). Key fields
    (sectionKey / pageKey) are compared case-insensitively because keys are
    authored lower-case ("qctest-130701-c-...")."""

    slug: str
    entry_value: str
    entry_id: str
    code: str
    prefix: str

    def in_namespace(self) -> bool:
        return (self.prefix in QCTEST_PREFIXES.values()
                and self.entry_value.strip().casefold().startswith(self.prefix.casefold())
                and bool(self.entry_id) and bool(self.code)
                and not self.code.upper().startswith(REAL_CODE_PREFIX))


class BGAdminPage(TenderWorkflowAdminPage):
    """`manage-bg-*` driver. Reuses the confirmed-live Object Authoring
    mechanics of TenderFieldsAdminPage / TenderWorkflowAdminPage (role login,
    Load-All list, id-scoped row actions, save-outcome probe, field access by
    `ObjectField_<key>` / `qc-ar-<key>`, rich text, picklists, uploads, History,
    Preview). Every tender-specific identity / data / delete method is
    overridden or disabled below."""

    FORM = 'form:has([name^="ObjectField_"])'
    EVIDENCE_ROOT = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence")

    def __init__(self, page, slug: str, agent: str):
        if slug not in RESOURCE:
            raise ValueError(f"unknown BG slug {slug!r}")
        if agent not in QCTEST_PREFIXES:
            raise ValueError(f"agent must be one of {sorted(QCTEST_PREFIXES)}")
        super().__init__(page)
        self.slug = slug
        self.agent = agent
        self.prefix = QCTEST_PREFIXES[agent]
        self.EVIDENCE_DIR = _os.path.join(self.EVIDENCE_ROOT, f"130701_{agent}")
        self.SAVE_REQUEST_PATTERN = _re.compile(rf"edit_info_item|/o/c/{RESOURCE[slug]}")
        self.entry_field = ENTRY_FIELD[slug]

    def for_object(self, slug: str) -> "BGAdminPage":
        """A sibling driver on the same browser page for another BG object
        (same agent; shares nothing else — each object has its own owned ids)."""
        return BGAdminPage(self.page, slug, self.agent)

    # ---- naming -----------------------------------------------------------------
    def name(self, tc_id: str, stamp: str, suffix: str = "") -> str:
        """Display text in this agent's namespace, e.g. QCTEST-130701-C-140428-1006T1130."""
        return f"{self.prefix}{tc_id}-{stamp}" + (f" {suffix}" if suffix else "")

    def key(self, tc_id: str, stamp: str) -> str:
        """A lower-case sectionKey / pageKey in this agent's namespace."""
        return f"{self.prefix}{tc_id}-{stamp}".lower()

    # ---- navigation ---------------------------------------------------------------
    def open_create_form_en(self) -> "BGAdminPage":
        if self.slug == SLUG_PAGE:
            raise AssertionError("BG Info Page has no create form on Object Authoring (live 2026-10-06)")
        return super().open_create_form_en()

    def open_entry_en(self, code: str) -> "BGAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self.page.locator(f'{self.FORM} [name="ObjectField_{self.entry_field}"]').first.wait_for(
            state="attached", timeout=90000)
        try:
            _wait_until(lambda: self.entry_value() != "", timeout=15.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    def entry_value(self) -> str:
        """Stored value of this object's ENTRY-column field on the open form."""
        if self.entry_field in RICH_KEYS[self.slug]:
            return self.rich_text(self.entry_field)
        return self.text_value(self.entry_field)

    # ---- identity / capture -------------------------------------------------------------
    def leftovers(self) -> list[dict]:
        """Read-only: rows whose ENTRY text is in THIS agent's namespace."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].strip().casefold().startswith(self.prefix.casefold())]

    def identify_created(self, entry_value: str, ids_before: set[str]) -> BGEntry | None:
        """The ONE new row (id not in `ids_before`, not a QCDEMO- code) whose
        ENTRY cell reads `entry_value` and whose own form reads it back
        exactly. None for zero or several matches. Read-only."""
        if not entry_value.casefold().startswith(self.prefix.casefold()):
            raise ValueError(f"{entry_value!r} is not in the {self.prefix} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].upper().startswith(REAL_CODE_PREFIX)
                 and r["title"].strip() == entry_value.strip()]
        matches = []
        for row in fresh:
            for attempt in (1, 2):
                try:
                    self.open_entry_en(row["code"])
                    stored = self.entry_value()
                    if " ".join(stored.split()) == " ".join(entry_value.split()):
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _logger.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        self.last_identify_matches = [
            BGEntry(slug=self.slug, entry_value=m["title"].strip(), entry_id=m["entry_id"], code=m["code"],
                    prefix=self.prefix) for m in matches]
        if len(matches) != 1:
            _logger.warning("identify_created(%r): %s matches among new rows %s", entry_value, len(matches), fresh)
            return None
        entry = BGEntry(slug=self.slug, entry_value=matches[0]["title"].strip(), entry_id=matches[0]["entry_id"],
                        code=matches[0]["code"], prefix=self.prefix)
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt(self, entry: BGEntry) -> BGEntry:  # type: ignore[override]
        if not isinstance(entry, BGEntry) or entry.slug != self.slug or entry.prefix != self.prefix \
                or not entry.in_namespace():
            raise ValueError(f"refusing to adopt {entry}: not a captured {self.prefix} {self.slug} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def create_entry(self, data: dict, publish: bool = True) -> BGEntry | None:
        """Fills a fresh create form with `data` (see fill_data), saves (Publish /
        Submit for Review, or Save as Draft) and captures the new record by
        list-id diff. Returns None (and logs) when the save was refused or the
        record could not be identified uniquely."""
        value = data.get(self.entry_field)
        if not value or not str(value).casefold().startswith(self.prefix.casefold()):
            raise ValueError(f"{self.entry_field} must start with {self.prefix}")
        ids_before = self.snapshot_ids()
        self.open_create_form_en()
        self.fill_data(data)
        self.click_publish() if publish else self.click_save_as_draft()
        if not self.save_went_through():
            _logger.warning("create_entry: save not confirmed %s", self.refusal_evidence())
            return None
        self.last_create_messages = self.success_messages(MSG_DRAFT_SAVED if not publish else MSG_SAVED_AND_PUBLISHED,
                                                          timeout=15.0)
        self.wait_arabic_saved()
        return self.identify_created(str(value), ids_before)

    def wait_arabic_saved(self, timeout: float = 20.0) -> bool:
        """A brand-new record saves its Arabic a moment later (guide §5)."""
        try:
            _wait_until(lambda: MSG_ARABIC_SAVED in self.rendered_body_text()
                        or "Arabic content was not" in self.rendered_body_text(), timeout=timeout, poll=0.5)
            return MSG_ARABIC_SAVED in self.rendered_body_text()
        except _WaitTimeoutError:
            return False

    # ---- rows ------------------------------------------------------------------------------
    def row_status_of(self, entry: BGEntry) -> str:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        if len(rows) != 1:
            return ""
        raw = " ".join(rows[0]["status"].split())
        if raw.casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        return normalize_status(raw)

    def wait_row_status(self, entry: BGEntry, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            self.open_list_all()
            seen["status"] = self.row_status_of(entry)
            return seen["status"] in expected

        try:
            _wait_until(_reached, timeout=timeout, poll=3.0)
        except _WaitTimeoutError:
            pass
        return seen["status"]

    def run_row_action(self, entry: BGEntry, action: str, comment: str = "") -> list[str]:  # type: ignore[override]
        """ONE id-scoped workflow action on a record this session captured
        (History is read-only and allowed on any row). Delete is refused here."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_disposable_entry()")
        if action != "history":
            if not isinstance(entry, BGEntry) or entry.slug != self.slug or not entry.in_namespace() \
                    or entry.prefix != self.prefix or entry.entry_id not in self.owned_entry_ids:
                raise ValueError(f"run_row_action refuses {entry}: not a captured {self.prefix} record")
            rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
            if len(rows) != 1 or rows[0]["title"].strip() != entry.entry_value:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {rows}")
        control = self._row_a(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry.entry_value!r} offers no {action!r}; offered {self.row_actions(entry)}")
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

    def preview_url(self, entry_id: str, locale: str = "en") -> str:
        """The record previewed on the real Visas page (signed-in staff only)."""
        return web_url(f"{VISAS_PUBLIC_PATH}?qcPreview={RESOURCE[self.slug]}%3A{entry_id}", locale=locale)

    # ---- guarded delete ------------------------------------------------------------------------
    def _delete_preconditions(self, entry: BGEntry) -> str:  # type: ignore[override]
        if not self.is_list_fully_expanded():
            return f"list not fully expanded ({self.rendered_row_count()} of {self.total_entry_count()})"
        links = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
        if links.count() != 1:
            return f"{links.count()} delete links carry id {entry.entry_id}"
        rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
        if len(rows) != 1:
            return f"{len(rows)} rows carry delete id {entry.entry_id}"
        row = rows[0]
        if row["code"] != entry.code or row["code"].upper().startswith(REAL_CODE_PREFIX):
            return f"row {entry.entry_id} points at {row['code']!r}, not the captured {entry.code!r}"
        if row["title"].strip() != entry.entry_value or row["label"].strip() != entry.entry_value:
            return f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, not {entry.entry_value!r}"
        return ""

    def delete_disposable_entry(self, entry: BGEntry) -> bool:  # type: ignore[override]
        """Deletes exactly the captured record or refuses (False, never raises)."""
        try:
            if (not isinstance(entry, BGEntry) or entry.slug != self.slug or entry.prefix != self.prefix
                    or not entry.in_namespace() or entry.entry_id not in self.owned_entry_ids):
                _logger.error("DELETE REFUSED: %r is not a captured %s %s record", entry, self.prefix, self.slug)
                return False
            self.open_entry_en(entry.code)
            live = " ".join(self.entry_value().split())
            if live != " ".join(entry.entry_value.split()):
                _logger.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions(entry)
            if not reason:
                reason = self._delete_preconditions(entry)  # re-check immediately before the click
            if reason:
                _logger.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            names = [n for n in (entry.entry_value, entry.code) if n]
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                dialog.accept() if any(n in dialog.message for n in names) else dialog.dismiss()

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
            if not any(any(n in m for n in names) for m in dialogs):
                _logger.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not self.row_present(entry)
            if gone:
                self.owned_entry_ids.discard(entry.entry_id)
                _logger.info("deleted %r", entry)
            return gone
        except Exception as exc:  # noqa: BLE001
            _logger.error("delete of %r failed: %r", entry, exc)
            return False

    # ---- fields ------------------------------------------------------------------------------------
    def counter_limit(self, key: str) -> int | None:
        """N of the live "<len> / N" counter under the EN field (None = no counter)."""
        text = self._en(key).evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           const m = (c.innerText || '').match(/(\\d+)\\s*\\/\\s*(\\d+)/); if (m) return m[2]; }
                       return ''; }""")
        return int(text) if text else None

    def native_max_length(self, key: str, arabic: bool = False) -> int:
        node = self._ar(key) if arabic else self._en(key)
        return int(node.evaluate("el => el.maxLength"))

    def upload_block_text(self, key: str) -> str:  # type: ignore[override]
        label = UPLOAD_KEYS.get(self.slug, {}).get(key, key)
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                return ((c ? c.innerText : '') + ' ' + (el.value || '')).replace(/\\s+/g, ' ').trim(); }""",
            label)

    def fill_data(self, data: dict) -> "BGAdminPage":
        """Fills every key `data` carries (None = untouched). Keys: EN text /
        rich keys as-is, Arabic twins as `<key>_ar`, picklists by option label,
        `displayOrder` (str/int). Rich-text values are TYPED as plain text
        into CKEditor (no HTML), `activeStatus` (bool), uploads as
        `<key>_file` (+ optional `<key>_stem`)."""
        for key in TEXT_KEYS[self.slug]:
            if data.get(key) is not None:
                self.fill_en(key, str(data[key]))
        for key in AR_TEXT_KEYS[self.slug]:
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, str(data[f"{key}_ar"]))
        for key in RICH_KEYS[self.slug]:
            if data.get(key) is not None:
                self.fill_rich(key, data[key])
            if data.get(f"{key}_ar") is not None:
                self.fill_rich_ar(key, data[f"{key}_ar"])
        for key in PICKLIST_KEYS.get(self.slug, ()):
            if data.get(key):
                self.pick(key, data[key])
        if self.slug in HAS_DISPLAY_ORDER and data.get("displayOrder") is not None:
            self.fill_number_key("displayOrder", str(data["displayOrder"]))
        for key in UPLOAD_KEYS.get(self.slug, {}):
            if data.get(f"{key}_file"):
                self.upload(key, data[f"{key}_file"], data.get(f"{key}_stem"))
        if data.get("activeStatus") is not None:
            self.set_active_status(bool(data["activeStatus"]))
        return self

    def read_data(self) -> dict:
        """Every stored value of the open record, keyed like fill_data()."""
        values: dict = {}
        for key in TEXT_KEYS[self.slug]:
            values[key] = self.text_value(key)
        for key in AR_TEXT_KEYS[self.slug]:
            values[f"{key}_ar"] = self.ar_value(key)
        for key in RICH_KEYS[self.slug]:
            values[key] = self.rich_text(key)
            values[f"{key}_ar"] = self.rich_text_ar(key)
        for key in PICKLIST_KEYS.get(self.slug, ()):
            values[key] = self.picklist_value(key)
        if self.slug in HAS_DISPLAY_ORDER:
            values["displayOrder"] = self.text_value("displayOrder")
        for key in UPLOAD_KEYS.get(self.slug, {}):
            values[f"{key}_uploaded_as"] = self.stored_file_name(key)
        values["activeStatus"] = self.active_status_stored()
        return values

    def wait_for_rich_text_loaded(self, timeout: float = 20.0) -> None:  # type: ignore[override]
        keys = RICH_KEYS[self.slug]
        if not keys:
            return
        try:
            _wait_until(lambda: any(self.rich_text(k) != "" for k in keys), timeout=timeout, poll=0.5)
        except Exception:  # noqa: BLE001 — the caller compares whatever loaded
            pass

    # ---- tender-specific helpers are not valid on BG objects -----------------------------------------
    def _not_bg(self, *_a, **_k):
        raise NotImplementedError("tender-specific helper; use the BGAdminPage API")

    fill_tender = fill_tender_a = read_tender = a_tender_data = _not_bg
    identify_created_a = adopt_a = delete_own_entry = a_leftovers = b_leftovers = _not_bg
    row_status_a = wait_status = fill_reference_number = fill_valid_form = _not_bg
    row_status_text_for_reference = upload_tender_document = upload_boq = _not_bg
    # Inherited unguarded deletes (by code / title / loop): only delete_disposable_entry may delete here.
    delete_entry_by_code = delete_entry_by_title = delete_all_entries_by_title = delete_own_entry_d = _not_bg


def bg_data(slug: str, entry_value: str, section_key: str = "", **overrides) -> dict:
    """A complete, valid EN+AR record for `slug` whose ENTRY field is
    `entry_value` (must carry the caller's QCTEST-130701-<X>- prefix; for a
    checklist item that IS the sectionKey). Display Order 100, Active ticked.
    `section_key` = the parent key (sections: pageKey defaults to
    visas-immigration; items: sectionKey)."""
    common = {"displayOrder": 100, "activeStatus": True}
    if slug == SLUG_SECTION:
        data = {"pageKey": VISAS_PAGE_KEY, "sectionKey": section_key or entry_value.lower(),
                "sectionTitle": entry_value, "sectionTitle_ar": "قسم اختبار آلي " + entry_value[-12:],
                "sectionEyebrow": "QCTEST eyebrow", "sectionEyebrow_ar": "عنوان تمهيدي تجريبي",
                "sectionBody": f"{entry_value} body.", "sectionBody_ar": "نص قسم تجريبي.", **common}
    elif slug == SLUG_CHECKLIST:
        data = {"sectionKey": entry_value, "itemText": f"QCTEST checklist item {entry_value[-12:]}",
                "itemText_ar": "بند قائمة تحقق تجريبي", **common}
    elif slug == SLUG_HIGHLIGHT:
        data = {"sectionKey": section_key, "itemText": entry_value, "itemText_ar": "عنصر مميز تجريبي", **common}
    elif slug == SLUG_SUBTOPIC:
        data = {"sectionKey": section_key, "blockHeading": entry_value, "blockHeading_ar": "عنوان كتلة تجريبي",
                "blockBody": f"{entry_value} body.", "blockBody_ar": "نص كتلة تجريبي.",
                "blockStyle": OPT_BLOCK_STYLE_PARAGRAPH, **common}
    elif slug == SLUG_LINK:
        data = {"sectionKey": section_key, "linkTitle": entry_value, "linkTitle_ar": "رابط مصدر رسمي تجريبي",
                "linkDescription": "QCTEST official source", "linkDescription_ar": "مصدر رسمي تجريبي",
                "url": "https://www.qatarchamber.com/", "openBehavior": OPT_OPEN_NEW_TAB, **common}
    elif slug == SLUG_TILE:
        data = {"sectionKey": section_key, "tileLabel": entry_value, "tileLabel_ar": "مربع قطاع تجريبي", **common}
    else:
        raise ValueError("BG Info Page records cannot be created on Object Authoring")
    data.update(overrides)
    return data


# --- A ---
# =============================================================================
# Workflow / lifecycle helpers (Agent A) — cms/tests/visas_immigration/
# test_visas_workflow_control_panel.py.
#
# REAL PAGE 109104 (user decision 2026-10-06, bg_rules.md ADDENDUM b): the
# real Visas & Immigration BG Info Page may be unpublished / republished /
# edited ONLY while this process holds scratchpad/locks/real_page_109104.lock
# (atomic O_CREAT|O_EXCL, never broken), after a full snapshot, and must be
# restored + diffed afterwards. `BGRealPageA` refuses every state-changing
# call unless the lock it was given is still held by THIS process.
# =============================================================================
import contextlib as _contextlib
import json as _json
from datetime import datetime as _datetime

SCRATCH_DIR = _os.getenv(
    "QC_BG_SCRATCH_DIR",
    r"C:\Users\HP\AppData\Local\Temp\claude\d--Qatar-Chamber-QaterChamber-main"
    r"\97685594-6e82-429e-b38d-51cb93f050ad\scratchpad",
)
REAL_PAGE_LOCK = _os.path.join(SCRATCH_DIR, "locks", "real_page_109104.lock")
SNAPSHOT_DIR = _os.path.join(SCRATCH_DIR, "snapshots")
VISAS_PAGE_TITLE = "Visas & Immigration"


class RealPageLock:
    """Holder token of scratchpad/locks/real_page_109104.lock."""

    def __init__(self, agent: str):
        self.agent = agent
        self.token = f"{agent} {_datetime.now().isoformat(timespec='seconds')} pid={_os.getpid()}"
        self.held = False

    def try_acquire(self) -> bool:
        _os.makedirs(_os.path.dirname(REAL_PAGE_LOCK), exist_ok=True)
        try:
            fd = _os.open(REAL_PAGE_LOCK, _os.O_CREAT | _os.O_EXCL | _os.O_WRONLY)
        except FileExistsError:
            return False
        with _os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(self.token)
        self.held = True
        return True

    def still_mine(self) -> bool:
        try:
            with open(REAL_PAGE_LOCK, encoding="utf-8") as handle:
                return self.held and handle.read().strip() == self.token
        except OSError:
            return False

    def release(self) -> None:
        if self.still_mine():
            _os.remove(REAL_PAGE_LOCK)
        self.held = False


@_contextlib.contextmanager
def real_page_lock(agent: str, timeout_s: float = 1800.0):
    """Waits (max 30 min) for the lock, yields the RealPageLock, always
    releases it. Another agent's lock is never broken."""
    lock = RealPageLock(agent)
    try:
        _wait_until(lock.try_acquire, timeout=timeout_s, poll=5.0)
    except _WaitTimeoutError:
        holder = ""
        try:
            with open(REAL_PAGE_LOCK, encoding="utf-8") as handle:
                holder = handle.read()
        except OSError:
            pass
        raise TimeoutError(f"real_page_109104.lock still held after {timeout_s:.0f}s by {holder!r}") from None
    try:
        yield lock
    finally:
        lock.release()


class BGRealPageA(BGAdminPage):
    """Lock-guarded driver for the REAL Visas & Immigration page record."""

    RAW_KEYS = ("pageKey", "eyebrowLabel", "pageTitle")
    RAW_AR_KEYS = ("eyebrowLabel", "pageTitle")
    PLAIN_RESTORABLE = ("eyebrowLabel", "pageTitle")

    def __init__(self, page, lock: RealPageLock | None = None):
        super().__init__(page, SLUG_PAGE, "A")
        self.lock = lock

    def _require_lock(self) -> None:
        if self.lock is None or not self.lock.still_mine():
            raise PermissionError("refusing to change real page 109104 without holding real_page_109104.lock")

    # ---- reads ------------------------------------------------------------------
    def open_real_page(self) -> "BGRealPageA":
        self.open_entry_en(VISAS_PAGE_CODE)
        try:
            _wait_until(lambda: self.text_value("pageKey") == VISAS_PAGE_KEY, timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            raise AssertionError(f"{VISAS_PAGE_CODE} did not load pageKey {VISAS_PAGE_KEY!r}") from None
        return self

    def real_row(self) -> dict:
        self.open_list_all()
        rows = [r for r in self.list_rows() if r["entry_id"] == VISAS_PAGE_ID]
        if len(rows) != 1 or rows[0]["code"] != VISAS_PAGE_CODE or rows[0]["title"].strip() != VISAS_PAGE_TITLE:
            raise AssertionError(f"real page row 109104 not uniquely identifiable: {rows}")
        return rows[0]

    def real_status(self) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        raw = " ".join(self.real_row()["status"].split())
        return STATUS_INACTIVE if raw.casefold() == STATUS_INACTIVE.casefold() else normalize_status(raw)

    def read_page_record(self) -> dict:
        """Every stored value of the open real record (raw HTML for rich text)."""
        form = self._form()
        values = {k: self.text_value(k) for k in self.RAW_KEYS}
        values.update({f"{k}_ar": self.ar_value(k) for k in self.RAW_AR_KEYS})
        values["heroDescription_html"] = form.locator('textarea[name="ObjectField_heroDescription"]').first.input_value()
        values["heroDescription_ar_html"] = form.locator('[id="qc-ar-heroDescription"]').first.input_value()
        values["heroBanner_value"] = form.locator('input[name="ObjectField_heroBanner"]').first.input_value()
        values["heroBanner_block"] = _re.sub(r"\s+", " ", self.upload_block_text("heroBanner"))
        values["heroBanner_file"] = self.stored_file_name("heroBanner")
        values["activeStatus"] = self.active_status_stored()
        return values

    @staticmethod
    def diff(before: dict, after: dict, keys=None) -> list[str]:
        keys = keys or sorted(set(before) | set(after))
        return [f"{k}: {before.get(k)!r} -> {after.get(k)!r}" for k in keys if before.get(k) != after.get(k)]

    def write_snapshot(self, record: dict, status: str, public: dict, extra: dict | None = None) -> str:
        _os.makedirs(SNAPSHOT_DIR, exist_ok=True)
        stamp = _datetime.now().strftime("%Y%m%d_%H%M%S")
        path = _os.path.join(SNAPSHOT_DIR, f"109104_A_{stamp}.json")
        with open(path, "w", encoding="utf-8") as handle:
            _json.dump({"record": record, "workflow_status": status, "public": public, **(extra or {})},
                       handle, ensure_ascii=False, indent=1)
        return path

    # ---- guarded changes ------------------------------------------------------------
    def real_row_actions(self) -> list[str]:
        self.real_row()
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-history="{VISAS_PAGE_ID}"])').first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def unpublish_real_page(self) -> list[str]:
        """Row action Unpublish on 109104 (lock held, identity re-checked)."""
        return self.real_row_action("unpublish")

    def real_row_action(self, action: str) -> list[str]:
        """Row action `unpublish` / `publish` on 109104 (lock held, identity re-checked)."""
        if action not in ("unpublish", "publish"):
            raise ValueError(f"real_row_action refuses {action!r}")
        self._require_lock()
        self.real_row()
        control = self.page.locator(f'[data-qc-oel-{action}="{VISAS_PAGE_ID}"]')
        if control.count() != 1:
            raise AssertionError(f"{control.count()} {action} controls carry id {VISAS_PAGE_ID}")
        messages: list[str] = []

        def _accept(dialog):
            messages.append(f"{dialog.type}: {dialog.message}")
            try:
                dialog.accept()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _accept)
        try:
            control.first.click(force=True)
            self._wait_for_settle()
        finally:
            self.page.remove_listener("dialog", _accept)
        self.last_row_action_dialogs = messages
        return messages

    def set_plain_field(self, key: str, value: str, arabic: bool = False) -> "BGRealPageA":
        self._require_lock()
        if key not in self.PLAIN_RESTORABLE:
            raise ValueError(f"only {self.PLAIN_RESTORABLE} may be changed on the real page by Agent A")
        self.fill_ar(key, value) if arabic else self.fill_en(key, value)
        return self

    def publish_open_record(self) -> bool:
        """Publish on the open real record form; True when the save went through."""
        self._require_lock()
        if self.text_value("pageKey") != VISAS_PAGE_KEY:
            raise AssertionError("the open form is not the real Visas page")
        self.click_publish()
        return self.save_went_through()

    def save_open_record_as_draft(self) -> bool:
        self._require_lock()
        if self.text_value("pageKey") != VISAS_PAGE_KEY:
            raise AssertionError("the open form is not the real Visas page")
        self.click_save_as_draft()
        return self.save_went_through()

    def wait_real_status(self, expected: tuple, timeout: float = 120.0) -> str:
        seen = {"status": ""}

        def _reached() -> bool:
            seen["status"] = self.real_status()
            return seen["status"] in expected

        try:
            _wait_until(_reached, timeout=timeout, poll=3.0)
        except _WaitTimeoutError:
            pass
        return seen["status"]


# --- B ---
# =============================================================================
# Page-level / section field helpers (Agent B) — cms/tests/visas_immigration/
# test_visas_page_fields_control_panel.py + test_visas_section_fields_control_panel.py.
#
# BGFieldsAdminPageB: UI helpers for B's OWN QCTEST-130701-B- records (rich
# text via the editor's own Source control, typed input, counters, picking an
# existing Documents & Media file). BGRealPageB: Agent A's lock-guarded real
# page driver re-namespaced to B; every write refuses unless B holds
# real_page_109104.lock and the open form is the real Visas page.
#
# LIVE 2026-10-06 (read-only recon): the real Hero Banner is D&M file entry
# 109054 (uuid 64ece315-5820-c87c-71ad-8978563b196a,
# visas-hero-passport-3d-1254x1254.png, folder 109052 "visas-immigration").
# Clicking its card in the item selector closes the picker and sets the
# hidden ObjectField_heroBanner to "109054" (dry run, nothing saved).
# =============================================================================
B_ORIGINAL_BANNER_ID = "109054"
B_ORIGINAL_BANNER_NAME = "visas-hero-passport-3d-1254x1254.png"
B_ORIGINAL_BANNER_UUID = "64ece315-5820-c87c-71ad-8978563b196a"

_B_CKE_NAME_JS = """([key, arabic]) => {
    if (!window.CKEDITOR) return '';
    const names = Object.keys(CKEDITOR.instances);
    return names.find(n => arabic ? n === 'qc-ar-' + key : n.endsWith('-ObjectField_' + key) || n === 'ObjectField_' + key) || '';
}"""


class BGFieldsAdminPageB(BGAdminPage):
    """Agent B field helpers. Writes go to whatever form is open — callers
    open only their own captured records (see open_own) or, through
    BGRealPageB, the lock-guarded real page."""

    # ---- own records ---------------------------------------------------------------
    def require_own(self, entry: BGEntry) -> None:
        if (not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != self.prefix
                or entry.slug != self.slug or entry.entry_id not in self.owned_entry_ids):
            raise ValueError(f"refusing {entry}: not a captured {self.prefix} {self.slug} record")

    def open_own(self, entry: BGEntry) -> "BGFieldsAdminPageB":
        self.require_own(entry)
        self.open_entry_en(entry.code)
        self.wait_for_rich_text_loaded()
        return self

    # ---- rich text (CKEditor 4) ------------------------------------------------------
    def cke_name(self, key: str, arabic: bool = False) -> str:
        return self.page.evaluate(_B_CKE_NAME_JS, [key, arabic])

    def rich_data(self, key: str, arabic: bool = False) -> str:
        """The editor's current HTML (CKEditor getData) — '' when empty."""
        name = self.cke_name(key, arabic)
        if not name:
            return ""
        return self.page.evaluate("(n) => CKEDITOR.instances[n].getData()", name)

    def _rich_body_b(self, key: str, arabic: bool = False):
        frame = self._rich_ar_iframe(key) if arabic else self._rich_iframe(key)
        return self.page.frame_locator(frame).locator("body")

    def clear_rich_b(self, key: str, arabic: bool = False) -> "BGFieldsAdminPageB":
        """Empties the editor the way a user does: click, select all, Delete."""
        body = self._rich_body_b(key, arabic)
        body.wait_for(state="visible")
        body.click()
        for combo in ("Delete", "Backspace"):
            self.page.keyboard.press("Control+A")
            self.page.keyboard.press(combo)
        return self

    def type_rich_b(self, key: str, text: str, arabic: bool = False) -> "BGFieldsAdminPageB":
        """Replaces the editor content with TYPED `text` ("\\n" = Enter = new paragraph)."""
        self.clear_rich_b(key, arabic)
        if text:
            self.page.keyboard.type(text)
        return self

    def set_rich_source(self, key: str, html: str, arabic: bool = False) -> "BGFieldsAdminPageB":
        """Writes `html` through the editor's own Source control (toolbar
        "Source" -> source textarea -> "Source" back to WYSIWYG)."""
        name = self.cke_name(key, arabic)
        if not name:
            raise AssertionError(f"no CKEditor instance for {key!r} (arabic={arabic})")
        chrome = self.page.locator(f'[id="cke_{name}"]')
        chrome.locator("a.cke_button__source").first.click()
        # Liferay's Source mode is a CodeMirror editor (live 2026-10-06); its own
        # setValue() is used instead of typing (CodeMirror auto-closes tags).
        source = chrome.locator(".CodeMirror").first
        source.wait_for(state="visible", timeout=15000)
        source.evaluate("(el, html) => el.CodeMirror.setValue(html)", html)
        chrome.locator("a.cke_button__source").first.click()
        _wait_until(lambda: self.page.evaluate("(n) => CKEDITOR.instances[n].mode", name) == "wysiwyg",
                    timeout=15.0, poll=0.3)
        chrome.locator('iframe[title="editor"]').first.wait_for(state="visible", timeout=15000)
        return self

    # ---- plain inputs ----------------------------------------------------------------
    def _field(self, key: str, arabic: bool = False):
        return self._ar(key) if arabic else self._en(key)

    def type_text(self, key: str, text: str, arabic: bool = False) -> "BGFieldsAdminPageB":
        """Click, select all, Delete, then TYPE `text` key by key (counter/limit
        handlers see real key events), then Tab out."""
        box = self._field(key, arabic)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if text:
            self.page.keyboard.type(text)
        box.press("Tab")
        return self

    def value_of(self, key: str, arabic: bool = False) -> str:
        return self._field(key, arabic).input_value()

    def counter_reading(self, key: str, arabic: bool = False) -> tuple[int, int] | None:
        """(current, limit) from the live "<len> / N" counter under the field."""
        text = self._field(key, arabic).evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 4 && c; i++, c = c.parentElement) {
                           const m = (c.innerText || '').match(/(\\d+)\\s*\\/\\s*(\\d+)/); if (m) return m[1] + '/' + m[2]; }
                       return ''; }""")
        if not text:
            return None
        current, limit = text.split("/")
        return int(current), int(limit)

    def field_flags(self, key: str, arabic: bool = False) -> dict:
        """{required_attr, aria_required, aria_invalid, label, label_star} of the field."""
        return self._field(key, arabic).evaluate(
            """el => { let c = el.parentElement, label = null;
                       for (let i = 0; i < 6 && c && !label; i++, c = c.parentElement) label = c.querySelector('label');
                       const text = label ? label.innerText.trim() : '';
                       return {required_attr: !!el.required, aria_required: el.getAttribute('aria-required') === 'true',
                               aria_invalid: el.getAttribute('aria-invalid') === 'true', label: text,
                               label_star: /\\*/.test(text)}; }""")

    def errors_for(self, key: str) -> list[str]:
        """Inline field errors owned by `key` (EN `ObjectField_<key>` or AR `qc-ar-<key>`)."""
        names = {f"ObjectField_{key}", f"qc-ar-{key}"}
        return [o["text"] for o in self.field_error_owners() if names & set(o["field"].split(","))]

    def rich_block_text(self, key: str) -> str:
        """All text in a rich-text field's block (label, inline messages)."""
        node = self._form().locator(f'[name="ObjectField_{key}"]:not([type="hidden"])').first
        return node.evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 6 && c && !c.querySelector('label'); i++) c = c.parentElement;
                       return c ? c.innerText.replace(/\\s+/g, ' ').trim() : ''; }""")

    # ---- attachments -------------------------------------------------------------------
    def file_preview_href(self, key: str) -> str:
        """href of the field's "Preview" link (identifies the stored D&M file)."""
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !c.querySelector('a'); i++) c = c.parentElement;
                const a = c ? [...c.querySelectorAll('a')].find(x => x.innerText.trim() === 'Preview') : null;
                return a ? a.getAttribute('href') : ''; }""") or ""

    def has_thumbnail(self, key: str) -> bool:
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return bool(node.evaluate(
            """(el) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !c.querySelector('img'); i++) c = c.parentElement;
                return !!(c && [...c.querySelectorAll('img')].some(i => i.offsetParent !== null)); }"""))

    def select_existing_file(self, key: str, file_entry_id: str, search: str) -> dict:
        """Opens the field's item selector, searches `search`, clicks the ONE card
        whose data-value carries fileEntryId == `file_entry_id` (never a
        positional pick). Returns {cards, hidden_value, block}."""
        self._open_picker(key)
        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        modal.wait_for(timeout=30000)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        box = frame.locator('input[name*="keywords"], input[placeholder*="Search"], input[type="search"]').first
        box.wait_for(state="attached", timeout=30000)
        box.fill(search)
        box.press("Enter")
        card = frame.locator(f'[data-value*=\'"fileEntryId":"{file_entry_id}"\']')
        card.first.wait_for(state="attached", timeout=30000)
        cards = card.count()
        if cards != 1:
            self.page.keyboard.press("Escape")
            raise AssertionError(f"{cards} picker cards carry fileEntryId {file_entry_id}")
        card.first.click()
        modal.wait_for(state="detached", timeout=20000)
        hidden = self._form().locator(f'input[name="ObjectField_{key}"]').first.input_value()
        return {"cards": cards, "hidden_value": hidden, "block": self.upload_block_text(key)}


class BGRealPageB(BGFieldsAdminPageB, BGRealPageA):
    """Agent A's lock-guarded real-page driver under Agent B's namespace, plus
    guarded writes for every hero field (Eyebrow, Page Title, Hero
    Description, Hero Banner). Reads are free; writes need the held lock."""

    def __init__(self, page, lock: RealPageLock | None = None):
        BGAdminPage.__init__(self, page, SLUG_PAGE, "B")
        self.lock = lock

    def _guard(self) -> None:
        self._require_lock()
        if self.text_value("pageKey") != VISAS_PAGE_KEY or getattr(self, "_entry_code", None) != VISAS_PAGE_CODE:
            raise AssertionError("the open form is not the real Visas & Immigration page record")

    def real_row(self) -> dict:  # type: ignore[override]
        """Row of 109104 identified by entry id + code (B's Page Title cases change
        the ENTRY-column title while the lock is held, so the title is not part of
        the identity here)."""
        self.open_list_all()
        rows = [r for r in self.list_rows() if r["entry_id"] == VISAS_PAGE_ID]
        if len(rows) != 1 or rows[0]["code"] != VISAS_PAGE_CODE:
            raise AssertionError(f"real page row 109104 not uniquely identifiable: {rows}")
        return rows[0]

    def read_page_record(self) -> dict:  # type: ignore[override]
        values = BGRealPageA.read_page_record(self)
        values["heroDescription_cke"] = self.rich_data("heroDescription")
        values["heroDescription_ar_cke"] = self.rich_data("heroDescription", arabic=True)
        values["heroBanner_href"] = self.file_preview_href("heroBanner")
        return values

    # ---- guarded writes ------------------------------------------------------------------
    def b_fill(self, key: str, value: str, arabic: bool = False) -> "BGRealPageB":
        self._guard()
        self.fill_ar(key, value) if arabic else self.fill_en(key, value)
        return self

    def b_type(self, key: str, value: str, arabic: bool = False) -> "BGRealPageB":
        self._guard()
        return self.type_text(key, value, arabic)

    def b_rich_source(self, key: str, html: str, arabic: bool = False) -> "BGRealPageB":
        self._guard()
        return self.set_rich_source(key, html, arabic)

    def b_rich_type(self, key: str, text: str, arabic: bool = False) -> "BGRealPageB":
        self._guard()
        return self.type_rich_b(key, text, arabic)

    def b_attempt_banner(self, file_path: str, stem: str) -> dict:
        self._guard()
        return self.attempt_upload("heroBanner", file_path, stem)

    def b_select_original_banner(self) -> dict:
        self._guard()
        return self.select_existing_file("heroBanner", B_ORIGINAL_BANNER_ID, _os.path.splitext(B_ORIGINAL_BANNER_NAME)[0])

    def b_set_active(self, active: bool) -> "BGRealPageB":
        self._guard()
        self.set_active_status(active)
        return self

    def b_publish(self) -> dict:
        self._guard()
        self.click_publish()
        went = self.save_went_through()
        return {"went_through": went, "refused": self.save_was_refused(), "evidence": self.refusal_evidence(),
                "messages": self.all_messages_text(),
                "editbar": self.success_messages(MSG_SAVED_AND_PUBLISHED, 10.0) if went else self.editbar_texts()}

# --- C ---
# (Agent C: checklist / highlight / sub-topic helpers go here.)
class BGItemsAdminPageC(BGAdminPage):
    """Agent C additions (checklist items, highlight card / items, sub-topic
    blocks). Pure UI helpers — identity, capture and delete stay in
    BGAdminPage. Construct with agent="C"."""

    def _rich_frame_el(self, key: str, arabic: bool):
        return self.page.locator(self._rich_ar_iframe(key) if arabic else self._rich_iframe(key)).first

    def _wait_rich_mounted(self, key: str, arabic: bool, timeout_ms: int = 90000) -> None:
        """The AR CKEditors mount seconds after the EN ones on a slow qcdev, and
        an EMPTY editable body can measure 0 px high (Playwright then calls it
        hidden): wait for the iframe ELEMENT itself to be visible instead."""
        frame_el = self._rich_frame_el(key, arabic)
        try:
            frame_el.wait_for(state="attached", timeout=timeout_ms)
        except Exception:
            self.evidence(f"rich_not_mounted_{key}_{'ar' if arabic else 'en'}")
            _logger.error("rich editor %s (ar=%s) not mounted; url %s; cke nodes %s", key, arabic, self.page.url,
                          self.page.evaluate("() => [...document.querySelectorAll('div.cke')].map(n => n.id)"))
            raise
        try:
            frame_el.scroll_into_view_if_needed(timeout=10000)
        except Exception:  # noqa: BLE001 — visibility is awaited below
            pass
        frame_el.wait_for(state="visible", timeout=timeout_ms)
        self._rich_body(key, arabic).wait_for(state="attached", timeout=timeout_ms)

    def _focus_rich(self, key: str, arabic: bool) -> None:
        self._wait_rich_mounted(key, arabic)
        body = self._rich_body(key, arabic)
        try:
            body.click(timeout=5000)
        except Exception:  # noqa: BLE001 — zero-height empty body: click the frame instead
            self._rich_frame_el(key, arabic).click()

    def fill_rich(self, key: str, text: str) -> "BGItemsAdminPageC":  # type: ignore[override]
        self._focus_rich(key, False)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.type(text)
        return self

    def fill_rich_ar(self, key: str, text: str) -> "BGItemsAdminPageC":  # type: ignore[override]
        self._focus_rich(key, True)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.type(text)
        return self

    def _rich_body(self, key: str, arabic: bool = False):
        frame = self._rich_ar_iframe(key) if arabic else self._rich_iframe(key)
        return self.page.frame_locator(frame).locator("body")

    def clear_rich(self, key: str, arabic: bool = False) -> "BGItemsAdminPageC":
        """Empties a CKEditor body the way a user does: click, select all, Delete."""
        self._focus_rich(key, arabic)
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Delete")
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Backspace")
        return self

    def type_rich(self, key: str, text: str, arabic: bool = False) -> "BGItemsAdminPageC":
        """Replaces a CKEditor body with `text` ("\\n" = Enter = a new paragraph)."""
        self.clear_rich(key, arabic)
        if text:
            self.page.keyboard.type(text)
        return self

    def rich_html(self, key: str, arabic: bool = False) -> str:
        try:
            return self._rich_body(key, arabic).inner_html()
        except Exception:  # noqa: BLE001 — evidence only
            return ""

    def picklist_options(self, key: str, probe_text: str = "QCTEST free text") -> dict:
        """Reads the picklist's options and probes free-text entry: types
        `probe_text` into the combobox search box, tabs away and reports whether
        that text became the stored value. {labels, free_text_accepted,
        stored_after_probe, box_after_probe}. Leaves the stored value as found."""
        prefix = self._picklist_prefix(key)
        toggle = self.page.locator(f'button[aria-controls="{prefix}-listbox"]')
        options = self.page.locator(f'li[role="option"][id^="{prefix}-option-"]')
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        before = hidden.input_value()
        toggle.click()
        options.first.wait_for(state="visible", timeout=10000)
        labels = [o.get_attribute("data-option-label") or o.inner_text().strip() for o in options.all()]
        keys = [(o.get_attribute("id") or "").replace(f"{prefix}-option-", "") for o in options.all()]
        self.page.keyboard.press("Escape")
        if options.first.is_visible():
            toggle.click()
        box = self.page.locator(f'input[id="{prefix}-select-from-list-input"]')
        stored_after, box_after = before, ""
        if box.count():
            box.first.click()
            self.page.keyboard.press("Control+A")
            self.page.keyboard.type(probe_text)
            self.page.keyboard.press("Tab")
            stored_after = hidden.input_value()
            box_after = box.first.input_value()
        accepted = stored_after not in ("", before, *keys) or probe_text in stored_after
        return {"labels": labels, "option_keys": keys, "free_text_accepted": accepted,
                "stored_before": before, "stored_after_probe": stored_after, "box_after_probe": box_after}

    def clear_picklist_is_empty(self, key: str) -> bool:
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        return hidden.input_value() == ""

    def edit_and_publish(self, entry: BGEntry, data: dict, rich_raw: dict | None = None) -> dict:
        """Re-opens ONE captured record by its code, applies `data` (fill_data
        keys) and `rich_raw` ({key: text} typed after a clear; "" = empty), clicks
        Publish and returns the save evidence. Own captured records only."""
        if not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != self.prefix \
                or entry.slug != self.slug or entry.entry_id not in self.owned_entry_ids:
            raise ValueError(f"edit_and_publish refuses {entry}: not a captured {self.prefix} {self.slug} record")
        self.open_entry_en(entry.code)
        self.wait_for_rich_text_loaded()
        if data:
            self.fill_data(data)
        for key, text in (rich_raw or {}).items():
            arabic = key.endswith("_ar")
            self.type_rich(key[:-3] if arabic else key, text, arabic=arabic)
        self.click_publish()
        return {"went_through": self.save_went_through(), "refused": self.save_was_refused(),
                "evidence": self.refusal_evidence(), "messages": self.all_messages_text()}

    def restore_entry_value(self, entry: BGEntry) -> bool:
        """When a test emptied/blanked the ENTRY field of its OWN record and the
        app accepted it, puts the captured value back so the guarded delete can
        verify identity again. Opens the record by its captured code only."""
        if not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != self.prefix \
                or entry.slug != self.slug or entry.entry_id not in self.owned_entry_ids:
            return False
        self.open_entry_en(entry.code)
        if " ".join(self.entry_value().split()) == " ".join(entry.entry_value.split()):
            return True
        if self.entry_field in RICH_KEYS[self.slug]:
            self.type_rich(self.entry_field, entry.entry_value)
        else:
            self.fill_en(self.entry_field, entry.entry_value)
        self.click_publish()
        self.open_entry_en(entry.code)
        return " ".join(self.entry_value().split()) == " ".join(entry.entry_value.split())

    def field_marked_required(self, key: str) -> dict:
        """Whether the EN field `key` is flagged mandatory on the open form:
        {required_attr, aria_required, label, label_star}."""
        node = self._form().locator(f'[name="ObjectField_{key}"]').first
        return node.evaluate(
            """el => { let c = el.parentElement, label = null;
                       for (let i = 0; i < 6 && c && !label; i++, c = c.parentElement) label = c.querySelector('label');
                       const text = label ? label.innerText.trim() : '';
                       return {required_attr: !!el.required, aria_required: el.getAttribute('aria-required') === 'true',
                               label: text, label_star: /\\*/.test(text) ||
                               !!(label && label.querySelector('.reference-mark, .lexicon-icon-asterisk, [class*="required"]'))}; }""")


# --- D ---
# (Agent D: links / images / display order / item status helpers go here.)
# Agent D (supporting image + alt, official source links, display order,
# item Active Status, Arabic authoring). Pure UI helpers on records THIS
# session captured — identity, capture and the guarded delete stay in
# BGAdminPage. Construct with agent="D".
D_SUBMIT_NAME_ANY_LOCALE = _re.compile(r"^\s*(Publish|Submit for Review|نشر|إرسال للمراجعة)\s*$")


class BGAdminPageD(BGItemsAdminPageC):
    """Agent D additions (reuses Agent C's picklist_options / restore_entry_value /
    rich-text helpers). Every write helper refuses a record that is not a
    captured QCTEST-130701-D- entry of this driver's object."""

    def _require_owned(self, entry: BGEntry) -> None:
        if (not isinstance(entry, BGEntry) or not entry.in_namespace() or entry.prefix != self.prefix
                or entry.slug != self.slug or entry.entry_id not in self.owned_entry_ids):
            raise ValueError(f"refusing {entry}: not a captured {self.prefix} {self.slug} record")

    # ---- navigation ------------------------------------------------------------------
    def open_owned(self, entry: BGEntry, locale: str = "en") -> "BGAdminPageD":
        """Opens ONE captured record by its captured code (EN or AR interface)."""
        self._require_owned(entry)
        if locale == "en":
            self.open_entry_en(entry.code)
        else:
            self.open(self._manage_url(edit_entry=entry.code, locale=locale))
            self._entry_code = entry.code
            self.page.locator(f'{self.FORM} [name="ObjectField_{self.entry_field}"]').first.wait_for(
                state="attached", timeout=90000)
            try:
                _wait_until(lambda: self.entry_value() != "", timeout=15.0, poll=0.5)
            except _WaitTimeoutError:
                pass
            _dismiss_chatbot_launcher(self.page)
        self.wait_for_rich_text_loaded()
        return self

    def stored(self, entry: BGEntry) -> dict:
        """Re-opens the captured record and returns every stored value (read_data)."""
        for attempt in (1, 2):  # qcdev sometimes renders a CKEditor iframe late: one re-open
            try:
                self.open_owned(entry)
                return self.read_data()
            except Exception:  # noqa: BLE001
                if attempt == 2:
                    raise
        return {}

    # ---- typing the way a user does ------------------------------------------------------
    def type_into(self, key: str, text: str) -> "BGAdminPageD":
        """Click, select all, delete, then TYPE `text` key by key into the EN
        input (number inputs silently drop characters they cannot hold, e.g.
        spaces — read the value back with text_value())."""
        box = self._en(key)
        box.click()
        box.press("Control+A")
        box.press("Delete")
        if text:
            self.page.keyboard.type(text)
        box.press("Tab")
        return self

    # ---- save on an already-open record -----------------------------------------------------
    def publish_open(self) -> dict:
        """Clicks Publish (EN or AR label) on the open form; returns the save evidence."""
        self.SUBMIT_NAME = D_SUBMIT_NAME_ANY_LOCALE
        self.click_publish()
        return {"went_through": self.save_went_through(), "refused": self.save_was_refused(),
                "evidence": self.refusal_evidence(), "messages": self.editbar_texts(),
                "field_errors": self._safe_field_errors(), "field_error_owners": self.field_error_owners(),
                "native": dict(getattr(self, "last_native_messages", {})),
                "invalid": list(getattr(self, "last_invalid_fields", []))}

    def edit_publish_typed(self, entry: BGEntry, data: dict, typed: dict | None = None,
                           locale: str = "en") -> dict:
        """Re-opens ONE captured record, applies `data` (fill_data keys) and
        `typed` ({key: text} via type_into), clicks Publish, returns evidence."""
        self.open_owned(entry, locale=locale)
        if data:
            self.fill_data(data)
        for key, text in (typed or {}).items():
            self.type_into(key, text)
        return self.publish_open()

    # ---- field facts ---------------------------------------------------------------------------
    def field_label(self, key: str) -> str:
        """Visible label text of the EN field `key` (incl. a trailing '*' / 'Required' marker)."""
        return self._en(key).evaluate(
            """el => { let c = el.parentElement;
                       for (let i = 0; i < 6 && c; i++, c = c.parentElement) {
                           const l = c.querySelector('label'); if (l) return l.innerText.replace(/\\s+/g, ' ').trim(); }
                       return ''; }""")

    def field_required(self, key: str) -> dict:
        """{native: el.required, label: <label text>, marked: '*' or 'Required' in the label}."""
        label = self.field_label(key)
        native = bool(self._en(key).evaluate("el => el.required"))
        return {"native": native, "label": label, "marked": ("*" in label) or ("Required" in label)}

    def upload_field_state(self, key: str) -> dict:
        """What the upload block shows: {text, thumbnail (an <img> inside the block), current_file}."""
        label = UPLOAD_KEYS.get(self.slug, {}).get(key, key)
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        info = node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                const imgs = c ? [...c.querySelectorAll('img')].filter(i => i.offsetParent !== null) : [];
                return {text: ((c ? c.innerText : '') + ' ' + (el.value || '')).replace(/\\s+/g, ' ').trim(),
                        thumbnail: imgs.length > 0, thumbnail_src: imgs.length ? imgs[0].getAttribute('src') : ''}; }""",
            label)
        info["current_file"] = self.stored_file_name(key)
        return info

    def picklist_free_text_stored(self, key: str, text: str) -> dict:
        """Types `text` into the picklist's combobox box (a typeahead filter) and
        reports what the form would store: {typed_box, stored_value, stored_label}."""
        prefix = self._picklist_prefix(key)
        box = self.page.locator(f'[id="{prefix}-select-from-list-input"]').first
        box.click()
        self.page.keyboard.type(text)
        self.page.keyboard.press("Tab")
        hidden = self._form().locator(f'input[type="hidden"][name="ObjectField_{key}"]').first
        return {"typed_box": box.input_value(), "stored_value": hidden.input_value(),
                "stored_label": self.picklist_value(key)}

    # ---- create with a look at the form before the save -----------------------------------------
    def create_with(self, data: dict, publish: bool = True, before_save=None) -> tuple:
        """Like create_entry(), but returns (entry | None, evidence) where
        evidence = {before: <before_save(self) result>, save: <publish/draft evidence>,
        arabic_saved}. `before_save` runs on the filled, unsaved create form."""
        value = data.get(self.entry_field)
        if not value or not str(value).casefold().startswith(self.prefix.casefold()):
            raise ValueError(f"{self.entry_field} must start with {self.prefix}")
        ids_before = self.snapshot_ids()
        self.open_create_form_en()
        self.fill_data(data)
        before = before_save(self) if before_save else None
        if publish:
            save = self.publish_open()
        else:
            self.click_save_as_draft()
            save = {"went_through": self.save_went_through(), "refused": self.save_was_refused(),
                    "evidence": self.refusal_evidence(), "messages": self.editbar_texts()}
        evidence = {"before": before, "save": save, "arabic_saved": False, "created_despite_error": False}
        if not save["went_through"]:
            # Live 2026-10-06: the form can report "This record was not saved: ...
            # error code: 1062" while the headless fallback DID create (and publish)
            # the record. Capture it (read-only diff) so it is never orphaned.
            entry = self.identify_created(str(value), ids_before)
            evidence["created_despite_error"] = entry is not None
            return entry, evidence
        evidence["arabic_saved"] = self.wait_arabic_saved()
        evidence["messages_after_arabic"] = self.editbar_texts()
        return self.identify_created(str(value), ids_before), evidence

"""
cms/pages/business_opportunities/opportunity_admin_page.py — Business
Opportunities (PBI 130697) Object Authoring Page Objects. CORE OWNER: Agent A.

Shared file: other agents add their own methods ONLY in a `# --- <AGENT> ---`
section at the end (small targeted edits, re-read first). Nothing in the core
section is renamed or removed without the owner.

LIVE RECON 2026-10-07 (qcdev, Site Content Editor 156488 / Author 156492,
read-only probes, see the Agent A Phase-3 report):

Objects (all `/web/qatar-chamber/manage-<slug>`):
  business-opportunity      BusinessOpportunity — the record (fields below)
  business-opportunity-page the listing page Hero/CTA + tab labels. ONE record
                            only (`QC-BIZOPP-130697-PAGE`): no "+ Add New", no
                            Delete row action ("This page holds this one record
                            only.") — it can only be edited in place, so every
                            test that touches it snapshots and restores it.
  opportunity-section       Section Title (EN/AR), Section Number, Display Order,
                            Active Status, relation -> Business Opportunity
  key-highlight             Item Text (rich EN/AR), Display Order, Active, relation
  co-investment             Label (EN/AR), Percentage (text), Value (text),
                            Display Order, Active, relation
  downloadable-resource     Document Title (EN/AR), File (.pdf), Display Order,
                            Active, relation (also used by OpportunitySubmission)
  project-gallery-item      Gallery Image (.jpg/.png/.svg), Display Order, Active,
                            relation (also used by OpportunitySubmission)

Entries list: the ENTRY column shows the entry's CODE (externalReferenceCode),
not its title — real rows read `QC-BIZOPP-130697-NN[-SEC-NN|-KH-NN|-CI-NN|
-DR-NN|-GAL-NN]`. A record created through the form gets a generated code, so
identity is captured by diffing the list's entry ids and reading the new
record's own title field back by code (never by position).

Relation pickers (`ObjectField_r_<rel>_c_businessOpportunityId`) are Liferay
"select from list" fields whose option label is the PARENT's entry code.

BusinessOpportunity form (Editor): opportunityTitle* (+AR*), sector (picklist),
subSector (+AR), country* (+AR*, plain text), companyOrganizationName* (+AR*),
investmentBrief (rich, EN required), investmentAmount* (number), currency*,
investmentType / timeline / riskProfile / industryPool (picklists),
bannerImage* / opportunityLogo* / heroBanner* (.jpg,.png,.svg), heroSummary
(rich, EN required), overviewBody (rich, EN required), investmentAmountRange*,
minimumTicket, submitterName* / submitterEntityType* / submittedByLocation*
(+AR*), submittedByLogo*, publishDate* / archiveDate* (DATE only — day
granularity, dd/mm/yyyy box over a hidden yyyy-mm-dd input), displayOrder*,
activeStatus (checkbox), lifecycleStatus (picklist Draft / Published /
Archived). Buttons: Editor "Save as Draft" / "Publish"; Author "Save as Draft" /
"Submit for Review". Author rows on records it does not own: View / Preview /
History only.

Anonymous `manage-*` URLs answer HTTP 404 with the site's "Coming Soon" page
(no login redirect) — OBJECT-AUTHORING-GUIDE §1.

Public: listing `/web/qatar-chamber/business-opportunities` (cards
`a.qc-bol-card` -> `business-opportunity?opportunity=<entry code>`), detail
sections `.qc-bod-*` (prose, stats, highlights, submitter, defs, gallery
`.qc-bod-shot`, files `.qc-bod-file`).

DELETE SAFETY (hard rule 1): `delete_own_entry()` deletes ONE record that this
object instance captured at creation (entry id adopted from a list-id diff,
title in the caller's QCTEST-130697-<X>- namespace, code not a real
QC-BIZOPP-130697- code), re-reads the record's title by code and the row's id /
code / label immediately before the click, and accepts the confirm() only when
it names that code. No positional, looping or substring delete exists here.
"""

from __future__ import annotations

import os as _os
import re as _re
from dataclasses import dataclass as _dataclass
from datetime import date as _date
from datetime import timedelta as _timedelta

from cms.pages.components.object_authoring_page import ObjectAuthoringPage, normalize_status, shows_message
from cms.pages.tenders.tender_admin_page import TenderFieldsAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import control_panel_url, web_url
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher

_log = _get_logger("opportunity_admin_page")

# ---- objects ----------------------------------------------------------------
BIZOPP_SLUG = "business-opportunity"
LISTING_PAGE_SLUG = "business-opportunity-page"
SECTION_SLUG = "opportunity-section"
KEY_HIGHLIGHT_SLUG = "key-highlight"
CO_INVESTMENT_SLUG = "co-investment"
RESOURCE_SLUG = "downloadable-resource"
GALLERY_SLUG = "project-gallery-item"

REAL_CODE_PREFIX = "QC-BIZOPP-130697-"
LISTING_PAGE_CODE = "QC-BIZOPP-130697-PAGE"
QCTEST_NAMESPACE = "QCTEST-130697-"
# Retest runs (ready-bug retests) use their own namespace; both are QCTEST-only.
QCTEST_NAMESPACES = (QCTEST_NAMESPACE, "QCTEST-R30-")

# ---- accounts -----------------------------------------------------------------
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492"}

# ---- edit-bar messages (exact) ----------------------------------------------------
MSG_DRAFT_SAVED = "Draft saved."
MSG_SAVED_AND_PUBLISHED = "Saved and published."
MSG_SUBMITTED_FOR_REVIEW = "Saved and submitted for review."
MSG_ARABIC_SAVED = "Arabic content saved for this record."
MSG_ARABIC_NOT_SAVED = "Arabic content was not"
MSG_BLOCKED = "Please complete the required fields"
# entries-list badge of a Published record whose Active Status is unticked
STATUS_INACTIVE = "Inactive"

# ---- BusinessOpportunity field keys ------------------------------------------------
K_TITLE = "opportunityTitle"
K_SECTOR = "sector"
K_SUB_SECTOR = "subSector"
K_COUNTRY = "country"
K_COMPANY = "companyOrganizationName"
K_BRIEF = "investmentBrief"
K_AMOUNT = "investmentAmount"
K_CURRENCY = "currency"
K_INVESTMENT_TYPE = "investmentType"
K_TIMELINE = "timeline"
K_RISK = "riskProfile"
K_INDUSTRY_POOL = "industryPool"
K_BANNER_IMAGE = "bannerImage"
K_LOGO = "opportunityLogo"
K_HERO_BANNER = "heroBanner"
K_HERO_SUMMARY = "heroSummary"
K_OVERVIEW = "overviewBody"
K_AMOUNT_RANGE = "investmentAmountRange"
K_MIN_TICKET = "minimumTicket"
K_SUBMITTER = "submitterName"
K_ENTITY = "submitterEntityType"
K_LOCATION = "submittedByLocation"
K_SUBMITTER_LOGO = "submittedByLogo"
K_PUBLISH_DATE = "publishDate"
K_ARCHIVE_DATE = "archiveDate"
K_DISPLAY_ORDER = "displayOrder"
K_LIFECYCLE = "lifecycleStatus"

BIZOPP_TEXT_KEYS = (K_TITLE, K_SUB_SECTOR, K_COUNTRY, K_COMPANY, K_CURRENCY, K_AMOUNT_RANGE, K_MIN_TICKET,
                    K_SUBMITTER, K_ENTITY, K_LOCATION)
BIZOPP_AR_TEXT_KEYS = (K_TITLE, K_SUB_SECTOR, K_COUNTRY, K_COMPANY, K_SUBMITTER, K_ENTITY, K_LOCATION)
BIZOPP_RICH_KEYS = (K_BRIEF, K_HERO_SUMMARY, K_OVERVIEW)
BIZOPP_NUMBER_KEYS = (K_AMOUNT, K_DISPLAY_ORDER)
BIZOPP_DATE_KEYS = (K_PUBLISH_DATE, K_ARCHIVE_DATE)
BIZOPP_PICKLIST_KEYS = (K_SECTOR, K_INVESTMENT_TYPE, K_TIMELINE, K_RISK, K_INDUSTRY_POOL, K_LIFECYCLE)
BIZOPP_IMAGE_KEYS = (K_BANNER_IMAGE, K_LOGO, K_HERO_BANNER, K_SUBMITTER_LOGO)
BIZOPP_UPLOAD_LABELS = {K_BANNER_IMAGE: "Banner Image", K_LOGO: "Opportunity Logo", K_HERO_BANNER: "Hero Banner",
                        K_SUBMITTER_LOGO: "Logo"}

# An existing Documents & Media ROOT file, picked (never uploaded) for the
# required image fields so plain record tests leave no D&M files behind.
EXISTING_IMAGE = "6th-World-Conference-Arbitration-Eng.png"

# ---- listing page (single record) field keys ------------------------------------------
P_EYEBROW = "eyebrowLabel"
P_TITLE = "pageTitle"
P_DESCRIPTION = "heroDescription"
P_HERO_IMAGE = "heroImage"
P_CTA_LABEL = "ctaLabel"
P_CTA_URL = "ctaRedirectUrl"
P_CTA_BEHAVIOR = "ctaOpenBehavior"
P_ACTIVE_TAB = "activeTabLabel"
P_ARCHIVE_TAB = "archiveTabLabel"
P_REFINE = "refineResultsHeading"
PAGE_TEXT_KEYS = (P_EYEBROW, P_TITLE, P_CTA_LABEL, P_ACTIVE_TAB, P_ARCHIVE_TAB, P_REFINE)
PAGE_PLAIN_KEYS = (P_CTA_URL,)
PAGE_RICH_KEYS = (P_DESCRIPTION,)
# snapshot / restore protocol of the shared record (brief rule 2)
PAGE_SNAPSHOT_KEYS = (PAGE_TEXT_KEYS + tuple(f"{k}_ar" for k in PAGE_TEXT_KEYS) + PAGE_PLAIN_KEYS
                      + tuple(f"{k}{s}" for k in PAGE_RICH_KEYS for s in ("", "_ar", "_html", "_html_ar"))
                      + (P_CTA_BEHAVIOR, "hero_image_block", "hero_image_file", "active_status", "status"))
PAGE_REQUIRED_NONEMPTY = (P_TITLE, P_EYEBROW, P_CTA_URL, P_DESCRIPTION, f"{P_DESCRIPTION}_html", "status")
PAGE_RESTORE_KEYS = (PAGE_TEXT_KEYS + tuple(f"{k}_ar" for k in PAGE_TEXT_KEYS) + PAGE_PLAIN_KEYS
                     + (f"{P_DESCRIPTION}_html", f"{P_DESCRIPTION}_html_ar", P_CTA_BEHAVIOR))
PAGE_VERIFY_KEYS = PAGE_RESTORE_KEYS + ("hero_image_file", "active_status", "status")


class PageRecordSafetyError(AssertionError):
    """The shared page record could not be snapshotted / restored safely."""

# ---- child objects: (slug, identity key, relation key) ----------------------------------
CHILD_OBJECTS = {
    SECTION_SLUG: ("sectionTitle", "r_opportunitySections_c_businessOpportunityId"),
    KEY_HIGHLIGHT_SLUG: ("itemText", "r_keyHighlights_c_businessOpportunityId"),
    CO_INVESTMENT_SLUG: ("label", "r_coInvestments_c_businessOpportunityId"),
    RESOURCE_SLUG: ("documentTitle", "r_downloadableResources_c_businessOpportunityId"),
    GALLERY_SLUG: ("displayOrder", "r_projectGalleryItems_c_businessOpportunityId"),
}


_WINDOWS_INVALID = _re.compile(r'[<>:"/\\|?*\x00-\x1f]+|\s+')
_WINDOWS_RESERVED = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def safe_file_name(name: str, limit: int = 120) -> str:
    """A Windows-valid file-name stem: the characters Windows forbids
    (< > : " / \\ | ? * and control chars) and whitespace become '_', the
    result is cut to `limit`, trailing dots / spaces / '_' are dropped (Windows
    strips trailing dots), and a reserved device name gets a '_' suffix.
    Arabic and other letters are kept."""
    stem = _WINDOWS_INVALID.sub("_", name or "").strip("._ ")[:limit].rstrip(". _") or "evidence"
    if stem.split(".")[0].upper() in _WINDOWS_RESERVED:
        stem += "_"
    return stem


@_dataclass(frozen=True)
class BizOppEntry:
    """Identity of ONE record a test created: object slug, the namespace it was
    created in, its identity value (title / item text / label) as stored, the
    entry id and the entry code."""

    slug: str
    prefix: str
    title: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return (self.prefix.startswith(QCTEST_NAMESPACES) and self.title.strip().startswith(self.prefix)
                and bool(self.entry_id) and bool(self.code) and not self.code.startswith(REAL_CODE_PREFIX))


class BizOppObjectPage(TenderFieldsAdminPage):
    """Generic driver for ONE Business-Opportunities object's manage page.

    Reuses the object-agnostic machinery of TenderFieldsAdminPage (role login,
    list expansion + row parsing, save-outcome probe, refusal evidence, date /
    picklist / upload helpers, edit-bar reads) re-pointed at `slug`. Every
    tender-specific method of that class (identify_created, delete_disposable_entry,
    fill_tender, ...) is NOT used here — the methods below replace them.

    `prefix` is the caller's QCTEST namespace (e.g. "QCTEST-130697-A-"); this
    instance only ever acts on records whose identity starts with it."""

    SLUG = BIZOPP_SLUG
    IDENTITY_KEY = K_TITLE
    IDENTITY_IS_RICH = False
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/")
    EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "130697_core")
    DESTRUCTIVE_ROW_ACTIONS = frozenset({"delete", "trash", "untrash"})
    ROW_ACTION_NAMES = ("view", "approve", "reject", "resubmit", "publish", "unpublish", "archive",
                        "restore", "return", "schedule", "history", "delete")
    HISTORY_CELL = "td.qc-oel__history"
    HISTORY_ACTION = ".qc-oel__history-action"
    UPLOAD_LABELS: dict = {}

    def __init__(self, page, prefix: str, evidence_dir: str | None = None):
        if not prefix.startswith(QCTEST_NAMESPACES):
            raise ValueError(f"prefix {prefix!r} is not in the {QCTEST_NAMESPACES} namespaces")
        ObjectAuthoringPage.__init__(self, page, self.SLUG)  # not TenderAdminPage's slug
        self.prefix = prefix
        self.owned_entry_ids: set[str] = set()
        self.last_uploaded_name = ""
        if evidence_dir:
            self.EVIDENCE_DIR = evidence_dir

    @property
    def FORM(self) -> str:  # noqa: N802 — overrides the tender class constant
        return f'form:has([name="ObjectField_{self.IDENTITY_KEY}"])'

    # ---- evidence -------------------------------------------------------------------
    def evidence(self, name: str, full_page: bool = True) -> str:
        """PNG under EVIDENCE_DIR + Allure attachment. Both the file name AND the
        name handed to attach_screenshot (which builds its own file name under
        reports/screenshots/) are Windows-safe: a raw ':' there (e.g. a key
        highlight identity 'Highlight one: 120 MW…') silently writes an NTFS
        alternate data stream instead of a visible file."""
        safe = safe_file_name(name)
        _os.makedirs(self.EVIDENCE_DIR, exist_ok=True)
        path = _os.path.join(self.EVIDENCE_DIR, safe + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, safe, "bizopp")
        except Exception as exc:  # noqa: BLE001 — evidence only
            _log.warning("evidence %s failed: %r", safe, exc)
        return path

    def success_messages(self, expected: str, timeout: float = 15.0) -> list[str]:
        """Edit-bar texts once `expected` shows; the publish message also
        matches Liferay's standard success toast (shows_message)."""
        try:
            _wait_until(lambda: any(shows_message(t, expected) for t in self.editbar_texts()),
                        timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            pass
        return self.editbar_texts()

    # ---- navigation ---------------------------------------------------------------
    def open_create_form_en(self) -> "BizOppObjectPage":
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self._locale = "en"
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "BizOppObjectPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self._locale = "en"
        self.page.locator(f'{self.FORM} [name="ObjectField_{self.IDENTITY_KEY}"]').first.wait_for(
            state="attached", timeout=90000)
        try:
            _wait_until(lambda: self.identity_value() != "", timeout=15.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    # ---- identity -----------------------------------------------------------------
    def identity_value(self) -> str:
        if self.IDENTITY_IS_RICH:
            try:
                return self.iframe_editor_text(self._rich_iframe(self.IDENTITY_KEY)).strip()
            except Exception:  # noqa: BLE001 — editor not mounted yet
                return ""
        return self._en(self.IDENTITY_KEY).input_value().strip()

    def name(self, tc_id: str, stamp: str, suffix: str = "") -> str:
        return f"{self.prefix}{tc_id}-{stamp}" + (f" {suffix}" if suffix else "")

    def identify_created_entry(self, identity: str, ids_before: set[str]) -> BizOppEntry | None:
        """The ONE new row (id not in `ids_before`, code not a real
        QC-BIZOPP-130697- code) whose own form reads `identity` exactly. None for
        zero or several matches. Read-only."""
        if not identity.strip().startswith(self.prefix):
            raise ValueError(f"{identity!r} is not in the {self.prefix} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].startswith(REAL_CODE_PREFIX)]
        matches = []
        for row in fresh:
            for attempt in (1, 2):  # one retry: a slow editEntry load must not orphan our record
                try:
                    self.open_entry_en(row["code"])
                    if self.identity_value() == identity.strip():
                        matches.append(row)
                    break
                except Exception as exc:  # noqa: BLE001 — an unreadable row is not ours
                    _log.warning("could not read new row %s (attempt %s): %r", row, attempt, exc)
        if len(matches) != 1:
            _log.warning("identify_created_entry(%r) on %s: %s matches among new rows %s",
                         identity, self.SLUG, len(matches), fresh)
            return None
        entry = BizOppEntry(slug=self.SLUG, prefix=self.prefix, title=identity.strip(),
                            entry_id=matches[0]["entry_id"], code=matches[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def adopt_entry(self, entry: BizOppEntry) -> BizOppEntry:
        if (not isinstance(entry, BizOppEntry) or entry.slug != self.SLUG or entry.prefix != self.prefix
                or not entry.in_namespace()):
            raise ValueError(f"refusing to adopt {entry}: not a captured {self.prefix} {self.SLUG} record")
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def leftovers(self) -> list[dict]:
        """Read-only: rows of this object whose identity field starts with this
        instance's prefix (opens each non-real row by code)."""
        self.open_list_all()
        found = []
        for row in [r for r in self.list_rows() if r["code"] and not r["code"].startswith(REAL_CODE_PREFIX)]:
            try:
                self.open_entry_en(row["code"])
                value = self.identity_value()
                if value.startswith(self.prefix):
                    found.append({**row, "identity": value})
            except Exception as exc:  # noqa: BLE001
                _log.warning("leftover scan could not read %s: %r", row, exc)
        return found

    # ---- rows -----------------------------------------------------------------------
    def _row(self, entry: BizOppEntry):
        return self.page.locator(", ".join(
            f'{self.ENTRIES_TABLE_ROW}:has([data-qc-oel-{a}="{entry.entry_id}"])' for a in self.ID_ATTRS))

    def row_of(self, entry: BizOppEntry) -> dict:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0] if len(rows) == 1 else {}

    def row_status_of(self, entry: BizOppEntry) -> str:
        """Normalized workflow badge of the captured row ("" when the row is gone)."""
        row = self.row_of(entry)
        if not row:
            return ""
        raw = " ".join(row["status"].split())
        # live 2026-10-07: a Published record whose Active Status is off shows "INACTIVE"
        if raw.casefold() == STATUS_INACTIVE.casefold():
            return STATUS_INACTIVE
        return normalize_status(raw)

    def row_status_raw(self, entry: BizOppEntry) -> str:
        return self.row_of(entry).get("status", "")

    def row_actions(self, entry: BizOppEntry) -> list[str]:
        row = self._row(entry).first
        return [n for n in self.ROW_ACTION_NAMES if row.locator(f"[data-qc-oel-{n}]").count() > 0]

    def row_link_labels(self, entry: BizOppEntry) -> list[str]:
        return [t.strip() for t in self._row(entry).first.locator("td").last.locator("a, button")
                .all_inner_texts() if t.strip()]

    def row_has_edit_link(self, entry: BizOppEntry) -> bool:
        return self._row(entry).first.locator('a[href*="editEntry="]').count() > 0

    def row_preview_href(self, entry: BizOppEntry) -> str:
        link = self._row(entry).first.get_by_role("link", name="Preview")
        href = link.first.get_attribute("href") if link.count() else ""
        return (href if href.startswith("http") else control_panel_url(href)) if href else ""

    def wait_status(self, entry: BizOppEntry, expected: tuple, timeout: float = 120.0) -> str:
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

    def run_row_action(self, entry: BizOppEntry, action: str, comment: str = "") -> list[str]:
        """Clicks ONE id-scoped workflow action on a record THIS instance
        captured, accepting every native confirm()/prompt() (prompts get
        `comment`); returns the dialog messages. Destructive actions refused."""
        if action in self.DESTRUCTIVE_ROW_ACTIONS:
            raise ValueError(f"run_row_action refuses {action!r}; use delete_own_entry()")
        if action != "history":
            if not isinstance(entry, BizOppEntry) or not entry.in_namespace() or entry.prefix != self.prefix:
                raise ValueError(f"run_row_action refuses {entry}: not a {self.prefix} record")
            if entry.entry_id not in self.owned_entry_ids:
                raise ValueError(f"run_row_action refuses {entry}: id not captured at creation")
            row = self.row_of(entry)
            if not row or row["code"] != entry.code:
                raise ValueError(f"run_row_action refuses {entry}: the row now reads {row}")
        control = self._row(entry).first.locator(f"[data-qc-oel-{action}]")
        if control.count() == 0:
            raise AssertionError(f"row {entry.code!r} offers no {action!r} action; offered {self.row_actions(entry)}")
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

    def history(self, entry: BizOppEntry) -> list[dict]:
        """Expands the captured row's History (inside the table) ->
        [{action, who, when, comment, text}]."""
        self.open_list_all()
        self._row(entry).first.locator("[data-qc-oel-history]").first.click(force=True)
        cell = self._row(entry).first.locator("xpath=following-sibling::tr[1]").locator(self.HISTORY_CELL)
        try:
            _wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text(), timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
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

    # ---- guarded delete -----------------------------------------------------------------
    def _delete_preconditions_of(self, entry: BizOppEntry) -> str:
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
        if row["title"].strip() != entry.code or row["label"].strip() != entry.code:
            return f"row {entry.entry_id} shows {row['title']!r} / label {row['label']!r}, not code {entry.code!r}"
        return ""

    def delete_own_entry(self, entry: BizOppEntry) -> bool:
        """Deletes exactly this captured record or refuses (False, never raises)."""
        try:
            if (not isinstance(entry, BizOppEntry) or entry.slug != self.SLUG or entry.prefix != self.prefix
                    or not entry.in_namespace() or entry.entry_id not in self.owned_entry_ids):
                _log.error("DELETE REFUSED: %r is not a captured %s %s record", entry, self.prefix, self.SLUG)
                return False
            self.open_entry_en(entry.code)
            live = self.identity_value()
            if live != entry.title:
                _log.error("DELETE REFUSED for %r: the record now reads %r", entry, live)
                return False
            self.open_list_all()
            reason = self._delete_preconditions_of(entry)
            if reason:
                _log.error("DELETE REFUSED for %r: %s", entry, reason)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            reason = self._delete_preconditions_of(entry)  # re-check immediately before the click
            if reason:
                _log.error("DELETE REFUSED for %r on re-check: %s", entry, reason)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                if entry.code in dialog.message:
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
            if not any(entry.code in m for m in dialogs):
                _log.error("DELETE NOT CONFIRMED for %r: dialogs %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = self.is_list_fully_expanded() and not any(
                r["entry_id"] == entry.entry_id for r in self.list_rows())
            if gone:
                _log.info("deleted %r", entry)
            return gone
        except Exception as exc:  # noqa: BLE001
            _log.error("delete of %r failed: %r", entry, exc)
            return False

    # ---- form helpers ------------------------------------------------------------------
    def _rich_ar_iframe(self, key: str) -> str:
        return f'[id="cke_qc-ar-{key}"] iframe[title="editor"]'

    def fill_rich_ar(self, key: str, text: str) -> "BizOppObjectPage":
        """The AR editor can mount late / off-screen (live 2026-10-07: its body
        never became 'visible' for 30 s once) — set it through the CKEditor
        instance first, typing into the iframe only as the fallback."""
        from html import escape  # noqa: PLC0415
        try:
            self.set_rich_html(key, f"<p>{escape(text)}</p>", ar=True)
            _wait_until(lambda: text in self.rich_text_ar(key), timeout=5.0, poll=0.5)
            return self
        except Exception:  # noqa: BLE001 — fall back to typing
            pass
        self.page.locator(f'[id="cke_qc-ar-{key}"]').first.scroll_into_view_if_needed()
        self.fill_iframe_editor(self._rich_ar_iframe(key), text)
        return self

    def rich_text(self, key: str) -> str:
        return self.iframe_editor_text(self._rich_iframe(key)).strip()

    def rich_text_ar(self, key: str) -> str:
        return self.iframe_editor_text(self._rich_ar_iframe(key)).strip()

    def rich_html(self, key: str) -> str:
        return self.page.frame_locator(self._rich_iframe(key)).locator("body").inner_html()

    def set_rich_html(self, key: str, html: str, ar: bool = False) -> "BizOppObjectPage":
        """Sets a CKEditor body's HTML through the editor instance (bullet lists /
        links the plain-text fill cannot produce). Falls back to the body."""
        target = f"qc-ar-{key}" if ar else None
        done = self.page.evaluate(
            """([key, target, html]) => {
                if (!window.CKEDITOR) return false;
                for (const name in CKEDITOR.instances) {
                    const inst = CKEDITOR.instances[name];
                    const el = inst.element && inst.element.$;
                    const n = (el && (el.name || el.id)) || name;
                    if ((target && (n === target || name === target)) ||
                        (!target && (n === 'ObjectField_' + key || name.endsWith('ObjectField_' + key)))) {
                        inst.setData(html); inst.updateElement && inst.updateElement(); inst.fire('change');
                        return true; } }
                return false; }""",
            [key, target, html],
        )
        if not done:
            frame = self.page.frame_locator(self._rich_ar_iframe(key) if ar else self._rich_iframe(key))
            frame.locator("body").evaluate("(b, h) => { b.innerHTML = h; }", html)
        return self

    def active_status_checked(self) -> bool:
        return self.active_status_stored() == "true"

    def file_block_text(self, key: str, label: str) -> str:
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            """(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                const v = el.value || el.placeholder || '';
                return ((c ? c.innerText : '') + ' ' + v).replace(/\\s+/g, ' ').trim(); }""",
            label,
        )

    def file_field_value(self, key: str) -> str:
        """The value the form would submit for an upload field (the picked
        fileEntryId; "" when nothing is attached)."""
        return self._form().locator(f'input[name="ObjectField_{key}"]').first.input_value()

    def stored_file_id(self, key: str, code: str | None = None) -> str:
        """The STORED fileEntryId of an attachment field, read-only via the
        object's headless REST (live 2026-10-13: an edit form no longer
        pre-fills ObjectField_<key>; it shows 'Current file: <name>' as a
        placeholder, so file_field_value() reads "" on a saved record)."""
        code = code or self._entry_code
        rest = self.SLUG.replace("-", "") + "s"
        return str(self.page.evaluate(
            """async ([rest, code, key]) => {
                const gid = Liferay.ThemeDisplay.getScopeGroupId();
                const r = await fetch(`/o/c/${rest}/scopes/${gid}/by-external-reference-code/${encodeURIComponent(code)}?p_auth=${Liferay.authToken}`);
                if (!r.ok) return "";
                const v = (await r.json())[key];
                return v && v.id ? String(v.id) : "";
            }""", [rest, code, key]))

    def attempt_upload_settled(self, key: str, file_path: str, stem: str | None = None,
                               settle_s: float = 5.0) -> dict:
        """attempt_upload() whose `attached` is decided by the field's own value
        (live 2026-10-07: after a good upload the field holds the fileEntryId and
        its block text does not repeat the file name; an oversized pick can be
        set briefly and then cleared, hence the settle wait)."""
        result = self.attempt_upload(key, file_path, stem)
        try:
            _wait_until(lambda: self.file_field_value(key) == "", timeout=settle_s, poll=0.5)
        except _WaitTimeoutError:
            pass
        result["field_value"] = self.file_field_value(key)
        result["attached"] = result["field_value"] != ""
        result["field_errors"] = self.field_errors()
        return result

    def upload(self, key: str, file_path: str, stem: str | None = None) -> "BizOppObjectPage":
        result = self.attempt_upload_settled(key, file_path, stem, settle_s=2.0)
        if not result["attached"]:
            raise AssertionError(f"upload of {file_path} into {key} was not attached: {result}")
        return self

    def upload_block_text(self, key: str) -> str:  # overrides the tender label table
        return self.file_block_text(key, self.UPLOAD_LABELS.get(key, key))

    def pick_existing_image(self, key: str, file_name: str = EXISTING_IMAGE) -> "BizOppObjectPage":
        """Picks an EXISTING Documents & Media root file for an image field
        (no upload, so nothing is added to D&M). One retry: live 2026-10-07 the
        picker once stayed open after the click (transient)."""
        try:
            return self._pick_existing_image_once(key, file_name)
        except AssertionError:
            self.page.keyboard.press("Escape")
            self._picker_closed(8000)
            return self._pick_existing_image_once(key, file_name)

    def _pick_existing_image_once(self, key: str, file_name: str) -> "BizOppObjectPage":
        self._open_picker(key)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        target = frame.get_by_text(file_name, exact=True).first
        try:
            target.wait_for(state="visible", timeout=10000)
        except Exception:  # noqa: BLE001 — not on the picker's first page (alphabetical, 20/page)
            search = frame.locator('input[name$="_keywords"]').first
            search.fill(file_name.rsplit(".", 1)[0])
            search.press("Enter")
        target.wait_for(state="visible", timeout=30000)
        target.click()
        if not self._picker_closed(5000):
            try:
                target.dblclick()
            except Exception:  # noqa: BLE001 — checked below
                pass
        if not self._picker_closed(10000):
            raise AssertionError(f"the D&M picker stayed open after picking {file_name!r} for {key}")
        field = self._form().locator(f'input[name="ObjectField_{key}"]').first
        try:
            _wait_until(lambda: field.input_value() != "", timeout=10.0, poll=0.3)
        except _WaitTimeoutError:
            raise AssertionError(f"picking {file_name!r} left ObjectField_{key} empty") from None
        return self

    def pick_relation(self, relation_key: str, parent_code: str) -> "BizOppObjectPage":
        """Relation picker: option label = the parent's entry code."""
        return self.pick(relation_key, parent_code)

    def relation_value(self, relation_key: str) -> str:
        return self.picklist_value(relation_key)

    def save_outcome(self) -> dict:
        return {"went_through": self.save_went_through(), "refused": self.save_was_refused(),
                **self.refusal_evidence()}

    def wait_arabic_saved(self, timeout: float = 25.0) -> str:
        """Guide §5: on a new record the Arabic is saved a moment after the record."""
        seen = {"text": ""}

        def _done() -> bool:
            try:
                seen["text"] = self.page.locator("body").inner_text()
            except Exception:  # noqa: BLE001 — mid-navigation
                return False
            return MSG_ARABIC_SAVED in seen["text"] or MSG_ARABIC_NOT_SAVED in seen["text"]

        try:
            _wait_until(_done, timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            return ""
        return MSG_ARABIC_SAVED if MSG_ARABIC_SAVED in seen["text"] else "the Arabic content was NOT saved"


class OpportunityAdminPage(BizOppObjectPage):
    """manage-business-opportunity (the opportunity record)."""

    SLUG = BIZOPP_SLUG
    IDENTITY_KEY = K_TITLE
    UPLOAD_LABELS = BIZOPP_UPLOAD_LABELS

    def fill_opportunity(self, data: dict) -> "OpportunityAdminPage":
        """Fills every key `data` carries (None / absent = left untouched).
        Text keys + `<key>_ar`; rich keys + `<key>_ar`; numbers; dates
        (dd/mm/yyyy); picklists (option label); images: "pick:<file>" picks an
        existing D&M file, a path uploads it; `active_status` bool."""
        for key in BIZOPP_TEXT_KEYS:
            if data.get(key) is not None:
                self.fill_en(key, data[key])
        for key in BIZOPP_AR_TEXT_KEYS:
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, data[f"{key}_ar"])
        for key in BIZOPP_RICH_KEYS:
            if data.get(key):
                self.fill_rich(key, data[key])
            if data.get(f"{key}_ar"):
                self.fill_rich_ar(key, data[f"{key}_ar"])
        for key in BIZOPP_NUMBER_KEYS:
            if data.get(key) is not None:
                self.fill_number_key(key, data[key])
        for key in BIZOPP_DATE_KEYS:
            if data.get(key) is not None:
                self.set_date(key, data[key])
        for key in BIZOPP_PICKLIST_KEYS:
            if data.get(key):
                self.pick(key, data[key])
        for key in BIZOPP_IMAGE_KEYS:
            value = data.get(key)
            if not value:
                continue
            if value.startswith("pick:"):
                self.pick_existing_image(key, value[len("pick:"):])
            else:
                self.upload(key, value, data.get(f"{key}_stem"))
                data[f"{key}_uploaded_as"] = self.last_uploaded_name
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    def read_opportunity(self) -> dict:
        """Every stored value of the open record, keyed like the fill data."""
        try:
            _wait_until(lambda: self.rich_text(K_HERO_SUMMARY) != "", timeout=20.0, poll=0.5)
        except Exception:  # noqa: BLE001 — caller compares whatever loaded
            pass
        values: dict = {}
        for key in BIZOPP_TEXT_KEYS + BIZOPP_NUMBER_KEYS:
            values[key] = self.text_value(key)
        for key in BIZOPP_AR_TEXT_KEYS:
            values[f"{key}_ar"] = self.ar_value(key)
        for key in BIZOPP_RICH_KEYS:
            values[key] = self.rich_text(key)
            values[f"{key}_ar"] = self.rich_text_ar(key)
        for key in BIZOPP_DATE_KEYS:
            values[key] = self.date_text(key)
            values[f"{key}_stored"] = self.date_stored(key)
        for key in BIZOPP_PICKLIST_KEYS:
            values[key] = self.picklist_value(key)
        for key in BIZOPP_IMAGE_KEYS:
            values[f"{key}_file"] = self.stored_file_name(key)
        values["active_status"] = self.active_status_stored()
        return values

    @staticmethod
    def default_data(title: str, **overrides) -> dict:
        """A complete, valid opportunity (EN + AR, existing D&M images picked,
        Active Status ticked, Display Order 100, publish today-ish, archive in
        the future). Dates dd/mm/yyyy."""
        data = {
            K_TITLE: title,
            f"{K_TITLE}_ar": f"{title} فرصة تجريبية",
            K_SECTOR: "Energy",
            K_SUB_SECTOR: "QCTEST Solar",
            f"{K_SUB_SECTOR}_ar": "طاقة شمسية تجريبية",
            K_COUNTRY: "Qatar",
            f"{K_COUNTRY}_ar": "قطر",
            K_COMPANY: "QCTEST Holding",
            f"{K_COMPANY}_ar": "شركة تجريبية",
            K_BRIEF: f"{title} investment brief (disposable automated-test record).",
            f"{K_BRIEF}_ar": "موجز استثمار لسجل اختبار آلي.",
            K_AMOUNT: "2000000",
            K_CURRENCY: "QAR",
            K_INVESTMENT_TYPE: "Equity",
            K_TIMELINE: "6–12 months",
            K_RISK: "Medium",
            K_INDUSTRY_POOL: "Energy",
            K_BANNER_IMAGE: f"pick:{EXISTING_IMAGE}",
            K_LOGO: f"pick:{EXISTING_IMAGE}",
            K_HERO_BANNER: f"pick:{EXISTING_IMAGE}",
            K_HERO_SUMMARY: f"{title} hero summary.",
            f"{K_HERO_SUMMARY}_ar": "ملخص الواجهة لسجل اختبار آلي.",
            K_OVERVIEW: f"{title} overview body.",
            f"{K_OVERVIEW}_ar": "نظرة عامة لسجل اختبار آلي.",
            K_AMOUNT_RANGE: "QAR 2M–5M",
            K_MIN_TICKET: "QAR 250,000",
            K_SUBMITTER: "QCTEST Submitter",
            f"{K_SUBMITTER}_ar": "مقدم تجريبي",
            K_ENTITY: "Private",
            f"{K_ENTITY}_ar": "خاص",
            K_LOCATION: "Doha, Qatar",
            f"{K_LOCATION}_ar": "الدوحة، قطر",
            K_SUBMITTER_LOGO: f"pick:{EXISTING_IMAGE}",
            K_PUBLISH_DATE: (_date.today() - _timedelta(days=6)).strftime("%d/%m/%Y"),
            K_ARCHIVE_DATE: (_date.today() + _timedelta(days=450)).strftime("%d/%m/%Y"),
            K_DISPLAY_ORDER: "100",
            K_LIFECYCLE: "Published",
            "active_status": True,
        }
        data.update(overrides)
        return data


class OpportunityChildAdminPage(BizOppObjectPage):
    """Generic child object of a Business Opportunity (section / key highlight /
    co-investment / downloadable resource / gallery item). Construct through
    `for_slug()`."""

    RELATION_KEY = ""

    @classmethod
    def for_slug(cls, slug: str, page, prefix: str, evidence_dir: str | None = None) -> "OpportunityChildAdminPage":
        identity, relation = CHILD_OBJECTS[slug]
        sub = type(f"OpportunityChild_{slug.replace('-', '_')}", (cls,), {
            "SLUG": slug, "IDENTITY_KEY": identity, "RELATION_KEY": relation,
            "IDENTITY_IS_RICH": slug == KEY_HIGHLIGHT_SLUG,
            "UPLOAD_LABELS": {"file": "File", "galleryImage": "Gallery Image"},
        })
        return sub(page, prefix, evidence_dir)

    def __init__(self, page, prefix: str, evidence_dir: str | None = None):
        super().__init__(page, prefix, evidence_dir)
        # entry ids of PARENT opportunities captured by the caller's own test
        # (live 2026-10-07: a reopened child form's relation holds the parent's
        # ENTRY ID, while the picker option label is the parent's code)
        self.owned_parent_ids: set[str] = set()

    def link_to(self, parent_code: str) -> "OpportunityChildAdminPage":
        return self.pick_relation(self.RELATION_KEY, parent_code)

    def gallery_identity(self, parent_entry_id: str, display_order: str) -> str:
        """Gallery items carry no text field: their identity is the (owned)
        parent entry id + display order, wrapped in this instance's prefix."""
        return f"{self.prefix}GAL {parent_entry_id} #{display_order}"

    def identity_value(self) -> str:
        if self.SLUG != GALLERY_SLUG:
            return super().identity_value()
        try:
            parent = self.relation_value(self.RELATION_KEY)
            order = self.text_value("displayOrder")
        except Exception:  # noqa: BLE001 — form not mounted yet
            return ""
        if parent and parent in self.owned_parent_ids:
            return self.gallery_identity(parent, order)
        return f"NOT-OWNED {parent} #{order}"

    def fill_child(self, data: dict) -> "OpportunityChildAdminPage":
        """Keys: `parent` (parent entry code), the identity key (+ `_ar`),
        itemText (rich, + `_ar`), sectionNumber / percentage / value (text),
        displayOrder, file / galleryImage ("pick:<name>" or a path to upload),
        active_status."""
        if data.get("parent"):
            self.link_to(data["parent"])
        for key in ("sectionTitle", "label", "documentTitle", "sectionNumber", "percentage", "value"):
            if data.get(key) is not None:
                self.fill_en(key, data[key])
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, data[f"{key}_ar"])
        if data.get("itemText"):
            self.fill_rich("itemText", data["itemText"])
        if data.get("itemText_ar"):
            self.fill_rich_ar("itemText", data["itemText_ar"])
        if data.get("displayOrder") is not None:
            self.fill_number_key("displayOrder", data["displayOrder"])
        for key in ("file", "galleryImage"):
            value = data.get(key)
            if not value:
                continue
            if value.startswith("pick:"):
                self.pick_existing_image(key, value[len("pick:"):])
            else:
                self.upload(key, value, data.get(f"{key}_stem"))
                data[f"{key}_uploaded_as"] = self.last_uploaded_name
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self


class OpportunityListingPageAdminPage(BizOppObjectPage):
    """manage-business-opportunity-page — the SINGLE shared listing-page record
    `QC-BIZOPP-130697-PAGE` (no create, no delete). Brief rule 2: edit only after
    `snapshot()`, always `restore()` + `diff()` afterwards. Only Agent A uses it."""

    SLUG = LISTING_PAGE_SLUG
    IDENTITY_KEY = P_TITLE
    UPLOAD_LABELS = {P_HERO_IMAGE: "Hero Image"}

    def open_page_record(self) -> "OpportunityListingPageAdminPage":
        return self.open_entry_en(LISTING_PAGE_CODE)

    # ---- shared-record safety (brief rule 2) ----------------------------------------------
    def _editor_loaded(self, strict: bool) -> bool:
        """The form is fully mounted: the record's code is the open one and every
        CKEditor instance is 'ready' (EN + AR Hero Description bodies present).
        `strict` (snapshot): Page Title / Eyebrow / CTA URL inputs and both Hero
        Description editors must also hold values."""
        try:
            if self._entry_code != LISTING_PAGE_CODE:
                return False
            ready = self.page.evaluate(
                "() => !!window.CKEDITOR && Object.keys(CKEDITOR.instances).length >= 2 &&"
                " Object.values(CKEDITOR.instances).every(i => i.status === 'ready')")
            if not ready:
                return False
            self.rich_text(P_DESCRIPTION), self.rich_text_ar(P_DESCRIPTION)  # both bodies mounted
            if not strict:
                return True
            return bool(self.text_value(P_TITLE).strip() and self.text_value(P_EYEBROW).strip()
                        and self.text_value(P_CTA_URL).strip() and self.rich_text(P_DESCRIPTION)
                        and self.rich_text_ar(P_DESCRIPTION))
        except Exception:  # noqa: BLE001 — still mounting
            return False

    def wait_editor_loaded(self, timeout: float = 60.0, strict: bool = True) -> None:
        """Raises PageRecordSafetyError (never swallows) when the editor does not finish loading."""
        try:
            _wait_until(lambda: self._editor_loaded(strict), timeout=timeout, poll=0.5)
        except _WaitTimeoutError:
            raise PageRecordSafetyError(
                f"{LISTING_PAGE_CODE}: the editor did not finish loading within {timeout:.0f}s "
                f"(title {self._safe(lambda: self.text_value(P_TITLE))!r}, eyebrow "
                f"{self._safe(lambda: self.text_value(P_EYEBROW))!r}, CTA URL "
                f"{self._safe(lambda: self.text_value(P_CTA_URL))!r}) — refusing to snapshot/restore") from None

    @staticmethod
    def _safe(read) -> str:
        try:
            return read()
        except Exception as exc:  # noqa: BLE001
            return f"<unreadable: {exc.__class__.__name__}>"

    @staticmethod
    def assert_snapshot_complete(snap: dict) -> None:
        missing = [k for k in PAGE_SNAPSHOT_KEYS if k not in snap]
        empty = [k for k in PAGE_REQUIRED_NONEMPTY if not str(snap.get(k, "")).strip()]
        if missing or empty:
            raise PageRecordSafetyError(f"{LISTING_PAGE_CODE}: INCOMPLETE snapshot — missing keys {missing}, "
                                        f"empty required values {empty}; nothing will be edited")

    def snapshot(self) -> dict:
        """Every stored value of the page record (open it first). Waits for the
        editor to load fully and asserts completeness (raises otherwise), then
        marks the snapshot `_complete` — restore() refuses any other dict."""
        self.wait_editor_loaded()
        snap = self.read_page()
        self.assert_snapshot_complete(snap)
        snap["_complete"] = True
        return snap

    def restore(self, snapshot: dict, before_save=None) -> dict:
        """Writes `snapshot` back and proves it: one retry when the attempt
        throws OR the re-opened record still differs; returns {} on success and
        raises PageRecordSafetyError naming every differing field otherwise.

        Guards: only a complete snapshot (from snapshot()) is accepted; only the
        fields that differ from the snapshot are written; "" is never written
        where the snapshot holds a non-empty value; the save restores the
        ORIGINAL status — Publish only when the snapshot was Published, Save as
        Draft only when it was Draft, anything else refused. `before_save()` is
        called right before the click (role re-check)."""
        if not snapshot.get("_complete"):
            raise PageRecordSafetyError("restore() refuses a snapshot that snapshot() did not validate")
        if snapshot["status"] not in ("Published", "Draft"):
            raise PageRecordSafetyError(f"restore() cannot reproduce the original status {snapshot['status']!r}")
        attempts: list = []
        for attempt in (1, 2):
            try:
                diff = self._restore_once(snapshot, before_save)
            except Exception as exc:  # noqa: BLE001 — retried once, then reported
                _log.error("restore attempt %s of %s threw: %r", attempt, LISTING_PAGE_CODE, exc)
                attempts.append(f"attempt {attempt} threw {exc!r}")
                continue
            if not diff:
                self.last_restore_attempts = attempts + [f"attempt {attempt}: restored (diff {{}})"]
                return {}
            attempts.append(f"attempt {attempt} left differences in {sorted(diff)}: {diff}")
        self.last_restore_attempts = attempts
        try:
            self.open_page_record()
            self.wait_editor_loaded(strict=False)
            final = self.diff(snapshot, self.read_page(), PAGE_VERIFY_KEYS)
        except Exception as exc:  # noqa: BLE001
            final = {"<record unreadable>": (None, repr(exc))}
        raise PageRecordSafetyError(
            f"RESTORE FAILED on {LISTING_PAGE_CODE} — fields that differ from the snapshot: {sorted(final)}; "
            + "; ".join(f"{k}: snapshot {v[0]!r} vs now {v[1]!r}" for k, v in final.items())
            + " | attempts: " + " || ".join(attempts))

    def _restore_once(self, snapshot: dict, before_save) -> dict:
        self.open_page_record()
        self.wait_editor_loaded(strict=False)
        self.page.wait_for_timeout(1500)  # late value hydration after CKEditor 'ready'
        live = self.read_page()
        data = {}
        for key in PAGE_RESTORE_KEYS:
            want = snapshot[key]
            if live.get(key) == want:
                continue
            if want == "" and str(live.get(key, "")) != "" and key in PAGE_REQUIRED_NONEMPTY:
                raise PageRecordSafetyError(f"refusing to write '' into required field {key}")
            data[key] = want
        for key, value in data.items():  # final guard against blanking a real value
            if value == "" and str(snapshot.get(key, "")) != "":
                raise PageRecordSafetyError(f"refusing to write '' over the non-empty snapshot value of {key}")
        _log.info("restoring %s fields: %s", LISTING_PAGE_CODE, sorted(data))
        if (not data and live.get("active_status") == snapshot["active_status"]
                and live.get("status") == snapshot["status"]):
            return self.diff(snapshot, live, PAGE_VERIFY_KEYS)  # nothing changed -> no write at all
        self.fill_page(data)
        if live.get("active_status") != snapshot["active_status"]:
            self.set_active_status(snapshot["active_status"] == "true")
        if before_save:
            before_save()
        if snapshot["status"] == "Published":
            self.click_publish()
        else:
            self.click_save_as_draft()
        if not self.save_went_through():
            raise PageRecordSafetyError(f"the restore save did not go through: {self.save_outcome()}")
        self.evidence("listing page restored")
        self.open_page_record()
        self.wait_editor_loaded(strict=False)
        self.page.wait_for_timeout(1500)
        return self.diff(snapshot, self.read_page(), PAGE_VERIFY_KEYS)

    def read_page(self) -> dict:
        """Current values of the open record (no completeness check)."""
        snap: dict = {}
        for key in PAGE_TEXT_KEYS:
            snap[key] = self.text_value(key)
            snap[f"{key}_ar"] = self.ar_value(key)
        for key in PAGE_PLAIN_KEYS:
            snap[key] = self.text_value(key)
        for key in PAGE_RICH_KEYS:
            # the stored HTML (backing textareas), not the editor's rendering
            snap[f"{key}_html"] = self._form().locator(f'textarea[name="ObjectField_{key}"]').first.input_value()
            snap[f"{key}_html_ar"] = self._form().locator(f'textarea[id="qc-ar-{key}"]').first.input_value()
            snap[key] = self.rich_text(key)
            snap[f"{key}_ar"] = self.rich_text_ar(key)
        snap[P_CTA_BEHAVIOR] = self.picklist_value(P_CTA_BEHAVIOR)
        snap["hero_image_block"] = self.upload_block_text(P_HERO_IMAGE)
        snap["hero_image_file"] = self.stored_file_name(P_HERO_IMAGE)
        snap["active_status"] = self.active_status_stored()
        snap["status"] = self.current_status()
        return snap

    def fill_page(self, data: dict) -> "OpportunityListingPageAdminPage":
        for key in PAGE_TEXT_KEYS:
            if data.get(key) is not None:
                self.fill_en(key, data[key])
            if data.get(f"{key}_ar") is not None:
                self.fill_ar(key, data[f"{key}_ar"])
        for key in PAGE_PLAIN_KEYS:
            if data.get(key) is not None:
                self.fill_en(key, data[key])
        for key in PAGE_RICH_KEYS:
            if data.get(f"{key}_html") is not None:
                self.set_rich_html(key, data[f"{key}_html"])
            if data.get(f"{key}_html_ar") is not None:
                self.set_rich_html(key, data[f"{key}_html_ar"], ar=True)
        if data.get(P_CTA_BEHAVIOR):
            self.pick(P_CTA_BEHAVIOR, data[P_CTA_BEHAVIOR])
        if data.get(P_HERO_IMAGE):
            value = data[P_HERO_IMAGE]
            if value.startswith("pick:"):
                self.pick_existing_image(P_HERO_IMAGE, value[len("pick:"):])
            else:
                self.upload(P_HERO_IMAGE, value, data.get(f"{P_HERO_IMAGE}_stem"))
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    @staticmethod
    def diff(before: dict, after: dict, keys: tuple | None = None) -> dict:
        """{key: (before, after)} for every snapshot key that differs."""
        keys = keys or tuple(before)
        return {k: (before.get(k), after.get(k)) for k in keys if before.get(k) != after.get(k)}


# ---- public (logged-out) reads -----------------------------------------------------
class BizOppPublicView(BasePage):
    """Logged-out reads of the public listing + detail page, keyed by entry code.
    Live 2026-10-07: cards `a.qc-bol-card` link to
    `business-opportunity?opportunity=<entry code>`; tabs `.qc-bol-tab`
    ("Active Opportunities (n)", "Archive (n)"); "Load more" `button.qc-bol-more`."""

    LISTING_PATH = "/web/qatar-chamber/business-opportunities"
    DETAIL_PATH = "/web/qatar-chamber/business-opportunity?opportunity={code}"
    CARD = "a.qc-bol-card"
    TAB = "button.qc-bol-tab, .qc-bol-tab"
    LOAD_MORE = "button.qc-bol-more"

    def screenshot(self, test_case_id: str = "NO-TC") -> bytes:
        """BasePage.screenshot with a Windows-safe evidence name (see safe_file_name)."""
        png = self.page.screenshot()
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, safe_file_name(test_case_id), "bizopp")
        return png

    def open_listing(self, locale: str = "en", tab: str = "active") -> "BizOppPublicView":
        self.open(web_url(self.LISTING_PATH, locale=locale))
        try:
            self.page.locator("header.qc-bol-hero").wait_for(timeout=60000)
            self.page.locator(f"{self.CARD}, p.qc-bol-empty").first.wait_for(timeout=30000)
        except Exception:  # noqa: BLE001 — reported by the caller
            return self
        if tab == "archive":
            self.page.locator(".qc-bol-tab").nth(1).click()
            self.page.wait_for_timeout(1500)
        self._expand()
        return self

    def _expand(self) -> None:
        cards, button = self.page.locator(self.CARD), self.page.locator(self.LOAD_MORE)
        for _ in range(20):
            if button.count() == 0 or not button.first.is_visible():
                break
            before = cards.count()
            button.first.click()
            try:
                _wait_until(lambda: cards.count() > before, timeout=10.0, poll=0.25)
            except _WaitTimeoutError:
                break

    def search(self, keyword: str) -> "BizOppPublicView":
        box = self.page.locator("input.qc-bol-search-input").first
        try:
            box.wait_for(state="visible", timeout=20000)
        except Exception:  # noqa: BLE001 — live 2026-10-07: one load rendered no listing; reopen once
            self.open_listing("en")
            box.wait_for(state="visible", timeout=60000)
        box.fill(keyword)
        box.press("Enter")
        self.page.wait_for_timeout(2500)
        self._expand()
        return self

    def tabs(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(".qc-bol-tab").all_inner_texts()]

    def cards(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('a.qc-bol-card')].filter(a => a.offsetParent !== null).map(a => {
                const q = s => { const n = a.querySelector(s); return n ? n.innerText.trim() : ''; };
                return {href: a.getAttribute('href') || '', title: q('.qc-bol-card-title'), tag: q('.qc-bol-card-cat'),
                        text: a.innerText.replace(/\\s+/g, ' ').trim()}; })"""
        )

    def card_for(self, code: str) -> dict:
        for card in self.cards():
            if card["href"].endswith(f"opportunity={code}"):
                return card
        return {}

    def hero(self) -> dict:
        return self.page.evaluate(
            """() => { const q = s => document.querySelector(s);
                const cta = q('a.qc-bol-cta'), img = q('img.qc-bol-hero-img'), d = q('.qc-bol-hero-desc');
                return {eyebrow: q('p.qc-bol-eyebrow') ? q('p.qc-bol-eyebrow').innerText.trim() : '',
                        title: q('h1.qc-bol-title') ? q('h1.qc-bol-title').innerText.trim() : '',
                        description: d ? d.innerText.trim() : '', description_html: d ? d.innerHTML : '',
                        description_lists: d ? d.querySelectorAll('ul li, ol li').length : 0,
                        description_links: d ? [...d.querySelectorAll('a')].map(a => a.href) : [],
                        cta_label: cta ? cta.innerText.trim() : '', cta_href: cta ? cta.href : '',
                        cta_target: cta ? (cta.getAttribute('target') || '') : '',
                        image_src: img ? img.src : '', image_loaded: img ? (img.complete && img.naturalWidth > 0) : false,
                        dir: document.documentElement.dir || ''}; }"""
        )

    def open_detail(self, code: str, locale: str = "en") -> "BizOppPublicView":
        self.open(web_url(self.DETAIL_PATH.format(code=code), locale=locale))
        try:
            self.page.locator(".qc-bod-sec, h1").first.wait_for(timeout=60000)
        except Exception:  # noqa: BLE001 — reported by the caller
            pass
        self.page.wait_for_timeout(1500)
        return self

    def detail(self) -> dict:
        return self.page.evaluate(
            """() => { const t = s => [...document.querySelectorAll(s)].map(n => n.innerText.replace(/\\s+/g, ' ').trim());
                const one = s => { const n = document.querySelector(s); return n ? n.innerText.replace(/\\s+/g, ' ').trim() : ''; };
                return {h1: one('h1'), body: document.body.innerText, dir: document.documentElement.dir || '',
                        chips: t('.qc-bod-chip'), summary: one('.qc-bod-hero-desc'),
                        stats: t('.qc-bod-stat'), highlights: t('.qc-bod-highlight-text'),
                        submitter_name: one('.qc-bod-submitter-name'), submitter_meta: one('.qc-bod-submitter-meta'),
                        submitter_logo: [...document.querySelectorAll('.qc-bod-submitter-logo img')].map(i => i.complete && i.naturalWidth > 0),
                        defs: t('.qc-bod-def'), shots: [...document.querySelectorAll('.qc-bod-shot img, img.qc-bod-shot')].map(i => i.getAttribute('src')),
                        files: [...document.querySelectorAll('.qc-bod-file')].map(f => ({text: f.innerText.replace(/\\s+/g, ' ').trim(),
                                 hrefs: [...f.querySelectorAll('a')].map(a => a.href)})),
                        prose: t('.qc-bod-prose')}; }"""
        )

    @staticmethod
    def attachment_id(src: str) -> str:
        """fileEntryId of a public image src `/o/qc-business-opportunities-api/attachment?id=<id>`
        ("" when the src has another shape)."""
        match = _re.search(r"attachment\?(?:.*&)?id=(\d+)", src or "")
        return match.group(1) if match else ""


# --- C ---
# (Agent C keeps its field-validation driver in opportunity_fields_c_page.py.)

# --- D ---

# --- E ---
class BizOppPublicViewE(BizOppPublicView):
    """Agent E: logged-out listing hero read at a given viewport width, plus the
    layout facts a max-length check needs (overflow / clipping / page scroll)."""

    def at_width(self, width: int, height: int = 900) -> "BizOppPublicViewE":
        self.page.set_viewport_size({"width": width, "height": height})
        return self

    def open_listing(self, locale: str = "en", tab: str = "active") -> "BizOppPublicViewE":
        """As the base, then waits (<= 20 s) for the ~1 MB hero image to finish
        decoding — live 2026-10-07 it completes 0.5-1.5 s after the hero mounts,
        so an immediate read reported 'not loaded' for an image that loads."""
        super().open_listing(locale, tab)
        try:
            _wait_until(lambda: self.page.evaluate(
                "() => { const i = document.querySelector('img.qc-bol-hero-img');"
                " return !i || (i.complete && i.naturalWidth > 0); }"), timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            pass  # reported by hero()['image_loaded']
        return self

    PAGE_API = "/o/qc-business-opportunities-api/page"

    def page_api(self, locale: str = "en") -> dict:
        """The public page API item (logged-out request): ctaRedirectUrl,
        ctaRedirectPath, ctaOpenBehavior, eyebrowLabel, pageTitle, … ({} on error)."""
        language = "ar_SA" if locale == "ar" else "en_US"
        try:
            response = self.page.request.get(web_url(f"{self.PAGE_API}?languageId={language}"), timeout=60000)
            return (response.json() or {}).get("item") or {}
        except Exception as exc:  # noqa: BLE001 — reported by the caller
            _log.warning("page API read failed: %r", exc)
            return {}

    def hero_layout(self) -> dict:
        return self.page.evaluate(
            """() => { const r = n => { if (!n) return null; const b = n.getBoundingClientRect(), s = getComputedStyle(n);
                    return {text: n.innerText.trim(), left: Math.round(b.left), right: Math.round(b.right),
                            width: Math.round(b.width), height: Math.round(b.height),
                            scroll_w: n.scrollWidth, client_w: n.clientWidth,
                            overflow_x: s.overflowX, text_overflow: s.textOverflow, white_space: s.whiteSpace,
                            lines: Math.round(b.height / (parseFloat(s.lineHeight) || parseFloat(s.fontSize) * 1.2))}; };
                const vw = document.documentElement.clientWidth;
                return {viewport: vw, page_scroll_w: document.documentElement.scrollWidth,
                        eyebrow: r(document.querySelector('p.qc-bol-eyebrow')),
                        title: r(document.querySelector('h1.qc-bol-title')),
                        hero: r(document.querySelector('header.qc-bol-hero'))}; }"""
        )

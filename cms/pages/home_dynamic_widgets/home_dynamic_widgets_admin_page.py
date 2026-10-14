"""
cms/pages/home_dynamic_widgets/home_dynamic_widgets_admin_page.py —
DynamicWidgetAdminPage.

Control_Panel Page Object for PBI 129384 (QC-HOME-008 — Home Page "Dynamic
Widgets": Weather / Marhaba Guide / B2B). Public counterpart:
web/pages/home_dynamic_widgets/home_dynamic_widgets_page.py.

REWRITTEN 2026-10-08 (Phase 3). The previous version captured, edited and
"restored" the two REAL records (`QCDEMO-129384-directory`,
`QCDEMO-129384-b2b-verified`) as TEST_USER, and its restore never put the
images back. Under the 2026-10-07 user order real shared data is untouched:
every write here goes to a disposable record, and the two real codes are
refused by `_guard()`.

OBJECT NAME. `cms/Content-Admin-Guide.docx` §15: **DynamicWidget** —
widgetImageEn / widgetImageAr, redirectUrl, openInNewTab, displayOrder,
activeStatus. Slug `dynamic-widget` (lower-kebab). The guide lists no
Weather field and no widget-type field; the Weather card is rendered by the
`qc-weather-widget` client extension (inline comment on the live page).

IDENTITY. The object has no title field; the entries list's Entry column
shows the record's external reference code (a UUID for a new record). A
disposable record is therefore identified by:
  1. the entry code read from the post-save URL (`previewEntry=` /
     `editEntry=`) — never by row position; and
  2. its Redirect URL, which always carries the marker `QCTEST-<tc>-<short>`
     and is re-read from the record's own form before any state change.
`_guard()` enforces both, and refuses the two real codes outright.

ACCOUNT. Every lifecycle write signs in as the QC Site Content Editor through
`config.settings.cms_role_credentials()` — an Editor's submit lands on
Published directly (standards.md, Content Editorial Workflow). Never
TEST_USER.

Live facts this file relies on are recorded in
`.claude/qa-runs/phase3_129384_2026-10-07_report.md` (probe of 2026-10-08).
"""

from __future__ import annotations

import logging
import re
import time

from cms.pages.components.disposable_object_admin import (
    DisposableObjectAdminPage,
    FieldSpec as F,
    ROLE_EDITOR,
)
from cms.pages.components.object_authoring_page import (
    STATUS_PUBLISHED,
    STATUS_UNKNOWN,
    UploadNotApplied,
    UploadPickerUnavailable,
    normalize_status,
)

logger = logging.getLogger(__name__)

REAL_CODES = ("QCDEMO-129384-directory", "QCDEMO-129384-b2b-verified")
# Real records added by the dev team 2026-09-19 — never written by this suite.
REAL_OTHER_CODES = ("1187b438-79ce-3e21-c233-6d2011705c0d", "1f8b96c6-e81b-d98a-40da-8d67afd7a075")
MARHABA_ERC, B2B_ERC = REAL_CODES  # read-only use (public-page identity)
SLUG = "dynamic-widget"


class RefusedWrite(RuntimeError):
    """A write/delete target could not be proven to be a disposable QCTEST record."""


def marker_url(tc_id, short: str) -> str:
    return f"https://qctest-{tc_id}.example.com/QCTEST-{tc_id}-{short}"


class DynamicWidgetAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Dynamic Widget"
    SLUG = SLUG
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = ""
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "image_en": F("Widget Image (EN)", kind="file", required=True, confirmed_live=True),
        "image_ar": F("Widget Image (AR)", kind="file", required=True, confirmed_live=True),
        "redirect_url": F("Redirect URL", kind="url", required=True, confirmed_live=True),
        "open_new_tab": F("Open in New Tab", kind="checkbox", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }
    # The non-draft submit is matched by structure, not label: an Editor sees
    # "Publish", an Author "Submit for Publishing"/"Submit for Review".
    SUBMIT_FOR_REVIEW_BUTTON = 'button[type="submit"][name="status"]:not(:text-is("Save as Draft"))'
    CODE_IN_URL = re.compile(r"(?:previewEntry|editEntry)=([^&#]+)")

    def __init__(self, page):
        super().__init__(page)
        self.created: list[str] = []
        self.last_outcome: str | None = None
        self.last_toast: str = ""
        self.last_files: dict[str, str] = {}
        self.all_files: set[str] = set()

    # ---- guards ---------------------------------------------------------
    def _guard(self, code: str) -> None:
        if not code or code in REAL_CODES:
            raise RefusedWrite(f"refusing to act on real/unknown dynamic-widget record {code!r}")
        self.open_code(code)
        if code in self.created:
            return  # created by THIS test, code read from its own post-save URL
        url = self.value("redirect_url")
        if "QCTEST-" not in url:
            raise RefusedWrite(f"record {code!r} carries no QCTEST marker (Redirect URL {url!r})")

    # ---- navigation ------------------------------------------------------
    def open_code(self, code: str) -> "DynamicWidgetAdminPage":
        self.open_entry_by_code(code, locale="en")
        return self

    def open_new(self) -> "DynamicWidgetAdminPage":
        """Create form. The page renders the form, then loads the entries list
        ("Loading entries…") and re-initialises; an upload made before that
        is lost (read live 2026-10-08: EN file empty at Publish). Wait for the
        list rows first."""
        self.open_new_entry_form(locale="en")
        self.page.locator(self.ENTRIES_TABLE_ROW).first.wait_for(state="visible", timeout=35000)
        return self

    # ---- reads -----------------------------------------------------------
    def value(self, key: str, locale: str = "en") -> str:
        spec = self.spec(key)
        if spec.kind == "file":
            return self.current_file_name(spec.label) or self.uploaded_filename(spec.label) or \
                self._placeholder_file(spec.label)
        return super().value(key, locale)

    def _placeholder_file(self, label: str) -> str:
        ph = self.page.get_by_role("textbox", name=f"{label} Select File").get_attribute("placeholder") or ""
        return ph[len("Current file:"):].split(" — ")[0].strip() if ph.startswith("Current file:") else ""

    def values(self) -> dict:
        return {k: self.value(k) for k in self.FIELDS}

    def status_now(self) -> str:
        try:
            return self.current_status()
        except Exception:  # noqa: BLE001
            return STATUS_UNKNOWN

    def submit_label(self) -> str:
        loc = self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON)
        return loc.first.inner_text().strip() if loc.count() else ""

    # ---- form fill ---------------------------------------------------------
    def fill_form(self, *, url: str | None = None, order: str | None = None, new_tab: bool | None = None,
                  active: bool | None = None, image_en: str | None = None, image_ar: str | None = None,
                  tag: str = "") -> "DynamicWidgetAdminPage":
        if image_en:
            self.upload("image_en", image_en, tag=tag)
        if image_ar:
            self.upload("image_ar", image_ar, tag=tag)
        if url is not None:
            self.page.get_by_role("textbox", name=self.label_pattern("Redirect URL")).fill(url)
        if order is not None:
            box = self.page.get_by_role("spinbutton", name=self.label_pattern("Display Order"))
            try:
                box.fill(order)
            except Exception:  # noqa: BLE001 — a number input refuses non-numeric text at input
                box.fill("")
                box.press_sequentially(order)
        if new_tab is not None:
            self.set_flag("open_new_tab", new_tab)
        if active is not None:
            self.set_flag("active_status", active)
        return self

    def upload(self, key: str, fixture_path: str, tag: str = "") -> "DynamicWidgetAdminPage":
        """Uploads a uniquely named QCTEST copy and remembers its name — the
        name is how a just-created record is found again (a NEW record's save
        returns to a blank form, no entry code in the URL; read live 2026-10-08)."""
        import os

        from core.web.overlays import dismiss_overlays

        copy = self.disposable_copy(fixture_path, tag)
        label = self.spec(key).label
        # A picker left open by an earlier step is closed inside upload_file().
        try:
            self.upload_file(label, copy)
        except Exception:  # noqa: BLE001 — one retry, then the real error surfaces
            self.page.keyboard.press("Escape")
            dismiss_overlays(self.page)
            self.upload_file(label, copy)
        name = os.path.basename(copy)
        # One retry max (2026-10-13): upload_file() now raises UploadNotApplied
        # when the field shows no file, so a third, unguarded upload_file()
        # here only re-masked a picker that had already failed twice.
        if not self._file_shown(label, name):
            raise UploadNotApplied(f"{label!r}: {name!r} is not shown on the form after upload")
        self.last_files[key] = name
        self.all_files.add(name)
        return self

    def _file_shown(self, label: str, name: str, timeout_ms: int = 10000) -> bool:
        end = time.monotonic() + timeout_ms / 1000
        while time.monotonic() < end:
            try:
                if name in (self.page.locator("body").inner_text() or ""):
                    return True
            except Exception:  # noqa: BLE001
                pass
            self.page.wait_for_timeout(500)
        return False

    def try_upload(self, key: str, fixture_path: str, tag: str = "") -> str:
        """Attempt an upload that may be refused. Returns '' when the picker
        accepted it, else the refusal/exception text."""
        try:
            self.upload(key, fixture_path, tag)
            return ""
        except UploadPickerUnavailable:
            raise  # the picker never opened: not a refusal (2026-10-13, false-green guard)
        except Exception as exc:  # noqa: BLE001 — the refusal itself is the observation
            msg = ""
            try:
                frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
                msg = " ".join(frame.locator(".alert, .form-feedback-item, [role=alert]").all_inner_texts())
            except Exception:  # noqa: BLE001
                pass
            self.page.keyboard.press("Escape")
            return (msg or str(exc)).strip()[:400] or "refused"

    # ---- save --------------------------------------------------------------
    def click_submit_once(self) -> str | None:
        """Click Publish/Submit exactly once and wait for an outcome:
        'nav' | 'toast' | 'refused' | 'spinner' | None. Never re-clicks."""
        start = self.page.url
        before = self._pre_save_snapshot()
        self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON).first.click()
        self.last_outcome = self._poll_save_outcome(start, before)
        self.last_toast = self._toast_text()
        return self.last_outcome

    def code_from_url(self) -> str:
        m = self.CODE_IN_URL.search(self.page.url)
        return m.group(1) if m else ""

    def create(self, tc_id, short: str, *, active: bool = False, new_tab: bool | None = True,
               order: str = "9900", url: str | None = None, image_en: str | None = None,
               image_ar: str | None = None) -> str:
        """Create one disposable record as the signed-in account and return its
        verified entry code. `url` must carry the QCTEST marker."""
        from cms.tests.home_dynamic_widgets import upload_files as uf

        url = url or marker_url(tc_id, short)
        self.snapshot_codes()
        self.open_new()
        self.fill_form(url=url, order=order, new_tab=new_tab, active=active,
                       image_en=image_en or uf.valid("marhaba_en.jpg"),
                       image_ar=image_ar or uf.valid("marhaba_ar.png"), tag=f"{tc_id}")
        self.click_submit_once()
        try:  # the lookup must not start while the save is still in flight
            self.page.locator(self.FORM_BUSY).first.wait_for(state="detached", timeout=120000)
        except Exception:  # noqa: BLE001
            pass
        code = self.code_from_url() or self.find_saved(url)
        if not code:
            # Register anything this object put on the public site BEFORE failing,
            # so the finalizer can take it down (review 2026-10-08 §2).
            for leak in self.public_leaks():
                self.remember(leak, url)
            raise AssertionError(f"create(): no saved record found (outcome={self.last_outcome!r}, "
                                 f"refusal={self.refusal_text()!r}, url={self.page.url})")
        self.remember(code, url)
        self.open_code(code)
        if self.value("redirect_url") != url:
            raise AssertionError(f"create(): record {code} did not persist its Redirect URL")
        return code

    def edit(self, code: str, **fields) -> str | None:
        """Guarded edit + one submit. Returns the save outcome."""
        self._guard(code)
        self.fill_form(**fields)
        return self.click_submit_once()

    # ---- list ----------------------------------------------------------------
    def open_list_all(self, role: str = ROLE_EDITOR) -> "DynamicWidgetAdminPage":
        self.open_list(role)
        self._show_all()
        return self

    def _show_all(self) -> None:
        """The list pages at 10 rows by default. Its page-size select's "All"
        option is value "0" (label localised — read live 2026-10-08 as
        "الكل" in an EN session), so it is chosen by value."""
        for sel in self.page.locator("select").all():
            try:
                values = sel.locator("option").evaluate_all("os => os.map(o => o.value)")
            except Exception:  # noqa: BLE001
                continue
            if "0" in values and "10" in values:
                sel.select_option(value="0")
                try:
                    self.page.locator("text=/Page 1 of [2-9]/").first.wait_for(state="detached", timeout=10000)
                except Exception:  # noqa: BLE001
                    pass
                self.page.wait_for_timeout(1000)
                return

    def row_count(self) -> int:
        return self.page.locator(self.ENTRIES_TABLE_ROW).count()

    def codes_listed(self) -> list[str]:
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        return [rows.nth(i).locator("td").first.inner_text().strip() for i in range(rows.count())]

    SCOPE_GROUP_ID = "37246"  # qatar-chamber site (fragment's getScopeGroupId(), read live 2026-10-08)

    def count_by_url(self, url: str) -> int | None:
        """How many entries (any status) carry exactly this Redirect URL, via
        the object's headless API in the signed-in session. None if the API
        cannot answer (then the caller relies on the save outcome)."""
        from urllib.parse import quote

        from config.settings import control_panel_url

        flt = quote(f"redirectUrl eq '{url}'")
        try:
            r = self.page.request.get(control_panel_url(
                f"/o/c/dynamicwidgets/scopes/{self.SCOPE_GROUP_ID}?filter={flt}&pageSize=50"),
                headers={"Accept": "application/json"})
            if not r.ok:
                return None
            data = r.json()
            return int(data.get("totalCount", len(data.get("items", []))))
        except Exception:  # noqa: BLE001
            return None

    def count_saved_since_snapshot(self, url: str) -> int | None:
        """How many entries created since `snapshot_codes()` hold exactly this
        Redirect URL, read off each NEW row's own form (entries list, "All"
        page size). Unlike `count_by_url()` it also sees records with Active
        unticked, which the headless API does not return (read live
        2026-10-08; 136066 read 0 for its own inactive save on 2026-10-13).
        None when no snapshot was taken."""
        before = getattr(self, "_codes_before", None)
        if before is None:
            return None
        self.open_list_all()
        found = 0
        for code in [c for c in self.codes_listed() if c and c not in before and c not in REAL_CODES]:
            try:
                self.open_code(code)
                if self.value("redirect_url") == url:
                    found += 1
            except Exception:  # noqa: BLE001 -- a row that will not open is not this save
                continue
        return found

    def snapshot_codes(self) -> None:
        """Entry codes listed before a save — the list-diff fallback below
        only ever considers codes that appeared AFTER it."""
        self.open_list_all()
        self._codes_before = set(self.codes_listed())

    def find_saved_in_list(self) -> str:
        """Fallback for records the headless API does not return (Active
        unticked — read live 2026-10-08): new codes in the entries list are
        opened one by one and accepted only when the form shows the uniquely
        named file this object uploaded. Identity by content, never position."""
        before = getattr(self, "_codes_before", None)
        names = {self.last_files.get("image_en"), self.last_files.get("image_ar")} - {None}
        if before is None or not names:
            return ""
        self.open_list_all()
        for code in [c for c in self.codes_listed() if c not in before and c not in REAL_CODES]:
            try:
                self.open_code(code)
                shown = {self.value("image_en"), self.value("image_ar")}
                if any(n.rsplit(".", 1)[0] in (v or "") for n in names for v in shown):
                    return code
            except Exception:  # noqa: BLE001
                continue
        return ""

    def find_saved(self, url: str, timeout: float = 30.0) -> str:
        """Entry code of the record THIS page object just saved: same Redirect
        URL and the same uniquely named EN image (or AR image if no EN one was
        uploaded). Polls the headless API (index lag). '' if none."""
        from urllib.parse import quote

        from config.settings import control_panel_url

        names = {self.last_files.get("image_en"), self.last_files.get("image_ar")} - {None}
        if not names:
            return ""
        if not url:
            return self.find_saved_in_list()
        flt = quote(f"redirectUrl eq '{url}'")
        end = time.monotonic() + timeout
        while True:
            try:
                r = self.page.request.get(control_panel_url(
                    f"/o/c/dynamicwidgets/scopes/{self.SCOPE_GROUP_ID}?filter={flt}&pageSize=50"),
                    headers={"Accept": "application/json"})
                for it in (r.json().get("items", []) if r.ok else []):
                    files = {(it.get("widgetImageEn") or {}).get("name"), (it.get("widgetImageAr") or {}).get("name")}
                    if any(n.rsplit(".", 1)[0] in (f or "") for n in names for f in files) and it.get("externalReferenceCode") not in REAL_CODES:
                        return it["externalReferenceCode"]
            except Exception:  # noqa: BLE001
                pass
            if time.monotonic() > end:
                return self.find_saved_in_list()
            self.page.wait_for_timeout(3000)

    LEDGER = ".claude/qa-runs/129384_qctest_ledger.txt"

    def remember(self, code: str, url: str = "") -> None:
        if code not in self.created:
            self.created.append(code)
            try:
                with open(self.LEDGER, "a", encoding="utf-8") as fh:
                    fh.write("\t".join((time.strftime("%Y-%m-%d %H:%M:%S"), code, url)) + "\n")
            except Exception:  # noqa: BLE001
                pass

    def row_status_for(self, code: str) -> str:
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")')
        if row.count() == 0:
            return ""
        return normalize_status(row.first.locator("td").nth(1).inner_text())

    def raw_row_status(self, code: str) -> str:
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")')
        return " ".join(row.first.locator("td").nth(1).inner_text().split()) if row.count() else ""

    # ---- lifecycle -----------------------------------------------------------
    def unpublish_code(self, code: str) -> "DynamicWidgetAdminPage":
        self._guard(code)
        self.open_list_all()
        self.filter_entries(code)
        self.unpublish_entry(code)
        return self

    def _row_by_exact_code(self, code: str):
        """The entries-list row whose Entry cell is exactly `code`, or None.
        The list paginates at 10 rows (observed 2026-10-13: test-created rows
        sat beyond page 1, so an exact-match scan of page 1 never found them
        and teardown deletes silently failed). Widen the page size to its
        largest option first, then scan every row."""
        def scan():
            rows = self.page.locator(self.ENTRIES_TABLE_ROW)
            for i in range(rows.count()):
                row = rows.nth(i)
                if " ".join(row.locator("td").first.inner_text().split()) == code:
                    return row
            return None

        self.open_list_all()
        try:
            self.filter_entries(code)
        except Exception:  # noqa: BLE001 -- the widened scan below still finds it
            pass
        found = scan()
        if found is not None:
            return found
        # Not on the (filtered) first page: reload the unfiltered list and
        # widen the page size to its last option ("الكل" = All; options are
        # texts 10/25/50/100/الكل, read live 2026-10-13). Never `networkidle`
        # here -- the site chatbot polls forever.
        self.open_list_all()
        size = self.page.locator('select:has(option:text-is("100"))').first
        if size.count():
            before = self.page.locator(self.ENTRIES_TABLE_ROW).count()
            size.select_option(index=size.locator("option").count() - 1)
            try:
                self.page.wait_for_function(
                    "n => document.querySelectorAll('table tbody tr').length > n",
                    arg=before, timeout=30000)
            except Exception:  # noqa: BLE001 -- fewer rows than one page: nothing more to load
                pass
        return scan()

    def delete_created(self, code: str) -> bool:
        """Teardown — permanently delete a record THIS test created (user
        approval 2026-10-12: test data is deleted, not only deactivated).
        Only codes in `self.created`, never REAL_CODES; the row is matched by
        its exact first-cell entry code (not substring) and deleted through
        that row's own `data-qc-oel-delete` control, then the list is re-read
        to prove it is gone. Never raises; returns success."""
        if not code or code in REAL_CODES or code not in self.created:
            return False
        try:
            # The Editor role has no Delete row action (role sheet 2026-09-27:
            # Editor = add/edit/publish/unpublish/archive/restore). Teardown
            # deletes as the admin TEST_USER, swapping cookies locally only.
            from config.settings import settings as _s
            from cms.pages.control_panel.login_page import CmsLoginPage as _L
            _L(self.page).ensure_signed_in_as(_s.test_user, _s.test_password)
            target = self._row_by_exact_code(code)
            if target is None:
                return True  # already gone
            if not getattr(self.page, "_qc_delete_dialogs", False):
                def _accept(d):
                    try:
                        d.accept()
                    except Exception:  # noqa: BLE001 -- another handler already answered it
                        pass
                self.page.on("dialog", _accept)
                self.page._qc_delete_dialogs = True
            target.locator("[data-qc-oel-delete]").first.click()
            self.page.wait_for_timeout(3000)  # confirm() chain + row removal; verified by re-read below
            return self._row_by_exact_code(code) is None
        except Exception:  # noqa: BLE001 -- teardown reports, never masks
            return False

    def deactivate(self, code: str, attempts: int = 3) -> bool:
        """Teardown — take a disposable record off the public site and VERIFY
        it by re-reading the record's own form. Retries (network drops on
        2026-10-08 left 7 test cards public). Never raises; returns success."""
        for _ in range(attempts):
            try:
                self._guard(code)
                if not self.flag("active_status"):
                    return True
                self.set_flag("active_status", False)
                self.click_submit_once()
                self.open_code(code)
                if not self.flag("active_status"):
                    return True
            except Exception as exc:  # noqa: BLE001 — retried; the final failure is logged loudly
                logger.warning("deactivate(%s) attempt failed: %s", code, exc)
                try:
                    self.page.wait_for_timeout(5000)
                except Exception:  # noqa: BLE001
                    pass
        logger.error("deactivate(%s) FAILED after %d attempts — record may still be PUBLIC", code, attempts)
        return False

    def sweep_public_qctest(self) -> dict:
        """Run-level guard: every card in the PUBLIC active feed whose images
        are QCTEST-named (and is not a real record) is unticked and verified.
        Returns {erc: inactive_ok}."""
        from config.settings import control_panel_url

        result = {}
        try:
            r = self.page.request.get(control_panel_url(
                f"/o/c/dynamicwidgets/scopes/{self.SCOPE_GROUP_ID}?filter=activeStatus%20eq%20true&pageSize=100"),
                headers={"Accept": "application/json"})
            items = r.json().get("items", []) if r.ok else []
        except Exception as exc:  # noqa: BLE001
            logger.error("sweep_public_qctest: feed unreadable: %s", exc)
            return {"<feed unreadable>": False}
        for it in items:
            erc = it.get("externalReferenceCode")
            names = [str((it.get(k) or {}).get("name", "")) for k in ("widgetImageEn", "widgetImageAr")]
            if erc in REAL_CODES or erc in REAL_OTHER_CODES or not all(n.startswith("QCTEST-") for n in names):
                continue
            self.remember(erc, it.get("redirectUrl", ""))
            result[erc] = self.deactivate(erc)
        return result

    def public_leaks(self) -> list[str]:
        """Entry codes in the PUBLIC active feed that this object created
        (by code, or by one of its uniquely named uploads)."""
        from config.settings import control_panel_url

        try:
            r = self.page.request.get(control_panel_url(
                f"/o/c/dynamicwidgets/scopes/{self.SCOPE_GROUP_ID}?filter=activeStatus%20eq%20true&pageSize=50"),
                headers={"Accept": "application/json"})
            items = r.json().get("items", []) if r.ok else []
        except Exception:  # noqa: BLE001
            return []
        stems = {n.rsplit(".", 1)[0] for n in self.all_files}
        leaks = []
        for it in items:
            erc = it.get("externalReferenceCode")
            names = " ".join(str((it.get(k) or {}).get("name", "")) for k in ("widgetImageEn", "widgetImageAr"))
            if erc not in REAL_CODES and (erc in self.created or any(st in names for st in stems)):
                leaks.append(erc)
        return leaks

    def delete_qctest(self, code: str) -> bool:
        """Teardown step 2 — delete a disposable record by its verified code.
        Refuses anything `_guard()` cannot prove is QCTEST. Never raises."""
        try:
            self._guard(code)
            self.open_list_all()
            self.filter_entries(code)
            row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")')
            if row.count() != 1:
                return False
            ok = self.delete_entry_by_code(code)
            self.open_list_all()
            return ok and self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")').count() == 0
        except Exception:  # noqa: BLE001
            return False

    def wait_status(self, code: str, expected: str, timeout: float = 90.0) -> bool:
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            self.open_code(code)
            if self.status_now() == expected:
                return True
            self.page.wait_for_timeout(3000)
        return False


# Backwards-compatible name used by older imports.
HomeDynamicWidgetsAdminPage = DynamicWidgetAdminPage
PUBLISHED = STATUS_PUBLISHED

"""
cms/pages/home_strategic_direction/home_strategic_direction_admin_page.py —
StrategicPillarCardAdminPage (PBI 129381, Home — Strategic Direction).

REWRITTEN 2026-10-07 (Phase 3, A-129381). The previous version drove the
retired Content & Data grid (`[role=menuitem] Content & Data`), signed in as
TEST_USER, and carried `delete_pillar_card_by_title()`: an unguarded
`:has-text(title)` substring delete with no QCTEST check. That method is GONE —
on this PBI's own batch a positional delete destroyed the real "Objectives"
card 49108 (docs/qa-decisions-log.md, 2026-09-03).

Object name: Content-Admin-Guide.docx §7 "Home — Strategic Direction":
`StrategicPillarCard (one entry per pillar)` — pillarTitle (bilingual),
pillarDescription (bilingual, rich text), pillarIcon, displayOrder,
activeStatus. Object Authoring slug `strategic-pillar-card`, re-read live
2026-10-07 (.claude/qa-runs/a129381/probe1.json). The guide lists NO
section-level object (no Section Tag / Heading / Description, no section
publish status): those are not CMS content records on this build.

IDENTITY (CONFIRMED LIVE 2026-10-07, probe1.json): this object's Entry column
shows the externalReferenceCode — real rows QCDEMO-129381-STRATEGIC_PILLAR_CARD-
01/02/03 = ids 49056/49082/49108 — NEVER the Pillar Title. Every title-based
row lookup inherited from ObjectAuthoringPage would therefore find nothing, so
each one is overridden here to go through a VERIFIED code: a code is accepted
for a title only after that entry's own form reads Pillar Title == title
exactly. The real QCDEMO rows are never opened by the scan.

SAFETY CONTRACT — the only delete path in this feature is
`delete_disposable()` below. It:
  1. refuses any title that does not start with `QCTEST-`;
  2. resolves the code by reading Pillar Title back off each non-QCDEMO row's
     own form (exact match; two matches raise RefusedDelete);
  3. re-reads Pillar Title from that code's form immediately before the click;
  4. requires exactly one row for the code, and that row's delete link to carry
     `data-qc-oel-label` == the code and a `data-qc-oel-delete` id that is NOT
     one of the real pillars (49056 Vision, 49082 Mission, 49108 Objectives);
  5. clicks only `a[data-qc-oel-delete="<that id>"]`, then re-lists and reports
     success only when that id is gone.
Nothing in this feature calls `newest_entry_code()`, `delete_entry_by_title()`
or `delete_entry_by_code()`.
"""

from __future__ import annotations

import logging
import re

from cms.pages.components.disposable_object_admin import (
    DISPOSABLE_PREFIX,
    ROLE_EDITOR,
    DisposableObjectAdminPage,
    FieldSpec,
)
from cms.pages.components.object_authoring_page import ObjectAuthoringPage, normalize_status

logger = logging.getLogger(__name__)

PILLAR_ICON_FIXTURE = "web/tests/home_strategic_direction/fixtures/pillar_icon.png"

# Real, shared pillar records (docs/qa-environment-notes.md §5d/§5e). Never a
# delete target; never mutated without ID-named user approval.
REAL_PILLAR_IDS = frozenset({"49056", "49082", "49108"})
REAL_PILLAR_TITLES = ("Vision", "Mission", "Objectives")


class RefusedDelete(RuntimeError):
    """A delete target could not be positively proven to be a QCTEST record."""


class StrategicPillarCardAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Strategic Pillar Card"
    SLUG = "strategic-pillar-card"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "pillar_title"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "pillar_title": FieldSpec("Pillar Title", "text", bilingual=True, required=True, confirmed_live=True),
        "pillar_description": FieldSpec(
            "Pillar Description", "rich", bilingual=True, required=True, ref="pillarDescription",
            default="QCTEST disposable pillar card description.",
            default_ar="وصف بطاقة ركيزة اختبارية.", confirmed_live=True,
        ),
        "pillar_icon": FieldSpec("Pillar Icon", "file", required=True, confirmed_live=True),
        # Multiples of 100 (OBJECT-AUTHORING-GUIDE); 9900 sorts after the real
        # cards so a QCTEST card never displaces Vision as the first card.
        "display_order": FieldSpec("Display Order", "number", required=True, default="9900", confirmed_live=True),
        "active_status": FieldSpec("Active Status", "checkbox", confirmed_live=True),
    }
    FILES = {"pillar_icon": PILLAR_ICON_FIXTURE}

    # The workflow submit button's LABEL varies by role and object (Editor:
    # "Publish", probe1.json; Author: "Submit for Review" or the legacy wording,
    # heads-up 2026-10-07). Matched by structure instead: the form's two
    # `name="status"` submit buttons are Save as Draft and the workflow submit.
    SUBMIT_FOR_REVIEW_BUTTON = 'button[type="submit"][name="status"]:not(:text-is("Save as Draft"))'

    REAL_CODE_PREFIX = "QCDEMO-129381-STRATEGIC_PILLAR_CARD"
    # CONFIRMED LIVE 2026-10-08 (probe7): `<select data-qc-oel-page-size>` with
    # options 10/25/50/100 (no value attrs) + value "0" (all). Default 10: a
    # card beyond row 10 sits on page 2 and was invisible to every lookup.
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"

    def __init__(self, page):
        super().__init__(page)
        self._codes: dict[str, str] = {}
        self._role = ROLE_EDITOR
        self._pending_title: str | None = None

    # ---- session ----------------------------------------------------------
    def sign_in(self, role: str) -> "StrategicPillarCardAdminPage":
        self._role = role
        super().sign_in(role)
        return self

    def open(self, url: str) -> None:
        """Bare navigation that re-signs as THIS test's role, never TEST_USER.

        BasePage.open() runs core/web/session_guard.reauthenticate(), which
        silently signs a dropped/logged-out context into TEST_USER whenever it
        lands on a `manage-*` URL (heads-up 2026-10-07). An Author or Site
        Member case would then run as super-admin. core/ is not edited; this
        page object simply does not go through that path."""
        from cms.pages.control_panel.login_page import CmsLoginPage
        from config.settings import cms_role_credentials
        from core.web.session_guard import is_dead_session, is_login_form_showing

        self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        if "/manage-" in url and (is_login_form_showing(self.page) or is_dead_session(self.page)):
            email, password = cms_role_credentials(self._role)
            CmsLoginPage(self.page).open_login().login(email, password)
            self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
        try:
            from core.web.overlays import dismiss_overlays
            dismiss_overlays(self.page)
        except Exception:  # noqa: BLE001
            pass

    def filter_entries(self, text: str) -> "StrategicPillarCardAdminPage":
        """The list search matches the Entry column (codes), not titles, so it
        is not used. Instead show the largest page so no row hides on page 2."""
        sel = self.page.locator(self.PAGE_SIZE_SELECT)
        try:
            if sel.count() and sel.first.input_value() != "0":
                sel.first.select_option(value="0")
                # wait until the table shows every row the "N total" counter promises
                self.page.wait_for_function(
                    "() => { const m = document.body.innerText.match(/([0-9]+) total/);"
                    " return !m || document.querySelectorAll('table tbody tr').length >= +m[1]; }",
                    timeout=20000,
                )
        except Exception:  # noqa: BLE001 — a smaller page is still correct, only slower
            pass
        return self

    # ---- identity: Pillar Title -> verified entry code --------------------
    def _row_codes(self) -> list[tuple[str, str]]:
        """(Entry-column code, entry id) for every listed row."""
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        out = []
        for i in range(rows.count()):
            row = rows.nth(i)
            code = row.locator("td").first.inner_text().strip()
            ids = row.evaluate(
                "el => Array.from(el.querySelectorAll('*')).flatMap(n => Array.from(n.attributes)"
                ".filter(a => a.name.startsWith('data-qc-oel-') && a.name !== 'data-qc-oel-label')"
                ".map(a => a.value))"
            )
            out.append((code, ids[0] if ids else ""))
        return out

    API_BASE = "/o/c/strategicpillarcards"

    def _api_title(self, entry_id: str) -> str | None:
        """Pillar Title (EN) of one entry by its numeric id via the object's
        own headless endpoint, with this page's signed-in session. None when
        the API does not answer (caller falls back to the form). REVIEW FIX
        2026-10-08 (item 7): replaces one form load per row per lookup."""
        if not entry_id or entry_id in REAL_PILLAR_IDS:
            return None
        from config.settings import control_panel_url

        try:
            resp = self.page.request.get(
                control_panel_url(f"{self.API_BASE}/{entry_id}"),
                headers={"Accept": "application/json", "Accept-Language": "en-US"},
                timeout=20000,
            )
            if resp.status != 200:
                return None
            body = resp.json()
            i18n = body.get("pillarTitle_i18n") or {}
            return i18n.get("en_US") or body.get("pillarTitle") or ""
        except Exception:  # noqa: BLE001
            return None

    def _read_title(self, code: str) -> str | None:
        """Pillar Title (EN) read off the entry's OWN FORM, or None when the
        form did not load. Used by the delete guard (identity re-read right
        before the click) and as the API fallback. The input renders empty and
        fills a moment later, so it is polled up to 20 s after the editing
        banner appears. Nothing is cached (review fix 2026-10-08: a sticky ""
        hid titled QCTEST records from teardown)."""
        if not code or code.startswith(self.REAL_CODE_PREFIX):
            return None
        try:
            self.open(self._manage_url(edit_entry=code, locale="en"))
            self._entry_code = code
            box = self.page.locator(self.EN_TITLE_INPUT)
            box.first.wait_for(state="visible", timeout=30000)
            self.page.locator(self.CANCEL_AND_ADD_NEW_LINK).first.wait_for(state="visible", timeout=30000)
            value = ""
            for _ in range(40):
                value = box.first.input_value()
                if value:
                    break
                self.page.wait_for_timeout(500)
            return value
        except Exception:  # noqa: BLE001
            return None

    def _verify_code(self, code: str, title: str) -> bool:
        return self._read_title(code) == title

    # The 27 untitled Drafts listed in the 2026-10-07 report §7 (no title, not
    # QCTEST, not deletable by this page). The headless GET-by-id answers 404
    # for drafts (probe9, 2026-10-08), so without this fixed list every lookup
    # loaded their 27 forms. This is a FIXED id list from the report, not a
    # learned cache: a new record can never land in it.
    KNOWN_UNTITLED_IDS = frozenset({
        "555085", "559326", "559408", "559544", "559582", "559611", "559663", "564387", "564393",
        "564454", "564472", "564536", "564662", "564680", "564723", "564745", "564768", "564800",
        "564976", "565001", "565024", "565048", "565074", "565099", "565133", "565198", "565220",
    })

    def _title_of(self, code: str, entry_id: str) -> str | None:
        if entry_id in self.KNOWN_UNTITLED_IDS:
            return ""
        got = self._api_title(entry_id)
        return got if got is not None else self._read_title(code)

    def code_for(self, title: str, refresh: bool = False, wait: bool = True) -> str:
        """Verified entry code for `title`, or "" when no entry carries it.
        Titles come from the headless API by entry id (no form loads); a row
        the API cannot answer is read from its form. Re-lists up to 3 times
        when a row was unreadable, or (with `wait`) when a just-saved record
        has not reached the list yet."""
        import time

        if not refresh and title in self._codes:
            return self._codes[title]
        found = ""
        for attempt in range(3):
            self.open_entries_list(locale="en")
            self.filter_entries(title)
            candidates = [
                (code, entry_id) for code, entry_id in self._row_codes()
                if code and not code.startswith(self.REAL_CODE_PREFIX) and entry_id not in REAL_PILLAR_IDS
            ]
            unreadable = False
            for code, entry_id in candidates:
                got = self._title_of(code, entry_id)
                if got is None:
                    unreadable = True
                elif got == title:
                    # Save as Draft can leave two copies with the same title (see
                    # report); reads use the first, delete_disposable() removes all.
                    found = found or code
            if found or not (unreadable or wait):
                break
            time.sleep(5)
        if found:
            self._codes[title] = found
        else:
            self._codes.pop(title, None)
        return found

    def _remember_saved(self, title: str) -> None:
        """A save navigates to `?previewEntry=<code>`; that code is accepted
        only once the entry's own form confirms the title."""
        # After Save as Draft the page lands on `?editEntry=<code>` (probe8,
        # 2026-10-08); older builds used `?previewEntry=<code>`.
        m = re.search(r"(?:previewEntry|editEntry)=([^&#]+)", self.page.url)
        if m and self._verify_code(m.group(1), title):
            self._codes[title] = m.group(1)

    def _row(self, title: str):
        code = self.code_for(title)
        if not code:
            return None, ""
        self.open_entries_list(locale="en")
        self.filter_entries(code)
        return self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")'), code

    # ---- title-based overrides --------------------------------------------
    def row_status_text(self, title: str) -> str:
        row, _ = self._row(title)
        if row is None or row.count() != 1:
            return ""
        return normalize_status(row.locator("td").nth(1).inner_text())

    def raw_row_status(self, title: str) -> str:
        row, _ = self._row(title)
        if row is None or row.count() != 1:
            return ""
        return row.locator("td").nth(1).inner_text().strip().upper()

    def row_visible(self, title: str) -> bool:
        return bool(self.code_for(title, refresh=True, wait=False))

    def entry_exists(self, title: str, role: str) -> bool:
        self.sign_in(role)
        return bool(self.code_for(title, refresh=True, wait=False))

    def status_of(self, title: str, role: str) -> str:
        self.sign_in(role)
        return self.row_status_text(title)

    def open_entry_by_edit_link(self, title: str) -> "StrategicPillarCardAdminPage":
        code = self.code_for(title)
        if not code:
            raise AssertionError(f"no entry with Pillar Title {title!r}")
        if self._read_title(code) != title:
            raise AssertionError(f"entry {code} did not load with Pillar Title {title!r}")
        return self

    def row_preview_url(self, title: str) -> str:
        row, code = self._row(title)
        if row is None or row.count() != 1:
            return ""
        return self.row_preview_url_by_code(code)

    def _run_row_action(self, title_or_code: str, action: str, comment: str = ""):
        code = title_or_code if title_or_code in self._codes.values() else self.code_for(title_or_code)
        if not code:
            raise AssertionError(f"no entry with Pillar Title {title_or_code!r}")
        self.open_entries_list(locale="en")
        self.filter_entries(code)
        return ObjectAuthoringPage._run_row_action(self, code, action, comment)

    def row_offers_action(self, title: str, action: str) -> bool:
        row, _ = self._row(title)
        if row is None or row.count() != 1:
            return False
        return row.locator(f"[{self.ROW_ACTION_ATTRS[action]}]").count() > 0

    def fill_required(self, title, skip=(), active=False, files=None):
        self._pending_title = title if title and title.startswith(DISPOSABLE_PREFIX) else None
        self._pending_skip = tuple(skip)
        return super().fill_required(title, skip=skip, active=active, files=files)

    EN_TITLE_INPUT = 'input[name="ObjectField_pillarTitle"]'
    AR_TITLE_INPUT = "#qc-ar-pillarTitle"

    def _restore_lost_title(self) -> None:
        """HEALED 2026-10-08. Serial runs saved drafts with an EMPTY Pillar
        Title (EN + AR) although the title had been typed first (7 untitled
        drafts: 555085, 559326, 559408, 559544, 559582, 559611, 559663 —
        description / order / active kept, title + icon lost). The title
        inputs are re-checked right before the save click and re-typed if
        the form dropped them. Recorded as an INCONCLUSIVE finding in the
        report; this keeps every QCTEST record findable and deletable."""
        title = self._pending_title
        if not title or "pillar_title" in getattr(self, "_pending_skip", ()):
            return
        try:
            en = self.page.locator(self.EN_TITLE_INPUT).first
            if en.count() and en.input_value() != title:
                # The EN title must be exactly what the test typed. AR is only
                # refilled when it was lost TOGETHER with EN, so a test that
                # empties AR on purpose keeps it empty.
                logger.warning("Pillar Title changed/lost before save (%r) — re-typing", en.input_value())
                en.fill(title)
                ar = self.page.locator(self.AR_TITLE_INPUT).first
                if ar.count() and not ar.input_value():
                    ar.fill(f"{title} AR")
                icon = self.page.locator('input[name="ObjectField_pillarIcon"]').first
                if "pillar_icon" not in getattr(self, "_pending_skip", ()) and icon.count() and not icon.input_value():
                    logger.warning("Pillar Icon was lost with the title — re-uploading")
                    self.upload("pillar_icon", self.FILES["pillar_icon"], tag=title)
        except Exception:  # noqa: BLE001 — the save itself reports any real problem
            pass

    INVALID_FIELD = '[aria-invalid="true"], .has-error, .is-invalid'

    def refusal_visible(self) -> bool:
        """Base check (red bar / English refusal text) OR any field marked
        invalid — a structural, language-neutral signal. Healed 2026-10-08:
        under the Arabic admin locale the refusal bar and Arabic inline errors
        rendered (reports/manual-exec-129381-135543.png) but the base check,
        tuned to the English text, missed them. No Arabic-text locator used."""
        if super().refusal_visible():
            return True
        try:
            self.page.locator(self.INVALID_FIELD).first.wait_for(state="attached", timeout=5000)
            return True
        except Exception:  # noqa: BLE001
            return False

    def field_present(self, key: str) -> bool:
        """Rich-text editors mount their iframe a moment after the form;
        waits for it (healed 2026-10-08, 135539 counted before mount)."""
        if self.spec(key).kind == "rich":
            try:
                self.page.locator(self._rich_iframe(key, "en")).first.wait_for(state="attached", timeout=20000)
                return True
            except Exception:  # noqa: BLE001
                return False
        return super().field_present(key)

    def _poll_save_outcome(self, start_url: str | None, before: dict | None = None) -> str | None:
        """Same outcome poll as ObjectAuthoringPage._poll_save_outcome (shared
        file, not edited), but this page lands on `?editEntry=<code>` after a
        save (probe8, 2026-10-08), not only `?previewEntry=`. Without this,
        every draft save waited the full 120 s cap and the caller then
        navigated away mid-save (review item 7)."""
        import time

        if before is None:
            before = self._pre_save_snapshot()
        t0 = time.monotonic()
        deadline = t0 + self.SETTLE_OUTCOME_TIMEOUT_MS / 1000
        not_started_deadline = t0 + self.SETTLE_NOT_STARTED_CAP_MS / 1000
        seen_busy = started = False
        while time.monotonic() < deadline:
            url = self.page.url
            if ("previewEntry=" in url or "editEntry=" in url) and (start_url is None or url != start_url):
                return "nav"
            toast = self._toast_text()
            if toast != before["toast"] and self.SAVE_SUCCESS_TEXT.search(toast):
                return "toast"
            if self._count(self.SAVE_REFUSAL) > before["refusals"]:
                return "refused"
            if not started and self._count(self.SUBMIT_STARTED) > 0:
                started = True
            busy = self._count(self.FORM_BUSY)
            if busy > 0:
                seen_busy = started = True
            elif seen_busy and busy == 0:
                return "spinner"
            if not started and time.monotonic() > not_started_deadline:
                return None
            try:
                self.page.wait_for_timeout(300)
            except Exception:  # noqa: BLE001 — page navigating
                time.sleep(0.3)
        return None

    def save_as_draft(self):
        self._restore_lost_title()
        super().save_as_draft()
        if self._pending_title:
            self._remember_saved(self._pending_title)
        return self

    def submit_for_review(self):
        self._restore_lost_title()
        super().submit_for_review()
        if self._pending_title:
            self._remember_saved(self._pending_title)
        return self

    def _rich_iframe(self, key: str, locale: str) -> str:
        # Two CKEditors on the form, EN then AR (probe1.json).
        return f'{self.RICH_TEXT_EDITOR_IFRAME_CSS} >> nth={1 if locale == "ar" else 0}'

    # ---- the ONLY delete path in this feature --------------------------
    def _delete_verified_code(self, code: str, title: str) -> bool:
        """Delete ONE entry by its code after re-proving it is `title` (a
        QCTEST title): form re-read, single row, label == code, id not real."""
        if not title.startswith(DISPOSABLE_PREFIX):
            raise RefusedDelete(f"refusing to delete non-QCTEST record {title!r}")
        if not code or code.startswith(self.REAL_CODE_PREFIX):
            raise RefusedDelete(f"{title!r} resolved to real/empty code {code!r}")
        form_title = self._read_title(code)
        if form_title != title:
            raise RefusedDelete(f"{code}: form Pillar Title {form_title!r} != {title!r}")
        self.open_entries_list(locale="en")
        self.filter_entries(code)
        rows = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{code}")')
        if rows.count() != 1:
            raise RefusedDelete(f"{rows.count()} rows match code {code!r}")
        delete_link = rows.first.locator("a[data-qc-oel-delete]").first
        entry_id = delete_link.get_attribute("data-qc-oel-delete") or ""
        label = delete_link.get_attribute("data-qc-oel-label") or ""
        if not entry_id or entry_id in REAL_PILLAR_IDS or label != code:
            raise RefusedDelete(f"{code}: delete link id={entry_id!r} label={label!r}; refusing")
        link = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
        if link.count() != 1:
            raise RefusedDelete(f"{link.count()} delete links for id {entry_id}")
        self.page.once("dialog", lambda d: d.accept())
        link.click(force=True)
        try:
            link.wait_for(state="detached", timeout=15000)
        except Exception:  # noqa: BLE001 — verified below by re-listing
            pass
        # Verify by re-listing: teardown "delete failed" warnings have been false before.
        self.open_entries_list(locale="en")
        self.filter_entries(code)
        return self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]').count() == 0

    def _codes_with_title(self, title: str) -> list:
        self.open_entries_list(locale="en")
        self.filter_entries(title)
        out = []
        for code, entry_id in self._row_codes():
            if code and not code.startswith(self.REAL_CODE_PREFIX) and entry_id not in REAL_PILLAR_IDS:
                if self._title_of(code, entry_id) == title:
                    out.append(code)
        return out

    def delete_disposable(self, title: str, role: str = ROLE_EDITOR) -> bool:
        """Guarded delete — see the module docstring's SAFETY CONTRACT.
        Deletes EVERY entry whose own form reads exactly this QCTEST title
        (Save as Draft can leave two copies — see report), each by its own
        verified code. Raises RefusedDelete on any identity doubt; returns
        False when nothing carrying the title was found or a click did not
        stick."""
        if not title or not title.startswith(DISPOSABLE_PREFIX):
            raise RefusedDelete(f"refusing to delete non-QCTEST record {title!r}")
        try:
            self.sign_in(role)
            codes = self._codes_with_title(title)
            if not codes:
                return False
            ok = all([self._delete_verified_code(code, title) for code in codes])
            if ok:
                self._codes.pop(title, None)
            return ok
        except RefusedDelete:
            raise
        except Exception:  # noqa: BLE001 — teardown never masks the test result
            return False

    # ---- conveniences ---------------------------------------------------
    def create(self, title: str, role: str = ROLE_EDITOR, active: bool = True,
               display_order: str | None = None, submit: bool = True) -> "StrategicPillarCardAdminPage":
        """Fill every required field (QCTEST icon copy), tick Active Status
        when `active`, then Submit for Review (or Save as Draft)."""
        self.open_form(role)
        self.fill_required(title, active=active, files=self.FILES)
        if display_order is not None:
            self.fill("display_order", display_order)
        if submit:
            self.submit_for_review()
        else:
            self.save_as_draft()
        return self

    def open_by_title(self, title: str, role: str = ROLE_EDITOR) -> "StrategicPillarCardAdminPage":
        self.sign_in(role)
        self.open_entry_by_edit_link(title)
        return self

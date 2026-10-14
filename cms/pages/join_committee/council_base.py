"""
cms/pages/join_committee/council_base.py — shared bases for Engineer A4's
Councils & Committees Page Objects (PBIs 130716, 130717, 130718, 130719).

Form mechanics are REUSED by import, never copied:
  * FragmentFormMixin (cms/pages/certificate_of_origin/fragment_form_mixin.py):
    save watch by ID, positive-signal refusal oracle, status / History / delete
    by ID, cached role sessions checked against my-user-account, the Editor
    Pending->Published re-read, date inputs by `input[name=ObjectField_<ref>]`;
  * _Po (cms/pages/partners_offers/partners_offers_admin_page.py): list-search
    teardown when no ID is known, settle-and-retry on ERR_ABORTED during a role
    login, "+ Add New" reveal when the manage page lands on a record preview.
Neither those files nor the shared ObjectAuthoringPage is edited.

Live facts (read-only probes 2026-10-04 as QC Site Content Editor, Form
Manager, Author and Contributor, reports/bug-evidence/a4_probe*_20261004.json):
  * Every object below is on the live Object Authoring sidebar; slugs and field
    refs (`ObjectField_<ref>` / `qc-ar-<ref>`) were read from the forms.
  * Two submit-button families: "Publish" (drafts on) and, on drafts-off record
    types, a button still labelled with the retired wording (vocabulary drift,
    CLAUDE.md non-negotiable 2) or "Submit for Review" for the Author. The submit
    is therefore located structurally (_StructuralSubmit), never by that label.
  * Submissions objects (Committee Joining Request, Business Council Membership
    Request, QAFL Membership Submission) have no create form for any role: a
    QCTEST submission is created through the PUBLIC form. Their rows carry
    data-qc-oel-view / -approve / -reject. Approve raises one confirm(); Reject
    raises a prompt ("Enter the reason (required)") and, on an empty reason, an
    alert "A rejection reason is required." with the record left Pending.
"""

from __future__ import annotations

import re
import time

from cms.pages.components.disposable_object_admin import DISPOSABLE_PREFIX
from cms.pages.control_panel import login_page as _lp
from cms.pages.partners_offers.partners_offers_admin_page import _Po
from config.settings import cms_role_credentials, control_panel_url

ROLE_FORM_MANAGER = "Form Manager"


class _StructuralSubmit:
    """The form's own submit button that is neither Save as Draft nor Unpublish
    nor the hidden helper button (whatever its label reads)."""

    SUBMIT_FOR_REVIEW_BUTTON = (
        'form:has(button:has-text("Save as Draft")) button[type="submit"]'
        ':is(:has-text("Submit"), :has-text("Publish"))'
        ':not(:has-text("Save as Draft")):not(:has-text("Unpublish")):visible'
    )


class _DraftsOff(_StructuralSubmit):
    """Drafts are turned off for the record type (live tooltip): the form is
    ready when the submit button is visible."""

    FORM_READY = _StructuralSubmit.SUBMIT_FOR_REVIEW_BUTTON


class _Council(_StructuralSubmit, _Po):
    """INCIDENT GUARD (2026-10-04, smoke tc_144506): manage-business-council-
    request-page opens the LIVE entry's edit form by default (submit visible,
    no "+ Add New" needed), so a "new" QCTEST fill was written onto the live
    entry 183176 with PUT /o/c/<plural>/183176. Two guards now apply to every
    Councils page object:
      1. a create form is ALWAYS reached through "+ Add New" and is verified
         empty (title input blank) before anything is typed;
      2. a network guard aborts any PUT / PATCH / DELETE to /o/c/<plural>/<id>
         whose id was listed on the manage page when the form was opened (real
         content) or is a known live singleton id, unless that id is a record
         this test itself created."""

    SLUG_CONFIRMED_LIVE = True  # read live 2026-10-04 (Object Authoring sidebar + forms)

    @staticmethod
    def label_pattern(field_label: str):
        """Smoke 2026-10-04: labels holding '/' ("Committee/Sector Name",
        "Display Order / Number") broke Playwright's selector parser when the
        shared regex was serialised; '/' is matched as any single char."""
        import re as _re
        from cms.pages.components.object_authoring_page import ObjectAuthoringPage
        pat = ObjectAuthoringPage.label_pattern(field_label)
        return _re.compile(pat.pattern.replace("/", "."), pat.flags)

    LIVE_IDS: tuple[str, ...] = ()

    def _protected(self) -> set:
        return self.__dict__.setdefault("_a4_protected", set(self.LIVE_IDS))

    def _install_guard(self):
        if self.__dict__.get("_a4_guarded"):
            return
        plural = self.PLURAL

        def handler(route, request):
            try:
                if request.method in ("PUT", "PATCH", "DELETE"):
                    path = request.url.split("?", 1)[0].rstrip("/")
                    if f"/o/c/{plural}/" in path:
                        eid = path.rsplit("/", 1)[-1]
                        ours = {rec[1] for rec in self._ident()["ids"].values()}
                        # A6 2026-10-04 (user-approved live singleton runs): one
                        # live id may be written by PUT / PATCH while its single
                        # test runs (allow_live_write / revoke_live_write).
                        # DELETE stays blocked on every protected id, always.
                        if request.method in ("PUT", "PATCH") and eid in self.__dict__.get("_a6_live_allow", ()):
                            return route.continue_()
                        if eid in self._protected() and eid not in ours:
                            from cms.pages.certificate_of_origin.fragment_form_mixin import log_leftover
                            log_leftover(f"GUARD BLOCKED {request.method} /o/c/{plural}/{eid} (pre-existing record)")
                            self.__dict__["_a4_blocked"] = eid
                            return route.abort()
            except Exception:  # noqa: BLE001 - the guard never breaks a request it cannot judge
                pass
            return route.continue_()

        self.page.route(f"**/o/c/{plural}/**", handler)
        self.__dict__["_a4_guarded"] = True

    def allow_live_write(self, live_id: str):
        """Exempt ONE approved live singleton id from the guard (PUT / PATCH
        only) for the duration of one test. Never touches _ident()["ids"], so
        teardown deletes can never resolve to the live record."""
        live_id = str(live_id)
        assert live_id in self.LIVE_IDS, f"{live_id} is not a live id of {self.SLUG}"
        self.__dict__["_a6_live_allow"] = {live_id}

    def revoke_live_write(self):
        self.__dict__["_a6_live_allow"] = set()

    def _open_manage(self, role, locale, form):
        _Po._open_manage(self, role, locale, form=False)
        self._install_guard()
        ids = self.page.evaluate(
            "() => [...document.querySelectorAll('[data-qc-oel-history],[data-qc-oel-delete],[data-qc-oel-unpublish],"
            "[data-qc-oel-view],[data-qc-oel-publish]')].map(e => e.getAttribute('data-qc-oel-history') || "
            "e.getAttribute('data-qc-oel-delete') || e.getAttribute('data-qc-oel-unpublish') || "
            "e.getAttribute('data-qc-oel-view') || e.getAttribute('data-qc-oel-publish'))")
        ours = {rec[1] for rec in self._ident()["ids"].values()}
        self._protected().update(i for i in ids if i and i not in ours)
        if form:
            self.page.locator(self.ADD_NEW_BUTTON).first.click()
            ready = self.page.locator(self.FORM_READY).first
            ready.wait_for(state="visible", timeout=35000)
            # condition: the create form re-renders after "+ Add New"; the
            # title input must read empty before anything is typed.
            spec = self.FIELDS.get(self.TITLE_FIELD)
            if spec is not None and spec.kind in ("text", "url"):
                box = self.page.get_by_role("textbox", name=self.label_pattern(spec.label)).first
                for _ in range(20):
                    if box.count() and box.input_value() == "":
                        break
                    self.page.wait_for_timeout(500)
                else:
                    raise RuntimeError(
                        f"{self.SLUG}: the form after '+ Add New' still holds {box.input_value()[:60]!r} - "
                        "refusing to type into what may be an existing record")
            # no entry id: the "Editing <title> (<state>)" banner of an existing
            # record must not be showing on the create form
            editing = [ln for ln in self.page.locator("body").inner_text().splitlines()
                       if ln.startswith("Editing ") and "(" in ln]
            if editing:
                raise RuntimeError(f"{self.SLUG}: the form is an existing record ({editing[0][:80]!r}) - refusing to fill")
        return self


# ---------------------------------------------------------------------------
# Submissions (webform records): reviewed by row actions, never authored
# ---------------------------------------------------------------------------
class SubmissionAdminPage:
    """A submissions object's entries list, as `role`. Rows are located by our
    own QCTEST company / applicant text only; a row that does not carry the
    QCTEST prefix is never acted on."""

    SLUG = ""
    PLURAL = ""
    SEARCH = 'input[placeholder^="Search entries"]'
    ROW = "table tbody tr"
    HEAD = "table thead th"

    def __init__(self, page):
        self.page = page

    # ---- session -------------------------------------------------------
    def sign_in(self, role: str):
        email, password = cms_role_credentials(role)
        if _lp._SESSION_OWNER.get(self.page) != email:
            ctx = self.page.context
            ctx.clear_cookies()
            for attempt in (0, 1):
                try:
                    _lp.CmsLoginPage(self.page).open_login().login(email, password)
                    break
                except Exception as exc:  # noqa: BLE001 - one settle-and-retry (ERR_ABORTED / slow login)
                    if attempt or ("ERR_ABORTED" not in str(exc) and "Timeout" not in str(exc)):
                        raise
                    self.page.wait_for_timeout(3000)
            _lp._SESSION_OWNER[self.page] = email
        return self

    def manage_url(self) -> str:
        return control_panel_url(f"/en/web/qatar-chamber/manage-{self.SLUG}")

    def open_list(self, role: str):
        self.sign_in(role)
        for attempt in (0, 1):
            try:
                self.page.goto(self.manage_url(), wait_until="domcontentloaded")
                break
            except Exception as exc:  # noqa: BLE001
                if attempt or "ERR_ABORTED" not in str(exc):
                    raise
                self.page.wait_for_timeout(2000)
        self.page.locator(self.HEAD).first.wait_for(state="attached", timeout=40000)
        return self

    # ---- rows ----------------------------------------------------------
    def find_row(self, needle: str, role: str, timeout_s: float = 60.0):
        """The single row holding `needle` (a QCTEST company name), searched and
        polled (a fresh public submission can take a moment to index)."""
        assert needle.startswith(DISPOSABLE_PREFIX), f"refusing to look up non-QCTEST row {needle!r}"
        deadline = time.monotonic() + timeout_s
        while True:
            self.open_list(role)
            box = self.page.locator(self.SEARCH).first
            # run 2026-10-04: for the Form Manager on the BCMR list the search
            # input exists but is hidden (no rows are served); only a visible
            # box is used, so an absent row is reported by the caller.
            if box.count() and box.is_visible():
                box.fill(needle)
                box.press("Enter")
            rows = self.page.locator(f'{self.ROW}:has-text("{needle}")')
            try:
                rows.first.wait_for(state="visible", timeout=8000)
                return rows.first
            except Exception:  # noqa: BLE001
                if time.monotonic() > deadline:
                    return None
                self.page.wait_for_timeout(4000)

    def headers(self) -> list[str]:
        return [" ".join(t.split()).upper() for t in self.page.locator(self.HEAD).all_inner_texts()]

    def cell(self, row, header: str) -> str:
        heads = self.headers()
        if header.upper() not in heads:
            return ""
        return " ".join(row.locator("td").nth(heads.index(header.upper())).inner_text().split())

    def request_status(self, needle: str, role: str) -> str:
        row = self.find_row(needle, role)
        return self.cell(row, "Request Status") if row is not None else ""

    def entry_id(self, row) -> str:
        for attr in ("data-qc-oel-view", "data-qc-oel-approve", "data-qc-oel-reject", "data-qc-oel-delete"):
            el = row.locator(f"[{attr}]")
            if el.count():
                return el.first.get_attribute(attr) or ""
        return ""

    def row_actions(self, row) -> list[str]:
        return row.evaluate(
            "r => [...r.querySelectorAll('[data-qc-oel-view],[data-qc-oel-approve],[data-qc-oel-reject],"
            "[data-qc-oel-delete],[data-qc-oel-unpublish]')].map(e => [...e.attributes]"
            ".filter(a => a.name.startsWith('data-qc-oel-') && a.name !== 'data-qc-oel-label')"
            ".map(a => a.name.slice(12)).join('/'))")

    def _act(self, needle: str, role: str, attr: str, answer: str | None) -> list[list[str]]:
        """Click our row's action and answer every native dialog it raises:
        confirm -> accept, prompt -> `answer` (None = dismiss), alert -> accept.
        Returns the dialogs seen [(type, message)]."""
        row = self.find_row(needle, role)
        assert row is not None, f"QCTEST submission {needle!r} is not in the {self.SLUG} list for {role}"
        ctl = row.locator(f"[data-qc-oel-{attr}]")
        assert ctl.count(), f"{role} is offered no {attr!r} action on {needle!r} (actions {self.row_actions(row)})"
        seen: list[list[str]] = []

        def on_dialog(d):
            seen.append([d.type, " ".join(d.message.split())[:200]])
            if d.type == "prompt":
                d.accept(answer) if answer is not None else d.dismiss()
            else:
                d.accept()

        self.page.on("dialog", on_dialog)
        try:
            ctl.first.click(force=True)
            # condition: the dialogs run synchronously from the click; the row
            # then re-renders. Upper bound 8 s (measured live: ~2 s).
            self.page.wait_for_timeout(1500)
            try:
                self.page.wait_for_load_state("networkidle", timeout=8000)
            except Exception:  # noqa: BLE001
                pass
        finally:
            self.page.remove_listener("dialog", on_dialog)
        return seen

    def approve(self, needle: str, role: str = ROLE_FORM_MANAGER):
        return self._act(needle, role, "approve", None)

    def reject(self, needle: str, reason: str | None, role: str = ROLE_FORM_MANAGER):
        return self._act(needle, role, "reject", reason)

    def view_text(self, needle: str, role: str = ROLE_FORM_MANAGER) -> str:
        """Text of the record's View dialog (read-only detail)."""
        row = self.find_row(needle, role)
        assert row is not None, f"QCTEST submission {needle!r} is not in the {self.SLUG} list for {role}"
        v = row.locator("[data-qc-oel-view]")
        (v.first if v.count() else row.get_by_text("View", exact=True).first).click(force=True)
        dlg = self.page.locator("[role=dialog]:visible, .modal.show, dialog[open]").last
        dlg.wait_for(state="visible", timeout=15000)
        return " ".join(dlg.inner_text().split())

    def view_has_editable_inputs(self) -> int:
        return self.page.locator(
            "[role=dialog]:visible input:not([type=hidden]):not([readonly]):not([disabled]), "
            "[role=dialog]:visible textarea:not([readonly]):not([disabled]), [role=dialog]:visible select:not([disabled])"
        ).count()

    def visible_row_count(self) -> int:
        return self.page.locator(self.ROW).filter(has=self.page.locator("td")).count()

    def status_filter_options(self) -> list[str]:
        return [" ".join(o.split()) for o in self.page.locator("select[data-qc-oel-status-filter] option").all_inner_texts()]

    def delete_qctest(self, needle: str, role: str) -> bool:
        """Delete OUR QCTEST submission by its row ID, when the role is offered
        Delete. Never raises; returns False when no Delete control exists."""
        try:
            if not needle.startswith(DISPOSABLE_PREFIX):
                return False
            row = self.find_row(needle, role, timeout_s=10)
            if row is None:
                return True
            eid = self.entry_id(row)
            link = row.locator(f'[data-qc-oel-delete="{eid}"]') if eid else row.locator("[data-qc-oel-delete]")
            if not link.count():
                return False
            self.page.once("dialog", lambda d: d.accept())
            link.first.click(force=True)
            self.page.wait_for_timeout(3000)
            return self.find_row(needle, role, timeout_s=5) is None
        except Exception:  # noqa: BLE001 - teardown never masks the result
            return False


def run_tag() -> str:
    return time.strftime("%m%d%H%M%S")


_WS = re.compile(r"\s+")


def squash(text: str) -> str:
    return _WS.sub(" ", text or "").strip()

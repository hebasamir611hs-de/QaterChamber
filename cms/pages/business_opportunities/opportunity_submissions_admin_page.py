"""
cms/pages/business_opportunities/opportunity_submissions_admin_page.py —
review side of PBI 130697 (Business Opportunities): Opportunity Submissions,
Opportunity Inquiries, and the two public forms that create them.

Core owner: Agent B. Other agents add helpers only in a `# --- <AGENT> ---`
section at the end of this file.

CONFIRMED LIVE 2026-10-07 (qcdev, CLI recon as Site Content Editor 156488 and
TEST_USER 20132):

  - `manage-opportunity-submission` and `manage-opportunity-inquiry` are
    "(view only)" objects in Object Authoring: no form, no Save/Submit button,
    and "0 total" entries for both accounts. A view-only object's rows offer
    only `data-qc-oel-view` and `data-qc-oel-unpublish` (seen on Event
    Registration, 37 rows) — no approve / reject / status / rejection-reason
    control exists on this surface.
  - Liferay's native Content & Data view of the same objects (definitions
    120183 OpportunitySubmission, 120047 OpportunityInquiry, panel link
    "Content & Data") opens for TEST_USER only. Its add form carries
    "Submission Status" + "Rejection Reason" (submission) and "Status"
    (inquiry) as plain fields; there are no Approve / Reject buttons. The
    Site Content Editor gets "You do not have the roles required to access
    this portlet." and has no product menu at all.
  - Form Manager (156500, the cases' "QC Admin Reviewer" per the user,
    2026-10-07) sees the same two "(view only)" lists (0 entries), no product
    menu, and "You do not have the roles required to access this portlet." on
    the native view. On a view-only object with rows (Event Registration) its
    only row action is `data-qc-oel-view`: a read-only field modal (no edit,
    no status, no approve/reject).
  - Object definition: validation "Rejection reason required when rejected";
    no object actions (notifications) defined; picklists
    submissionStatus = pending / approved / rejected,
    inquiryStatus = pending / inProgress / completed / closed.
  - Public intake: POST /o/qc-business-opportunities-api/submissions and
    /inquiries answer HTTP 500 (the forms show "Something went wrong. Nothing
    was saved. Please review your entries and try again." and "Something went
    wrong and your inquiry was not sent. Please try again."). reCAPTCHA is
    switched off on qcdev (/o/qc-recaptcha-api/config: enabled=false), so the
    forms are submitted normally — nothing is bypassed.

RE-CONFIRMED LIVE 2026-10-12 (Agent H re-run, CLI recon as Form Manager,
Site Content Editor and TEST_USER):

  - Public intake now WORKS: POST /submissions and /inquiries answer HTTP 200
    (success screen + reference QC-BO-SUB-<date>-<code> / QC-BO-INQ-<date>-
    <code>). A submission lands in manage-opportunity-submission, an inquiry in
    manage-opportunity-inquiry (nothing crosses over).
  - Both lists are still "(view only)". Columns: ENTRY (the entry's ERC UUID,
    not a name) / STATUS (the workflow status, "PUBLISHED" on arrival) / LAST
    MODIFIED / ACTIONS. The business Submission Status / Inquiry Status
    ("Pending") is visible only inside the View modal.
  - Row actions: Form Manager = View (+ Preview on submissions, which opens an
    empty public submit form); Editor = View, Unpublish (+ Preview);
    TEST_USER = View, Unpublish, Delete (+ Preview). The View modal is a
    read-only field list with only a close button: no Approve / Reject /
    Rejection Reason input / status control, no History.
  - Native Content & Data: still denied to the Form Manager; TEST_USER lists
    the rows there.

The only state-changing control this module drives is `guarded_delete()`, as
TEST_USER, on a row this run created and verified by exact name + entry id +
ERC immediately before the click. The public-form drivers only ever type
QCTEST-130697-H- values.
"""

from __future__ import annotations

import os as _os
import re as _re
from pathlib import Path as _Path

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials, control_panel_url, settings, web_url
from core.web.base_page import BasePage

_PROJECT_ROOT = _Path(__file__).resolve().parents[3]

QCTEST_PREFIX = "QCTEST-R32-N-"  # ready-bug retest agent N (2026-10-14)
QCTEST_B_PREFIX = QCTEST_PREFIX  # backward-compatible alias
SUBMISSION_SLUG = "opportunity-submission"
INQUIRY_SLUG = "opportunity-inquiry"
OBJECT_LABELS = {SUBMISSION_SLUG: "Opportunity Submission", INQUIRY_SLUG: "Opportunity Inquiry"}

ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
# User decision 2026-10-07: the Form Manager is the cases' "QC Admin Reviewer" (only role
# meant to open/edit submissions); TEST_USER is the cases' "Administrator".
ROLE_FORM_MANAGER = "Form Manager"
ROLE_ADMIN = "Administrator (TEST_USER)"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492", "Content Contributor": "156496",
                 ROLE_FORM_MANAGER: "156500", ROLE_ADMIN: "20132"}
BIZOPP_RECORD_SLUG = "business-opportunity"

# Liferay native object-entries portlets (Content & Data panel link), read live.
NATIVE_ENTRIES_PATH = {
    SUBMISSION_SLUG: (
        "/en/group/qatar-chamber/~/control_panel/manage?p_p_id="
        "com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_Z1M9"
        "&p_p_lifecycle=0&p_p_state=maximized&p_v_l_s_g_id=37246"
        "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_Z1M9_objectDefinitionId=120183"
    ),
    INQUIRY_SLUG: (
        "/en/group/qatar-chamber/~/control_panel/manage?p_p_id="
        "com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_N0N0"
        "&p_p_lifecycle=0&p_p_state=maximized&p_v_l_s_g_id=37246"
        "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_N0N0_objectDefinitionId=120047"
    ),
}
NATIVE_DENIED_TEXT = "You do not have the roles required to access this portlet."
AUTH_FAILED_TEXT = "Authentication failed"

# Row-level workflow / review attributes a review control would carry.
REVIEW_ROW_ATTRS = ("approve", "reject", "resubmit", "publish", "return", "schedule")
REVIEW_BUTTON_NAMES = ("Approve", "Reject", "Publish as Opportunity", "Save", "Update Status")
REVIEW_FIELD_LABELS = ("Rejection Reason", "Submission Status", "Status")

# Public-form messages (exact, read live 2026-10-07).
MSG_SUBMISSION_FAILED = "Something went wrong. Nothing was saved. Please review your entries and try again."
MSG_INQUIRY_FAILED = "Something went wrong and your inquiry was not sent. Please try again."
INTAKE_API = "/o/qc-business-opportunities-api/"


def _evidence_dir() -> str:
    return _os.path.join(str(_PROJECT_ROOT), "reports", "evidence", "ready32", "N")


class OpportunityReviewAdminPage(ObjectAuthoringPage):
    """Read-only driver of the Opportunity Submission / Inquiry staff surfaces."""

    LIST_HEADING = "h2, h3, .qc-oel__title"
    PAGE_SIZE_SELECT = "select[data-qc-oel-page-size]"
    ENTRY_COUNT = "[data-qc-oel-count]"
    NAV_LINKS = "a[href*='/manage-']"

    def __init__(self, page, slug: str = SUBMISSION_SLUG):
        super().__init__(page, slug)

    # ---- session -------------------------------------------------------------
    def login_as_role(self, role: str) -> str:
        """Real login in this (auth-free) context: "ok" / "auth_failed" / "unknown"."""
        if role == ROLE_ADMIN:
            email, password = settings.test_user, settings.test_password
        else:
            email, password = cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        try:
            login.login(email, password)
            return "ok"
        except Exception:  # noqa: BLE001 — classified below
            try:
                self.page.wait_for_load_state("load")
                self.open(control_panel_url("/en/home"))
                if self.signed_in_user()[0]:
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            return "auth_failed" if AUTH_FAILED_TEXT in self.body_text() else "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']"""
        )
        return info[0], info[1]

    def body_text(self) -> str:
        try:
            return self.page.locator("body").inner_text()
        except Exception:  # noqa: BLE001
            return ""

    # ---- Object Authoring manage page ----------------------------------------
    def open_manage(self, slug: str | None = None) -> int | None:
        """Opens manage-<slug> (EN); returns the HTTP status of the navigation."""
        if slug:
            self.slug = slug
        response = self.page.goto(control_panel_url(f"/web/qatar-chamber/manage-{self.slug}"),
                                  wait_until="load", timeout=90000)
        try:
            self.page.get_by_text(f"{OBJECT_LABELS.get(self.slug, '')} entries").first.wait_for(timeout=30000)
        except Exception:  # noqa: BLE001 — a denied page has no list heading
            pass
        self._wait_list_rendered()  # the page-size select is re-rendered with the configured list
        select = self.page.locator(self.PAGE_SIZE_SELECT)
        if select.count() and select.first.is_visible() and select.first.input_value() != "0":
            select.first.select_option("0")
            # Healed 2026-10-13 (ready30 C): the list page now keeps a request open, so
            # "networkidle" can time out; fall back to the re-rendered table.
            try:
                self.page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:  # noqa: BLE001
                pass
        self._wait_list_rendered()
        return response.status if response else None

    def _wait_list_rendered(self) -> None:
        """Healed 2026-10-13 (ready30 C): the list first paints a generic table
        (Entry / Status / Last modified / Actions, no rows) and then the configured
        columns + rows; wait for the configured render (a row action or "0 total")."""
        try:
            self.page.wait_for_function(
                "() => document.querySelector('table tbody tr [data-qc-oel-view]') || /\\b0 total/.test(document.body.innerText)",
                timeout=30000)
        except Exception:  # noqa: BLE001 — denied pages have neither
            pass

    def list_heading_visible(self) -> bool:
        return self.page.get_by_text(f"{OBJECT_LABELS.get(self.slug, '')} entries").count() > 0

    def total_entries(self) -> int | None:
        match = _re.search(r"(\d+)\s*total", self.body_text())
        return int(match.group(1)) if match else None

    def list_rows(self) -> list[dict]:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('table tbody tr')].map(r => ({
                text: r.innerText.replace(/\\s+/g, ' ').trim(),
                actions: [...r.querySelectorAll('*')].flatMap(n => [...n.attributes]
                    .filter(a => a.name.startsWith('data-qc-oel-') && a.name !== 'data-qc-oel-label')
                    .map(a => a.name.replace('data-qc-oel-', '')))
            }))"""
        )

    def nav_entry(self, label: str) -> dict:
        """The Object Authoring left-nav entry for `label`: present? view only?"""
        return self.page.evaluate(
            """(label) => {
                const links = [...document.querySelectorAll('a')].filter(a => a.innerText.trim() === label);
                if (!links.length) return {present: false, view_only: false};
                const a = links[0];
                const around = (a.parentElement ? a.parentElement.innerText : a.innerText) + ' ' +
                               (a.nextElementSibling ? a.nextElementSibling.innerText : '') + ' ' +
                               (a.parentElement && a.parentElement.nextElementSibling ? a.parentElement.nextElementSibling.innerText : '');
                return {present: true, view_only: /view only/i.test(around)};
            }""",
            label,
        )

    def review_controls(self) -> dict:
        """Every review control the page offers (empty lists = none)."""
        rows = self.list_rows()
        row_actions = sorted({a for r in rows for a in r["actions"] if a in REVIEW_ROW_ATTRS})
        buttons = [n for n in REVIEW_BUTTON_NAMES
                   if self.page.get_by_role("button", name=n, exact=True).count() > 0]
        fields = [f for f in REVIEW_FIELD_LABELS if self.page.get_by_label(f, exact=True).count() > 0]
        forms = self.page.locator("form:has([name^='ObjectField_'])").count()
        return {"row_actions": row_actions, "buttons": buttons, "fields": fields, "authoring_forms": forms,
                "rows": len(rows)}

    def authoring_access(self) -> dict:
        """Read-only: on manage-business-opportunity, the form buttons and the row
        actions this account is offered (nothing is clicked)."""
        self.open_manage(BIZOPP_RECORD_SLUG)
        rows = self.list_rows()
        return {
            "form_buttons": [n for n in ("Save as Draft", "Publish", "Submit for Review")
                             if self.page.get_by_role("button", name=n, exact=True).count() > 0],
            "row_actions": sorted({a for r in rows for a in r["actions"]}),
            "rows": len(rows),
        }

    # ---- Liferay native Content & Data view ----------------------------------
    def open_native_entries(self, slug: str) -> str:
        """"denied" / "list" / "other" for the native object-entries portlet."""
        self.page.goto(control_panel_url(NATIVE_ENTRIES_PATH[slug]), wait_until="load", timeout=90000)
        self.page.wait_for_load_state("networkidle")
        body = self.body_text()
        if NATIVE_DENIED_TEXT in body:
            return "denied"
        if self.page.get_by_text("Add Opportunity", exact=False).count() or self.page.get_by_role("button", name="New").count():
            return "list (can add / edit)"
        if "No Results Found" in body or self.page.locator("table tbody tr").count():
            return "list"
        return "other"

    def has_product_menu_link(self, text: str) -> bool:
        self.open(control_panel_url("/en/home"))
        toggle = self.page.locator('[data-qa-id="productMenu"]')
        if toggle.count() == 0:
            return False
        toggle.first.click()
        return self.page.get_by_role("link", name=text).count() > 0

    # ---- rows / View modal (read-only) -----------------------------------------
    def entry_ids(self) -> list[str]:
        """Entry ids of the rows on the open list (from each row's View action)."""
        return self.page.evaluate(
            "() => [...document.querySelectorAll('table tbody tr [data-qc-oel-view]')]"
            ".map(a => a.getAttribute('data-qc-oel-view'))")

    def row_by_id(self, entry_id: str) -> dict | None:
        for row in self.page.evaluate(
            """() => [...document.querySelectorAll('table tbody tr')].map(r => ({
                id: (r.querySelector('[data-qc-oel-view]') || {getAttribute: () => ''}).getAttribute('data-qc-oel-view'),
                cells: [...r.querySelectorAll('td')].map(td => td.innerText.replace(/\\s+/g, ' ').trim()),
                actions: [...r.querySelectorAll('a, button')].map(a => (a.innerText || '').trim()).filter(t => t)
            }))"""
        ):
            if row["id"] == str(entry_id):
                return row
        return None

    def list_headers(self) -> list[str]:
        return [h.strip() for h in self.page.locator("table thead th").all_inner_texts()]

    def view_entry(self, entry_id: str) -> dict:
        """Opens the row's View modal (read-only) and returns its field lines and
        every interactive control inside it; the list is reloaded afterwards."""
        before = set(self.body_text().splitlines())
        self.page.locator(f"[data-qc-oel-view='{entry_id}']").first.click()
        self.page.wait_for_timeout(3000)
        lines = [line for line in self.body_text().splitlines() if line.strip() and line not in before]
        controls = self.page.evaluate(
            """() => {
                const d = document.querySelector('[role=dialog], dialog[open], .modal.show') || document.body;
                const vis = e => !!e.offsetParent;
                return {
                  buttons: [...d.querySelectorAll('button')].filter(vis)
                      .map(b => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(t => t && t.length > 1),
                  inputs: [...d.querySelectorAll('input:not([type=hidden]), select, textarea')].filter(vis)
                      .filter(i => !i.disabled && !i.readOnly).map(i => i.tagName + ':' + (i.name || i.id))
                };
            }""")
        fields: dict[str, str] = {}
        for i, line in enumerate(lines[:-1]):
            nxt = lines[i + 1]
            if line in ("Submission Status", "Inquiry Status", "Rejection Reason", "Reference Number", "Id",
                        "External Reference Code", "Project Opportunity Name", "Your Name", "Company",
                        "Opportunity Inquiries ERC", "Creator"):
                fields.setdefault(line, nxt)
        # Healed 2026-10-13 (ready30 C): the line diff above drops values that also appear
        # elsewhere on the page (the new status filter lists "Pending"/"Approved"), so the
        # modal's own <dt>/<dd> pairs win for the plain (single-value) fields.
        pairs = self.page.evaluate(
            """() => { const dl = document.querySelector('[data-qc-oel-viewer-body]'); if (!dl) return [];
                return [...dl.querySelectorAll('dt')].map(dt => [dt.innerText.trim(),
                    (dt.nextElementSibling ? dt.nextElementSibling.innerText.trim() : '')]); }""")
        for label, value in pairs:
            if label in ("Submission Status", "Inquiry Status", "Creator", "Id") and value and "\n" not in value:
                fields[label] = value
        return {"lines": lines, "fields": fields, "controls": controls}

    def entry_name(self, view: dict) -> str:
        """The EN name line of a View modal (submission or inquiry)."""
        lines = view["lines"]
        for label in ("Project Opportunity Name", "Your Name"):
            if label in lines:
                idx = lines.index(label)
                for line in lines[idx + 1: idx + 3]:
                    if line.startswith("en_US: "):
                        return line[len("en_US: "):]
        return ""

    # ---- guarded delete (TEST_USER only, own QCTEST rows only) ----------------
    def guarded_delete(self, slug: str, entry_id: str, expected_name: str) -> str:
        """Deletes ONE entry this run created: verifies on the open list that the
        row's View shows exactly `expected_name` (QCTEST prefix) and its ERC
        equals the row's delete label, then accepts the native confirm only if
        it names that ERC. Returns "deleted" or the exact reason it refused."""
        if not expected_name.startswith(QCTEST_PREFIX):
            return f"refused: {expected_name!r} is not a {QCTEST_PREFIX} value"
        self.open_manage(slug)
        view = self.view_entry(entry_id)
        name, erc = self.entry_name(view), view["fields"].get("External Reference Code", "")
        if name != expected_name or view["fields"].get("Id") != str(entry_id):
            return f"refused: entry {entry_id} shows name {name!r} / id {view['fields'].get('Id')!r}"
        self.open_manage(slug)
        link = self.page.locator(f"[data-qc-oel-delete='{entry_id}']")
        if link.count() != 1 or link.first.get_attribute("data-qc-oel-label") != erc:
            return f"refused: delete link for {entry_id} missing or not labelled {erc!r}"
        seen: dict = {}

        def _on_dialog(dialog):
            seen["message"] = dialog.message
            if erc and erc in dialog.message:
                dialog.accept()
            else:
                dialog.dismiss()

        self.page.once("dialog", _on_dialog)
        link.first.click(force=True)
        self.page.wait_for_timeout(4000)
        if not (erc and erc in seen.get("message", "")):
            return f"refused: confirm text {seen.get('message')!r} does not name {erc!r}"
        for _ in range(4):  # the submission delete (with attachments) can take a few seconds to settle
            self.open_manage(slug)
            if str(entry_id) not in self.entry_ids():
                return "deleted"
            self.page.wait_for_timeout(5000)
        return f"still listed after confirm {seen['message']!r}"

    # ---- review actions (ready30 C, 2026-10-13: built by the fix for bug 149526) ----
    # Read live 2026-10-13 on qcdev. Row actions carry data-qc-oel-<attr>="<entryId>":
    #   submission  Pending  -> Approve (confirm 'Approve: "<ERC>"?'), Reject (prompt
    #               'Reject "<ERC>". Enter the reason (required):'; empty -> alert
    #               "A rejection reason is required."), History.
    #               Approved -> Reject, History; Rejected -> Approve, History.
    #   inquiry     Pending -> "Mark In Progress" (data-qc-oel-approve, confirm);
    #               In-progress -> "Mark Completed" / "Close".
    # Success shows "Success:The opportunity submission has been approved./rejected."
    # History expands inline (.qc-oel__history) from GET /o/qc-object-status/review-history/<id>.
    SUCCESS_NOTICE = "[role=alert], .alert, .qc-oel__msg, .qc-oel__notice, .qc-oel__toast"
    HISTORY_CELL = ".qc-oel__history"

    def row_action_link(self, entry_id: str, title: str):
        """The row action <a> of `entry_id` whose visible label is exactly `title`."""
        return self.page.locator(f"table tbody tr:has([data-qc-oel-view='{entry_id}']) td.qc-oel__cell-action a",
                                 has_text=_re.compile(rf"^\s*{_re.escape(title)}\s*$"))

    def review_action(self, slug: str, entry_id: str, title: str, expected_name: str,
                      reason: str | None = None, settle_ms: int = 30000) -> dict:
        """Clicks ONE review action on OUR QCTEST row (row must show `expected_name`,
        which must carry QCTEST_PREFIX). Native confirm is accepted only if it names
        the row's ERC; a prompt gets `reason` (or is dismissed when reason is None).
        Returns dialogs, success notices, the PATCH status and the row after reload."""
        if not expected_name.startswith(QCTEST_PREFIX):
            raise ValueError(f"{expected_name!r} is not a {QCTEST_PREFIX} value")
        row = self.wait_for_entry(slug, entry_id)
        if not row or expected_name not in " ".join(row["cells"]):
            raise AssertionError(f"refused: row {entry_id} does not show {expected_name!r}: {row}")
        erc = row["cells"][0]
        link = self.row_action_link(entry_id, title)
        if link.count() != 1:
            return {"offered": False, "actions": row["actions"], "dialogs": [], "notices": [], "row": row}
        dialogs: list[str] = []
        writes: list[dict] = []

        def _on_dialog(dialog):
            dialogs.append(f"{dialog.type}: {dialog.message}")
            if dialog.type == "prompt":
                dialog.accept(reason) if reason is not None else dialog.dismiss()
            elif dialog.type == "confirm":
                dialog.accept() if erc in dialog.message else dialog.dismiss()
            else:
                dialog.accept()

        def _on_response(resp):
            if resp.request.method in ("PATCH", "PUT", "POST") and str(entry_id) in resp.url:
                writes.append({"method": resp.request.method, "url": resp.url, "status": resp.status})

        self.page.on("dialog", _on_dialog)
        self.page.on("response", _on_response)
        try:
            link.first.click()
            notices: list[str] = []
            # Healed 2026-10-14 (ready32 N): the success toast now shows only briefly before the
            # list reloads (shared list fragment change), so poll every 100 ms, not 500 ms.
            for _ in range(settle_ms // 100):
                self.page.wait_for_timeout(100)
                try:  # the list reloads itself after the action (context may be destroyed mid-read)
                    notices = [t.strip() for t in self.page.locator(self.SUCCESS_NOTICE).all_inner_texts() if t.strip()]
                except Exception:  # noqa: BLE001
                    notices = []
                if notices or any(d.startswith("alert") for d in dialogs):
                    break
        finally:
            self.page.remove_listener("dialog", _on_dialog)
            self.page.remove_listener("response", _on_response)
        self.open_manage(slug)
        return {"offered": True, "dialogs": dialogs, "notices": sorted(set(notices)), "writes": writes,
                "row": self.row_by_id(entry_id)}

    def publish_as_opportunity(self, entry_id: str, expected_name: str, tries: int = 2) -> dict:
        """Added 2026-10-14 (ready32 N, bug 150023): Editor/Administrator row action
        "Publish as Opportunity" on OUR Approved QCTEST submission. Confirm accepted only
        if it names the row's ERC. Returns the landing URL, the POST status and the
        Opportunity Title value of the opened Business Opportunity form (a Draft)."""
        if not expected_name.startswith(QCTEST_PREFIX):
            raise ValueError(f"{expected_name!r} is not a {QCTEST_PREFIX} value")
        out: dict = {"dialogs": [], "posts": [], "url": "", "title_value": "", "body": ""}
        for _ in range(tries):  # one retry: a transient "Failed to fetch" was seen on qcdev
            row = self.wait_for_entry(SUBMISSION_SLUG, entry_id)
            if not row or expected_name not in " ".join(row["cells"]):
                raise AssertionError(f"refused: row {entry_id} does not show {expected_name!r}: {row}")
            erc = row["cells"][0]
            link = self.row_action_link(entry_id, "Publish as Opportunity")
            if link.count() != 1:
                out["actions"] = row["actions"]
                return out

            def _on_dialog(dialog):
                out["dialogs"].append(f"{dialog.type}: {dialog.message}")
                if dialog.type == "confirm":
                    dialog.accept() if erc in dialog.message else dialog.dismiss()
                else:
                    dialog.accept()

            def _on_response(resp):
                if resp.request.method == "POST" and "publish-as-opportunity" in resp.url:
                    out["posts"].append(resp.status)

            self.page.on("dialog", _on_dialog)
            self.page.on("response", _on_response)
            try:
                link.first.click()
                try:
                    self.page.wait_for_url(_re.compile(r"manage-business-opportunity\?editEntry="), timeout=60000)
                except Exception:  # noqa: BLE001 — reported through url
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
                self.page.remove_listener("response", _on_response)
            out["url"] = self.page.url
            if "editEntry=" in out["url"]:
                break
        if "editEntry=" in out["url"]:
            # The Opportunity Title input is not label-associated: read the form's text inputs.
            try:
                self.page.wait_for_function(
                    "(n) => [...document.querySelectorAll('form input[type=text], form input:not([type])')]"
                    ".some(i => i.value === n)", arg=expected_name, timeout=45000)
                out["title_value"] = expected_name
            except Exception:  # noqa: BLE001 — reported as not pre-filled
                pass
            out["body"] = self.body_text()[:4000]
        return out

    def wait_for_entry(self, slug: str, entry_id: str, tries: int = 8) -> dict | None:
        """Re-opens the list until `entry_id` is listed (a fresh public submission can
        take a few seconds to reach the list); returns its row or None."""
        for _ in range(tries):
            self.open_manage(slug)
            row = self.row_by_id(entry_id)
            if row:
                return row
            self.page.wait_for_timeout(5000)
        return None

    @staticmethod
    def row_status(row: dict | None) -> str:
        """Status cell of a review row (submission col 5, inquiry col 6 — found by value)."""
        cells = (row or {}).get("cells", [])
        for c in cells:
            if c.upper() in ("PENDING", "APPROVED", "REJECTED", "IN-PROGRESS", "COMPLETED", "CLOSED"):
                return c.upper()
        return ""

    def history_text(self, slug: str, entry_id: str) -> str:
        """Opens the row's History (inline expansion) and returns its visible text."""
        self.open_manage(slug)
        self.page.locator(f"[data-qc-oel-history='{entry_id}']").first.click()
        cell = self.page.locator(f"{self.HISTORY_CELL}:visible").first
        try:
            cell.locator(".qc-oel__history-who").first.wait_for(timeout=20000)
        except Exception:  # noqa: BLE001 — empty history returned as ""
            return ""
        return cell.inner_text()

    def opportunity_record_titles(self) -> str:
        """Read-only: body text of manage-business-opportunity (all rows)."""
        self.open_manage(BIZOPP_RECORD_SLUG)
        return self.body_text()

    # ---- evidence --------------------------------------------------------------
    def evidence(self, name: str) -> str:
        _os.makedirs(_evidence_dir(), exist_ok=True)
        path = _os.path.join(_evidence_dir(), _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        png = self.page.screenshot(path=path, full_page=True)
        try:
            import allure  # noqa: PLC0415
            allure.attach(png, name=name, attachment_type=allure.attachment_type.PNG)
        except Exception:  # noqa: BLE001 — evidence only
            pass
        return path


class _PublicIntakeForm(BasePage):
    """Shared intake mechanics: one POST to the BO module, outcome captured."""

    def _submit_and_capture(self, click_selector: str, endpoint: str, timeout_ms: int = 60000) -> int | None:
        with self.page.expect_response(
            lambda r: INTAKE_API + endpoint in r.url and r.request.method == "POST", timeout=timeout_ms
        ) as info:
            self.page.locator(click_selector).click()
        self.last_body = {}
        try:
            self.last_body = info.value.json()
        except Exception:  # noqa: BLE001 — body not always retrievable after the form re-renders
            pass
        return info.value.status


class PublicOpportunitySubmissionForm(_PublicIntakeForm):
    """The public "Submit a Business Opportunity" webform (locators read live 2026-10-07)."""

    PATH = "/web/qatar-chamber/submit-business-opportunity"
    SUBMIT = "button.qc-bos__submit"
    DONE = "div.qc-bos__done"
    STATUS = "div.qc-bos__status"
    REFERENCE = "strong.qc-bos__ref-inline, [data-qc-bos-ref]"

    def open_form(self) -> "PublicOpportunitySubmissionForm":
        self.open(web_url(self.PATH))
        self.page.locator(self.SUBMIT).wait_for(state="visible", timeout=60000)
        # Select options come from GET <apiBase>/lookups; wait until Sector is populated.
        self.page.wait_for_function(
            "() => document.querySelector('#qc-bos-sector') && document.querySelector('#qc-bos-sector').options.length > 1",
            timeout=30000)
        return self

    def fill_qctest(self, name: str, image: str, pdf: str, email: str) -> "PublicOpportunitySubmissionForm":
        if not name.startswith(QCTEST_B_PREFIX):
            raise ValueError(f"{name!r} is not a {QCTEST_B_PREFIX} value")
        p = self.page
        p.locator("#qc-bos-projectOpportunityName").fill(name)
        p.locator("#qc-bos-projectOpportunityNameAr").fill(name + " AR")
        p.select_option("#qc-bos-sector", "energy")
        self._select_or_text("country", "Qatar")
        p.locator("#qc-bos-companyOrganizationName").fill(f"{QCTEST_B_PREFIX}Company")
        p.locator("#qc-bos-investmentBrief").fill("QCTEST investment brief (EN).")
        p.locator("#qc-bos-investmentBriefAr").fill("QCTEST investment brief (AR).")
        p.locator("#qc-bos-keyHighlights").fill("QCTEST key highlights.")
        p.locator("#qc-bos-investmentAmount").fill("5000000")
        self._select_or_text("currency", "QAR")
        p.select_option("#qc-bos-investmentType", "jointVenture")
        p.select_option("#qc-bos-timeline", "sixToTwelveMonths")
        p.select_option("#qc-bos-riskProfile", "medium")
        p.select_option("#qc-bos-industryPool", "energy")
        for field in ("bannerImage", "opportunityLogo", "galleryImages"):
            p.set_input_files(f"#qc-bos-{field}", image)
        p.set_input_files("#qc-bos-supportingDocuments", pdf)
        p.locator("#qc-bos-contactInformation").fill(f"{QCTEST_B_PREFIX}Contact")
        p.locator("#qc-bos-contactEmail").fill(email)
        p.locator("#qc-bos-mobileNumber").fill("55123456")
        p.locator("#qc-bos-privacyPolicyConsent").check()
        return self

    def _select_or_text(self, key: str, value: str) -> None:
        """Country / Currency render a text input when their lookup list is empty (live)."""
        select = self.page.locator(f"#qc-bos-{key}")
        if select.is_visible() and select.locator("option").count() > 1:
            select.select_option(label=value)
        else:
            self.page.locator(f"#qc-bos-{key}-text").fill(value)

    def submit(self) -> dict:
        status = self._submit_and_capture(self.SUBMIT, "submissions")
        try:
            self.page.locator(f"{self.DONE}:visible, {self.STATUS}:visible").first.wait_for(timeout=30000)
        except Exception:  # noqa: BLE001 — outcome read below
            pass
        done = self.page.locator(self.DONE).is_visible()
        ref = ""
        if done and self.page.locator(self.REFERENCE).count():
            ref = self.page.locator(self.REFERENCE).first.inner_text().strip()
        message = self.page.locator(self.STATUS).inner_text().strip() if self.page.locator(self.STATUS).count() else ""
        if done and not ref:
            match = _re.search(r"QC-BO-SUB-[\w-]+", self.page.locator(self.DONE).inner_text())
            ref = match.group(0).rstrip(".") if match else ""
        body = getattr(self, "last_body", {}) or {}
        return {"http": status, "success": done, "reference": ref, "message": message, "id": str(body.get("id", ""))}


class PublicOpportunityInquiryForm(_PublicIntakeForm):
    """The "Submit an inquiry" modal on a public opportunity detail page (read live 2026-10-07)."""

    DETAIL_PATH = "/web/qatar-chamber/business-opportunity?opportunity={code}"
    CTA = "button.qc-bod-cta"
    SUBMIT = "button.qc-bod-form-submit"
    FORM_ERROR = "[data-qc-bod-form-error]"
    DONE_CLOSE = "button.qc-bod-done-close"

    def open_modal(self, opportunity_code: str) -> "PublicOpportunityInquiryForm":
        self.open(web_url(self.DETAIL_PATH.format(code=opportunity_code)))
        self.page.locator(self.CTA).first.click()
        self.page.locator("input[name=yourName]").wait_for(state="visible", timeout=30000)
        return self

    def fill_qctest(self, name: str, email: str, company: str, message: str) -> "PublicOpportunityInquiryForm":
        if not (name.startswith(QCTEST_B_PREFIX) and company.startswith(QCTEST_B_PREFIX)):
            raise ValueError(f"inquiry name and company must carry the {QCTEST_PREFIX} prefix")
        p = self.page
        p.locator("input[name=yourName]").fill(name)
        p.locator("input[name=emailAddress]").fill(email)
        p.locator("input[name=mobileNumber]").fill("55123456")
        p.locator("input[name=company]").fill(company)
        p.select_option("select[name=inquiryType]", "generalInterest")
        p.locator("textarea[name=message]").fill(message)
        return self

    def submit(self) -> dict:
        status = self._submit_and_capture(self.SUBMIT, "inquiries")
        try:
            self.page.locator(f"{self.FORM_ERROR}:visible, {self.DONE_CLOSE}:visible").first.wait_for(timeout=30000)
        except Exception:  # noqa: BLE001
            pass
        error = self.page.locator(self.FORM_ERROR)
        message = error.inner_text().strip() if error.count() and error.is_visible() else ""
        body = getattr(self, "last_body", {}) or {}
        return {"http": status, "success": self.page.locator(self.DONE_CLOSE).is_visible(), "message": message,
                "id": str(body.get("id", "")), "reference": body.get("referenceNumber", "")}

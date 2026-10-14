"""
cms/tests/gm_message/gm_message_singleton.py -- the module-level baseline for
PBI 129397's live singleton, GM Message 79878
(`QCDEMO-129397-general-managers-message`). See cms/tests/singleton_baseline.py
for the contract: captured once at module start, restored once at module end,
`tools/restore_singleton.py --pbi 129397` after a killed run.

Account: the TEST_USER admin session (the account the per-test restores used).

Status moves go through singleton_baseline.drive_to_published() /
drive_to_editable() (documented row actions, fresh list read) -- never a form
submit on an Unpublished record, which is what stranded 79878 on 2026-10-12.
"""

from __future__ import annotations

import re
from pathlib import Path

from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED, STATUS_UNPUBLISHED
from cms.pages.gm_message.gm_message_admin_page import (
    GM_MESSAGE_ENTRY_CODE,
    GM_MESSAGE_OBJECT_AUTHORING_SLUG,
    GmMessageAdminPage,
)
from cms.tests.singleton_baseline import (
    GATE_WORKFLOW_BUDGET,
    RecordAdapter,
    SingletonBaseline,
    copy_with_name,
    drive_to_editable,
    drive_to_published,
    ensure_cms_session,
    list_status,
    slugify,
)
from config.settings import control_panel_url

A = GmMessageAdminPage
AR = A.AR_SUFFIX
PBI = "129397"
RESTORE_BUDGET = 300.0  # s -- module-end / CLI status step
MANAGE_URL = control_panel_url(f"/en/web/qatar-chamber/manage-{GM_MESSAGE_OBJECT_AUTHORING_SLUG}")
FILE_LABELS = (A.LABEL_HERO, A.LABEL_HERO + AR, A.LABEL_PORTRAIT, A.LABEL_PORTRAIT + AR)
_IMAGE_MAGIC = (b"\xff\xd8", b"\x89PNG", b"GIF8", b"<svg", b"<?xml", b"RIFF")


def norm_html(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def same_file(actual: str, expected: str) -> bool:
    """Liferay dedupes a same-named re-upload as 'name (n).ext'."""
    strip = lambda s: re.sub(r"\s*\(\d+\)(?=\.[^.]+$)", "", (s or "").strip())  # noqa: E731
    return strip(actual) == strip(expected)


def read_state(admin: GmMessageAdminPage) -> dict:
    """Fresh read of every field. Absent labels are skipped instantly
    (field_count), never auto-waited, so a VERIFY-LIVE miss costs nothing."""
    authoring = admin.open_record("en")
    state = {"status": authoring.current_status()}
    for label in A.TEXT_LABELS:
        for lab in (label, label + AR):
            state[lab] = authoring.field_value(lab) if authoring.field_count(lab) else None
    for loc in ("en", "ar"):
        state[f"content_{loc}"] = admin.page_content_html_or_none(loc)
    for label in FILE_LABELS:
        state[f"file:{label}"] = (
            authoring.current_file_name(label) if admin.has_file_field(label) else None
        )
    state["active"] = admin.active_status_or_none()
    return state


class GmMessageRecord(RecordAdapter):
    key = "gm_message_79878"
    title = "GM Message 79878"

    def prepare(self, page) -> None:
        """TEST_USER on the manage page; one re-login if the saved session is
        stale. Read-only (--dry-run): nothing is typed."""
        ensure_cms_session(page, MANAGE_URL, allow_login=not self.read_only)

    def read(self, page) -> dict:
        return read_state(A(page))

    def download_files(self, page, state: dict, dest: Path) -> dict:
        authoring = A(page).open_record("en")
        saved = {}
        for label in FILE_LABELS:
            name = state.get(f"file:{label}") or ""
            if not name:
                continue
            folder = dest / slugify(label)
            folder.mkdir(parents=True, exist_ok=True)
            got = authoring.download_current_file(label, str(folder / name))
            head = Path(got).read_bytes()[:8] if got else b""
            if not head.lstrip().startswith(_IMAGE_MAGIC):
                raise AssertionError(
                    f"could not download the current {label!r} of {self.title} as image bytes "
                    f"(got {head!r}) -- refusing to start a run without a byte-level baseline")
            saved[f"file:{label}"] = str(Path(slugify(label)) / name)
        return saved

    def same(self, key: str, have, want) -> bool:
        if key.startswith("content_"):
            return norm_html(have) == norm_html(want)
        if key.startswith("file:"):
            return same_file(have or "", want)
        return have == want

    # ---- workflow (documented transitions, fresh list read) ------------------
    @staticmethod
    def _list(admin):
        return lambda: admin.open_list("en")

    @staticmethod
    def _submit_draft(admin):
        """Draft -> the form's Submit for Review (status=0, locale-independent)."""
        return lambda: admin.submit_publish(admin.open_record("en"))

    def _to_published(self, admin, budget: float) -> None:
        drive_to_published(self._list(admin), GM_MESSAGE_ENTRY_CODE, self._submit_draft(admin),
                           budget=budget)

    def apply(self, page, target: dict, files_dir: Path) -> None:
        """One pass:
        1. read, and work out which FIELDS differ (status handled in step 4);
        2. only if a field differs: make the record editable (Published ->
           unpublish, Pending Review -> approve -> unpublish, Archived ->
           restore) and confirm it left Published on a fresh read;
        3. write ONLY the differing fields, then Save as Draft;
        4. drive the status to the captured one (Published: row Publish from
           Unpublished, Submit for Review from Draft, approve from Pending)."""
        admin = A(page)
        changed = [k for k in self.changed_keys(read_state(admin), target) if k != "status"]
        if changed:
            drive_to_editable(self._list(admin), GM_MESSAGE_ENTRY_CODE)
            authoring = admin.open_record("en")
            if authoring.current_status() == STATUS_PUBLISHED:
                raise AssertionError(f"{self.title} still opens as Published after the unpublish "
                                     "step -- not writing any field")
            for key in changed:
                if key.startswith("content_"):
                    admin.set_page_content_html(target[key], key.split("_", 1)[1])
                elif key.startswith("file:"):
                    rel = target["_files"].get(key)
                    if not rel:
                        raise AssertionError(f"no captured bytes for {key!r} in the snapshot")
                    authoring.upload_file(key.split(":", 1)[1], copy_with_name(files_dir / rel, target[key]))
                elif key == "active":
                    admin.set_active_status(bool(target["active"]))
                else:
                    authoring.fill_text(key, target[key])
            authoring.save_as_draft()  # commits the writes; no required-field gate
        if target["status"] == STATUS_PUBLISHED:
            self._to_published(admin, budget=RESTORE_BUDGET)
        elif (target["status"] in (STATUS_UNPUBLISHED, STATUS_DRAFT)
              and list_status(self._list(admin), GM_MESSAGE_ENTRY_CODE) == STATUS_PUBLISHED):
            drive_to_editable(self._list(admin), GM_MESSAGE_ENTRY_CODE)  # baseline was not live

    def ensure_ready(self, page) -> None:
        """Every case's precondition is the Published record -- status only,
        no field write."""
        self._to_published(A(page), budget=GATE_WORKFLOW_BUDGET)


def build_baseline() -> SingletonBaseline:
    return SingletonBaseline(PBI, "gm_message", [GmMessageRecord()])

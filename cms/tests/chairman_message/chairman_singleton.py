"""
cms/tests/chairman_message/chairman_singleton.py -- the module-level baseline
for PBI 129393's two live records. See cms/tests/singleton_baseline.py for the
contract (captured once at module start, restored once at module end,
`tools/restore_singleton.py --pbi 129393` after a killed run).

Records
-------
* Chairman Message Page singleton `QCDEMO-129393-chairmans-message` (row
  78261) -- every text field EN/AR, Message Content HTML EN/AR (CKEditor
  getData/setData), the portrait (file name + bytes), the hyperlink fields,
  Active Status when the form renders one, and the workflow status.
* About Hero Banner row with Page Key `chairman-message` -- written by
  tc_134760 (Banner Image Alt Text; the Banner Image bytes are captured too).
  Disposable `QCTEST-<tc>-HERO` rows are NOT part of this: they are still
  deleted per test, by exact title.

Account: QC Site Content Editor -- the account the per-test restores used.
"""

from __future__ import annotations

import re
from pathlib import Path

from cms.pages.chairman_message.chairman_message_admin_page import (
    CHAIRMAN_MESSAGE_ENTRY_CODE,
    HERO_PAGE_KEY,
    ChairmanHeroBannerAdminPage,
    ChairmanMessageAdminPage,
)
from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import (
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.tests.singleton_baseline import (
    GATE_WORKFLOW_BUDGET,
    RESTORE_WORKFLOW_BUDGET,
    RecordAdapter,
    SingletonBaseline,
    copy_with_name,
    drive_to_editable,
    drive_to_published,
    ensure_cms_session,
)
from config.settings import control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until

PBI = "129393"
EN, AR = "en", "ar"
PUBLISH_TIMEOUT = 75.0
UNPUBLISH_TIMEOUT = 30.0
UNPUBLISH_BUDGET = 150.0  # s -- one row unpublish, verified on a fresh list read
# Every field the form holds, in the snapshot's "<key>_<locale>" naming.
RECORD_KEYS = ("page_title", "hero_alt", "portrait_alt", "name", "designation",
               "message", "hyperlink_title", "hyperlink_url", "portrait")


def _manage_url() -> str:
    return control_panel_url(f"/en/web/qatar-chamber/manage-{ChairmanMessageAdminPage.SLUG}")


def locales(key: str) -> tuple:
    return (EN, AR) if ChairmanMessageAdminPage.FIELDS[key].bilingual else (EN,)


def read_field(admin: ChairmanMessageAdminPage, key: str, locale: str = EN) -> str:
    if key in admin.TEXT_KEYS:
        return admin.text_of(key, locale)
    if key == "message":
        return admin.message_html(locale)
    if key == "portrait":
        return admin.portrait_name()
    return admin.value(key)


def write_field(admin: ChairmanMessageAdminPage, key: str, value: str, locale: str = EN) -> None:
    if key in admin.TEXT_KEYS:
        admin.set_text(key, value, locale)
    elif key == "message":
        admin.set_message_html(value, locale)
    elif key == "portrait":
        admin.restore_existing_file("portrait", value)
    else:
        admin.fill(key, value)


def _wait(check, timeout: float) -> bool:
    try:
        wait_until(check, timeout=timeout, poll=2.0)
        return True
    except WaitTimeoutError:
        return False


def make_editable(admin: ChairmanMessageAdminPage) -> ChairmanMessageAdminPage:
    """A Published record must be unpublished before any edit (guide §4).
    It lands on `Unpublished` (standards.md §States), not Draft.

    Driven through the ROW action (`data-qc-oel-unpublish`, whole
    confirm()/prompt() chain accepted) and verified on a fresh entries-list
    read -- `drive_to_editable`. Changed 2026-10-13: the form's "Unpublish to
    edit as draft" button path waited on `networkidle`, which this page never
    reaches after the click (load fired, then 30 s timeout -- 134829 / 134831
    / 134834), stranding 78261 Unpublished with the test dead."""
    admin.open_record()
    if admin.current_status() not in (STATUS_PUBLISHED, STATUS_PENDING_REVIEW):
        return admin
    drive_to_editable(lambda: admin.open_entries_list(locale=EN), CHAIRMAN_MESSAGE_ENTRY_CODE,
                      budget=UNPUBLISH_BUDGET)
    admin.open_record()
    return admin


def submit_form(admin: ChairmanMessageAdminPage) -> None:
    """The open form's Submit for Review; raises on a visible refusal. Does
    not assert the landing status (the account decides it)."""
    admin.submit_for_review()
    if admin.refusal_visible():
        raise AssertionError(f"Submit was refused: {admin.refusal_text()!r}")


def to_published(admin: ChairmanMessageAdminPage, budget: float) -> None:
    """Documented transitions only, verified by a fresh entries-list read:
    approve / row Publish from Unpublished / Submit for Review from Draft.
    A form submit on an UNPUBLISHED record never publishes it (GM incident
    2026-10-12), which is why the old publish() path is not used here."""
    def _submit_draft() -> None:
        admin.open_record()
        submit_form(admin)

    drive_to_published(lambda: admin.open_entries_list(locale=EN), CHAIRMAN_MESSAGE_ENTRY_CODE,
                       _submit_draft, budget=budget)


def publish(admin: ChairmanMessageAdminPage) -> None:
    """Editor Submit for Review -- privileged path -> Published, confirmed by re-read.

    FIX 2026-10-13 (134779): on an UNPUBLISHED record the form's value=0
    control reads "Save Changes" and KEEPS the record Unpublished, so the
    "Submit for Review"/"Publish" text match timed out. There the edits are
    saved through that control (by attribute), then the row action
    `[data-qc-oel-publish]` publishes (to_published, fresh list read)."""
    if admin.current_status() == STATUS_UNPUBLISHED:
        admin.submit_via(admin.PUBLISH_SUBMIT)
        if admin.refusal_visible():
            raise AssertionError(f"Save Changes was refused: {admin.refusal_text()!r}")
        to_published(admin, budget=PUBLISH_TIMEOUT)
    else:
        admin.submit_for_review()
        if admin.refusal_visible():
            raise AssertionError(f"Submit was refused: {admin.refusal_text()!r}")
    admin.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_TIMEOUT)


class ChairmanMessageRecord(RecordAdapter):
    key = "chairman_message_78261"
    title = "Chairman Message Page 78261 (QCDEMO-129393-chairmans-message)"

    def prepare(self, page) -> None:
        if self.read_only:  # --dry-run: read as the saved TEST_USER session, type nothing
            ensure_cms_session(page, _manage_url(), allow_login=False)
            return
        ChairmanMessageAdminPage(page).sign_in(ROLE_EDITOR)

    def read(self, page) -> dict:
        admin = ChairmanMessageAdminPage(page)
        admin.open_record()
        state = {"status": admin.current_status()}
        for key in RECORD_KEYS:
            for loc in locales(key):
                state[f"{key}_{loc}"] = read_field(admin, key, loc)
        state["active"] = admin.active_status_or_none()
        return state

    def download_files(self, page, state: dict, dest: Path) -> dict:
        name = state.get("portrait_en") or ""
        if not name:
            return {}
        admin = ChairmanMessageAdminPage(page)
        admin.open_record()
        folder = dest / "portrait"
        folder.mkdir(parents=True, exist_ok=True)
        if not admin.download_current_file(admin.spec("portrait").label, str(folder / name)):
            raise AssertionError("could not download the Chairman Portrait bytes -- refusing to start")
        return {"portrait_en": str(Path("portrait") / name)}

    def same(self, key: str, have, want) -> bool:
        if key == "portrait_en":  # a byte re-upload is stored as `name (n).ext`
            strip = lambda v: re.sub(r"\s*\(\d+\)(?=\.[^.]+$)", "", (v or "").strip())  # noqa: E731
            return strip(have) == strip(want)
        return have == want

    def _approve_if_pending(self, admin) -> None:
        admin.open_record()
        if admin.current_status() == STATUS_PENDING_REVIEW:
            admin.open_entries_list(locale=EN)
            admin.approve_entry(CHAIRMAN_MESSAGE_ENTRY_CODE)

    def apply(self, page, target: dict, files_dir: Path) -> None:
        """One pass: approve a pending version, unpublish if a field must be
        written, write every differing field, then publish (or save a draft)
        to match the captured status. The portrait is restored by re-selecting
        the captured Documents & Media file; its downloaded bytes are the
        fallback when that file is no longer in the picker."""
        admin = ChairmanMessageAdminPage(page)
        self._approve_if_pending(admin)
        changed = [k for k in self.changed_keys(self.read(page), target) if k != "status"]
        if changed:
            make_editable(admin)
        errors = []
        for key in changed:
            try:
                if key == "active":
                    admin.set_active_status(bool(target["active"]))
                    continue
                field, loc = key.rsplit("_", 1)
                if field == "portrait":
                    try:
                        admin.restore_existing_file("portrait", target[key])
                    except Exception:  # noqa: BLE001 -- fall back to the captured bytes
                        rel = target.get("_files", {}).get(key)
                        if not rel:
                            raise
                        admin.upload_file(admin.spec("portrait").label,
                                          copy_with_name(files_dir / rel, target[key]))
                else:
                    write_field(admin, field, target[key], loc)
            except Exception as exc:  # noqa: BLE001 -- still republish the rest
                errors.append(f"{key}: {exc!r}")
        if target["status"] == STATUS_PUBLISHED:
            if changed:
                submit_form(admin)  # commits the open form holding the writes
            to_published(admin, RESTORE_WORKFLOW_BUDGET)
        elif changed:
            admin.save_as_draft()
        if errors:
            raise AssertionError(f"restore writes failed: {errors!r}")

    def ensure_ready(self, page) -> None:
        """Every case starts from the Published record (status only)."""
        admin = ChairmanMessageAdminPage(page)
        admin.sign_in(ROLE_EDITOR)
        to_published(admin, GATE_WORKFLOW_BUDGET)


class ChairmanHeroRow(RecordAdapter):
    key = "about_hero_chairman_message"
    title = "About Hero Banner row chairman-message"
    per_test_precondition = False  # only tc_134760 touches it

    def prepare(self, page) -> None:
        if self.read_only:  # --dry-run: read as the saved TEST_USER session, type nothing
            ensure_cms_session(page, _manage_url(), allow_login=False)
            return
        ChairmanHeroBannerAdminPage(page).sign_in(ROLE_EDITOR)

    def read(self, page) -> dict:
        hero = ChairmanHeroBannerAdminPage(page)
        hero.open_by_key(HERO_PAGE_KEY)
        return {"alt_en": hero.alt_text(), "image": hero.image_name(), "status": hero.current_status()}

    def download_files(self, page, state: dict, dest: Path) -> dict:
        if not state.get("image"):
            return {}
        hero = ChairmanHeroBannerAdminPage(page)
        hero.open_by_key(HERO_PAGE_KEY)
        folder = dest / "banner_image"
        folder.mkdir(parents=True, exist_ok=True)
        if not hero.download_current_file(hero.IMAGE_LABEL, str(folder / state["image"])):
            raise AssertionError("could not download the chairman-message Banner Image -- refusing to start")
        return {"image": str(Path("banner_image") / state["image"])}

    def same(self, key: str, have, want) -> bool:
        if key == "image":
            stem = (want or "").rsplit(".", 1)[0]
            return bool(stem) and stem in (have or "")
        return have == want

    def apply(self, page, target: dict, files_dir: Path) -> None:
        hero = ChairmanHeroBannerAdminPage(page)
        changed = [k for k in self.changed_keys(self.read(page), target) if k != "status"]
        hero.open_by_key(HERO_PAGE_KEY)
        if changed and hero.current_status() == STATUS_PUBLISHED:
            hero.unpublish_to_edit_as_draft()
            _wait(lambda: hero.reopen().current_status() != STATUS_PUBLISHED, UNPUBLISH_TIMEOUT)
        if "image" in changed:
            rel = target.get("_files", {}).get("image")
            if not rel:
                raise AssertionError("no captured Banner Image bytes in the snapshot")
            hero.upload_file(hero.IMAGE_LABEL, copy_with_name(files_dir / rel, target["image"]))
        if "alt_en" in changed:
            hero.fill_alt_text(target["alt_en"])
        if target["status"] == STATUS_PUBLISHED:
            if changed or hero.current_status() != STATUS_PUBLISHED:
                hero.publish()
                hero.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_TIMEOUT)
        elif changed:
            hero.save_as_draft()


def build_baseline() -> SingletonBaseline:
    return SingletonBaseline(PBI, "chairman_message", [ChairmanMessageRecord(), ChairmanHeroRow()])

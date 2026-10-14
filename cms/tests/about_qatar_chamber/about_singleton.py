"""
cms/tests/about_qatar_chamber/about_singleton.py -- the module-level baseline
for PBI 129392's two live records. See cms/tests/singleton_baseline.py for the
contract (captured once at module start, restored once at module end,
`tools/restore_singleton.py --pbi 129392` after a killed run).

Records
-------
* AboutQatarChamberPage singleton `QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY`
  -- text fields EN/AR, Page Content HTML EN/AR (CKEditor getData/setData,
  never typed), the Content Image bytes, Active Status, workflow status.
* AboutHeroBanner row `QCDEMO-ABOUT-HERO-about-us` -- written by tc_134697 /
  tc_134698 (Banner Image bytes, Banner Image Alt Text, workflow status).
  Disposable `QCTEST-<tc>-HERO` rows are NOT part of this: they are still
  deleted per test, by exact title.

Account: the TEST_USER admin session (the account the per-test restores used).

REUSES the module's previous recovery file: a `dirty.json` left in
reports/backups/about_qatar_chamber_129392/ by a run killed under the old
per-test scheme is converted into an unrestored snapshot on the next start,
so the engine heals from it like any interrupted run.
"""

from __future__ import annotations

import datetime as _dt
import html as _html
import json
import re
import shutil
from pathlib import Path

from cms.pages.about_qatar_chamber.about_qatar_chamber_admin_page import (
    ABOUT_PAGE_ENTRY_CODE,
    ABOUT_PAGE_SLUG,
    HERO_BANNER_ABOUT_US_PAGE_KEY,
    AboutQatarChamberAdminPage,
)
from cms.pages.components.object_authoring_page import (
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    ObjectAuthoringPage,
)
from cms.tests.singleton_baseline import (
    BACKUP_ROOT,
    GATE_WORKFLOW_BUDGET,
    RESTORE_WORKFLOW_BUDGET,
    SNAPSHOT_FILE,
    STATE_IN_PROGRESS,
    RecordAdapter,
    SingletonBaseline,
    copy_with_name,
    drive_to_published,
    ensure_cms_session,
)
from config.settings import control_panel_url

PBI = "129392"
SLUG = "about_qatar_chamber"
PUBLISH_CONFIRM_TIMEOUT = 120.0
TEXT_EN_KEYS = ("page_title", "alt_text", "hyperlink_title", "hyperlink_url")
TEXT_AR_KEYS = ("page_title", "alt_text")
LEGACY_BACKUP_DIR = BACKUP_ROOT / "about_qatar_chamber_129392"
LEGACY_DIRTY_MARKER = LEGACY_BACKUP_DIR / "dirty.json"
MANAGE_URL = control_panel_url(f"/en/web/qatar-chamber/manage-{ABOUT_PAGE_SLUG}")


def norm_html(value: str) -> str:
    """HTML compared on content: entities decoded, inter-tag whitespace and
    nbsp collapsed (CKEditor's getData() pretty-prints)."""
    text = _html.unescape(value or "").replace("\xa0", " ")
    return re.sub(r">\s+<", "><", text).strip()


def image_matches(actual: str, original: str) -> bool:
    """A re-upload becomes `<stem> (N).png` (Liferay de-duplication)."""
    stem = (original or "").rsplit(".", 1)[0]
    return bool(stem) and stem in (actual or "")


def read_page_form(admin: AboutQatarChamberAdminPage, authoring) -> dict:
    """Every field of the open page-record form (the runtime read tests use)."""
    state = {f"{k}_en": admin.page_text(k, "en") for k in TEXT_EN_KEYS}
    state.update({f"{k}_ar": admin.page_text(k, "ar") for k in TEXT_AR_KEYS})
    state["content_en"] = admin.page_content_html("en")
    state["content_ar"] = admin.page_content_html("ar")
    state["image"] = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    state["active"] = admin.active_status_or_none()
    state["workflow"] = authoring.current_status()
    return state


def _sign_in_admin(page, read_only: bool = False) -> None:
    """TEST_USER on a CMS-only page; one re-login if the saved session is
    stale. Read-only (--dry-run): nothing is typed."""
    ensure_cms_session(page, MANAGE_URL, allow_login=not read_only)


def _page_to_published(admin: AboutQatarChamberAdminPage, budget: float) -> None:
    """Documented transitions only, verified by a fresh entries-list read
    (approve / row Publish from Unpublished / Submit from Draft)."""
    drive_to_published(
        lambda: ObjectAuthoringPage(admin.page, slug=ABOUT_PAGE_SLUG).open_entries_list(locale="en"),
        ABOUT_PAGE_ENTRY_CODE,
        lambda: admin.open_page_record_in("en").submit_via(admin.PUBLISH_SUBMIT),
        budget=budget,
    )


class AboutPageRecord(RecordAdapter):
    key = "about_page"
    title = "About Qatar Chamber page record (QCDEMO-129392-...-ENTRY)"

    def prepare(self, page) -> None:
        _sign_in_admin(page, self.read_only)

    def read(self, page) -> dict:
        admin = AboutQatarChamberAdminPage(page)
        return read_page_form(admin, admin.open_page_record_in("en"))

    def download_files(self, page, state: dict, dest: Path) -> dict:
        if not state.get("image"):
            return {}
        admin = AboutQatarChamberAdminPage(page)
        authoring = admin.open_page_record_in("en")
        folder = dest / "content_image"
        folder.mkdir(parents=True, exist_ok=True)
        if not authoring.download_current_file(admin.CONTENT_IMAGE_UPLOAD_LABEL,
                                               str(folder / state["image"])):
            raise AssertionError("could not download the Content Image bytes -- refusing to start")
        return {"image": str(Path("content_image") / state["image"])}

    def same(self, key: str, have, want) -> bool:
        if key.startswith("content_"):
            return norm_html(have) == norm_html(want)
        if key == "image":
            return image_matches(have, want) if want else not have
        return have == want

    def _approve_if_pending(self, admin) -> None:
        if admin.open_page_record_in("en").current_status() == STATUS_PENDING_REVIEW:
            admin.open_page_entries_list().approve_entry(ABOUT_PAGE_ENTRY_CODE)

    def apply(self, page, target: dict, files_dir: Path) -> None:
        """One pass: approve a pending version, write ONLY the differing
        fields, commit them, then drive the status to the captured one. This
        form edits a Published record in place (Publish = "Save"); the status
        step goes through drive_to_published() -- a form submit on an
        UNPUBLISHED record never publishes it (GM incident 2026-10-12)."""
        admin = AboutQatarChamberAdminPage(page)
        self._approve_if_pending(admin)
        authoring = admin.open_page_record_in("en")
        changed = [k for k in self.changed_keys(read_page_form(admin, authoring), target)
                   if k != "workflow"]
        for key in changed:
            if key.startswith("content_"):
                admin.set_page_content_html(target[key], key.split("_", 1)[1])
            elif key == "image":
                rel = target.get("_files", {}).get("image")
                if not rel:
                    raise AssertionError("no captured Content Image bytes in the snapshot")
                authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL,
                                      copy_with_name(files_dir / rel, target["image"]))
            elif key == "active":
                admin.set_active_status(bool(target["active"]))
            else:
                field, locale = key.rsplit("_", 1)
                admin.fill_page_text(field, target[key], locale)
        if target["workflow"] == STATUS_PUBLISHED:
            if changed:
                authoring.submit_via(admin.PUBLISH_SUBMIT)  # commits the writes
            _page_to_published(admin, RESTORE_WORKFLOW_BUDGET)
        elif changed:
            authoring.submit_via(admin.SAVE_DRAFT_SUBMIT)

    def ensure_ready(self, page) -> None:
        """Every case starts from the Published record (status only)."""
        _page_to_published(AboutQatarChamberAdminPage(page), GATE_WORKFLOW_BUDGET)


class AboutHeroRow(RecordAdapter):
    key = "about_hero_about_us"
    title = "AboutHeroBanner row about-us (QCDEMO-ABOUT-HERO-about-us)"
    per_test_precondition = False  # only tc_134697/134698 touch it; they handle status

    def prepare(self, page) -> None:
        _sign_in_admin(page, self.read_only)

    def read(self, page) -> dict:
        admin = AboutQatarChamberAdminPage(page)
        authoring = admin.open_hero_banner_record()
        page_key = authoring.field_value(admin.PAGE_KEY_LABEL)
        if page_key != HERO_BANNER_ABOUT_US_PAGE_KEY:
            raise AssertionError(f"opened the wrong AboutHeroBanner row (Page Key {page_key!r})")
        return {
            "page_key": page_key,
            "image": authoring.current_file_name(admin.BANNER_IMAGE_UPLOAD_LABEL),
            "alt_en": authoring.field_value(admin.BANNER_IMAGE_ALT_TEXT_LABEL),
            "workflow": authoring.current_status(),
        }

    def download_files(self, page, state: dict, dest: Path) -> dict:
        if not state.get("image"):
            return {}
        admin = AboutQatarChamberAdminPage(page)
        authoring = admin.open_hero_banner_record()
        folder = dest / "banner_image"
        folder.mkdir(parents=True, exist_ok=True)
        if not authoring.download_current_file(admin.BANNER_IMAGE_UPLOAD_LABEL,
                                               str(folder / state["image"])):
            raise AssertionError("could not download the about-us Banner Image bytes -- refusing to start")
        return {"image": str(Path("banner_image") / state["image"])}

    def same(self, key: str, have, want) -> bool:
        if key == "image":
            return image_matches(have, want) if want else not have
        return have == want

    def apply(self, page, target: dict, files_dir: Path) -> None:
        """One pass. A direct replace persists in one save; an EMPTY field
        (tc_134698's phase 1) also takes a plain upload. Unpublish first
        because Save as Draft is disabled on a Published row."""
        admin = AboutQatarChamberAdminPage(page)
        changed = [k for k in self.changed_keys(self.read(page), target) if k != "workflow"]
        authoring = admin.open_hero_banner_record()
        if changed and authoring.current_status() == STATUS_PUBLISHED:
            authoring.unpublish_to_edit_as_draft()
        if "image" in changed:
            rel = target.get("_files", {}).get("image")
            if not rel:
                raise AssertionError("no captured Banner Image bytes in the snapshot")
            authoring.upload_file(admin.BANNER_IMAGE_UPLOAD_LABEL,
                                  copy_with_name(files_dir / rel, target["image"]))
        if "alt_en" in changed:
            authoring.fill_text(admin.BANNER_IMAGE_ALT_TEXT_LABEL, target["alt_en"])
        if target["workflow"] == STATUS_PUBLISHED:
            if changed or authoring.current_status() != STATUS_PUBLISHED:
                authoring.submit_for_review()  # TEST_USER: privileged -> Published
                authoring.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_CONFIRM_TIMEOUT)
        elif changed:
            authoring.save_as_draft()


def migrate_legacy_marker(baseline: SingletonBaseline) -> None:
    """Turns the old per-test scheme's `dirty.json` (a page-record baseline
    written before a mutation, deleted only after a verified restore) into an
    unrestored snapshot, so the engine heals from it. No-op when absent."""
    if not LEGACY_DIRTY_MARKER.exists():
        return
    legacy = json.loads(LEGACY_DIRTY_MARKER.read_text(encoding="utf-8"))
    stamp = _dt.datetime.fromtimestamp(LEGACY_DIRTY_MARKER.stat().st_mtime).strftime("%Y%m%d-%H%M")
    folder = BACKUP_ROOT / f"{PBI}_{SLUG}_{stamp}-legacy"
    folder.mkdir(parents=True, exist_ok=True)
    state = {k: v for k, v in legacy.items() if not k.startswith("_")}
    state["_files"] = {}
    image_backup = legacy.get("_image_backup")
    if state.get("image") and image_backup and Path(image_backup).exists():
        dest = folder / "files" / AboutPageRecord.key / "content_image"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(image_backup, dest / state["image"])
        # Same layout capture() writes: relative to the snapshot dir.
        state["_files"]["image"] = (Path("files") / AboutPageRecord.key / "content_image" / state["image"]).as_posix()
    (folder / SNAPSHOT_FILE).write_text(json.dumps({
        "pbi": PBI, "slug": SLUG, "state": STATE_IN_PROGRESS,
        "created": _dt.datetime.now().isoformat(timespec="seconds"),
        "note": f"converted from {LEGACY_DIRTY_MARKER} (left by tc_{legacy.get('_tc', '?')})",
        "records": {AboutPageRecord.key: state},
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    LEGACY_DIRTY_MARKER.unlink()


def build_baseline() -> SingletonBaseline:
    return SingletonBaseline(PBI, SLUG, [AboutPageRecord(), AboutHeroRow()],
                             before_start=migrate_legacy_marker)

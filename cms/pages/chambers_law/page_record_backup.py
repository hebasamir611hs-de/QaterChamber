"""
cms/pages/chambers_law/page_record_backup.py -- read / compare / restore the
Chamber Laws Page singleton (`QCDEMO-129394-CHAMBER_LAWS_PAGE-ENTRY`) against
its backed-up originals.

Shared by two callers (user decision 2026-10-12: restore ONCE per run, not
after every test):
  - the module-scoped autouse fixture in
    `cms/tests/chambers_law/test_chambers_law_control_panel.py`, whose
    teardown restores the record after the whole module ran;
  - `tools/restore_chamber_laws_page.py`, the standalone CLI for when a run
    was killed before that teardown could fire.

The originals live in `reports/backups/chamber_laws_page_20261012/`:
`snapshot.json` (all EN/AR texts, both Intro Content HTML bodies, the
workflow status, the image file name) and `content_image.png` (the image's
bytes). The snapshot carries no Status-picklist / Active Status entries;
both read "Published" / ticked in the read-only probe taken on 2026-10-12
before any test wrote to the record.

Intro Content is written back through CKEditor's own setData() (typing
cannot reproduce `&amp;`, curly quotes or paragraph boundaries exactly) and
compared on decoded, whitespace-normalised HTML.
"""

import html as _html
import json
import re
import shutil
import tempfile
from pathlib import Path

from cms.pages.chambers_law.chambers_law_admin_page import CHAMBERS_LAW_PAGE_ENTRY_CODE
from cms.pages.components.object_authoring_page import (
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
)
from core.utils.logger import get_logger
from core.utils.waits import wait_until

logger = get_logger("chambers_law_page_backup")

ROOT = Path(__file__).resolve().parents[3]
PAGE_BACKUP_DIR = ROOT / "reports" / "backups" / "chamber_laws_page_20261012"
PAGE_SNAPSHOT = PAGE_BACKUP_DIR / "snapshot.json"
PAGE_BACKUP_IMAGE = PAGE_BACKUP_DIR / "content_image.png"

# ChambersLawAdminPage.PAGE_TEXT_FIELDS key -> snapshot label.
PAGE_TEXT_KEYS = {
    "page_title": "Page Title",
    "intro_heading": "Intro Heading",
    "alt_text": "Content Image Alt Text",
    "refs_heading": "References Heading",
}
ORIGINAL_PAGE_STATUS = "Published"   # Status picklist, read 2026-10-12
ORIGINAL_ACTIVE_STATUS = True        # Active Status, read 2026-10-12
PUBLISH_CONFIRM_TIMEOUT = 120.0
RESTORE_VERIFY_TIMEOUT = 60.0


def temp_dir() -> str:
    path = Path(tempfile.gettempdir()) / "qc_chambers_law_129394"
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def norm_html(value: str) -> str:
    """HTML compared on content: entities decoded, inter-tag whitespace and
    nbsp collapsed (CKEditor's getData() pretty-prints)."""
    text = _html.unescape(value or "").replace("\xa0", " ")
    return re.sub(r">\s+<", "><", text).strip()


def image_matches(actual: str, original: str) -> bool:
    """A re-upload becomes `<stem> (N).png` (Liferay de-duplication)."""
    stem = (original or "").rsplit(".", 1)[0]
    return bool(stem) and stem in (actual or "")


def snapshot_state() -> dict:
    snap = json.loads(PAGE_SNAPSHOT.read_text(encoding="utf-8"))
    state = {}
    for key, label in PAGE_TEXT_KEYS.items():
        state[f"{key}_en"] = snap[label]
        state[f"{key}_ar"] = snap[f"{label} — العربية"]
    state["intro_en"] = snap["intro_html_en"]
    state["intro_ar"] = snap["intro_html_ar"]
    state["image"] = snap["content_image"]
    state["page_status"] = ORIGINAL_PAGE_STATUS
    state["active"] = ORIGINAL_ACTIVE_STATUS
    state["workflow"] = snap["status"]
    return state


def read_open_form(admin, authoring) -> dict:
    state = {}
    for key in PAGE_TEXT_KEYS:
        for loc in ("en", "ar"):
            state[f"{key}_{loc}"] = admin.page_text(key, loc)
    state["intro_en"] = admin.intro_html("en")
    state["intro_ar"] = admin.intro_html("ar")
    state["image"] = authoring.current_file_name(admin.CONTENT_IMAGE_UPLOAD_LABEL)
    state["page_status"] = admin.page_status_value()
    state["active"] = admin.active_status_checked()
    state["workflow"] = authoring.current_status()
    return state


def read_page_state(admin) -> dict:
    authoring = admin.open_page_record(locale="en")
    return read_open_form(admin, authoring)


def state_diff(actual: dict, target: dict) -> list:
    diffs = []
    for key, want in target.items():
        have = actual.get(key)
        if key.startswith("intro_"):
            same = norm_html(have) == norm_html(want)
        elif key == "image":
            same = image_matches(have, want)
        else:
            same = have == want
        if not same:
            diffs.append(f"{key}: have {have!r} want {want!r}")
    return diffs


def apply_page_state(admin, target: dict) -> None:
    """Writes every field that differs from `target` back and publishes.
    A record left in Pending Review (an Author submission) is approved
    first so the Editor-side form becomes writable again."""
    authoring = admin.open_page_record(locale="en")
    if authoring.current_status() == STATUS_PENDING_REVIEW:
        admin.open_page_entries_list().approve_entry(CHAMBERS_LAW_PAGE_ENTRY_CODE)
        authoring = admin.open_page_record(locale="en")
    current = read_open_form(admin, authoring)
    if not state_diff(current, target):
        return
    for key in PAGE_TEXT_KEYS:
        for loc in ("en", "ar"):
            if current[f"{key}_{loc}"] != target[f"{key}_{loc}"]:
                admin.fill_page_text(key, target[f"{key}_{loc}"], loc)
    for loc in ("en", "ar"):
        if norm_html(current[f"intro_{loc}"]) != norm_html(target[f"intro_{loc}"]):
            admin.set_intro_html(target[f"intro_{loc}"], loc)
    if current["page_status"] != target["page_status"]:
        admin.choose_page_status(target["page_status"])
    if current["active"] != target["active"]:
        admin.set_active_status(target["active"])
    if not image_matches(current["image"], target["image"]):
        tmp = Path(temp_dir()) / target["image"]
        shutil.copyfile(PAGE_BACKUP_IMAGE, tmp)
        authoring.upload_file(admin.CONTENT_IMAGE_UPLOAD_LABEL, str(tmp))
    authoring.submit_via(admin.PUBLISH_SUBMIT)
    if target["workflow"] == STATUS_PUBLISHED:
        authoring.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_CONFIRM_TIMEOUT)


def restore_page(admin, target: dict | None = None) -> None:
    """One restore pass, then a VERIFIED re-read from a fresh navigation
    (polled briefly: a field write can lag the publish). Raises with the
    remaining differences if the record still does not match."""
    target = target or snapshot_state()
    apply_page_state(admin, target)
    last = {"diff": []}

    def _matches() -> bool:
        last["diff"] = state_diff(read_page_state(admin), target)
        return not last["diff"]

    try:
        wait_until(_matches, timeout=RESTORE_VERIFY_TIMEOUT, poll=5)
    except Exception:  # noqa: BLE001 -- re-raised with the evidence below
        raise AssertionError(
            "restore did not commit on the Chamber Laws Page record: "
            + "; ".join(last["diff"])
        )


def restore_with_retries(admin, attempts: int = 3) -> list:
    """restore_page() retried (it is idempotent). Returns [] on success,
    else the per-attempt errors; never raises."""
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            restore_page(admin)
            return []
        except Exception as exc:  # noqa: BLE001 -- retried, then reported
            errors.append(f"attempt {attempt}: {exc!r}")
            logger.warning("Chamber Laws Page restore attempt %d failed: %r", attempt, exc)
    return errors


# ===========================================================================
# AboutHeroBanner row `QCDEMO-ABOUT-HERO-chamber-laws` (pageKey chamber-laws)
# USER APPROVAL 2026-10-12 (this record only): hero cases 134897, 134899,
# 134900, 134901, 134902 may write to it. Same pattern as the page record:
# snapshot BEFORE the module runs, restore ONCE at module end, verify by
# re-read. The snapshot is taken once and NEVER overwritten -- a re-capture
# after a dead run would bake test data in as the "original".
# ===========================================================================
HERO_BACKUP_DIR = ROOT / "reports" / "backups" / "chamber_laws_hero_20261012"
HERO_SNAPSHOT = HERO_BACKUP_DIR / "snapshot.json"
HERO_IMAGE_LABEL = "Banner Image"
HERO_IMAGE_AR_LABEL = "Banner Image (Arabic)"
HERO_ALT_EN = 'input[name="ObjectField_bannerImageAltText"]'
HERO_ALT_AR = "#qc-ar-bannerImageAltText"
HERO_PAGE_KEY = 'input[name="ObjectField_pageKey"]'
HERO_ACTIVE = 'input[name="ObjectField_activeStatus"]'
# File names our hero fixtures upload -- a snapshot showing one of these is
# already polluted and is refused (the live original is chamber-laws-hero.jpeg).
_TEST_HERO_FILE = re.compile(r"^(hero|content|lawbook)[-.( ]", re.I)


def _open_hero(admin):
    return admin.open_hero_record(admin.HERO_BANNER_CHAMBER_LAWS_CODE, locale="en")


def read_hero_open_form(admin, authoring) -> dict:
    page = admin.page
    return {
        "page_key": page.locator(HERO_PAGE_KEY).first.input_value(),
        "alt_en": page.locator(HERO_ALT_EN).first.input_value(),
        "alt_ar": page.locator(HERO_ALT_AR).first.input_value(),
        "active": page.locator(HERO_ACTIVE).first.is_checked(),
        "image": authoring.current_file_name(HERO_IMAGE_LABEL),
        "image_ar": authoring.current_file_name(HERO_IMAGE_AR_LABEL),
        "workflow": authoring.current_status(),
    }


def read_hero_state(admin) -> dict:
    return read_hero_open_form(admin, _open_hero(admin))


def hero_snapshot_exists() -> bool:
    return HERO_SNAPSHOT.exists()


def snapshot_hero(admin) -> dict:
    """Captures every field of the hero row + the bytes of each stored image
    into HERO_BACKUP_DIR. No-op (returns the existing snapshot) when one is
    already on disk. Refuses to capture a row that already carries test data."""
    if HERO_SNAPSHOT.exists():
        return hero_snapshot_state()
    authoring = _open_hero(admin)
    state = read_hero_open_form(admin, authoring)
    polluted = [k for k in ("image", "image_ar") if state[k] and _TEST_HERO_FILE.match(state[k])]
    if polluted or state["alt_en"] == "Newspaper headlines background":
        raise RuntimeError(
            f"refusing to snapshot the hero row: it already carries test data ({state!r}); "
            "restore it by hand first"
        )
    HERO_BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    for key, label in (("image", HERO_IMAGE_LABEL), ("image_ar", HERO_IMAGE_AR_LABEL)):
        if state[key]:
            dest = HERO_BACKUP_DIR / f"{key}__{state[key]}"
            authoring.download_current_file(label, str(dest))
            state[f"{key}_file"] = dest.name
    HERO_SNAPSHOT.write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    logger.info("hero snapshot written: %s", state)
    return state


def hero_snapshot_state() -> dict:
    return json.loads(HERO_SNAPSHOT.read_text(encoding="utf-8"))


_HERO_COMPARED = ("page_key", "alt_en", "alt_ar", "active", "image", "image_ar", "workflow")


def hero_diff(actual: dict, target: dict) -> list:
    diffs = []
    for key in _HERO_COMPARED:
        have, want = actual.get(key), target.get(key)
        same = image_matches(have, want) if key.startswith("image") and want else have == want
        if not same:
            diffs.append(f"hero {key}: have {have!r} want {want!r}")
    return diffs


def apply_hero_state(admin, target: dict) -> None:
    authoring = _open_hero(admin)
    current = read_hero_open_form(admin, authoring)
    if not hero_diff(current, target):
        return
    page = admin.page
    if current["page_key"] != target["page_key"]:
        page.locator(HERO_PAGE_KEY).first.fill(target["page_key"])
    if current["alt_en"] != target["alt_en"]:
        page.locator(HERO_ALT_EN).first.fill(target["alt_en"])
    if current["alt_ar"] != target["alt_ar"]:
        page.locator(HERO_ALT_AR).first.fill(target["alt_ar"])
    if current["active"] != target["active"]:
        box = page.locator(HERO_ACTIVE).first
        box.check() if target["active"] else box.uncheck()
    for key, label in (("image", HERO_IMAGE_LABEL), ("image_ar", HERO_IMAGE_AR_LABEL)):
        if target.get(key) and not image_matches(current[key], target[key]):
            tmp = Path(temp_dir()) / target[key]
            shutil.copyfile(HERO_BACKUP_DIR / target[f"{key}_file"], tmp)
            authoring.upload_file(label, str(tmp))
    authoring.submit_via(admin.PUBLISH_SUBMIT)
    if target["workflow"] == STATUS_PUBLISHED:
        authoring.wait_for_status(STATUS_PUBLISHED, timeout=PUBLISH_CONFIRM_TIMEOUT)


def restore_hero(admin, target: dict | None = None) -> None:
    """One restore pass + a VERIFIED re-read; raises with what still differs.
    An image the original did NOT have (image_ar empty) is not removed: the
    hero cases never upload to the Arabic image field."""
    target = target or hero_snapshot_state()
    apply_hero_state(admin, target)
    last = {"diff": []}

    def _matches() -> bool:
        last["diff"] = hero_diff(read_hero_state(admin), target)
        return not last["diff"]

    try:
        wait_until(_matches, timeout=RESTORE_VERIFY_TIMEOUT, poll=5)
    except Exception:  # noqa: BLE001 -- re-raised with the evidence below
        raise AssertionError("restore did not commit on the hero row: " + "; ".join(last["diff"]))


def restore_hero_with_retries(admin, attempts: int = 3) -> list:
    """restore_hero() retried; [] on success (or when no snapshot exists --
    nothing was ever written then), else the errors. Never raises."""
    if not HERO_SNAPSHOT.exists():
        return []
    errors = []
    for attempt in range(1, attempts + 1):
        try:
            restore_hero(admin)
            return []
        except Exception as exc:  # noqa: BLE001 -- retried, then reported
            errors.append(f"hero attempt {attempt}: {exc!r}")
            logger.warning("hero restore attempt %d failed: %r", attempt, exc)
    return errors

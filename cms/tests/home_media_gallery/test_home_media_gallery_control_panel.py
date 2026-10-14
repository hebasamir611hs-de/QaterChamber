"""
cms/tests/home_media_gallery/test_home_media_gallery_control_panel.py — 28
Automation-tagged Control_Panel cases of PBI 129388 (QC-HOME-012, Home Media
Gallery Section): the 20 P1/P2 cases from
.claude/qa-runs/phase3-20261012/129388.todo.json, plus the 8 P3/P4 cases from
129388.p34.todo.json (end of file). The Azure title, steps and expected
results are the oracle.

P1/P2 scripted 2026-10-12 and run live 2026-10-12/13. The P3/P4 block was
scripted OFFLINE 2026-10-13 and has not been executed.

Objects (cms/Content-Admin-Guide.docx §14): videos are **MediaItem**
(`manage-media-item`), and albums come from the Media Center **Photo Album**
object (`manage-photo-album`), whose Submit needs one published **Album
Photo** (`manage-album-photo`). All three slugs were read off the live
sidebar 2026-10-13. Remaining VERIFY-LIVE items are listed in
cms/pages/home_media_gallery/home_media_gallery_admin_page.py.

FIX PASS 5 (2026-10-14) -- READ THIS FIRST: the Home Media Gallery is fed by
**Video Record** (`manage-video-record`, via /o/qc-video-library-api) and
**Photo Album** (via /o/qc-photo-gallery-api) ONLY -- read live from the
fragment's config/source comment and an anonymous Home load's network calls.
**Media Item feeds nothing on Home.** The video cases 133654 / 133657 / 133666
/ 133676 now run on Video Record (`HomeVideoRecordAdminPage`).

FIX PASS 6 (2026-10-14): every remaining "Open Create Video screen" case
(133646 video half, 133647, 133656, 133661, 133662, 133669, 133671, 133672,
133674, 133675, 133677, 133678, 133679, 133681-133685, 133688) runs on Video
Record too; no case is left on Media Item. Field mapping: Media Title (EN/AR)
-> Video Title + Arabic twin; Thumbnail Image -> Video Thumbnail; Video File /
Embed URL -> Video Source Type + Video URL / Video File; Publication Date ->
Published Date. Video Record's Active Status is TICKED by default, so every
case that needs no Home card saves with it unticked. Under the
opt-in nothing is deleted: a QCTEST video is left Inactive (or Unpublished)
and proved gone from Home by `_take_off_home()`.

Every record created here is `QCTEST-<tc_id>-<short>`. It is deleted by exact
title in `finally` on every run. No shared record is touched, so there is no
xdist_group.

Accounts are resolved through cms_role_credentials(): Site Content Editor for
create and publish. The forced-browsing case uses a fresh logged-out context.
"Save" in a case means Submit for Review as Editor, because Save as Draft skips
required-field validation.

Public checks run in a fresh logged-out context on the Home page Media Gallery.
Every tab is read. Two gates apply: Published and Active Status ticked. Active
Status defaults to unticked, so it is ticked wherever the case needs the item
to be visible.

Upload sizes: by project rule, up to 3 MB accepted is OK. The oversize case
therefore uses a 3.1 MB file.
"""

from __future__ import annotations

import re
import tempfile
from pathlib import Path

import allure
import pytest

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.components.object_authoring_page import (
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    STATUS_UNPUBLISHED,
)
from cms.pages.home_media_gallery.home_media_gallery_admin_page import (
    QCTEST_EMBED_URL,
    HomeGalleryAlbumAdminPage,
    HomeGalleryAlbumPhotoAdminPage,
    HomeVideoRecordAdminPage,
)
from cms.tests import authoring_checks as ck
from cms.tests.authoring_checks import dispose as _dispose
from cms.tests.authoring_checks import run_title
from cms.tests.live_write_guard import LiveRecord, deletes_suppressed, log_live_write
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from tools.fixture_factory import make_jpg, make_mp4, make_pdf, make_png
from web.pages.home_media_gallery.home_media_gallery_page import HomeMediaGalleryPage

PBI = "129388"
ONE_MB = 1024 * 1024
PUBLIC_TIMEOUT = 60.0
# Tab labels read live off the public Home gallery 2026-10-13.
TAB_ALL = "All Media"
TAB_VIDEOS = "Video"
TAB_ALBUMS = "Albums"


def _fixture(name: str, maker, size: int) -> str:
    folder = Path(tempfile.gettempdir()) / "qc_home_media_gallery_129388"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    if not path.exists() or path.stat().st_size != size:
        path.write_bytes(maker(size))
    return str(path)


VALID_JPG = _fixture("thumbnail_500kb.jpg", make_jpg, 500 * 1024)
BAD_PDF = _fixture("thumbnail.pdf", make_pdf, 20 * 1024)
BIG_JPG = _fixture("thumbnail_3_1mb.jpg", make_jpg, int(3.1 * ONE_MB))
VALID_MP4 = _fixture("video_1mb.mp4", make_mp4, ONE_MB)
JPG_1MB = _fixture("thumbnail_1mb.jpg", make_jpg, ONE_MB)  # P3 cases name a 1 MB file
PNG_1MB = _fixture("thumbnail_1mb.png", make_png, ONE_MB)

ALBUM = HomeGalleryAlbumAdminPage
PHOTO = HomeGalleryAlbumPhotoAdminPage
ALBUM_FILES = {"cover_image": VALID_JPG}


def _attach(name: str, data) -> None:
    try:
        allure.attach(str(data), name=name, attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# public probe — every gallery tab, logged-out context
# ---------------------------------------------------------------------------
def _gallery_tabs(anon, text: str) -> dict:
    """{tab: text present among that tab's card titles} on a fresh Home load."""
    gallery = HomeMediaGalleryPage(anon).open_home().scroll_to_section()
    seen = {}
    for tab in [t.strip() for t in gallery.tab_texts()] or [TAB_ALL]:
        try:
            gallery.click_tab(tab)
        except Exception:  # noqa: BLE001 — a single-tab section has nothing to click
            pass
        seen[tab] = any(text in t for t in gallery.card_titles())
    return seen


def probe(anon, text: str, expect: bool = True) -> bool:
    """authoring_checks.PublicProbe: reloads Home until `text`'s presence in
    ANY gallery tab equals `expect`; returns the last observation."""
    seen = {"any": not expect, "tabs": {}}

    def _poll() -> bool:
        try:
            tabs = _gallery_tabs(anon, text)
        except Exception:  # noqa: BLE001 — section not rendered: no observation,
            return False   # so a negative check can never pass on a dead page
        seen["tabs"], seen["any"] = tabs, any(tabs.values())
        return seen["any"] == expect

    try:
        wait_until(_poll, timeout=PUBLIC_TIMEOUT, poll=3.0, message=f"gallery never matched {text!r}")
    except WaitTimeoutError:
        pass
    _attach(f"gallery tabs for {text[:40]!r}", seen["tabs"])
    return seen["any"]


def _anon(browser):
    ctx = new_context(browser, use_auth_state=False)
    return ctx, ctx.new_page()


def _close(ctx) -> None:
    try:
        ctx.close()
    except Exception:  # noqa: BLE001
        pass


# ---------------------------------------------------------------------------
# local check bodies (shapes authoring_checks does not cover)
# ---------------------------------------------------------------------------
def _publish_and_find_in_tabs(page, browser, admin_cls, tc, files, type_tab, extra=None) -> None:
    """Editor publishes an Active QCTEST item; it must show under All Media
    AND its own type tab."""
    admin = admin_cls(page)
    title = run_title(tc, "pub")
    ctx, anon = _anon(browser)
    try:
        with allure.step("Create with valid fields, Active Status ticked, and Publish"):
            admin.open_form(ROLE_EDITOR)
            admin.fill_required(title, active=True, files=files)
            for key, val in (extra or {}).items():
                admin.fill(key, val)
            admin.submit_for_review()
            refused = admin.refusal_visible()
            status = admin.status_of(title, ROLE_EDITOR)
        assert not refused, f"validation refused a valid item: {admin.refusal_text()!r}"
        assert status == STATUS_PUBLISHED, f"status is {status!r}, not Published"
        with allure.step("Check the Home Page Media Gallery"):
            shown = probe(anon, title)
            tabs = _gallery_tabs(anon, title) if shown else {}
        assert shown, f"{title!r} is Published + Active but not in the Home Media Gallery"
        assert tabs.get(TAB_ALL), f"{title!r} not under {TAB_ALL!r}: {tabs!r}"
        assert tabs.get(type_tab), f"{title!r} not under {type_tab!r}: {tabs!r}"
    finally:
        _dispose(admin, title)
        _close(ctx)


def _publish_album_with_photo(page, tc, short, cover=None) -> dict:
    """Publishes a QCTEST Photo Album the way the form requires.

    Live 2026-10-13: Submit on a new album is refused with "An album must
    contain at least one published photo". So, as Site Content Editor:
    save the album as Draft, publish one QCTEST Album Photo linked to it by
    exact title, then reopen the album and Submit. Returns what each step
    observed; the caller asserts. Tear down with `_teardown_album()`.

    `cover` overrides the Album Cover Image fixture (TC 133670: a PNG). The
    cover's filename readout right after upload is kept as
    `seen["cover_on_upload"]`."""
    album, photo = ALBUM(page), PHOTO(page)
    title = run_title(tc, short)
    photo_title = f"{title}-photo"
    seen = {"album": album, "photo": photo, "title": title, "photo_title": photo_title}
    with allure.step("Save the QCTEST album as Draft (Active Status ticked)"):
        album.open_form(ROLE_EDITOR)
        album.fill_required(title, active=True, files={"cover_image": cover} if cover else ALBUM_FILES)
        if cover:  # read only for 133670; the P1/P2 path runs as it did live
            seen["cover_on_upload"] = album.value("cover_image")
        album.save_as_draft()
        seen["draft"] = album.status_of(title, ROLE_EDITOR)
    assert seen["draft"] == STATUS_DRAFT, f"precondition: the album draft was not saved ({seen['draft']!r})"
    with allure.step("Publish one QCTEST Album Photo in that album"):
        seen["photo_status"] = photo.create_published_photo(title, photo_title, VALID_JPG, ROLE_EDITOR)
    assert seen["photo_status"] == STATUS_PUBLISHED, (
        f"precondition: the album photo is {seen['photo_status']!r}, not Published"
    )
    with allure.step("Reopen the album and Submit (Editor -> Published)"):
        album.open_list(ROLE_EDITOR)
        album.open_entry_by_edit_link(title)
        # Live 2026-10-13, one run: Submit on the reopened draft was refused
        # with "Album Title (العربية): Arabic content is required" (the next
        # run read the Arabic back intact, so it loads/saves late, not never).
        # The Arabic is saved a moment after the record
        # (OBJECT-AUTHORING-GUIDE), so it is read for evidence and re-entered.
        seen["title_ar_on_reopen"] = album.value("album_title", locale="ar")
        album.fill("album_title", f"{title} AR", locale="ar")
        album.submit_for_review()
        seen["refused"], seen["refusal"] = album.refusal_visible(), album.refusal_text()
        seen["status"] = album.status_of(title, ROLE_EDITOR)
    _attach("album publish outcome", {k: v for k, v in seen.items() if k not in ("album", "photo")})
    return seen


def _teardown_album(seen: dict) -> None:
    """Photo first, then album -- each by exact QCTEST title."""
    out = {
        "photo": _dispose(seen["photo"], seen["photo_title"]),
        "album": _dispose(seen["album"], seen["title"]),
    }
    _attach("teardown", out)


# ---------------------------------------------------------------------------
# Video cases on the object that feeds Home (fix pass 5, 2026-10-14)
# ---------------------------------------------------------------------------
# Live 2026-10-14: the Home Media Gallery reads ONLY the Video Record module
# (/o/qc-video-library-api/videos) and the Photo Album module
# (/o/qc-photo-gallery-api/albums) -- the fragment's own config and source
# comment say so, an anonymous Home load calls nothing else, and every video
# card's ERC is a Video Record entry. Media Item feeds nothing on Home, so the
# video cases (133654 / 133657 / 133666 / 133676) run on Video Record.
# QCTEST video records are never deleted under the opt-in (dispose() keeps and
# logs them); `_take_off_home()` leaves each one Inactive -- or Unpublished
# when Inactive alone does not hide it -- and proves it gone from Home.
VIDEO = HomeVideoRecordAdminPage
VIDEO_FILES = {"thumbnail": VALID_JPG}
MP4_20MB = _fixture("video_20mb.mp4", make_mp4, 20 * ONE_MB)  # TC 133676 names a 20 MB .mp4
TITLE_AR_133661 = "إطلاق الخدمات الرقمية لفرفة قطر"  # TC 133661 precondition, verbatim
EMBED_URL_133677 = "https://www.youtube.com/watch?v=abc123"  # TC 133677 precondition


def _video_record(title: str) -> LiveRecord:
    return LiveRecord(VIDEO.SLUG, title, "disposable QCTEST Video Record")


def _create_video(admin, title: str, tc, active: bool, source: str = VIDEO.SOURCE_EXTERNAL_URL,
                  url: str | None = QCTEST_EMBED_URL, video_file: str | None = None,
                  lookup: str | None = None) -> dict:
    """Editor creates one QCTEST Video Record and clicks Publish (Editor's
    Submit lands on Published). Returns what was observed; the caller asserts."""
    admin.open_form(ROLE_EDITOR)
    # The URL is filled below (or not, for Direct Upload) -- never by fill_required.
    admin.fill_required(title, skip=("video_url",), active=active, files=VIDEO_FILES)
    if source != VIDEO.SOURCE_EXTERNAL_URL:
        admin.fill("video_source_type", source)
    if url:
        admin.fill("video_url", url)
    if video_file:
        admin.upload("video_file", video_file, tag=str(tc))
    log_live_write(_video_record(title), "<create>", title, tc, action="create",
                   note=f"QCTEST Video Record, source={source}, active={active}, Publish as Site Content Editor")
    admin.submit_for_review()  # live-write-guard: disposable QCTEST row
    seen = {"refused": admin.refusal_visible(), "refusal": admin.refusal_text()}
    # `lookup` (default: the title) finds the row -- a title the CMS
    # sanitises on save is stored differently from what was typed (133666).
    seen["status"] = "" if seen["refused"] else admin.status_of(lookup or title, ROLE_EDITOR)
    _attach("create outcome", seen)
    return seen


def _take_off_home(admin, anon, title: str, tc) -> dict:
    """Teardown for a QCTEST video that may be on Home: untick Active Status
    and Publish in place; if the card is STILL on Home, Unpublish the row.
    Proves the result anonymously. Never raises (the test's own result wins)."""
    out = {"title": title}
    try:
        admin.open_list(ROLE_EDITOR)
        if not admin.row_visible(title):
            # Reported loudly (2026-10-14: a sanitised title was looked up by
            # its typed form and the QCTEST video stayed on Home).
            out["row"] = "NOT FOUND -- check Home by hand"
            out["still_on_home"] = probe(anon, title, expect=False)
            _attach("teardown: off Home", out)
            return out
        admin.open_entry_by_edit_link(title)
        if admin.flag("active_status"):
            admin.set_flag("active_status", False)
            log_live_write(_video_record(title), "Active Status", False, tc, action="status",
                           note="teardown: take the QCTEST video off Home (nothing is deleted)")
            admin.submit_for_review()  # live-write-guard: disposable QCTEST row
        out["inactive_hides"] = not probe(anon, title, expect=False)
        if not out["inactive_hides"]:
            log_live_write(_video_record(title), "<workflow>", STATUS_UNPUBLISHED, tc, action="unpublish",
                           note="teardown: Inactive did not hide the QCTEST video from Home")
            admin.open_list(ROLE_EDITOR)
            admin.unpublish_entry(title)
            out["unpublished"] = not probe(anon, title, expect=False)
    except Exception as exc:  # noqa: BLE001 -- reported, never masks the result
        out["error"] = repr(exc)
    _attach("teardown: off Home", out)
    return out


def _still_published(admin, title: str) -> dict:
    """An INACTIVE row shows an `INACTIVE` badge instead of its workflow
    state and offers neither Publish nor Unpublish (live 2026-10-14), so the
    workflow state is read from the row's History: the newest workflow
    transition ("Published", "Unpublished", ...), skipping Deactivated /
    Activated, which are not workflow moves."""
    admin.open_list(ROLE_EDITOR)
    badge = admin.row_status_text(title)
    stored = admin.stored_status(title)
    verbs = admin.history_verbs(title)
    return {
        "badge": badge,
        "stored_status": stored,
        "history": verbs,
        "last_workflow": next((v for v in verbs if v in admin.WORKFLOW_VERBS), ""),
    }


def _api_has(anon, title: str) -> bool:
    """The gallery's own video source, read anonymously (corroboration)."""
    gallery = HomeMediaGalleryPage(anon).open_home()
    return any(title in t for t in gallery.video_api_titles())


# ---------------------------------------------------------------------------
# Fix pass 6 (2026-10-14): the remaining "Create Video" cases on Video Record
# ---------------------------------------------------------------------------
# Every one of these TCs starts "Open Create Video screen", so they run on
# Video Record too. Field mapping: Media Title (EN/AR) -> Video Title + its
# Arabic twin; Thumbnail Image -> Video Thumbnail; Video File / Embed URL ->
# Video Source Type + Video URL (External URL) / Video File (Direct Upload);
# Publication Date -> Published Date.
# Active Status is TICKED by default on this form: every case that does not
# need a Home card saves with it UNTICKED, so an unexpected accept can never
# reach the public gallery. A save is proved by the row existing and its
# History recording the Publish (an INACTIVE row shows no workflow badge).
def _video_refused(page, tc, short: str, what: str, skip: tuple = (), prep=None,
                   lookup=None) -> dict:
    """Editor fills Create Video (Active Status unticked), runs `prep(admin,
    title)` for the field under test, clicks Publish. The case's outcome is
    "Save is blocked ... item is not saved": the form must stay open, and NO
    row may exist afterwards. `lookup` (default: the title) finds the row.
    A refusal without a red bar (native required-field blocking) still
    counts as blocked -- wording / toast differences are not findings."""
    admin = VIDEO(page)
    title = run_title(tc, short)
    find = lookup(title) if lookup else title
    seen = {"title": find}
    try:
        with allure.step(f"Open Create Video and fill every mandatory field except: {what}"):
            admin.open_form(ROLE_EDITOR)
            admin.fill_required(title, skip=tuple(skip), active=False, files=VIDEO_FILES)
            if prep:
                seen["prep"] = prep(admin, title)
        with allure.step("Click Publish (Editor)"):
            log_live_write(_video_record(find), "<create>", find, tc, action="attempt",
                           note=f"expected REFUSED: {what}; Active Status unticked")
            admin.submit_for_review()  # live-write-guard: disposable QCTEST row (expected refused)
            seen["refused"], seen["refusal"] = admin.refusal_visible(), admin.refusal_text()
            seen["form_still_open"] = admin.form_still_open()
        with allure.step("Read the entries list: the record must not exist"):
            admin.open_list(ROLE_EDITOR)
            seen["stored"] = admin.row_visible(find)
            if seen["stored"]:
                seen["row"] = _still_published(admin, find)
        _attach("refusal outcome", seen)
        assert not seen["stored"], (
            f"FINDING -- {what}: the Video Record was SAVED anyway ({seen.get('row')!r}); "
            f"refusal shown: {seen['refusal']!r}"
        )
        assert seen["refused"] or seen["form_still_open"], (
            f"{what}: no row was stored, but the form neither showed a refusal nor stayed open -- "
            f"the Publish click may not have happened"
        )
        return seen
    finally:
        _dispose(admin, find)


def _save_video_and_read_back(admin, title, tc, thumb=VALID_JPG, url=QCTEST_EMBED_URL,
                              date_value=None, active=False) -> dict:
    """Editor: Create Video (Source Type = External URL), Publish, navigate
    away to the entries list, re-open the row's Edit screen and read the
    case's fields back. The caller asserts and takes the record off Home."""
    seen = {}
    skip = ("thumbnail", "video_url") + (("published_date",) if date_value else ())
    with allure.step("Open the Create Video screen and fill it"):
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, skip=skip, active=active, files=VIDEO_FILES)
        admin.upload("thumbnail", thumb, tag=str(tc))
        seen["thumbnail_on_upload"] = admin.value("thumbnail")
        if url:
            admin.fill("video_url", url)
        if date_value:
            admin.fill("published_date", date_value)
            seen["date_typed_held"] = admin.value("published_date")
    with allure.step("Click Publish (Editor)"):
        log_live_write(_video_record(title), "<create>", title, tc, action="create",
                       note=f"QCTEST Video Record, External URL, active={active}, Publish as Site Content Editor")
        admin.submit_for_review()  # live-write-guard: disposable QCTEST row
        seen["refused"], seen["refusal"] = admin.refusal_visible(), admin.refusal_text()
    with allure.step("Navigate away (entries list) and re-open the item's Edit screen"):
        seen["row"] = _still_published(admin, title)
        if seen["row"]["badge"]:
            admin.open_entry_by_edit_link(title)
            seen["thumbnail"] = admin.value("thumbnail")
            seen["video_url"] = admin.value("video_url")
            seen["published_date"] = admin.value("published_date")
            seen["active"] = admin.flag("active_status")
    _attach("save + reopen", seen)
    return seen


def _assert_saved(seen: dict) -> None:
    assert not seen["refused"], f"Save was refused: {seen['refusal']!r}"
    assert seen["row"]["badge"], "no entries-list row after Save -- the item was not saved"
    assert "Published" in seen["row"]["history"], f"the Publish was not recorded (row: {seen['row']!r})"


def _draft_not_on_home(page, browser, tc, short: str) -> None:
    """Editor saves a QCTEST video as Draft with Active Status TICKED; a
    logged-out visitor must not see it in any gallery tab, nor in the
    gallery's video API. Teardown unticks Active Status and saves as Draft
    again (never Submit, which would publish it) and re-checks Home."""
    admin = VIDEO(page)
    title = run_title(tc, short)
    ctx, anon = _anon(browser)
    try:
        with allure.step("Create a video with all valid fields, Active Status = True, and Save as Draft"):
            admin.open_form(ROLE_EDITOR)
            admin.fill_required(title, active=True, files=VIDEO_FILES)
            log_live_write(_video_record(title), "<create>", title, tc, action="save-draft",
                           note="QCTEST Video Record, Active Status ticked, Save as Draft (Site Content Editor)")
            admin.save_as_draft()  # live-write-guard: disposable QCTEST row
            refusal = admin.refusal_text() if admin.refusal_visible() else ""
            status = admin.status_of(title, ROLE_EDITOR)
            stored = admin.stored_status(title)
            admin.open_entry_by_edit_link(title)
            active = admin.flag("active_status")
            _attach("draft saved", {"refusal": refusal, "badge": status, "stored": stored, "active": active})
        assert status == STATUS_DRAFT, f"precondition: the video is {status!r}, not Draft ({refusal!r})"
        assert active, "precondition: Active Status was not saved as True"
        with allure.step("Check every Media Gallery tab on Home (logged-out); corroborate on the video API"):
            shown = probe(anon, title, expect=False)
            in_api = _api_has(anon, title)
            _attach("public evidence", {"in_gallery": shown, "in_video_api": in_api})
        assert not shown, (
            f"FINDING -- {title!r} is Draft (Active Status = True) but is in the Home Media Gallery "
            f"(video API returns it: {in_api})"
        )
        assert not in_api, f"FINDING -- the gallery's video API returns the Draft {title!r} to a visitor"
    finally:
        _deactivate_draft(admin, anon, title, tc)
        _dispose(admin, title)
        _close(ctx)


def _deactivate_draft(admin, anon, title: str, tc) -> dict:
    """Draft teardown: untick Active Status and Save as Draft (the record
    stays Draft); prove it is off Home. Never raises."""
    out = {"title": title}
    try:
        admin.open_list(ROLE_EDITOR)
        if not admin.row_visible(title):
            out["row"] = "NOT FOUND"
        else:
            admin.open_entry_by_edit_link(title)
            if admin.flag("active_status"):
                admin.set_flag("active_status", False)
                log_live_write(_video_record(title), "Active Status", False, tc, action="status",
                               note="teardown: untick Active Status, Save as Draft (nothing is deleted)")
                admin.save_as_draft()  # live-write-guard: disposable QCTEST row
            out["badge"] = admin.status_of(title, ROLE_EDITOR)
        out["still_on_home"] = probe(anon, title, expect=False)
    except Exception as exc:  # noqa: BLE001 -- reported, never masks the result
        out["error"] = repr(exc)
    _attach("teardown: draft deactivated", out)
    return out


# ===========================================================================
# Access / RBAC
# ===========================================================================
@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Site Content Editor can access the Media Center module and publish media items")
@allure.label("pbi", PBI)
@allure.label("testcase", "133646")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_129388
@pytest.mark.tc_133646
@pytest.mark.traceability("MEDIA-GALLERY-TC-133646")
@pytest.mark.timeout(480)
def test_133646_site_content_editor_can_access_media_center(page):
    outcomes = {}
    # Fix pass 6 (2026-10-14): the Create Video screen is Video Record (the
    # gallery's video source); Media Item feeds nothing on Home. Its video
    # source fields are conditional on Video Source Type (live 2026-10-14:
    # no Video URL on a fresh form), so each is checked after picking the
    # source type that shows it. Nothing is saved.
    for name, cls, keys in (("video", VIDEO, ("video_title", "video_source_type", "thumbnail",
                                              "duration", "published_date", "video_category",
                                              "active_status")),
                            ("album", ALBUM, ("album_title", "cover_image", "published_date"))):
        with allure.step(f"Open the Create {name.title()} screen as Site Content Editor"):
            admin = cls(page)
            admin.open_form(ROLE_EDITOR)
            missing = [k for k in keys if not admin.field_present(k)]
            if cls is VIDEO:
                for source, key in ((VIDEO.SOURCE_EXTERNAL_URL, "video_url"),
                                    (VIDEO.SOURCE_DIRECT_UPLOAD, "video_file")):
                    admin.fill("video_source_type", source)
                    if not admin.field_present(key):
                        missing.append(f"{key} (Source Type = {source})")
            outcomes[name] = {"missing": missing, "publish": admin.submit_enabled()}
    _attach("create screens", outcomes)
    for name, out in outcomes.items():
        assert not out["missing"], f"Create {name} screen lacks fields {out['missing']!r}"
        assert out["publish"], f"Create {name} screen offers no enabled Publish action"


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Auth / RBAC")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that forced browsing to the Media Center admin edit screen is blocked for an unauthenticated user")
@allure.label("pbi", PBI)
@allure.label("testcase", "133647")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.security
@pytest.mark.pbi_129388
@pytest.mark.tc_133647
@pytest.mark.traceability("MEDIA-GALLERY-TC-133647")
@pytest.mark.timeout(300)
def test_133647_unauthenticated_forced_browsing_blocked(browser):
    # Fix pass 6 (2026-10-14): the Create Video admin URL is manage-video-record.
    ck.check_anonymous_denied(browser, VIDEO)


# ===========================================================================
# Publication to the Home Page Media Gallery
# ===========================================================================
@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that publishing a video in the Media Center module makes it automatically appear on the Home Page Media Gallery")
@allure.label("pbi", PBI)
@allure.label("testcase", "133654")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129388
@pytest.mark.tc_133654
@pytest.mark.traceability("MEDIA-GALLERY-TC-133654")
@pytest.mark.timeout(480)
def test_133654_published_video_appears_on_home_gallery(page, browser):
    # Fix pass 5 (2026-10-14): retargeted from Media Item (which feeds nothing
    # on Home) to Video Record, the gallery's video source.
    admin = VIDEO(page)
    title = run_title(133654, "pub")
    ctx, anon = _anon(browser)
    try:
        with allure.step("Create a Video Record with valid Title EN/AR, Thumbnail, Video URL, "
                         "Published Date = today, Active = True, and Publish"):
            seen = _create_video(admin, title, 133654, active=True)
        assert not seen["refused"], f"validation refused a valid video: {seen['refusal']!r}"
        assert seen["status"] == STATUS_PUBLISHED, f"status is {seen['status']!r}, not Published"
        with allure.step("Check the Home Page Media Gallery (logged-out visitor)"):
            shown = probe(anon, title)
            tabs = _gallery_tabs(anon, title) if shown else {}
        assert shown, f"{title!r} is Published + Active but not in the Home Media Gallery"
        assert tabs.get(TAB_ALL), f"{title!r} not under {TAB_ALL!r}: {tabs!r}"
        assert tabs.get(TAB_VIDEOS), f"{title!r} not under {TAB_VIDEOS!r}: {tabs!r}"
    finally:
        _take_off_home(admin, anon, title, 133654)
        _dispose(admin, title)
        _close(ctx)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Publish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that publishing an album (with Flickr-imported photos) makes it automatically appear on the Home Page Media Gallery")
@allure.label("pbi", PBI)
@allure.label("testcase", "133655")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129388
@pytest.mark.tc_133655
@pytest.mark.traceability("MEDIA-GALLERY-TC-133655")
@pytest.mark.timeout(300)
def test_133655_published_album_appears_on_home_gallery(page, browser):
    # The album's photo is a QCTEST Album Photo (manage-album-photo), standing
    # in for a Flickr-imported one -- see _publish_album_with_photo().
    ctx, anon = _anon(browser)
    seen = None
    try:
        seen = _publish_album_with_photo(page, 133655, "pub")
        title = seen["title"]
        assert not seen["refused"], f"validation refused a valid album: {seen['refusal']!r}"
        assert seen["status"] == STATUS_PUBLISHED, f"status is {seen['status']!r}, not Published"
        with allure.step("Check the Home Page Media Gallery"):
            shown = probe(anon, title)
            tabs = _gallery_tabs(anon, title) if shown else {}
        assert shown, f"{title!r} is Published + Active but not in the Home Media Gallery"
        assert tabs.get(TAB_ALL), f"{title!r} not under {TAB_ALL!r}: {tabs!r}"
        assert tabs.get(TAB_ALBUMS), f"{title!r} not under {TAB_ALBUMS!r}: {tabs!r}"
    finally:
        if seen:
            _teardown_album(seen)
        else:
            if not deletes_suppressed():
                ALBUM(page).delete_disposable(run_title(133655, "pub"))
        _close(ctx)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Draft")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a video/album saved as Draft does not appear on the Home Page Media Gallery")
@allure.label("pbi", PBI)
@allure.label("testcase", "133656")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129388
@pytest.mark.tc_133656
@pytest.mark.traceability("MEDIA-GALLERY-TC-133656")
@pytest.mark.timeout(600)
def test_133656_draft_item_not_on_home_gallery(page, browser):
    # Fix pass 6 (2026-10-14): on Video Record. Active Status is ticked so
    # only the Draft gate keeps the video off Home.
    _draft_not_on_home(page, browser, 133656, "draft")


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that deactivating (Active Status = False) a previously visible video removes it from the Home Page Media Gallery")
@allure.label("pbi", PBI)
@allure.label("testcase", "133657")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129388
@pytest.mark.tc_133657
@pytest.mark.traceability("MEDIA-GALLERY-TC-133657")
@pytest.mark.timeout(480)
def test_133657_deactivated_video_removed_from_home_gallery(page, browser):
    # Fix pass 5 (2026-10-14): on Video Record (the gallery's video source),
    # and edited IN PLACE -- untick Active, Publish. The old Unpublish-first
    # path would make "gone from Home" pass for the wrong reason (and an
    # Editor submit on an Unpublished record stays Unpublished). "Remained
    # Published" is read from the row's offered actions: an INACTIVE row
    # shows the INACTIVE badge instead of its workflow state.
    admin = VIDEO(page)
    title = run_title(133657, "deact")
    ctx, anon = _anon(browser)
    try:
        with allure.step("Precondition: a Published + Active QCTEST video is visible on Home"):
            seen = _create_video(admin, title, 133657, active=True)
            assert seen["status"] == STATUS_PUBLISHED, f"precondition: not Published ({seen!r})"
            assert probe(anon, title), f"precondition: {title!r} is not visible on Home"
        with allure.step("Edit the video, set Active Status = False, and Publish (in place)"):
            admin.open_list(ROLE_EDITOR)
            admin.open_entry_by_edit_link(title)
            admin.set_flag("active_status", False)
            log_live_write(_video_record(title), "Active Status", False, 133657, action="status",
                           note="the step under test: untick Active Status, Publish in place")
            admin.submit_for_review()  # live-write-guard: disposable QCTEST row
            refusal = admin.refusal_text() if admin.refusal_visible() else ""
            admin.open_list(ROLE_EDITOR)
            admin.open_entry_by_edit_link(title)
            active = admin.flag("active_status")
            row = _still_published(admin, title)
            _attach("after the save", {"refusal": refusal, "active": active, "row": row})
        assert not refusal, f"the save was refused: {refusal!r}"
        assert not active, "Active Status was not saved as False"
        with allure.step("Reload Home and check every gallery tab; corroborate on the gallery's video API"):
            still = probe(anon, title, expect=False)
            in_api = _api_has(anon, title)
            _attach("public evidence", {"in_gallery": still, "in_video_api": in_api})
        assert not still, (
            f"FINDING -- {title!r} has Active Status = False but is still in the Home Media Gallery "
            f"(also returned by /o/qc-video-library-api/videos: {in_api})"
        )
        # Step 2 also expects "video remains Published". Live 2026-10-14 the
        # deactivation is stored as a STATUS change (headless status code 6
        # "incomplete", badge INACTIVE; History: Submitted for review ->
        # Edited -> Deactivated, no Published), not as a flag on a Published
        # record. Checked last, so the Home result above is always reported.
        code = (row.get("stored_status") or {}).get("code")
        assert code == 0, (
            f"FINDING -- after Active Status = False the video does not remain Published: its stored "
            f"workflow status is {row.get('stored_status')!r} (0 = approved/Published), badge "
            f"{row['badge']!r}, History {row['history']!r}. The card IS gone from Home."
        )
    finally:
        _take_off_home(admin, anon, title, 133657)
        _dispose(admin, title)
        _close(ctx)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Unpublish")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that unpublishing a previously visible album removes it from the Home Page Media Gallery")
@allure.label("pbi", PBI)
@allure.label("testcase", "133658")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.regression
@pytest.mark.pbi_129388
@pytest.mark.tc_133658
@pytest.mark.traceability("MEDIA-GALLERY-TC-133658")
@pytest.mark.timeout(300)
def test_133658_unpublished_album_removed_from_home_gallery(page, browser):
    # Local body, not ck.check_unpublish_hides(): an album needs a published
    # photo before it can be published (see _publish_album_with_photo()).
    ctx, anon = _anon(browser)
    seen = None
    try:
        seen = _publish_album_with_photo(page, 133658, "unpub")
        album, title = seen["album"], seen["title"]
        assert seen["status"] == STATUS_PUBLISHED, (
            f"precondition: album is {seen['status']!r}, not Published ({seen['refusal']!r})"
        )
        assert probe(anon, title), f"precondition: {title!r} is not visible after publish"
        with allure.step("Unpublish the album"):
            album.open_list(ROLE_EDITOR)
            album.unpublish_entry(title)
            status = album.status_of(title, ROLE_EDITOR)
        assert status == STATUS_UNPUBLISHED, f"after Unpublish the album is {status!r}"
        assert not probe(anon, title, False), f"{title!r} is Unpublished but still visible to a visitor"
    finally:
        if seen:
            _teardown_album(seen)
        else:
            if not deletes_suppressed():
                ALBUM(page).delete_disposable(run_title(133658, "unpub"))
        _close(ctx)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Flickr albums")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that album photos can only be managed through the Flickr-integrated import flow, not a generic upload control")
@allure.label("pbi", PBI)
@allure.label("testcase", "133659")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.regression
@pytest.mark.pbi_129388
@pytest.mark.tc_133659
@pytest.mark.traceability("MEDIA-GALLERY-TC-133659")
@pytest.mark.timeout(300)
def test_133659_album_photos_only_via_flickr_import(page):
    admin = ALBUM(page)
    with allure.step("Open the Create Album screen as Site Content Editor"):
        admin.open_form(ROLE_EDITOR)
    with allure.step("Inspect the attachment / upload controls"):
        labels = admin.attachment_field_labels()
        raw = admin.raw_file_inputs()
        _attach("attachment controls", {"labels": labels, "raw_file_inputs": raw})
    photo_uploads = [lbl for lbl in labels if "photo" in lbl.casefold()]
    assert not photo_uploads, f"a generic photo upload control is on the Album form: {photo_uploads!r}"
    assert raw == 0, f"{raw} raw drag-and-drop file input(s) are rendered on the Album form"


# ===========================================================================
# Field validation (Video Record -- fix pass 6)
# ===========================================================================
@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that Media Title (EN) cannot be left empty")
@allure.label("pbi", PBI)
@allure.label("testcase", "133661")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133661
@pytest.mark.traceability("MEDIA-GALLERY-TC-133661")
@pytest.mark.timeout(480)
def test_133661_media_title_en_required(page):
    # Fix pass 6 (2026-10-14): Media Title (EN) -> Video Record "Video Title".
    # The Arabic carries the case's text, prefixed with the run's QCTEST
    # title so the entries list can be searched for a wrongly saved row.
    def _prep(admin, title):
        admin.fill("video_title", f"{title} {TITLE_AR_133661}", locale="ar")
        admin.fill("video_url", QCTEST_EMBED_URL)
        return {"en": admin.value("video_title"), "ar": admin.value("video_title", locale="ar")}

    _video_refused(page, 133661, "en-empty", "Video Title (EN) left empty", skip=("video_title", "video_url"),
                   prep=_prep, lookup=lambda t: f"{t} {TITLE_AR_133661}")


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Verify that Media Title (AR) cannot be left empty")
@allure.label("pbi", PBI)
@allure.label("testcase", "133662")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133662
@pytest.mark.traceability("MEDIA-GALLERY-TC-133662")
@pytest.mark.timeout(480)
def test_133662_media_title_ar_required(page):
    # Fix pass 6 (2026-10-14): Media Title (AR) -> the Arabic twin of Video
    # Title. Before this pass the case left the EN side empty (a copy of 133661).
    def _prep(admin, title):
        admin.fill("video_title", title)
        admin.fill("video_url", QCTEST_EMBED_URL)
        return {"en": admin.value("video_title"), "ar": admin.value("video_title", locale="ar")}

    _video_refused(page, 133662, "ar-empty", "Video Title (AR) left empty", skip=("video_title", "video_url"),
                   prep=_prep)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Security")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that special/script-tag characters entered in Media Title (EN) are handled safely")
@allure.label("pbi", PBI)
@allure.label("testcase", "133666")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.security
@pytest.mark.pbi_129388
@pytest.mark.tc_133666
@pytest.mark.traceability("MEDIA-GALLERY-TC-133666")
@pytest.mark.timeout(480)
def test_133666_script_tag_in_media_title_handled_safely(page, browser):
    # Fix pass 5 (2026-10-14): the "Create Video screen" is Video Record (the
    # gallery's video source); on Media Item the card could never reach Home.
    # Live 2026-10-14 the CMS SANITISES the title on save -- the tags are
    # stripped ("QCTEST-133666-<uid><script>alert(1)</script>" is stored as
    # "QCTEST-133666-<uid>alert(1)") -- which is the case's "saves with the
    # value safely sanitised" branch. Every lookup therefore uses the unique
    # run prefix, never the typed title.
    admin = VIDEO(page)
    prefix = run_title(133666, "")  # "QCTEST-133666-" (+ a run uid under the opt-in)
    payload = "<script>alert(1)</script>"
    title = prefix + payload
    ctx, anon = _anon(browser)
    dialogs = []
    anon.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    try:
        with allure.step("Enter the script-tag string in Title EN, fill the rest, and Save"):
            seen = _create_video(admin, title, 133666, active=True, lookup=prefix)
        if seen["refused"]:
            return  # the case's second accepted branch: blocked with a validation error
        assert seen["status"] == STATUS_PUBLISHED, (
            f"saved but not Published ({seen['status']!r}) -- cannot inspect the card"
        )
        with allure.step("Read the stored title"):
            admin.open_list(ROLE_EDITOR)
            stored = next((t for t, _ in admin.row_statuses() if t.startswith(prefix)), "")
            _attach("stored title", stored)
        with allure.step("View the item's card on the Home Page Media Gallery"):
            # The card must be on Home at all before its rendering can be judged.
            card = probe(anon, prefix)
            gallery = HomeMediaGalleryPage(anon)
            gallery.click_tab(TAB_ALL)  # probe() leaves the LAST tab (Albums) selected
            card_title = next((t for t in gallery.card_titles() if t.startswith(prefix)), "") if card else ""
            card_html = gallery.card_html(prefix) if card else ""
            _attach("card", {"title": card_title, "html": card_html[:800], "dialogs": dialogs})
        assert card, f"{stored!r} is Published + Active but its card is not in the Home Media Gallery"
        assert not dialogs, f"a script executed on the Home page: {dialogs!r}"
        assert "<script" not in card_html.lower(), "a <script> element was rendered inside the card"
        assert card_title in (stored, title), (
            f"the card title {card_title!r} is neither the sanitised stored title {stored!r} "
            f"nor the escaped typed text {title!r}"
        )
    finally:
        _take_off_home(admin, anon, prefix, 133666)
        _dispose(admin, prefix)
        _close(ctx)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a video/album cannot be saved without a Thumbnail Image")
@allure.label("pbi", PBI)
@allure.label("testcase", "133671")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133671
@pytest.mark.traceability("MEDIA-GALLERY-TC-133671")
@pytest.mark.timeout(480)
def test_133671_thumbnail_required(page):
    # Fix pass 6 (2026-10-14): Thumbnail Image -> Video Record "Video Thumbnail".
    _video_refused(page, 133671, "nothumb", "Video Thumbnail left empty", skip=("thumbnail",))


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid file type is rejected for Thumbnail Image")
@allure.label("pbi", PBI)
@allure.label("testcase", "133672")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133672
@pytest.mark.traceability("MEDIA-GALLERY-TC-133672")
@pytest.mark.timeout(300)
def test_133672_thumbnail_invalid_type_rejected(page):
    # Fix pass 6 (2026-10-14): Video Record "Video Thumbnail". Nothing is
    # saved: the form is filled with Active Status unticked and never submitted.
    ck.check_file_refused(page, VIDEO, 133672, "thumbnail", BAD_PDF)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a thumbnail file exceeding 2MB is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "133674")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133674
@pytest.mark.traceability("MEDIA-GALLERY-TC-133674")
@pytest.mark.timeout(300)
def test_133674_thumbnail_oversize_rejected(page):
    # 2.1 MB sits inside the project's 3 MB tolerance; 3.1 MB is the assertion.
    # Fix pass 6 (2026-10-14): Video Record "Video Thumbnail".
    ck.check_file_refused(page, VIDEO, 133674, "thumbnail", BIG_JPG)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Video item saves successfully when only a Video File is uploaded (no Embed URL)")
@allure.label("pbi", PBI)
@allure.label("testcase", "133676")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133676
@pytest.mark.traceability("MEDIA-GALLERY-TC-133676")
@pytest.mark.timeout(480)
def test_133676_video_file_only_saves(page):
    # Fix pass 5 (2026-10-14): Media Item has no Video File upload (one text
    # field "Video File / Embed URL"); the Create Video screen with a real
    # Video File upload is Video Record, Video Source Type = Direct Upload
    # (Video URL then hidden and empty). The 20 MB .mp4 the case names is
    # used. Saved with Active Status UNTICKED so the QCTEST video never
    # reaches Home; "saved" is proved by the row existing, offering the
    # Published-state actions, and the stored Video File read back.
    admin = VIDEO(page)
    title = run_title(133676, "ok")
    try:
        with allure.step("Open Create Video, Source Type = Direct Upload, upload a valid .mp4, leave Video URL empty"):
            seen = _create_video(admin, title, 133676, active=False, source=VIDEO.SOURCE_DIRECT_UPLOAD,
                                 url=None, video_file=MP4_20MB)
        assert not seen["refused"], f"Save was refused: {seen['refusal']!r}"
        with allure.step("Reopen the saved record"):
            row = _still_published(admin, title)
            admin.open_entry_by_edit_link(title)
            stored = {"video_file": admin.value("video_file"), "video_url": admin.value("video_url"),
                      "source": admin.value("video_source_type")}
            _attach("read back", {"row": row, **stored})
        assert row["badge"], f"no entries-list row for {title!r} after Save"
        assert stored["video_file"], "the Video File was not stored"
        assert not stored["video_url"], f"Video URL is not empty: {stored['video_url']!r}"
        # Saved with Active Status unticked: the History records the Publish
        # (Created -> Published -> Deactivated, live 2026-10-14).
        assert "Published" in row["history"], f"the Publish was not recorded (row: {row!r})"
    finally:
        _dispose(admin, title)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Video item saves successfully when only an Embed URL is provided (no Video File)")
@allure.label("pbi", PBI)
@allure.label("testcase", "133677")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133677
@pytest.mark.traceability("MEDIA-GALLERY-TC-133677")
@pytest.mark.timeout(300)
def test_133677_embed_url_only_saves(page):
    # Fix pass 6 (2026-10-14): Video Record, Source Type = External URL with
    # the case's URL, no Video File. Active Status unticked (no Home card needed).
    admin = VIDEO(page)
    title = run_title(133677, "url")
    try:
        seen = _save_video_and_read_back(admin, title, 133677, url=EMBED_URL_133677)
        if seen["row"]["badge"]:
            seen["source"] = admin.value("video_source_type")
            seen["video_file"] = admin.value("video_file") if admin.field_present("video_file") else ""
        _attach("read back", seen)
        _assert_saved(seen)
        assert seen.get("video_url") == EMBED_URL_133677, f"stored Video URL is {seen.get('video_url')!r}"
        assert seen.get("source") == VIDEO.SOURCE_EXTERNAL_URL, f"stored Source Type is {seen.get('source')!r}"
        assert not seen.get("video_file"), f"a Video File is stored: {seen.get('video_file')!r}"
    finally:
        _dispose(admin, title)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a Video item cannot be saved with neither Video File nor Embed URL provided")
@allure.label("pbi", PBI)
@allure.label("testcase", "133678")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133678
@pytest.mark.traceability("MEDIA-GALLERY-TC-133678")
@pytest.mark.timeout(480)
def test_133678_video_needs_file_or_embed_url(page):
    # Fix pass 6 (2026-10-14): Video Record. Neither source is given under
    # either source type: External URL with Video URL empty, and Direct
    # Upload with no Video File. Both saves must be refused.
    _video_refused(page, 133678, "nourl", "Source Type = External URL with Video URL empty",
                   skip=("video_url",))

    def _direct_upload(admin, title):
        admin.fill("video_source_type", VIDEO.SOURCE_DIRECT_UPLOAD)
        return {"source": admin.value("video_source_type"), "video_url": admin.value("video_url")}

    _video_refused(page, 133678, "nofile", "Source Type = Direct Upload with no Video File",
                   skip=("video_url",), prep=_direct_upload)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the Video File/Embed URL field is not required for an Album-type item")
@allure.label("pbi", PBI)
@allure.label("testcase", "133680")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133680
@pytest.mark.traceability("MEDIA-GALLERY-TC-133680")
@pytest.mark.timeout(300)
def test_133680_video_source_not_required_for_album(page):
    admin = ALBUM(page)
    with allure.step("Open the Create Album screen and inspect the Video File/Embed URL control"):
        admin.open_form(ROLE_EDITOR)
        present = admin.field_present("video_embed")
        required = admin.field_required("video_embed") if present else False
        _attach("video control on album form", {"present": present, "required": required})
    assert not required, "Video File/Embed URL is enforced as mandatory on the Album form"
    seen = None
    try:
        with allure.step("Fill all album-mandatory fields (no video source) and Save"):
            seen = _publish_album_with_photo(page, 133680, "ok")
        assert not seen["refused"], f"Save was refused: {seen['refusal']!r}"
        assert seen["status"] == STATUS_PUBLISHED, f"album status is {seen['status']!r} after Save"
    finally:
        if seen:
            _teardown_album(seen)
        else:
            if not deletes_suppressed():
                ALBUM(page).delete_disposable(run_title(133680, "ok"))


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a video/album cannot be saved without a Publication Date")
@allure.label("pbi", PBI)
@allure.label("testcase", "133684")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133684
@pytest.mark.traceability("MEDIA-GALLERY-TC-133684")
@pytest.mark.timeout(480)
def test_133684_publication_date_required(page):
    # Fix pass 6 (2026-10-14): Publication Date -> Video Record "Published
    # Date" (native date input). It is cleared explicitly, and the test
    # proves it is empty, so a form-side default cannot fill it.
    def _clear_date(admin, title):
        admin.fill("published_date", "")
        held = admin.value("published_date")
        assert not held, f"precondition: Published Date could not be cleared (holds {held!r})"
        return {"published_date": held}

    _video_refused(page, 133684, "nodate", "Published Date left empty", skip=("published_date",),
                   prep=_clear_date)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Draft")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an item with Active Status = True but still in Draft/Pending Review does not appear in the Media Gallery")
@allure.label("pbi", PBI)
@allure.label("testcase", "133688")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.workflow
@pytest.mark.pbi_129388
@pytest.mark.tc_133688
@pytest.mark.traceability("MEDIA-GALLERY-TC-133688")
@pytest.mark.timeout(600)
def test_133688_active_draft_not_in_gallery(page, browser):
    # Fix pass 6 (2026-10-14): on Video Record. Saved as Draft with Active
    # Status = True; only the Published gate differs.
    _draft_not_on_home(page, browser, 133688, "actdraft")


# ===========================================================================
# P3/P4 batch -- 8 cases from .claude/qa-runs/phase3-20261012/129388.p34.todo.json
# Scripted OFFLINE 2026-10-13 (no browser). Not yet executed.
# ===========================================================================
def _uploaded_token(filename: str) -> str:
    """The unique part of a QCTEST upload's name (disposable_copy() appends
    10 hex chars); it survives the lower-casing of a D&M friendly URL."""
    m = re.search(r"([0-9a-f]{10})\.[A-Za-z0-9]+$", filename or "")
    return m.group(1) if m else Path(filename or "").stem


def _parse_date(raw: str):
    """A date control's read-back as a `date`, whatever format it renders
    (ISO from a native input, or the picker's MM/DD/YYYY)."""
    from datetime import datetime

    text = (raw or "").strip()[:10]
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _card_image_on_home(anon, title: str) -> str:
    """Image URL of the gallery card titled `title`, from whichever tab shows
    it (fresh Home load, logged-out context). "" when no card is found."""
    gallery = HomeMediaGalleryPage(anon).open_home().scroll_to_section()
    for tab in [t.strip() for t in gallery.tab_texts()] or [TAB_ALL]:
        try:
            gallery.click_tab(tab)
        except Exception:  # noqa: BLE001 -- single-tab section
            pass
        card = gallery.card_locator_by_title(title)
        if card.count():
            return gallery.card_image_src(card.first)
    return ""


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid JPG thumbnail under 2MB uploads and saves successfully")
@allure.label("pbi", PBI)
@allure.label("testcase", "133669")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129388
@pytest.mark.tc_133669
@pytest.mark.traceability("MEDIA-GALLERY-TC-133669")
@pytest.mark.timeout(480)
def test_133669_jpg_thumbnail_under_2mb_saves(page):
    # Fix pass 6 (2026-10-14): Video Record "Video Thumbnail", 1 MB JPG.
    # Active Status unticked (no Home card needed).
    admin = VIDEO(page)
    title = run_title(133669, "jpg")
    try:
        seen = _save_video_and_read_back(admin, title, 133669, thumb=JPG_1MB)
        assert seen["thumbnail_on_upload"], "the 1 MB JPG did not upload: the Video Thumbnail shows no file"
        _assert_saved(seen)
        assert seen.get("thumbnail") == seen["thumbnail_on_upload"], (
            f"stored thumbnail {seen.get('thumbnail')!r} is not the uploaded JPG {seen['thumbnail_on_upload']!r}"
        )
    finally:
        _dispose(admin, title)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that a valid PNG thumbnail under 2MB uploads and saves successfully")
@allure.label("pbi", PBI)
@allure.label("testcase", "133670")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129388
@pytest.mark.tc_133670
@pytest.mark.traceability("MEDIA-GALLERY-TC-133670")
@pytest.mark.timeout(480)
def test_133670_png_thumbnail_under_2mb_saves(page):
    # Create ALBUM: the album's thumbnail is the Photo Album object's
    # "Album Cover Image" (cover_image). Save = Submit as Editor, which needs
    # one published QCTEST Album Photo first (_publish_album_with_photo).
    # Per-run title: a leftover Published "QCTEST-133670-png" from an earlier
    # run whose teardown failed made status_of() read THAT row ("the album
    # draft was not saved ('Published')", 2026-10-13). Rows are found by
    # exact title, so a fixed title is only safe when nothing was left behind.
    import uuid

    short = f"png-{uuid.uuid4().hex[:6]}"
    seen = None
    try:
        seen = _publish_album_with_photo(page, 133670, short, cover=PNG_1MB)
        album, title = seen["album"], seen["title"]
        with allure.step("Re-open the album and read the stored cover"):
            album.open_list(ROLE_EDITOR)
            album.open_entry_by_edit_link(title)
            stored = album.value("cover_image")
        _attach("cover", {"on_upload": seen["cover_on_upload"], "stored": stored})
        assert seen["cover_on_upload"].lower().endswith(".png"), (
            f"the 1 MB PNG did not upload: the cover shows {seen['cover_on_upload']!r}"
        )
        assert not seen["refused"], f"Save was refused: {seen['refusal']!r}"
        assert seen["status"] == STATUS_PUBLISHED, f"album status is {seen['status']!r} after Save"
        assert stored == seen["cover_on_upload"], f"stored cover {stored!r} is not the uploaded PNG"
    finally:
        if seen:
            _teardown_album(seen)
        else:
            if not deletes_suppressed():
                ALBUM(page).delete_disposable(run_title(133670, short))


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Thumbnail Image persists after save and reload")
@allure.label("pbi", PBI)
@allure.label("testcase", "133675")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129388
@pytest.mark.tc_133675
@pytest.mark.traceability("MEDIA-GALLERY-TC-133675")
@pytest.mark.timeout(900)
def test_133675_thumbnail_persists_after_reload(page, browser):
    # Fix pass 6 (2026-10-14): Video Record. The case checks the Home card
    # too, so this video is Active; `_take_off_home()` leaves it Inactive.
    admin = VIDEO(page)
    title = run_title(133675, "thumb")
    ctx, anon = _anon(browser)
    try:
        seen = _save_video_and_read_back(admin, title, 133675, thumb=JPG_1MB, active=True)
        _assert_saved(seen)
        assert seen["thumbnail_on_upload"], "precondition: the JPG thumbnail did not upload"
        assert seen.get("thumbnail") == seen["thumbnail_on_upload"], (
            f"Edit screen shows {seen.get('thumbnail')!r}, not the saved {seen['thumbnail_on_upload']!r}"
        )
        with allure.step("Check the item's card image on the Home Page Media Gallery"):
            shown = probe(anon, title)
            src = _card_image_on_home(anon, title) if shown else ""
            token = _uploaded_token(seen["thumbnail_on_upload"])
            _attach("home card image", {"src": src, "expected token": token})
        assert shown, f"{title!r} is Published + Active but not in the Home Media Gallery"
        assert token and token.lower() in src.lower(), (
            f"the Home card image {src!r} is not the saved thumbnail ({token!r})"
        )
    finally:
        _take_off_home(admin, anon, title, 133675)
        _dispose(admin, title)
        _close(ctx)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the system's handling when both Video File and Embed URL are provided together")
@allure.label("pbi", PBI)
@allure.label("testcase", "133679")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.pbi_129388
@pytest.mark.tc_133679
@pytest.mark.traceability("MEDIA-GALLERY-TC-133679")
@pytest.mark.timeout(480)
def test_133679_video_file_and_embed_url_together(page):
    # Fix pass 6 (2026-10-14): Video Record. Its "Video Source Type" picklist
    # names ONE source; the case's "both" is reached by entering a Video URL
    # (External URL), then switching to Direct Upload and uploading an .mp4.
    # Pass = blocked with a message, or saved with ONE defined source whose
    # field is stored. Active Status unticked (no Home card needed).
    admin = VIDEO(page)
    title = run_title(133679, "both")
    seen = {}
    try:
        with allure.step("Enter a valid Video URL AND upload a valid Video File, fill the rest"):
            admin.open_form(ROLE_EDITOR)
            admin.fill_required(title, skip=("video_url",), active=False, files=VIDEO_FILES)
            admin.fill("video_url", QCTEST_EMBED_URL)
            admin.fill("video_source_type", VIDEO.SOURCE_DIRECT_UPLOAD)
            admin.upload("video_file", VALID_MP4, tag="133679")
            seen["before_save"] = {"source": admin.value("video_source_type"),
                                   "video_url": admin.value("video_url"),
                                   "video_file": admin.value("video_file")}
        with allure.step("Click Publish (Editor)"):
            log_live_write(_video_record(title), "<create>", title, 133679, action="create",
                           note="QCTEST Video Record, URL then Direct Upload file, Active Status unticked")
            admin.submit_for_review()  # live-write-guard: disposable QCTEST row
            seen["refused"], seen["refusal"] = admin.refusal_visible(), admin.refusal_text()
        with allure.step("Re-open the record and read which source was stored"):
            seen["row"] = _still_published(admin, title)
            if seen["row"]["badge"]:
                admin.open_entry_by_edit_link(title)
                seen["stored"] = {"source": admin.value("video_source_type"),
                                  "video_url": admin.value("video_url"),
                                  "video_file": admin.value("video_file") if admin.field_present("video_file")
                                  else ""}
        _attach("outcome", seen)
        if seen["refused"]:
            assert seen["refusal"].strip(), "the save was blocked without a clear validation message"
            assert not seen["row"]["badge"], f"the save was 'blocked' yet a row exists: {seen['row']!r}"
            return
        _assert_saved(seen)
        stored = seen.get("stored", {})
        source = stored.get("source", "")
        assert source in (VIDEO.SOURCE_DIRECT_UPLOAD, VIDEO.SOURCE_EXTERNAL_URL), (
            f"FINDING -- saved with no defined Video Source Type: {stored!r}"
        )
        used = stored.get("video_file") if source == VIDEO.SOURCE_DIRECT_UPLOAD else stored.get("video_url")
        assert used, f"FINDING -- Source Type is {source!r} but that source's value is not stored: {stored!r}"
    finally:
        _dispose(admin, title)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an invalid Embed URL format is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "133681")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129388
@pytest.mark.tc_133681
@pytest.mark.traceability("MEDIA-GALLERY-TC-133681")
@pytest.mark.timeout(480)
def test_133681_invalid_embed_url_rejected(page):
    # Fix pass 6 (2026-10-14): Video Record, Source Type = External URL,
    # Video URL = `notaurl`. The refusal text is not matched (wording
    # differences are not defects on this project); nothing may be stored.
    def _bad_url(admin, title):
        admin.fill("video_url", "notaurl")
        return {"video_url": admin.value("video_url")}

    _video_refused(page, 133681, "badurl", "Video URL = 'notaurl'", skip=("video_url",), prep=_bad_url)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Video source")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the Video File/Embed URL value persists after save and reload")
@allure.label("pbi", PBI)
@allure.label("testcase", "133682")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129388
@pytest.mark.tc_133682
@pytest.mark.traceability("MEDIA-GALLERY-TC-133682")
@pytest.mark.timeout(480)
def test_133682_embed_url_persists_after_reload(page):
    # Fix pass 6 (2026-10-14): Video Record "Video URL" (Source Type =
    # External URL). Active Status unticked (no Home card needed).
    admin = VIDEO(page)
    title = run_title(133682, "embed")
    try:
        seen = _save_video_and_read_back(admin, title, 133682)
        _assert_saved(seen)
        assert seen.get("video_url") == QCTEST_EMBED_URL, (
            f"Video URL after reload is {seen.get('video_url')!r}, not {QCTEST_EMBED_URL!r}"
        )
    finally:
        _dispose(admin, title)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a valid Publication Date is accepted and saved")
@allure.label("pbi", PBI)
@allure.label("testcase", "133683")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133683
@pytest.mark.traceability("MEDIA-GALLERY-TC-133683")
@pytest.mark.timeout(480)
def test_133683_valid_publication_date_saved(page):
    # Fix pass 6 (2026-10-14): Video Record "Published Date" (native date
    # input; MM/DD/YYYY is converted to ISO by the page object). The case's
    # 18/04/2026 is compared as a date. Active Status unticked.
    from datetime import date as _date

    admin = VIDEO(page)
    title = run_title(133683, "date")
    expected = _date(2026, 4, 18)
    try:
        seen = _save_video_and_read_back(admin, title, 133683, date_value=expected.strftime("%m/%d/%Y"))
        _assert_saved(seen)
        stored = _parse_date(seen.get("published_date", ""))
        assert stored == expected, f"Published Date stored as {seen.get('published_date')!r}, not 18 Apr 2026"
    finally:
        _dispose(admin, title)


@allure.epic("Home")
@allure.feature("Media Gallery — Control Panel")
@allure.story("Field validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that an invalid Publication Date format is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "133685")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_129388
@pytest.mark.tc_133685
@pytest.mark.traceability("MEDIA-GALLERY-TC-133685")
@pytest.mark.timeout(480)
def test_133685_invalid_publication_date_rejected(page):
    # Fix pass 6 (2026-10-14): Video Record "Published Date" (native date
    # input). It is cleared first, then 32/13/2026 is typed: a native input
    # that will not hold it is recorded. The pass rests on the save being
    # blocked with nothing stored.
    def _bad_date(admin, title):
        admin.fill("published_date", "")
        try:
            admin.fill("published_date", "32/13/2026")
            typed = "accepted by the input"
        except Exception as exc:  # noqa: BLE001 -- the input refused the text
            typed = f"refused by the input: {str(exc).splitlines()[0]}"
        return {"typed": typed, "field holds": admin.value("published_date")}

    _video_refused(page, 133685, "baddate", "Published Date = 32/13/2026", skip=("published_date",),
                   prep=_bad_date)

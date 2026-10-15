"""
cms/tests/photo_gallery/photo_support.py — per-photo helpers shared by the two
Photo Gallery Control_Panel modules (test layer; no raw Playwright).

Since ADO 148169 (deployed 2026-10-12) an album's photos are "Album Photo"
records (manage-album-photo?qcParent=<albumId>). Consequences for every case:
  - an album is published only with >= 1 published photo
    ("An album must contain at least one published photo."), so a "published
    album" precondition = draft album (with cover) + one published photo +
    Publish on the album;
  - an album that still has photos cannot be deleted ("This Photo Album is used
    by N Album Photos ..."), so teardown unpublishes albums, deletes their
    (titled, captured) photos, then the album; anything refused by that rule
    is LEFT unpublished and reported, never forced.
  - choosing a Flickr Source Folder now IMPORTS that folder's photos as Draft
    photos into the album, so albums here no longer pick one.
"""

from __future__ import annotations

import os

import allure

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.photo_gallery.album_photo_admin_page import AlbumPhotoAdminPage
from cms.pages.photo_gallery.event_category_admin_page import EventCategoryAdminPage
from cms.pages.photo_gallery.gallery_admin_base import GalleryEntry
from cms.pages.photo_gallery.photo_album_admin_page import PhotoAlbumAdminPage

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
PHOTO_JPG = os.path.join(FIXTURES, "pa_qctest_photo_a.jpg")
PHOTO_JPG_B = os.path.join(FIXTURES, "p_qctest_photo_b.jpg")
PHOTO_JPG_C = os.path.join(FIXTURES, "p_qctest_photo_c.jpg")
PHOTO_BMP = os.path.join(FIXTURES, "p_qctest_photo.bmp")
PHOTO_SLUG = "album-photo"


class PhotoRegistry:
    """Records a test created (captured identity) + each photo's album id."""

    def __init__(self, prefix: str):
        self.prefix = prefix
        self._entries: dict[tuple[str, str], GalleryEntry] = {}
        self.parents: dict[str, str] = {}
        self.untracked: list[str] = []  # photos that cannot be captured by title (blank title)

    @property
    def entries(self) -> list[GalleryEntry]:
        order = {PHOTO_SLUG: 0, "photo-album": 1}
        return sorted(self._entries.values(), key=lambda e: order.get(e.slug, 2))

    def track(self, entry: GalleryEntry, parent_id: str = "") -> GalleryEntry:
        if not entry.in_namespace() or not entry.title.startswith(self.prefix):
            raise ValueError(f"{entry} is not a {self.prefix} record")
        self._entries[(entry.slug, entry.entry_id)] = entry
        if parent_id:
            self.parents[entry.entry_id] = str(parent_id)
        return entry

    def forget(self, entry: GalleryEntry) -> None:
        self._entries.pop((entry.slug, entry.entry_id), None)


def photo_page(admin, album_id: str) -> AlbumPhotoAdminPage:
    photos = AlbumPhotoAdminPage(admin.page, admin.prefix, admin.evidence_dir, parent_id=str(album_id))
    photos.pinned_role = admin.pinned_role
    return photos


def photo_data(title: str | None, file: str = PHOTO_JPG, **overrides) -> dict:
    data = {"file": file, "file_stem": "qctest-130714-photo", "title": title,
            "title_ar": (f"صورة اختبار {title[-12:]}" if title else None)}
    data.update(overrides)
    return data


def add_photo(admin, registry: PhotoRegistry, album_id: str, data: dict, publish: bool = True,
              fill=None) -> dict:
    """Opens the album's '+ Add photo', fills it (`fill(photos)` or fill_photo(data)),
    clicks Publish / Save as Draft. Registers the captured photo (titled ones).
    Returns {went_through, entry, new_rows, evidence, messages, before, photos}."""
    photos = photo_page(admin, album_id)
    before = photos.stored_photo_ids()
    result = {"went_through": False, "entry": None, "new_rows": [], "evidence": {}, "messages": "",
              "before": before, "photos": photos, "form": {}}
    title = data.get("title") or ""
    try:
        photos.open_add_form()
        result["form"] = photos.read_photo()
        (fill or (lambda p: p.fill_photo(data)))(photos)
        photos.click_publish() if publish else photos.click_save_as_draft()
        result["went_through"] = photos.save_went_through()
        result["evidence"] = photos.refusal_evidence()
        result["messages"] = photos.all_messages_text()
        photos.evidence(f"photo {title[:60] or 'untitled'} after {'publish' if publish else 'draft'}")
    finally:
        try:
            result["new_rows"] = photos.new_rows(before)
            if title.startswith(registry.prefix) and result["new_rows"]:
                entry = photos.identify_new_photo(title, before)
                if entry:
                    result["entry"] = registry.track(entry, album_id)
            captured = result["entry"].entry_id if result["entry"] else ""
            registry.untracked += [f"{r['entry_id']} ({r['title'][:60]!r}) in album {album_id}"
                                   for r in result["new_rows"] if r["entry_id"] != captured]
        except Exception as exc:  # noqa: BLE001 — registration must not mask the result
            allure.attach(repr(exc), name="photo registration failed")
    allure.attach(repr({k: v for k, v in result.items() if k != "photos"}), name=f"add photo {title[:60]!r}")
    return result


def publish_album(albums: PhotoAlbumAdminPage, entry: GalleryEntry) -> dict:
    """Publish (role's submit button) on an existing album's edit form."""
    albums.open_entry_en(entry.code)
    out_pre = {}
    if not albums.ar_value(albums.TITLE_KEY):
        # qcdev 2026-10-15 (NEW issue, reported): a new record's Arabic title is
        # sometimes not kept ("...Arabic content could not be matched to it. Open
        # Edit on the new record and enter the Arabic again."). Follow that
        # instruction so the publish rule under test is what gets exercised.
        albums.fill_ar(albums.TITLE_KEY, f"ألبوم اختبار {entry.title[-12:]}")
        out_pre["arabic_re_entered"] = True
    albums.click_publish()
    out = {"went_through": albums.save_went_through(), "messages": albums.all_messages_text(),
           "evidence": albums.refusal_evidence(), **out_pre}
    albums.open_list_all()
    out["status"] = albums.row_status(entry)
    return out


def cleanup(page, prefix: str, evidence_dir: str, entries: list[GalleryEntry], parents: dict[str, str],
            role: str, login) -> tuple[list[str], list[str]]:
    """Teardown for photo-gallery records (one signed-in Editor context).
    `login(admin)` must sign `admin` in and return True. Returns (outcome, failures)."""
    outcome, failures = [], []
    albums = PhotoAlbumAdminPage(page, prefix, evidence_dir)
    if not login(albums):
        return outcome, ["teardown could not sign in as the Site Content Editor"]
    albums.pinned_role = role
    categories = EventCategoryAdminPage(page, prefix, evidence_dir)
    categories.pinned_role = role
    # 1. unpublish our published albums (a published album's last photo cannot be deleted)
    for entry in [e for e in entries if e.slug == albums.slug]:
        try:
            albums.open_list_all()
            albums.adopt(entry)
            if albums.row_present(entry) and "unpublish" in albums.row_actions(entry):
                albums.run_row_action(entry, "unpublish")
                outcome.append(f"unpublished album {entry.title}")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"unpublish {entry.title}: {exc!r}")
    for entry in entries:
        label = f"{entry.slug} {entry.title[:90]} (id {entry.entry_id}, code {entry.code})"
        if entry.slug == PHOTO_SLUG:
            cleaner = AlbumPhotoAdminPage(page, prefix, evidence_dir, parent_id=parents.get(entry.entry_id, ""))
            cleaner.pinned_role = role
        else:
            cleaner = albums if entry.slug == albums.slug else categories
        try:
            cleaner.open_list_all()
            if not cleaner.row_present(entry):
                (outcome if cleaner.is_list_fully_expanded() else failures).append(
                    f"already gone: {label}" if cleaner.is_list_fully_expanded()
                    else f"{label}: not found and the list is NOT fully expanded")
                continue
            cleaner.adopt(entry)
            if cleaner.delete_own_entry(entry):
                outcome.append(f"removed (to Recycle Bin) {label}")
                continue
            refusal = " ".join(cleaner.last_delete_messages)
            if "is used by" in refusal or "does not allow deletes" in refusal:
                cleaner.open_list_all()
                if "unpublish" in cleaner.row_actions(entry):
                    cleaner.run_row_action(entry, "unpublish")
                    cleaner.open_list_all()
                outcome.append(f"LEFT ({refusal}); now {cleaner.row_status(entry)}: {label}")
            else:
                failures.append(f"NOT removed {label}: (dialogs {cleaner.last_delete_dialogs}, "
                                f"messages {cleaner.last_delete_messages})")
        except Exception as exc:  # noqa: BLE001
            failures.append(f"{label}: {exc!r}")
    return outcome, failures


def is_published(admin, entry: GalleryEntry) -> bool:
    admin.open_list_all()
    return admin.row_status(entry) == STATUS_PUBLISHED

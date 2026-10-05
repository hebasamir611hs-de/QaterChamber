"""
cms/pages/photo_gallery/photo_album_admin_page.py — PhotoAlbumAdminPage.

`/web/qatar-chamber/manage-photo-album` ("Photo Album", slug "photo-album")
for PBI 130714. Read live 2026-10-05 as Site Content Editor (156488):

  Album Title            ObjectField_albumTitle (required) + #qc-ar-albumTitle
  Album Cover Image      ObjectField_albumCoverImage — Documents & Media picker,
                         help "Upload a .jpg,.jpeg,.png no larger than 5 MB."
  Published Date         ObjectField_publishedDate (date, required)
  Photo Count            ObjectField_photoCount (plain number box, typed by hand)
  View Count             ObjectField_viewCount (plain number box)
  Event Category         ObjectField_r_photoAlbums_c_eventCategoryId (select from list)
  Flickr Source Folder   ObjectField_r_flickrAlbumSource_c_flickrAlbumId (select
                         from list of manage-flickr-album records)
  Uploaded Photos Album  ObjectField_r_uploadedAlbumSource_c_uploadedAlbumId
                         (select from list of manage-uploaded-album records)
  Active Status          ObjectField_activeStatus (ticked by default)

HOW PHOTOS GET INTO AN ALBUM (probe 2026-10-05): there is NO Photos panel, no
"Add Photo" control and no per-photo record (title / thumbnail framing /
display order / publish status) on this or any other Photo Gallery object.
An album's photos are the files of ONE Documents & Media folder, chosen
indirectly: the album points at a Flickr Album record (manage-flickr-album:
Album Name, Flickr Photoset ID, Documents Folder ID, Photo Count, Source —
136 records, e.g. "First_Test_Album_QChamber" -> folder 52245, Source
"documentFolder") or at an Uploaded Photos Album record (manage-uploaded-album:
Folder Name, Documents Folder ID, Photo Count, Source — 0 records). The three
real albums each point at a Flickr Album record. Flickr import itself is not
reachable from these Editor screens.

The row Preview opens `/web/qatar-chamber/photo-album-details?qcPreview=photoalbums%3A<id>`;
the public detail is `/web/qatar-chamber/photo-album-details?erc=<code>`.
"""

from __future__ import annotations

from cms.pages.photo_gallery.gallery_admin_base import GalleryAdminPage
from config.settings import web_url

PHOTO_ALBUM_SLUG = "photo-album"
K_ALBUM_TITLE = "albumTitle"
K_COVER_IMAGE = "albumCoverImage"
K_PUBLISHED_DATE = "publishedDate"
K_PHOTO_COUNT = "photoCount"
K_VIEW_COUNT = "viewCount"
K_EVENT_CATEGORY = "r_photoAlbums_c_eventCategoryId"
K_FLICKR_SOURCE = "r_flickrAlbumSource_c_flickrAlbumId"
K_UPLOADED_SOURCE = "r_uploadedAlbumSource_c_uploadedAlbumId"
K_ACTIVE_STATUS = "activeStatus"

LABEL_ALBUM_TITLE = "Album Title"
LABEL_ALBUM_TITLE_AR = "Album Title — العربية"
LABEL_COVER_IMAGE = "Album Cover Image"
LABEL_PUBLISHED_DATE = "Published Date"
LABEL_PHOTO_COUNT = "Photo Count"
LABEL_VIEW_COUNT = "View Count"
LABEL_EVENT_CATEGORY = "Event Category"
LABEL_FLICKR_SOURCE = "Flickr Source Folder"
LABEL_UPLOADED_SOURCE = "Uploaded Photos Album"
COVER_HELP_TEXT = "Upload a .jpg,.jpeg,.png no larger than 5 MB."

ALBUM_DETAILS_PATH = "/web/qatar-chamber/photo-album-details"


class PhotoAlbumAdminPage(GalleryAdminPage):
    TITLE_KEY = K_ALBUM_TITLE

    def __init__(self, page, prefix: str, evidence_dir: str):
        super().__init__(page, PHOTO_ALBUM_SLUG, prefix, evidence_dir)

    def fill_album(self, data: dict) -> "PhotoAlbumAdminPage":
        """Keys (None/absent = untouched): title, title_ar, published_date (dd/mm/yyyy),
        photo_count, view_count, category (label), flickr_source (label),
        uploaded_source (label), cover (file path) + cover_stem, active."""
        if data.get("title") is not None:
            self.fill_en(K_ALBUM_TITLE, data["title"])
        if data.get("title_ar") is not None:
            self.fill_ar(K_ALBUM_TITLE, data["title_ar"])
        if data.get("published_date") is not None:
            self.set_date(K_PUBLISHED_DATE, data["published_date"])
        if data.get("photo_count") is not None:
            self.fill_number(K_PHOTO_COUNT, str(data["photo_count"]))
        if data.get("view_count") is not None:
            self.fill_number(K_VIEW_COUNT, str(data["view_count"]))
        if data.get("category"):
            self.pick(K_EVENT_CATEGORY, data["category"])
        if data.get("flickr_source"):
            self.pick(K_FLICKR_SOURCE, data["flickr_source"])
        if data.get("uploaded_source"):
            self.pick(K_UPLOADED_SOURCE, data["uploaded_source"])
        if data.get("cover"):
            self.upload(K_COVER_IMAGE, data["cover"], data.get("cover_stem"))
        if data.get("active") is not None:
            self.set_active_status(bool(data["active"]))
        return self

    def read_album(self) -> dict:
        return {
            "title": self.text_value(K_ALBUM_TITLE),
            "title_ar": self.ar_value(K_ALBUM_TITLE),
            "published_date": self.date_text(K_PUBLISHED_DATE),
            "photo_count": self.text_value(K_PHOTO_COUNT),
            "view_count": self.text_value(K_VIEW_COUNT),
            "category": self.picklist_text(K_EVENT_CATEGORY),
            "category_id": self.picklist_value(K_EVENT_CATEGORY),
            "flickr_source": self.picklist_text(K_FLICKR_SOURCE),
            "flickr_source_id": self.picklist_value(K_FLICKR_SOURCE),
            "uploaded_source": self.picklist_text(K_UPLOADED_SOURCE),
            "cover_file": self.stored_file_name(K_COVER_IMAGE),
            "active": self.active_status_stored(),
        }

    def photos_panel_present(self) -> dict:
        """What the form offers for adding photos: an explicit Photos panel /
        Add Photo control, or only the indirect folder-source pickers."""
        text = self.form_text()
        return {
            "photos_panel": self._form().get_by_text("Photos", exact=True).count() > 0,
            "add_photo": (self.page.get_by_role("button", name="Add Photo").count()
                          + self.page.get_by_role("link", name="Add Photo").count()) > 0,
            "flickr_source_field": self.has_field(K_FLICKR_SOURCE),
            "uploaded_source_field": self.has_field(K_UPLOADED_SOURCE),
            "form_text": " | ".join(t.strip() for t in text.split("\n") if t.strip()),
        }

    @staticmethod
    def public_detail_url(code: str, locale: str = "en") -> str:
        return web_url(f"{ALBUM_DETAILS_PATH}?erc={code}", locale=locale)


# --- PB ---
# Agent PB (field validation, cases 143157-143162; 143164-143169 are blocked —
# see PA's "HOW PHOTOS GET INTO AN ALBUM" note above). PBFieldsMixin
# (pb_form_support.py) is mixed in FRONT of PA's PhotoAlbumAdminPage: readers
# only plus a role-pinned open(); no PA method is changed. Live 2026-10-05:
# Album Cover Image carries NO `required` attribute, the Event Category hidden
# value input carries none either; Album Title (EN/AR) and Published Date do.
from cms.pages.photo_gallery.pb_form_support import (  # noqa: E402
    PB_EVIDENCE_DIR as _PB_EVIDENCE_DIR,
    PB_QCTEST_PREFIX as _PB_QCTEST_PREFIX,
    PBFieldsMixin as _PBFieldsMixin,
)

ALBUM_TITLE_LIMIT = 200


class PhotoAlbumFieldsPB(_PBFieldsMixin, PhotoAlbumAdminPage):
    """manage-photo-album for Agent PB (QCTEST-130714-PB- namespace)."""

    def __init__(self, page):
        PhotoAlbumAdminPage.__init__(self, page, _PB_QCTEST_PREFIX, _PB_EVIDENCE_DIR)
        self.pb_init()

    def fill_album_pb(self, data: dict) -> "PhotoAlbumFieldsPB":
        """Same keys as fill_album(); titles go in with a change event and the
        cover through attempt_upload_pb() (asserts it attached)."""
        data = dict(data)
        if data.get("title") is not None:
            self.fill_en_change(K_ALBUM_TITLE, data.pop("title"))
        if data.get("title_ar") is not None:
            self.fill_ar_change(K_ALBUM_TITLE, data.pop("title_ar"))
        cover = data.pop("cover", None)
        stem = data.pop("cover_stem", None)
        self.fill_album(data)
        if cover:
            self.upload_pb(K_COVER_IMAGE, cover, stem)
        return self

    def photo_capabilities(self) -> dict:
        """Read-only: does this form (or the page) offer any per-photo control?"""
        labels = self.form_labels()
        text = self.visible_text()
        wanted = ("Add Photo", "Photo File", "Photo Title", "Thumbnail Framing", "Photos")
        return {"labels": labels,
                "found": {w: (w in text) for w in wanted},
                "photo_file_inputs": self.page.locator('input[type="file"]').count()}

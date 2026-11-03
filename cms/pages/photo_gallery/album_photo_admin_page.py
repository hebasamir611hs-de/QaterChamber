"""
cms/pages/photo_gallery/album_photo_admin_page.py — AlbumPhotoAdminPage.

`/web/qatar-chamber/manage-album-photo` ("Album Photo", slug "album-photo",
Object QCDEMO-130714-ALBUM_PHOTO) — the per-photo model delivered for ADO bug
148169 on 2026-10-12. Read live 2026-10-13 as Site Content Editor (156488):

  Album              ObjectField_r_albumPhotos_c_photoAlbumId (select from list;
                     preset from ?qcParent=<albumId>)
  Photo File         ObjectField_photoFile (required) — Documents & Media picker:
                     existing files + "Drag & Drop Your Files or Browse to Upload";
                     help "Upload a .jpg,.jpeg,.png no larger than 10 MB."
  Photo Title        ObjectField_photoTitle + #qc-ar-photoTitle (optional, "0 / 200")
  Thumbnail Framing  ObjectField_thumbnailFraming (select from list, required,
                     default "Centre"; 9 options)
  Display Order      ObjectField_displayOrder (number, required; next 100-grid
                     value prefilled on Add)
  Active Status      ObjectField_activeStatus (ticked by default)

`?qcParent=<albumId>` scopes the list to one album; `&qcAdd=1` opens the add
form with the Album preset. The album's edit form carries the Photos panel
(`[data-qc-oel-child-panel]`) — see PhotoAlbumAdminPage.photos_panel().
"""

from __future__ import annotations

import re

from cms.pages.photo_gallery.gallery_admin_base import REAL_CODE_PREFIXES, GalleryAdminPage, GalleryEntry
from config.settings import control_panel_url
from core.utils.waits import WaitTimeoutError, wait_until

ALBUM_PHOTO_SLUG = "album-photo"
K_PHOTO_ALBUM = "r_albumPhotos_c_photoAlbumId"
K_PHOTO_FILE = "photoFile"
K_PHOTO_TITLE = "photoTitle"
K_THUMBNAIL_FRAMING = "thumbnailFraming"
K_PHOTO_DISPLAY_ORDER = "displayOrder"

LABEL_PHOTO_FILE = "Photo File"
LABEL_PHOTO_TITLE = "Photo Title"
LABEL_THUMBNAIL_FRAMING = "Thumbnail Framing"
LABEL_PHOTO_DISPLAY_ORDER = "Display Order"
PHOTO_TITLE_LIMIT = 200
FRAMING_DEFAULT = "Centre"
FRAMING_OPTIONS = ("Centre", "Top", "Bottom", "Left", "Right", "Top left", "Top right", "Bottom left",
                   "Bottom right")
MSG_UNSUPPORTED_TYPE = "Unsupported file type. Accepted formats: JPG, JPEG, PNG."
MSG_ALBUM_NEEDS_PUBLISHED_PHOTO = "An album must contain at least one published photo."
MSG_ALBUM_NEEDS_PUBLISHED_PHOTO_AR = "يجب أن يحتوي الألبوم على صورة منشورة واحدة على الأقل"
MSG_UNSUPPORTED_TYPE_AR = "نوع الملف غير مدعوم"
PICKER_DEVICE_UPLOAD_TEXT = "Browse to Upload"


class AlbumPhotoAdminPage(GalleryAdminPage):
    """manage-album-photo, scoped to ONE album through `parent_id` (?qcParent=)."""

    TITLE_KEY = K_PHOTO_TITLE

    def __init__(self, page, prefix: str, evidence_dir: str, parent_id: str = ""):
        super().__init__(page, ALBUM_PHOTO_SLUG, prefix, evidence_dir)
        self.parent_id = parent_id

    def for_album(self, album_id: str) -> "AlbumPhotoAdminPage":
        self.parent_id = str(album_id)
        return self

    def _manage_url(self, edit_entry: str | None = None, locale: str | None = None) -> str:
        prefix = f"/{locale}" if locale else ""
        query = []
        if self.parent_id:
            query.append(f"qcParent={self.parent_id}")
        if edit_entry:
            query.append(f"editEntry={edit_entry}")
        elif self.parent_id:
            query.append("qcAdd=1")
        path = f"{prefix}/web/qatar-chamber/manage-{self.slug}" + (("?" + "&".join(query)) if query else "")
        return control_panel_url(path)

    def open_add_form(self) -> "AlbumPhotoAdminPage":
        """The album's '+ Add photo' target (Album preset, next Display Order)."""
        if not self.parent_id:
            raise ValueError("open_add_form needs the album id (for_album())")
        return self.open_create_form_en()

    def is_list_fully_expanded(self) -> bool:
        """An album with no photo yet renders an empty list (no rows, count 0 or
        absent) - that IS fully expanded."""
        if self.rendered_row_count() == 0 and self.total_entry_count() in (None, 0):
            return True
        # Live 2026-10-14: the ?qcParent= list renders no "n total" counter; it is
        # complete when no page-size selector limits it.
        if self.parent_id and self.total_entry_count() is None:
            select = self.page.locator(self.PAGE_SIZE_SELECT)
            return not (select.count() and select.first.is_visible() and select.first.input_value() != "0")
        return super().is_list_fully_expanded()

    def open(self, url: str) -> None:
        try:
            super().open(url)
        except Exception:  # noqa: BLE001 — one retry on a transient net::ERR_ABORTED
            self.page.wait_for_load_state("load")
            super().open(url)

    def open_add_href(self, href: str) -> "AlbumPhotoAdminPage":
        """Follows a panel '+ Add photo' href (site-relative)."""
        self.open(href if href.startswith("http") else control_panel_url(href))
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        return self

    def photo_file_picker_options(self) -> dict:
        """Opens the Photo File Documents & Media picker, reads what it offers, and
        closes it with Escape (nothing selected or uploaded)."""
        self._open_picker(K_PHOTO_FILE)
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        body = frame.locator("body")
        try:
            wait_until(lambda: PICKER_DEVICE_UPLOAD_TEXT in body.inner_text()
                       and ("DOCUMENTS" in body.inner_text() or "FOLDERS" in body.inner_text()),
                       timeout=45.0, poll=0.5)
        except WaitTimeoutError:
            pass
        text = " ".join(body.inner_text().split())
        result = {"library_entries": ("DOCUMENTS" in text or "FOLDERS" in text) and bool(
                      re.search(r"Showing \d+ to \d+ of [\d,]+ entries", text)),
                  "device_upload": PICKER_DEVICE_UPLOAD_TEXT in text and frame.locator('input[type="file"]').count() > 0,
                  "text": text[:600]}
        self.page.keyboard.press("Escape")
        try:
            self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
        except Exception:  # noqa: BLE001
            pass
        return result

    def upload_attempt(self, file_path: str, stem: str | None = None) -> dict:
        """attempt_upload() into Photo File (the picker's own refusal is evidence)."""
        return self.attempt_upload(K_PHOTO_FILE, file_path, stem)

    # ---- fields ------------------------------------------------------------------------
    def fill_photo(self, data: dict) -> "AlbumPhotoAdminPage":
        """Keys (None/absent = untouched): file (path) + file_stem, title, title_ar,
        framing (label), display_order, active."""
        if data.get("file"):
            self.upload(K_PHOTO_FILE, data["file"], data.get("file_stem"))
        if data.get("title") is not None:
            self.fill_en(K_PHOTO_TITLE, data["title"])
        if data.get("title_ar") is not None:
            self.fill_ar(K_PHOTO_TITLE, data["title_ar"])
        if data.get("framing"):
            self.pick(K_THUMBNAIL_FRAMING, data["framing"])
        if data.get("display_order") is not None:
            self.fill_number(K_PHOTO_DISPLAY_ORDER, str(data["display_order"]))
        if data.get("active") is not None:
            self.set_active_status(bool(data["active"]))
        return self

    def control_info(self, key: str) -> dict:
        """required / maxLength / min / type / validationMessage of one EN control."""
        return self._en(key).evaluate(
            "e => ({required: e.required, maxLength: e.maxLength, min: e.min, max: e.max, type: e.type,"
            " validationMessage: e.validationMessage})")

    def clear_framing(self) -> dict:
        """Tries to leave Thumbnail Framing unset: empties the combobox text and
        blurs. Returns {text, value} as the form holds them afterwards."""
        prefix = self._picklist_prefix(K_THUMBNAIL_FRAMING)
        box = self.page.locator(f'[id="{prefix}-select-from-list-input"]').first
        box.click()
        box.press("Control+A")
        box.press("Delete")
        box.press("Tab")
        return {"text": box.input_value(), "value": self.picklist_value(K_THUMBNAIL_FRAMING)}

    def read_photo(self) -> dict:
        return {
            "album_id": self.picklist_value(K_PHOTO_ALBUM),
            "file": self.stored_file_name(K_PHOTO_FILE),
            "file_field": self.field_block_text(K_PHOTO_FILE),
            "title": self.text_value(K_PHOTO_TITLE),
            "title_ar": self.ar_value(K_PHOTO_TITLE),
            "framing": self.picklist_text(K_THUMBNAIL_FRAMING),
            "framing_value": self.picklist_value(K_THUMBNAIL_FRAMING),
            "display_order": self.text_value(K_PHOTO_DISPLAY_ORDER),
            "active": self.active_status_stored(),
        }

    # ---- identity (titles may be blank) ----------------------------------------------
    def new_rows(self, ids_before: set[str]) -> list[dict]:
        """Rows of THIS album's photo list whose id was not there before (read-only)."""
        self.open_list_all()
        return [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                and not any(r["code"].startswith(p) for p in REAL_CODE_PREFIXES)]

    def identify_new_photo(self, title: str, ids_before: set[str]) -> GalleryEntry | None:
        """The ONE new photo of this album titled `title` (prefix-checked)."""
        if not self.parent_id:
            raise ValueError("identify_new_photo needs the album id")
        return self.identify_created(title, ids_before)

    def stored_photo_ids(self) -> set[str]:
        return self.snapshot_ids()


def unsupported_type_shown(text: str) -> bool:
    return MSG_UNSUPPORTED_TYPE.rstrip(".") in text or MSG_UNSUPPORTED_TYPE_AR in text

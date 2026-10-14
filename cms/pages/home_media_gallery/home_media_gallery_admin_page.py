"""
cms/pages/home_media_gallery/home_media_gallery_admin_page.py — Control_Panel
Page Objects for PBI 129388 (QC-HOME-012, Home Media Gallery Section).

Object names come from cms/Content-Admin-Guide.docx §14 "Home — Media Gallery":
  * Videos — **MediaItem** (fields mediaTitleEn/Ar, thumbnailImage,
    videoFileEmbedUrl, publicationDate, activeStatus). Field labels follow
    cms/liferay-context.md (QCDEMO-129388, object id 50743, label "Media Item").
  * Photo albums — "synced automatically from Flickr — not edited here". The
    album cases therefore use the Media Center **Photo Album** object
    (cms/pages/photo_albums), which feeds the same gallery.

SUPERSEDED 2026-10-14 (fix passes 5-6): the Home gallery reads ONLY Video
Record and Photo Album; every PBI 129388 video case now uses
HomeVideoRecordAdminPage. HomeMediaItemAdminPage is kept but no test uses it.

Every record a test creates is a disposable `QCTEST-<tc_id>-<short>`, deleted
by exact title (DisposableObjectAdminPage guards against anything else).

VERIFY-LIVE:
  * slug `media-item` is inferred from the object label "Media Item" and has
    NOT been read off the live Object Authoring sidebar. `SLUG_CONFIRMED_LIVE`
    stays False, so the page refuses to navigate until someone confirms it.
  * the Photo Album slug is still empty in cms/pages/photo_albums, so the album
    cases refuse to navigate for the same reason.
  * the schema has a single text field "Video File / Embed URL" and no separate
    video upload control. `video_file` below is the control that TC 133676 names.
  * Publication Date entry format (MM/DD/YYYY assumed).
"""

from __future__ import annotations

import re
from datetime import date

from cms.pages.components.disposable_object_admin import (
    DisposableObjectAdminPage,
    FieldSpec as F,
)
from cms.pages.photo_albums.photo_albums_admin_page import PhotoAlbumAdminPage

# Today's date, so a QCTEST item is never hidden behind newer real items or
# held back as future-dated. VERIFY-LIVE: entry format.
TODAY = date.today().strftime("%m/%d/%Y")
QCTEST_EMBED_URL = "https://www.youtube.com/embed/qctest129388"


class _GalleryFormMixin:
    """Form-level reads shared by the two gallery objects."""

    def submit_enabled(self) -> bool:
        btn = self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON)
        return btn.count() > 0 and btn.first.is_enabled()

    def attachment_field_labels(self) -> list[str]:
        """Accessible names of every attachment control on the form
        (`<Label> Select File`), with the suffix removed."""
        boxes = self.page.get_by_role("textbox", name=re.compile(r"Select File$"))
        names = [boxes.nth(i).get_attribute("aria-label") or "" for i in range(boxes.count())]
        return [n.replace("Select File", "").strip() for n in names]

    def raw_file_inputs(self) -> int:
        """`input[type=file]` drop zones rendered directly on the form (outside
        the Documents & Media picker iframe)."""
        return self.page.locator('form input[type="file"]').count()

    def field_required(self, key: str) -> bool:
        kind = self.spec(key).kind
        if kind in ("date", "select"):
            # Not role=textbox by name on this surface (2026-10-13) -- resolved
            # through the field's <label>, see DisposableObjectAdminPage.
            try:
                box = self.date_input(key) if kind == "date" else self.combobox(key)
            except LookupError:
                return False
        else:
            box = self.page.get_by_role("textbox", name=self.label_pattern(self.spec(key).label))
        if box.count() == 0:
            return False
        return box.first.evaluate("el => !!el.required || el.getAttribute('aria-required') === 'true'")


class HomeMediaItemAdminPage(_GalleryFormMixin, DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Media Item"  # read live off the sidebar 2026-10-13
    SLUG = "media-item"  # read live 2026-10-13: "Media Item -> manage-media-item"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "title_en"
    FIELDS = {
        "title_en": F("Media Title (EN)", required=True, max_len=200),
        "title_ar": F("Media Title (AR)", required=True, default="QCTEST عنوان وسائط", max_len=200),
        "thumbnail": F("Thumbnail Image", kind="file", required=True),
        "embed_url": F("Video File / Embed URL", kind="url", default=QCTEST_EMBED_URL, max_len=500),
        "video_file": F("Video File", kind="file"),  # VERIFY-LIVE: not in the documented schema
        "publication_date": F("Publication Date", kind="date", required=True,
                              ref="publicationDate", default=TODAY),
        "active_status": F("Active Status", kind="checkbox"),
    }


class HomeGalleryAlbumPhotoAdminPage(DisposableObjectAdminPage):
    """Album Photo (`manage-album-photo`) -- one photo row of a Photo Album.

    Added 2026-10-13: a Photo Album's Submit is refused with "An album must
    contain at least one published photo", so every album case first saves
    its QCTEST album as Draft, then publishes ONE QCTEST Album Photo linked
    to it here, then submits the album.

    Form read live 2026-10-13 (manage-album-photo, Editor): Album (required
    relationship picker; a Draft QCTEST album IS offered), Photo File
    (required upload), Photo Title + "— العربية", Thumbnail Framing
    (required: Centre / Top / Bottom / Left / Right / Top left / Top right /
    Bottom left / Bottom right), Display Order (required number). No Active
    Status field. The album list's "Photos" row action
    (`data-qc-oel-child-link`) opens this same form scoped to one album
    (`?qcParent=<album id>`).

    Deliberately NOT `cms/pages/photo_albums.PhotoAdminPage` (still
    SLUG-less there): giving that class a slug would start PBI 130714's
    tests navigating."""

    SIDEBAR_LABEL = "Album Photo"
    SLUG = "album-photo"  # read live 2026-10-13
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "photo_title"
    ACTIVE_FIELD = None
    FIELDS = {
        "album": F("Album", kind="select", required=True),
        "photo_file": F("Photo File", kind="file", required=True),
        "photo_title": F("Photo Title", bilingual=True, max_len=200),
        "thumbnail_framing": F("Thumbnail Framing", kind="select", required=True, default="Centre"),
        "display_order": F("Display Order", kind="number", required=True, default="9900"),
    }

    def select_album_exact(self, album_title: str) -> "HomeGalleryAlbumPhotoAdminPage":
        """Links the photo to `album_title` ONLY when exactly one Album
        option reads that title -- never a contains-match and never "the
        first option", which could attach a QCTEST photo to a real album."""
        if not album_title.startswith("QCTEST-"):
            raise ValueError(f"refusing to attach a test photo to non-disposable album {album_title!r}")
        options = self.select_options("album")
        exact = [o for o in options if self._norm(o) == self._norm(album_title)]
        if len(exact) != 1:
            raise LookupError(
                f"Album picker: {len(exact)} option(s) read exactly {album_title!r}; options: {options}"
            )
        self.select_option("album", album_title)
        return self

    def create_published_photo(self, album_title: str, photo_title: str, photo_file: str,
                               role: str) -> str:
        """Creates and submits one QCTEST photo in `album_title` as `role`;
        returns its row status."""
        self.open_form(role)
        self.select_album_exact(album_title)
        self.upload("photo_file", photo_file, tag=photo_title)
        self.fill("photo_title", photo_title)
        self.fill("photo_title", f"{photo_title} AR", locale="ar")
        self.fill("thumbnail_framing", self.spec("thumbnail_framing").default)
        self.fill("display_order", self.spec("display_order").default)
        self.submit_for_review()
        return self.status_of(photo_title, role)


class HomeGalleryAlbumAdminPage(_GalleryFormMixin, PhotoAlbumAdminPage):
    """Media Center Photo Album, as the Home Media Gallery's album source.
    Published Date is set to today so the album can surface on Home."""

    FIELDS = dict(
        PhotoAlbumAdminPage.FIELDS,
        published_date=F("Published Date", kind="date", required=True, ref="publishedDate", default=TODAY),
        video_embed=F("Video File / Embed URL", kind="url"),  # 133680: must be absent or optional
    )


class HomeVideoRecordAdminPage(_GalleryFormMixin, DisposableObjectAdminPage):
    """Media Center **Video Record** (`manage-video-record`) -- the object
    that ACTUALLY feeds the Home Media Gallery's video cards.

    Established live 2026-10-14 (fix pass 5):
      * the Home gallery fragment's own config is `videoApiBase:
        /o/qc-video-library-api` + `galleryApiBase: /o/qc-photo-gallery-api`;
        its source comment says "Video Record and Photo Album are the only
        sources now" (MediaItem and the Flickr mirror were dropped);
      * an anonymous Home load calls `/o/qc-video-library-api/videos` and
        `/o/qc-photo-gallery-api/albums` and nothing under `/o/c/mediaitems`;
      * every video card's ERC is a Video Record entry (QCDEMO-130715-VIDEO-*).
    So the video cases of PBI 129388 run here, not on Media Item.

    Form read live 2026-10-14 as Site Content Editor: Video Title (required,
    + AR twin required), Video Source Type (picklist: Flickr / External URL /
    Direct Upload -- conditional Flickr Video / Video URL / Video File),
    Video Thumbnail (required upload), Duration (required text), Video
    Description (+AR), Published Date (required `type=date`), View Count,
    Video Category (relationship picker), Active Status (TICKED by default).

    Deliberately NOT cms/pages/video_library.VideoRecordAdminPage (SLUG-less
    there): giving that class a slug would start PBI 130715's tests
    navigating."""

    SIDEBAR_LABEL = "Video Record"
    SLUG = "video-record"  # read live 2026-10-14: "Video Record -> manage-video-record"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "video_title"
    FIELDS = {
        "video_title": F("Video Title", bilingual=True, required=True, max_len=200),
        "video_source_type": F("Video Source Type", kind="select", required=True, default="External URL"),
        "video_url": F("Video URL", kind="url", default=QCTEST_EMBED_URL),
        # Accessible name with Source Type = Direct Upload is "Video File
        # Required Select File" (an sr-only "Required" span, read live
        # 2026-10-14); upload_file() matches "<label> Select File" as a
        # substring, so the label carries "Required". Only valid in that mode.
        "video_file": F("Video File Required", kind="file"),
        "thumbnail": F("Video Thumbnail", kind="file", required=True),
        "duration": F("Duration", required=True, default="01:00"),
        # Today, so a QCTEST video sorts first (the gallery sorts by date).
        "published_date": F("Published Date", kind="date", required=True, ref="publishedDate", default=TODAY),
        # Required on save ("Video Category is required.", live 2026-10-14);
        # fill_required() links the first offered option -- linking changes
        # nothing on the category itself.
        "video_category": F("Video Category", kind="select", required=True),
        "active_status": F("Active Status", kind="checkbox"),
    }
    SOURCE_EXTERNAL_URL = "External URL"
    SOURCE_DIRECT_UPLOAD = "Direct Upload"
    # "Video URL" is named "Video URL Required" (sr-only span) when External
    # URL is the source, so the anchored label lookup misses it; the control
    # is addressed by its object-field name instead (read live 2026-10-14).
    VIDEO_URL_INPUT = 'input[name="ObjectField_videoUrl"]'

    def fill(self, key: str, value: str, locale: str = "en") -> "HomeVideoRecordAdminPage":
        if key == "video_url":
            self.page.locator(self.VIDEO_URL_INPUT).first.fill(value)
            return self
        return super().fill(key, value, locale)

    def fill_required(self, title: str, skip: tuple[str, ...] = (), active: bool = False,
                      files: dict[str, str] | None = None) -> "HomeVideoRecordAdminPage":
        """The base fill, plus the Video URL: it is required whenever Source
        Type = External URL (the default the base fill picks), so a case
        about another field would otherwise be refused for the missing URL
        instead (fix pass 6, 2026-10-14). Skip `video_url` to leave it empty
        or to fill it / switch the source yourself."""
        super().fill_required(title, skip=skip, active=active, files=files)
        if "video_url" not in skip and "video_source_type" not in skip:
            self.fill("video_url", self.spec("video_url").default)
        return self

    # The source controls render only after a Video Source Type pick (live
    # 2026-10-14, 133646: neither showed on an immediate check right after
    # the pick). VERIFY-LIVE: that a bounded wait is enough.
    CONDITIONAL_FIELD_MS = 8000

    def field_present(self, key: str) -> bool:
        if key == "video_url":
            # "Video URL" is named "Video URL Required" (see VIDEO_URL_INPUT).
            box = self.page.locator(self.VIDEO_URL_INPUT).first
        elif key == "video_file":
            box = self.page.get_by_role(
                "textbox", name=re.compile(r"^Video File\b.*Select File$")).first
        else:
            return super().field_present(key)
        try:
            box.wait_for(state="attached", timeout=self.CONDITIONAL_FIELD_MS)
        except Exception:  # noqa: BLE001 -- never rendered for this source type
            return False
        return True

    def form_still_open(self) -> bool:
        """The create/edit form's Submit control is still on screen -- a
        refused save leaves the user on the form."""
        return self.page.locator(self.SUBMIT_FOR_REVIEW_BUTTON).count() > 0

    # The Source Type picklist's visible combobox sometimes reads "" right
    # after a pick that DID register (live 2026-10-14, 133676); the hidden
    # `<name>-label` control the Select-from-List fragment writes is checked
    # before the pick is called failed.
    SOURCE_TYPE_LABEL_INPUT = 'input[name="ObjectField_videoSourceType-label"]'

    def select_option(self, key: str, option_label: str) -> "HomeVideoRecordAdminPage":
        if key != "video_source_type":
            return super().select_option(key, option_label)
        # A re-pick click on a list that already closed can also time out
        # (133657, live 2026-10-14) -- one fresh attempt, then the hidden
        # control decides.
        for attempt in (1, 2):
            try:
                return super().select_option(key, option_label)
            except Exception:  # noqa: BLE001 -- LookupError or a click timeout
                hidden = self.page.locator(self.SOURCE_TYPE_LABEL_INPUT).first.input_value()
                if self._norm(hidden) == self._norm(option_label):
                    return self
                if attempt == 2:
                    raise
                self.page.keyboard.press("Escape")
        return self

    # The file readout (`<strong role=textbox>`) is named plain "Video File"
    # while the hidden upload control carries "Video File Required Select
    # File" (live 2026-10-14, 133676: the mp4 attached but the readout lookup
    # by "Video File Required" found nothing and upload_file() raised).
    VIDEO_FILE_READOUT_LABEL = "Video File"

    def _video_file_readout(self) -> str:
        box = self.page.get_by_role("textbox", name=self.label_pattern(self.VIDEO_FILE_READOUT_LABEL))
        return box.first.inner_text(timeout=2000).strip() if box.count() else ""

    def _upload_readouts(self, field_label: str) -> dict:
        out = super()._upload_readouts(field_label)
        if field_label == self.FIELDS["video_file"].label and not out.get("selected"):
            try:
                out["selected"] = self._video_file_readout()
            except Exception:  # noqa: BLE001 -- no readout rendered
                pass
        return out

    # History trail verbs, newest first (read live 2026-10-14 on an INACTIVE
    # row: "Deactivated ... / Published ... / Created ..."). An INACTIVE row
    # shows the INACTIVE badge instead of its workflow state and offers
    # neither Publish nor Unpublish, so its workflow state is read here.
    _HISTORY_VERB = re.compile(
        r"^(Created|Published|Unpublished|Deactivated|Activated|Archived|Restored|Submitted|"
        r"Rejected|Resubmitted|Returned|Scheduled|Updated|Edited|Saved|Drafted)\b")
    WORKFLOW_VERBS = {"Published", "Unpublished", "Archived", "Restored", "Submitted",
                      "Rejected", "Resubmitted", "Returned", "Scheduled", "Drafted"}

    def history_verbs(self, title: str) -> list[str]:
        """The row's History actions, newest first (call on the entries list)."""
        self.history_entries(title)
        text = self.page.locator(self.HISTORY_LIST).first.inner_text()
        return [m.group(1) for m in (self._HISTORY_VERB.match(line.strip()) for line in text.splitlines()) if m]

    # The record's workflow status as the headless API stores it, read with
    # the page's own CSRF-aware fetch (read live 2026-10-14: an INACTIVE
    # Video Record reads status code 6 "incomplete", not 0 "approved").
    _STATUS_JS = (
        "id => Liferay.Util.fetch('/o/c/videorecords/' + id + '?fields=status,activeStatus',"
        " {headers: {Accept: 'application/json'}}).then(r => r.json())"
    )

    def stored_status(self, title: str) -> dict:
        """`{"code": int, "label": str, "active": bool}` of the row matching
        `title` on the open entries list; {} when the row or the read fails."""
        self.filter_entries(title)
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")').first
        if not row.count():
            return {}
        entry_id = row.locator("[data-qc-oel-history]").first.get_attribute("data-qc-oel-history")
        try:
            data = self.page.evaluate(self._STATUS_JS, entry_id)
        except Exception:  # noqa: BLE001
            return {}
        status = data.get("status") or {}
        return {"code": status.get("code"), "label": status.get("label"), "active": data.get("activeStatus")}

    def last_workflow_verb(self, title: str) -> str:
        """Newest History action that is a workflow transition ("" if none)."""
        return next((v for v in self.history_verbs(title) if v in self.WORKFLOW_VERBS), "")

    def value(self, key: str, locale: str = "en") -> str:
        if key == "video_file":
            try:
                readout = self._video_file_readout()
            except Exception:  # noqa: BLE001
                readout = ""
            return readout or self.current_file_name(self.FIELDS["video_file"].label)
        if key == "video_source_type":
            return self.page.locator(self.SOURCE_TYPE_LABEL_INPUT).first.input_value()
        if key == "video_url":
            return self.page.locator(self.VIDEO_URL_INPUT).first.input_value()
        return super().value(key, locale)

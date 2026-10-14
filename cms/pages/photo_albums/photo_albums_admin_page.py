"""
cms/pages/photo_albums/photo_albums_admin_page.py — Control_Panel Page
Objects for PBI 130714 (QC - Media Center - Photo Albums).

Authored through the "Photo Gallery Page Hero" (page-level, SINGLETON) and
"Photo Album" objects, per the 2026-10-01 coordinator ruling. The cases also
author Event Categories and per-photo rows (title, framing, display order);
whether those are their own sidebar objects or panels inside the Photo Album
form is read live — `PhotoEventCategoryAdminPage` / `PhotoAdminPage` keep an
empty SLUG until then, so they cannot navigate.

Flickr-imported albums are real shared content: never edited here.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class PhotoGalleryPageHeroAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Photo Gallery Page Hero"
    SLUG = "page-hero"  # read live off the Object Authoring sidebar 2026-10-13
    SLUG_CONFIRMED_LIVE = True
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100),
        "hero_background_image": F("Hero Background Image", kind="file", required=True),
        "active_status": F("Active Status", kind="checkbox"),
    }


class PhotoEventCategoryAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Photo Gallery Event Category"
    SLUG = "event-category"  # read live off the Object Authoring sidebar 2026-10-13
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "name"
    FIELDS = {
        "name": F("Name", bilingual=True, required=True, max_len=200),
        "display_order": F("Display Order", kind="number", required=True, default="9900"),
        "publish_status": F("Publish Status", kind="select"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class PhotoAlbumAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Photo Album"
    SLUG = "photo-album"  # read live off the Object Authoring sidebar 2026-10-13
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "album_title"
    FIELDS = {
        "album_title": F("Album Title", bilingual=True, required=True, max_len=200),
        "event_category": F("Event Category", kind="select", required=True),
        # Live label is "Album Cover Image" (read 2026-10-13, manage-photo-album);
        # "Cover Image" only reached the picker by substring and never the readout.
        "cover_image": F("Album Cover Image", kind="file", required=True, confirmed_live=True),
        "published_date": F("Published Date", kind="date", required=True, ref="publishedDate",
                            default="01/06/2027"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class PhotoAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live): per-photo object or Photos panel inside Photo Album
    SLUG = ""
    TITLE_FIELD = "photo_title"
    FIELDS = {
        "photo_file": F("Photo File", kind="file", required=True),
        "photo_title": F("Photo Title", bilingual=True, max_len=200),
        "thumbnail_framing": F("Thumbnail Framing", kind="select", required=True),
        "display_order": F("Display Order", kind="number", required=True, default="100"),
        "album": F("Album", kind="select", required=True),
        "active_status": F("Active Status", kind="checkbox"),
    }

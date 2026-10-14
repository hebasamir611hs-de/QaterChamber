"""
cms/pages/video_library/video_library_admin_page.py — Control_Panel Page
Objects for PBI 130715 (QC - Media Center - Video Library).

Objects come from the live Object Authoring sidebar (2026-10-01 brief):
the page-level hero (SINGLETON), Video Category, and the video record.
Their sidebar labels and slugs are read live before the run; until then
`SLUG` is empty and DisposableObjectAdminPage refuses to navigate. Field
labels are the test cases' wording until read live.

Flickr-imported videos and the Flickr integration settings are real shared
content/configuration: read only.
"""

from cms.pages.components.disposable_object_admin import DisposableObjectAdminPage, FieldSpec as F


class VideoLibraryPageHeroAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live): page-level hero object for the Video Library page
    SLUG = ""
    SINGLETON = True
    TITLE_FIELD = "page_title"
    FIELDS = {
        "page_title": F("Page Title", bilingual=True, required=True, max_len=100),
        "hero_background_image": F("Hero Background Image", kind="file", required=True),
        "page_status": F("Page Status", kind="select"),
        "last_modified": F("Last Modified Date"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class VideoCategoryAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Video Category"  # TODO(live): exact sidebar text
    SLUG = ""
    TITLE_FIELD = "category_name"
    FIELDS = {
        "category_id": F("Category ID"),
        "category_name": F("Category Name", bilingual=True, required=True, max_len=200),
        "display_order": F("Display Order", kind="number", required=True, default="9900"),
        "publish_status": F("Publish Status", kind="select"),
        "active_status": F("Active Status", kind="checkbox"),
    }


class VideoRecordAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = ""  # TODO(live): video record object
    SLUG = ""
    TITLE_FIELD = "video_title"
    FIELDS = {
        "video_id": F("Video ID"),
        "video_title": F("Video Title", bilingual=True, required=True, max_len=200),
        "video_category": F("Video Category", kind="select", required=True),
        # Default variant: External URL source; VideoRecordUploadAdminPage is
        # the Direct Upload variant.
        "video_source_type": F("Video Source Type", kind="select", required=True, default="External URL"),
        "video_url": F("Video URL", kind="url", required=True,
                       default="https://www.youtube.com/watch?v=qctest00001"),
        "video_file": F("Video File", kind="file"),
        "video_thumbnail": F("Video Thumbnail", kind="file", required=True),
        "duration": F("Duration", required=True, default="04:30"),
        "video_description": F("Video Description", kind="rich", bilingual=True,
                               ref="videoDescription", max_len=2000),
        "published_date": F("Published Date", kind="date", required=True, ref="publishedDate",
                            default="01/06/2027"),
        "video_status": F("Video Status", kind="select"),
        "flickr_video_id": F("Flickr Video ID"),
        "flickr_source_folder": F("Flickr Source Folder"),
        "last_modified": F("Last Modified Date"),
        "active_status": F("Active Status", kind="checkbox"),
    }
    SOURCE_EXTERNAL_URL = "External URL"
    SOURCE_DIRECT_UPLOAD = "Direct Upload"


class VideoRecordUploadAdminPage(VideoRecordAdminPage):
    """Same object, Direct Upload variant (Video Source Type = Direct Upload)."""

    FIELDS = dict(
        VideoRecordAdminPage.FIELDS,
        video_source_type=F("Video Source Type", kind="select", required=True, default="Direct Upload"),
        video_url=F("Video URL", kind="url"),
        video_file=F("Video File", kind="file", required=True),
    )

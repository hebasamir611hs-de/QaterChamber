"""
cms/pages/video_gallery/video_category_admin_page.py — VideoCategoryAdminPage.

`/web/qatar-chamber/manage-video-category` (slug "video-category") for PBI
130715. Shares the whole lifecycle / guarded-delete machinery of
VideoGalleryAdminPage (video_record_admin_page.py — read its module
docstring for the DELETE SAFETY rules).

LIVE 2026-10-05 (Editor 156488, read-only): fields categoryName* (+
`#qc-ar-categoryName`*), displayOrder* (number), activeStatus. Six real
categories, codes QCDEMO-130715-VIDEOCAT-<slug>, all PUBLISHED: Institutional
135063, Events 135067, Leadership 135071, Training 135075, Promotional
135208, Live Streams 135212 (Training is not on the public chip row).
Preview link: `/web/qatar-chamber/video-library?qcPreview=videocategories%3A<id>`.
Display Order uses the 100-grid (100, 200, 300 …; user rule).

CORE OWNER: Agent VA. VB / VC add helpers in their own `# --- <AGENT> ---`
sections or subclasses.
"""

from __future__ import annotations

from cms.pages.video_gallery.video_record_admin_page import (
    QCTEST_PBI_PREFIX,
    VIDEO_CATEGORY_SLUG,
    VideoGalleryAdminPage,
)

KC_NAME = "categoryName"
KC_DISPLAY_ORDER = "displayOrder"
KC_ACTIVE = "activeStatus"

REAL_CATEGORY_NAMES = ("Institutional", "Events", "Leadership", "Training", "Promotional", "Live Streams")


class VideoCategoryAdminPage(VideoGalleryAdminPage):
    """manage-video-category (slug "video-category")."""

    TITLE_KEY = KC_NAME
    PREVIEW_TYPE = "videocategories"

    def __init__(self, page, owner_prefix: str, evidence_dir: str | None = None):
        super().__init__(page, VIDEO_CATEGORY_SLUG, owner_prefix, evidence_dir)

    def fill_category(self, data: dict) -> "VideoCategoryAdminPage":
        """Keys: categoryName, categoryName_ar, displayOrder, active_status (None = untouched)."""
        if data.get(KC_NAME) is not None:
            self.fill_en(KC_NAME, data[KC_NAME])
        if data.get(f"{KC_NAME}_ar") is not None:
            self.fill_ar(KC_NAME, data[f"{KC_NAME}_ar"])
        if data.get(KC_DISPLAY_ORDER) is not None:
            self.fill_number_key(KC_DISPLAY_ORDER, str(data[KC_DISPLAY_ORDER]))
        if data.get("active_status") is not None:
            self.set_active_status(bool(data["active_status"]))
        return self

    def read_category(self) -> dict:
        return {KC_NAME: self.text_value(KC_NAME), f"{KC_NAME}_ar": self.ar_value(KC_NAME),
                KC_DISPLAY_ORDER: self.text_value(KC_DISPLAY_ORDER),
                "active_status": self.active_status_stored()}

    @staticmethod
    def default_category_data(name: str, name_ar: str = "", display_order: int = 700, **overrides) -> dict:
        if not name.startswith(QCTEST_PBI_PREFIX):
            raise ValueError(f"disposable categories must use a {QCTEST_PBI_PREFIX}<agent>- name")
        data = {KC_NAME: name, f"{KC_NAME}_ar": name_ar or f"{name} تصنيف تجريبي",
                KC_DISPLAY_ORDER: display_order, "active_status": True}
        data.update(overrides)
        return data

"""
cms/pages/photo_gallery/event_category_admin_page.py — EventCategoryAdminPage.

`/web/qatar-chamber/manage-event-category` ("Photo Gallery Event Category",
slug "event-category") for PBI 130714. Read live 2026-10-05 as Site Content
Editor (156488): the form has exactly

  - Event Category Name (`ObjectField_categoryName`, required) and its
    Arabic twin `#qc-ar-categoryName` ("Event Category Name — العربية *"),
  - Display Order (`ObjectField_displayOrder`, number, required),
  - Active Status (`ObjectField_activeStatus`, ticked by default),

then Save as Draft / Publish (Editor). There is NO separate "Publish Status"
field: publication is the workflow status (row badge) plus Active Status.
Three real categories exist (Institutional 144315, Collaboration 144319,
Events 144323; codes QCDEMO-130714-EVENT_CATEGORY-*) — never acted on.
The row Preview opens `/web/qatar-chamber/photo-gallery?qcPreview=eventcategories%3A<id>`.

All lifecycle / guarded-delete helpers come from GalleryAdminPage.
"""

from __future__ import annotations

from cms.pages.photo_gallery.gallery_admin_base import GalleryAdminPage

EVENT_CATEGORY_SLUG = "event-category"
K_CATEGORY_NAME = "categoryName"
K_DISPLAY_ORDER = "displayOrder"
K_ACTIVE_STATUS = "activeStatus"

LABEL_CATEGORY_NAME = "Event Category Name"
LABEL_CATEGORY_NAME_AR = "Event Category Name — العربية"
LABEL_DISPLAY_ORDER = "Display Order"
LABEL_ACTIVE_STATUS = "Active Status"

REAL_CATEGORY_NAMES = ("Institutional", "Collaboration", "Events")


class EventCategoryAdminPage(GalleryAdminPage):
    TITLE_KEY = K_CATEGORY_NAME

    def __init__(self, page, prefix: str, evidence_dir: str):
        super().__init__(page, EVENT_CATEGORY_SLUG, prefix, evidence_dir)

    def fill_category(self, data: dict) -> "EventCategoryAdminPage":
        """Keys: name, name_ar, display_order, active (None/absent = untouched)."""
        if data.get("name") is not None:
            self.fill_en(K_CATEGORY_NAME, data["name"])
        if data.get("name_ar") is not None:
            self.fill_ar(K_CATEGORY_NAME, data["name_ar"])
        if data.get("display_order") is not None:
            self.fill_number(K_DISPLAY_ORDER, str(data["display_order"]))
        if data.get("active") is not None:
            self.set_active_status(bool(data["active"]))
        return self

    def read_category(self) -> dict:
        return {
            "name": self.text_value(K_CATEGORY_NAME),
            "name_ar": self.ar_value(K_CATEGORY_NAME),
            "display_order": self.text_value(K_DISPLAY_ORDER),
            "active": self.active_status_stored(),
        }


# --- PB ---
# Agent PB (field validation, cases 143151-143153). PBFieldsMixin
# (pb_form_support.py) is mixed in FRONT of PA's EventCategoryAdminPage: it adds
# readers only and a role-pinned open(); no PA method is changed. Display Order
# is `input[type=number]` with min -2147483648, so a negative value is NOT
# stopped by the browser (live 2026-10-05).
from cms.pages.photo_gallery.pb_form_support import (  # noqa: E402
    PB_EVIDENCE_DIR as _PB_EVIDENCE_DIR,
    PB_QCTEST_PREFIX as _PB_QCTEST_PREFIX,
    PBFieldsMixin as _PBFieldsMixin,
)

CATEGORY_NAME_LIMIT = 200


class EventCategoryFieldsPB(_PBFieldsMixin, EventCategoryAdminPage):
    """manage-event-category for Agent PB (QCTEST-130714-PB- namespace)."""

    def __init__(self, page):
        EventCategoryAdminPage.__init__(self, page, _PB_QCTEST_PREFIX, _PB_EVIDENCE_DIR)
        self.pb_init()

    def fill_category_pb(self, data: dict) -> "EventCategoryFieldsPB":
        """Same keys as fill_category(); text goes in with a change event."""
        if data.get("name") is not None:
            self.fill_en_change(K_CATEGORY_NAME, data["name"])
        if data.get("name_ar") is not None:
            self.fill_ar_change(K_CATEGORY_NAME, data["name_ar"])
        rest = {k: v for k, v in data.items() if k in ("display_order", "active")}
        return self.fill_category(rest)

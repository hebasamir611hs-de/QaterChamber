"""
cms/pages/home_services/our_services_admin_page.py — ServiceCardAdminPage /
OurServicesSectionAdminPage.

Object Authoring Page Objects for PBI 129371 (QC-HOME-003 — Our Services),
added 2026-10-15 (Phase 3). The older HomeServicesAdminPage drives the retired
Content & Data path and is not used by the new tests.

READ LIVE 2026-10-15 (Editor, sidebar + forms, nothing saved by the read):
  - Sidebar: "Our Services Section" (manage-our-services-section), "Service
    Card" (manage-service-card), "Filter Tab" (manage-filter-tab), "Our
    Services Tab Mapping" (manage-our-services-tab-mapping). Bug 139172 (Done)
    moved the section Tag / Heading / Description into the section object.
  - Our Services Section is a SINGLETON ("holds this one record"): one row,
    QCDEMO-129371-OSS-DEFAULT, PUBLISHED. Fields: Section Tag, Section Heading
    (required, bilingual "— العربية" twin), Section Description (textarea,
    bilingual), Active Status. No View All label/URL field on it.
  - Service Card: Image Thumbnail, Icon (pickers, required), Title (required,
    bilingual), Short Description (bilingual), Redirect URL (required),
    Display Order (required), Active Status, Assigned Tab (required). The
    Entry column shows the Title; real rows are QCDEMO-129371-SERVICE_CARD-NN.
  - Filter tabs: All Services / Membership / Legal / E-Services / Information
    (QCDEMO-129371-FILTER_TAB-01..05).
  - The Editor's workflow button reads "Publish".
"""

from __future__ import annotations

from cms.pages.components.disposable_object_admin import (
    DisposableObjectAdminPage,
    FieldSpec as F,
)

OSS_ENTRY_CODE = "QCDEMO-129371-OSS-DEFAULT"


def default_png(name: str = "QCTEST-service-card-default.png", size=(400, 300)) -> str:
    """A small valid PNG in temp (never fixtures/), made once per process."""
    import tempfile
    from pathlib import Path

    from PIL import Image

    path = Path(tempfile.gettempdir()) / name
    if not path.exists():
        Image.new("RGB", size, (20, 60, 120)).save(path, "PNG")
    return str(path)


class ServiceCardAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Service Card"
    SLUG = "service-card"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "title"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "thumbnail": F("Image Thumbnail", kind="file", required=True, confirmed_live=True),
        "icon": F("Icon", kind="file", required=True, confirmed_live=True),
        "title": F("Title", required=True, bilingual=True, confirmed_live=True),
        "short_description": F("Short Description", bilingual=True, confirmed_live=True),
        "redirect_url": F("Redirect URL", kind="url", required=True,
                          default="https://qatarchamber.com/en/services", confirmed_live=True),
        # Multiples of 100; 9900 sorts a QCTEST card after every real card.
        "display_order": F("Display Order", kind="number", required=True, default="9900",
                           confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
        "assigned_tab": F("Assigned Tab", kind="select", required=True, default="Information",
                          confirmed_live=True),
    }

    def fill_required(self, title, skip=(), active=False, files=None):
        """Both pickers get a small QCTEST PNG unless given or skipped."""
        files = dict(files or {})
        for key in ("thumbnail", "icon"):
            if key not in skip:
                files.setdefault(key, default_png())
        return super().fill_required(title, skip=skip, active=active, files=files)

    def value(self, key: str, locale: str = "en") -> str:
        if self.spec(key).kind == "file":
            return self.current_file_name(self.spec(key).label) or self.uploaded_filename(self.spec(key).label)
        return super().value(key, locale)

    def entry_code(self, title: str) -> str:
        """The record's Entry code, read from its row's Edit link."""
        self.filter_entries(title)
        row = self._row_locator(title)
        href = row.locator("a[href*='editEntry=']").first.get_attribute("href") or ""
        return href.split("editEntry=", 1)[-1].split("&", 1)[0]


class OurServicesSectionAdminPage(DisposableObjectAdminPage):
    """The ONE live section record. Never deleted, never created; a test that
    writes to it restores the snapshot and leaves it Published."""

    SIDEBAR_LABEL = "Our Services Section"
    SLUG = "our-services-section"
    SLUG_CONFIRMED_LIVE = True
    SINGLETON = True
    TITLE_FIELD = "section_tag"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "section_tag": F("Section Tag", required=True, bilingual=True, confirmed_live=True),
        "section_heading": F("Section Heading", required=True, bilingual=True, confirmed_live=True),
        "section_description": F("Section Description", bilingual=True, confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }
    TEXT_KEYS = ("section_tag", "section_heading", "section_description")

    def open_record(self, role: str) -> "OurServicesSectionAdminPage":
        self.sign_in(role)
        self.open_entry_by_code(OSS_ENTRY_CODE)
        return self

    def snapshot(self) -> dict:
        """Every text value, EN and AR, plus Active Status, from the open form."""
        snap = {f"{k}:{loc}": self.value(k, loc) for k in self.TEXT_KEYS for loc in ("en", "ar")}
        snap["active_status"] = self.flag("active_status")
        return snap

    def apply(self, snap: dict) -> "OurServicesSectionAdminPage":
        for key, val in snap.items():
            if key == "active_status":
                self.set_flag("active_status", bool(val))
                continue
            field, loc = key.split(":")
            self.fill(field, val, locale=loc)
        return self

    def list_status(self) -> str:
        self.open_entries_list()
        return self.row_status_text_by_code(OSS_ENTRY_CODE)


class FilterTabAdminPage(DisposableObjectAdminPage):
    """Filter Tab (read live 2026-10-15): Tab Label (required, bilingual),
    Display Order (required), Active Status. Entry column = Tab Label."""

    SIDEBAR_LABEL = "Filter Tab"
    SLUG = "filter-tab"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "tab_label"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "tab_label": F("Tab Label", required=True, bilingual=True, confirmed_live=True),
        # 9900 puts a QCTEST tab after the five real tabs.
        "display_order": F("Display Order", kind="number", required=True, default="9900",
                           confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }

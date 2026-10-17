"""
cms/pages/photo_gallery/page_hero_admin_page.py — PageHeroAdminPage (Agent PB).

`/web/qatar-chamber/manage-page-hero` ("Photo Gallery Page Hero", slug
"page-hero") for PBI 130714. Read live 2026-10-05 as the Site Content Editor
(156488), read-only, before any test wrote to it:

  FORM
    Page Title            input[name=ObjectField_pageTitle]  required, NO maxlength
    Page Title — العربية * #qc-ar-pageTitle                    required, NO maxlength
    Hero Background Image input[name=ObjectField_heroBackgroundImage] required,
                          accept ".jpg,.jpeg,.png", help line
                          "Upload a .jpg,.jpeg,.png no larger than 2 MB."
    Active Status         checkbox, ticked by default
    Save as Draft / Publish ("As an Editor, what you publish here goes live
    straight away.")

  THE TWO REAL RECORDS — NEVER DELETED, NEVER LEFT CHANGED
    "Photo Albums"  code QCDEMO-130714-PAGE_HERO-listing  id 144327  (listing hero,
                    AR "ألبومات الصور", image hero-photo-gallery.jpg)
    "Album details" code QCDEMO-130714-PAGE_HERO-details  id 144333  (detail hero)
  Both PUBLISHED + Active. The public listing `/web/qatar-chamber/photo-gallery`
  renders the listing record's Page Title in `h1.qc-pgl-hero-title`.

  Rules this module enforces (TEST_OWNED snapshot/restore, Annual Reports Page
  pattern, commit d422936):
    - there is no delete / unpublish method for a real record here;
    - `snapshot()` reads every field (EN + AR title, Active Status, stored
      image name AND its bytes' sha256, row status) off a FRESH open BEFORE a
      test edits anything; `restore()` writes back only what differs, publishes,
      and re-verifies from a fresh open (`remaining` must be empty);
    - validation cases that must not create a record (empty image, oversized
      image) run on the CREATE form with Active Status unticked; anything that
      unexpectedly saves is a QCTEST-130714-PB- record captured by id and removed
      through PA's guarded `delete_own_entry()`.
"""

from __future__ import annotations

import hashlib
import os
import tempfile

from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.photo_gallery.gallery_admin_base import GalleryAdminPage
from cms.pages.photo_gallery.pb_form_support import PB_EVIDENCE_DIR, PB_QCTEST_PREFIX, PBFieldsMixin, norm
from core.utils.logger import get_logger

logger = get_logger("page_hero_admin_page")

PAGE_HERO_SLUG = "page-hero"
K_PAGE_TITLE = "pageTitle"
K_HERO_IMAGE = "heroBackgroundImage"

HERO_LISTING_CODE = "QCDEMO-130714-PAGE_HERO-listing"
HERO_LISTING_ID = "144327"
HERO_DETAILS_CODE = "QCDEMO-130714-PAGE_HERO-details"
HERO_DETAILS_ID = "144333"
REAL_HEROES = {HERO_LISTING_CODE: HERO_LISTING_ID, HERO_DETAILS_CODE: HERO_DETAILS_ID}

HERO_IMAGE_HELP = "Upload a .jpg,.jpeg,.png no larger than 2 MB."
HERO_IMAGE_MAX_BYTES = 2 * 1024 * 1024
PAGE_TITLE_LIMIT = 100


class PageHeroAdminPage(PBFieldsMixin, GalleryAdminPage):
    TITLE_KEY = K_PAGE_TITLE

    def __init__(self, page):
        GalleryAdminPage.__init__(self, page, PAGE_HERO_SLUG, PB_QCTEST_PREFIX, PB_EVIDENCE_DIR)
        self.pb_init()

    # ---- real records (read + guarded edit only) -------------------------------
    @staticmethod
    def _check_real(code: str) -> None:
        if code not in REAL_HEROES:
            raise ValueError(f"{code!r} is not one of the two real Page Hero records")

    def open_real(self, code: str = HERO_LISTING_CODE) -> "PageHeroAdminPage":
        """Opens a real hero's edit form (English interface) fully hydrated."""
        self._check_real(code)
        self.open_entry_en(code)
        self.wait_arabic_ready()
        return self

    def real_row_status(self, code: str = HERO_LISTING_CODE) -> str:
        self._check_real(code)
        self.open_list_all()
        rows = [r for r in self.list_rows() if r["entry_id"] == REAL_HEROES[code]]
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        return normalize_status(rows[0]["status"]) if len(rows) == 1 else ""

    def read_form(self) -> dict:
        return {"title": self.text_value(K_PAGE_TITLE), "title_ar": self.ar_value(K_PAGE_TITLE),
                "active": self.active_status_stored(), "image": self.stored_file_placeholder_name(K_HERO_IMAGE)}

    def snapshot(self, code: str = HERO_LISTING_CODE, keep_bytes_in: str | None = None) -> dict:
        """Every value a test can touch, read off a FRESH open; optionally keeps
        the stored image's bytes on disk (for a byte-exact restore)."""
        self.open_real(code)
        snap = {"code": code, **self.read_form()}
        data = self.file_bytes(K_HERO_IMAGE)
        snap["image_sha256"] = hashlib.sha256(data).hexdigest() if data else ""
        snap["image_size"] = len(data)
        if keep_bytes_in and data and snap["image"]:
            path = os.path.join(keep_bytes_in, snap["image"])
            with open(path, "wb") as handle:
                handle.write(data)
            snap["image_path"] = path
        snap["row_status"] = self.real_row_status(code)
        return snap

    @staticmethod
    def differences(baseline: dict, current: dict) -> list[str]:
        keys = ("title", "title_ar", "active", "image", "image_sha256", "row_status")
        return [k for k in keys if norm(current.get(k)) != norm(baseline.get(k))]

    def restore(self, baseline: dict) -> dict:
        """Writes back whatever differs from `baseline`, publishes, and verifies from a
        fresh open. Returns {"changed", "remaining", "final"}."""
        code = baseline["code"]
        self._check_real(code)
        current = self.snapshot(code)
        diffs = self.differences(baseline, current)
        report = {"changed": diffs, "remaining": [], "final": current}
        if not diffs:
            return report
        self.open_real(code)
        if "title" in diffs:
            self.fill_en_change(K_PAGE_TITLE, baseline["title"])
        if "title_ar" in diffs:
            self.fill_ar_change(K_PAGE_TITLE, baseline["title_ar"])
        if "active" in diffs:
            self.set_active_status(baseline["active"] == "true")
        if {"image", "image_sha256"} & set(diffs):
            path = baseline.get("image_path", "")
            if not path or not os.path.exists(path):
                raise AssertionError("the hero image differs from the baseline but its bytes were not captured")
            self.upload_pb(K_HERO_IMAGE, path)
        self.click_publish()
        if not self.save_went_through():
            raise AssertionError(f"restore Publish was refused: {self.pb_refusal_evidence()}")
        final = self.snapshot(code)
        report["final"] = final
        remaining = self.differences(baseline, final)
        # a byte-identical re-upload necessarily gets a new D&M name; the sha is what matters
        if "image" in remaining and "image_sha256" not in remaining:
            remaining.remove("image")
        report["remaining"] = remaining
        if final.get("row_status") != STATUS_PUBLISHED:
            report["remaining"].append("row_status")
        return report

    @staticmethod
    def scratch_dir() -> str:
        path = os.path.join(tempfile.gettempdir(), "qctest_130714_pb_hero_baseline")
        os.makedirs(path, exist_ok=True)
        return path

    # ---- create-form helpers (validation without a record) -----------------------
    def fill_hero(self, data: dict) -> "PageHeroAdminPage":
        """Keys: title, title_ar, image (path), active (None/absent = untouched)."""
        if data.get("title") is not None:
            self.fill_en_change(K_PAGE_TITLE, data["title"])
        if data.get("title_ar") is not None:
            self.fill_ar_change(K_PAGE_TITLE, data["title_ar"])
        if data.get("image"):
            self.upload_pb(K_HERO_IMAGE, data["image"], data.get("image_stem"))
        if data.get("active") is not None:
            self.set_active_status(bool(data["active"]))
        return self

    def image_help_text(self) -> str:
        text = self.field_block_text(K_HERO_IMAGE)
        return HERO_IMAGE_HELP if HERO_IMAGE_HELP in text else text

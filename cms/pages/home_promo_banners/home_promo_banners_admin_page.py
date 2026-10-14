"""
cms/pages/home_promo_banners/home_promo_banners_admin_page.py —
PromotionalBannerAdminPage.

Control_Panel Page Object for PBI 129368 (QC-HOME-002 — Promotional Banners /
Ad Slots). Public counterpart: web/pages/home_promo_banners/home_promo_banners_page.py.

REWRITTEN 2026-10-07 (Phase 3). The previous version drove Content & Data
(retired for Object-Definition records), fell back to a TEST_USER login, and
deleted the `.first` row matching a substring with no QCTEST guard. All three
are gone: this class extends DisposableObjectAdminPage, so it signs in through
`config.settings.cms_role_credentials()`, works only on Object Authoring
(`manage-promotional-banner`), and deletes only an exact `QCTEST-*` title.

OBJECT NAME. `cms/Content-Admin-Guide.docx` §16: **PromotionalBanner** —
bannerImageEN/AR, bannerImageMobileEN/AR (optional), bannerAltTextEN/AR,
redirectUrl ("bilingual"), openInNewTab, startDate/endDate (optional),
displayOrder, activeStatus. Slug = lower-kebab of the name.

READ LIVE 2026-10-07 (read-only probe, Editor + Author, no record touched):
  - Sidebar label "Promotional Banner" -> /web/qatar-chamber/manage-promotional-banner.
  - Form labels exactly as in FIELDS below. The date inputs are native
    `<input type="date" name="ObjectField_startDate|endDate">` and are driven
    by name, ISO `YYYY-MM-DD`.
  - "Redirect URL" is bilingual: EN control `Redirect URL`, AR control
    `Redirect URL — العربية` (CORRECTED 2026-10-07: the first probe only
    enumerated `name^=ObjectField_redirectUrl` and missed the AR control).
  - The non-draft submit button is `button[type=submit][name=status]` and its
    visible label on this object is not the one ObjectAuthoringPage expects,
    so SUBMIT_FOR_REVIEW_BUTTON is overridden by structure (name=status, not
    the draft button), not by label.
  - Entries list: Entry (= Banner Alt Text (EN)) | Status | Last modified |
    Actions; 3 real rows, all PUBLISHED; an Editor's rows render only
    `data-qc-oel-delete` (no unpublish/history attribute on these rows).
  - Real rows (never touched): the three alt texts in REAL_BANNER_TITLES.

Display Order default 9900: multiples of 100 (OBJECT-AUTHORING-GUIDE), and it
sorts a QCTEST banner after the real ones.
"""

from __future__ import annotations

import re

from cms.pages.components.disposable_object_admin import (
    DisposableObjectAdminPage,
    FieldSpec as F,
)
from cms.pages.components.object_authoring_page import (
    STATUS_ARCHIVED,
    STATUS_DRAFT,
    STATUS_PENDING_REVIEW,
    STATUS_PUBLISHED,
    STATUS_REJECTED,
    STATUS_SCHEDULED,
    STATUS_UNKNOWN,
    STATUS_UNPUBLISHED,
    normalize_status,
)

REAL_BANNER_TITLES = (
    "Verified by Qatar Chamber — stand out with trusted verification",
    "Qatar Chamber Commercial & Industrial Directory — register your business",
    "Get Verified by Qatar Chamber",
)


class PromotionalBannerAdminPage(DisposableObjectAdminPage):
    SIDEBAR_LABEL = "Promotional Banner"
    SLUG = "promotional-banner"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "alt_en"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "image_en": F("Banner Image (EN)", kind="file", required=True, confirmed_live=True),
        "image_ar": F("Banner Image (AR)", kind="file", required=True, confirmed_live=True),
        "alt_en": F("Banner Alt Text (EN)", required=True, max_len=150, confirmed_live=True),
        "alt_ar": F("Banner Alt Text (AR)", required=True, max_len=150,
                    default="بانر اختبار QCTEST", confirmed_live=True),
        # Bilingual (guide §16; PBI "Redirect URL (Per Lang.)"): the AR control is
        # labelled "Redirect URL — العربية" (seen live 2026-10-07 on the form
        # screenshot reports/manual-repro-129368-image-en-big-submit.png).
        "redirect_url": F("Redirect URL", kind="url", ref="redirectUrl", bilingual=True, confirmed_live=True),
        "open_new_tab": F("Open in New Tab", kind="checkbox", confirmed_live=True),
        "display_order": F("Display Order", kind="number", required=True, default="9900",
                           confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
        "start_date": F("Start Date", kind="date", ref="startDate", confirmed_live=True),
        "end_date": F("End Date", kind="date", ref="endDate", confirmed_live=True),
    }

    # Structural match (see module docstring): the workflow submit is the
    # name=status submit button that is not Save as Draft.
    SUBMIT_FOR_REVIEW_BUTTON = 'button[type="submit"][name="status"]:not(:text-is("Save as Draft"))'
    DATE_FORMAT = "%Y-%m-%d"

    def fill(self, key: str, value: str, locale: str = "en") -> "PromotionalBannerAdminPage":
        spec = self.spec(key)
        if spec.kind == "date":
            self.page.locator(f'input[name="ObjectField_{spec.ref}"]').fill(value)
            return self
        return super().fill(key, value, locale)

    def value(self, key: str, locale: str = "en") -> str:
        spec = self.spec(key)
        if spec.kind == "date":
            return self.page.locator(f'input[name="ObjectField_{spec.ref}"]').input_value()
        if spec.kind == "file":
            # HEALED 2026-10-07 (run 1638): on a reopened, saved record the
            # attached file shows as "Current file: ..." (current_file_name);
            # uploaded_filename() only reflects a newly picked, unsaved file.
            return self.current_file_name(spec.label) or self.uploaded_filename(spec.label)
        return super().value(key, locale)

    # HEALED 2026-10-07 (run 1638): a Published row with Active Status off
    # rendered a status cell that normalize_status() maps to "Unknown" (the
    # cell carries more than the bare badge). Read the workflow word out of
    # the cell instead; the raw text is kept for assertion messages.
    _STATUS_SEARCH_ORDER = (
        STATUS_UNPUBLISHED, STATUS_PENDING_REVIEW, STATUS_PUBLISHED, STATUS_DRAFT,
        STATUS_REJECTED, STATUS_ARCHIVED, STATUS_SCHEDULED,
    )
    last_status_raw: str = ""

    def row_status_text(self, title: str) -> str:
        self.filter_entries(title)
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title}")')
        if row.count() == 0:
            self.last_status_raw = ""
            return ""
        raw = row.first.locator("td").nth(1).inner_text()
        self.last_status_raw = raw
        exact = normalize_status(raw)
        if exact != STATUS_UNKNOWN:
            return exact
        collapsed = " ".join(raw.split()).casefold()
        for status in self._STATUS_SEARCH_ORDER:
            if re.search(rf"(?<![a-z]){re.escape(status.casefold())}(?![a-z])", collapsed):
                return status
        return STATUS_UNKNOWN

    # HEALED 2026-10-07 (run 1638): "Select File" clicks timed out when the
    # previous picker iframe had not detached yet. Wait for it to go, and
    # retry the upload once after clearing overlays.
    def upload(self, key: str, fixture_path: str, tag: str = "") -> "PromotionalBannerAdminPage":
        from core.web.overlays import dismiss_overlays

        modal = self.page.locator(self.UPLOAD_MODAL_IFRAME)
        try:
            modal.first.wait_for(state="detached", timeout=30000)
        except Exception:  # noqa: BLE001
            self.page.keyboard.press("Escape")
        try:
            return super().upload(key, fixture_path, tag)
        except Exception:  # noqa: BLE001 — one retry, then the real error surfaces
            self.page.keyboard.press("Escape")
            dismiss_overlays(self.page)
            return super().upload(key, fixture_path, tag)

    def unpublish(self, title: str) -> "PromotionalBannerAdminPage":
        """Unpublish as the product offers it: the row action when the row
        renders one, otherwise the in-form Unpublish control on the record."""
        self.open_list("Site Content Editor")
        if self.row_offers_action(title, "unpublish"):
            self.unpublish_entry(title)
        else:
            self.open_entry_by_edit_link(title)
            self.unpublish_to_edit_as_draft()
        return self

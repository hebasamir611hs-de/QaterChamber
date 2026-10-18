"""
cms/pages/home_hero_banner/hero_banner_fields_admin_page.py —
HeroSlideFieldsAdminPage / AchievementCounterFieldsAdminPage.

Disposable-record Page Objects for the PBI 129367 (QC-HOME-001 — Hero Banner)
field cases, added 2026-10-15 (Phase 3). They extend DisposableObjectAdminPage,
so they sign in through `cms_role_credentials()` (never TEST_USER), work only on
Object Authoring and only on `QCTEST-*` records, and can be driven by
cms/tests/authoring_checks.py. The older HeroBannerSlideAdminPage in
home_hero_banner_admin_page.py is left as it is for the tests that still use it.

READ LIVE 2026-10-15 (Editor, new-entry form, nothing saved by the read):
  - manage-hero-banner-slide: Banner Image (picker, ObjectField_bannerImage,
    required) · Banner Title (EN)/(AR) (required) · Banner Subtitle
    (Description) (EN)/(AR) (textarea, optional) · Button 1 Label (EN)/(AR),
    Button 1 Link, Button 2 Label (EN)/(AR), Button 2 Link (all required) ·
    Display Order (number, required) · Active Status · Counters Active Status.
    EN and AR are SEPARATE fields here, not one bilingual field with an
    "— العربية" twin.
  - manage-achievement-counter: Counter Title (EN)/(AR), Counter Value, Counter
    Icon (picker), Counter Display Order, Counter Active Status, Active Status.
    No field carries `required`.
  - The Entry column of a new record shows its UUID, not its title. The
    entries search DOES match the title (one row comes back for a unique
    QCTEST title), so a title resolves to its code through that search and
    every row action then runs against the code. Probe record kept:
    `QCTEST-PROBE-hero-entry` (f232cf8a-dd1d-bbb4-c6f2-1cf142393f5e, Draft).
  - Required text inputs are enforced by native HTML5 validation, which writes
    no DOM message. A refusal therefore also counts the browser's
    `validationMessage` on an invalid required control.
"""

from __future__ import annotations

from cms.pages.components.disposable_object_admin import (
    DisposableObjectAdminPage,
    FieldSpec as F,
)
from core.utils.waits import WaitTimeoutError, wait_until

BANNER_IMAGE_LIBRARY_FOLDER = "Flickr"
BANNER_IMAGE_LIBRARY_FILE = "download.png"


def default_banner_png() -> str:
    """A small valid PNG in temp (never fixtures/), made once per process."""
    import tempfile
    from pathlib import Path

    from PIL import Image

    path = Path(tempfile.gettempdir()) / "QCTEST-hero-banner-default.png"
    if not path.exists():
        Image.new("RGB", (1200, 500), (120, 20, 40)).save(path, "PNG")
    return str(path)


class _UuidEntryAdmin(DisposableObjectAdminPage):
    """Entry column = UUID. Titles are resolved to codes through the search."""

    _codes: dict

    def __init__(self, page):
        super().__init__(page)
        self._codes = {}

    SEARCH_BUDGET_S = 30.0
    SEARCH_RETRY_S = 4.0

    def _search_rows(self, text: str) -> list[str]:
        """Codes of the rows the entries search returns for `text`. A fresh
        record reaches the search index a few seconds after its save, so an
        empty result is searched again (every SEARCH_RETRY_S, up to
        SEARCH_BUDGET_S) until exactly one row comes back."""
        import time

        box = self.page.locator(self.ENTRIES_SEARCH_INPUT)
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        if box.count() == 0:
            return []
        codes: list[str] = []
        deadline = time.monotonic() + self.SEARCH_BUDGET_S
        while True:
            box.fill(text)
            box.press("Enter")
            seen: dict = {}

            def _one() -> bool:
                n = rows.count()
                seen["codes"] = [rows.nth(i).locator("td").first.inner_text().strip() for i in range(n)]
                return n == 1

            try:
                wait_until(_one, timeout=self.SEARCH_RETRY_S, poll=0.5)
            except WaitTimeoutError:
                pass
            codes = seen.get("codes", [])
            if len(codes) == 1 or time.monotonic() >= deadline:
                return codes

    def code_for(self, title: str) -> str:
        """The Entry code of the ONE record whose content matches `title`.
        Searches every time, so the row is also the one on screen."""
        codes = self._search_rows(title)
        if len(codes) == 1:
            self._codes[title] = codes[0]
            return codes[0]
        return ""

    def filter_entries(self, text: str):
        self.code_for(text)  # leaves the list filtered to that one row
        return self

    def _as_code(self, title_or_code: str) -> str:
        return self.code_for(title_or_code) or title_or_code

    def row_status_text(self, title: str) -> str:
        code = self.code_for(title)
        return self.row_status_text_by_code(code) if code else ""

    def row_visible(self, title: str) -> bool:
        return bool(self.code_for(title))

    def open_entry_by_edit_link(self, title: str):
        code = self.code_for(title)
        assert code, f"no single entry matches {title!r}"
        self.open_entry_by_code(code)
        return self

    def _run_row_action(self, title_or_code: str, action: str, comment: str = ""):
        return super(DisposableObjectAdminPage, self)._run_row_action(self._as_code(title_or_code), action, comment)

    def row_offers_action(self, title: str, action: str) -> bool:
        code = self.code_for(title)
        return bool(code) and self._row_locator(code).locator(f"[{self.ROW_ACTION_ATTRS[action]}]").count() > 0

    def row_preview_url(self, title: str) -> str:
        code = self.code_for(title)
        return self.row_preview_url_by_code(code) if code else ""

    def history_entries(self, title_or_code: str):
        return super().history_entries(self._as_code(title_or_code))

    def open_list(self, role: str, locale: str | None = "en"):
        self._codes = {}
        return super().open_list(role, locale)

    def delete_disposable(self, title: str, role: str = "Site Content Editor") -> bool:
        """The base matches the row by `:has-text(title)`, but here the Entry
        column shows the UUID, so it never found a row and returned False —
        every QCTEST row of the 2026-10-15 run was silently kept (healed
        2026-10-18). Resolves the ONE row the exact-title search returns to
        its code, then deletes that row by code. Never raises."""
        from cms.pages.components.disposable_object_admin import DISPOSABLE_PREFIX
        from cms.pages.components.object_authoring_page import ObjectAuthoringPage

        if not title.startswith(DISPOSABLE_PREFIX):
            raise ValueError(f"refusing to delete non-disposable record {title!r}")
        try:
            self.open_list(role)
            code = self.code_for(title)  # leaves the list filtered to that one row
            if not code:
                return False
            ObjectAuthoringPage._run_row_action(self, code, "delete")
            self.open_list(role)
            return not self.code_for(title)
        except Exception:  # noqa: BLE001
            return False

    # ---- refusal: native HTML5 required validation leaves no DOM text ---
    def _refusal_messages(self) -> list[str]:
        out = super()._refusal_messages()
        # A successful save navigates to `?previewEntry=<id>` and shows a NEW,
        # empty form, whose blank required fields are not a refusal (healed
        # 2026-10-15: 135089 read them as one). Native messages count only
        # while the page is still the form that was submitted.
        if "previewEntry=" in self.page.url:
            return out
        native = self.page.evaluate(
            """() => [...document.querySelectorAll('form input, form textarea')]
                 .filter(e => e.willValidate && !e.checkValidity())
                 .map(e => `${e.name}: ${e.validationMessage}`)"""
        )
        return out + list(native)


class HeroSlideFieldsAdminPage(_UuidEntryAdmin):
    SIDEBAR_LABEL = "Hero Banner Slide"
    SLUG = "hero-banner-slide"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "title_en"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "image": F("Banner Image", kind="file", required=True, confirmed_live=True),
        "title_en": F("Banner Title (EN)", required=True, max_len=100, confirmed_live=True),
        "title_ar": F("Banner Title (AR)", required=True, max_len=100,
                      default="شريحة اختبار QCTEST", confirmed_live=True),
        "subtitle_en": F("Banner Subtitle (Description) (EN)", confirmed_live=True),
        "subtitle_ar": F("Banner Subtitle (Description) (AR)", confirmed_live=True),
        "b1_label_en": F("Button 1 Label (EN)", required=True, max_len=50, default="Learn More",
                         confirmed_live=True),
        "b1_label_ar": F("Button 1 Label (AR)", required=True, max_len=50, default="اعرف المزيد",
                         confirmed_live=True),
        "b1_link": F("Button 1 Link", kind="url", required=True,
                     default="https://qatarchamber.com/about-us", confirmed_live=True),
        "b2_label_en": F("Button 2 Label (EN)", required=True, max_len=50, default="Contact Us",
                         confirmed_live=True),
        "b2_label_ar": F("Button 2 Label (AR)", required=True, max_len=50, default="تواصل معنا",
                         confirmed_live=True),
        "b2_link": F("Button 2 Link", kind="url", required=True,
                     default="https://qatarchamber.com/contact-us", confirmed_live=True),
        # Multiples of 100 (OBJECT-AUTHORING-GUIDE); 9900 sorts a QCTEST slide
        # after every real slide.
        "display_order": F("Display Order", kind="number", required=True, default="9900",
                           confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
        "counters_active": F("Counters Active Status", kind="checkbox", confirmed_live=True),
    }

    def fill_required(self, title, skip=(), active=False, files=None):
        """As the base, but Banner Image always gets a small QCTEST PNG unless
        another fixture is given or the field is skipped. CORRECTED
        2026-10-15: the library file Flickr/download.png is no longer listed
        in the Editor's picker, so the image is uploaded (a uniquely named
        QCTEST copy; D&M test files stay, per the cleanup policy)."""
        files = dict(files or {})
        if "image" not in skip:
            files.setdefault("image", default_banner_png())
        return super().fill_required(title, skip=skip, active=active, files=files)

    def pick_library_image(self):
        self.select_existing_file_from_library(
            self.spec("image").label, BANNER_IMAGE_LIBRARY_FOLDER, BANNER_IMAGE_LIBRARY_FILE
        )
        return self

    def value(self, key: str, locale: str = "en") -> str:
        if self.spec(key).kind == "file":
            return (self.page.locator('input[name="ObjectField_bannerImage"]').input_value()
                    or self.current_file_name(self.spec(key).label)
                    or self.uploaded_filename(self.spec(key).label))
        return super().value(key, locale)


class AchievementCounterFieldsAdminPage(_UuidEntryAdmin):
    SIDEBAR_LABEL = "Achievement Counter"
    SLUG = "achievement-counter"
    SLUG_CONFIRMED_LIVE = True
    TITLE_FIELD = "title_en"
    ACTIVE_FIELD = "active_status"
    FIELDS = {
        "title_en": F("Counter Title (EN)", confirmed_live=True),
        "title_ar": F("Counter Title (AR)", confirmed_live=True),
        "value": F("Counter Value", confirmed_live=True),
        "display_order": F("Counter Display Order", kind="number", default="9900", confirmed_live=True),
        "counter_active": F("Counter Active Status", kind="checkbox", confirmed_live=True),
        "active_status": F("Active Status", kind="checkbox", confirmed_live=True),
    }

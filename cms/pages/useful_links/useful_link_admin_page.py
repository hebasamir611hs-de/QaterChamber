"""
cms/pages/useful_links/useful_link_admin_page.py — UsefulLinkAdminPage.

Control_Panel Page Object for PBI 130702's "Useful Link" object
(`/web/qatar-chamber/manage-useful-link`) — one row per organization card
inside a Useful Link Category. Shares the session guard, Publish button,
validation reader and exact-title safe delete with the category object via
`_UsefulLinksAuthoringBase` (see useful_link_category_admin_page.py's module
docstring for the evidence trail and the ROLE / TEST-DATA notes that apply
here unchanged — Link Items are authored as the Site Content Editor; unlike
the Category form, the Editor's Link form binds `ObjectField_displayOrder`
correctly, confirmed live 2026-09-30).

CONFIRMED LIVE 2026-09-29 (throwaway Playwright probe scripts, TEST_USER,
1920x1080, under the cross-agent qcdev browser mutex):

  Form fields (exact accessible names):
    Logo            — attachment; hidden textbox "Logo Select File" + sibling
                      "Select File" button; filename readout <strong
                      aria-label="Logo">. Help line: "Upload a
                      .jpg,.jpeg,.png,.svg no larger than 2 MB." (required)
    textbox "Logo Alt Text" / "Logo Alt Text — العربية"   (optional)
    textbox "Organization Name"                (required, counter 0/150)
    textbox "Organization Name — العربية *"    (required)
    textbox "Website Label" / "Website Label — العربية"  (optional, 0/150)
    textbox "External URL"                     (required)
    Open Behavior   — select-from-list, options "Same Tab" / "New Tab"
                      (1st "Open Options Menu" button on the form)
    spinbutton "Display Order"                 (required)
    checkbox "Active Status"                   (unchecked by default)
    Link Category   — select-from-list of every category title
                      (2nd "Open Options Menu" button on the form)
  Buttons: "Save as Draft" / "Publish" (no "Submit for Review").

  Validation messages (verbatim):
    "Logo is required — upload a file before publishing."
    "External URL is not a valid URL — start it with https:// for another
     site, or with / for a page on this one."
    "External URL cannot be only spaces."
    "Organization Name is 151 characters; the maximum is 150."
    "Organization Name cannot be only spaces."
    "Website Label is 151 characters; the maximum is 150."
  Logo picker: a .bmp is refused inside the picker itself with "Please enter
  a file with a valid extension (.jpg,.jpeg,.png,.svg)." and no Add button.
  A 2.3 MB .png is ACCEPTED by the picker (Add button offered) — whether the
  2 MB limit is enforced at Publish is exactly what tc_140746 checks.

  List: 46 seeded rows, 10 per page — `open_list()` switches the page-size
  selector to "All" before any row lookup (never the client-side search
  filter; see the category module's FINDING note).

  Delete / Recycle Bin: row Delete moves the record to the list's own
  "Recycle Bin (n)" (`details[data-qc-oel-trash]`, Restore only — no
  permanent delete from the editor surface; re-confirmed live 2026-09-30 as
  admin: the bin's only per-entry control is `a[data-qc-oel-untrash]`
  "Restore"). A QCTEST link recycled out of a REAL category therefore stays
  in that bin as known debris.

  FINDING (candidate product defect): once a Link Item has been deleted (it
  sits in the Recycle Bin), its parent category can no longer be deleted —
  POST /o/qc-object-status/trash/<categoryId> answers HTTP 400
  {"error":"Delete failed: null"} and the editor sees nothing at all (the row
  simply stays). Reproduced live 2026-09-29 on QCTEST-PROBE-ULCAT-97350713;
  restoring the recycled link first made the category delete succeed.
  Teardown therefore restores such a child before deleting the category
  (UsefulLinkCategoryAdminPage.teardown_category()).

  Public card: `a.qc-ul-card` inside its category's panel; New Tab renders
  target="_blank" rel="noopener noreferrer"; `.qc-ul-org` = Organization
  Name, `.qc-ul-site` = Website Label.
"""

from __future__ import annotations

import os
import re
import shutil
import tempfile
import uuid

from cms.pages.useful_links.useful_link_category_admin_page import (
    FIELD_ACTIVE_STATUS,
    _UsefulLinksAuthoringBase,
)
from core.utils.logger import get_logger

logger = get_logger(__name__)

LINK_SLUG = "useful-link"

FIELD_LOGO = "Logo"
FIELD_LOGO_ALT_EN = "Logo Alt Text"
FIELD_LOGO_ALT_AR = "Logo Alt Text — العربية"
FIELD_ORG_NAME_EN = "Organization Name"
FIELD_ORG_NAME_AR = "Organization Name — العربية *"
FIELD_WEBSITE_LABEL_EN = "Website Label"
FIELD_WEBSITE_LABEL_AR = "Website Label — العربية"
FIELD_EXTERNAL_URL = "External URL"
FIELD_OPEN_BEHAVIOR = "Open Behavior"
FIELD_LINK_CATEGORY = "Link Category"
FIELD_DISPLAY_ORDER = "Display Order"

OPEN_BEHAVIOR_SAME_TAB = "Same Tab"
OPEN_BEHAVIOR_NEW_TAB = "New Tab"

MSG_LOGO_REQUIRED = "Logo is required"
MSG_URL_INVALID = "External URL is not a valid URL"
MSG_URL_SPACES = "External URL cannot be only spaces."
MSG_ORG_SPACES = "Organization Name cannot be only spaces."
MSG_ORG_MAX = "Organization Name is 151 characters; the maximum is 150."
MSG_LABEL_MAX = "Website Label is 151 characters; the maximum is 150."
MSG_PICKER_BAD_EXTENSION = "Please enter a file with a valid extension"
# CONFIRMED LIVE 2026-09-30: the picker answers this for a file whose NAME
# already exists in the site's Documents library (any earlier run that
# published a link with the same logo file leaves it there). A uniquely
# named copy of the same bytes uploads fine — tests upload per-test copies.
MSG_PICKER_UPLOAD_ERROR = "An unexpected error occurred while uploading your file."


class UsefulLinkAdminPage(_UsefulLinksAuthoringBase):
    """manage-useful-link — one row per organization card."""

    OPTIONS_MENU_BUTTON_NAME = "Open Options Menu"
    VISIBLE_OPTION = '[role="option"]:visible'

    ENTRY_TITLE_FIELD = FIELD_ORG_NAME_EN

    def __init__(self, page):
        super().__init__(page, LINK_SLUG)

    # ---- Select-from-list fields ------------------------------------------
    def _options_button(self, field: str):
        """Both select-from-list fields expose an identically named "Open
        Options Menu" button; each is scoped through its own input's
        aria-labelledby label text (Open Behavior / Link Category) rather
        than by position."""
        input_box = self.page.locator("input[id$='-select-from-list-input']")
        for i in range(input_box.count()):
            candidate = input_box.nth(i)
            label_ids = (candidate.get_attribute("aria-labelledby") or "").split()
            label_text = " ".join(
                self.page.locator(f"#{lid}").inner_text().strip() for lid in label_ids if lid
            )
            if label_text.startswith(field):
                return candidate.locator(
                    "xpath=ancestor::*[.//button[@aria-label='Open Options Menu']][1]"
                ).get_by_role("button", name=self.OPTIONS_MENU_BUTTON_NAME)
        raise AssertionError(f"No select-from-list field labelled {field!r} on the form")

    def _choose(self, field: str, option_text: str) -> None:
        self._options_button(field).click()
        option = self.page.locator(self.VISIBLE_OPTION).filter(
            has_text=re.compile(rf"^\s*{re.escape(option_text)}\s*$")
        ).first
        option.wait_for(state="visible", timeout=10000)
        option.click()

    def select_open_behavior(self, behavior: str) -> "UsefulLinkAdminPage":
        self._choose(FIELD_OPEN_BEHAVIOR, behavior)
        return self

    def select_category(self, category_title: str) -> "UsefulLinkAdminPage":
        self._choose(FIELD_LINK_CATEGORY, category_title)
        return self

    def select_list_value(self, field: str) -> str:
        """Visible label text currently shown in a select-from-list field."""
        input_box = self.page.locator("input[id$='-select-from-list-input']")
        for i in range(input_box.count()):
            candidate = input_box.nth(i)
            label_ids = (candidate.get_attribute("aria-labelledby") or "").split()
            label_text = " ".join(
                self.page.locator(f"#{lid}").inner_text().strip() for lid in label_ids if lid
            )
            if label_text.startswith(field):
                return candidate.input_value().strip()
        return ""

    # ---- Logo -----------------------------------------------------------------
    def upload_logo(self, file_path: str) -> "UsefulLinkAdminPage":
        """Uploads a logo expected to be valid; fails with the picker's own
        message (instead of a bare Add-button timeout) if it is refused."""
        result = self.attempt_logo_upload(file_path)
        if not result["accepted"]:
            raise AssertionError(f"Logo picker refused {file_path!r}: {result['message']!r}")
        return self

    def logo_filename(self) -> str:
        return self.uploaded_filename(FIELD_LOGO)

    @staticmethod
    def _uniquely_named_copy(file_path: str) -> str:
        """Same bytes, same extension, unique name (`<stem>-<8 hex><ext>`):
        the picker refuses a name already present in the Documents library
        (MSG_PICKER_UPLOAD_ERROR), and every published link leaves its logo
        there."""
        stem, ext = os.path.splitext(os.path.basename(file_path))
        target_dir = os.path.join(tempfile.gettempdir(), "useful_link_qctest_uploads")
        os.makedirs(target_dir, exist_ok=True)
        target = os.path.join(target_dir, f"{stem}-{uuid.uuid4().hex[:8]}{ext}")
        shutil.copyfile(file_path, target)
        return target

    def attempt_logo_upload(self, file_path: str) -> dict:
        """Opens the Logo picker and drops `file_path` into it WITHOUT
        assuming it is acceptable. Returns {"accepted": bool, "message": str}
        — accepted means the picker staged the file and offered its Add
        button (which is then clicked so the form carries the file); a
        refusal returns the picker's own message and closes the picker."""
        file_path = self._uniquely_named_copy(file_path)
        hidden = self.page.get_by_role("textbox", name=f"{FIELD_LOGO} Select File")
        hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path, timeout=60000)
        staged = frame.get_by_text("1 of 1")
        refused = frame.get_by_text(
            re.compile(f"{re.escape(MSG_PICKER_BAD_EXTENSION)}|{re.escape(MSG_PICKER_UPLOAD_ERROR)}")
        )
        try:
            staged.or_(refused).first.wait_for(state="visible", timeout=20000)
        except Exception:  # noqa: BLE001 — neither signal; report what the picker shows
            pass
        if refused.count() > 0:
            message = refused.first.inner_text().strip()
            self.page.keyboard.press("Escape")
            try:
                self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=8000)
            except Exception:  # noqa: BLE001
                pass
            return {"accepted": False, "message": message}
        frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT).click(timeout=15000)
        self.page.locator(self.UPLOAD_MODAL_IFRAME).wait_for(state="detached", timeout=15000)
        return {"accepted": True, "message": ""}

    # ---- Field fill ---------------------------------------------------------
    def fill_link(
        self,
        org_en: str | None = None,
        org_ar: str | None = None,
        website_label_en: str | None = None,
        website_label_ar: str | None = None,
        external_url: str | None = None,
        open_behavior: str | None = None,
        display_order: str | None = None,
        active: bool | None = None,
        category_title: str | None = None,
    ) -> "UsefulLinkAdminPage":
        text = lambda label: (lambda v: self._textbox(label).fill(v))  # noqa: E731
        fills = [
            (FIELD_ORG_NAME_EN, org_en, text(FIELD_ORG_NAME_EN)),
            (FIELD_ORG_NAME_AR, org_ar, text(FIELD_ORG_NAME_AR)),
            (FIELD_WEBSITE_LABEL_EN, website_label_en, text(FIELD_WEBSITE_LABEL_EN)),
            (FIELD_WEBSITE_LABEL_AR, website_label_ar, text(FIELD_WEBSITE_LABEL_AR)),
            (FIELD_EXTERNAL_URL, external_url, text(FIELD_EXTERNAL_URL)),
            (FIELD_DISPLAY_ORDER, display_order, self.set_display_order),
            (FIELD_ACTIVE_STATUS, active, self.set_active_status),
        ]
        fills += [
            (FIELD_OPEN_BEHAVIOR, open_behavior, self.select_open_behavior),
            (FIELD_LINK_CATEGORY, category_title, self.select_category),
        ]
        self._fill_verified([f for f in fills if f[1] is not None])
        return self

    def field(self, label: str) -> str:
        return self._textbox(label).input_value()

    def _holds(self, label: str, value) -> bool:
        if label in (FIELD_OPEN_BEHAVIOR, FIELD_LINK_CATEGORY):
            return self.select_list_value(label) == value
        return super()._holds(label, value)

    def create_link(
        self,
        org_en: str,
        category_title: str,
        logo_path: str,
        org_ar: str = "منظمة اختبار",
        external_url: str = "https://example.com",
        open_behavior: str = OPEN_BEHAVIOR_NEW_TAB,
        display_order: str = "100",
        active: bool = True,
        website_label_en: str | None = "example.com",
        website_label_ar: str | None = "example.com",
    ) -> bool:
        """Setup helper for tests whose subject is not the link form itself:
        a complete, valid Link Item published into `category_title`."""
        self.open_new_form()
        self.upload_logo(logo_path)
        self.fill_link(
            org_en=org_en, org_ar=org_ar, website_label_en=website_label_en,
            website_label_ar=website_label_ar, external_url=external_url,
            open_behavior=open_behavior, display_order=display_order, active=active,
            category_title=category_title,
        )
        return self.publish() or self.saved_despite_ambiguous_submit(org_en)

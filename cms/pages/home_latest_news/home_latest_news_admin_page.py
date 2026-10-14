"""
cms/pages/home_latest_news/home_latest_news_admin_page.py — HomeLatestNewsAdminPage.

Control_Panel Page Object for PBI 129372 (Home Page "Latest News" section).

REWRITTEN 2026-10-07 (Phase 3, 7-state workflow migration). The previous
version drove the raw Object Definition through Content & Data, which is
retired for Object-Definition-backed records (standards.md "Object Authoring
Is the Only Path"), and logged in as TEST_USER as a fallback. Its
"No Workflow" finding was an artifact of that path and is withdrawn.

OBJECTS (live Object Authoring sidebar, read 2026-10-07 as Site Content Editor;
NewsArticle is also in cms/Content-Admin-Guide.docx section 11):
  - "News Article"              -> manage-news-article
      fields: Title | Title — العربية * | Thumbnail Image | Publication Date |
              View Count | Active/Published Status
  - "Home Latest News Section"  -> manage-home-latest-news-section
      fields: Section Tag (+ — العربية) | Section Heading (+ — العربية) |
              Section Description (+ — العربية, textarea 0/1000) |
              View All Label (+ — العربية) | Active Status (ticked by default)
      ONE real record: QCDEMO-129372-HOME_LATEST_NEWS_SECTION-MAIN (PUBLISHED,
      id 147240). Never opened for write by this suite — `+ Add New` / the
      empty create form only, and every delete is guarded against that code.
  - "News Archive Page"         -> manage-news-archive-page (the View All
      target). Real singleton; never mutated here.

Editor form submit button reads "Publish" (SUBMIT_FOR_REVIEW_BUTTON matches
both labels). As Editor it lands on Published directly.

PUBLIC FACTS (logged-out, 2026-10-07): section `data-qc-count=3`; cards link
to /web/qatar-chamber/news-article?id=<id> (detail heading `.qc-nd-heading`);
View All links to /web/qatar-chamber/news.
"""

from __future__ import annotations

import datetime
import os
import re
import time

from cms.pages.components.object_authoring_page import (
    ObjectAuthoringPage,
    normalize_status,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials
from core.utils.logger import get_logger
from core.web.base_page import BasePage

logger = get_logger("home_latest_news_admin_page")

NEWS_SLUG = "news-article"
SECTION_SLUG = "home-latest-news-section"

# News Article field labels (live accessible names)
F_TITLE = "Title"
F_TITLE_AR = "Title — العربية"
F_THUMBNAIL = "Thumbnail Image"
F_PUB_DATE = "Publication Date"
F_ACTIVE = "Active/Published Status"

# Home Latest News Section field labels
S_TAG = "Section Tag"
S_TAG_AR = "Section Tag — العربية"
S_HEADING = "Section Heading"
S_HEADING_AR = "Section Heading — العربية"
S_DESC = "Section Description"
S_DESC_AR = "Section Description — العربية"
S_ACTIVE = "Active Status"

# The one real section record — never a delete/write target.
LIVE_SECTION_CODE = "QCDEMO-129372-HOME_LATEST_NEWS_SECTION-MAIN"
# Real editorial article codes seen live — never a delete/write target.
LIVE_NEWS_CODES = ("QCDEMO-129372-NEWS-1", "QCDEMO-129372-NEWS-2", "QCDEMO-129372-NEWS-3")

QCTEST_PREFIX = "QCTEST-"

# User decision 2026-10-07 (one round): "do not delete anything this round".
# QC_KEEP_QCTEST=1 turns every delete helper below into a logged no-op and
# records what it would have removed, so the report can list it.
KEEP_QCTEST = os.getenv("QC_KEEP_QCTEST") == "1"
KEPT: list = []


class HomeLatestNewsAdminPage(BasePage):
    """Thin feature layer over ObjectAuthoringPage for the two objects above."""

    def __init__(self, page):
        super().__init__(page)
        self.news = ObjectAuthoringPage(page, slug=NEWS_SLUG)
        self.section = ObjectAuthoringPage(page, slug=SECTION_SLUG)

    # ---- accounts ----------------------------------------------------------
    def sign_in_as(self, role: str) -> "HomeLatestNewsAdminPage":
        """Sign the page in as a named role (never TEST_USER). Uses
        ensure_signed_in_as(): a bare login() on the default page fixture
        (pre-loaded TEST_USER storageState) would not switch accounts."""
        email, password = cms_role_credentials(role)
        CmsLoginPage(self.page).ensure_signed_in_as(email, password)
        return self

    # ---- forms -------------------------------------------------------------
    def box(self, label: str):
        """Textbox by accessible name. A required field's name carries a
        trailing " *" (live 2026-10-07: "Title — العربية *"), which an
        exact match on the bare label misses — fall back to that shape."""
        exact = self.page.get_by_role("textbox", name=label, exact=True)
        if exact.count():
            return exact.first
        return self.page.get_by_role(
            "textbox", name=ObjectAuthoringPage.label_pattern(label)
        ).first

    def checkbox_checked(self, label: str) -> bool:
        """Exact-name read. ObjectAuthoringPage.is_checked() builds a regex
        selector that fails to parse on a "/" in the label
        ("Active/Published Status", rerun2 2026-10-07)."""
        return self.page.get_by_role("checkbox", name=label, exact=True).is_checked()

    def publish_disabled(self, authoring: ObjectAuthoringPage) -> bool:
        """True when the form's Publish/Submit button is rendered disabled
        (the form blocking a submit client-side counts as a refusal)."""
        btn = self.page.locator(authoring.SUBMIT_FOR_REVIEW_BUTTON).first
        try:
            if btn.is_disabled():
                return True
            cls = btn.get_attribute("class") or ""
            return "disabled" in cls.split()
        except Exception:  # noqa: BLE001
            return False

    def fill(self, label: str, value: str) -> None:
        self.box(label).fill(value)

    def value(self, label: str) -> str:
        return self.box(label).input_value()

    DATE_PLACEHOLDER_NAME = "dd/mm/yyyy"

    def date_box(self, label: str):
        """The date input for `label`.

        FIXED 2026-10-07 (review): on this surface a date field's accessible
        name is its PLACEHOLDER (`dd/mm/yyyy`), not its label — same widget as
        magazine_issue_admin_page.py:139 (FIELD_ISSUE_DATE). The list's two
        "Modified from/to" filters carry the same placeholder, so the input is
        resolved by its own label first (the first input after the label
        text), and only then by placeholder name inside the entry <form>."""
        exact = self.page.get_by_role("textbox", name=label, exact=True)
        if exact.count():
            return exact.first
        by_label = self.page.locator(
            f"xpath=//label[starts-with(normalize-space(.), '{label}')]"
            "/following::input[not(@type='hidden')][1]"
        )
        if by_label.count():
            return by_label.first
        return self.page.locator("form").get_by_role(
            "textbox", name=self.DATE_PLACEHOLDER_NAME, exact=True
        ).first

    def set_date(self, authoring: ObjectAuthoringPage, label: str, value: datetime.date) -> None:
        """Native `type=date` gets ISO; a text date is typed in the order its
        placeholder states (dd/mm/yyyy here — MM/DD is never assumed)."""
        box = self.date_box(label)
        kind = (box.get_attribute("type") or "text").lower()
        if kind == "date":
            box.fill(value.isoformat())
            return
        placeholder = (box.get_attribute("placeholder") or self.DATE_PLACEHOLDER_NAME).lower()
        text = value.strftime("%m/%d/%Y") if placeholder.startswith("mm") else value.strftime("%d/%m/%Y")
        box.click()
        self.page.keyboard.type(text, delay=20)

    def date_value(self, label: str) -> str:
        return self.date_box(label).input_value()

    def fill_news_article(
        self,
        title: str = "",
        title_ar: str = "",
        pub_date: datetime.date | None = None,
        thumbnail: str | None = None,
        active: bool = True,
    ) -> "HomeLatestNewsAdminPage":
        """Opens the empty create form and fills only what is passed."""
        a = self.news
        a.open_new_entry_form()
        if title:
            self.fill(F_TITLE, title)
        if title_ar:
            self.fill(F_TITLE_AR, title_ar)
        if pub_date is not None:
            self.set_date(a, F_PUB_DATE, pub_date)
        a.set_checkbox(F_ACTIVE, active)
        if thumbnail:
            a.upload_file(F_THUMBNAIL, thumbnail)
        return self

    # Positive success banner (live: "Saved and published.", "Saved ...").
    SAVED_BANNER = re.compile(r"Saved and published|Saved and submitted|Saved as draft|^Saved", re.I)
    # Client-side field errors added to the form 2026-10-07 evening (live:
    # "Use dd/mm/yyyy" under Publication Date) are not in SAVE_REFUSAL.
    INLINE_FIELD_ERROR = '[aria-invalid="true"]:visible, .has-error:visible, .invalid-feedback:visible, .form-feedback-item:visible'

    def save_outcome(self, authoring: ObjectAuthoringPage) -> str:
        """After a Save/Publish: "refused" when a refusal bar or an inline
        field error is on screen, "saved" when a success banner is, else
        "unknown" (never guessed as saved — a silent no-op is not a save)."""
        if authoring._count(authoring.SAVE_REFUSAL) > 0:  # noqa: SLF001 — read-only probe of a public selector
            return "refused"
        if authoring._count(self.INLINE_FIELD_ERROR) > 0:  # noqa: SLF001
            return "refused"
        try:
            banners = self.page.locator(".alert:visible, [role=status]:visible, [role=alert]:visible").all_inner_texts()
        except Exception:  # noqa: BLE001
            banners = []
        if any(self.SAVED_BANNER.search(t.strip()) for t in banners):
            return "saved"
        if "previewEntry=" in self.page.url:
            return "saved"
        return "unknown"

    def refusal_text(self, authoring: ObjectAuthoringPage) -> str:
        try:
            return " | ".join(self.page.locator(authoring.SAVE_REFUSAL).all_inner_texts())[:500]
        except Exception:  # noqa: BLE001
            return ""

    # ---- status polling -----------------------------------------------------
    def wait_row_status(
        self, authoring: ObjectAuthoringPage, title: str, expected: str, timeout_s: float = 120.0
    ) -> str:
        """Re-reads the entries list until `title`'s row shows `expected`
        (normalized) or the timeout lapses; returns the last status read.
        Publish commits in ~27-30 s on qcdev (measured 2026-09-15), so a
        single read right after the click races the transition."""
        expected = normalize_status(expected)
        deadline = time.monotonic() + timeout_s
        last = ""
        while True:
            authoring.open_entries_list()
            last = authoring.row_status_text(title)
            if last == expected or time.monotonic() >= deadline:
                return last
            self.page.wait_for_timeout(3000)

    # ---- guarded teardown -----------------------------------------------------
    def delete_qctest_article(self, title: str) -> int:
        """Deletes every row whose title is exactly-contained `title`, only
        inside the QCTEST- namespace (delete_all_entries_by_title enforces
        the prefix). Never raises."""
        if not title.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing to delete non-QCTEST title {title!r}")
        if KEEP_QCTEST:
            logger.warning("KEEP_QCTEST: not deleting news article(s) titled %r", title)
            KEPT.append(("news", title))
            return 0
        try:
            return self.news.delete_all_entries_by_title(title)
        except Exception:  # noqa: BLE001
            logger.warning("teardown: QCTEST article %r may remain", title)
            return 0

    def delete_verified_entry(
        self, authoring: ObjectAuthoringPage, field_label: str, qctest_value: str
    ) -> str:
        """For rows whose Entry column is not the title: resolve the code by
        reading `field_label` back from each row's form (never by position),
        refuse anything that is a known live record or whose read-back value
        is not QCTEST-, then delete by that code. Returns the deleted code
        or ""."""
        if not qctest_value.startswith(QCTEST_PREFIX):
            raise ValueError(f"refusing: {qctest_value!r} is not a QCTEST value")
        if KEEP_QCTEST:
            logger.warning("KEEP_QCTEST: not deleting entry with %s=%r", field_label, qctest_value)
            KEPT.append((authoring.slug, f"{field_label}={qctest_value}"))
            return ""
        try:
            code = self.find_code_by_field(authoring, field_label, qctest_value)
            if not code:
                return ""
            authoring.open_entry_by_code(code)
            if not self._await_value(field_label, qctest_value):
                return ""
            authoring.open_entries_list()
            return code if authoring.delete_entry_by_code(code) else ""
        except Exception:  # noqa: BLE001
            logger.warning("teardown: QCTEST entry with %s=%r may remain", field_label, qctest_value)
            return ""

    def _await_value(self, label: str, expected: str, timeout_ms: int = 10000) -> bool:
        """The edit form fills its inputs after the page settles; poll the
        read-back instead of reading once (a single early read returned ""
        live 2026-10-07 and lost a just-saved entry)."""
        deadline = time.monotonic() + timeout_ms / 1000
        while True:
            try:
                if self.value(label) == expected:
                    return True
            except Exception:  # noqa: BLE001 — form still mounting
                pass
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(500)

    def find_code_by_field(self, authoring: ObjectAuthoringPage, label: str, value: str) -> str:
        """Verified (never positional) lookup: opens each non-live row by its
        own Entry code and returns the one whose `label` reads back `value`."""
        authoring.open_entries_list()
        rows = self.page.locator(authoring.ENTRIES_TABLE_ROW)
        codes = [rows.nth(i).locator("td").nth(0).inner_text().strip() for i in range(rows.count())]
        for code in codes:
            if not code or code == LIVE_SECTION_CODE or code in LIVE_NEWS_CODES:
                continue
            try:
                authoring.open_entry_by_code(code)
            except Exception:  # noqa: BLE001
                continue
            if self._await_value(label, value, timeout_ms=6000):
                return code
        return ""

    # ---- section form (create form only; never the live record) ------------
    def open_new_section_form(self) -> "HomeLatestNewsAdminPage":
        """Empty create form only. Asserts it IS empty, so a future change
        that opens the live record here can never be typed over
        (singleton-manage-page trap, incident 183176)."""
        self.section.open_new_entry_form()
        for label in (S_TAG, S_HEADING, S_DESC):
            value = self.value(label)
            assert value == "", (
                f"create form for {SECTION_SLUG} is not empty ({label}={value!r}) — "
                "refusing to type over what may be the live record"
            )
        return self

    def has_rich_text_bold_control(self, label: str) -> bool:
        """True if the field renders a rich-text editor with a Bold control
        (CKEditor iframe/toolbar). A plain <textarea> has none."""
        try:
            box = self.page.get_by_role("textbox", name=label, exact=True)
            tag = box.first.evaluate("el => el.tagName.toLowerCase()") if box.count() else ""
            if tag == "textarea":
                container = box.first.locator("xpath=ancestor::*[contains(@class,'form-group')][1]")
                return container.locator('[aria-label*="Bold" i], [title*="Bold" i], .cke_button__bold').count() > 0
            return self.page.locator('[aria-label*="Bold" i], .cke_button__bold').count() > 0
        except Exception:  # noqa: BLE001
            return False

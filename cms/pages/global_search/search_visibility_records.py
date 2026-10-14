"""
cms/pages/global_search/search_visibility_records.py — SearchVisibilityRecords.

CMS side of PBI 131055's content-visibility cases (141849–141852). The search
tests need content in known workflow states, so this class creates DISPOSABLE
records, changes their state and deletes them. QA Manager authorised this on
2026-10-03, for disposable records only.

Object: `Publication` (cms/Content-Admin-Guide.docx §12). Why this one:
  - It is one of the public search's content types
    (GlobalSearchPage.CASE_CONTENT_TYPES).
  - It has a working Object Authoring Page Object (PublicationAdminPage)
    whose Entry column shows the real title, so exact-title lookups work.
  - NewsArticle (§11) has only a Content & Data page object, and that path
    is retired.

Every record is titled `QCTEST-<tc_id>-<ts>[-<suffix>]` and created as QC
Site Content Editor. For that account Submit lands on Published directly.
Records are deleted by EXACT Entry-cell title. Real Publications are never
touched. Each record uploads the generated cover/PDF fixtures; those
Documents & Media copies are not deleted (not approved).
"""

import re

from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.components.object_authoring_page import normalize_status
from cms.pages.publications import publication_admin_page as pub
from config.settings import cms_role_credentials

FIXTURES = "cms/tests/publications/fixtures"
EDITOR_ROLE = "Site Content Editor"


class SearchVisibilityRecords:
    def __init__(self, page):
        self.page = page
        self.admin = pub.PublicationAdminPage(page)

    def sign_in_editor(self) -> "SearchVisibilityRecords":
        login = CmsLoginPage(self.page)
        login.open_login().login(*cms_role_credentials(EDITOR_ROLE))
        if not login.login_succeeded():
            raise AssertionError("Site Content Editor login did not reach a signed-in page")
        return self

    # ---- create ------------------------------------------------------------
    def create(self, title: str, publish: bool, active: bool = True) -> str:
        """Creates a Publication with every guide-listed field filled. Saves it
        as Draft, and when `publish` is set, reopens it and submits it as
        Editor. Returns the normalized row status afterwards."""
        if not title.startswith("QCTEST-"):
            raise ValueError(f"refusing to create a non-QCTEST record {title!r}")
        a = self.admin
        a.open_new_entry_form()
        a.fill_text(pub.FIELD_PUBLICATION_TITLE_EN, title)
        a.fill_text(pub.FIELD_PUBLICATION_TITLE_AR, f"{title} منشور")
        a.fill_text(pub.FIELD_PUBLICATION_DESCRIPTION_EN, f"{title} disposable search-visibility record.")
        a.fill_text(pub.FIELD_PUBLICATION_DESCRIPTION_AR, f"{title} سجل تجريبي.")
        a.select_publication_type("Report")
        self._upload(pub.FIELD_COVER_IMAGE, f"{FIXTURES}/valid_cover_1_5mb.jpg")
        a.set_publication_date("01/01/2026")
        self._upload(pub.FIELD_FILE_ATTACHMENT, f"{FIXTURES}/valid_pdf_4mb.pdf")
        # Page Count is NOT in guide §12, but the live form refuses Save as
        # Draft without it (probe 2026-10-03: native "Please fill out this
        # field." on ObjectField_pageCount, row never created). It is filled
        # only so the disposable record can exist; nothing asserts on it.
        # Guide-vs-implementation conflict reported to the QA Manager.
        a.fill_number(pub.FIELD_PAGE_COUNT, "1")
        a.set_active_status(active)
        a.save_as_draft()
        if publish:
            self._open_exact(title)
            a.submit_for_review()
        return self.status(title)

    PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'
    PICKER_ADD = "button.btn-primary:not(.dropdown-toggle):visible"

    def _upload(self, field_label: str, path: str) -> None:
        """Upload through the Documents & Media picker. It uses the same steps
        as the shared `upload_file()`, with two waits made explicit after a
        live failure on 2026-10-03, where the picker's Add click timed out at
        15 s:
          - wait for the picker's file input, not the iframe's visibility;
          - wait for "Add" (btn-primary, NOT the "New" dropdown-toggle) to be
            visible and enabled before clicking it.
        Same mechanics as image_alt_text_admin_component's healed upload."""
        from core.utils.waits import wait_until

        field = self.page.get_by_role("textbox", name=f"{field_label} Select File")
        field.locator("xpath=..").get_by_role("button", name="Select File").click()
        self.page.locator(self.PICKER_IFRAME).first.wait_for(state="attached", timeout=60000)
        frame = self.page.frame_locator(self.PICKER_IFRAME).first
        frame.locator('input[type="file"]').wait_for(state="attached", timeout=60000)
        frame.locator('input[type="file"]').set_input_files(path)
        add = frame.locator(self.PICKER_ADD).first
        add.wait_for(state="visible", timeout=60000)
        wait_until(lambda: add.is_enabled(), timeout=60.0, poll=0.5,
                   message=f"picker Add never enabled for {field_label!r}")
        add.click()
        self.page.locator(self.PICKER_IFRAME).first.wait_for(state="detached", timeout=30000)

    def publish(self, title: str) -> str:
        """Reopens THIS disposable Draft and submits it as Editor, which lands
        on Published. Returns the status afterwards."""
        self._open_exact(title)
        self.admin.submit_for_review()
        return self.status(title)

    def unpublish(self, title: str) -> str:
        """Row action Unpublish on THIS disposable record. Its row is located
        by exact title, and the click goes by entry id. Returns the status
        afterwards."""
        self._require_single(title)
        self.admin.unpublish_entry(title)
        return self.status(title)

    # ---- read ----------------------------------------------------------------
    def _rows_exact(self, title: str):
        cell = self.page.locator("td.qc-oel__cell-title", has_text=re.compile(rf"^\s*{re.escape(title)}\s*$"))
        return self.page.locator(self.admin.authoring.ENTRIES_TABLE_ROW).filter(has=cell)

    LIST_SEARCH = "input[data-qc-oel-q]"

    def _open_list_filtered(self, text: str) -> None:
        """Entries list narrowed with the list's own search box. The list is
        PAGINATED (10 rows per page, 35+ Publications on 2026-10-03), so a
        row past page 1 is invisible to a bare table read. That gap made the
        first latency probe read "no row" for a record it had in fact saved.
        Waits until the table shows a row containing `text`, or until 10 s
        pass (no such row: callers then see zero exact rows)."""
        self.admin.open_entries_list()
        box = self.page.locator(self.LIST_SEARCH)
        box.fill(text)
        box.press("Enter")
        try:
            self.page.locator(f"{self.admin.authoring.ENTRIES_TABLE_ROW}:has-text(\"{text}\")").first.wait_for(
                state="visible", timeout=10000)
        except Exception:  # noqa: BLE001 — absent row is a valid answer
            pass

    def _require_single(self, title: str) -> None:
        self._open_list_filtered(title)
        n = self._rows_exact(title).count()
        if n != 1:
            raise AssertionError(f"expected exactly one row titled {title!r}, found {n}")

    def _open_exact(self, title: str) -> None:
        self._require_single(title)
        self.admin.open_entry_by_edit_link(title)

    def status(self, title: str) -> str:
        """Normalized status of the row whose Entry cell is exactly `title`
        ("" when absent)."""
        self._open_list_filtered(title)
        rows = self._rows_exact(title)
        if rows.count() == 0:
            return ""
        return normalize_status(rows.first.locator("td").nth(1).inner_text())

    # ---- teardown --------------------------------------------------------------
    def delete_exact(self, title: str, max_rounds: int = 5) -> bool:
        """Deletes every row whose Entry cell is exactly `title`, one at a
        time, by entry id. Refuses non-QCTEST titles. Returns True when none
        remain. Never raises (teardown)."""
        if not title.startswith("QCTEST-"):
            raise ValueError(f"refusing to delete non-QCTEST record {title!r}")
        for _ in range(max_rounds):
            try:
                self._open_list_filtered(title)
                rows = self._rows_exact(title)
                if rows.count() == 0:
                    return True
                entry_id = rows.first.locator("a[data-qc-oel-delete]").get_attribute("data-qc-oel-delete")
                if not entry_id:
                    return False
                self.page.once("dialog", lambda d: d.accept())
                link = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
                link.click(force=True)
                link.wait_for(state="detached", timeout=15000)
            except Exception:  # noqa: BLE001 — teardown; the caller reports leftovers
                return False
        return False

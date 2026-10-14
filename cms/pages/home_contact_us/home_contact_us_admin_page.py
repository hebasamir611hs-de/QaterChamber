"""
cms/pages/home_contact_us/home_contact_us_admin_page.py — Control_Panel Page
Objects for PBI 129390 (QC-HOME-014, Home "Quick Contact Us" section).

REWRITTEN 2026-10-08 (Phase 3, B-129390). Read live as Editor / Form Manager /
TEST_USER / site member / logged-out (reports/recon-129390.json,
reports/recon2-129390.json):

The public section (fragment "QC Home Contact Us") is fed by THREE things:

1. **InquiryCategory** object (Content-Admin-Guide §20) — Object Authoring
   `manage-inquiry-category`. Live rows QCDEMO-129390-INQCAT-01..11 (record
   52706.. 52746), all PUBLISHED. Create form (bare URL = empty create form):
   textbox "Category Label", textbox "Category Label — العربية *", spinbutton
   "Display Order", checkbox "Active Status" — Active Status is TICKED by
   default on a new entry. Editor's submit button reads "Publish".
   -> `InquiryCategoryAdminPage`. Every test works on disposable
   `QCTEST-<tc>-*` categories; the 11 live rows are never written.

2. **"Contact Us Section" Journal article 53012** (structure 52431) — the
   documented exception to "Object Authoring is the only content path"
   (CLAUDE.md #4). Its Fields panel DOES render now (2026-10-08, TEST_USER):
   Section Tag, Section Heading, Section Description (textarea), Email Support
   Address, Telephone Number, Location Address (textarea), Map Embed URL, Form
   Recipient Email(s), Send Message Button Label — none carries `required` or
   `maxlength`. The QC Site Content Editor and the site member both get
   "You do not have the roles required to access this portlet." on the
   article's edit URL and on the Web Content portlet.
   -> `ContactUsSectionArticlePage`. Tests create a disposable
   `QCTEST-129390-*` article of the same structure and only ever Save it as a
   Draft; 53012 itself is opened read-only.

3. **Inquiry** object (`manage-inquiry`) — where public submissions are stored
   (the fragment POSTs to /o/qc-inquiry/submit, which persists an Inquiry
   entry with inquiryStatus=pending; the emails are the object's onAfterAdd
   actions). -> `InquiryAdminPage` (read-only lookups).

No method here deletes anything that is not positively a QCTEST record.
"""

import re

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_about_summary.home_about_summary_admin_page import (  # generic QCTEST helpers
    Disposables,
    _DisposableRecordMixin,
)
from config.settings import cms_role_credentials, control_panel_url, settings
from core.web.base_page import BasePage

QCTEST_PREFIX = "QCTEST-"

# ---- live identifiers (read-only) -------------------------------------------
INQUIRY_CATEGORY_SLUG = "inquiry-category"
INQUIRY_SLUG = "inquiry"
LIVE_CATEGORY_CODES = [f"QCDEMO-129390-INQCAT-{i:02d}" for i in range(1, 12)]

CONTACT_US_SECTION_ARTICLE_ID = "53012"
CONTACT_US_SECTION_GROUP_ID = "37246"
CONTACT_US_SECTION_DDM_STRUCTURE_ID = "52431"

_J = "com_liferay_journal_web_portlet_JournalPortlet"
ARTICLE_53012_EDIT_PATH = (
    f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={_J}&p_p_lifecycle=0&p_p_state=maximized"
    f"&_{_J}_mvcRenderCommandName=/journal/edit_article&_{_J}_articleId={CONTACT_US_SECTION_ARTICLE_ID}"
    f"&_{_J}_groupId={CONTACT_US_SECTION_GROUP_ID}"
)
NEW_ARTICLE_PATH = (
    f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={_J}&p_p_lifecycle=0&p_p_state=maximized"
    f"&_{_J}_mvcRenderCommandName=/journal/edit_article&_{_J}_groupId={CONTACT_US_SECTION_GROUP_ID}"
    f"&_{_J}_folderId=0&_{_J}_ddmStructureId={CONTACT_US_SECTION_DDM_STRUCTURE_ID}"
)
WEB_CONTENT_PATH = f"/en/group/qatar-chamber/~/control_panel/manage?p_p_id={_J}"
NO_ROLE_MESSAGE = "You do not have the roles required to access this portlet."

# ---- InquiryCategory field labels (live 2026-10-08) -------------------------
FIELD_CATEGORY_LABEL_EN = "Category Label"
FIELD_CATEGORY_LABEL_AR = "Category Label — العربية *"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_ACTIVE_STATUS = "Active Status"


def sign_in(page, role: str | None):
    """role=None -> TEST_USER (setup-only, never for a permission case)."""
    if role is None:
        CmsLoginPage(page).ensure_signed_in_as(settings.test_user, settings.test_password)
    else:
        email, password = cms_role_credentials(role)
        CmsLoginPage(page).ensure_signed_in_as(email, password)


class InquiryCategoryAdminPage(_DisposableRecordMixin, ObjectAuthoringPage):
    TITLE_FIELDS = (FIELD_CATEGORY_LABEL_EN, FIELD_CATEGORY_LABEL_AR)

    def __init__(self, page):
        super().__init__(page, INQUIRY_CATEGORY_SLUG)

    def fill_category(self, prefix: str, *, label_en: str | None = None, label_ar: str | None = None,
                      display_order: str | None = "9900", active: bool = False) -> dict:
        """Fill the create form. Defaults keep the record off the public
        dropdown (Active Status unticked) and at the end of the order."""
        values = {
            FIELD_CATEGORY_LABEL_EN: f"{prefix} label" if label_en is None else label_en,
            FIELD_CATEGORY_LABEL_AR: f"{prefix} تصنيف" if label_ar is None else label_ar,
            FIELD_DISPLAY_ORDER: display_order,
        }
        self.fill_text(FIELD_CATEGORY_LABEL_EN, values[FIELD_CATEGORY_LABEL_EN])
        self.fill_text(FIELD_CATEGORY_LABEL_AR, values[FIELD_CATEGORY_LABEL_AR])
        if display_order is not None:
            self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).fill(display_order)
        self.tick(FIELD_ACTIVE_STATUS, active)
        return values

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).input_value()

    def display_order_validity(self) -> dict:
        """The number input's own constraint state (min / validity flags)."""
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).evaluate(
            "el => ({value: el.value, min: el.min, step: el.step, valid: el.validity.valid,"
            " message: el.validationMessage, badInput: el.validity.badInput})")

    def is_live_code(self, code: str) -> bool:
        return code in LIVE_CATEGORY_CODES

    # ---- pagination-aware list reads (live: 10 rows per page; the 11th live
    # row and every new entry sit on later pages) -----------------------------
    # HEALED 2026-10-08: the two hidden date-picker popups ("Modified from/to")
    # also render "‹ ›" buttons earlier in the DOM; only the visible pager
    # button ("Page n of m" bar) is the right one.
    NEXT_PAGE = 'button:text-is("›"):visible'

    def _next_page(self) -> bool:
        nxt = self.page.locator(self.NEXT_PAGE)
        if not nxt.count():
            return False
        b = nxt.last
        if b.is_disabled() or "disabled" in (b.get_attribute("class") or ""):
            return False
        first = self.page.locator(self.ENTRIES_TABLE_ROW).first.inner_text()
        b.click()
        try:
            self.page.wait_for_function(
                "t => { const r = document.querySelector('table tbody tr'); return r && r.innerText !== t; }",
                arg=first, timeout=15000)
        except Exception:  # noqa: BLE001 — same rows = no further page
            return False
        return True

    def entry_codes(self) -> list:
        self.open_entries_list(locale="en")
        codes = []
        for _ in range(20):
            rows = self.page.locator(self.ENTRIES_TABLE_ROW)
            codes += [rows.nth(i).locator("td").nth(0).inner_text().strip() for i in range(rows.count())]
            if not self._next_page():
                break
        return list(dict.fromkeys(codes))

    def goto_row(self, code: str) -> bool:
        self.open_entries_list(locale="en")
        for _ in range(20):
            if self.row_visible_by_code(code):
                return True
            if not self._next_page():
                return False
        return False

    def delete_qctest(self, code: str) -> bool:
        """Pagination-aware override: QCTEST identity re-read first, delete on
        the page that shows the row, then verify across every page."""
        if not code or self.is_live_code(code) or not self.is_qctest(code):
            raise AssertionError(f"refusing to delete {code!r}: not positively a QCTEST record")
        if self.goto_row(code):
            self.delete_entry_by_code(code)
        return code not in self.entry_codes()

    def deactivate(self, code: str) -> str:
        """Unpublish a QCTEST category (row action) so it leaves the public
        dropdown at once; teardown deletes it later. Returns the new status."""
        if self.is_live_code(code):
            raise AssertionError("refusing to touch a live category")
        if not self.goto_row(code):
            return "row not found"
        self.unpublish_entry(code, comment="QCTEST teardown")
        self.goto_row(code)
        return self.row_status_text_by_code(code)


class InquiryAdminPage(ObjectAuthoringPage):
    """Stored public submissions (read-only use)."""

    def __init__(self, page):
        super().__init__(page, INQUIRY_SLUG)

    def rows_matching(self, needle: str) -> list:
        self.open_entries_list(locale="en")
        sel = self.page.locator("select").filter(has=self.page.locator('option[value="50"]'))
        if sel.count():
            sel.first.select_option("50")
            self.page.wait_for_load_state("networkidle")
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        return [t for t in rows.all_inner_texts() if needle in t]

    def entry_text(self, code: str) -> str:
        self.open_entry_by_code(code, locale="en")
        return self.rendered_body_text()


class ContactUsSectionArticlePage(BasePage):
    """The Journal article behind the section. Fields are located by the DDM
    field-reference prefix in the input name (`ddm$$<field>$`), which is stable;
    the random token after it is not."""

    FIELD_REFS = {
        "Section Tag": "sectionTag",
        "Section Heading": "sectionHeading",
        "Section Description": "sectionDescription",
        "Email Support Address": "emailSupportAddress",
        "Telephone Number": "telephoneNumber",
        "Location Address": "locationAddress",
        "Map Embed URL": "mapEmbedUrl",
        "Form Recipient Email(s)": "formRecipientEmail",
        "Send Message Button Label": "sendMessageButtonLabel",
    }
    TITLE_INPUT = f'input[name="_{_J}_titleMapAsXML"]'
    SAVE_AS_DRAFT = 'button:has-text("Save as Draft")'
    PUBLISH = 'button[type="submit"]:has-text("Publish"), button:text-is("Publish")'
    PREVIEW = 'button:has-text("Preview")'
    LOCALE_TOGGLE = 'button:has-text("en-US"), button:has-text("ar-SA")'
    SUCCESS = '.alert-success, [role="alert"]:has-text("Success")'
    ERROR = '.alert-danger, .form-feedback-item, .has-error .form-feedback-item, [role="alert"].alert-danger'

    MODAL = '.modal-dialog:visible, [role="dialog"]:visible'
    FIELD_ERROR = ".form-feedback-item, .form-feedback-group, .help-block"

    def _field(self, label: str, locale: str = "en_US"):
        """Live 2026-10-08: each DDM input is named
        `..._ddm$$<ref>$<token>$0$$<locale>`; after switching the toolbar to
        ar-SA the visible inputs carry the `$$ar_SA` suffix and the en_US ones
        are hidden."""
        ref = self.FIELD_REFS[label]
        exact = self.page.locator(f'[name*="ddm$${ref}$"][name$="$${locale}"]')
        if locale == "en_US" or exact.count():
            return exact.first
        # Live 2026-10-14: after the toolbar switch to ar-SA on a form whose EN
        # values were already typed, the inputs keep a non-ar_SA name (no
        # `$$ar_SA` input exists at all) while the VISIBLE input is the AR
        # translation being edited (screenshot reports/probe-article-ar2-
        # 20261014.png). Fall back to the visible, non-hidden input.
        return self.page.locator(
            f'[name*="ddm$${ref}$"]:not([type="hidden"]):visible').first

    # ---- navigation ------------------------------------------------------
    def open_article_53012(self) -> "ContactUsSectionArticlePage":
        """READ-ONLY use: the live article. Callers never fill or save it."""
        self.open(control_panel_url(ARTICLE_53012_EDIT_PATH))
        return self

    def open_new_article(self) -> "ContactUsSectionArticlePage":
        self.open(control_panel_url(NEW_ARTICLE_PATH))
        self._field("Section Heading").wait_for(timeout=60000)
        return self

    def goto_bare(self, path: str):
        resp = self.page.goto(control_panel_url(path), wait_until="domcontentloaded", timeout=60000)
        return resp.status if resp else None

    def no_role_message_shown(self) -> bool:
        return NO_ROLE_MESSAGE in self.page.locator("body").inner_text()

    def fields_rendered(self) -> dict:
        return {label: self.page.locator(f'[name*="ddm$${ref}$"]').count() > 0 for label, ref in self.FIELD_REFS.items()}

    def form_actions(self) -> dict:
        return {name: self.page.locator(sel).count() > 0 for name, sel in (
            ("Save as Draft", self.SAVE_AS_DRAFT), ("Publish", self.PUBLISH), ("Preview", self.PREVIEW))}

    # ---- fields ------------------------------------------------------------
    def set_title(self, title: str) -> "ContactUsSectionArticlePage":
        self.page.locator(self.TITLE_INPUT).fill(title)
        return self

    def title_value(self) -> str:
        return self.page.locator(self.TITLE_INPUT).input_value()

    def fill(self, label: str, value: str, locale: str = "en_US") -> "ContactUsSectionArticlePage":
        self._field(label, locale).fill(value)
        return self

    def value(self, label: str, locale: str = "en_US") -> str:
        return self._field(label, locale).input_value()

    def attrs(self, label: str) -> dict:
        return self._field(label).evaluate(
            "el => ({maxlength: el.getAttribute('maxlength'), required: el.required, type: el.type,"
            " ariaRequired: el.getAttribute('aria-required')})")

    def switch_content_locale(self, target: str = "ar-SA") -> "ContactUsSectionArticlePage":
        """Toolbar translation switcher. Live 2026-10-08: the menu items read
        'en-US English Language: Default' / 'ar-SA Arabic Language: ...'."""
        current = "en-US" if target == "ar-SA" else "ar-SA"
        self.page.locator(f'button:has-text("{current}")').first.click()
        self.page.locator('[role="menuitem"]:visible, .dropdown-item:visible').filter(has_text=target).first.click()
        suffix = target.replace("-", "_")
        try:
            self.page.locator(f'[name*="ddm$$sectionHeading$"][name$="$${suffix}"]').first.wait_for(timeout=15000)
        except Exception:  # noqa: BLE001 -- see _field(): the input may keep its old name
            self.page.locator(f'button:has-text("{target}")').first.wait_for(timeout=15000)
        return self

    def fill_all_valid(self, prefix: str, locale: str = "en_US") -> dict:
        ar = locale.startswith("ar")
        values = {
            "Section Tag": "تواصل معنا" if ar else "Get in touch",
            "Section Heading": f"{prefix} عنوان" if ar else f"{prefix} heading",
            "Section Description": "وصف تجريبي" if ar else "Reach out to us for enquiries, support, or information.",
            "Email Support Address": "support@qcci.org",
            "Telephone Number": "+974 44559111",
            "Location Address": "الدوحة، قطر" if ar else "Lusail Boulevard 69, Doha, Qatar",
            "Map Embed URL": "https://www.google.com/maps/embed?pb=QCTEST",
            "Form Recipient Email(s)": "heba.samir611.hs@gmail.com",
            "Send Message Button Label": "إرسال الرسالة" if ar else "Send Message",
        }
        for label, v in values.items():
            # live 2026-10-08: the required fields are required in ar-SA too
            # ("Email Support Address (AR) *"), so the AR translation is filled
            # completely — except a field that renders no ar_SA input at all
            # (Map Embed URL), which is skipped.
            # live 2026-10-14: in ar-SA a non-translatable field (Map Embed URL)
            # renders but is never editable -- skipped.
            if locale != "en_US":
                field = self._field(label, locale)
                try:
                    if field.count() == 0 or not field.is_editable(timeout=3000):
                        continue
                except Exception:  # noqa: BLE001 -- not attached / not editable
                    continue
            self.fill(label, v, locale)
        return values

    # ---- actions ------------------------------------------------------------
    def _confirm_modal(self, button_text: str) -> str:
        """New articles open a "<action> With Permissions" modal; confirm it
        with its own button. Returns the modal title ('' when none showed)."""
        modal = self.page.locator(self.MODAL).first
        try:
            modal.wait_for(timeout=8000)
        except Exception:  # noqa: BLE001 — no modal on this path
            return ""
        title = modal.inner_text()[:80]
        # Viewable By defaults to "Anyone (Guest Role)"; a disposable QCTEST
        # article is restricted to its owner so a visitor can never reach it.
        sel = modal.locator("select")
        if sel.count():
            opts = sel.first.locator("option").all_inner_texts()
            owner = next((o for o in opts if "Owner" in o), None)
            if owner:
                sel.first.select_option(label=owner)
                title += f" | Viewable By -> {owner}"
        modal.locator(f'button:has-text("{button_text}")').last.click()
        return title

    def _outcome(self, start_url: str, modal: str) -> dict:
        """Wait for a success alert, an inline field error or the form-level
        'This form is invalid' message; report without assuming success."""
        # HEALED 2026-10-08: the previous combined selector mixed `text=` into a
        # CSS list, which is invalid, so the wait returned at once and a save
        # still in flight read as "not saved". Poll real signals instead: a
        # client-side refusal shows at once; a server save ends in a redirect
        # to the article's own edit URL (articleId=...) and/or a success alert.
        import time
        deadline = time.time() + 180
        body = ""
        while time.time() < deadline:
            try:
                body = self.page.locator("body").inner_text(timeout=5000)
                if ("articleId=" in self.page.url and self.page.url != start_url)                         or self.page.locator(self.SUCCESS).count()                         or "This form is invalid" in body                         or (not modal and self.page.locator(self.FIELD_ERROR).count()):
                    break
            except Exception:  # noqa: BLE001 — mid-navigation
                pass
            self.page.wait_for_timeout(1000)  # poll interval, not a fixed wait
        try:
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)
            body = self.page.locator("body").inner_text(timeout=10000)
        except Exception:  # noqa: BLE001
            pass
        invalid = ""
        if "This form is invalid" in body:
            i = body.index("This form is invalid")
            invalid = body[i:i + 120].split(chr(10))[0]
        errors = [t.strip() for t in self.page.locator(self.FIELD_ERROR).all_inner_texts() if t.strip()]
        success = self.page.locator(self.SUCCESS).count() > 0
        moved = "articleId=" in self.page.url and self.page.url != start_url
        return {"saved": (success or moved) and not invalid and not errors, "success_alert": success, "moved": moved,
                "error": invalid or " | ".join(errors)[:400], "errors": errors[:10], "modal": modal,
                "url": self.page.url, "article_id": self.article_id_from_url()}

    def save_as_draft(self) -> dict:
        start = self.page.url
        self.page.locator(self.SAVE_AS_DRAFT).first.click()
        modal = self._confirm_modal("Save as Draft")
        return self._outcome(start, modal)

    _APPROVED_RE = r"Version:\s*[\d.]+\s*APPROVED"

    def _approved_shown(self) -> bool:
        import re as _re
        try:
            return bool(_re.search(self._APPROVED_RE, self.page.locator("body").inner_text(timeout=5000)))
        except Exception:  # noqa: BLE001 -- mid-navigation
            return False

    def is_published(self, article_id: str) -> bool:
        """headless-delivery serves an article by key only once it is APPROVED
        (read live 2026-10-14). Uses the page's own signed-in session."""
        url = control_panel_url(
            f"/o/headless-delivery/v1.0/sites/{CONTACT_US_SECTION_GROUP_ID}/structured-contents/by-key/{article_id}")
        try:
            return self.page.request.get(url).status == 200
        except Exception:  # noqa: BLE001
            return False

    def publish(self) -> dict:
        """Live 2026-10-14: a successful Publish re-renders the SAME edit form
        and its properties panel can keep showing the old DRAFT badge, but the
        article IS published (headless-delivery serves it, e.g. 747461 at
        15:48 UTC). The proof is therefore headless-delivery by key, polled."""
        start = self.page.url
        article_id = self.article_id_from_url()
        self.page.locator('button.btn-primary:text-is("Publish"), button[type="submit"]:text-is("Publish")').first.click()
        modal = self._confirm_modal("Publish")
        from core.utils.waits import WaitTimeoutError, wait_until

        published = False
        if article_id:
            try:
                wait_until(lambda: self.is_published(article_id), timeout=120, poll=5.0,
                           message="article never became APPROVED after Publish")
                published = True
            except WaitTimeoutError:
                published = False
        if published:
            return {"saved": True, "success_alert": False, "moved": False, "error": "", "errors": [], "modal": modal,
                    "url": self.page.url, "article_id": article_id, "published_via_headless": True}
        out = self._outcome(start, modal)
        out["published_via_headless"] = False
        return out

    def field_error(self, label: str, locale: str = "en_US") -> str:
        """Inline message rendered under one DDM field (live: 'This field is
        required.')."""
        try:
            return self._field(label, locale).evaluate(
                """el => { let n = el; for (let i = 0; i < 6 && n; i++, n = n.parentElement) {
                       const f = n.querySelector('.form-feedback-item, .form-feedback-group, .help-block');
                       if (f && f.innerText.trim()) return f.innerText.trim(); } return ''; }""")
        except Exception:  # noqa: BLE001
            return ""

    def set_searchable(self, on: bool) -> "ContactUsSectionArticlePage":
        """'Searchable' lives in the collapsed SEARCH panel; set it directly."""
        self.page.locator(f'input[name="_{_J}_indexable"]').evaluate(
            "(el, on) => { if (el.checked !== on) { el.checked = on; el.dispatchEvent(new Event('change', {bubbles: true})); } }", on)
        return self

    def preview_text(self) -> str:
        """Open Preview and return the rendered preview's text (popup page or
        modal iframe). Live 2026-10-14: the toolbar shows Cancel / Save as
        Draft / Publish + a dropdown toggle; Preview is not a toolbar button,
        so the dropdown and the kebab menu are tried as well."""
        candidates = [self.page.locator(self.PREVIEW).first]
        for toggle in ('button.dropdown-toggle.btn-primary', '.control-menu-nav button.dropdown-toggle'):
            candidates.append((toggle, 'text="Preview"'))
        for cand in candidates:
            try:
                if isinstance(cand, tuple):
                    self.page.locator(cand[0]).last.click(timeout=5000)
                    target = self.page.locator(f'[role="menuitem"]:has-text("Preview"), .dropdown-item:has-text("Preview")').first
                    target.wait_for(state="visible", timeout=5000)
                else:
                    if not cand.count() or not cand.is_visible():
                        continue
                    target = cand
                try:
                    with self.page.context.expect_page(timeout=15000) as pop:
                        target.click()
                    newp = pop.value
                    newp.wait_for_load_state("domcontentloaded")
                    txt = newp.locator("body").inner_text()
                    newp.close()
                    return txt
                except Exception:  # noqa: BLE001 -- no popup: modal iframe
                    frame = self.page.frame_locator(".modal iframe").first
                    return frame.locator("body").inner_text(timeout=30000)
            except Exception:  # noqa: BLE001 -- try the next place
                self.page.keyboard.press("Escape")
                continue
        return ""

    def article_id_from_url(self) -> str:
        m = re.search(r"articleId=([^&#]+)", self.page.url)
        return m.group(1) if m else ""

    # ---- QCTEST teardown -----------------------------------------------------
    # The Web Content admin list renders "Web Content is temporarily
    # unavailable." on qcdev (2026-10-08), so a created article cannot be found
    # or deleted through the UI list. Teardown therefore goes by ID: the
    # articleId the post-save URL carries -> headless-delivery GET by-key ->
    # exact-title + QCTEST- check -> DELETE -> re-GET expects 404.
    API = "/o/headless-delivery/v1.0"

    def _api(self, method: str, path: str):
        import base64
        token = base64.b64encode(f"{settings.test_user}:{settings.test_password}".encode()).decode()
        r = self.page.request.fetch(control_panel_url(self.API + path), method=method,
                                    headers={"Authorization": f"Basic {token}", "Accept": "application/json"})
        try:
            body = r.json() if r.text().strip().startswith("{") else {}
        except Exception:  # noqa: BLE001
            body = {}
        return r.status, body

    def lookup_article(self, article_id: str) -> dict:
        status, body = self._api("GET", f"/sites/{CONTACT_US_SECTION_GROUP_ID}/structured-contents/by-key/{article_id}")
        return {"status": status, "id": body.get("id"), "title": body.get("title"), "key": body.get("key")}

    def delete_qctest_article(self, article_id: str, expected_title: str) -> dict:
        """Delete ONE article by its articleId, only when its live title is
        exactly `expected_title` and starts with QCTEST-. Verified by re-GET."""
        if not expected_title.startswith(QCTEST_PREFIX):
            raise AssertionError(f"refusing to delete {expected_title!r}: not a QCTEST title")
        if article_id == CONTACT_US_SECTION_ARTICLE_ID:
            raise AssertionError("refusing to delete the live article 53012")
        found = self.lookup_article(article_id)
        if found["status"] == 404:
            return {"article_id": article_id, "gone": True, "note": "not found before delete", "lookup": found}
        if found.get("title") != expected_title:
            raise AssertionError(f"refusing to delete article {article_id}: title is {found.get('title')!r}")
        status, _ = self._api("DELETE", f"/structured-contents/{found['id']}")
        after = self.lookup_article(article_id)
        return {"article_id": article_id, "id": found["id"], "delete_status": status,
                "after_status": after["status"], "gone": after["status"] == 404}


__all__ = [
    "InquiryCategoryAdminPage", "InquiryAdminPage", "ContactUsSectionArticlePage", "Disposables", "sign_in",
    "FIELD_CATEGORY_LABEL_EN", "FIELD_CATEGORY_LABEL_AR", "FIELD_DISPLAY_ORDER", "FIELD_ACTIVE_STATUS",
    "LIVE_CATEGORY_CODES", "ARTICLE_53012_EDIT_PATH", "WEB_CONTENT_PATH", "NO_ROLE_MESSAGE",
]

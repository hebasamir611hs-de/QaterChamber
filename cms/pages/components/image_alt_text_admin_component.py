"""
cms/pages/components/image_alt_text_admin_component.py — ImageAltTextRecordPage.

Carrier for PBI 129364's site-wide alt-text rule ("an image cannot be
published without EN + AR alt text"). Cases 134492, 134515–134523, 134642 and
134645–134652 run on DISPOSABLE QCTEST records of the `StrategicPartner`
Object.

Why StrategicPartner: cms/Content-Admin-Guide.docx §18 ("Home — Strategic
Partners") lists it with an image field (`logoImage`) and a bilingual
alt-text field (`logoAltText`). It has a working Object Authoring Page Object
(StrategicPartnersAdminPage). It is never HeaderConfiguration's logo, and
never a real record.

READ LIVE 2026-10-01 as QC Site Content Editor (create form,
/en/web/qatar-chamber/manage-strategic-partner, nothing saved):
  - Partner Name `ObjectField_partnerName` (required). Its AR twin
    "Partner Name — العربية" is required, dir=rtl, and has no name attribute.
  - Logo Image `ObjectField_logoImage` (required), a "Select File" button, and
    the help line "Upload a .jpg,.jpeg,.png,.svg,.webp no larger than 2 MB."
  - Logo Alt Text `ObjectField_logoAltText` (required, no maxlength). Its AR
    twin "Logo Alt Text — العربية" is required, dir=rtl, no name, no maxlength.
  - Display Order `ObjectField_displayOrder` (required).
  - Active Status `ObjectField_activeStatus`. TICKED by default on this create
    form, contrary to standards.md's "defaults unticked" note.
  - Buttons "Save as Draft" / "Publish" ("As an Editor, what you publish here
    goes live straight away.").
  - The Select File dialog is Liferay's Documents & Media item selector. It
    offers a keyword search, a file input and the folder/document lists, and
    NO alt-text inputs at all.

HEALED 2026-10-02 (live probe, QCTEST records only; evidence in
reports/bug-verify-alttext-20261002-2316/):
  - Picker "Add" is `button.btn-primary` WITHOUT `.dropdown-toggle`. The
    toolbar "New" (EN) / "جديد" (AR) is also `.btn-primary`, but it is a
    dropdown-toggle. It is visible from the start, so the old `.last` lookup
    could resolve to it before "Add" rendered, then wait 15 s for a picker
    that never closed. That was the /ar timeout.
  - The picker iframe does not report "visible" for a while after it is
    attached; the file input inside it is the readiness signal. The picker
    took 10.4 s to open on a quiet server, so 60 s budgets now apply.
  - After Publish, StrategicPartner shows NO text notice in the page, unlike
    HeaderConfiguration's "Saved and submitted for publishing.". The page
    returns to a blank create form, the list gains the row, and the preview
    header reads "Previewing <title> (<status>)". `publish()` now records
    every notice text added to the DOM from the click onwards (including a
    transient toast), so `confirmation_text()` can't miss a short-lived one.

Locators are structural (name attributes, the rtl twin that follows each EN
field, the form's last submit button), so the same code drives the /ar
interface without any Arabic selector.

QCTEST hygiene: every record is titled `QCTEST-<tc_id>-partner`, Display
Order 9900, Active Status UNTICKED (stays off the public carousel). It is
deleted by EXACT Entry-column title in the test's `finally`. The logo is
uploaded from the generated fixture partner_logo_qctest.png. The uploaded
Documents & Media copy is not deleted (not approved).
"""

import re
import time

from cms.pages.home_strategic_partners.home_strategic_partners_admin_page import (
    StrategicPartnersAdminPage,
)
from core.utils.waits import wait_until

LOGO_FIXTURE = "web/tests/home_strategic_partners/fixtures/partner_logo_qctest.png"
QCTEST_DISPLAY_ORDER = "9900"

EN_NAME = 'input[name="ObjectField_partnerName"]'
EN_ALT = 'input[name="ObjectField_logoAltText"]'
LOGO_INPUT = 'input[name="ObjectField_logoImage"]'
DISPLAY_ORDER = 'input[name="ObjectField_displayOrder"]'
ACTIVE = 'input[name="ObjectField_activeStatus"]'
FORM = f"form:has({EN_ALT})"
SUBMIT_BUTTONS = f'{FORM} button[type="submit"]'  # [Save as Draft, Publish] in that order
PICKER_IFRAME = 'iframe[src*="selectFileEntry"]'
CONFIRMATION = '[data-qc-oel-status], .alert-success, [role="status"], .alert-info, .toast'
# Same family the HeaderConfiguration page object reads (header_admin_component.SUCCESS_NOTICE_RE).
SUCCESS_NOTICE_RE = re.compile(
    r"Draft saved\.|Saved and submitted for (?:publishing|review)\.|Published\.|"
    r"Your request completed successfully\.", re.I)
PICKER_FILE_INPUT = 'input[type="file"]'
PICKER_ADD_BUTTON = "button.btn-primary:not(.dropdown-toggle):visible"
PICKER_BUDGET_MS = 60000
_NOTICE_OBSERVER_JS = """() => {
  window.__qcNotices = [];
  const seen = (t) => { t = (t || '').trim(); if (t && t.length < 300) window.__qcNotices.push(t); };
  const obs = new MutationObserver(ms => ms.forEach(m => m.addedNodes.forEach(n => {
    if (n.nodeType === 1 && n.matches && n.matches('.alert, .toast, [role=status], [role=alert], [data-qc-oel-status]')) seen(n.innerText);
    else if (n.nodeType === 3 && n.parentElement && n.parentElement.closest('.alert, .toast, [role=status], [data-qc-oel-status]')) seen(n.textContent);
  })));
  obs.observe(document.body, {childList: true, subtree: true, characterData: true});
  window.__qcNoticeObserver = obs;
}"""
ERROR_SURFACES = '[data-qc-oel-editbar], [role="alert"], .alert-danger, .form-feedback-item, .invalid-feedback'


def _is_save_post(request) -> bool:
    """A same-site document/fetch POST that is not the chatbot or analytics
    traffic the site polls with in the background."""
    url = request.url.lower()
    return (request.method == "POST" and "qcdev.ihorizons.com" in url
            and request.resource_type in ("document", "fetch", "xhr")
            and not any(noise in url for noise in ("chat", "analytics", "recaptcha")))


def qctest_title(tc_id: int) -> str:
    return f"QCTEST-{tc_id}-partner"


def _rtl_twin(en_selector: str) -> str:
    return f'xpath=(//input[@name="{en_selector.split(chr(34))[1]}"]/following::input[@dir="rtl"])[1]'


AR_NAME = _rtl_twin(EN_NAME)
AR_ALT = _rtl_twin(EN_ALT)


class ImageAltTextRecordPage(StrategicPartnersAdminPage):
    # ---- form ------------------------------------------------------------
    def open_create_form(self, locale: str = "en") -> "ImageAltTextRecordPage":
        self.open(self._manage_url(locale=locale))
        self._locale = locale
        self.wait_for(EN_ALT, timeout=35000)
        return self

    def fill_record(self, title: str, alt_en: str | None, alt_ar: str | None,
                    name_ar: str = "شريك اختبار QCTEST") -> "ImageAltTextRecordPage":
        """Fills every required field. None leaves an alt-text box untouched (empty)."""
        self.page.locator(EN_NAME).fill(title)
        self.page.locator(AR_NAME).fill(name_ar)
        if alt_en is not None:
            self.page.locator(EN_ALT).fill(alt_en)
        if alt_ar is not None:
            self.page.locator(AR_ALT).fill(alt_ar)
        self.page.locator(DISPLAY_ORDER).fill(QCTEST_DISPLAY_ORDER)
        active = self.page.locator(ACTIVE)
        if active.is_checked():
            active.uncheck()
        return self

    def set_alt_en(self, value: str) -> "ImageAltTextRecordPage":
        self.page.locator(EN_ALT).fill(value)
        return self

    def set_alt_ar(self, value: str) -> "ImageAltTextRecordPage":
        self.page.locator(AR_ALT).fill(value)
        return self

    def alt_en_value(self) -> str:
        return self.page.locator(EN_ALT).input_value()

    def alt_ar_value(self) -> str:
        return self.page.locator(AR_ALT).input_value()

    def alt_ar_direction(self) -> str:
        return self.page.locator(AR_ALT).get_attribute("dir") or ""

    def alt_fields_required(self) -> tuple[bool, bool]:
        return (self.page.locator(EN_ALT).evaluate("e => e.required"),
                self.page.locator(AR_ALT).evaluate("e => e.required"))

    def _open_picker(self):
        """Clicks the Logo Image field's own Select File button (the button in
        the same wrapper as the hidden ObjectField_logoImage textbox, which is
        locale-neutral), then waits for the picker's file input. The iframe is
        attached long before it reports visible, so its file input is the
        readiness signal.

        HEALED 2026-10-02: one live run's click landed while the form's upload
        script was not yet wired (the page sat with no modal for 60 s; see
        allure-results-cms-a11y-heal-20261002-2324, tc_134492/134517). The
        click is now retried: up to 3 attempts, each followed by a 20 s
        condition wait for the iframe, with overlays dismissed in between."""
        from core.web.overlays import dismiss_overlays

        button = self.page.locator(LOGO_INPUT).locator("xpath=..").locator("button").first
        button.wait_for(state="visible", timeout=30000)
        iframe = self.page.locator(PICKER_IFRAME).first
        for attempt in range(3):
            button.click()
            try:
                iframe.wait_for(state="attached", timeout=20000)
                break
            except Exception:  # noqa: BLE001 — retry; the final attempt re-raises below
                if attempt == 2:
                    raise
                dismiss_overlays(self.page)
        frame = self.page.frame_locator(PICKER_IFRAME).first
        frame.locator(PICKER_FILE_INPUT).wait_for(state="attached", timeout=PICKER_BUDGET_MS)
        return frame

    def upload_logo_fixture(self) -> "ImageAltTextRecordPage":
        """One structural path for both interfaces (EN and /ar): open the
        picker, set the fixture on its file input, wait until the picker's own
        "Add" button (btn-primary, not the "New" dropdown-toggle) is visible
        and enabled, click it, then wait for the picker to close."""
        frame = self._open_picker()
        # Unique file name per upload (2026-10-03): after ~40 uploads of the same
        # "partner_logo_qctest.png", Documents & Media began refusing it with
        # "An unexpected error occurred while uploading your file." while a fresh
        # name uploaded fine (reports/upload-verify-20261003-1301). Same bytes,
        # new name — passed as an in-memory payload, nothing written to disk.
        with open(LOGO_FIXTURE, "rb") as fh:
            payload = fh.read()
        frame.locator(PICKER_FILE_INPUT).set_input_files({
            "name": f"QCTEST-logo-{time.strftime('%Y%m%d%H%M%S')}-{time.time_ns() % 100000}.png",
            "mimeType": "image/png",
            "buffer": payload,
        })
        add = frame.locator(PICKER_ADD_BUTTON)
        add.first.wait_for(state="visible", timeout=PICKER_BUDGET_MS)
        wait_until(lambda: add.first.is_enabled(), timeout=30.0, poll=0.3,
                   message="picker Add button never became enabled after the upload")
        add.first.click()
        self.page.locator(PICKER_IFRAME).wait_for(state="detached", timeout=30000)
        return self

    # ---- the image upload dialog (134492) ----------------------------------
    def open_logo_picker(self) -> "ImageAltTextRecordPage":
        self._open_picker()
        return self

    def screenshot_png(self) -> bytes:
        return self.page.screenshot()

    def picker_alt_text_inputs(self) -> list[dict]:
        """Inputs inside the upload dialog whose label/name/placeholder/aria
        mentions alt text, plus whether each is required."""
        frame = [f for f in self.page.frames if "selectFileEntry" in (f.url or "")][0]
        return frame.evaluate("""() => Array.from(document.querySelectorAll('input, textarea'))
            .filter(e => e.type !== 'hidden')
            .map(e => ({label: ((e.labels && e.labels[0]) ? e.labels[0].innerText : '').trim(),
                        name: e.name || '', ph: e.placeholder || '', aria: e.getAttribute('aria-label') || '',
                        required: !!e.required}))
            .filter(i => /alt/i.test(i.label + ' ' + i.name + ' ' + i.ph + ' ' + i.aria))""")

    def picker_inputs_summary(self) -> list[str]:
        frame = [f for f in self.page.frames if "selectFileEntry" in (f.url or "")][0]
        return frame.evaluate("""() => Array.from(document.querySelectorAll('input, textarea, select'))
            .filter(e => e.type !== 'hidden').map(e => e.type + ':' + (e.name || e.getAttribute('aria-label') || ''))""")

    def close_picker(self) -> None:
        close = self.page.locator('.modal-dialog button.close, .modal-dialog [aria-label="close"], .modal-dialog [aria-label="Close"]')
        if close.count():
            close.first.click()
        else:
            self.page.keyboard.press("Escape")
        self.page.locator(PICKER_IFRAME).wait_for(state="detached", timeout=10000)

    # ---- publish + outcome ---------------------------------------------------
    def _texts(self, selector: str) -> list[str]:
        return [t.strip() for t in self.page.locator(selector).all_inner_texts() if t.strip()]

    def publish(self) -> "ImageAltTextRecordPage":
        """Clicks the form's last submit button ("Publish" for an Editor) and
        waits for the save request itself. If a POST fires, waits for its
        response and the reloaded page. If none fires within 10 s, the
        browser blocked the submit client-side (a valid "blocked" outcome),
        recorded in `self.last_publish_posted`. Confirmation and error texts
        present BEFORE the click are snapshotted, so only text that appears
        afterwards counts."""
        self._before_confirm = self._texts(CONFIRMATION)
        self._before_body = self.page.locator("body").inner_text()
        try:
            self.page.evaluate(_NOTICE_OBSERVER_JS)
        except Exception:  # noqa: BLE001 — observer is a bonus signal, never a blocker
            pass
        self._before_errors = self._texts(ERROR_SURFACES)
        self.last_publish_posted = False
        try:
            with self.page.expect_request(_is_save_post, timeout=10000) as req:
                self.page.locator(SUBMIT_BUTTONS).last.click()
            self.last_publish_posted = True
            try:
                req.value.response()
            except Exception:  # noqa: BLE001 — response may be superseded by the navigation
                pass
            self.page.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception:  # noqa: BLE001 — no POST: blocked client-side
            pass
        return self

    def _observed_notices(self) -> list[str]:
        try:
            return self.page.evaluate("() => window.__qcNotices || []")
        except Exception:  # noqa: BLE001 — a full reload drops the observer
            return []

    def confirmation_text(self, timeout: float = 20.0) -> str:
        """A success notice that appeared AFTER publish(): any notice text
        the DOM observer caught (transient toasts included), any new
        CONFIRMATION-surface text, or a SUCCESS_NOTICE_RE match in the body
        that wasn't there before. Bounded, condition-based wait; "" if none."""
        before_confirm = set(getattr(self, "_before_confirm", []))
        before_body = getattr(self, "_before_body", "")
        found = {"t": ""}

        def _read() -> bool:
            for t in self._observed_notices():
                if SUCCESS_NOTICE_RE.search(t):
                    found["t"] = t
                    return True
            for t in self._texts(CONFIRMATION):
                if t not in before_confirm:
                    found["t"] = t
                    return True
            body = self.page.locator("body").inner_text()
            for m in SUCCESS_NOTICE_RE.finditer(body):
                if m.group(0) not in before_body:
                    found["t"] = m.group(0)
                    return True
            return False
        try:
            wait_until(_read, timeout=timeout, poll=0.5, message="no success notice rendered")
        except Exception:  # noqa: BLE001
            pass
        return found["t"]

    def post_save_summary(self) -> str:
        """What the page shows after a save, for failure messages: the
        observer's captured notices and the preview header line."""
        lines = [l.strip() for l in self.page.locator("body").inner_text().splitlines()
                 if l.strip().startswith("Previewing")]
        return f"notices={self._observed_notices()} preview={lines[:1]}"

    def message_shown(self, expected: str, timeout: float = 15.0) -> bool:
        try:
            wait_until(lambda: expected in self.page.locator("body").inner_text(),
                       timeout=timeout, poll=0.5, message=f"{expected!r} never rendered")
            return True
        except Exception:  # noqa: BLE001
            return False

    def validation_evidence(self) -> dict:
        """What the page shows after a blocked publish, for failure messages.
        `new_errors` holds only error texts that appeared after the click.
        Page chrome that was already there (e.g. the activation-key banner)
        is excluded. `native_invalid` holds the browser's constraint messages,
        which follow the browser locale, not the page's."""
        before = set(getattr(self, "_before_errors", []))
        errors = self._texts(ERROR_SURFACES)
        native = self.page.evaluate("""() => Array.from(document.querySelectorAll('form input, form textarea'))
            .filter(e => e.willValidate && !e.checkValidity())
            .map(e => (e.name || ((e.labels && e.labels[0]) ? e.labels[0].innerText.trim() : '?')) + ': ' + e.validationMessage)""")
        return {"new_errors": [t for t in errors if t not in before][:10],
                "posted": getattr(self, "last_publish_posted", None),
                "native_invalid": native[:10]}

    # ---- entries list, by EXACT title -----------------------------------------
    def _row_exact(self, title: str):
        rows = self.page.locator(self.ENTRIES_TABLE_ROW)
        cell = self.page.locator("td.qc-oel__cell-title", has_text=re.compile(rf"^\s*{re.escape(title)}\s*$"))
        return rows.filter(has=cell)

    def open_list(self) -> "ImageAltTextRecordPage":
        self.open(self._manage_url(locale="en"))
        self.wait_for(f"{self.ENTRIES_TABLE_ROW}", first=True, timeout=35000)
        return self

    def row_status_exact(self, title: str) -> str:
        """Normalized status of the row whose Entry cell is exactly `title`;
        "" when no such row exists."""
        self.open_list()
        row = self._row_exact(title)
        if row.count() == 0:
            return ""
        from cms.pages.components.object_authoring_page import normalize_status
        return normalize_status(row.first.locator("td").nth(1).inner_text())

    def field_required(self, selector: str) -> bool:
        """True when the form field exists and is marked `required`."""
        field = self.page.locator(selector).first
        return field.count() > 0 and field.evaluate("e => e.required === true")

    def row_badge_raw(self, title: str) -> str:
        """The row's badge text verbatim, upper-cased ("" when no row). Unlike
        `row_status_exact`, keeps "INACTIVE": on this build a PUBLISHED record
        with Active Status unticked shows INACTIVE (confirmed live 2026-10-01),
        which `normalize_status` maps to Unknown."""
        self.open_list()
        row = self._row_exact(title)
        if row.count() == 0:
            return ""
        return row.first.locator("td").nth(1).inner_text().strip().upper()

    def open_record_for_edit(self, title: str) -> "ImageAltTextRecordPage":
        self.open_list()
        if self._row_exact(title).count() != 1:
            raise AssertionError(f"expected exactly one row titled {title!r}")
        self.open_entry_by_edit_link(title)
        self.wait_for(EN_ALT, timeout=15000)
        return self

    def delete_qctest_exact(self, title: str, max_rounds: int = 5) -> bool:
        """Deletes every row whose Entry cell is exactly `title`, one at a
        time, by its own entry id. Refuses any non-QCTEST title. Returns True
        when none remain. Never raises (teardown)."""
        if not title.startswith("QCTEST-"):
            raise ValueError(f"refusing to delete non-QCTEST record {title!r}")
        for _ in range(max_rounds):
            try:
                self.open_list()
                rows = self._row_exact(title)
                if rows.count() == 0:
                    return True
                entry_id = rows.first.locator("a[data-qc-oel-delete]").get_attribute("data-qc-oel-delete")
                if not entry_id:
                    return False
                self.page.once("dialog", lambda d: d.accept())
                link = self.page.locator(f'a[data-qc-oel-delete="{entry_id}"]')
                link.click(force=True)
                link.wait_for(state="detached", timeout=15000)
            except Exception:  # noqa: BLE001 — best-effort teardown; caller reports leftovers
                return False
        return False

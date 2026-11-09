"""
cms/pages/media_center/mc_subscriber_list_admin_page.py — Media Center
newsletter subscription (PBI 130709, suite 140368, batch 2, SUBS-A agent).

Three read-mostly surfaces, one module (one page-object file per agent):

  McSubscribeBand          public Media Center subscription band (logged out)
  McUnsubscribeLinkPage    public one-click unsubscribe page (the link the
                           Subscription Confirmation email carries)
  McSubscriberListAdminPage  staff list `manage-newsletter-subscriber`

LIVE RECON 2026-10-12 (qcdev, QC Site Content Editor 156488 + logged-out
contexts; one disposable address qctest.mchub.a+recon-1012211540@example.com):

  Public band  /web/qatar-chamber/media-center
    section.qc-mc-sub[data-qc-mcsub-ready="true"] > form[data-qc-mcsub-form]
    (novalidate) with input#qc-mc-sub-email (aria-label "Email address",
    placeholder "Enter Your E-mail Address") and button[data-qc-mcsub-btn]
    ("Subscribe"). The fragment trims the typed value and POSTs
    /o/qc-newsletter/subscribe?email=..&languageId=en_US|ar_SA&recaptchaToken=
    (score key -> empty token accepted). Body status success|duplicate|
    invalid|captcha|throttled|error is rendered into p[data-qc-mcsub-message]
    (role=status; class --ok / --error). Nothing identifying the SOURCE PAGE
    is sent — the footer newsletter posts to the same endpoint.

  Unsubscribe  /web/qatar-chamber/newsletter-unsubscribe?token=<unsubscribeToken>
    Looks the token up, shows the email + button[data-qc-unsub-confirm]
    ("Confirm Unsubscribe"); success state [data-qc-unsub-state="success"].

  Staff list   /web/qatar-chamber/manage-newsletter-subscriber
    "Newsletter Subscriber entries" + [data-qc-oel-count] "N total". View-only
    (no Add, no Edit, no Delete for the Editor). Filters (client-side over all
    fetched rows): input[data-qc-oel-q] (matches ANY field value),
    select[data-qc-oel-status-filter] ("" All statuses / Active /
    Unsubscribed, on the `active` field), "Subscribed from" / "to" date
    pickers (visible dd/mm/yyyy text box .qc-oel__dtp-text feeding hidden
    input[type=date][data-qc-oel-from|to]; range on lastSubscribedOn's ISO
    date part, both ends inclusive), button[data-qc-oel-reset] "Reset",
    button[data-qc-oel-export] "Export CSV" (browser-built CSV of the filtered
    rows, file newsletter-subscriber-<yyyy-mm-dd>.csv, header
    Email,Status,Subscription status,Subscribed on,Unsubscribed on).
    Columns: Email | Subscription status | Subscribed on | Unsubscribed on |
    Status (badge) | actions View (a[data-qc-oel-view=<id>]) / Preview /
    History. Pager select[data-qc-oel-page-size] (10 default, "0" = all).
    View opens div.qc-oel__viewer-panel[role=dialog] listing dt/dd: Preferred
    Language, Unsubscribe Token, Active, Last Subscribed On, Email, Last
    Unsubscribed On, Unsubscribe Confirmation Sent On + Record (Creator, Date
    Created/Modified, ERC, Friendly Url Path, Id, Status). There is NO Source
    Page field (the Object definition has none either).

DATA SAFETY: this module has NO delete / edit / unsubscribe-by-admin action.
The only write it can make is a public subscription or a token unsubscribe,
and both are refused unless the address is one of this agent's own
`qctest.mchub.a+...@example.com` test addresses (`is_own_address`).
"""

from __future__ import annotations

import csv as _csv
import io as _io
import os as _os
import re as _re
from datetime import date as _date
from datetime import datetime as _datetime

from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import cms_role_credentials, control_panel_url, web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher

logger = get_logger("mc_subscriber_list_admin_page")

PUBLIC_PATH = "/web/qatar-chamber/media-center"
SUBSCRIBER_PATH = "/web/qatar-chamber/manage-newsletter-subscriber"
UNSUBSCRIBE_PATH = "/web/qatar-chamber/newsletter-unsubscribe"

EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "subsA")

ROLE_EDITOR = "Site Content Editor"
ROLE_USER_IDS = {ROLE_EDITOR: "156488"}

OWN_ADDRESS_RE = _re.compile(r"^qctest\.mchub\.a\+[\w.-]+@example\.com$", _re.I)

# Band copy (exact wording from the story, as shipped in the fragment).
MSG_SUCCESS_EN = ("You have successfully subscribed to Media Center updates. "
                  "Thank you for staying connected with Qatar Chamber.")
MSG_DUPLICATE_EN = "This email address is already subscribed."
BAND_HEADING_EN = "Stay connected to Qatar's business story"

UNSUB_SUCCESS_EN = "You have been successfully unsubscribed from the Qatar Chamber newsletter."

ROW_DATE_FORMAT = "%m/%d/%Y, %I:%M:%S %p"   # en-US toLocaleString() as rendered
EMPTY_CELL = "—"


def own_address(tc: str, stamp: str, tag: str = "") -> str:
    return f"qctest.mchub.a+{tc}{tag}-{stamp}@example.com"


def is_own_address(email: str) -> bool:
    return bool(OWN_ADDRESS_RE.match((email or "").strip()))


def parse_row_date(text: str) -> _datetime | None:
    text = " ".join((text or "").split())
    if not text or text == EMPTY_CELL:
        return None
    try:
        return _datetime.strptime(text, ROW_DATE_FORMAT)
    except ValueError:
        return None


def ui_date(day: _date) -> str:
    """dd/mm/yyyy — what the list's date pickers accept when typed."""
    return f"{day.day:02d}/{day.month:02d}/{day.year}"


def _evidence_path(name: str, ext: str = "png") -> str:
    _os.makedirs(EVIDENCE_DIR, exist_ok=True)
    return _os.path.join(EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + "." + ext)


class _Evidence(BasePage):
    def evidence(self, name: str, full_page: bool = False) -> str:
        path = _evidence_path(name)
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "mc130709-subsA")
        except Exception as exc:  # noqa: BLE001 — evidence only
            logger.warning("evidence %s failed: %r", name, exc)
        return path


# =============================================================================
# Public subscription band
# =============================================================================
class McSubscribeBand(_Evidence):
    BAND = "section.qc-mc-sub"
    BAND_READY = 'section.qc-mc-sub[data-qc-mcsub-ready="true"]'
    HEADING = "[data-qc-mcsub-heading]"
    EMAIL_INPUT = "#qc-mc-sub-email"
    SUBSCRIBE_BTN = "section.qc-mc-sub button[data-qc-mcsub-btn]"
    MESSAGE = "[data-qc-mcsub-message]"
    SUBSCRIBE_URL_PART = "/o/qc-newsletter/subscribe"

    def open_hub(self, locale: str = "en") -> "McSubscribeBand":
        self.open(web_url(PUBLIC_PATH, locale=locale))
        self.page.locator(self.BAND_READY).first.wait_for(state="attached", timeout=60000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def is_signed_in(self) -> bool:
        return bool(self.page.evaluate(
            "() => !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"))

    def band_shown(self) -> bool:
        band = self.page.locator(self.BAND).first
        return band.count() > 0 and band.is_visible() and self.page.locator(self.EMAIL_INPUT).is_visible()

    def heading(self) -> str:
        return " ".join(self.page.locator(self.HEADING).first.inner_text().split())

    def subscribe(self, typed_value: str) -> dict:
        """Types `typed_value` exactly as given and clicks Subscribe.
        Returns {api_status, http, message, message_ok, request_email}."""
        candidate = typed_value.strip()
        if not is_own_address(candidate.lower()):
            raise ValueError(f"refusing to subscribe {typed_value!r}: not a SUBS-A test address")
        self.page.locator(self.EMAIL_INPUT).scroll_into_view_if_needed()
        self.page.locator(self.EMAIL_INPUT).fill(typed_value)
        with self.page.expect_response(lambda r: self.SUBSCRIBE_URL_PART in r.url, timeout=60000) as info:
            self.page.locator(self.SUBSCRIBE_BTN).click()
        response = info.value
        try:
            body = response.json()
        except Exception:  # noqa: BLE001 — an unparseable body is reported as-is
            body = {}
        message = self.page.locator(self.MESSAGE)
        try:
            wait_until(lambda: message.is_visible() and message.inner_text().strip() != "", timeout=20.0, poll=0.3)
        except WaitTimeoutError:
            pass
        from urllib.parse import parse_qs, urlparse  # noqa: PLC0415
        sent = parse_qs(urlparse(response.url).query).get("email", [""])[0]
        cls = message.get_attribute("class") or ""
        return {"api_status": body.get("status"), "http": response.status,
                "message": " ".join(message.inner_text().split()) if message.is_visible() else "",
                "message_ok": "qc-mc-sub-message--ok" in cls, "request_email": sent,
                "at": _datetime.now()}

    def band_evidence(self, name: str) -> str:
        path = _evidence_path(name)
        try:
            self.page.locator(self.BAND).first.screenshot(path=path)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            with open(path, "rb") as handle:
                attach_screenshot(handle.read(), name, "mc130709-subsA")
        except Exception:  # noqa: BLE001
            return self.evidence(name)
        return path


# =============================================================================
# Public one-click unsubscribe page (the confirmation email's link)
# =============================================================================
class McUnsubscribeLinkPage(_Evidence):
    CONFIRM_BTN = "[data-qc-unsub-confirm]"
    EMAIL = "[data-qc-unsub-email]"
    STATE = '[data-qc-unsub-state="{name}"]'

    def open_link(self, token: str) -> "McUnsubscribeLinkPage":
        self.open(web_url(f"{UNSUBSCRIBE_PATH}?token={token}"))
        return self

    def shown_email(self) -> str:
        self.page.locator(self.CONFIRM_BTN).wait_for(state="visible", timeout=45000)
        return self.page.locator(self.EMAIL).first.inner_text().strip()

    def confirm(self) -> str:
        """Clicks Confirm Unsubscribe; returns the final visible state text."""
        email = self.shown_email()
        if not is_own_address(email):
            raise ValueError(f"refusing to unsubscribe {email!r}: not a SUBS-A test address")
        self.page.locator(self.CONFIRM_BTN).click()
        names = ("success", "already", "invalid", "error")
        wait_until(lambda: any(self.page.locator(self.STATE.format(name=n)).is_visible() for n in names),
                   timeout=45.0, poll=0.3)
        for n in names:
            node = self.page.locator(self.STATE.format(name=n))
            if node.is_visible():
                return " ".join(node.inner_text().split())
        return ""


# =============================================================================
# Staff subscriber list
# =============================================================================
class McSubscriberListAdminPage(_Evidence):
    ROOT = ".qc-oel"
    COUNT = "[data-qc-oel-count]"
    LIST_STATUS = "[data-qc-oel-status]"
    ROW_LOADED = "[data-qc-oel-view]"
    SEARCH = "input[data-qc-oel-q]"
    STATUS_FILTER = "select[data-qc-oel-status-filter]"
    DATE_TEXT = ".qc-oel__filters .qc-oel__dtp-text"       # [0] Subscribed from, [1] to
    DATE_FROM = "input[data-qc-oel-from]"
    DATE_TO = "input[data-qc-oel-to]"
    RESET = "button[data-qc-oel-reset]"
    EXPORT = "button[data-qc-oel-export]"
    PAGE_SIZE = "select[data-qc-oel-page-size]"
    HEADERS = "table[data-qc-oel-table] thead th"
    VIEWER = ".qc-oel__viewer-panel"
    VIEWER_CLOSE = "button[data-qc-oel-viewer-close]"   # the backdrop carries the same hook

    _ROWS_JS = """() => [...document.querySelectorAll('tbody[data-qc-oel-body] tr')]
        .filter(t => t.offsetParent !== null && t.querySelector('[data-qc-oel-view]'))
        .map(t => { const td = [...t.querySelectorAll('td')].map(c => c.innerText.trim());
                    const v = t.querySelector('[data-qc-oel-view]');
                    return {email: td[0] || '', subscription_status: td[1] || '', subscribed_on: td[2] || '',
                            unsubscribed_on: td[3] || '', status_badge: td[4] || '',
                            entry_id: v ? v.getAttribute('data-qc-oel-view') : ''}; })"""

    def __init__(self, page):
        super().__init__(page)
        self.role = ""

    # ---- session ----------------------------------------------------------------
    def login_as_role(self, role: str = ROLE_EDITOR, attempts: int = 3) -> str:
        """Real login in an auth-free context. "ok" / "auth_failed" / "unknown".
        Signs any current session out first (the shared session guard may have
        re-logged a dropped session in as TEST_USER), and retries a login page
        that times out under qcdev load."""
        email, password = cms_role_credentials(role)
        outcome = "unknown"
        for _ in range(attempts):
            try:
                if self.signed_in_user()[0]:
                    self.page.goto(control_panel_url("/c/portal/logout"), wait_until="domcontentloaded",
                                   timeout=90000)
                login = CmsLoginPage(self.page)
                login.open_login()
                login.login(email, password)
                self.role = role
                return "ok"
            except Exception as exc:  # noqa: BLE001 — classified below, then retried
                logger.warning("login as %s failed: %r", role, exc)
                try:
                    body = self.page.locator("body").inner_text()
                except Exception:  # noqa: BLE001
                    body = ""
                if "Authentication failed" in body:
                    return "auth_failed"
        return outcome

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']""")
        return info[0], info[1]

    # ---- list -----------------------------------------------------------------------
    def _ensure_role(self) -> None:
        """BasePage's session guard re-logs a dropped session in as TEST_USER; this
        page must stay on the role the test signed in as, so sign back in as it."""
        expected = ROLE_USER_IDS.get(self.role)
        if expected and self.signed_in_user()[0] != expected:
            logger.warning("session is no longer %s — signing in again", self.role)
            self.login_as_role(self.role)
            self.open(web_url(SUBSCRIBER_PATH, locale="en"))

    def open_list(self) -> "McSubscriberListAdminPage":
        """Opens the list in English, waits for the rows, shows every row (page size All)."""
        self.open(web_url(SUBSCRIBER_PATH, locale="en"))
        self._ensure_role()
        self.page.locator(self.ROW_LOADED).first.wait_for(state="attached", timeout=90000)
        size = self.page.locator(self.PAGE_SIZE)
        if size.count() and size.first.is_visible() and size.first.input_value() != "0":
            size.first.select_option("0")
        total = self.total_count()
        try:
            wait_until(lambda: total is None or len(self.rows()) >= total, timeout=20.0, poll=0.3)
        except WaitTimeoutError:
            logger.warning("page size All did not settle to %s rows", total)
        _dismiss_chatbot_launcher(self.page)
        return self

    def heading_text(self) -> str:
        return self.page.locator(f"{self.ROOT} .qc-oel__title").first.inner_text().strip()

    def total_count(self) -> int | None:
        node = self.page.locator(self.COUNT)
        if not node.count():
            return None
        match = _re.search(r"(\d+)\s*total", node.first.inner_text())
        return int(match.group(1)) if match else None

    def headers(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(self.HEADERS).all_inner_texts()]

    def rows(self) -> list[dict]:
        return self.page.evaluate(self._ROWS_JS)

    def rows_for(self, email: str) -> list[dict]:
        """Rows (of those currently shown) whose Email cell is exactly `email` (case-insensitive)."""
        return [r for r in self.rows() if r["email"].strip().lower() == email.strip().lower()]

    def _settle(self) -> None:
        """Filtering is synchronous client-side; wait for the DOM to stop changing."""
        last = {"sig": None, "stable": 0}

        def _stable() -> bool:
            sig = (len(self.rows()), self.page.locator(self.LIST_STATUS).first.inner_text()
                   if self.page.locator(self.LIST_STATUS).count() else "")
            last["stable"] = last["stable"] + 1 if sig == last["sig"] else 0
            last["sig"] = sig
            return last["stable"] >= 2

        try:
            wait_until(_stable, timeout=10.0, poll=0.25)
        except WaitTimeoutError:
            pass

    def search(self, text: str) -> "McSubscriberListAdminPage":
        self.page.locator(self.SEARCH).fill(text)
        self._settle()
        return self

    def set_status_filter(self, value: str) -> "McSubscriberListAdminPage":
        """value: "Active" / "Unsubscribed" / "" (All statuses)."""
        self.page.locator(self.STATUS_FILTER).select_option(value)
        self._settle()
        return self

    def status_filter_options(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(f"{self.STATUS_FILTER} option").all_inner_texts()]

    def set_date_range(self, start: _date, end: _date) -> "McSubscriberListAdminPage":
        """Types both dates (dd/mm/yyyy) into the visible pickers, as a user does."""
        boxes = self.page.locator(self.DATE_TEXT)
        for index, day in ((0, start), (1, end)):
            box = boxes.nth(index)
            box.click()
            box.fill("")
            box.type(ui_date(day))
            box.press("Tab")
        try:
            wait_until(lambda: self.date_range_values() == (start.isoformat(), end.isoformat()),
                       timeout=10.0, poll=0.3)
        except WaitTimeoutError:
            pass
        self._settle()
        return self

    def date_range_values(self) -> tuple[str, str]:
        return (self.page.locator(self.DATE_FROM).input_value(), self.page.locator(self.DATE_TO).input_value())

    def reset_filters(self) -> "McSubscriberListAdminPage":
        self.page.locator(self.RESET).click()
        self._settle()
        return self

    def filter_state(self) -> dict:
        return {"q": self.page.locator(self.SEARCH).input_value(),
                "status": self.page.locator(self.STATUS_FILTER).input_value(),
                "from": self.page.locator(self.DATE_FROM).input_value(),
                "to": self.page.locator(self.DATE_TO).input_value(),
                "page_size": self.page.locator(self.PAGE_SIZE).input_value()
                if self.page.locator(self.PAGE_SIZE).count() else ""}

    def list_message(self) -> str:
        node = self.page.locator(self.LIST_STATUS)
        return node.first.inner_text().strip() if node.count() and node.first.is_visible() else ""

    def wait_for_row(self, email: str, timeout: float = 90.0, predicate=None) -> list[dict]:
        """Reloads the list until a row for `email` (matching `predicate(row)`) shows."""
        found = {"rows": []}

        def _present() -> bool:
            self.open_list()
            self.search(email)
            found["rows"] = self.rows_for(email)
            return bool(found["rows"]) and (predicate is None or all(predicate(r) for r in found["rows"]))

        try:
            wait_until(_present, timeout=timeout, poll=3.0)
        except WaitTimeoutError:
            pass
        return found["rows"]

    # ---- export -------------------------------------------------------------------
    def export_csv(self, name: str) -> dict:
        """Clicks Export CSV; saves the download under the evidence dir.
        Returns {suggested, path, header, rows(list[dict]), raw}."""
        with self.page.expect_download(timeout=30000) as info:
            self.page.locator(self.EXPORT).click()
        download = info.value
        path = _evidence_path(name, "csv")
        download.save_as(path)
        with open(path, encoding="utf-8-sig", newline="") as handle:
            raw = handle.read()
        reader = list(_csv.reader(_io.StringIO(raw)))
        header = reader[0] if reader else []
        rows = [dict(zip(header, r)) for r in reader[1:]]
        return {"suggested": download.suggested_filename, "path": path, "header": header, "rows": rows,
                "raw": raw}

    def export_button_text(self) -> str:
        node = self.page.locator(self.EXPORT)
        return node.first.inner_text().strip() if node.count() and node.first.is_visible() else ""

    # ---- record viewer (read-only) ---------------------------------------------------
    def view_record(self, email: str) -> dict:
        """Opens View on the row whose Email is exactly `email`; returns {label: value}."""
        rows = self.rows_for(email)
        if len(rows) != 1:
            raise AssertionError(f"expected exactly one row for {email!r} to open, found {len(rows)}")
        self.page.locator(f'a[data-qc-oel-view="{rows[0]["entry_id"]}"]').click()
        panel = self.page.locator(self.VIEWER).first
        panel.wait_for(state="visible", timeout=20000)
        try:
            wait_until(lambda: panel.locator("dt").count() > 0, timeout=15.0, poll=0.3)
        except WaitTimeoutError:
            pass
        fields = self.page.evaluate(
            """(sel) => { const p = document.querySelector(sel); if (!p) return {};
                const out = {}; const dts = p.querySelectorAll('dt');
                dts.forEach(dt => { const dd = dt.nextElementSibling; out[dt.innerText.trim()] = dd ? dd.innerText.trim() : ''; });
                out['__title'] = (p.querySelector('[data-qc-oel-viewer-title]') || {innerText: ''}).innerText.trim();
                return out; }""", self.VIEWER)
        return fields

    def close_viewer(self) -> None:
        close = self.page.locator(self.VIEWER_CLOSE)
        if close.count() and close.first.is_visible():
            close.first.click()

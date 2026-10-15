"""
cms/pages/media_center/mc_subscriber_admin_b_page.py — PBI 130709 batch 2
(SUBS-B): Media Center subscriber management (`manage-newsletter-subscriber`)
— manual unsubscribe, its History trail, reactivation, role access — plus the
News module driver for case 149285 (news edit reflected in the hub feed).

LIVE RECON 2026-10-12 (read-only except the agent's own example.com rows):

  Public band (logged-out /web/qatar-chamber/media-center): fragment
  `qc-media-center-subscribe` — input [data-qc-mcsub-input], button
  [data-qc-mcsub-btn], message [data-qc-mcsub-message] (class `--ok` on
  success). Posts to /o/qc-newsletter/subscribe; the endpoint THROTTLES
  ("Too many attempts. Please try again in a few minutes.", HTTP 429
  {"status":"throttled"}) after a handful of posts from one client, so
  subscribe() backs off and retries inside a bounded budget.

  Subscriber list (`manage-newsletter-subscriber`, a qc-oel entry list):
    columns  Email | Subscription status | Subscribed on | Unsubscribed on |
             Status (badge) | actions
    filters  search [data-qc-oel-q], status select [data-qc-oel-status-filter]
             (Active / Unsubscribed), Subscribed from/to, Reset, Export CSV
             [data-qc-oel-export]
    actions  TEST_USER: Edit, Preview, Unsubscribe ([data-qc-oel-reject] —
             confirm() 'Unsubscribe: "<email>"?'), Unpublish, History, Delete.
             Site Content Editor: View, Preview, History (no Unsubscribe) +
             Export CSV. Author / Form Manager: HTTP 404 page reading
             "Access Denied. You do not have permission to perform this action."
    History  expands in-table (ul.qc-oel__history-list): action, who, when and
             per-field changes (e.g. Active Subscription true -> false).

  News feed on the hub (fragment qc-mc-nf) reads /o/qc-media-center-api/news,
  whose items are entries of the **News** object (`manage-qcdemo131059-news`,
  ERCs QCDEMO-131059-NEWS-*), NOT of `manage-news-article` (the Home "Latest
  News" object) that case 149285 names — see the test module.

DELETE SAFETY: subscriber rows are deleted only by EXACT email in the
`qctest.mchub.b+` namespace, re-verified on the row (title cell + delete label)
and in the confirm() text; News entries only when captured by this session
(list-id diff + exact QCTEST-130709-NEWS- title) and re-verified. No
positional, looping or substring delete exists here.
"""

from __future__ import annotations

import json as _json
import os as _os
import re as _re
from dataclasses import dataclass as _dataclass
from datetime import datetime as _datetime

from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.tenders.tender_admin_page import TenderWorkflowAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import cms_role_credentials as _cms_role_credentials
from config.settings import control_panel_url, settings, web_url
from core.utils.logger import get_logger as _get_logger
from core.utils.waits import WaitTimeoutError as _WaitTimeoutError
from core.utils.waits import wait_until as _wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays

_logger = _get_logger("mc_subscriber_admin_b_page")

EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "subsB")

MEDIA_CENTER_PATH = "/web/qatar-chamber/media-center"
SUBSCRIBER_PATH = "/web/qatar-chamber/manage-newsletter-subscriber"
CASE_NEWS_PATH = "/web/qatar-chamber/manage-news-article"
NEWS_SLUG = "qcdemo131059-news"
NEWS_API = "/o/qc-media-center-api/news"

EMAIL_PREFIX = "qctest.mchub.b+"
EMAIL_DOMAIN = "example.com"
NEWS_PREFIX = "QCTEST-130709"

ROLE_ADMIN = "Administrator (TEST_USER)"
ROLE_EDITOR = "Site Content Editor"
ROLE_AUTHOR = "Site Content Author"
ROLE_FORM_MANAGER = "Form Manager"
ROLE_MEMBER = "Site Member"
ROLE_USER_IDS = {ROLE_EDITOR: "156488", ROLE_AUTHOR: "156492", ROLE_FORM_MANAGER: "156500",
                 ROLE_MEMBER: "156516"}

MSG_ACCESS_DENIED = "Access Denied. You do not have permission to perform this action."
MSG_SUBSCRIBED = "You have successfully subscribed to Media Center updates."
MSG_THROTTLED = "Too many attempts"
MSG_SAVED_AND_PUBLISHED = "Saved and published."

LIST_DATE_FORMAT = "%m/%d/%Y, %I:%M:%S %p"
_EMAIL_RE = _re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")


def subscriber_email(tc: str, stamp: str) -> str:
    return f"{EMAIL_PREFIX}{tc}-{stamp}@{EMAIL_DOMAIN}"


def is_own_email(email: str) -> bool:
    email = (email or "").strip()
    return email.startswith(EMAIL_PREFIX) and email.endswith(f"@{EMAIL_DOMAIN}") and email == email.lower()


def parse_list_date(text: str) -> _datetime | None:
    try:
        return _datetime.strptime(" ".join((text or "").split()), LIST_DATE_FORMAT)
    except ValueError:
        return None


def _shot(page, name: str, full_page: bool = True) -> str:
    _os.makedirs(EVIDENCE_DIR, exist_ok=True)
    path = _os.path.join(EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
    try:
        png = page.screenshot(path=path, full_page=full_page)
        from core.utils.reporting import attach_screenshot  # noqa: PLC0415
        attach_screenshot(png, name, "mc130709_subsB")
    except Exception as exc:  # noqa: BLE001 — evidence only
        _logger.warning("evidence %s failed: %r", name, exc)
    return path


# ===========================================================================
# Public hub (logged-out): subscription band + news feed
# ===========================================================================
class McHubPublicView(BasePage):
    BAND = "section.qc-mc-sub"
    INPUT = "[data-qc-mcsub-input]"
    BUTTON = "[data-qc-mcsub-btn]"
    MESSAGE = "[data-qc-mcsub-message]"
    SUBSCRIBE_ENDPOINT = "/o/qc-newsletter/subscribe"
    NEWS_SECTION = "[data-qc-mcnf-section-object]"
    NEWS_TITLES = ".qc-mc-nf-lead-title, .qc-mc-nf-card-title"

    def open_hub(self, locale: str = "en") -> "McHubPublicView":
        self.open(web_url(MEDIA_CENTER_PATH, locale=locale))
        dismiss_overlays(self.page, grace_ms=1500)
        try:
            self.page.locator(self.BAND).first.wait_for(state="attached", timeout=30000)
        except Exception:  # noqa: BLE001 — reported by band_visible()
            pass
        return self

    def signed_in(self) -> bool:
        return bool(self.page.evaluate(
            "() => !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"))

    def band_visible(self) -> bool:
        band = self.page.locator(self.BAND).first
        return band.count() > 0 and band.is_visible() and self.page.locator(self.INPUT).first.is_visible()

    def message(self) -> dict:
        node = self.page.locator(self.MESSAGE).first
        return {"text": " ".join(node.inner_text().split()) if node.count() else "",
                "class": (node.get_attribute("class") or "") if node.count() else ""}

    def subscribe_once(self, email: str) -> dict:
        self.page.locator(self.INPUT).first.fill(email)
        with self.page.expect_response(lambda r: self.SUBSCRIBE_ENDPOINT in r.url, timeout=60000) as info:
            self.page.locator(self.BUTTON).first.click()
        response = info.value
        try:
            body = response.text()[:300]
        except Exception:  # noqa: BLE001
            body = ""
        try:
            _wait_until(lambda: self.message()["text"] != "", timeout=10.0, poll=0.3)
        except _WaitTimeoutError:
            pass
        return {"status": response.status, "body": body, **self.message()}

    @staticmethod
    def is_throttled(result: dict) -> bool:
        """The endpoint answers a throttle as HTTP 429 OR as HTTP 200 with
        {"status":"throttled"} (both seen live 2026-10-12)."""
        return (result.get("status") == 429 or '"throttled"' in (result.get("body") or "")
                or MSG_THROTTLED in (result.get("text") or ""))

    def subscribe(self, email: str, budget_s: float = 1500.0, backoff_s: float = 120.0) -> dict:
        """Subscribes `email` from the band; on the endpoint's throttle (429)
        re-opens the page and retries every `backoff_s` within `budget_s`."""
        if not is_own_email(email):
            raise ValueError(f"{email!r} is not a {EMAIL_PREFIX}…@{EMAIL_DOMAIN} test address")
        attempts: list[dict] = []

        def _try() -> bool:
            if attempts:
                self.open_hub()
            result = self.subscribe_once(email)
            attempts.append(result)
            _logger.info("subscribe %s -> %s %s", email, result["status"], result["text"])
            return not self.is_throttled(result)

        try:
            _wait_until(_try, timeout=budget_s, poll=backoff_s)
        except _WaitTimeoutError:
            pass
        last = dict(attempts[-1]) if attempts else {"status": None, "body": "", "text": "", "class": ""}
        last["attempts"] = len(attempts)
        last["throttled"] = self.is_throttled(last) if attempts else False
        last["ok"] = last.get("status") == 200 and '"success"' in (last.get("body") or "")
        return last

    # ---- news feed ------------------------------------------------------------------
    def news_feed_titles(self) -> list[str]:
        section = self.page.locator(self.NEWS_SECTION).first
        if section.count() == 0:
            return []
        try:
            _wait_until(lambda: section.locator(self.NEWS_TITLES).count() > 0, timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            return []
        return [" ".join(t.split()) for t in section.locator(self.NEWS_TITLES).all_inner_texts()]

    def poll_news_feed(self, predicate, timeout: float = 120.0) -> tuple[bool, list[str]]:
        seen = {"titles": []}

        def _ok() -> bool:
            self.open_hub()
            seen["titles"] = self.news_feed_titles()
            return bool(predicate(seen["titles"]))

        try:
            _wait_until(_ok, timeout=timeout, poll=5.0)
            return True, seen["titles"]
        except _WaitTimeoutError:
            return False, seen["titles"]

    def news_api_items(self) -> list[dict]:
        status, text = self.page.evaluate(
            "async (u) => { const r = await fetch(u, {cache: 'no-store'}); return [r.status, await r.text()]; }",
            NEWS_API)
        if status != 200:
            return []
        return [{"erc": i.get("erc"), "id": i.get("id"), "titleEn": i.get("titleEn"),
                 "publicationDate": i.get("publicationDate")} for i in _json.loads(text).get("items", [])]

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)


# ===========================================================================
# Subscriber list (`manage-newsletter-subscriber`)
# ===========================================================================
class McSubscriberAdminPage(BasePage):
    BODY = "tbody[data-qc-oel-body]"
    ROW_LOADED = "[data-qc-oel-history]"
    SEARCH = "[data-qc-oel-q]"
    STATUS_FILTER = "select[data-qc-oel-status-filter]"
    PAGE_SIZE = "select[data-qc-oel-page-size]"
    EXPORT = "[data-qc-oel-export]"
    HEADERS = "table[data-qc-oel-table] thead th"
    UNSUBSCRIBE_BY_ID = '[data-qc-oel-reject="{entry_id}"]'
    UNSUBSCRIBE_BY_EMAIL = '[data-qc-oel-unsubscribe][data-qc-oel-unsubscribe-email="{email}"]'
    HISTORY_BY_ID = '[data-qc-oel-history="{entry_id}"]'
    DELETE_BY_ID = 'a[data-qc-oel-delete="{entry_id}"]'
    HISTORY_ROW = "tr[data-qc-oel-history-row]"
    ROW_ACTION_ATTRS = ("view", "reject", "unpublish", "publish", "approve", "history", "delete", "unsubscribe")

    _ROWS_JS = r"""(attrs) => [...document.querySelectorAll('tbody[data-qc-oel-body] tr')]
        .filter(r => !r.hasAttribute('data-qc-oel-history-row'))
        .map(r => {
            const tds = r.querySelectorAll('td');
            let id = '';
            for (const a of attrs) { const n = r.querySelector('[data-qc-oel-' + a + ']');
                                     if (n) { id = n.getAttribute('data-qc-oel-' + a); break; } }
            const acts = attrs.filter(a => r.querySelector('[data-qc-oel-' + a + ']'));
            const links = [...r.querySelectorAll('td:last-child a, td:last-child button')].map(a => a.innerText.trim()).filter(Boolean);
            const edit = r.querySelector('a[href*="editEntry="]');
            const t = (i) => tds[i] ? tds[i].innerText.trim() : '';
            return {entry_id: id, email: t(0), subscription_status: t(1), subscribed_on: t(2),
                    unsubscribed_on: t(3), status: t(4), actions: acts, links: links,
                    edit_href: edit ? edit.getAttribute('href') : '',
                    visible: r.getClientRects().length > 0};
        })"""

    _TOAST_OBSERVER_JS = r"""() => { window.__qcSubsSeen = [];
        if (window.__qcSubsObs) window.__qcSubsObs.disconnect();
        window.__qcSubsObs = new MutationObserver(ms => { for (const m of ms) {
            const nodes = m.type === 'characterData' ? [m.target.parentElement] : [...m.addedNodes, m.target];
            for (const n of nodes) { if (!n || n.nodeType !== 1) continue;
                const cls = (n.className && n.className.baseVal === undefined) ? String(n.className) : '';
                const t = (n.innerText || '').trim();
                if (t && t.length < 400 && /alert|toast|notice|flash|status|message/i.test(cls + ' ' + (n.getAttribute('role') || '')))
                    window.__qcSubsSeen.push(cls + ' :: ' + t.replace(/\s+/g, ' ')); } } });
        window.__qcSubsObs.observe(document.body, {childList: true, subtree: true, characterData: true,
                                                   attributes: true, attributeFilter: ['hidden', 'class']}); }"""

    def __init__(self, page):
        super().__init__(page)
        self.role = ""
        self.last_http_status: int | None = None

    # ---- session -----------------------------------------------------------------
    def login_admin(self) -> str:
        # Healed 2026-10-14 (ready32 N): post-reset qcdev takes ~13-20 s to land a login,
        # past the 15 s sign-in wait; one retry when the session did land / was slow.
        login = CmsLoginPage(self.page)
        try:
            login.open_login()
            login.login(settings.test_user, settings.test_password)
        except Exception:  # noqa: BLE001
            self.page.wait_for_load_state("load")
            if not self.signed_in_user()[0]:
                login.open_login()
                login.login(settings.test_user, settings.test_password)
        self.role = ROLE_ADMIN
        return "ok"

    def login_as_role(self, role: str) -> str:
        email, password = _cms_role_credentials(role)
        login = CmsLoginPage(self.page)
        login.open_login()
        self.role = role
        try:
            login.login(email, password)
            return "ok"
        except Exception:  # noqa: BLE001 — classified below
            try:
                self.page.wait_for_load_state("load")
                if self.signed_in_user()[0]:
                    return "ok"
            except Exception:  # noqa: BLE001
                pass
            body = self.page.locator("body").inner_text()
            return "auth_failed" if "Authentication failed" in body else "unknown"

    def signed_in_user(self) -> tuple[str, str]:
        info = self.page.evaluate(
            """() => (window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())
                ? [String(Liferay.ThemeDisplay.getUserId()), String(Liferay.ThemeDisplay.getUserName() || '')]
                : ['', '']""")
        return info[0], info[1]

    # ---- navigation ----------------------------------------------------------------
    def open_list(self, expect_rows: bool = True) -> "McSubscriberAdminPage":
        response = self.page.goto(control_panel_url(SUBSCRIBER_PATH), wait_until="load")
        self.last_http_status = response.status if response else None
        if expect_rows:
            self.page.locator(self.ROW_LOADED).first.wait_for(state="attached", timeout=90000)
            select = self.page.locator(self.PAGE_SIZE)
            if select.count() and select.first.is_visible() and select.first.input_value() != "0":
                select.first.select_option("0")
                try:
                    _wait_until(lambda: self.total_count() is None
                                or len(self.rows()) >= (self.total_count() or 0), timeout=15.0, poll=0.3)
                except _WaitTimeoutError:
                    _logger.warning("page-size ALL did not settle")
            _dismiss_chatbot_launcher(self.page)
        return self

    def access_probe(self) -> dict:
        """Opens the list expecting a refusal; reports what the session actually sees."""
        self.open_list(expect_rows=False)
        try:
            _wait_until(lambda: self.page.locator(self.ROW_LOADED).count() > 0
                        or MSG_ACCESS_DENIED in self.page.locator("body").inner_text()
                        or "Access Denied" in self.page.locator("body").inner_text(), timeout=45.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        body = self.page.locator("body").inner_text()
        own_session = {e.lower() for e in _EMAIL_RE.findall(body)}
        return {
            "http_status": self.last_http_status,
            "url": self.page.url,
            "signed_in_user": self.signed_in_user(),
            "access_denied_exact": MSG_ACCESS_DENIED in body,
            "denial_lines": [ln.strip() for ln in body.splitlines()
                             if _re.search(r"denied|permission|not found|could not load", ln, _re.I)][:6],
            "subscriber_rows": self.page.locator(self.ROW_LOADED).count(),
            "emails_on_page": sorted(own_session),
            "export_button": self.page.locator(self.EXPORT).count(),
        }

    # ---- reading ---------------------------------------------------------------------
    def total_count(self) -> int | None:
        node = self.page.locator("[data-qc-oel-count]")
        if node.count() == 0:
            return None
        match = _re.search(r"(\d+)\s*total", node.first.inner_text())
        return int(match.group(1)) if match else None

    def column_headers(self) -> list[str]:
        return [" ".join(t.split()) for t in self.page.locator(self.HEADERS).all_inner_texts() if t.strip()]

    def rows(self) -> list[dict]:
        return self.page.evaluate(self._ROWS_JS, list(self.ROW_ACTION_ATTRS))

    def visible_rows(self) -> list[dict]:
        return [r for r in self.rows() if r["visible"]]

    def rows_for(self, email: str) -> list[dict]:
        """Every row (visible or not) whose Email cell is exactly `email`."""
        return [r for r in self.rows() if r["email"].strip().lower() == email.strip().lower()]

    def search(self, text: str) -> "McSubscriberAdminPage":
        box = self.page.locator(self.SEARCH).first
        box.fill(text)
        try:
            _wait_until(lambda: all(text.lower() in r["email"].lower() for r in self.visible_rows()),
                        timeout=10.0, poll=0.3)
        except _WaitTimeoutError:
            pass
        return self

    def filter_status(self, value: str) -> "McSubscriberAdminPage":
        self.page.locator(self.STATUS_FILTER).first.select_option(value)
        try:
            _wait_until(lambda: all(r["subscription_status"] == value or r["status"].casefold() == value.casefold()
                                    for r in self.visible_rows()), timeout=10.0, poll=0.3)
        except _WaitTimeoutError:
            pass
        return self

    def wait_row(self, email: str, predicate, timeout: float = 60.0) -> dict:
        """Re-opens the list until the ONE row of `email` satisfies `predicate`."""
        seen = {"row": {}}

        def _ok() -> bool:
            self.open_list()
            rows = self.rows_for(email)
            seen["row"] = rows[0] if len(rows) == 1 else {"_count": len(rows), "_rows": rows}
            return len(rows) == 1 and bool(predicate(rows[0]))

        try:
            _wait_until(_ok, timeout=timeout, poll=3.0)
        except _WaitTimeoutError:
            pass
        return seen["row"]

    # ---- actions -----------------------------------------------------------------------
    def _guard_own_row(self, email: str) -> dict:
        if not is_own_email(email):
            raise ValueError(f"refusing to act on {email!r}: not a {EMAIL_PREFIX} test address")
        rows = self.rows_for(email)
        if len(rows) != 1 or not rows[0]["entry_id"]:
            raise AssertionError(f"expected exactly one row for {email!r}, found {len(rows)}")
        return rows[0]

    def unsubscribe(self, email: str) -> dict:
        """Clicks the row's Unsubscribe action on OUR OWN address; accepts only
        a confirm() naming that address. Returns dialogs, toast-ish nodes seen,
        and the click time."""
        self.search(email)
        row = self._guard_own_row(email)
        control = self.page.locator(self.UNSUBSCRIBE_BY_ID.format(entry_id=row["entry_id"]))
        label_attr = "data-qc-oel-label"
        if control.count() == 0:
            # LIVE 2026-10-13 (149981 fix): the duplicate reject link was dropped;
            # the one remaining row action is the e-mail-keyed Unsubscribe link.
            control = self.page.locator(self.UNSUBSCRIBE_BY_EMAIL.format(email=email))
            label_attr = "data-qc-oel-unsubscribe-email"
        if control.count() != 1 or (control.first.get_attribute(label_attr) or "").strip() != email:
            raise AssertionError(f"Unsubscribe control for {email!r} not found / mislabelled ({control.count()})")
        dialogs: list[str] = []

        def _on_dialog(dialog):
            dialogs.append(f"{dialog.type}: {dialog.message}")
            dialog.accept() if (email in dialog.message or dialog.type == "alert") else dialog.dismiss()

        # The action reloads the page, so the observer is also registered as
        # an init script (it re-arms on the reloaded document) and the
        # visible alert/toast nodes are read after the reload as well.
        if not getattr(self, "_toast_init_armed", False):
            self.page.add_init_script(
                "document.addEventListener('DOMContentLoaded', () => { const f = " + self._TOAST_OBSERVER_JS
                + "; f(); });")
            self._toast_init_armed = True
        self.page.evaluate(self._TOAST_OBSERVER_JS)
        self.page.on("dialog", _on_dialog)
        clicked_at = _datetime.now()
        try:
            control.first.click()
            try:
                _wait_until(lambda: any(r["subscription_status"] != "Active" for r in self.rows_for(email))
                            or bool(self.page.evaluate("() => (window.__qcSubsSeen || []).length")),
                            timeout=30.0, poll=0.5)
            except _WaitTimeoutError:
                pass
            try:
                _wait_until(lambda: bool(self.page.evaluate("() => (window.__qcSubsSeen || []).length")),
                            timeout=6.0, poll=0.3)
            except _WaitTimeoutError:
                pass
        finally:
            self.page.remove_listener("dialog", _on_dialog)
        try:
            self.page.wait_for_load_state("load")
        except Exception:  # noqa: BLE001
            pass
        try:
            _wait_until(lambda: bool(self.page.evaluate("() => (window.__qcSubsSeen || []).length"))
                        or bool(self.visible_alerts()), timeout=10.0, poll=0.3)
        except _WaitTimeoutError:
            pass
        seen = list(self.page.evaluate("() => window.__qcSubsSeen || []")) + self.visible_alerts()
        return {"dialogs": dialogs, "seen": seen, "clicked_at": clicked_at, "entry_id": row["entry_id"],
                "row_after": (self.rows_for(email) or [{}])[0]}

    ALERTS = ".alert, [role='alert'], .lfr-alert-container .alert, [data-qc-oel-editbar], .toast, .qc-oel__flash"

    def visible_alerts(self) -> list[str]:
        try:
            return [" ".join(t.split()) for t in self.page.locator(self.ALERTS).all_inner_texts() if t.strip()]
        except Exception:  # noqa: BLE001 — mid-navigation
            return []

    def click_token_unsubscribe(self, email: str) -> dict:
        """Clicks the token-based Unsubscribe link ([data-qc-oel-unsubscribe],
        shown to the Editor since 2026-10-13) on OUR OWN row; accepts confirms
        naming the address; returns dialogs, alerts and the row afterwards."""
        self.search(email)
        self._guard_own_row(email)
        link = self.page.locator(f'[data-qc-oel-unsubscribe][data-qc-oel-unsubscribe-email="{email}"]')
        if link.count() != 1:
            return {"present": False}
        dialogs: list[str] = []

        def _on_dialog(dialog):
            dialogs.append(f"{dialog.type}: {dialog.message}")
            dialog.accept() if (email in dialog.message or dialog.type == "alert") else dialog.dismiss()

        self.page.on("dialog", _on_dialog)
        try:
            link.first.click()
            try:
                _wait_until(lambda: bool(dialogs) and bool(self.visible_alerts()), timeout=15.0, poll=0.5)
            except _WaitTimeoutError:
                pass
            try:
                self.page.wait_for_load_state("load")
            except Exception:  # noqa: BLE001
                pass
        finally:
            self.page.remove_listener("dialog", _on_dialog)
        body = self.page.locator("body").inner_text()
        return {"present": True, "dialogs": dialogs, "alerts": self.visible_alerts(),
                "access_denied": MSG_ACCESS_DENIED in body or any(MSG_ACCESS_DENIED in d for d in dialogs)}

    def history(self, email: str) -> list[dict]:
        """Expands the row's in-table History -> [{action, who, when, changes:[{field, before, after}], text}]."""
        self.search(email)
        row = self._guard_own_row(email) if is_own_email(email) else None
        if row is None:
            return []
        self.page.locator(self.HISTORY_BY_ID.format(entry_id=row["entry_id"])).first.click()
        cell = self.page.locator(self.HISTORY_ROW).first
        try:
            _wait_until(lambda: cell.count() == 1 and "Loading" not in cell.inner_text()
                        and cell.locator("li").count() > 0, timeout=20.0, poll=0.5)
        except _WaitTimeoutError:
            return []
        return self.page.evaluate(r"""() => {
            const list = document.querySelector('tr[data-qc-oel-history-row] ul.qc-oel__history-list');
            if (!list) return [];
            return [...list.children].map(li => {
                const q = (s) => { const n = li.querySelector(':scope > ' + s); return n ? n.innerText.trim() : ''; };
                const changes = [...li.querySelectorAll('.qc-oel__history-changes > li')].map(c => {
                    const b = c.querySelectorAll('bdi');
                    return {field: (c.querySelector('.qc-oel__history-field') || {}).innerText || '',
                            before: b[0] ? b[0].innerText : '', after: b[1] ? b[1].innerText : ''}; });
                return {action: q('.qc-oel__history-action'), who: q('.qc-oel__history-who'),
                        when: q('.qc-oel__history-when'), changes: changes,
                        text: li.innerText.replace(/\s+/g, ' ').trim()}; });
        }""")

    def export_csv(self, download_dir: str) -> dict:
        button = self.page.locator(self.EXPORT).first
        result = {"button": button.count() > 0 and button.is_visible(), "filename": "", "path": "", "text": ""}
        if not result["button"]:
            return result
        with self.page.expect_download(timeout=60000) as info:
            button.click()
        download = info.value
        _os.makedirs(download_dir, exist_ok=True)
        path = _os.path.join(download_dir, download.suggested_filename or "subscribers.csv")
        download.save_as(path)
        with open(path, encoding="utf-8-sig", errors="replace") as handle:
            result.update(filename=download.suggested_filename, path=path, text=handle.read())
        return result

    def api_set_active(self, email: str, active: bool) -> dict:
        """The 'direct update request' a user could send without the UI action:
        PATCH /o/c/newslettersubscribers/<id> {active} on OUR OWN row only."""
        self.search(email)
        row = self._guard_own_row(email)
        self.page.wait_for_function("() => window.Liferay && Liferay.authToken", timeout=30000)
        status, text = self.page.evaluate(
            """async ([u, b]) => { const r = await fetch(u, {method: 'PATCH', headers: {'Accept': 'application/json',
                    'Content-Type': 'application/json', 'x-csrf-token': Liferay.authToken}, body: JSON.stringify(b)});
                return [r.status, await r.text()]; }""",
            [f"/o/c/newslettersubscribers/{row['entry_id']}", {"active": bool(active)}])
        return {"status": int(status), "body": text[:400], "entry_id": row["entry_id"]}

    def delete_own(self, email: str) -> bool:
        """Deletes the ONE row whose Email is exactly `email` (our namespace only)."""
        try:
            if not is_own_email(email):
                _logger.error("DELETE REFUSED: %r is not a test address", email)
                return False
            self.open_list()
            rows = self.rows_for(email)
            if not rows:
                return True
            if len(rows) != 1:
                _logger.error("DELETE REFUSED for %r: %s rows carry it", email, len(rows))
                return False
            entry_id = rows[0]["entry_id"]
            link = self.page.locator(self.DELETE_BY_ID.format(entry_id=entry_id))
            if link.count() != 1 or (link.first.get_attribute("data-qc-oel-label") or "").strip() != email:
                _logger.error("DELETE REFUSED for %r: delete link mismatch", email)
                return False
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                dialog.accept() if email in dialog.message else dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                self.search(email)
                link.first.click()
                try:
                    link.first.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001 — verified below
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            if not any(email in m for m in dialogs):
                _logger.error("DELETE NOT CONFIRMED for %r: %s", email, dialogs)
                return False
            self.open_list()
            return not self.rows_for(email)
        except Exception as exc:  # noqa: BLE001
            _logger.error("delete_own(%r) failed: %r", email, exc)
            return False

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)


# ===========================================================================
# News module (feed source) — disposable QCTEST-130709-NEWS-* articles only
# ===========================================================================
@_dataclass(frozen=True)
class NewsEntry:
    title: str
    entry_id: str
    code: str

    def in_namespace(self) -> bool:
        return (self.title.strip().startswith(NEWS_PREFIX) and bool(self.entry_id) and bool(self.code)
                and not self.code.upper().startswith("QCDEMO-"))


class McNewsAdminPage(TenderWorkflowAdminPage):
    """`manage-<slug>` driver for a news object on the confirmed Object
    Authoring mechanics (role login, Load-All list, save-outcome probe,
    `ObjectField_<key>` / `qc-ar-<key>` access, in-table History)."""

    FORM = 'form:has([name="ObjectField_title"])'
    EVIDENCE_DIR = EVIDENCE_DIR
    SAVE_REQUEST_PATTERN = _re.compile(r"edit_info_item|/o/c/")

    def __init__(self, page, slug: str = NEWS_SLUG):
        super().__init__(page)
        self.slug = slug

    def open_create_form(self) -> "McNewsAdminPage":
        self.open(self._manage_url(locale="en"))
        self._entry_code = None
        self.page.get_by_role("button", name=self.SUBMIT_NAME).first.wait_for(timeout=90000)
        self._form().locator('[name="ObjectField_title"]').first.wait_for(timeout=60000)
        _dismiss_chatbot_launcher(self.page)
        return self

    def open_entry_en(self, code: str) -> "McNewsAdminPage":
        self.open(self._manage_url(edit_entry=code, locale="en"))
        self._entry_code = code
        self._form().locator('[name="ObjectField_title"]').first.wait_for(state="attached", timeout=90000)
        try:
            _wait_until(lambda: self.text_value("title") != "", timeout=15.0, poll=0.5)
        except _WaitTimeoutError:
            pass
        _dismiss_chatbot_launcher(self.page)
        return self

    UPLOAD_LABELS = {"image": "Image", "thumbnail": "Thumbnail"}

    def upload_block_text(self, key: str) -> str:  # type: ignore[override]
        label = self.UPLOAD_LABELS[key]
        node = self._form().locator(f'input[name="ObjectField_{key}"]').first
        return node.evaluate(
            r"""(el, label) => { let c = el.parentElement;
                for (let i = 0; i < 8 && c && !(c.innerText || '').includes(label); i++) c = c.parentElement;
                const v = el.value || el.placeholder || '';
                return ((c ? c.innerText : '') + ' ' + v).replace(/\s+/g, ' ').trim(); }""",
            label)

    def tick_category(self, label: str) -> "McNewsAdminPage":
        box = self._form().get_by_role("checkbox", name=label, exact=True)
        box.first.check()
        if not box.first.is_checked():
            raise AssertionError(f"Category Tags {label!r} did not tick")
        return self

    def fill_article(self, title: str, title_ar: str, body: str, body_ar: str, date_ddmmyyyy: str,
                     active: bool = True, category: str = "Collaboration",
                     image: str | None = None) -> "McNewsAdminPage":
        self.fill_en("title", title)
        self.fill_ar("title", title_ar)
        self.page.locator(self._rich_iframe("description")).first.wait_for(timeout=30000)
        self.fill_rich("description", body)
        if self.page.locator(self._rich_ar_iframe("description")).count():
            self.fill_rich_ar("description", body_ar)
        self.tick_category(category)
        if image:
            self.upload("image", image, stem="qctest-130709-news")
        self.set_date("publicationDate", date_ddmmyyyy)
        self.set_active_status(active)
        return self

    def rows_titled(self, title: str) -> list[dict]:
        self.open_list_all()
        return [r for r in self.list_rows() if r["title"].strip() == title.strip()]

    def identify_created(self, title: str, ids_before: set[str]) -> NewsEntry | None:
        if not title.startswith(NEWS_PREFIX):
            raise ValueError(f"{title!r} is not in the {NEWS_PREFIX} namespace")
        self.open_list_all()
        fresh = [r for r in self.list_rows() if r["entry_id"] not in ids_before and r["code"]
                 and not r["code"].upper().startswith("QCDEMO-") and r["title"].strip() == title.strip()]
        if len(fresh) != 1:
            _logger.warning("identify_created(%r): %s candidates %s", title, len(fresh), fresh)
            return None
        entry = NewsEntry(title=fresh[0]["title"].strip(), entry_id=fresh[0]["entry_id"], code=fresh[0]["code"])
        self.owned_entry_ids.add(entry.entry_id)
        return entry

    def row_status_of(self, entry: NewsEntry) -> str:
        from cms.pages.components.object_authoring_page import normalize_status  # noqa: PLC0415
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return normalize_status(" ".join(rows[0]["status"].split())) if len(rows) == 1 else ""

    def row_status_raw_of(self, entry: NewsEntry) -> str:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return " ".join(rows[0]["status"].split()) if len(rows) == 1 else ""

    def row_title_of(self, entry: NewsEntry) -> str:
        rows = [r for r in self.list_rows() if r["entry_id"] == entry.entry_id]
        return rows[0]["title"].strip() if len(rows) == 1 else ""

    def delete_disposable(self, entry: NewsEntry, current_title: str) -> bool:
        """Deletes exactly the captured article (title re-verified) or refuses."""
        try:
            if (not isinstance(entry, NewsEntry) or not entry.in_namespace()
                    or entry.entry_id not in self.owned_entry_ids or not current_title.startswith(NEWS_PREFIX)):
                _logger.error("DELETE REFUSED: %r is not a captured %s article", entry, NEWS_PREFIX)
                return False
            self.open_list_all()
            if not self.is_list_fully_expanded():
                self.open_list_all()
            rows = [r for r in self.list_rows() if r["delete_id"] == entry.entry_id]
            if len(rows) != 1 or rows[0]["code"] != entry.code or rows[0]["title"].strip() != current_title:
                _logger.error("DELETE REFUSED for %r: row reads %s", entry, rows)
                return False
            link = self.page.locator(self.DELETE_LINK_BY_ID.format(entry_id=entry.entry_id))
            if link.count() != 1:
                return False
            names = [current_title, entry.code]
            dialogs: list[str] = []

            def _on_dialog(dialog):
                dialogs.append(dialog.message)
                dialog.accept() if any(n in dialog.message for n in names) else dialog.dismiss()

            self.page.on("dialog", _on_dialog)
            try:
                link.first.click(force=True)
                try:
                    link.first.wait_for(state="detached", timeout=20000)
                except Exception:  # noqa: BLE001
                    pass
            finally:
                self.page.remove_listener("dialog", _on_dialog)
            if not any(any(n in m for n in names) for m in dialogs):
                _logger.error("DELETE NOT CONFIRMED for %r: %s", entry, dialogs)
                return False
            self.open_list_all()
            gone = not any(r["entry_id"] == entry.entry_id for r in self.list_rows())
            if gone:
                self.owned_entry_ids.discard(entry.entry_id)
            return gone
        except Exception as exc:  # noqa: BLE001
            _logger.error("delete of %r failed: %r", entry, exc)
            return False

    def evidence(self, name: str, full_page: bool = True) -> str:
        return _shot(self.page, name, full_page)

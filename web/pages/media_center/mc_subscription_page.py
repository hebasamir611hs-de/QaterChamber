"""
web/pages/media_center/mc_subscription_page.py — FE-SUBS (PBI 130709, Azure
plan 137724 / suite 140368, batch 3 FRONTEND).

Public Media Center subscription band + the public one-click unsubscribe page,
plus a READ-ONLY subscriber-record reader for the staff-side checks.

  McSubscriptionBand     /web/qatar-chamber/media-center (AR /ar/web/...)
  McUnsubscribeLinkPage  /web/qatar-chamber/newsletter-unsubscribe?token=<t>
  McSubscriberRecords    manage-newsletter-subscriber list + /o/c/newslettersubscribers
                         (TEST_USER session; read-only)

LOCATOR EXTRACTION (live qcdev 2026-10-18, logged-out, 1920x1080 / 768x1024 /
390x844 / 375x812, EN + AR):

  Band  section.qc-mc-sub[data-qc-mcsub-ready="true"][dir=ltr|rtl]
          .qc-mc-sub-band  (radius/padding; layers .qc-mc-sub-texture,
                            .qc-mc-sub-gradient (the brand gradient), .qc-mc-sub-decor)
          .qc-mc-sub-inner (flex row on desktop, column <= tablet)
          span.qc-mc-sub-badge[data-qc-mcsub-badge] > img.qc-mc-sub-badge-img  (envelope)
          h2[data-qc-mcsub-heading]  p[data-qc-mcsub-desc]
          form[data-qc-mcsub-form][novalidate]
            input#qc-mc-sub-email[data-qc-mcsub-input][type=email]
            button[data-qc-mcsub-btn] > span[data-qc-mcsub-btn-label] + svg.qc-mc-sub-btn-ico
          p[data-qc-mcsub-message][role=status]  (class --ok / --error)
        Copy comes from the hero singleton QCDEMO-130709-HERO-MAIN
        (/o/c/mediacenterheros: subscriptionHeading / subscriptionDescription /
        emailFieldPlaceholder / subscribeButtonLabel / subscriptionIcon) with a
        built-in bilingual fallback. Empty and format validation are CLIENT-side
        (no request leaves); a valid address POSTs
        /o/qc-newsletter/subscribe?email=..&languageId=en_US|ar_SA&recaptchaToken=
        -> {"status": success|duplicate|invalid|captcha|throttled|error}. The
        endpoint throttles per client ("Too many attempts", HTTP 429 or 200
        {status: throttled}); `subscribe_with_backoff` waits it out.

  Unsubscribe page  section.qc-unsub — states [data-qc-unsub-state=
        loading|confirm|success|invalid|already|error] (only one not hidden),
        h1[data-qc-unsub-title], [data-qc-unsub-email],
        button[data-qc-unsub-confirm]. The link does NOT unsubscribe on open:
        it shows the address + "Confirm Unsubscribe"; the click POSTs
        /o/qc-newsletter/unsubscribe?token=. Title / prompt / success /
        already copy may be overlaid from the page-config object
        NewsletterUnsubscribePage (QCDEMO-129566-NEWSLETTER-UNSUBSCRIBE-PAGE-main).

DATA SAFETY: the only writes this module can make are a public subscription
and a token unsubscribe, both refused unless the address is one of FE-SUBS's
own `qctest.mchub.fe+...@example.com` addresses. The record reader never
edits, unsubscribes or deletes.
"""

from __future__ import annotations

import json as _json
import os as _os
import re as _re
from datetime import datetime as _datetime
from datetime import timezone as _timezone
from urllib.parse import parse_qs as _parse_qs
from urllib.parse import quote as _quote
from urllib.parse import urlparse as _urlparse

from cms.pages.media_center.mc_subscriber_admin_b_page import McSubscriberAdminPage
from config.settings import PROJECT_ROOT as _PROJECT_ROOT
from config.settings import web_url
from core.utils.logger import get_logger
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage
from core.web.overlays import _dismiss_chatbot_launcher, dismiss_overlays

logger = get_logger("mc_subscription_page")

HUB_PATH = "/web/qatar-chamber/media-center"
UNSUBSCRIBE_PATH = "/web/qatar-chamber/newsletter-unsubscribe"
EVIDENCE_DIR = _os.path.join(str(_PROJECT_ROOT), "reports", "mc130709", "FE-SUBS")

# example.com or any of its sub-domains (reserved, RFC 2606) — the 150/151-char cases need a long domain
OWN_ADDRESS_RE = _re.compile(r"^qctest\.mchub\.fe\+[\w.-]+@([a-z0-9-]+\.)*example\.com$", _re.I)

THROTTLE_TEXT = "Too many attempts"
THROTTLE_TEXT_AR = "محاولات كثيرة"


def own_address(tc: str, stamp: str, tag: str = "") -> str:
    return f"qctest.mchub.fe+{tc}{tag}-{stamp}@example.com"


def is_own_address(email: str) -> bool:
    return bool(OWN_ADDRESS_RE.match((email or "").strip()))


def parse_iso(value) -> _datetime | None:
    if not value:
        return None
    try:
        return _datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def utc_now() -> _datetime:
    return _datetime.now(_timezone.utc)


def _evidence_path(name: str, ext: str = "png") -> str:
    _os.makedirs(EVIDENCE_DIR, exist_ok=True)
    return _os.path.join(EVIDENCE_DIR, _re.sub(r"[^\w.-]+", "_", name)[:120] + "." + ext)


class _Evidence(BasePage):
    def evidence(self, name: str, full_page: bool = False, locator: str | None = None) -> str:
        path = _evidence_path(name)
        try:
            if locator and self.page.locator(locator).count():
                png = self.page.locator(locator).first.screenshot(path=path)
            else:
                png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "mc130709-fesubs")
        except Exception as exc:  # noqa: BLE001 — evidence only
            logger.warning("evidence %s failed: %r", name, exc)
        return path

    def is_signed_in(self) -> bool:
        return bool(self.page.evaluate(
            "() => !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"))


# =============================================================================
# Public subscription band
# =============================================================================
class McSubscriptionBand(_Evidence):
    SECTION = "section.qc-mc-sub"
    SECTION_READY = 'section.qc-mc-sub[data-qc-mcsub-ready="true"]'
    BAND = ".qc-mc-sub-band"
    GRADIENT = ".qc-mc-sub-gradient"
    TEXTURE = ".qc-mc-sub-texture"
    DECOR = ".qc-mc-sub-decor"
    INNER = ".qc-mc-sub-inner"
    ICON_CIRCLE = "[data-qc-mcsub-badge]"
    ICON_IMG = "[data-qc-mcsub-badge] img, [data-qc-mcsub-badge] svg"
    BODY = ".qc-mc-sub-body"
    HEADING = "[data-qc-mcsub-heading]"
    DESCRIPTION = "[data-qc-mcsub-desc]"
    FORM = "form[data-qc-mcsub-form]"
    INPUT = "input[data-qc-mcsub-input]"
    BUTTON = "button[data-qc-mcsub-btn]"
    BUTTON_LABEL = "[data-qc-mcsub-btn-label]"
    BUTTON_ICON = "svg.qc-mc-sub-btn-ico"
    MESSAGE = "[data-qc-mcsub-message]"
    FOOTER = ".qc-global-site-footer"
    VIDEO_FEED_FOCUSABLES = "section.qc-mc-vf a[href]:visible, section.qc-mc-vf button:visible"
    SUBSCRIBE_URL_PART = "/o/qc-newsletter/subscribe"

    def __init__(self, page):
        super().__init__(page)
        self.locale = "en"
        self._requests: list[dict] = []
        self.page.on("request", self._on_request)

    def _on_request(self, request) -> None:
        if self.SUBSCRIBE_URL_PART in request.url:
            sent = _parse_qs(_urlparse(request.url).query)
            self._requests.append({"url": request.url, "method": request.method,
                                   "email": sent.get("email", [""])[0],
                                   "languageId": sent.get("languageId", [""])[0]})

    # ---- navigation ------------------------------------------------------------
    def open_hub(self, locale: str = "en") -> "McSubscriptionBand":
        self.locale = locale
        self.open(web_url(HUB_PATH, locale=locale))
        self.page.locator(self.SECTION_READY).first.wait_for(state="attached", timeout=60000)
        dismiss_overlays(self.page, grace_ms=1500)
        _dismiss_chatbot_launcher(self.page)
        # copy is overlaid from the hero record asynchronously; wait for the heading
        wait_until(lambda: self.page.locator(self.HEADING).inner_text().strip() != "", timeout=20.0, poll=0.3)
        return self

    def http_status_of_hub(self, locale: str = "en") -> int | None:
        response = self.page.goto(web_url(HUB_PATH, locale=locale), wait_until="domcontentloaded", timeout=90000)
        self.locale = locale
        self.page.locator(self.SECTION_READY).first.wait_for(state="attached", timeout=60000)
        dismiss_overlays(self.page, grace_ms=1500)
        _dismiss_chatbot_launcher(self.page)
        return response.status if response else None

    def scroll_to_band(self) -> "McSubscriptionBand":
        self.page.locator(self.SECTION).first.scroll_into_view_if_needed()
        return self

    def title(self) -> str:
        return self.page.title()

    # ---- reads -------------------------------------------------------------------
    def copy(self) -> dict:
        icon = self.page.locator(self.ICON_IMG).first
        icon_state = icon.evaluate(
            """e => ({tag: e.tagName.toLowerCase(), loaded: e.tagName.toLowerCase() !== 'img'
                       || (e.complete && e.naturalWidth > 0),
                      w: e.getBoundingClientRect().width, h: e.getBoundingClientRect().height})"""
        ) if icon.count() else {"tag": "", "loaded": False, "w": 0, "h": 0}
        return {
            "heading": " ".join(self.page.locator(self.HEADING).inner_text().split()),
            "description": " ".join(self.page.locator(self.DESCRIPTION).inner_text().split()),
            "placeholder": self.page.locator(self.INPUT).get_attribute("placeholder") or "",
            "button_label": " ".join(self.page.locator(self.BUTTON_LABEL).inner_text().split()),
            "button_enabled": self.page.locator(self.BUTTON).is_enabled(),
            "input_editable": self.page.locator(self.INPUT).is_editable(),
            "icon_visible": self.page.locator(self.ICON_CIRCLE).is_visible() and icon.count() > 0
            and icon.is_visible(),
            "icon": icon_state,
            "band_visible": self.page.locator(self.BAND).is_visible(),
            "section_dir": self.page.locator(self.SECTION).get_attribute("dir") or "",
        }

    def box(self, locator: str) -> dict:
        """Document-space box + a few computed styles of the first match."""
        return self.page.locator(locator).first.evaluate(
            """(el) => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
                return {x: r.x + scrollX, y: r.y + scrollY, w: r.width, h: r.height,
                        right: r.right + scrollX, bottom: r.bottom + scrollY,
                        vx: r.x, vright: r.right, textAlign: s.textAlign, direction: s.direction,
                        visible: r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'}; }""")

    def layout(self) -> dict:
        names = {"band": self.BAND, "icon": self.ICON_CIRCLE, "heading": self.HEADING,
                 "description": self.DESCRIPTION, "form": self.FORM, "input": self.INPUT, "button": self.BUTTON}
        return {k: self.box(v) for k, v in names.items()}

    def document_state(self) -> dict:
        return self.page.evaluate(
            """() => ({dir: document.documentElement.getAttribute('dir') || '', lang: document.documentElement.lang,
                       scroll_width: document.documentElement.scrollWidth,
                       client_width: document.documentElement.clientWidth,
                       viewport: [innerWidth, innerHeight]})""")

    def band_above_footer(self) -> dict:
        band, footer = self.box(self.SECTION), self.box(self.FOOTER)
        return {"band_bottom": band["bottom"], "footer_top": footer["y"]}

    def element_at_centre_is(self, locator: str) -> bool:
        """True when a tap at the element's centre lands on it (nothing overlays it)."""
        self.page.locator(locator).first.scroll_into_view_if_needed()
        return bool(self.page.locator(locator).first.evaluate(
            """(el) => { const r = el.getBoundingClientRect();
                const hit = document.elementFromPoint(r.x + r.width / 2, r.y + r.height / 2);
                return !!hit && (hit === el || el.contains(hit)); }"""))

    # ---- input --------------------------------------------------------------------
    def type_email(self, text: str) -> "McSubscriptionBand":
        self.scroll_to_band()
        self.page.locator(self.INPUT).fill(text)
        return self

    def clear_email(self) -> "McSubscriptionBand":
        self.page.locator(self.INPUT).fill("")
        return self

    def input_value(self) -> str:
        return self.page.locator(self.INPUT).input_value()

    def focus_email_field(self) -> "McSubscriptionBand":
        self.page.locator(self.INPUT).focus()
        return self

    def input_is_focused(self) -> bool:
        return self.is_focused(self.INPUT)

    def tab_to_email_field(self, max_presses: int = 15) -> bool:
        """Keyboard-only: focus the last focusable of the section before the band
        (the video feed) and Tab forward until the email field holds focus."""
        self.page.locator(self.VIDEO_FEED_FOCUSABLES).last.focus()
        return self.press_tab_until_focused(self.INPUT, max_presses=max_presses)

    def email_focus_style(self) -> dict:
        return self.page.locator(self.INPUT).evaluate(
            """e => { const s = getComputedStyle(e);
                return {outline_style: s.outlineStyle, outline_width: s.outlineWidth, outline_color: s.outlineColor,
                        box_shadow: s.boxShadow, border_color: s.borderTopColor, focus_visible: e.matches(':focus-visible')}; }""")

    def typed_text_visual_order(self) -> dict:
        """Lays the field's current value out with the input's own computed
        direction/font in a throw-away span inside the form and reports where the
        first char, the '@' and the last char land, so a bidi reversal of the
        address (e.g. '@' jumping to an edge) is detected from real geometry."""
        return self.page.locator(self.INPUT).evaluate(
            """(inp) => {
                const s = getComputedStyle(inp); const v = inp.value;
                const span = document.createElement('span');
                span.textContent = v; span.dir = s.direction;
                Object.assign(span.style, {position: 'absolute', visibility: 'hidden', whiteSpace: 'pre',
                    font: s.font, direction: s.direction, unicodeBidi: s.unicodeBidi});
                inp.parentElement.appendChild(span);
                const rect = (i) => { const r = document.createRange(); r.setStart(span.firstChild, i);
                                      r.setEnd(span.firstChild, i + 1); return r.getBoundingClientRect().x; };
                const at = v.indexOf('@');
                const out = {value: v, direction: s.direction, unicode_bidi: s.unicodeBidi, text_align: s.textAlign,
                             x_first: rect(0), x_at: at >= 0 ? rect(at) : null, x_last: rect(v.length - 1)};
                span.remove(); return out; }""")

    # ---- submission ------------------------------------------------------------------
    def requests_sent(self) -> list[dict]:
        return list(self._requests)

    def message(self) -> dict:
        node = self.page.locator(self.MESSAGE).first
        if not node.count():
            return {"text": "", "visible": False, "ok": False, "error": False, "direction": "", "align": ""}
        cls = node.get_attribute("class") or ""
        st = node.evaluate("e => { const s = getComputedStyle(e); return [s.direction, s.textAlign]; }")
        visible = node.is_visible()
        return {"text": " ".join(node.inner_text().split()) if visible else "", "visible": visible,
                "ok": "qc-mc-sub-message--ok" in cls, "error": "qc-mc-sub-message--error" in cls,
                "direction": st[0], "align": st[1]}

    def _wait_message(self, timeout: float = 30.0) -> dict:
        try:
            wait_until(lambda: self.message()["text"] != "", timeout=timeout, poll=0.3)
        except WaitTimeoutError:
            pass
        return self.message()

    def _act(self, via: str) -> None:
        if via == "enter":
            self.page.locator(self.INPUT).press("Enter")
        elif via == "dblclick":
            self.page.locator(self.BUTTON).dblclick()
        else:
            self.page.locator(self.BUTTON).click()

    def submit_without_request(self, via: str = "click", watch_s: float = 4.0) -> dict:
        """For client-side validation outcomes: submits and reports the message
        plus every subscribe request that left within `watch_s` (expected none)."""
        before = len(self._requests)
        self.scroll_to_band()
        self._act(via)
        msg = self._wait_message(timeout=10.0)
        try:
            wait_until(lambda: len(self._requests) > before, timeout=watch_s, poll=0.25)
        except WaitTimeoutError:
            pass
        return {**msg, "requests": self._requests[before:]}

    def submit(self, typed_value: str | None, via: str = "click") -> dict:
        """Types `typed_value` (None = keep what is in the field) and submits
        once via click / enter / dblclick. Returns the API outcome(s) and the
        rendered message. Refuses any address outside FE-SUBS's namespace."""
        value = self.input_value() if typed_value is None else typed_value
        if not is_own_address(value.strip()):
            raise ValueError(f"refusing to subscribe {value!r}: not an FE-SUBS test address")
        if typed_value is not None and via == "enter":
            # keyboard-only path: the field already holds focus (Tab); type key by key
            self.page.keyboard.type(typed_value)
        elif typed_value is not None:
            self.type_email(typed_value)
        before = len(self._requests)
        responses: list[dict] = []

        def _on_response(resp):
            if self.SUBSCRIBE_URL_PART in resp.url:
                try:
                    body = resp.text()[:400]
                except Exception:  # noqa: BLE001 — body unavailable is reported as empty
                    body = ""
                status = ""
                try:
                    status = (_json.loads(body) or {}).get("status", "")
                except Exception:  # noqa: BLE001
                    pass
                responses.append({"http": resp.status, "body": body, "api_status": status})

        self.page.on("response", _on_response)
        try:
            with self.page.expect_response(lambda r: self.SUBSCRIBE_URL_PART in r.url, timeout=90000):
                self._act(via)
            msg = self._wait_message(timeout=30.0)
            try:  # a second (double) post would answer shortly after the first
                wait_until(lambda: len(responses) >= len(self._requests) - before, timeout=8.0, poll=0.3)
            except WaitTimeoutError:
                pass
        finally:
            self.page.remove_listener("response", _on_response)
        return {**msg, "responses": responses, "requests": self._requests[before:], "at": utc_now(),
                "api_status": responses[0]["api_status"] if responses else None}

    @staticmethod
    def is_throttled(result: dict) -> bool:
        return (any(r["http"] == 429 or r["api_status"] == "throttled" for r in result.get("responses", []))
                or THROTTLE_TEXT in result.get("text", "") or THROTTLE_TEXT_AR in result.get("text", ""))

    def subscribe_with_backoff(self, typed_value: str, via: str = "click", budget_s: float = 5400.0,
                               poll_s: float = 300.0, before_each=None) -> dict:
        """Submits; while the endpoint answers 'throttled' (anti-abuse limit, not a
        product failure) re-opens the hub in the same locale and retries every
        `poll_s` within `budget_s`. `before_each(band)` re-runs pre-submit UI
        steps (e.g. Tab to the field) on every attempt."""
        attempts: list[dict] = []

        def _try() -> bool:
            if attempts:
                self.open_hub(self.locale)
            if before_each:
                before_each(self)
            result = self.submit(typed_value, via=via)
            attempts.append(result)
            logger.info("subscribe %s via %s -> %s / %s", typed_value, via, result["api_status"], result["text"])
            return not self.is_throttled(result)

        try:
            wait_until(_try, timeout=budget_s, poll=poll_s)
        except WaitTimeoutError:
            pass
        last = dict(attempts[-1]) if attempts else {}
        last["attempts"] = len(attempts)
        last["throttled"] = self.is_throttled(last) if attempts else False
        return last


# =============================================================================
# Public unsubscribe page (the link every Media Center email carries)
# =============================================================================
class McUnsubscribeLinkPage(_Evidence):
    ROOT = "section.qc-unsub"
    TITLE = "[data-qc-unsub-title]"
    EMAIL = "[data-qc-unsub-email]"
    CONFIRM = "button[data-qc-unsub-confirm]"
    STATES = ("confirm", "success", "invalid", "already", "error")
    STATE = '[data-qc-unsub-state="{name}"]'

    def open_link(self, token: str, locale: str = "en") -> int | None:
        url = web_url(f"{UNSUBSCRIBE_PATH}?token={_quote(token, safe='')}", locale=locale)
        response = self.page.goto(url, wait_until="domcontentloaded", timeout=90000)
        dismiss_overlays(self.page, grace_ms=1000)
        self.page.locator(self.ROOT).first.wait_for(state="attached", timeout=45000)
        try:
            wait_until(lambda: self.state()["name"] != "", timeout=45.0, poll=0.3)
        except WaitTimeoutError:
            pass
        return response.status if response else None

    def state(self) -> dict:
        return self.page.evaluate(
            """(names) => { const root = document.querySelector('section.qc-unsub');
                if (!root) return {name: '', text: ''};
                for (const n of names) { const el = root.querySelector('[data-qc-unsub-state="' + n + '"]');
                    if (el && !el.hidden && el.getClientRects().length) {
                        const t = el.querySelector('.qc-unsub-text');
                        return {name: n, text: (t ? t.innerText : el.innerText).replace(/\\s+/g, ' ').trim(),
                                direction: getComputedStyle(el).direction}; } }
                return {name: '', text: ''}; }""", list(self.STATES))

    def page_facts(self) -> dict:
        body = self.page.locator("body").inner_text()
        return {"url": self.page.url, "html_dir": self.page.evaluate("() => document.documentElement.dir"),
                "lang": self.page.evaluate("() => document.documentElement.lang"),
                "title": " ".join(self.page.locator(self.TITLE).first.inner_text().split())
                if self.page.locator(self.TITLE).count() else "",
                "email_shown": self.page.locator(self.EMAIL).first.inner_text().strip()
                if self.page.locator(self.EMAIL).count() else "",
                "trace_like": bool(_re.search(r"Exception|Traceback|Internal Server Error|stack trace", body, _re.I)),
                "login_form": self.page.locator("input[type=password]").count() > 0,
                "signed_in": self.is_signed_in()}

    def confirm(self) -> dict:
        """Clicks Confirm Unsubscribe — only when the page shows one of FE-SUBS's own addresses."""
        email = self.page.locator(self.EMAIL).first.inner_text().strip()
        if not is_own_address(email):
            raise ValueError(f"refusing to unsubscribe {email!r}: not an FE-SUBS test address")
        self.page.locator(self.CONFIRM).click()
        try:
            wait_until(lambda: self.state()["name"] in ("success", "already", "invalid", "error"),
                       timeout=45.0, poll=0.3)
        except WaitTimeoutError:
            pass
        return self.state()


# =============================================================================
# Subscriber records (read-only; TEST_USER = Administrator per rules 2026-10-07)
# =============================================================================
class McSubscriberRecords(McSubscriberAdminPage):
    """Reads the subscriber list as the Administrator (TEST_USER). The QC Site
    Content Editor account the cases name is locked out on qcdev since
    2026-10-18; the list content is identical for both roles (read-only)."""

    READER_ROLE = "Site Content Editor"

    def sign_in(self) -> str:
        """Read-only reader session. Since 2026-10-20 the QC Site Content Editor
        (the role the cases name; PBI 9: view + export) — TEST_USER is locked out."""
        return self.login_as_role(self.READER_ROLE)

    _API_JS = """async ([gid, filter]) => {
        const u = '/o/c/newslettersubscribers/scopes/' + gid + '?pageSize=50&filter=' + encodeURIComponent(filter);
        const r = await fetch(u, {headers: {'Accept': 'application/json', 'x-csrf-token': Liferay.authToken}});
        return [r.status, await r.text()]; }"""

    def api_records(self, needle: str) -> list[dict]:
        """Every record whose email CONTAINS `needle` (case-insensitive compare
        done here; the filter is lower-case contains)."""
        self.page.wait_for_function("() => window.Liferay && Liferay.authToken && Liferay.ThemeDisplay",
                                    timeout=30000)
        gid = self.page.evaluate("() => Liferay.ThemeDisplay.getScopeGroupId()")
        status, text = self.page.evaluate(self._API_JS, [str(gid), f"contains(email,'{needle.lower()}')"])
        if int(status) != 200:
            raise AssertionError(f"subscriber API answered {status}: {text[:200]}")
        items = _json.loads(text).get("items", [])
        return [{"id": i.get("id"), "email": i.get("email"), "active": i.get("active"),
                 "lastSubscribedOn": i.get("lastSubscribedOn"), "lastUnsubscribedOn": i.get("lastUnsubscribedOn"),
                 "preferredLanguage": i.get("preferredLanguage"), "unsubscribeToken": i.get("unsubscribeToken"),
                 "status": (i.get("status") or {}).get("label")}
                for i in items if needle.lower() in (i.get("email") or "").lower()]

    def record(self, email: str) -> list[dict]:
        return [r for r in self.api_records(email) if (r["email"] or "").lower() == email.lower()]

    def list_rows(self, term: str) -> list[dict]:
        """UI list (page size All), searched by `term`; rows whose Email contains it."""
        try:
            self.open_list()
        except Exception:  # noqa: BLE001 — a long run can drop the session; sign in once more
            self.sign_in()
            self.open_list()
        self.search(term)
        return [r for r in self.visible_rows() if term.lower() in r["email"].lower()]

    def evidence_rows(self, name: str) -> str:
        path = _evidence_path(name)
        try:
            self.page.locator("table[data-qc-oel-table]").first.screenshot(path=path)
        except Exception as exc:  # noqa: BLE001 — evidence only
            logger.warning("evidence %s failed: %r", name, exc)
        return path

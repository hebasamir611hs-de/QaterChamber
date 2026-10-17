"""
web/pages/announcement_popup/announcement_popup_page.py — AnnouncementPopupPage.

Public-website Page Object for PBI 131032 ("Global Announcement Popup").

Source of truth, CONFIRMED LIVE 2026-09-24:
  - feed: GET /o/qc-newsletter/announcement-popups -> {"items": [...], "status": "ok"}
    (currently {"items": [], "status": "ok"} — nothing published on qcdev).
    Item fields: id, titleEn/titleAr, descriptionEn/descriptionAr (rich HTML),
    ctaLabelEn/ctaLabelAr, ctaUrl, displayScope (allPages|specificPages),
    targetPages, displayFrequency.
  - renderer /o/qc-announcement-popup/qc-announcement-popup.js builds:
      #qc-announcement-popup-root.qc-ann-overlay[dir]
        div.qc-ann-card[role=dialog][aria-modal=true][aria-labelledby=qc-ann-title]
          div.qc-ann-accent, button.qc-ann-close[aria-label], h2#qc-ann-title.qc-ann-title,
          div.qc-ann-desc (innerHTML), div.qc-ann-actions > a.qc-ann-cta (only when
          BOTH label and URL are set), label.qc-ann-dns > input.qc-ann-dns-cb
    Close/Escape/backdrop click remove the whole overlay from the DOM.

IMPORTANT: BasePage.open() auto-dismisses this popup (core/web/overlays.py),
so `open_in_scope()` navigates with a plain page.goto() — BasePage is not
changed. The API is never mocked.
"""

from config.settings import web_url
from core.web.base_page import BasePage

ANNOUNCEMENT_API = "/o/qc-newsletter/announcement-popups"
HOME_PATH = "/web/qatar-chamber"


class AnnouncementPopupPage(BasePage):
    ROOT = "#qc-announcement-popup-root"
    CARD = "#qc-announcement-popup-root div.qc-ann-card[role='dialog']"
    CLOSE = "#qc-announcement-popup-root button.qc-ann-close"
    TITLE = "#qc-announcement-popup-root .qc-ann-title"
    DESC = "#qc-announcement-popup-root .qc-ann-desc"
    ACTIONS = "#qc-announcement-popup-root .qc-ann-actions"
    CTA = "#qc-announcement-popup-root a.qc-ann-cta"
    DESC_BOLD = "#qc-announcement-popup-root .qc-ann-desc :is(strong, b)"
    DESC_LINK = "#qc-announcement-popup-root .qc-ann-desc a[href]"
    PAGE_LINK = "main a[href], #main-content a[href]"

    # ---- Feed -------------------------------------------------------------------
    def published_items(self) -> list:
        resp = self.page.request.get(web_url(ANNOUNCEMENT_API))
        try:
            return resp.json().get("items", []) if resp.ok else []
        except Exception:  # noqa: BLE001 — non-JSON reply = nothing published
            return []

    @staticmethod
    def scope_path(item: dict) -> str:
        """A page inside the item's display scope."""
        if item.get("displayScope") == "specificPages":
            tokens = [t.strip() for t in (item.get("targetPages") or "").replace(",", "\n").split("\n") if t.strip()]
            if tokens:
                return tokens[0] if tokens[0].startswith("/") else "/" + tokens[0]
        return HOME_PATH

    # ---- Navigation (no auto-dismiss) ---------------------------------------------
    def open_in_scope(self, item: dict, locale: str = "en") -> "AnnouncementPopupPage":
        self.page.goto(web_url(self.scope_path(item), locale=locale))
        self.page.locator(self.CARD).wait_for(state="visible", timeout=15000)
        return self

    def close_popup(self) -> None:
        self.page.locator(self.CLOSE).click()
        self.page.locator(self.ROOT).wait_for(state="detached", timeout=10000)

    def press(self, key: str) -> None:
        self.page.keyboard.press(key)

    def tab_to_close(self, max_presses: int = 30) -> bool:
        for _ in range(max_presses):
            self.page.keyboard.press("Tab")
            if self.page.evaluate("() => !!document.activeElement && document.activeElement.classList.contains('qc-ann-close')"):
                return True
        return False

    def wait_detached(self, timeout: int = 10000) -> bool:
        try:
            self.page.locator(self.ROOT).wait_for(state="detached", timeout=timeout)
            return True
        except Exception:  # noqa: BLE001
            return False

    # ---- State ------------------------------------------------------------------
    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def text_of(self, locator: str) -> str:
        loc = self.page.locator(locator)
        return loc.first.inner_text().strip() if loc.count() else ""

    def html_of(self, locator: str) -> str:
        loc = self.page.locator(locator)
        return loc.first.inner_html() if loc.count() else ""

    def box(self, locator: str):
        loc = self.page.locator(locator)
        return loc.first.bounding_box() if loc.count() else None

    def style(self, locator: str, props) -> dict:
        return self.page.locator(locator).first.evaluate(
            "(e, props) => { const c = getComputedStyle(e); const o = {}; props.forEach(p => o[p] = c.getPropertyValue(p)); return o; }",
            list(props),
        )

    def attribute(self, locator: str, name: str):
        return self.page.locator(locator).first.get_attribute(name)

    def hover(self, locator: str) -> None:
        self.page.locator(locator).first.hover()

    def focus_visible(self, locator: str) -> bool:
        return self.page.locator(locator).first.evaluate("e => e === document.activeElement && e.matches(':focus-visible')")

    def current_url(self) -> str:
        return self.page.url

    def viewport(self) -> dict:
        return self.page.evaluate("() => ({w: innerWidth, h: innerHeight})")

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")

    def clipped_in_popup(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('#qc-announcement-popup-root *')]
                .filter(e => e.offsetParent !== null && e.children.length === 0 && e.scrollWidth > e.clientWidth + 1
                        && getComputedStyle(e).overflowX !== 'visible').map(e => String(e.className) || e.tagName)"""
        )

    def scroll_by(self, dy: int) -> int:
        before = self.page.evaluate("() => scrollY")
        self.page.mouse.wheel(0, dy)
        self.page.wait_for_function("(b) => scrollY !== b", arg=before, timeout=5000)
        return self.page.evaluate("() => scrollY") - before

    def page_is_scroll_locked(self) -> bool:
        return self.page.evaluate("() => document.documentElement.classList.contains('qc-a11y-scroll-locked')")

    def click_first_page_link(self) -> str:
        before = self.page.url
        self.page.locator(self.PAGE_LINK).first.click()
        self.page.wait_for_url(lambda u: u != before, timeout=20000)
        return self.page.url

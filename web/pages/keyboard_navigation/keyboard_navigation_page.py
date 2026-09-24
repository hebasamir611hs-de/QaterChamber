"""
web/pages/keyboard_navigation/keyboard_navigation_page.py — KeyboardNavigationPage.

Site-wide keyboard-navigation Page Object for PBI 131054 ("QC - 001 -
Keyboard Navigation"). Keyboard navigation is a cross-page concern, so this
object drives REAL key presses (`page.keyboard.press`) on whichever public
page a case names and reads the focused element's state — it never calls
`element.focus()` for a "tabbed to" case.

Locators — CONFIRMED LIVE 2026-09-24 by a disclosed scripted Playwright probe
(real Tab walks, Chromium/Chrome/Edge/Firefox, 1920/1440/768/375):
  - skip link `a.qc-skip-link` ("Skip to main content"): parked above the
    viewport (translateY(-65px)), slides in with a 0.15s transform on focus;
    a second, sr-only Liferay "Skip to Main Content" link follows it.
  - header nav `header.qc-global-site-header nav.qc-nav` > `a.qc-nav-link`;
    mega-menu toggles carry aria-haspopup="true" + aria-controls="qc-submenu-N";
    ArrowDown opens the submenu and moves focus into it.
  - at <= 1440px the nav collapses behind `button.qc-hamburger` ("Menu");
    Enter opens it (aria-expanded="true") and moves focus to the first link.
  - Contact Us `/contact-us`: `#qc-cu-fullName` (label "Full Name *") and
    `button.qc-cu-submit` ("Submit Inquiry"). FAQ: `button.qc-faq-q`.
  - announcement popup (core/web/overlays.py): `#qc-announcement-popup-root`,
    close `button.qc-ann-close`; feed `/o/qc-newsletter/announcement-popups`.
"""

from config.settings import web_url
from core.web.base_page import BasePage

HOME_PATH = "/web/qatar-chamber"
CONTACT_PATH = "/contact-us"
FAQ_PATH = "/web/qatar-chamber/faq"
VMO_PATH = "/about-us/vision-mission-objectives"
ANNOUNCEMENT_API = "/o/qc-newsletter/announcement-popups"

_FOCUS_JS = """
() => {
    const e = document.activeElement;
    if (!e || e === document.body || e === document.documentElement) return null;
    const r = e.getBoundingClientRect(), c = getComputedStyle(e);
    return {
        tag: e.tagName.toLowerCase(), cls: String(e.className), id: e.id || "",
        text: (e.innerText || e.value || e.getAttribute("aria-label") || "").trim().replace(/\\s+/g, " ").slice(0, 60),
        role: e.getAttribute("role"), expanded: e.getAttribute("aria-expanded"),
        focusVisible: e.matches(":focus-visible"),
        outlineStyle: c.outlineStyle, outlineWidth: c.outlineWidth, outlineColor: c.outlineColor,
        boxShadow: c.boxShadow, borderColor: c.borderTopColor, backgroundColor: c.backgroundColor,
        x: r.x, y: r.y, width: r.width, height: r.height, docY: r.y + scrollY,
        offViewport: r.width > 0 && (r.right <= 0 || r.left >= innerWidth),
        inHeader: !!e.closest("header.qc-global-site-header"),
        section: (() => { const s = e.closest(".lfr-layout-structure-item-qc-home-hero-banner, [class*='lfr-layout-structure-item-']");
                          return s ? (String(s.className).match(/lfr-layout-structure-item-(qc-[a-z0-9-]+)/) || [,""])[1] : ""; })(),
        key: e.tagName + "|" + String(e.className) + "|" + (e.innerText || e.getAttribute("aria-label") || "").trim().slice(0, 30)
             + "|" + Math.round(r.x + scrollX) + "|" + Math.round(r.y + scrollY),
    };
}
"""

_STYLE_JS = """
(e) => { const c = getComputedStyle(e); return {
    outlineStyle: c.outlineStyle, outlineWidth: c.outlineWidth, outlineColor: c.outlineColor,
    boxShadow: c.boxShadow, borderColor: c.borderTopColor, backgroundColor: c.backgroundColor}; }
"""


class KeyboardNavigationPage(BasePage):
    SKIP_LINK = "a.qc-skip-link"
    HEADER = "header.qc-global-site-header"
    NAV = "header.qc-global-site-header nav.qc-nav"
    NAV_LINK = "header.qc-global-site-header a.qc-nav-link"
    HAMBURGER = "header.qc-global-site-header button.qc-hamburger"
    LANG_TOGGLE = "header.qc-global-site-header a.qc-lang-switcher"
    CONTACT_NAME = "#qc-cu-fullName"
    CONTACT_SUBMIT = "button.qc-cu-submit"
    FAQ_QUESTION = "button.qc-faq-q"
    TAB_CONTROL = "[role='tab']"
    FOOTER_SUBMIT = "footer button[type='submit'], .qc-global-site-footer button[type='submit']"
    ANN_ROOT = "#qc-announcement-popup-root"
    ANN_CLOSE = "#qc-announcement-popup-root button.qc-ann-close"

    # ---- Navigation -------------------------------------------------------------
    def open_path(self, path: str = HOME_PATH, locale: str = "en") -> "KeyboardNavigationPage":
        self.open(web_url(path, locale=locale))
        self.page.wait_for_load_state("load")
        self.wait_for("body")
        # Client-rendered header/content: wait for the header's nav or hamburger.
        self.page.wait_for_function(
            "() => !!document.querySelector('header.qc-global-site-header a.qc-nav-link, header.qc-global-site-header button.qc-hamburger')",
            timeout=30000,
        )
        return self

    def open_path_keep_popup(self, path: str = HOME_PATH) -> "KeyboardNavigationPage":
        """Navigate WITHOUT BasePage.open()'s global overlay dismissal — the
        announcement popup is the subject of 141807."""
        self.page.goto(web_url(path))
        return self

    def switch_language(self) -> "KeyboardNavigationPage":
        """Header language toggle; waits for the real navigation."""
        before = self.page.url
        self.click(self.LANG_TOGGLE)
        self.wait_for_url(lambda u: u != before, timeout=30000)
        return self

    def published_announcements(self) -> list:
        resp = self.page.request.get(web_url(ANNOUNCEMENT_API))
        try:
            return resp.json().get("items", []) if resp.ok else []
        except Exception:  # noqa: BLE001 — a non-JSON reply means "nothing published"
            return []

    # ---- Keyboard ---------------------------------------------------------------
    def press(self, key: str) -> dict:
        self.page.keyboard.press(key)
        return self.focused()

    def focused(self):
        return self.page.evaluate(_FOCUS_JS)

    def tab_until(self, predicate, max_presses: int = 80, key: str = "Tab"):
        """Press `key` until predicate(focused) is true. Returns (presses, info)
        or (None, last_info) when not reached."""
        info = None
        for i in range(max_presses):
            self.page.keyboard.press(key)
            info = self.focused()
            if info and predicate(info):
                return i + 1, info
        return None, info

    def settle(self) -> None:
        """Wait for every FINITE running animation/transition to finish (the
        skip link's 0.15s slide-in, menu/panel transitions). Infinite ones —
        the partner-logo marquee runs forever — are ignored."""
        self.page.wait_for_function(
            """() => document.getAnimations().every((a) => a.playState !== 'running'
                       || a.effect.getComputedTiming().iterations === Infinity)""",
            timeout=5000,
        )

    def unfocused_style(self, locator: str) -> dict:
        return self.page.locator(locator).first.evaluate(_STYLE_JS)

    def is_displayed(self, locator: str) -> bool:
        return self.page.locator(locator).first.is_visible()

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def attribute(self, locator: str, name: str):
        return self.page.locator(locator).first.get_attribute(name)

    def box(self, locator: str):
        return self.page.locator(locator).first.bounding_box()

    def element_facts(self, locator: str) -> dict:
        return self.page.locator(locator).first.evaluate(
            """e => ({tag: e.tagName.toLowerCase(), type: e.getAttribute('type'), role: e.getAttribute('role'),
                     name: (e.getAttribute('aria-label') || e.innerText || e.value || '').trim(),
                     ariaLabel: e.getAttribute('aria-label'), labelledby: e.getAttribute('aria-labelledby'),
                     expanded: e.getAttribute('aria-expanded'), haspopup: e.getAttribute('aria-haspopup'),
                     controls: e.getAttribute('aria-controls')})"""
        )

    def controlled_panel_visible(self, toggle_locator: str) -> bool:
        return self.page.locator(toggle_locator).first.evaluate(
            """t => { const id = t.getAttribute('aria-controls'); const p = id && document.getElementById(id);
                      if (!p) return false; const r = p.getBoundingClientRect(), c = getComputedStyle(p);
                      return r.height > 0 && c.visibility !== 'hidden' && c.display !== 'none'; }"""
        )

    def current_url(self) -> str:
        return self.page.url

    def viewport_width(self) -> int:
        return self.page.evaluate("() => innerWidth")

    def document_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir")

    def focus_walk(self, max_stops: int = 240) -> list:
        """Real Tab walk from the current focus through the page; returns the
        focus info for every stop (stops when focus leaves the document or
        the walk cycles back to its first stop)."""
        stops, first = [], None
        for _ in range(max_stops):
            self.page.keyboard.press("Tab")
            self.page.wait_for_timeout(120)  # carousels/scroll-snap reposition the focused slide
            info = self.focused()
            if info is None:
                break
            if first is None:
                first = info["key"]
            elif info["key"] == first:
                break
            stops.append(info)
        return stops

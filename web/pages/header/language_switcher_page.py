"""
web/pages/header/language_switcher_page.py — LanguageSwitcherPage.

Public-facing header Language Switcher (PBI 133380 "QC-GBL-002 — Language
Switcher"). Locators extracted CLI-first via tools/extract_locators.py
against the live homepage at the framework's default viewport (1920x1080):

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --scope header

The CLI hit the site's Liferay "developer mode connection limit" redirect
(the same one already disclosed in web/pages/footer/footer_page.py) before
it could harvest the header — confirmed reproducible across 3 consecutive
runs in this session. Per automation-standards.md's fallback rule ("the
target state can't be reached deterministically by script"), the header was
then inspected via the disclosed Playwright-MCP fallback: the reset link
was followed once, then `header.qc-global-site-header`'s real DOM was read
via `browser_evaluate` (scoped `outerHTML`, never a full-page dump) and the
switcher's live behaviour (label flip, `dir`/`lang` flip, URL prefix) was
observed by actually clicking it once:

    header.qc-global-site-header[data-show-language-switcher="true"]  - header root
    a.qc-lang-switcher[data-qc-lang]                                   - the switcher itself
        text "AR" (English render) / "EN" (Arabic render)
        href -> /c/portal/update_language?p_l_id=39&redirect=%2Fhome&languageId=<ar_SA|en_US>
    a.qc-logo[data-qc-logo]                                            - header logo
    a.qc-nav-link (nav.qc-nav ul.qc-nav-list)                          - main nav links
    a.qc-search-btn[data-qc-search]                                    - search icon (right of switcher)
    button.qc-accessibility-btn[aria-label="Accessibility tools"]      - accessibility icon (right of switcher)

Confirmed live: clicking `.qc-lang-switcher` on the English homepage
navigated to `https://qcdev.ihorizons.com/ar/home`, flipped
`document.documentElement.dir` to "rtl" and `.lang` to "ar-SA", and the
switcher's own text flipped to "EN" with its `href` now pointing at
`languageId=en_US` — i.e. language state is carried in the URL path
(`/ar/...` vs no prefix) + `html[dir]`/`html[lang]`, not a JS-readable
cookie (Liferay's `GUEST_LANGUAGE_ID` cookie is HttpOnly), so state queries
below assert on URL/`dir`/`lang`, never on `document.cookie`. Re-loading
`/home` in the same browser context returned `/ar/home` again — the
session-scoped language preference persisted (used by the
new-visitor/returning-visitor cases below).

No TODO(locator) remains for anything on the public switcher — every
element the 29 approved cases reference on the live header was reachable
and resolved to a real, unique selector.
"""

from config.settings import web_url
from core.web.base_page import BasePage

HOME_URL = web_url("/home")
HOME_URL_AR = web_url("/home", locale="ar")


class LanguageSwitcherPage(BasePage):
    # ---- Structure -----------------------------------------------------
    HEADER = "header.qc-global-site-header"
    LOGO_LINK = "header a.qc-logo"
    NAV_LIST = "header ul.qc-nav-list"
    SEARCH_BUTTON = "header a.qc-search-btn"
    ACCESSIBILITY_BUTTON = "header button.qc-accessibility-btn"

    # ---- Language switcher ----------------------------------------------
    SWITCHER = "header a.qc-lang-switcher"

    @staticmethod
    def nav_link_locator(link_text: str) -> str:
        return f'header a.qc-nav-link:has-text("{link_text}")'

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_home(self, url: str = HOME_URL) -> "LanguageSwitcherPage":
        self.open(url)
        self.wait_for(self.HEADER)
        return self

    def open_home_arabic(self) -> "LanguageSwitcherPage":
        return self.open_home(HOME_URL_AR)

    def reload(self) -> "LanguageSwitcherPage":
        self.page.reload()
        self.wait_for(self.HEADER)
        return self

    def current_url(self) -> str:
        return self.page.url

    def navigate_via_nav_link(self, link_text: str) -> "LanguageSwitcherPage":
        self.click(self.nav_link_locator(link_text))
        self.wait_for(self.HEADER)
        return self

    def go_back(self) -> "LanguageSwitcherPage":
        self.page.go_back()
        self.wait_for(self.HEADER)
        return self

    def go_forward(self) -> "LanguageSwitcherPage":
        self.page.go_forward()
        self.wait_for(self.HEADER)
        return self

    # ------------------------------------------------------------------
    # Switcher state / actions
    # ------------------------------------------------------------------
    def is_switcher_visible(self) -> bool:
        return self.is_visible(self.SWITCHER)

    def switcher_label(self) -> str:
        return self.text(self.SWITCHER)

    def switcher_href(self) -> str:
        return self.page.locator(self.SWITCHER).get_attribute("href")

    def click_switcher(self) -> "LanguageSwitcherPage":
        self.click(self.SWITCHER)
        self.wait_for(self.HEADER)
        return self

    def double_click_switcher(self) -> "LanguageSwitcherPage":
        self.page.locator(self.SWITCHER).dblclick(force=True, timeout=5000)
        self.wait_for(self.HEADER)
        return self

    def hover_switcher(self) -> None:
        self.page.locator(self.SWITCHER).hover()

    def focus_switcher_via_tab(self) -> bool:
        return self.press_tab_until_focused(self.SWITCHER)

    def is_switcher_focused(self) -> bool:
        return self.is_focused(self.SWITCHER)

    def switcher_style(self) -> dict:
        return self.page.locator(self.SWITCHER).evaluate(
            "el => { const r = el.getBoundingClientRect(); const cs = getComputedStyle(el); "
            "return {width: r.width, height: r.height, padding: cs.padding, "
            "borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor, "
            "color: cs.color, fontSize: cs.fontSize, fontWeight: cs.fontWeight}; }"
        )

    def switcher_outline_on_focus(self) -> str:
        """Reads outline/box-shadow while the switcher currently holds
        keyboard focus — call right after focus_switcher_via_tab()."""
        return self.page.locator(self.SWITCHER).evaluate(
            "el => { const cs = getComputedStyle(el); return cs.outlineStyle + ' ' + cs.outlineWidth + ' ' + cs.boxShadow; }"
        )

    def switcher_bounding_x(self) -> float:
        return self.page.locator(self.SWITCHER).evaluate("el => el.getBoundingClientRect().x")

    def switcher_computed_display_state(self, pressed: bool = False) -> str:
        """Best-effort pressed/active-state read: `:active` cannot be forced
        via CSS pseudo-class from evaluate(), so this returns the switcher's
        current backgroundColor while a mouse button is held via
        press_and_hold_switcher()."""
        return self.page.locator(self.SWITCHER).evaluate("el => getComputedStyle(el).backgroundColor")

    def press_and_hold_switcher(self) -> None:
        box = self.page.locator(self.SWITCHER).bounding_box()
        self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        self.page.mouse.down()

    def release_mouse(self) -> None:
        self.page.mouse.up()

    # ------------------------------------------------------------------
    # Layout / language state
    # ------------------------------------------------------------------
    def html_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir")

    def html_lang(self) -> str:
        return self.page.evaluate("() => document.documentElement.lang")

    def is_rtl(self) -> bool:
        return self.html_dir() == "rtl"

    def logo_bounding_x(self) -> float:
        return self.page.locator(self.LOGO_LINK).evaluate("el => el.getBoundingClientRect().x")

    def nav_link_texts(self) -> list:
        return self.page.locator("header a.qc-nav-link").all_inner_texts()

    def is_nav_link_visible(self, link_text: str) -> bool:
        return self.is_visible(self.nav_link_locator(link_text))

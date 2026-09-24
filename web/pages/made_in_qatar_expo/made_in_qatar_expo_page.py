"""
web/pages/made_in_qatar_expo/made_in_qatar_expo_page.py — MadeInQatarExpoPage.

Public-website Page Object for PBI 130708 ("QC - Events - 005 - Made in Qatar
Expo"). Real URL: `/web/qatar-chamber/made-in-qatar-expo` (Arabic: the same
path behind the `/ar` prefix, built with `web_url(path, locale="ar")`).

Locators: `tools/extract_locators.py --url <page> --scope main` returned 0
candidates (the component's content is non-interactive rich text + 2 CTA
links outside `main`'s role/testid/id tiers). Everything below came from a
disclosed, scripted Playwright DOM probe (plain shell script, not the MCP),
CONFIRMED LIVE 2026-09-24 against qcdev at 1920x1080. The component's own
custom-attribute family is `data-qc-miq-*` — highest-tier locator available:

    section.qc-miq[dir][data-qc-miq-ready="true"]   (client-rendered; the
        `ready` flag flips once content is hydrated — waited on in open())
    header[data-qc-miq-hero]
      nav[data-qc-miq-crumbs][aria-label=Breadcrumb] > a.qc-miq-crumb (Home,
        Events) + span.qc-miq-crumb.is-current[aria-current=page]
      p[data-qc-miq-eyebrow] / h1[data-qc-miq-title] / div[data-qc-miq-desc]
      div[data-qc-miq-hero-cta] > a.qc-miq-cta.qc-miq-cta-pill > span.qc-miq-cta-label
      div[data-qc-miq-hero-art] > img[data-qc-miq-hero-img]
    div[data-qc-miq-band]
      div[data-qc-miq-about] > p[data-qc-miq-about-eyebrow], h2[data-qc-miq-about-title],
        div[data-qc-miq-about-body] (3 <p>)
      aside[data-qc-miq-card] > img[data-qc-miq-card-logo], p[data-qc-miq-card-eyebrow],
        h3[data-qc-miq-card-heading], div[data-qc-miq-card-desc],
        div[data-qc-miq-card-cta] > a.qc-miq-cta.qc-miq-cta-solid

Live observations recorded at probe time (asserted by the tests, not here):
  - Breadcrumb "Events" href is `/web/qatar-chamber/chamber-events`, which
    returns HTTP 404 "Coming Soon"; the real Events landing page is
    `/web/qatar-chamber/events` (ChamberEventsPage.LISTING_PATH).
  - Copy uses the typographic apostrophe U+2019 ("Qatar’s").
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.chamber_events.chamber_events_page import ChamberEventsPage


class MadeInQatarExpoPage(BasePage):
    PATH = "/web/qatar-chamber/made-in-qatar-expo"
    HOME_PATH = "/web/qatar-chamber"

    # ---- Root -----------------------------------------------------------------
    ROOT = "section.qc-miq"
    ROOT_READY = "section.qc-miq[data-qc-miq-ready='true']"

    # ---- Hero -----------------------------------------------------------------
    HERO = "[data-qc-miq-hero]"
    HERO_COPY = "[data-qc-miq-hero] .qc-miq-hero-copy"
    HERO_ART = "[data-qc-miq-hero-art]"
    HERO_EYEBROW = "[data-qc-miq-eyebrow]"
    HERO_TITLE = "[data-qc-miq-title]"
    HERO_DESC = "[data-qc-miq-desc]"
    HERO_CTA = "[data-qc-miq-hero-cta] a.qc-miq-cta"
    HERO_CTA_LABEL = "[data-qc-miq-hero-cta] .qc-miq-cta-label"

    # ---- Breadcrumb -----------------------------------------------------------
    BREADCRUMB = "[data-qc-miq-crumbs]"
    CRUMB_LINK = "[data-qc-miq-crumbs] a.qc-miq-crumb"

    # ---- About ----------------------------------------------------------------
    ABOUT = "[data-qc-miq-about]"
    ABOUT_EYEBROW = "[data-qc-miq-about-eyebrow]"
    ABOUT_TITLE = "[data-qc-miq-about-title]"
    ABOUT_BODY = "[data-qc-miq-about-body]"
    ABOUT_BODY_PARAGRAPH = "[data-qc-miq-about-body] p"

    # ---- Side CTA card --------------------------------------------------------
    CARD = "[data-qc-miq-card]"
    CARD_COPY = "[data-qc-miq-card] .qc-miq-card-copy"
    CARD_LOGO = "[data-qc-miq-card-logo]"
    CARD_EYEBROW = "[data-qc-miq-card-eyebrow]"
    CARD_HEADING = "[data-qc-miq-card-heading]"
    CARD_DESC = "[data-qc-miq-card-desc]"
    CARD_CTA = "[data-qc-miq-card-cta] a.qc-miq-cta"
    CARD_CTA_LABEL = "[data-qc-miq-card-cta] .qc-miq-cta-label"

    HOVER_PROPS = ("background-color", "color", "border-color", "box-shadow", "transform")
    FOCUS_PROPS = ("outline-style", "outline-width", "outline-color", "box-shadow")

    # ---- Navigation -----------------------------------------------------------
    def open_page(self, locale: str = "en") -> "MadeInQatarExpoPage":
        self.open(web_url(self.PATH, locale=locale))
        # Liferay renders this fragment client-side: wait for the hydration
        # flag and the real hero title, not just the load state.
        self.wait_for(self.ROOT_READY, state="attached", timeout=20000)
        self.wait_for(self.HERO_TITLE, timeout=20000)
        return self

    def click_breadcrumb_events(self) -> ChamberEventsPage:
        self.click(f"{self.CRUMB_LINK}:has-text('Events')")
        self._wait_left_page()
        return ChamberEventsPage(self.page)

    def click_breadcrumb_home(self) -> BasePage:
        self.click(f"{self.CRUMB_LINK}:has-text('Home')")
        self._wait_left_page()
        return BasePage(self.page)

    def _wait_left_page(self) -> None:
        # click() resolves on dispatch; wait until the browser has actually
        # navigated off this page before anyone reads the URL/title.
        self.wait_for_url(lambda url: self.PATH not in url)
        self.page.wait_for_load_state("domcontentloaded")

    def scroll_to(self, locator: str) -> None:
        self.page.locator(locator).scroll_into_view_if_needed()

    # ---- State queries --------------------------------------------------------
    def text_of(self, locator: str) -> str:
        return self.page.locator(locator).inner_text().strip()

    def texts_of(self, locator: str) -> list[str]:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def breadcrumb_items(self) -> list[str]:
        return self.texts_of(f"{self.BREADCRUMB} .qc-miq-crumb")

    def crumb_href(self, label: str) -> str | None:
        return self.get_attribute(f"{self.CRUMB_LINK}:has-text('{label}')", "href")

    def document_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir || getComputedStyle(document.documentElement).direction")

    def root_dir(self) -> str:
        return self.get_attribute(self.ROOT, "dir") or ""

    def explicit_ltr_descendants(self) -> int:
        return self.page.locator(f"{self.ROOT} [dir='ltr']").count()

    def image_loaded(self, locator: str) -> bool:
        return self.page.locator(locator).evaluate("el => el.complete && el.naturalWidth > 0")

    def image_alt(self, locator: str) -> str:
        return self.get_attribute(locator, "alt") or ""

    def computed_style(self, locator: str, props) -> dict:
        return self.page.locator(locator).evaluate(
            "(el, props) => { const c = getComputedStyle(el); const o = {}; props.forEach(p => o[p] = c.getPropertyValue(p)); return o; }",
            list(props),
        )

    def text_alignment(self, locator: str) -> dict:
        """Direction/alignment facts for one text element: computed
        `direction`/`text-align`, plus where the FIRST rendered line box of
        its text actually sits inside the element's content box (gap to the
        left edge / right edge in px) — so left/right alignment is measured
        from real rendered geometry, not inferred from CSS keywords alone.
        Also reports clipping (scroll size larger than client size)."""
        return self.page.locator(locator).evaluate(
            """el => {
                const c = getComputedStyle(el);
                const r = el.getBoundingClientRect();
                const pl = parseFloat(c.paddingLeft) || 0, pr = parseFloat(c.paddingRight) || 0;
                const range = document.createRange();
                range.selectNodeContents(el);
                const rects = [...range.getClientRects()].filter(x => x.width > 0);
                const first = rects[0] || r;
                return {
                    text: el.innerText.trim(),
                    direction: c.direction,
                    textAlign: c.textAlign,
                    leftGap: Math.round(first.left - (r.left + pl)),
                    rightGap: Math.round((r.right - pr) - first.right),
                    clipped: el.scrollWidth > el.clientWidth + 1
                        || (c.overflowY !== 'visible' && el.scrollHeight > el.clientHeight + 1),
                    ellipsis: c.textOverflow === 'ellipsis' && el.scrollWidth > el.clientWidth,
                };
            }"""
        )

    def box(self, locator: str) -> dict:
        """Document-relative bounding box (left/top/right/bottom/width/height)."""
        return self.page.locator(locator).evaluate(
            """el => { const b = el.getBoundingClientRect();
                return {left: b.left + scrollX, top: b.top + scrollY, right: b.right + scrollX,
                        bottom: b.bottom + scrollY, width: b.width, height: b.height}; }"""
        )

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )

    def clipped_text_elements(self) -> list[str]:
        """Text-bearing elements inside the component whose content overflows
        their own box (horizontal clipping/truncation)."""
        return self.page.evaluate(
            """root => [...document.querySelectorAll(root + ' p, ' + root + ' h1, ' + root + ' h2, '
                        + root + ' h3, ' + root + ' .qc-miq-cta-label, ' + root + ' .qc-miq-crumb')]
                .filter(e => e.offsetParent !== null && e.scrollWidth > e.clientWidth + 1)
                .map(e => e.className || e.tagName)""",
            self.ROOT,
        )

    # ---- Interaction state ----------------------------------------------------
    def hover_styles(self, locator: str) -> tuple[dict, dict]:
        """Computed hover-relevant styles before and after a real mouse hover."""
        self.scroll_to(locator)
        self.page.mouse.move(0, 0)
        before = self.computed_style(locator, self.HOVER_PROPS)
        self.page.locator(locator).hover()
        # Wait for the CSS transition to settle on the hovered element.
        self.page.wait_for_function(
            "sel => { const el = document.querySelector(sel); return el && el.matches(':hover') "
            "&& el.getAnimations().every(a => a.playState !== 'running'); }",
            arg=locator,
            timeout=5000,
        )
        after = self.computed_style(locator, self.HOVER_PROPS)
        return before, after

    def keyboard_focus_styles(self, locator: str) -> tuple[dict, dict, bool]:
        """Styles before focus, styles after reaching the element with a real
        Tab keystroke, and whether it matches :focus-visible.

        Focus is parked on the focusable element immediately preceding the
        target in tab order, then Tab is pressed — a genuine keyboard focus
        move (so :focus-visible applies) without walking the whole header."""
        self.scroll_to(locator)
        before = self.computed_style(locator, self.FOCUS_PROPS)
        self.page.locator(locator).evaluate(
            """el => {
                const all = [...document.querySelectorAll('a[href], button, input, select, textarea, [tabindex]')]
                    .filter(x => x.tabIndex >= 0 && !x.disabled && x.offsetParent !== null);
                const i = all.indexOf(el);
                if (i > 0) all[i - 1].focus(); else document.body.focus();
            }"""
        )
        self.press_key("Tab")
        self.page.wait_for_function(
            "sel => { const el = document.querySelector(sel); return el === document.activeElement "
            "&& el.getAnimations().every(a => a.playState !== 'running'); }",
            arg=locator,
            timeout=5000,
        )
        after = self.computed_style(locator, self.FOCUS_PROPS)
        focus_visible = self.page.locator(locator).evaluate("el => el.matches(':focus-visible')")
        return before, after, focus_visible

    def set_viewport(self, width: int, height: int) -> "MadeInQatarExpoPage":
        self.page.set_viewport_size({"width": width, "height": height})
        self.page.wait_for_function("w => window.innerWidth === w", arg=width, timeout=5000)
        self.wait_for(self.CARD)
        return self

    def current_path(self) -> str:
        return self.page.evaluate("() => location.pathname.replace(/\\/$/, '')")

    def title(self) -> str:
        return self.page.title()

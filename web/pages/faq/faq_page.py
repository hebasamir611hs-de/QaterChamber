"""
web/pages/faq/faq_page.py — FaqPage.

Public-website Page Object for PBI 131052 ("QC - 001 - FAQ Knowledge Base").
URL `/web/qatar-chamber/faq` (Arabic: `/ar` prefix via
`web_url(path, locale="ar")`).

Locators: the CLI extractor only surfaces header/footer chrome for this
page's non-interactive markup; the structure below came from a disclosed,
scripted Playwright DOM probe (shell script, not the MCP), CONFIRMED LIVE
2026-09-24 at 1920x1080, 768x1024 and 375x667, EN and AR:

    section.qc-faq[dir][data-qc-faq-page-size="5"]
      header.qc-faq-hero (maroon linear-gradient)
        nav.qc-faq-breadcrumb > a.qc-faq-crumb (Home) + span.qc-faq-crumb-sep ("/")
                              + span.qc-faq-crumb-current[aria-current=page] (FAQs)
        h1.qc-faq-hero-title / p.qc-faq-hero-subtitle
      div.qc-faq-inner
        div.qc-faq-search > input.qc-faq-search-input[type=search] (+ clear button)
        div.qc-faq-chips[role=tablist] > button.qc-faq-chip (All / categories)
        div.qc-faq-list > div.qc-faq-item > button.qc-faq-q[aria-expanded]
            > span.qc-faq-q-text (span.qc-faq-q-cat + span.qc-faq-q-label)
            + span.qc-faq-q-icon ; div.qc-faq-a[hidden]
        nav.qc-faq-pagination > span.qc-faq-page-info + button.qc-faq-page-btn (Prev/1/2/Next)

The approved Figma cases describe a different component set in places (a
Search BUTTON, a "Browse by topic" eyebrow, an H2, a "Select Category"
dropdown and a "Load More" button). Those are looked up SEMANTICALLY (by
role/accessible name/text inside the FAQ section) — never by an invented
class — so a test can report "not rendered" honestly, and would measure the
element automatically if a build ships it.
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent


class FaqPage(BasePage):
    PATH = "/web/qatar-chamber/faq"

    # ---- Global chrome ---------------------------------------------------------
    PAGE_BODY = "body"

    # ---- Component (live) -------------------------------------------------------
    ROOT = "section.qc-faq"
    HERO = "header.qc-faq-hero"
    HERO_TITLE = "h1.qc-faq-hero-title"
    HERO_SUBTITLE = ".qc-faq-hero-subtitle"
    CRUMB_HOME = "nav.qc-faq-breadcrumb a.qc-faq-crumb"
    CRUMB_CURRENT = ".qc-faq-crumb-current"
    CRUMB_SEP = ".qc-faq-crumb-sep"
    CRUMB_SEP_ICON = "nav.qc-faq-breadcrumb svg"
    SEARCH = ".qc-faq-search"
    SEARCH_INPUT = "input.qc-faq-search-input"
    CHIPS = "[data-qc-faq-chips]"
    CHIP = "button.qc-faq-chip"
    LIST = "[data-qc-faq-list]"
    ITEM = ".qc-faq-item"
    QUESTION = "button.qc-faq-q"
    QUESTION_LABEL = ".qc-faq-q-label"
    QUESTION_ICON = ".qc-faq-q-icon"
    PAGINATION = "nav.qc-faq-pagination"
    PAGE_INFO = ".qc-faq-page-info"
    PAGE_BUTTON = "button.qc-faq-page-btn"
    # Semantic lookups for the Figma-described controls (scoped to ROOT).
    DROPDOWN = "section.qc-faq select, section.qc-faq [role='combobox'], section.qc-faq [aria-haspopup='listbox']"
    TEXT_NODES = ("section.qc-faq h1, section.qc-faq h2, section.qc-faq p, section.qc-faq a, "
                  "section.qc-faq button, section.qc-faq span, section.qc-faq input")

    # ---- Navigation -------------------------------------------------------------
    def open_faq(self, locale: str = "en") -> "FaqPage":
        """Open the page and wait for the client-rendered accordion list."""
        self.open(web_url(self.PATH, locale=locale))
        self.wait_for(self.HERO_TITLE, timeout=30000)
        self.wait_for(self.ITEM, first=True, timeout=30000)
        return self

    def enable_dark_mode(self) -> "FaqPage":
        """Real Dark mode switch, then wait for colour transitions to settle."""
        AccessibilityToolsComponent(self.page).enable_dark_mode()
        self._wait_transitions()
        return self

    def enable_high_contrast(self) -> "FaqPage":
        AccessibilityToolsComponent(self.page).enable_high_contrast()
        self._wait_transitions()
        return self

    def high_contrast_state(self) -> dict:
        """Switch state (read with the panel open — its switches only exist
        while the panel is rendered) plus the <html> class signal."""
        tools = AccessibilityToolsComponent(self.page)
        tools.open_panel()
        checked = tools.is_high_contrast_switch_checked()
        tools.close_panel()
        return {"switch_checked": checked, "active": tools.is_high_contrast_active()}

    def _wait_transitions(self) -> None:
        self.page.wait_for_function(
            "() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=10000
        )

    def scroll_to(self, locator: str, index: int = 0) -> None:
        self.page.locator(locator).nth(index).scroll_into_view_if_needed()

    # ---- Semantic lookups (Figma-described controls) ------------------------------
    def _role(self, role: str, name: str = None, level: int = None):
        kwargs = {}
        if name is not None:
            kwargs.update(name=name, exact=True)
        if level is not None:
            kwargs["level"] = level
        return self.page.locator(self.ROOT).get_by_role(role, **kwargs)

    def _text(self, text: str):
        return self.page.locator(self.ROOT).get_by_text(text, exact=True)

    def role_count(self, role: str, name: str = None, level: int = None) -> int:
        return self._role(role, name, level).count()

    def role_texts(self, role: str, level: int = None) -> list:
        return [t.strip() for t in self._role(role, level=level).all_inner_texts()]

    def role_style(self, role: str, props, name: str = None, level: int = None) -> dict:
        return self._style_of(self._role(role, name, level).first, props)

    def role_box(self, role: str, name: str = None, level: int = None):
        return self._role(role, name, level).first.bounding_box()

    def text_count(self, text: str) -> int:
        return self._text(text).count()

    def text_style(self, text: str, props) -> dict:
        return self._style_of(self._text(text).first, props)

    # ---- Generic state queries -----------------------------------------------------
    @staticmethod
    def _style_of(locator, props) -> dict:
        return locator.evaluate(
            "(el, props) => { const c = getComputedStyle(el); const o = {};"
            " props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; }",
            list(props),
        )

    def styles(self, locator: str, props, nth: int = 0) -> dict:
        return self._style_of(self.page.locator(locator).nth(nth), props)

    def styles_all(self, locator: str, props) -> list:
        return self.page.locator(locator).evaluate_all(
            "(els, props) => els.map(el => { const c = getComputedStyle(el); const o = {};"
            " props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; })",
            list(props),
        )

    def box(self, locator: str, nth: int = 0):
        return self.page.locator(locator).nth(nth).bounding_box()

    def boxes(self, locator: str) -> list:
        loc = self.page.locator(locator)
        return [loc.nth(i).bounding_box() for i in range(loc.count())]

    def expanded_question_count(self) -> int:
        return self.page.locator(f"{self.QUESTION}[aria-expanded='true']").count()

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def texts(self, locator: str) -> list:
        return [" ".join((t or "").split()) for t in self.page.locator(locator).all_text_contents()]

    def tag_of(self, locator: str, nth: int = 0) -> str:
        return self.page.locator(locator).nth(nth).evaluate("el => el.tagName.toLowerCase()")

    def placeholder(self, locator: str) -> str:
        return self.page.locator(locator).first.get_attribute("placeholder") or ""

    def document_dir(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.dir || getComputedStyle(document.documentElement).direction"
        )

    def theme(self):
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def resolved_text_align(self, locator: str, nth: int = 0) -> str:
        """Computed text-align resolved to a physical side (start/end are logical)."""
        return self.page.locator(locator).nth(nth).evaluate(
            """el => { const s = getComputedStyle(el), rtl = s.direction === 'rtl', a = s.textAlign;
                if (a === 'start') return rtl ? 'right' : 'left';
                if (a === 'end') return rtl ? 'left' : 'right';
                return a; }"""
        )

    def clickable_box(self, locator: str, nth: int = 0):
        """Box of the nearest clickable element (button/a) containing the
        nth match — the real touch target for a decorative icon."""
        return self.page.locator(locator).nth(nth).evaluate(
            """el => { const t = el.closest('button, a, [role=button]') || el; const r = t.getBoundingClientRect();
                return {x: r.x, y: r.y, width: r.width, height: r.height, tag: t.tagName.toLowerCase()}; }"""
        )

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )

    def overflowing_elements(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll("body *")]
                .filter((e) => { const r = e.getBoundingClientRect();
                    return r.width > 0 && r.right > innerWidth + 1 && getComputedStyle(e).visibility !== "hidden"; })
                .slice(0, 5).map((e) => e.tagName.toLowerCase() + "." + String(e.className).trim()
                    + " (right=" + Math.round(e.getBoundingClientRect().right) + "px)")"""
        )

    def clipped_text_elements(self) -> list:
        return self.page.evaluate(
            """(root) => [...document.querySelectorAll(root + " *")]
                .filter((e) => e.offsetParent !== null && e.children.length === 0
                    && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== "visible")
                .map((e) => String(e.className) || e.tagName)""",
            self.ROOT,
        )

    def visible_text_contrasts(self) -> list:
        """WCAG contrast for every rendered leaf text node in the FAQ section.
        Background = first solid ancestor colour; when a gradient is reached
        first, the ratio is the MINIMUM across the gradient's colour stops
        (worst case). Text alpha is blended over the background.
        aria-hidden decorative glyphs are excluded (WCAG 1.4.3 decoration)."""
        return self.page.evaluate(
            """
            (sel) => {
                const parse = (c) => { const m = c.match(/[0-9.]+/g) || [0, 0, 0, 0];
                    return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
                const lum = (rgb) => { const f = (v) => { v /= 255;
                    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]); };
                const ratio = (fg, bg) => { const a = fg[3]; const mix = [0, 1, 2].map((i) => fg[i] * a + bg[i] * (1 - a));
                    const l1 = lum(mix), l2 = lum(bg); return (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05); };
                return [...document.querySelectorAll(sel)].filter((e) => {
                    // aria-hidden glyphs (e.g. the "/" crumb separator) are decoration,
                    // exempt from WCAG 1.4.3 — not text a reader must parse.
                    if (e.offsetParent === null || e.closest('[aria-hidden="true"]')) return false;
                    const t = [...e.childNodes].filter((n) => n.nodeType === 3).map((n) => n.textContent).join("").trim();
                    return t.length > 0 || (e.tagName === "INPUT" && e.placeholder);
                }).map((e) => {
                    const s = getComputedStyle(e);
                    let n = e, bgs = null;
                    while (n && n.nodeType === 1) {
                        const cs = getComputedStyle(n);
                        if (cs.backgroundImage && cs.backgroundImage.includes("gradient")) {
                            bgs = (cs.backgroundImage.match(/rgba?\\([^)]*\\)/g) || []).map(parse); break; }
                        const c = parse(cs.backgroundColor);
                        if (c[3] > 0) { bgs = [c]; break; }
                        n = n.parentElement;
                    }
                    if (!bgs || !bgs.length) bgs = [[255, 255, 255, 1]];
                    const fg = parse(s.color);
                    const r = Math.min(...bgs.map((b) => ratio(fg, b)));
                    const txt = [...e.childNodes].filter((x) => x.nodeType === 3).map((x) => x.textContent).join("").trim()
                        || e.placeholder || "";
                    return {el: e.tagName.toLowerCase() + "." + String(e.className).split(" ")[0], text: txt.slice(0, 30),
                            color: s.color, background: bgs.map((b) => "rgb(" + b.slice(0, 3).join(", ") + ")").join(" / "),
                            fontSize: parseFloat(s.fontSize), fontWeight: +s.fontWeight, ratio: Math.round(r * 100) / 100};
                });
            }
            """,
            self.TEXT_NODES,
        )

    def effective_background(self, locator: str, nth: int = 0) -> str:
        return self.page.locator(locator).nth(nth).evaluate(
            """(el) => { let n = el; while (n && n.nodeType === 1) { const s = getComputedStyle(n);
                if (s.backgroundImage && s.backgroundImage !== 'none') return s.backgroundImage;
                if (s.backgroundColor && s.backgroundColor !== 'rgba(0, 0, 0, 0)') return s.backgroundColor;
                n = n.parentElement; } return 'rgb(255, 255, 255)'; }"""
        )

    def relative_luminance(self, css_colour: str) -> float:
        return self.page.evaluate(
            """(c) => { const m = (c.match(/[0-9.]+/g) || [0, 0, 0]).map(Number);
                const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); }""",
            css_colour,
        )

"""
web/pages/sectoral_committees/sectoral_committees_page.py — SectoralCommitteesPage.

Public-website Page Object for PBI 130716 ("QC - Councils, Committees &
Partnerships - 001 - Sectoral Committees and Business Councils").

URL (header menu Councils, Committees & Partnerships > Sectoral Committees and
Business Councils), CONFIRMED LIVE 2026-09-26:
  /web/qatar-chamber/sectoral-committees-and-business-councils   (AR: /ar prefix)
Client-rendered fragment `section.qc-sc` (Loading… status until data arrives).

Locators — disclosed scripted Playwright DOM probe at 1920/768/390, EN + AR:
  section.qc-sc
    .qc-sc-hero > nav.qc-sc-breadcrumb (a.qc-sc-crumb--home + svg.qc-sc-crumb-icon,
        svg.qc-sc-crumb-sep, a.qc-sc-crumb--current), p.qc-sc-hero-eyebrow, h1.qc-sc-hero-title,
        p.qc-sc-hero-subtitle, .qc-sc-hero-figure img
    .qc-sc-body
      section.qc-sc-sector (p.qc-sc-eyebrow, h2.qc-sc-heading, .qc-sc-lede)
      .qc-sc-lead-card > button.qc-sc-lead-head[aria-expanded] (span.qc-sc-lead-icon, .qc-sc-lead-eyebrow,
          .qc-sc-lead-title, .qc-sc-lead-desc, span.qc-sc-toggle) + div.qc-sc-lead-panel[hidden]
          > .qc-sc-leader-grid > article.qc-sc-leader (span.qc-sc-leader-num, p.qc-sc-leader-name, p.qc-sc-leader-sector)
      section.qc-sc-directory (.qc-sc-eyebrow, .qc-sc-heading, .qc-sc-lede, .qc-sc-search input.qc-sc-search-input
          + span.qc-sc-search-icon), .qc-sc-rows > div.qc-sc-row[data-qc-sc-haystack]
          > button.qc-sc-row-head[aria-expanded] (span.qc-sc-row-num, .qc-sc-row-title, .qc-sc-row-desc, span.qc-sc-toggle)
          + div.qc-sc-row-panel[hidden] > .qc-sc-mandate (p.qc-sc-mandate-eyebrow, p.qc-sc-mandate-heading,
          ul.qc-sc-mandate-list > li.qc-sc-mandate-item (span.qc-sc-mandate-icon + span.qc-sc-mandate-text))
      section.qc-sc-cta (.qc-sc-eyebrow, h2.qc-sc-cta-heading, p.qc-sc-cta-body, a.qc-sc-cta-card x3
          (span.qc-sc-cta-icon, .qc-sc-cta-title, .qc-sc-cta-desc, span.qc-sc-cta-arrow))
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

PATH = "/web/qatar-chamber/sectoral-committees-and-business-councils"


class SectoralCommitteesPage(BasePage):
    PAGE_BODY = "body"
    HEADER = "header.qc-global-site-header"
    NAV_PARENT = "header.qc-global-site-header a.qc-nav-link[href*='/committee']"
    NAV_PAGE_LINK = "header.qc-global-site-header a.qc-nav-link[href*='sectoral-committees-and-business-councils']"
    FOOTER = ".qc-global-site-footer"

    ROOT = "section.qc-sc"
    HERO = ".qc-sc-hero"
    HERO_INNER = ".qc-sc-hero-inner"
    CRUMBS = "nav.qc-sc-breadcrumb"
    CRUMB_ITEMS = "nav.qc-sc-breadcrumb > :is(a, span)"
    CRUMB_HOME_ICON = "svg.qc-sc-crumb-icon"
    CRUMB_SEP = "svg.qc-sc-crumb-sep"
    HERO_EYEBROW = "p.qc-sc-hero-eyebrow"
    HERO_TITLE = "h1.qc-sc-hero-title"
    HERO_SUBTITLE = "p.qc-sc-hero-subtitle"
    HERO_TEXT = ".qc-sc-hero-text"
    BODY = ".qc-sc-body"

    SECTOR = "section.qc-sc-sector"
    SECTOR_EYEBROW = "section.qc-sc-sector p.qc-sc-eyebrow"
    SECTOR_HEADING = "section.qc-sc-sector h2.qc-sc-heading"
    SECTOR_BODY = "section.qc-sc-sector .qc-sc-lede"

    LEAD_CARD = ".qc-sc-lead-card"
    LEAD_HEAD = "button.qc-sc-lead-head"
    LEAD_ICON = "span.qc-sc-lead-icon"
    LEAD_ICON_SVG = "span.qc-sc-lead-icon svg"
    LEAD_EYEBROW = ".qc-sc-lead-eyebrow"
    LEAD_TITLE = ".qc-sc-lead-title"
    LEAD_DESC = ".qc-sc-lead-desc"
    LEAD_TOGGLE = "button.qc-sc-lead-head span.qc-sc-toggle"
    LEAD_TOGGLE_ICON = "button.qc-sc-lead-head span.qc-sc-toggle svg"
    LEAD_PANEL = "div.qc-sc-lead-panel"
    LEADER = "article.qc-sc-leader"
    LEADER_NUM = "span.qc-sc-leader-num"
    LEADER_NAME = "p.qc-sc-leader-name"
    LEADER_SECTOR = "p.qc-sc-leader-sector"

    DIRECTORY = "section.qc-sc-directory"
    DIR_EYEBROW = "section.qc-sc-directory p.qc-sc-eyebrow"
    DIR_HEADING = "section.qc-sc-directory h2.qc-sc-heading"
    DIR_BODY = "section.qc-sc-directory .qc-sc-lede"
    SEARCH_FIELD = ".qc-sc-search"
    SEARCH = "input.qc-sc-search-input"
    SEARCH_ICON = "span.qc-sc-search-icon"
    ROWS = "[data-qc-sc-rows]"
    ROW = "div.qc-sc-row"
    VISIBLE_ROW = "div.qc-sc-row:not([hidden])"
    ROW_HEAD = "button.qc-sc-row-head"
    ROW_NUM = "span.qc-sc-row-num"
    ROW_TITLE = ".qc-sc-row-title"
    ROW_DESC = ".qc-sc-row-desc"
    ROW_TOGGLE = "button.qc-sc-row-head span.qc-sc-toggle"
    ROW_PANEL = "div.qc-sc-row-panel"
    MANDATE_EYEBROW = "p.qc-sc-mandate-eyebrow"
    MANDATE_HEADING = "p.qc-sc-mandate-heading"
    MANDATE_ITEM = "li.qc-sc-mandate-item"
    MANDATE_ICON = "span.qc-sc-mandate-icon"
    MANDATE_TEXT = "span.qc-sc-mandate-text"
    EMPTY = "[data-qc-sc-empty]"

    CTA = "section.qc-sc-cta"
    CTA_EYEBROW = "section.qc-sc-cta .qc-sc-eyebrow"
    CTA_HEADING = "h2.qc-sc-cta-heading"
    CTA_BODY = "p.qc-sc-cta-body"
    CTA_CARD = "a.qc-sc-cta-card"
    CTA_ICON = "span.qc-sc-cta-icon"
    CTA_TITLE = ".qc-sc-cta-title"
    CTA_DESC = ".qc-sc-cta-desc"
    CTA_ARROW = "span.qc-sc-cta-arrow"

    # ---- Navigation -------------------------------------------------------------
    def open_page(self, locale: str = "en") -> "SectoralCommitteesPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_ready()
        return self

    def wait_ready(self) -> None:
        self.wait_for(self.HERO_TITLE, timeout=30000)
        self.wait_for(self.ROW, first=True, timeout=30000)
        self.page.wait_for_function(
            "() => { const s = document.querySelector('[data-qc-sc-status]'); return !s || s.hidden; }", timeout=30000)

    def enable_dark_mode(self) -> "SectoralCommitteesPage":
        AccessibilityToolsComponent(self.page).enable_dark_mode()
        self.page.wait_for_function(
            "() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=10000)
        return self

    def menu_labels(self) -> dict:
        """Header menu labels: the parent item and the page's own menu link."""
        return self.page.evaluate(
            """([p, l]) => ({parent: ((document.querySelector(p) || {}).textContent || '').trim(),
                             page: ((document.querySelector(l) || {}).textContent || '').trim()})""",
            [self.NAV_PARENT, self.NAV_PAGE_LINK])

    # ---- Interactions (each waits for the resulting state) --------------------------
    def toggle_lead(self) -> None:
        before = self.page.locator(self.LEAD_HEAD).get_attribute("aria-expanded")
        self.click(self.LEAD_HEAD)
        self.page.wait_for_function(
            "(b) => document.querySelector('button.qc-sc-lead-head').getAttribute('aria-expanded') !== b", arg=before)
        self._settle()

    def toggle_row(self, index: int) -> None:
        head = self.page.locator(self.ROW).nth(index).locator(self.ROW_HEAD)
        before = head.get_attribute("aria-expanded")
        head.click()
        self.page.wait_for_function(
            "([i, b]) => document.querySelectorAll('div.qc-sc-row')[i].querySelector('button.qc-sc-row-head')"
            ".getAttribute('aria-expanded') !== b", arg=[index, before])
        self._settle()

    def row_index(self, title: str) -> int:
        return self.page.locator(self.ROW).evaluate_all(
            "(rows, t) => rows.findIndex(r => r.querySelector('.qc-sc-row-title').textContent.trim() === t)", title)

    def search(self, text: str) -> None:
        before = self.visible_row_titles()
        self.page.locator(self.SEARCH).fill(text)
        try:
            self.page.wait_for_function(
                "(b) => JSON.stringify([...document.querySelectorAll('div.qc-sc-row')].filter(r => !r.hidden && r.offsetParent)"
                ".map(r => r.querySelector('.qc-sc-row-title').textContent.trim())) !== b",
                arg=__import__("json").dumps(before, ensure_ascii=False), timeout=8000)
        except Exception:  # noqa: BLE001 — an unchanged list is itself a valid outcome
            pass

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH).input_value()

    def _settle(self) -> None:
        self.page.wait_for_function(
            "() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=10000)

    def click_cta(self, index: int = 0) -> str:
        before = self.page.url
        self.page.locator(self.CTA_CARD).nth(index).click()
        self.wait_for_url(lambda u: u != before, timeout=30000)
        return self.page.url

    # ---- 2026-10-07 additions (suite 140375 functional cases) ------------------------
    # Provenance: anonymous read-only GET of the page HTML, saved as
    # reports/locators/sectoral_committees/sectoral_en_anon_20261007.html. The fragment
    # JS there sets `aria-expanded` AND toggles class `is-open` on the head button
    # (CSS rotates the "+" toggle 45deg into the "x" when `is-open`), un-hides
    # `[data-qc-sc-empty]` (role=status) on no match, and builds the search haystack
    # from committeeName + shortDescription. Leaders come from /o/c/committeeleadercards
    # (leaderName, committeeSectorName, displayOrder on the 100-grid, *ActiveStatus).
    CRUMB_HOME = "a.qc-sc-crumb--home"  # UNVERIFIED (static HTML only; href set by fragment JS)
    OPEN_CLASS = "is-open"
    NAV_COMMITTEE_ITEM = ("header.qc-global-site-header nav.qc-nav ul.qc-nav-list > "
                          "li.qc-has-children:has(> a.qc-nav-link[href*='/committee'])")  # UNVERIFIED
    NAV_SUBMENU = ".qc-nav-sub"
    HOME_PATH = "/home"

    def open_home(self) -> "SectoralCommitteesPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.HEADER)
        return self

    def open_via_main_menu(self) -> "SectoralCommitteesPage":
        """Main Menu > Councils, Committees & Partnerships (hover opens the
        dropdown; the top item is a link) > Sectoral Committees and Business Councils."""
        item = self.page.locator(self.NAV_COMMITTEE_ITEM).first
        item.hover()
        item.locator(self.NAV_SUBMENU).first.wait_for(state="visible")
        item.locator(self.NAV_SUBMENU).first.locator(
            "a.qc-nav-link[href*='sectoral-committees-and-business-councils']").first.click()
        self.wait_for_url(lambda u: "sectoral-committees-and-business-councils" in u, timeout=30000)
        self.wait_ready()
        return self

    def reload_page(self) -> "SectoralCommitteesPage":
        self.page.reload(wait_until="domcontentloaded")
        self.wait_ready()
        return self

    def lead_expanded(self) -> bool:
        return self.page.locator(self.LEAD_HEAD).get_attribute("aria-expanded") == "true"

    def lead_icon_open(self) -> bool:
        """True when the toggle shows the close (x) state: head carries `is-open`."""
        return self.OPEN_CLASS in (self.page.locator(self.LEAD_HEAD).get_attribute("class") or "").split()

    def row_icon_open(self, index: int) -> bool:
        cls = self.page.locator(self.ROW).nth(index).locator(self.ROW_HEAD).get_attribute("class") or ""
        return self.OPEN_CLASS in cls.split()

    def row_panel_visible(self, index: int) -> bool:
        return self.page.locator(self.ROW).nth(index).locator(self.ROW_PANEL).is_visible()

    def row_panel_box(self, index: int):
        return self.page.locator(self.ROW).nth(index).locator(self.ROW_PANEL).bounding_box()

    def double_click_lead(self) -> None:
        """Two clicks inside one dblclick gesture (well under 200 ms apart), then
        wait for every running animation to finish."""
        self.page.locator(self.LEAD_HEAD).dblclick()
        self._settle()

    def focus_search(self) -> None:
        self.page.locator(self.SEARCH).click()

    def search_is_focused(self) -> bool:
        return self.page.evaluate("(s) => document.activeElement === document.querySelector(s)", self.SEARCH)

    def search_focus_ring(self) -> dict:
        return self.page.locator(self.SEARCH).evaluate(
            "e => { const c = getComputedStyle(e), p = getComputedStyle(e.parentElement);"
            " return {outline: c.outlineStyle + ' ' + c.outlineWidth, shadow: c.boxShadow,"
            " border: c.borderTopColor, parentShadow: p.boxShadow, parentBorder: p.borderTopColor}; }")

    def type_search(self, text: str) -> None:
        """Types key by key (the case's 'filters as you type') and waits for the
        list to settle the same way search() does."""
        before = self.visible_row_titles()
        self.page.locator(self.SEARCH).press_sequentially(text)
        try:
            self.page.wait_for_function(
                "(b) => JSON.stringify([...document.querySelectorAll('div.qc-sc-row')].filter(r => !r.hidden && r.offsetParent)"
                ".map(r => r.querySelector('.qc-sc-row-title').textContent.trim())) !== b",
                arg=__import__("json").dumps(before, ensure_ascii=False), timeout=8000)
        except Exception:  # noqa: BLE001 — an unchanged list is itself a valid outcome
            pass

    def clear_search(self) -> None:
        self.search("")

    def search_placeholder(self) -> str:
        return self.page.locator(self.SEARCH).get_attribute("placeholder") or ""

    def empty_state_visible(self) -> bool:
        loc = self.page.locator(self.EMPTY)
        return loc.count() > 0 and loc.first.is_visible()

    def empty_state_text(self) -> str:
        loc = self.page.locator(self.EMPTY)
        return " ".join((loc.first.text_content() or "").split()) if loc.count() else ""

    def cta_index(self, title: str) -> int:
        return self.page.locator(self.CTA_CARD).evaluate_all(
            "(cards, t) => cards.findIndex(c => (c.querySelector('.qc-sc-cta-title') || {}).textContent?.trim() === t)",
            title)

    def cta_titles(self) -> list:
        return self.texts(self.CTA_TITLE)

    def hover_cta(self, index: int) -> dict:
        """Hovers the card and returns its computed cursor plus the box, so a test
        can check it is interactive over its whole area."""
        card = self.page.locator(self.CTA_CARD).nth(index)
        card.scroll_into_view_if_needed()
        card.hover()
        return card.evaluate("e => ({cursor: getComputedStyle(e).cursor, tag: e.tagName.toLowerCase(),"
                             " href: e.getAttribute('href')})")

    def click_crumb_home(self) -> str:
        before = self.page.url
        self.page.locator(self.CRUMB_HOME).first.click()
        self.wait_for_url(lambda u: u != before, timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")
        return self.page.url

    def crumb_home_cursor(self) -> str:
        loc = self.page.locator(self.CRUMB_HOME).first
        loc.hover()
        return loc.evaluate("e => getComputedStyle(e).cursor")

    def status_of(self, url: str) -> int:
        """HTTP status of `url` fetched with this (anonymous) context's cookies."""
        return self.page.request.get(url).status

    def page_title(self) -> str:
        return self.page.title()

    def api_active_leaders(self) -> list:
        """Leader cards in CMS Display Order, read the same way the fragment reads
        them (anonymous /o/c/committeeleadercards, *ActiveStatus true, numeric
        ascending displayOrder). Returns [{name, sector, order}]."""
        return self.page.evaluate(
            """async () => {
                const g = (window.Liferay && Liferay.ThemeDisplay) ? Liferay.ThemeDisplay.getScopeGroupId() : '';
                const r = await fetch('/o/c/committeeleadercards/scopes/' + g + '?pageSize=200',
                                      {credentials: 'same-origin', headers: {accept: 'application/json'}});
                const items = ((await r.json()) || {}).items || [];
                const active = i => Object.keys(i).filter(k => /activestatus$/i.test(k)).every(k => i[k] === true);
                return items.filter(active)
                    .sort((a, b) => Number(a.displayOrder) - Number(b.displayOrder))
                    .map(i => ({name: (i.leaderName || '').trim(), sector: (i.committeeSectorName || '').trim(),
                                order: i.displayOrder}));
            }""")

    def dialog_watch(self) -> list:
        """Starts recording any JS dialog (alert/confirm/prompt) the page raises;
        each is dismissed so a test never hangs on one."""
        seen = []

        def _on(d):
            seen.append(f"{d.type}: {d.message}")
            try:
                d.dismiss()
            except Exception:  # noqa: BLE001
                pass

        self.page.on("dialog", _on)
        return seen

    # ---- State --------------------------------------------------------------------
    def attr(self, locator: str, name: str, nth: int = 0):
        return self.page.locator(locator).nth(nth).get_attribute(name)

    def row_expanded(self, index: int) -> bool:
        return self.page.locator(self.ROW).nth(index).locator(self.ROW_HEAD).get_attribute("aria-expanded") == "true"

    def row_child_styles(self, index: int, child: str, props, nth: int = 0) -> dict:
        return self.page.locator(self.ROW).nth(index).locator(child).nth(nth).evaluate(
            "(e, props) => { const c = getComputedStyle(e); const o = {}; props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; }",
            list(props))

    def row_child_box(self, index: int, child: str, nth: int = 0):
        return self.page.locator(self.ROW).nth(index).locator(child).nth(nth).bounding_box()

    def row_child_icon(self, index: int, child: str, nth: int = 0) -> dict:
        return self.page.locator(self.ROW).nth(index).locator(child).nth(nth).evaluate(
            """e => { const svg = e.tagName.toLowerCase() === 'svg' ? e : e.querySelector('svg'); const t = svg || e;
                const r = t.getBoundingClientRect(), c = getComputedStyle(t);
                const path = svg ? svg.querySelector('path, polyline, line') : null; const pc = path ? getComputedStyle(path) : c;
                return {width: r.width, height: r.height, stroke: pc.stroke, color: c.color, background: c.backgroundColor, hasSvg: !!svg}; }""")

    def row_mandate_texts(self, index: int) -> list:
        return [" ".join(t.split()) for t in self.page.locator(self.ROW).nth(index).locator(self.MANDATE_TEXT).all_text_contents()]

    def row_mandate_visible(self, index: int) -> int:
        loc = self.page.locator(self.ROW).nth(index).locator(self.MANDATE_ITEM)
        return sum(1 for i in range(loc.count()) if loc.nth(i).is_visible())

    def row_text(self, index: int, child: str) -> str:
        return " ".join(self.page.locator(self.ROW).nth(index).locator(child).first.text_content().split())

    def visible_row_titles(self) -> list:
        return self.page.locator(self.ROW).evaluate_all(
            "rows => rows.filter(r => !r.hidden && r.offsetParent).map(r => r.querySelector('.qc-sc-row-title').textContent.trim())")

    def visible_row_nums(self) -> list:
        return self.page.locator(self.ROW).evaluate_all(
            "rows => rows.filter(r => !r.hidden && r.offsetParent).map(r => r.querySelector('.qc-sc-row-num').textContent.trim())")

    def visible_count(self, locator: str) -> int:
        loc = self.page.locator(locator)
        return sum(1 for i in range(loc.count()) if loc.nth(i).is_visible())

    def leaders(self) -> list:
        return self.page.locator(self.LEADER).evaluate_all(
            """els => els.map(e => ({num: (e.querySelector('.qc-sc-leader-num') || {}).textContent?.trim() || '',
                                     name: (e.querySelector('.qc-sc-leader-name') || {}).textContent?.trim() || '',
                                     sector: (e.querySelector('.qc-sc-leader-sector') || {}).textContent?.trim() || '',
                                     visible: e.offsetParent !== null}))""")

    def texts(self, locator: str) -> list:
        return [" ".join((t or "").split()) for t in self.page.locator(locator).all_text_contents()]

    def text_of(self, locator: str, nth: int = 0) -> str:
        loc = self.page.locator(locator)
        return " ".join(loc.nth(nth).text_content().split()) if loc.count() > nth else ""

    def styles(self, locator: str, props, nth: int = 0, pseudo: str = None) -> dict:
        return self.page.locator(locator).nth(nth).evaluate(
            "(e, [props, ps]) => { const c = getComputedStyle(e, ps); const o = {}; props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; }",
            [list(props), pseudo])

    def icon_styles(self, locator: str, nth: int = 0) -> dict:
        """Box + colour facts for an icon container: its own svg (if any) or the mask/pseudo glyph."""
        return self.page.locator(locator).nth(nth).evaluate(
            """e => { const svg = e.tagName.toLowerCase() === 'svg' ? e : e.querySelector('svg');
                const t = svg || e; const r = t.getBoundingClientRect(), c = getComputedStyle(t);
                const path = svg ? svg.querySelector('path, polyline, line, circle, rect') : null;
                const pc = path ? getComputedStyle(path) : c;
                return {width: r.width, height: r.height, stroke: pc.stroke, color: c.color, fill: pc.fill,
                        strokeWidth: pc.strokeWidth, background: c.backgroundColor, hasSvg: !!svg}; }""")

    def box(self, locator: str, nth: int = 0):
        loc = self.page.locator(locator)
        return loc.nth(nth).bounding_box() if loc.count() > nth else None

    def boxes(self, locator: str) -> list:
        loc = self.page.locator(locator)
        return [loc.nth(i).bounding_box() for i in range(loc.count())]

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def document_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.dir")

    def theme(self):
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def current_url(self) -> str:
        return self.page.url

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate("() => document.documentElement.scrollWidth - document.documentElement.clientWidth")

    def clipped_text(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('section.qc-sc *')].filter(e => e.offsetParent && e.children.length === 0
                       && !/sr-only/.test(String(e.className))   // visually-hidden labels are clipped by design
                       && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible')
                       .map(e => String(e.className))""")

    def section_order(self) -> list:
        return self.page.evaluate(
            """() => [['hero', '.qc-sc-hero'], ['sector', 'section.qc-sc-sector'], ['directory', 'section.qc-sc-directory'],
                      ['cta', 'section.qc-sc-cta'], ['footer', '.qc-global-site-footer']]
                     .map(([n, s]) => { const e = document.querySelector(s); return [n, e ? e.getBoundingClientRect().top + scrollY : null]; })""")

    def low_contrast_text(self, scope: str = "section.qc-sc", normal: float = 4.5, large: float = 3.0) -> list:
        """Visible leaf text below `normal` (or `large` for large text) contrast against the nearest solid background."""
        return self.page.evaluate(
            """([s, NORMAL, LARGE]) => { const parse = c => { const m = c.match(/[0-9.]+/g) || [0,0,0,0]; return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
                const lum = r => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                                   return 0.2126 * f(r[0]) + 0.7152 * f(r[1]) + 0.0722 * f(r[2]); };
                const out = [];
                document.querySelectorAll(s + ', ' + s + ' *').forEach(e => {
                    if (!e.offsetParent || e.closest('[aria-hidden="true"], .qc-sc-hero')) return;
                    const t = [...e.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join('').trim(); if (!t) return;
                    let n = e, bg = null; while (n && n.nodeType === 1) { const c = parse(getComputedStyle(n).backgroundColor); if (c[3] > 0) { bg = c; break; } n = n.parentElement; }
                    bg = bg || [255, 255, 255, 1]; const st = getComputedStyle(e), fg = parse(st.color), a = fg[3] * parseFloat(st.opacity || 1);
                    const mix = [0, 1, 2].map(i => fg[i] * a + bg[i] * (1 - a)); const l1 = lum(mix), l2 = lum(bg);
                    const r = (Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05);
                    const large = parseFloat(st.fontSize) >= 24 || (parseFloat(st.fontSize) >= 18.66 && +st.fontWeight >= 700);
                    if (r < (large ? LARGE : NORMAL)) out.push(String(e.className).split(' ')[0] + " '" + t.slice(0, 25) + "' " + st.color
                                                        + ' on rgb(' + bg.slice(0, 3).join(', ') + ') = ' + Math.round(r * 100) / 100);
                }); return out; }""", [scope, normal, large])

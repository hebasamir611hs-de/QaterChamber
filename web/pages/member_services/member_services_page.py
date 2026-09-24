"""
web/pages/member_services/member_services_page.py — MemberServicesPage.

Public-website Page Object for PBI 129400 ("QC-SVC-001 — Member's
Services"). URL: `/web/qatar-chamber/our-services/member-services` (Arabic:
same path behind `/ar`, via `web_url(path, locale="ar")`). The header
language toggle redirects through `/c/portal/update_language` and lands on
a different friendly URL (`/ar/member-services`, `/our-services/member-services`)
— so toggling waits on "URL changed + component rendered", never on a
hard-coded destination.

Locators: CLI extractor surfaced only header/footer chrome; the component
internals below came from a disclosed scripted Playwright DOM probe (shell
script, not the MCP), CONFIRMED LIVE 2026-09-24 against qcdev at 1920x1080,
768x1024 and 375x812. Component attribute/class family `qc-ms-*`:

    section.qc-member-services[dir]
      .qc-ms-hero (.qc-ms-hero-overlay gradient, .qc-ms-hero-inner > h1.qc-ms-hero-title)
      .qc-ms-content
        .qc-ms-headrow > h2.qc-ms-heading, p.qc-ms-intro
        [data-qc-ms-listview] > [data-qc-ms-cards] > a.qc-ms-card[data-qc-ms-key]
            (.qc-ms-card-ico tile, .qc-ms-card-name, .qc-ms-card-desc, .qc-ms-card-cta pill + svg)
          + .qc-ms-list-support img
        [data-qc-ms-detailview] (hidden until a card is opened; URL gets #<key>)
          .qc-ms-detail > aside.qc-ms-sidebar (button.qc-ms-side-head "All Services",
              [role=tablist] a.qc-ms-side-item[data-qc-ms-key] (.is-active + aria-selected),
              each: .qc-ms-side-ico tile, .qc-ms-side-label, .qc-ms-side-chev svg)
            + span.qc-ms-vdiv + [data-qc-ms-panel] (h3.qc-ms-subheading, .qc-ms-richtext p,
              .qc-ms-reqdocs li (::before dash), a.qc-ms-cta + svg)
            + .qc-ms-detail-support img
    header.qc-global-site-header (a.qc-nav-link, a.qc-lang-switcher)
    .qc-global-site-footer (gradient background)
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent


class MemberServicesPage(BasePage):
    PATH = "/web/qatar-chamber/our-services/member-services"
    NEW_MEMBERSHIP = "new-membership"

    # ---- Global chrome ----------------------------------------------------------
    PAGE_BODY = "body"
    HEADER = "header.qc-global-site-header"
    HEADER_NAV_LINK = "header.qc-global-site-header a.qc-nav-link"
    LANG_TOGGLE = "header.qc-global-site-header a.qc-lang-switcher"
    FOOTER = ".qc-global-site-footer"

    # ---- Component root / hero ----------------------------------------------------
    ROOT = "section.qc-member-services"
    HERO = ".qc-ms-hero"
    HERO_OVERLAY = ".qc-ms-hero-overlay"
    HERO_TITLE = ".qc-ms-hero-title"
    CONTENT = ".qc-ms-content"
    HEADING = ".qc-ms-heading"
    INTRO = ".qc-ms-intro"

    # ---- List view ----------------------------------------------------------------
    LIST_VIEW = "[data-qc-ms-listview]"
    CARDS = "[data-qc-ms-cards]"
    CARD = "a.qc-ms-card"
    CARD_BY_KEY = "a.qc-ms-card[data-qc-ms-key='{key}']"
    CARD_ICON_TILE = ".qc-ms-card-ico"
    CARD_NAME = ".qc-ms-card-name"
    CARD_DESC = ".qc-ms-card-desc"
    CARD_CTA = ".qc-ms-card-cta"
    CARD_CTA_ICON = ".qc-ms-card-cta svg"
    LIST_SUPPORT = ".qc-ms-list-support"
    LIST_SUPPORT_IMG = ".qc-ms-list-support img"

    # ---- Detail view --------------------------------------------------------------
    DETAIL_VIEW = "[data-qc-ms-detailview]"
    DETAIL = ".qc-ms-detail"
    SIDEBAR = "aside.qc-ms-sidebar"
    SIDE_HEAD = "button.qc-ms-side-head"
    SIDEBAR_DROPDOWN = "aside.qc-ms-sidebar select"
    SIDE_ITEM = "a.qc-ms-side-item"
    SIDE_ITEM_ACTIVE = "a.qc-ms-side-item.is-active"
    SIDE_ITEM_INACTIVE = "a.qc-ms-side-item:not(.is-active)"
    SIDE_ICON_TILE = ".qc-ms-side-ico"
    SIDE_LABEL = ".qc-ms-side-label"
    SIDE_CHEVRON = ".qc-ms-side-chev"
    VDIVIDER = ".qc-ms-vdiv"
    PANEL = "[data-qc-ms-panel]"
    SUBHEADING = "[data-qc-ms-panel] h3.qc-ms-subheading"
    BODY_TEXT = "[data-qc-ms-panel] .qc-ms-richtext p"
    REQ_DOCS_LIST = "[data-qc-ms-panel] .qc-ms-reqdocs ul"
    REQ_DOCS_ITEM = "[data-qc-ms-panel] .qc-ms-reqdocs li"
    CTA = "[data-qc-ms-panel] a.qc-ms-cta"
    CTA_LABEL = "[data-qc-ms-panel] a.qc-ms-cta > span"
    CTA_ICON = "[data-qc-ms-panel] a.qc-ms-cta svg"
    DETAIL_SUPPORT = ".qc-ms-detail-support"

    _RENDERED_JS = """() => {
        const cards = document.querySelectorAll('a.qc-ms-card');
        const list = document.querySelector('[data-qc-ms-listview]');
        const detail = document.querySelector('[data-qc-ms-detailview]');
        if (!cards.length || !list || !detail) return false;
        return (!list.hidden && list.offsetParent !== null)
            || (!detail.hidden && !!document.querySelector('[data-qc-ms-panel] h3.qc-ms-subheading'));
    }"""

    # ---- Navigation -------------------------------------------------------------
    def open_list(self, locale: str = "en") -> "MemberServicesPage":
        self.open(web_url(self.PATH, locale=locale))
        self._wait_rendered()
        return self

    def open_detail(self, key: str = NEW_MEMBERSHIP, locale: str = "en") -> "MemberServicesPage":
        self.open_list(locale)
        return self.open_service(key)

    def open_service(self, key: str) -> "MemberServicesPage":
        """Clicks the list-view card (or sidebar row, when already in the
        detail view) for `key` and waits until the panel shows that service."""
        card = self.CARD_BY_KEY.format(key=key)
        target = card if self.is_visible(card) else f"{self.SIDE_ITEM}[data-qc-ms-key='{key}']"
        self.click(target)
        self.wait_for(f"{self.SIDE_ITEM_ACTIVE}[data-qc-ms-key='{key}']", state="attached")
        self.wait_for(self.SUBHEADING, first=True)
        return self

    def toggle_language(self) -> "MemberServicesPage":
        before = self.page.url
        self.click(self.LANG_TOGGLE)
        self.wait_for_url(lambda url: url != before, timeout=20000)
        self._wait_rendered()
        return self

    def enable_dark_mode(self) -> "MemberServicesPage":
        AccessibilityToolsComponent(self.page).enable_dark_mode()
        return self

    def _wait_rendered(self) -> None:
        self.wait_for(self.ROOT, state="attached", timeout=20000)
        self.page.wait_for_function(self._RENDERED_JS, timeout=20000)

    # ---- State queries ----------------------------------------------------------
    def current_url(self) -> str:
        return self.page.url

    def document_dir(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.dir || getComputedStyle(document.documentElement).direction"
        )

    def theme(self) -> str | None:
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def root_dir(self) -> str:
        return self.get_attribute(self.ROOT, "dir") or ""

    def language_toggle_label(self) -> str:
        return self.text(self.LANG_TOGGLE).strip()

    def texts(self, locator: str) -> list[str]:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def card_names(self) -> list[str]:
        return self.texts(f"{self.CARD} {self.CARD_NAME}")

    def side_labels(self) -> list[str]:
        return self.texts(f"{self.SIDE_ITEM} {self.SIDE_LABEL}")

    def side_head_text(self) -> str:
        return self.text(self.SIDE_HEAD).strip()

    def subheadings(self) -> list[str]:
        return self.texts(self.SUBHEADING)

    def active_service_key(self) -> str | None:
        loc = self.page.locator(self.SIDE_ITEM_ACTIVE)
        return loc.first.get_attribute("data-qc-ms-key") if loc.count() else None

    def active_row_count(self) -> int:
        return self.page.locator(self.SIDE_ITEM_ACTIVE).count()

    def aria_selected_count(self) -> int:
        return self.page.locator(f"{self.SIDE_ITEM}[aria-selected='true']").count()

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    def is_list_view(self) -> bool:
        return self.is_visible(self.LIST_VIEW)

    def is_detail_view(self) -> bool:
        return self.is_visible(self.DETAIL_VIEW)

    def styles(self, locator: str, props, pseudo: str | None = None, nth: int = 0) -> dict:
        """Computed style values for `props` on the nth match (optionally a
        pseudo-element such as '::before')."""
        return self.page.locator(locator).nth(nth).evaluate(
            "(el, [props, pseudo]) => { const c = getComputedStyle(el, pseudo); const o = {};"
            " props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; }",
            [list(props), pseudo],
        )

    def styles_all(self, locator: str, props) -> list[dict]:
        return self.page.locator(locator).evaluate_all(
            "(els, props) => els.map(el => { const c = getComputedStyle(el); const o = {};"
            " props.forEach(p => o[p] = c.getPropertyValue(p).trim()); return o; })",
            list(props),
        )

    def box(self, locator: str, nth: int = 0) -> dict:
        """Document-relative border box of the nth match."""
        return self.page.locator(locator).nth(nth).evaluate(
            """el => { const b = el.getBoundingClientRect();
                return {left: b.left + scrollX, top: b.top + scrollY, right: b.right + scrollX,
                        bottom: b.bottom + scrollY, width: b.width, height: b.height}; }"""
        )

    def boxes(self, locator: str) -> list[dict]:
        return self.page.locator(locator).evaluate_all(
            """els => els.map(el => { const b = el.getBoundingClientRect();
                return {left: b.left + scrollX, top: b.top + scrollY, right: b.right + scrollX,
                        bottom: b.bottom + scrollY, width: b.width, height: b.height,
                        visible: el.offsetParent !== null && b.width > 0 && b.height > 0}; })"""
        )

    def content_box(self, locator: str) -> dict:
        """Document-relative content box (border box minus border + padding)."""
        return self.page.locator(locator).evaluate(
            """el => { const b = el.getBoundingClientRect(), c = getComputedStyle(el);
                const n = p => parseFloat(c.getPropertyValue(p)) || 0;
                const left = b.left + scrollX + n('border-left-width') + n('padding-left');
                const right = b.right + scrollX - n('border-right-width') - n('padding-right');
                const top = b.top + scrollY + n('border-top-width') + n('padding-top');
                return {left, right, top, width: right - left}; }"""
        )

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )

    def overflowing_elements(self) -> list[str]:
        """Elements whose right edge extends past the viewport width."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('body *')]
                .filter(e => { const r = e.getBoundingClientRect();
                    return r.width > 0 && r.right > innerWidth + 1 && getComputedStyle(e).visibility !== 'hidden'; })
                .slice(0, 5).map(e => e.tagName.toLowerCase() + '.' + String(e.className).trim().split(/\\s+/).join('.')
                    + ' (right=' + Math.round(e.getBoundingClientRect().right) + 'px)')"""
        )

    def clipped_text_elements(self) -> list[str]:
        return self.page.evaluate(
            """root => [...document.querySelectorAll(root + ' :is(h1,h2,h3,p,li,span,a)')]
                .filter(e => e.offsetParent !== null && e.children.length === 0
                    && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== 'visible')
                .map(e => String(e.className) || e.tagName)""",
            self.ROOT,
        )

    def gradient_border_sources(self, locator: str) -> dict:
        """Every place a gradient border could be painted from, for the
        first match: the element's own border-image-source and
        background-image (border-box trick) plus both pseudo-elements'
        background-image and border-image-source."""
        return self.page.locator(locator).first.evaluate(
            """el => { const o = {};
                for (const [k, ps] of [['self', null], ['::before', '::before'], ['::after', '::after']]) {
                    const c = getComputedStyle(el, ps);
                    o[k + ' border-image-source'] = c.borderImageSource;
                    o[k + ' background-image'] = c.backgroundImage;
                }
                const c = getComputedStyle(el);
                o['self border'] = c.borderTopWidth + ' ' + c.borderTopStyle + ' ' + c.borderTopColor;
                return o; }"""
        )

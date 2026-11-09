"""
web/pages/laws_regulations/laws_regulations_page.py — LawsRegulationsPage.

Public-frontend Page Object for PBI 130699 "QC - Business Gateway - 006 -
Laws & Regulations": `/web/qatar-chamber/laws-regulations` (Arabic:
`/ar/web/qatar-chamber/laws-regulations`), reached from the main menu's
Business Gateway -> "Laws & Regulations" link.

Locators confirmed live 2026-09-29 by an anonymous scoped Playwright DOM probe
(the CLI extractor walks only interactive roles; the `qc-lawreg-*` card
internals are spans inside one anchor, so they were read with a scoped
`evaluate()`, never guessed). The fragment exposes stable `data-qc-lawreg-*`
hooks, preferred over classes.

HOW THE PAGE WORKS (the fragment's own source, read live):
  - Client-rendered: the delivered HTML carries no card; the fragment fetches
    `/o/c/lawregulations/scopes/<groupId>?pageSize=200` and renders only
    entries whose `activeStatus` is truthy, sorted ascending by
    `displayOrder`. Workflow state is not filtered client-side, so draft
    exclusion depends on what that response serves an anonymous visitor —
    `delivered_source_contains()` checks BOTH the document and that response.
  - 6 cards initially; "Load More" (`button[data-qc-lawreg-more]`) adds 6
    and hides itself when exhausted.
  - A card is ONE `<a class="qc-lawreg-card">`; its `href` is the entry's
    External URL and `target="_blank"` only when Open Behavior = New Tab. The
    external-link icon (`.qc-lawreg-ext`) is an aria-hidden span INSIDE that
    anchor, so "clicking the icon" clicks the card link.
  - Chip = "{lawNumber} · {year}" (U+00B7), rendered VERBATIM: the real
    records store Law Number as "Law No. 11", which is why the live chip
    reads "Law No. 11 · 2015". A Law Number of "25" renders "25 · 2005".
  - Search (`input[data-qc-lawreg-search]`) filters client-side over title +
    number + year; no match shows `[data-qc-lawreg-empty]`
    ("No laws or regulations match your search." /
    "لا توجد قوانين أو لوائح مطابقة لبحثك.").
  - Hero title "Laws & Regulations" / "القوانين واللوائح"; search placeholder
    "Search.." / "بحث.."; root `dir` is rtl on the Arabic site.
"""

from __future__ import annotations

import json

from config.settings import web_url
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage

PUBLIC_PATH = "/web/qatar-chamber/laws-regulations"
LAW_REGULATIONS_API_MARKER = "/o/c/lawregulations/"
# A console error the site emits on every page load regardless of this
# feature (third-party storage-access API) — observed on the healthy page.
BASELINE_CONSOLE_NOISE = ("requestStorageAccess",)


class LawsRegulationsPage(BasePage):
    ROOT = ".qc-lawreg"
    HERO_TITLE = "[data-qc-lawreg-title]"
    GRID = "[data-qc-lawreg-grid]"
    CARD = "a.qc-lawreg-card"
    CARD_CHIP = ".qc-lawreg-chip"
    CARD_EXT_ICON = ".qc-lawreg-ext"
    CARD_TITLE = ".qc-lawreg-card-title"
    SEARCH_INPUT = "input[data-qc-lawreg-search]"
    LOAD_MORE = "button[data-qc-lawreg-more]"
    EMPTY_STATE = "[data-qc-lawreg-empty]"
    STATUS = "[data-qc-lawreg-status]"

    def __init__(self, page):
        super().__init__(page)
        self.document_html = ""
        self.api_body = ""
        self.console_errors: list[str] = []
        self.page.on("console", self._on_console)
        self.page.on("pageerror", lambda exc: self.console_errors.append(f"pageerror: {exc}"))

    def _on_console(self, message) -> None:
        if message.type == "error":
            self.console_errors.append(message.text)

    # ---- Navigation --------------------------------------------------------
    def open_page(self, locale: str = "en") -> "LawsRegulationsPage":
        """Loads the page and keeps what was DELIVERED: the document HTML and
        the lawregulations response the page itself fetched (observed, not a
        separate API call)."""
        url = web_url(PUBLIC_PATH, locale=locale)
        captured = {"doc": "", "api": ""}

        def _on_response(response):
            try:
                if response.request.resource_type == "document" and PUBLIC_PATH in response.url:
                    captured["doc"] = response.text()
                elif LAW_REGULATIONS_API_MARKER in response.url:
                    captured["api"] = response.text()
            except Exception:  # noqa: BLE001 — a body can be unavailable on redirects
                pass

        self.page.on("response", _on_response)
        try:
            self.open(url)
            self._wait_for_cards()
            wait_until(lambda: captured["api"] != "", timeout=15.0, poll=0.25,
                       message="the page never fetched its lawregulations data")
        finally:
            self.page.remove_listener("response", _on_response)
        self.document_html = captured["doc"]
        self.api_body = captured["api"]
        return self

    def _wait_for_cards(self) -> None:
        self.page.locator(self.GRID).wait_for(state="attached", timeout=30000)
        try:
            self.page.locator(self.CARD).first.wait_for(state="visible", timeout=30000)
        except Exception:  # noqa: BLE001 — an empty grid is a legitimate state for the caller to assert on
            pass

    def load_all(self, max_clicks: int = 30) -> int:
        """Clicks Load More until it disappears; returns clicks made."""
        clicks = 0
        more = self.page.locator(self.LOAD_MORE)
        while clicks < max_clicks and more.count() and more.first.is_visible():
            before = self.page.locator(self.CARD).count()
            more.first.click()
            clicks += 1
            try:
                wait_until(
                    lambda: self.page.locator(self.CARD).count() > before
                    or not more.first.is_visible(),
                    timeout=10.0, poll=0.2, message="Load More did not add cards",
                )
            except WaitTimeoutError:
                break
        return clicks

    def is_load_more_visible(self) -> bool:
        more = self.page.locator(self.LOAD_MORE)
        return more.count() > 0 and more.first.is_visible()

    # ---- Cards ----------------------------------------------------------------
    def visible_card_titles(self) -> list[str]:
        return self.page.evaluate(
            """(sel) => [...document.querySelectorAll(sel.card)]
                .filter(c => c.offsetParent !== null)
                .map(c => (c.querySelector(sel.title) || {}).innerText || '')
                .map(t => t.trim())""",
            {"card": self.CARD, "title": self.CARD_TITLE},
        )

    def visible_card_count(self) -> int:
        return len(self.visible_card_titles())

    def card(self, title: str) -> dict | None:
        """The rendered card whose title equals `title` exactly, or None:
        {index, chip, title, href, target, visible, opacity, classes}."""
        return self.page.evaluate(
            """(args) => {
                const cards = [...document.querySelectorAll(args.card)].filter(c => c.offsetParent !== null);
                const i = cards.findIndex(c => ((c.querySelector(args.title) || {}).innerText || '').trim() === args.want);
                if (i < 0) return null;
                const c = cards[i];
                return {
                    index: i,
                    chip: ((c.querySelector(args.chip) || {}).innerText || '').trim(),
                    title: ((c.querySelector(args.title) || {}).innerText || '').trim(),
                    href: c.getAttribute('href') || '',
                    target: c.getAttribute('target') || '',
                    visible: c.offsetParent !== null,
                    opacity: getComputedStyle(c).opacity,
                    classes: c.className,
                    has_ext_icon: !!c.querySelector(args.ext),
                };
            }""",
            {"card": self.CARD, "title": self.CARD_TITLE, "chip": self.CARD_CHIP,
             "ext": self.CARD_EXT_ICON, "want": title},
        )

    def has_card(self, title: str) -> bool:
        return self.card(title) is not None

    def card_text_style(self, title: str, part: str) -> dict:
        """Computed typography of a card's `part` ("chip" | "title"):
        {font_family, font_weight, font_size, line_height, text_align, color}."""
        selector = self.CARD_CHIP if part == "chip" else self.CARD_TITLE
        return self.page.evaluate(
            """(args) => {
                const card = [...document.querySelectorAll(args.card)]
                    .find(c => ((c.querySelector(args.title) || {}).innerText || '').trim() === args.want);
                if (!card) return {};
                const el = card.querySelector(args.part);
                const s = getComputedStyle(el);
                return {font_family: s.fontFamily, font_weight: s.fontWeight, font_size: s.fontSize,
                        line_height: s.lineHeight, text_align: s.textAlign, color: s.color};
            }""",
            {"card": self.CARD, "title": self.CARD_TITLE, "part": selector, "want": title},
        )

    def blank_or_raw_card_texts(self) -> list[str]:
        """Cards whose title/chip is empty or shows a raw placeholder
        ("null", "undefined", "{", a dotted language key)."""
        return self.page.evaluate(
            """(sel) => [...document.querySelectorAll(sel.card)].filter(c => c.offsetParent !== null)
                .map(c => [((c.querySelector(sel.title) || {}).innerText || '').trim(),
                           ((c.querySelector(sel.chip) || {}).innerText || '').trim()])
                .filter(([t, ch]) => !t || /\\bnull\\b|\\bundefined\\b|\\{|\\}|^[a-z]+(-[a-z]+)+$/i.test(t + ' ' + ch))
                .map(p => p.join(' | '))""",
            {"card": self.CARD, "title": self.CARD_TITLE, "chip": self.CARD_CHIP},
        )

    # ---- Search ---------------------------------------------------------------
    def search(self, keyword: str) -> "LawsRegulationsPage":
        box = self.page.locator(self.SEARCH_INPUT)
        box.fill(keyword)
        # The fragment filters synchronously on the input event `fill()`
        # dispatches, so the grid is already re-rendered once the value lands.
        wait_until(lambda: box.input_value() == keyword, timeout=5.0, poll=0.1,
                   message="search box did not take the keyword")
        return self

    def is_empty_state_visible(self) -> bool:
        empty = self.page.locator(self.EMPTY_STATE)
        return empty.count() > 0 and empty.first.is_visible()

    def empty_state_text(self) -> str:
        return self.page.locator(self.EMPTY_STATE).first.inner_text().strip()

    # ---- Page chrome ------------------------------------------------------------
    def hero_title_text(self) -> str:
        return self.page.locator(self.HERO_TITLE).first.inner_text().strip()

    def search_placeholder(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).get_attribute("placeholder") or ""

    def layout_dir(self) -> str:
        return self.page.locator(self.ROOT).first.get_attribute("dir") or ""

    def status_text(self) -> str:
        status = self.page.locator(self.STATUS)
        return status.first.inner_text().strip() if status.count() else ""

    # ---- Delivered content ------------------------------------------------------
    def delivered_source_contains(self, text: str) -> bool:
        """True if `text` is in the delivered document HTML or in the
        lawregulations response the page fetched for this visitor."""
        return text in self.document_html or text in self.api_body

    def rendered_text_contains(self, text: str) -> bool:
        return text in self.page.locator("body").inner_text()

    # ---- Following a card link ---------------------------------------------------
    def follow_card_link(self, title: str) -> dict:
        """Clicks the card's external-link icon (it lives inside the card
        anchor) and reports where the browser went: {clicked_href, final_url,
        status, redirected, opened_new_tab}. `status` and `redirected` come
        from the opened tab's own PerformanceNavigationTiming entry — the
        popup's first request is emitted before Playwright hands the page
        over, so a request listener cannot observe it reliably."""
        card = self.page.locator(self.CARD).filter(
            has=self.page.locator(self.CARD_TITLE, has_text=title)
        ).first
        clicked_href = card.get_attribute("href") or ""
        context = self.page.context
        pages_before = len(context.pages)
        try:
            with context.expect_page(timeout=20000) as popup_info:
                card.locator(self.CARD_EXT_ICON).click()
            popup = popup_info.value
        except Exception:  # noqa: BLE001 — no new tab: the link opened in place
            return {
                "clicked_href": clicked_href,
                "final_url": self.page.url,
                "status": None,
                "redirected": None,
                "opened_new_tab": len(context.pages) > pages_before,
            }
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=45000)
        except Exception:  # noqa: BLE001 — a slow external host still reports its URL below
            pass
        timing = {}
        try:
            timing = popup.evaluate(
                """() => { const n = performance.getEntriesByType('navigation')[0];
                           return n ? {status: n.responseStatus, redirects: n.redirectCount, name: n.name} : {}; }"""
            )
        except Exception:  # noqa: BLE001 — cross-context evaluation can fail on an error page
            pass
        result = {
            "clicked_href": clicked_href,
            "final_url": popup.url,
            "status": timing.get("status"),
            "redirected": (timing.get("redirects") or 0) > 0 if timing else None,
            "opened_new_tab": True,
        }
        popup.close()
        return result

    def current_url(self) -> str:
        return self.page.url

    def follow_card_link_in_place(self, title: str, timeout: float = 45.0) -> dict:
        """For a Same Tab card: clicks the external-link icon and waits for
        THIS tab to leave the Laws & Regulations page. Returns
        {clicked_href, final_url, new_tab_opened}."""
        card = self.page.locator(self.CARD).filter(
            has=self.page.locator(self.CARD_TITLE, has_text=title)
        ).first
        clicked_href = card.get_attribute("href") or ""
        context = self.page.context
        pages_before = len(context.pages)
        card.locator(self.CARD_EXT_ICON).click()
        try:
            wait_until(lambda: PUBLIC_PATH not in self.page.url, timeout=timeout, poll=0.25,
                       message="the current tab never left the Laws & Regulations page")
            self.page.wait_for_load_state("domcontentloaded", timeout=45000)
        except Exception:  # noqa: BLE001 — reported through final_url, asserted by the caller
            pass
        return {
            "clicked_href": clicked_href,
            "final_url": self.page.url,
            "new_tab_opened": len(context.pages) > pages_before,
        }

    def go_back(self) -> str:
        """Browser Back; waits for the Laws & Regulations grid when Back
        lands on it. Returns the URL Back landed on."""
        self.page.go_back(wait_until="domcontentloaded", timeout=60000)
        if PUBLIC_PATH in self.page.url:
            self._wait_for_cards()
        return self.page.url

    def delivered_entries(self) -> list[dict]:
        """The entries in the lawregulations response THIS page load fetched
        (observed, not a separate API call): [{title, display_order, active}]."""
        try:
            items = json.loads(self.api_body or "{}").get("items", [])
        except ValueError:
            return []
        return [
            {"title": (i.get("lawTitle") or "").strip(),
             "display_order": i.get("displayOrder"),
             "active": bool(i.get("activeStatus"))}
            for i in items
        ]

    def new_console_errors(self, since: int = 0) -> list[str]:
        return [
            e for e in self.console_errors[since:]
            if not any(noise in e for noise in BASELINE_CONSOLE_NOISE)
        ]

"""
web/pages/visas_immigration/visas_immigration_page.py — VisasImmigrationPage.

Public Page Object for the Business Gateway "Visas & Immigration" page (PBI
130701): `/web/qatar-chamber/visas-immigration` (EN) and
`/ar/web/qatar-chamber/visas-immigration` (AR, dir=rtl).

Read live 2026-10-06 off the rendered DOM (anonymous context). The fragment
builds everything client-side from the seven BG objects after load, so every
read waits for `.qc-visas` to become visible (`root.hidden=false` is set only
once the data rendered; the root stays hidden when the BG Info Page is
missing / not approved — `is_rendered()` False).

Structure: hero (eyebrow / h1 title / description / hero image) -> rows
(`.qc-visas-row`, one per active section in displayOrder; the
`official-sources` section is NESTED as a `.qc-visas-block` inside the
previous article) -> page-foot disclaimer. Inside an article: section eyebrow,
h2 title, `.qc-visas-prose` body, `.qc-visas-checks` checklist, sub-topic
blocks (`.qc-visas-block` > h3 + prose or checks), source links
(`a.qc-visas-src`). The rail holds either the supporting photo or the
highlight card (`.qc-visas-card`, pills `.qc-visas-pill-label`).

Use in a FRESH unauthenticated context for any "visible to visitors"
assertion: signed-in staff also see drafts here (qc-object-preview.js).
"""

from config.settings import web_url
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.base_page import BasePage

PUBLIC_PATH = "/web/qatar-chamber/visas-immigration"

ROOT = ".qc-visas"
ROOT_READY = '.qc-visas[data-qc-visas-ready="true"]'
CRUMB = "a.qc-visas-crumb"
EYEBROW = "[data-qc-visas-eyebrow]"
TITLE = "[data-qc-visas-title]"
DESCRIPTION = "[data-qc-visas-desc]"
HERO_IMG = "[data-qc-visas-hero-img]"
SECTIONS = "[data-qc-visas-sections]"
ROW = ".qc-visas-row"
ARTICLE = ".qc-visas-article"
SEC_EYEBROW = ".qc-visas-sec-eyebrow"
SEC_TITLE = ".qc-visas-sec-title"
PROSE = ".qc-visas-prose"
CHECKS = ".qc-visas-checks"
CHECK_LABEL = ".qc-visas-check-label"
BLOCK = ".qc-visas-block"
BLOCK_HEAD = ".qc-visas-block-head"
PHOTO_IMG = "img.qc-visas-photo-img"
CARD = ".qc-visas-card"
CARD_EYEBROW = ".qc-visas-card-eyebrow"
CARD_TITLE = ".qc-visas-card-title"
PILL_LABEL = ".qc-visas-pill-label"
SOURCE_LINK = "a.qc-visas-src"
SOURCE_TITLE = ".qc-visas-src-title"
SOURCE_DESC = ".qc-visas-src-desc"
DISCLAIMER = "[data-qc-visas-disclaimer]"

# One JS read of the whole rendered model — cheaper and race-free compared
# with dozens of locator round-trips.
_MODEL_JS = r"""() => {
  const root = document.querySelector('.qc-visas');
  if (!root) return null;
  const txt = (n) => n ? n.innerText.trim() : '';
  const block = (b) => ({
    heading: txt(b.querySelector('.qc-visas-block-head')),
    style: b.querySelector('.qc-visas-checks') ? 'checklist' : (b.querySelector('.qc-visas-prose') ? 'paragraph' : ''),
    lines: [...b.querySelectorAll('.qc-visas-check-label')].map(txt),
    prose: txt(b.querySelector('.qc-visas-prose')),
    html: (b.querySelector('.qc-visas-prose') || {}).innerHTML || '',
    links: [...b.querySelectorAll('a.qc-visas-src')].map(a => ({title: txt(a.querySelector('.qc-visas-src-title')),
             desc: txt(a.querySelector('.qc-visas-src-desc')), href: a.getAttribute('href'), target: a.getAttribute('target') || '',
             rel: a.getAttribute('rel') || ''}))});
  const rows = [...root.querySelectorAll('.qc-visas-row')].map(r => {
    const art = r.querySelector('.qc-visas-article');
    const direct = (sel) => [...art.children].filter(c => c.matches(sel));
    const head = art.querySelector('.qc-visas-sec-head');
    const card = r.querySelector('.qc-visas-card');
    const photo = r.querySelector('img.qc-visas-photo-img');
    const intro = art.querySelector(':scope > .qc-visas-prose, :scope > .qc-visas-sec-split > .qc-visas-prose');
    const checks = direct('.qc-visas-checks')[0];
    return {
      eyebrow: txt(head && head.querySelector('.qc-visas-sec-eyebrow')),
      title: txt(head && head.querySelector('.qc-visas-sec-title')),
      body: txt(intro), body_html: intro ? intro.innerHTML : '',
      checklist: checks ? [...checks.querySelectorAll('.qc-visas-check-label')].map(txt) : [],
      blocks: direct('.qc-visas-block').map(block),
      links: direct('.qc-visas-srcs').flatMap(s => [...s.querySelectorAll('a.qc-visas-src')]).map(a => ({
             title: txt(a.querySelector('.qc-visas-src-title')), desc: txt(a.querySelector('.qc-visas-src-desc')),
             href: a.getAttribute('href'), target: a.getAttribute('target') || '', rel: a.getAttribute('rel') || ''})),
      photo: photo ? {src: photo.getAttribute('src'), alt: photo.getAttribute('alt')} : null,
      card: card ? {eyebrow: txt(card.querySelector('.qc-visas-card-eyebrow')), heading: txt(card.querySelector('.qc-visas-card-title')),
                    pills: [...card.querySelectorAll('.qc-visas-pill-label')].map(txt)} : null,
      full: r.classList.contains('is-full')};
  });
  const disc = root.querySelector('[data-qc-visas-disclaimer]');
  const hero = root.querySelector('[data-qc-visas-hero-img]');
  return {hidden: root.hidden, dir: root.dir, ready: root.getAttribute('data-qc-visas-ready'),
          page_key: root.getAttribute('data-qc-visas-page-key'),
          crumbs: [...root.querySelectorAll('a.qc-visas-crumb')].map(txt),
          eyebrow: txt(root.querySelector('[data-qc-visas-eyebrow]')), title: txt(root.querySelector('[data-qc-visas-title]')),
          description: txt(root.querySelector('[data-qc-visas-desc]')),
          description_html: (root.querySelector('[data-qc-visas-desc]') || {}).innerHTML || '',
          hero_img: hero && !hero.hidden ? hero.getAttribute('src') : '',
          rows, disclaimer: disc && !disc.hidden ? txt(disc) : '',
          disclaimer_html: disc && !disc.hidden ? disc.innerHTML : ''};
}"""


class VisasImmigrationPage(BasePage):
    """Public Visas & Immigration page (EN / AR)."""

    def open_page(self, locale: str = "en", query: str = "") -> "VisasImmigrationPage":
        url = web_url(PUBLIC_PATH, locale=locale) + (f"?{query}" if query else "")
        self.open(url)
        self.page.locator(ROOT_READY).first.wait_for(state="attached", timeout=30000)
        self.wait_settled()
        return self

    def wait_settled(self, timeout: float = 20.0) -> None:
        """Until the fragment has either rendered rows or hidden itself."""
        def _settled() -> bool:
            model = self.model()
            return bool(model) and (model["hidden"] or bool(model["title"]))

        try:
            wait_until(_settled, timeout=timeout, poll=0.5)
        except WaitTimeoutError:
            pass

    def model(self) -> dict | None:
        return self.page.evaluate(_MODEL_JS)

    def is_rendered(self) -> bool:
        model = self.model()
        return bool(model) and not model["hidden"]

    # ---- convenience reads ---------------------------------------------------
    def section_titles(self) -> list[str]:
        """Rendered row titles in order (nested sections are blocks, see nested_block_headings)."""
        return [r["title"] for r in (self.model() or {}).get("rows", [])]

    def row_by_title(self, title: str) -> dict | None:
        for row in (self.model() or {}).get("rows", []):
            if row["title"] == title:
                return row
        return None

    def all_block_headings(self) -> list[str]:
        return [b["heading"] for r in (self.model() or {}).get("rows", []) for b in r["blocks"]]

    def all_links(self) -> list[dict]:
        out = []
        for row in (self.model() or {}).get("rows", []):
            out += row["links"]
            for b in row["blocks"]:
                out += b["links"]
        return out

    def body_text(self) -> str:
        return self.page.locator(ROOT).first.inner_text()

    def poll_until(self, predicate, timeout: float = 30.0, reload: bool = True, locale: str = "en") -> bool:
        """Re-opens the page until `predicate(model)` holds (publish propagation)."""
        def _check() -> bool:
            if reload:
                self.open_page(locale)
            model = self.model()
            return bool(model) and bool(predicate(model))

        try:
            wait_until(_check, timeout=timeout, poll=3.0)
            return True
        except WaitTimeoutError:
            return False

    def layout_report(self) -> dict:
        """Horizontal-overflow / clipped-text evidence for char-limit checks."""
        return self.page.evaluate(
            """() => {
              const doc = document.documentElement;
              const root = document.querySelector('.qc-visas');
              const clipped = [...(root ? root.querySelectorAll('h1,h2,h3,p,span,a,li,div') : [])]
                .filter(n => n.children.length === 0 && n.innerText && n.innerText.trim()
                             && (n.scrollWidth > n.clientWidth + 1) && getComputedStyle(n).overflow !== 'visible')
                .slice(0, 20).map(n => ({cls: n.className, text: n.innerText.slice(0, 80)}));
              return {scroll_width: doc.scrollWidth, client_width: doc.clientWidth,
                      horizontal_scroll: doc.scrollWidth > doc.clientWidth + 1, clipped};
            }""")

    # --- A ---
    # Workflow-case reads (Agent A). Read-only.
    def http_status(self) -> int:
        """HTTP status of the current document's navigation (Chromium)."""
        return int(self.page.evaluate(
            "() => { const n = performance.getEntriesByType('navigation')[0]; return n ? (n.responseStatus || 0) : 0; }"))

    def headings_in_order(self) -> list[str]:
        """Section titles (h2) and block / nested-section headings (h3) in document order."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('.qc-visas .qc-visas-sec-title, .qc-visas .qc-visas-block-head')]
                     .map(n => n.innerText.trim())""")

    def _style(self, selector: str, text: str) -> dict:
        return self.page.evaluate(
            """([sel, text]) => { const n = [...document.querySelectorAll(sel)].find(e => e.innerText.trim() === text);
                 if (!n) return null; const s = getComputedStyle(n);
                 return {fontFamily: s.fontFamily, fontSize: s.fontSize, fontWeight: s.fontWeight, color: s.color}; }""",
            [selector, text])

    def block_heading_style(self, heading: str) -> dict | None:
        return self._style(f"{ROOT} {BLOCK_HEAD}", heading)

    def source_title_style(self, title: str) -> dict | None:
        return self._style(f"{ROOT} {SOURCE_TITLE}", title)

    def source_desc_style(self, description: str) -> dict | None:
        return self._style(f"{ROOT} {SOURCE_DESC}", description)

    def links_to_page(self) -> list[dict]:
        """Every anchor OUTSIDE the fragment (header / nav / footer) pointing at this page."""
        return self.page.evaluate(
            """(path) => [...document.querySelectorAll('a[href]')].filter(a => !a.closest('.qc-visas')
                 && a.getAttribute('href').includes(path)).map(a => ({text: a.innerText.trim(), href: a.getAttribute('href')}))""",
            "visas-immigration")

    def open_raw(self, url: str) -> int:
        """Plain navigation with NO session guard / re-login (for unauthenticated
        probes: BasePage.open() may sign the admin back in). Returns the HTTP status."""
        response = self.page.goto(url, wait_until="domcontentloaded")
        return response.status if response else 0

    def document_text(self) -> str:
        return self.page.locator("body").inner_text()

    def current_url(self) -> str:
        return self.page.url

    def is_signed_in(self) -> bool:
        return bool(self.page.evaluate(
            "() => !!(window.Liferay && Liferay.ThemeDisplay && Liferay.ThemeDisplay.isSignedIn())"))

    def button_count(self, name: str) -> int:
        return self.page.get_by_role("button", name=name).count()

    def a_evidence(self, folder: str, name: str, full_page: bool = True) -> str:
        """PNG under `folder` (+ Allure attachment); returns the path."""
        import os
        import re
        from core.utils.reporting import attach_screenshot
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        png = self.page.screenshot(path=path, full_page=full_page)
        attach_screenshot(png, name, "visas_immigration")
        return path


# --- C ---
# Agent C (checklist items, highlight card / items, sub-topic blocks): scoped
# reads of ONE row (found by its exact h2 section title) — styles, raw markup.
_C_ROW_JS = r"""(title) => [...document.querySelectorAll('.qc-visas-row')].find(r => {
    const h = r.querySelector('.qc-visas-sec-title'); return h && h.innerText.trim() === title; })"""

_C_STYLES_JS = r"""([title, sel]) => {
  const row = (""" + _C_ROW_JS + r""")(title);
  if (!row) return null;
  return [...row.querySelectorAll(sel)].map(n => { const c = getComputedStyle(n); const r = n.getBoundingClientRect();
    return {text: n.innerText.trim(), raw: n.textContent, tag: n.tagName.toLowerCase(), font_family: c.fontFamily,
            font_size: c.fontSize, font_weight: c.fontWeight, color: c.color, background_color: c.backgroundColor,
            background_image: c.backgroundImage, width: Math.round(r.width * 10) / 10, direction: c.direction,
            text_align: c.textAlign, overflow: c.overflow, text_overflow: c.textOverflow, white_space: c.whiteSpace,
            scroll_width: n.scrollWidth, client_width: n.clientWidth, list_style: c.listStyleType,
            left: Math.round(r.left), right: Math.round(r.right), viewport: window.innerWidth}; });
}"""

_C_MARKUP_JS = r"""(title) => {
  const row = (""" + _C_ROW_JS + r""")(title);
  if (!row) return null;
  const art = row.querySelector('.qc-visas-article');
  const checks = [...art.children].filter(c => c.matches('.qc-visas-checks'))[0];
  const card = row.querySelector('.qc-visas-card');
  const blocks = [...art.children].filter(c => c.matches('.qc-visas-block')).map(b => ({
      heading_raw: (b.querySelector('.qc-visas-block-head') || {}).textContent ?? null,
      heading: (b.querySelector('.qc-visas-block-head') || {innerText: ''}).innerText.trim(),
      html: b.innerHTML, ul: b.querySelectorAll('ul').length, li: b.querySelectorAll('li').length,
      check_rows: [...b.querySelectorAll('.qc-visas-check')].map(c => c.innerText.trim()),
      prose: [...b.querySelectorAll('.qc-visas-prose')].map(p => ({text: p.innerText.trim(), html: p.innerHTML})),
      check_disc: b.querySelectorAll('.qc-visas-check-disc').length}));
  return {
    rail: !!row.querySelector('.qc-visas-rail'), full: row.classList.contains('is-full'),
    checklist_rows: checks ? [...checks.querySelectorAll('.qc-visas-check')].map(c => ({
        text: c.innerText.trim(), html: (c.querySelector('.qc-visas-check-label') || {}).innerHTML || ''})) : [],
    card: card ? {html: card.innerHTML, has_pills: card.classList.contains('has-pills'),
        eyebrow_nodes: [...card.querySelectorAll('.qc-visas-card-eyebrow')].map(n => n.textContent),
        heading_nodes: [...card.querySelectorAll('.qc-visas-card-title')].map(n => n.textContent),
        pill_nodes: [...card.querySelectorAll('.qc-visas-pill-label')].map(n => n.textContent)} : null,
    blocks};
}"""

_C_CHIP_JS = r"""([title, text]) => {
  const row = (""" + _C_ROW_JS + r""")(title);
  if (!row) return null;
  const label = [...row.querySelectorAll('.qc-visas-pill-label')].find(n => n.innerText.trim() === text);
  if (!label) return null;
  const out = [];
  for (let n = label, i = 0; n && i < 3; n = n.parentElement, i++) {
    const c = getComputedStyle(n); const r = n.getBoundingClientRect();
    out.push({cls: n.className, background_color: c.backgroundColor, background_image: c.backgroundImage,
              width: Math.round(r.width * 10) / 10});
  }
  return out;
}"""


class VisasPublicViewC(VisasImmigrationPage):
    """Agent C reads of one QCTEST row on the public page."""

    def c_styles(self, row_title: str, selector: str) -> list[dict] | None:
        """Computed style + box of every `selector` match inside the row titled `row_title`."""
        return self.page.evaluate(_C_STYLES_JS, [row_title, selector])

    def c_markup(self, row_title: str) -> dict | None:
        """Raw structure of the row: article checklist rows, card nodes, sub-topic blocks."""
        return self.page.evaluate(_C_MARKUP_JS, row_title)

    def c_chip_chain(self, row_title: str, pill_text: str) -> list[dict] | None:
        """Background / width of a pill label and its two ancestors (chip fill evidence)."""
        return self.page.evaluate(_C_CHIP_JS, [row_title, pill_text])

    def c_poll_row(self, row_title: str, predicate, timeout: float, locale: str = "en") -> tuple[bool, float]:
        """Re-opens the page until the row exists and `predicate(row_model)` holds.
        Returns (ok, seconds until it held / until timeout)."""
        import time as _time  # noqa: PLC0415 — monotonic clock for the budget only
        started = _time.monotonic()
        state = {"at": 0.0}

        def _check() -> bool:
            self.open_page(locale)
            row = self.row_by_title(row_title)
            if row is not None and predicate(row):
                state["at"] = _time.monotonic() - started
                return True
            return False

        try:
            wait_until(_check, timeout=timeout, poll=0.5)
            return True, state["at"]
        except WaitTimeoutError:
            return False, _time.monotonic() - started

    def c_evidence(self, path: str, full_page: bool = True) -> str:
        import os as _os  # noqa: PLC0415
        _os.makedirs(_os.path.dirname(path), exist_ok=True)
        try:
            self.page.screenshot(path=path, full_page=full_page)
        except Exception:  # noqa: BLE001 — evidence only
            return ""
        return path


# --- D ---
# Agent D (supporting image + alt, official source links, checklist order /
# Active Status, Arabic overview card): scoped reads of ONE row found by its
# exact h2 section title, plus link-click outcomes. Read-only except clicks.
_D_ROW_JS = r"""(title) => {
  const row = [...document.querySelectorAll('.qc-visas-row')].find(r => {
      const h = r.querySelector('.qc-visas-sec-title'); return h && h.innerText.trim() === title; });
  if (!row) return null;
  const st = (n) => { if (!n) return null; const c = getComputedStyle(n); const r = n.getBoundingClientRect();
      return {text: n.innerText.trim(), font_family: c.fontFamily, font_size: c.fontSize, font_weight: c.fontWeight,
              color: c.color, background_color: c.backgroundColor, text_align: c.textAlign, direction: c.direction,
              width: Math.round(r.width * 10) / 10, height: Math.round(r.height * 10) / 10, x: Math.round(r.x), y: Math.round(r.y),
              right: Math.round(r.right), scroll_width: n.scrollWidth, client_width: n.clientWidth,
              overflow: c.overflow, text_overflow: c.textOverflow, white_space: c.whiteSpace}; };
  const art = row.querySelector('.qc-visas-article');
  const rail = row.querySelector('.qc-visas-rail');
  const img = row.querySelector('img.qc-visas-photo-img');
  const checks = [...art.children].filter(c => c.matches('.qc-visas-checks'))[0];
  return {
    full: row.classList.contains('is-full'), rail: rail ? st(rail) : null, article: st(art),
    rail_children: rail ? [...rail.children].map(c => c.className) : [],
    photo: img ? {src: img.getAttribute('src'), alt: img.getAttribute('alt'), has_alt_attr: img.hasAttribute('alt'),
                  complete: img.complete, natural_w: img.naturalWidth, natural_h: img.naturalHeight,
                  object_fit: getComputedStyle(img).objectFit, box: st(img)} : null,
    imgs_in_row: row.querySelectorAll('img').length,
    checklist: checks ? [...checks.querySelectorAll('.qc-visas-check-label')].map(st) : [],
    blocks: [...art.children].filter(c => c.matches('.qc-visas-block')).map(b => ({
        heading: (b.querySelector('.qc-visas-block-head') || {innerText: ''}).innerText.trim(), box: st(b)})),
    links: [...row.querySelectorAll('a.qc-visas-src')].map(a => ({
        href: a.getAttribute('href'), target: a.getAttribute('target'), has_target: a.hasAttribute('target'),
        rel: a.getAttribute('rel') || '', anchor: st(a),
        title: st(a.querySelector('.qc-visas-src-title')), desc: st(a.querySelector('.qc-visas-src-desc')),
        desc_nodes: a.querySelectorAll('.qc-visas-src-desc').length,
        empty_children: [...a.querySelectorAll('.qc-visas-src-copy > *')].filter(n => !n.innerText.trim()).length})),
    empty_href_anchors: [...row.querySelectorAll('a')].filter(a => !(a.getAttribute('href') || '').trim()
                                                                  || a.getAttribute('href') === '#').length,
    blank_anchors: [...row.querySelectorAll('a.qc-visas-src')].filter(a => !a.innerText.trim()).length};
}"""

_D_CARD_JS = r"""(index) => {
  const rows = [...document.querySelectorAll('.qc-visas-row')];
  const row = rows[index]; if (!row) return null;
  const st = (n) => { if (!n) return null; const c = getComputedStyle(n); const r = n.getBoundingClientRect();
      return {text: n.innerText.trim(), font_family: c.fontFamily, font_size: c.fontSize, font_weight: c.fontWeight,
              color: c.color, background_color: c.backgroundColor, background_image: c.backgroundImage,
              x: Math.round(r.x), right: Math.round(r.right), width: Math.round(r.width)}; };
  const card = row.querySelector('.qc-visas-card');
  const checks = row.querySelector('.qc-visas-checks');
  return {title: (row.querySelector('.qc-visas-sec-title') || {innerText: ''}).innerText.trim(),
          card: st(card), eyebrow: st(row.querySelector('.qc-visas-card-eyebrow')),
          heading: st(row.querySelector('.qc-visas-card-title')),
          pills: [...row.querySelectorAll('.qc-visas-pill-label')].map(st), checks: st(checks),
          article: st(row.querySelector('.qc-visas-article'))};
}"""


class VisasPublicViewD(VisasImmigrationPage):
    """Agent D reads of one row on the public page (use a FRESH anonymous context)."""

    def d_row(self, row_title: str) -> dict | None:
        return self.page.evaluate(_D_ROW_JS, row_title)

    def d_row_card(self, index: int) -> dict | None:
        """Highlight-card styles of the rendered row at `index` (0-based, real rows first)."""
        return self.page.evaluate(_D_CARD_JS, index)

    def d_poll_row(self, row_title: str, predicate, timeout: float, locale: str = "en") -> tuple:
        """Re-opens the page until the row exists and `predicate(d_row)` holds.
        Returns (ok, seconds until it held / until timeout, last row read)."""
        import time as _time  # noqa: PLC0415 — monotonic clock for the budget only
        started = _time.monotonic()
        state = {"at": 0.0, "row": None}

        def _check() -> bool:
            self.open_page(locale)
            state["row"] = self.d_row(row_title)
            if state["row"] is not None and predicate(state["row"]):
                state["at"] = _time.monotonic() - started
                return True
            return False

        try:
            wait_until(_check, timeout=timeout, poll=0.5)
            return True, state["at"], state["row"]
        except WaitTimeoutError:
            return False, _time.monotonic() - started, state["row"]

    def d_scroll_photo_into_view(self, row_title: str) -> dict | None:
        """Scrolls the row's lazy photo into view and waits for it to finish loading."""
        img = self.page.locator(f'{ROW}:has({SEC_TITLE}:text-is("{row_title}")) {PHOTO_IMG}').first
        if img.count() == 0:
            return self.d_row(row_title)
        img.scroll_into_view_if_needed()
        try:
            wait_until(lambda: bool(img.evaluate("i => i.complete && i.naturalWidth > 0")), timeout=15.0, poll=0.5)
        except WaitTimeoutError:
            pass
        return self.d_row(row_title)

    def d_fetch_status(self, src: str) -> dict:
        """GET of a page-relative asset through this (anonymous) context: {url, status, content_type, bytes}."""
        from urllib.parse import urljoin  # noqa: PLC0415
        url = urljoin(self.page.url, src)
        response = self.page.context.request.get(url)
        body = response.body()
        return {"url": url, "status": response.status, "content_type": response.headers.get("content-type", ""),
                "bytes": len(body)}

    def d_page_html(self) -> str:
        return self.page.content()

    def d_click_link(self, row_title: str, link_title: str, timeout_ms: int = 30000) -> dict:
        """Clicks the source link titled `link_title` in the row and reports
        {tabs_before, tabs_after, nav_request_url, current_url, popup_request_url,
        popup_url}. Same tab: the first main-frame navigation request; new tab:
        the popup's first navigation request."""
        link = self.page.locator(f'{ROW}:has({SEC_TITLE}:text-is("{row_title}")) {SOURCE_LINK}'
                                 f':has({SOURCE_TITLE}:text-is("{link_title}"))').first
        link.scroll_into_view_if_needed()
        context = self.page.context
        before_url = self.page.url
        out = {"tabs_before": len(context.pages), "nav_request_url": "", "popup_request_url": "", "popup_url": ""}
        nav_requests: list = []
        popups: list = []

        def _on_request(request):
            try:
                if request.is_navigation_request() and request.frame == self.page.main_frame:
                    nav_requests.append(request.url)
            except Exception:  # noqa: BLE001
                pass

        def _on_page(new_page):
            popups.append(new_page)

        all_nav: list = []

        def _on_ctx_request(request):
            try:
                if request.is_navigation_request():
                    all_nav.append(request.url)
            except Exception:  # noqa: BLE001
                pass

        self.page.on("request", _on_request)
        context.on("page", _on_page)
        context.on("request", _on_ctx_request)
        try:
            # Sync Playwright only dispatches events inside its own calls, so wait
            # for the popup with expect_page (it pumps events), not with a sleep loop.
            popup = None
            try:
                with context.expect_page(timeout=8000) as info:
                    link.click()
                popup = info.value
            except Exception as exc:  # noqa: BLE001 — no new tab within 8 s: same-tab navigation
                popup = None
                out["popup_wait"] = repr(exc)[:300]
            if popup is not None:
                try:
                    popup.wait_for_url(lambda u: u.startswith("http"), wait_until="commit", timeout=timeout_ms)
                except Exception:  # noqa: BLE001 — external site may be unreachable (chrome-error page)
                    pass
                out["popup_url"] = popup.url
                others = [u for u in all_nav if u not in nav_requests]
                out["popup_request_url"] = others[0] if others else ""
            else:
                try:
                    self.page.wait_for_url(lambda u: u != before_url, wait_until="commit", timeout=timeout_ms)
                except Exception:  # noqa: BLE001
                    pass
        finally:
            self.page.remove_listener("request", _on_request)
            context.remove_listener("page", _on_page)
            context.remove_listener("request", _on_ctx_request)
        out["nav_request_url"] = nav_requests[0] if nav_requests else ""
        out["tabs_after"] = len(context.pages)
        out["current_url"] = self.page.url
        return out

    def d_evidence(self, folder: str, name: str, full_page: bool = True) -> str:
        """PNG under `folder` (+ Allure attachment); returns the path ("" on failure)."""
        import os as _os  # noqa: PLC0415
        import re as _re  # noqa: PLC0415
        _os.makedirs(folder, exist_ok=True)
        path = _os.path.join(folder, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "visas_immigration")
        except Exception:  # noqa: BLE001 — evidence only
            return ""
        return path


# --- B ---
# Agent B (hero eyebrow / title / description / banner, section eyebrow /
# title / body, page-foot disclaimer): computed style + box + overflow of one
# element, hero image facts, rich-text markup, budgeted publish polling.
_B_EL_JS = r"""([sel, title]) => {
  let scope = document;
  if (title) {
    scope = [...document.querySelectorAll('.qc-visas-row')].find(r => {
      const h = r.querySelector('.qc-visas-sec-title'); return h && h.innerText.trim() === title; });
    if (!scope) return null;
  }
  const n = scope.querySelector(sel);
  if (!n) return null;
  const c = getComputedStyle(n); const r = n.getBoundingClientRect();
  return {text: n.innerText.trim(), raw: n.textContent, hidden: n.hidden || c.display === 'none',
          font_family: c.fontFamily, font_size: c.fontSize, font_weight: c.fontWeight, color: c.color,
          width: Math.round(r.width * 10) / 10, height: Math.round(r.height), top: Math.round(r.top + window.scrollY),
          left: Math.round(r.left), right: Math.round(r.right), direction: c.direction, text_align: c.textAlign,
          overflow: c.overflow, text_overflow: c.textOverflow, white_space: c.whiteSpace,
          scroll_width: n.scrollWidth, client_width: n.clientWidth, viewport: window.innerWidth,
          html: n.innerHTML};
}"""

_B_MARKUP_JS = r"""([sel, title]) => {
  let scope = document;
  if (title) {
    scope = [...document.querySelectorAll('.qc-visas-row')].find(r => {
      const h = r.querySelector('.qc-visas-sec-title'); return h && h.innerText.trim() === title; });
    if (!scope) return null;
  }
  const n = scope.querySelector(sel);
  if (!n) return null;
  return {headings: [...n.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => ({tag: h.tagName.toLowerCase(), text: h.innerText.trim()})),
          lists: [...n.querySelectorAll('ul')].map(u => [...u.querySelectorAll(':scope > li')].map(li => li.innerText.trim())),
          anchors: [...n.querySelectorAll('a')].map(a => ({text: a.innerText.trim(), href: a.getAttribute('href')})),
          paragraphs: [...n.querySelectorAll('p')].map(p => p.innerText.trim()),
          text: n.innerText, html: n.innerHTML};
}"""


class VisasPublicViewB(VisasImmigrationPage):
    """Agent B reads (anonymous context)."""

    def b_el(self, selector: str, row_title: str = "") -> dict | None:
        """Style/box/overflow of the first `selector` match (inside the row titled `row_title` if given)."""
        return self.page.evaluate(_B_EL_JS, [selector, row_title])

    def b_markup(self, selector: str, row_title: str = "") -> dict | None:
        return self.page.evaluate(_B_MARKUP_JS, [selector, row_title])

    def b_hero_img(self) -> dict | None:
        return self.page.evaluate(
            """() => { const i = document.querySelector('[data-qc-visas-hero-img]'); if (!i || i.hidden) return null;
                 const c = getComputedStyle(i); const r = i.getBoundingClientRect();
                 return {src: i.getAttribute('src'), alt: i.getAttribute('alt'), complete: i.complete,
                         natural_w: i.naturalWidth, natural_h: i.naturalHeight, w: Math.round(r.width), h: Math.round(r.height),
                         object_fit: c.objectFit}; }""")

    def b_scroll_hero_into_view(self) -> None:
        self.page.locator(HERO_IMG).first.scroll_into_view_if_needed()

    def b_fetch_status(self, src: str) -> dict:
        from urllib.parse import urljoin  # noqa: PLC0415
        url = urljoin(self.page.url, src)
        response = self.page.context.request.get(url)
        return {"url": url, "status": response.status, "content_type": response.headers.get("content-type", ""),
                "bytes": len(response.body())}

    def b_source_links_bottom(self) -> int:
        """Document Y of the bottom edge of the last official-source link (0 = none)."""
        return int(self.page.evaluate(
            """() => { const a = [...document.querySelectorAll('.qc-visas a.qc-visas-src')];
                 if (!a.length) return 0; const r = a[a.length - 1].getBoundingClientRect();
                 return Math.round(r.bottom + window.scrollY); }"""))

    def b_poll(self, predicate, budget_s: float = 5.0, grace_s: float = 40.0, locale: str = "en") -> dict:
        """Re-opens the page until `predicate(model)` holds. Returns {ok, seen_at
        (start of the first successful poll, seconds), within_budget}."""
        import time as _time  # noqa: PLC0415 — monotonic clock for the budget only
        started = _time.monotonic()
        state = {"seen_at": None}

        def _check() -> bool:
            poll_start = _time.monotonic() - started
            self.open_page(locale)
            model = self.model()
            if model and predicate(model):
                state["seen_at"] = round(poll_start, 1)
                return True
            return False

        try:
            wait_until(_check, timeout=budget_s + grace_s, poll=0.5)
        except WaitTimeoutError:
            pass
        seen = state["seen_at"]
        return {"ok": seen is not None, "seen_at": seen, "within_budget": seen is not None and seen <= budget_s}

    def b_evidence(self, folder: str, name: str, full_page: bool = True) -> str:
        import os as _os  # noqa: PLC0415
        import re as _re  # noqa: PLC0415
        _os.makedirs(folder, exist_ok=True)
        path = _os.path.join(folder, _re.sub(r"[^\w.-]+", "_", name)[:120] + ".png")
        try:
            png = self.page.screenshot(path=path, full_page=full_page)
            from core.utils.reporting import attach_screenshot  # noqa: PLC0415
            attach_screenshot(png, name, "visas_immigration")
        except Exception:  # noqa: BLE001 — evidence only
            return ""
        return path

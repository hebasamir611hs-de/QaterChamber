"""
web/pages/home_latest_news/home_latest_news_page.py — HomeLatestNewsPage.

PBI 129372 / QC-HOME-004A "Latest News Section" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 7 approved, Automation-tagged, UI-category,
Web-platform cases scoped for this batch (ADO TC 135317, 135318, 135319,
135320, 135321, 135322, 135323); Control_Panel-tagged cases for this same
PBI are explicit out-of-scope for this run and are NOT touched here (see the
sibling home_latest_news_admin_page.py skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "news"
    -> 0 candidates

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home \
        --scope "section.qc-home-latest-news"
    -> [role] uniq=1  get_by_role("link", name="Qatari-Saudi Cooperation ...")
    -> [role] uniq=1  get_by_role("link", name="Qatar Chamber Explores Relations ...")
    -> [role] uniq=3  get_by_role("link", name="View All")             NON-UNIQUE (3)
    -> [role] uniq=0  get_by_role("link", name="Qatar Chamber Concludes Training ...") NON-UNIQUE (0)

The harvester's SEL list (a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable]) surfaces each card only as one
big `<a>` whose accessible name concatenates title+date+views (no way to
select the thumbnail/date/title/view-count as four distinct elements from
this list), and "View All" is non-unique because BOTH viewall variants
(--top / --bottom, only one visible per breakpoint) and Qatar Chamber's own
site-wide "View All" wording elsewhere match the same role/name query. This
is the documented "ambiguous element" fallback condition in
automation-standards.md's Tooling-priority table, resolved the same way
every sibling Page Object in this tree resolves it: additional, disclosed,
scoped Playwright scripts (still CLI/shell, never the Playwright MCP) that
reused BasePage's own license-gate/overlay guard sequence before reading the
live DOM structurally.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home, 1920x1080):

    section.qc-home-latest-news                                   (SECTION)
      div.qc-ln-inner
        div.qc-ln-head[display:flex, justify-content:space-between]  (HEAD)
          div.qc-ln-head-text
            span.qc-ln-tag           "Latest News"                   (TAG)
            h2.qc-ln-heading         "Stay Connected & Informed"     (HEADING)
            p.qc-ln-desc             "Stay informed with the latest  (DESCRIPTION)
                                       developments in Qatar's business
                                       landscape, upcoming chamber
                                       initiatives, and official economic
                                       updates."
          a.qc-ln-viewall.qc-ln-viewall--top   "View All"             (VIEW_ALL_TOP)
        div.qc-ln-grid[display:grid]                                  (GRID)
          a.qc-ln-card (x3, one per published article)                (CARD)
            div.qc-ln-card-media
              img.qc-ln-card-img[alt]                                 (CARD_IMAGE, relative)
            div.qc-ln-card-body
              h3.qc-ln-card-title    e.g. "Qatari-Saudi Cooperation    (CARD_TITLE, relative)
                                       in the Field of Maritime
                                       Transport and Shipping Discussed"
              div.qc-ln-card-meta
                span.qc-ln-meta-item (x2, ALWAYS in this fixed order — (CARD_META_ITEM, relative)
                    nth(0): calendar-icon svg + span.qc-ln-meta-text    confirmed live across
                            e.g. "Mar 3, 2026"           (the DATE)     all 3 cards, both
                    nth(1): eye-icon svg + span.qc-ln-meta-text         languages)
                            e.g. "2,869"                 (the VIEW COUNT)
        a.qc-ln-viewall.qc-ln-viewall--bottom  "View All"              (VIEW_ALL_BOTTOM)

Real, CLI-verified findings from this extraction pass (reported, not
silently corrected):
  - qcdev currently has exactly 3 published news articles live (both EN and
    AR render 3 `a.qc-ln-card` cards, same 3 articles, localized) — there is
    no "fewer than configured count" (e.g. exactly 2 published) state on
    qcdev today. TC 135323 needs that precise CMS precondition; Control_Panel
    /CMS content publishing is explicit out-of-scope for this Web-only batch
    (mirrors the identical situation already logged for PBI 129368's TC
    135176 in home_promo_banners_page.py) — scripted against real Page-Object
    methods below but SKIPPED with a concrete reason in the test module,
    never fabricated as an unobserved pass.
  - Responsive grid, measured live via getComputedStyle(.qc-ln-grid) and
    each card's bounding box (no CSS parsed from a <style> text-node — it
    lives in an unscoped page-wide <style> sibling, not inside the section,
    so live computed geometry was read directly instead):
      * 1920x1080 (desktop): gridTemplateColumns has 3 tracks (397px each);
        all 3 cards share one row (identical y=2176); no horizontal page
        overflow (scrollWidth == clientWidth == 1920).
      * 768x1024 (tablet): gridTemplateColumns has 2 tracks (354px each);
        3 cards reflow into 2 rows (cards 1-2 at y=2158, card 3 wraps to
        y=2474); no horizontal overflow (scrollWidth == clientWidth == 768).
      * 375x667 (mobile): gridTemplateColumns has 1 track (339px); all 3
        cards stack in one column, each its own row (y=2307/2612/2918); no
        horizontal overflow (scrollWidth == clientWidth == 375).
    Within a card at every breakpoint checked, the thumbnail/title/date/
    view-count boxes stack vertically with no overlap (e.g. desktop first
    card: image y=2176-2399, title y=2415-2461, meta y=2473-2488).
  - Two "View All" CTA variants exist, NOT one: `.qc-ln-viewall--top`
    (inside `.qc-ln-head`, next to the heading) and `.qc-ln-viewall--bottom`
    (below the card grid). Live visibility is breakpoint-driven: desktop and
    tablet show only `--top` (`--bottom` has zero width/height); mobile
    (375x667) shows only `--bottom` (`--top` has zero width/height) — this
    is exactly what keeps the CTA "reachable" per TC 135320 at a stacked
    mobile layout. Both point to the same href
    (`https://qcdev.ihorizons.com/web/qatar-chamber/news`).
  - CONFIRMED MISMATCH vs. TC 135321/135322's stated CTA alignment: `.qc-ln-
    head` is `display:flex; justify-content:space-between`, so the heading
    sits at the row's START and `.qc-ln-viewall--top` at the row's END. On
    the EN (LTR) page the CTA's bounding box is x=1463 of a 1920px viewport
    — the RIGHT half, not the "left-aligned" TC 135321 states. On the AR
    (RTL) page the row mirrors and the CTA's box is x=336 of 1920px — the
    LEFT half, not the "right-aligned" TC 135322 states (the heading/cards/
    tag/description all correctly mirror to the opposite side in RTL,
    confirmed live: heading x=944, cards x=1187/761/336 decreasing left).
    Scripted per each case's exact literal stated alignment regardless — a
    real, honestly-reported mismatch, not silently adjusted (mirrors the
    identical pattern already logged in header_component.py and
    home_promo_banners_page.py for other elements on this project).
  - EN and AR tag/heading/description text confirmed live and non-empty:
    EN — tag "Latest News", heading "Stay Connected & Informed", description
    "Stay informed with the latest developments in Qatar's business
    landscape, upcoming chamber initiatives, and official economic updates."
    AR — tag "آخر الأخبار", heading "ابقَ على تواصل واطلاع", description
    "ابقَ على اطلاع بآخر مستجدات بيئة الأعمال في قطر، ومبادرات الغرفة
    القادمة، والتحديثات الاقتصادية الرسمية." (CORRECTED 2026-10-07:
    read live again; the earlier "والتحديات" was a transcription typo) <html dir="rtl" lang="ar-SA"> and
    the section's own computed `direction: rtl` both confirmed live on AR;
    <html dir="ltr"> and computed `direction: ltr` confirmed live on EN.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeLatestNewsPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    HTML_ROOT = "html"
    SECTION = "section.qc-home-latest-news"
    HEAD = f"{SECTION} >> .qc-ln-head"
    TAG = f"{SECTION} >> .qc-ln-tag"
    HEADING = f"{SECTION} >> .qc-ln-heading"
    DESCRIPTION = f"{SECTION} >> .qc-ln-desc"
    GRID = f"{SECTION} >> .qc-ln-grid"
    CARD = f"{GRID} >> a.qc-ln-card"
    VIEW_ALL_TOP = f"{SECTION} >> .qc-ln-viewall--top"
    VIEW_ALL_BOTTOM = f"{SECTION} >> .qc-ln-viewall--bottom"
    # Relative selectors — always chained off a specific card Locator via
    # `.locator(...)`, never resolved standalone (all 3 cards share these
    # classes).
    CARD_IMAGE = "img.qc-ln-card-img"
    CARD_TITLE = ".qc-ln-card-title"
    CARD_META_ITEM = ".qc-ln-meta-item"
    CARD_META_TEXT = ".qc-ln-meta-text"

    # Borrowed placeholder budget — see HomePromoBannersPage's own note:
    # not independently re-measured for this content type, per
    # cms-profile.md's "re-probe before assuming it generalizes" caveat.
    RELOAD_POLL_TIMEOUT_MS = 5000
    RELOAD_POLL_INTERVAL_MS = 500

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeLatestNewsPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeLatestNewsPage":
        """Loads the homepage directly on the Arabic locale
        (`web_url("/home", locale="ar")` -> `/ar/home`) — mirrors the same
        sibling-Page-Object pattern already established elsewhere in this
        project (home_promo_banners_page.py, language_switcher_component.py)."""
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeLatestNewsPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    # ── Page/section-level direction ─────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    # ── Head text (tag / heading / description) ──────────────────────────
    def tag_text(self) -> str:
        return self.text(self.TAG).strip()

    def heading_text(self) -> str:
        return self.text(self.HEADING).strip()

    def description_text(self) -> str:
        return self.text(self.DESCRIPTION).strip()

    # ── Cards ─────────────────────────────────────────────────────────────
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def _card(self, index: int = 0):
        return self.page.locator(self.CARD).nth(index)

    def card_thumbnail_visible(self, index: int = 0) -> bool:
        try:
            return self._card(index).locator(self.CARD_IMAGE).is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's contract
            return False

    def card_title_text(self, index: int = 0) -> str:
        return self._card(index).locator(self.CARD_TITLE).inner_text().strip()

    def card_date_text(self, index: int = 0) -> str:
        items = self._card(index).locator(self.CARD_META_ITEM)
        return items.nth(0).locator(self.CARD_META_TEXT).inner_text().strip()

    def card_view_count_text(self, index: int = 0) -> str:
        items = self._card(index).locator(self.CARD_META_ITEM)
        return items.nth(1).locator(self.CARD_META_TEXT).inner_text().strip()

    def card_elements_all_visible(self, index: int = 0) -> bool:
        """True only if the card's thumbnail, title, date, and view-count
        are ALL visible — the four required elements TC 135317 checks."""
        card = self._card(index)
        try:
            return (
                card.locator(self.CARD_IMAGE).is_visible()
                and card.locator(self.CARD_TITLE).is_visible()
                and card.locator(self.CARD_META_ITEM).nth(0).is_visible()
                and card.locator(self.CARD_META_ITEM).nth(1).is_visible()
            )
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's contract
            return False

    def card_element_boxes(self, index: int = 0) -> dict:
        card = self._card(index)
        meta_items = card.locator(self.CARD_META_ITEM)
        return {
            "thumbnail": card.locator(self.CARD_IMAGE).bounding_box(),
            "title": card.locator(self.CARD_TITLE).bounding_box(),
            "date": meta_items.nth(0).bounding_box(),
            "views": meta_items.nth(1).bounding_box(),
        }

    @staticmethod
    def _boxes_overlap(a: dict, b: dict) -> bool:
        if not a or not b:
            return False
        return not (
            a["x"] + a["width"] <= b["x"]
            or b["x"] + b["width"] <= a["x"]
            or a["y"] + a["height"] <= b["y"]
            or b["y"] + b["height"] <= a["y"]
        )

    def card_elements_non_overlapping(self, index: int = 0) -> bool:
        """True if the thumbnail/title/date/view-count boxes within one
        card do not overlap each other — TC 135317's "non-overlapping"
        requirement."""
        boxes = self.card_element_boxes(index)
        keys = list(boxes.keys())
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                if self._boxes_overlap(boxes[keys[i]], boxes[keys[j]]):
                    return False
        return True

    def has_placeholder_cards(self) -> bool:
        """True if any rendered card slot is missing one of its four
        required elements — an empty/placeholder card filling an
        unpublished slot (TC 135323's "no placeholder/empty cards")."""
        for i in range(self.card_count()):
            if not self.card_elements_all_visible(i):
                return True
        return False

    # ── Grid layout / responsiveness ─────────────────────────────────────
    def card_boxes(self) -> list:
        cards = self.page.locator(self.CARD)
        boxes = []
        for i in range(cards.count()):
            box = cards.nth(i).bounding_box()
            if box:
                boxes.append(box)
        return boxes

    def cards_overlap(self) -> bool:
        boxes = self.card_boxes()
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if self._boxes_overlap(boxes[i], boxes[j]):
                    return True
        return False

    def grid_column_count(self) -> int:
        cols = self.page.locator(self.GRID).evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )
        return len([c for c in cols.strip().split(" ") if c])

    def cards_flow_direction(self) -> str:
        """"ltr" if card x-positions strictly increase left-to-right,
        "rtl" if they strictly decrease (a full mirror), else "mixed"."""
        xs = [b["x"] for b in self.card_boxes()]
        if len(xs) < 2:
            return "mixed"
        if all(xs[i] < xs[i + 1] for i in range(len(xs) - 1)):
            return "ltr"
        if all(xs[i] > xs[i + 1] for i in range(len(xs) - 1)):
            return "rtl"
        return "mixed"

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    # ── View All CTA ──────────────────────────────────────────────────────
    def is_view_all_top_visible(self) -> bool:
        return self.is_visible(self.VIEW_ALL_TOP)

    def is_view_all_bottom_visible(self) -> bool:
        return self.is_visible(self.VIEW_ALL_BOTTOM)

    def is_view_all_reachable(self) -> bool:
        """True if whichever View All CTA variant the current breakpoint
        shows (--top on desktop/tablet, --bottom on mobile — see docstring)
        is visible and carries a resolvable href, after scrolling it into
        view. TC 135320's "View All CTA remains reachable" requirement."""
        if self.is_view_all_top_visible():
            locator = self.VIEW_ALL_TOP
        elif self.is_view_all_bottom_visible():
            locator = self.VIEW_ALL_BOTTOM
        else:
            return False
        self.page.locator(locator).scroll_into_view_if_needed()
        return bool(self.page.locator(locator).get_attribute("href"))

    def _horizontal_half(self, x) -> str:
        viewport = self.page.viewport_size
        if x is None or not viewport:
            return "unknown"
        return "left_half" if x < viewport["width"] / 2 else "right_half"

    def view_all_top_horizontal_position(self) -> str:
        """"left_half" or "right_half" of the current viewport — see
        docstring for the confirmed live mismatch against TC 135321/135322's
        stated alignment."""
        box = self.page.locator(self.VIEW_ALL_TOP).bounding_box()
        return self._horizontal_half(box["x"] if box else None)

    # ── Navigation / ordering (added 2026-10-07, Phase 3) ──────────────────
    DETAIL_HEADING = ".qc-nd-heading"
    VIEW_ALL_HREF = "/web/qatar-chamber/news"

    def card_titles(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.CARD} {self.CARD_TITLE}").all_inner_texts()]

    def card_href(self, index: int = 0) -> str:
        return self._card(index).get_attribute("href") or ""

    def card_index_by_title(self, title: str) -> int:
        titles = self.card_titles()
        return titles.index(title) if title in titles else -1

    def card_dates(self) -> list:
        """Publication dates of every card, parsed from the EN meta text
        (e.g. "Sep 15, 2026"). Unparseable entries come back as None."""
        import datetime
        out = []
        for i in range(self.card_count()):
            raw = self.card_date_text(i)
            parsed = None
            for fmt in ("%b %d, %Y", "%B %d, %Y", "%d %b %Y", "%Y-%m-%d"):
                try:
                    parsed = datetime.datetime.strptime(raw, fmt).date()
                    break
                except ValueError:
                    continue
            out.append(parsed)
        return out

    def click_card(self, index: int = 0) -> None:
        card = self._card(index)
        card.scroll_into_view_if_needed()
        # force: the site-wide chatbot launcher can overlap the grid.
        card.click(force=True)
        self.page.wait_for_url("**news-article**", timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")

    def detail_heading_text(self, timeout_ms: int = 20000) -> str:
        loc = self.page.locator(self.DETAIL_HEADING).first
        loc.wait_for(state="visible", timeout=timeout_ms)
        return loc.inner_text().strip()

    def detail_image_srcs(self) -> list:
        return self.page.eval_on_selector_all("img", "els => els.map(e => e.currentSrc || e.src)")

    def detail_body_text(self) -> str:
        return self.page.locator("body").inner_text()

    def click_view_all_top(self) -> None:
        cta = self.page.locator(self.VIEW_ALL_TOP)
        cta.scroll_into_view_if_needed()
        cta.click(force=True)
        # The click starts a navigation; wait for the URL to change rather
        # than a load state the current page already satisfies (live
        # 2026-10-07: page.url still read /home right after the click).
        self.page.wait_for_url(f"**{self.VIEW_ALL_HREF}**", timeout=30000)
        self.page.wait_for_load_state("domcontentloaded")

    def view_all_count(self) -> int:
        return self.page.locator(f"{self.VIEW_ALL_TOP}, {self.VIEW_ALL_BOTTOM}").count()

    # Figma (REST, absoluteBoundingBox, read 2026-10-07): View All TEXT left
    # x inside a 1920-wide frame — EN 849:15904 -> 1519, AR 1188:10142 -> 346.
    FIGMA_VIEW_ALL_TEXT_X = {"en": 1519, "ar": 346}
    # The View All BUTTON (instance "Buttons/Button") in the same frames:
    # (left x, right x). EN 1499..1620, AR 300..435. This is the layout box
    # Rule 1's ±2 px applies to; the glyph start inside it moves with font
    # rasterisation (live EN text sits 3.3 px right of Figma's inside a
    # button that matches to 0.3 px), so it is not asserted.
    FIGMA_VIEW_ALL_BUTTON = {"en": (1499.0, 1620.0), "ar": (300.0, 435.0)}

    def view_all_box(self) -> tuple:
        box = self.page.locator(self.VIEW_ALL_TOP).bounding_box()
        return (box["x"], box["x"] + box["width"])

    def view_all_text_x(self) -> float:
        """Left x (viewport px) of the top View All label's own text glyphs,
        measured with a DOM Range so button padding is excluded."""
        return self.page.locator(self.VIEW_ALL_TOP).evaluate(
            """el => { const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT);
                let n; while ((n = w.nextNode())) { if (n.textContent.trim()) {
                  const r = document.createRange(); r.selectNodeContents(n);
                  const b = r.getBoundingClientRect(); if (b.width) return b.left; } }
                return el.getBoundingClientRect().left; }"""
        )

    def view_count_texts(self) -> list:
        return [self.card_view_count_text(i) for i in range(self.card_count())]

    # ── API-response shaping (added 2026-10-07, user order "execute every case") ──
    # The section is client-rendered from two guest headless-API calls (read
    # live from the fragment script 2026-10-07):
    #   /o/c/newsarticles/scopes/<gid>?filter=activeStatus eq true
    #       &sort=publicationDate:desc&pageSize=<fragment articleCount=3>
    #   /o/c/homelatestnewssections/scopes/<gid>?filter=activeStatus eq true&pageSize=1
    # and AC-8 hides View All when the configured viewAllUrl answers 404.
    # States that real shared data cannot be put in without touching real
    # records (0 or 2 articles, a non-first section record, an unpublished
    # listing page) are produced by reshaping THESE responses in the visitor's
    # own browser context only — the real fragment code still does all of the
    # rendering. Every test using this says so in its docstring/allure step.
    NEWS_API_GLOB = "**/o/c/newsarticles/**"
    SECTION_API_GLOB = "**/o/c/homelatestnewssections/**"

    def shape_news_items(self, transform) -> None:
        """Route the articles call: fetch the real response, then
        `transform(items) -> items` before the fragment sees it."""
        import json as _json

        def handler(route):
            resp = route.fetch()
            data = resp.json()
            data["items"] = transform(list(data.get("items", [])))
            data["totalCount"] = len(data["items"])
            route.fulfill(response=resp, json=data)

        self.page.route(self.NEWS_API_GLOB, handler)

    def _pick_by_marker(self, glob: str, marker: str, size_param: str) -> None:
        import json as _json
        import re as _re

        def handler(route):
            url = _re.sub(r"pageSize=\d+", "pageSize=100", route.request.url)
            resp = route.fetch(url=url)
            data = resp.json()
            mine = [i for i in data.get("items", []) if marker in _json.dumps(i, ensure_ascii=False)]
            data["items"] = mine[:1] if size_param == "1" else mine
            data["totalCount"] = len(data["items"])
            route.fulfill(response=resp, json=data)

        self.page.route(glob, handler)

    def pick_section_record(self, marker: str) -> None:
        """Make the section call return the (real, stored, guest-visible)
        section record whose JSON contains `marker`."""
        self._pick_by_marker(self.SECTION_API_GLOB, marker, "1")

    def put_article_first(self, marker: str) -> None:
        """Real articles call, with the stored article containing `marker`
        moved to position 0 (when it is older than the live top 3)."""
        import json as _json

        def handler(route):
            import re as _re
            url = _re.sub(r"pageSize=\d+", "pageSize=100", route.request.url)
            resp = route.fetch(url=url)
            data = resp.json()
            items = data.get("items", [])
            mine = [i for i in items if marker in _json.dumps(i, ensure_ascii=False)]
            rest = [i for i in items if i not in mine]
            data["items"] = (mine + rest)[:3]
            route.fulfill(response=resp, json=data)

        self.page.route(self.NEWS_API_GLOB, handler)

    def make_listing_404(self) -> None:
        """AC-8: the fragment probes the configured viewAllUrl; answer 404."""
        self.page.route(
            "**/web/qatar-chamber/news-archive**",
            lambda route: route.fulfill(status=404, body="Not Found"),
        )

    def visible_text_contains_any(self, titles: list, timeout_ms: int = 20000) -> list:
        """Titles (from `titles`) rendered visibly anywhere on the current
        page, polled up to `timeout_ms` for client-side rendering."""
        import time
        deadline = time.monotonic() + timeout_ms / 1000
        found = []
        while True:
            found = [t for t in titles if self.page.get_by_text(t, exact=False).first.is_visible()]
            if found or time.monotonic() >= deadline:
                return found
            self.page.wait_for_timeout(1000)

    # ── CMS content-verification (Control_Panel-driven propagation checks) ──
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def article_visible_by_title(self, title: str) -> bool:
        """True if any Latest News card renders this title. Uses
        Playwright's own is_visible() (not mere DOM presence) so an
        unpublished/absent article is correctly reported absent."""
        try:
            locator = self.page.locator(f'{self.SECTION} {self.CARD_TITLE}:text-is("{title}")')
            return locator.first.is_visible()
        except Exception:  # noqa: BLE001 — mirrors BasePage.is_visible's never-throws contract
            return False

    def reload_until(self, predicate, timeout_ms: int | None = None, interval_ms: int | None = None) -> bool:
        """Poll open_home() + predicate(self) until True or timeout — never
        a bare sleep. Mirrors HomePromoBannersPage.reload_until()'s shape."""
        import time

        timeout_ms = timeout_ms if timeout_ms is not None else self.RELOAD_POLL_TIMEOUT_MS
        interval_ms = interval_ms if interval_ms is not None else self.RELOAD_POLL_INTERVAL_MS
        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if predicate(self):
                return True
            if time.monotonic() >= deadline:
                return False
            self.page.wait_for_timeout(interval_ms)

    def reload_until_article_matches(self, title: str, expected_visible: bool,
                                      timeout_ms: int | None = None) -> bool:
        return self.reload_until(
            lambda p: p.article_visible_by_title(title) == expected_visible,
            timeout_ms=timeout_ms,
        )

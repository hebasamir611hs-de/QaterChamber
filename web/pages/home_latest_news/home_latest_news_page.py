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
    القادمة، والتحديات الاقتصادية الرسمية." <html dir="rtl" lang="ar-SA"> and
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

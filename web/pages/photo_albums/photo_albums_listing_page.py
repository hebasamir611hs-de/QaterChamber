"""
web/pages/photo_albums/photo_albums_listing_page.py — PhotoAlbumsListingPage.

Public-frontend Page Object for PBI 130714 ("QC - Insights & Media - 006 -
Photo Gallery"), listing page at
`/web/qatar-chamber/photo-gallery` (AR: `/ar/web/qatar-chamber/photo-gallery`).

The real path was NOT the naively-guessed slug — it was resolved from the
live homepage's rendered album-card anchors (`a[href]` whose visible text
matched /photo|insight|gallery|album/i), read via a scripted DOM probe
(`page.eval_on_selector_all('a', ...)`), mirroring gm_message_page.py's and
org_structure_page.py's precedent for a hover-only nav this project's
extractor can't walk.

Locators: `tools/extract_locators.py` against the live listing page returned
only the header/footer chrome plus the search/filter/sort controls (the only
genuinely interactive elements on this page — confirmed via a CLI run,
2026-09-21). The page's own structural elements (hero, breadcrumb, cards,
grid, badges, chips, meta line, Load More) are not `<a>/<button>/<input>` the
harvester walks by default (cards ARE `<a>` but with no accessible name of
their own beyond the whole card's text), so a scripted DOM-class probe
(`page.eval_on_selector_all('[class*=qc-pgl]', ...)`) against the live page
confirmed the real, stable `qc-pgl-*` custom classes below — same
CLI-first technique as gm_message_page.py's `qc-gm-*` probe, no MCP fallback
needed. Confirmed live (2026-09-21) against
https://qcdev.ihorizons.com/web/qatar-chamber/photo-gallery at the framework's
default 1920x1080 viewport:

    header.qc-pgl-hero
        div.qc-pgl-hero-bg[style*=background-image]
        div.qc-pgl-hero-overlay
        div.qc-pgl-hero-inner > h1.qc-pgl-hero-title ("Photo Albums")
            nav.qc-pgl-crumbs[aria-label="Breadcrumb"]
                a.qc-pgl-crumb (Home) > svg.qc-pgl-crumb-ico
                svg.qc-pgl-crumb-sep (between crumbs)
                a.qc-pgl-crumb (Insights & Media, a working link)
                span.qc-pgl-crumb.qc-pgl-crumb-current (Photo Albums, current)
    form.qc-pgl-controls[data-qc-pgl-form]
        div.qc-pgl-field.qc-pgl-search > input.qc-pgl-search-input[placeholder="Search Photo Albums..."]
                                        > button.qc-pgl-search-btn[aria-label="Search photo albums"]
        div.qc-pgl-field.qc-pgl-cat > select.qc-pgl-select[data-qc-pgl-cat][aria-label="Filter by event"]
            (confirmed live options: "All Events" / "Institutional" / "Collaboration" / "Events")
        div.qc-pgl-field.qc-pgl-sort > select.qc-pgl-select[data-qc-pgl-sort][aria-label="Sort albums"]
            (confirmed live options: "Most Recent" (value=recent, default) / "Most Viewed" (value=viewed))
    p/span.qc-pgl-status (results count line, e.g. "0 albums shown")
    div.qc-pgl-grid (CSS grid; confirmed 3x "424px" tracks at both 1920 and
        1440 widths, 1 track at 768 and 375 — see the responsive tests'
        docstrings for the one case whose expected "tablet intermediate"
        wording does not match this live behaviour)
        a.qc-pgl-card[href="/web/qatar-chamber/photo-album-details?erc=<code>"]
            div.qc-pgl-cover > img.qc-pgl-cover-img[alt=<album title>]
                              > span.qc-pgl-badge (e.g. "5 photos")
            div.qc-pgl-card-text
                span.qc-pgl-chip (Event Category name, e.g. "Institutional")
                h3.qc-pgl-card-title
                div.qc-pgl-meta > span.qc-pgl-meta-item (date, e.g. "Mar 3, 2026")
                                 > span.qc-pgl-meta-item (view count, e.g. "2,861")
    div.qc-pgl-empty (empty-state message; confirmed live EN: "No photo
        albums found for your search." / AR: "لا توجد ألبومات صور مطابقة
        لبحثك.")
    button.qc-pgl-more[data-qc-pgl-more] ("Load More" — confirmed live
        `hidden` on this environment's real data set, which has only 3
        published albums that all fit on a single page; see the module
        docstring in test_photo_albums_web.py for the cases this makes
        untestable without a CMS write)

Live data set confirmed 2026-09-21 (qcdev, 3 published albums total — no
album in this environment matches several QA cases' example titles/counts
verbatim, e.g. "Qatar-Belgium Business Forum 2026"/"Chairman Delegation Visit
to Novgorod" do not exist here; tests use the real live album titles/counts
instead and note the substitution):
    1. "QICCA Concludes 'Qualification and Preparation of Arbitrators'
       Programmes" — category "Institutional", 5 photos, views "2,861"
    2. "Qatar Chamber calls on shipping firms to register in the TIR System"
       — category "Collaboration", 4 photos, views "2,854"
    3. "Qatar Chamber Signs Strategic Partnership with International Trade
       Council" — category "Events", 4 photos, views "2,853"
"""

from config.settings import web_url
from core.web.base_page import BasePage

PHOTO_ALBUMS_PATH = "/web/qatar-chamber/photo-gallery"


class PhotoAlbumsListingPage(BasePage):
    # ---- Hero ---------------------------------------------------------
    HERO = ".qc-pgl-hero"
    HERO_BG = ".qc-pgl-hero-bg"
    HERO_OVERLAY = ".qc-pgl-hero-overlay"
    HERO_TITLE = ".qc-pgl-hero-title"

    # ---- Breadcrumb -----------------------------------------------------
    CRUMBS_NAV = ".qc-pgl-crumbs"
    CRUMB = ".qc-pgl-crumb"
    CRUMB_CURRENT = ".qc-pgl-crumb-current"

    # ---- Controls row ---------------------------------------------------
    CONTROLS = ".qc-pgl-controls"
    SEARCH_INPUT = ".qc-pgl-search-input"
    SEARCH_BTN = ".qc-pgl-search-btn"
    CAT_SELECT = "select[data-qc-pgl-cat]"
    SORT_SELECT = "select[data-qc-pgl-sort]"

    # ---- Results / grid ---------------------------------------------------
    STATUS = ".qc-pgl-status"
    GRID = ".qc-pgl-grid"
    CARD = ".qc-pgl-card"
    CARD_COVER_IMG = ".qc-pgl-cover-img"
    CARD_BADGE = ".qc-pgl-badge"
    CARD_CHIP = ".qc-pgl-chip"
    CARD_TITLE = ".qc-pgl-card-title"
    CARD_META_ITEM = ".qc-pgl-meta-item"
    EMPTY = ".qc-pgl-empty"
    MORE_BTN = ".qc-pgl-more"

    # ---- Navigation -----------------------------------------------------
    def open_photo_albums(self, locale: str = "en") -> "PhotoAlbumsListingPage":
        self.open(web_url(PHOTO_ALBUMS_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    # ---- Hero / breadcrumb queries ---------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_bg_style(self) -> str:
        return self.get_attribute(self.HERO_BG, "style") or ""

    def hero_overlay_color(self) -> str:
        return self.page.locator(self.HERO_OVERLAY).first.evaluate(
            "el => getComputedStyle(el).backgroundColor"
        )

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.CRUMBS_NAV)

    def breadcrumb_texts(self) -> list:
        return self.page.locator(self.CRUMB).all_text_contents()

    def breadcrumb_current_text(self) -> str:
        return self.text(self.CRUMB_CURRENT)

    def breadcrumb_link_hrefs(self) -> list:
        """href of every non-current breadcrumb link (an <a>, not the
        current <span>)."""
        return self.page.locator(f"a{self.CRUMB}").evaluate_all(
            "els => els.map(e => e.getAttribute('href'))"
        )

    # ---- Controls row ------------------------------------------------------
    def search_placeholder(self) -> str:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder") or ""

    def category_selected_label(self) -> str:
        return self.page.locator(self.CAT_SELECT).evaluate(
            "el => el.options[el.selectedIndex].text"
        )

    def sort_selected_label(self) -> str:
        return self.page.locator(self.SORT_SELECT).evaluate(
            "el => el.options[el.selectedIndex].text"
        )

    def category_options(self) -> list:
        return self.page.locator(f"{self.CAT_SELECT} option").all_text_contents()

    def sort_options(self) -> list:
        return self.page.locator(f"{self.SORT_SELECT} option").all_text_contents()

    def search(self, term: str) -> "PhotoAlbumsListingPage":
        self.type(self.SEARCH_INPUT, term)
        self.click(self.SEARCH_BTN)
        self.page.wait_for_timeout(600)  # client-side filter re-render, no navigation to wait_for_url on
        return self

    def clear_search(self) -> "PhotoAlbumsListingPage":
        self.type(self.SEARCH_INPUT, "")
        self.click(self.SEARCH_BTN)
        self.page.wait_for_timeout(600)
        return self

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    def select_category(self, label: str) -> "PhotoAlbumsListingPage":
        self.select_option(self.CAT_SELECT, label=label)
        self.page.wait_for_timeout(600)
        return self

    def select_sort(self, label: str) -> "PhotoAlbumsListingPage":
        self.select_option(self.SORT_SELECT, label=label)
        self.page.wait_for_timeout(600)
        return self

    # ---- Grid / cards --------------------------------------------------
    def grid_template_columns(self) -> str:
        return self.page.locator(self.GRID).first.evaluate(
            "el => getComputedStyle(el).gridTemplateColumns"
        )

    def grid_column_count(self) -> int:
        return len(self.grid_template_columns().split())

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_text_contents()

    def card_by_title(self, title: str):
        return self.page.locator(self.CARD).filter(has_text=title).first

    def card_chip_text(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_CHIP).text_content()

    def card_badge_text(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_BADGE).text_content()

    def card_meta_items(self, index: int) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META_ITEM).all_text_contents()

    def card_cover_alt(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_COVER_IMG).get_attribute("alt") or ""

    def card_view_count(self, index: int) -> int:
        """The second meta item is the view count (date is first) — parsed
        as an int (commas stripped) so callers can compare/sort numerically."""
        raw = self.card_meta_items(index)[1]
        return int(raw.replace(",", "").strip())

    def open_card_by_title(self, title: str):
        """Clicks the card whose title matches `title` and returns an
        AlbumDetailsPage bound to the SAME page object (Playwright page is
        shared; the caller constructs an AlbumDetailsPage(self.page) after
        this navigates, mirroring gm_message_page.py's next-Page-Object
        return convention).

        Waits for the AJAX-filtered grid to settle (networkidle) before
        clicking — a caller that just applied a search/filter/sort can reach
        this call before the re-render finishes, landing the click on a stale
        pre-filter card (HEALED 2026-09-23). Clicks the card's own title text
        specifically (`CARD_TITLE`, which bubbles to the enclosing `<a>`)
        rather than the whole card's bounding-box center, mirroring the same
        fix in video_library_listing_page.py where the card's center can be
        covered by a non-title overlay element.

        Also waits for the destination Details page's own title element
        (`.qc-pgd-title`) to actually render before returning — mirrors
        open_album()'s existing `wait_for(HERO_TITLE)` pattern. Without this,
        `domcontentloaded` alone does not guarantee the details title has
        populated yet, so a caller reading it immediately after this call can
        observe a stale/empty value (HEALED 2026-09-23)."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:  # noqa: BLE001 — best-effort settle, never block the click
            pass
        self.page.locator(self.CARD_TITLE).filter(has_text=title).first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for(".qc-pgd-title")

    def status_text(self) -> str:
        return self.text(self.STATUS)

    def empty_text(self) -> str:
        return self.text(self.EMPTY)

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.MORE_BTN)

    def click_load_more(self) -> "PhotoAlbumsListingPage":
        self.click(self.MORE_BTN)
        self.page.wait_for_timeout(600)
        return self

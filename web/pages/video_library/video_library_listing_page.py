"""
web/pages/video_library/video_library_listing_page.py — VideoLibraryListingPage.

Public-frontend Page Object for PBI 130715 ("QC - Insights & Media - 007 -
Video Gallery"), listing page at
`/web/qatar-chamber/video-library` (AR: `/ar/web/qatar-chamber/video-library`).

The real path was NOT the case wording's implied slug ("Video Gallery") — a
direct-URL probe (mirroring photo_albums_listing_page.py's precedent for a
hover-only nav menu this project's extractor can't walk) confirmed
`/web/qatar-chamber/video-gallery` 404s ("Coming Soon") while
`/web/qatar-chamber/video-library` 200s with page title "Video Library -
Qatar Chamber - Liferay DXP". Same CLI-first technique as
photo_albums_listing_page.py: a scripted `page.eval_on_selector_all` DOM-class
probe (`[class*=qc-vll]`) against the live page, run at the framework's
default 1920x1080 viewport (`tools/extract_locators.py` itself returns only
header/footer chrome plus the two `<select>` controls for this page — the
hero/breadcrumb/cards/chips/grid/badges are not bare `<a>/<button>/<input>`
the harvester walks by default). Confirmed live 2026-09-21 against
https://qcdev.ihorizons.com/web/qatar-chamber/video-library:

    header.qc-vll-hero
        div.qc-vll-hero-bg[style*=background-image]
        div.qc-vll-hero-overlay
        div.qc-vll-hero-inner > h1.qc-vll-hero-title ("Video Library")
            nav.qc-vll-crumbs[aria-label="Breadcrumb"]
                a.qc-vll-crumb (Home), a.qc-vll-crumb (Insights & Media,
                    links to THIS SAME listing page's own href — same
                    "middle crumb links to the hub page it belongs to"
                    pattern as photo_albums_listing_page.py),
                span.qc-vll-crumb.qc-vll-crumb-current ("Videos")
    form.qc-vll-controls[data-qc-vll-form]
        div.qc-vll-field.qc-vll-search > input.qc-vll-search-input[placeholder="Search videos..."]
                                        > button.qc-vll-search-btn[aria-label="Search videos"]
        div.qc-vll-field.qc-vll-cat > select.qc-vll-select[data-qc-vll-cat][aria-label="Filter by category"]
            (confirmed live options: "All Categories"/"Institutional"/"Events"/
             "Leadership"/"Promotional"/"Live Streams" — NO "Training" category
             exists on this environment, unlike TC 142951's example list; see
             the "Data adaptations" note in test_video_library_web.py)
        div.qc-vll-field.qc-vll-sort > select.qc-vll-select[data-qc-vll-sort][aria-label="Sort videos"]
            (confirmed live options: "Most Recent" (value=recent, default) /
             "Most Viewed" (value=viewed))
    div.qc-vll-chipstrip
        div.qc-vll-chips[data-qc-vll-chips][role=group][aria-label="Filter by category"]
            button.qc-vll-chip[data-category=""][aria-pressed=true] ("All Videos", selected by default)
            button.qc-vll-chip[data-category="institutional"] ("Institutional")
            button.qc-vll-chip[data-category="events"] ("Events")
            button.qc-vll-chip[data-category="leadership"] ("Leadership")
            button.qc-vll-chip[data-category="promotional"] ("Promotional")
            button.qc-vll-chip[data-category="livestreams"] ("Live Streams")
    p/span.qc-vll-status (results count line, e.g. "5 videos shown")
    div.qc-vll-grid (CSS grid; confirmed live: 3 tracks of 424px at BOTH 1920
        and 1440 widths, 2 tracks of 352px at 768, 1 track of 335px at 375 —
        UNLIKE photo_albums_listing_page.py's tablet mismatch, this page's
        768px layout genuinely IS the "intermediate column count" TC 142961
        expects: confirmed 2 columns, not 1)
        a.qc-vll-card[href="/web/qatar-chamber/video-details?erc=<code>"]
            div.qc-vll-thumb > img.qc-vll-thumb-img[alt=<video title>]
                              > div.qc-vll-thumb-shade
                              > span.qc-vll-duration (e.g. "12:45")
                              > div.qc-vll-play (play-button overlay, SVG icon)
            div.qc-vll-card-text
                div.qc-vll-card-head > span.qc-vll-tag (category, e.g. "Events")
                                      > h3.qc-vll-card-title
                div.qc-vll-meta > span.qc-vll-meta-item (published date, e.g. "Feb 18, 2026")
                                 > span.qc-vll-meta-item > span.qc-vll-ltr (view
                                     count, e.g. "9,319" — CONFIRMED LIVE: the
                                     raw number only, no "views" word suffix
                                     anywhere in the DOM (checked innerText and
                                     getComputedStyle(...,'::after').content on
                                     both the wrapping span and the inner
                                     .qc-vll-ltr span — both "none"); TC 142952's
                                     own wording ("142 views") is NOT literally
                                     what renders — see the "Data adaptations"
                                     note in test_video_library_web.py)
    div.qc-vll-empty (empty-state message; confirmed live EN: "No videos
        found for your search.")
    button.qc-vll-more[data-qc-vll-more] ("Load More" — confirmed live
        `hidden` on this environment's real data set, which has only 5
        published videos that all fit on a single page and load in one
        request ("5 videos shown"); see the module docstring in
        test_video_library_web.py for the cases this makes untestable
        without a CMS write)

Live data set confirmed 2026-09-21 (qcdev, 5 published videos total, in
default Most-Recent order — no video in this environment matches several QA
cases' own example titles/durations/view counts verbatim, e.g. "QC Annual
Forum 2026" does not exist here; tests use the real live video
titles/durations/counts instead and note the substitution):
    1. erc=QCDEMO-130715-VIDEO-09 "Qatar Chamber Media Library - Uploaded
       Clip Sample" — Institutional, 00:05, views "7", Sep 3, 2026 (a
       deliberate Direct-Upload demo record per its own description; its
       playback FAILS live — the poster/embed toggle stays on the poster and
       `.qc-vdt-player-error` becomes visible after Play is clicked, confirmed
       live 2026-09-21 — this is the real, reproducible precondition
       TC 143077 needs, not a simulated one)
    2. erc=QCDEMO-130715-VIDEO-02 "Qatar Chamber Discusses Trade Cooperation
       with Victoria's Minister for Finance and Economic Growth" — Events,
       12:45, views "9,319", Feb 18, 2026 (plays back correctly — used for
       all play/pause/seek/volume/share cases)
    3. erc=QCDEMO-130715-VIDEO-06 "Qatar Chamber Discusses Strengthening
       Cooperation with the U.S. Chamber of Commerce" — Live Streams, 45:00,
       views "5,627", Feb 5, 2026
    4. erc=QCDEMO-130715-VIDEO-03 "The Chamber and the Ministry of Finance
       Discuss the Mandatory List of Local Products in Government
       Procurement" — Leadership, 14:20, views "15,210", Jan 22, 2026 (its
       real duration, 14:20, matches TC 143081's own worded example exactly —
       used as the Flickr/10-minute-cap case's subject video)
    5. erc=QCDEMO-130715-VIDEO-05 "Qatar Chamber Participates in Oman
       International Exhibition and Forum 2026" — Promotional, 03:48, views
       "22,459", Jan 9, 2026
"""

from config.settings import web_url
from core.web.base_page import BasePage

VIDEO_LIBRARY_PATH = "/web/qatar-chamber/video-library"


class VideoLibraryListingPage(BasePage):
    # ---- Hero ---------------------------------------------------------
    HERO = ".qc-vll-hero"
    HERO_BG = ".qc-vll-hero-bg"
    HERO_OVERLAY = ".qc-vll-hero-overlay"
    HERO_TITLE = ".qc-vll-hero-title"

    # ---- Breadcrumb -----------------------------------------------------
    CRUMBS_NAV = ".qc-vll-crumbs"
    CRUMB = ".qc-vll-crumb"
    CRUMB_CURRENT = ".qc-vll-crumb-current"

    # ---- Controls row ---------------------------------------------------
    CONTROLS = ".qc-vll-controls"
    SEARCH_INPUT = ".qc-vll-search-input"
    SEARCH_BTN = ".qc-vll-search-btn"
    CAT_SELECT = "select[data-qc-vll-cat]"
    SORT_SELECT = "select[data-qc-vll-sort]"

    # ---- Category chip strip --------------------------------------------
    CHIPSTRIP = ".qc-vll-chipstrip"
    CHIPS_GROUP = ".qc-vll-chips"
    CHIP = ".qc-vll-chip"

    # ---- Results / grid ---------------------------------------------------
    STATUS = ".qc-vll-status"
    GRID = ".qc-vll-grid"
    CARD = "a.qc-vll-card"
    CARD_THUMB_IMG = ".qc-vll-thumb-img"
    CARD_THUMB_FALLBACK = ".qc-vll-thumb-fallback"
    CARD_DURATION = ".qc-vll-duration"
    CARD_PLAY_OVERLAY = ".qc-vll-play"
    CARD_TAG = ".qc-vll-tag"
    CARD_TITLE = ".qc-vll-card-title"
    CARD_META_ITEM = ".qc-vll-meta-item"
    EMPTY = ".qc-vll-empty"
    MORE_BTN = ".qc-vll-more"

    # ---- Navigation -----------------------------------------------------
    def open_video_library(self, locale: str = "en") -> "VideoLibraryListingPage":
        self.open(web_url(VIDEO_LIBRARY_PATH, locale=locale))
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

    def search(self, term: str) -> "VideoLibraryListingPage":
        self.type(self.SEARCH_INPUT, term)
        self.click(self.SEARCH_BTN)
        self.page.wait_for_timeout(600)  # client-side filter re-render, no navigation to wait_for_url on
        return self

    def clear_search(self) -> "VideoLibraryListingPage":
        self.type(self.SEARCH_INPUT, "")
        self.click(self.SEARCH_BTN)
        self.page.wait_for_timeout(600)
        return self

    def search_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).input_value()

    def select_category(self, label: str) -> "VideoLibraryListingPage":
        self.select_option(self.CAT_SELECT, label=label)
        self.page.wait_for_timeout(600)
        return self

    def select_sort(self, label: str) -> "VideoLibraryListingPage":
        self.select_option(self.SORT_SELECT, label=label)
        self.page.wait_for_timeout(600)
        return self

    # ---- Category chip strip --------------------------------------------
    def chip_labels(self) -> list:
        return self.page.locator(self.CHIP).all_text_contents()

    def click_chip(self, label: str) -> "VideoLibraryListingPage":
        self.page.locator(self.CHIP).filter(has_text=label).first.click()
        self.page.wait_for_timeout(600)
        return self

    def selected_chip_label(self) -> str:
        """The single chip currently carrying aria-pressed="true"."""
        pressed = self.page.locator(f'{self.CHIP}[aria-pressed="true"]')
        return pressed.first.text_content() if pressed.count() else ""

    def is_chip_selected(self, label: str) -> bool:
        chip = self.page.locator(self.CHIP).filter(has_text=label).first
        return chip.get_attribute("aria-pressed") == "true"

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

    def card_tag_text(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_TAG).text_content()

    def card_duration_text(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_DURATION).text_content()

    def card_meta_items(self, index: int) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META_ITEM).all_text_contents()

    def card_thumb_alt(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_THUMB_IMG).get_attribute("alt") or ""

    def card_published_date(self, index: int) -> str:
        return self.card_meta_items(index)[0]

    def card_view_count(self, index: int) -> int:
        """The second meta item is the raw view count (date is first,
        confirmed live to carry NO "views" word suffix) — parsed as an int
        (commas stripped) so callers can compare/sort numerically."""
        raw = self.card_meta_items(index)[1]
        return int(raw.replace(",", "").strip())

    def is_card_play_overlay_visible(self, index: int) -> bool:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_PLAY_OVERLAY).is_visible()

    def is_card_thumb_fallback_visible(self, index: int) -> bool:
        """True when the card renders the placeholder SVG (`.qc-vll-thumb-
        fallback`) instead of a real `<img>` — CONFIRMED live 2026-09-22 for
        a disposable video whose Video Thumbnail field's underlying asset
        API 500s (`/o/qc-video-library-api/asset?...field=videoThumbnail`
        returns HTTP 500) — used by TC 143076."""
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_THUMB_FALLBACK).is_visible()

    def open_card_by_title(self, title: str) -> None:
        """Clicks the card whose title matches `title` and navigates to its
        Video Details page (Playwright `page` is shared; the caller
        constructs a VideoDetailsPage(self.page) after this navigates,
        mirroring photo_albums_listing_page.py's next-Page-Object return
        convention).

        Waits for the AJAX-filtered grid to settle (networkidle) before
        clicking — a caller that just applied a search/filter/sort can reach
        this call before the re-render finishes, landing the click on a stale
        pre-filter card (HEALED 2026-09-23). Clicks the card's own title text
        specifically (`CARD_TITLE`, which bubbles to the enclosing `<a>`)
        rather than the whole card's bounding-box center — the video card's
        center is covered by `CARD_PLAY_OVERLAY`, a centered Play button that
        stops click propagation instead of letting it reach the card's own
        anchor, confirmed live 2026-09-23.

        Also waits for the destination Details page's own title element
        (`.qc-vdt-title`) to actually render before returning — mirrors
        open_video()'s existing `wait_for(HERO_TITLE)` pattern and
        photo_albums_listing_page.py's identical HEALED fix. Without this,
        `domcontentloaded` alone does not guarantee the details title has
        populated yet, so a caller reading it immediately after this call can
        observe a stale/empty value (HEALED 2026-09-23)."""
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:  # noqa: BLE001 — best-effort settle, never block the click
            pass
        self.page.locator(self.CARD_TITLE).filter(has_text=title).first.click()
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for(".qc-vdt-title")

    def status_text(self) -> str:
        return self.text(self.STATUS)

    def empty_text(self) -> str:
        return self.text(self.EMPTY)

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.MORE_BTN)

    def click_load_more(self) -> "VideoLibraryListingPage":
        self.click(self.MORE_BTN)
        self.page.wait_for_timeout(600)
        return self

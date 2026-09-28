"""
web/pages/photo_albums/album_details_page.py — AlbumDetailsPage.

Public-frontend Page Object for PBI 130714 ("QC - Insights & Media - 006 -
Photo Gallery"), Album Details page at
`/web/qatar-chamber/photo-album-details?erc=<code>`
(AR: `/ar/web/qatar-chamber/photo-album-details?erc=<code>`).

Same CLI-first DOM-class-probe technique as
photo_albums_listing_page.py's module docstring (a scripted
`page.eval_on_selector_all('[class]', ...)` filtered to `qc-` classes — the
extractor itself returns nothing for this page's own structural elements,
only header/footer chrome). Confirmed live 2026-09-21 against
https://qcdev.ihorizons.com/web/qatar-chamber/photo-album-details?erc=QCDEMO-130714-PHOTO_ALBUM-first-test-album
at the framework's default 1920x1080 viewport:

    header.qc-pgd-hero
        div.qc-pgd-hero-bg[style*=background-image]
        div.qc-pgd-hero-overlay
        div.qc-pgd-hero-inner > h1.qc-pgd-hero-title ("Album details")
            nav.qc-pgd-crumbs[aria-label="Breadcrumb"]
                a.qc-pgd-crumb (Home), a.qc-pgd-crumb (Insights & Media),
                span.qc-pgd-crumb.qc-pgd-crumb-current ("Photo Albums" — the
                    LISTING page's own name, confirmed live; the crumb trail
                    does NOT include the album's own title)
    div.qc-pgd-body > div.qc-pgd-shell
        div.qc-pgd-head
            span.qc-pgd-chip (Event Category, e.g. "Institutional" — a
                DELIBERATELY separate component from the listing card's
                chip per the live HTML's own comment: 36px tall here vs 22px
                on the card)
            h2.qc-pgd-title (album title)
            div.qc-pgd-meta > span.qc-pgd-meta-item x3: published date
                (e.g. "Mar 3, 2026"), total view count (e.g. "2,863"),
                image count (e.g. "5 images")
        div.qc-pgd-mosaic (photo grid; rows qc-pgd-row1/row2/row3)
            button.qc-pgd-box.qc-pgd-lead[data-qc-pgd-index="0"] (the lead
                photo — full width above the rest, confirmed via bounding
                box: spans the full content width at every viewport tested)
                > img.qc-pgd-box-img[alt=<photo name>]
            button.qc-pgd-box.qc-pgd-tall / .qc-pgd-small / .qc-pgd-wide
                (remaining photos, each its own box class — no forced
                cropping class; `object-fit` is NOT `cover` on these
                confirmed live, i.e. natural aspect ratio is preserved)
    div.qc-pgd-lb (lightbox overlay, hidden until a box is clicked)
        div.qc-pgd-lb-scrim
        div.qc-pgd-lb-dialog[role=dialog][aria-modal=true]
            button.qc-pgd-lb-close[aria-label="Close"]
            button.qc-pgd-lb-nav.qc-pgd-lb-prev[aria-label="Previous photo"]
            figure.qc-pgd-lb-figure > img.qc-pgd-lb-img
                                     > figcaption.qc-pgd-lb-caption
                                         > span.qc-pgd-lb-title
                                         > span.qc-pgd-lb-count (e.g. "2 of 5")
            button.qc-pgd-lb-nav.qc-pgd-lb-next[aria-label="Next photo"]
    div.qc-pgd-empty / div.qc-pgd-status (not populated on a normal
        published-album view; present in the DOM for the empty/zero-photo
        state, not directly probed this session — see the module docstring
        in test_photo_albums_control_panel-equivalent skip notes)

View-count behaviour confirmed live 2026-09-21: opening the Details page via
a fresh navigation increments the total view count (observed 2,861 -> 2,863
across the FIRST goto — this framework's `page` fixture's own
license-gate/reauth checks issue a background re-check that can itself count
as a second "view" server-side; the exact delta is not asserted as exactly
+1 for that reason). A same-session PAGE RELOAD does **not** increment it
further (2,863 stayed 2,863 across `page.reload()`), which is what
TC 143141 verifies.
"""

from config.settings import web_url
from core.web.base_page import BasePage

ALBUM_DETAILS_PATH = "/web/qatar-chamber/photo-album-details"


class AlbumDetailsPage(BasePage):
    # ---- Hero ---------------------------------------------------------
    HERO = ".qc-pgd-hero"
    HERO_TITLE = ".qc-pgd-hero-title"

    # ---- Breadcrumb -----------------------------------------------------
    CRUMBS_NAV = ".qc-pgd-crumbs"
    CRUMB = ".qc-pgd-crumb"
    CRUMB_CURRENT = ".qc-pgd-crumb-current"

    # ---- Meta / head ------------------------------------------------------
    HEAD = ".qc-pgd-head"
    CHIP = ".qc-pgd-chip"
    TITLE = ".qc-pgd-title"
    META = ".qc-pgd-meta"
    META_ITEM = ".qc-pgd-meta-item"

    # ---- Mosaic / photo grid ------------------------------------------------
    MOSAIC = ".qc-pgd-mosaic"
    BOX = ".qc-pgd-box"
    BOX_LEAD = ".qc-pgd-box.qc-pgd-lead"
    BOX_IMG = ".qc-pgd-box-img"

    # ---- Lightbox -----------------------------------------------------
    LIGHTBOX = ".qc-pgd-lb"
    LB_IMG = ".qc-pgd-lb-img"
    LB_CAPTION_TITLE = ".qc-pgd-lb-title"
    LB_COUNT = ".qc-pgd-lb-count"
    LB_NEXT = ".qc-pgd-lb-next"
    LB_PREV = ".qc-pgd-lb-prev"
    LB_CLOSE = ".qc-pgd-lb-close"

    EMPTY = ".qc-pgd-empty"

    # ---- Navigation -----------------------------------------------------
    def open_album(self, erc: str, locale: str = "en") -> "AlbumDetailsPage":
        self.open(web_url(f"{ALBUM_DETAILS_PATH}?erc={erc}", locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_album_expect_not_found(self, erc: str, locale: str = "en") -> int:
        """Navigates directly to an Unpublished/deleted album's erc URL and
        returns the real HTTP status the server answered with (143182/143183).
        Caller is responsible for using a logged-out `page` fixture
        (`{"auth": False}`) — an authenticated CMS session can render a
        staging/preview view of Unpublished content instead of the real
        public not-found state.

        CONFIRMED LIVE 2026-09-22 (disposable QCTEST record): this page does
        NOT fall back to the site's generic "Coming Soon" 404 for a missing
        erc — the query-param route itself always resolves (HTTP 200), and
        the page renders its own graceful in-page not-available state
        instead (`.qc-pgd-empty`, text "This photo album is not available.").
        Callers should assert on `is_empty_state_visible()` /
        `empty_state_text()`, not on this method's returned status, for the
        "not found" cases — the status is still returned for completeness/
        transparency."""
        url = web_url(f"{ALBUM_DETAILS_PATH}?erc={erc}", locale=locale)
        response = self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for(self.EMPTY)
        return response.status if response else 0

    def empty_state_text(self) -> str:
        return self.text(self.EMPTY)

    def reload_same_session(self) -> "AlbumDetailsPage":
        self.page.reload()
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for(self.HERO_TITLE)
        return self

    # ---- Hero / breadcrumb queries ---------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.CRUMBS_NAV)

    def breadcrumb_texts(self) -> list:
        return self.page.locator(self.CRUMB).all_text_contents()

    # ---- Meta / head queries --------------------------------------------
    def chip_text(self) -> str:
        return self.text(self.CHIP)

    def title_text(self) -> str:
        return self.text(self.TITLE)

    def meta_items(self) -> list:
        return self.page.locator(self.META_ITEM).all_text_contents()

    def published_date_text(self) -> str:
        return self.meta_items()[0]

    def view_count(self) -> int:
        return int(self.meta_items()[1].replace(",", "").strip())

    def image_count_text(self) -> str:
        return self.meta_items()[2]

    # ---- Mosaic queries --------------------------------------------------
    def box_count(self) -> int:
        return self.page.locator(self.BOX).count()

    def is_lead_box_visible(self) -> bool:
        return self.is_visible(self.BOX_LEAD)

    def lead_box_bounding_box(self) -> dict:
        return self.page.locator(self.BOX_LEAD).first.bounding_box()

    def box_bounding_box(self, index: int) -> dict:
        return self.page.locator(self.BOX).nth(index).bounding_box()

    def box_object_fit(self, index: int) -> str:
        return self.page.locator(self.BOX).nth(index).locator(self.BOX_IMG).evaluate(
            "el => getComputedStyle(el).objectFit"
        )

    def distinct_box_x_offsets(self) -> list:
        """Distinct rounded X offsets of every box AFTER the lead photo —
        used to tell a single-column reflow (all boxes share one X offset)
        apart from a multi-column grid (more than one distinct X offset)."""
        boxes = self.page.locator(self.BOX).all()
        rects = [b.bounding_box() for b in boxes[1:]]
        return sorted({round(r["x"]) for r in rects if r})

    def click_box(self, index: int) -> "AlbumDetailsPage":
        self.page.locator(self.BOX).nth(index).click()
        self.wait_for(self.LIGHTBOX)
        return self

    # ---- Lightbox queries/actions -----------------------------------------
    def is_lightbox_visible(self) -> bool:
        return self.is_visible(self.LIGHTBOX)

    def lightbox_caption_title(self) -> str:
        return self.text(self.LB_CAPTION_TITLE)

    def lightbox_count_text(self) -> str:
        return self.text(self.LB_COUNT)

    def lightbox_click_next(self) -> "AlbumDetailsPage":
        self.click(self.LB_NEXT)
        self.page.wait_for_timeout(300)
        return self

    def lightbox_click_prev(self) -> "AlbumDetailsPage":
        self.click(self.LB_PREV)
        self.page.wait_for_timeout(300)
        return self

    def lightbox_close(self) -> "AlbumDetailsPage":
        self.click(self.LB_CLOSE)
        self.wait_for(self.LIGHTBOX, state="hidden")
        return self

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

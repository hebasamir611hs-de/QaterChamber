"""
web/pages/video_library/video_details_page.py — VideoDetailsPage.

Public-frontend Page Object for PBI 130715 ("QC - Insights & Media - 007 -
Video Gallery"), Video Details page at
`/web/qatar-chamber/video-details?erc=<code>`
(AR: `/ar/web/qatar-chamber/video-details?erc=<code>`).

Same CLI-first DOM-class-probe technique as
video_library_listing_page.py's module docstring (`tools/extract_locators.py`
itself returns only header/footer chrome for this page too — a scripted
`page.eval_on_selector_all('[class]', ...)` filtered to `qc-vdt` classes
found the real structure). Confirmed live 2026-09-21 against
https://qcdev.ihorizons.com/web/qatar-chamber/video-details?erc=QCDEMO-130715-VIDEO-02
at the framework's default 1920x1080 viewport:

    header.qc-vdt-hero
        div.qc-vdt-hero-bg / div.qc-vdt-hero-overlay
        div.qc-vdt-hero-inner > h1.qc-vdt-hero-title ("Video details")
            nav.qc-vdt-crumbs[aria-label="Breadcrumb"]
                a.qc-vdt-crumb (Home, href=/web/qatar-chamber),
                a.qc-vdt-crumb (Insights & Media, href=/web/qatar-chamber/video-library
                    — the LISTING page's own href, same "middle crumb links to
                    the hub page" pattern as the listing page and as
                    photo_albums's Details page),
                span.qc-vdt-crumb.qc-vdt-crumb-current ("Videos")
    div.qc-vdt-body > div.qc-vdt-shell
        div.qc-vdt-head (not a literal class name confirmed separately from
            the fields below, but the structural block containing all of):
            span.qc-vdt-tag (category, e.g. "Events")
            h2.qc-vdt-title (video title)
            div.qc-vdt-metarow > span.qc-vdt-meta-item x2: published date
                (e.g. "Feb 18, 2026"), total view count (e.g. "9,319" — same
                CONFIRMED "raw number, no 'views' word" behaviour as the
                listing card's meta line)
        div.qc-vdt-desc (rich-text description; renders as one <p> per
            paragraph — CONFIRMED: no live video's description is exactly 2
            paragraphs (VIDEO-02 has 3, VIDEO-09 has 1, VIDEO-06 has 3,
            VIDEO-03 has 4, VIDEO-05 is empty) — TC 142956's own "two
            paragraphs" precondition is adapted to VIDEO-02's real 3-paragraph
            description, asserting the underlying intent (paragraphs render as
            distinct <p> elements, not one run-on block) rather than an exact
            count of 2; see the disclosed adaptation in
            test_video_library_web.py)
        div.qc-vdt-player[data-qc-vdt-player]
            div.qc-vdt-poster[data-qc-vdt-poster] (visible before Play)
                div.qc-vdt-poster-media > img.qc-vdt-poster-img[alt=<title>]
                div.qc-vdt-poster-shade
                span.qc-vdt-duration[data-qc-vdt-duration] (e.g. "12:45")
                button.qc-vdt-play[data-qc-vdt-play][aria-label="Play video"]
            div.qc-vdt-embed[data-qc-vdt-embed] (hidden until Play; when it
                unhides it contains the real HTML5 <video controls playsinline
                preload="metadata" src=... poster=...> element — CONFIRMED
                live, not an iframe/Flickr embed even for the Flickr-sourced
                VIDEO-03; see the module docstring in
                test_video_library_web.py for TC 143081's 10-minute-cap note)
            p.qc-vdt-player-error[data-qc-vdt-player-error] ("This video is
                currently unavailable. Please try again later." — CONFIRMED
                live to become the visible state instead of the video embed
                when Play is clicked on erc=QCDEMO-130715-VIDEO-09, this
                environment's genuinely-broken Direct-Upload demo record; see
                video_library_listing_page.py's module docstring)
        div.qc-vdt-share[data-qc-vdt-share]
            span.qc-vdt-share-label[data-qc-vdt-share-label] ("Social Share:")
            div.qc-vdt-share-icons[data-qc-vdt-share-icons]
                a.qc-vdt-share-btn[aria-label="Share on Facebook"]
                    [href="https://www.facebook.com/sharer/sharer.php?u=<page-url>"]
                a.qc-vdt-share-btn[aria-label="Share on X"]
                    [href="https://twitter.com/intent/tweet?url=<page-url>&text=<title>"]
                a.qc-vdt-share-btn[aria-label="Share on LinkedIn"]
                    [href="https://www.linkedin.com/sharing/share-offsite/?url=<page-url>"]
                a.qc-vdt-share-btn[aria-label="Share on WhatsApp"]
                    [href="https://wa.me/?text=<title> <page-url>"]
                (all 4 confirmed live 2026-09-21 with real, correctly
                URL-encoded hrefs pointing at THIS video's own page URL/title —
                each opens target="_blank" rel="noopener noreferrer")

View-count behaviour confirmed live 2026-09-21 (same pattern as
photo_albums's AlbumDetailsPage): opening the Details page via a fresh
navigation increments the total view count; a same-session PAGE RELOAD does
NOT increment it further — see reload_same_session()/TC 143082 below, which
mirrors AlbumDetailsPage's TC 143141 precedent and its documented reason an
exact "+1" is not asserted (this framework's own post-navigation
license-gate/reauth re-check can itself contribute an extra server-side view).
"""

import time

from config.settings import web_url
from core.web.base_page import BasePage

VIDEO_DETAILS_PATH = "/web/qatar-chamber/video-details"


class VideoDetailsPage(BasePage):
    # ---- Hero ---------------------------------------------------------
    HERO = ".qc-vdt-hero"
    HERO_TITLE = ".qc-vdt-hero-title"

    # ---- Breadcrumb -----------------------------------------------------
    CRUMBS_NAV = ".qc-vdt-crumbs"
    CRUMB = ".qc-vdt-crumb"
    CRUMB_CURRENT = ".qc-vdt-crumb-current"

    # ---- Meta / head ------------------------------------------------------
    TAG = ".qc-vdt-tag"
    TITLE = ".qc-vdt-title"
    META_ITEM = ".qc-vdt-meta-item"
    DESC = ".qc-vdt-desc"
    DESC_PARAGRAPH = ".qc-vdt-desc p"

    # ---- Player -----------------------------------------------------
    PLAYER = ".qc-vdt-player"
    POSTER = ".qc-vdt-poster"
    POSTER_IMG = ".qc-vdt-poster-img"
    DURATION_BADGE = ".qc-vdt-duration"
    PLAY_BTN = ".qc-vdt-play"
    EMBED = ".qc-vdt-embed"
    VIDEO_EL = ".qc-vdt-embed video"
    PLAYER_ERROR = ".qc-vdt-player-error"
    NOT_FOUND = ".qc-vdt-notfound"

    # ---- Social share -----------------------------------------------------
    SHARE = ".qc-vdt-share"
    SHARE_LABEL = ".qc-vdt-share-label"
    SHARE_BTN = ".qc-vdt-share-btn"

    # ---- Navigation -----------------------------------------------------
    def open_video(self, erc: str, locale: str = "en") -> "VideoDetailsPage":
        self.open(web_url(f"{VIDEO_DETAILS_PATH}?erc={erc}", locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_video_expect_not_found(self, erc: str, locale: str = "en") -> int:
        """Navigates directly to an Unpublished/deleted video's erc URL and
        returns the real HTTP status. CONFIRMED live 2026-09-22 (disposable
        QCTEST record) — same soft-404 shape as photo_albums's
        AlbumDetailsPage.open_album_expect_not_found(): the route always
        resolves (HTTP 200) and renders its own in-page "No videos are
        currently available." message (`.qc-vdt-notfound`) instead of the
        site's generic 404. Caller is responsible for a logged-out `page`
        fixture (`{"auth": False}`)."""
        url = web_url(f"{VIDEO_DETAILS_PATH}?erc={erc}", locale=locale)
        response = self.page.goto(url)
        self.page.wait_for_load_state("domcontentloaded")
        self.wait_for(self.NOT_FOUND)
        return response.status if response else 0

    def not_found_text(self) -> str:
        return self.text(self.NOT_FOUND)

    def reload_same_session(self) -> "VideoDetailsPage":
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
    def tag_text(self) -> str:
        return self.text(self.TAG)

    def title_text(self) -> str:
        return self.text(self.TITLE)

    def meta_items(self) -> list:
        return self.page.locator(self.META_ITEM).all_text_contents()

    def published_date_text(self) -> str:
        return self.meta_items()[0]

    def view_count(self) -> int:
        return int(self.meta_items()[1].replace(",", "").strip())

    def wait_for_view_count_increase(self, baseline: int, timeout_ms: int = 3000,
                                      poll_ms: int = 500) -> int:
        """Polls the view count for up to `timeout_ms` until it exceeds
        `baseline` — CONFIRMED live the increment lands asynchronously
        server-side ~1-2s after the Details page request, so a single
        immediate read races the write (TC 142992). Each poll tick does a
        same-session reload (confirmed NOT to itself add another view — see
        reload_same_session()/TC 143082) to pick up the freshly-committed
        server value, then re-reads the meta line. Returns the last observed
        count whether or not it exceeded baseline within the window, so the
        caller's own assertion is the real pass/fail signal — this only
        absorbs the known commit lag, it does not mask a genuine non-increment."""
        count = self.view_count()
        deadline = time.monotonic() + (timeout_ms / 1000)
        while count <= baseline and time.monotonic() < deadline:
            self.page.wait_for_timeout(poll_ms)
            self.reload_same_session()
            count = self.view_count()
        return count

    # ---- Description --------------------------------------------------
    def description_paragraph_count(self) -> int:
        return self.page.locator(self.DESC_PARAGRAPH).count()

    def description_text(self) -> str:
        return self.text(self.DESC)

    # ---- Player queries/actions -----------------------------------------
    def is_poster_visible(self) -> bool:
        return self.is_visible(self.POSTER)

    def duration_badge_text(self) -> str:
        return self.text(self.DURATION_BADGE)

    def click_play(self) -> "VideoDetailsPage":
        self.click(self.PLAY_BTN)
        self.page.wait_for_timeout(500)
        return self

    def is_embed_visible(self) -> bool:
        return self.is_visible(self.EMBED)

    def is_playback_element_present(self) -> bool:
        """True once EITHER a real <video> (Direct Upload source) OR an
        <iframe> (External URL / YouTube source) has mounted inside the
        embed container after Play — CONFIRMED live that this environment's
        5 published videos split across both source types (see module
        docstring): only erc=QCDEMO-130715-VIDEO-09 (Direct Upload) renders
        a real <video>; the other 4 render a YouTube <iframe>. Used by the
        "Play starts inline playback" case, which only needs to confirm
        SOME real playback element mounted in-page (no redirect/new tab),
        not which source type backs it."""
        return self.page.locator(f"{self.EMBED} video, {self.EMBED} iframe").count() > 0

    def is_player_error_visible(self) -> bool:
        return self.is_visible(self.PLAYER_ERROR)

    def player_error_text(self) -> str:
        return self.text(self.PLAYER_ERROR)

    def is_video_element_present(self) -> bool:
        return self.page.locator(self.VIDEO_EL).count() > 0

    def video_paused(self) -> bool:
        return self.page.locator(self.VIDEO_EL).evaluate("el => el.paused")

    def pause_video(self) -> "VideoDetailsPage":
        self.page.locator(self.VIDEO_EL).evaluate("el => el.pause()")
        return self

    def video_current_time(self) -> float:
        return self.page.locator(self.VIDEO_EL).evaluate("el => el.currentTime")

    def video_duration(self) -> float:
        return self.page.locator(self.VIDEO_EL).evaluate("el => el.duration")

    def seek_to_fraction(self, fraction: float) -> "VideoDetailsPage":
        """Sets the real HTML5 <video>'s currentTime to `fraction` of its
        duration (drives the seek bar programmatically — the concrete,
        deterministic stand-in for "drag the seek bar", since a real mouse
        drag on a native <video> scrubber is not reliably targetable by
        Playwright across browsers/controls skins)."""
        self.page.locator(self.VIDEO_EL).evaluate(
            "(el, frac) => { el.currentTime = el.duration * frac; }", fraction
        )
        self.page.wait_for_timeout(300)
        return self

    def video_volume(self) -> float:
        return self.page.locator(self.VIDEO_EL).evaluate("el => el.volume")

    def set_video_volume(self, volume: float) -> "VideoDetailsPage":
        self.page.locator(self.VIDEO_EL).evaluate("(el, v) => { el.volume = v; }", volume)
        return self

    def video_muted(self) -> bool:
        return self.page.locator(self.VIDEO_EL).evaluate("el => el.muted")

    def set_video_current_time(self, seconds: float) -> "VideoDetailsPage":
        self.page.locator(self.VIDEO_EL).evaluate(
            "(el, t) => { el.currentTime = t; }", seconds
        )
        return self

    def play_video(self) -> "VideoDetailsPage":
        """JS-level play() (distinct from click_play(), which clicks the
        POSTER's own Play button to first mount the <video> element).
        Resolves once playback has genuinely started (readyState advances /
        `play()` promise resolves) rather than a raw sleep."""
        self.page.locator(self.VIDEO_EL).evaluate("el => el.play()")
        return self

    # ---- Social share -----------------------------------------------------
    def is_share_label_visible(self) -> bool:
        return self.is_visible(self.SHARE_LABEL)

    def share_label_text(self) -> str:
        return self.text(self.SHARE_LABEL)

    def share_button_locator(self, platform_aria_label: str) -> str:
        return f'{self.SHARE_BTN}[aria-label="{platform_aria_label}"]'

    def share_button_href(self, platform_aria_label: str) -> str:
        return self.get_attribute(self.share_button_locator(platform_aria_label), "href") or ""

    def share_icons_count(self) -> int:
        return self.page.locator(self.SHARE_BTN).count()

    def click_share_button_expect_popup(self, platform_aria_label: str):
        """Clicks the named share icon and returns the resulting popup Page
        (Playwright `expect_page` context) — the concrete way to confirm a
        share action genuinely opens the target platform's share dialog in a
        new tab, not just that the href string looks right. Caller is
        responsible for closing the returned popup."""
        with self.page.context.expect_page() as popup_info:
            self.click(self.share_button_locator(platform_aria_label))
        return popup_info.value

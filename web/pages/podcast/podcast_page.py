"""
web/pages/podcast/podcast_page.py — PodcastPage.

Public-frontend Page Object for PBI 130713 ("QC - Insights & Media - 005 -
Podcast"), single page at `/web/qatar-chamber/podcast`
(AR: `/ar/web/qatar-chamber/podcast`) — hero + episode listing (with inline
AI-Highlights popup + a sticky bottom audio player) + subscription band, all
on ONE page (unlike video_library/photo_albums, there is no separate
Details sub-page).

Locators — CLI-first extraction log, confirmed live 2026-09-21 against
https://qcdev.ihorizons.com/web/qatar-chamber/podcast at the framework's
default 1920x1080 viewport:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/podcast --viewport 1920x1080
    -> confirms header/footer chrome + the 3 platform links
       (get_by_role("link", name="Listen on Apple Music"/"RSS Feed"/
       "Listen on Spotify")) and the Load More button
       (get_by_role("button", name="Load More")) — the hero/episode-list/
       popup/sticky-player internals are not bare interactive elements the
       harvester walks by default (composed divs/spans), same class of gap
       already documented for video_library_listing_page.py and
       photo_albums_listing_page.py. Resolved the same way: a scripted
       `page.eval_on_selector_all` DOM-class probe (`[class*=qc-]`) plus
       targeted `inner_html()` reads against the live page.

Real DOM structure confirmed live (2026-09-21):

    header.qc-podcast-hero
        div.qc-ph-bg > div.qc-ph-bg-image[style*=background-image]
        div.qc-ph-inner > div.qc-ph-text
            nav.qc-ph-crumbs[aria-label="Breadcrumb"]
                a.qc-ph-crumb (Home, href="/web/qatar-chamber")
                span.qc-ph-crumb ("Insights & Media" — a PLAIN SPAN here, NOT
                    a link, unlike video_library_listing_page.py's/
                    photo_albums_listing_page.py's middle crumb, which link
                    to their own hub page — confirmed live via inner_html(),
                    not assumed)
                span.qc-ph-crumb.is-current[aria-current="page"] ("Podcast")
            div.qc-ph-badges > span.qc-ph-badge ("5 Episodes", "Weekly")
            h1.qc-ph-title ("Qatar Chamber Podcast")
            p.qc-ph-desc
            div.qc-ph-host
                img.qc-ph-host-avatar[alt=<host name>]
                span.qc-ph-host-name / span.qc-ph-host-title
            div.qc-ph-platforms
                a.qc-ph-platform[href][target=_blank][aria-label="Listen on Apple Music"]
                a.qc-ph-platform[href][target=_blank][aria-label="RSS Feed"]
                a.qc-ph-platform[href][target=_blank][aria-label="Listen on Spotify"]
                    (DOM order is Apple Music, RSS, Spotify — NOT the hero
                    text's own left-to-right platform-button reading order
                    implied by some cases; confirmed via inner_html(), used
                    as-is, not reordered)

    section.qc-podcast-listing
        div.qc-pl-card (one per episode; 4 render on first load, "Load More"
            reveals the 5th — confirmed live: exactly 5 published episodes
            total on this environment)
            img.qc-pl-img
            h3.qc-pl-title
            p.qc-pl-desc
            div.qc-pl-meta
                span.qc-pl-meta-item.qc-pl-meta-badge > span ("Episode {n}")
                button.qc-pl-meta-item.qc-pl-ai > span ("AI Highlights" —
                    CONFIRMED LIVE: only renders on episodes that have BOTH
                    highlight fields populated; 2 of 5 live episodes carry it
                    (Episode 24, Episode 23), the other 3 (21, 20, 19) render
                    with NO AI Highlights control at all — a real, live
                    "hidden when unconfigured" case, not simulated)
                span.qc-pl-meta-item (published date, e.g. "May 10, 2026")
                span.qc-pl-meta-item (duration, e.g. "42 MIN" — CONFIRMED
                    LIVE: always renders as a whole-minute integer + " MIN",
                    never HH:MM:SS, on all 5 live episodes: 42/38/42/38/45 MIN)
                span.qc-pl-meta-item (plays, e.g. "19 plays" — CONFIRMED LIVE
                    plural "plays" even at count 1, e.g. Episode 19 "1 plays";
                    no live episode exceeds 20 plays, so the >1000
                    abbreviation rule (TC 143626/143627) cannot be observed
                    here without a CMS write — see test module docstring)
            div.qc-pl-actions
                button.qc-pl-play ("Play")
                a.qc-pl-download[href][download] (download link — CONFIRMED
                    LIVE: every one of the 5 live episodes renders this
                    control; NONE is an Option-B/embed-only episode on this
                    environment — see test module docstring for TC 143560/
                    143585's resulting SKIP)
        div.qc-pl-empty (empty-state text; confirmed live EN: "No episodes
            are currently available.")
        button.qc-pl-more ("Load More" — visible with exactly 4 of 5
            episodes shown; clicking it appends the 5th and the button then
            reports `is_visible() == False`, confirmed live, not assumed)

    AI Highlights popup (mounted on-demand by clicking a card's `.qc-pl-ai`
    button — NOT present in the initial harvest, same
    "state the script can't reach deterministically" condition documented
    in accessibility_tools_component.py's module docstring):
        div.qc-pl-popup-overlay (dimmed backdrop — clicking it closes the popup)
        div.qc-pl-popup[role=dialog?]
            button.qc-pl-popup-close[aria-label="Close"]
            span.qc-pl-popup-eyebrow ("AI Highlights")
            h3.qc-pl-popup-heading ("AI Episode Highlights")
            ul.qc-pl-popup-list > li (one per configured highlight point)
        Pressing Escape also closes the popup (confirmed live, standard
        dialog-dismiss behavior — no explicit keydown handler needed to be
        read, the close is observed via popup visibility going False)

        *** REAL, CONFIRMED LIVE FINDING (2026-09-21) — worth flagging back,
        not silently normalized ***: Episode 24's and Episode 23's popups
        render THE EXACT SAME two highlight strings verbatim ("Latest Episode
        Key Takeaway: Forum 2026 generated QAR 2.8B in bilateral agreements
        across 12 trade deals." / "Trending Topic: Digital trade corridors
        and blockchain-based cross-border transactions.") — confirmed via two
        separate live reads (open Episode 24's popup, close it, open Episode
        23's popup) rather than assumed from one read. This means TC 143593
        ("popup shows only the selected episode's highlights, not another
        episode's") is scripted to assert real per-episode distinctness and
        is EXPECTED TO FAIL live, surfacing this as a genuine product
        candidate bug rather than being weakened, skipped, or silently
        adjusted to pass (automation-standards.md's Result-integrity
        section) — flagged in this batch's report for the QA Manager/user to
        triage and decide on filing, per this project's own
        "confirm independently before filing" bug-filing convention (not
        filed here).

    Sticky player (`.qc-ppl`, mounted on first Play click, persists across
    later Play clicks on OTHER episodes — confirmed live: clicking a second
    card's Play button updates the SAME `.qc-ppl` instance's
    title/eyebrow/audio src rather than mounting a second instance):
        div.qc-ppl-meta > span.qc-ppl-thumb / span.qc-ppl-eyebrow ("Episode
            {n}") / span.qc-ppl-title
        div.qc-ppl-controls
            button.qc-ppl-back[aria-label="Skip back 15 seconds"]
            button.qc-ppl-play[aria-label="Pause"/"Play"] (toggles;
                confirmed live to carry class `is-playing` while playing)
            button.qc-ppl-fwd[aria-label="Skip forward 15 seconds"]
        div.qc-ppl-embed[hidden] > iframe.qc-ppl-embed-frame (Option-B
            embed slot — CONFIRMED LIVE always `hidden` on this environment;
            no live episode uses it, see the "Option-B" note above)
        audio.qc-ppl-audio (the real HTML5 <audio> element backing Option-A
            playback — CONFIRMED LIVE: all 5 live episodes' audio resolves to
            the SAME short ~19s placeholder file regardless of the row's own
            stated "NN MIN" duration badge — a real, live, worth-flagging
            mismatch between the displayed duration metadata and the actual
            playable audio length, not a locator issue)
        div.qc-ppl-progress-wrap > div.qc-ppl-bar[role=slider] (scrub/seek)
            > div.qc-ppl-bar-fill / div.qc-ppl-bar-knob
        span.qc-ppl-time ("0:00 / 0:19" format)
        div.qc-ppl-vol > button.qc-ppl-mute[aria-label="Mute"] +
            input.qc-ppl-vol-range (range input)
        div.qc-ppl-error (unavailable-audio message; CONFIRMED LIVE, both
            locales, via a genuine network-level simulation — see
            simulate_broken_audio() below, and the test module's TC 143589):
              EN: "This episode is currently unavailable. Please try again
                  later."
              AR: "يتعذّر تشغيل هذه الحلقة حالياً، يرجى المحاولة لاحقاً"
        button.qc-ppl-close[aria-label="Close player"]

    Subscription band (`.qc-podcast-subscribe`):
        p.qc-psub-banner[hidden][role=status]
        div.qc-psub-band
            div.qc-psub-icon[style*=background-image]
            h2.qc-psub-heading ("Never miss a new episode")
            p.qc-psub-desc
            form.qc-psub-form[novalidate]
                input.qc-psub-input[type=email][placeholder="Enter your email"]
                span.qc-psub-error[hidden][role=alert] (validation error text)
                button.qc-psub-submit ("Subscribe")
            p.qc-psub-status[hidden][role=status] (success/duplicate message
                — CONFIRMED LIVE, both hidden/shown via the SAME element, not
                two separate ones)

        *** REAL, CONFIRMED LIVE VALUES (2026-09-21), via real form
        submissions against this environment's real public subscription
        endpoint (synthetic, disposable `qa.podcast.test.<timestamp>@
        example.com` addresses — not destructive to any existing shared
        qcdev content, the same class of "genuine use of the public feature
        under test" already used for prior batches' newsletter/subscribe
        forms) ***:
          - Empty submit -> qc-psub-error: "This field is required." (MSG-5)
          - Whitespace-only (" ") submit -> qc-psub-error: "This field is
            required." (MSG-5) — CONFIRMED trimmed to empty before validation
          - Invalid format ("not-an-email") -> qc-psub-error: "Please enter a
            valid email address." (MSG-4)
          - Valid NEW email -> qc-psub-status: "You are subscribed! We will
            email you when a new episode is published." — NOT the case's own
            literal wording ("You have successfully subscribed to Qatar
            Chamber Podcast updates. Thank you for tuning in.") — a real,
            disclosed mismatch, asserted against the REAL observed text (see
            test module docstring's "Data adaptations" note, same convention
            as video_library/photo_albums batches)
          - Immediate re-submit of the SAME email -> qc-psub-status: "This
            email address is already subscribed." (matches MSG-6 wording
            from TC 143599 closely)
          - AR locale valid NEW email -> qc-psub-status: "تم اشتراكك! سنرسل
            لك بريدًا إلكترونيًا عند نشر حلقة جديدة." — again NOT the case's
            own literal AR wording, real text asserted instead
          - AR locale duplicate -> qc-psub-status: "هذا البريد الإلكتروني
            مشترك بالفعل" — MATCHES TC 143679's own stated wording exactly
          - Mixed-case ("QA.Podcast.Mixed.<ts>@Example.COM") and
            leading/trailing-whitespace-padded ("  qa.podcast.padded.<ts>@
            example.com  ") addresses both submit successfully with the SAME
            success status text and NO validation error — confirms
            front-end ACCEPTANCE of both; this batch has no CMS/Control_Panel
            access to open the stored subscriber record and confirm it was
            actually persisted lowercased/trimmed (TC 143820/143823's own
            second half) — see test module docstring

Admin-denial gap (TC 143542): no Podcast Control_Panel/admin management
URL is known or confirmed reachable on this environment this batch. Three
plausible slugs guessed by analogy to this project's OTHER object-admin
pages' `manage-<slug>` pattern (`manage-podcast`, `manage-podcast-episode`,
`manage-podcast-episodes`) all resolve to a generic "Coming Soon" 404
fallback for an ANONYMOUS visitor — not a login redirect, and not proof one
way or the other about RBAC on the real admin surface once it exists. Since
Control_Panel-tagged work is explicitly excluded from this batch and no
Podcast Control_Panel Page Object has been authored yet to confirm the real
admin path, TC 143542 is SKIPPED rather than asserted against a guessed URL
— see test module docstring.
"""

from config.settings import web_url
from core.web.base_page import BasePage

PODCAST_PATH = "/web/qatar-chamber/podcast"


class PodcastPage(BasePage):
    # ---- Hero -------------------------------------------------------------
    HERO = ".qc-podcast-hero"
    HERO_TITLE = ".qc-ph-title"
    HERO_DESC = ".qc-ph-desc"
    HERO_BADGES = ".qc-ph-badges"
    BADGE = ".qc-ph-badge"
    HOST = ".qc-ph-host"
    HOST_NAME = ".qc-ph-host-name"
    HOST_TITLE = ".qc-ph-host-title"
    HOST_AVATAR = ".qc-ph-host-avatar"
    PLATFORMS = ".qc-ph-platforms"
    PLATFORM_LINK = "a.qc-ph-platform"

    # ---- Breadcrumb ---------------------------------------------------------
    CRUMBS_NAV = ".qc-ph-crumbs"
    CRUMB = ".qc-ph-crumb"
    CRUMB_CURRENT = ".qc-ph-crumb.is-current"

    # ---- Episode listing ----------------------------------------------------
    LISTING = ".qc-podcast-listing"
    CARD = ".qc-pl-card"
    CARD_TITLE = ".qc-pl-title"
    CARD_DESC = ".qc-pl-desc"
    CARD_META_ITEM = ".qc-pl-meta-item"
    CARD_META_BADGE = ".qc-pl-meta-badge"
    CARD_AI_BTN = ".qc-pl-ai"
    CARD_PLAY_BTN = ".qc-pl-play"
    CARD_DOWNLOAD = "a.qc-pl-download"
    EMPTY = ".qc-pl-empty"
    MORE_BTN = ".qc-pl-more"

    # ---- AI Highlights popup ------------------------------------------------
    POPUP = ".qc-pl-popup"
    POPUP_OVERLAY = ".qc-pl-popup-overlay"
    POPUP_CLOSE = ".qc-pl-popup-close"
    POPUP_HEADING = ".qc-pl-popup-heading"
    POPUP_LIST_ITEM = ".qc-pl-popup-list li"

    # ---- Sticky player --------------------------------------------------
    PLAYER = ".qc-ppl"
    PLAYER_EYEBROW = ".qc-ppl-eyebrow"
    PLAYER_TITLE = ".qc-ppl-title"
    PLAYER_BACK = ".qc-ppl-back"
    PLAYER_PLAY = ".qc-ppl-play"
    PLAYER_FWD = ".qc-ppl-fwd"
    PLAYER_AUDIO = "audio.qc-ppl-audio"
    PLAYER_BAR = ".qc-ppl-bar"
    PLAYER_TIME = ".qc-ppl-time"
    PLAYER_MUTE = ".qc-ppl-mute"
    PLAYER_VOL_RANGE = ".qc-ppl-vol-range"
    PLAYER_ERROR = ".qc-ppl-error"
    PLAYER_CLOSE = ".qc-ppl-close"
    PLAYER_EMBED = ".qc-ppl-embed"
    PLAYER_EMBED_FRAME = ".qc-ppl-embed-frame"

    # ---- Subscription band --------------------------------------------------
    SUB_BAND = ".qc-podcast-subscribe"
    SUB_INPUT = ".qc-psub-input"
    SUB_SUBMIT = ".qc-psub-submit"
    SUB_ERROR = ".qc-psub-error"
    SUB_STATUS = ".qc-psub-status"
    SUB_HEADING = ".qc-psub-heading"
    SUB_DESC = ".qc-psub-desc"

    # The one real, live audio-source pattern every episode's Option-A audio
    # resolves through (see module docstring) — the network pattern
    # simulate_broken_audio() aborts, mirroring
    # accessibility_tools_component.py's real-bundle-block precedent.
    AUDIO_REQUEST_PATTERN = "**/o/qc-podcast/asset/episode/**/audio*"

    # Podcast Episodes Object Authoring admin URL (objectDefinitionId=50342)
    # — confirmed live 2026-09-22 while authoring disposable QCTEST
    # episodes (see test module's 143542/143529/143531/etc.).
    EPISODES_ADMIN_URL = (
        "https://qcdev.ihorizons.com/group/qatar-chamber/~/control_panel/manage"
        "?p_p_id=com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_C9D7"
        "&p_p_lifecycle=0&p_p_state=maximized&p_v_l_s_g_id=37246"
        "&_com_liferay_object_web_internal_object_definitions_portlet_ObjectDefinitionsPortlet_C9D7_objectDefinitionId=50342"
    )

    # ---- Navigation ----------------------------------------------------
    def open_podcast(self, locale: str = "en") -> "PodcastPage":
        self.open(web_url(PODCAST_PATH, locale=locale))
        self.wait_for(self.HERO_TITLE)
        return self

    def fetch_episode_audio_status(self, object_entry_id: str) -> int:
        """Direct HTTP GET on an episode's audio-asset API route (the same
        route the real Download link points at: `/o/qc-podcast/asset/
        episode/<id>/audio`) — used by TC 143628 to confirm an Unpublished
        episode's file is denied even via a known direct URL. Uses the
        page's own request context so a logged-out `page` fixture
        (`{"auth": False}`) issues this as a genuinely anonymous request."""
        url = f"https://qcdev.ihorizons.com/o/qc-podcast/asset/episode/{object_entry_id}/audio"
        response = self.page.request.get(url)
        return response.status

    def open_episodes_admin_as_visitor(self) -> None:
        """Navigates directly to the Podcast Episodes Object Authoring admin
        URL — used by TC 143542 with a logged-out `page` fixture
        (`{"auth": False}`) to confirm a Public Visitor is denied access.
        Uses open_anonymous() (never open()) so a login form encountered
        here does NOT silently re-authenticate the shared TEST_USER, which
        would defeat the whole point of this check."""
        self.open_anonymous(self.EPISODES_ADMIN_URL)

    def is_admin_entries_table_visible(self) -> bool:
        return self.page.locator("table").count() > 0

    def simulate_broken_audio(self) -> "PodcastPage":
        """MUST be called before open_podcast() — aborts every real episode
        audio-file request (AUDIO_REQUEST_PATTERN), the genuine network-level
        precondition for TC 143589's "unavailable/failed audio source" case
        (mirrors accessibility_tools_component.py's real-bundle-abort
        precedent — a real simulated failure against a real request, not an
        invented one)."""
        self.page.route(self.AUDIO_REQUEST_PATTERN, lambda route: route.abort())
        return self

    # ---- Hero queries ----------------------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def badge_texts(self) -> list:
        return self.page.locator(self.BADGE).all_text_contents()

    def host_name_text(self) -> str:
        return self.text(self.HOST_NAME)

    def host_title_text(self) -> str:
        return self.text(self.HOST_TITLE)

    def is_host_visible(self) -> bool:
        return self.is_visible(self.HOST)

    def platform_labels(self) -> list:
        return self.page.locator(self.PLATFORM_LINK).evaluate_all(
            "els => els.map(e => e.getAttribute('aria-label'))"
        )

    def platform_href(self, label: str) -> str:
        loc = self.page.locator(f'a.qc-ph-platform[aria-label="{label}"]')
        return loc.get_attribute("href") or ""

    def click_platform(self, label: str):
        """Clicks a platform link (all render target="_blank") and returns
        the new page/tab Playwright opens."""
        with self.page.context.expect_page() as new_page_info:
            self.page.locator(f'a.qc-ph-platform[aria-label="{label}"]').click()
        return new_page_info.value

    # ---- Breadcrumb queries -----------------------------------------------
    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.CRUMBS_NAV)

    def breadcrumb_texts(self) -> list:
        return self.page.locator(self.CRUMB).all_text_contents()

    def breadcrumb_current_text(self) -> str:
        return self.text(self.CRUMB_CURRENT)

    # ---- Episode listing queries --------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def card_titles(self) -> list:
        return self.page.locator(self.CARD_TITLE).all_text_contents()

    def card_by_title(self, title: str):
        return self.page.locator(self.CARD).filter(has_text=title).first

    def card_index_by_title(self, title: str) -> int:
        return self.card_titles().index(title)

    def episode_badge_text(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META_BADGE).text_content()

    def card_meta_texts(self, index: int) -> list:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_META_ITEM).all_text_contents()

    def is_ai_highlights_visible(self, index: int) -> bool:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_AI_BTN).count() > 0

    def click_ai_highlights(self, index: int) -> "PodcastPage":
        self.page.locator(self.CARD).nth(index).locator(self.CARD_AI_BTN).click()
        self.wait_for(self.POPUP)
        return self

    def click_play(self, index: int) -> "PodcastPage":
        self.page.locator(self.CARD).nth(index).locator(self.CARD_PLAY_BTN).click()
        self.wait_for(self.PLAYER)
        return self

    def is_download_visible(self, index: int) -> bool:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_DOWNLOAD).count() > 0

    def download_href(self, index: int) -> str:
        return self.page.locator(self.CARD).nth(index).locator(self.CARD_DOWNLOAD).get_attribute("href") or ""

    def is_empty_state_visible(self) -> bool:
        return self.is_visible(self.EMPTY)

    def empty_text(self) -> str:
        return self.text(self.EMPTY)

    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.MORE_BTN)

    def click_load_more(self) -> "PodcastPage":
        self.click(self.MORE_BTN)
        self.page.wait_for_timeout(600)
        return self

    def load_all_episodes(self) -> "PodcastPage":
        """Idempotent: clicks Load More only while it is visible."""
        while self.is_load_more_visible():
            self.click_load_more()
        return self

    # ---- AI Highlights popup queries ----------------------------------------
    def is_popup_visible(self) -> bool:
        return self.is_visible(self.POPUP)

    def popup_highlight_texts(self) -> list:
        return self.page.locator(self.POPUP_LIST_ITEM).all_text_contents()

    def close_popup_via_close_button(self) -> "PodcastPage":
        self.click(self.POPUP_CLOSE)
        return self

    def close_popup_via_overlay(self) -> "PodcastPage":
        """Clicks the dimmed backdrop at a corner offset, NOT its default
        center point — CONFIRMED live (TC 143527) the overlay spans the full
        viewport (e.g. 1920x1080) while the popup panel itself is a small
        centered box within it (e.g. x=720-1200, y=416.5-663.5 at the
        framework's 1920x1080 default), so Playwright's default center-click
        on the overlay lands ON the popup panel that's stacked on top of it,
        not on the exposed backdrop around it. A (10, 10) viewport-relative
        offset is always clear of that centered panel regardless of the
        popup's own (smaller) footprint."""
        self.click(self.POPUP_OVERLAY, position={"x": 10, "y": 10})
        return self

    def close_popup_via_escape(self) -> "PodcastPage":
        self.press_key("Escape")
        return self

    # ---- Sticky player queries/actions --------------------------------------
    def is_player_visible(self) -> bool:
        return self.is_visible(self.PLAYER)

    def player_title_text(self) -> str:
        return self.text(self.PLAYER_TITLE)

    def player_eyebrow_text(self) -> str:
        return self.text(self.PLAYER_EYEBROW)

    def is_player_playing(self) -> bool:
        cls = self.get_attribute(self.PLAYER_PLAY, "class") or ""
        return "is-playing" in cls

    def player_time_text(self) -> str:
        return self.text(self.PLAYER_TIME)

    def player_aria_label(self) -> str:
        return self.get_attribute(self.PLAYER_PLAY, "aria-label") or ""

    def click_player_play_pause(self) -> "PodcastPage":
        self.click(self.PLAYER_PLAY)
        return self

    def click_skip_forward(self) -> "PodcastPage":
        self.click(self.PLAYER_FWD)
        return self

    def click_skip_back(self) -> "PodcastPage":
        self.click(self.PLAYER_BACK)
        return self

    def seek_to_fraction(self, fraction: float) -> "PodcastPage":
        """Clicks the scrub bar at `fraction` (0..1) of its own width —
        the real, click-based way this bar's own `role="slider"` responds
        (confirmed live it is a click/drag target, not a native <input
        type=range>)."""
        bar = self.page.locator(self.PLAYER_BAR)
        box = bar.bounding_box()
        x = box["x"] + box["width"] * fraction
        y = box["y"] + box["height"] / 2
        self.page.mouse.click(x, y)
        return self

    def set_volume(self, value: float) -> "PodcastPage":
        """`value` in 0..1 — sets the native range input and dispatches an
        `input` event so the player's own JS listener picks it up (a bare
        `fill()`/attribute set does not fire the listener)."""
        self.page.locator(self.PLAYER_VOL_RANGE).evaluate(
            "(el, v) => { el.value = v; el.dispatchEvent(new Event('input', {bubbles: true})); }",
            value,
        )
        return self

    def volume_value(self) -> str:
        return self.page.locator(self.PLAYER_VOL_RANGE).input_value()

    def click_mute(self) -> "PodcastPage":
        self.click(self.PLAYER_MUTE)
        return self

    def is_muted(self) -> bool:
        label = self.get_attribute(self.PLAYER_MUTE, "aria-label") or ""
        return "unmute" in label.lower()

    def close_player(self) -> "PodcastPage":
        self.click(self.PLAYER_CLOSE)
        return self

    def is_player_error_visible(self) -> bool:
        return self.is_visible(self.PLAYER_ERROR)

    def player_error_text(self) -> str:
        return self.text(self.PLAYER_ERROR)

    def is_embed_visible(self) -> bool:
        """True once the Option-B external-embed iframe slot
        (`.qc-ppl-embed`) is unhidden — used by TC 143585."""
        return self.is_visible(self.PLAYER_EMBED)

    def embed_frame_src(self) -> str:
        return self.get_attribute(self.PLAYER_EMBED_FRAME, "src") or ""

    # ---- Subscription band queries/actions ----------------------------------
    def is_subscribe_band_visible(self) -> bool:
        return self.is_visible(self.SUB_BAND)

    def subscribe_heading_text(self) -> str:
        return self.text(self.SUB_HEADING)

    def subscribe_desc_text(self) -> str:
        return self.text(self.SUB_DESC)

    def subscribe_placeholder(self) -> str:
        return self.get_attribute(self.SUB_INPUT, "placeholder") or ""

    def subscribe(self, email: str) -> "PodcastPage":
        self.type(self.SUB_INPUT, email)
        self.click(self.SUB_SUBMIT)
        self.page.wait_for_timeout(1200)  # client-side async submit, no navigation to wait_for_url on
        return self

    def double_click_subscribe(self, email: str) -> "PodcastPage":
        """Types the email once, then fires the submit click TWICE back to
        back (no wait between) — the real reproduction of TC 143599's
        rapid-double-submit race-condition step. Polls (up to 5s) for the
        status element to become non-empty rather than a fixed wait —
        CONFIRMED live the rapid double-submit path can settle server-side
        slower than a fixed 1500ms; if it's still blank after the poll
        window, that surfaces as a real failure rather than being masked by
        a longer sleep."""
        self.type(self.SUB_INPUT, email)
        self.page.locator(self.SUB_SUBMIT).click()
        self.page.locator(self.SUB_SUBMIT).click()
        try:
            self.wait_for_condition(
                "sel => { const el = document.querySelector(sel); "
                "return !!el && el.textContent.trim().length > 0; }",
                arg=self.SUB_STATUS,
                timeout=5000,
            )
        except Exception:
            # A status that's still blank after the poll window is a real
            # observation (see TC 143599's own docstring/diagnosis), not a
            # wait-plumbing error — let the caller's own assertion on
            # subscribe_status_text() surface it rather than raising here.
            pass
        return self

    def subscribe_error_text(self) -> str:
        return self.text(self.SUB_ERROR)

    def subscribe_status_text(self) -> str:
        return self.text(self.SUB_STATUS)

    def is_subscribe_error_visible(self) -> bool:
        return self.is_visible(self.SUB_ERROR)

    def is_subscribe_status_visible(self) -> bool:
        return self.is_visible(self.SUB_STATUS)

    def subscribe_input_value(self) -> str:
        return self.page.locator(self.SUB_INPUT).input_value()

"""
web/pages/chamber_events/chamber_events_page.py — ChamberEventsPage /
ChamberEventDetailPage.

Public/web Page Object for PBI 130704 ("QC - Events - 001 - Chamber
Events") — the Chamber Events listing page, its per-event detail page, the
registration modal, and the Add-to-Calendar menu.

CONFIRMED LIVE 2026-09-22 (Playwright MCP, unauthenticated session against
`https://qcdev.ihorizons.com/web/qatar-chamber/events`, disclosed CLI-first
fallback per automation-standards.md's Tooling priority — the CLI
extractor's role/testid/id tiers alone surfaced the tab bar and the global
header/footer, but not the CSS-class-based card/modal internals, mirroring
the same gap already documented in home_business_events_page.py's own
module docstring):

  - Listing page controls form: `form.qc-chev-controls` containing the
    search input (`input.qc-chev-search-input[type="search"]`, placeholder
    "Search", `aria-label="Search events"` — NOT the global site-search
    overlay input, which is a separate `.qc-search-overlay__input` element
    reached via the header's "Search" link) and the status tablist
    (`div.qc-chev-tabs[role="tablist"]`, 4 `role="tab"` buttons:
    `data-qc-chev-tab="all|upcoming|ongoing|previous"`, text "All Events" /
    "Upcoming" / "Ongoing" / "Previous").
  - Section heading block: `p.qc-chev-eyebrow` ("Connect. Learn.
    Participate." on this dev data), `p.qc-chev-kicker` ("Chamber
    program"), `p.qc-chev-count` ("N events" — live count text).
  - Grid: `div.qc-chev-grid` containing `a.qc-chev-card` cards, each with
    `href="/web/qatar-chamber/events/event?id=<N>"`, `.qc-chev-card-media >
    img.qc-chev-card-img`, `.qc-chev-badges` (`.qc-chev-badge-<status>` +
    `.qc-chev-badge-sector`), `h3.qc-chev-card-title`, `.qc-chev-meta`
    date/time rows (`.qc-chev-meta-item`/`.qc-chev-meta-text`), and a
    `.qc-chev-venue` row. Confirmed statuses seen live: "Previous",
    "Upcoming" — CARD_BADGE_STATUS below is generic for any of
    Upcoming/Ongoing/Previous per the class-suffix pattern
    (`qc-chev-badge-<lowercased-status>`).
  - Detail page: Register control is `a[data-qc-ed-register]` (text
    contains "Register" — confirmed rendered as a role="button" link with
    an icon, no visible-text assertion made live beyond presence); Add to
    Calendar toggle is `button[data-qc-ed-calendar]`
    (`aria-expanded="false"|"true"`); its option menu items read
    "Google Calendar", "Outlook Calendar", "Download .ics file" (confirmed
    live via a direct button/link text scan — no single stable class was
    captured for the menu container itself in this pass, so
    CALENDAR_OPTION() below matches on that confirmed text, a Playwright
    `:text-is()` filter combined with a generic clickable-element role,
    which is stable regardless of the wrapping container's own class).
  - Registration modal: `div.qc-ed-modal`, fields addressed by real `id`
    attributes confirmed live: `#qc-ed-companyName`, `#qc-ed-attendeeName`,
    `#qc-ed-designation`, `#qc-ed-email` (type=email),
    `#qc-ed-mobileNumber` (type=tel), `#qc-ed-telephone` (type=tel),
    `#qc-ed-website`; Sectors of Interest is a set of unlabeled checkboxes
    inside the modal (confirmed live: 3 `input[type="checkbox"]` with no
    `name`/`id` — SECTOR_CHECKBOX() below scopes by the checkbox's own
    visible sibling label text, the confirmed-safe generic pattern for an
    unlabeled-input multi-select); submit is
    `button[data-qc-ed-submit][type="submit"]` (text "Submit
    registration"); close is `button[data-qc-ed-modal-close]` (`aria-label
    ="Close"`, text "×").
  - No live probe was done against a Registration-Limit-reached event, a
    Previous-event's ended sidebar card, the ICS/Outlook download
    artifacts themselves, dark-mode/high-contrast toggles, or RTL mirroring
    — those assertions in the test module use the SAME confirmed-live
    structural locators above (badges/cards/modal/buttons are
    locale/theme-agnostic by class name) plus a small number of
    `TODO(locator)`-marked constants below for the few elements that were
    not independently confirmed live this session (the ended-state
    sidebar card and the dark/high-contrast toggle controls, which belong
    to the shared `accessibility_tools`/`header` components elsewhere in
    this project, not to this feature's own DOM).
"""

import re

from core.web.base_page import BasePage
from config.settings import web_url


class ChamberEventsPage(BasePage):
    LISTING_PATH = "/web/qatar-chamber/events"

    # ---- Hero / section heading -------------------------------------------
    HERO_EYEBROW = "p.qc-chev-eyebrow"
    HERO_TITLE = "h1"
    HERO_SUBTITLE = ".qc-chev-hero p, .qc-chev-subtitle"
    HERO_BREADCRUMB = "nav[aria-label='Breadcrumb'], .breadcrumb"
    KICKER_LABEL = "p.qc-chev-kicker"
    EVENT_COUNT = "p.qc-chev-count"

    # ---- Controls: search + status tabs ------------------------------------
    CONTROLS_FORM = "form.qc-chev-controls"
    SEARCH_INPUT = "input.qc-chev-search-input"
    TABLIST = "div.qc-chev-tabs[role='tablist']"
    TAB = f"{TABLIST} [role='tab']"
    LOAD_MORE_BUTTON = "button:has-text('Load more')"

    TAB_ALL = "All Events"
    TAB_UPCOMING = "Upcoming"
    TAB_ONGOING = "Ongoing"
    TAB_PREVIOUS = "Previous"

    # ---- Grid / cards -------------------------------------------------------
    GRID = "div.qc-chev-grid"
    CARD = "a.qc-chev-card"
    CARD_IMAGE = ".qc-chev-card-img"
    CARD_TITLE = ".qc-chev-card-title"
    CARD_BADGES = ".qc-chev-badges"
    CARD_BADGE_SECTOR = ".qc-chev-badge-sector"
    CARD_META = ".qc-chev-meta"
    CARD_META_TEXT = ".qc-chev-meta-text"
    CARD_VENUE = ".qc-chev-venue"
    EMPTY_STATE = "[class*='chev-empty'], [class*='no-results']"

    def open_listing(self, locale: str | None = None) -> "ChamberEventsPage":
        path = self.LISTING_PATH if not locale else f"/{locale}{self.LISTING_PATH}"
        self.open(web_url(path))
        self.wait_for(self.TABLIST)
        return self

    def select_tab(self, tab_label: str) -> "ChamberEventsPage":
        # Tabs keep a fixed order in both locales, so the English label maps to
        # a position — lets the same call work on the Arabic (RTL) listing.
        order = [self.TAB_ALL, self.TAB_UPCOMING, self.TAB_ONGOING, self.TAB_PREVIOUS]
        if tab_label in order:
            self.page.locator(self.TAB).nth(order.index(tab_label)).click()
        else:
            self.click(f"{self.TABLIST} [role='tab']:text-is('{tab_label}')")
        self.page.wait_for_timeout(300)
        return self

    def active_tab_label(self) -> str:
        return self.page.locator(f"{self.TAB}[aria-selected='true']").inner_text().strip()

    def search(self, keyword: str) -> "ChamberEventsPage":
        box = self.page.locator(self.SEARCH_INPUT)
        box.fill(keyword)
        box.press("Enter")
        self.page.wait_for_timeout(400)
        return self

    def event_count_text(self) -> str:
        return self.text(self.EVENT_COUNT)

    def card_titles(self) -> list[str]:
        return self.page.locator(f"{self.CARD} {self.CARD_TITLE}").all_text_contents()

    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def _title_locator(self, title: str):
        # Regex match instead of a :text-is('...') string — titles can contain
        # quotes (e.g. "Novgorod Region's government") that break CSS parsing.
        return self.page.locator(
            self.CARD_TITLE, has_text=re.compile(rf"^\s*{re.escape(title.strip())}\s*$")
        )

    def card_for_title(self, title: str):
        return self.page.locator(self.CARD).filter(has=self._title_locator(title)).first

    def card_by_id(self, event_id: str):
        return self.page.locator(f"{self.CARD}[href*='?id={event_id}']")

    def has_card_with_title(self, title: str) -> bool:
        return self.page.locator(self.CARD).filter(has=self._title_locator(title)).count() > 0

    def is_empty_state_shown(self) -> bool:
        if self.card_count() > 0:
            return False
        return self.is_visible(self.EMPTY_STATE) or "no" in self.page.locator("body").inner_text().lower()

    def badge_status_for_title(self, title: str) -> str:
        card = self.card_for_title(title)
        return card.locator("[class*='qc-chev-badge-']:not(.qc-chev-badge-sector)").inner_text().strip()

    def sector_badge_for_title(self, title: str) -> str:
        return self.card_for_title(title).locator(self.CARD_BADGE_SECTOR).inner_text().strip()

    def open_first_card_in_tab(self, tab_label: str) -> "ChamberEventDetailPage":
        self.select_tab(tab_label)
        self.page.locator(self.CARD).first.click()
        # The card click is a client-side navigation — "load" is already
        # satisfied by the listing, so wait for the detail URL explicitly.
        self.page.wait_for_url(re.compile(r"/events/event\?id="))
        return ChamberEventDetailPage(self.page).wait_until_rendered()

    LOOKUP_API = "/o/qc-events-api/lookup?id={id}&languageId=en-US"

    def event_ids(self) -> list[str]:
        hrefs = self.page.locator(self.CARD).evaluate_all("els => els.map(e => e.getAttribute('href'))")
        return [h.split("id=")[-1] for h in hrefs if h and "id=" in h]

    def first_event_id_with_description(self) -> str | None:
        # Same public endpoint the detail page itself renders from.
        for event_id in self.event_ids():
            resp = self.page.request.get(web_url(self.LOOKUP_API.format(id=event_id)))
            if resp.ok and (resp.json().get("item", {}).get("eventDescription") or "").strip():
                return event_id
        return None

    def open_event_by_id(self, event_id: str) -> "ChamberEventDetailPage":
        self.open(web_url(f"/web/qatar-chamber/events/event?id={event_id}"))
        return ChamberEventDetailPage(self.page).wait_until_rendered()

    def click_load_more(self) -> "ChamberEventsPage":
        self.click(self.LOAD_MORE_BUTTON)
        self.page.wait_for_timeout(400)
        return self

    def is_load_more_visible(self) -> bool:
        return self.is_visible(self.LOAD_MORE_BUTTON)


class ChamberEventDetailPage(BasePage):
    RENDERED_MARKER = "h1.qc-ed-title"

    def wait_until_rendered(self) -> "ChamberEventDetailPage":
        # The detail body is filled in client-side after the URL settles; the
        # title is the last header piece to populate, so wait for real text.
        self.wait_for(self.RENDERED_MARKER, timeout=30000)
        self.page.wait_for_function(
            "s => (document.querySelector(s)?.textContent || '').trim().length > 0",
            arg=self.RENDERED_MARKER, timeout=30000,
        )
        return self

    # ---- Header -------------------------------------------------------------
    DETAIL_TITLE = "h1"
    DETAIL_BREADCRUMB = "nav[aria-label='Breadcrumb'], .breadcrumb"
    DETAIL_STATUS_BADGE = "[class*='qc-ed-badge-']:not([class*='sector'])"
    DETAIL_CATEGORY_TAG = "[class*='qc-ed-badge-sector']"
    HERO_IMAGE = "[class*='qc-ed-hero'] img, [class*='qc-ed-media'] img"

    # ---- Key info row ---------------------------------------------------------
    KEY_INFO_ROW = ".qc-ed-meta"

    # ---- Body sections --------------------------------------------------------
    OVERVIEW_SECTION = ".qc-ed-main > .qc-ed-rich >> nth=0"
    WHAT_TO_EXPECT_SECTION = "[class*='qc-ed-expect']"
    WHAT_TO_EXPECT_BULLET = "[class*='qc-ed-expect'] li"

    # ---- Sidebar / actions ------------------------------------------------------
    SIDEBAR = "[class*='qc-ed-sidebar'], aside"
    REGISTER_BUTTON = "[data-qc-ed-register]"
    ADD_TO_CALENDAR_BUTTON = "[data-qc-ed-calendar]"
    CALENDAR_OPTION_GOOGLE = ":text-is('Google Calendar')"
    CALENDAR_OPTION_OUTLOOK = ":text-is('Outlook Calendar')"
    CALENDAR_OPTION_ICS = ":text-is('Download .ics file')"
    # Confirmed live 2026-09-24 on a Previous event (id=167923).
    ENDED_CARD = ".qc-ed-status"
    ENDED_CARD_MESSAGE = f"{ENDED_CARD} :text('This event has ended')"
    CLOSED_MESSAGE_EN = ":text('Registration is currently closed as all available spots have been filled')"
    CLOSED_MESSAGE_AR = ":text('التسجيل مغلق حاليًا')"

    # ---- Registration modal ------------------------------------------------------
    MODAL = "div.qc-ed-modal"
    FIELD_COMPANY_NAME = "#qc-ed-companyName"
    FIELD_ATTENDEE_NAME = "#qc-ed-attendeeName"
    FIELD_DESIGNATION = "#qc-ed-designation"
    FIELD_EMAIL = "#qc-ed-email"
    FIELD_MOBILE = "#qc-ed-mobileNumber"
    FIELD_TELEPHONE = "#qc-ed-telephone"
    FIELD_WEBSITE = "#qc-ed-website"
    SUBMIT_BUTTON = "[data-qc-ed-submit]"
    MODAL_CLOSE_BUTTON = "[data-qc-ed-modal-close]"
    SUCCESS_MESSAGE = ":text('Your event registration has been submitted successfully')"
    INLINE_ERROR = "[class*='error'], [aria-invalid='true'] ~ *"

    def open_register_modal(self) -> "ChamberEventDetailPage":
        self.click(self.REGISTER_BUTTON)
        self.wait_for(self.MODAL)
        return self

    def close_modal(self) -> "ChamberEventDetailPage":
        self.click(self.MODAL_CLOSE_BUTTON)
        return self

    def fill_registration(
        self,
        company_name: str = "",
        attendee_name: str = "",
        designation: str = "",
        email: str = "",
        mobile: str = "",
        telephone: str = "",
        website: str = "",
    ) -> "ChamberEventDetailPage":
        if company_name:
            self.type(self.FIELD_COMPANY_NAME, company_name)
        if attendee_name:
            self.type(self.FIELD_ATTENDEE_NAME, attendee_name)
        if designation:
            self.type(self.FIELD_DESIGNATION, designation)
        if email:
            self.type(self.FIELD_EMAIL, email)
        if mobile:
            self.type(self.FIELD_MOBILE, mobile)
        if telephone:
            self.type(self.FIELD_TELEPHONE, telephone)
        if website:
            self.type(self.FIELD_WEBSITE, website)
        return self

    def sector_checkbox(self, label_text: str):
        """Sectors of Interest checkboxes are unlabeled `input[type=checkbox]`
        (confirmed live) — scoped by the checkbox's own row/sibling text,
        the confirmed-safe generic pattern for this modal."""
        return self.page.locator(
            f"{self.MODAL} label:has-text('{label_text}') input[type='checkbox'], "
            f"{self.MODAL} :has-text('{label_text}') >> input[type='checkbox']"
        ).first

    def field_value(self, field_selector: str) -> str:
        return self.page.locator(field_selector).input_value()

    def submit(self) -> "ChamberEventDetailPage":
        self.click(self.SUBMIT_BUTTON)
        self.page.wait_for_timeout(500)
        return self

    def is_success_shown(self) -> bool:
        return self.is_visible(self.SUCCESS_MESSAGE)

    def is_register_visible(self) -> bool:
        return self.is_visible(self.REGISTER_BUTTON)

    def is_add_to_calendar_visible(self) -> bool:
        return self.is_visible(self.ADD_TO_CALENDAR_BUTTON)

    def is_ended_card_shown(self) -> bool:
        return self.is_visible(self.ENDED_CARD_MESSAGE)

    def is_closed_message_shown_en(self) -> bool:
        return self.is_visible(self.CLOSED_MESSAGE_EN)

    def is_closed_message_shown_ar(self) -> bool:
        return self.is_visible(self.CLOSED_MESSAGE_AR)

    def open_calendar_menu(self) -> "ChamberEventDetailPage":
        self.click(self.ADD_TO_CALENDAR_BUTTON)
        self.page.wait_for_timeout(300)
        return self

    def calendar_option_labels(self) -> list[str]:
        candidates = ["Google Calendar", "Outlook Calendar", "Download .ics file"]
        return [c for c in candidates if self.page.locator(f":text-is('{c}')").count() > 0]

    def download_ics(self):
        with self.page.expect_download() as dl_info:
            self.click(f":text-is('Download .ics file')")
        return dl_info.value

    def status_badge_text(self) -> str:
        return self.text(self.DETAIL_STATUS_BADGE)

    def category_tag_text(self) -> str:
        return self.text(self.DETAIL_CATEGORY_TAG)

    def title_text(self) -> str:
        return self.text(self.DETAIL_TITLE)

    def breadcrumb_text(self) -> str:
        return self.text(self.DETAIL_BREADCRUMB)

    def overview_text(self) -> str:
        return self.text(self.OVERVIEW_SECTION)

    def what_to_expect_bullets(self) -> list[str]:
        return self.page.locator(self.WHAT_TO_EXPECT_BULLET).all_text_contents()

    def key_info_text(self) -> str:
        return self.text(self.KEY_INFO_ROW)

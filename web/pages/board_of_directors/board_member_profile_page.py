"""
web/pages/board_of_directors/board_member_profile_page.py — BoardMemberProfilePage.

Public-frontend Page Object for PBI 129398, the individual member profile
page at `/web/qatar-chamber/board-member?erc=QCDEMO-129398-member-<NN>`
(reached in practice by clicking a card on BoardOfDirectorsPage's listing —
the erc query param is server-assigned per member and not something a test
should hand-construct except for the fixed IDs confirmed live below).

DOM probe (mirroring board_of_directors_page.py's approach) against a live
profile page confirmed the real, stable `qc-bmp-*` ("board member profile")
custom classes:

    .qc-bmp-hero > .qc-bmp-hero-inner
        .qc-bmp-hero-eyebrow    ("Leadership & Governance")
        .qc-bmp-hero-title      (member full name, page title)
        .qc-bmp-hero-position   (position, below name)
        .qc-bmp-breadcrumb > .qc-bmp-crumb-home
    .qc-bmp-summary
        .qc-bmp-photo-wrap > .qc-bmp-photo
        .qc-bmp-badge (role badge pill — absent for grid-only Board Members
            per the case data; present for Chairman/Vice Chairmen/GM)
        .qc-bmp-name
        .qc-bmp-bio
        .qc-bmp-divider
        .qc-bmp-share[data-qc-share] > 5x a.qc-bmp-share-btn, each with a
            stable aria-label: "Share on Facebook" / "Share on X" /
            "Share on LinkedIn" / "Share on WhatsApp" / "Share on Telegram"
            (confirmed in that exact left-to-right order)
    .qc-bmp-biography  ("Biography" heading + .qc-bmp-rich body)
    .qc-bmp-experience ("Professional Experience" heading + .qc-bmp-exp-card)
        .qc-bmp-exp-item, each with .qc-bmp-exp-bullet / .qc-bmp-exp-role /
        .qc-bmp-exp-org

Audited all 18 live member profiles (member-01 .. member-18): every one has
both a populated Biography and Professional Experience section — there is no
bio-less / experience-less fixture in this environment (see the batch
report; 133442/133446 are BLOCKED, not scripted here).
"""

from core.web.base_page import BasePage

# Share buttons render in this fixed left-to-right order, confirmed live.
SHARE_BUTTON_LABELS = [
    "Share on Facebook",
    "Share on X",
    "Share on LinkedIn",
    "Share on WhatsApp",
    "Share on Telegram",
]


class BoardMemberProfilePage(BasePage):
    # ---- Hero ---------------------------------------------------------------
    HERO_EYEBROW = ".qc-bmp-hero-eyebrow"
    HERO_TITLE = ".qc-bmp-hero-title"
    HERO_POSITION = ".qc-bmp-hero-position"
    BREADCRUMB = ".qc-bmp-breadcrumb"
    BREADCRUMB_HOME_LINK = ".qc-bmp-crumb-home"

    # ---- Summary card ---------------------------------------------------------
    SUMMARY = ".qc-bmp-summary"
    PHOTO = ".qc-bmp-photo"
    BADGE = ".qc-bmp-badge"
    NAME = ".qc-bmp-name"
    BIO = ".qc-bmp-bio"
    DIVIDER = ".qc-bmp-divider"
    SHARE_ROW = ".qc-bmp-share"
    SHARE_BUTTON = ".qc-bmp-share-btn"

    # ---- Biography / Experience -----------------------------------------------
    BIOGRAPHY_SECTION = ".qc-bmp-biography"
    BIOGRAPHY_HEADING = ".qc-bmp-biography .qc-bmp-block-title"
    BIOGRAPHY_BODY = ".qc-bmp-biography .qc-bmp-rich"
    EXPERIENCE_SECTION = ".qc-bmp-experience"
    EXPERIENCE_HEADING = ".qc-bmp-experience .qc-bmp-block-title"
    EXPERIENCE_CARD = ".qc-bmp-exp-card"
    EXPERIENCE_ITEM = ".qc-bmp-exp-item"

    # ---- Navigation -----------------------------------------------------------
    def open_by_url(self, url: str) -> "BoardMemberProfilePage":
        self.open(url)
        return self

    def click_breadcrumb_home(self) -> None:
        self.click(self.BREADCRUMB_HOME_LINK)
        try:
            self.page.wait_for_url(lambda url: "board-member" not in url, timeout=15000)
        except Exception:
            pass  # surfaced by the caller's own URL assertion, not swallowed
        self.page.wait_for_load_state("domcontentloaded")

    # ---- Hero -------------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_position_text(self) -> str:
        return self.text(self.HERO_POSITION)

    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME_LINK)

    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.BREADCRUMB)

    # ---- Summary card -------------------------------------------------------------
    def is_summary_visible(self) -> bool:
        return self.is_visible(self.SUMMARY)

    def is_photo_visible(self) -> bool:
        return self.is_visible(self.PHOTO)

    def is_badge_visible(self) -> bool:
        return self.is_visible(self.BADGE)

    def badge_text(self) -> str:
        return self.text(self.BADGE)

    def name_text(self) -> str:
        return self.text(self.NAME)

    def bio_text(self) -> str:
        return self.text(self.BIO)

    def is_divider_visible(self) -> bool:
        return self.is_visible(self.DIVIDER)

    def share_button_count(self) -> int:
        return self.page.locator(self.SHARE_BUTTON).count()

    def share_button_labels_in_order(self) -> list:
        return self.page.locator(self.SHARE_BUTTON).evaluate_all(
            "els => els.map(e => e.getAttribute('aria-label'))"
        )

    # ---- Biography ------------------------------------------------------------------
    def is_biography_section_visible(self) -> bool:
        return self.is_visible(self.BIOGRAPHY_SECTION)

    def biography_heading_text(self) -> str:
        return self.text(self.BIOGRAPHY_HEADING)

    def biography_body_text(self) -> str:
        return self.text(self.BIOGRAPHY_BODY)

    # ---- Professional Experience ------------------------------------------------------
    def is_experience_section_visible(self) -> bool:
        return self.is_visible(self.EXPERIENCE_SECTION)

    def experience_heading_text(self) -> str:
        return self.text(self.EXPERIENCE_HEADING)

    def experience_item_count(self) -> int:
        return self.page.locator(self.EXPERIENCE_ITEM).count()

    def full_page_text(self) -> str:
        """For the negative "section is hidden entirely" cases (133442/
        133446, BLOCKED in this batch for lack of a fixture) — kept as a
        general helper for any similarly-shaped presence/absence assertion."""
        return self.page.locator("body").inner_text()

    def computed_style(self, locator, props: list) -> dict:
        handle = self.page.locator(locator).first
        return handle.evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

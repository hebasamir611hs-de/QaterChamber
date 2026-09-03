"""
web/pages/home_latest_news/home_latest_news_page.py — HomeLatestNewsPage.

Web/public Page Object for PBI 129372 (Home Page "Stay Connected &
Informed" / Latest News section) — counterpart to
cms/pages/home_latest_news/home_latest_news_admin_page.py.

CONFIRMED LIVE STRUCTURE (2026-09-02, headless Chromium against qcdev's
public Home Page, no auth):
  - `section.qc-home-latest-news` — real, stable CSS class, confirmed
    present in the DOM on page load (server-rendered content for this
    coupled/traditional Liferay project per cms-profile.md), carrying
    `data-qc-count`, `data-qc-view-all-url`, and `data-qc-detail-base`
    attributes.
  - Card structure: `.qc-ln-inner` > (head) + repeated `a.qc-ln-card` ->
    `.qc-ln-card-body` > `h3.qc-ln-card-title` (confirmed live: the card's
    own `href` embeds the News Article object entry id, e.g.
    `/web/qatar-chamber/news-article?id=48759`, and that id round-trips to
    the same row in the admin object-entries list at objectDefinitionId
    48649 — confirmed this session by cross-referencing the object entry
    ExternalReferenceCode `...129372-NEWS_ARTICLE` embedded in the card
    image's own `src` query string. This is the definitive proof the
    section is driven by this project's custom "News Articles" object
    (cms/pages/home_latest_news/home_latest_news_admin_page.py), not
    Liferay's native Web Content/Journal Articles.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeLatestNewsPage(BasePage):
    HOME_PATH = "/en/home"

    SECTION = "section.qc-home-latest-news"
    CARD = f"{SECTION} a.qc-ln-card"
    CARD_TITLE = f"{SECTION} .qc-ln-card-title"

    # Borrowed placeholder budget — see HomePromoBannersPage's own note:
    # not independently re-measured for this content type, per
    # cms-profile.md's "re-probe before assuming it generalizes" caveat.
    RELOAD_POLL_TIMEOUT_MS = 5000
    RELOAD_POLL_INTERVAL_MS = 500

    def open_home(self) -> "HomeLatestNewsPage":
        self.open(web_url(self.HOME_PATH))
        self.wait_for(self.SECTION, state="attached")
        return self

    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def article_visible_by_title(self, title: str) -> bool:
        """True if any Latest News card renders this title. Uses
        Playwright's own is_visible() (not mere DOM presence) so an
        unpublished/absent article is correctly reported absent."""
        try:
            locator = self.page.locator(f'{self.CARD_TITLE}:text-is("{title}")')
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

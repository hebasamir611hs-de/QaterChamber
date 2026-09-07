"""
web/pages/home_strategic_partners/home_strategic_partners_page.py —
StrategicPartnersPage.

Public-frontend Page Object for the Home Page's "Strategic Partners"
carousel (PBI 129391) — see home_strategic_partners_admin_page.py for the
Control_Panel counterpart that authors these records.

CONFIRMED LIVE this session (`/en/home`):
  - Section is identified by its own `<h2>Strategic Partners</h2>` heading.
  - Each partner's logo renders as `img.qc-sp-logo` with `alt` equal to that
    record's own authored "Logo Alt Text" field value verbatim (confirmed
    live for the 3 real active records: alt="QatarEnergy logo", "Qatar
    Airways logo", "QNB logo") — unlike Community Partners, whose alt is
    derived from Partner Name with no separate Alt Text field, this object
    has its own real Logo Alt Text field and the carousel uses it directly.
  - The carousel renders each logo MULTIPLE times (duplicated marquee/loop
    pattern, confirmed live: 12 `img.qc-sp-logo` for 3 active partners, 4
    copies each) — assertions here must be presence/absence via `alt`,
    never a raw count of `img.qc-sp-logo`.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class StrategicPartnersPage(BasePage):
    SECTION_HEADING = 'h2:text-is("Strategic Partners")'
    LOGO_BY_ALT = 'img.qc-sp-logo[alt="{alt}"]'

    def open_home(self) -> "StrategicPartnersPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION_HEADING)
        return self

    def is_logo_visible_by_alt(self, alt_text: str) -> bool:
        locator = self.page.locator(self.LOGO_BY_ALT.format(alt=alt_text))
        return locator.first.is_visible() if locator.count() > 0 else False

    def reload_until_logo_matches(self, alt_text: str, expected_visible: bool, timeout_ms: int = 15000, interval_ms: int = 1500) -> bool:
        """Poll (reload + re-check), never a bare sleep — mirrors
        CommunityPartnersPage.reload_until_logo_matches()'s established
        publish-then-verify precedent."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if self.is_logo_visible_by_alt(alt_text) == expected_visible:
                return True
            if time.monotonic() >= deadline:
                return self.is_logo_visible_by_alt(alt_text) == expected_visible
            self.page.wait_for_timeout(interval_ms)

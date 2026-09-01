"""
web/pages/home_community_partners/home_community_partners_page.py —
CommunityPartnersPage.

Public-frontend Page Object for the Home Page's "Community Partners"
carousel (PBI 129385) — see home_community_partners_admin_page.py for the
Control_Panel counterpart that authors these records.

CONFIRMED LIVE this session (2026-08-31, qcdev /en/home):
  - Section is identified by its own `<h2>Community Partners</h2>` heading.
  - Each partner's logo renders as `img.qc-partner-logo` with `alt` equal
    to that partner's Partner Name (EN) — confirmed live for all 3 real
    records (alt="QatarEnergy", alt="Qatar Airways", alt="QNB"). There is
    no separate authored Alt Text field (see admin Page Object's module
    docstring) — the carousel derives alt text from Partner Name (EN).
  - The carousel renders each logo MULTIPLE times (a duplicated marquee/
    loop pattern, confirmed live: 12 `img.qc-partner-logo` elements for 3
    real partners, 4 copies each) — assertions here must be
    presence/absence via `alt`, never a raw count of `img.qc-partner-logo`.

VERDICT (2026-09-01, framework-improvement review): a permanent dedicated
"QA-TEST Partner" record was considered as a safer alternative to
mutate-then-restore against the real "Qatar Airways" record for TC 135832.
NOT adopted. Reasoning is NOT a fixed-N layout concern — the marquee's
duplicated-loop rendering (3 real partners x 4 copies = 12 logos) is
consistent with a variable-length loop that would render a 4th partner the
same way it renders these 3, so no live evidence of count-based breakage
was found or claimed. The reasoning is that a permanent test record would
appear as a real logo in the LIVE public Home Page marquee for every real
visitor, not just in a test context — genuine content pollution regardless
of how gracefully the carousel scales. That is reason enough on its own.
TC 135832 continues to mutate-then-restore the real Qatar Airways record,
per cms-profile.md's TEST_OWNED-vs-real tradeoff — correctness over
convenience.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class CommunityPartnersPage(BasePage):
    SECTION_HEADING = 'h2:text-is("Community Partners")'
    PARTNER_LOGO_BY_ALT = 'img.qc-partner-logo[alt="{name}"]'

    def open_home(self) -> "CommunityPartnersPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION_HEADING)
        return self

    def is_partner_logo_visible(self, partner_name: str) -> bool:
        locator = self.PARTNER_LOGO_BY_ALT.format(name=partner_name)
        return self.page.locator(locator).first.is_visible() if self.page.locator(locator).count() > 0 else False

    def reload_until_logo_matches(self, partner_name: str, expected_visible: bool, timeout_ms: int = 8000, interval_ms: int = 1000) -> bool:
        """Poll (reload + re-check), never a bare sleep — cms-profile.md's
        confirmed ~0s propagation figure plus a conservative safety-margin
        poll, mirroring home_strategic_direction_page.py's reload_until_
        card_description_matches() precedent for this same class of
        publish-then-verify check."""
        import time

        deadline = time.monotonic() + (timeout_ms / 1000)
        while True:
            self.open_home()
            if self.is_partner_logo_visible(partner_name) == expected_visible:
                return True
            if time.monotonic() >= deadline:
                return self.is_partner_logo_visible(partner_name) == expected_visible
            self.page.wait_for_timeout(interval_ms)

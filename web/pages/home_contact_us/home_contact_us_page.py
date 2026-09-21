"""
web/pages/home_contact_us/home_contact_us_page.py — HomeContactUsPage.

Public-frontend counterpart to
cms/pages/home_contact_us/home_contact_us_admin_page.py, for PBI 129390's
Home Page "Contact Us" section (fragment "QC Home Contact Us").

CONFIRMED LIVE 2026-09-07 (headless Chromium, 1920x1080, un-authenticated
context, real qcdev Home Page HTML) — used ONLY to back TC-136498's public-
read assertion (see the admin-side test module docstring for why that test
is itself `@pytest.mark.skip`; this page object exists so the intended body
is real, not invented, once the Fields-panel product blocker clears):

  - Heading renders as `<h2 class="qc-contact-heading">Connect with Qatar
    Chamber to Move Your Business Forward</h2>` — confirmed live via
    `get_by_text("Connect with Qatar Chamber", exact=False)` resolving to
    exactly one element with this class.
  - Only the heading class was independently confirmed this session (the
    narrow scope needed for TC-136498's own assertion); Email Support/
    Telephone/Location/CTA selectors were NOT extracted — do not add them
    here as real until independently confirmed live, per this project's
    "never invent selectors as real" rule.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomeContactUsPage(BasePage):
    SECTION_HEADING = ".qc-contact-heading"

    def open_home(self, locale: str = "en") -> "HomeContactUsPage":
        self.open(web_url("/", locale=locale))
        return self

    def wait_for_section(self) -> "HomeContactUsPage":
        self.wait_for(self.SECTION_HEADING)
        return self

    def heading_text(self) -> str:
        return self.text(self.SECTION_HEADING)

    def reload_until_heading_matches(
        self, expected_text: str, timeout_ms: int = 5000, interval_ms: int = 500
    ) -> bool:
        """Poll (reload + re-check), never a bare sleep — same shape as
        HomeAboutSummaryPage.reload_until_heading_matches(), per
        cms-profile.md's Publish/Propagation Latency Budget guidance (not
        independently re-measured for this section; conservative default
        used)."""
        elapsed = 0
        while elapsed <= timeout_ms:
            self.open_home()
            self.wait_for_section()
            if self.heading_text() == expected_text:
                return True
            self.page.wait_for_timeout(interval_ms)
            elapsed += interval_ms
        return False

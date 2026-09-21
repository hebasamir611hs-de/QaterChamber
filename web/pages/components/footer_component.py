"""
web/pages/components/footer_component.py — FooterComponent.

Public-frontend Page Object for the REAL site-wide `<footer>`'s "Follow Us on
Social Media" section (PBI 129366, QC-GBL-004). Minimal, read-only query
surface — built to satisfy the "no locators in tests" rule
(.claude/context/active/standards.md).

ARCHITECTURE FIX (2026-09-16, this session — confirmed live, real qcdev Home
Page DOM, un-authenticated context): this class previously resolved to the
WRONG container. The live Home page has two genuinely separate, non-nested
DOM containers that (by coincidence) currently render the identical 9
production social hrefs, which made the bug invisible by href comparison
alone:
  - `div.qc-home-social`, heading exact text "Find us on social media" — the
    Home-page widget, PBI 129373 / QC-HOME-004B. See
    `web/pages/home_social_icons/home_social_icons_page.py`'s
    `HomeSocialIconsPage` for that container's own Page Object — THIS class
    does not target it.
  - `ul.qc-footer-social` inside the real `<footer>` element, heading exact
    text "Follow Us on Social Media" — the actual site footer, PBI 129366 /
    QC-GBL-004. THIS is what this class now targets.
Confirmed live this session: `footer div.qc-home-social` matches 0 elements
(not nested either way) — the two containers are siblings-at-large in the
page, not ancestor/descendant. The previous implementation located via
`get_by_text("Find us on social media")` (the HOME widget's own heading) then
walked two ancestor levels up — which resolves to `div.qc-home-social`, not
`footer`. Its old justification ("footer a also matches all 9 links at the
same hrefs") is void: proves nothing about which container was actually
matched, since both currently render the same 9 production entries.

CONFIRMED LIVE 2026-09-16 (scripted Playwright, real qcdev Home Page HTML,
un-authenticated context, this fix):
  - `footer ul.qc-footer-social` is a stable, unique (count=1) CSS scope —
    used directly below instead of a heading-text/ancestor walk.
  - The real footer's own heading, exact text "Follow Us on Social Media",
    confirmed live inside `<footer>` (distinct from the Home widget's "Find
    us on social media").
  - The 9 real production links inside this container, confirmed hrefs (in
    this FIXED left-to-right order — Facebook, X, LinkedIn, YouTube,
    Instagram, Snapchat, Flickr, Telegram, WhatsApp):
    `https://facebook.com/qatarchamber`, `https://x.com/qatarchamber`,
    `https://linkedin.com/company/qatarchamber`,
    `https://youtube.com/@qatarchamber`,
    `https://instagram.com/qatarchamber`,
    `https://snapchat.com/add/qatarchamber`,
    `https://www.flickr.com/photos/qatarchamber`,
    `https://t.me/qatarchamber`, `https://wa.me/97444559111`.
  - Each link DOES carry a real accessible name via `aria-label` (e.g.
    `aria-label="Facebook"`) — the earlier docstring's "empty accessible
    name" claim was itself wrong (only the link's own `textContent` is
    empty; `aria-label` is present and is what Playwright's accessible-name
    computation actually uses). Not relied upon here regardless: a
    freshly-created test entry's `aria-label` is still just one of the 9
    fixed Platform values, so `href` substring matching remains the only
    reliable per-entry identity signal for a test-created marker.
  - Only the 8 PBI-129366 fields (Display Order / Active Status, not the
    separate "Home Display Order" / "Show on Home" fields — see
    `cms/pages/components/footer_admin_component.py`'s Finding #1) were
    confirmed to drive THIS container; this class does not attempt to
    locate the separate Home-page widget instance of the same object.

COVERAGE GAP, flagged for the QA Manager / PBI 129366 (QC-GBL-004), not
resolved here: before this fix, NOTHING in this suite exercised this real
footer container — `FooterComponent` pointed at the Home widget instead, and
after this fix `FooterComponent` has zero callers (the 3 tests that used it,
131188/131194/131196, are PBI-129373/HOME-004B cases and were rewired to
`HomeSocialIconsPage`, the container their own intent actually needs — see
that Page Object's module docstring). This class remains correct and ready,
but no test currently exercises PBI 129366's own public-visibility
assertions (frontend position / active-status exclusion / draft-has-no-
effect) against the real footer — a genuine gap belonging to GBL-004's own
test design, not filled in as a side effect of this fix.
"""

from core.web.base_page import BasePage
from config.settings import web_url

FOOTER_HEADING_TEXT = "Follow Us on Social Media"
FOOTER_SOCIAL_CONTAINER = "footer ul.qc-footer-social"

# Confirmed live (see module docstring) — WhatsApp renders LAST among the 9
# real production icons, making it a tie-safe comparison target for a
# "does a newly Display-Order'd icon render EARLIER" check (unlike comparing
# against Facebook, whose own real Display Order value is unknown and could
# tie with a test-created entry also set to Display Order=1). Shared with
# `HomeSocialIconsPage` (imported from here) rather than redefined, since
# both containers currently render the identical 9 production hrefs.
PRODUCTION_WHATSAPP_HREF = "https://wa.me/97444559111"


class FooterComponent(BasePage):
    """Read-only query surface over the real public `<footer>`'s Social
    Media Icons section (`ul.qc-footer-social`). No admin/authoring actions
    — see `SocialMediaIconAdminPage`
    (`cms/pages/components/footer_admin_component.py`) for those."""

    def open_home(self, locale: str = "en") -> "FooterComponent":
        """Deliberately uses `BasePage.open_anonymous()`, never `open()` —
        see that method's own docstring: `open()` unconditionally
        reauthenticates on any non-login-flow URL if it detects a login
        form, which would silently re-authenticate an intentionally
        anonymous context (this Page Object's only intended use — see
        standards.md's "Draft/Unpublish Public-Visibility Checks —
        Mandatory Logged-Out Context")."""
        url = web_url("/", locale=locale)
        self.open_anonymous(url)
        self.page.get_by_text(FOOTER_HEADING_TEXT).first.wait_for(state="visible", timeout=10000)
        # The heading being visible does not guarantee the icon LINKS
        # underneath it have mounted yet — wait on the container's own
        # first real link (a condition, not a sleep) before any caller
        # reads `social_icon_hrefs()`, or a same-tick read could see a
        # short/empty link list and fail every test's own positive control.
        self._social_icon_links().first.wait_for(state="visible", timeout=10000)
        return self

    def _social_icon_links(self):
        return self.page.locator(FOOTER_SOCIAL_CONTAINER).get_by_role("link")

    def social_icon_hrefs(self) -> list:
        """Ordered list of every social icon link's `href`, left to right —
        the ordering IS the frontend's own rendered position, driven by each
        entry's Display Order (see module docstring)."""
        links = self._social_icon_links()
        return [links.nth(i).get_attribute("href") or "" for i in range(links.count())]

    def has_production_icons(self) -> bool:
        """Positive control — confirms the section container was actually
        found and holds real content, so a subsequent "our marker is absent"
        assertion cannot silently pass against an empty/wrong container."""
        return any(PRODUCTION_WHATSAPP_HREF in href for href in self.social_icon_hrefs())

    def has_icon_with_href_marker(self, marker: str) -> bool:
        return any(marker in href for href in self.social_icon_hrefs())

    def index_of_href_marker(self, marker: str) -> int:
        hrefs = self.social_icon_hrefs()
        for i, href in enumerate(hrefs):
            if marker in href:
                return i
        return -1

    def index_of_production_whatsapp(self) -> int:
        hrefs = self.social_icon_hrefs()
        for i, href in enumerate(hrefs):
            if PRODUCTION_WHATSAPP_HREF in href:
                return i
        return -1

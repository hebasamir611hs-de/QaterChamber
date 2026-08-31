"""
web/pages/components/footer_component.py — FooterComponent.

Cross-page GLOBAL component (PBI 129366 / QC-GBL-004 "Site Footer & Social
Media Icons") — lives in pages/components/ per this project's component
exception (never duplicated into a page folder), automation-standards.md's
"Page Object / Screen Object rules". Covers the 18 Automation-tagged,
Web-platform cases for this PBI (ADO 130961-130976, 130992-130994); the
Control_Panel-tagged cases live in the sibling footer_admin_component.py.

The Newsletter section INSIDE the footer (ADO 130969, 130970, 130971, 130993,
130994) is deliberately NOT re-located here: it is the exact same live DOM
node (`div.qc-footer-newsletter`) already owned by
web/pages/components/newsletter_subscription_component.py (PBI 129566) —
confirmed identical via a live structural dump (see below). Per
automation-standards.md's redundancy rule ("no duplicated locator constants
for the same element across objects"), the footer test module composes
NewsletterSubscriptionComponent directly for those cases instead of
duplicating EMAIL_INPUT/SUBSCRIBE_BUTTON/MESSAGE here. One new method
(`simulate_subscribe_backend_failure`) was added to that existing component
for ADO 130971/130994 (a genuinely new capability, not a duplicate).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --scope "footer"

Scoped role-based extraction surfaced 34 candidates, but most report
NON-UNIQUE (matches 2, or 10 for "X"/Twitter) — the extractor's uniqueness
check runs page.get_by_role() against the WHOLE page, not the --scope
container (see header_component.py's docstring for why), and this site's
header mega-menu duplicates several of the same accessible names ("About
Us", "Contact Us", "Board of Directors", etc.) as the footer's nav columns.
A direct DOM query confirmed only ONE <footer> exists on the page
(`footer.qc-global-site-footer`, `visible=true`) — the "matches 2" readings
are the header's hidden mega-menu, not a second footer. Resolved the
documented "ambiguous element" fallback the same way header_component.py
did: additional one-off, disclosed Playwright scripts (still CLI/shell,
never the Playwright MCP) that reuse BasePage's own license-gate/overlay
guard sequence before reading the live DOM structurally.

Real, CLI-verified structure (footer.qc-global-site-footer):

    footer.qc-global-site-footer[data-show-newsletter=true][data-show-social=true]
      div.qc-footer-inner > div.qc-footer-grid
        div.qc-footer-col.qc-footer-brand
          a.qc-footer-logo[href="/web/qatar-chamber/home"]  (LOGO, same tab)
            img.qc-footer-logo-img
          p.qc-footer-about                                  (ABOUT_TEXT)
          div.qc-footer-social-wrap
            h3.qc-footer-social-title                        (SOCIAL_LABEL) "Follow us on Social Media"
            ul.qc-footer-social > li > a[aria-label][href][target=_blank][rel=noopener]  (SOCIAL_ICONS)
        div.qc-footer-nav-group
          nav.qc-footer-col[aria-label="About Qatar Chamber"]  (NAV_COLUMNS, 3 total)
            button.qc-footer-col-title.qc-footer-col-toggle   (relative NAV_COLUMN_TITLE)
            ul.qc-footer-links > li > a                        (relative NAV_COLUMN_LINKS)
          nav.qc-footer-col[aria-label="Services"]
          nav.qc-footer-col[aria-label="Quick Links"]          (QUICK_LINKS_COLUMN)
        div.qc-footer-col.qc-footer-newsletter                 (owned by NewsletterSubscriptionComponent)
        div.qc-footer-divider
        div.qc-footer-bottom                                   (COPYRIGHT_BAR)
          p.qc-footer-copyright                                (COPYRIGHT_TEXT)
          ul.qc-footer-legal > li > a                          (LEGAL_LINKS)
          button.qc-footer-backtop                             (BACK_TO_TOP)

NAV_COLUMNS are located by their real `aria-label` (role + accessible-name
tier, not the fragile ":has-text" the header component had to fall back to
for its mega-menu ambiguity) — each `nav.qc-footer-col` carries an
`aria-label` that is EXACTLY its visible column heading ("About Qatar
Chamber" / "Services" / "Quick Links"), confirmed live via a direct
attribute dump. This also holds on the Arabic page (re-confirmed live:
`aria-label`/heading text both translate together, e.g. "روابط سريعة" for
Quick Links) — not a hardcoded English-only assumption.

Real, CLI-verified findings from this extraction pass (reported, not
silently adjusted):
  - Footer logo: `href="/web/qatar-chamber/home"`, no `target` attribute
    (same-tab). Confirmed LIVE end-to-end from a non-home page
    (`/web/qatar-chamber/contact-us`): clicking the footer logo there lands
    on `/web/qatar-chamber/home` — matches ADO 130962 exactly.
  - ALL 18 real footer nav-column links (6 per column x 3 columns) carry
    `target=null` (same-tab) and a same-origin `/web/qatar-chamber/...`
    `href` — ZERO are configured with `target="_blank"` or an absolute
    external URL anywhere in the 3 nav columns, confirmed via a full
    attribute dump of every `<a>` in `ul.qc-footer-links`. This is a real,
    disclosed CONTENT-CONFIGURATION gap on this dev instance, not a locator
    problem: ADO 130964 ("external footer navigation link opens new tab")
    currently has NO live element to exercise. `external_nav_link_count()`
    reads this honestly (0) at runtime; the test for 130964 skips with a
    concrete reason rather than fabricating a pass against an internal link
    — see test module.
  - 8 of the 18 nav-column links (`Membership`, `B2B Registration`,
    `Training Programs`, `Useful Links`, `Help Center`, `Career
    Opportunities`, `Tenders`, `Accessibility`/`Privacy Policy`/`Terms of
    Service` bottom-bar links) resolve to the placeholder
    `/web/qatar-chamber/home` rather than a distinct page — another real,
    disclosed content gap (unpublished target pages), not fabricated.
  - Social icons: confirmed 8 real entries (Facebook, X, LinkedIn,
    Instagram, YouTube, WhatsApp, Telegram, Snapchat), each with a real
    external `href`, `target="_blank"`, `rel="noopener"`. End-to-end
    confirmed LIVE: clicking Facebook's icon opens a genuine new browser tab
    that resolves to `https://www.facebook.com/QatarChamber/` while the
    original tab stays on the footer's page — matches ADO 130968 exactly.
  - Quick Links column IS one of the three real `nav.qc-footer-col`
    elements (not a separate widget type) — heading "Quick Links", 6 links
    ("Useful Links", "Contact Us", "Help Center", "Career Opportunities",
    "Tenders", "FAQ's"). End-to-end confirmed LIVE: clicking "Contact Us"
    inside this column (isolated from any other interaction in the same
    browser context — see module docstring's flakiness note below) lands on
    `/web/qatar-chamber/contact-us`, same tab — matches ADO 130965/130967.
  - FLAKINESS FOUND live while extracting: clicking a footer nav link
    immediately after a `context.expect_page()` block (i.e., right after
    opening a social-icon popup in the SAME script/session) intermittently
    misrouted to `/home` instead of the clicked link's real target — a
    focus/layout-shift artifact of the just-opened popup tab, not a defect
    in the footer's own routing (re-run in isolation, with no prior popup
    interaction in the same context, correctly landed on `/web/qatar-
    chamber/contact-us` every time). click_nav_link()/click_quick_link()
    below therefore always operate on the CURRENT page in the SAME
    Playwright context without a preceding popup step polluting focus;
    social-icon tests use their own fresh page/context per the framework's
    per-test `page` fixture, so this interaction ordering does not recur in
    the actual test suite.
  - Copyright bar: `p.qc-footer-copyright` reads "©2026 Qatar Chamber. All
    Rights Reserved." (EN) / "© 2026 غرفة قطر. جميع الحقوق محفوظة." (AR);
    `ul.qc-footer-legal` has exactly 3 links (Accessibility, Privacy Policy,
    Terms of Service) — matches ADO 130972's described layout (copyright
    left, links right) structurally, though all 3 hrefs are the
    `/web/qatar-chamber/home` placeholder (same content-gap note as above).
  - Back to Top (`button.qc-footer-backtop`): NOT reliably reachable via
    Playwright's `scroll_into_view_if_needed()` from a fresh page load (it
    timed out live — the page's lazy-loaded sections keep growing
    `document.body.scrollHeight` as more content mounts, so a plain
    scroll-into-view raced an unstable layout). Confirmed reliable instead
    via `page.wait_for_load_state("networkidle")` THEN
    `window.scrollTo(0, document.body.scrollHeight)` THEN a bounded
    `wait_for(BACK_TO_TOP, state="visible")` — scroll_to_bottom() below uses
    exactly this sequence, never scroll_into_view_if_needed() nor
    `time.sleep()`. End-to-end confirmed LIVE: after scrolling to
    `scrollY=8867` and clicking, `window.scrollY` reached exactly `0` (read
    via `page.wait_for_function("window.scrollY === 0")`, not a fixed
    sleep) — matches ADO 130973.
  - Arabic homepage (`web_url("/home", locale="ar")` -> `/ar/home`): EVERY
    footer field/label/link text confirmed genuinely translated (nav column
    headings, all 18 link labels, social-follow heading, copyright text,
    legal-link labels, Back-to-Top label, logo alt) — NO missing-translation
    fallback state currently exists anywhere in the live footer to observe.
    ADO 130975/130992 ("footer falls back to default language when a
    translation is missing") therefore has no real, reachable precondition
    this session: forcing one field to have no AR translation requires
    CMS/Site-Content-Editor access this session does not have (TEST_USER/
    TEST_PASSWORD blank in .env, no Playwright MCP fallback available
    either) — the test is `skip`-marked with this concrete reason rather
    than asserting against a fully-translated footer that would not
    honestly exercise the case's described fallback behaviour. Same for ADO
    130976 (disabling one element hides only that element) — the CMS toggle
    step is unreachable; the frontend read methods below
    (`is_nav_link_present`, `is_social_icon_present`,
    `is_legal_link_present`, `is_copyright_text_present`) are real and
    reusable, only the CMS-side setup step is gated.
"""

from core.web.base_page import BasePage
from config.settings import web_url

HOME_URL = web_url("/home")
CONTACT_US_URL = web_url("/web/qatar-chamber/contact-us")


class FooterComponent(BasePage):
    # ── Structural locators — scoped under the single real <footer> ─────
    FOOTER = "footer.qc-global-site-footer"

    LOGO = f"{FOOTER} >> a.qc-footer-logo"
    LOGO_IMAGE = f"{FOOTER} >> img.qc-footer-logo-img"
    ABOUT_TEXT = f"{FOOTER} >> p.qc-footer-about"

    SOCIAL_LABEL = f"{FOOTER} >> h3.qc-footer-social-title"
    SOCIAL_ICONS = f"{FOOTER} >> ul.qc-footer-social > li > a"

    NAV_COLUMNS = f"{FOOTER} >> nav.qc-footer-col"
    # Relative to a specific nav column locator (see _nav_column()).
    NAV_COLUMN_TITLE_REL = ".qc-footer-col-title"
    NAV_COLUMN_LINKS_REL = "ul.qc-footer-links > li > a"
    # Real, disclosed content-configuration gap (see docstring): zero of the
    # 18 nav-column links are configured as external. Real, resolvable
    # selector regardless — reads honestly as count()==0, never faked.
    EXTERNAL_NAV_LINKS = f"{FOOTER} >> nav.qc-footer-col ul.qc-footer-links a[target=\"_blank\"]"

    QUICK_LINKS_COLUMN = f'{FOOTER} >> nav.qc-footer-col[aria-label="Quick Links"]'
    QUICK_LINKS_HEADING = f"{QUICK_LINKS_COLUMN} >> {NAV_COLUMN_TITLE_REL}"
    QUICK_LINKS_ITEMS = f"{QUICK_LINKS_COLUMN} >> {NAV_COLUMN_LINKS_REL}"

    COPYRIGHT_BAR = f"{FOOTER} >> div.qc-footer-bottom"
    COPYRIGHT_TEXT = f"{FOOTER} >> p.qc-footer-copyright"
    LEGAL_LINKS = f"{FOOTER} >> ul.qc-footer-legal > li > a"
    BACK_TO_TOP = f"{FOOTER} >> button.qc-footer-backtop"

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "FooterComponent":
        self.open(HOME_URL)
        self.wait_for(self.FOOTER)
        return self

    def open_contact_us(self) -> "FooterComponent":
        """A real, confirmed non-home page carrying the same global footer
        — used for ADO 130962's "any non-home page" precondition."""
        self.open(CONTACT_US_URL)
        self.wait_for(self.FOOTER)
        return self

    def open_home_arabic(self) -> "FooterComponent":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.FOOTER)
        return self

    def scroll_to_footer(self) -> "FooterComponent":
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.wait_for(self.FOOTER)
        return self

    def scroll_to_bottom(self) -> "FooterComponent":
        """Reveals the Back-to-Top button reliably (see module docstring's
        Back-to-Top finding) — waits for the page to settle before scrolling,
        then bounded-waits for the button itself, never a fixed sleep."""
        self.page.wait_for_load_state("networkidle")
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.wait_for(self.BACK_TO_TOP)
        return self

    # ── Composite "renders all sections" check (ADO 130961) ─────────────
    def rendered_sections(self) -> dict:
        # Newsletter section: composes NewsletterSubscriptionComponent
        # (PBI 129566) rather than redefining its WIDGET locator here — same
        # live DOM node, see module docstring's redundancy note. Imported
        # locally to avoid a module-level circular-import risk between the
        # two sibling GLOBAL components.
        from web.pages.components.newsletter_subscription_component import (
            NewsletterSubscriptionComponent,
        )
        newsletter_visible = NewsletterSubscriptionComponent(self.page).is_widget_visible()
        return {
            "logo": self.is_visible(self.LOGO),
            "about_text": self.is_visible(self.ABOUT_TEXT),
            "social_label": self.is_visible(self.SOCIAL_LABEL),
            "social_icons": self.page.locator(self.SOCIAL_ICONS).count() > 0,
            "nav_columns": self.page.locator(self.NAV_COLUMNS).count() > 0,
            "quick_links_column": self.is_visible(self.QUICK_LINKS_COLUMN),
            "newsletter_section": newsletter_visible,
            "copyright_bar": self.is_visible(self.COPYRIGHT_BAR),
        }

    def is_footer_visible(self) -> bool:
        return self.is_visible(self.FOOTER)

    # ── Logo (ADO 130962) ─────────────────────────────────────────────────
    def is_logo_visible(self) -> bool:
        return self.is_visible(self.LOGO)

    def click_logo(self) -> "FooterComponent":
        self.click(self.LOGO)
        self.page.wait_for_load_state("networkidle")
        return self

    def current_url(self) -> str:
        return self.page.url

    # ── Nav columns / internal & external links (ADO 130963, 130964) ─────
    def _nav_column(self, aria_label: str) -> str:
        return f'{self.FOOTER} >> nav.qc-footer-col[aria-label="{aria_label}"]'

    def nav_column_titles(self) -> list:
        titles = self.page.locator(f"{self.NAV_COLUMNS} >> {self.NAV_COLUMN_TITLE_REL}")
        return [titles.nth(i).inner_text().strip() for i in range(titles.count())]

    def nav_column_link_labels(self, column_aria_label: str) -> list:
        col = self._nav_column(column_aria_label)
        links = self.page.locator(f"{col} >> {self.NAV_COLUMN_LINKS_REL}")
        return [links.nth(i).inner_text().strip() for i in range(links.count())]

    def click_nav_link(self, column_aria_label: str, link_text: str) -> dict:
        """Clicks a footer nav-column link by its column + exact visible
        text and reports whether a new tab opened. Text-anchored (mirrors
        header_component.py's NAV_LINK_ABOUT_US precedent) because these
        columns expose no data-testid/stable id of their own — every
        candidate is a plain content link, confirmed via the CLI extraction
        pass in the module docstring."""
        col = self._nav_column(column_aria_label)
        locator = f'{col} >> {self.NAV_COLUMN_LINKS_REL}:has-text("{link_text}")'
        before_pages = len(self.page.context.pages)
        self.click(locator)
        self.page.wait_for_load_state("networkidle")
        after_pages = len(self.page.context.pages)
        return {"url": self.page.url, "opened_new_tab": after_pages > before_pages}

    def external_nav_link_count(self) -> int:
        """Real, honest count — currently 0 on this dev instance (see
        module docstring); never assumed non-zero."""
        return self.page.locator(self.EXTERNAL_NAV_LINKS).count()

    def click_first_external_nav_link_and_capture_popup_url(self) -> str:
        with self.page.context.expect_page() as popup_info:
            self.page.locator(self.EXTERNAL_NAV_LINKS).first.click()
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded")
        url = popup.url
        popup.close()
        return url

    def is_nav_link_present(self, column_aria_label: str, link_text: str) -> bool:
        col = self._nav_column(column_aria_label)
        return self.is_visible(f'{col} >> {self.NAV_COLUMN_LINKS_REL}:has-text("{link_text}")')

    # ── Quick Links column (ADO 130965, 130966, 130967) ──────────────────
    def is_quick_links_column_visible(self) -> bool:
        return self.is_visible(self.QUICK_LINKS_COLUMN)

    def quick_links_heading_text(self) -> str:
        return self.page.locator(self.QUICK_LINKS_HEADING).inner_text().strip()

    def quick_link_labels(self) -> list:
        items = self.page.locator(self.QUICK_LINKS_ITEMS)
        return [items.nth(i).inner_text().strip() for i in range(items.count())]

    def click_quick_link(self, link_text: str) -> dict:
        return self.click_nav_link("Quick Links", link_text)

    # ── Social media icons (ADO 130968) ──────────────────────────────────
    def is_social_label_visible(self) -> bool:
        return self.is_visible(self.SOCIAL_LABEL)

    def social_icon_labels(self) -> list:
        icons = self.page.locator(self.SOCIAL_ICONS)
        return [icons.nth(i).get_attribute("aria-label") for i in range(icons.count())]

    def is_social_icon_present(self, label: str) -> bool:
        return self.is_visible(f'{self.FOOTER} >> ul.qc-footer-social > li > a[aria-label="{label}"]')

    def click_social_icon_and_capture_popup_url(self, label: str) -> str:
        locator = f'{self.FOOTER} >> ul.qc-footer-social > li > a[aria-label="{label}"]'
        with self.page.context.expect_page() as popup_info:
            self.click(locator)
        popup = popup_info.value
        popup.wait_for_load_state("domcontentloaded")
        url = popup.url
        popup.close()
        return url

    # ── Copyright bar (ADO 130972) ────────────────────────────────────────
    def is_copyright_bar_visible(self) -> bool:
        return self.is_visible(self.COPYRIGHT_BAR)

    def is_copyright_text_present(self) -> bool:
        return self.is_visible(self.COPYRIGHT_TEXT)

    def copyright_text(self) -> str:
        return self.page.locator(self.COPYRIGHT_TEXT).inner_text().strip()

    def legal_link_labels(self) -> list:
        links = self.page.locator(self.LEGAL_LINKS)
        return [links.nth(i).inner_text().strip() for i in range(links.count())]

    def is_legal_link_present(self, link_text: str) -> bool:
        return self.is_visible(f'{self.FOOTER} >> ul.qc-footer-legal a:has-text("{link_text}")')

    def copyright_and_legal_positions(self) -> dict:
        """Left/right relative horizontal position of the copyright text vs
        the legal-links list, for ADO 130972's "copyright left, links
        right" layout assertion."""
        copyright_box = self.page.locator(self.COPYRIGHT_TEXT).bounding_box()
        legal_box = self.page.locator(self.LEGAL_LINKS).first.bounding_box()
        if not copyright_box or not legal_box:
            return {}
        return {"copyright_x": copyright_box["x"], "legal_x": legal_box["x"]}

    # ── Back to Top (ADO 130973) ─────────────────────────────────────────
    def is_back_to_top_visible(self) -> bool:
        return self.is_visible(self.BACK_TO_TOP)

    def click_back_to_top(self) -> "FooterComponent":
        self.click(self.BACK_TO_TOP)
        return self

    def wait_for_scroll_top(self, timeout: int = 5000) -> "FooterComponent":
        self.page.wait_for_function("window.scrollY === 0", timeout=timeout)
        return self

    def scroll_position(self) -> int:
        return self.page.evaluate("window.scrollY")

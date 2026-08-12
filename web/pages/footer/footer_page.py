"""
web/pages/footer/footer_page.py — FooterPage.

Public-facing Site Footer (PBI 133231 "QC-GBL-004 — Site Footer & Social Media
Icons"). All locators below were extracted CLI-first via
tools/extract_locators.py against the live homepage at the framework's
default viewport (1920x1080):

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --scope footer

The first extractor run returned every footer control (role-based, unique):
button "About Qatar Chamber"/"Services"/"Quick Links" (column toggles),
link "Chairman's Message" … "FAQ's" (nav/quick links), textbox "Email
address", button "Subscribe", link "Accessibility"/"Privacy Policy"/
"Terms of Service" (bottom bar), plus the 8 social links (Facebook, X,
LinkedIn, Instagram, YouTube, WhatsApp, Telegram, Snapchat) which the
extractor flagged NON-UNIQUE by role+name only because `get_by_role` is
evaluated page-wide and this dev build repeats the same social block
outside <footer> (a "Contact us" widget in <main>) — confirmed by
disclosed Playwright-MCP fallback (browser_evaluate scoped to
`document.querySelector('footer')`) after the CLI hit the site's
Liferay "developer mode connection limit" redirect once (a
state that could not be reached deterministically by script alone until
the one-time reset link was followed — see the automation report for the
full disclosure). That inspection confirmed the real, stable, footer-scoped
markup used below (all classnames are the site's own `qc-*` hooks, i.e.
already-stable "data-testid-equivalent" selectors — CSS tier, scoped to
`footer` so they never collide with the duplicate block elsewhere on the
page):

    footer.qc-global-site-footer            - footer root
    .qc-footer-brand                        - branding column (logo + description)
    a.qc-footer-logo / img.qc-footer-logo-img
    .qc-footer-social-wrap / h3.qc-footer-social-title / ul.qc-footer-social
    a.qc-social-link[aria-label=...] / img.qc-social-img[alt=...]
    button.qc-footer-col-toggle             - "About Qatar Chamber" / "Services" / "Quick Links"
    a.qc-footer-link                        - every nav/quick/bottom link (unique by visible text)
    h3.qc-footer-col-title                  - newsletter heading (only <h3> with this class)
    .qc-footer-newsletter-text              - newsletter description
    input.qc-footer-input / button.qc-footer-subscribe
    p.qc-footer-copyright / div.qc-footer-bottom
    button.qc-footer-backtop

No public-page TODOs remain in this Page Object — every element the 184
cases reference on the live footer was reachable and resolved to a real,
unique selector.
"""

from config.settings import web_url
from core.web.base_page import BasePage

HOME_URL = web_url("/home")


class FooterPage(BasePage):
    # ---- Structure ---------------------------------------------------
    FOOTER = "footer.qc-global-site-footer"
    BRAND_COLUMN = "footer .qc-footer-brand"

    # ---- Branding (logo + description) -------------------------------
    LOGO_LINK = "footer .qc-footer-brand a.qc-footer-logo"
    LOGO_IMG = "footer .qc-footer-brand img.qc-footer-logo-img"
    DESCRIPTION = "footer .qc-footer-brand p"

    # ---- Social media ---------------------------------------------------
    SOCIAL_WRAP = "footer .qc-footer-social-wrap"
    SOCIAL_LABEL = "footer h3.qc-footer-social-title"
    SOCIAL_LIST = "footer ul.qc-footer-social"

    @staticmethod
    def social_icon_locator(platform: str) -> str:
        return f'footer ul.qc-footer-social a.qc-social-link[aria-label="{platform}"]'

    @staticmethod
    def social_icon_img_locator(platform: str) -> str:
        return f'footer ul.qc-footer-social img.qc-social-img[alt="{platform}"]'

    # ---- Nav columns (About Qatar Chamber / Services / Useful Links) ----
    @staticmethod
    def nav_column_toggle_locator(column_name: str) -> str:
        return f'footer button.qc-footer-col-toggle:has-text("{column_name}")'

    @staticmethod
    def footer_link_locator(link_text: str) -> str:
        """Shared by nav links, Quick Links, and copyright bottom-bar links —
        the site markup gives all of them the same `.qc-footer-link` hook;
        each is unique on the page by its own visible text."""
        return f'footer a.qc-footer-link:has-text("{link_text}")'

    # ---- Newsletter ------------------------------------------------------
    NEWSLETTER_HEADING = "footer h3.qc-footer-col-title"
    NEWSLETTER_DESCRIPTION = "footer .qc-footer-newsletter-text"
    EMAIL_INPUT = "footer input.qc-footer-input"
    SUBSCRIBE_BUTTON = "footer button.qc-footer-subscribe"

    # ---- Copyright / bottom bar -------------------------------------------
    COPYRIGHT_TEXT = "footer p.qc-footer-copyright"
    BOTTOM_BAR = "footer div.qc-footer-bottom"
    BACK_TO_TOP_BUTTON = "footer button.qc-footer-backtop"

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------
    def open_home(self, url: str = HOME_URL) -> "FooterPage":
        self.open(url)
        self.wait_for(self.FOOTER)
        return self

    # ------------------------------------------------------------------
    # Branding
    # ------------------------------------------------------------------
    def logo_href(self) -> str:
        return self.page.locator(self.LOGO_LINK).get_attribute("href")

    def logo_alt(self) -> str:
        return self.page.locator(self.LOGO_IMG).get_attribute("alt")

    def logo_src(self) -> str:
        return self.page.locator(self.LOGO_IMG).get_attribute("src")

    def click_logo(self) -> None:
        self.click(self.LOGO_LINK)

    def description_text(self) -> str:
        return self.text(self.DESCRIPTION) if self.is_visible(self.DESCRIPTION) else ""

    # ------------------------------------------------------------------
    # Social media
    # ------------------------------------------------------------------
    def social_label_text(self) -> str:
        return self.text(self.SOCIAL_LABEL)

    def is_social_label_visible(self) -> bool:
        return self.is_visible(self.SOCIAL_LABEL)

    def social_icon_href(self, platform: str) -> str:
        return self.page.locator(self.social_icon_locator(platform)).get_attribute("href")

    def social_icon_alt(self, platform: str) -> str:
        return self.page.locator(self.social_icon_img_locator(platform)).get_attribute("alt")

    def is_social_icon_visible(self, platform: str) -> bool:
        return self.is_visible(self.social_icon_locator(platform))

    def social_icon_target(self, platform: str) -> str:
        return self.page.locator(self.social_icon_locator(platform)).get_attribute("target")

    def click_social_icon(self, platform: str) -> None:
        self.click(self.social_icon_locator(platform))

    def hover_social_icon(self, platform: str) -> None:
        self.page.locator(self.social_icon_locator(platform)).hover()

    def social_icons_count(self) -> int:
        return self.page.locator("footer ul.qc-footer-social a.qc-social-link").count()

    # ------------------------------------------------------------------
    # Nav columns / Quick Links / bottom bar (shared .qc-footer-link hook)
    # ------------------------------------------------------------------
    def is_nav_column_visible(self, column_name: str) -> bool:
        return self.is_visible(self.nav_column_toggle_locator(column_name))

    def is_footer_link_visible(self, link_text: str) -> bool:
        return self.is_visible(self.footer_link_locator(link_text))

    def footer_link_href(self, link_text: str) -> str:
        return self.page.locator(self.footer_link_locator(link_text)).get_attribute("href")

    def footer_link_target(self, link_text: str) -> str:
        return self.page.locator(self.footer_link_locator(link_text)).get_attribute("target")

    def click_footer_link(self, link_text: str) -> None:
        self.click(self.footer_link_locator(link_text))

    def footer_link_display_index(self, link_text: str) -> int:
        """0-based position of the link among its DOM siblings — used to
        assert Display-Order cases ("appears first")."""
        return self.page.locator(self.footer_link_locator(link_text)).evaluate(
            "el => Array.prototype.indexOf.call(el.parentElement.children, el)"
        )

    def nav_column_heading_text(self, column_name: str) -> str:
        return self.text(self.nav_column_toggle_locator(column_name))

    def social_icon_display_index(self, platform: str) -> int:
        return self.page.locator(self.social_icon_locator(platform)).evaluate(
            "el => Array.prototype.indexOf.call(el.parentElement.children, el)"
        )

    # ------------------------------------------------------------------
    # Newsletter
    # ------------------------------------------------------------------
    def newsletter_heading_text(self) -> str:
        return self.text(self.NEWSLETTER_HEADING)

    def newsletter_description_text(self) -> str:
        return self.text(self.NEWSLETTER_DESCRIPTION) if self.is_visible(self.NEWSLETTER_DESCRIPTION) else ""

    def email_placeholder(self) -> str:
        return self.page.locator(self.EMAIL_INPUT).get_attribute("placeholder")

    def subscribe_button_label(self) -> str:
        return self.text(self.SUBSCRIBE_BUTTON)

    def enter_newsletter_email(self, email: str) -> None:
        self.type(self.EMAIL_INPUT, email)

    def click_subscribe(self) -> None:
        self.click(self.SUBSCRIBE_BUTTON)

    def is_newsletter_email_valid(self) -> bool:
        """Reads the native HTML5 constraint-validation state of the email
        input (`type="email" required` — confirmed live, no custom
        validation-message element exists in the DOM to select instead)."""
        return self.page.locator(self.EMAIL_INPUT).evaluate("el => el.validity.valid")

    def newsletter_email_validation_message(self) -> str:
        return self.page.locator(self.EMAIL_INPUT).evaluate("el => el.validationMessage")

    # ------------------------------------------------------------------
    # Copyright / bottom bar
    # ------------------------------------------------------------------
    def copyright_text(self) -> str:
        return self.text(self.COPYRIGHT_TEXT)

    def is_copyright_bar_visible(self) -> bool:
        return self.is_visible(self.BOTTOM_BAR)

    def is_copyright_text_visible(self) -> bool:
        return self.is_visible(self.COPYRIGHT_TEXT)

    # ------------------------------------------------------------------
    # Back to top
    # ------------------------------------------------------------------
    def is_back_to_top_visible(self) -> bool:
        return self.is_visible(self.BACK_TO_TOP_BUTTON)

    def click_back_to_top(self) -> None:
        self.click(self.BACK_TO_TOP_BUTTON)

    def scroll_to_bottom(self) -> None:
        self.page.locator(self.FOOTER).scroll_into_view_if_needed()

    def scroll_to_top(self) -> None:
        self.page.evaluate("() => window.scrollTo(0, 0)")

    # ------------------------------------------------------------------
    # Layout / style state (for UI + compatibility cases)
    # ------------------------------------------------------------------
    def footer_background(self) -> str:
        return self.page.locator(self.FOOTER).evaluate("el => getComputedStyle(el).backgroundImage")

    def footer_font_family(self) -> str:
        return self.page.locator(self.FOOTER).evaluate("el => getComputedStyle(el).fontFamily")

    def footer_text_color(self, locator: str) -> str:
        return self.page.locator(locator).evaluate("el => getComputedStyle(el).color")

    def element_font_style(self, locator: str) -> dict:
        return self.page.locator(locator).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, "
            "fontSize: cs.fontSize, lineHeight: cs.lineHeight, textAlign: cs.textAlign}; }"
        )

    def is_footer_rtl(self) -> bool:
        return self.page.locator(self.FOOTER).evaluate(
            "el => getComputedStyle(el).direction === 'rtl' || document.documentElement.dir === 'rtl'"
        )

    def is_footer_visible(self) -> bool:
        return self.is_visible(self.FOOTER)

    def is_description_visible(self) -> bool:
        return self.is_visible(self.DESCRIPTION)

    def copyright_text_color(self) -> str:
        return self.footer_text_color(self.COPYRIGHT_TEXT)

    def social_label_style(self) -> dict:
        return self.element_font_style(self.SOCIAL_LABEL)

    def quick_links_heading_style(self) -> dict:
        return self.element_font_style(self.nav_column_toggle_locator("Quick Links"))

    def newsletter_description_style(self) -> dict:
        return self.element_font_style(self.NEWSLETTER_DESCRIPTION)

    def subscribe_button_style(self) -> dict:
        return self.element_font_style(self.SUBSCRIBE_BUTTON)

    def footer_link_style(self, link_text: str) -> dict:
        return self.element_font_style(self.footer_link_locator(link_text))

    def is_footer_stacked(self) -> bool:
        """Columns are stacked (single-column flow) rather than side-by-side —
        used by the tablet/mobile compatibility cases."""
        return self.page.locator("footer .qc-footer-brand").evaluate(
            "brand => { const cols = document.querySelectorAll('footer .qc-footer-col'); "
            "if (cols.length < 2) return true; "
            "const r0 = cols[0].getBoundingClientRect(); const r1 = cols[1].getBoundingClientRect(); "
            "return r0.bottom <= r1.top + 1; }"
        )

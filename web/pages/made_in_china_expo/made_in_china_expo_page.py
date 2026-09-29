"""
web/pages/made_in_china_expo/made_in_china_expo_page.py — MadeInChinaExpoPage.

Public delivery-surface Page Object for PBI 130953 ("QC - Events - 006 -
Made in China Expo"). CONFIRMED LIVE 2026-09-22 (anonymous/unauthenticated
browser context, 1920x1080):

REAL PUBLIC PATH — the QA batch's own stated path (`/events/made-in-china-
expo`) 404s. The real, live path is **`/made-in-china-expo`** (site root, no
`/events/` segment) — resolved via the CMS Hero singleton's own row-level
"Preview" link target (`/web/qatar-chamber/made-in-china-expo?qcPreview=
...`), confirmed live to 200 and render the full hero/about/card content.
Every navigation method below uses this REAL path, not the case's literal
(wrong) text — see cms/pages/made_in_china_expo/
made_in_china_expo_hero_admin_page.py's module docstring for the full
evidence trail. This mismatch is reported as a finding, not silently
"corrected" in the case itself.

CONFIRMED-LIVE PRODUCT DEFECT — both the Hero CTA and the Side CTA Card's
own anchor resolve to `href="https://www.qatarchamber.com/"` with
`target="_blank"` — NOT `https://www.madeinchinaexpo.com` as the relevant
QA cases (tc_144249/144250/144259/144260) expect. Confirmed via a direct
HTML dump of the live, rendered anchor tags (not inferred). The CURRENT
live Open Behavior for BOTH ctas is "New Tab" (`target="_blank"`,
`rel="noopener noreferrer"`) — this happens to match tc_144250's precondition
(Open Behavior = New Tab) with NO write needed, but does NOT match
tc_144249's precondition (Same Tab), which would require an authoring
write against the live singleton and is SKIPPED per this project's
destructive-ops rule.

REAL, CONFIRMED-LIVE STRUCTURE — the page ships a full set of stable
`data-qc-mic-*` custom data attributes (this project's `data-testid`-tier
convention), confirmed via a direct HTML dump of `#main-content`:

    section[data-qc-mic-ready]      the whole page's outer <section>
        (also carries data-qc-mic-home-url / data-qc-mic-events-url —
        the breadcrumb's own resolved hrefs, and dir="ltr"/"rtl")
    nav[data-qc-mic-crumbs]         breadcrumb (a.qc-mic-crumb, in order: Home, Events)
    [data-qc-mic-hero]              hero section
      [data-qc-mic-eyebrow]        hero eyebrow
      [data-qc-mic-title]          hero title (h1)
      [data-qc-mic-desc]           hero description
      [data-qc-mic-hero-img] img   hero banner image (real alt text confirmed live)
      [data-qc-mic-hero-cta] a     hero CTA anchor
    [data-qc-mic-about]             about section
      [data-qc-mic-about-eyebrow]  about eyebrow
      [data-qc-mic-about-title]    about title (h2)
      [data-qc-mic-about-body]     about body paragraphs
      [data-qc-mic-about-icon] img supporting image
    [data-qc-mic-band]              2-column layout band wrapping about+card
    [data-qc-mic-card]              side CTA card
      [data-qc-mic-card-logo] img  card logo (real alt text confirmed live)
      [data-qc-mic-card-eyebrow]   card eyebrow
      [data-qc-mic-card-heading]   card heading (h3)
      [data-qc-mic-card-subtext]   card subtext
      [data-qc-mic-card-cta] a     card CTA anchor

Confirmed-live text (EN, current published content): hero eyebrow "Qatari
industry. Local ambition.", hero title "Made in China Expo", about eyebrow
"About the exhibition", about title "Connecting markets and business
opportunities", card eyebrow "Official exhibition website", card heading
"Explore Made in China", both CTA labels "Visit the Official Expo Website".

AR variant CONFIRMED LIVE reachable at `/ar/made-in-china-expo` (200,
`<html dir="rtl" lang="ar-SA">`) — this project's standard
`web_url(path, locale="ar")` convention applies unchanged.
"""

from core.web.base_page import BasePage
from config.settings import web_url

PATH = "made-in-china-expo"
EXTERNAL_EXPO_URL = "https://www.madeinchinaexpo.com"


class MadeInChinaExpoPage(BasePage):
    SECTION_ROOT = "[data-qc-mic-ready]"
    BREADCRUMB = "[data-qc-mic-crumbs]"
    BREADCRUMB_HOME_LINK = f"{BREADCRUMB} a.qc-mic-crumb >> nth=0"
    BREADCRUMB_EVENTS_LINK = f"{BREADCRUMB} a.qc-mic-crumb >> nth=1"

    HERO_SECTION = "[data-qc-mic-hero]"
    HERO_EYEBROW = "[data-qc-mic-eyebrow]"
    HERO_TITLE = "[data-qc-mic-title]"
    HERO_DESC = "[data-qc-mic-desc]"
    # CONFIRMED LIVE 2026-09-22: `data-qc-mic-hero-img` sits directly ON the
    # <img> tag itself (`<img class="qc-mic-hero-img" data-qc-mic-hero-img=""
    # alt="..." src="...">`), NOT on a wrapping element — an earlier
    # `"[data-qc-mic-hero-img] img"` (descendant-img) locator matched ZERO
    # elements and timed out on every attribute read. Same fix applies to
    # CARD_LOGO below.
    HERO_IMG = "[data-qc-mic-hero-img]"
    HERO_CTA = "[data-qc-mic-hero-cta] a"

    ABOUT_SECTION = "[data-qc-mic-about]"
    ABOUT_EYEBROW = "[data-qc-mic-about-eyebrow]"
    ABOUT_TITLE = "[data-qc-mic-about-title]"
    ABOUT_BODY = "[data-qc-mic-about-body]"
    # CONFIRMED LIVE 2026-09-22: `data-qc-mic-about-icon` is a DECORATIVE
    # `aria-hidden="true"` SVG icon beside the About heading, NOT the
    # About Section's own "Supporting Image" field — that field's own
    # upload does not appear to render anywhere on this page at all (a
    # full page-wide `<img>` sweep found exactly 2 real images: the Hero
    # banner and the Side Card logo, neither is a "Supporting Image").
    # Kept as a real, disclosed finding rather than silently repointed to
    # look like a field it isn't; is_about_image_visible() is therefore not
    # used by any test in this batch (no visible Supporting Image render to
    # assert against).
    ABOUT_ICON_DECORATION = "[data-qc-mic-about-icon]"

    BAND = "[data-qc-mic-band]"

    CARD_SECTION = "[data-qc-mic-card]"
    CARD_LOGO = "[data-qc-mic-card-logo]"
    CARD_EYEBROW = "[data-qc-mic-card-eyebrow]"
    CARD_HEADING = "[data-qc-mic-card-heading]"
    CARD_SUBTEXT = "[data-qc-mic-card-subtext]"
    CARD_CTA = "[data-qc-mic-card-cta] a"

    def open_public_page(self, locale: str = "en") -> "MadeInChinaExpoPage":
        self.open(web_url(PATH, locale=locale))
        self.wait_for(self.SECTION_ROOT, timeout=15000)
        return self

    def open_public_page_anonymous(self, locale: str = "en") -> "MadeInChinaExpoPage":
        """Anonymous/logged-out navigation — see standards.md's mandatory
        logged-out-context rule for draft/unpublish public-visibility
        checks. Never call on the shared authenticated `page` fixture."""
        self.open_anonymous(web_url(PATH, locale=locale))
        return self

    # ---- direction / RTL ----------------------------------------------
    def html_dir(self) -> str:
        return self.page.locator("html").get_attribute("dir") or ""

    def html_lang(self) -> str:
        return self.page.locator("html").get_attribute("lang") or ""

    # ---- breadcrumb -----------------------------------------------------
    def click_breadcrumb_home(self) -> None:
        self.click(self.BREADCRUMB_HOME_LINK)

    def click_breadcrumb_events(self) -> None:
        self.click(self.BREADCRUMB_EVENTS_LINK)

    def breadcrumb_text(self) -> str:
        return self.text(self.BREADCRUMB)

    # ---- hero -------------------------------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO_SECTION)

    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def hero_image_alt(self) -> str:
        return self.get_attribute(self.HERO_IMG, "alt") or ""

    def is_hero_cta_visible(self) -> bool:
        return self.is_visible(self.HERO_CTA)

    def hero_cta_label(self) -> str:
        return self.text(self.HERO_CTA)

    def hero_cta_href(self) -> str:
        return self.get_attribute(self.HERO_CTA, "href") or ""

    def hero_cta_target(self) -> str:
        return self.get_attribute(self.HERO_CTA, "target") or ""

    def click_hero_cta(self) -> None:
        self.click(self.HERO_CTA)

    # ---- about section ------------------------------------------------
    def is_about_visible(self) -> bool:
        return self.is_visible(self.ABOUT_SECTION)

    def about_eyebrow_text(self) -> str:
        return self.text(self.ABOUT_EYEBROW)

    def about_title_text(self) -> str:
        return self.text(self.ABOUT_TITLE)

    def about_body_text(self) -> str:
        return self.text(self.ABOUT_BODY)

    # ---- side CTA card --------------------------------------------------
    def is_card_visible(self) -> bool:
        return self.is_visible(self.CARD_SECTION)

    def is_card_logo_visible(self) -> bool:
        return self.is_visible(self.CARD_LOGO)

    def card_logo_alt(self) -> str:
        return self.get_attribute(self.CARD_LOGO, "alt") or ""

    def card_eyebrow_text(self) -> str:
        return self.text(self.CARD_EYEBROW)

    def card_heading_text(self) -> str:
        return self.text(self.CARD_HEADING)

    def card_subtext_text(self) -> str:
        return self.text(self.CARD_SUBTEXT)

    def is_card_cta_visible(self) -> bool:
        return self.is_visible(self.CARD_CTA)

    def card_cta_label(self) -> str:
        return self.text(self.CARD_CTA)

    def card_cta_href(self) -> str:
        return self.get_attribute(self.CARD_CTA, "href") or ""

    def card_cta_target(self) -> str:
        return self.get_attribute(self.CARD_CTA, "target") or ""

    def click_card_cta(self) -> None:
        self.click(self.CARD_CTA)

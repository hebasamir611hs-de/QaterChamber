"""
cms/pages/about_qatar_chamber/about_qatar_chamber_admin_page.py --
AboutQatarChamberObjectAuthoringPage.

PBI 129392 (QC-ABOUT 001 -- Qatar Chamber / the About Us page).

═══════════════════════════════════════════════════════════════════════
OBJECT NAMES FOR THIS FEATURE (from cms/Content-Admin-Guide.docx)
═══════════════════════════════════════════════════════════════════════
Source of truth is the team's Content Admin Guide, per standards.md ->
*"Object Names Come From cms/Content-Admin-Guide.docx -- Never Guessed,
Never Probed First"*. Guide section 23 + section 22 give TWO objects:

  - **AboutQatarChamberPage** (guide section 23, "one entry") -> slug
    `about-qatar-chamber-page` (`manage-about-qatar-chamber-page`).
    Singleton entry code `QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY`.
    Guide fields: pageTitle, pageContent, contentImage,
    contentImageAltText, hyperlinkTitle + hyperlinkUrl, pageStatus.

  - **AboutHeroBanner** (guide section 22) -> slug `about-hero-banner`
    (`manage-about-hero-banner`). ONE ROW PER PAGE, selected by `pageKey`;
    the About Us row is `QCDEMO-ABOUT-HERO-about-us`. Fields: pageKey,
    bannerImage, bannerImageAltText. Four rows exist live (about-us,
    chairman-message, vision-mission-objectives, chamber-laws).

**THE HERO BANNER IS NOT ON THE PAGE OBJECT -- THIS IS A REAL TRAP.**
The guide warns: *"the About Us and Chairman objects (sections 23, 24)
also contain an old heroBannerImage field -- it is no longer used for the
banner. Set the banner in AboutHeroBanner."* Confirmed live 2026-09-09,
with the exact mechanism:

  - `manage-about-qatar-chamber-page` DOES still render a `Hero Banner
    Image` attachment field, and it DOES hold a file
    (`about-hero-banner.png`, doc `4561f252-...`).
  - The public About Us page carries that file only as a DATA ATTRIBUTE
    (`data-qc-ap-hero-img` on `div.qc-about-page`) and never renders it.
  - What actually renders is `div.qc-ap-hero-media`'s inline
    `background-image: url(.../about-us-hero.png/7d50e4ad-...)` -- the
    **AboutHeroBanner** row's `Banner Image`.

So a test that writes the page object's own `Hero Banner Image` will save
happily and change NOTHING on the site. Any hero-banner case must drive
`open_hero_banner_record()`. `HERO_BANNER_IMAGE_LABEL_LEGACY` below is
kept only to name the trap explicitly, never to be written by a test.
═══════════════════════════════════════════════════════════════════════

Field labels below were read off the real edit forms live 2026-09-09
(authenticated headless Chromium, scoped CLI probe -- never the Playwright
MCP), in on-screen order. Composes `ObjectAuthoringPage`
(cms/pages/components/object_authoring_page.py) for all navigation and
lifecycle, mirroring `ChambersLawAdminPage`'s established convention --
this class holds only object identities + field-label constants.

Entry-column note (matters for which lookup helper is correct): BOTH of
these objects render a CODE in their Entry column -- the page object shows
its `QCDEMO-129392-...` external reference code, and AboutHeroBanner shows
the `pageKey` (`about-us`, `chairman-message`, ...). Neither renders a
title, so the `_by_code` lookups are the RIGHT ones here. (Contrast
`LawEntry`, whose Entry column renders the Law Title, where title-keyed
lookups are required -- getting that backwards cost two failed runs on
PBI 129394.)
"""

from core.web.base_page import BasePage
from cms.pages.components.object_authoring_page import ObjectAuthoringPage

# ---- Object Authoring identities (guide sections 23 + 22) ---------------
ABOUT_PAGE_SLUG = "about-qatar-chamber-page"
ABOUT_PAGE_ENTRY_CODE = "QCDEMO-129392-ABOUT_QATAR_CHAMBER_PAGE-ENTRY"

HERO_BANNER_SLUG = "about-hero-banner"
HERO_BANNER_ABOUT_US_ENTRY_CODE = "QCDEMO-ABOUT-HERO-about-us"
HERO_BANNER_ABOUT_US_PAGE_KEY = "about-us"


class AboutQatarChamberAdminPage(BasePage):
    """Drives PBI 129392's two Object Authoring objects. Every navigation
    and lifecycle action goes through `ObjectAuthoringPage` -- `Content &
    Data` is retired project-wide for Object-Definition-backed records
    (standards.md)."""

    ARABIC_SUFFIX = " — العربية"

    # ---- AboutQatarChamberPage fields (confirmed live, on-screen order) --
    PAGE_TITLE_LABEL = "Page Title"
    # The rich-text body. Its rendered LABEL is "Page Content Required"
    # (the required marker is concatenated into the accessible name), but
    # rich text is addressed by DOM field NAME, not label -- see
    # ObjectAuthoringPage.fill_rich_text()/rich_text_value().
    PAGE_CONTENT_FIELD_NAME = "pageContent"
    PAGE_CONTENT_LABEL = "Page Content Required"
    CONTENT_IMAGE_UPLOAD_LABEL = "Content Image"
    CONTENT_IMAGE_ALT_TEXT_LABEL = "Content Image Alt Text"
    HYPERLINK_TITLE_LABEL = "Hyperlink Title"
    HYPERLINK_URL_LABEL = "Hyperlink URL"
    # DO NOT WRITE THIS FIELD -- see the module docstring's trap note. It
    # exists on the form and saves cleanly, but the public page ignores it.
    HERO_BANNER_IMAGE_LABEL_LEGACY = "Hero Banner Image"
    HERO_BANNER_ALT_TEXT_LABEL_LEGACY = "Hero Banner Alt Text"

    # ---- AboutHeroBanner fields (the REAL hero banner) -------------------
    PAGE_KEY_LABEL = "Page Key"
    BANNER_IMAGE_UPLOAD_LABEL = "Banner Image"
    BANNER_IMAGE_ALT_TEXT_LABEL = "Banner Image Alt Text"

    def __init__(self, page):
        super().__init__(page)

    # ---- Navigation ------------------------------------------------------
    def open_page_record(self) -> "ObjectAuthoringPage":
        """The AboutQatarChamberPage singleton (guide section 23)."""
        authoring = ObjectAuthoringPage(self.page, slug=ABOUT_PAGE_SLUG)
        authoring.open_entry_by_code(ABOUT_PAGE_ENTRY_CODE)
        return authoring

    def open_page_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=ABOUT_PAGE_SLUG)
        authoring.open_entries_list()
        return authoring

    def open_hero_banner_record(self) -> "ObjectAuthoringPage":
        """The AboutHeroBanner row whose pageKey is `about-us` (guide
        section 22) -- the object that ACTUALLY renders the hero banner."""
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        authoring.open_entry_by_code(HERO_BANNER_ABOUT_US_ENTRY_CODE)
        return authoring

    def open_hero_banner_entries_list(self) -> "ObjectAuthoringPage":
        authoring = ObjectAuthoringPage(self.page, slug=HERO_BANNER_SLUG)
        authoring.open_entries_list()
        return authoring

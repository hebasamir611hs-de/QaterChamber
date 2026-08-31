"""
web/pages/about_chairman_message/chairman_message_page.py — ChairmanMessagePage.

PBI 129393 / QC-ABOUT-002 "Chairman's Message". New page/module folder —
this is the first About Us CONTENT page automated on this project (distinct
from home_about_summary, which is the Home page's own "About Us Section &
Achievements Counters" widget, PBI 129389). Folder named `about_chairman_message`
per active/standards.md's `<section>_<feature>` convention already used for
Home-page sections (`home_<feature>`) — this project has no "About pages"
table yet, so this establishes the `about_<feature>` pattern for sibling About
Us pages (General Manager's Message, Vision/Mission, Board, etc.) to follow.

--- CLI-first extraction log ---

Found the live URL by hovering the header's "About us" mega-menu (the static
extractor harvest never sees a hover-only submenu — same documented
"ambiguous/unreachable via role" condition header_component.py's own docstring
already resolved for this same mega-menu) via one disclosed, scoped Playwright
script (still CLI/shell, never the Playwright MCP), reusing BasePage's own
license-gate/overlay guard sequence:

    Chairman's Message -> /web/qatar-chamber/about-us/chairman-message

Then ran the framework's own extractor against the real page:

    python tools/extract_locators.py \
        --url https://qcdev.ihorizons.com/web/qatar-chamber/about-us/chairman-message \
        --viewport 1920x1080 --max 60

The harvester's SEL list (a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable]) surfaced only the global header/
footer/chat-widget controls — every element specific to this page (hero band,
breadcrumb, portrait, Name Card, message body, Signature block) is a plain
<div>/<span>/<p>/<h1>/<h2>/<img> with no role/label of its own, the same
documented "ambiguous element" condition already resolved the same way in
home_about_summary_page.py and header_component.py: one additional, disclosed,
scoped Playwright script reading the live DOM/computed-style/geometry
structure directly, never the Playwright MCP.

Real, CLI-verified structure (EN,
https://qcdev.ihorizons.com/web/qatar-chamber/about-us/chairman-message):

    section.qc-cm
      div.qc-cm-hero
        div.qc-cm-hero-media[role="img"][aria-label="Chairman's Message"]  (CSS background-image, no <img> tag)
        div.qc-cm-hero-overlay                                             (dark gradient overlay)
        div.qc-cm-hero-inner
          h1.qc-cm-hero-title                                              "Chairman's Message"
          nav.qc-cm-breadcrumb
            a.qc-cm-crumb.qc-cm-crumb-home[href="/web/qatar-chamber"] > svg + span "Home"
            svg  (chevron separator)
            span.qc-cm-crumb.qc-cm-crumb-current                           "About Us"
      div.qc-cm-content
        div.qc-cm-grid
          aside.qc-cm-card
            div.qc-cm-portrait-wrap
              div.qc-cm-portrait-deco
              img.qc-cm-portrait-img[alt="Portrait of H.E. Sheikh Khalifa bin
                  Jassim bin Mohammed Al Thani, Chairman of the Board of Qatar Chamber"]
            div.qc-cm-namecard
              p.qc-cm-name                                                 "H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani"
              p.qc-cm-designation                                          "Chairman of The Board"
          div.qc-cm-message
            div.qc-cm-body
              h2                                                           "Dear members and visitors"
              p x6                                                          (6 body paragraphs, no bullet list, no inline link)
            div.qc-cm-signature
              span.qc-cm-sig-icon > svg (feather icon)
              div.qc-cm-sig-text
                p.qc-cm-sig-regards                                        "Best Regards,"
                p.qc-cm-sig-name                                           "H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani"
                p.qc-cm-sig-desig                                          "Chairman of The Board"

Real, CLI-verified findings (reported to the QA Manager, not silently
corrected here — scripted per each case's exact stated wording regardless,
per this project's established convention already documented in
header_component.py / home_about_summary_page.py):

  - HERO HEIGHT: live hero band measures ~118px tall (118.09375), not the
    140px TC 134752 states. Full 1920px width, background-image, and dark
    gradient overlay (`linear-gradient(90deg, rgba(66,44,27,0.82) 0%,
    rgba(145,23,49,0.82) 100%)`) all CONFIRMED LIVE; title renders Cairo 30px
    weight 700, line-height 38.1px, colour rgb(255,255,255), left-aligned —
    all MATCH TC 134752 exactly except the stated height.
  - BREADCRUMB: the live breadcrumb renders only TWO labelled items — "Home"
    (a real link, href="/web/qatar-chamber") and "About Us" (the CURRENT/leaf
    item, rendered as a plain, non-interactive <span class="qc-cm-crumb-current">,
    no href) — there is NO third item naming "Chairman's Message" at all. This
    is a genuine, repeated mismatch against TC 134753 (breadcrumb should end
    with "Chairman's Message"), TC 134763/134764 (Arabic breadcrumb leaf
    should read the Arabic page title), and TC 134785 (clicking "About Us" in
    the breadcrumb should navigate to the About Us page — impossible, it is
    not a link). Confirmed identically in Arabic: breadcrumb reads "الرئيسية"
    then "من نحن" (also 2 items, leaf = "من نحن" not "رسالة رئيس مجلس الإدارة").
    Scripted per each case's exact literal wording anyway — these assertions
    are expected to fail honestly against the real, live breadcrumb.
  - PORTRAIT: 393x470, 16px corner radius — MATCHES TC 134754 exactly. The
    decorative maroon backing rectangle (`.qc-cm-portrait-deco`,
    rgb(145,23,49), 20px corner radius) measures 212x364.27, not the case's
    stated 213x343 — width is a rounding-tolerance match, height is a real
    23px mismatch. The 424px-wide gradient-filled, 20px-radius column IS
    confirmed live, but on `aside.qc-cm-card` (not `.qc-cm-portrait-wrap`,
    which itself has no radius/gradient of its own — the wrap sits inside the
    styled card).
  - NAME CARD (TC 134755): CONFIRMED LIVE, genuine pass — name Cairo 20px/700/
    30px line-height/rgb(145,23,49)/centred; designation Cairo 18px/400/
    28.08px line-height/rgb(166,111,67)/centred; vertical gap between them
    measures exactly 8.0px.
  - SALUTATION HEADING (TC 134756): typography CONFIRMED LIVE exactly (Cairo
    30px/700/38.1px line-height/rgb(145,23,49)/left-aligned) — but the message
    column itself measures 696px wide, not the case's stated 760px (a repeated
    mismatch also affecting TC 134757/134758/134766).
  - BODY PARAGRAPHS (TC 134757): typography CONFIRMED LIVE exactly (Cairo
    18px/400/28.08px line-height/rgb(52,52,50)/left-aligned). The gap between
    the salutation heading and the first paragraph measures 16.0px, not the
    case's stated 24px. Column width mismatch (696 vs 760) applies here too.
  - SIGNATURE BLOCK (TC 134758): 696x108.23 (height matches the case's stated
    108; width does not — same 696-vs-760 mismatch), fill rgb(246,240,236),
    12px corner radius, "Best Regards," rgb(74,74,73) / Chairman Name Cairo
    18px/700/rgb(145,23,49) / Designation Cairo 18px/400/rgb(166,111,67) — ALL
    CONFIRMED LIVE exactly. The 64x64 fully-rounded icon (border-radius 9999px)
    filled rgb(166,111,67) with a white feather icon sits exactly 20.0px to
    the left of the text block — CONFIRMED LIVE, genuine pass.
  - RICH TEXT (TC 134759, Control_Panel-gated — see the sibling admin page
    object): the live message body renders a heading (h2) and 6 paragraphs,
    but NO bullet list (`ul`/`ol`) and NO inline link anywhere in
    `.qc-cm-body` — confirmed via `.qc-cm-body a` returning 0 matches. There is
    currently no live content to verify a bullet list or an inline hyperlink
    against without first performing the case's CMS-authoring step (blocked,
    see admin page object).
  - ALT TEXT (TC 134760, Control_Panel-gated): the hero band is a CSS
    background-image on a `<div role="img" aria-label="Chairman's Message">`
    (no literal `alt` attribute — the ARIA label is its accessible-name
    equivalent), genuinely distinct from the portrait's own
    `alt="Portrait of H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani,
    Chairman of the Board of Qatar Chamber"`. Both are non-empty and mutually
    distinct RIGHT NOW — but neither matches the case's specific CMS-configured
    strings ("Qatar Chamber board room" / "Chairman Sheikh Khalifa bin Jassim
    Al Thani"), which requires the blocked CMS step to set.
  - EN/AR LAYOUT MIRRORING (TC 134761, 134762): CONFIRMED LIVE, genuine pass
    both ways. EN: dir="ltr", portrait column (`aside.qc-cm-card`, x=352) left
    of the message column (`div.qc-cm-message`, x=872). AR: dir="rtl", message
    column renders FIRST (x=352) with the portrait column to its right
    (x=1144) — a true mirror, not merely repositioned. AR hero title reads
    "رسالة رئيس مجلس الإدارة" and the salutation reads "السادة الأعضاء والزوار"
    exactly as TC 134762 states.
  - LANGUAGE SWITCH (TC 134781, 134782): CONFIRMED LIVE — the header's
    language-switcher link is `/c/portal/update_language?...&redirect=%2Fweb%2F
    qatar-chamber%2Fabout-us%2Fchairman-message&...`; clicking it lands on
    `/ar/about-us/chairman-message` (or back on the EN URL in reverse) — the
    SAME page, genuinely never bounced to the homepage.
  - BREADCRUMB "ABOUT US" CLICK (TC 134785): the breadcrumb's "About Us" item
    is confirmed live to be a plain `<span>` with no `href` (see BREADCRUMB
    finding above) — there is nothing to click. This case is scripted to
    attempt the click and assert real navigation, which will genuinely fail
    against this live implementation (a real defect to report, not to hide).
  - RESPONSIVE (TC 134766/134767/134768): desktop content container measures
    1248px wide at x=336 (not the case's stated 1320px/300px padding);
    tablet (768x1024) and mobile (390x844, EN + AR) both CONFIRMED LIVE with
    no horizontal overflow, the portrait/Name Card stacking above the message/
    Signature block, and every Signature-block element staying visible.
  - DARK MODE (TC 134841-134844): reused the SAME global Dark Mode toggle
    already built for PBI 129364 (`AccessibilityToolsComponent` — composed
    here, never re-declared, per this project's established "compose, don't
    duplicate" convention already used by `accessibility_tools_component.py`
    itself for `HeaderComponent`). CONFIRMED LIVE: body background flips to
    rgb(29,29,27) with light text; the Signature block panel background
    changes to rgb(41,34,28) (still visually distinct from the page
    background); the hero overlay gradient KEEPS its rgb(145,23,49) maroon
    stop unchanged; the footer background stays rgb(145,23,49) (maroon)
    unchanged. HOWEVER — the Name Card's name/designation colours do NOT
    "stay in their brand colours" as TC 134841/134842 state: they switch from
    rgb(145,23,49)/rgb(166,111,67) to light legibility tones
    (rgb(246,240,236) / a lighter tan) in dark mode, a genuine, repeatable
    mismatch against those cases' literal wording — scripted per the case's
    exact stated expectation anyway, and expected to fail honestly.
  - NO LIVE HYPERLINK (TC 134780, 134828, 134829, 134834, 134839, 134840):
    `.qc-cm-body a` returns 0 matches on the live page — there is currently no
    inline hyperlink anywhere in the message content to click, read the label
    of, or verify open-behaviour against. Every one of these cases needs the
    blocked CMS step to configure one first; there is no pre-existing content
    that lets the public-page half be verified independently (see the sibling
    test module's module docstring for the explicit runtime-skip on each).
  - UNAVAILABLE-PAGE ERROR HANDLING (TC 134845): the case's own precondition
    ("unpublish it or take its backing service offline") cannot be performed
    without the blocked CMS step, so this is scripted against a genuine,
    already-unavailable Liferay URL on the SAME site instance as a disclosed,
    concrete stand-in for "an unavailable page" — mirroring the same
    "simulate the precondition" pattern already established in
    accessibility_tools_component.py's `start_open_failure_simulation()`.
    CONFIRMED LIVE: a non-existent page under this site returns HTTP 404 with
    a friendly "Coming Soon" message, the real site header AND footer intact,
    and no stack trace/raw exception text.
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.header_component import HeaderComponent
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

CHAIRMAN_MESSAGE_PATH = "/web/qatar-chamber/about-us/chairman-message"
# A genuine, confirmed-live 404 on this same site instance — the disclosed
# stand-in for "the page is unavailable" (TC 134845), since the real
# unpublish action needs the blocked CMS step (see module docstring).
NONEXISTENT_PAGE_PATH = "/web/qatar-chamber/about-us/chairman-message-nonexistent-129393"


class ChairmanMessagePage(BasePage):
    # ── Locators — real, CLI-verified constants (see module docstring) ──────
    HERO = ".qc-cm-hero"
    HERO_MEDIA = ".qc-cm-hero-media"
    HERO_OVERLAY = ".qc-cm-hero-overlay"
    HERO_TITLE = ".qc-cm-hero-title"
    BREADCRUMB = "nav.qc-cm-breadcrumb"
    BREADCRUMB_ITEMS = f"{BREADCRUMB} >> .qc-cm-crumb"
    BREADCRUMB_HOME_LINK = ".qc-cm-crumb-home"
    BREADCRUMB_CURRENT = ".qc-cm-crumb-current"
    CONTENT = ".qc-cm-content"
    GRID = ".qc-cm-grid"
    CARD = "aside.qc-cm-card"
    PORTRAIT_WRAP = ".qc-cm-portrait-wrap"
    PORTRAIT_IMG = "img.qc-cm-portrait-img"
    PORTRAIT_DECO = ".qc-cm-portrait-deco"
    NAMECARD = ".qc-cm-namecard"
    NAME = "p.qc-cm-name"
    DESIGNATION = "p.qc-cm-designation"
    MESSAGE_COLUMN = "div.qc-cm-message"
    BODY = ".qc-cm-body"
    SALUTATION_HEADING = ".qc-cm-body h2"
    BODY_PARAGRAPHS = ".qc-cm-body p"
    BODY_LISTS = ".qc-cm-body ul, .qc-cm-body ol"
    BODY_LINKS = ".qc-cm-body a"
    SIGNATURE = ".qc-cm-signature"
    SIG_ICON = ".qc-cm-sig-icon"
    SIG_TEXT = ".qc-cm-sig-text"
    SIG_REGARDS = ".qc-cm-sig-regards"
    SIG_NAME = ".qc-cm-sig-name"
    SIG_DESIG = ".qc-cm-sig-desig"
    HTML_ROOT = "html"
    FOOTER = "footer"
    # Stable href-based CSS locator into the header's own "About us" mega-menu
    # (not re-declared on HeaderComponent — this link is specific to THIS
    # page/PBI, everything else about the mega-menu already lives there).
    NAV_SUBMENU_CHAIRMAN_LINK = f'a[href="{CHAIRMAN_MESSAGE_PATH}"]'

    _STYLE_JS = (
        "el => { const cs = getComputedStyle(el); return {"
        "color: cs.color, backgroundColor: cs.backgroundColor, fontFamily: cs.fontFamily,"
        "fontSize: cs.fontSize, fontWeight: cs.fontWeight, lineHeight: cs.lineHeight,"
        "textAlign: cs.textAlign, borderRadius: cs.borderRadius,"
        "backgroundImage: cs.backgroundImage"
        "}; }"
    )

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self.a11y = AccessibilityToolsComponent(page)

    def _style(self, locator: str):
        return self.page.locator(locator).first.evaluate(self._STYLE_JS)

    def _box(self, locator: str):
        box = self.page.locator(locator).first.bounding_box()
        if not box:
            return None
        return {"x": box["x"], "y": box["y"], "w": box["width"], "h": box["height"]}

    # ── Navigation ───────────────────────────────────────────────────────
    def open_en(self) -> "ChairmanMessagePage":
        self.open(web_url(CHAIRMAN_MESSAGE_PATH))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_ar(self) -> "ChairmanMessagePage":
        self.open(web_url(CHAIRMAN_MESSAGE_PATH, locale="ar"))
        self.wait_for(self.HERO_TITLE)
        return self

    def open_via_main_menu(self) -> "ChairmanMessagePage":
        """TC 134775 — reaches the page via Main Menu -> About Us -> Chairman's
        Message, hovering the header's real mega-menu rather than a direct URL.
        Waits on network-idle before the trailing wait_for(HERO_TITLE) — this
        site's client-side (senna.js) routing is measurably async, same
        rationale already documented on HeaderComponent.open_about_us_via_nav()."""
        self.header.open_home()
        self.page.locator(self.header.NAV_LINK_ABOUT_US).hover()
        self.page.locator(self.NAV_SUBMENU_CHAIRMAN_LINK).click()
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.HERO_TITLE)
        return self

    def open_nonexistent_page(self) -> "ChairmanMessagePage":
        """TC 134845 — see module docstring's "UNAVAILABLE-PAGE ERROR HANDLING"
        finding for why this stands in for the case's own unpublish/take-
        offline precondition."""
        self.open(web_url(NONEXISTENT_PAGE_PATH))
        return self

    def switch_to_arabic(self) -> "ChairmanMessagePage":
        self.click(self.header.LANGUAGE_SWITCHER)
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.HERO_TITLE)
        return self

    def switch_to_english(self) -> "ChairmanMessagePage":
        self.click(self.header.LANGUAGE_SWITCHER)
        self.page.wait_for_load_state("networkidle")
        self.wait_for(self.HERO_TITLE)
        return self

    def click_breadcrumb_about_us(self) -> bool:
        """TC 134785 — attempts to click the breadcrumb's "About Us" entry and
        reports whether real navigation occurred (URL changed away from this
        page). See module docstring: the live element is a non-interactive
        <span>, so this is expected to honestly return False."""
        before_url = self.page.url
        try:
            self.page.locator(self.BREADCRUMB_CURRENT).click(timeout=3000)
            self.page.wait_for_load_state("networkidle", timeout=5000)
        except Exception:  # noqa: BLE001 — never throws; a non-clickable span is a real, expected outcome
            return False
        return self.page.url != before_url

    def current_url(self) -> str:
        return self.page.url

    # ── Direction / column order ────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def portrait_column_x(self):
        box = self._box(self.CARD)
        return box["x"] if box else None

    def message_column_x(self):
        box = self._box(self.MESSAGE_COLUMN)
        return box["x"] if box else None

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def is_single_column_stack(self) -> bool:
        """True if the portrait card sits entirely ABOVE the message column
        (mobile/tablet stacked layout) rather than beside it."""
        card = self._box(self.CARD)
        message = self._box(self.MESSAGE_COLUMN)
        if not card or not message:
            return False
        return (card["y"] + card["h"]) <= message["y"]

    # ── Hero band (TC 134752) ───────────────────────────────────────────
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_box(self):
        return self._box(self.HERO)

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE)

    def hero_title_style(self) -> dict:
        return self._style(self.HERO_TITLE)

    def hero_has_background_image(self) -> bool:
        style = self._style(self.HERO_MEDIA)
        return style["backgroundImage"] not in ("none", "")

    def hero_overlay_gradient(self) -> str:
        return self._style(self.HERO_OVERLAY)["backgroundImage"]

    def hero_accessible_label(self) -> str:
        """TC 134760 — the hero band's ARIA label (its `alt`-text equivalent —
        see module docstring: it is a CSS background-image div, no literal
        `alt` attribute exists to read)."""
        return self.page.locator(self.HERO_MEDIA).get_attribute("aria-label")

    # ── Breadcrumb (TC 134753, 134761-134765, 134785) ───────────────────
    def breadcrumb_item_texts(self) -> list:
        items = self.page.locator(self.BREADCRUMB_ITEMS)
        return [items.nth(i).inner_text().strip() for i in range(items.count())]

    def breadcrumb_item_count(self) -> int:
        return self.page.locator(self.BREADCRUMB_ITEMS).count()

    def breadcrumb_leaf_text(self) -> str:
        return self.text(self.BREADCRUMB_CURRENT)

    def breadcrumb_style(self) -> dict:
        return self._style(self.BREADCRUMB_CURRENT)

    def is_breadcrumb_current_a_link(self) -> bool:
        tag = self.page.locator(self.BREADCRUMB_CURRENT).evaluate("el => el.tagName")
        href = self.page.locator(self.BREADCRUMB_CURRENT).get_attribute("href")
        return tag.lower() == "a" and bool(href)

    # ── Portrait / decorative backing (TC 134754) ───────────────────────
    def portrait_box(self):
        return self._box(self.PORTRAIT_IMG)

    def portrait_style(self) -> dict:
        return self._style(self.PORTRAIT_IMG)

    def portrait_deco_box(self):
        return self._box(self.PORTRAIT_DECO)

    def portrait_deco_style(self) -> dict:
        return self._style(self.PORTRAIT_DECO)

    def card_box(self):
        return self._box(self.CARD)

    def card_style(self) -> dict:
        return self._style(self.CARD)

    def portrait_alt_text(self) -> str:
        return self.page.locator(self.PORTRAIT_IMG).get_attribute("alt")

    # ── Name Card (TC 134755) ───────────────────────────────────────────
    def name_text(self) -> str:
        return self.text(self.NAME)

    def name_style(self) -> dict:
        return self._style(self.NAME)

    def designation_text(self) -> str:
        return self.text(self.DESIGNATION)

    def designation_style(self) -> dict:
        return self._style(self.DESIGNATION)

    def name_to_designation_gap(self):
        name = self._box(self.NAME)
        designation = self._box(self.DESIGNATION)
        if not name or not designation:
            return None
        return round(designation["y"] - (name["y"] + name["h"]), 1)

    # ── Salutation heading + body (TC 134756, 134757, 134759) ───────────
    def message_column_box(self):
        return self._box(self.MESSAGE_COLUMN)

    def salutation_text(self) -> str:
        return self.text(self.SALUTATION_HEADING)

    def salutation_style(self) -> dict:
        return self._style(self.SALUTATION_HEADING)

    def body_paragraph_count(self) -> int:
        return self.page.locator(self.BODY_PARAGRAPHS).count()

    def body_paragraph_style(self) -> dict:
        return self._style(self.BODY_PARAGRAPHS)

    def heading_to_body_gap(self):
        heading = self._box(self.SALUTATION_HEADING)
        first_p = self._box(self.BODY_PARAGRAPHS)
        if not heading or not first_p:
            return None
        return round(first_p["y"] - (heading["y"] + heading["h"]), 1)

    def body_list_count(self) -> int:
        return self.page.locator(self.BODY_LISTS).count()

    def body_link_count(self) -> int:
        return self.page.locator(self.BODY_LINKS).count()

    def body_links(self) -> list:
        links = self.page.locator(self.BODY_LINKS)
        return [
            {"text": links.nth(i).inner_text().strip(), "href": links.nth(i).get_attribute("href")}
            for i in range(links.count())
        ]

    # ── Signature block (TC 134758, 134765) ─────────────────────────────
    def signature_box(self):
        return self._box(self.SIGNATURE)

    def signature_style(self) -> dict:
        return self._style(self.SIGNATURE)

    def sig_icon_box(self):
        return self._box(self.SIG_ICON)

    def sig_icon_style(self) -> dict:
        return self._style(self.SIG_ICON)

    def sig_regards_text(self) -> str:
        return self.text(self.SIG_REGARDS)

    def sig_regards_style(self) -> dict:
        return self._style(self.SIG_REGARDS)

    def sig_name_text(self) -> str:
        return self.text(self.SIG_NAME)

    def sig_name_style(self) -> dict:
        return self._style(self.SIG_NAME)

    def sig_desig_text(self) -> str:
        return self.text(self.SIG_DESIG)

    def sig_desig_style(self) -> dict:
        return self._style(self.SIG_DESIG)

    def sig_icon_to_text_gap(self):
        icon = self._box(self.SIG_ICON)
        text = self._box(self.SIG_TEXT)
        if not icon or not text:
            return None
        return round(text["x"] - (icon["x"] + icon["w"]), 1)

    # ── Auth (TC 134769) ─────────────────────────────────────────────────
    def is_login_prompt_visible(self) -> bool:
        return self.is_visible('form[action*="login"], .login-form, [aria-label*="login" i]')

    def all_key_sections_visible(self) -> dict:
        return {
            "hero": self.is_hero_visible(),
            "breadcrumb": self.is_visible(self.BREADCRUMB),
            "portrait": self.is_visible(self.PORTRAIT_IMG),
            "namecard": self.is_visible(self.NAMECARD),
            "message_body": self.is_visible(self.BODY),
            "signature": self.is_visible(self.SIGNATURE),
        }

    # ── Scroll-through (TC 134786) ──────────────────────────────────────
    def scroll_to_footer(self) -> "ChairmanMessagePage":
        self.page.locator(self.FOOTER).first.scroll_into_view_if_needed()
        return self

    def is_footer_visible(self) -> bool:
        return self.is_visible(self.FOOTER)

    # ── Dark mode (TC 134841-134844) — composes AccessibilityToolsComponent,
    #    never re-declares its locators/state (see module docstring). ──────
    def open_accessibility_panel(self) -> "ChairmanMessagePage":
        self.click(self.header.ACCESSIBILITY_BUTTON)
        self.wait_for(self.a11y.PANEL)
        return self

    def enable_dark_mode(self) -> "ChairmanMessagePage":
        self.open_accessibility_panel()
        self.a11y.switch_to_dark_mode()
        return self

    def body_background_color(self) -> str:
        return self.page.evaluate("() => getComputedStyle(document.body).backgroundColor")

    def body_text_color(self) -> str:
        return self.page.evaluate("() => getComputedStyle(document.body).color")

    def footer_background_color(self) -> str:
        return self.page.locator(self.FOOTER).first.evaluate("el => getComputedStyle(el).backgroundColor")

    def hero_overlay_contains_maroon(self) -> bool:
        return "145, 23, 49" in self.hero_overlay_gradient()

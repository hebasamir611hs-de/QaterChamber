"""
web/pages/qatar_market_overview/qatar_market_overview_page.py —
QatarMarketOverviewPage.

Public-frontend Page Object for PBI 130694 ("QC - Business Gateway - 002 -
Qatar Market Overview", part of Invest in Qatar / Business Gateway per
background.md's INVEST service). PBI ID resolved the same way pytest.ini's
own `pbi_129389` note already documents for this project (no direct Azure
PBI-lookup tool available this session): every content record's own
`externalReferenceCode`/`objectDefinitionExternalReferenceCode` on this page
is prefixed `QCDEMO-130694-...` (e.g. `QCDEMO-130694-EMIR-PROFILE`,
`QCDEMO-130694-QATAR_MARKET_OVERVIEW_PAGE`, `QCDEMO-130694-PAGE`) — CONFIRMED
LIVE via a disclosed scripted DOM probe reading the hero/Emir image `src`
query strings — the same "external reference code encodes the PBI number"
convention already relied on for pbi_129389. This batch is public-website-
only (Platform=Web, no Control_Panel/CMS work) — sourced from Azure DevOps
suite 140360 (plan 137724), 46 cases tagged `Web` with no `Control_Panel`
tag, of which 45 also carry `Tag=Automation` (140631 is `Tag=Manual` — no
test exists for it anywhere in this module, by design, mirroring the
`tc_140195`/`tc_140196` precedent in
`food_handlers_certification_page.py`'s own test module).

REAL LIVE URL — NOT the literal path every case's own steps use. Every
case's steps say `/en/business-gateway/qatar-market-overview` /
`/ar/business-gateway/qatar-market-overview` — CONFIRMED LIVE this 404s
("Coming Soon" placeholder, same as `hall_booking_page.py` and
`food_handlers_certification_page.py`'s own documented literal-path gaps).
The real, working page (confirmed HTTP 200, matching title "Qatar Market
Overview") is at `/web/qatar-chamber/qatar-market-overview` (Arabic:
`/ar/web/qatar-chamber/qatar-market-overview`) — the same
`/web/qatar-chamber/<slug>` scheme this repo's prior two Business-Gateway-
adjacent batches already document. Reached live via the real main-menu
path: Home -> hover "Business Gateway" -> click "Qatar Market Overview" (a
direct leaf link under a hover-revealed submenu — CONFIRMED LIVE via
`get_by_role("link", name="Business Gateway").hover()` then
`get_by_role("link", name="Qatar Market Overview")`, mirroring
`hall_booking_page.py`/`food_handlers_certification_page.py`'s own
`navigate_via_main_menu()` pattern exactly).

Locators extracted CLI-first via tools/extract_locators.py against the live
page (only surfaces global header/footer/nav chrome — this page's own
content is entirely non-interactive/rich, the same class of gap
`hall_booking_page.py`/`food_handlers_certification_page.py`'s own
docstrings already document for their `data-qc-hb-*`/`data-qc-fh-*`
batches):

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/qatar-market-overview

Everything page-specific below came from a disclosed, scripted DOM probe
(still CLI — plain Playwright scripts run in the shell, never the
Playwright MCP), confirmed live against qcdev at the framework's default
1920x1080 viewport. This component's own custom-attribute family is
`data-qc-qmo-*` ("qmo" = Qatar Market Overview), highest-tier locator here
exactly as the two prior Business-Gateway-adjacent Page Objects give their
own custom-attribute families precedence over generic CSS:

    [data-qc-qmo-crumbs] nav > a.qc-qmo-crumb[href="/web/qatar-chamber"] (Home),
      a.qc-qmo-crumb.is-current[aria-current="page"][href=".../business-gateway"]
      (the trailing/current crumb, labelled "Business Gateway")
    p.qc-qmo-eyebrow[data-qc-qmo-eyebrow]           "Business Gateway"
    h1[data-qc-qmo-title]                            "Qatar Market Overview"
    [data-qc-qmo-desc]                                hero description paragraph
    div.qc-qmo-hero[data-qc-qmo-hero] > div.qc-qmo-hero-grid
      div.qc-qmo-hero-copy (eyebrow/title/desc above)
      div.qc-qmo-hero-art > img.qc-qmo-hero-img[data-qc-qmo-hero-img][src][alt=""]
        CONFIRMED LIVE, REAL DISCLOSED GAPS against tc_140538/tc_140539:
          1. `alt` attribute is EMPTY (same accessibility gap class
             `food_handlers_certification_page.py`'s own hero image already
             documents for this project).
          2. The uploaded image is a real, loaded 848x848 SQUARE photo
             (`naturalWidth===naturalHeight===848`), not the wide banner the
             case's own description assumes ("QCTEST-130694-hero.png...
             1920x520 px"). It renders `object-fit: contain` inside a small
             424x322 `.qc-qmo-hero-art` container (final rendered box
             322x322) alongside the hero copy — NOT a full-bleed 1920px-wide
             banner image. tc_140539's own "Banner spans the full 1920px
             container width" expectation is therefore a genuine, disclosed
             FAIL against this environment's real hero layout (a text+photo
             hero, not a full-width banner hero like Hall Booking's) — see
             that test's own docstring, not silently loosened.
          3. Hero title computed font-size is 40px, not the case's quoted
             48px (title/eyebrow COLOR and font-family DO match: eyebrow
             `rgb(145, 23, 49)` = #911731, title `rgb(29, 29, 27)` = #1D1D1B,
             `font-family: Cairo, ...`, `font-weight: 700` all CONFIRMED
             LIVE to match tc_140538's literal tokens). Colour/weight/family
             ARE asserted below (directly measurable via getComputedStyle,
             no Figma access needed since the case already quotes the exact
             hex); literal px font-size is asserted too, as a disclosed real
             mismatch, not silently dropped.
    div.qc-qmo-intro > p.qc-qmo-intro-eyebrow[data-qc-qmo-intro-eyebrow]
      "Country Reference"; h2[data-qc-qmo-intro-heading] "Discover Qatar";
      p[data-qc-qmo-intro-subtext] — CONFIRMED LIVE, REAL DISCLOSED FINDING
      (the opposite direction from what tc_140557's own premise assumed):
      the live subtext already reads "Navigate the three core topics below.
      Open as many sections as you need to compare information side by
      side." — describing MULTI-open behaviour correctly, NOT the case's own
      quoted "Only one section opens at a time..." wording (which would
      indeed contradict this component's real, CONFIRMED-LIVE multi-open
      accordion behaviour, exactly as tc_140557 hypothesized). Since the
      live copy has evidently already been corrected to describe the real
      shipped behaviour, tc_140557's own real intent ("does the intro
      subtext accurately describe the shipped accordion behaviour") is
      satisfied by the CURRENT state, even though the case's own illustrative
      quoted wording is stale — see that test's own docstring for the exact
      disclosed reasoning, and tc_140540's own docstring for why its LITERAL
      wording match still, correctly, fails (a different case, different
      literal expectation).
    section [data-qc-qmo-accordion].qc-qmo-accordion > div.qc-qmo-row (×3)
      button.qc-qmo-head[aria-expanded][aria-controls="qc-qmo-panel-<key>-N"]
        span.qc-qmo-num ("01".."03") + span.qc-qmo-head-copy >
        span.qc-qmo-head-title / span.qc-qmo-head-sub + span.qc-qmo-toggle
      CONFIRMED LIVE panel ids (0-indexed, do NOT hardcode — read
      `aria-controls` at runtime instead): qc-qmo-panel-glance-0 (01 Qatar at
      a Glance), qc-qmo-panel-emir-1 (02 The Emir),
      qc-qmo-panel-government-2 (03 Government and Legislatives).
      CONFIRMED LIVE, REAL ARCHITECTURE (relevant to tc_140573/tc_140574/
      tc_140576/tc_140629's own "content is present/absent in the DOM"
      wording): each panel div (`#qc-qmo-panel-*`) is ALWAYS mounted in the
      DOM with its full content (10 fact cards, 2 tables, the whole Emir
      profile, etc. all present as real elements at all times) — collapse/
      expand toggles the panel's own `hidden` attribute (and `aria-expanded`
      on its header), it does NOT add/remove the content nodes themselves.
      This is the EXACT same shape `hall_booking_page.py`'s own
      `is_accordion_body_hidden()` already establishes and asserts on for
      this project's other accordion component — collapsed state is
      verified via `hidden`/visibility, never via literal DOM-node absence,
      and is disclosed here rather than silently assumed.
      CONFIRMED LIVE, genuine multi-open support (tc_140575/tc_140629's
      premise): expanding section 01 then section 02 WITHOUT collapsing 01
      left BOTH panels' `hidden` attribute removed and `aria-expanded=true`
      simultaneously — real, working multi-open, consistent with the
      corrected intro subtext described above.
      CONFIRMED LIVE colour tokens (tc_140541/tc_140542/tc_140556):
        collapsed header num color = rgb(108,108,107) = #6C6C6B (MATCHES
          tc_140541's own quoted collapsed-number token);
        collapsed header TITLE color = rgb(0,0,0) = #000000 — REAL,
          DISCLOSED MISMATCH against tc_140541's own quoted #1D1D1B for the
          collapsed title (asserted as literally worded, a genuine fail);
        expanded header num AND title color = rgb(145,23,49) = #911731,
          MATCHING tc_140542's own quoted accent-colour tokens for BOTH the
          number and the title;
        the three headers' own subtitles (`.qc-qmo-head-sub`) read, in
        order, "Country profile, key facts, economy and practical
        information" / "Head of State, constitutional role, biography and
        experience" / "Government structure, constitutional development and
        institutional modernization" — CONFIRMED LIVE this Figma-flagged
        "design-source defect" (section 02 carrying section 03's subtitle)
        is NOT present in the shipped page; tc_140556 genuinely PASSES.

    Section 01 (`#qc-qmo-panel-glance-0`, "Qatar at a Glance") —
    tc_140543/140544/140545/140546/140547/140548:
      .qc-qmo-panel-intro.qc-qmo-rt > p                (the setup-route intro
        paragraph, tc_140543)
      .qc-qmo-highlight > .qc-qmo-highlight-title / .qc-qmo-highlight-body
        ("What shapes your setup?" card, tc_140543)
      h3.qc-qmo-subhead ("Country facts") + div.qc-qmo-facts > .qc-qmo-fact
        > .qc-qmo-fact-label / .qc-qmo-fact-value / .qc-qmo-fact-desc — 10
        cards, live order CONFIRMED: Location & Geography, Area, Capital,
        Major Cities, Religion, Language, Climate, Currency, National Day,
        Local Time (tc_140544, exact live order matches the case)
      h3.qc-qmo-subhead ("Economic snapshot") + div.qc-qmo-snapshot.qc-qmo-rt
        > p (tc_140545)
      div.qc-qmo-table-box (×2, Largest listed companies / GDP by sector) >
        div.qc-qmo-table-head > p.qc-qmo-table-eyebrow / p.qc-qmo-table-title
        / div.qc-qmo-table-sub.qc-qmo-rt; div.qc-qmo-table-scroll >
        table.qc-qmo-table > thead > th.qc-qmo-th(.qc-qmo-th-value) ; tbody >
        tr > td.qc-qmo-td(.qc-qmo-td-value); p.qc-qmo-table-note — CONFIRMED
        LIVE row counts (10 / 7) and first-row/footnote text match
        tc_140546/tc_140547 exactly (tc_140546, tc_140547)
      h3.qc-qmo-subhead ("Practical information") + div.qc-qmo-info-grid >
        .qc-qmo-info-card > .qc-qmo-info-title / .qc-qmo-info-list >
        .qc-qmo-info-item — 3 cards (Official Working Hours / Official
        Holidays / Electric Current), CONFIRMED LIVE item text matches
        tc_140548 exactly (tc_140548)

    Section 02 (`#qc-qmo-panel-emir-1`, "The Emir") —
    tc_140549/140550/140551:
      div.qc-qmo-emir-copy > p.qc-qmo-eyebrow.qc-qmo-emir-eyebrow ("Head of
        State") / h3.qc-qmo-emir-name (full name) /
        div.qc-qmo-emir-body.qc-qmo-rt > p (biography paragraph)
      div.qc-qmo-emir-figure > img.qc-qmo-emir-img[src][alt] + div
        .qc-qmo-emir-caption > .qc-qmo-emir-caption-name /
        .qc-qmo-emir-caption-role — CONFIRMED LIVE the alt attribute IS
        non-empty here ("Portrait of HH Sheikh Tamim Bin Hamad Al-Thani,
        Emir of the State of Qatar"), unlike the hero image above — a real,
        different (better) accessibility state for THIS image (tc_140549)
      div.qc-qmo-tiles > .qc-qmo-tile > .qc-qmo-tile-label / .qc-qmo-tile-value
        — 2 tiles, CONFIRMED LIVE text matches tc_140550 exactly
      Four `h3.qc-qmo-subhead` + `ul.qc-qmo-bullets > li.qc-qmo-bullet >
        div.qc-qmo-rt > p` GROUPS in document order: "Functions of the
        Emir" (8 items), "Academic Qualifications" (2), "Selected
        Experience" (5), "Selected Medals & Orders" (3) — CONFIRMED LIVE
        counts and first-item text match tc_140551 exactly. Identified by
        the SAME `.qc-qmo-subhead` element the accordion-header/section-01
        group headings use (a shared, reused class across this whole
        component) — scoped per-group by pairing each subhead with its
        immediately-following `ul.qc-qmo-bullets` sibling, not by a
        dedicated "profile group" wrapper element (none exists).

    Section 03 (`#qc-qmo-panel-government-2`, "Government and
    Legislatives") — tc_140552/140553/140554/140569/140577:
      .qc-qmo-panel-intro.qc-qmo-rt > p (tc_140552's own intro paragraph)
      Five `.qc-qmo-block` elements (each `.qc-qmo-block-label` +
        `.qc-qmo-block-body`), in order: "Government Structure", "History
        of Government", "Institutional Development & Modernization",
        "Institutional Levers", "Public-Sector Modernization" — CONFIRMED
        LIVE order/text matches tc_140552 exactly.
      Each `.qc-qmo-block` is immediately followed by a sibling
        `.qc-qmo-block-stack` (5 of them) — the "Institutional Development &
        Modernization" one holds `.qc-qmo-tags > .qc-qmo-tag` (7 chips,
        CONFIRMED LIVE text/order matches tc_140553 exactly); the
        "Institutional Levers" one holds `.qc-qmo-levers > .qc-qmo-lever >
        .qc-qmo-lever-title / .qc-qmo-lever-body` (6 cards, CONFIRMED LIVE
        title/description text matches tc_140554 exactly, including the
        first ("Policy & Planning") and last ("Technology & Performance")).
      CONFIRMED LIVE, REAL DISCLOSED GAP (tc_140569's "external link" step /
      tc_140577 in full): a full-document `querySelectorAll('a')` scoped to
      `[data-qc-qmo-accordion]`, AND a whole-page-source substring search
      for "qatarchamber.com"/"External Reference", both returned ZERO
      matches — there is currently NO external link anywhere in ANY
      section's content on this environment. tc_140577's entire premise (a
      configured external link inside section 03) has no live counterpart
      and would require CMS/Object-Authoring content work to create, which
      is out of scope for this Web-only batch — see the test module's own
      per-test disposition (140577 is disclosed/skipped, not fabricated;
      140569's OTHER three steps — anonymous view, expand, collapse — are
      fully live-verifiable and ARE scripted; only its external-link step is
      omitted, disclosed in that test's own docstring).

    Arabic page (`/ar/web/qatar-chamber/qatar-market-overview`) — CONFIRMED
    LIVE fully translated: `html dir="rtl"`, hero title "نظرة عامة على سوق
    قطر" (matches tc_140555's own quoted title exactly), breadcrumb "الرئيسية
    › بوابة الأعمال", all 10 Country Fact labels, the Emir's full name, and
    all five Section-03 block titles/bodies translated to real Arabic (no
    English leaking through anywhere probed) — the live counterpart for
    tc_140630's "section with no Arabic translation" precondition does NOT
    exist on this environment (every section IS fully translated); see the
    test module's own disposition for that case (reported, not automated).
    The AR intro subtext carries the SAME corrected "open as many as you
    need" meaning as the EN one (not the case's quoted "one section at a
    time" AR text) — same disclosed finding as the EN side above.

    Accessibility Tools panel (shared `AccessibilityToolsComponent`,
    extended here — see that file's own module docstring) — Dark mode via
    `data-theme`, High Contrast via the `qc-a11y-contrast` class +
    `aria-checked`, BOTH CONFIRMED LIVE to persist across a full page
    reload. High Contrast CONFIRMED LIVE to genuinely repaint colours (a
    Country-Fact description text + background moved from
    rgb(108,108,107)-on-rgb(255,255,255) to rgb(255,255,255)-on-rgb(0,0,0) —
    a real ~21:1 contrast ratio, comfortably over the 4.5:1 the WCAG-style
    `contrast_ratio_against_background()` helper below computes).
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

QATAR_MARKET_OVERVIEW_PATH = "/web/qatar-chamber/qatar-market-overview"
HOME_PATH = "/web/qatar-chamber"

# Live-confirmed section order (0-indexed, matches accordion header order).
SECTION_GLANCE = 0
SECTION_EMIR = 1
SECTION_GOVERNMENT = 2

# JS contrast-ratio computation — walks up for the nearest non-transparent
# background, converts sRGB -> linear, and returns the WCAG relative-
# luminance contrast ratio. Kept here (not core/utils) since no other page
# in this repo needed a real numeric contrast check yet — see module
# docstring's High Contrast section for the live evidence this is based on.
_CONTRAST_RATIO_JS = """
(el) => {
    function parseRgb(str) {
        const m = (str || '').match(/[\\d.]+/g);
        return m ? m.slice(0, 3).map(Number) : [255, 255, 255];
    }
    function luminance(rgb) {
        const a = rgb.map((v) => {
            v /= 255;
            return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * a[0] + 0.7152 * a[1] + 0.0722 * a[2];
    }
    const fg = parseRgb(getComputedStyle(el).color);
    let bgEl = el;
    let bg = null;
    while (bgEl) {
        const c = getComputedStyle(bgEl).backgroundColor;
        if (c && c !== 'rgba(0, 0, 0, 0)' && c !== 'transparent') {
            bg = parseRgb(c);
            break;
        }
        bgEl = bgEl.parentElement;
    }
    if (!bg) bg = [255, 255, 255];
    const l1 = luminance(fg);
    const l2 = luminance(bg);
    const lighter = Math.max(l1, l2);
    const darker = Math.min(l1, l2);
    return (lighter + 0.05) / (darker + 0.05);
}
"""


class QatarMarketOverviewPage(BasePage):
    # ---- Page chrome / hero -------------------------------------------
    CRUMBS = "[data-qc-qmo-crumbs]"
    CRUMB_HOME = ".qc-qmo-crumb:not(.is-current)"
    CRUMB_CURRENT = ".qc-qmo-crumb.is-current"
    # Scoped to the hero container — CONFIRMED LIVE `.qc-qmo-eyebrow` is a
    # SHARED class also used by the Emir section's own eyebrow
    # (`.qc-qmo-eyebrow.qc-qmo-emir-eyebrow`), and accordion panels stay
    # DOM-mounted at all times (see module docstring) — an unscoped
    # `.qc-qmo-eyebrow` locator is a real strict-mode ambiguity (2 matches),
    # not a page-structure defect. Always read/query the hero eyebrow
    # through this HERO_ROOT-scoped constant, never the bare class.
    EYEBROW = "[data-qc-qmo-hero] .qc-qmo-eyebrow"
    TITLE = "[data-qc-qmo-title]"
    HERO_DESC = "[data-qc-qmo-desc]"
    HERO_ROOT = "[data-qc-qmo-hero]"
    HERO_ART = ".qc-qmo-hero-art"
    HERO_IMAGE = "[data-qc-qmo-hero-img]"

    # ---- Discover Qatar intro ------------------------------------------
    INTRO_EYEBROW = "[data-qc-qmo-intro-eyebrow]"
    INTRO_HEADING = "[data-qc-qmo-intro-heading]"
    INTRO_SUBTEXT = "[data-qc-qmo-intro-subtext]"

    # ---- Accordion -------------------------------------------------------
    ACCORDION_ROOT = "[data-qc-qmo-accordion]"
    HEAD = ".qc-qmo-head"
    HEAD_NUM = ".qc-qmo-num"
    HEAD_TITLE = ".qc-qmo-head-title"
    HEAD_SUB = ".qc-qmo-head-sub"

    # ---- Section 01 — Qatar at a Glance ----------------------------------
    PANEL_INTRO = ".qc-qmo-panel-intro"
    HIGHLIGHT = ".qc-qmo-highlight"
    HIGHLIGHT_TITLE = ".qc-qmo-highlight-title"
    HIGHLIGHT_BODY = ".qc-qmo-highlight-body"
    SUBHEAD = ".qc-qmo-subhead"
    FACTS = ".qc-qmo-facts"
    FACT_ITEM = ".qc-qmo-fact"
    FACT_LABEL = ".qc-qmo-fact-label"
    FACT_VALUE = ".qc-qmo-fact-value"
    FACT_DESC = ".qc-qmo-fact-desc"
    SNAPSHOT = ".qc-qmo-snapshot"
    TABLE_BOX = ".qc-qmo-table-box"
    TABLE_EYEBROW = ".qc-qmo-table-eyebrow"
    TABLE_TITLE = ".qc-qmo-table-title"
    TABLE_SUB = ".qc-qmo-table-sub"
    TABLE_NOTE = ".qc-qmo-table-note"
    TABLE_TH = ".qc-qmo-th"
    TABLE_ROW = "tbody tr"
    TABLE_TD = ".qc-qmo-td"
    INFO_GRID = ".qc-qmo-info-grid"
    INFO_CARD = ".qc-qmo-info-card"
    INFO_TITLE = ".qc-qmo-info-title"
    INFO_ITEM = ".qc-qmo-info-item"

    # ---- Section 02 — The Emir --------------------------------------------
    EMIR_EYEBROW = ".qc-qmo-emir-eyebrow"
    EMIR_NAME = ".qc-qmo-emir-name"
    EMIR_BODY = ".qc-qmo-emir-body"
    EMIR_IMAGE = ".qc-qmo-emir-img"
    EMIR_CAPTION_NAME = ".qc-qmo-emir-caption-name"
    EMIR_CAPTION_ROLE = ".qc-qmo-emir-caption-role"
    TILE = ".qc-qmo-tile"
    TILE_LABEL = ".qc-qmo-tile-label"
    TILE_VALUE = ".qc-qmo-tile-value"
    BULLETS_LIST = ".qc-qmo-bullets"
    BULLET_ITEM = ".qc-qmo-bullet"

    # ---- Section 03 — Government and Legislatives -------------------------
    BLOCK = ".qc-qmo-block"
    BLOCK_LABEL = ".qc-qmo-block-label"
    BLOCK_BODY = ".qc-qmo-block-body"
    BLOCK_STACK = ".qc-qmo-block-stack"
    TAGS = ".qc-qmo-tags"
    TAG = ".qc-qmo-tag"
    LEVERS = ".qc-qmo-levers"
    LEVER = ".qc-qmo-lever"
    LEVER_TITLE = ".qc-qmo-lever-title"
    LEVER_BODY = ".qc-qmo-lever-body"

    # ---- Header language toggle -------------------------------------------
    LANGUAGE_TOGGLE = "a.qc-lang-switcher"

    # ---- Navigation ---------------------------------------------------------
    def open_qatar_market_overview(self, locale: str = "en") -> "QatarMarketOverviewPage":
        self.open(web_url(QATAR_MARKET_OVERVIEW_PATH, locale=locale))
        self.wait_for(self.TITLE, state="visible")
        return self

    def navigate_via_main_menu(self) -> "QatarMarketOverviewPage":
        """Home -> hover "Business Gateway" -> click "Qatar Market
        Overview" — CONFIRMED LIVE this is a hover-revealed submenu leaf
        link (see module docstring), same shape as
        hall_booking_page.py/food_handlers_certification_page.py's own
        navigate_via_main_menu()."""
        self.open(web_url(HOME_PATH))
        gateway_link = self.page.get_by_role("link", name="Business Gateway", exact=True).first
        gateway_link.hover()
        self.page.wait_for_timeout(500)
        qmo_link = self.page.get_by_role("link", name="Qatar Market Overview", exact=True).first
        qmo_link.wait_for(state="visible")
        qmo_link.hover()
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            qmo_link.click()
        self.wait_for(self.TITLE, state="visible")
        return self

    # ---- Breadcrumb -----------------------------------------------------------
    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.CRUMBS)

    def breadcrumb_text(self) -> str:
        return self.text(self.CRUMBS)

    def click_breadcrumb_home(self) -> None:
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.CRUMB_HOME)

    # ---- Hero -----------------------------------------------------------------
    def eyebrow_text(self) -> str:
        return self.text(self.EYEBROW)

    def title_text(self) -> str:
        return self.text(self.TITLE)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def hero_image_state(self) -> dict:
        img = self.page.locator(self.HERO_IMAGE)
        if img.count() == 0:
            return {"exists": False, "src": "", "alt": "", "loaded": False, "width": 0, "height": 0}
        box = img.bounding_box()
        return {
            "exists": True,
            "src": img.get_attribute("src") or "",
            "alt": img.get_attribute("alt") or "",
            "loaded": bool(img.evaluate("el => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0")),
            "natural_width": img.evaluate("el => el.naturalWidth"),
            "natural_height": img.evaluate("el => el.naturalHeight"),
            "width": box["width"] if box else 0,
            "height": box["height"] if box else 0,
        }

    def hero_box_width(self) -> float:
        box = self.page.locator(self.HERO_ROOT).bounding_box()
        return box["width"] if box else 0

    def hero_art_width(self) -> float:
        """The hero banner IMAGE's own container width — CONFIRMED LIVE to
        be a small (424px at 1920px viewport) art panel beside the hero
        copy, NOT a full-bleed banner (see module docstring's tc_140539
        disclosed finding). Distinct from hero_box_width() (the whole hero
        SECTION, which genuinely does span 1920px)."""
        box = self.page.locator(self.HERO_ART).bounding_box()
        return box["width"] if box else 0

    def computed_style(self, locator: str, *props: str) -> dict:
        """Generic computed-style state query — a shared reader used across
        several design-token cases (color/font-family/font-weight/font-size),
        rather than one bespoke method per element."""
        el = self.page.locator(locator).first
        return el.evaluate(
            "(el, props) => Object.fromEntries(props.map(p => [p, getComputedStyle(el)[p]]))",
            list(props),
        )

    # ---- Discover Qatar intro ---------------------------------------------------
    def intro_eyebrow_text(self) -> str:
        return self.text(self.INTRO_EYEBROW)

    def intro_heading_text(self) -> str:
        return self.text(self.INTRO_HEADING)

    def intro_subtext_text(self) -> str:
        return self.text(self.INTRO_SUBTEXT)

    # ---- Accordion — headers -----------------------------------------------------
    def header_count(self) -> int:
        return self.page.locator(self.HEAD).count()

    def _panel_id(self, position: int) -> str:
        return self.page.locator(self.HEAD).nth(position).get_attribute("aria-controls")

    def panel_locator(self, position: int):
        return self.page.locator(f"#{self._panel_id(position)}")

    def header_num_text(self, position: int) -> str:
        return self.page.locator(self.HEAD).nth(position).locator(self.HEAD_NUM).inner_text()

    def header_title_text(self, position: int) -> str:
        return self.page.locator(self.HEAD).nth(position).locator(self.HEAD_TITLE).inner_text()

    def header_sub_text(self, position: int) -> str:
        return self.page.locator(self.HEAD).nth(position).locator(self.HEAD_SUB).inner_text()

    def header_num_color(self, position: int) -> str:
        return self.page.locator(self.HEAD).nth(position).locator(self.HEAD_NUM).evaluate(
            "el => getComputedStyle(el).color"
        )

    def header_title_color(self, position: int) -> str:
        return self.page.locator(self.HEAD).nth(position).locator(self.HEAD_TITLE).evaluate(
            "el => getComputedStyle(el).color"
        )

    def is_header_expanded(self, position: int) -> bool:
        return self.page.locator(self.HEAD).nth(position).get_attribute("aria-expanded") == "true"

    def is_panel_hidden(self, position: int) -> bool:
        """The real, live-confirmed collapse signal — panels stay mounted
        in the DOM at all times with their full content; collapse toggles
        the `hidden` attribute, it does not remove the content nodes (see
        module docstring). Mirrors hall_booking_page.py's own
        is_accordion_body_hidden()."""
        return self.panel_locator(position).get_attribute("hidden") is not None

    def click_header(self, position: int, timeout: int = 6000) -> "QatarMarketOverviewPage":
        head = self.page.locator(self.HEAD).nth(position)
        was_expanded = head.get_attribute("aria-expanded") == "true"
        head.click()
        self.page.wait_for_function(
            "([pos, expectExpanded]) => { const h = document.querySelectorAll('.qc-qmo-head')[pos]; "
            "return !!h && (h.getAttribute('aria-expanded') === (expectExpanded ? 'true' : 'false')); }",
            arg=[position, not was_expanded],
            timeout=timeout,
        )
        return self

    def panel_content_signature(self, position: int) -> dict:
        """A cheap, real "does any body content render" signature used for
        the collapsed-by-default / no-body-content cases: counts of the
        content types that live inside a panel, read against the REAL
        hidden/visible state (not literal DOM presence — see
        is_panel_hidden's own docstring)."""
        panel = self.panel_locator(position)
        return {
            "hidden": panel.get_attribute("hidden") is not None,
            "fact_cards": panel.locator(self.FACT_ITEM).count(),
            "info_cards": panel.locator(self.INFO_CARD).count(),
            "tiles": panel.locator(self.TILE).count(),
            "levers": panel.locator(self.LEVER).count(),
            "tags": panel.locator(self.TAG).count(),
        }

    def section_links(self, position: int) -> list:
        """Every anchor inside a panel — used to confirm/deny the presence
        of a configured external link (see module docstring's tc_140569/
        tc_140577 disclosed finding: currently always empty)."""
        anchors = self.panel_locator(position).locator("a")
        return [
            {
                "text": anchors.nth(i).inner_text(),
                "href": anchors.nth(i).get_attribute("href"),
                "target": anchors.nth(i).get_attribute("target"),
            }
            for i in range(anchors.count())
        ]

    # ---- Section 01 — Qatar at a Glance -------------------------------------------
    def panel_intro_text(self, position: int) -> str:
        return self.panel_locator(position).locator(self.PANEL_INTRO).inner_text()

    def highlight_title_text(self) -> str:
        return self.panel_locator(SECTION_GLANCE).locator(self.HIGHLIGHT_TITLE).inner_text()

    def highlight_body_text(self) -> str:
        return self.panel_locator(SECTION_GLANCE).locator(self.HIGHLIGHT_BODY).inner_text()

    def subhead_text(self, position: int, index: int) -> str:
        return self.panel_locator(position).locator(self.SUBHEAD).nth(index).inner_text()

    def fact_count(self) -> int:
        return self.panel_locator(SECTION_GLANCE).locator(self.FACT_ITEM).count()

    def fact_state(self, index: int) -> dict:
        fact = self.panel_locator(SECTION_GLANCE).locator(self.FACT_ITEM).nth(index)
        return {
            "label": fact.locator(self.FACT_LABEL).inner_text(),
            "value": fact.locator(self.FACT_VALUE).inner_text(),
            "desc": fact.locator(self.FACT_DESC).inner_text(),
        }

    def snapshot_text(self) -> str:
        return self.panel_locator(SECTION_GLANCE).locator(self.SNAPSHOT).inner_text()

    def table_count(self) -> int:
        return self.panel_locator(SECTION_GLANCE).locator(self.TABLE_BOX).count()

    def table_state(self, index: int) -> dict:
        box = self.panel_locator(SECTION_GLANCE).locator(self.TABLE_BOX).nth(index)
        headers = box.locator(self.TABLE_TH)
        rows = box.locator(self.TABLE_ROW)
        first_row_cells = rows.first.locator(self.TABLE_TD)
        return {
            "eyebrow": box.locator(self.TABLE_EYEBROW).inner_text(),
            "title": box.locator(self.TABLE_TITLE).inner_text(),
            "sub": box.locator(self.TABLE_SUB).inner_text(),
            "note": box.locator(self.TABLE_NOTE).inner_text(),
            "headers": [headers.nth(i).inner_text() for i in range(headers.count())],
            "row_count": rows.count(),
            "first_row": [first_row_cells.nth(i).inner_text() for i in range(first_row_cells.count())],
        }

    def info_card_count(self) -> int:
        return self.panel_locator(SECTION_GLANCE).locator(self.INFO_CARD).count()

    def info_card_state(self, index: int) -> dict:
        card = self.panel_locator(SECTION_GLANCE).locator(self.INFO_CARD).nth(index)
        items = card.locator(self.INFO_ITEM)
        return {
            "title": card.locator(self.INFO_TITLE).inner_text(),
            "items": [items.nth(i).inner_text() for i in range(items.count())],
        }

    # ---- Section 02 — The Emir -----------------------------------------------------
    def emir_eyebrow_text(self) -> str:
        return self.panel_locator(SECTION_EMIR).locator(self.EMIR_EYEBROW).inner_text()

    def emir_name_text(self) -> str:
        return self.panel_locator(SECTION_EMIR).locator(self.EMIR_NAME).inner_text()

    def emir_body_text(self) -> str:
        return self.panel_locator(SECTION_EMIR).locator(self.EMIR_BODY).inner_text()

    def emir_image_state(self) -> dict:
        img = self.panel_locator(SECTION_EMIR).locator(self.EMIR_IMAGE)
        if img.count() == 0:
            return {"exists": False, "src": "", "alt": "", "loaded": False}
        return {
            "exists": True,
            "src": img.get_attribute("src") or "",
            "alt": img.get_attribute("alt") or "",
            "loaded": bool(img.evaluate("el => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0")),
        }

    def emir_caption_state(self) -> dict:
        panel = self.panel_locator(SECTION_EMIR)
        return {
            "name": panel.locator(self.EMIR_CAPTION_NAME).inner_text(),
            "role": panel.locator(self.EMIR_CAPTION_ROLE).inner_text(),
        }

    def emir_tile_count(self) -> int:
        return self.panel_locator(SECTION_EMIR).locator(self.TILE).count()

    def emir_tile_state(self, index: int) -> dict:
        tile = self.panel_locator(SECTION_EMIR).locator(self.TILE).nth(index)
        return {
            "label": tile.locator(self.TILE_LABEL).inner_text(),
            "value": tile.locator(self.TILE_VALUE).inner_text(),
        }

    def emir_profile_group_labels(self) -> list:
        """The four `h3.qc-qmo-subhead` group headings inside the Emir
        panel, in document order (see module docstring — a shared class
        with the Section-01 group headings, scoped here to this panel)."""
        subheads = self.panel_locator(SECTION_EMIR).locator(self.SUBHEAD)
        return [subheads.nth(i).inner_text() for i in range(subheads.count())]

    def emir_profile_group_items(self, index: int) -> list:
        """Bullet item texts for the Nth profile-list group — the
        `ul.qc-qmo-bullets` immediately following the Nth `.qc-qmo-subhead`
        (no dedicated group-wrapper element exists, see module docstring)."""
        subhead = self.panel_locator(SECTION_EMIR).locator(self.SUBHEAD).nth(index)
        bullets_html = subhead.evaluate(
            """(el) => {
                let sib = el.nextElementSibling;
                while (sib && !sib.classList.contains('qc-qmo-bullets')) sib = sib.nextElementSibling;
                if (!sib) return [];
                return Array.from(sib.querySelectorAll('.qc-qmo-bullet')).map(li => li.innerText.trim());
            }"""
        )
        return bullets_html

    # ---- Section 03 — Government and Legislatives -----------------------------------
    def block_count(self, position: int = SECTION_GOVERNMENT) -> int:
        return self.panel_locator(position).locator(self.BLOCK).count()

    def block_state(self, index: int, position: int = SECTION_GOVERNMENT) -> dict:
        block = self.panel_locator(position).locator(self.BLOCK).nth(index)
        return {
            "title": block.locator(self.BLOCK_LABEL).inner_text(),
            "body": block.locator(self.BLOCK_BODY).inner_text(),
        }

    def tag_count(self) -> int:
        return self.panel_locator(SECTION_GOVERNMENT).locator(self.TAG).count()

    def tag_texts(self) -> list:
        tags = self.panel_locator(SECTION_GOVERNMENT).locator(self.TAG)
        return [tags.nth(i).inner_text() for i in range(tags.count())]

    def lever_count(self) -> int:
        return self.panel_locator(SECTION_GOVERNMENT).locator(self.LEVER).count()

    def lever_state(self, index: int) -> dict:
        lever = self.panel_locator(SECTION_GOVERNMENT).locator(self.LEVER).nth(index)
        return {
            "title": lever.locator(self.LEVER_TITLE).inner_text(),
            "body": lever.locator(self.LEVER_BODY).inner_text(),
        }

    # ---- Language toggle --------------------------------------------------------------
    def language_toggle_label(self) -> str:
        return self.text(self.LANGUAGE_TOGGLE)

    def click_language_toggle(self) -> "QatarMarketOverviewPage":
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.LANGUAGE_TOGGLE)
        self.wait_for(self.TITLE, state="visible")
        return self

    def html_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def html_lang(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    # ---- Theme / High Contrast — composes AccessibilityToolsComponent -----------------
    def set_theme_dark(self, enabled: bool) -> "QatarMarketOverviewPage":
        AccessibilityToolsComponent(self.page).set_dark_mode(enabled)
        return self

    def current_theme(self) -> str:
        return AccessibilityToolsComponent(self.page).current_theme()

    def set_high_contrast(self, enabled: bool) -> "QatarMarketOverviewPage":
        AccessibilityToolsComponent(self.page).set_high_contrast(enabled)
        return self

    def is_high_contrast_active(self) -> bool:
        return AccessibilityToolsComponent(self.page).is_high_contrast_active()

    def contrast_ratio_against_background(self, locator: str) -> float:
        """WCAG-style relative-luminance contrast ratio between `locator`'s
        own computed text color and the nearest non-transparent ancestor
        background — see module docstring's `_CONTRAST_RATIO_JS`."""
        return self.page.locator(locator).first.evaluate(_CONTRAST_RATIO_JS)

    def contrast_ratio_in_panel(self, position: int, locator: str) -> float:
        return self.panel_locator(position).locator(locator).first.evaluate(_CONTRAST_RATIO_JS)

    # ---- Layout-health primitives (compatibility-matrix cases) -----------------------
    def has_horizontal_overflow(self) -> bool:
        return bool(self.page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth + 1"
        ))

    def viewport_width(self) -> int:
        return self.page.evaluate("() => window.innerWidth")

"""
web/pages/food_handlers_certification/food_handlers_certification_page.py —
FoodHandlersCertificationPage.

Public-frontend Page Object for PBI 129696 (QC-Training-002 — Food Handlers
Certification and Authorization Training Program), under the `SVC` service/
module (standards.md's Service/Module Codes: Training Platform lives under
"Our Services"). Sourced from Azure DevOps suite 140259 (plan 137724), the
34 injected cases filtered down to `Tag=Web` with no `Control_Panel` tag; 32
of the 34 also carry `Tag=Automation` and are scripted here (140195/140196
are `Manual` — no test exists for them, see the test module's own
docstring). This is the pure public-facing (Platform=Web) surface only — no
admin/CMS steps anywhere in this batch (rule from the task itself: this PBI
has no CMS/Control_Panel side to this batch).

REAL LIVE URL — NOT the literal path the QA cases' steps use. Every case's
own step text says `/en/our-services/training/food-handlers-certification`
— CONFIRMED LIVE this 404s ("Coming Soon" placeholder). The real, working
page (confirmed 200, matching content) is at
`/web/qatar-chamber/training/food-handlers-certification` (Arabic:
`/ar/web/qatar-chamber/training/food-handlers-certification`) — the exact
same `/web/qatar-chamber/<slug>` scheme this repo's own
`hall_booking_page.py` already documents for the Halls Booking page. Reached
live via the real main-menu path: Home -> hover "Our Services" -> click
"Food Handlers Certification" (a direct leaf link under Our Services in the
live mega-menu — CONFIRMED LIVE there is no separate "Training" hover step
in between, unlike the cases' literal "Our Services > Training > Food
Handlers Certification" wording; "Training Programs" is a sibling leaf, not
an ancestor, of "Food Handlers Certification" in the live nav).

Locators extracted CLI-first via tools/extract_locators.py against the live
page (WEB_BASE_URL=https://qcdev.ihorizons.com) at the framework default
viewport:

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/web/qatar-chamber/training/food-handlers-certification

    -> role=link[name="fhp@qcci.org"] / "44559187 – 44559893" / "50088830"
       (the three Section 05 contact channels — already real mailto/tel/
       wa.me anchors, not plain text)
    -> role=link[name="Login"] / "Create Account"  (Platform CTA banner —
       CONFIRMED LIVE these are real <a> elements, not <button>s, despite
       every case's own wording calling them "buttons")
    -> role=button[name="Accessibility tools"]  (opens the Light/Dark theme
       panel — see accessibility_tools_component.py)
    -> role=link[name="Home"]  (breadcrumb's own "Home" crumb)

Everything else (hero, quick facts, sticky index, the 5 sections, the
Platform CTA banner's copy) is non-interactive/rich content that
`extract_locators.py`'s harvester does not surface at all (the exact same
class of gap `hall_booking_page.py`'s own module docstring already
documents for its `data-qc-hb-*` batch) — found instead via a disclosed,
scripted DOM probe (still CLI — a plain Playwright script run in the shell,
not the Playwright MCP), confirmed live against qcdev at the framework's
default 1920x1080 viewport. This component's own custom-attribute family is
`data-qc-fh-*` ("fh" = Food Handlers), the highest-tier locator here exactly
as `hall_booking_page.py` gives its own `data-qc-hb-*` family precedence
over generic CSS:

    <html data-theme="light|dark" dir="ltr|rtl" lang="en-US|ar-SA">
    nav.qc-fh-crumbs[data-qc-fh-crumbs]
      a.qc-fh-crumb[href="/web/qatar-chamber"]                (Home — NOT is-current)
      a.qc-fh-crumb.is-current[aria-current="page"][href=...]  (the trailing/current
        crumb, labelled "Training" — CONFIRMED LIVE there is NO separate 3rd
        crumb for the page's own title; "Training" itself is marked
        aria-current="page", matching case 140179's own wording ("the
        current page as the non-clickable trailing crumb") more precisely
        than 140165/140168's wording, which implies a 3rd crumb that does
        not exist live — the two cases describe the SAME real breadcrumb,
        just with slightly different literal phrasing; scoped to the real,
        confirmed 2-crumb structure)
    p.qc-fh-eyebrow[data-qc-fh-eyebrow]                       "Qatar Chamber of Commerce & Industry"
    h1.qc-fh-title[data-qc-fh-title]                          "Food Handlers Certification & Authorization Training"
    div.qc-fh-hero-desc.qc-fh-rt[data-qc-fh-desc] > p
    img.qc-fh-hero-img[data-qc-fh-hero-img][src][alt=""]      CONFIRMED LIVE: a real,
      loaded photo (non-empty src, natural dimensions > 0) but an EMPTY
      `alt` attribute — a real, disclosed accessibility gap against
      tc_140168's own expected result ("non-empty alt attribute"); see the
      test module's own per-test docstring, not silently loosened here.
    div.qc-fh-facts[data-qc-fh-facts] > div.qc-fh-fact
      span.qc-fh-fact-label / span.qc-fh-fact-value            4 tiles, live-confirmed
      order: Training Types/2 types, Test at Qatar Chamber/In Person,
      Test Fees/QAR 50, License Validity/3 Years
    nav.qc-fh-index[data-qc-fh-index]                         CONFIRMED LIVE
      `position: sticky` on its own parent (stays pinned after a 2000px
      real-wheel scroll — see scroll_by_wheel(), same technique
      hall_booking_page.py's own docstring establishes: a synthetic
      `window.scrollTo()` is NOT used here for this reason too).
      a.qc-fh-index-item[href="#qc-fh-s0N"] > span.qc-fh-index-num ("01".."05")
        + span.qc-fh-index-label ("Overview"/"Test"/"Training"/"License"/"Contact")
      CONFIRMED LIVE, REAL PRODUCT GAP (not a locator/script issue): clicking
      an index item DOES scroll the viewport to its target section (native
      in-page anchor jump — verified: target section's top lands near the
      viewport top after the click), but NO `.is-active`/`aria-current`
      class or attribute is EVER applied to any `.qc-fh-index-item` — tested
      via a real click, a direct `scrollIntoView`, AND 15 incremental real
      mouse-wheel steps, all three showing zero DOM change on the index
      items. This directly contradicts tc_140194's expected "highlights the
      section currently in the viewport" behavior — see that test's own
      docstring; a real, disclosed FAIL, not silently adapted away.
    section#qc-fh-s01..05.qc-fh-section
      .qc-fh-section-badge / .qc-fh-section-title / .qc-fh-rt.qc-fh-section-body
      .qc-fh-fee > .qc-fh-fee-label / .qc-fh-fee-value          (Sections 02, 04 only)
      h3.qc-fh-block-title                                      ("Test Requirements" /
        "Test Results" / "License Requirements" / "License Validity" /
        "Applicable Regulations" — one per named sub-block)
      ul.qc-fh-bullets > li.qc-fh-bullet > span.qc-fh-bullet-text.qc-fh-rt
      article.qc-fh-card > h4.qc-fh-card-title / .qc-fh-card-desc         (Section 03,
        2 cards: "Training through Qatar Chamber" with 2
        div.qc-fh-sub[.qc-fh-sub-label/.qc-fh-sub-desc/.qc-fh-sub-price]
        children — "Internal Training" QAR 150/person, "External Training"
        QAR 200/person; "Internal Company Training" with its own
        ul.qc-fh-bullets.is-tight condition list)
      div.qc-fh-callout.is-importantRed    (Section 02 — "Important Notes")
      div.qc-fh-callout.is-successGreen    (Section 03 — "Attendance Certificate")
      div.qc-fh-callout.is-infoAmber       (Section 03 — "Next Step", an INLINE
        `<p class="qc-fh-callout-inline"><strong>Next Step: </strong>...</p>`
        format, no separate `.qc-fh-callout-title` element — different
        internal structure from the other two callouts, handled by
        `callout_text()` reading the whole callout's `inner_text()` rather
        than assuming a `.qc-fh-callout-title` child always exists)
      div.qc-fh-channels > div.qc-fh-channel                    (Section 05, 3 channels
        in order: Email/mailto:fhp@qcci.org, Phone/tel:44559187 (the FIRST
        of the two numbers — 44559893 is in the same anchor's visible text
        but NOT a second href; see CONTACT CHANNELS note below),
        Mobile/Whatsapp/https://wa.me/97450088830 target="_blank")
    div[data-qc-fh-cta] > div.qc-fh-cta
      .qc-fh-cta-eyebrow "Ready to continue?" / .qc-fh-cta-heading
      "Food Handling Certification Platform" / .qc-fh-cta-sub.qc-fh-rt
      a.qc-fh-cta-btn (×2: "Login", "Create Account") — CONFIRMED LIVE REAL
      CONTENT GAP: both currently carry `href="/"` (resolves to the site's
      own home page), NOT any external Food Handling Certification Platform
      URL, and neither carries `target="_blank"`. Clicking "Login" was
      confirmed live (via `expect_navigation`) to land on
      `https://qcdev.ihorizons.com/` — the site root, not an external HTTPS
      platform. This is a real, disclosed, live-confirmed gap against
      tc_140185/tc_140245's own expected "reaches the configured external
      platform" — a genuine FAIL, not adapted/loosened; see those tests'
      own docstrings. tc_140176's own narrower wording ("each carries a
      non-empty href") still genuinely passes, since `href="/"` IS
      non-empty.
    a.qc-lang-switcher                                          header AR/EN toggle,
      href=/c/portal/update_language?...languageId=ar_SA|en_US — same
      pattern hall_booking_page.py already documents.

CONTACT CHANNELS — Phone anchor detail (tc_140182): CONFIRMED LIVE the
Phone channel is ONE `<a href="tel:44559187">44559187 – 44559893</a>` — a
single anchor whose href only encodes the FIRST number; the second number
(44559893) is part of the same anchor's visible text but is NOT itself a
second `tel:` href/anchor. tc_140182's own case text says "the value
exposes two anchors with hrefs 'tel:44559187' and 'tel:44559893'" — this is
a real, disclosed mismatch against live markup (one anchor, one working
tel: href for the FIRST number only); see that test's own docstring, a
genuine FAIL, not silently adapted.

BREADCRUMB "Training" crumb navigation (tc_140179): CONFIRMED LIVE (via
`page.expect_navigation`, NOT a plain `.click()` — the same
`expect_navigation` requirement `hall_booking_page.py`'s own docstring
already flags for this project's breadcrumb links, and a first,
un-navigation-wrapped probe attempt during this same investigation produced
a FALSE "does not navigate" reading purely from that race, corrected before
being written up here) that clicking `.qc-fh-crumb.is-current` DOES
navigate — to `https://qcdev.ihorizons.com/web/qatar-chamber/our-services/member-services`,
a real Services-domain landing page, not the case's literal
"/en/our-services/training" path. Scoped like `hall_booking_page.py` scopes
its own SERVICES_PATH assertion: verified as "navigates away from the Food
Handlers page to a real, resolvable Services-area URL", not a literal-path
match to the case's own illustrative wording.

CALLOUT STYLE VALUES (tc_140250): CONFIRMED LIVE this page currently
carries all THREE named Style treatments simultaneously on three DIFFERENT
already-published callouts (Important Notes = `is-importantRed`, Attendance
Certificate = `is-successGreen`, Next Step = `is-infoAmber`) rather than one
callout being cycled through the three via CMS publish (which tc_140250's
own steps describe, and which is out of scope — no CMS/Control_Panel work
in this batch). `callout_color_state(modifier_class)` reads each one's own
computed title-color/background-color so the test can verify the three
treatments are genuinely DISTINCT from one another (the real intent behind
"is visually distinct") using only what is live today — disclosed scope
adaptation, not a fabricated pass. Per the task's own practical-scope note,
no literal hex value from the QA case text is asserted anywhere in this
Page Object or its tests (this batch has no Figma access) — colours are
compared to EACH OTHER (distinctness), and/or to the SAME element's own
Light-theme reading (theme-driven change), never to a hard-coded hex.
"""

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

FOOD_HANDLERS_PATH = "/web/qatar-chamber/training/food-handlers-certification"
HOME_PATH = "/web/qatar-chamber"

# Section anchor ids, in the live, Display-Order-1..5 order.
SECTION_IDS = (
    "qc-fh-s01",  # Overview
    "qc-fh-s02",  # Test
    "qc-fh-s03",  # Training
    "qc-fh-s04",  # License
    "qc-fh-s05",  # Contact
)

CALLOUT_IMPORTANT = ".qc-fh-callout.is-importantRed"
CALLOUT_SUCCESS = ".qc-fh-callout.is-successGreen"
CALLOUT_INFO = ".qc-fh-callout.is-infoAmber"


class FoodHandlersCertificationPage(BasePage):
    # ---- Page chrome / hero -------------------------------------------
    CRUMBS_NAV = "[data-qc-fh-crumbs]"
    CRUMB_HOME = ".qc-fh-crumb:not(.is-current)"
    CRUMB_CURRENT = ".qc-fh-crumb.is-current"
    EYEBROW = "[data-qc-fh-eyebrow]"
    TITLE = "[data-qc-fh-title]"
    HERO_DESC = "[data-qc-fh-desc]"
    HERO_IMAGE = "[data-qc-fh-hero-img]"

    # ---- Quick facts -----------------------------------------------------
    FACTS = "[data-qc-fh-facts]"
    FACT_ITEM = ".qc-fh-fact"
    FACT_LABEL = ".qc-fh-fact-label"
    FACT_VALUE = ".qc-fh-fact-value"

    # ---- Sticky section index ---------------------------------------------
    INDEX_NAV = "[data-qc-fh-index]"
    INDEX_ITEM = ".qc-fh-index-item"
    INDEX_ITEM_NUM = ".qc-fh-index-num"
    INDEX_ITEM_LABEL = ".qc-fh-index-label"

    # ---- Section internals (scoped under a section id) ---------------------
    SECTION_BADGE = ".qc-fh-section-badge"
    SECTION_TITLE = ".qc-fh-section-title"
    SECTION_BODY = ".qc-fh-section-body"
    FEE_TILE = ".qc-fh-fee"
    FEE_LABEL = ".qc-fh-fee-label"
    FEE_VALUE = ".qc-fh-fee-value"
    BLOCK_TITLE = ".qc-fh-block-title"
    BLOCK_BODY = ".qc-fh-block-body"
    BULLET_TEXT = ".qc-fh-bullet-text"
    CARD = ".qc-fh-card"
    CARD_TITLE = ".qc-fh-card-title"
    CARD_DESC = ".qc-fh-card-desc"
    SUB_ITEM = ".qc-fh-sub"
    SUB_LABEL = ".qc-fh-sub-label"
    SUB_DESC = ".qc-fh-sub-desc"
    SUB_PRICE = ".qc-fh-sub-price"
    CALLOUT_TITLE = ".qc-fh-callout-title"
    CHANNELS = ".qc-fh-channels"
    CHANNEL_ITEM = ".qc-fh-channel"
    CHANNEL_LABEL = ".qc-fh-channel-label"
    CHANNEL_VALUE = ".qc-fh-channel-value"

    # ---- Platform CTA banner ------------------------------------------------
    CTA_ROOT = "[data-qc-fh-cta]"
    CTA_EYEBROW = ".qc-fh-cta-eyebrow"
    CTA_HEADING = ".qc-fh-cta-heading"
    CTA_SUB = ".qc-fh-cta-sub"
    CTA_BUTTON = ".qc-fh-cta-btn"

    # ---- Header language toggle ---------------------------------------------
    LANGUAGE_TOGGLE = "a.qc-lang-switcher"

    # ---- Navigation -----------------------------------------------------------
    def open_food_handlers(self, locale: str = "en") -> "FoodHandlersCertificationPage":
        self.open(web_url(FOOD_HANDLERS_PATH, locale=locale))
        self.wait_for(self.TITLE, state="visible")
        return self

    def navigate_via_main_menu(self) -> "FoodHandlersCertificationPage":
        """Home -> hover "Our Services" -> click "Food Handlers
        Certification" — CONFIRMED LIVE this is a direct leaf link under
        the Our Services hover-menu, no intermediate "Training" hover step
        (see module docstring)."""
        self.open(web_url(HOME_PATH))
        services_link = self.page.get_by_role("link", name="Our Services", exact=True).first
        services_link.hover()
        self.page.wait_for_timeout(500)
        fh_link = self.page.get_by_role("link", name="Food Handlers Certification", exact=True).first
        fh_link.wait_for(state="visible")
        fh_link.hover()
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            fh_link.click()
        self.wait_for(self.TITLE, state="visible")
        return self

    # ---- Breadcrumb ------------------------------------------------------
    def is_breadcrumb_visible(self) -> bool:
        return self.is_visible(self.CRUMBS_NAV)

    def breadcrumb_text(self) -> str:
        return self.text(self.CRUMBS_NAV)

    def click_breadcrumb_home(self) -> None:
        # CONFIRMED LIVE (see module docstring): a plain click() + a
        # separate wait_for_load_state() call races the real navigation on
        # this component — must be wrapped in expect_navigation.
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.CRUMB_HOME)

    def click_breadcrumb_current(self) -> None:
        """Clicks the "Training" (is-current/aria-current="page") crumb —
        CONFIRMED LIVE this DOES navigate (see module docstring) when
        properly awaited."""
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.CRUMB_CURRENT)

    # ---- Hero --------------------------------------------------------------
    def eyebrow_text(self) -> str:
        return self.text(self.EYEBROW)

    def title_text(self) -> str:
        return self.text(self.TITLE)

    def hero_desc_text(self) -> str:
        return self.text(self.HERO_DESC)

    def hero_image_state(self) -> dict:
        img = self.page.locator(self.HERO_IMAGE)
        if img.count() == 0:
            return {"exists": False, "src": "", "alt": "", "loaded": False}
        return {
            "exists": True,
            "src": img.get_attribute("src") or "",
            "alt": img.get_attribute("alt") or "",
            "loaded": bool(img.evaluate("el => el.complete && el.naturalWidth > 0 && el.naturalHeight > 0")),
        }

    # ---- Quick facts ---------------------------------------------------------
    def fact_count(self) -> int:
        return self.page.locator(self.FACT_ITEM).count()

    def fact_pairs(self) -> list:
        """[(label, value), ...] in document (display) order."""
        items = self.page.locator(self.FACT_ITEM)
        pairs = []
        for i in range(items.count()):
            item = items.nth(i)
            pairs.append((
                item.locator(self.FACT_LABEL).inner_text(),
                item.locator(self.FACT_VALUE).inner_text(),
            ))
        return pairs

    # ---- Sticky section index --------------------------------------------------
    def is_section_index_visible(self) -> bool:
        return self.is_visible(self.INDEX_NAV)

    def index_item_count(self) -> int:
        return self.page.locator(self.INDEX_ITEM).count()

    def index_item_number_text(self, position: int) -> str:
        return self.page.locator(self.INDEX_ITEM).nth(position).locator(self.INDEX_ITEM_NUM).inner_text()

    def index_item_label_text(self, position: int) -> str:
        return self.page.locator(self.INDEX_ITEM).nth(position).locator(self.INDEX_ITEM_LABEL).inner_text()

    def index_item_labels(self) -> list:
        return [self.index_item_label_text(i) for i in range(self.index_item_count())]

    def click_index_item(self, position: int, timeout: int = 4000) -> "FoodHandlersCertificationPage":
        """In-page anchor jump (native browser scroll, not a scroll-spy
        state change — see module docstring's CONFIRMED-LIVE note on
        is-active never being applied). Waits for the target section's own
        bounding-rect top to actually settle near the viewport top —
        CONFIRMED LIVE the browser's native smooth-scroll anchor jump takes
        longer than a fixed short sleep for a long scroll distance, so a
        blind `wait_for_timeout` sampled it mid-scroll on some positions.
        Polls the real DOM condition instead of sleeping a fixed amount."""
        section_id = SECTION_IDS[position]
        self.page.locator(self.INDEX_ITEM).nth(position).click()
        self.page.wait_for_function(
            "id => { const el = document.getElementById(id); "
            "if (!el) return false; const top = el.getBoundingClientRect().top; "
            "return top > -400 && top < 500; }",
            arg=section_id,
            timeout=timeout,
        )
        return self

    def is_index_item_active(self, position: int) -> bool:
        """CONFIRMED LIVE this is currently ALWAYS False for every position
        — no is-active/aria-current state is ever applied to any index
        item, regardless of scroll or click (see module docstring). Kept
        as a real, honest state query (not a fabricated pass) so
        tc_140194's test can assert the case's real expected behavior and
        fail visibly against this confirmed gap."""
        item = self.page.locator(self.INDEX_ITEM).nth(position)
        classes = item.get_attribute("class") or ""
        aria_current = item.get_attribute("aria-current") or ""
        return "is-active" in classes or aria_current == "true"

    def scroll_by_wheel(self, delta_y: int, steps: int = 10, step_pause_ms: int = 200) -> None:
        """Real, incremental mouse-wheel scroll — same technique
        hall_booking_page.py's own docstring establishes as the one that
        actually drives this project's scroll-spy components (a synthetic
        window.scrollTo() does not)."""
        for _ in range(steps):
            self.page.mouse.wheel(0, delta_y)
            self.page.wait_for_timeout(step_pause_ms)

    def is_index_sticky_after_scroll(self, delta_y: int = 2000) -> bool:
        index = self.page.locator(self.INDEX_NAV)
        self.scroll_by_wheel(delta_y // 10, steps=10)
        return index.is_visible()

    # ---- Sections / content --------------------------------------------------
    def section_locator(self, position: int):
        return self.page.locator(f"#{SECTION_IDS[position]}")

    def is_section_visible(self, position: int) -> bool:
        return self.is_visible(f"#{SECTION_IDS[position]}")

    def section_badge_text(self, position: int) -> str:
        return self.section_locator(position).locator(self.SECTION_BADGE).inner_text()

    def section_title_text(self, position: int) -> str:
        return self.section_locator(position).locator(self.SECTION_TITLE).inner_text()

    def section_body_text(self, position: int) -> str:
        return self.section_locator(position).locator(self.SECTION_BODY).inner_text()

    def section_paragraph_count(self, position: int) -> int:
        return self.section_locator(position).locator(f"{self.SECTION_BODY} p").count()

    def fee_label_text(self, position: int) -> str:
        return self.section_locator(position).locator(self.FEE_LABEL).inner_text()

    def fee_value_text(self, position: int) -> str:
        return self.section_locator(position).locator(self.FEE_VALUE).inner_text()

    def block_title_texts(self, position: int) -> list:
        titles = self.section_locator(position).locator(self.BLOCK_TITLE)
        return [titles.nth(i).inner_text() for i in range(titles.count())]

    def block_body_text_after(self, position: int, block_title: str) -> str:
        """The `.qc-fh-block-body` immediately following the `h3` whose
        text equals `block_title` (e.g. "License Validity",
        "Applicable Regulations") — both Section 04 blocks share the same
        `.qc-fh-block-body` class, so they are distinguished by their own
        preceding heading text rather than position alone."""
        return self.section_locator(position).evaluate(
            """(el, title) => {
                const headings = Array.from(el.querySelectorAll('.qc-fh-block-title'));
                const h = headings.find(x => x.textContent.trim() === title);
                if (!h) return '';
                let sib = h.nextElementSibling;
                while (sib && !sib.classList.contains('qc-fh-block-body')) sib = sib.nextElementSibling;
                return sib ? sib.textContent.trim() : '';
            }""",
            block_title,
        )

    def bullet_texts(self, position: int) -> list:
        bullets = self.section_locator(position).locator(self.BULLET_TEXT)
        return [bullets.nth(i).inner_text() for i in range(bullets.count())]

    def callout_text(self, style_modifier: str) -> str:
        """Whole-callout `inner_text()` for a given style modifier selector
        (CALLOUT_IMPORTANT / CALLOUT_SUCCESS / CALLOUT_INFO) — reads the
        callout as a whole rather than assuming a `.qc-fh-callout-title`
        child always exists (the Info/amber callout has no such element —
        see module docstring)."""
        callout = self.page.locator(style_modifier)
        return callout.inner_text() if callout.count() else ""

    def callout_exists(self, style_modifier: str) -> bool:
        return self.page.locator(style_modifier).count() > 0

    def callout_color_state(self, style_modifier: str) -> dict:
        """Reads the callout's own computed colors, used to compare
        DISTINCTNESS between the three Style values (tc_140250) — never
        compared to a literal hex from the QA case text (see module
        docstring's practical-scope note)."""
        callout = self.page.locator(style_modifier)
        if callout.count() == 0:
            return {"exists": False, "background_color": "", "title_color": ""}
        background_color = callout.first.evaluate("el => getComputedStyle(el).backgroundColor")
        title_el = callout.first.locator(self.CALLOUT_TITLE)
        if title_el.count() == 0:
            # Info/amber callout — no dedicated title element, read the <strong> instead.
            title_el = callout.first.locator("strong")
        title_color = title_el.first.evaluate("el => getComputedStyle(el).color") if title_el.count() else ""
        return {"exists": True, "background_color": background_color, "title_color": title_color}

    def card_count(self, position: int) -> int:
        return self.section_locator(position).locator(self.CARD).count()

    def card_title_text(self, position: int, card_index: int) -> str:
        return self.section_locator(position).locator(self.CARD).nth(card_index).locator(self.CARD_TITLE).inner_text()

    def sub_item_count(self, position: int, card_index: int) -> int:
        return self.section_locator(position).locator(self.CARD).nth(card_index).locator(self.SUB_ITEM).count()

    def sub_item_state(self, position: int, card_index: int, sub_index: int) -> dict:
        sub = self.section_locator(position).locator(self.CARD).nth(card_index).locator(self.SUB_ITEM).nth(sub_index)
        return {
            "label": sub.locator(self.SUB_LABEL).inner_text(),
            "description": sub.locator(self.SUB_DESC).inner_text(),
            "price": sub.locator(self.SUB_PRICE).inner_text(),
        }

    # ---- Section 05 — Contact channels ----------------------------------------
    def channel_count(self) -> int:
        return self.page.locator(self.CHANNEL_ITEM).count()

    def channel_label_text(self, position: int) -> str:
        return self.page.locator(self.CHANNEL_ITEM).nth(position).locator(self.CHANNEL_LABEL).inner_text()

    def channel_value_locator(self, position: int):
        return self.page.locator(self.CHANNEL_ITEM).nth(position).locator(self.CHANNEL_VALUE)

    def channel_value_text(self, position: int) -> str:
        return self.channel_value_locator(position).inner_text()

    def channel_href(self, position: int) -> str:
        return self.channel_value_locator(position).get_attribute("href") or ""

    def channel_target(self, position: int) -> str:
        return self.channel_value_locator(position).get_attribute("target") or ""

    def click_channel(self, position: int) -> None:
        self.channel_value_locator(position).click()

    # ---- Platform CTA banner -----------------------------------------------
    def is_cta_banner_visible(self) -> bool:
        return self.is_visible(self.CTA_ROOT)

    def cta_eyebrow_text(self) -> str:
        return self.text(f"{self.CTA_ROOT} {self.CTA_EYEBROW}")

    def cta_heading_text(self) -> str:
        return self.text(f"{self.CTA_ROOT} {self.CTA_HEADING}")

    def cta_sub_text(self) -> str:
        return self.text(f"{self.CTA_ROOT} {self.CTA_SUB}")

    def cta_button_count(self) -> int:
        return self.page.locator(self.CTA_BUTTON).count()

    def cta_button_label_text(self, position: int) -> str:
        return self.page.locator(self.CTA_BUTTON).nth(position).inner_text()

    def cta_button_href(self, position: int) -> str:
        return self.page.locator(self.CTA_BUTTON).nth(position).get_attribute("href") or ""

    def cta_button_by_label(self, label: str):
        return self.page.locator(self.CTA_BUTTON).filter(has_text=label).first

    def click_cta_button(self, label: str) -> None:
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.cta_button_by_label(label).click()

    # ---- Language toggle --------------------------------------------------------
    def language_toggle_label(self) -> str:
        return self.text(self.LANGUAGE_TOGGLE)

    def click_language_toggle(self) -> "FoodHandlersCertificationPage":
        with self.page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            self.click(self.LANGUAGE_TOGGLE)
        self.wait_for(self.TITLE, state="visible")
        return self

    def html_dir(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def html_lang(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    # ---- Theme (Light/Dark) — composes AccessibilityToolsComponent -----------
    def set_theme_dark(self, enabled: bool) -> "FoodHandlersCertificationPage":
        AccessibilityToolsComponent(self.page).set_dark_mode(enabled)
        return self

    def current_theme(self) -> str:
        return AccessibilityToolsComponent(self.page).current_theme()

    # ---- Layout-health primitives (compatibility-matrix cases) -----------------
    def has_horizontal_overflow(self) -> bool:
        return bool(self.page.evaluate(
            "() => document.documentElement.scrollWidth > window.innerWidth + 1"
        ))

    def viewport_width(self) -> int:
        return self.page.evaluate("() => window.innerWidth")

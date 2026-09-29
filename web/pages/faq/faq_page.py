"""web/pages/faq/faq_page.py — FaqPage.

The public FAQ Knowledge Base page (PBI 131052 "QC - 001 - FAQ Knowledge
Base", LINKS service, Web platform) at `/web/qatar-chamber/faq`
(AR: `/ar/web/qatar-chamber/faq`).

Holds NO assertions — tests assert. Every navigation is ANONYMOUS
(`BasePage.open_anonymous()`), never `open()`: an authenticated Liferay
session renders the admin control menu above the page and changes the
layout the UI/compatibility cases measure, and standards.md's
"Draft/Unpublish Public-Visibility Checks — Mandatory Logged-Out Context"
rule applies to every public-visibility read in this batch.

Shared component objects are COMPOSED, not re-declared:
  * `HeaderComponent`  — header/nav landmark and the accessibility-tools
    trigger button (`self.header`).
  * `AccessibilityToolsComponent` — the Dark Mode and High Contrast
    switches and their `<html>`-level signals (`self.accessibility`), used
    by the theme/contrast compatibility cases instead of re-implementing
    theme handling here.

RE-POINTED AT THE DELIVERED BUILD — 2026-09-28
------------------------------------------------------------------------
This Page Object was first written on 2026-09-23 against an EARLIER,
INCOMPLETE build of the FAQ fragment, and a 2026-09-27 batch then rewrote
case expectations to match that incomplete build under a "design drift"
ruling. **qcdev now serves the finished build, and it implements the
approved design.** Everything below was re-harvested live on 2026-09-28 and
the dead selectors for the old markup have been DELETED rather than kept as
build-tolerant unions: the old forms are definitively gone, so the object
documents one truth.

What changed under us (old build -> delivered build):
    h1 "Frequently Asked Questions"        -> "How can we help?"
    p.qc-faq-hero-subtitle                 -> p.qc-faq-hero-sub
    div.qc-faq-search + live-as-you-type   -> form.qc-faq-searchbar with a
                                              real button[data-qc-faq-search-btn]
    button.qc-faq-search-clear             -> (removed)
    span.qc-faq-crumb-sep ("/" text)       -> svg.qc-faq-crumb-sep (chevron)
    a.qc-faq-crumb[data-qc-faq-home-link]  -> a.qc-faq-crumb[data-qc-faq-home]
    (no eyebrow)                           -> p.qc-faq-eyebrow "Browse by topic"
    (no h2)                                -> h2.qc-faq-heading
    div.qc-faq-chips role=tablist          -> select.qc-faq-cat[data-qc-faq-cat]
    nav[data-qc-faq-pagination] + page btns-> button.qc-faq-more (Load More)
    span.qc-faq-page-info "Showing 1-5 of 8" -> p.qc-faq-count
                                              "Showing 1-6 of 8 questions"
    p[data-qc-faq-empty]                   -> p.qc-faq-state
    span.qc-faq-q-cat / -q-text / -q-icon  -> span.qc-faq-q-label +
                                              span.qc-faq-q-chip
    div.qc-faq-a-inner                     -> div.qc-faq-rt
    pageSize 5                             -> 6 (data-qc-faq-page-size="6")

TOOLING DISCLOSURE (CLI extraction only, qcdev, READ-ONLY, 2026-09-28)
------------------------------------------------------------------------
Harvested with `tools/extract_locators.py` plus scoped Playwright probe
scripts run in the SHELL at the framework's default 1920x1080 viewport.
**The Playwright MCP was available this session and was NOT used at all.**
Nothing in this batch created, edited, published, unpublished or deleted any
CMS content.

Delivered structure (EN, 2026-09-28):

    section.qc-faq[data-qc-faq-api][data-qc-faq-home-url][data-qc-faq-page-size="6"]
      header.qc-faq-hero                          (maroon gradient hero)
        div.qc-faq-shell.qc-faq-hero-shell
          nav.qc-faq-crumbs[data-qc-faq-crumbs-nav][aria-label="Breadcrumb"]
            a.qc-faq-crumb[data-qc-faq-home][href=/web/qatar-chamber]
              svg.qc-faq-crumb-ico + span[data-qc-faq-home-label] "Home"
            svg.qc-faq-crumb-sep                  (chevron-right ICON)
            span.qc-faq-crumb-current[data-qc-faq-crumb-current][aria-current=page] "FAQs"
          div.qc-faq-hero-copy
            h1.qc-faq-hero-title[data-qc-faq-title] "How can we help?"
            p.qc-faq-hero-sub[data-qc-faq-sub]     (648px, rgba(255,255,255,0.7))
          form.qc-faq-searchbar[data-qc-faq-form][role=search]
            span.qc-faq-search-field > svg.qc-faq-search-ico
                                     + input.qc-faq-search-input[data-qc-faq-search]
            button.qc-faq-search-btn[type=submit][data-qc-faq-search-btn] "Search"
      div.qc-faq-body > div.qc-faq-shell
        div.qc-faq-head
          div.qc-faq-head-copy
            p.qc-faq-eyebrow[data-qc-faq-eyebrow] "Browse by topic"
            h2.qc-faq-heading[data-qc-faq-heading] "Frequently asked questions"
          span.qc-faq-cat-wrap
            select.qc-faq-cat[data-qc-faq-cat][aria-label="Select Category"]
            svg.qc-faq-cat-caret                  (chevron-DOWN icon)
        div.qc-faq-results
          p.qc-faq-count[data-qc-faq-count]       "Showing 1-6 of 8 questions"
          div.qc-faq-list[data-qc-faq-list]
            div.qc-faq-item
              button.qc-faq-q[aria-expanded][id]
                span.qc-faq-q-label + span.qc-faq-q-chip   (icon, right-aligned)
              div.qc-faq-a[role=region][hidden] > div.qc-faq-rt
          p.qc-faq-state[data-qc-faq-state][hidden]
          button.qc-faq-more[data-qc-faq-more] > svg.qc-faq-more-ico
                                               + span[data-qc-faq-more-label] "Load More"

Behaviour measured live on the delivered build (not inferred):
  * `pageSize` is 6, read off `section.qc-faq[data-qc-faq-page-size]`.
  * Search executes ONLY on submit — typing alone changes nothing (measured:
    typing "membership" and waiting 1.5s left all 8 entries rendered; clicking
    Search narrowed it to 4). `search()` therefore types AND submits.
  * "Load More" APPENDS the next page in place (6 -> 8 entries) and the
    button gains `hidden` once every entry is shown. There is no numbered
    pagination on this build.
  * Two near-simultaneous Load More clicks append the remaining entries ONCE
    (measured: 8 unique items, count "Showing 1-8 of 8 questions").
  * The count line `p.qc-faq-count` is ALWAYS rendered for a non-empty
    result set, including a single-page filtered set (measured: the
    "Membership" filter shows "Showing 1-3 of 3 questions"). On a zero-result
    search the fragment empties its text and it collapses to zero height —
    so `results_count_text()` keeps a text/visibility guard and returns
    `None` there rather than a stale or blank string.
  * The category `<select>` offers a placeholder "Select Category" (value
    "") plus "All Categories" (value "all") and then one option per category
    that HAS published entries. Both "Select Category" and "All Categories"
    show the unfiltered list; "Select Category" is the case's default/clear
    option.
  * Zero-results copy: "No FAQs are available in this category yet." for an
    empty category; "No results found for your search." for a search.
  * Content source is the anonymous JAX-RS module `GET /o/qc-faq/faqs`.

NO PER-ITEM CATEGORY BADGE ON THIS BUILD
-----------------------------------------
The old markup exposed each entry's category as `span.qc-faq-q-cat`, and the
filtering tests used it as an INDEPENDENT source to prove a filter really
filtered. The delivered item renders only a question label and an icon; the
category lives server-side (option values are `QCDEMO-131052-FAQCAT-*`).
`question_category_badges()` is therefore GONE rather than returning a
misleading `[]`. The filtering proof moved to a pair of observations that
are still independent of each other: the filtered question set is a
non-empty STRICT SUBSET of the unfiltered set, and the count line's own
stated total agrees with the number of rendered rows.

Live content at the time of writing: **8 published entries**, page size 6,
categories Membership / Services / General. The approved cases describe 12
entries across General / Membership / Events / Exhibitions plus a "What is
Made in Qatar Expo?" entry — that is a stale CONTENT inventory (not design),
and the tests read those quantities live; see the test module's docstring.
"""

from core.web.base_page import BasePage
from config.settings import web_url
from web.pages.components.accessibility_tools_component import (
    AccessibilityToolsComponent,
)
from web.pages.components.header_component import HeaderComponent

# ── Site paths (joined onto WEB_BASE_URL via config.settings.web_url) ─────
FAQ_PATH = "/web/qatar-chamber/faq"
HOME_PATH_MARKER = "/web/qatar-chamber"

# Viewports the compatibility cases name, by their own case wording. These
# are CASE DATA, not a shared breakpoint table: PBI 131054's cases name a
# 375x812 mobile viewport while PBI 131052's name 375x667, so the two PBIs'
# tuples deliberately live with their own cases rather than being hoisted
# into one shared constant that would silently change a case's stated size.
DESKTOP_VIEWPORT = (1920, 1080)
TABLET_VIEWPORT = (768, 1024)
MOBILE_VIEWPORT = (375, 667)

# The fragment's configured page size, read off its own root attribute
# (`section.qc-faq[data-qc-faq-page-size="6"]`). Named so a test that reasons
# about "how many items should the first page hold" does not carry a bare 6.
# The delivered value now AGREES with the approved cases' "6 shown initially".
FRAGMENT_PAGE_SIZE = 6


class FaqPage(BasePage):
    """Query + drive surface for the public FAQ Knowledge Base page."""

    # ── Section root ────────────────────────────────────────────────────
    SECTION = "section.qc-faq"

    # ── Hero ────────────────────────────────────────────────────────────
    HERO = "header.qc-faq-hero"
    HERO_TITLE = "h1.qc-faq-hero-title[data-qc-faq-title]"
    HERO_SUBTITLE = "p.qc-faq-hero-sub[data-qc-faq-sub]"

    # ── Breadcrumb ──────────────────────────────────────────────────────
    BREADCRUMB = "nav.qc-faq-crumbs[data-qc-faq-crumbs-nav]"
    BREADCRUMB_HOME_LINK = "a.qc-faq-crumb[data-qc-faq-home]"
    # The case names a chevron-right ICON between the crumbs. The delivered
    # build renders it as a real inline `<svg>` sibling of the two crumbs.
    BREADCRUMB_SEPARATOR = f"{BREADCRUMB} svg.qc-faq-crumb-sep"
    BREADCRUMB_CURRENT = "span.qc-faq-crumb-current[data-qc-faq-crumb-current]"

    # ── Search ──────────────────────────────────────────────────────────
    # The pill the case styles (border-radius 9999px, the 1px #EDEDED
    # hairline and the 0 20px 40px rgba(29,29,27,.1) drop shadow) is the FORM
    # itself — `span.qc-faq-search-field` inside it carries neither.
    SEARCH_WRAPPER = "form.qc-faq-searchbar[data-qc-faq-form]"
    SEARCH_INPUT = "input[data-qc-faq-search]"
    SEARCH_ICON = f"{SEARCH_WRAPPER} svg.qc-faq-search-ico"
    # ONE Search control: the case's maroon submit button, which is also the
    # control that actually executes the query. Located by the fragment's own
    # hook attribute so it is locale-independent (AR renders "ابحث").
    SEARCH_SUBMIT_BUTTON = "button[data-qc-faq-search-btn]"

    # ── Category filter (the case's "Select Category" dropdown) ─────────
    CATEGORY_SELECT = "select[data-qc-faq-cat]"
    CATEGORY_CARET_ICON = "span.qc-faq-cat-wrap svg.qc-faq-cat-caret"

    # ── Content-section header ──────────────────────────────────────────
    SECTION_HEAD = "div.qc-faq-head"
    EYEBROW_LABEL = "p.qc-faq-eyebrow[data-qc-faq-eyebrow]"
    SECTION_H2 = "h2.qc-faq-heading[data-qc-faq-heading]"

    # ── Results count ───────────────────────────────────────────────────
    RESULTS_COUNT = "p.qc-faq-count[data-qc-faq-count]"

    # ── Accordion list ──────────────────────────────────────────────────
    FAQ_LIST = "div.qc-faq-list[data-qc-faq-list]"
    FAQ_ITEM = "div.qc-faq-item"
    FAQ_QUESTION_BUTTON = "button.qc-faq-q"
    FAQ_QUESTION_LABEL = "span.qc-faq-q-label"
    FAQ_QUESTION_ICON = "span.qc-faq-q-chip"
    FAQ_ANSWER = "div.qc-faq-a"
    FAQ_ANSWER_INNER = "div.qc-faq-rt"

    # ── Zero-results state ──────────────────────────────────────────────
    EMPTY_MESSAGE = "p[data-qc-faq-state]"

    # ── "Load More" ─────────────────────────────────────────────────────
    # By the fragment's own hook, never by the "Load More" label, so the same
    # constant drives the Arabic page ("تحميل المزيد"). The LABEL is read
    # separately through `load_more_label()` for the copy assertions.
    LOAD_MORE_BUTTON = "button[data-qc-faq-more]"
    LOAD_MORE_LABEL = "span[data-qc-faq-more-label]"
    LOAD_MORE_ICON = f"{LOAD_MORE_BUTTON} svg"

    # ── Expected-copy constants the CASES name (asserted verbatim) ──────
    # Kept here so the tests read as intent and the exact strings live in one
    # place. As of the delivered build these are also what the site renders.
    CASE_HERO_HEADING = "How can we help?"
    CASE_HERO_SUBTEXT = (
        "Find services, events, publications, and information across the website."
    )
    CASE_EYEBROW_TEXT = "Browse by topic"
    CASE_SECTION_HEADING = "Frequently asked questions"
    # The dropdown's default/clear option, per #141651/#141675/#141676/#141678.
    CASE_CATEGORY_DEFAULT_LABEL = "Select Category"
    CASE_CATEGORY_DROPDOWN_LABEL = "Select Category"
    CASE_LOAD_MORE_LABEL = "Load More"
    CASE_SEARCH_BUTTON_LABEL = "Search"

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)
        self.accessibility = AccessibilityToolsComponent(page)
        self._console_messages = []
        self._dialog_messages = []

    # ── Navigation (always anonymous — see module docstring) ────────────
    def open_faq(self, locale: str = "en") -> "FaqPage":
        """Load the FAQ Knowledge Base page and wait for the fragment to
        finish its first client-side render.

        The list is painted from `GET /o/qc-faq/faqs`, so `networkidle` alone
        is not enough — the wait below is on the fragment's own rendered
        outcome (a question button exists, or the empty state is showing),
        never a timed sleep."""
        self.open_anonymous(web_url(FAQ_PATH, locale=locale))
        self.wait_for(self.SECTION, first=True)
        self.wait_for_first_render()
        return self

    def wait_for_first_render(self, timeout: int = 15000) -> None:
        """Condition-based wait for the fragment's initial render: either at
        least one accordion item exists, or the empty-state paragraph is
        visible. Bounded; never a `sleep`."""
        self.wait_for_condition(
            """() => {
                const root = document.querySelector('section.qc-faq');
                if (!root) return false;
                if (root.querySelectorAll('div.qc-faq-item').length > 0) return true;
                const empty = root.querySelector('[data-qc-faq-state]');
                return !!empty && !empty.hidden;
            }""",
            timeout=timeout,
        )

    def current_url(self) -> str:
        return self.page.url

    def configured_page_size(self) -> int | None:
        """The fragment's own `data-qc-faq-page-size`, so a test can compare
        the rendered first page against the product's configuration rather
        than against a number copied into the suite."""
        raw = self.get_attribute(self.SECTION, "data-qc-faq-page-size")
        try:
            return int(raw)
        except (TypeError, ValueError):
            return None

    # ── Generic document state ──────────────────────────────────────────
    def document_direction(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('dir') "
            "|| getComputedStyle(document.body).direction"
        )

    def document_language(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('lang') || ''"
        )

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).first.evaluate(
            "el => getComputedStyle(el).direction"
        )

    def has_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > "
            "document.documentElement.clientWidth"
        )

    def viewport_size(self) -> dict:
        return self.page.evaluate(
            "() => ({width: window.innerWidth, height: window.innerHeight})"
        )

    # ── Generic style / geometry readers ────────────────────────────────
    def computed_style(self, locator: str, properties: tuple) -> dict:
        """Computed values of `properties` on the FIRST match of `locator`.

        Returns `{}` when nothing matches, so a test asserting on a control
        this build does not render gets an empty dict and its own presence
        assertion fires first — instead of this reader raising."""
        target = self.page.locator(locator).first
        if target.count() == 0:
            return {}
        return target.evaluate(
            "(el, props) => { const cs = getComputedStyle(el); const out = {};"
            " for (const p of props) out[p] = cs[p]; return out; }",
            list(properties),
        )

    def bounding_box(self, locator: str) -> dict | None:
        target = self.page.locator(locator).first
        if target.count() == 0:
            return None
        return target.bounding_box()

    # Walk up from a text node to whatever actually PAINTS behind it, and
    # report every colour that paint can be, not just one.
    #
    # HELPER BUG FIX 2026-09-28 (ADO-141659, ADO-141657) — KEPT AND RE-VERIFIED
    # against the delivered build on 2026-09-28: the FAQ hero still paints
    # itself with a `linear-gradient` BACKGROUND-IMAGE and leaves
    # `background-color` at `rgba(0, 0, 0, 0)` (measured:
    # `radial-gradient(... rgba(196,154,98,.18), rgba(196,155,98,0) 55%),
    #  linear-gradient(164.77deg, rgb(70,7,30) 8.13%, rgb(96,20,48) 48.33%,
    #  rgb(145,23,49) 91.87%)`). A `backgroundColor`-only walk would fall
    # through the hero entirely and score its white heading and white
    # breadcrumb as "white on white — 1.00:1", a fabricated illegibility on a
    # hero that is plainly readable. A gradient is not one colour, so this
    # returns the LIST of opaque colour stops and the caller scores the WORST
    # of them — stricter than picking one stop, and never a guess. Translucent
    # stops (the hero's `rgba(196, 154, 98, 0.18)` sheen and its `alpha: 0`
    # end stop) are decoration over those opaque stops, not backgrounds in
    # their own right, so they are excluded rather than mistaken for a solid
    # beige.
    _BACKGROUND_CHAIN_JS = r"""el => {
      const opaqueStops = (image) => {
        const out = [];
        if (!image || image === 'none') return out;
        const re = /rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*(?:,\s*([0-9.]+)\s*)?\)/g;
        let m;
        while ((m = re.exec(image)) !== null) {
          const alpha = m[4] === undefined ? 1 : parseFloat(m[4]);
          if (alpha === 1) out.push('rgb(' + m[1] + ', ' + m[2] + ', ' + m[3] + ')');
        }
        return out;
      };
      let n = el;
      while (n) {
        const cs = getComputedStyle(n);
        const bg = cs.backgroundColor;
        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return [bg];
        const stops = opaqueStops(cs.backgroundImage);
        if (stops.length) return stops;
        n = n.parentElement;
      }
      return ['rgb(255, 255, 255)'];
    }"""

    def effective_background_colors(self, locator: str) -> list:
        """Every colour the first PAINTING ancestor can put behind this text
        — one entry for a solid background, one per opaque stop for a
        gradient. `[]` when the element does not exist."""
        target = self.page.locator(locator).first
        if target.count() == 0:
            return []
        return target.evaluate(self._BACKGROUND_CHAIN_JS)

    def effective_background_color(self, locator: str) -> str | None:
        """The single most representative painted background behind the
        element (the first entry of `effective_background_colors`), for the
        readers that want one colour rather than a gradient's whole set."""
        colours = self.effective_background_colors(locator)
        return colours[0] if colours else None

    def element_count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    # ── Hero ────────────────────────────────────────────────────────────
    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_title_style(self) -> dict:
        return self.computed_style(
            self.HERO_TITLE,
            ("fontSize", "fontWeight", "fontFamily", "color", "textAlign"),
        )

    def hero_background(self) -> dict:
        return self.computed_style(
            self.HERO, ("backgroundColor", "backgroundImage")
        )

    def hero_subtitle_text(self) -> str:
        return self.text(self.HERO_SUBTITLE).strip()

    def hero_subtitle_style(self) -> dict:
        return self.computed_style(
            self.HERO_SUBTITLE,
            ("fontSize", "fontWeight", "fontFamily", "color", "width"),
        )

    def is_hero_above_search(self) -> bool:
        """True when the hero block is rendered above the search bar in the
        document's visual order (the cases' "hero renders above the search
        bar" precondition). On the delivered build the search bar sits INSIDE
        the hero, which still satisfies "above" — the hero starts first."""
        return self.page.evaluate(
            """() => { const hero = document.querySelector('header.qc-faq-hero');
                const search = document.querySelector('form.qc-faq-searchbar');
                if (!hero || !search) return false;
                return hero.getBoundingClientRect().top <
                       search.getBoundingClientRect().top; }"""
        )

    # ── Breadcrumb ──────────────────────────────────────────────────────
    def breadcrumb_home_text(self) -> str:
        return self.text(self.BREADCRUMB_HOME_LINK).strip()

    def breadcrumb_home_href(self) -> str | None:
        return self.get_attribute(self.BREADCRUMB_HOME_LINK, "href")

    def breadcrumb_separator_icon_count(self) -> int:
        """How many separator ICON nodes the breadcrumb renders between the
        crumbs — the cases expect a chevron-right icon, so a text-only
        separator would report 0. Counts real `<svg>`/`<i>`/`<img>` nodes and
        a CSS background/::before image on the delivered separator element."""
        return self.page.evaluate(
            """() => { const nav = document.querySelector(
                    'nav.qc-faq-crumbs[data-qc-faq-crumbs-nav]');
                if (!nav) return 0;
                const seps = [...nav.children].filter(
                    (el) => el.classList.contains('qc-faq-crumb-sep'));
                let n = 0;
                for (const sep of seps) {
                    const tag = sep.tagName.toLowerCase();
                    if (['svg', 'i', 'img'].includes(tag)) { n += 1; continue; }
                    n += sep.querySelectorAll('svg, i, img, use').length;
                    const cs = getComputedStyle(sep);
                    if (cs.backgroundImage && cs.backgroundImage !== 'none') n += 1;
                    const before = getComputedStyle(sep, '::before');
                    if (before.backgroundImage
                        && before.backgroundImage !== 'none') n += 1;
                }
                return n; }"""
        )

    def breadcrumb_separator_box(self) -> dict | None:
        return self.bounding_box(self.BREADCRUMB_SEPARATOR)

    def breadcrumb_current_text(self) -> str:
        return self.text(self.BREADCRUMB_CURRENT).strip()

    def breadcrumb_current_is_link(self) -> bool:
        return self.page.evaluate(
            """() => { const cur = document.querySelector(
                    '[data-qc-faq-crumb-current]');
                return !!cur && (cur.tagName.toLowerCase() === 'a'
                        || !!cur.closest('a')); }"""
        )

    def breadcrumb_style(self) -> dict:
        return self.computed_style(
            self.BREADCRUMB_HOME_LINK, ("fontSize", "fontWeight", "color")
        )

    def click_breadcrumb_home(self) -> None:
        # AUTOMATION BUG FIX 2026-09-27 (ADO-141684) — KEPT: this used to be
        # `click()` + `wait_for_load_state("domcontentloaded")`. click()
        # resolves on DISPATCH and wait_for_load_state returns immediately
        # while the ORIGIN document is still current, so the test's
        # current_url() read came back as the FAQ URL and the navigation
        # assertion failed on timing rather than on behaviour.
        # base_page.wait_for_url() is the framework's helper for this hazard.
        self.click(self.BREADCRUMB_HOME_LINK)
        self.wait_for_url(lambda url: "/faq" not in url)

    # ── Search ──────────────────────────────────────────────────────────
    def search_wrapper_style(self) -> dict:
        return self.computed_style(
            self.SEARCH_WRAPPER,
            (
                "borderRadius",
                "borderTopWidth",
                "borderTopStyle",
                "borderTopColor",
                "boxShadow",
                "backgroundColor",
            ),
        )

    def search_input_value(self) -> str:
        return self.page.locator(self.SEARCH_INPUT).first.input_value()

    def search_input_placeholder(self) -> str | None:
        return self.get_attribute(self.SEARCH_INPUT, "placeholder")

    def type_search_term(self, term: str) -> "FaqPage":
        """Type into the search field WITHOUT submitting — for the cases that
        assert the typed value is accepted before the query is executed
        (#141677 explicitly requires that typing alone does not filter)."""
        self.type(self.SEARCH_INPUT, term)
        return self

    def search(self, term: str) -> "FaqPage":
        """Enter `term` and submit it through the delivered Search button,
        then wait for the fragment's own filtered render.

        AUTOMATION BUG FIX 2026-09-28 (ADO-141688) — KEPT AND RE-VERIFIED on
        the delivered build: typing alone never executes the query (measured
        2026-09-28: typing "membership" and waiting 1.5s left all 8 entries
        rendered and the count line untouched at "Showing 1-8 of 8 questions";
        clicking the button narrowed it to 4). An earlier version of this
        method typed and nothing else, so every caller died on a bare
        `TimeoutError` waiting for a filtered list the page was never going to
        produce. The wait was correct; the ACTION was incomplete.

        The old build's "no submit control" tolerance is GONE: this build
        always renders `button[data-qc-faq-search-btn]`, so the submit is
        unconditional and a missing button is a real failure, not a branch."""
        self.type_search_term(term)
        self.click(self.SEARCH_SUBMIT_BUTTON)
        self.wait_for_search_settled(term)
        return self

    def wait_for_search_settled(self, term: str, timeout: int = 10000) -> None:
        """Condition-based wait on the product's OWN rendered outcome after a
        submit: the field holds `term`, and either every rendered item's text
        contains it (the fragment filters on the stripped question + answer,
        both of which are inside the item's own DOM) or the zero-results
        paragraph is showing. No `sleep`, and no debounce constant copied out
        of the fragment."""
        self.page.wait_for_function(
            """(term) => {
                const root = document.querySelector('section.qc-faq');
                if (!root) return false;
                const input = root.querySelector('[data-qc-faq-search]');
                if (!input || input.value !== term) return false;
                const needle = term.trim().toLowerCase();
                if (!needle) return true;
                const items = [...root.querySelectorAll('div.qc-faq-item')];
                const empty = root.querySelector('[data-qc-faq-state]');
                if (items.length === 0) return !!empty && !empty.hidden;
                return items.every(
                    (i) => (i.textContent || '').toLowerCase().indexOf(needle) !== -1);
            }""",
            arg=term,
            timeout=timeout,
        )

    def search_submit_button_count(self) -> int:
        """Matches for the Search submit button inside the FAQ hero — the
        control cases #141647/#141677 describe."""
        return self.element_count(self.SEARCH_SUBMIT_BUTTON)

    def search_submit_button_label(self) -> str:
        if self.search_submit_button_count() == 0:
            return ""
        return self.text(self.SEARCH_SUBMIT_BUTTON).strip()

    def search_submit_button_style(self) -> dict:
        return self.computed_style(
            self.SEARCH_SUBMIT_BUTTON,
            ("backgroundColor", "color", "fontSize", "fontWeight", "borderRadius"),
        )

    def click_search_button(self) -> "FaqPage":
        """Click the FAQ section's Search submit button without typing first
        — for #141677, which types through `type_search_term()` and then
        submits as a separate, asserted step."""
        self.click(self.SEARCH_SUBMIT_BUTTON)
        return self

    def search_wrapper_box(self) -> dict | None:
        return self.bounding_box(self.SEARCH_WRAPPER)

    def search_submit_button_box(self) -> dict | None:
        return self.bounding_box(self.SEARCH_SUBMIT_BUTTON)

    def hero_title_box(self) -> dict | None:
        return self.bounding_box(self.HERO_TITLE)

    def hero_subtitle_box(self) -> dict | None:
        return self.bounding_box(self.HERO_SUBTITLE)

    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def is_search_inside_form(self) -> bool:
        return self.page.evaluate(
            "() => !!document.querySelector('[data-qc-faq-search]')?.closest('form')"
        )

    # ── Category filter (the delivered "Select Category" <select>) ──────
    def category_select_count(self) -> int:
        """Matches for the `<select>` category dropdown the cases describe
        (#141651, #141675-#141679, #141686)."""
        return self.element_count(self.CATEGORY_SELECT)

    def category_labels(self) -> list:
        """Every option label the dropdown offers, in document order."""
        if self.category_select_count() == 0:
            return []
        return self.page.locator(self.CATEGORY_SELECT).first.evaluate(
            "el => [...el.options].map(o => (o.text || '').trim())"
        )

    # Kept as an alias so the option-list cases read in their own vocabulary.
    def category_select_option_labels(self) -> list:
        return self.category_labels()

    def selected_category_label(self) -> str | None:
        if self.category_select_count() == 0:
            return None
        return self.page.locator(self.CATEGORY_SELECT).first.evaluate(
            "el => ((el.selectedOptions[0] || {}).text || '').trim()"
        )

    def category_select_default_label(self) -> str | None:
        return self.selected_category_label()

    def category_select_style(self) -> dict:
        return self.computed_style(
            self.CATEGORY_SELECT,
            (
                "borderRadius",
                "borderTopWidth",
                "borderTopStyle",
                "borderTopColor",
                "boxShadow",
                "backgroundColor",
                "color",
            ),
        )

    def category_caret_icon_count(self) -> int:
        """Chevron-down icon nodes rendered with the dropdown (#141651)."""
        return self.element_count(self.CATEGORY_CARET_ICON)

    def select_category(self, label: str) -> "FaqPage":
        """Choose the dropdown option whose label is exactly `label`, then
        wait for the fragment's own re-render (its `change` handler re-renders
        the list; the wait is on the product's rendered state, not a timer)."""
        self.select_option(self.CATEGORY_SELECT, label=label)
        self.page.wait_for_function(
            """(label) => {
                const sel = document.querySelector('select[data-qc-faq-cat]');
                if (!sel) return false;
                const chosen = ((sel.selectedOptions[0] || {}).text || '').trim();
                if (chosen !== label) return false;
                const root = document.querySelector('section.qc-faq');
                if (!root) return false;
                if (root.querySelectorAll('div.qc-faq-item').length > 0) return true;
                const empty = root.querySelector('[data-qc-faq-state]');
                return !!empty && !empty.hidden;
            }""",
            arg=label,
        )
        return self

    # ── Eyebrow / section heading ───────────────────────────────────────
    def eyebrow_label_count(self) -> int:
        return self.element_count(self.EYEBROW_LABEL)

    def eyebrow_label_text(self) -> str:
        if self.eyebrow_label_count() == 0:
            return ""
        return self.text(self.EYEBROW_LABEL).strip()

    def eyebrow_label_style(self) -> dict:
        return self.computed_style(
            self.EYEBROW_LABEL, ("fontSize", "fontWeight", "color")
        )

    def section_h2_texts(self) -> list:
        return [
            (text or "").strip()
            for text in self.page.locator(self.SECTION_H2).all_inner_texts()
        ]

    def section_h2_style(self) -> dict:
        return self.computed_style(
            self.SECTION_H2, ("fontSize", "fontWeight", "color")
        )

    def eyebrow_box(self) -> dict | None:
        return self.bounding_box(self.EYEBROW_LABEL)

    def section_h2_box(self) -> dict | None:
        return self.bounding_box(self.SECTION_H2)

    # ── Results count ───────────────────────────────────────────────────
    def results_count_text(self) -> str | None:
        """The "Showing A–B of N questions" line, or `None` when the fragment
        is not actually SHOWING one.

        READER GUARD KEPT (and re-verified 2026-09-28): the delivered build
        renders the count line for every non-empty result set, INCLUDING a
        single-page filtered set (measured: the "Membership" filter shows
        "Showing 1–3 of 3 questions"). On a zero-result search it empties the
        paragraph's text and the element collapses to zero height rather than
        being removed, so a naive `inner_text()` read would return `''` — or,
        on the old build, last render's stale numbers. Text and visibility are
        therefore both part of the read. The old build's pagination-nav
        coupling is gone: this build has no pagination nav."""
        if self.element_count(self.RESULTS_COUNT) == 0:
            return None
        target = self.page.locator(self.RESULTS_COUNT).first
        text = target.evaluate("el => (el.textContent || '').trim()")
        if not text:
            return None
        if not target.is_visible():
            return None
        return text

    def results_count_style(self) -> dict:
        return self.computed_style(
            self.RESULTS_COUNT, ("fontSize", "fontWeight", "color")
        )

    # ── Accordion list ──────────────────────────────────────────────────
    def item_count(self) -> int:
        return self.element_count(self.FAQ_ITEM)

    def question_labels(self) -> list:
        return [
            (text or "").strip()
            for text in self.page.locator(
                f"{self.FAQ_ITEM} >> {self.FAQ_QUESTION_LABEL}"
            ).all_inner_texts()
        ]

    def question_label_style(self, index: int = 0) -> dict:
        return self.computed_style(
            f"{self.FAQ_ITEM} >> nth={index} >> {self.FAQ_QUESTION_LABEL}",
            ("fontSize", "fontWeight", "fontFamily", "color"),
        )

    def question_button_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(
            f"{self.FAQ_ITEM} >> nth={index} >> {self.FAQ_QUESTION_BUTTON}"
        )

    def question_label_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(
            f"{self.FAQ_ITEM} >> nth={index} >> {self.FAQ_QUESTION_LABEL}"
        )

    def question_icon_box(self, index: int = 0) -> dict | None:
        return self.bounding_box(
            f"{self.FAQ_ITEM} >> nth={index} >> {self.FAQ_QUESTION_ICON}"
        )

    def expanded_states(self) -> list:
        """`aria-expanded` of every accordion header, in document order."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('button.qc-faq-q')]
                .map((b) => b.getAttribute('aria-expanded'))"""
        )

    def is_item_expanded(self, index: int = 0) -> bool:
        states = self.expanded_states()
        return index < len(states) and states[index] == "true"

    def toggle_item(self, index: int = 0) -> "FaqPage":
        """Click an accordion header and wait for the fragment's own
        `aria-expanded` flip (its handler toggles synchronously; the wait is
        on the product's state, not a timer)."""
        before = self.expanded_states()
        expected = "false" if (index < len(before) and before[index] == "true") else "true"
        self.click(f"{self.FAQ_ITEM} >> nth={index} >> {self.FAQ_QUESTION_BUTTON}")
        self.page.wait_for_function(
            """([index, expected]) => {
                const buttons = [...document.querySelectorAll('button.qc-faq-q')];
                return !!buttons[index]
                    && buttons[index].getAttribute('aria-expanded') === expected;
            }""",
            arg=[index, expected],
        )
        return self

    def item_texts(self) -> list:
        """Each rendered entry's FULL text (question + answer), read with
        `textContent` so a collapsed answer still contributes — the fragment
        filters on exactly this text, so a search assertion has to read it the
        same way `inner_text` cannot (it returns '' when hidden)."""
        return [
            " ".join((text or "").split())
            for text in self.page.locator(self.FAQ_ITEM).all_text_contents()
        ]

    def answer_text(self, index: int = 0) -> str:
        return self.page.locator(
            f"{self.FAQ_ITEM} >> nth={index} >> {self.FAQ_ANSWER}"
        ).first.inner_text().strip()

    def is_answer_visible(self, index: int = 0) -> bool:
        return self.page.evaluate(
            """(index) => { const panels =
                    [...document.querySelectorAll('div.qc-faq-a')];
                const panel = panels[index];
                if (!panel) return false;
                if (panel.hasAttribute('hidden')) return false;
                return panel.getBoundingClientRect().height > 0; }""",
            index,
        )

    def answer_visibility_states(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll('div.qc-faq-a')].map(
                (p) => !p.hasAttribute('hidden')
                       && p.getBoundingClientRect().height > 0)"""
        )

    def item_boxes(self) -> list:
        """Bounding boxes of every rendered accordion item — the layout
        evidence a "does long content break the list?" check needs."""
        return self.page.evaluate(
            """() => [...document.querySelectorAll('div.qc-faq-item')].map((it) => {
                const r = it.getBoundingClientRect();
                return {x: Math.round(r.x), y: Math.round(r.y),
                        width: Math.round(r.width), height: Math.round(r.height)};
            })"""
        )

    def longest_question_length(self) -> int:
        labels = self.question_labels()
        return max((len(label) for label in labels), default=0)

    def longest_answer_length(self) -> int:
        lengths = self.page.evaluate(
            """() => [...document.querySelectorAll('div.qc-faq-a')].map(
                (p) => (p.textContent || '').trim().length)"""
        )
        return max(lengths, default=0)

    # ── Zero-results state ──────────────────────────────────────────────
    def is_empty_message_visible(self) -> bool:
        return self.page.evaluate(
            """() => { const empty = document.querySelector('[data-qc-faq-state]');
                return !!empty && !empty.hidden
                    && (empty.textContent || '').trim().length > 0; }"""
        )

    def empty_message_text(self) -> str:
        if self.element_count(self.EMPTY_MESSAGE) == 0:
            return ""
        return self.page.locator(self.EMPTY_MESSAGE).first.evaluate(
            "el => (el.textContent || '').trim()"
        )

    # ── "Load More" ─────────────────────────────────────────────────────
    def load_more_button_count(self) -> int:
        return self.element_count(self.LOAD_MORE_BUTTON)

    def load_more_label(self) -> str:
        """The button's own visible label, read off its dedicated
        `data-qc-faq-more-label` span so the copy assertions never have to
        strip the icon out of the button's text."""
        if self.element_count(self.LOAD_MORE_LABEL) == 0:
            return ""
        return self.text(self.LOAD_MORE_LABEL).strip()

    def load_more_button_style(self) -> dict:
        return self.computed_style(
            self.LOAD_MORE_BUTTON,
            (
                "borderRadius",
                "borderTopWidth",
                "borderTopStyle",
                "borderTopColor",
                "boxShadow",
                "color",
                "fontSize",
                "fontWeight",
            ),
        )

    def is_load_more_visible(self) -> bool:
        return self.page.evaluate(
            """() => { const b = document.querySelector('[data-qc-faq-more]');
                return !!b && !b.hasAttribute('hidden')
                    && b.getBoundingClientRect().height > 0; }"""
        )

    def is_load_more_enabled(self) -> bool:
        return self.page.evaluate(
            """() => { const b = document.querySelector('[data-qc-faq-more]');
                return !!b && !b.disabled; }"""
        )

    def load_more_icon_count(self) -> int:
        """Icon nodes rendered inside the Load More button (the case names a
        left `refresh-cw-03` icon)."""
        return self.element_count(self.LOAD_MORE_ICON)

    def load_more_icon_box(self) -> dict | None:
        return self.bounding_box(self.LOAD_MORE_ICON)

    def load_more_label_box(self) -> dict | None:
        return self.bounding_box(self.LOAD_MORE_LABEL)

    def load_more_button_box(self) -> dict | None:
        return self.bounding_box(self.LOAD_MORE_BUTTON)

    def click_load_more(self) -> "FaqPage":
        """Click Load More and wait for the fragment's own append to land —
        either more rows are rendered than before, or the button has retired
        itself. Never a timer."""
        before = self.item_count()
        self.click(self.LOAD_MORE_BUTTON)
        self._wait_for_load_more_settled(before)
        return self

    def load_all_entries(self, max_clicks: int = 20) -> "FaqPage":
        """Click Load More until it retires itself, so the caller holds the
        WHOLE current result set rather than just the first page.

        Bounded by `max_clicks` so a product bug that never retires the button
        stops the test instead of hanging it. Each click waits on the
        fragment's own rendered outcome, never a timer.

        The bound raises `RuntimeError`, not `AssertionError`: this is a hang
        guard belonging to the driver, and a Page Object must never contribute
        an assertion to a test's verdict (standards.md)."""
        clicks = 0
        while self.is_load_more_visible() and self.is_load_more_enabled():
            if clicks >= max_clicks:
                raise RuntimeError(
                    f"'Load More' was still offering entries after "
                    f"{max_clicks} clicks ({self.item_count()} rows rendered) "
                    f"— it never retired itself"
                )
            self.click_load_more()
            clicks += 1
        return self

    def double_click_load_more(self) -> "FaqPage":
        """Two near-simultaneous clicks on Load More (#141687's edge case).
        Goes through the wrapper's own locator so no test touches raw
        Playwright."""
        before = self.item_count()
        self.double_click(self.LOAD_MORE_BUTTON)
        self._wait_for_load_more_settled(before)
        return self

    def _wait_for_load_more_settled(self, before: int, timeout: int = 10000) -> None:
        self.page.wait_for_function(
            """(before) => {
                const rows = document.querySelectorAll('div.qc-faq-item').length;
                if (rows > before) return true;
                const b = document.querySelector('[data-qc-faq-more]');
                return !b || b.hasAttribute('hidden') || b.disabled;
            }""",
            arg=before,
            timeout=timeout,
        )

    # ── Theme / contrast (composed from AccessibilityToolsComponent) ────
    def current_theme(self) -> str | None:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('data-theme')"
        )

    def enable_dark_mode(self) -> "FaqPage":
        self.accessibility.enable_dark_mode()
        return self

    def enable_high_contrast(self) -> "FaqPage":
        """Open the accessibility panel, flip High Contrast on if it is not
        already on, wait for the product's own `<html class="qc-a11y-contrast">`
        signal, then close the panel. Mirrors
        `AccessibilityToolsComponent.enable_dark_mode()`'s idempotent shape
        and reuses that component's own locators/queries — nothing is
        re-declared here."""
        self.accessibility.click_accessibility_button()
        self.wait_for(self.accessibility.PANEL)
        if not self.accessibility.is_high_contrast_active():
            self.accessibility.activate_high_contrast()
        self.page.wait_for_function(
            "() => document.documentElement.classList.contains('qc-a11y-contrast')"
        )
        self.accessibility.close_panel()
        return self

    def is_high_contrast_active(self) -> bool:
        return self.accessibility.is_high_contrast_active()

    # ── Legibility sampling (theme / contrast cases) ────────────────────
    # Named text surfaces sampled across the hero + content section. Kept as
    # (name, locator) pairs so a failure names WHICH surface lost contrast.
    #
    # RE-POINTED 2026-09-28 at the delivered markup. The 2026-09-27 pass had
    # made several of these "build-tolerant" comma-unions covering both the
    # old and the new markup; the old halves are definitively gone, so each
    # entry is now the single real selector. Two entries are DROPPED, not
    # re-pointed, because the delivered item has no equivalent surface at all:
    #   * "category chip" — the role=tablist chips were replaced by a
    #     `<select>`, whose placeholder is an unadjudicated sub-4.5:1 surface
    #     (see below) and so must not silently take the chip's place;
    #   * "accordion category badge" — the delivered item renders only a
    #     question label and an icon; there is no per-item category text.
    # Eight real surfaces remain, comfortably over the floor of 5, and the
    # floor is NOT lowered — it exists so this check cannot hollow out.
    #
    # DELIBERATELY NOT SAMPLED, and why — reported to the QA Manager rather
    # than silently added or silently dropped. Each is a real delivered
    # surface that currently measures BELOW 4.5:1, i.e. adding it would turn
    # these tests red on what looks like a genuine WCAG 1.4.3 defect that has
    # no bug raised against it yet, and none of the three has been adjudicated:
    #   * the count line `p.qc-faq-count` and the "Browse by topic" eyebrow
    #     `p.qc-faq-eyebrow` — rgb(196, 69, 97) on rgb(29, 29, 27) = 3.51:1
    #     in DARK theme (both are fine in Light at 8.86:1);
    #   * the category `select.qc-faq-cat` placeholder — rgb(168, 168, 167)
    #     on white = 2.38:1 in LIGHT theme.
    # Add them the moment those are ruled on; the entries are one line each.
    CONTRAST_SAMPLE_TARGETS = (
        ("hero heading", HERO_TITLE),
        ("hero subtitle", HERO_SUBTITLE),
        ("breadcrumb Home link", BREADCRUMB_HOME_LINK),
        ("breadcrumb current crumb", BREADCRUMB_CURRENT),
        ("search input", SEARCH_INPUT),
        ("section heading", SECTION_H2),
        ("accordion question", f"{FAQ_ITEM} >> {FAQ_QUESTION_LABEL}"),
        ("accordion answer", f"{FAQ_ITEM} >> {FAQ_ANSWER_INNER}"),
    )

    def text_contrast_samples(self) -> list:
        """`[{name, color, background, backgrounds}]` for every named text
        surface that is currently rendered — the raw material for a
        legibility assertion. The test computes the WCAG ratio; this object
        only observes.

        `backgrounds` is every colour the painting ancestor can put behind
        the text (one entry for a solid fill, one per opaque stop for a
        gradient) so the test can score the WORST of them; `background` is
        the first of those, kept for the readers and messages that want a
        single colour."""
        samples = []
        for name, locator in self.CONTRAST_SAMPLE_TARGETS:
            if self.element_count(locator) == 0:
                continue
            style = self.computed_style(locator, ("color",))
            backgrounds = self.effective_background_colors(locator)
            samples.append(
                {
                    "name": name,
                    "color": style.get("color"),
                    "background": backgrounds[0] if backgrounds else None,
                    "backgrounds": backgrounds,
                }
            )
        return samples

    # ── Touch targets (responsive cases) ────────────────────────────────
    # The controls a visitor actually taps. The accordion's tap target is
    # the whole header BUTTON, not the 24px icon glyph inside it, so it is
    # the button that is measured.
    TOUCH_TARGET_SELECTORS = (
        ("search input", SEARCH_INPUT),
        ("Search button", SEARCH_SUBMIT_BUTTON),
        ("category dropdown", CATEGORY_SELECT),
        ("accordion header", f"{FAQ_ITEM} >> {FAQ_QUESTION_BUTTON}"),
        ("Load More button", LOAD_MORE_BUTTON),
    )

    def touch_target_boxes(self) -> list:
        """`[{name, width, height}]` for each tappable control that exists."""
        boxes = []
        for name, locator in self.TOUCH_TARGET_SELECTORS:
            box = self.bounding_box(locator)
            if box is None:
                continue
            boxes.append(
                {
                    "name": name,
                    "width": round(box["width"]),
                    "height": round(box["height"]),
                }
            )
        return boxes

    def elements_within_viewport(self) -> list:
        """`[{name, overflows, left, right, viewportWidth}]` — whether each
        key block spills outside the viewport horizontally (the layout cases'
        "no overflow" check).

        The content-section header is represented by its ROW
        (`div.qc-faq-head`), not by the `<select>` inside it: the dropdown is
        deliberately right-aligned within that row, so measuring the select
        would report a third "left edge" for a row that is in fact aligned to
        the same grid column as everything else."""
        return self.page.evaluate(
            """() => { const targets = {
                    'hero': 'header.qc-faq-hero',
                    'search bar': 'form.qc-faq-searchbar',
                    'section header': 'div.qc-faq-head',
                    'accordion list': 'div.qc-faq-list',
                    'load more': 'button[data-qc-faq-more]'};
                const width = document.documentElement.clientWidth;
                const out = [];
                for (const [name, sel] of Object.entries(targets)) {
                    const el = document.querySelector(sel);
                    if (!el) continue;
                    const r = el.getBoundingClientRect();
                    if (r.width === 0 && r.height === 0) continue;
                    out.push({name, overflows: r.left < -1 || r.right > width + 1,
                              left: Math.round(r.left), right: Math.round(r.right),
                              viewportWidth: width});
                }
                return out; }"""
        )

    # ── Console / dialog capture (security + no-JS-error cases) ─────────
    def start_console_capture(self) -> "FaqPage":
        """Record every console message from now on. Must be called BEFORE
        the navigation whose errors are being asserted on."""
        self._console_messages = []
        self.page.on("console", lambda msg: self._console_messages.append(msg))
        return self

    def console_error_texts(self) -> list:
        return [
            message.text
            for message in self._console_messages
            if message.type in ("error",)
        ]

    def start_dialog_capture(self) -> "FaqPage":
        """Record and auto-dismiss any native dialog (an `alert()` fired by a
        successful script injection would otherwise block the page). Must be
        called BEFORE the injection is submitted."""
        self._dialog_messages = []

        def _handle(dialog):
            self._dialog_messages.append(dialog.message)
            dialog.dismiss()

        self.page.on("dialog", _handle)
        return self

    def dialog_messages(self) -> list:
        return list(self._dialog_messages)

    def page_html_contains(self, needle: str) -> bool:
        """True when `needle` appears UNESCAPED in the rendered HTML — the
        reflected-XSS check. A sanitised page escapes it into entities, so
        this reads False."""
        return self.page.evaluate(
            "(needle) => document.documentElement.innerHTML.indexOf(needle) !== -1",
            needle,
        )

    def injected_script_element_count(self, marker: str) -> int:
        """`<script>` elements injected into the live DOM carrying `marker` —
        0 on a sanitised page."""
        return self.page.evaluate(
            """(marker) => [...document.querySelectorAll('script')].filter(
                (s) => (s.textContent || '').indexOf(marker) !== -1).length""",
            marker,
        )

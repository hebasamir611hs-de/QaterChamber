"""
web/pages/tir_carnet/tir_carnet_page.py — TirCarnetPage.

Public-frontend Page Object for PBI 129403 (QC-SVC-004 — TIR Carnet),
`/our-services/tir-carnet` (Arabic: `/ar/our-services/tir-carnet`). URLs are
always built through `config.settings.web_url()` — never hard-coded.

Canonical path, confirmed live 2026-09-16 (and matching the shape the ATA
Carnet module uses, so every service module in this batch navigates the same
way): `/tir-carnet` answers 302 and `/en/tir-carnet` answers 301, both to
`/our-services/tir-carnet`; `/ar/tir-carnet` answers 301 to
`/ar/our-services/tir-carnet`. Navigating the canonical path directly returns
200 and saves a redirect per navigation.

Locators extracted CLI-first via `tools/extract_locators.py` against the live
page (WEB_BASE_URL=https://qcdev.ihorizons.com) at the framework default
viewport (1920x1080), 2026-09-16:

    python3 tools/extract_locators.py \
      --url https://qcdev.ihorizons.com/our-services/tir-carnet

(the original harvest ran against `/en/tir-carnet`, which 301s to exactly the
page above — same DOM, same locators)

    -> get_by_role("button", name="What is TIR?")                      (FAQ Q1)
    -> get_by_role("button", name="Where can I find details of the TIR convention, 1975?")
    -> get_by_role("link",   name="01Overview") ... "04Frequently asked questions"
    -> get_by_role("link",   name="Download")  x3                      (resource cards)
    -> #main-content

The CLI harvester only walks a,button,input,select,textarea,[role],
[data-testid],[data-test],[aria-label],[contenteditable], so it does not
surface this page's non-interactive `qc-tir-*` wrapper structure (hero,
quick-facts strip, sticky index panel, statistics strip, benefit cards,
criteria rows, numbered steps, resource cards). That structure was confirmed
against the SAME live page with a scoped `page.evaluate()` class-inventory
probe — the same disclosed, script-only fallback used by
web/pages/chambers_law/chambers_law_page.py (no MCP was needed or used):

    section.qc-tir
      header.qc-tir-hero
        nav.qc-tir-crumbs > a.qc-tir-crumb (x2)
        p.qc-tir-eyebrow / h1.qc-tir-title / div.qc-tir-hero-desc.qc-tir-rt
        div.qc-tir-hero-art > img.qc-tir-hero-img
        div.qc-tir-facts > div.qc-tir-fact (x4)
            span.qc-tir-fact-icon
            div.qc-tir-fact-text > span.qc-tir-fact-label + span.qc-tir-fact-value
      div.qc-tir-body > div.qc-tir-layout
        aside.qc-tir-index-col  (position: sticky; top: 96px)
          nav.qc-tir-index > a.qc-tir-index-item (x4)
              span.qc-tir-index-num + span.qc-tir-index-label
        div.qc-tir-content
          section.qc-tir-section (x5)
            div.qc-tir-section-head
              span.qc-tir-section-icon
              div.qc-tir-section-heading
                span.qc-tir-section-badge + h2.qc-tir-section-title
          div.qc-tir-overview > div.qc-tir-video (> iframe) + div.qc-tir-stats
            div.qc-tir-stat (x5) > span.qc-tir-stat-value + span.qc-tir-stat-label
          div.qc-tir-cards > article.qc-tir-card (x3)
            span.qc-tir-card-icon + div.qc-tir-card-text
              h3.qc-tir-card-title + div.qc-tir-card-desc
          ul.qc-tir-criteria > li.qc-tir-criterion (x4) > span.qc-tir-criterion-check
          div.qc-tir-prepare (title/intro/list)
          ol.qc-tir-steps > li.qc-tir-step (x4)
            span.qc-tir-step-num + div.qc-tir-step-text
              h3.qc-tir-step-title + div.qc-tir-step-desc
          div.qc-tir-faq > div.qc-tir-faq-item (x11)
            button.qc-tir-faq-q[aria-expanded] > span.qc-tir-faq-mark
            div.qc-tir-faq-a[hidden]        (opened item gains `.is-open` on the item)
          div.qc-tir-files > article.qc-tir-file (x3)
            span.qc-tir-file-glyph + div.qc-tir-file-text
              span.qc-tir-file-title + span.qc-tir-file-meta
            a.qc-tir-file-btn

Live-env notes (confirmed on the same 2026-09-16 probe):
- The site-wide announcement modal and the Liferay license interstitial are
  handled centrally by core/web/overlays.py and core/web/license_gate.py via
  BasePage.open() — this Page Object adds no local dismissal of its own.
- The FAQ accordion ships fully collapsed: every `button.qc-tir-faq-q` has
  `aria-expanded="false"` and every `div.qc-tir-faq-a` carries the `hidden`
  attribute (computed `display: none`, height 0). Expanding an item sets
  `aria-expanded="true"`, removes `hidden`, adds `.is-open` on the item, and
  rotates `span.qc-tir-faq-mark` 45deg.
- The accordion's own expand indicator is genuinely mirrored per locale: the
  mark sits at the trailing (right) edge of the question in EN and at the
  right-to-left leading edge (visually left) in AR.
- Section surfaces are painted by `div.qc-tir-body` (#FFFFFF); most inner
  blocks declare `background-color: transparent` and inherit that white
  surface, so surface checks go through `effective_background()` (walks to
  the nearest painted ancestor) rather than reading a transparent own-value.
"""

import re

from config.settings import web_url
from core.web.base_page import BasePage
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent

TIR_CARNET_PATH = "/our-services/tir-carnet"

# `linear-gradient(105deg, rgb(74, 10, 34) 0%, rgb(109, 16, 41) 46%, ...)`
_GRADIENT_ANGLE_RE = re.compile(r"linear-gradient\(\s*([\d.]+deg)")
_GRADIENT_STOP_RE = re.compile(r"(rgba?\([^)]*\))\s*([\d.]+%)?")
# Any Arabic-script character — used by the RTL case to prove a field renders
# its Arabic value rather than falling back to the English one.
_ARABIC_RE = re.compile(r"[؀-ۿ]")

# Walks up from an element until it finds an ancestor that actually paints a
# background, so a transparent element sitting on a white panel reports the
# white it visually renders on (see the module docstring's surface note).
_EFFECTIVE_BG_JS = """
(el) => {
  let node = el;
  while (node) {
    const bg = getComputedStyle(node).backgroundColor;
    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
    node = node.parentElement;
  }
  return 'none';
}
"""

_COMPUTED_STYLE_JS = """
(el, props) => {
  const s = getComputedStyle(el);
  const out = {};
  for (const p of props) out[p] = s[p];
  return out;
}
"""


class TirCarnetPage(BasePage):
    # ---- Page root ---------------------------------------------------------
    SECTION = "section.qc-tir"
    MAIN_CONTENT = "#main-content"

    # ---- Hero --------------------------------------------------------------
    HERO = "header.qc-tir-hero"
    HERO_CRUMBS = "nav.qc-tir-crumbs"
    HERO_CRUMB = ".qc-tir-crumb"
    HERO_EYEBROW = ".qc-tir-eyebrow"
    HERO_TITLE = "h1.qc-tir-title"
    HERO_DESC = ".qc-tir-hero-desc"
    HERO_IMAGE = "img.qc-tir-hero-img"

    # ---- Quick-facts strip -------------------------------------------------
    FACTS = ".qc-tir-facts"
    FACT = ".qc-tir-fact"
    FACT_ICON = ".qc-tir-fact-icon"
    FACT_LABEL = ".qc-tir-fact-label"
    FACT_VALUE = ".qc-tir-fact-value"

    # ---- Sticky section index ----------------------------------------------
    INDEX_COL = "aside.qc-tir-index-col"
    INDEX = "nav.qc-tir-index"
    INDEX_ITEM = "a.qc-tir-index-item"
    INDEX_NUM = ".qc-tir-index-num"
    INDEX_LABEL = ".qc-tir-index-label"

    # ---- Content column / sections -----------------------------------------
    LAYOUT = ".qc-tir-layout"
    CONTENT = ".qc-tir-content"
    SECTION_BLOCK = "section.qc-tir-section"
    SECTION_BADGE = ".qc-tir-section-badge"
    SECTION_TITLE = "h2.qc-tir-section-title"
    SECTION_ICON = ".qc-tir-section-icon"

    # ---- Overview: video + statistics --------------------------------------
    OVERVIEW = ".qc-tir-overview"
    VIDEO = ".qc-tir-video"
    VIDEO_IFRAME = ".qc-tir-video iframe"
    STATS = ".qc-tir-stats"
    STAT = ".qc-tir-stat"
    STAT_VALUE = ".qc-tir-stat-value"
    STAT_LABEL = ".qc-tir-stat-label"

    # ---- Benefit cards -----------------------------------------------------
    CARDS = ".qc-tir-cards"
    CARD = "article.qc-tir-card"
    CARD_ICON = ".qc-tir-card-icon"
    CARD_TITLE = ".qc-tir-card-title"
    CARD_DESC = ".qc-tir-card-desc"

    # ---- Eligibility criteria ----------------------------------------------
    CRITERIA = "ul.qc-tir-criteria"
    CRITERION = "li.qc-tir-criterion"
    CRITERION_CHECK = ".qc-tir-criterion-check"

    # ---- Numbered steps ----------------------------------------------------
    STEPS = "ol.qc-tir-steps"
    STEP = "li.qc-tir-step"
    STEP_NUM = ".qc-tir-step-num"
    STEP_TEXT = ".qc-tir-step-text"
    STEP_TITLE = ".qc-tir-step-title"
    STEP_DESC = ".qc-tir-step-desc"

    # ---- FAQ accordion -----------------------------------------------------
    FAQ = ".qc-tir-faq"
    FAQ_ITEM = ".qc-tir-faq-item"
    FAQ_QUESTION = "button.qc-tir-faq-q"
    FAQ_ANSWER = ".qc-tir-faq-a"
    FAQ_MARK = ".qc-tir-faq-mark"
    FAQ_OPEN_ITEM = ".qc-tir-faq-item.is-open"

    # ---- Downloadable resources --------------------------------------------
    FILES = ".qc-tir-files"
    FILE = "article.qc-tir-file"
    FILE_TITLE = ".qc-tir-file-title"
    FILE_META = ".qc-tir-file-meta"
    FILE_BUTTON = "a.qc-tir-file-btn"

    # ---- Navigation --------------------------------------------------------
    def open_tir_carnet(self, locale: str = "en") -> "TirCarnetPage":
        self.open(web_url(TIR_CARNET_PATH, locale=locale))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_faq_section(self) -> None:
        self.page.locator(self.FAQ).scroll_into_view_if_needed()

    # ---- Generic state helpers ---------------------------------------------
    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_language(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    def computed_style(self, locator: str, props: list) -> dict:
        return self.page.locator(locator).first.evaluate(_COMPUTED_STYLE_JS, props)

    def effective_background(self, locator: str) -> str:
        """The background colour this element visually renders on — its own
        if it paints one, otherwise the nearest painted ancestor's (see the
        module docstring's surface note)."""
        return self.page.locator(locator).first.evaluate(_EFFECTIVE_BG_JS)

    def box(self, locator: str) -> dict:
        return self.page.locator(locator).first.bounding_box()

    def boxes(self, locator: str) -> list:
        loc = self.page.locator(locator)
        return [loc.nth(i).bounding_box() for i in range(loc.count())]

    def texts(self, locator: str) -> list:
        return [t.strip() for t in self.page.locator(locator).all_inner_texts()]

    def count(self, locator: str) -> int:
        return self.page.locator(locator).count()

    @staticmethod
    def contains_arabic(value: str) -> bool:
        return bool(_ARABIC_RE.search(value or ""))

    # ---- Hero --------------------------------------------------------------
    def is_hero_visible(self) -> bool:
        return self.is_visible(self.HERO)

    def hero_eyebrow_text(self) -> str:
        return self.text(self.HERO_EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.HERO_TITLE).strip()

    def hero_gradient_raw(self) -> str:
        return self.computed_style(self.HERO, ["backgroundImage"])["backgroundImage"]

    def hero_gradient_parts(self) -> dict:
        """Parses the hero's computed `linear-gradient(...)` into
        {'angle': '105deg', 'stops': [('rgb(74, 10, 34)', '0%'), ...]} so a
        token assertion can name the exact part that deviates instead of
        diffing one opaque string. Returns {'angle': None, 'stops': []} when
        the hero paints no gradient at all."""
        raw = self.hero_gradient_raw() or ""
        angle_match = _GRADIENT_ANGLE_RE.search(raw)
        stops = [
            (color, position)
            for color, position in _GRADIENT_STOP_RE.findall(raw)
        ]
        return {
            "raw": raw,
            "angle": angle_match.group(1) if angle_match else None,
            "stops": stops,
        }

    # ---- Quick-facts strip -------------------------------------------------
    def fact_count(self) -> int:
        return self.count(self.FACT)

    def fact_labels(self) -> list:
        return self.texts(self.FACT_LABEL)

    def fact_values(self) -> list:
        return self.texts(self.FACT_VALUE)

    # ---- Sticky section index ----------------------------------------------
    def index_numbers(self) -> list:
        return self.texts(self.INDEX_NUM)

    def index_labels(self) -> list:
        return self.texts(self.INDEX_LABEL)

    def index_item_count(self) -> int:
        return self.count(self.INDEX_ITEM)

    def index_box(self) -> dict:
        return self.box(self.INDEX_COL)

    def content_box(self) -> dict:
        return self.box(self.CONTENT)

    # ---- Sections ----------------------------------------------------------
    def section_titles(self) -> list:
        return self.texts(self.SECTION_TITLE)

    def section_badges(self) -> list:
        return self.texts(self.SECTION_BADGE)

    # ---- Overview ----------------------------------------------------------
    def is_video_embedded(self) -> bool:
        return self.count(self.VIDEO_IFRAME) > 0 and self.is_visible(self.VIDEO)

    def video_src(self) -> str:
        return self.page.locator(self.VIDEO_IFRAME).first.get_attribute("src") or ""

    def stat_count(self) -> int:
        return self.count(self.STAT)

    def stat_values(self) -> list:
        return self.texts(self.STAT_VALUE)

    def stat_labels(self) -> list:
        return self.texts(self.STAT_LABEL)

    # ---- Benefit cards -----------------------------------------------------
    def card_count(self) -> int:
        return self.count(self.CARD)

    def card_titles(self) -> list:
        return self.texts(self.CARD_TITLE)

    # ---- Criteria ----------------------------------------------------------
    def criterion_count(self) -> int:
        return self.count(self.CRITERION)

    def criterion_texts(self) -> list:
        return self.texts(self.CRITERION)

    def criterion_boxes(self) -> list:
        return self.boxes(self.CRITERION)

    def criterion_check_boxes(self) -> list:
        return self.boxes(self.CRITERION_CHECK)

    # ---- Steps -------------------------------------------------------------
    def step_count(self) -> int:
        return self.count(self.STEP)

    def step_numbers(self) -> list:
        return self.texts(self.STEP_NUM)

    def step_titles(self) -> list:
        return self.texts(self.STEP_TITLE)

    def step_boxes(self) -> list:
        return self.boxes(self.STEP)

    def step_number_boxes(self) -> list:
        return self.boxes(self.STEP_NUM)

    def step_text_boxes(self) -> list:
        return self.boxes(self.STEP_TEXT)

    # ---- FAQ accordion -----------------------------------------------------
    def faq_item_count(self) -> int:
        return self.count(self.FAQ_ITEM)

    def faq_questions(self) -> list:
        return self.texts(self.FAQ_QUESTION)

    def faq_expanded_flags(self) -> list:
        """The `aria-expanded` attribute of every question, in page order."""
        loc = self.page.locator(self.FAQ_QUESTION)
        return [loc.nth(i).get_attribute("aria-expanded") for i in range(loc.count())]

    def faq_answer_states(self) -> list:
        """Per answer: whether it carries the `hidden` attribute, its computed
        display, and its rendered height — the three independent signals that
        an answer is genuinely collapsed rather than merely transparent."""
        return self.page.locator(self.FAQ_ANSWER).evaluate_all(
            """
            (els) => els.map(e => ({
                hidden: e.hasAttribute('hidden'),
                display: getComputedStyle(e).display,
                visibility: getComputedStyle(e).visibility,
                height: Math.round(e.getBoundingClientRect().height),
            }))
            """
        )

    def faq_marks_visible(self) -> list:
        """Whether each question's collapsed/expanded indicator renders."""
        return self.page.locator(self.FAQ_MARK).evaluate_all(
            "(els) => els.map(e => getComputedStyle(e).display !== 'none' "
            "&& getComputedStyle(e).visibility !== 'hidden')"
        )

    def faq_mark_transforms(self) -> list:
        return self.page.locator(self.FAQ_MARK).evaluate_all(
            "(els) => els.map(e => getComputedStyle(e).transform)"
        )

    def faq_open_item_count(self) -> int:
        return self.count(self.FAQ_OPEN_ITEM)

    def faq_accordion_geometry(self) -> dict:
        """Everything needed to prove the accordion is rendering at its
        fully-collapsed height: the container height, each item's height,
        each question row's height, and the measured vertical gaps between
        consecutive items (read from the DOM, so no magic spacing constant
        is baked into a test)."""
        return self.page.evaluate(
            """
            (sel) => {
              const faq = document.querySelector(sel.faq);
              const items = [...document.querySelectorAll(sel.item)];
              const rects = items.map(i => i.getBoundingClientRect());
              const gaps = [];
              for (let i = 1; i < rects.length; i++)
                gaps.push(Math.round(rects[i].top - rects[i - 1].bottom));
              return {
                container_height: Math.round(faq.getBoundingClientRect().height),
                item_heights: rects.map(r => Math.round(r.height)),
                question_heights: items.map(i =>
                    Math.round(i.querySelector(sel.question).getBoundingClientRect().height)),
                gaps: gaps,
              };
            }
            """,
            {"faq": self.FAQ, "item": self.FAQ_ITEM, "question": self.FAQ_QUESTION},
        )

    def faq_mark_box(self, index: int = 0) -> dict:
        return self.page.locator(self.FAQ_MARK).nth(index).bounding_box()

    def faq_question_box(self, index: int = 0) -> dict:
        return self.page.locator(self.FAQ_QUESTION).nth(index).bounding_box()

    def expand_faq(self, index: int) -> None:
        """Clicks a question by its position and waits for its own answer to
        become visible — an explicit element-state wait, never a delay."""
        item = self.page.locator(self.FAQ_ITEM).nth(index)
        item.locator(self.FAQ_QUESTION).click()
        item.locator(self.FAQ_ANSWER).wait_for(state="visible")

    def faq_answer_markup(self, index: int) -> dict:
        """Structural read of one answer's RENDERED markup: the tag census of
        its real child elements, its heading/list/link content, and its raw
        innerHTML + innerText. A rich-text field delivered as raw HTML would
        show an empty tag census with the tags visible as TEXT — which is why
        both the parsed structure and the plain text are returned together."""
        return self.page.locator(self.FAQ_ANSWER).nth(index).evaluate(
            """
            (el) => {
              const census = {};
              el.querySelectorAll('*').forEach(n => {
                const t = n.tagName.toLowerCase();
                census[t] = (census[t] || 0) + 1;
              });
              return {
                tags: census,
                headings: [...el.querySelectorAll('h1,h2,h3,h4,h5,h6')].map(h => h.textContent.trim()),
                bullets: [...el.querySelectorAll('ul li, ol li')].map(li => li.textContent.trim()),
                links: [...el.querySelectorAll('a')].map(a => ({
                    text: a.textContent.trim(),
                    href: a.getAttribute('href'),
                    target: a.getAttribute('target'),
                })),
                html: el.innerHTML,
                text: el.innerText,
              };
            }
            """
        )

    def faq_index_with_rich_answer(self) -> int:
        """Index of the first FAQ whose answer is configured with the full
        rich-text payload TC 138029 step 1 authors — a heading, at least two
        bullet items and an inline hyperlink — or -1 when no answer on the
        live page carries it. Used by that test to detect its (CMS-authored)
        precondition rather than guess at an item number."""
        return self.page.locator(self.FAQ_ANSWER).evaluate_all(
            """
            (els) => {
              for (let i = 0; i < els.length; i++) {
                const e = els[i];
                const hasHeading = e.querySelectorAll('h1,h2,h3,h4,h5,h6').length > 0;
                const bullets = e.querySelectorAll('ul li, ol li').length;
                const hasLink = e.querySelectorAll('a[href]').length > 0;
                if (hasHeading && bullets >= 2 && hasLink) return i;
              }
              return -1;
            }
            """
        )

    # ---- Downloadable resources --------------------------------------------
    def file_count(self) -> int:
        return self.count(self.FILE)

    def file_titles(self) -> list:
        return self.texts(self.FILE_TITLE)

    # ---- Global chrome / extra regions (batch 2, confirmed live 2026-09-24) --
    # Header language toggle routes through /c/portal/update_language and
    # lands on the other locale's canonical URL. Dark mode is reached only via
    # the site-wide Accessibility tools widget.
    PAGE_BODY = "body"
    HEADER = "header.qc-global-site-header"
    HEADER_NAV_LINK = "header.qc-global-site-header a.qc-nav-link"
    LANG_TOGGLE = "header.qc-global-site-header a.qc-lang-switcher"
    HERO_COPY = ".qc-tir-hero-copy"
    HERO_ART = ".qc-tir-hero-art"
    # Rich-text body copy inside content sections only (the hero description
    # is also `.qc-tir-rt`, white on the gradient, and must not stand in).
    SECTION_RT = "section.qc-tir-section .qc-tir-rt"
    # Section prose only — SECTION_RT minus the card/step/FAQ rich text that
    # the language case checks under their own slots (avoids double-counting).
    SECTION_PROSE = ("section.qc-tir-section .qc-tir-rt:not(.qc-tir-card-desc)"
                     ":not(.qc-tir-step-desc):not(.qc-tir-faq-a)")

    def toggle_language(self) -> "TirCarnetPage":
        """Click the header language toggle and wait for the real navigation
        (URL changed) plus the page root — never read state straight after
        click(), which still sees the previous locale."""
        before = self.page.url
        self.click(self.LANG_TOGGLE)
        self.wait_for_url(lambda url: url != before, timeout=20000)
        self.wait_for(self.SECTION)
        self.wait_for(self.HERO_TITLE)
        return self

    def enable_dark_mode(self) -> "TirCarnetPage":
        """Flip the real Dark mode switch, then wait for the theme's CSS
        colour transitions to finish — computed colours read mid-transition
        are interpolated values (confirmed live: index labels measured
        rgb(199,199,199) mid-fade vs rgb(237,237,237) settled)."""
        AccessibilityToolsComponent(self.page).enable_dark_mode()
        self.page.wait_for_function(
            "() => document.getAnimations().every((a) => a.playState !== 'running')", timeout=10000
        )
        return self

    def wait_for_fonts(self) -> "TirCarnetPage":
        """Wait for web fonts (Cairo) so text-driven sizes are final."""
        self.page.wait_for_function("() => document.fonts.status === 'loaded'", timeout=15000)
        return self

    def scroll_to(self, locator: str, index: int = 0) -> None:
        self.page.locator(locator).nth(index).scroll_into_view_if_needed()

    def language_toggle_label(self) -> str:
        return self.text(self.LANG_TOGGLE).strip()

    def theme(self):
        return self.page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    def is_displayed(self, locator: str, index: int = 0) -> bool:
        return self.page.locator(locator).nth(index).is_visible()

    def text_contents(self, locator: str) -> list:
        """textContent of every match — reads collapsed (hidden) FAQ answers
        too, which inner_text() reports as ''."""
        return [" ".join((t or "").split()) for t in self.page.locator(locator).all_text_contents()]

    def resolved_text_align(self, locator: str, index: int = 0) -> str:
        """Computed text-align resolved to a physical side (start/end are
        logical: start == right under direction: rtl)."""
        return self.page.locator(locator).nth(index).evaluate(
            """(el) => { const s = getComputedStyle(el), rtl = s.direction === 'rtl', a = s.textAlign;
                if (a === 'start') return rtl ? 'right' : 'left';
                if (a === 'end') return rtl ? 'left' : 'right';
                return a; }"""
        )

    def computed_styles_all(self, locator: str, props: list) -> list:
        return self.page.locator(locator).evaluate_all(
            "(els, props) => els.map((el) => { const s = getComputedStyle(el); const o = {};"
            " for (const p of props) o[p] = s[p]; return o; })",
            props,
        )

    def section_in_view(self):
        return self.page.evaluate(
            """(sel) => { const s = [...document.querySelectorAll(sel)].find((e) => {
                    const r = e.getBoundingClientRect(); return r.bottom > 0 && r.top < innerHeight; });
                return s ? (s.id || (s.querySelector('h2') || {}).textContent || null) : null; }""",
            self.SECTION_BLOCK,
        )

    def horizontal_overflow_px(self) -> int:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth - document.documentElement.clientWidth"
        )

    def overflowing_elements(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll("body *")]
                .filter((e) => { const r = e.getBoundingClientRect();
                    return r.width > 0 && r.right > innerWidth + 1 && getComputedStyle(e).visibility !== "hidden"; })
                .slice(0, 5).map((e) => e.tagName.toLowerCase() + "." + String(e.className).trim()
                    + " (right=" + Math.round(e.getBoundingClientRect().right) + "px)")"""
        )

    def clipped_text_elements(self) -> list:
        return self.page.evaluate(
            """() => [...document.querySelectorAll("header.qc-tir-hero *, .qc-tir-content *")]
                .filter((e) => e.offsetParent !== null && e.children.length === 0
                    && e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX !== "visible")
                .map((e) => String(e.className) || e.tagName)"""
        )

    def text_contrast(self, locator: str, index: int = 0) -> dict:
        """WCAG contrast of the nth match's text against the first solid
        ancestor background (text alpha blended). ratio=None when a gradient
        or image background is reached first (not measurable)."""
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const parse = (c) => { const m = c.match(/[0-9.]+/g) || [0, 0, 0, 0];
                    return [+m[0], +m[1], +m[2], m.length > 3 ? +m[3] : 1]; };
                const lum = (rgb) => { const f = (v) => { v /= 255;
                    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                    return 0.2126 * f(rgb[0]) + 0.7152 * f(rgb[1]) + 0.0722 * f(rgb[2]); };
                const s = getComputedStyle(el);
                let node = el, bg = null, blocker = null;
                while (node && node.nodeType === 1) {
                    const cs = getComputedStyle(node);
                    if (cs.backgroundImage && cs.backgroundImage !== "none") { blocker = cs.backgroundImage; break; }
                    const c = parse(cs.backgroundColor);
                    if (c[3] > 0) { bg = c; break; }
                    node = node.parentElement;
                }
                if (!bg && !blocker) bg = [255, 255, 255, 1];
                const fg = parse(s.color);
                const out = {color: s.color, fontSize: parseFloat(s.fontSize), fontWeight: +s.fontWeight,
                             text: (el.textContent || "").trim().slice(0, 40)};
                if (!bg) return Object.assign(out, {ratio: null, background: blocker});
                const a = fg[3];
                const mix = [0, 1, 2].map((i) => fg[i] * a + bg[i] * (1 - a));
                const l1 = lum(mix), l2 = lum(bg);
                return Object.assign(out, {ratio: Math.round((Math.max(l1, l2) + 0.05) / (Math.min(l1, l2) + 0.05) * 100) / 100,
                                           background: "rgb(" + bg.slice(0, 3).join(", ") + ")"});
            }
            """
        )

    def relative_luminance(self, css_colour: str) -> float:
        return self.page.evaluate(
            """(c) => { const m = (c.match(/[0-9.]+/g) || [0, 0, 0]).map(Number);
                const f = (v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
                return 0.2126 * f(m[0]) + 0.7152 * f(m[1]) + 0.0722 * f(m[2]); }""",
            css_colour,
        )

    def child_box(self, parent: str, child: str, index: int = 0):
        """bounding_box() of the first `child` inside the index-th `parent`."""
        return self.page.locator(parent).nth(index).locator(child).first.bounding_box()

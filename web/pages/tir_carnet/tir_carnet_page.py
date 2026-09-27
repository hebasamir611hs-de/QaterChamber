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

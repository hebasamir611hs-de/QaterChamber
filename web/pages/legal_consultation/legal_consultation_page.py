"""
web/pages/legal_consultation/legal_consultation_page.py — LegalConsultationPage.

Public-frontend Page Object for PBI 129404 (QC-SVC-006 — Legal Consulting),
`/en/legal-consultation` (Arabic: `/ar/legal-consultation`).

URL note — navigate the canonical path, not the /en redirect
------------------------------------------------------------------
Confirmed live 2026-09-16 against WEB_BASE_URL=https://qcdev.ihorizons.com:

    /en/legal-consultation             -> 200, REDIRECTS to /our-services/legal-consultation
    /ar/legal-consultation             -> 200, REDIRECTS to /ar/our-services/legal-consultation
    /our-services/legal-consultation   -> 200 directly, no redirect
    /ar/our-services/legal-consultation-> 200 directly, no redirect
    /legal-consultation                -> no such route

The canonical path is used here so no test pays a redirect hop, and so this
module matches the other service pages in this suite. It fits
`config.settings.web_url()` exactly: English takes no prefix, Arabic goes
through `locale="ar"` -> ARABIC_PATH_PREFIX. The URL is never hard-coded.

(An earlier single navigation to the canonical path timed out on
`wait_until="load"`; that was a transient qcdev blip, not a routing fact — six
consecutive `load` navigations afterwards completed in 1.3-9.2s. The real
readiness hazard on this page is `networkidle`, below.)

Readiness — never `networkidle` on this page
------------------------------------------------------------------
The page body is rendered client-side (a `.qc-lc-status` "Loading…" node is
swapped out once the content arrives), and the embedded reCAPTCHA Enterprise
script plus the site chat widget keep the network intermittently busy: a
`wait_until="networkidle"` navigation was observed timing out at 30s against
this exact URL while the page itself had been fully rendered for ~25s of that.
`open_legal_consultation()` therefore navigates normally (BasePage.open ->
`page.goto`, default `load`) and then waits on a real content element.

Locator extraction — CLI-first, with a disclosed scoped-DOM fallback
------------------------------------------------------------------
    python3 tools/extract_locators.py --url https://qcdev.ihorizons.com/en/legal-consultation

surfaced the interactive layer only (the harvester walks
a,button,input,select,textarea,[role],[data-testid],[aria-label]) — the four
FAQ accordion triggers came back as unique `role=button` candidates:

    -> get_by_role("button", name="Who is eligible to request a legal consultation?")
    -> get_by_role("button", name="How long does it take to receive a response?")
    -> get_by_role("button", name="Which documents can I attach to my request?")
    -> get_by_role("button", name="Is the consultation confidential, and is there a fee?")

Everything else this PBI's cases assert on (hero eyebrow/title/description,
the quick-facts tiles, the section index, the five section badges/headings,
the overview info cards, the eligibility criteria rows, the two scope groups,
the four workflow steps, the next-step banner) is non-interactive
`<p>/<span>/<div>/<li>` markup that the CLI harvester does not walk by design.
Those were confirmed by a scoped Playwright `evaluate()` DOM probe against the
same live page at the framework viewport (1920x1080) — the same disclosed
fallback pattern used in `chambers_law_page.py`, and NOT the Playwright MCP
(a plain script sufficed; the whole DOM never entered context, only the class
skeleton below).

Confirmed structure (live, EN and AR identical):

    section.qc-lc
      header.qc-lc-hero
        nav.qc-lc-crumbs > a.qc-lc-crumb (x2: Home, Services)
        div.qc-lc-hero-grid > div.qc-lc-hero-copy
          p.qc-lc-eyebrow / h1.qc-lc-title / div.qc-lc-hero-desc
          div.qc-lc-hero-ctas > div.qc-lc-cta-row > button.qc-lc-cta
        div.qc-lc-hero-art > img.qc-lc-hero-img
      div.qc-lc-facts > div.qc-lc-fact (x4)
          span.qc-lc-fact-icon > img
          div.qc-lc-fact-text > span.qc-lc-fact-label + span.qc-lc-fact-value
      div.qc-lc-body > div.qc-lc-layout
        aside.qc-lc-index-col > nav.qc-lc-index > a.qc-lc-index-item (x5)
            span.qc-lc-index-num + span.qc-lc-index-label
        div.qc-lc-content > section.qc-lc-section (x5, ids below)
            div.qc-lc-section-head
              span.qc-lc-section-icon
              div.qc-lc-section-heading
                span.qc-lc-section-badge + h2.qc-lc-section-title
            #qc-lc-overview    : div.qc-lc-intro, div.qc-lc-cards > article.qc-lc-card (x3)
                                   span.qc-lc-card-icon > img, h3.qc-lc-card-title, div.qc-lc-card-desc
            #qc-lc-eligibility : ul.qc-lc-criteria > li.qc-lc-criterion (x3)
                                   span.qc-lc-criterion-check > svg
            #qc-lc-scope       : div.qc-lc-scope > div.qc-lc-scope-group (x2)
                                   .qc-lc-scope-group--included / --excluded
                                   div.qc-lc-scope-head > span.qc-lc-scope-glyph
                                   ul.qc-lc-scope-list > li.qc-lc-scope-item
                                     > span.qc-lc-scope-dot
            #qc-lc-process     : ol.qc-lc-steps > li.qc-lc-step (x4)
                                   span.qc-lc-step-num, h3.qc-lc-step-title,
                                   div.qc-lc-step-desc
            #qc-lc-faq         : div.qc-lc-faq > div.qc-lc-faq-item (x4)
                                   button.qc-lc-faq-q[aria-expanded]
                                     > span.qc-lc-faq-mark
                                   div.qc-lc-faq-a[hidden]
      div.qc-lc-banner
        div.qc-lc-banner-copy
          span.qc-lc-banner-eyebrow / h2.qc-lc-banner-title / div.qc-lc-banner-body
        div.qc-lc-banner-ctas > button.qc-lc-cta
      div.qc-lc-modal[data-qc-lc-modal][hidden]        <- the request form
        div.qc-lc-modal-backdrop[data-qc-lc-modal-close]
        div.qc-lc-dialog[role=dialog][aria-modal=true]
          div.qc-lc-dialog-head > span.qc-lc-dialog-eyebrow + h2.qc-lc-dialog-title
          button.qc-lc-dialog-x
          div.qc-lc-alert[role=alert][aria-live=polite][hidden]
          form.qc-lc-form > div.qc-lc-grid > div.qc-lc-field (x10)
            label.qc-lc-label (+ span.qc-lc-req for required)
            input.qc-lc-input / div.qc-lc-phone > input.qc-lc-phone-input /
            select.qc-lc-select / textarea.qc-lc-textarea /
            label.qc-lc-drop + input.qc-lc-file / div.qc-lc-captcha
            span.qc-lc-error
          input.qc-lc-hp[name=website][aria-hidden]     <- honeypot
          div.qc-lc-dialog-actions
            button.qc-lc-btn--ghost (Cancel) + button.qc-lc-btn--primary (Submit)

The request form is a MODAL on this same page (there is no separate form URL);
it is `hidden` at load and opened by either "Request Legal Consultation"
button — `open_request_form()` drives the hero one.

CAPTCHA — invisible reCAPTCHA Enterprise
------------------------------------------------------------------
`div.qc-lc-captcha[data-qc-recaptcha]` is an empty mount node; its parent
`.qc-lc-field` (label "Security check*" / "التحقق الأمني*") is `hidden`
(`display: none`) and Google's widget renders as the score-based *invisible*
Enterprise badge, not as an in-form challenge. So the CAPTCHA is present and
armed but is NOT a visible form control — see the report/notes on TC 138493,
and TC 138477's submission blocker.

No announcement overlay was showing on this page at extraction time (the
`#qc-announcement-popup-root` close button never appeared within 3s), but
BasePage.open()'s global dismissal covers it for free if it returns.
"""

from config.settings import web_url
from core.web.base_page import BasePage

# The canonical path — identical for both locales; web_url(locale="ar")
# prepends ARABIC_PATH_PREFIX. See the module docstring for why the /en/<slug>
# and /ar/<slug> friendly URLs are deliberately not used.
LEGAL_CONSULTATION_PATH = "/our-services/legal-consultation"


class LegalConsultationPage(BasePage):
    # ---- Root / hero -------------------------------------------------------
    ROOT = "section.qc-lc"
    HERO = ".qc-lc-hero"
    CRUMBS = "nav.qc-lc-crumbs"
    CRUMB = ".qc-lc-crumb"
    HERO_COPY = ".qc-lc-hero-copy"
    EYEBROW = ".qc-lc-eyebrow"
    TITLE = "h1.qc-lc-title"
    HERO_DESC = ".qc-lc-hero-desc"
    HERO_CTAS = ".qc-lc-hero-ctas"
    HERO_CTA = ".qc-lc-hero-ctas .qc-lc-cta"
    HERO_IMG = ".qc-lc-hero-img"

    # ---- Quick-facts strip -------------------------------------------------
    FACTS = ".qc-lc-facts"
    FACT = ".qc-lc-fact"
    FACT_ICON = ".qc-lc-fact-icon"
    FACT_ICON_IMG = ".qc-lc-fact-icon img"
    FACT_LABEL = ".qc-lc-fact-label"
    FACT_VALUE = ".qc-lc-fact-value"

    # ---- Section index (01..05) --------------------------------------------
    INDEX_COL = ".qc-lc-index-col"
    INDEX = "nav.qc-lc-index"
    INDEX_ITEM = ".qc-lc-index-item"
    INDEX_NUM = ".qc-lc-index-num"
    INDEX_LABEL = ".qc-lc-index-label"

    # ---- Sections ----------------------------------------------------------
    CONTENT = ".qc-lc-content"
    SECTION = "section.qc-lc-section"
    SECTION_BADGE = ".qc-lc-section-badge"
    SECTION_TITLE = ".qc-lc-section-title"
    SECTION_ICON = ".qc-lc-section-icon"

    SECTION_OVERVIEW = "#qc-lc-overview"
    SECTION_ELIGIBILITY = "#qc-lc-eligibility"
    SECTION_SCOPE = "#qc-lc-scope"
    SECTION_PROCESS = "#qc-lc-process"
    SECTION_FAQ = "#qc-lc-faq"

    # ---- Section 01 — overview + info cards --------------------------------
    INTRO = ".qc-lc-intro"
    CARDS = ".qc-lc-cards"
    CARD = ".qc-lc-card"
    CARD_ICON = ".qc-lc-card-icon"
    CARD_ICON_IMG = ".qc-lc-card-icon img"
    CARD_TITLE = ".qc-lc-card-title"
    CARD_DESC = ".qc-lc-card-desc"

    # ---- Section 02 — eligibility criteria ---------------------------------
    CRITERIA = "ul.qc-lc-criteria"
    CRITERION = "li.qc-lc-criterion"
    CRITERION_CHECK = ".qc-lc-criterion-check"

    # ---- Section 03 — scope / exclusions -----------------------------------
    SCOPE = ".qc-lc-scope"
    SCOPE_GROUP = ".qc-lc-scope-group"
    SCOPE_GROUP_INCLUDED = ".qc-lc-scope-group--included"
    SCOPE_GROUP_EXCLUDED = ".qc-lc-scope-group--excluded"
    SCOPE_HEAD = ".qc-lc-scope-head"
    SCOPE_GLYPH = ".qc-lc-scope-glyph"
    SCOPE_ITEM = ".qc-lc-scope-item"

    # ---- Section 04 — workflow steps ---------------------------------------
    STEPS = "ol.qc-lc-steps"
    STEP = "li.qc-lc-step"
    STEP_NUM = ".qc-lc-step-num"
    STEP_TITLE = ".qc-lc-step-title"
    STEP_DESC = ".qc-lc-step-desc"

    # ---- Section 05 — FAQ accordion ----------------------------------------
    FAQ = ".qc-lc-faq"
    FAQ_ITEM = ".qc-lc-faq-item"
    FAQ_QUESTION = ".qc-lc-faq-q"
    FAQ_MARK = ".qc-lc-faq-mark"
    FAQ_ANSWER = ".qc-lc-faq-a"

    # ---- Next-step banner --------------------------------------------------
    BANNER = ".qc-lc-banner"
    BANNER_EYEBROW = ".qc-lc-banner-eyebrow"
    BANNER_TITLE = ".qc-lc-banner-title"
    BANNER_BODY = ".qc-lc-banner-body"
    BANNER_CTA = ".qc-lc-banner .qc-lc-cta"

    # ---- Request-form modal ------------------------------------------------
    MODAL = ".qc-lc-modal"
    DIALOG = ".qc-lc-dialog"
    DIALOG_EYEBROW = ".qc-lc-dialog-eyebrow"
    DIALOG_TITLE = ".qc-lc-dialog-title"
    DIALOG_CLOSE = ".qc-lc-dialog-x"
    FORM = "form.qc-lc-form"
    FIELD = ".qc-lc-field"
    FIELD_LABEL = ".qc-lc-label"
    FIELD_REQUIRED_MARK = ".qc-lc-req"
    CAPTCHA_MOUNT = ".qc-lc-captcha"
    RECAPTCHA_IFRAME = 'iframe[src*="recaptcha"]'
    SUBMIT_BUTTON = ".qc-lc-btn--primary"
    CANCEL_BUTTON = ".qc-lc-btn--ghost"

    # Field control ids (confirmed live) — used by field-level queries so a
    # test never restates a raw selector.
    FIELD_CONTROL_IDS = (
        "qc-lc-fullName",
        "qc-lc-companyName",
        "qc-lc-email",
        "qc-lc-phone",
        "qc-lc-category",
        "qc-lc-subject",
        "qc-lc-description",
        "qc-lc-attachment",
    )

    # ---- Navigation --------------------------------------------------------
    def open_legal_consultation(self, locale: str = "en") -> "LegalConsultationPage":
        """Open the public Legal Consultation page.

        Waits on the last client-rendered element the cases touch (the final
        FAQ trigger) rather than on `networkidle`, which this page cannot
        reach reliably — see the module docstring.
        """
        self.open(web_url(LEGAL_CONSULTATION_PATH, locale=locale))
        self.wait_for(self.TITLE, state="visible", timeout=30000)
        self.wait_for(self.FAQ_QUESTION, state="visible", timeout=30000, first=True)
        return self

    def document_direction(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('dir')")

    def document_language(self) -> str:
        return self.page.evaluate("() => document.documentElement.getAttribute('lang')")

    # ---- Generic measurement helpers --------------------------------------
    def box(self, locator: str, index: int = 0) -> dict:
        """Bounding box of the nth match — {x, y, width, height} in CSS px."""
        return self.page.locator(locator).nth(index).bounding_box()

    def computed_style(self, locator: str, props: list, index: int = 0) -> dict:
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el, props) => {
                const s = getComputedStyle(el);
                const out = {};
                for (const p of props) out[p] = s[p];
                return out;
            }
            """,
            props,
        )

    def overflow_metrics(self, locator: str, index: int = 0) -> dict:
        """scroll/client sizes + the overflow mode — the pair needed to tell
        real clipping/truncation from harmless `overflow: visible` spill."""
        return self.page.locator(locator).nth(index).evaluate(
            """
            (el) => {
                const s = getComputedStyle(el);
                return {
                    scrollWidth: el.scrollWidth, clientWidth: el.clientWidth,
                    scrollHeight: el.scrollHeight, clientHeight: el.clientHeight,
                    overflowX: s.overflowX, overflowY: s.overflowY,
                    textOverflow: s.textOverflow,
                };
            }
            """
        )

    def image_is_loaded(self, locator: str, index: int = 0) -> bool:
        """True only when the <img> actually decoded (a broken icon reports
        complete=true with naturalWidth 0)."""
        return self.page.locator(locator).nth(index).evaluate(
            "(img) => img.complete === true && img.naturalWidth > 0"
        )

    # ---- Hero --------------------------------------------------------------
    def hero_eyebrow_text(self) -> str:
        return self.text(self.EYEBROW).strip()

    def hero_title_text(self) -> str:
        return self.text(self.TITLE).strip()

    def hero_description_text(self) -> str:
        return self.text(self.HERO_DESC).strip()

    def hero_cta_text(self) -> str:
        return self.text(self.HERO_CTA).strip()

    def hero_background_image(self) -> str:
        return self.computed_style(self.HERO, ["backgroundImage"])["backgroundImage"]

    def breadcrumb_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.CRUMB).all_inner_texts()]

    # ---- Quick facts -------------------------------------------------------
    def fact_count(self) -> int:
        return self.page.locator(self.FACT).count()

    def fact_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.FACT_LABEL).all_inner_texts()]

    def fact_values(self) -> list:
        return [t.strip() for t in self.page.locator(self.FACT_VALUE).all_inner_texts()]

    def fact_tiles(self) -> list:
        """One record per tile: label/value text, geometry, and whether the
        icon <img> really decoded — everything TC 138484 measures, harvested
        in a single round-trip so the tiles are compared at one layout."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-fact')).map((tile) => {
                const r = tile.getBoundingClientRect();
                const label = tile.querySelector('.qc-lc-fact-label');
                const value = tile.querySelector('.qc-lc-fact-value');
                const iconImg = tile.querySelector('.qc-lc-fact-icon img');
                const lr = label.getBoundingClientRect();
                return {
                    label: label.textContent.trim(),
                    value: value.textContent.trim(),
                    x: r.x, right: r.right, width: r.width,
                    labelRight: lr.right, labelHeight: lr.height,
                    hasIcon: !!iconImg,
                    iconLoaded: !!iconImg && iconImg.complete && iconImg.naturalWidth > 0,
                };
            })
            """
        )

    # ---- Section index -----------------------------------------------------
    def index_numbers(self) -> list:
        return [t.strip() for t in self.page.locator(self.INDEX_NUM).all_inner_texts()]

    def index_labels(self) -> list:
        return [t.strip() for t in self.page.locator(self.INDEX_LABEL).all_inner_texts()]

    def index_is_on_leading_side(self) -> bool:
        """True when the index column sits BEFORE the content column in
        reading order (left in LTR, right in RTL) — the direction-agnostic
        way to express 'the index sits on the mirrored side'."""
        index_box = self.box(self.INDEX_COL)
        content_box = self.box(self.CONTENT)
        rtl = self.document_direction() == "rtl"
        return index_box["x"] > content_box["x"] if rtl else index_box["x"] < content_box["x"]

    # ---- Sections ----------------------------------------------------------
    def section_badges(self) -> list:
        return [t.strip() for t in self.page.locator(self.SECTION_BADGE).all_inner_texts()]

    def section_titles(self) -> list:
        return [t.strip() for t in self.page.locator(self.SECTION_TITLE).all_inner_texts()]

    def section_badge_text(self, section_selector: str) -> str:
        return self.page.locator(f"{section_selector} {self.SECTION_BADGE}").inner_text().strip()

    def section_title_text(self, section_selector: str) -> str:
        return self.page.locator(f"{section_selector} {self.SECTION_TITLE}").inner_text().strip()

    def intro_text(self) -> str:
        return self.text(self.INTRO).strip()

    # ---- Section 01 — info cards -------------------------------------------
    def card_count(self) -> int:
        return self.page.locator(self.CARD).count()

    def cards(self) -> list:
        """Rendered order is the delivery-surface expression of the CMS 'Card
        Display Order' — one record per card with its icon/title/description
        state, in DOM order."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-card')).map((card) => {
                const img = card.querySelector('.qc-lc-card-icon img');
                const iconBox = card.querySelector('.qc-lc-card-icon').getBoundingClientRect();
                return {
                    title: card.querySelector('.qc-lc-card-title').textContent.trim(),
                    description: card.querySelector('.qc-lc-card-desc').textContent.trim(),
                    hasIcon: !!img,
                    iconLoaded: !!img && img.complete && img.naturalWidth > 0,
                    iconWidth: iconBox.width, iconHeight: iconBox.height,
                };
            })
            """
        )

    # ---- Section 02 — criteria ---------------------------------------------
    def criteria(self) -> list:
        """One record per eligibility row, in rendered (Display Order) order,
        with its check-mark glyph state and the glyph's position relative to
        the row — direction-agnostic, so the same query serves EN and AR."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-criterion')).map((row) => {
                const check = row.querySelector('.qc-lc-criterion-check');
                const cb = check ? check.getBoundingClientRect() : null;
                const rb = row.getBoundingClientRect();
                return {
                    text: row.textContent.trim(),
                    hasCheck: !!check,
                    checkRendered: !!cb && cb.width > 0 && cb.height > 0,
                    checkHasGlyph: !!check && (!!check.querySelector('svg') || !!check.querySelector('img')),
                    checkCenterX: cb ? cb.x + cb.width / 2 : null,
                    rowX: rb.x, rowRight: rb.right,
                };
            })
            """
        )

    # ---- Section 03 — scope groups -----------------------------------------
    def scope_group_count(self) -> int:
        return self.page.locator(self.SCOPE_GROUP).count()

    def scope_groups(self) -> list:
        """Both grouped lists with the heading text, the heading/glyph colours
        and the item texts — everything TC 138487 distinguishes them by."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-scope-group')).map((group) => {
                const head = group.querySelector('.qc-lc-scope-head');
                const glyph = group.querySelector('.qc-lc-scope-glyph');
                return {
                    className: group.className,
                    included: group.classList.contains('qc-lc-scope-group--included'),
                    excluded: group.classList.contains('qc-lc-scope-group--excluded'),
                    head: head.textContent.trim(),
                    headColor: getComputedStyle(head).color,
                    glyphColor: glyph ? getComputedStyle(glyph).color : null,
                    glyphHTML: glyph ? glyph.innerHTML.trim() : null,
                    items: Array.from(group.querySelectorAll('.qc-lc-scope-item'))
                                .map((li) => li.textContent.trim()),
                };
            })
            """
        )

    # ---- Section 04 — workflow steps ---------------------------------------
    def steps(self) -> list:
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-step')).map((step) => ({
                number: step.querySelector('.qc-lc-step-num').textContent.trim(),
                title: step.querySelector('.qc-lc-step-title').textContent.trim(),
                description: step.querySelector('.qc-lc-step-desc').textContent.trim(),
            }))
            """
        )

    # ---- Section 05 — FAQ accordion ----------------------------------------
    def faq_question_texts(self) -> list:
        return [t.strip() for t in self.page.locator(self.FAQ_QUESTION).all_inner_texts()]

    def faq_items(self) -> list:
        """Per-item collapsed/expanded state plus the geometry TC 138489
        measures and the chevron position TC 138476 checks for mirroring."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-faq-item')).map((item) => {
                const q = item.querySelector('.qc-lc-faq-q');
                const a = item.querySelector('.qc-lc-faq-a');
                const mark = item.querySelector('.qc-lc-faq-mark');
                const qb = q.getBoundingClientRect();
                const ab = a.getBoundingClientRect();
                const mb = mark ? mark.getBoundingClientRect() : null;
                return {
                    question: q.textContent.trim(),
                    expanded: q.getAttribute('aria-expanded'),
                    answerHidden: a.hasAttribute('hidden'),
                    answerDisplay: getComputedStyle(a).display,
                    answerHeight: ab.height,
                    answerVisible: a.offsetParent !== null,
                    hasMark: !!mark,
                    markCenterX: mb ? mb.x + mb.width / 2 : null,
                    questionX: qb.x, questionRight: qb.right, questionHeight: qb.height,
                    itemHeight: item.getBoundingClientRect().height,
                };
            })
            """
        )

    def faq_container_height(self) -> float:
        return self.box(self.FAQ)["height"]

    def expand_faq(self, index: int = 0) -> None:
        self.page.locator(self.FAQ_QUESTION).nth(index).click()
        self.page.locator(self.FAQ_ANSWER).nth(index).wait_for(state="visible", timeout=10000)

    def faq_answer_html(self, index: int = 0) -> str:
        return self.page.locator(self.FAQ_ANSWER).nth(index).inner_html()

    # ---- Next-step banner --------------------------------------------------
    def banner_eyebrow_text(self) -> str:
        return self.text(self.BANNER_EYEBROW).strip()

    def banner_title_text(self) -> str:
        return self.text(self.BANNER_TITLE).strip()

    def banner_body_text(self) -> str:
        return self.text(self.BANNER_BODY).strip()

    def banner_cta_text(self) -> str:
        return self.text(self.BANNER_CTA).strip()

    def banner_surface(self) -> dict:
        """Whether the banner is its own surface, and whether it sits OUTSIDE
        Section 05 — the pair TC 138492 means by 'its own contrasting surface,
        separated from Section 05'."""
        return self.page.evaluate(
            """
            () => {
                const banner = document.querySelector('.qc-lc-banner');
                const faq = document.querySelector('#qc-lc-faq');
                const bs = getComputedStyle(banner);
                const fs = getComputedStyle(faq);
                const bb = banner.getBoundingClientRect();
                return {
                    insideFaqSection: faq.contains(banner),
                    backgroundImage: bs.backgroundImage,
                    backgroundColor: bs.backgroundColor,
                    borderRadius: bs.borderRadius,
                    sectionBackgroundImage: fs.backgroundImage,
                    sectionBackgroundColor: fs.backgroundColor,
                    top: bb.top, bottom: bb.bottom,
                    faqBottom: faq.getBoundingClientRect().bottom,
                    direction: bs.direction,
                };
            }
            """
        )

    def banner_element_order(self) -> dict:
        """Vertical positions of the four banner elements, for the arrangement
        assertion (same arrangement, mirrored, in Arabic)."""
        return self.page.evaluate(
            """
            () => {
                const y = (s) => document.querySelector(s).getBoundingClientRect().y;
                const x = (s) => document.querySelector(s).getBoundingClientRect().x;
                const right = (s) => document.querySelector(s).getBoundingClientRect().right;
                return {
                    eyebrowY: y('.qc-lc-banner-eyebrow'), titleY: y('.qc-lc-banner-title'),
                    bodyY: y('.qc-lc-banner-body'), ctaY: y('.qc-lc-banner .qc-lc-cta'),
                    copyX: x('.qc-lc-banner-copy'), copyRight: right('.qc-lc-banner-copy'),
                    titleX: x('.qc-lc-banner-title'), titleRight: right('.qc-lc-banner-title'),
                    ctaX: x('.qc-lc-banner .qc-lc-cta'), ctaRight: right('.qc-lc-banner .qc-lc-cta'),
                    bannerX: x('.qc-lc-banner'), bannerRight: right('.qc-lc-banner'),
                };
            }
            """
        )

    # ---- Hero arrangement --------------------------------------------------
    def hero_element_order(self) -> dict:
        return self.page.evaluate(
            """
            () => {
                const b = (s) => document.querySelector(s).getBoundingClientRect();
                return {
                    crumbsY: b('.qc-lc-crumbs').y,
                    eyebrowY: b('.qc-lc-eyebrow').y,
                    titleY: b('h1.qc-lc-title').y,
                    descY: b('.qc-lc-hero-desc').y,
                    ctaY: b('.qc-lc-hero-ctas').y,
                    copyX: b('.qc-lc-hero-copy').x,
                    copyRight: b('.qc-lc-hero-copy').right,
                    copyWidth: b('.qc-lc-hero-copy').width,
                    descX: b('.qc-lc-hero-desc').x,
                    descWidth: b('.qc-lc-hero-desc').width,
                    eyebrowX: b('.qc-lc-eyebrow').x,
                    titleX: b('h1.qc-lc-title').x,
                    ctaX: b('.qc-lc-hero-ctas .qc-lc-cta').x,
                };
            }
            """
        )

    # ---- Request-form modal ------------------------------------------------
    def open_request_form(self) -> "LegalConsultationPage":
        """Open the request-form modal from the hero CTA.

        Rendering only — nothing here fills or submits the form. The live
        reCAPTCHA Enterprise has no agreed bypass on this project, and a real
        submission would write an untorn-down request record.
        """
        self.click(self.HERO_CTA)
        self.wait_for(self.DIALOG, state="visible", timeout=15000)
        return self

    def is_request_form_open(self) -> bool:
        return self.is_visible(self.DIALOG)

    def request_form_title_text(self) -> str:
        return self.text(self.DIALOG_TITLE).strip()

    def request_form_eyebrow_text(self) -> str:
        return self.text(self.DIALOG_EYEBROW).strip()

    def request_form_fields(self) -> list:
        """One record per `.qc-lc-field` on the form, whether visible or not,
        with its label text, its required marker, its control type and the
        control's alignment/direction. TC 138493 filters on `visible`; the
        hidden rows (the conditional 'Please specify the category' field and
        the invisible-reCAPTCHA 'Security check' row) stay in the payload so
        a test can reason about them explicitly rather than never see them."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-field')).map((field) => {
                const label = field.querySelector('.qc-lc-label');
                const control = field.querySelector('input, select, textarea');
                return {
                    label: label ? label.textContent.trim() : null,
                    labelFor: label ? label.getAttribute('for') : null,
                    labelTextAlign: label ? getComputedStyle(label).textAlign : null,
                    labelDirection: label ? getComputedStyle(label).direction : null,
                    requiredMark: !!field.querySelector('.qc-lc-req'),
                    controlTag: control ? control.tagName.toLowerCase() : null,
                    controlId: control ? control.id : null,
                    controlName: control ? control.getAttribute('name') : null,
                    controlType: control ? control.getAttribute('type') : null,
                    controlPlaceholder: control ? control.getAttribute('placeholder') : null,
                    controlDirection: control ? getComputedStyle(control).direction : null,
                    visible: field.offsetParent !== null,
                    isCaptcha: !!field.querySelector('.qc-lc-captcha'),
                };
            })
            """
        )

    def request_form_direction(self) -> str:
        return self.computed_style(self.FORM, ["direction"])["direction"]

    def captcha_state(self) -> dict:
        """The CAPTCHA is invisible reCAPTCHA Enterprise — its mount node is
        an empty div and its field wrapper is display:none, so 'is it there'
        has to be answered by the mount node plus Google's own loaded frame,
        not by the field's visibility."""
        return self.page.evaluate(
            """
            () => {
                const mount = document.querySelector('.qc-lc-captcha');
                const field = mount ? mount.closest('.qc-lc-field') : null;
                const frames = Array.from(document.querySelectorAll('iframe[src*="recaptcha"]'));
                return {
                    mountPresent: !!mount,
                    mountAttribute: mount ? mount.getAttribute('data-qc-recaptcha') : null,
                    fieldLabel: field && field.querySelector('.qc-lc-label')
                        ? field.querySelector('.qc-lc-label').textContent.trim() : null,
                    fieldVisible: !!field && field.offsetParent !== null,
                    fieldDisplay: field ? getComputedStyle(field).display : null,
                    recaptchaFrames: frames.length,
                    recaptchaLoaded: frames.some((f) => f.getBoundingClientRect().width > 0),
                };
            }
            """
        )

    def fill_request_form(
        self,
        full_name: str,
        company_name: str,
        email: str,
        phone: str,
        category_label: str,
        subject: str,
        description: str,
    ) -> "LegalConsultationPage":
        """Fill every required field of the request form.

        Not reachable on the current build — the live reCAPTCHA Enterprise has
        no agreed bypass, so `submit_request_form()` below is gated in the test
        that uses it. Written out so the submission case runs unchanged the
        moment a bypass is configured.
        """
        self.type("#qc-lc-fullName", full_name)
        self.type("#qc-lc-companyName", company_name)
        self.type("#qc-lc-email", email)
        self.type("#qc-lc-phone", phone)
        self.select_option("#qc-lc-category", label=category_label)
        self.type("#qc-lc-subject", subject)
        self.type("#qc-lc-description", description)
        return self

    def submit_request_form(self) -> "LegalConsultationPage":
        """Submit the request form and wait for the form's own alert region to
        answer. See `fill_request_form()` on reachability."""
        self.click(f"{self.DIALOG} {self.SUBMIT_BUTTON}")
        self.wait_for(".qc-lc-alert", state="visible", timeout=30000)
        return self

    def request_form_label_alignment(self) -> list:
        """Per-visible-field label/field edge geometry — the direction-agnostic
        way to check a label is start-aligned (left in LTR, right in RTL)
        rather than trusting `text-align: start`'s computed string."""
        return self.page.evaluate(
            """
            () => Array.from(document.querySelectorAll('.qc-lc-field'))
                .filter((f) => f.offsetParent !== null && f.querySelector('.qc-lc-label'))
                .map((field) => {
                    const label = field.querySelector('.qc-lc-label');
                    const fb = field.getBoundingClientRect();
                    const lb = label.getBoundingClientRect();
                    return {
                        label: label.textContent.trim(),
                        fieldX: fb.x, fieldRight: fb.right,
                        labelX: lb.x, labelRight: lb.right,
                        direction: getComputedStyle(label).direction,
                        textAlign: getComputedStyle(label).textAlign,
                    };
                })
            """
        )

    def confirmation_message(self) -> dict:
        """The post-submit alert (`div.qc-lc-alert[role=alert][aria-live=polite]`),
        which is `hidden` until the form answers. Text plus the alignment the
        Arabic case asserts on."""
        return self.page.evaluate(
            """
            () => {
                const alert = document.querySelector('.qc-lc-alert');
                if (!alert) return null;
                const s = getComputedStyle(alert);
                return {
                    text: alert.textContent.trim(),
                    hidden: alert.hasAttribute('hidden'),
                    visible: alert.offsetParent !== null,
                    direction: s.direction,
                    textAlign: s.textAlign,
                    className: alert.className,
                };
            }
            """
        )

    def faq_answer_markup(self, index: int = 0) -> dict:
        """Structural read of one FAQ answer's rendered rich text — the shape
        TC 138490 needs to tell 'rendered as markup' from 'printed as raw
        HTML' from 'stripped to plain text'."""
        return self.page.locator(self.FAQ_ANSWER).nth(index).evaluate(
            """
            (answer) => {
                const links = Array.from(answer.querySelectorAll('a[href]'));
                const lists = Array.from(answer.querySelectorAll('ul, ol'));
                return {
                    html: answer.innerHTML,
                    text: answer.textContent.trim(),
                    headings: Array.from(answer.querySelectorAll('h1,h2,h3,h4,h5,h6'))
                                   .map((h) => h.textContent.trim()),
                    listCount: lists.length,
                    listItems: lists.length
                        ? Array.from(lists[0].querySelectorAll('li')).map((li) => li.textContent.trim())
                        : [],
                    links: links.map((a) => ({ text: a.textContent.trim(), href: a.getAttribute('href') })),
                };
            }
            """
        )

    def faq_answers_markup(self) -> list:
        return [self.faq_answer_markup(i) for i in range(self.page.locator(self.FAQ_ITEM).count())]

    def submit_button_text(self) -> str:
        return self.text(f"{self.DIALOG} {self.SUBMIT_BUTTON}").strip()

    def is_submit_button_visible(self) -> bool:
        return self.is_visible(f"{self.DIALOG} {self.SUBMIT_BUTTON}")

    def category_options(self) -> list:
        return [t.strip() for t in self.page.locator(f"{self.FORM} select option").all_inner_texts()]

"""
web/pages/home_promo_banners/home_promo_banners_page.py — HomePromoBannersPage.

PBI 129368 / QC-HOME-002 "Promotional Banners / Ad Slots" — its own Home-page
section/module folder per active/standards.md's Home-page sections table. This
pass covers the 9 approved, Automation-tagged, UI-category, Web-platform
cases scoped for this batch (ADO TC 135105, 135106, 135107, 135108, 135174,
135175, 135176, 135179, 135180); Control_Panel-tagged cases for this same PBI
are explicit out-of-scope for this run and are NOT touched here (see the
sibling home_promo_banners_admin_page.py skeleton).

--- CLI-first extraction log ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --viewport 1920x1080

    -> [role] uniq=1  get_by_role("region", name="Promotional banners")
    -> [role] uniq=1  get_by_role("button", name="Previous banner")
    -> [role] uniq=1  get_by_role("button", name="Next banner")

Scoping to the region itself surfaced only the two arrow buttons:

    python tools/extract_locators.py --url .../home --scope "[aria-label=\"Promotional banners\"]"
    -> 2 candidates only (both arrows)

The harvester's SEL list (a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable]) does not include bare <img> or
unlabelled pagination-dot elements, so the banner image and the dots
container never surfaced — the documented "ambiguous/unreachable via role"
condition in automation-standards.md's Tooling-priority table, resolved the
same way every sibling component in this tree resolves it: one additional,
disclosed, scoped Playwright script (still CLI/shell, never the Playwright
MCP) that reused BasePage's own license-gate/overlay guard sequence before
reading the live DOM structurally.

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home):

    section                                                          (implicit wrapper)
      div.qc-promo-carousel[role=region][aria-label="Promotional banners"]   (CAROUSEL)
        button.qc-promo-arrow.qc-promo-arrow--prev[aria-label="Previous banner"]  (ARROW_PREV)
        div.qc-promo-viewport                                        (VIEWPORT)
          div[data-qc-promo-track]                                   (TRACK)
            div.qc-promo-slide[data-clone]        -- leading clone (infinite-loop illusion)
            div.qc-promo-slide                    -- real slide 1 (banner 1)
              a.qc-promo-link > picture > img.qc-promo-img[alt]      (SLIDE_IMAGE, relative)
            div.qc-promo-slide                    -- real slide 2 (banner 2)
            div.qc-promo-slide                    -- real slide 3 (banner 3)
            div.qc-promo-slide[data-clone]        -- trailing clone
        button.qc-promo-arrow.qc-promo-arrow--next[aria-label="Next banner"]  (ARROW_NEXT)
      div.qc-promo-dots[role=tablist][aria-label="Select banner"]     (DOTS_CONTAINER — SIBLING
        button.qc-promo-dot[role=tab][aria-label="Banner N"]           of .qc-promo-carousel,
            [data-index=N-1][aria-selected]        (DOT)               NOT nested inside it)

Every qc-promo-* class is unique on the page (count()==1 each, confirmed
live via `page.locator(sel).count()`) — plain CSS, no scoping chain needed
(unlike header_component.py's nav, there is no duplicate mega-menu here; the
Hero Banner section uses distinctly different labels — "Go to slide N" /
"Previous slide" / "Next slide" — so there is no collision).

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here):
  - CONFIRMED PRODUCT DEFECT: `.qc-promo-dots` computes `display: none` at
    every point observed (fresh load, after scrolling into view + 1.5s
    settle, after one Next-arrow click, after two Next-arrow clicks, on
    both the EN and AR homepage) even though the section has 3 active
    banners. Two real console errors accompany every load of this widget:
    "Cannot read properties of null (reading 'addEventListener')" and
    "Cannot set properties of null (setting 'hidden')" — a JS init
    exception in the promo-carousel's own script, consistent with an
    un-hide step never executing. The dots' internal STATE still tracks
    correctly despite being invisible (`aria-selected` flips 0->1->2 in
    lock-step with the track's `translateX`, confirmed live across two
    Next-arrow clicks), so this reads as a rendering/init bug, not a
    state-logic bug. A direct Playwright click on a dot (`.qc-promo-dot`)
    fails outright ("Element is not visible") even with `force=True`,
    because a `display:none` element has no dispatchable coordinates — TC
    135108's "click directly on a pagination dot" step is therefore not
    currently executable against the live site at all. Scripted per the
    case's literal expected result regardless (never routed around) — see
    test_home_promo_banners_web.py for the resulting real, honest failures.
  - The nav arrows are NOT "semi-transparent rounded squares" as TC 135105/
    106 state: computed style is `border-radius: 50%` (a full circle, not a
    square with rounded corners) and `background-color: rgb(255, 255, 255)`
    (fully opaque white — no alpha channel, i.e. alpha=1, not
    semi-transparent). They ARE correctly vertically centered on the
    image's vertical center (confirmed via bounding-box math: arrow center
    y ≈ 1081.94, image center y ≈ 1081.90) and DO mirror sides correctly in
    RTL (prev arrow lands at the right edge / x=1536, next arrow at the
    left edge / x=336, vs. prev=336/next=... on EN — confirmed live on the
    AR homepage) — both scripted as real, passing sub-checks; the
    shape/opacity mismatch is scripted per the case's literal stated
    appearance and will fail honestly.
  - The 3 real (non-clone) banners' EN alt text/images observed live do NOT
    match TC 135174/135175's example values (`promo-en.jpg` /
    "Qatar Chamber Annual Forum 2026"): the actual configured banners are
    "Verified by Qatar Chamber — stand out with trusted verification",
    "Qatar Chamber Commercial & Industrial Directory — register your
    business", and "Get Verified by Qatar Chamber", each with a real,
    non-empty `alt` attribute and a real image file
    (promo-verified-laptop-desktop*.png, promo-directory-desktop*.png,
    promo-verified-shield-desktop*.png respectively). Scripted per the
    case's real, observed live values (not the example placeholder text),
    per this batch's own instruction to prefer the live value and note the
    discrepancy here rather than hardcode a value that doesn't match
    reality.
  - The Arabic alt text is genuinely translated, non-empty, and distinct
    per slide (confirmed live, e.g. "موثّق من غرفة قطر — تميّز بتوثيق يعكس
    مصداقية عملك"), and the AR page's `<html dir="rtl">` plus the
    carousel's own computed `direction: rtl` are both confirmed live.
  - No horizontal page overflow (`document.documentElement.scrollWidth` ==
    `clientWidth`) at 375x812, 768x1024, or 1440x900, and the banner
    image's rendered width tracks its `.qc-promo-viewport` container's
    width within ~2px at all three (337/339, 582/584, 1094/1096) — genuine
    passes for TC 135179/135180.
  - No single-active-banner state exists on qcdev today (3 active banners
    live) and this batch carries no CMS/admin tooling in scope to
    publish/unpublish one (Control_Panel is explicit out-of-scope for this
    run) — TC 135176 is scripted against real Page-Object methods below but
    SKIPPED with a concrete reason in the test rather than fabricated as an
    unobserved pass.
"""

from core.web.base_page import BasePage
from config.settings import web_url


class HomePromoBannersPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    HTML_ROOT = "html"
    CAROUSEL = ".qc-promo-carousel"
    VIEWPORT = f"{CAROUSEL} >> .qc-promo-viewport"
    TRACK = "[data-qc-promo-track]"
    REAL_SLIDES = ".qc-promo-slide:not([data-clone])"
    # Relative selector — always chained off a specific slide Locator via
    # `.locator(...)`, never resolved standalone (5 slides share this class:
    # 3 real + 2 loop-clones).
    SLIDE_IMAGE = "img.qc-promo-img"
    ARROW_PREV = ".qc-promo-arrow--prev"
    ARROW_NEXT = ".qc-promo-arrow--next"
    # Sibling of .qc-promo-carousel (NOT nested inside it) — see docstring's
    # structure diagram.
    DOTS_CONTAINER = ".qc-promo-dots"
    DOT = f"{DOTS_CONTAINER} >> .qc-promo-dot"

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomePromoBannersPage":
        self.open(web_url("/home"))
        self.wait_for(self.CAROUSEL)
        return self

    def open_home_arabic(self) -> "HomePromoBannersPage":
        """Loads the homepage directly on the Arabic locale
        (`web_url("/home", locale="ar")` -> `/ar/home`) — mirrors the same
        sibling-component pattern already established for this project's
        other GLOBAL/Home-page objects (header_component.py,
        newsletter_subscription_component.py, accessibility_tools_component.py)."""
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.CAROUSEL)
        return self

    def scroll_to_section(self) -> "HomePromoBannersPage":
        self.page.locator(self.CAROUSEL).scroll_into_view_if_needed()
        return self

    # ── Page-level direction ─────────────────────────────────────────────
    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def carousel_direction(self) -> str:
        return self.page.locator(self.CAROUSEL).evaluate("el => getComputedStyle(el).direction")

    # ── Section / slide presence ─────────────────────────────────────────
    def is_carousel_visible(self) -> bool:
        return self.is_visible(self.CAROUSEL)

    def real_slide_count(self) -> int:
        return self.page.locator(self.REAL_SLIDES).count()

    def real_slide_alt_text(self, index: int) -> str:
        slide = self.page.locator(self.REAL_SLIDES).nth(index)
        return slide.locator(self.SLIDE_IMAGE).get_attribute("alt")

    def real_slide_src(self, index: int) -> str:
        slide = self.page.locator(self.REAL_SLIDES).nth(index)
        return slide.locator(self.SLIDE_IMAGE).get_attribute("src")

    def current_slide_alt_text(self) -> str:
        """Finds whichever real slide is CURRENTLY on-screen by comparing
        each slide's bounding-box x-offset to the clipping viewport's own
        x — a position-based read, independent of the broken pagination-dot
        visuals (see docstring). Used to verify the displayed banner
        actually changes on arrow navigation."""
        viewport_box = self.page.locator(self.VIEWPORT).bounding_box()
        slides = self.page.locator(self.REAL_SLIDES)
        best_i, best_dx = None, None
        for i in range(slides.count()):
            box = slides.nth(i).bounding_box()
            if not box or not viewport_box:
                continue
            dx = abs(box["x"] - viewport_box["x"])
            if best_dx is None or dx < best_dx:
                best_dx, best_i = dx, i
        if best_i is None:
            return None
        return slides.nth(best_i).locator(self.SLIDE_IMAGE).get_attribute("alt")

    # ── Nav arrows ───────────────────────────────────────────────────────
    def _arrow_locator(self, which: str) -> str:
        return self.ARROW_NEXT if which == "next" else self.ARROW_PREV

    def is_arrow_visible(self, which: str = "next") -> bool:
        return self.is_visible(self._arrow_locator(which))

    def arrow_style(self, which: str = "next") -> dict:
        loc = self.page.locator(self._arrow_locator(which))
        box = loc.bounding_box()
        style = loc.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {borderRadius: cs.borderRadius, backgroundColor: cs.backgroundColor}; }"
        )
        style["width"] = box["width"] if box else 0
        style["height"] = box["height"] if box else 0
        return style

    def is_arrow_rounded_square(self, which: str = "next") -> bool:
        """A ROUNDED SQUARE has corners rounded meaningfully less than a
        full circle — border-radius clearly under half the box's own size.
        A `border-radius: 50%` box (the live value, see docstring) is a
        full CIRCLE, not a rounded square, and this returns False for it."""
        style = self.arrow_style(which)
        br = style["borderRadius"].strip()
        if br.endswith("%"):
            return float(br.rstrip("%")) < 50
        px = float(br.replace("px", "").split(" ")[0])
        half = min(style["width"], style["height"]) / 2
        return px < half

    def is_arrow_semi_transparent(self, which: str = "next") -> bool:
        bg = self.arrow_style(which)["backgroundColor"].strip()
        if bg.startswith("rgba"):
            alpha = float(bg.rstrip(")").split(",")[-1])
            return alpha < 1
        return False  # bare "rgb(...)" carries no alpha channel -> opaque

    def is_arrow_vertically_centered_on_image(self, which: str = "next", tolerance: float = 3) -> bool:
        arrow_box = self.page.locator(self._arrow_locator(which)).bounding_box()
        image_box = self.page.locator(self.VIEWPORT).bounding_box()
        if not arrow_box or not image_box:
            return False
        arrow_center_y = arrow_box["y"] + arrow_box["height"] / 2
        image_center_y = image_box["y"] + image_box["height"] / 2
        return abs(arrow_center_y - image_center_y) <= tolerance

    def arrow_x_position(self, which: str = "next") -> float:
        box = self.page.locator(self._arrow_locator(which)).bounding_box()
        return box["x"] if box else None

    def click_next(self) -> "HomePromoBannersPage":
        self._click_arrow_and_wait_for_slide_change(self.ARROW_NEXT)
        return self

    def click_prev(self) -> "HomePromoBannersPage":
        self._click_arrow_and_wait_for_slide_change(self.ARROW_PREV)
        return self

    def _click_arrow_and_wait_for_slide_change(self, arrow_locator: str) -> None:
        """Explicit wait (no sleep): captures the track's transform BEFORE
        the click, then waits until it differs — the carousel's own
        slide-change signal, confirmed live to update on every arrow
        click (translateX(-100%) -> -200% -> -300%)."""
        old_transform = self.page.locator(self.TRACK).evaluate("el => el.style.transform")
        self.click(arrow_locator)
        self.page.wait_for_function(
            "(old) => { const el = document.querySelector('[data-qc-promo-track]'); "
            "return el && el.style.transform !== old; }",
            arg=old_transform,
        )

    # ── Pagination dots ──────────────────────────────────────────────────
    def is_dots_container_visible(self) -> bool:
        return self.is_visible(self.DOTS_CONTAINER)

    def dot_count(self) -> int:
        return self.page.locator(self.DOT).count()

    def active_dot_index(self) -> int:
        """Reads `aria-selected` across the dot buttons — confirmed live to
        track the active slide correctly even while the container itself
        renders `display:none` (see docstring)."""
        dots = self.page.locator(self.DOT)
        for i in range(dots.count()):
            if dots.nth(i).get_attribute("aria-selected") == "true":
                return i
        return -1

    def dot_shape(self, index: int) -> dict:
        dot = self.page.locator(self.DOT).nth(index)
        return dot.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {width: cs.width, height: cs.height, ariaSelected: el.getAttribute('aria-selected')}; }"
        )

    def is_dot_elongated_pill(self, index: int) -> bool:
        shape = self.dot_shape(index)
        w = float(shape["width"].replace("px", ""))
        h = float(shape["height"].replace("px", ""))
        return w > h

    def is_dot_small_circle(self, index: int) -> bool:
        shape = self.dot_shape(index)
        w = float(shape["width"].replace("px", ""))
        h = float(shape["height"].replace("px", ""))
        return abs(w - h) < 1

    def click_dot(self, index: int) -> "HomePromoBannersPage":
        """Issued exactly as TC 135108 describes ("click directly on a
        pagination dot") — never routed around the confirmed display:none
        defect (see docstring). On the live site this currently raises a
        real Playwright "element is not visible" failure, which is the
        honest result, not a framework bug."""
        self.click(f"{self.DOT} >> nth={index}")
        return self

    # ── Responsive / layout ──────────────────────────────────────────────
    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    def image_width_matches_container(self, tolerance: float = 4) -> bool:
        """Compares the (first) real slide's rendered image width against
        its own clipping viewport (`.qc-promo-viewport`) — the true image
        container, distinct from `.qc-promo-carousel` which also includes
        the two arrow buttons' own width."""
        viewport_box = self.page.locator(self.VIEWPORT).bounding_box()
        image_box = self.page.locator(self.REAL_SLIDES).first.locator(self.SLIDE_IMAGE).bounding_box()
        if not viewport_box or not image_box:
            return False
        return abs(image_box["width"] - viewport_box["width"]) <= tolerance

"""
web/pages/home_featured_event/home_featured_event_page.py — HomeFeaturedEventPage.

PBI 129382 / QC-HOME-006 "Upcoming Featured Event" — its own Home-page
section/module folder per active/standards.md's Home-page sections table.
This pass covers the 18 approved, Automation-tagged, UI-category,
Web-platform cases scoped for this run (ADO TC 135634-135645, 135646-135650,
135652 — 135651 is not part of the handed-off set). Control_Panel-tagged
cases for this same PBI (135653-135657) are scripted separately in the
sibling home_featured_event_admin_page.py / test_home_featured_event_control_panel.py.

--- CLI-first extraction log (2026-08-24, live https://qcdev.ihorizons.com) ---

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Coming Up"
    -> 0 candidates

    python tools/extract_locators.py --url https://qcdev.ihorizons.com/home --find "Event"
    -> only a "View event: Meeting business delegation of the Novgorod
       Region's government" link and the (unrelated) Business-Events-carousel
       tablist/tabs (Chamber Events/Global Events/All Events) surfaced.

The harvester's SEL list (a,button,input,select,textarea,[role],[data-testid],
[data-test],[aria-label],[contenteditable]) does not include bare <span>,
<h2>, <p>, <img>, <hr>, or <dl>/<dt>/<dd> elements with no role/label — every
piece of this section (badge, heading, description, category pills, title,
divider, date/time/location meta) is exactly that, so none of it surfaced —
the documented "ambiguous/unreachable via role" condition in
automation-standards.md's Tooling-priority table. Resolved the same way
every sibling component in this tree resolves it: one additional, disclosed,
scoped Playwright script (still CLI/shell, never the Playwright MCP) that
reused BasePage's own license-gate/overlay guard sequence, then read the
live DOM structurally and via getComputedStyle().

Real, CLI-verified structure (EN, https://qcdev.ihorizons.com/home,
1920x1080, one event pinned/active):

    section.qc-home-upcoming-event                                    (SECTION)
      div.qc-ue-inner                                                 (INNER)
        div.qc-ue-head
          div.qc-ue-head-text
            span.qc-ue-tag                    "Upcoming Events"       (TAG_BADGE)
            h2.qc-ue-heading                  "What's Coming Up"      (HEADING)
            p.qc-ue-desc                      (description copy)      (DESCRIPTION)
          a.qc-ue-viewall.qc-ue-viewall--top  "View All" + svg arrow  (VIEW_ALL_TOP)
        div.qc-ue-card                        (display:grid, 2 cols)  (CARD)
          a.qc-ue-media  [aria-label="View event: ..."]               (MEDIA)
            img.qc-ue-img                                             (IMAGE)
          div.qc-ue-details                                           (DETAILS)
            div.qc-ue-tags
              span.qc-ue-event-tag (x2, e.g. "Chamber Events","Business") (CATEGORY_TAGS)
            h3.qc-ue-title         (pinned event title)                (TITLE)
            p.qc-ue-summary        "You are cordially invited to attend" (SUMMARY)
            hr.qc-ue-divider                                           (DIVIDER)
            dl.qc-ue-meta                                              (META_LIST)
              div.qc-ue-meta-item
                span.qc-ue-meta-icon > svg (calendar)                  (META_ICON)
                span.qc-ue-meta-text
                  dt.qc-ue-meta-label[data-qc-ue-date-label] "Date"    (DATE_LABEL)
                  dd.qc-ue-meta-value[data-qc-ue-date] "19 November 2025" (DATE_VALUE)
              div.qc-ue-meta-item  (clock icon)                        ...
                dt[data-qc-ue-time-label] "Time" / dd[data-qc-ue-time] "09:30 A.M."
              div.qc-ue-meta-item.qc-ue-meta-item--location (pin icon) (LOCATION_ITEM)
                dt[data-qc-ue-location-label] "Location" /
                dd[data-qc-ue-location] "Qatar Chamber - Lusail (4th floor)"
        a.qc-ue-viewall.qc-ue-viewall--bottom "View All" + svg arrow   (VIEW_ALL_BOTTOM)

No pagination/dots element of any kind exists anywhere inside the section
(confirmed live: `section.qc-home-upcoming-event [class*="pag"],
section.qc-home-upcoming-event [class*="dot"]` -> 0 matches) with exactly
one event pinned — matches TC 135652's accepted "...or is hidden entirely"
wording literally (there is nothing to make visible at all).

Real, CLI-verified findings from this extraction pass (reported to the QA
Manager, not silently corrected here):
  - TC 135634 badge: text color #A66F43 and background #F6F0EC MATCH the
    Figma spec exactly; the border does NOT — live computed border-color is
    #E9DBD0, not the case's stated #D7BEAA (border-width 1px does match).
  - TC 135636 description: the live copy matches the case's exact quoted
    sentence (whitespace/entity differences aside — a `'` vs `'` apostrophe
    rendering, same character). The stated typography does NOT match: live
    font-size is 16px (case: 18px), line-height 24px (case: 28px), color
    #6C6C6B (case: #7C7B7B). Font-family (Cairo) and weight (400/Regular) do
    match.
  - TC 135637 CTA: background #911731, white text, border-radius 9999px,
    and a real `<svg>` classic arrow-up-right glyph (`path d="M7 17L17
    7M9 7h8v8"`) all MATCH. Padding is "12px 22px" live, not the case's
    stated "12px/18px" (horizontal padding is 22px, not 18px).
  - TC 135638 category pills: live background is #FFFFFF, not the case's
    stated #F6F6F6 (text #6C6C6B and border 1px #DEDEDD both match, pill
    shape/border-radius 9999px matches). Confirmed uniform across both
    pills ("Chamber Events" and "Business").
  - TC 135640 icon-buttons: live circles are 46x46 (`border-radius: 50%`,
    `background-color: #911731`), not exactly the case's stated 48px
    diameter — 2px off live, everything else (shape, maroon fill) matches.
  - TC 135641 date/time/location label vs value: live label is 13px, not
    the case's stated 14px, with color #6C6C6B (case: #A8A8A7) and computed
    line-height ~15.6px (case: 22px). Live value is Cairo Semibold (600,
    matches "Semibold") at 16px (matches), color #1D1D1B (case: #4A4A49),
    line-height ~20.8px (case: 24px). Font-family/weight direction of the
    label-vs-value contrast is correct; the concrete hex/line-height
    numbers largely are not.
  - TC 135642 section layout: vertical section padding is 64px (matches);
    the real horizontal "outer padding" — measured as the gap between the
    viewport edge and `.qc-ue-inner`'s own bounding box at 1920px width —
    is 336px on each side, not the case's stated 300px. The column gap
    between the image and details columns IS exactly 48px (matches).
  - TC 135643 event image: the container (`.qc-ue-media`) IS a real
    16px-radius rounded box (matches); its rendered height is 337.5px, not
    the case's stated 350px (~12.5px short).
  - TC 135644 divider: live thickness is 1px (matches); live color is
    #DEDEDD, not the case's stated #E9DBD0 — notably, #E9DBD0 is what the
    TAG_BADGE's own border actually renders as (see TC 135634 above), a
    real, reproducible value-swap between these two elements' hard-coded
    colors, not a guess.
  - TC 135645 (no event pinned -> section absent): a real event IS
    currently pinned/active on qcdev and this batch carries no CMS/admin
    tooling in scope (Control_Panel test credentials are unavailable this
    session — see the sibling admin Page Object's docstring) to unpin it —
    SKIPPED with a concrete reason below rather than fabricated as a pass,
    mirroring the sibling home_promo_banners_page.py's TC 135176 precedent.
  - TC 135646 (AR/RTL): confirmed live at https://qcdev.ihorizons.com/ar/home
    — `<html dir="rtl">`, the section's own computed `direction: rtl`,
    heading/description `text-align: start` (renders right-aligned under
    RTL), and the two-column order genuinely flips: the image column's
    bounding-box x (984) is to the RIGHT of the details column's (336) at
    1920px width — the opposite of the LTR page's left-image/right-details
    order. No horizontal overflow. A genuine, confirmed PASS.
  - TC 135647 (EN/LTR): confirmed live — `dir="ltr"`, section
    `direction: ltr`, image column left of details column (as designed). A
    genuine, confirmed PASS.
  - TC 135648 (375px mobile): confirmed live — `.qc-ue-card` computes a
    single grid column (339px) at this width; the image (`.qc-ue-media`)
    and details (`.qc-ue-details`) bounding boxes stack vertically with a
    22px gap and no overlap; no horizontal page overflow. A genuine,
    confirmed PASS.
  - TC 135649 (768px tablet): confirmed live — `.qc-ue-card` keeps 2 columns
    (352px each) rather than stacking, and there is no horizontal overflow
    or overlap at this width — satisfies the case's literal wording
    ("adapts without overlap, truncation, or horizontal scroll") even
    though it does not switch to a single column the way the 375px case
    does. A genuine, confirmed PASS.
  - TC 135650 (loading skeleton on slow 3G): confirmed live that this
    fragment is SERVER-rendered — the section's real markup (including the
    live event's data) is already present in the initial HTML response
    (checked at Playwright's `wait_until="commit"`), and no
    skeleton/shimmer/placeholder-loading class exists anywhere in the page
    at all. There is no client-side async fetch for this section to show a
    loading placeholder during. Scripted per the case's literal expected
    result (a skeleton should appear) regardless of this finding — it will
    fail honestly against the live implementation, not routed around.
"""

import re

from core.web.base_page import BasePage
from config.settings import web_url


def _rgb_to_hex(rgb: str) -> str:
    """Converts a computed 'rgb(r, g, b)' string to '#RRGGBB' (upper-case),
    for readable comparisons against Figma's hex specs."""
    nums = re.findall(r"\d+", rgb or "")
    if len(nums) < 3:
        return rgb
    return "#" + "".join(f"{int(n):02X}" for n in nums[:3])


class HomeFeaturedEventPage(BasePage):
    # ── Locators — real, CLI-verified constants (see docstring) ─────────────
    HTML_ROOT = "html"
    SECTION = "section.qc-home-upcoming-event"
    INNER = f"{SECTION} >> .qc-ue-inner"
    TAG_BADGE = f"{SECTION} >> .qc-ue-tag"
    HEADING = f"{SECTION} >> .qc-ue-heading"
    DESCRIPTION = f"{SECTION} >> .qc-ue-desc"
    VIEW_ALL_TOP = f"{SECTION} >> a.qc-ue-viewall--top"
    VIEW_ALL_BOTTOM = f"{SECTION} >> a.qc-ue-viewall--bottom"
    CARD = f"{SECTION} >> .qc-ue-card"
    MEDIA = f"{CARD} >> a.qc-ue-media"
    IMAGE = f"{MEDIA} >> img.qc-ue-img"
    DETAILS = f"{CARD} >> .qc-ue-details"
    CATEGORY_TAGS = f"{DETAILS} >> .qc-ue-event-tag"
    TITLE = f"{DETAILS} >> .qc-ue-title"
    SUMMARY = f"{DETAILS} >> .qc-ue-summary"
    DIVIDER = f"{DETAILS} >> hr.qc-ue-divider"
    META_LIST = f"{DETAILS} >> dl.qc-ue-meta"
    META_ITEMS = f"{META_LIST} >> .qc-ue-meta-item"
    # Relative selector — chained off a specific meta-item Locator via
    # `.locator(...)`, never resolved standalone (3 items share this class).
    META_ICON = ".qc-ue-meta-icon"
    DATE_LABEL = f"{META_LIST} >> [data-qc-ue-date-label]"
    DATE_VALUE = f"{META_LIST} >> [data-qc-ue-date]"
    TIME_LABEL = f"{META_LIST} >> [data-qc-ue-time-label]"
    TIME_VALUE = f"{META_LIST} >> [data-qc-ue-time]"
    LOCATION_LABEL = f"{META_LIST} >> [data-qc-ue-location-label]"
    LOCATION_VALUE = f"{META_LIST} >> [data-qc-ue-location]"
    # No pagination/dots markup exists anywhere in this section with a single
    # pinned event (confirmed live, see docstring) — kept as a real,
    # resolvable-but-absent selector so pagination_indicator_present() reads
    # an honest False rather than raising.
    PAGINATION_ANY = f'{SECTION} [class*="pag"], {SECTION} [class*="dot"]'
    # Never observed live (see docstring) — a real, intent-based selector for
    # the loading state the case describes, resolvable but absent today.
    SKELETON_ANY = f'{SECTION} [class*="skeleton"], {SECTION} [class*="shimmer"], {SECTION} [class*="placeholder-loading"]'

    # ── Navigation ───────────────────────────────────────────────────────
    def open_home(self) -> "HomeFeaturedEventPage":
        self.open(web_url("/home"))
        self.wait_for(self.SECTION)
        return self

    def open_home_arabic(self) -> "HomeFeaturedEventPage":
        self.open(web_url("/home", locale="ar"))
        self.wait_for(self.SECTION)
        return self

    def scroll_to_section(self) -> "HomeFeaturedEventPage":
        self.page.locator(self.SECTION).scroll_into_view_if_needed()
        return self

    def start_navigating_to_home_without_waiting(self) -> "HomeFeaturedEventPage":
        """Starts the Home Page navigation but returns as soon as the
        navigation COMMITS, rather than waiting for the full "load" event
        the way `open()`/`open_home()` do — needed only for TC 135650's
        "observe the section area DURING the fetch" step, where waiting for
        the page to finish loading first would defeat the point of checking
        for a transient loading placeholder. Callers must still explicitly
        `wait_for(SECTION)` afterward once they're done observing the
        transient state."""
        self.page.goto(web_url("/home"), wait_until="commit")
        return self

    # ── Section-level ────────────────────────────────────────────────────
    def is_section_visible(self) -> bool:
        return self.is_visible(self.SECTION)

    def page_direction(self) -> str:
        return self.page.locator(self.HTML_ROOT).get_attribute("dir")

    def section_direction(self) -> str:
        return self.page.locator(self.SECTION).evaluate("el => getComputedStyle(el).direction")

    def has_page_horizontal_overflow(self) -> bool:
        return self.page.evaluate(
            "() => document.documentElement.scrollWidth > document.documentElement.clientWidth"
        )

    # ── Generic computed-style helper ───────────────────────────────────
    def _style(self, locator: str, index: int = 0) -> dict:
        loc = self.page.locator(locator).nth(index)
        box = loc.bounding_box()
        style = loc.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {color: cs.color, backgroundColor: cs.backgroundColor, "
            "borderColor: cs.borderColor, borderWidth: cs.borderWidth, borderRadius: cs.borderRadius, "
            "fontFamily: cs.fontFamily, fontWeight: cs.fontWeight, fontSize: cs.fontSize, "
            "lineHeight: cs.lineHeight, padding: cs.padding}; }"
        )
        style["colorHex"] = _rgb_to_hex(style["color"])
        style["backgroundColorHex"] = _rgb_to_hex(style["backgroundColor"])
        style["borderColorHex"] = _rgb_to_hex(style["borderColor"])
        style["width"] = round(box["width"]) if box else None
        style["height"] = round(box["height"]) if box else None
        return style

    def _text(self, locator: str, index: int = 0) -> str:
        return self.page.locator(locator).nth(index).inner_text().strip()

    # ── Badge (TC 135634) ────────────────────────────────────────────────
    def badge_text(self) -> str:
        return self._text(self.TAG_BADGE)

    def badge_style(self) -> dict:
        return self._style(self.TAG_BADGE)

    # ── Heading (TC 135635) ──────────────────────────────────────────────
    def heading_text(self) -> str:
        return self._text(self.HEADING)

    def heading_style(self) -> dict:
        return self._style(self.HEADING)

    # ── Description (TC 135636) ──────────────────────────────────────────
    def description_text(self) -> str:
        return self._text(self.DESCRIPTION)

    def description_style(self) -> dict:
        return self._style(self.DESCRIPTION)

    # ── View All CTA (TC 135637) ─────────────────────────────────────────
    def cta_style(self, which: str = "top") -> dict:
        locator = self.VIEW_ALL_TOP if which == "top" else self.VIEW_ALL_BOTTOM
        return self._style(locator)

    def cta_has_icon(self, which: str = "top") -> bool:
        locator = self.VIEW_ALL_TOP if which == "top" else self.VIEW_ALL_BOTTOM
        return self.page.locator(locator).locator("svg").count() > 0

    # ── Category badges (TC 135638) ──────────────────────────────────────
    def category_tag_count(self) -> int:
        return self.page.locator(self.CATEGORY_TAGS).count()

    def category_tag_text(self, index: int) -> str:
        return self._text(self.CATEGORY_TAGS, index)

    def category_tag_style(self, index: int) -> dict:
        return self._style(self.CATEGORY_TAGS, index)

    # ── Event title (TC 135639) ──────────────────────────────────────────
    def title_text(self) -> str:
        return self._text(self.TITLE)

    def title_style(self) -> dict:
        return self._style(self.TITLE)

    # ── Date/Time/Location icon-buttons (TC 135640) ─────────────────────
    def meta_icon_style(self, index: int) -> dict:
        item = self.page.locator(self.META_ITEMS).nth(index)
        icon = item.locator(self.META_ICON)
        box = icon.bounding_box()
        style = icon.evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {backgroundColor: cs.backgroundColor, borderRadius: cs.borderRadius}; }"
        )
        style["backgroundColorHex"] = _rgb_to_hex(style["backgroundColor"])
        style["width"] = round(box["width"]) if box else None
        style["height"] = round(box["height"]) if box else None
        return style

    def is_meta_icon_circle(self, index: int) -> bool:
        style = self.meta_icon_style(index)
        return style["borderRadius"].strip() == "50%"

    # ── Date/Time/Location label + value (TC 135641) ────────────────────
    def date_label_text(self) -> str:
        return self._text(self.DATE_LABEL)

    def date_value_text(self) -> str:
        return self._text(self.DATE_VALUE)

    def time_value_text(self) -> str:
        return self._text(self.TIME_VALUE)

    def location_value_text(self) -> str:
        return self._text(self.LOCATION_VALUE)

    def date_label_style(self) -> dict:
        return self._style(self.DATE_LABEL)

    def date_value_style(self) -> dict:
        return self._style(self.DATE_VALUE)

    # ── Section layout (TC 135642) ───────────────────────────────────────
    def section_vertical_padding(self) -> dict:
        return self.page.locator(self.SECTION).evaluate(
            "el => { const cs = getComputedStyle(el); "
            "return {paddingTop: cs.paddingTop, paddingBottom: cs.paddingBottom}; }"
        )

    def section_outer_gutter(self) -> dict:
        """The visual left/right gutter between the viewport edge and
        `.qc-ue-inner`'s own content box — the case's "section's outer
        padding" as actually experienced, since `.qc-ue-inner` is a
        max-width, auto-margin-centered container rather than the section
        itself carrying the full horizontal padding (see docstring)."""
        return self.page.evaluate(
            """() => {
                const inner = document.querySelector('.qc-ue-inner');
                const box = inner.getBoundingClientRect();
                return {left: Math.round(box.x), right: Math.round(window.innerWidth - box.right)};
            }"""
        )

    def column_gap(self) -> str:
        return self.page.locator(self.CARD).evaluate(
            "el => { const cs = getComputedStyle(el); return cs.columnGap || cs.gap; }"
        )

    # ── Event image container (TC 135643) ────────────────────────────────
    def image_container_style(self) -> dict:
        box = self.page.locator(self.MEDIA).bounding_box()
        radius = self.page.locator(self.MEDIA).evaluate("el => getComputedStyle(el).borderRadius")
        return {"height": round(box["height"]) if box else None, "borderRadius": radius}

    # ── Divider (TC 135644) ──────────────────────────────────────────────
    def divider_style(self) -> dict:
        box = self.page.locator(self.DIVIDER).bounding_box()
        style = self.page.locator(self.DIVIDER).evaluate(
            "el => { const cs = getComputedStyle(el); return {backgroundColor: cs.backgroundColor}; }"
        )
        style["backgroundColorHex"] = _rgb_to_hex(style["backgroundColor"])
        style["height"] = round(box["height"]) if box else None
        return style

    # ── No-pinned-event state (TC 135645) ────────────────────────────────
    def is_section_absent(self) -> bool:
        return self.page.locator(self.SECTION).count() == 0

    # ── RTL/LTR (TC 135646 / 135647) ─────────────────────────────────────
    def media_x(self) -> float:
        box = self.page.locator(self.MEDIA).bounding_box()
        return box["x"] if box else None

    def details_x(self) -> float:
        box = self.page.locator(self.DETAILS).bounding_box()
        return box["x"] if box else None

    # ── Responsive (TC 135648 / 135649) ──────────────────────────────────
    def card_grid_template_columns(self) -> str:
        return self.page.locator(self.CARD).evaluate("el => getComputedStyle(el).gridTemplateColumns")

    def media_box(self) -> dict:
        return self.page.locator(self.MEDIA).bounding_box()

    def details_box(self) -> dict:
        return self.page.locator(self.DETAILS).bounding_box()

    def is_stacked_vertically(self) -> bool:
        """True if the details column starts at/after the media column ends
        (vertical stack), rather than sitting beside it (2-column grid)."""
        media, details = self.media_box(), self.details_box()
        if not media or not details:
            return False
        return details["y"] >= media["y"] + media["height"] - 1

    # ── Loading skeleton (TC 135650) ─────────────────────────────────────
    def is_skeleton_visible(self) -> bool:
        return self.is_visible(self.SKELETON_ANY)

    def throttle_network_slow_3g(self) -> None:
        """Emulates "Slow 3G" via a real CDP session (Chromium-only, matches
        this project's Chromium-only browser factory) — the case's literal
        "Throttle network to slow 3G" step, not skipped or approximated with
        a plain wait."""
        cdp = self.page.context.new_cdp_session(self.page)
        cdp.send(
            "Network.emulateNetworkConditions",
            {
                "offline": False,
                "downloadThroughput": 50 * 1024 / 8,   # ~50kb/s, "Slow 3G"
                "uploadThroughput": 50 * 1024 / 8,
                "latency": 400,
            },
        )

    # ── Pagination indicator (TC 135652) ─────────────────────────────────
    def pagination_indicator_present(self) -> bool:
        return self.page.locator(self.PAGINATION_ANY).count() > 0

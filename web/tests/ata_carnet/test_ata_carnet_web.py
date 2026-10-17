"""
web/tests/ata_carnet/test_ata_carnet_web.py — Web-platform cases for ADO
parent PBI 129402 (QC-SVC-003 — ATA Carnet), sourced verbatim from the
approved/injected Azure DevOps suite handed over by the QA Manager.

Scripted here (both Automation-tagged Web cases in the batch):
  - 137770 — English page renders LTR and matches the approved Figma design
             tokens (frame 3036:132072, EN desktop light).
  - 137772 — Arabic page renders RTL with the index, content and banner
             mirrored (frame 3036:132156, AR desktop light).

Nothing from the batch is skipped: 2 attempted, 2 scripted.

Batch 2 (2026-09-24, suite 137987) extends this module with:
  - 137746 / 137747 — EN->AR and AR->EN header language switch.
  - 137774 / 137775 — light and dark mode (dark via the Accessibility tools
             widget).
  - 137776 / 137777 / 137778 — desktop, tablet and mobile viewports.
Every test in this module runs in a fresh UNAUTHENTICATED context
(`{"auth": False}`): with the default cached CMS storageState, per-worker
state files carrying `GUEST_LANGUAGE_ID=ar_SA` rendered the English URL in
Arabic under xdist (the 137770 run showed 65 deviations under xdist vs 59
serially). 137770 and 137772 received only that fixture parameter and the
`svc` selector marker in batch 2 — their assertions are unchanged.

AXIS-2 MARKER NOTE (`eserv`) — deliberate, do not strip it as "not on the
case". Neither case's Azure `Tags` line carries a Service/Module tag, while
PBI 130947's Certificate of Origin cases in the same E-Services family all
carry `ESERV`. That is a known Phase-2 injection inconsistency on the Azure
side (raised with the user by the QA Manager), not a signal that these pages
are outside ESERV — `pytest.ini` already defines `eserv` as covering ATA
Carnet by name. The QA Manager ruled that both tests carry
`@pytest.mark.eserv` (same ruling given to the TIR Carnet batch), because
leaving them unselectable by service would make `pytest -m eserv` silently
incomplete, which is the worse failure. When the case tags are corrected in
Azure, this marker simply becomes mechanically derived like every other.

HOW THESE TWO TESTS ASSERT (read before changing anything here)
---------------------------------------------------------------
Both cases are token-conformance cases: one case = one Azure Test Case = one
test (Axis C), and each of their four steps carries a long list of Figma
values in its EXPECTED text. A chain of bare asserts would stop at the first
deviation and hide the rest, so each test:

  1. HARD-asserts the structural preconditions (the hero, the quick-facts
     strip, the section index, the cards, the fees table and the banner are
     actually rendered) — there is nothing to measure if a region is absent,
     so those fail fast; and
  2. records every expected-vs-actual VALUE comparison in `_TokenCheck`, then
     fails the test at the end with the complete diff.

This is not a weakened assertion: every value the case states is still
compared, and a single deviation still fails the test. It only changes WHEN
the failure is raised, so one run yields the whole design-token diff (which
is exactly what a UI bug filed off this case needs to carry).

TWO EXPECTED-VALUE READINGS, DISCLOSED RATHER THAN QUIETLY CHOSEN
-----------------------------------------------------------------
- "Hero uses 40px/300px padding": the same rendered inset is produced either
  by real padding on the full-bleed band or by a centred max-width wrapper.
  The test measures the INSET between the hero band and its content shell
  (`hero_content_inset()`), which is mechanism-agnostic and is what the
  Figma frame's padding describes visually. It is read against the shell —
  the hero's content wrapper — and not against the hero grid, because the
  shell stacks the breadcrumb row, the hero grid and the quick-facts strip,
  so a hero-to-grid measurement would report the breadcrumb row as part of
  the top padding.
- "text left-aligned" / "right-aligned": the page uses the logical
  `text-align: start`, which resolves to left in LTR and right in RTL. The
  Page Object resolves the logical value to a physical side
  (`resolved_text_align()`) so the assertion reads like the case while
  staying correct for a logical-properties implementation.

LIVE-ENVIRONMENT NOTE (confirmed 2026-09-16 against qcdev.ihorizons.com, at
the framework default 1920x1080 viewport, via tools/extract_locators.py plus
a scoped Playwright DOM/computed-style probe — see ata_carnet_page.py's
module docstring for the extraction trail): the live build's rendered values
differ from many of the Figma token values these cases state as EXPECTED
(hero gradient angle/stops, hero padding, eyebrow/description type ramp,
hero image size and shadow, quick-facts strip fill/radius, section-index
width/fill/row size/number chip/label weight, card and banner radii, fees
table border colour, banner padding and CTA padding, and the Arabic CTA
arrow edge). Those values are NOT adjusted here: per
automation-standards.md's "Result integrity" section, an automated test
asserts the QA case's expected result, and a product that does not match it
must fail visibly. The full expected-vs-live comparison was reported back to
the QA Manager with this batch so that the discrepancy is triaged as a
product bug (or a case correction) by the people who own that decision —
never silently absorbed into the test.
"""

import re

import allure
import pytest

from core.web.design_tokens import font_family_contains, hex_to_rgb
from web.pages.ata_carnet.ata_carnet_page import AtaCarnetPage

# Arabic block (incl. Arabic-Indic digits and presentation forms). Used to
# prove a string is the ARABIC value, not an untranslated English fallback.
# Latin brand tokens inside an Arabic string ("ATA Carnet") are expected and
# must not fail the check, so this asserts the PRESENCE of Arabic script
# rather than the absence of Latin characters.
_ARABIC_RE = re.compile("[" + "\u0600-\u06FF" + "\u0750-\u077F" + "\uFB50-\uFDFF" + "\uFE70-\uFEFF" + "]")


def _has_arabic(value: str) -> bool:
    return bool(_ARABIC_RE.search(value or ""))


class _TokenCheck:
    """Collects expected-vs-actual deviations for a design-token case.

    Every recorded comparison is a real assertion — the owning test ends with
    `assert not check.deviations, check.report()`, so any single deviation
    still turns the test red. Collecting them first only means one run
    surfaces the complete diff instead of the first line of it.
    """

    def __init__(self):
        self.deviations = []
        self._step = ""

    def step(self, name: str) -> None:
        self._step = name

    def _record(self, label: str, expected, actual) -> None:
        self.deviations.append(
            f"[{self._step}] {label}: expected {expected!r}, got {actual!r}"
        )

    def equals(self, label: str, actual, expected) -> None:
        if actual != expected:
            self._record(label, expected, actual)

    def px(self, label: str, actual, expected_px: float, tolerance: float = 1.0) -> None:
        """Numeric px comparison with a 1px tolerance for sub-pixel layout —
        a browser reporting 47.99px for a 48px box is a render artefact, not
        a token deviation."""
        try:
            value = float(str(actual).replace("px", ""))
        except (TypeError, ValueError):
            self._record(label, f"{expected_px}px", actual)
            return
        if abs(value - expected_px) > tolerance:
            self._record(label, f"{expected_px}px", f"{value}px")

    def contains(self, label: str, haystack: str, needle: str) -> None:
        if needle not in (haystack or ""):
            self._record(label, f"substring {needle!r}", haystack)

    def truthy(self, label: str, condition: bool, expected: str, actual) -> None:
        if not condition:
            self._record(label, expected, actual)

    def report(self) -> str:
        head = f"{len(self.deviations)} design-token deviation(s) vs. the approved Figma values:"
        return "\n".join([head, *(f"  - {d}" for d in self.deviations)])


# Figma-verified expected values, mirrored verbatim from each case's EXPECTED
# text so the numbers live in one reviewable place instead of scattered
# literals inside the test bodies.
WHITE = "rgb(255, 255, 255)"
HERO_GRADIENT_PARTS = (
    "118deg",
    "rgb(70, 7, 30)",      # rgba(70,7,30,1) — Chrome normalises alpha 1 to rgb()
    "rgb(96, 20, 48)",
    "48%",
    "rgb(145, 23, 49)",
)
HERO_RADIAL_WASH = "rgba(196, 154, 98, 0.18)"
INDEX_BG = hex_to_rgb("#F6F6F6")
INDEX_BORDER = hex_to_rgb("#EDEDED")
INDEX_LABEL_COLOR = hex_to_rgb("#6C6C6B")
CARD_BG = hex_to_rgb("#FFFFFF")
CARD_BORDER = hex_to_rgb("#EDEDED")
FEES_BORDER = hex_to_rgb("#E9DBD0")


# ---------------------------------------------------------------------------
# 137770 — English ATA Carnet page: LTR rendering + approved Figma tokens
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title(
    "English ATA Carnet page renders left-to-right and matches the approved Figma design tokens"
)
@allure.label("pbi", "129402")
@allure.label("testcase", "137770")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129402
@pytest.mark.tc_137770
@pytest.mark.svc
@pytest.mark.traceability("137770")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_ata_carnet_en_ltr_layout_and_design_tokens(page):
    """Azure Test Case 137770 (PBI 129402) — Figma frame 3036:132072
    (EN desktop light). Four steps: LTR/typography baseline, hero, quick-facts
    strip + sticky section index, Covered Items card + fees table + next-step
    banner."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()

    # -- Arrange / Act: step 1 — open the English page on a desktop viewport --
    with allure.step("Open the public ATA Carnet page in English on a desktop viewport"):
        ata.open_ata_carnet(locale="en")

    check.step("step 1 — direction & typography")
    check.equals("document dir", ata.document_direction(), "ltr")
    body_font = ata.body_font_family()
    check.truthy("body font-family is Cairo", font_family_contains(body_font), "Cairo", body_font)
    for label, locator in (
        ("hero title", AtaCarnetPage.HERO_TITLE),
        ("hero description", AtaCarnetPage.HERO_DESC),
        ("section body", AtaCarnetPage.SECTION_BODY),
        ("section index label", AtaCarnetPage.INDEX_LABEL),
        ("category card title", AtaCarnetPage.CARD_TITLE),
    ):
        check.equals(f"{label} text-align", ata.resolved_text_align(locator), "left")
        family = ata.computed_style(locator, ["fontFamily"])["fontFamily"]
        check.truthy(f"{label} font-family is Cairo", font_family_contains(family), "Cairo", family)

    # -- step 2 — the hero ----------------------------------------------------
    with allure.step("Inspect the hero"):
        assert ata.is_visible(AtaCarnetPage.HERO), "hero band did not render"
        check.step("step 2 — hero")

        inset = ata.hero_content_inset()
        check.px("hero top padding", inset["top"], 40)
        check.px("hero bottom padding", inset["bottom"], 40)
        check.px("hero left padding", inset["left"], 300)
        check.px("hero right padding", inset["right"], 300)

        layers = ata.background_layers(AtaCarnetPage.HERO)
        for part in HERO_GRADIENT_PARTS:
            check.contains("hero gradient", layers["element"], part)
        all_layers = " | ".join(v or "" for v in layers.values())
        check.contains("hero radial wash colour", all_layers, HERO_RADIAL_WASH)
        check.contains("hero radial wash", all_layers, "radial-gradient")

        eyebrow = ata.computed_style(
            AtaCarnetPage.HERO_EYEBROW, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
        )
        check.truthy("hero eyebrow font-family is Cairo",
                     font_family_contains(eyebrow["fontFamily"]), "Cairo", eyebrow["fontFamily"])
        check.equals("hero eyebrow font-weight (Cairo Regular)", eyebrow["fontWeight"], "400")
        check.px("hero eyebrow font-size", eyebrow["fontSize"], 12)
        check.px("hero eyebrow line-height", eyebrow["lineHeight"], 18)
        check.equals("hero eyebrow colour (50% white)", eyebrow["color"], "rgba(255, 255, 255, 0.5)")

        title = ata.computed_style(
            AtaCarnetPage.HERO_TITLE, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
        )
        check.truthy("hero title font-family is Cairo",
                     font_family_contains(title["fontFamily"]), "Cairo", title["fontFamily"])
        check.equals("hero title font-weight (Cairo Bold)", title["fontWeight"], "700")
        check.px("hero title font-size", title["fontSize"], 48)
        check.px("hero title line-height", title["lineHeight"], 60)
        check.equals("hero title colour", title["color"], WHITE)

        desc = ata.computed_style(
            AtaCarnetPage.HERO_DESC,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color", "maxWidth"],
        )
        check.truthy("hero description font-family is Cairo",
                     font_family_contains(desc["fontFamily"]), "Cairo", desc["fontFamily"])
        check.equals("hero description font-weight (Cairo Regular)", desc["fontWeight"], "400")
        check.px("hero description font-size", desc["fontSize"], 16)
        check.px("hero description line-height", desc["lineHeight"], 24)
        check.equals("hero description colour (70% white)", desc["color"], "rgba(255, 255, 255, 0.7)")
        check.px("hero description max-width", desc["maxWidth"], 648)

        img_box = ata.box(AtaCarnetPage.HERO_IMG)
        check.px("hero image width", img_box["width"], 424)
        check.px("hero image height", img_box["height"], 322)
        shadow = ata.computed_style(AtaCarnetPage.HERO_IMG, ["boxShadow"])["boxShadow"]
        check.contains("hero image shadow offset/blur", shadow, "0px 4px 4px")
        check.contains("hero image shadow colour", shadow, "rgba(0, 0, 0, 0.25)")

    # -- step 3 — quick-facts strip and the sticky section index --------------
    with allure.step("Inspect the quick-facts strip and the sticky section index"):
        assert ata.is_visible(AtaCarnetPage.FACTS_STRIP), "quick-facts strip did not render"
        assert ata.is_visible(AtaCarnetPage.INDEX), "sticky section index did not render"
        check.step("step 3 — quick-facts strip & section index")

        strip = ata.computed_style(
            AtaCarnetPage.FACTS_STRIP,
            ["backgroundColor", "borderTopColor", "borderLeftColor", "borderRightColor",
             "borderTopWidth", "borderTopLeftRadius", "borderTopRightRadius"],
        )
        check.equals("quick-facts container fill", strip["backgroundColor"], "rgba(29, 29, 27, 0.1)")
        check.px("quick-facts border width", strip["borderTopWidth"], 1)
        for side in ("borderTopColor", "borderLeftColor", "borderRightColor"):
            check.equals(f"quick-facts {side}", strip[side], "rgba(255, 255, 255, 0.2)")
        check.px("quick-facts top-left radius", strip["borderTopLeftRadius"], 24)
        check.px("quick-facts top-right radius", strip["borderTopRightRadius"], 24)

        tile = ata.computed_style(
            AtaCarnetPage.FACT, ["paddingTop", "paddingBottom", "paddingLeft", "paddingRight"]
        )
        check.px("quick-fact tile padding-top", tile["paddingTop"], 24)
        check.px("quick-fact tile padding-bottom", tile["paddingBottom"], 24)
        check.px("quick-fact tile padding-left", tile["paddingLeft"], 20)
        check.px("quick-fact tile padding-right", tile["paddingRight"], 20)
        icon_box = ata.box(AtaCarnetPage.FACT_ICON)
        check.px("quick-fact icon tile width", icon_box["width"], 48)
        check.px("quick-fact icon tile height", icon_box["height"], 48)

        index_box = ata.box(AtaCarnetPage.INDEX)
        check.px("section index width", index_box["width"], 312)
        index_style = ata.computed_style(
            AtaCarnetPage.INDEX,
            ["backgroundColor", "borderTopColor", "borderTopWidth", "borderRadius"],
        )
        check.equals("section index fill", index_style["backgroundColor"], INDEX_BG)
        check.equals("section index border colour", index_style["borderTopColor"], INDEX_BORDER)
        check.px("section index border width", index_style["borderTopWidth"], 1)
        check.px("section index radius", index_style["borderRadius"], 8)

        row_box = ata.box(AtaCarnetPage.INDEX_ITEM)
        check.px("section index row width", row_box["width"], 312)
        check.px("section index row height", row_box["height"], 48)

        chip_box = ata.box(AtaCarnetPage.INDEX_NUM)
        check.px("section index number chip width", chip_box["width"], 28)
        check.px("section index number chip height", chip_box["height"], 28)
        chip_fill = ata.computed_style(AtaCarnetPage.INDEX_NUM, ["backgroundColor"])["backgroundColor"]
        check.equals("section index number chip fill", chip_fill, INDEX_BORDER)

        index_label = ata.computed_style(
            AtaCarnetPage.INDEX_LABEL, ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"]
        )
        check.truthy("section index label font-family is Cairo",
                     font_family_contains(index_label["fontFamily"]), "Cairo", index_label["fontFamily"])
        check.equals("section index label weight (Cairo SemiBold)", index_label["fontWeight"], "600")
        check.px("section index label font-size", index_label["fontSize"], 14)
        check.px("section index label line-height", index_label["lineHeight"], 22)
        check.equals("section index label colour", index_label["color"], INDEX_LABEL_COLOR)

    # -- step 4 — Covered Items card, fees table, next-step banner -------------
    with allure.step("Inspect a Covered Items card, the fees table and the next-step banner"):
        assert ata.count(AtaCarnetPage.CARD) > 0, "no Covered Items category card rendered"
        assert ata.is_visible(AtaCarnetPage.FEES), "fees table did not render"
        assert ata.is_visible(AtaCarnetPage.NEXTSTEP), "next-step banner did not render"
        check.step("step 4 — cards, fees table & next-step banner")

        card = ata.computed_style(
            AtaCarnetPage.CARD,
            ["backgroundColor", "paddingTop", "paddingLeft", "borderTopWidth",
             "borderTopColor", "borderRadius"],
        )
        check.equals("category card fill", card["backgroundColor"], CARD_BG)
        check.px("category card padding", card["paddingTop"], 24)
        check.px("category card padding", card["paddingLeft"], 24)
        check.px("category card border width", card["borderTopWidth"], 1)
        check.equals("category card border colour", card["borderTopColor"], CARD_BORDER)
        check.px("category card radius", card["borderRadius"], 8)
        cards_gap = ata.computed_style(AtaCarnetPage.CARDS, ["gap"])["gap"]
        check.px("category card spacing", cards_gap.split()[0], 16)

        fees_box = ata.box(AtaCarnetPage.FEES)
        check.px("fees table width", fees_box["width"], 944)
        fees = ata.computed_style(
            AtaCarnetPage.FEES, ["borderTopColor", "borderTopWidth", "borderRadius"]
        )
        check.equals("fees table border colour", fees["borderTopColor"], FEES_BORDER)
        check.px("fees table border width", fees["borderTopWidth"], 1)
        check.px("fees table radius", fees["borderRadius"], 12)

        banner_box = ata.box(AtaCarnetPage.NEXTSTEP)
        check.px("next-step banner width", banner_box["width"], 944)
        banner = ata.computed_style(
            AtaCarnetPage.NEXTSTEP,
            ["paddingTop", "paddingBottom", "paddingLeft", "paddingRight", "borderRadius"],
        )
        for side in ("paddingTop", "paddingBottom", "paddingLeft", "paddingRight"):
            check.px(f"next-step banner {side}", banner[side], 32)
        check.px("next-step banner radius", banner["borderRadius"], 10)
        banner_bg = ata.background_layers(AtaCarnetPage.NEXTSTEP)["element"]
        check.equals("next-step banner uses the hero gradient", banner_bg,
                     ata.background_layers(AtaCarnetPage.HERO)["element"])

        banner_eyebrow = ata.computed_style(AtaCarnetPage.NEXTSTEP_EYEBROW, ["color"])["color"]
        check.equals("next-step eyebrow colour (40% white)", banner_eyebrow, "rgba(255, 255, 255, 0.4)")
        heading = ata.computed_style(
            AtaCarnetPage.NEXTSTEP_HEADING,
            ["fontFamily", "fontWeight", "fontSize", "lineHeight", "color"],
        )
        check.truthy("next-step heading font-family is Cairo",
                     font_family_contains(heading["fontFamily"]), "Cairo", heading["fontFamily"])
        check.equals("next-step heading weight (Cairo Bold)", heading["fontWeight"], "700")
        check.px("next-step heading font-size", heading["fontSize"], 18)
        check.px("next-step heading line-height", heading["lineHeight"], 28)
        check.equals("next-step heading colour", heading["color"], WHITE)

        banner_ctas = ata.cta_count(AtaCarnetPage.NEXTSTEP_CTAS)
        check.equals("next-step CTA count", banner_ctas, 2)
        for i in range(banner_ctas):
            cta = ata.cta_style(
                AtaCarnetPage.NEXTSTEP_CTAS,
                ["borderRadius", "paddingTop", "paddingBottom", "paddingLeft", "paddingRight"],
                index=i,
            )
            check.px(f"next-step CTA {i + 1} pill radius", cta["borderRadius"], 9999)
            check.px(f"next-step CTA {i + 1} padding-top", cta["paddingTop"], 12)
            check.px(f"next-step CTA {i + 1} padding-bottom", cta["paddingBottom"], 12)
            check.px(f"next-step CTA {i + 1} padding-left", cta["paddingLeft"], 18)
            check.px(f"next-step CTA {i + 1} padding-right", cta["paddingRight"], 18)

    # -- Assert ---------------------------------------------------------------
    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137772 — Arabic ATA Carnet page: RTL with index, content and banner mirrored
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("RTL / Arabic rendering")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title(
    "Arabic ATA Carnet page renders right-to-left with the index, content and banner mirrored"
)
@allure.label("pbi", "129402")
@allure.label("testcase", "137772")
@pytest.mark.web
@pytest.mark.ui
@pytest.mark.eserv
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129402
@pytest.mark.tc_137772
@pytest.mark.svc
@pytest.mark.traceability("137772")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_ata_carnet_ar_rtl_mirrored_layout(page):
    """Azure Test Case 137772 (PBI 129402) — Figma frame 3036:132156
    (AR desktop light). Four steps: RTL/typography baseline, Arabic values
    across every content slot, sticky index mirrored to the right of the
    content column, and the fees table / status badges / CTAs mirrored."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()

    # -- Arrange / Act: step 1 — open the Arabic page on a desktop viewport ---
    with allure.step("Open the public ATA Carnet page in Arabic on a desktop viewport"):
        ata.open_ata_carnet(locale="ar")

    check.step("step 1 — direction & typography")
    check.equals("document dir", ata.document_direction(), "rtl")
    body_font = ata.body_font_family()
    check.truthy("body font-family is Cairo", font_family_contains(body_font), "Cairo", body_font)
    for label, locator in (
        ("hero title", AtaCarnetPage.HERO_TITLE),
        ("hero description", AtaCarnetPage.HERO_DESC),
        ("section title", AtaCarnetPage.SECTION_TITLE),
        ("section body", AtaCarnetPage.SECTION_BODY),
        ("section index label", AtaCarnetPage.INDEX_LABEL),
        ("category card title", AtaCarnetPage.CARD_TITLE),
    ):
        check.equals(f"{label} text-align", ata.resolved_text_align(locator), "right")
        family = ata.computed_style(locator, ["fontFamily"])["fontFamily"]
        check.truthy(f"{label} font-family is Cairo", font_family_contains(family), "Cairo", family)

    # -- step 2 — every content slot carries its Arabic value ------------------
    with allure.step("Inspect the page direction and text alignment"):
        check.step("step 2 — Arabic content values")
        slots = (
            ("index label", ata.index_labels()),
            ("section badge", ata.section_badges()),
            ("section title", ata.section_titles()),
            ("section body", ata.section_bodies()),
            ("country name", ata.country_names()),
            ("country note", ata.country_notes()),
            ("fee item", ata.fee_item_texts()),
            ("status label", [ata.country_status_text()]),
        )
        for name, values in slots:
            check.truthy(f"{name}s rendered", len(values) > 0, "at least one value", values)
            for value in values:
                check.truthy(f"{name} is the Arabic value", _has_arabic(value),
                             "Arabic text", value)

    # -- step 3 — index mirrored to the right of the content column ------------
    with allure.step("Inspect the placement of the sticky index relative to the content column"):
        assert ata.is_visible(AtaCarnetPage.INDEX), "sticky section index did not render"
        assert ata.is_visible(AtaCarnetPage.CONTENT), "content column did not render"
        check.step("step 3 — mirrored index & content padding")

        index_box = ata.box(AtaCarnetPage.INDEX)
        content_box = ata.box(AtaCarnetPage.CONTENT)
        check.truthy(
            "section index sits to the RIGHT of the content column",
            index_box["x"] > content_box["x"] + content_box["width"] - 1,
            "index.x greater than the content column's right edge",
            f"index.x={index_box['x']}, content right edge="
            f"{content_box['x'] + content_box['width']}",
        )
        check.px("section index width", index_box["width"], 312)

        content_pad = ata.computed_style(
            AtaCarnetPage.CONTENT, ["paddingRight", "paddingLeft"]
        )
        check.px("content column inner padding on its RIGHT edge", content_pad["paddingRight"], 40)
        check.px("content column inner padding on its LEFT edge", content_pad["paddingLeft"], 0)

    # -- step 4 — fees table, status badges and CTAs mirrored ------------------
    with allure.step("Inspect the fees table, the Open/Closed badges and both CTAs"):
        assert ata.is_visible(AtaCarnetPage.FEES), "fees table did not render"
        assert ata.count(AtaCarnetPage.HOUR_BADGE) > 0, "no operating-hours status badge rendered"
        check.step("step 4 — mirrored fees columns, Arabic badges & CTA icons")

        head_cells = ata.fee_row_cells(head=True)
        check.equals("fees table header cell count", len(head_cells), 3)
        if len(head_cells) == 3:
            item, member, non_member = head_cells
            check.truthy(
                "fee-item column is the leading (right-most) column",
                item["x"] > member["x"],
                "fee item right of the member column",
                f"item.x={item['x']}, member.x={member['x']}",
            )
            check.truthy(
                "member column is mirrored to the right of the non-member column",
                member["x"] > non_member["x"],
                "member right of non-member",
                f"member.x={member['x']}, non-member.x={non_member['x']}",
            )

        for badge in ata.hour_badge_texts():
            check.truthy("Open/Closed badge is the Arabic status text", _has_arabic(badge),
                         "Arabic status text", badge)

        for scope_name, scope in (
            ("hero", AtaCarnetPage.HERO_CTAS),
            ("next-step banner", AtaCarnetPage.NEXTSTEP_CTAS),
        ):
            cta_count = ata.cta_count(scope)
            check.equals(f"{scope_name} CTA count", cta_count, 2)
            for i in range(cta_count):
                check.equals(
                    f"{scope_name} CTA {i + 1} arrow icon edge",
                    ata.cta_icon_side(scope, index=i),
                    "leading",
                )

    # -- Assert ---------------------------------------------------------------
    assert not check.deviations, check.report()


# ===========================================================================
# Batch 2 (2026-09-24): language switch, light/dark theme, viewports.
# Same `_TokenCheck` soft-assert pattern: every expected-vs-actual comparison
# is recorded, and the test fails once with the complete list.
# ===========================================================================

ANON = {"auth": False}
anonymous = pytest.mark.parametrize("page", [ANON], indirect=True)

EN_INDEX_LABELS = ["Overview", "Covered Items", "Eligible Items", "Member countries", "Fees", "Operating hours"]
HEADER_NAV_LIGHT = hex_to_rgb("#1D1D1B")
BODY_COPY_LIGHT = hex_to_rgb("#4A4A49")
PAGE_BG_LIGHT = hex_to_rgb("#FFFFFF")

# WCAG 2.x AA floors — the case's "legible ... at the design's contrast" states
# no number, so the measurable, published minimum is used (disclosed in the
# 137775 docstring): 4.5:1 for normal text, 3:1 for large text (>= 24px, or
# >= 18.66px at weight >= 700).
AA_NORMAL, AA_LARGE = 4.5, 3.0


def _overlap(a: dict, b: dict) -> bool:
    return (a["x"] < b["x"] + b["width"] - 1 and b["x"] < a["x"] + a["width"] - 1
            and a["y"] < b["y"] + b["height"] - 1 and b["y"] < a["y"] + a["height"] - 1)


def _inside(inner: dict, outer: dict) -> bool:
    return (inner["x"] >= outer["x"] - 1 and inner["x"] + inner["width"] <= outer["x"] + outer["width"] + 1)


def _check_no_overflow(check: _TokenCheck, ata: AtaCarnetPage) -> None:
    overflow = ata.horizontal_overflow_px()
    check.truthy("no horizontal scrollbar", overflow <= 0, "0px overflow",
                 f"{overflow}px, overflowing: {ata.overflowing_elements()}")
    clipped = ata.clipped_text_elements()
    check.truthy("no clipped content", not clipped, "no clipped text", clipped)


def _check_top_regions_no_overlap(check: _TokenCheck, ata: AtaCarnetPage) -> None:
    regions = {"hero copy": AtaCarnetPage.HERO_COPY, "hero image": AtaCarnetPage.HERO_ART,
               "quick-facts strip": AtaCarnetPage.FACTS_STRIP, "content column": AtaCarnetPage.CONTENT}
    if ata.is_displayed(AtaCarnetPage.INDEX):
        regions["section index"] = AtaCarnetPage.INDEX
    boxes = {name: ata.box(loc) for name, loc in regions.items()}
    names = list(boxes)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = boxes[names[i]], boxes[names[j]]
            check.truthy(f"{names[i]} / {names[j]} do not overlap", not _overlap(a, b), "no overlap", f"{a} vs {b}")


def _check_index_on_narrow(check: _TokenCheck, ata: AtaCarnetPage) -> None:
    """Narrow viewports: the index must collapse (compact control) or
    reposition without overlapping the content. Removed entirely, with no
    collapsed control left for section navigation, is neither — recorded
    as a deviation."""
    if ata.is_displayed(AtaCarnetPage.INDEX):
        idx, content = ata.box(AtaCarnetPage.INDEX), ata.box(AtaCarnetPage.CONTENT)
        check.truthy("section index repositioned without overlapping content", not _overlap(idx, content),
                     "no overlap", f"index={idx} content={content}")
    else:
        visible_items = sum(1 for b in ata.boxes(AtaCarnetPage.INDEX_ITEM) if b["visible"])
        col = ata.computed_style(AtaCarnetPage.INDEX_COL, ["display"])["display"]
        check.truthy("section index collapses or repositions", visible_items > 0,
                     "a collapsed or repositioned section index still offering section navigation",
                     f"index column display={col!r}; 0 of {ata.count(AtaCarnetPage.INDEX_ITEM)} index entries "
                     f"rendered and no collapsed control present (index removed entirely)")


def _check_six_sections(check: _TokenCheck, ata: AtaCarnetPage) -> None:
    sections = ata.boxes(AtaCarnetPage.SECTION)
    check.equals("content section count", len(sections), 6)
    for i, b in enumerate(sections):
        check.truthy(f"section {i + 1} rendered", b["visible"], "visible", b)


def _check_ctas_tappable(check: _TokenCheck, ata: AtaCarnetPage, viewport_width: int) -> None:
    for scope_name, scope in (("hero", AtaCarnetPage.HERO_CTAS), ("next-step banner", AtaCarnetPage.NEXTSTEP_CTAS)):
        ata.scroll_to(scope)
        boxes = ata.cta_boxes(scope)
        check.equals(f"{scope_name} CTA count", len(boxes), 2)
        for i, b in enumerate(boxes):
            check.truthy(f"{scope_name} CTA {i + 1} fully visible",
                         b["visible"] and b["x"] >= 0 and b["x"] + b["width"] <= viewport_width + 1,
                         f"inside the {viewport_width}px viewport", b)
            check.truthy(f"{scope_name} CTA {i + 1} tap target", b["height"] >= 44, ">= 44px tall", f"{b['height']}px")


# ---------------------------------------------------------------------------
# 137746 — EN -> AR language switch
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching the site language from English to Arabic renders the ATA Carnet page in Arabic")
@allure.label("pbi", "129402")
@allure.label("testcase", "137746")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.arabic
@pytest.mark.rtl
@pytest.mark.pbi_129402
@pytest.mark.tc_137746
@anonymous
def test_ata_carnet_language_switch_en_to_ar(page):
    """Azure TC 137746 | PBI 129402 — EN page -> header 'AR' toggle -> Arabic RTL,
    toggle offers 'EN', every content slot Arabic and right-aligned, index
    mirrored to the right of the content column."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()

    with allure.step("Open the English page with its six-entry index"):
        ata.open_ata_carnet(locale="en")
        check.step("step 1 — English page")
        check.equals("index entries", ata.index_labels(), EN_INDEX_LABELS)

    with allure.step("Click the 'AR' toggle in the header"):
        check.equals("toggle label before switch", ata.language_toggle_label(), "AR")
        ata.toggle_language()

    with allure.step("Arabic RTL page; toggle offers 'EN'"):
        check.step("step 3 — direction & toggle")
        check.equals("document dir", ata.document_direction(), "rtl")
        check.equals("toggle label after switch", ata.language_toggle_label(), "EN")

    with allure.step("Index, sections, fees, country notes, Open/Closed and CTAs are Arabic and right-aligned"):
        check.step("step 4 — Arabic content")
        slots = (
            ("index label", ata.index_labels()),
            ("section title", ata.section_titles()),
            ("section content", ata.texts_of(AtaCarnetPage.SECTION_RT)),
            ("fee item", ata.fee_item_texts()),
            ("country note", ata.country_notes()),
            ("Open/Closed status", ata.hour_badge_texts()),
            ("CTA label", ata.cta_texts(AtaCarnetPage.HERO_CTAS) + ata.cta_texts(AtaCarnetPage.NEXTSTEP_CTAS)),
        )
        for name, values in slots:
            check.truthy(f"{name}s rendered", len(values) > 0, "at least one value", values)
            for value in values:
                check.truthy(f"{name} is Arabic", _has_arabic(value), "Arabic text", value)
        for name, loc in (("index label", AtaCarnetPage.INDEX_LABEL), ("section title", AtaCarnetPage.SECTION_TITLE),
                          ("section content", AtaCarnetPage.SECTION_RT), ("fee item", AtaCarnetPage.FEE_ITEM)):
            check.equals(f"{name} alignment", ata.resolved_text_align(loc), "right")
        idx, content = ata.box(AtaCarnetPage.INDEX), ata.box(AtaCarnetPage.CONTENT)
        check.truthy("index mirrored to the right of the content column",
                     idx["x"] >= content["x"] + content["width"] - 1,
                     "index left edge >= content right edge",
                     f"index.x={idx['x']}, content right={content['x'] + content['width']}")

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137747 — AR -> EN language switch
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Language toggle")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching the site language from Arabic back to English restores English content and LTR")
@allure.label("pbi", "129402")
@allure.label("testcase", "137747")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129402
@pytest.mark.tc_137747
@anonymous
def test_ata_carnet_language_switch_ar_to_en(page):
    """Azure TC 137747 | PBI 129402 — AR page -> 'EN' toggle -> English LTR, index
    on the left with the six English labels. Step 2 ("note the section in
    view") is recorded as an Allure attachment; the expected result makes no
    claim about it, so it is not asserted."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()

    with allure.step("Open the Arabic page"):
        ata.open_ata_carnet(locale="ar")
        check.step("step 1 — Arabic page")
        check.equals("document dir", ata.document_direction(), "rtl")

    with allure.step("Note the section currently in view"):
        allure.attach(str(ata.section_in_view()), "section in view before switch", allure.attachment_type.TEXT)

    with allure.step("Click the 'EN' toggle in the header"):
        ata.toggle_language()

    with allure.step("English LTR, index back on the left, English index labels"):
        check.step("step 4 — English page")
        check.equals("document dir", ata.document_direction(), "ltr")
        idx, content = ata.box(AtaCarnetPage.INDEX), ata.box(AtaCarnetPage.CONTENT)
        check.truthy("index on the left of the content column", idx["x"] + idx["width"] <= content["x"] + 1,
                     "index right edge <= content left edge",
                     f"index right={idx['x'] + idx['width']}, content.x={content['x']}")
        check.equals("index labels", ata.index_labels(), EN_INDEX_LABELS)
        allure.attach(str(ata.section_in_view()), "section in view after switch", allure.attachment_type.TEXT)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137774 — light mode
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("ATA Carnet page renders correctly in light mode")
@allure.label("pbi", "129402")
@allure.label("testcase", "137774")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.pbi_129402
@pytest.mark.tc_137774
@anonymous
def test_ata_carnet_light_mode(page):
    """Azure TC 137774 | PBI 129402 — ST-20 light mode (site default theme),
    Figma frame 3036:132072. "Body copy" is read from the six content
    sections' rich text (SECTION_RT), not the hero's white description."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()
    ata.open_ata_carnet(locale="en")

    check.step("step 1 — light mode")
    check.truthy("light theme active", ata.theme() in (None, "light"), "light", ata.theme())

    with allure.step("Page background, header and section index"):
        check.step("step 3 — page, header, index")
        check.equals("page background", ata.computed_style(AtaCarnetPage.PAGE_BODY, ["backgroundColor"])["backgroundColor"],
                     PAGE_BG_LIGHT)
        check.equals("header background", ata.computed_style(AtaCarnetPage.HEADER, ["backgroundColor"])["backgroundColor"],
                     PAGE_BG_LIGHT)
        for colour in sorted({s["color"] for s in ata.computed_styles_all(AtaCarnetPage.HEADER_NAV_LINK, ["color"])}):
            check.equals("header navigation label colour", colour, HEADER_NAV_LIGHT)
        index = ata.computed_style(AtaCarnetPage.INDEX, ["backgroundColor", "borderTopWidth", "borderTopStyle",
                                                         "borderTopColor"])
        check.equals("section index fill", index["backgroundColor"], INDEX_BG)
        check.equals("section index border", f"{index['borderTopWidth']} {index['borderTopStyle']}", "1px solid")
        check.equals("section index border colour", index["borderTopColor"], INDEX_BORDER)
        for colour in sorted({s["color"] for s in ata.computed_styles_all(AtaCarnetPage.INDEX_LABEL, ["color"])}):
            check.equals("section index label colour", colour, INDEX_LABEL_COLOR)

    with allure.step("Covered Items card and fees table"):
        check.step("step 4 — card, body copy, fees table")
        card = ata.computed_style(AtaCarnetPage.CARD, ["backgroundColor", "borderTopWidth", "borderTopColor",
                                                       "borderRadius"])
        check.equals("category card fill", card["backgroundColor"], CARD_BG)
        check.px("category card border width", card["borderTopWidth"], 1)
        check.equals("category card border colour", card["borderTopColor"], CARD_BORDER)
        check.px("category card radius", card["borderRadius"], 8)
        for colour in sorted({s["color"] for s in ata.computed_styles_all(AtaCarnetPage.SECTION_RT, ["color"])}):
            check.equals("body copy colour", colour, BODY_COPY_LIGHT)
        fees = ata.computed_style(AtaCarnetPage.FEES, ["borderTopColor", "borderRadius"])
        check.equals("fees table border colour", fees["borderTopColor"], FEES_BORDER)
        check.px("fees table radius", fees["borderRadius"], 12)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137775 — dark mode
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Theme")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("ATA Carnet page renders correctly in dark mode")
@allure.label("pbi", "129402")
@allure.label("testcase", "137775")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.pbi_129402
@pytest.mark.tc_137775
@anonymous
def test_ata_carnet_dark_mode(page):
    """Azure TC 137775 | PBI 129402 — ST-21 dark mode via the Accessibility tools
    widget (prefers-color-scheme alone does not flip this site).

    The case states no hex tokens for dark mode, so it is asserted as:
      - page/header adopt a dark palette (background relative luminance < 0.2);
      - index labels, section headings and section body text meet WCAG AA
        contrast against their actual background (4.5:1, large text 3:1) —
        "the design's contrast" has no number, so the published minimum is the
        measurable floor;
      - cards and the fees table change surface/border from their light values
        and cards sit on a dark fill;
      - the hero gradient and every CTA's shape (radius, padding, size) are
        unchanged from light mode.
    NOTE: the next-step banner is painted with the hero gradient in BOTH themes
    (it is already a dark surface); there is no separate dark banner surface to
    compare, which is recorded as an Allure note rather than asserted."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()
    ata.open_ata_carnet(locale="en")
    ata.wait_for_fonts()  # light-mode CTA sizes must be read after the Cairo swap

    cta_props = ["borderRadius", "paddingTop", "paddingRight", "paddingBottom", "paddingLeft"]
    light = {
        "hero": ata.background_layers(AtaCarnetPage.HERO)["element"],
        "card": ata.computed_style(AtaCarnetPage.CARD, ["backgroundColor", "borderTopColor"]),
        "fees": ata.computed_style(AtaCarnetPage.FEES, ["borderTopColor"]),
        "cta_style": ata.computed_styles_all(AtaCarnetPage.CTA, cta_props),
        "cta_box": [(b["width"], b["height"]) for b in ata.boxes(AtaCarnetPage.CTA)],
        "banner": ata.background_layers(AtaCarnetPage.NEXTSTEP)["element"],
    }

    with allure.step("Turn dark mode on"):
        ata.enable_dark_mode()
        check.step("step 1 — dark mode")
        check.equals("dark theme active", ata.theme(), "dark")

    with allure.step("Page, header and section index adopt the dark palette and stay legible"):
        check.step("step 3 — dark palette & legibility")
        for name, loc in (("page", AtaCarnetPage.PAGE_BODY), ("header", AtaCarnetPage.HEADER)):
            bg = ata.computed_style(loc, ["backgroundColor"])["backgroundColor"]
            check.truthy(f"{name} background is dark", ata.relative_luminance(bg) < 0.2,
                         "relative luminance < 0.2", bg)
        for name, loc in (("index label", AtaCarnetPage.INDEX_LABEL), ("section heading", AtaCarnetPage.SECTION_TITLE),
                          ("section body text", AtaCarnetPage.SECTION_RT)):
            for i in range(ata.count(loc)):
                c = ata.text_contrast(loc, i)
                if c["ratio"] is None:
                    allure.attach(str(c), f"{name} {i + 1}: contrast not measurable (gradient bg)",
                                  allure.attachment_type.TEXT)
                    continue
                large = c["fontSize"] >= 24 or (c["fontSize"] >= 18.66 and c["fontWeight"] >= 700)
                need = AA_LARGE if large else AA_NORMAL
                check.truthy(f"{name} {i + 1} contrast", c["ratio"] >= need, f">= {need}:1",
                             f"{c['ratio']}:1 ({c['color']} on {c['background']}, '{c['text']}')")

    with allure.step("Cards and fees table go dark; hero gradient and CTA shapes unchanged"):
        check.step("step 4 — surfaces & unchanged elements")
        card = ata.computed_style(AtaCarnetPage.CARD, ["backgroundColor", "borderTopColor"])
        check.truthy("category card fill is dark", ata.relative_luminance(card["backgroundColor"]) < 0.2,
                     "relative luminance < 0.2", card["backgroundColor"])
        check.truthy("category card border changed from light", card["borderTopColor"] != light["card"]["borderTopColor"],
                     f"not {light['card']['borderTopColor']}", card["borderTopColor"])
        fees = ata.computed_style(AtaCarnetPage.FEES, ["borderTopColor"])
        check.truthy("fees table border changed from light", fees["borderTopColor"] != light["fees"]["borderTopColor"],
                     f"not {light['fees']['borderTopColor']}", fees["borderTopColor"])
        check.equals("hero gradient unchanged", ata.background_layers(AtaCarnetPage.HERO)["element"], light["hero"])
        check.equals("CTA shapes unchanged (radius/padding)", ata.computed_styles_all(AtaCarnetPage.CTA, cta_props),
                     light["cta_style"])
        dark_boxes = [(b["width"], b["height"]) for b in ata.boxes(AtaCarnetPage.CTA)]
        check.truthy("CTA sizes unchanged", len(dark_boxes) == len(light["cta_box"]) and all(
            abs(dw - lw) <= 1 and abs(dh - lh) <= 1 for (dw, dh), (lw, lh) in zip(dark_boxes, light["cta_box"])),
            f"{light['cta_box']} (+/-1px)", dark_boxes)
        banner = ata.background_layers(AtaCarnetPage.NEXTSTEP)["element"]
        allure.attach(f"light: {light['banner']}\ndark:  {banner}", "next-step banner surface (note)",
                      allure.attachment_type.TEXT)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137776 — desktop viewport
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("ATA Carnet page renders correctly at desktop viewport width (1920x1080)")
@allure.label("pbi", "129402")
@allure.label("testcase", "137776")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129402
@pytest.mark.tc_137776
@pytest.mark.parametrize("page", [{"viewport": (1920, 1080), "auth": False}], indirect=True)
def test_ata_carnet_desktop_viewport(page):
    """Azure TC 137776 | PBI 129402 — ENV-1 at 1920x1080."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()
    ata.open_ata_carnet(locale="en")

    with allure.step("No horizontal scrollbar, no clipping, no overlap"):
        check.step("steps 2-3 — integrity")
        _check_no_overflow(check, ata)
        _check_top_regions_no_overlap(check, ata)

    with allure.step("Scroll through the six sections to the banner; check the desktop grid"):
        check.step("step 4 — desktop layout")
        _check_six_sections(check, ata)
        ata.scroll_to(AtaCarnetPage.NEXTSTEP)
        idx, content = ata.box(AtaCarnetPage.INDEX), ata.box(AtaCarnetPage.CONTENT)
        check.px("section index width", idx["width"], 312)
        check.truthy("index on the left with the content column beside it",
                     idx["x"] + idx["width"] <= content["x"] + 1, "index right edge <= content left edge",
                     f"index right={idx['x'] + idx['width']}, content.x={content['x']}")
        facts = ata.boxes(AtaCarnetPage.FACT)
        check.equals("quick-facts tile count", len(facts), 4)
        check.truthy("quick-facts tiles in one row", len({round(b["y"]) for b in facts}) == 1,
                     "same row", [b["y"] for b in facts])
        cards = ata.boxes(AtaCarnetPage.CARD)
        check.equals("Covered Items card count", len(cards), 3)
        check.truthy("Covered Items cards in one row", len({round(b["y"]) for b in cards}) == 1,
                     "same row", [b["y"] for b in cards])
        ata.scroll_to(AtaCarnetPage.HOURS)
        hours = ata.boxes(AtaCarnetPage.HOUR)
        cols, rows = sorted({round(b["x"]) for b in hours}), sorted({round(b["y"]) for b in hours})
        check.equals("operating hours grid (columns x rows)", (len(cols), len(rows)), (2, 2))
        if len(hours) == 4 and len(cols) == 2 and len(rows) == 2:
            first = min(hours, key=lambda b: (b["y"], b["x"]))
            right = next(b for b in hours if round(b["x"]) == cols[1] and round(b["y"]) == rows[0])
            below = next(b for b in hours if round(b["x"]) == cols[0] and round(b["y"]) == rows[1])
            check.px("operating hours column gap", right["x"] - (first["x"] + first["width"]), 16)
            check.px("operating hours row gap", below["y"] - (first["y"] + first["height"]), 16)

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137777 — tablet viewport
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("ATA Carnet page renders correctly at tablet viewport width (768x1024)")
@allure.label("pbi", "129402")
@allure.label("testcase", "137777")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129402
@pytest.mark.tc_137777
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_ata_carnet_tablet_viewport(page):
    """Azure TC 137777 | PBI 129402 — ENV-2 responsive integrity at 768x1024
    (no tablet Figma frame, Assumption A-4). "Collapses or repositions" is
    read as: section navigation is still offered (compact/collapsed control
    or relocated index) without overlapping content — removing the index
    entirely is recorded as a deviation (see _check_index_on_narrow)."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()
    ata.open_ata_carnet(locale="en")

    with allure.step("No horizontal scrollbar, no clipping, no overlap"):
        check.step("steps 2-3 — integrity")
        _check_no_overflow(check, ata)
        _check_top_regions_no_overlap(check, ata)

    with allure.step("All six sections render; index collapses/repositions; cards, rows, badges legible"):
        check.step("step 4 — sections, index, legibility")
        _check_six_sections(check, ata)
        _check_index_on_narrow(check, ata)
        for i in range(ata.count(AtaCarnetPage.CARD)):
            card = ata.box(AtaCarnetPage.CARD, i)
            parts = {n: ata.child_box(AtaCarnetPage.CARD, s, i) for n, s in
                     (("icon", AtaCarnetPage.CARD_ICON), ("title", AtaCarnetPage.CARD_TITLE), ("desc", AtaCarnetPage.CARD_DESC))}
            for n, b in parts.items():
                check.truthy(f"card {i + 1} {n} inside card", _inside(b, card), "inside the card", f"{b} card={card}")
            check.truthy(f"card {i + 1} title/desc no overlap", not _overlap(parts["title"], parts["desc"]),
                         "no overlap", f"{parts['title']} vs {parts['desc']}")
        for r in range(ata.count(AtaCarnetPage.FEE_BODY_ROW)):
            cells = ata.fee_row_cells(r)
            for a in range(len(cells)):
                for b in range(a + 1, len(cells)):
                    ca = {"x": cells[a]["x"], "y": 0, "width": cells[a]["width"], "height": 1}
                    cb = {"x": cells[b]["x"], "y": 0, "width": cells[b]["width"], "height": 1}
                    check.truthy(f"fee row {r + 1} cells {a + 1}/{b + 1} no overlap", not _overlap(ca, cb),
                                 "no overlap", f"{cells[a]} vs {cells[b]}")
        for i in range(ata.count(AtaCarnetPage.HOUR)):
            check.truthy(f"hours card {i + 1} badge inside card",
                         _inside(ata.child_box(AtaCarnetPage.HOUR, AtaCarnetPage.HOUR_BADGE, i), ata.box(AtaCarnetPage.HOUR, i)),
                         "inside the card", "badge outside its card")
        check.truthy("hero image inside its container", _inside(ata.box(AtaCarnetPage.HERO_IMG), ata.box(AtaCarnetPage.HERO_ART)),
                     "inside", f"{ata.box(AtaCarnetPage.HERO_IMG)} vs {ata.box(AtaCarnetPage.HERO_ART)}")

    assert not check.deviations, check.report()


# ---------------------------------------------------------------------------
# 137778 — mobile viewport
# ---------------------------------------------------------------------------
@allure.epic("Our Services")
@allure.feature("ATA Carnet")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("ATA Carnet page renders correctly at mobile viewport width (375x812)")
@allure.label("pbi", "129402")
@allure.label("testcase", "137778")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.eserv
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129402
@pytest.mark.tc_137778
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
def test_ata_carnet_mobile_viewport(page):
    """Azure TC 137778 | PBI 129402 — ENV-3 at 375x812. Same "collapses or
    repositions" reading as 137777."""
    ata = AtaCarnetPage(page)
    check = _TokenCheck()
    ata.open_ata_carnet(locale="en")

    with allure.step("No horizontal scrollbar, no clipping, no overlap"):
        check.step("steps 2-3 — integrity")
        _check_no_overflow(check, ata)
        _check_top_regions_no_overlap(check, ata)

    with allure.step("Single column; index collapses/repositions; blocks stack; CTAs tappable"):
        check.step("step 4 — single column & stacking")
        _check_six_sections(check, ata)
        content = ata.box(AtaCarnetPage.CONTENT)
        for i, s in enumerate(ata.boxes(AtaCarnetPage.SECTION)):
            check.truthy(f"section {i + 1} in the single column", abs(s["x"] - content["x"]) <= 1
                         and abs(s["width"] - content["width"]) <= 1, "full content-column width",
                         f"{s} vs column {content}")
        _check_index_on_narrow(check, ata)
        for name, loc in (("quick-facts tile", AtaCarnetPage.FACT), ("category card", AtaCarnetPage.CARD),
                          ("country card", AtaCarnetPage.COUNTRY), ("fee row", AtaCarnetPage.FEE_ROW),
                          ("schedule card", AtaCarnetPage.HOUR)):
            boxes = [b for b in ata.boxes(loc) if b["visible"]]
            check.truthy(f"{name}s rendered", len(boxes) > 0, "at least one", 0)
            for i, b in enumerate(boxes):
                check.truthy(f"{name} {i + 1} within viewport", b["x"] >= -1 and b["x"] + b["width"] <= 376,
                             "no horizontal overflow", b)
            stacked = all(boxes[i]["y"] + boxes[i]["height"] <= boxes[i + 1]["y"] + 1 for i in range(len(boxes) - 1))
            if name != "country card":  # the country grid may legitimately wrap 2-up on a phone
                check.truthy(f"{name}s stacked", stacked, "one per row", [b["y"] for b in boxes])
        _check_ctas_tappable(check, ata, 375)

    assert not check.deviations, check.report()

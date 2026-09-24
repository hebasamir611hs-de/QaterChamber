"""
web/tests/made_in_qatar_expo/test_made_in_qatar_expo_web.py

Web-platform cases for PBI 130708 ("QC - Events - 005 - Made in Qatar Expo"),
11 approved Azure Test Cases tagged Automation (142631-142641).

Public page — every test runs in an UNAUTHENTICATED context
(`{"auth": False}` via the `page` fixture's indirect param). The cached CMS
storageState files can carry `GUEST_LANGUAGE_ID=ar_SA`, which would render
the English URL in Arabic under xdist; a fresh anonymous context per test
keeps EN and AR independent.

Copy comparison note: the live copy uses the typographic apostrophe U+2019
("Qatar’s") where the case text types a straight apostrophe; `_norm()`
treats the two as the same character (same glyph intent, not a wording
difference). Nothing else is normalised beyond whitespace.

Known product finding (asserted, not weakened): the breadcrumb "Events"
link points to `/web/qatar-chamber/chamber-events`, which serves a 404
"Coming Soon" page instead of the Events landing page
(`/web/qatar-chamber/events`) — tc_142637 is expected to FAIL until fixed.
"""

import re

import allure
import pytest

from web.pages.chamber_events.chamber_events_page import ChamberEventsPage
from web.pages.made_in_qatar_expo.made_in_qatar_expo_page import MadeInQatarExpoPage

PBI = "130708"
ARABIC = re.compile(r"[\u0600-\u06FF]")
ANON = {"auth": False}

pytestmark = [
    pytest.mark.web,
    pytest.mark.expo,
    pytest.mark.pbi_130708,
]
# Public page: anonymous context (responsive tests pass their own dict with a viewport).
anonymous = pytest.mark.parametrize("page", [ANON], indirect=True)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u2019", "'")).strip()


def _assert_ltr_left(expo: MadeInQatarExpoPage, locator: str) -> None:
    a = expo.text_alignment(locator)
    assert a["direction"] == "ltr", f"{locator}: direction {a['direction']!r}, expected 'ltr'"
    assert a["textAlign"] in ("start", "left"), f"{locator}: text-align {a['textAlign']!r}"
    assert a["leftGap"] <= 1, f"{locator}: first line starts {a['leftGap']}px from the left edge (not left-aligned)"


def _assert_arabic_rtl(expo: MadeInQatarExpoPage, locator: str) -> None:
    a = expo.text_alignment(locator)
    assert ARABIC.search(a["text"]), f"{locator}: no Arabic script in {a['text'][:80]!r}"
    assert a["direction"] == "rtl", f"{locator}: direction {a['direction']!r}, expected 'rtl'"
    assert a["textAlign"] in ("start", "right"), f"{locator}: text-align {a['textAlign']!r} with rtl"
    assert a["rightGap"] <= 1, f"{locator}: first line ends {a['rightGap']}px from the right edge (not right-aligned)"
    assert not a["clipped"] and not a["ellipsis"], f"{locator}: text is clipped/truncated"


def _assert_rtl_document(expo: MadeInQatarExpoPage) -> None:
    assert expo.document_dir() == "rtl", f"<html dir> is {expo.document_dir()!r}, expected 'rtl'"
    assert expo.root_dir() == "rtl", f"section.qc-miq dir is {expo.root_dir()!r}, expected 'rtl'"
    assert expo.explicit_ltr_descendants() == 0, "component contains dir='ltr' islands inside the RTL page"


def _overlaps(a: dict, b: dict) -> bool:
    return a["left"] < b["right"] - 1 and b["left"] < a["right"] - 1 and a["top"] < b["bottom"] - 1 and b["top"] < a["bottom"] - 1


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------

@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Hero")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("EN hero renders eyebrow, title, description and CTA left-aligned (LTR)")
@allure.label("pbi", PBI)
@allure.label("testcase", "142631")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.tc_142631
@anonymous
def test_hero_renders_en_ltr(page):
    """Azure TC 142631 | PBI 130708 — EN hero section content and LTR alignment."""
    with allure.step("Open the EN Made in Qatar Expo page"):
        expo = MadeInQatarExpoPage(page).open_page()

    with allure.step("Hero elements are visible with the approved copy"):
        for loc in (expo.HERO_EYEBROW, expo.HERO_TITLE, expo.HERO_DESC, expo.HERO_CTA):
            assert expo.is_visible(loc), f"{loc} not visible"
        assert _norm(expo.text_of(expo.HERO_EYEBROW)) == "Qatari industry. Local ambition."
        assert _norm(expo.text_of(expo.HERO_TITLE)) == "Made in Qatar Expo"
        assert len(_norm(expo.text_of(expo.HERO_DESC))) > 20, "hero description paragraph is empty"
        assert _norm(expo.text_of(expo.HERO_CTA_LABEL)) == "Visit the Official Expo Website"

    with allure.step("Hero is LTR and left-aligned"):
        assert expo.document_dir() == "ltr"
        for loc in (expo.HERO_EYEBROW, expo.HERO_TITLE, expo.HERO_DESC):
            _assert_ltr_left(expo, loc)
        cta, copy = expo.box(expo.HERO_CTA), expo.box(expo.HERO_COPY)
        assert abs(cta["left"] - copy["left"]) <= 1, f"hero CTA not left-aligned: cta.left={cta['left']} copy.left={copy['left']}"


@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Hero")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("AR hero renders RTL with Arabic eyebrow, title, description and CTA right-aligned")
@allure.label("pbi", PBI)
@allure.label("testcase", "142632")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_142632
@anonymous
def test_hero_renders_ar_rtl(page):
    """Azure TC 142632 | PBI 130708 — AR hero section RTL rendering."""
    with allure.step("Open the AR Made in Qatar Expo page"):
        expo = MadeInQatarExpoPage(page).open_page(locale="ar")

    with allure.step("Document and component are RTL with no LTR islands"):
        _assert_rtl_document(expo)

    with allure.step("Arabic hero copy is present and right-aligned"):
        for loc in (expo.HERO_EYEBROW, expo.HERO_TITLE, expo.HERO_DESC, expo.HERO_CTA_LABEL):
            assert expo.is_visible(loc), f"{loc} not visible"
            _assert_arabic_rtl(expo, loc)
        cta, copy = expo.box(expo.HERO_CTA), expo.box(expo.HERO_COPY)
        assert abs(cta["right"] - copy["right"]) <= 1, f"hero CTA not right-aligned: cta.right={cta['right']} copy.right={copy['right']}"


# ---------------------------------------------------------------------------
# About the exhibition
# ---------------------------------------------------------------------------

@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("About the exhibition")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("EN About section renders below the hero with eyebrow, title and body paragraphs")
@allure.label("pbi", PBI)
@allure.label("testcase", "142633")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.tc_142633
@anonymous
def test_about_section_renders_en(page):
    """Azure TC 142633 | PBI 130708 — EN About the exhibition section."""
    with allure.step("Open the EN page and scroll to About"):
        expo = MadeInQatarExpoPage(page).open_page()
        expo.scroll_to(expo.ABOUT)

    with allure.step("About sits below the hero"):
        assert expo.box(expo.ABOUT)["top"] >= expo.box(expo.HERO)["bottom"] - 1

    with allure.step("Eyebrow, title and body render with the approved copy"):
        assert expo.is_visible(expo.ABOUT_EYEBROW) and expo.is_visible(expo.ABOUT_TITLE)
        assert _norm(expo.text_of(expo.ABOUT_EYEBROW)) == "About the exhibition"
        assert _norm(expo.text_of(expo.ABOUT_TITLE)) == "A platform for Qatar's industrial capabilities"
        paragraphs = [p for p in expo.texts_of(expo.ABOUT_BODY_PARAGRAPH) if p]
        assert paragraphs, "About body has no rendered paragraphs"
        assert expo.is_visible(expo.ABOUT_BODY)


@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("About the exhibition")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("AR About section renders RTL, Arabic, right-aligned and untruncated")
@allure.label("pbi", PBI)
@allure.label("testcase", "142634")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_142634
@anonymous
def test_about_section_renders_ar_rtl(page):
    """Azure TC 142634 | PBI 130708 — AR About the exhibition section."""
    with allure.step("Open the AR page and scroll to About"):
        expo = MadeInQatarExpoPage(page).open_page(locale="ar")
        expo.scroll_to(expo.ABOUT)

    with allure.step("RTL document with Arabic eyebrow/title/body right-aligned"):
        _assert_rtl_document(expo)
        for loc in (expo.ABOUT_EYEBROW, expo.ABOUT_TITLE, expo.ABOUT_BODY):
            assert expo.is_visible(loc), f"{loc} not visible"
            _assert_arabic_rtl(expo, loc)
        assert expo.clipped_text_elements() == []


# ---------------------------------------------------------------------------
# Side CTA card
# ---------------------------------------------------------------------------

@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Explore Made in Qatar card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("EN side CTA card renders logo, eyebrow, heading, subtext and CTA")
@allure.label("pbi", PBI)
@allure.label("testcase", "142635")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.tc_142635
@anonymous
def test_side_card_renders_en(page):
    """Azure TC 142635 | PBI 130708 — EN Explore Made in Qatar side card."""
    with allure.step("Open the EN page and scroll to the side card"):
        expo = MadeInQatarExpoPage(page).open_page()
        expo.scroll_to(expo.CARD)

    with allure.step("Logo is visible and loaded"):
        assert expo.is_visible(expo.CARD_LOGO)
        assert expo.image_loaded(expo.CARD_LOGO), "Made in Qatar logo image did not load"
        assert "Made in Qatar" in expo.image_alt(expo.CARD_LOGO)

    with allure.step("Card copy and CTA match the approved text"):
        for loc in (expo.CARD_EYEBROW, expo.CARD_HEADING, expo.CARD_DESC, expo.CARD_CTA):
            assert expo.is_visible(loc), f"{loc} not visible"
        assert _norm(expo.text_of(expo.CARD_EYEBROW)) == "Official exhibition website"
        assert _norm(expo.text_of(expo.CARD_HEADING)) == "Explore Made in Qatar"
        assert len(_norm(expo.text_of(expo.CARD_DESC))) > 10, "card subtext is empty"
        assert _norm(expo.text_of(expo.CARD_CTA_LABEL)) == "Visit the Official Expo Website"


@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Explore Made in Qatar card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("AR side CTA card renders RTL with Arabic copy right-aligned")
@allure.label("pbi", PBI)
@allure.label("testcase", "142636")
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.tc_142636
@anonymous
def test_side_card_renders_ar_rtl(page):
    """Azure TC 142636 | PBI 130708 — AR Explore Made in Qatar side card."""
    with allure.step("Open the AR page and scroll to the side card"):
        expo = MadeInQatarExpoPage(page).open_page(locale="ar")
        expo.scroll_to(expo.CARD)

    with allure.step("RTL document with Arabic eyebrow/heading/subtext/CTA right-aligned"):
        _assert_rtl_document(expo)
        assert expo.is_visible(expo.CARD_LOGO) and expo.image_loaded(expo.CARD_LOGO)
        for loc in (expo.CARD_EYEBROW, expo.CARD_HEADING, expo.CARD_DESC, expo.CARD_CTA_LABEL):
            assert expo.is_visible(loc), f"{loc} not visible"
            _assert_arabic_rtl(expo, loc)


# ---------------------------------------------------------------------------
# Breadcrumb
# ---------------------------------------------------------------------------

@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Breadcrumb Home > Events > Made in Qatar Expo renders and its links navigate")
@allure.label("pbi", PBI)
@allure.label("testcase", "142637")
@pytest.mark.ui
@pytest.mark.tc_142637
@anonymous
def test_breadcrumb_renders_and_navigates(page):
    """Azure TC 142637 | PBI 130708 — breadcrumb trail and link navigation.

    Both link checks are collected and reported together so one broken link
    does not hide the other's result."""
    with allure.step("Open the EN page"):
        expo = MadeInQatarExpoPage(page).open_page()

    with allure.step("Breadcrumb is visible above the hero title with the full trail"):
        assert expo.is_visible(expo.BREADCRUMB)
        assert [_norm(t) for t in expo.breadcrumb_items()] == ["Home", "Events", "Made in Qatar Expo"]
        assert expo.box(expo.BREADCRUMB)["bottom"] <= expo.box(expo.HERO_TITLE)["top"] + 1

    failures = []
    with allure.step("Click 'Events' -> Events landing page"):
        events_href = expo.crumb_href("Events")
        expo.click_breadcrumb_events()
        events_path, events_title = expo.current_path(), expo.title()
        if events_path != ChamberEventsPage.LISTING_PATH or "Chamber Events" not in events_title:
            failures.append(
                f"'Events' crumb (href={events_href!r}) landed on {events_path!r} titled "
                f"{events_title!r}; expected {ChamberEventsPage.LISTING_PATH!r} ('Chamber Events')"
            )

    with allure.step("Back on the expo page, click 'Home' -> homepage"):
        expo = MadeInQatarExpoPage(page).open_page()
        expo.click_breadcrumb_home()
        home_path, home_title = expo.current_path(), expo.title()
        if home_path != expo.HOME_PATH or not home_title.startswith("Home"):
            failures.append(f"'Home' crumb landed on {home_path!r} titled {home_title!r}; expected {expo.HOME_PATH!r}")

    assert not failures, " | ".join(failures)


# ---------------------------------------------------------------------------
# CTA hover / focus
# ---------------------------------------------------------------------------

def _assert_hover_and_focus(expo: MadeInQatarExpoPage, cta: str) -> None:
    with allure.step("Hover changes the CTA's visual style"):
        before, after = expo.hover_styles(cta)
        changed = {k: (before[k], after[k]) for k in before if before[k] != after[k]}
        allure.attach(str({"before": before, "after": after}), "hover styles", allure.attachment_type.TEXT)
        assert changed, f"no hover style change on {cta}: {before}"

    with allure.step("Keyboard Tab focus shows a visible focus indicator"):
        before, after, focus_visible = expo.keyboard_focus_styles(cta)
        allure.attach(str({"before": before, "after": after}), "focus styles", allure.attachment_type.TEXT)
        assert focus_visible, f"{cta} is not :focus-visible after keyboard Tab"
        outline = after["outline-style"] not in ("none", "") and after["outline-width"] not in ("0px", "")
        ring = after["box-shadow"] not in ("none", "") and after["box-shadow"] != before["box-shadow"]
        assert outline or ring, f"no visible focus outline/ring on {cta}: {after}"


@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Hero")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hero CTA shows a hover style and a keyboard focus outline")
@allure.label("pbi", PBI)
@allure.label("testcase", "142638")
@pytest.mark.ui
@pytest.mark.tc_142638
@anonymous
def test_hero_cta_hover_and_focus(page):
    """Azure TC 142638 | PBI 130708 — hero CTA hover + keyboard focus states."""
    expo = MadeInQatarExpoPage(page).open_page()
    _assert_hover_and_focus(expo, expo.HERO_CTA)


@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Explore Made in Qatar card")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Side card CTA shows a hover style and a keyboard focus outline")
@allure.label("pbi", PBI)
@allure.label("testcase", "142639")
@pytest.mark.ui
@pytest.mark.tc_142639
@anonymous
def test_side_card_cta_hover_and_focus(page):
    """Azure TC 142639 | PBI 130708 — side card CTA hover + keyboard focus states."""
    expo = MadeInQatarExpoPage(page).open_page()
    _assert_hover_and_focus(expo, expo.CARD_CTA)


# ---------------------------------------------------------------------------
# Responsive
# ---------------------------------------------------------------------------

@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("375x812: sections stack, no overflow/truncation, CTAs full-width and tappable")
@allure.label("pbi", PBI)
@allure.label("testcase", "142640")
@pytest.mark.compatibility
@pytest.mark.tc_142640
@pytest.mark.parametrize("page", [{"viewport": (375, 812), "auth": False}], indirect=True)
def test_mobile_375_layout(page):
    """Azure TC 142640 | PBI 130708 — mobile 375x812 layout."""
    with allure.step("Open the EN page at 375x812"):
        expo = MadeInQatarExpoPage(page).open_page()

    with allure.step("No horizontal scroll and no clipped text"):
        assert expo.horizontal_overflow_px() <= 0, f"horizontal overflow of {expo.horizontal_overflow_px()}px"
        assert expo.clipped_text_elements() == []

    with allure.step("Sections stack vertically without overlap"):
        copy, art = expo.box(expo.HERO_COPY), expo.box(expo.HERO_ART)
        hero, about, card = expo.box(expo.HERO), expo.box(expo.ABOUT), expo.box(expo.CARD)
        assert art["top"] >= copy["bottom"] - 1, "hero illustration is not stacked below the hero copy"
        assert about["top"] >= hero["bottom"] - 1, "About is not stacked below the hero"
        assert card["top"] >= about["bottom"] - 1, "side card is not stacked below About"
        for name, a, b in (("copy/art", copy, art), ("about/card", about, card), ("hero/about", hero, about)):
            assert not _overlaps(a, b), f"{name} overlap: {a} vs {b}"

    with allure.step("CTA buttons span their column and are tappable"):
        for cta, column in ((expo.HERO_CTA, expo.HERO_COPY), (expo.CARD_CTA, expo.CARD_COPY)):
            c, col = expo.box(cta), expo.box(column)
            assert c["width"] >= col["width"] - 2, f"{cta} is {c['width']}px wide in a {col['width']}px column (not full-width)"
            assert c["height"] >= 44, f"{cta} is only {c['height']}px tall (tap target < 44px)"


@allure.epic("Events")
@allure.feature("Made in Qatar Expo")
@allure.story("Responsive layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("768x1024: layout reflows without overlap/clipping and the side card repositions")
@allure.label("pbi", PBI)
@allure.label("testcase", "142641")
@pytest.mark.compatibility
@pytest.mark.tc_142641
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_tablet_768_layout(page):
    """Azure TC 142641 | PBI 130708 — tablet 768x1024 layout and card breakpoint."""
    with allure.step("Open the EN page at 768x1024"):
        expo = MadeInQatarExpoPage(page).open_page()

    with allure.step("No horizontal scroll, clipping or overlap"):
        assert expo.horizontal_overflow_px() <= 0, f"horizontal overflow of {expo.horizontal_overflow_px()}px"
        assert expo.clipped_text_elements() == []
        copy, art = expo.box(expo.HERO_COPY), expo.box(expo.HERO_ART)
        about, card = expo.box(expo.ABOUT), expo.box(expo.CARD)
        assert not _overlaps(copy, art), f"hero copy/art overlap: {copy} vs {art}"
        assert not _overlaps(about, card), f"about/card overlap: {about} vs {card}"

    with allure.step("At tablet width the side card sits below About"):
        tablet_card = card
        assert tablet_card["top"] >= about["bottom"] - 1, "side card not below About at 768px"

    with allure.step("At desktop width the side card moves beside About"):
        expo.set_viewport(1920, 1080)
        about, card = expo.box(expo.ABOUT), expo.box(expo.CARD)
        assert card["left"] >= about["right"] - 1 and card["top"] < about["bottom"], (
            f"side card did not reposition beside About at 1920px: about={about} card={card}"
        )

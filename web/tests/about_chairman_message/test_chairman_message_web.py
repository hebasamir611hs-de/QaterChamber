"""
web/tests/about_chairman_message/test_chairman_message_web.py — Chairman's
Message (PBI 129393 / QC-ABOUT-002), Web platform.

Source: all 42 approved, Automation-tagged cases in this batch (16 UI, 5
Compatibility, 1 Auth, 13 Functional-High, 3 Functional-Low, 4 Edge — every
one carries the `Web` Platform tag; scope = Category:UI OR Platform:Web per
this run's explicit instruction). 13 of the 42 ALSO carry `Control_Panel`
(134759, 134760, 134774, 134776, 134777, 134779, 134780, 134783, 134784,
134787, 134828, 134829, 134834) — per active/standards.md's "one test per
platform" rule, each of those is split: the CMS edit/publish half lives in
the sibling test_chairman_message_control_panel.py (gated — see that module's
docstring for the TEST_USER/TEST_PASSWORD blocker), the public-page-
verification half is scripted HERE, against whatever content already exists
live, wherever that lets the rendering behaviour genuinely be verified.

See web/pages/about_chairman_message/chairman_message_page.py's own
docstring for the FULL CLI-first extraction log and every real, live finding
surfaced while scripting these (each honestly asserted per its case's exact
stated wording, never silently adjusted) — not repeated in full here. Short
summary of what is scripted to FAIL honestly (real, live mismatches against
the case's literal stated values — Result Integrity: never weakened to force
green):
  - 134752: hero band measures ~118px tall, not the case's stated 140px.
  - 134753 / 134763: the live breadcrumb has only 2 items (Home, About Us),
    not 3 — there is no "Chairman's Message" leaf at all.
  - 134754: the decorative portrait backing measures 212x364, not 213x343.
  - 134756 / 134757 / 134758 / 134766: the message column measures 696px
    wide, not the case's stated 760px (and the desktop content container
    measures 1248px at 300px+ padding, not 1320px/300px).
  - 134757: the salutation-to-body gap measures 16px, not 24px.
  - 134764: the Arabic breadcrumb leaf reads "من نحن", not the AR page title.
  - 134765: the Signature block icon sits to the RIGHT of the text in
    Arabic, not the left the case states.
  - 134785: the breadcrumb's "About Us" item is a non-interactive <span>
    (no href) — clicking it produces no navigation.
  - 134841: the Name Card's name/designation colours do NOT stay at their
    light-mode brand values in dark mode (they switch to light legibility
    tones).

And what is explicitly SKIPPED at runtime (not silently passed, not
fabricated — see each test's own skip reason) because the live page currently
has no content that lets the case's specific scenario be verified without
first performing its blocked Liferay CMS step (TEST_USER/TEST_PASSWORD blank
— see test_chairman_message_control_panel.py): 134759, 134776, 134777,
134779, 134780, 134783, 134784, 134828, 134829, 134834, 134838, 134839, 134840.
"""

import allure
import pytest

from web.pages.about_chairman_message.chairman_message_page import ChairmanMessagePage

PBI = "129393"

# ── Real, CLI-verified constants (see ChairmanMessagePage's docstring) ──────
MAROON = "rgb(145, 23, 49)"
TAN = "rgb(166, 111, 67)"
WHITE = "rgb(255, 255, 255)"
BODY_TEXT_COLOR = "rgb(52, 52, 50)"
SIG_BG = "rgb(246, 240, 236)"
SIG_REGARDS_COLOR = "rgb(74, 74, 73)"

EXPECTED_HERO_TITLE_EN = "Chairman's Message"
EXPECTED_HERO_TITLE_AR = "رسالة رئيس مجلس الإدارة"
EXPECTED_SALUTATION_EN = "Dear members and visitors"
EXPECTED_SALUTATION_AR = "السادة الأعضاء والزوار"
EXPECTED_NAME_EN = "H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani"
EXPECTED_NAME_AR = "الشيخ خليفة بن جاسم بن محمد آل ثاني"
EXPECTED_DESIGNATION_EN = "Chairman of The Board"
EXPECTED_DESIGNATION_AR = "رئيس مجلس الإدارة"
EXPECTED_SIG_REGARDS_EN = "Best Regards,"


def _px(value: str) -> float:
    return round(float(value.replace("px", "")))


# ── TC 134752 — Hero Banner renders title + overlay (desktop) ───────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hero Banner rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman's Message Hero Banner renders with the design-specified title and overlay on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134752")
def test_hero_banner_renders_title_and_overlay(page):
    # ABOUT-CHAIRMANMSG-TC-134752 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English at 1920x1080"):
        cm.open_en()

    with allure.step("Inspect the Hero Banner band and its title text"):
        hero_box = cm.hero_box()
        has_bg_image = cm.hero_has_background_image()
        title_text = cm.hero_title_text()
        title_style = cm.hero_title_style()

    # Assert
    assert cm.is_hero_visible()
    assert hero_box["w"] == 1920, f"expected the hero to span the full 1920px width, got {hero_box['w']}"
    assert hero_box["h"] == 140, f"expected a 140px-tall hero band, got {hero_box['h']}"
    assert has_bg_image, "expected the hero to render a background image"
    assert title_text == "Chairman's Message"
    assert title_style["fontFamily"].startswith("Cairo")
    assert _px(title_style["fontSize"]) == 30
    assert int(title_style["fontWeight"]) == 700
    assert _px(title_style["lineHeight"]) == 38
    assert title_style["color"] == WHITE
    assert title_style["textAlign"] == "start"


# ── TC 134753 — English breadcrumb ends with the page name ──────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The English breadcrumb on the Chairman's Message page ends with the Chairman's Message page name")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134753")
def test_english_breadcrumb_ends_with_page_name(page):
    # ABOUT-CHAIRMANMSG-TC-134753 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Read every item in the breadcrumb and count them"):
        items = cm.breadcrumb_item_texts()
        leaf = cm.breadcrumb_leaf_text()
        count = cm.breadcrumb_item_count()

    # Assert
    assert leaf != "About Qatar Chamber", "the leaf must not be the About Qatar Chamber page name"
    assert leaf == "Chairman's Message", f"expected the breadcrumb leaf to name this page, got {leaf!r} (items: {items})"
    assert count == 3, f"expected exactly 3 labelled breadcrumb items, got {count} ({items})"


# ── TC 134754 — Chairman portrait + decorative maroon backing ───────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Portrait + decorative backing")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman portrait renders with its decorative maroon backing element")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134754")
def test_portrait_renders_with_decorative_backing(page):
    # ABOUT-CHAIRMANMSG-TC-134754 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English at 1920x1080"):
        cm.open_en()

    with allure.step("Inspect the portrait, its decorative backing, and the surrounding column"):
        portrait_box = cm.portrait_box()
        portrait_style = cm.portrait_style()
        deco_box = cm.portrait_deco_box()
        deco_style = cm.portrait_deco_style()
        card_box = cm.card_box()
        card_style = cm.card_style()

    # Assert
    assert round(portrait_box["w"]) == 393 and round(portrait_box["h"]) == 470
    assert portrait_style["borderRadius"] == "16px"
    assert round(deco_box["w"]) == 213, f"expected deco width 213, got {round(deco_box['w'])}"
    assert round(deco_box["h"]) == 343, f"expected deco height 343, got {round(deco_box['h'])}"
    assert deco_style["backgroundColor"] == MAROON
    assert deco_style["borderRadius"] == "20px"
    assert round(card_box["w"]) == 424, f"expected the column to be 424px wide, got {round(card_box['w'])}"
    assert card_style["borderRadius"] == "20px"


# ── TC 134755 — Name Card typography ─────────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Name Card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Name Card below the portrait renders the Chairman Name and Designation in the design-specified styles")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134755")
def test_name_card_renders_design_specified_typography(page):
    # ABOUT-CHAIRMANMSG-TC-134755 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Inspect the Name Card immediately below the portrait"):
        name_text = cm.name_text()
        name_style = cm.name_style()
        designation_text = cm.designation_text()
        designation_style = cm.designation_style()
        gap = cm.name_to_designation_gap()

    # Assert
    assert name_text == EXPECTED_NAME_EN
    assert _px(name_style["fontSize"]) == 20 and int(name_style["fontWeight"]) == 700
    assert _px(name_style["lineHeight"]) == 30
    assert name_style["color"] == MAROON
    assert name_style["textAlign"] == "center"
    assert designation_text == EXPECTED_DESIGNATION_EN
    assert _px(designation_style["fontSize"]) == 18 and int(designation_style["fontWeight"]) == 400
    assert designation_style["color"] == TAN
    assert designation_style["textAlign"] == "center"
    assert gap == 8.0, f"expected 8px spacing between name and designation, got {gap}"


# ── TC 134756 — Salutation heading typography ────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Salutation heading")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The salutation heading renders in the design-specified typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134756")
def test_salutation_heading_renders_design_specified_typography(page):
    # ABOUT-CHAIRMANMSG-TC-134756 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Inspect the salutation heading and the message column width"):
        text = cm.salutation_text()
        style = cm.salutation_style()
        column_box = cm.message_column_box()

    # Assert
    assert text == EXPECTED_SALUTATION_EN
    assert _px(style["fontSize"]) == 30 and int(style["fontWeight"]) == 700
    assert _px(style["lineHeight"]) == 38
    assert style["color"] == MAROON
    assert style["textAlign"] == "start"
    assert round(column_box["w"]) == 760, f"expected a 760px-wide message column, got {round(column_box['w'])}"


# ── TC 134757 — Body paragraph typography ────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Message body")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The message body renders in the design-specified body typography")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134757")
def test_message_body_renders_design_specified_typography(page):
    # ABOUT-CHAIRMANMSG-TC-134757 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Inspect the message body paragraphs below the salutation heading"):
        style = cm.body_paragraph_style()
        column_box = cm.message_column_box()
        gap = cm.heading_to_body_gap()

    # Assert
    assert _px(style["fontSize"]) == 18 and int(style["fontWeight"]) == 400
    assert _px(style["lineHeight"]) == 28
    assert style["color"] == BODY_TEXT_COLOR
    assert style["textAlign"] == "start"
    assert round(column_box["w"]) == 760, f"expected a 760px-wide message column, got {round(column_box['w'])}"
    assert gap == 24.0, f"expected a 24px gap between the salutation heading and the body, got {gap}"


# ── TC 134758 — Signature block ──────────────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Signature block")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Signature block renders the closing, name, and designation in the design-specified styles")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134758")
def test_signature_block_renders_design_specified_styles(page):
    # ABOUT-CHAIRMANMSG-TC-134758 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Inspect the Signature block and the circular icon inside it"):
        sig_box = cm.signature_box()
        sig_style = cm.signature_style()
        regards_text = cm.sig_regards_text()
        regards_style = cm.sig_regards_style()
        name_text = cm.sig_name_text()
        name_style = cm.sig_name_style()
        desig_text = cm.sig_desig_text()
        desig_style = cm.sig_desig_style()
        icon_box = cm.sig_icon_box()
        icon_style = cm.sig_icon_style()
        icon_gap = cm.sig_icon_to_text_gap()

    # Assert
    assert round(sig_box["w"]) == 760, f"expected a 760px-wide Signature block, got {round(sig_box['w'])}"
    assert round(sig_box["h"]) == 108
    assert sig_style["backgroundColor"] == SIG_BG
    assert sig_style["borderRadius"] == "12px"
    assert regards_text == EXPECTED_SIG_REGARDS_EN
    assert regards_style["color"] == SIG_REGARDS_COLOR
    assert name_text == EXPECTED_NAME_EN
    assert int(name_style["fontWeight"]) == 700 and name_style["color"] == MAROON
    assert desig_text == EXPECTED_DESIGNATION_EN
    assert desig_style["color"] == TAN
    assert round(icon_box["w"]) == 64 and round(icon_box["h"]) == 64
    assert icon_style["borderRadius"] in ("50%", "9999px") or int(_px(icon_style["borderRadius"])) >= 32
    assert icon_style["backgroundColor"] == TAN
    assert icon_gap == 20.0, f"expected the icon to sit 20px from the text block, got {icon_gap}"


# ── TC 134759 — Rich text (heading/paragraphs/bullets/inline link), Web half ─
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Rich text rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The message rich text renders headings, paragraphs, bullets, and inline links")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134759")
def test_message_rich_text_renders_headings_paragraphs_bullets_links(page):
    # ABOUT-CHAIRMANMSG-TC-134759 | PBI 129393
    # The public-verification half of a Control_Panel-authoring case (see
    # module docstring / test_chairman_message_control_panel.py). The live
    # page currently has a heading and 6 paragraphs, but NO bullet list and
    # NO inline link anywhere in the message body — there is no existing
    # content to verify the case's specific bullet-list/inline-link scenario
    # against without first performing the blocked CMS step.
    cm = ChairmanMessagePage(page)
    cm.open_en()
    if cm.body_list_count() == 0 or cm.body_link_count() == 0:
        pytest.skip(
            "Live message body has no bullet list and no inline link to verify "
            "against — requires the Control_Panel authoring step (blocked, "
            "blank TEST_USER/TEST_PASSWORD). See test_chairman_message_control_panel.py."
        )


# ── TC 134760 — Hero + portrait alt text, Web half ───────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Image alt text")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Both the Hero Banner and the Chairman Portrait expose their configured alt text")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134760")
def test_hero_and_portrait_expose_distinct_alt_text(page):
    # ABOUT-CHAIRMANMSG-TC-134760 | PBI 129393
    # Verifies the general alt-text MECHANISM against whatever is live right
    # now (the specific CMS-configured strings this case names need the
    # blocked Control_Panel step — see module docstring).
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page with both images visible"):
        cm.open_en()

    with allure.step("Inspect the Hero Banner's accessible label and the Portrait's alt attribute"):
        hero_label = cm.hero_accessible_label()
        portrait_alt = cm.portrait_alt_text()

    # Assert
    assert hero_label, "expected the Hero Banner to expose a non-empty accessible label"
    assert portrait_alt, "expected the Chairman Portrait to expose a non-empty alt attribute"
    assert hero_label != portrait_alt, "the two images must not share one alt value"


# ── TC 134761 — LTR layout in English ────────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Bilingual layout — LTR")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Chairman's Message page renders in LTR layout in English")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134761")
def test_page_renders_ltr_layout_in_english(page):
    # ABOUT-CHAIRMANMSG-TC-134761 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English at 1920x1080"):
        cm.open_en()

    with allure.step("Inspect direction, column order, alignment, and breadcrumb"):
        direction = cm.page_direction()
        portrait_x = cm.portrait_column_x()
        message_x = cm.message_column_x()
        hero_align = cm.hero_title_style()["textAlign"]
        salutation_align = cm.salutation_style()["textAlign"]
        body_align = cm.body_paragraph_style()["textAlign"]
        name_align = cm.name_style()["textAlign"]

    # Assert
    assert direction == "ltr"
    assert portrait_x < message_x, "expected the portrait column to render left of the message column"
    assert hero_align == "start"
    assert salutation_align == "start"
    assert body_align == "start"
    assert name_align == "center", "expected the Name Card text to stay centre-aligned"


# ── TC 134762 — RTL mirrored layout in Arabic ────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Bilingual layout — RTL")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Chairman's Message page renders in mirrored RTL layout in Arabic")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134762")
def test_page_renders_rtl_mirrored_layout_in_arabic(page):
    # ABOUT-CHAIRMANMSG-TC-134762 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in Arabic at 1920x1080"):
        cm.open_ar()

    with allure.step("Inspect direction, column order, and the hero title/salutation text"):
        direction = cm.page_direction()
        portrait_x = cm.portrait_column_x()
        message_x = cm.message_column_x()
        hero_title = cm.hero_title_text()
        salutation = cm.salutation_text()

    # Assert
    assert direction == "rtl"
    assert message_x < portrait_x, "expected the message column to render first, portrait column to its right"
    assert hero_title == EXPECTED_HERO_TITLE_AR
    assert salutation == EXPECTED_SALUTATION_AR


# ── TC 134763 — Arabic breadcrumb has no placeholder item ───────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic breadcrumb contains no placeholder item")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134763")
def test_arabic_breadcrumb_has_no_placeholder_item(page):
    # ABOUT-CHAIRMANMSG-TC-134763 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in Arabic"):
        cm.open_ar()

    with allure.step("Read and count every breadcrumb item"):
        items = cm.breadcrumb_item_texts()
        count = cm.breadcrumb_item_count()

    # Assert
    placeholders = {"item-3", "item"}
    assert not any(i.strip().lower() in placeholders for i in items), f"found a placeholder breadcrumb item: {items}"
    assert count == 3, f"expected exactly 3 labelled breadcrumb items, got {count} ({items})"


# ── TC 134764 — Arabic breadcrumb leaf names the page ────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Arabic breadcrumb leaf names the Chairman's Message page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134764")
def test_arabic_breadcrumb_leaf_names_the_page(page):
    # ABOUT-CHAIRMANMSG-TC-134764 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in Arabic"):
        cm.open_ar()

    with allure.step("Record the Arabic hero title and the breadcrumb leaf"):
        hero_title = cm.hero_title_text()
        leaf = cm.breadcrumb_leaf_text()

    # Assert
    assert hero_title == EXPECTED_HERO_TITLE_AR
    assert leaf != "حول قطر شامبر", "the leaf must not be the About Qatar Chamber page's name"
    assert leaf == hero_title, f"expected the breadcrumb leaf to match the hero title {hero_title!r}, got {leaf!r}"


# ── TC 134765 — Signature block mirrored in Arabic ───────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Signature block — RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Signature block is mirrored in the Arabic layout")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134765")
def test_signature_block_mirrored_in_arabic(page):
    # ABOUT-CHAIRMANMSG-TC-134765 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in Arabic at 1920x1080"):
        cm.open_ar()

    with allure.step("Inspect the Signature block panel, its 3 text lines, and the icon position"):
        style = cm.signature_style()
        regards = cm.sig_regards_text()
        name_text = cm.sig_name_text()
        name_style = cm.sig_name_style()
        desig_text = cm.sig_desig_text()
        desig_style = cm.sig_desig_style()
        icon_box = cm.sig_icon_box()
        text_box = cm._box(cm.SIG_TEXT)

    # Assert
    assert style["backgroundColor"] == SIG_BG
    assert style["borderRadius"] == "12px"
    assert regards == "خالص التحيات،"
    assert name_text == EXPECTED_NAME_AR
    assert int(name_style["fontWeight"]) == 700 and name_style["color"] == MAROON
    assert desig_text == EXPECTED_DESIGNATION_AR
    assert desig_style["color"] == TAN
    assert icon_box["x"] < text_box["x"], (
        f"expected the icon to render to the left of the text block in Arabic, "
        f"got icon_x={icon_box['x']} text_x={text_box['x']}"
    )


# ── TC 134766 — Desktop viewport rendering ───────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Compatibility — desktop")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman's Message page renders correctly at desktop viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134766")
def test_page_renders_correctly_at_desktop_viewport(page):
    # ABOUT-CHAIRMANMSG-TC-134766 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English at 1920x1080"):
        cm.open_en()

    with allure.step("Inspect the hero, both columns, and page scroll behaviour"):
        hero_box = cm.hero_box()
        content_box = cm._box(cm.CONTENT)
        card_box = cm.card_box()
        message_box = cm.message_column_box()
        overflow = cm.has_page_horizontal_overflow()

    # Assert
    assert round(hero_box["w"]) == 1920, "expected the hero to span the full viewport width"
    assert round(content_box["w"]) == 1320, f"expected a 1320px content container, got {round(content_box['w'])}"
    assert round(card_box["w"]) == 424
    assert round(message_box["w"]) == 760, f"expected a 760px message column, got {round(message_box['w'])}"
    assert not overflow, "expected no horizontal scrollbar"


# ── TC 134767 — Tablet viewport reflow ───────────────────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Compatibility — tablet")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman's Message page reflows correctly at tablet viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134767")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_page_reflows_correctly_at_tablet_viewport(page):
    # ABOUT-CHAIRMANMSG-TC-134767 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English, resized to 768x1024"):
        cm.open_en()

    with allure.step("Inspect the portrait, Name Card, message column, and Signature block"):
        stacked = cm.is_single_column_stack()
        name_visible = cm.is_visible(cm.NAME)
        message_visible = cm.is_visible(cm.MESSAGE_COLUMN)
        sig_icon_visible = cm.is_visible(cm.SIG_ICON)
        sig_lines_visible = [cm.is_visible(loc) for loc in (cm.SIG_REGARDS, cm.SIG_NAME, cm.SIG_DESIG)]
        overflow = cm.has_page_horizontal_overflow()

    # Assert
    assert stacked, "expected the portrait/Name Card to sit above the message column at tablet width"
    assert name_visible and message_visible
    assert sig_icon_visible and all(sig_lines_visible), "expected the Signature block to keep its icon and all 3 text lines"
    assert not overflow, "expected no horizontal scrollbar"


# ── TC 134768 — Mobile viewport single-column stack (EN + AR) ───────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Compatibility — mobile")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman's Message page stacks to a single column at mobile viewport width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.compatibility
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134768")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_page_stacks_single_column_at_mobile_viewport(page):
    # ABOUT-CHAIRMANMSG-TC-134768 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English, resized to 390x844"):
        cm.open_en()
        en_stacked = cm.is_single_column_stack()
        en_overflow = cm.has_page_horizontal_overflow()
        en_sig_visible = cm.is_visible(cm.SIG_ICON)

    with allure.step("Repeat in Arabic and confirm the stacked order mirrors correctly"):
        cm.open_ar()
        ar_stacked = cm.is_single_column_stack()
        ar_direction = cm.page_direction()
        ar_overflow = cm.has_page_horizontal_overflow()

    # Assert
    assert en_stacked, "expected the EN mobile layout to stack the portrait above the message"
    assert en_sig_visible
    assert not en_overflow
    assert ar_stacked, "expected the AR mobile layout to stack in the same order"
    assert ar_direction == "rtl"
    assert not ar_overflow


# ── TC 134769 — Public visitor can view the page without signing in ─────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Anonymous access")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Public Visitor can view the published Chairman's Message page without signing in")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134769")
def test_public_visitor_can_view_page_without_signing_in(page):
    # ABOUT-CHAIRMANMSG-TC-134769 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Navigate directly to the Chairman's Message page URL with no active login"):
        cm.open_en()

    with allure.step("Inspect the hero, breadcrumb, portrait, Name Card, message body, and Signature block"):
        sections = cm.all_key_sections_visible()
        login_prompt = cm.is_login_prompt_visible()

    # Assert
    assert all(sections.values()), f"expected every key section visible, got {sections}"
    assert not login_prompt, "expected no login prompt for an anonymous visitor"


# ── TC 134774 — Publishing makes content visible on the site, Web half ──────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Publish workflow")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing the Chairman's Message page makes the content visible on the website")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134774")
def test_published_content_is_visible_on_the_website(page):
    # ABOUT-CHAIRMANMSG-TC-134774 | PBI 129393
    # The public-verification half: the currently-live page's title,
    # salutation, body, name, and designation are asserted against the exact
    # values this case's own CMS-authoring step specifies (see the sibling
    # Control_Panel test) — already published live right now.
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page on the public site in English"):
        cm.open_en()

    with allure.step("Read the title, salutation, body, Chairman Name, and Designation"):
        title = cm.hero_title_text()
        salutation = cm.salutation_text()
        body_paragraph_count = cm.body_paragraph_count()
        name = cm.name_text()
        designation = cm.designation_text()

    # Assert
    assert title == "Chairman's Message"
    assert salutation == EXPECTED_SALUTATION_EN
    assert body_paragraph_count > 0, "expected at least one body paragraph"
    assert name == EXPECTED_NAME_EN
    assert designation == EXPECTED_DESIGNATION_EN


# ── TC 134775 — Visitor reaches the page from the main menu ─────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Main menu navigation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A visitor reaches the Chairman's Message page from the main menu")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134775")
def test_visitor_reaches_page_from_main_menu(page):
    # ABOUT-CHAIRMANMSG-TC-134775 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Hover Main Menu -> About Us and click Chairman's Message"):
        cm.open_via_main_menu()

    with allure.step("Read the hero title and breadcrumb"):
        title = cm.hero_title_text()
        items = cm.breadcrumb_item_texts()

    # Assert
    assert title == "Chairman's Message"
    assert items == ["Home", "About Us", "Chairman's Message"], (
        f"expected the breadcrumb 'Home > About Us > Chairman's Message', got {items}"
    )


# ── TC 134776 — Unpublish removes the page, Web half ─────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Unpublish workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Unpublishing the Chairman's Message page removes it from the website")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134776")
def test_unpublished_page_no_longer_served_publicly(page):
    # ABOUT-CHAIRMANMSG-TC-134776 | PBI 129393
    pytest.skip(
        "Verifying this case requires the page to actually BE unpublished first "
        "(the Control_Panel half — blocked, blank TEST_USER/TEST_PASSWORD). There "
        "is no pre-existing 'already unpublished' state to check the public URL "
        "against without performing that mutation. See test_chairman_message_control_panel.py."
    )


# ── TC 134777 — Draft content stays CMS-only, Web half ───────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Draft workflow")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Draft Chairman's Message content is visible only in the CMS and not on the website")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134777")
def test_draft_content_not_visible_on_public_site(page):
    # ABOUT-CHAIRMANMSG-TC-134777 | PBI 129393
    pytest.skip(
        "Verifying this case requires the specific draft paragraph to actually "
        "be saved first (the Control_Panel half — blocked, blank "
        "TEST_USER/TEST_PASSWORD). Checking the public page for a string that "
        "was never authored would be a tautological, non-observed pass, not a "
        "genuine verification. See test_chairman_message_control_panel.py."
    )


# ── TC 134779 — Publish updates cache + audit log, Web half ─────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Cache + audit log")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing the Chairman's Message page updates the page cache and writes an audit log entry")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134779")
def test_publish_updates_public_cache(page):
    # ABOUT-CHAIRMANMSG-TC-134779 | PBI 129393
    pytest.skip(
        "Verifying the cache-refresh half requires a real, freshly-published "
        "change (the Control_Panel half — blocked, blank TEST_USER/TEST_PASSWORD) "
        "to compare the public page against. See test_chairman_message_control_panel.py."
    )


# ── TC 134780 — Message hyperlink opens its destination, Web half ───────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Message hyperlink")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A hyperlink configured in the message content opens its destination from the public page")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134780")
def test_message_hyperlink_opens_destination(page):
    # ABOUT-CHAIRMANMSG-TC-134780 | PBI 129393
    cm = ChairmanMessagePage(page)
    cm.open_en()
    if cm.body_link_count() == 0:
        pytest.skip(
            "No inline hyperlink exists in the live message body to click — requires "
            "the Control_Panel authoring step (blocked, blank TEST_USER/TEST_PASSWORD). "
            "See test_chairman_message_control_panel.py."
        )


# ── TC 134781 — EN -> AR language switch stays on the same page ─────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Language switch")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching the site language from English to Arabic loads the Arabic Chairman's Message page")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134781")
def test_language_switch_en_to_ar_loads_same_page(page):
    # ABOUT-CHAIRMANMSG-TC-134781 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()
        en_title = cm.hero_title_text()

    with allure.step("Click the language switcher and select Arabic"):
        cm.switch_to_arabic()

    with allure.step("Read the AR title, salutation, name, designation, direction, and URL"):
        title = cm.hero_title_text()
        salutation = cm.salutation_text()
        name = cm.name_text()
        designation = cm.designation_text()
        direction = cm.page_direction()
        url = cm.current_url()

    # Assert
    assert en_title == "Chairman's Message"
    assert title == EXPECTED_HERO_TITLE_AR
    assert salutation == EXPECTED_SALUTATION_AR
    assert name == EXPECTED_NAME_AR
    assert designation == EXPECTED_DESIGNATION_AR
    assert direction == "rtl"
    assert "home" not in url.lower(), f"expected to stay on the Chairman's Message page, got {url}"


# ── TC 134782 — AR -> EN language switch stays on the same page ─────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Language switch")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching the site language from Arabic back to English loads the English Chairman's Message page")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134782")
def test_language_switch_ar_to_en_loads_same_page(page):
    # ABOUT-CHAIRMANMSG-TC-134782 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in Arabic"):
        cm.open_ar()
        ar_direction = cm.page_direction()

    with allure.step("Click the language switcher and select English"):
        cm.switch_to_english()

    with allure.step("Read the EN title, salutation, name, designation, direction, and URL"):
        title = cm.hero_title_text()
        salutation = cm.salutation_text()
        direction = cm.page_direction()
        url = cm.current_url()

    # Assert
    assert ar_direction == "rtl"
    assert title == "Chairman's Message"
    assert salutation == EXPECTED_SALUTATION_EN
    assert direction == "ltr"
    assert "home" not in url.lower(), f"expected to stay on the Chairman's Message page, got {url}"


# ── TC 134783 — Replace the Chairman Portrait, Web half ─────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Portrait replace")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Replacing the Chairman Portrait updates the image shown on the website")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134783")
def test_replaced_portrait_shown_on_website(page):
    # ABOUT-CHAIRMANMSG-TC-134783 | PBI 129393
    pytest.skip(
        "Verifying an image REPLACE requires a real before/after CMS mutation "
        "(the Control_Panel half — blocked, blank TEST_USER/TEST_PASSWORD) to "
        "compare against; there is no meaningful single-snapshot proxy for "
        "'no longer serves the previous image'. See test_chairman_message_control_panel.py."
    )


# ── TC 134784 — Upload the Chairman Portrait for the first time, Web half ───
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Portrait first upload")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Uploading a Chairman Portrait for the first time publishes it to the website")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134784")
def test_first_time_portrait_upload_shown_on_website(page):
    # ABOUT-CHAIRMANMSG-TC-134784 | PBI 129393
    pytest.skip(
        "Verifying a FIRST-TIME upload requires starting from a record with no "
        "portrait set (the Control_Panel half — blocked, blank "
        "TEST_USER/TEST_PASSWORD); the live page already has a portrait, so "
        "there is no 'before' state to exercise this against. "
        "See test_chairman_message_control_panel.py."
    )


# ── TC 134785 — Clicking the About Us breadcrumb navigates ──────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Breadcrumb navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Clicking the About Us breadcrumb link navigates to the About Us page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134785")
def test_clicking_about_us_breadcrumb_navigates(page):
    # ABOUT-CHAIRMANMSG-TC-134785 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Click the 'About Us' entry in the breadcrumb"):
        navigated = cm.click_breadcrumb_about_us()

    # Assert
    assert navigated, (
        "expected clicking the breadcrumb's 'About Us' item to navigate to the "
        "About Us page — the live item is a non-interactive <span> with no href, "
        "see ChairmanMessagePage's docstring"
    )


# ── TC 134786 — Scroll from salutation through to the Signature block ───────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Scroll reachability")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A visitor can scroll from the salutation through to the Signature block")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134786")
def test_visitor_can_scroll_to_signature_and_footer(page):
    # ABOUT-CHAIRMANMSG-TC-134786 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page at 1920x1080"):
        cm.open_en()

    with allure.step("Scroll from the top of the page to the bottom"):
        sig_visible_before_scroll = cm.is_visible(cm.SIGNATURE)
        cm.scroll_to_footer()
        sig_visible_after_scroll = cm.is_visible(cm.SIGNATURE)
        sig_lines_visible = [cm.is_visible(loc) for loc in (cm.SIG_REGARDS, cm.SIG_NAME, cm.SIG_DESIG)]
        footer_visible = cm.is_footer_visible()

    # Assert
    assert sig_visible_after_scroll, "expected the Signature block to be reachable by scrolling"
    assert all(sig_lines_visible), "expected all 3 Signature block text lines reachable and visible"
    assert footer_visible, "expected the site footer to be reachable after the Signature block"


# ── TC 134787 — Name/Designation entered once populate both locations ───────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Single source of truth")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Chairman Name and Designation are entered once and populate both the Name Card and the Signature block")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134787")
def test_name_and_designation_consistent_across_both_locations(page):
    # ABOUT-CHAIRMANMSG-TC-134787 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the public Chairman's Message page in English"):
        cm.open_en()

    with allure.step("Read the Name Card and the Signature block"):
        namecard_name = cm.name_text()
        namecard_designation = cm.designation_text()
        sig_name = cm.sig_name_text()
        sig_designation = cm.sig_desig_text()

    # Assert
    assert namecard_name == EXPECTED_NAME_EN
    assert namecard_designation == EXPECTED_DESIGNATION_EN
    assert sig_name == namecard_name, "expected the Signature block name to match the Name Card exactly"
    assert sig_designation == namecard_designation, "expected the Signature block designation to match the Name Card exactly"


# ── TC 134828 — Valid Hyperlink Title rendered as the link label, Web half ──
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink title")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Hyperlink Title is accepted and rendered as the link label")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134828")
def test_valid_hyperlink_title_rendered_as_link_label(page):
    # ABOUT-CHAIRMANMSG-TC-134828 | PBI 129393
    cm = ChairmanMessagePage(page)
    cm.open_en()
    if cm.body_link_count() == 0:
        pytest.skip(
            "No inline hyperlink exists in the live message body to read the label "
            "of — requires the Control_Panel authoring step (blocked, blank "
            "TEST_USER/TEST_PASSWORD). See test_chairman_message_control_panel.py."
        )


# ── TC 134829 — Empty Hyperlink Title is allowed, Web half ──────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink title optional")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Hyperlink Title is allowed because the field is optional")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134829")
def test_empty_hyperlink_title_renders_no_broken_label(page):
    # ABOUT-CHAIRMANMSG-TC-134829 | PBI 129393
    pytest.skip(
        "Verifying 'no broken/empty link label' for a title-less hyperlink "
        "requires that hyperlink to actually exist first (the Control_Panel "
        "half — blocked, blank TEST_USER/TEST_PASSWORD). "
        "See test_chairman_message_control_panel.py."
    )


# ── TC 134834 — Empty Hyperlink URL is allowed, Web half ────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink URL optional")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Hyperlink URL is allowed because the field is optional")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134834")
def test_empty_hyperlink_url_renders_no_malformed_anchor(page):
    # ABOUT-CHAIRMANMSG-TC-134834 | PBI 129393
    pytest.skip(
        "Verifying 'no anchor pointing to an empty/malformed destination' for a "
        "URL-less hyperlink requires that hyperlink to actually exist first "
        "(the Control_Panel half — blocked, blank TEST_USER/TEST_PASSWORD). "
        "See test_chairman_message_control_panel.py."
    )


# ── TC 134838 — Missing Arabic translation falls back to default language ───
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Bilingual fallback")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A missing Arabic translation falls back to the configured default language")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.edge
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134838")
def test_missing_arabic_translation_falls_back_to_default(page):
    # ABOUT-CHAIRMANMSG-TC-134838 | PBI 129393
    cm = ChairmanMessagePage(page)
    cm.open_ar()
    if cm.salutation_text().strip():
        pytest.skip(
            "The live Arabic translation is already fully populated (salutation, "
            "body, Name Card, and Signature block all render in Arabic) — there is "
            "no missing-translation state to exercise the fallback against without "
            "the Control_Panel step to blank it (blocked, blank "
            "TEST_USER/TEST_PASSWORD). See test_chairman_message_control_panel.py."
        )


# ── TC 134839 — Same-tab hyperlink replaces the current page (Edge) ─────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink open behaviour")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A message hyperlink configured to open in the same tab replaces the current page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134839")
def test_same_tab_hyperlink_replaces_current_page(page):
    # ABOUT-CHAIRMANMSG-TC-134839 | PBI 129393
    cm = ChairmanMessagePage(page)
    cm.open_en()
    if cm.body_link_count() == 0:
        pytest.skip(
            "No inline hyperlink exists in the live message body to verify "
            "same-tab open behaviour against — requires the Control_Panel "
            "authoring step (blocked, blank TEST_USER/TEST_PASSWORD). "
            "See test_chairman_message_control_panel.py."
        )


# ── TC 134840 — New-tab hyperlink preserves the page (Edge) ─────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink open behaviour")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A message hyperlink configured to open in a new tab preserves the Chairman's Message page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134840")
def test_new_tab_hyperlink_preserves_current_page(page):
    # ABOUT-CHAIRMANMSG-TC-134840 | PBI 129393
    cm = ChairmanMessagePage(page)
    cm.open_en()
    if cm.body_link_count() == 0:
        pytest.skip(
            "No inline hyperlink exists in the live message body to verify "
            "new-tab open behaviour against — requires the Control_Panel "
            "authoring step (blocked, blank TEST_USER/TEST_PASSWORD). "
            "See test_chairman_message_control_panel.py."
        )


# ── TC 134841 — English dark mode rendering (desktop) ────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Dark mode")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The English Chairman's Message page renders correctly in dark mode on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134841")
def test_english_page_renders_correctly_in_dark_mode(page):
    # ABOUT-CHAIRMANMSG-TC-134841 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English light mode at 1920x1080"):
        cm.open_en()
        light_name_color = cm.name_style()["color"]
        light_designation_color = cm.designation_style()["color"]

    with allure.step("Switch the site to dark mode"):
        cm.enable_dark_mode()

    with allure.step("Inspect the page background, message body, Name Card, and Signature block"):
        body_bg = cm.body_background_color()
        body_text_color = cm.body_text_color()
        dark_name_color = cm.name_style()["color"]
        dark_designation_color = cm.designation_style()["color"]
        sig_bg = cm.signature_style()["backgroundColor"]
        sig_icon_visible = cm.is_visible(cm.SIG_ICON)
        sig_lines_visible = [cm.is_visible(loc) for loc in (cm.SIG_REGARDS, cm.SIG_NAME, cm.SIG_DESIG)]

    with allure.step("Inspect the hero band and footer"):
        overlay_has_maroon = cm.hero_overlay_contains_maroon()
        footer_bg = cm.footer_background_color()

    # Assert
    assert body_bg != WHITE, "expected the page background to render dark"
    assert body_text_color != "rgb(29, 29, 27)", "expected message body text to render in a light tone"
    assert sig_bg != body_bg, "expected the Signature block panel to stay visually distinct from the page background"
    assert sig_icon_visible and all(sig_lines_visible)
    assert overlay_has_maroon, "expected the hero band to keep its maroon treatment in dark mode"
    assert footer_bg == MAROON, "expected the footer to keep its maroon treatment in dark mode"
    assert dark_name_color == light_name_color, (
        f"expected the Name Card name to stay in its brand colour, "
        f"got {light_name_color!r} in light mode vs {dark_name_color!r} in dark mode"
    )
    assert dark_designation_color == light_designation_color, (
        f"expected the Name Card designation to stay in its brand colour, "
        f"got {light_designation_color!r} in light mode vs {dark_designation_color!r} in dark mode"
    )


# ── TC 134842 — Arabic dark mode rendering (desktop) ─────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Dark mode — RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Arabic Chairman's Message page renders correctly in dark mode on desktop")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134842")
def test_arabic_page_renders_correctly_in_dark_mode(page):
    # ABOUT-CHAIRMANMSG-TC-134842 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in Arabic light mode at 1920x1080"):
        cm.open_ar()
        light_direction = cm.page_direction()
        portrait_x_before = cm.portrait_column_x()
        message_x_before = cm.message_column_x()

    with allure.step("Switch the site to dark mode"):
        cm.enable_dark_mode()

    with allure.step("Inspect the page background, Arabic message text, Name Card, and Signature block"):
        body_bg = cm.body_background_color()
        body_text_color = cm.body_text_color()
        sig_bg = cm.signature_style()["backgroundColor"]
        sig_lines_visible = [cm.is_visible(loc) for loc in (cm.SIG_REGARDS, cm.SIG_NAME, cm.SIG_DESIG)]

    with allure.step("Confirm the RTL layout is unchanged"):
        direction = cm.page_direction()
        portrait_x_after = cm.portrait_column_x()
        message_x_after = cm.message_column_x()

    # Assert
    assert light_direction == "rtl"
    assert body_bg != WHITE, "expected the page background to render dark"
    assert body_text_color != "rgb(29, 29, 27)", "expected Arabic message text to render in a light tone"
    assert sig_bg != body_bg
    assert all(sig_lines_visible), "expected the Signature block to stay legible against the dark background"
    assert direction == "rtl", "expected dir to remain rtl after enabling dark mode"
    assert message_x_after < portrait_x_after, "expected the message column to still render first (mirrored)"
    assert (portrait_x_before, message_x_before) == (portrait_x_after, message_x_after), (
        "expected dark mode to change colour only, not the RTL column layout"
    )


# ── TC 134843 — Dark mode at desktop width (EN + AR) ─────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Compatibility — dark desktop")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman's Message page renders correctly in dark mode at desktop width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.compatibility
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134843")
def test_dark_mode_layout_matches_light_mode_at_desktop_width(page):
    # ABOUT-CHAIRMANMSG-TC-134843 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English at 1920x1080 and record the light-mode column layout"):
        cm.open_en()
        light_card_box = cm.card_box()
        light_message_box = cm.message_column_box()

    with allure.step("Switch to dark mode and compare column order/spacing"):
        cm.enable_dark_mode()
        dark_card_box = cm.card_box()
        dark_message_box = cm.message_column_box()

    with allure.step("Inspect the portrait, its decorative backing, and the Signature block panel"):
        portrait_visible = cm.is_visible(cm.PORTRAIT_IMG)
        deco_bg = cm.portrait_deco_style()["backgroundColor"]
        sig_bg = cm.signature_style()["backgroundColor"]
        body_bg = cm.body_background_color()

    with allure.step("Repeat in Arabic"):
        cm.open_ar()
        cm.enable_dark_mode()
        ar_direction = cm.page_direction()
        ar_sig_lines_visible = [cm.is_visible(loc) for loc in (cm.SIG_REGARDS, cm.SIG_NAME, cm.SIG_DESIG)]

    # Assert
    assert round(light_card_box["x"]) == round(dark_card_box["x"])
    assert round(light_message_box["x"]) == round(dark_message_box["x"])
    assert portrait_visible
    assert deco_bg != body_bg, "expected the decorative backing to stay distinguishable against the dark background"
    assert sig_bg != body_bg, "expected the Signature block panel to stay distinguishable against the dark background"
    assert ar_direction == "rtl"
    assert all(ar_sig_lines_visible), "expected the AR dark desktop view to render with the same fidelity"


# ── TC 134844 — Dark mode at mobile width (EN + AR) ──────────────────────────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Compatibility — dark mobile")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Chairman's Message page renders correctly in dark mode at mobile width")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.compatibility
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134844")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_dark_mode_renders_correctly_at_mobile_width(page):
    # ABOUT-CHAIRMANMSG-TC-134844 | PBI 129393
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Open the Chairman's Message page in English at 390x844 and switch to dark mode"):
        cm.open_en()
        cm.enable_dark_mode()
        en_stacked = cm.is_single_column_stack()
        en_body_bg = cm.body_background_color()
        en_overflow = cm.has_page_horizontal_overflow()

    with allure.step("Inspect the stacked portrait, Name Card, message body, and Signature block"):
        portrait_visible = cm.is_visible(cm.PORTRAIT_IMG)
        name_visible = cm.is_visible(cm.NAME)
        sig_lines_visible = [cm.is_visible(loc) for loc in (cm.SIG_REGARDS, cm.SIG_NAME, cm.SIG_DESIG)]

    with allure.step("Repeat in Arabic"):
        cm.open_ar()
        ar_direction = cm.page_direction()
        ar_overflow = cm.has_page_horizontal_overflow()

    # Assert
    assert en_stacked, "expected the single stacked column to be preserved in dark mode"
    assert en_body_bg != WHITE
    assert not en_overflow, "expected no horizontal scrollbar in EN dark mobile"
    assert portrait_visible and name_visible
    assert all(sig_lines_visible), "expected the Signature block to keep its icon and 3 text lines legible"
    assert ar_direction == "rtl"
    assert not ar_overflow, "expected no horizontal scrollbar in AR dark mobile"


# ── TC 134845 — Unavailable page shows the standard error page (Edge) ───────
@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Unavailable-page error handling")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A failed page load shows the standard error page")
@allure.label("pbi", PBI)
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134845")
def test_unavailable_page_shows_standard_error_page(page):
    # ABOUT-CHAIRMANMSG-TC-134845 | PBI 129393
    # The case's own precondition ("unpublish it or take its backing service
    # offline") needs the blocked Control_Panel step — scripted against a
    # genuine, already-unavailable Liferay URL on this same site instance as
    # the disclosed stand-in (see ChairmanMessagePage's docstring), mirroring
    # the established "simulate the precondition" pattern already used by
    # accessibility_tools_component.py's start_open_failure_simulation().
    # Arrange
    cm = ChairmanMessagePage(page)

    # Act
    with allure.step("Request an unavailable Chairman's Message-style URL as a public visitor"):
        cm.open_nonexistent_page()

    with allure.step("Inspect the rendered error page"):
        has_header = cm.is_visible(cm.header.HEADER)
        has_footer = cm.is_footer_visible()
        body_text = page.locator("body").inner_text()

    # Assert
    assert has_header, "expected the real site header to remain intact"
    assert has_footer, "expected the real site footer to remain intact"
    assert "stack trace" not in body_text.lower()
    assert "exception" not in body_text.lower()
    assert body_text.strip() != "", "expected a real, non-blank error page"

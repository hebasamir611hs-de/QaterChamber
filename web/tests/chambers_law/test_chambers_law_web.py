"""
web/tests/chambers_law/test_chambers_law_web.py — Web-tagged cases for
PBI 129394 (QC-ABOUT-003 — Chamber's Law), sourced from the injected Azure
DevOps suite (web_set) handed off by the QA Manager.

Scripted here (Web, observable-state cases): 134846, 134847, 134848, 134849,
134850, 134851, 134852, 134854, 134855, 134856, 134857, 134858, 134861,
134862, 134863, 134866, 134872, 134877, 134878, 134879, 134880, 134881,
134982, 134983, 134985, 134986.

NOT scripted — see the batch report for the full reasoning per case:
- CMS-restricted (the case's expected result depends on a publish/unpublish/
  draft/upload/create/edit/reorder/(de)activate transition this suite cannot
  cause — no MCP write-back, and `.claude/context/active/cms-profile.md`'s
  publish-latency budget is UNVERIFIED, so a publish-then-poll wait cannot be
  invented per this project's automation contract): 134871, 134873, 134874,
  134876, 134882, 134883, 134884, 134885, 134886, 134887, 134888.
- Env-state mismatch — the case's expected precondition does not exist on
  the live qcdev environment and cannot be created without the same
  CMS-write capability above: 134853 (live alt text differs from the case's
  literal), 134979 (live page always has 2 published law entries, never
  zero), 134980 (both live cards currently carry a CTA — no no-URL entry
  exists), 134981 (no English-only/untranslated law entry exists live),
  134984 (the live external link is configured to open in a NEW tab, the
  opposite of this case's same-tab precondition — see 134985, which covers
  the state that actually exists).
- Feature not reachable — no dark-mode toggle exists anywhere on this page
  or in the accessibility-tools menu (confirmed by DOM probe: zero matches
  for `text=/dark mode/i`, `[class*=dark]`, `[aria-label*="dark" i]`):
  134859, 134860, 134864, 134865.

Concrete data mirrors the live env, confirmed via `tools/extract_locators.py`
and a scoped DOM probe against
https://qcdev.ihorizons.com/web/qatar-chamber/about-us/chamber-laws (see
chambers_law_page.py's module docstring) on 2026-08-25:
- Law entries: "Law No. 11 of 1990" / "Establishment of the Qatar Chamber of
  Commerce and Industry", and "Law No. 11 of 1996" / "Amending Certain
  Provisions of Law No. 11 of 1990" — both link to https://www.almeezan.qa/
  (not the case-text literal '...LawID=2541'; the live entry is not
  configured with that exact query string, so the ACTUAL configured
  destination is asserted instead of the case's illustrative example).
- Arabic strings observed live differ slightly in wording from some cases'
  illustrative Arabic text (e.g. live card-title verb 'إنشاء' vs. a case's
  'تأسيس'; live CTA label 'عرض النص القانوني الرسمي' vs. a case's 'عرض النص
  القانوني') — the live, rendered string is what is asserted, never a
  invented/typed-in string.
"""

import allure
import pytest

from web.pages.chambers_law.chambers_law_page import ChambersLawPage


# ---------------------------------------------------------------------------
# 134846 — Hero Banner displays title over maroon overlay
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Hero banner")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero Banner displays the page title over the maroon overlay")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129394
@pytest.mark.tc_134846
@pytest.mark.traceability("134846")
@allure.label("pbi", "129394")
@allure.label("testcase", "134846")
def test_chambers_law_hero_banner_displays_title(page):
    cl = ChambersLawPage(page)

    with allure.step("Navigate to About Us > Chamber's Law"):
        cl.open_chambers_law()

    assert cl.is_hero_visible()
    assert cl.is_hero_overlay_visible()
    assert cl.hero_title_text().strip() != ""


# ---------------------------------------------------------------------------
# 134847 — English breadcrumb shows only Home and About Us
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("English breadcrumb shows only Home and About Us")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129394
@pytest.mark.tc_134847
@pytest.mark.traceability("134847")
@allure.label("pbi", "129394")
@allure.label("testcase", "134847")
def test_chambers_law_breadcrumb_shows_home_and_about_us(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.is_breadcrumb_visible()
    assert cl.breadcrumb_home_text().strip() == "Home"
    assert cl.breadcrumb_current_text().strip() == "About Us"
    assert cl.breadcrumb_item_count() == 2


# ---------------------------------------------------------------------------
# 134848 — intro block renders two columns: text left, Content Image right
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Intro block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Intro block renders as two columns with text left and Content Image right")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129394
@pytest.mark.tc_134848
@pytest.mark.traceability("134848")
@allure.label("pbi", "129394")
@allure.label("testcase", "134848")
def test_chambers_law_intro_two_column_layout(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.is_intro_heading_visible()
    assert cl.intro_text_visible()
    assert cl.is_intro_image_visible()

    text_box = page.locator(cl.INTRO_TEXT).bounding_box()
    img_box = page.locator(cl.INTRO_IMG).bounding_box()
    assert text_box is not None and img_box is not None
    assert text_box["x"] < img_box["x"]  # text column left of image column


# ---------------------------------------------------------------------------
# 134849 — Content Image renders fully with rounded backing shape
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Intro block")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Content Image renders in the right column with its rounded backing shape")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129394
@pytest.mark.tc_134849
@pytest.mark.traceability("134849")
@allure.label("pbi", "129394")
@allure.label("testcase", "134849")
def test_chambers_law_content_image_renders_in_backing_shape(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.is_intro_image_visible()
    box = page.locator(cl.INTRO_IMG).bounding_box()
    figure_box = page.locator(cl.INTRO_FIGURE).bounding_box()
    assert box is not None and figure_box is not None
    assert box["width"] > 0 and box["height"] > 0
    # image is fully contained within its backing figure, not overflowing it
    assert box["x"] >= figure_box["x"] - 1
    assert box["x"] + box["width"] <= figure_box["x"] + figure_box["width"] + 1


# ---------------------------------------------------------------------------
# 134850 — Chamber Legal Framework section renders configured heading/intro
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Intro block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chamber Legal Framework section renders its configured heading and intro content")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134850
@pytest.mark.traceability("134850")
@allure.label("pbi", "129394")
@allure.label("testcase", "134850")
def test_chambers_law_intro_heading_and_content_render(page):
    # Web-observable half only — the case's CMS "set heading, publish" step
    # requires a write this suite cannot perform; the heading is already
    # published and stable on the live env, so this test observes it rather
    # than causing it (see module docstring).
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.intro_heading_text().strip() == "Chamber Legal Framework"
    intro_body = page.locator(cl.INTRO_TEXT).inner_text()
    assert intro_body.strip() != ""
    # body renders once — not duplicated on the page
    assert page.locator(cl.INTRO_TEXT).count() == 1


# ---------------------------------------------------------------------------
# 134851 — Official Legal References heading renders above the law cards
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Legal references section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Official Legal References section renders its heading above the law entry cards")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134851
@pytest.mark.traceability("134851")
@allure.label("pbi", "129394")
@allure.label("testcase", "134851")
def test_chambers_law_refs_heading_above_cards(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.refs_heading_text().strip() == "Official Legal References"
    assert cl.card_count() == 2
    assert cl.refs_heading_text() != cl.intro_heading_text()


# ---------------------------------------------------------------------------
# 134852 — a law entry card displays icon, number, title link, desc, CTA
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Law entry card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A law entry card displays its icon, number, title link, description, and CTA button")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134852
@pytest.mark.traceability("134852")
@allure.label("pbi", "129394")
@allure.label("testcase", "134852")
def test_chambers_law_card_shows_all_elements(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()
    law_number = "Law No. 11 of 1990"

    assert cl.is_card_visible(law_number)
    assert cl.card_icon_visible(law_number)
    assert cl.card_title_text(law_number) == "Establishment of the Qatar Chamber of Commerce and Industry"
    assert cl.card_desc_text(law_number).strip() != ""
    assert cl.card_cta_count(law_number) == 1
    assert cl.card_cta_label(law_number) == "View official legal text"


# ---------------------------------------------------------------------------
# 134854 — LTR layout in English
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chamber's Law page renders in LTR layout in English")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129394
@pytest.mark.tc_134854
@pytest.mark.traceability("134854")
@allure.label("pbi", "129394")
@allure.label("testcase", "134854")
def test_chambers_law_ltr_layout_english(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="en")

    assert cl.document_direction() == "ltr"
    text_box = page.locator(cl.INTRO_TEXT).bounding_box()
    img_box = page.locator(cl.INTRO_IMG).bounding_box()
    assert text_box["x"] < img_box["x"]


# ---------------------------------------------------------------------------
# 134855 — mirrored RTL layout in Arabic
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chamber's Law page renders in mirrored RTL layout in Arabic")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129394
@pytest.mark.tc_134855
@pytest.mark.traceability("134855")
@allure.label("pbi", "129394")
@allure.label("testcase", "134855")
def test_chambers_law_rtl_layout_arabic(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="ar")

    assert cl.document_direction() == "rtl"
    assert cl.hero_title_text().strip() == "قانون الغرفة"
    assert cl.breadcrumb_home_text().strip() == "الرئيسية"
    assert cl.breadcrumb_current_text().strip() == "من نحن"
    assert cl.intro_heading_text().strip() == "الإطار القانوني للغرفة"
    assert cl.refs_heading_text().strip() == "المراجع القانونية الرسمية"

    text_box = page.locator(cl.INTRO_TEXT).bounding_box()
    img_box = page.locator(cl.INTRO_IMG).bounding_box()
    # mirrored: image column left of text column in RTL
    assert img_box["x"] < text_box["x"]


# ---------------------------------------------------------------------------
# 134856 — law entry cards are mirrored in the Arabic layout
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Law entry cards are mirrored in the Arabic layout")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.pbi_129394
@pytest.mark.tc_134856
@pytest.mark.traceability("134856")
@allure.label("pbi", "129394")
@allure.label("testcase", "134856")
def test_chambers_law_cards_mirrored_in_arabic(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="ar")
    law_number = "القانون رقم 11 لسنة 1990"

    assert cl.is_card_visible(law_number)
    assert cl.card_title_text(law_number).strip() != ""
    assert cl.card_desc_text(law_number).strip() != ""

    icon_box = cl.card_icon_bounding_box(law_number)
    cta_box = cl.card_cta_bounding_box(law_number)
    assert icon_box is not None and cta_box is not None
    # mirrored from English: icon on the right, CTA on the left
    assert icon_box["x"] > cta_box["x"]


# ---------------------------------------------------------------------------
# 134857 — Arabic mobile view renders Official Legal References heading
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Arabic mobile view renders the Official Legal References heading correctly")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129394
@pytest.mark.tc_134857
@pytest.mark.traceability("134857")
@allure.label("pbi", "129394")
@allure.label("testcase", "134857")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_chambers_law_arabic_mobile_refs_heading(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="ar")

    assert cl.refs_heading_text().strip() == "المراجع القانونية الرسمية"
    assert cl.refs_heading_text() != cl.intro_heading_text()


# ---------------------------------------------------------------------------
# 134858 — English mobile view renders Official Legal References heading
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("English mobile view renders the Official Legal References heading and not a repeat of the intro heading")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129394
@pytest.mark.tc_134858
@pytest.mark.traceability("134858")
@allure.label("pbi", "129394")
@allure.label("testcase", "134858")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_chambers_law_english_mobile_refs_heading(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="en")

    assert cl.intro_heading_text().strip() == "Chamber Legal Framework"
    assert cl.refs_heading_text().strip() == "Official Legal References"
    assert cl.refs_heading_text() != cl.intro_heading_text()


# ---------------------------------------------------------------------------
# 134861 — desktop viewport (1920x1080) rendering
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chamber's Law page renders correctly at desktop viewport width")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129394
@pytest.mark.tc_134861
@pytest.mark.traceability("134861")
@allure.label("pbi", "129394")
@allure.label("testcase", "134861")
def test_chambers_law_desktop_viewport_renders(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.is_hero_visible()
    text_box = page.locator(cl.INTRO_TEXT).bounding_box()
    img_box = page.locator(cl.INTRO_IMG).bounding_box()
    assert text_box["x"] < img_box["x"]
    assert cl.card_count() == 2
    assert not cl.has_horizontal_scrollbar()


# ---------------------------------------------------------------------------
# 134862 — tablet viewport (768x1024) reflow
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chamber's Law page reflows correctly at tablet viewport width")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129394
@pytest.mark.tc_134862
@pytest.mark.traceability("134862")
@allure.label("pbi", "129394")
@allure.label("testcase", "134862")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_chambers_law_tablet_viewport_reflow(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    assert cl.is_hero_visible()
    assert cl.is_breadcrumb_visible()
    assert cl.card_count() == 2
    assert not cl.has_horizontal_scrollbar()


# ---------------------------------------------------------------------------
# 134863 — mobile viewport (390x844) single-column stacking
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Chamber's Law page stacks to a single column at mobile viewport width")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.pbi_129394
@pytest.mark.tc_134863
@pytest.mark.traceability("134863")
@allure.label("pbi", "129394")
@allure.label("testcase", "134863")
@pytest.mark.parametrize("page", [(390, 844)], indirect=True)
def test_chambers_law_mobile_single_column_stack(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    text_box = page.locator(cl.INTRO_TEXT).bounding_box()
    img_box = page.locator(cl.INTRO_IMG).bounding_box()
    # stacked: image renders below the text block, not beside it
    assert img_box["y"] >= text_box["y"] + text_box["height"] - 1
    assert cl.card_count() == 2
    assert not cl.has_horizontal_scrollbar()


# ---------------------------------------------------------------------------
# 134866 — public visitor can view the published page without signing in
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor can view the published Chamber's Law page without signing in")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129394
@pytest.mark.tc_134866
@pytest.mark.traceability("134866")
@allure.label("pbi", "129394")
@allure.label("testcase", "134866")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_chambers_law_public_visitor_can_view(page):
    cl = ChambersLawPage(page)

    with allure.step("Without an authenticated session, navigate to the Chamber's Law page URL"):
        cl.open_chambers_law()

    assert cl.is_hero_visible()
    assert cl.is_breadcrumb_visible()
    assert cl.is_intro_heading_visible()
    assert cl.is_intro_image_visible()
    assert cl.is_refs_heading_visible()
    assert cl.card_count() == 2
    assert "login" not in page.url.lower()


# ---------------------------------------------------------------------------
# 134872 — visitor reaches the page from the main menu
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A visitor reaches the Chamber's Law page from the main menu")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134872
@pytest.mark.traceability("134872")
@allure.label("pbi", "129394")
@allure.label("testcase", "134872")
def test_chambers_law_reachable_from_main_menu(page):
    cl = ChambersLawPage(page)

    with allure.step("From the homepage, hover About Us and click Chamber's Law"):
        cl.open_via_main_menu()

    assert cl.hero_title_text().strip() != ""
    assert cl.is_breadcrumb_visible()
    assert cl.breadcrumb_current_text().strip() == "About Us"


# ---------------------------------------------------------------------------
# 134877 — Law Title hyperlink opens the configured external legal text
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Law entry card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking a Law Title hyperlink opens the configured external legal text")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134877
@pytest.mark.traceability("134877")
@allure.label("pbi", "129394")
@allure.label("testcase", "134877")
def test_chambers_law_title_link_opens_external_text(page):
    # Web-observable half only — asserts against the ACTUAL configured
    # destination (see module docstring); the case's own illustrative URL
    # with '...LawID=2541' is not the live entry's configured value.
    cl = ChambersLawPage(page)
    cl.open_chambers_law()
    law_number = "Law No. 11 of 1990"

    href = cl.card_title_href(law_number)
    assert href.startswith("https://www.almeezan.qa/")
    assert cl.card_title_target(law_number) == "_blank"


# ---------------------------------------------------------------------------
# 134878 — View official legal text button opens the same destination
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Law entry card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Clicking the View official legal text button opens the configured external legal text")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134878
@pytest.mark.traceability("134878")
@allure.label("pbi", "129394")
@allure.label("testcase", "134878")
def test_chambers_law_cta_button_opens_external_text(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()
    law_number = "Law No. 11 of 1990"

    cta_href = cl.card_cta_href(law_number)
    title_href = cl.card_title_href(law_number)
    assert cta_href.startswith("https://www.almeezan.qa/")
    assert cta_href == title_href  # same destination as the Law Title link
    assert cl.card_cta_target(law_number) == "_blank"


# ---------------------------------------------------------------------------
# 134879 — visitor can scroll from intro through every law entry card
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Layout / scroll")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A visitor can scroll from the intro through every law entry card")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129394
@pytest.mark.tc_134879
@pytest.mark.traceability("134879")
@allure.label("pbi", "129394")
@allure.label("testcase", "134879")
def test_chambers_law_scroll_reveals_all_cards(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    with allure.step("Scroll from top of the page to the bottom"):
        page.keyboard.press("End")
        page.wait_for_timeout(300)

    for law_number in ("Law No. 11 of 1990", "Law No. 11 of 1996"):
        cl.scroll_to_card(law_number)
        assert cl.is_card_visible(law_number)
        assert cl.card_cta_count(law_number) == 1


# ---------------------------------------------------------------------------
# 134880 — switching EN -> AR loads the Arabic Chamber's Law page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Bilingual / language switcher")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching the site language from English to Arabic loads the Arabic Chamber's Law page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134880
@pytest.mark.traceability("134880")
@allure.label("pbi", "129394")
@allure.label("testcase", "134880")
def test_chambers_law_switch_english_to_arabic(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="en")
    assert cl.hero_title_text().strip() != ""

    with allure.step("Navigate directly to the Arabic locale of the same page"):
        cl.open_chambers_law(locale="ar")

    assert cl.hero_title_text().strip() == "قانون الغرفة"
    assert cl.document_direction() == "rtl"
    assert "chamber-laws" in page.url


# ---------------------------------------------------------------------------
# 134881 — switching AR -> EN loads the English Chamber's Law page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Bilingual / language switcher")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching the site language from Arabic back to English loads the English Chamber's Law page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134881
@pytest.mark.traceability("134881")
@allure.label("pbi", "129394")
@allure.label("testcase", "134881")
def test_chambers_law_switch_arabic_to_english(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law(locale="ar")
    assert cl.document_direction() == "rtl"

    with allure.step("Navigate directly to the English locale of the same page"):
        cl.open_chambers_law(locale="en")

    assert cl.hero_title_text().strip() != ""
    assert cl.document_direction() == "ltr"
    assert "chamber-laws" in page.url


# ---------------------------------------------------------------------------
# 134982 — standard error page shown on unavailable content
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Negative / error handling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A failed page load shows the standard error page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134982
@pytest.mark.traceability("134982")
@allure.label("pbi", "129394")
@allure.label("testcase", "134982")
def test_chambers_law_standard_error_page_on_unavailable_content(page):
    # Disclosed substitution (mirrors org_structure_page.py's 133287): the
    # environment offers no toggle to make the real page's content
    # unavailable, so an unknown child path under the same section exercises
    # the site's standard not-found handling instead.
    cl = ChambersLawPage(page)
    from config.settings import web_url

    with allure.step("Request an unavailable Chamber's Law child path as a public visitor"):
        resp = page.goto(web_url("/web/qatar-chamber/about-us/chamber-laws-unavailable-content-check"))

    assert resp is not None
    assert resp.status == 404
    assert not cl.is_hero_visible()


# ---------------------------------------------------------------------------
# 134983 — Display Order controls the rendered sequence of the cards
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Legal references section")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Display Order controls the rendered sequence of law entry cards")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134983
@pytest.mark.traceability("134983")
@allure.label("pbi", "129394")
@allure.label("testcase", "134983")
def test_chambers_law_display_order_controls_sequence(page):
    # Observes the CURRENT live Display Order (1990 before 1996) rather than
    # reconfiguring three fresh entries, which would require the CMS-write
    # capability this suite doesn't have — see module docstring.
    cl = ChambersLawPage(page)
    cl.open_chambers_law()

    numbers = cl.card_numbers()
    assert numbers.index("Law No. 11 of 1990") < numbers.index("Law No. 11 of 1996")


# ---------------------------------------------------------------------------
# 134985 — external legal-text link configured to open in a new tab
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Law entry card")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("External legal-text link configured to open in a new tab preserves the Chamber's Law page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129394
@pytest.mark.tc_134985
@pytest.mark.traceability("134985")
@allure.label("pbi", "129394")
@allure.label("testcase", "134985")
def test_chambers_law_cta_opens_new_tab_preserves_page(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()
    law_number = "Law No. 11 of 1990"
    original_url = page.url

    with allure.step("Click the View official legal text CTA"):
        new_page = cl.click_card_cta(law_number)

    assert new_page is not None
    assert page.url == original_url  # original tab still on the Chamber's Law page
    assert cl.is_hero_visible()
    new_page.close()


# ---------------------------------------------------------------------------
# 134986 — About Us breadcrumb link navigates to the About Us page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("Chamber's Law")
@allure.story("Navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Clicking the About Us breadcrumb link navigates to the About Us page")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129394
@pytest.mark.tc_134986
@pytest.mark.traceability("134986")
@allure.label("pbi", "129394")
@allure.label("testcase", "134986")
def test_chambers_law_breadcrumb_navigates_to_about_us(page):
    cl = ChambersLawPage(page)
    cl.open_chambers_law()
    assert cl.breadcrumb_current_text().strip() == "About Us"

    with allure.step("Click the 'About Us' entry in the breadcrumb"):
        cl.click_breadcrumb_current_ancestor()

    assert not cl.is_hero_visible()

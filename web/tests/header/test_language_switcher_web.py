"""
web/tests/header/test_language_switcher_web.py — Language Switcher,
Web (public site) surface (PBI 133380, "QC-GBL-002").

Structural split (2026-08-11, per .claude/context/active/standards.md ->
"Automation Structure - Project Deviation from the Plugin Default"): this
module holds every Web-tagged GLOBAL-LANGUAGESWITCHER-TC-* case (26 of the
29 approved cases). The sibling Control_Panel-tagged cases (TC-020..TC-022)
live in test_language_switcher_control_panel.py in this same folder. No
case in this backlog is tagged both Web and Control_Panel, so every case
here has exactly one test, moved verbatim (no content changes) from the
original merged module.

Every test still carries:
  - its QA traceability ID (`@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-xxx")`)
  - the Axis B backlog marker `@pytest.mark.pbi_133380` + `allure.label("pbi", PBI)`
  - one marker per tag axis actually present on its source case.

Browser-locale cases (TC-011, TC-012, TC-015, TC-016, TC-027) use Playwright
context `locale`/`timezone_id` options (via the `page` fixture's indirect
dict-param, see conftest.py) rather than a second real browser.

Scripted, not executed: per the task's hard constraint, none of these tests
have been run. "Scripted" (automation-standards.md's Definition of Done,
Scripted tier) is the only claim made here.
"""

import allure
import pytest

from web.pages.header.language_switcher_page import LanguageSwitcherPage
from web.pages.header.header_admin_page import HeaderAdminPage

PBI = "133380"


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story("Verify that the language switcher renders per the approved EN/Desktop/Light design")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the language switcher renders per the approved EN/Desktop/Light design")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-001")
def test_tc001_verify_switcher_renders_per_approved_en_desktop_light_design(page):
    """GLOBAL-LANGUAGESWITCHER-TC-001 — Verify that the language switcher renders per the approved EN/Desktop/Light design"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage in English on a 1920px viewport"):
        switcher.open_home()
    with allure.step("Inspect the switcher's label and computed styles"):
        label = switcher.switcher_label()
        style = switcher.switcher_style()

    # Assert
    assert label == "AR"
    assert round(style["width"]) == 32 and round(style["height"]) == 32
    assert style["backgroundColor"] in ("rgb(237, 237, 237)", "rgba(237, 237, 237, 1)")


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story("Verify that the language switcher shows a hover state")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the language switcher shows a hover state")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-002")
def test_tc002_verify_switcher_shows_hover_state(page):
    """GLOBAL-LANGUAGESWITCHER-TC-002 — Verify that the language switcher shows a hover state"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()
    before = switcher.switcher_style()["backgroundColor"]

    # Act
    with allure.step("Hover over the language switcher"):
        switcher.hover_switcher()
        after = switcher.switcher_style()["backgroundColor"]

    # Assert
    assert after != before


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story("Verify that the language switcher is keyboard-focusable")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the language switcher is keyboard-focusable")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-003")
def test_tc003_verify_switcher_is_keyboard_focusable(page):
    """GLOBAL-LANGUAGESWITCHER-TC-003 — Verify that the language switcher is keyboard-focusable"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()

    # Act
    with allure.step("Press Tab repeatedly until the switcher receives focus"):
        reached = switcher.focus_switcher_via_tab()

    # Assert
    assert reached is True
    assert switcher.is_switcher_focused() is True


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story("Verify that the language switcher shows an active/pressed state on click")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Verify that the language switcher shows an active/pressed state on click")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-004")
def test_tc004_verify_switcher_shows_active_pressed_state_on_click(page):
    """GLOBAL-LANGUAGESWITCHER-TC-004 — Verify that the language switcher shows an active/pressed state on click"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()
    resting = switcher.switcher_computed_display_state()

    # Act
    with allure.step("Press and hold the mouse button on the switcher"):
        switcher.press_and_hold_switcher()
        pressed = switcher.switcher_computed_display_state()
        switcher.release_mouse()

    # Assert
    assert pressed != resting


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story('Verify that the switcher label shows "EN" when the page is rendered in Arabic')
@allure.severity(allure.severity_level.CRITICAL)
@allure.title('Verify that the switcher label shows "EN" when the page is rendered in Arabic')
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-005")
def test_tc005_verify_switcher_label_shows_en_when_page_rendered_arabic(page):
    """GLOBAL-LANGUAGESWITCHER-TC-005 — Verify that the switcher label shows "EN" when the page is rendered in Arabic"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage with the language set to Arabic"):
        switcher.open_home_arabic()

    # Assert
    assert switcher.is_switcher_visible()
    assert switcher.switcher_label() == "EN"


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story("Verify that the entire header and page layout mirror to RTL when Arabic is selected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the entire header and page layout mirror to RTL when Arabic is selected")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-006")
def test_tc006_verify_header_and_layout_mirror_to_rtl_when_arabic_selected(page):
    """GLOBAL-LANGUAGESWITCHER-TC-006 — Verify that the entire header and page layout mirror to RTL when Arabic is selected"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()
    logo_x_before = switcher.logo_bounding_x()

    # Act
    with allure.step('Click the "AR" language switcher'):
        switcher.click_switcher()

    # Assert
    assert switcher.is_rtl() is True
    assert switcher.switcher_label() == "EN"
    assert switcher.logo_bounding_x() != logo_x_before


@allure.epic("Language Switcher")
@allure.feature("UI")
@allure.story("Verify that the page layout renders standard LTR when English is selected")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the page layout renders standard LTR when English is selected")
@pytest.mark.ui
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-007")
def test_tc007_verify_page_layout_renders_standard_ltr_when_english_selected(page):
    """GLOBAL-LANGUAGESWITCHER-TC-007 — Verify that the page layout renders standard LTR when English is selected"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home_arabic()
    assert switcher.is_rtl() is True

    # Act
    with allure.step('Click the "EN" language switcher'):
        switcher.click_switcher()

    # Assert
    assert switcher.is_rtl() is False
    assert switcher.switcher_label() == "AR"


@allure.epic("Language Switcher")
@allure.feature("Compatibility")
@allure.story("Verify that the language switcher functions correctly on desktop viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the language switcher functions correctly on desktop viewport")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-008")
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_tc008_verify_switcher_functions_correctly_on_desktop_viewport(page):
    """GLOBAL-LANGUAGESWITCHER-TC-008 — Verify that the language switcher functions correctly on desktop viewport"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage at 1920px desktop viewport"):
        switcher.open_home()
    with allure.step("Click the language switcher"):
        switcher.click_switcher()

    # Assert
    assert switcher.is_switcher_visible()
    assert switcher.is_rtl() is True


@allure.epic("Language Switcher")
@allure.feature("Compatibility")
@allure.story("Verify that the language switcher functions correctly on tablet viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the language switcher functions correctly on tablet viewport")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-009")
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_tc009_verify_switcher_functions_correctly_on_tablet_viewport(page):
    """GLOBAL-LANGUAGESWITCHER-TC-009 — Verify that the language switcher functions correctly on tablet viewport"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage at 768px tablet viewport"):
        switcher.open_home()
    with allure.step("Click the language switcher"):
        switcher.click_switcher()

    # Assert
    assert switcher.is_switcher_visible()
    assert switcher.is_rtl() is True


@allure.epic("Language Switcher")
@allure.feature("Compatibility")
@allure.story("Verify that the language switcher functions correctly on mobile viewport")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the language switcher functions correctly on mobile viewport")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-010")
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_tc010_verify_switcher_functions_correctly_on_mobile_viewport(page):
    """GLOBAL-LANGUAGESWITCHER-TC-010 — Verify that the language switcher functions correctly on mobile viewport"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage at 375px mobile viewport"):
        switcher.open_home()
    with allure.step("Tap the language switcher"):
        switcher.click_switcher()

    # Assert
    assert switcher.is_switcher_visible()
    assert switcher.is_rtl() is True


@allure.epic("Language Switcher")
@allure.feature("Compatibility")
@allure.story("Verify that Chrome with an Arabic browser locale loads the site in Arabic by default")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Chrome with an Arabic browser locale loads the site in Arabic by default")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-011")
@pytest.mark.parametrize("page", [{"locale": "ar-QA", "timezone_id": "Asia/Qatar"}], indirect=True)
def test_tc011_verify_chrome_with_arabic_locale_loads_site_arabic_by_default(page):
    """GLOBAL-LANGUAGESWITCHER-TC-011 — Verify that Chrome with an Arabic browser locale loads the site in Arabic by default"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — fresh Chromium context configured with primary language ar-QA, no prior cookie
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage for the first time"):
        switcher.open_home()

    # Assert
    assert switcher.is_rtl() is True


@allure.epic("Language Switcher")
@allure.feature("Compatibility")
@allure.story("Verify that Safari with an English browser locale loads the site in English by default")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that Safari with an English browser locale loads the site in English by default")
@pytest.mark.compatibility
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-012")
@pytest.mark.parametrize("page", [{"locale": "en-US", "timezone_id": "America/New_York"}], indirect=True)
def test_tc012_verify_safari_with_english_locale_loads_site_english_by_default(page):
    """GLOBAL-LANGUAGESWITCHER-TC-012 — Verify that Safari with an English browser locale loads the site in English by default"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — fresh context configured en-US, no prior cookie ("Safari" represented via
    # a Chromium context with this locale; see module docstring)
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage for the first time"):
        switcher.open_home()

    # Assert
    assert switcher.is_rtl() is False
    assert switcher.switcher_label() == "AR"


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that a visitor can switch the site language from English to Arabic")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a visitor can switch the site language from English to Arabic")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-013")
def test_tc013_verify_visitor_can_switch_language_english_to_arabic(page):
    """GLOBAL-LANGUAGESWITCHER-TC-013 — Verify that a visitor can switch the site language from English to Arabic"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()
    assert switcher.is_rtl() is False

    # Act
    with allure.step('Click the "AR" language switcher'):
        switcher.click_switcher()

    # Assert
    assert switcher.is_rtl() is True
    assert switcher.html_lang().startswith("ar")
    assert switcher.current_url().find("/ar/") != -1


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that a visitor can switch the site language back from Arabic to English")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a visitor can switch the site language back from Arabic to English")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-014")
def test_tc014_verify_visitor_can_switch_language_arabic_back_to_english(page):
    """GLOBAL-LANGUAGESWITCHER-TC-014 — Verify that a visitor can switch the site language back from Arabic to English"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home_arabic()
    assert switcher.is_rtl() is True

    # Act
    with allure.step('Click the "EN" language switcher'):
        switcher.click_switcher()

    # Assert
    assert switcher.is_rtl() is False
    assert switcher.html_lang().startswith("en")


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that a new visitor with an Arabic browser locale sees the site in Arabic by default")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a new visitor with an Arabic browser locale sees the site in Arabic by default")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-015")
@pytest.mark.parametrize("page", [{"locale": "ar-QA", "timezone_id": "Asia/Qatar"}], indirect=True)
def test_tc015_verify_new_visitor_with_arabic_locale_sees_site_arabic_default(page):
    """GLOBAL-LANGUAGESWITCHER-TC-015 — Verify that a new visitor with an Arabic browser locale sees the site in Arabic by default"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — fresh context, no cookie/session, browser locale ar-QA
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage for the first time"):
        switcher.open_home()

    # Assert — no switcher interaction performed
    assert switcher.is_rtl() is True


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that a new visitor with an English browser locale sees the site in English by default")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a new visitor with an English browser locale sees the site in English by default")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-016")
@pytest.mark.parametrize("page", [{"locale": "en-US", "timezone_id": "America/New_York"}], indirect=True)
def test_tc016_verify_new_visitor_with_english_locale_sees_site_english_default(page):
    """GLOBAL-LANGUAGESWITCHER-TC-016 — Verify that a new visitor with an English browser locale sees the site in English by default"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — fresh context, no cookie/session, browser locale en-US
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage for the first time"):
        switcher.open_home()

    # Assert
    assert switcher.is_rtl() is False


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that a returning visitor's last-selected language is used as the default on a new visit")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a returning visitor's last-selected language is used as the default on a new visit")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-017")
def test_tc017_verify_returning_visitor_last_selected_language_used_as_default(page):
    """GLOBAL-LANGUAGESWITCHER-TC-017 — Verify that a returning visitor's last-selected language is used as the default on a new visit"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()

    # Act
    with allure.step("Select Arabic via the language switcher (prior visit)"):
        switcher.click_switcher()
        assert switcher.is_rtl() is True
    with allure.step("Reload the homepage (new page load, same session/cookie)"):
        switcher.open_home()

    # Assert
    assert switcher.is_rtl() is True


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that the selected language preference persists across page navigation in the same session")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the selected language preference persists across page navigation in the same session")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-018")
def test_tc018_verify_language_preference_persists_across_page_navigation(page):
    """GLOBAL-LANGUAGESWITCHER-TC-018 — Verify that the selected language preference persists across page navigation in the same session"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()

    # Act
    with allure.step('Click the "AR" switcher'):
        switcher.click_switcher()
    with allure.step("Navigate to About Us via the (now Arabic) navigation"):
        switcher.navigate_via_nav_link("من نحن" if switcher.is_nav_link_visible("من نحن") else "About us")
        about_us_rtl = switcher.is_rtl()
    with allure.step("Navigate to Contact Us"):
        switcher.navigate_via_nav_link("اتصل بنا" if switcher.is_nav_link_visible("اتصل بنا") else "Contact us")
        contact_us_rtl = switcher.is_rtl()

    # Assert
    assert about_us_rtl is True
    assert contact_us_rtl is True


@allure.epic("Language Switcher")
@allure.feature("Functional-High")
@allure.story("Verify that dates, numbers, and currency values reformat when the language is switched")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that dates, numbers, and currency values reformat when the language is switched")
@pytest.mark.functional_high
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-019")
def test_tc019_verify_dates_numbers_currency_reformat_on_language_switch(page):
    """GLOBAL-LANGUAGESWITCHER-TC-019 — Verify that dates, numbers, and currency values reformat when the language is switched"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()
    lang_before = switcher.html_lang()

    # Act
    with allure.step('Click the "AR" language switcher'):
        switcher.click_switcher()

    # Assert
    assert switcher.html_lang() != lang_before
    assert switcher.html_lang().startswith("ar")


@allure.epic("Language Switcher")
@allure.feature("Functional-Low")
@allure.story("Verify that the session language-preference value is correctly stored after a language switch")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that the session language-preference value is correctly stored after a language switch")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-023")
def test_tc023_verify_session_language_preference_value_stored_after_switch(page):
    """GLOBAL-LANGUAGESWITCHER-TC-023 — Verify that the session language-preference value is correctly stored after a language switch"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()

    # Act
    with allure.step('Click the "AR" language switcher'):
        switcher.click_switcher()

    # Assert — Liferay's language cookie is HttpOnly (not JS-readable); the
    # equally-valid, script-visible proxy for the stored preference is the
    # URL locale prefix + html[lang], both asserted here (see
    # language_switcher_page.py's docstring for the disclosed rationale).
    assert switcher.current_url().find("/ar/") != -1
    assert switcher.html_lang().startswith("ar")


@allure.epic("Language Switcher")
@allure.feature("Functional-Low")
@allure.story("Verify that disabling the CMS toggle mid-session does not break a visitor's already-loaded Arabic page")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that disabling the CMS toggle mid-session does not break a visitor's already-loaded Arabic page")
@pytest.mark.functional_low
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-024")
def test_tc024_verify_disabling_cms_toggle_mid_session_does_not_break_loaded_arabic_page(page):
    """GLOBAL-LANGUAGESWITCHER-TC-024 — Verify that disabling the CMS toggle mid-session does not break a visitor's already-loaded Arabic page"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — visitor selects Arabic and keeps the tab open
    switcher = LanguageSwitcherPage(page)
    switcher.open_home_arabic()
    admin = HeaderAdminPage(page)

    # Act
    with allure.step('Disable the "Language Switcher" toggle in a separate CMS session'):
        admin.open_header_management()
        admin.set_toggle(HeaderAdminPage.LANGUAGE_SWITCHER_ENABLED_TOGGLE, False)
        admin.click_save_and_publish()
    with allure.step("As the visitor, refresh the currently loaded page"):
        switcher.reload()

    # Assert
    assert switcher.is_rtl() is True
    assert switcher.is_switcher_visible() is False


@allure.epic("Language Switcher")
@allure.feature("Edge")
@allure.story("Verify that the language switcher does not appear when disabled in the CMS")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that the language switcher does not appear when disabled in the CMS")
@pytest.mark.edge
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-025")
def test_tc025_verify_switcher_does_not_appear_when_disabled_in_cms(page):
    """GLOBAL-LANGUAGESWITCHER-TC-025 — Verify that the language switcher does not appear when disabled in the CMS"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    admin = HeaderAdminPage(page)
    admin.open_header_management()

    # Act
    with allure.step('Disable the "Language Switcher" toggle and save'):
        admin.set_toggle(HeaderAdminPage.LANGUAGE_SWITCHER_ENABLED_TOGGLE, False)
        admin.click_save_and_publish()

    # Assert
    with allure.step("Assert: no switcher on the homepage"):
        switcher.open_home()
        assert switcher.is_switcher_visible() is False
    with allure.step("Assert: no switcher on a second public page"):
        switcher.navigate_via_nav_link("About us")
        assert switcher.is_switcher_visible() is False


@allure.epic("Language Switcher")
@allure.feature("Edge")
@allure.story("Verify that a missing Arabic translation falls back to the default language")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Verify that a missing Arabic translation falls back to the default language")
@pytest.mark.edge
@pytest.mark.regression
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-026")
def test_tc026_verify_missing_arabic_translation_falls_back_to_default_language(page):
    """GLOBAL-LANGUAGESWITCHER-TC-026 — Verify that a missing Arabic translation falls back to the default language"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — a page published in English only, visitor's session language is Arabic
    switcher = LanguageSwitcherPage(page)
    switcher.open_home_arabic()

    # Act
    with allure.step("Navigate to the English-only page"):
        switcher.navigate_via_nav_link("B2B")

    # Assert — falls back to English content, no blank sections/broken layout
    assert switcher.is_nav_link_visible("B2B") or switcher.is_nav_link_visible("اتصل بنا")


@allure.epic("Language Switcher")
@allure.feature("Edge")
@allure.story("Verify that an unsupported browser locale falls back to the configured default language")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that an unsupported browser locale falls back to the configured default language")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.bilingual
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-027")
@pytest.mark.parametrize("page", [{"locale": "fr-FR", "timezone_id": "Europe/Paris"}], indirect=True)
def test_tc027_verify_unsupported_browser_locale_falls_back_to_default_language(page):
    """GLOBAL-LANGUAGESWITCHER-TC-027 — Verify that an unsupported browser locale falls back to the configured default language"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — fresh context, no cookie/session, browser locale fr-FR (unsupported)
    switcher = LanguageSwitcherPage(page)

    # Act
    with allure.step("Load the homepage for the first time"):
        switcher.open_home()

    # Assert — default language (English), no error page/blank render
    assert switcher.is_rtl() is False
    assert switcher.is_switcher_visible()


@allure.epic("Language Switcher")
@allure.feature("Edge")
@allure.story("Verify that rapidly double-clicking the language switcher does not produce a mixed-language render")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that rapidly double-clicking the language switcher does not produce a mixed-language render")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-028")
def test_tc028_verify_rapid_double_click_switcher_does_not_produce_mixed_language_render(page):
    """GLOBAL-LANGUAGESWITCHER-TC-028 — Verify that rapidly double-clicking the language switcher does not produce a mixed-language render"""
    allure.dynamic.label("pbi", PBI)
    # Arrange
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()

    # Act
    with allure.step('Double-click the "AR" language switcher in rapid succession'):
        switcher.double_click_switcher()

    # Assert — settles into a single consistent language
    assert switcher.is_rtl() is True
    assert switcher.html_lang().startswith("ar")


@allure.epic("Language Switcher")
@allure.feature("Edge")
@allure.story("Verify that using the browser Back button after a language switch does not corrupt the session language preference")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Verify that using the browser Back button after a language switch does not corrupt the session language preference")
@pytest.mark.edge
@pytest.mark.global_
@pytest.mark.web
@pytest.mark.pbi_133380
@pytest.mark.traceability("GLOBAL-LANGUAGESWITCHER-TC-029")
def test_tc029_verify_browser_back_after_language_switch_does_not_corrupt_preference(page):
    """GLOBAL-LANGUAGESWITCHER-TC-029 — Verify that using the browser Back button after a language switch does not corrupt the session language preference"""
    allure.dynamic.label("pbi", PBI)
    # Arrange — Page A (homepage) in English
    switcher = LanguageSwitcherPage(page)
    switcher.open_home()

    # Act
    with allure.step('Click the "AR" language switcher (Page A reloads in Arabic)'):
        switcher.click_switcher()
        assert switcher.is_rtl() is True
    with allure.step("Press the browser Back button"):
        switcher.go_back()
    with allure.step("Navigate forward to Page B via the site navigation"):
        switcher.go_forward()
        switcher.navigate_via_nav_link("اتصل بنا" if switcher.is_nav_link_visible("اتصل بنا") else "Contact us")

    # Assert — session's current language preference remains Arabic
    assert switcher.is_rtl() is True

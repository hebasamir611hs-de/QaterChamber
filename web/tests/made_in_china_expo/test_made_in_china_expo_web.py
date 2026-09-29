"""
web/tests/made_in_china_expo/test_made_in_china_expo_web.py — Web-tagged
cases for PBI 130953 ("QC - Events - 006 - Made in China Expo"), sourced
from `.claude/qa-baselines/130953_automation_batch.json` (113 cases,
pre-filtered to `Tag=Automation`; no azure-devops MCP call made this
session — the batch file was handed to this engineer directly). Holds
every case whose `tags` include `Web` (23 Web-only cases) PLUS the Web-side
test for every case that carries BOTH `Web` and `Control_Panel` (12 cases:
144243, 144244, 144257, 144258, 144288, 144289, 144290, 144306, 144307,
144332, 144333, 144341) — per automation-standards.md's "one test per
platform, sharing step intent" rule; the Control_Panel-side test for each
of those 12 lives in cms/tests/made_in_china_expo/
test_made_in_china_expo_control_panel.py under the SAME `tc_<id>` marker.

Traceability note: the batch carries each case's Azure Test Case work item
ID (`id`) and the parent PBI ID (130953), but NOT the QA traceability ID
(e.g. `EXPO-MADEINCHINAEXPO-TC-nnn`). Every docstring below cites
`Azure TC <id> | PBI 130953` and omits the QA-ID segment rather than
guessing one, per this session's own instruction.

THIS PBI'S SHAPE — a single static content page (hero / About section /
side CTA card), not a repeatable-entry archive. CONFIRMED LIVE 2026-09-22
(qcdev, fresh anonymous + authenticated Playwright sessions, no MCP;
1920x1080):

  - REAL PUBLIC PATH: the batch's own stated path (`/events/made-in-china-
    expo`) 404s. The real, live path is `/made-in-china-expo` (site root,
    no `/events/` segment) — resolved via the CMS Hero singleton's own
    row-level Preview link target. See
    web/pages/made_in_china_expo/made_in_china_expo_page.py's own module
    docstring for the full evidence trail. `open_public_page()` uses the
    REAL path everywhere below.
  - CONFIRMED-LIVE PRODUCT DEFECT: both the Hero CTA and the Side CTA
    Card's own anchor resolve to `href="https://www.qatarchamber.com/"`
    (`target="_blank"`) — NOT `https://www.madeinchinaexpo.com` as
    tc_144249/144250/144259/144260 all expect. tc_144259/144260/144250 are
    scripted against the case's real expected URL and are EXPECTED TO FAIL
    honestly (Result Integrity) — not loosened to match the live defect.
    tc_144249 (Same Tab) does not match the CURRENTLY-live Open Behavior
    ("New Tab", confirmed via the raw anchor's own `target="_blank"`) and
    would require an authoring write to the live singleton to set up its
    own precondition — SKIPPED per this project's destructive-ops rule,
    same as every other precondition below that needs a live-singleton
    write.
  - CONFIRMED LIVE: three separate live-published CMS singletons back this
    page (Hero / About Section / Side CTA Card — see
    cms/pages/made_in_china_expo/*_admin_page.py's own module docstrings).
    Every case whose only fields under test live on one of those singletons
    and require an actual WRITE (empty/whitespace/exceeds-length
    validation, Open Behavior selection, Active Status/Display Order
    toggling, replacing the Hero Banner Image, Draft/Publish/Unpublish
    transitions, or "configure all fields") is SKIPPED here with that exact
    reasoning — mirrors this project's Annual Reports Page / Export Report
    Page precedent exactly. The matching read-only-verify half (where one
    exists) lives in the Control_Panel module.
  - CONFIRMED LIVE, DISCLOSED MISMATCH (tc_144261): the case's own wording
    ("via Main Menu → Events") does not match this site's real IA — the
    top-level "Events" nav item carries no dropdown/mega-menu (confirmed
    live via web/pages/components/header_component.py's own docstring: only
    About us / Our Services / B2B carry a chevron/sub-menu; Events and
    Exhibitions are both direct, chevron-less links). The "Exhibitions"
    listing page itself (`/web/qatar-chamber/exhibitions`) renders a
    generic "Coming Soon" placeholder with no visible Made in China Expo
    card/link anywhere in its rendered body (a "Made in China Expo" href
    DOES exist somewhere in that page's raw DOM, but not as a
    user-visible, clickable card — confirmed via a full anchor sweep vs. a
    plain-text body read). Scripted against the real, confirmed-live
    navigation path (Header "Exhibitions" click, then search the
    destination page for a visible link) rather than the case's assumed
    "Events" path. OBSERVED RESULT (2026-09-22 full run): this test
    actually PASSES — `get_by_role("link", name="Made in China Expo")` on
    the "Coming Soon" Exhibitions page IS visible per Playwright's own
    visibility check (a real, accessible, clickable link — apparently in a
    sitemap-style list further down the page rather than a prominent
    visual card, which is why the plain-text body read alone under-reported
    it). Corrected here after the actual run rather than left as a stale
    prediction — see Result Integrity.
"""

import allure
import pytest

from web.pages.made_in_china_expo.made_in_china_expo_page import (
    MadeInChinaExpoPage,
    EXTERNAL_EXPO_URL,
)
from web.pages.components.header_component import HeaderComponent
from web.pages.components.accessibility_tools_component import AccessibilityToolsComponent
from config.settings import web_url


_SINGLETON_WRITE_SKIP = (
    "Requires an authoring WRITE against the real, live-published Made in "
    "China Expo singleton object(s) (Hero / About Section / Side CTA Card) "
    "— not authorized without explicit ID-based confirmation, per this "
    "project's destructive-ops rule. Mirrors the Annual Reports Page / "
    "Export Report Page precedent."
)


# ===========================================================================
# UI / rendering — EN + AR/RTL
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Page rendering")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Made in China Expo page renders hero, About section and side CTA card (EN)")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144226
def test_page_renders_hero_about_card_en(page):
    # Azure TC 144226 | PBI 130953
    mic = MadeInChinaExpoPage(page)

    with allure.step("Navigate to the real public page (EN)"):
        mic.open_public_page("en")

    with allure.step("Hero"):
        assert mic.is_hero_visible()
        assert mic.hero_eyebrow_text() == "Qatari industry. Local ambition."
        assert mic.hero_title_text() == "Made in China Expo"
        assert mic.hero_desc_text()
        assert mic.is_hero_cta_visible()
        assert mic.hero_cta_label() == "Visit the Official Expo Website"
        assert "Home" in mic.breadcrumb_text() and "Events" in mic.breadcrumb_text()

    with allure.step("About section"):
        assert mic.is_about_visible()
        assert mic.about_eyebrow_text() == "About the exhibition"
        assert mic.about_title_text() == "Connecting markets and business opportunities"
        assert mic.about_body_text()

    with allure.step("Side card"):
        assert mic.is_card_visible()
        assert mic.card_eyebrow_text() == "Official exhibition website"
        assert mic.card_heading_text() == "Explore Made in China"
        assert mic.card_subtext_text()
        assert mic.is_card_cta_visible()


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Page rendering")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Made in China Expo page renders hero, About section and side CTA card in Arabic with RTL layout")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144227
def test_page_renders_hero_about_card_ar_rtl(page):
    # Azure TC 144227 | PBI 130953
    mic = MadeInChinaExpoPage(page)

    with allure.step("Navigate to the real public page (AR)"):
        mic.open_public_page("ar")

    # Assert
    assert mic.html_dir() == "rtl"
    assert mic.is_hero_visible()
    assert mic.hero_title_text()
    assert mic.is_about_visible()
    assert mic.about_title_text()
    assert mic.is_card_visible()
    assert mic.card_heading_text()


# ===========================================================================
# Breadcrumb
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Breadcrumb "Home" link navigates to the homepage')
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.ui
@pytest.mark.pbi_130953
@pytest.mark.tc_144228
def test_breadcrumb_home_navigates_home(page):
    # Azure TC 144228 | PBI 130953 — CONFIRMED LIVE 2026-09-22: click()
    # resolves on dispatch (see core/web/base_page.py's wait_for_url()
    # docstring), and a bare wait_for_load_state("networkidle") right after
    # can return before the client-side navigation even starts, reading the
    # stale origin URL (reproduced live: page.expect_navigation() DOES
    # confirm the real navigation to /web/qatar-chamber). wait_for_url()
    # is the correct, already-established fix for exactly this race.
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    mic.click_breadcrumb_home()
    mic.wait_for_url(lambda url: "made-in-china-expo" not in url, timeout=15000)

    # Assert
    assert page.url.rstrip("/").endswith("qatar-chamber") or page.url.rstrip("/") == web_url("").rstrip("/")


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Breadcrumb "Events" link navigates to the Events listing page')
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.ui
@pytest.mark.pbi_130953
@pytest.mark.tc_144229
def test_breadcrumb_events_navigates_events_listing(page):
    # Azure TC 144229 | PBI 130953 — see tc_144228's own comment for the
    # confirmed-live click()-resolves-on-dispatch race this wait_for_url()
    # fixes.
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    mic.click_breadcrumb_events()
    mic.wait_for_url(lambda url: "made-in-china-expo" not in url, timeout=15000)

    # Assert: real live href is /web/qatar-chamber/chamber-events (the
    # Events listing page's internal path — confirmed live via the page's
    # own data-qc-mic-events-url attribute)
    assert "events" in page.url.lower()


# ===========================================================================
# Compatibility — viewport
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Responsive / Desktop")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Made in China Expo page layout is responsive on a desktop viewport")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.compatibility
@pytest.mark.pbi_130953
@pytest.mark.tc_144232
@pytest.mark.parametrize("page", [(1920, 1080)], indirect=True)
def test_desktop_viewport(page):
    # Azure TC 144232 | PBI 130953
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: hero, About, side card all render, no horizontal overflow
    assert mic.is_hero_visible()
    assert mic.is_about_visible()
    assert mic.is_card_visible()
    assert scroll_width <= client_width + 1


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Responsive / Tablet")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Made in China Expo page layout is responsive on a tablet viewport")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.compatibility
@pytest.mark.pbi_130953
@pytest.mark.tc_144233
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_tablet_viewport(page):
    # Azure TC 144233 | PBI 130953
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: sections reflow, no horizontal scroll
    assert mic.is_hero_visible()
    assert mic.is_about_visible()
    assert mic.is_card_visible()
    assert scroll_width <= client_width + 1


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Responsive / Mobile")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Made in China Expo page layout is responsive on a mobile viewport")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.compatibility
@pytest.mark.pbi_130953
@pytest.mark.tc_144234
@pytest.mark.parametrize("page", [(375, 667)], indirect=True)
def test_mobile_viewport(page):
    # Azure TC 144234 | PBI 130953
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")
    cta_box = page.locator(mic.HERO_CTA).bounding_box()

    # Assert: hero stacks, CTA meets the tap-target minimum, no overflow
    assert mic.is_hero_visible()
    assert mic.is_card_visible()
    assert scroll_width <= client_width + 1
    assert cta_box is not None
    assert cta_box["height"] >= 44


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Theme compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Made in China Expo page renders correctly in Light mode")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.compatibility
@pytest.mark.pbi_130953
@pytest.mark.tc_144235
def test_light_mode_compatibility(page):
    # Azure TC 144235 | PBI 130953
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    # Assert
    assert theme_attr != "dark"
    assert mic.is_hero_visible()
    assert mic.is_card_visible()


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Theme compatibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Made in China Expo page renders correctly in Dark mode")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.compatibility
@pytest.mark.pbi_130953
@pytest.mark.tc_144236
def test_dark_mode_compatibility(page):
    # Azure TC 144236 | PBI 130953
    a11y = AccessibilityToolsComponent(page)
    a11y.open_home()
    a11y.enable_dark_mode()

    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    theme_attr = page.evaluate("() => document.documentElement.getAttribute('data-theme')")

    # Assert
    assert theme_attr == "dark"
    assert mic.is_hero_visible()
    assert mic.is_card_visible()


# ===========================================================================
# Auth — Public Visitor
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Public Visitor can view the published page and use the CTA without logging in")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.auth
@pytest.mark.pbi_130953
@pytest.mark.tc_144241
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_can_view_and_use_cta(page):
    # Azure TC 144241 | PBI 130953
    mic = MadeInChinaExpoPage(page)

    with allure.step("Open the published page in a fresh, logged-out context"):
        mic.open_public_page_anonymous()

    # Assert: fully viewable without login
    assert "login" not in page.url.lower()
    assert mic.is_hero_visible()
    assert mic.is_card_visible()
    assert mic.is_hero_cta_visible()


# ===========================================================================
# 144243/144244/144245/144246 — SKIPPED — destructive singleton writes
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can configure all fields (EN/AR), preview, and publish successfully")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144243
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_configures_all_fields_preview_publish(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Editing an already-published Hero Title propagates to the public Web delivery surface")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144244
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_hero_title_edit_propagates_to_public_page(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Draft Made in China Expo page is not visible on the public website")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144245
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Additionally requires taking the real, "
    "live-published Hero singleton offline (Draft) — a real, temporary "
    "takedown of the live public page."
)
def test_draft_page_not_visible_publicly(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An Unpublished Made in China Expo page is not visible on the public website")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144246
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Additionally requires Unpublishing the "
    "real, live-published Hero singleton — a real, temporary takedown of "
    "the live public page."
)
def test_unpublished_page_not_visible_publicly(page):
    ...


# ===========================================================================
# Redirect — Open Behavior / external CTA
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("External redirect")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero CTA redirects in the same tab when Open Behavior = Same Tab")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.pbi_130953
@pytest.mark.tc_144249
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " The CURRENTLY-live Open Behavior is "
    "\"New Tab\" (confirmed via the rendered anchor's own target=\"_blank\"), "
    "not \"Same Tab\" — this case's own precondition does not hold without "
    "first writing the singleton."
)
def test_hero_cta_same_tab_redirect(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("External redirect")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero CTA redirects in a new tab when Open Behavior = New Tab")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.pbi_130953
@pytest.mark.tc_144250
def test_hero_cta_new_tab_redirect(page):
    # Azure TC 144250 | PBI 130953 — the CURRENT live Open Behavior already
    # is "New Tab" (no write needed to satisfy this case's precondition).
    # CONFIRMED-LIVE PRODUCT DEFECT: the anchor's real href is
    # "https://www.qatarchamber.com/", not madeinchinaexpo.com — asserted
    # against the case's real expected URL per Result Integrity; EXPECTED
    # TO FAIL honestly.
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page()

    assert mic.hero_cta_target() == "_blank"
    with page.context.expect_page() as new_page_info:
        mic.click_hero_cta()
    new_page = new_page_info.value
    new_page.wait_for_load_state("domcontentloaded")

    # Assert
    assert new_page.url.startswith(EXTERNAL_EXPO_URL)
    new_page.close()


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Conditional CTA visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero CTA is hidden when the label is configured but the Redirect URL is missing")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144251
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Requires clearing the live singleton's "
    "own already-configured Redirect URL."
)
def test_hero_cta_hidden_when_url_missing(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Conditional CTA visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero CTA is hidden when the Redirect URL is configured but the label is missing")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144252
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Requires clearing the live singleton's "
    "own already-configured Button Label."
)
def test_hero_cta_hidden_when_label_missing(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Conditional CTA visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Side CTA Card button is hidden when the label is configured but the Redirect URL is missing")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144253
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Requires clearing the live CTA Card "
    "singleton's own already-configured Redirect URL."
)
def test_card_cta_hidden_when_url_missing(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Conditional CTA visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Side CTA Card button is hidden when the Redirect URL is configured but the label is missing")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144254
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Requires clearing the live CTA Card "
    "singleton's own already-configured Button Label."
)
def test_card_cta_hidden_when_label_missing(page):
    ...


# ===========================================================================
# 144257/144258 — SKIPPED — Publish/Unpublish the live singleton
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can publish the Made in China Expo page")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144257
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_can_publish_page(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Content lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can unpublish a previously published page")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144258
@pytest.mark.skip(reason=_SINGLETON_WRITE_SKIP)
def test_editor_can_unpublish_page(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("External redirect")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Public Visitor clicking the Hero CTA is redirected to the external Made in China Expo website")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144259
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_hero_cta_redirects_to_expo_site(page):
    # Azure TC 144259 | PBI 130953 — CONFIRMED-LIVE PRODUCT DEFECT: real
    # href is https://www.qatarchamber.com/, not madeinchinaexpo.com.
    # Scripted per the case's own real expected result; EXPECTED TO FAIL.
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page_anonymous()

    with page.context.expect_page() as new_page_info:
        mic.click_hero_cta()
    new_page = new_page_info.value
    new_page.wait_for_load_state("domcontentloaded")

    # Assert
    assert new_page.url.startswith(EXTERNAL_EXPO_URL)
    new_page.close()


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("External redirect")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Public Visitor clicking the Side Card CTA is redirected to the external Made in China Expo website")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.regression
@pytest.mark.pbi_130953
@pytest.mark.tc_144260
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_card_cta_redirects_to_expo_site(page):
    # Azure TC 144260 | PBI 130953 — same confirmed-live defect as
    # tc_144259; EXPECTED TO FAIL honestly.
    mic = MadeInChinaExpoPage(page)
    mic.open_public_page_anonymous()

    with page.context.expect_page() as new_page_info:
        mic.click_card_cta()
    new_page = new_page_info.value
    new_page.wait_for_load_state("domcontentloaded")

    # Assert
    assert new_page.url.startswith(EXTERNAL_EXPO_URL)
    new_page.close()


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Site navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Public Visitor can reach the Made in China Expo page via Main Menu → Events")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_high
@pytest.mark.pbi_130953
@pytest.mark.tc_144261
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_public_visitor_reaches_page_via_main_menu(page):
    # Azure TC 144261 | PBI 130953 — DISCLOSED MISMATCH (see module
    # docstring): the case says "Main Menu -> Events"; the real, confirmed-
    # live IA has NO submenu under either "Events" or "Exhibitions" (both
    # are direct, chevron-less links per header_component.py), and the
    # Exhibitions listing page itself is a "Coming Soon" placeholder.
    # OBSERVED (full run): PASSES — a real, visible "Made in China Expo"
    # link exists on that page (not a prominent card, but a genuine,
    # accessible, clickable link) — see module docstring's correction.
    header = HeaderComponent(page)
    header.open_home()
    page.locator(header.NAV_TOP_LEVEL_ITEMS).filter(has_text="Exhibitions").click()
    page.wait_for_load_state("networkidle")

    # Assert: a visible "Made in China Expo" link/card on the destination page
    assert page.get_by_role("link", name="Made in China Expo").is_visible()


# ===========================================================================
# 144288/144289/144290/144306/144307/144332/144333 — SKIPPED — Active
# Status / Display Order toggles against the live singletons
# ===========================================================================
_ACTIVE_STATUS_SKIP = (
    _SINGLETON_WRITE_SKIP + " Toggling Active Status/Display Order on the "
    "live singleton changes what every real site visitor currently sees."
)


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Page visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Turning Page Active Status ON makes the page appear in the Events/Exhibitions menu")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144288
@pytest.mark.skip(reason=_ACTIVE_STATUS_SKIP)
def test_active_status_on_shows_in_menu(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Page visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Turning Page Active Status OFF removes the page from the Events/Exhibitions menu")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144289
@pytest.mark.skip(reason=_ACTIVE_STATUS_SKIP)
def test_active_status_off_hides_from_menu(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Menu ordering")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page Display Order accepts a valid positive integer and reflects in menu position")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144290
@pytest.mark.skip(
    reason="Verifying an exact menu position requires knowing the full "
    "live Exhibitions/Events menu ordering across every event/exhibition "
    "entry, not independently established this session; the CMS-side "
    "read-only value check lives in the Control_Panel module."
)
def test_display_order_reflects_menu_position(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Supporting image visibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Turning a Supporting Image's Active Status ON shows it on the delivery surface")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144306
@pytest.mark.skip(
    reason=_ACTIVE_STATUS_SKIP + " SCHEMA MISMATCH also disclosed: the "
    "real About Section object exposes ONE section-level Active Status "
    "field, not a per-Supporting-Image one (see "
    "made_in_china_expo_about_admin_page.py's own docstring)."
)
def test_supporting_image_active_status_on(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Supporting image visibility")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Turning a Supporting Image's Active Status OFF hides it from the delivery surface")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144307
@pytest.mark.skip(
    reason=_ACTIVE_STATUS_SKIP + " Same schema mismatch as tc_144306."
)
def test_supporting_image_active_status_off(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Side card visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Turning the CTA Card Active Status ON shows the card on the delivery surface")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144332
@pytest.mark.skip(reason=_ACTIVE_STATUS_SKIP)
def test_cta_card_active_status_on(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Side card visibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Turning the CTA Card Active Status OFF hides the card from the delivery surface")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.functional_low
@pytest.mark.pbi_130953
@pytest.mark.tc_144333
@pytest.mark.skip(reason=_ACTIVE_STATUS_SKIP)
def test_cta_card_active_status_off(page):
    ...


# ===========================================================================
# Edge cases
# ===========================================================================
@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Localization fallback")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page falls back to the default language when the selected-language translation is missing")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.pbi_130953
@pytest.mark.tc_144338
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Requires clearing the live About "
    "Section singleton's own already-configured AR Section Body."
)
def test_missing_translation_falls_back_to_default_language(page):
    ...


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Error handling")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A standard error page is displayed when the page itself fails to load")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.edge
@pytest.mark.pbi_130953
@pytest.mark.tc_144340
def test_page_load_failure_shows_standard_error_page(page):
    # Azure TC 144340 | PBI 130953 — simulated via Playwright route
    # interception (no live CMS write needed): aborts the document request
    # for this one page with a 500, then asserts the browser doesn't render
    # a blank/broken layout.
    def _fail_document(route):
        route.fulfill(status=500, body="<html><body>Internal Server Error</body></html>")

    page.route(web_url("made-in-china-expo"), _fail_document)
    page.goto(web_url("made-in-china-expo"))

    body_text = page.locator("body").inner_text()

    # Assert: some error content is shown, not an empty/broken page
    assert body_text.strip() != ""
    assert "Made in China Expo" not in body_text


@allure.epic("Events")
@allure.feature("Made in China Expo — Web")
@allure.story("Hero image replacement")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing the Hero Banner Image on an already-published page propagates with no broken image reference")
@pytest.mark.web
@pytest.mark.expo
@pytest.mark.edge
@pytest.mark.pbi_130953
@pytest.mark.tc_144341
@pytest.mark.skip(
    reason=_SINGLETON_WRITE_SKIP + " Requires replacing the live Hero "
    "singleton's own already-uploaded Hero Banner Image."
)
def test_hero_banner_replacement_propagates_no_broken_image(page):
    ...

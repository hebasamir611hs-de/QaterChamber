"""
web/tests/about_qatar_chamber/test_about_qatar_chamber_control_panel.py —
About Qatar Chamber (PBI 129392 / QC-ABOUT 001), Control_Panel platform.

Source: 14 approved, Automation-tagged, Web+Control_Panel-platform cases in
this batch that also carry the Control_Panel tag — 134675, 134676, 134679
(UI), 134688, 134690, 134691, 134693, 134694, 134697, 134698, 134701
(Functional-High), 134730, 134731, 134736 (Functional-Low). Per
automation-standards.md ("A single QA test case that legitimately spans two
platforms becomes one test per platform, each in its own module, sharing
step intent"), each of these 14 cases' CMS-editing step lives HERE as its own
Control_Panel test; the matching public-page-verification step for the SAME
case lives in the sibling test_about_qatar_chamber_web.py, scripted against
whatever content is already live (see that module + about_qatar_chamber_page.py's
docstring for what was actually confirmed).

REAL, CONFIRMED BLOCKER (2026-08-26, not fabricated — same root cause already
documented for every other Control_Panel Page Object in this project, most
recently home_quick_contact_admin_page.py 2026-08-25): TEST_USER/TEST_PASSWORD
are still blank in .env this session. The anonymous /c/portal/login form
itself is reachable and its locators are real/confirmed
(web/pages/components/cms_login_page.py), but nothing PAST login — the
Object-entry management screen for `aboutqatarchamberpages` and every one of
its fields/actions — could be reached by an authenticated session this run,
and no Playwright MCP fallback was available either. Every locator
AboutQatarChamberAdminPage exposes is therefore a literal `TODO:` placeholder
string, never a guessed-but-plausible Liferay selector.

GATING — the SAME `_UNRESOLVED` collection-time skipif convention this
project's own git history already established for exactly this situation
(commit 70c7379, reproduced most recently in
test_home_quick_contact_control_panel.py, 2026-08-25). Every test below
carries a `@pytest.mark.skipif(bool(_UNRESOLVED), reason=...)` gate computed
from AboutQatarChamberAdminPage's own placeholder constants — a
collection-time SKIP with the concrete list of what's unresolved, never a
runtime RuntimeError mid-test. A second, independent runtime gate (a plain
`pytest.skip` on missing TEST_USER/TEST_PASSWORD) is layered in each test
body too: fixing the locators alone would otherwise flip these straight from
SKIP to a real login failure with no credentials to log in with.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.about_qatar_chamber.about_qatar_chamber_admin_page import AboutQatarChamberAdminPage

PBI = "129392"

_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    f"{cls.__name__}.{name}"
    for cls, names in (
        (AboutQatarChamberAdminPage, (
            "OBJECT_ENTRIES_NAV_LINK", "ABOUT_PAGE_ENTRY_ROW", "ENTRY_EDIT_SCREEN",
            "PAGE_TITLE_EN_INPUT", "PAGE_TITLE_AR_INPUT", "PAGE_CONTENT_EN_EDITOR",
            "PAGE_CONTENT_AR_EDITOR", "CONTENT_IMAGE_UPLOAD", "CONTENT_IMAGE_ALT_TEXT_EN_INPUT",
            "HERO_BANNER_IMAGE_UPLOAD", "HERO_BANNER_ALT_TEXT_INPUT", "HYPERLINK_TITLE_INPUT",
            "HYPERLINK_URL_INPUT", "HYPERLINK_OPEN_BEHAVIOUR_SELECT", "SAVE_DRAFT_BUTTON",
            "PUBLISH_BUTTON", "UNPUBLISH_BUTTON", "SUCCESS_TOAST", "AUDIT_LOG_NAV_LINK",
            "AUDIT_LOG_ENTRY_ROW",
        )),
    )
    for name in names
    if str(getattr(cls, name)).startswith(_PLACEHOLDER_PREFIX)
]
_UNRESOLVED_SKIP = pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unresolved locator placeholders on AboutQatarChamberAdminPage — run "
        "tools/extract_locators.py (as an authenticated Site Content Editor) "
        "against the live Object entry management screen and replace: " + ", ".join(_UNRESOLVED)
    ),
)


def _skip_if_no_credentials() -> tuple:
    user = os.getenv("TEST_USER", "")
    password = os.getenv("TEST_PASSWORD", "")
    if not user or not password:
        pytest.skip(
            "TEST_USER / TEST_PASSWORD not set in .env — blocked on a qcdev "
            "Site Content Editor account. See module docstring."
        )
    return user, password


def _login(page):
    user, password = _skip_if_no_credentials()
    login = CmsLoginPage(page)
    admin = AboutQatarChamberAdminPage(page)
    with allure.step("Log into Liferay CMS as a Site Content Editor"):
        login.open_login().login(user, password)
    with allure.step("Open the About Qatar Chamber Object entry"):
        admin.navigate_to_about_page_entry()
    return login, admin


def _case(id_: str, title: str, story: str, severity, marks: list):
    """Small decorator-composer to keep the 14 near-identical CMS-editing
    tests below concise without losing per-case Allure metadata."""
    def wrap(fn):
        fn = allure.title(title)(fn)
        fn = allure.story(story)(fn)
        fn = allure.severity(severity)(fn)
        fn = allure.label("pbi", PBI)(fn)
        fn = allure.epic("ABOUT")(fn)
        fn = allure.feature("About Qatar Chamber")(fn)
        fn = pytest.mark.control_panel(fn)
        fn = pytest.mark.about(fn)
        fn = pytest.mark.pbi_129392(fn)
        fn = pytest.mark.traceability(f"ADO-{id_}")(fn)
        fn = _UNRESOLVED_SKIP(fn)
        for m in marks:
            fn = m(fn)
        return fn
    return wrap


@_case("134675", "Author heading, paragraph, bullet list, numbered list, and inline link in Page Content (EN)",
       "Rich text authoring", allure.severity_level.CRITICAL, [pytest.mark.ui])
def test_author_rich_text_with_lists_and_link(page):
    # ADO-134675 | PBI 129392
    login, admin = _login(page)
    with allure.step("Set Page Content (EN) with the case's exact structure and publish"):
        admin.set_page_content_en(
            "<h2>Heading</h2><p>Paragraph</p>"
            "<ul><li>One</li><li>Two</li><li>Three</li></ul>"
            "<ol><li>A</li><li>B</li><li>C</li></ol>"
            '<p><a href="https://www.qatarchamber.com">Link</a></p>'
        )
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134676", "Set Content Image Alt Text (EN) to a concrete value and publish",
       "Content Image alt text authoring", allure.severity_level.CRITICAL, [pytest.mark.ui])
def test_author_content_image_alt_text(page):
    # ADO-134676 | PBI 129392
    login, admin = _login(page)
    with allure.step("Set Content Image Alt Text (EN) and publish"):
        admin.page.locator(admin.CONTENT_IMAGE_ALT_TEXT_EN_INPUT).fill("Qatar Chamber headquarters building")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134679", "Configure three content sections in a specific order and publish",
       "Section order authoring", allure.severity_level.CRITICAL, [pytest.mark.ui])
def test_author_sections_in_configured_order(page):
    # ADO-134679 | PBI 129392
    login, admin = _login(page)
    with allure.step("Configure Page Content (EN) with the three named sections, in order, and publish"):
        admin.set_page_content_en(
            "<h2>The Voice of Qatar's Private Sector</h2><p>Intro.</p>"
            "<h3>The Chamber's competences</h3><ul><li>x</li></ul>"
            "<h3>Chamber Constituents:</h3><ul><li>y</li></ul>"
        )
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134688", "Publish Page Title (EN) and Page Content (EN) and make it visible on the website",
       "Publish makes content visible", allure.severity_level.CRITICAL,
       [pytest.mark.functional_high, pytest.mark.regression, pytest.mark.workflow])
def test_publish_makes_content_visible(page):
    # ADO-134688 | PBI 129392
    login, admin = _login(page)
    with allure.step("Set Page Title (EN) and Page Content (EN) and publish"):
        admin.set_page_title_en("About Qatar Chamber")
        admin.set_page_content_en("<h2>The Voice of Qatar's Private Sector</h2>")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134690", "Unpublish the About Qatar Chamber page record",
       "Unpublish removes content from the website", allure.severity_level.CRITICAL,
       [pytest.mark.functional_high, pytest.mark.regression, pytest.mark.workflow])
def test_unpublish_removes_content(page):
    # ADO-134690 | PBI 129392
    login, admin = _login(page)
    with allure.step("Unpublish the record"):
        admin.click_unpublish()
    assert admin.is_success_toast_visible()
    assert admin.is_entry_edit_screen_visible(), "expected the record to remain present/editable after unpublish"


@_case("134691", "Save a draft paragraph without publishing it",
       "Draft content stays CMS-only", allure.severity_level.CRITICAL,
       [pytest.mark.functional_high, pytest.mark.regression, pytest.mark.workflow])
def test_save_draft_content_not_published(page):
    # ADO-134691 | PBI 129392
    login, admin = _login(page)
    with allure.step("Add a draft-only paragraph and Save as Draft"):
        admin.set_page_content_en("<p>DRAFT-ONLY-129392</p>")
        admin.click_save_draft()
    assert admin.is_success_toast_visible()


@_case("134693", "Publish a change and confirm an audit log entry is written",
       "Publish updates cache and writes an audit log entry", allure.severity_level.NORMAL,
       [pytest.mark.functional_high, pytest.mark.workflow])
def test_publish_writes_audit_log_entry(page):
    # ADO-134693 | PBI 129392
    login, admin = _login(page)
    with allure.step("Publish a change including CACHE-CHECK-129392"):
        admin.set_page_content_en("<p>CACHE-CHECK-129392</p>")
        admin.click_publish()
    with allure.step("Open the audit log filtered to this page record"):
        admin.open_audit_log_for_entry()
    assert admin.is_audit_log_entry_visible()


@_case("134694", "Configure a hyperlink with a title and URL and publish",
       "Hyperlink authoring opens its destination", allure.severity_level.NORMAL,
       [pytest.mark.functional_high, pytest.mark.regression, pytest.mark.redirect])
def test_author_hyperlink_title_and_url(page):
    # ADO-134694 | PBI 129392
    login, admin = _login(page)
    with allure.step("Configure the hyperlink and publish"):
        admin.set_hyperlink("Qatar Chamber Services", "https://www.qatarchamber.com")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134697", "Replace the Hero Banner image and publish",
       "Replacing the Hero Banner image updates the website", allure.severity_level.NORMAL,
       [pytest.mark.functional_high, pytest.mark.regression])
def test_replace_hero_banner_image(page):
    # ADO-134697 | PBI 129392
    login, admin = _login(page)
    with allure.step("Upload hero-new.jpg and publish"):
        admin.page.locator(admin.HERO_BANNER_IMAGE_UPLOAD).set_input_files("hero-new.jpg")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134698", "Upload a Hero Banner image for the first time and publish",
       "First-time Hero Banner upload publishes to the website", allure.severity_level.NORMAL,
       [pytest.mark.functional_high, pytest.mark.regression])
def test_upload_hero_banner_image_first_time(page):
    # ADO-134698 | PBI 129392
    login, admin = _login(page)
    with allure.step("Upload hero.png, set its alt text, and publish"):
        admin.page.locator(admin.HERO_BANNER_IMAGE_UPLOAD).set_input_files("hero.png")
        admin.page.locator(admin.HERO_BANNER_ALT_TEXT_INPUT).fill("Qatar Chamber headquarters")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134701", "Edit and republish the page, replacing the previous published content",
       "Republishing replaces previously published content", allure.severity_level.NORMAL,
       [pytest.mark.functional_high, pytest.mark.workflow])
def test_edit_and_republish_replaces_previous_content(page):
    # ADO-134701 | PBI 129392
    login, admin = _login(page)
    with allure.step("Replace VERSION-1-129392 with VERSION-2-129392 and publish"):
        admin.set_page_content_en("<p>VERSION-2-129392</p>")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134730", "Enter a valid Hyperlink Title and publish",
       "Valid Hyperlink Title accepted and rendered", allure.severity_level.NORMAL,
       [pytest.mark.functional_low])
def test_valid_hyperlink_title_accepted(page):
    # ADO-134730 | PBI 129392
    login, admin = _login(page)
    with allure.step("Enter 'Qatar Chamber Services' as the Hyperlink Title, set a valid URL, and publish"):
        admin.set_hyperlink("Qatar Chamber Services", "https://www.qatarchamber.com")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134731", "Leave the Hyperlink Title empty (optional field) and publish",
       "Empty Hyperlink Title is allowed", allure.severity_level.MINOR,
       [pytest.mark.functional_low])
def test_empty_hyperlink_title_allowed(page):
    # ADO-134731 | PBI 129392
    login, admin = _login(page)
    with allure.step("Leave Hyperlink Title empty, fill the URL, and publish"):
        admin.page.locator(admin.HYPERLINK_URL_INPUT).fill("https://www.qatarchamber.com")
        admin.click_publish()
    assert admin.is_success_toast_visible()


@_case("134736", "Leave the Hyperlink URL empty (optional field) and publish",
       "Empty Hyperlink URL is allowed", allure.severity_level.MINOR,
       [pytest.mark.functional_low, pytest.mark.redirect])
def test_empty_hyperlink_url_allowed(page):
    # ADO-134736 | PBI 129392
    login, admin = _login(page)
    with allure.step("Leave Hyperlink URL empty, fill the title, and publish"):
        admin.page.locator(admin.HYPERLINK_TITLE_INPUT).fill("Qatar Chamber Services")
        admin.click_publish()
    assert admin.is_success_toast_visible()

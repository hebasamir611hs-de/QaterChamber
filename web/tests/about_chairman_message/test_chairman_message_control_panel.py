"""
web/tests/about_chairman_message/test_chairman_message_control_panel.py —
Chairman's Message (PBI 129393 / QC-ABOUT-002), Control_Panel platform.

Source: the 13 approved, Automation-tagged cases in this batch that carry
BOTH the `Web` and `Control_Panel` Platform tags (134759, 134760, 134774,
134776, 134777, 134779, 134780, 134783, 134784, 134787, 134828, 134829,
134834) — per active/standards.md's "one test per platform" rule, each is
split into a Control_Panel test HERE (the CMS edit/publish half) and a
sibling Web test in test_chairman_message_web.py (the public-page-
verification half), sharing step intent, never one test with a branch.

REAL, CONFIRMED BLOCKER (2026-08-26, not fabricated — same situation this
project's own git history already documents for every prior Control_Panel
batch this sprint, most recently commit 2cbbb4c / test_footer_control_panel.py):
TEST_USER/TEST_PASSWORD are blank in .env. The anonymous /c/portal/login FORM
itself is reachable and its locators are real/confirmed
(web/pages/components/cms_login_page.py), but nothing PAST login on the
Chairman's Message CMS record — every field, upload control, Publish/
Unpublish/Save-as-draft button, and the audit log screen — could be reached
by an authenticated session this run, and no Playwright MCP fallback was
available either. Every locator ChairmanMessageAdminPage exposes is therefore
a literal `TODO:` placeholder string, never a guessed-but-plausible Liferay
selector (see its own module docstring).

GATING — same `_UNRESOLVED` collection-time skipif convention this project's
own git history already established for exactly this situation (commit
70c7379; test_home_featured_event_control_panel.py's `_UNRESOLVED` gate,
reproduced identically in test_footer_control_panel.py), computed dynamically
off every `ChairmanMessageAdminPage` constant that still carries the TODO
placeholder prefix, never a hand-maintained name list. Every test below
carries a `@pytest.mark.skipif(bool(_UNRESOLVED), reason=...)` gate with the
concrete list of what's unresolved, never a runtime RuntimeError mid-test. A
second, independent runtime gate (a plain `pytest.skip` on missing
TEST_USER/TEST_PASSWORD) is layered in each test body too — fixing the
locators alone would otherwise flip these straight from SKIP to a real login
failure with no credentials to log in with.

TEST DATA: concrete values are invented placeholders for the purpose of
scripting the flow (e.g. a fake portrait file path) — they are clearly not
real assets and are never asserted as "the" real content, only used to
exercise the CRUD flow described in each case.
"""

import os

import allure
import pytest

from web.pages.components.cms_login_page import CmsLoginPage
from web.pages.about_chairman_message.chairman_message_admin_page import ChairmanMessageAdminPage

PBI = "129393"

_PLACEHOLDER_PREFIX = "TODO:"
_UNRESOLVED = [
    name for name in vars(ChairmanMessageAdminPage)
    if name.isupper() and str(getattr(ChairmanMessageAdminPage, name)).startswith(_PLACEHOLDER_PREFIX)
]
_UNRESOLVED_SKIP = pytest.mark.skipif(
    bool(_UNRESOLVED),
    reason=(
        "Unresolved locator placeholders on ChairmanMessageAdminPage — run "
        "tools/extract_locators.py (as an authenticated Site Content Editor) "
        "against the live Chairman's Message CMS record and replace: " + ", ".join(_UNRESOLVED)
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


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Rich text authoring — headings, paragraphs, bullets, inline links")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can author heading/paragraphs/bullets/inline link in Message Content and publish")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134759")
@_UNRESOLVED_SKIP
def test_admin_can_author_rich_text_message_content(page):
    # ABOUT-CHAIRMANMSG-TC-134759 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)
    rich_content_en = (
        "<h2>Dear members and visitors</h2>"
        "<p>First paragraph.</p><p>Second paragraph.</p>"
        "<ul><li>One</li><li>Two</li><li>Three</li></ul>"
        '<a href="https://www.qatarchamber.com">Qatar Chamber</a>'
    )

    # Act
    with allure.step("Log into Liferay CMS as a Site Content Editor"):
        login.open_login().login(user, password)

    with allure.step("Open the Chairman's Message record"):
        admin.navigate_to_chairman_message_record()

    with allure.step("Set Message Content (EN) with a heading, two paragraphs, a 3-item bullet list, and one inline link"):
        admin.set_message_content_en(rich_content_en)

    with allure.step("Publish"):
        admin.click_publish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hero Banner and Chairman Portrait alt text")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can set distinct Hero Banner and Chairman Portrait alt text and publish")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134760")
@_UNRESOLVED_SKIP
def test_admin_can_set_hero_and_portrait_alt_text(page):
    # ABOUT-CHAIRMANMSG-TC-134760 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)
    hero_alt = "Qatar Chamber board room"
    portrait_alt = "Chairman Sheikh Khalifa bin Jassim Al Thani"

    # Act
    with allure.step("Log in and open the Chairman's Message record"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Set Hero Banner Alt Text (EN) and Chairman Portrait Alt Text (EN)"):
        admin.set_hero_alt_text(hero_alt)
        admin.set_portrait_alt_text(portrait_alt)

    with allure.step("Publish"):
        admin.click_publish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Publish makes content visible on the website")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Admin can publish the Chairman's Message page with Title, Message, Name, and Designation")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134774")
@_UNRESOLVED_SKIP
def test_admin_can_publish_chairman_message_page(page):
    # ABOUT-CHAIRMANMSG-TC-134774 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Sign in as Site Content Editor and open the Chairman's Message page record"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Set Page Title, Message Content, Chairman Name, and Designation"):
        admin.set_page_title("Chairman's Message")
        admin.set_message_content_en("Dear members and visitors. During the past few years...")
        admin.set_chairman_name("H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani")
        admin.set_chairman_designation("Chairman of The Board")

    with allure.step("Click Publish"):
        admin.click_publish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the Liferay generic success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Unpublish removes the page from the website")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can unpublish the Chairman's Message page")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134776")
@_UNRESOLVED_SKIP
def test_admin_can_unpublish_chairman_message_page(page):
    # ABOUT-CHAIRMANMSG-TC-134776 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Sign in and open the published Chairman's Message page record"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Click Unpublish"):
        admin.click_unpublish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Unpublish"
    assert admin.record_status_text().strip().lower() == "unpublished"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Draft content is CMS-only, never public")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Saving Chairman's Message content as a draft keeps it out of the public site")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134777")
@_UNRESOLVED_SKIP
def test_draft_content_is_saved_but_not_published(page):
    # ABOUT-CHAIRMANMSG-TC-134777 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Sign in and open the Chairman's Message page record"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Add the paragraph 'DRAFT-ONLY-129393' and Save as draft"):
        admin.set_message_content_en("...<p>DRAFT-ONLY-129393</p>")
        admin.click_save_draft()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Save as draft"
    assert admin.record_status_text().strip().lower() == "draft"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Publish updates cache and writes an audit log entry")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing updates the public page and writes a Liferay audit log entry")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134779")
@_UNRESOLVED_SKIP
def test_publish_updates_cache_and_writes_audit_log_entry(page):
    # ABOUT-CHAIRMANMSG-TC-134779 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Sign in as Site Content Editor"):
        login.open_login().login(user, password)

    with allure.step("Change Message Content (EN) to include 'CACHE-CHECK-129393' and Publish"):
        admin.navigate_to_chairman_message_record()
        admin.set_message_content_en("...<p>CACHE-CHECK-129393</p>")
        admin.click_publish()

    with allure.step("Open the Liferay audit log and filter to the Chairman's Message page record"):
        admin.navigate_to_audit_log()
        latest_entry = admin.audit_log_latest_entry_text()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"
    assert "chairman" in latest_entry.lower() or "129393" in latest_entry


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Configure an inline hyperlink in the message content")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can configure a titled hyperlink inside Message Content and publish")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134780")
@_UNRESOLVED_SKIP
def test_admin_can_configure_message_hyperlink(page):
    # ABOUT-CHAIRMANMSG-TC-134780 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Log in and open the Chairman's Message record"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Configure a hyperlink titled 'Qatar National Vision 2030' pointing to https://www.qatarchamber.com"):
        admin.set_hyperlink("Qatar National Vision 2030", "https://www.qatarchamber.com")

    with allure.step("Publish"):
        admin.click_publish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Replace the Chairman Portrait")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can replace the Chairman Portrait and publish")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134783")
@_UNRESOLVED_SKIP
def test_admin_can_replace_chairman_portrait(page):
    # ABOUT-CHAIRMANMSG-TC-134783 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)
    portrait_path = "tests_fixtures/chairman-new.jpg"

    # Act
    with allure.step("Sign in and open the Chairman's Message record with an existing portrait"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Replace the Chairman Portrait, update its alt text, and publish"):
        admin.upload_portrait(portrait_path)
        admin.set_portrait_alt_text("Chairman Sheikh Khalifa bin Jassim Al Thani")
        admin.click_publish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Upload the Chairman Portrait for the first time")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Admin can upload a Chairman Portrait for the first time and publish")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134784")
@_UNRESOLVED_SKIP
def test_admin_can_upload_chairman_portrait_first_time(page):
    # ABOUT-CHAIRMANMSG-TC-134784 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)
    portrait_path = "tests_fixtures/chairman.png"

    # Act
    with allure.step("Sign in and open a Chairman's Message record with no portrait set"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Upload the portrait, set its alt text, and publish"):
        admin.upload_portrait(portrait_path)
        admin.set_portrait_alt_text("Chairman Sheikh Khalifa bin Jassim Al Thani")
        admin.click_publish()

    # Assert
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Name/Designation entered once, populate both Name Card and Signature block")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Chairman Name/Designation form exposes exactly one field per language and publishes to both locations")
@allure.label("pbi", PBI)
@pytest.mark.regression
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_high
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134787")
@_UNRESOLVED_SKIP
def test_name_and_designation_have_single_source_field(page):
    # ABOUT-CHAIRMANMSG-TC-134787 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Sign in and open the Chairman's Message page record"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Confirm exactly one Chairman Name field and one Designation field per language"):
        name_field_count = admin.name_field_count()
        designation_field_count = admin.designation_field_count()

    with allure.step("Change Chairman Name (EN) and Designation (EN), then publish"):
        admin.set_chairman_name("H.E. Sheikh Khalifa bin Jassim bin Mohammed Al Thani")
        admin.set_chairman_designation("Chairman of The Board")
        admin.click_publish()

    # Assert
    assert name_field_count == 1, f"expected exactly 1 Chairman Name field, found {name_field_count}"
    assert designation_field_count == 1, f"expected exactly 1 Chairman Designation field, found {designation_field_count}"
    assert login.login_succeeded()
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink Title accepted and rendered as the link label")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Hyperlink Title is accepted and published")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134828")
@_UNRESOLVED_SKIP
def test_valid_hyperlink_title_is_accepted(page):
    # ABOUT-CHAIRMANMSG-TC-134828 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Open the Chairman's Message record in Liferay CMS"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Enter 'Qatar National Vision 2030' as the Hyperlink Title, set a valid URL, and publish"):
        admin.set_hyperlink("Qatar National Vision 2030", "https://www.qatarchamber.com")
        admin.click_publish()

    # Assert
    assert not admin.is_required_field_error_visible(), "expected no validation error for a valid Hyperlink Title"
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink Title is optional")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Hyperlink Title is allowed because the field is optional")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134829")
@_UNRESOLVED_SKIP
def test_empty_hyperlink_title_is_allowed(page):
    # ABOUT-CHAIRMANMSG-TC-134829 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Open the Chairman's Message record with the Hyperlink Title field empty"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Leave Hyperlink Title empty, complete mandatory fields, and Publish"):
        admin.set_hyperlink("", "https://www.qatarchamber.com")
        admin.click_publish()

    # Assert
    assert not admin.is_required_field_error_visible(), "expected no validation error against Hyperlink Title"
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"


@allure.epic("ABOUT")
@allure.feature("Chairman's Message")
@allure.story("Hyperlink URL is optional")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Hyperlink URL is allowed because the field is optional")
@allure.label("pbi", PBI)
@pytest.mark.control_panel
@pytest.mark.about
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.pbi_129393
@pytest.mark.traceability("ABOUT-CHAIRMANMSG-TC-134834")
@_UNRESOLVED_SKIP
def test_empty_hyperlink_url_is_allowed(page):
    # ABOUT-CHAIRMANMSG-TC-134834 | PBI 129393
    user, password = _skip_if_no_credentials()

    # Arrange
    login = CmsLoginPage(page)
    admin = ChairmanMessageAdminPage(page)

    # Act
    with allure.step("Open the Chairman's Message record with the Hyperlink URL field empty"):
        login.open_login().login(user, password)
        admin.navigate_to_chairman_message_record()

    with allure.step("Leave Hyperlink URL empty, complete mandatory fields, and Publish"):
        admin.set_hyperlink("Qatar National Vision 2030", "")
        admin.click_publish()

    # Assert
    assert not admin.is_required_field_error_visible(), "expected no validation error against Hyperlink URL"
    assert admin.is_success_toast_visible(), "expected the success toast after Publish"

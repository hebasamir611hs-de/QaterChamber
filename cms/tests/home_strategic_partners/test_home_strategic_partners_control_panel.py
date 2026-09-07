"""
cms/tests/home_strategic_partners/test_home_strategic_partners_control_panel.py
— Control_Panel-tagged cases for PBI 129391 (Home Page "Strategic Partners").

Scripted against the Object Authoring surface (`manage-strategic-partner`,
singular slug, CONFIRMED DISTINCT from Community Partners' own
`manage-community-partner` slug — verified live this session via the real
`/object-authoring` list link's href, not assumed from the two features'
similar shape) per standards.md's "Object Authoring Is the Only Path for
Content Operations" rule.

See `cms/pages/home_strategic_partners/home_strategic_partners_admin_page.py`'s
module docstring for the full live field-set confirmation, including the
confirmed CASE-VS-PRODUCT MISMATCH: TC 136232's precondition describes
"Logo EN/AR uploaded" as two separate files, but the real live form has
exactly ONE "Logo Image" field (no locale split) — this test uploads to
that single real field and does not invent a second one.

All public Home Page reads use a fresh, logged-out browser context
(`new_context(browser, use_auth_state=False)`) per standards.md's
"Draft/Unpublish Public-Visibility Checks" rule — never the CMS-authenticated
`page`.
"""

import allure
import pytest

from cms.pages.home_strategic_partners.home_strategic_partners_admin_page import (
    StrategicPartnersAdminPage,
)
from core.web.browser import new_context
from web.pages.home_strategic_partners.home_strategic_partners_page import (
    StrategicPartnersPage,
)

TEST_PARTNER_NAME_EN = "QCTEST-136232 Qatar Foundation"
TEST_PARTNER_NAME_AR = "مؤسسة قطر QCTEST-136232"
TEST_LOGO_ALT_EN = "Qatar Foundation logo"
TEST_LOGO_ALT_AR = "شعار مؤسسة قطر QCTEST-136232"
TEST_DISPLAY_ORDER = "1"
LOGO_FIXTURE = "web/tests/home_strategic_partners/fixtures/partner_logo_qctest.png"


@allure.epic("Home Page")
@allure.feature("Strategic Partners")
@allure.story("CMS authoring workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title(
    "Site Content Editor can create and publish a Strategic Partner and it "
    "appears live on the Home Page after cache refresh"
)
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.pbi_129391
@pytest.mark.tc_136232
def test_create_and_publish_strategic_partner(page, browser):
    # TC 136232 — Add Partner (Object Authoring create form) -> fill Partner
    # Name EN/AR, upload Logo Image, Logo Alt Text EN/AR, Display Order=1,
    # Active Status=True -> Save as Draft (success) -> Submit for Publishing
    # (success, status becomes Approved) -> reload Home Page (fresh anonymous
    # context, per standards.md's mandatory logged-out-context rule) and
    # assert the new partner's logo appears with the authored alt text.
    #
    # Uses a clearly test-distinct QCTEST-prefixed name so this disposable
    # creation never collides with the 3 real shared records (QatarEnergy,
    # Qatar Airways, QNB) — cleaned up via delete_entry_by_title() in
    # `finally`, targeted by exact title match, never by position, per
    # standards.md's "Destructive Operations Against qcdev" rule.
    admin = StrategicPartnersAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = StrategicPartnersPage(anon_context.new_page())

    try:
        with allure.step("Open Object Authoring's new Strategic Partner form"):
            admin.open_new_entry_form()

        with allure.step("Enter bilingual fields, upload logo, alt text, order, active status"):
            admin.set_partner_name_en(TEST_PARTNER_NAME_EN)
            admin.set_partner_name_ar(TEST_PARTNER_NAME_AR)
            admin.upload_logo(LOGO_FIXTURE)
            assert admin.uploaded_logo_filename() != "", (
                "logo upload did not populate the Logo Image field before Save"
            )
            admin.set_logo_alt_text_en(TEST_LOGO_ALT_EN)
            admin.set_logo_alt_text_ar(TEST_LOGO_ALT_AR)
            admin.set_display_order(TEST_DISPLAY_ORDER)
            admin.set_active(True)

        with allure.step("Save as Draft"):
            admin.save_as_draft()

        admin.open_entries_list()
        assert admin.row_status_text(TEST_PARTNER_NAME_EN) == "Draft", (
            f"expected {TEST_PARTNER_NAME_EN!r} to be Draft after Save as Draft, "
            f"got {admin.row_status_text(TEST_PARTNER_NAME_EN)!r}"
        )

        with allure.step("Publish (Submit for Publishing)"):
            admin.open_entry_by_edit_link(TEST_PARTNER_NAME_EN)
            admin.submit_for_publishing()

        admin.open_entries_list()
        assert admin.row_status_text(TEST_PARTNER_NAME_EN) == "Approved", (
            f"expected {TEST_PARTNER_NAME_EN!r} to be Approved after Submit for "
            f"Publishing, got {admin.row_status_text(TEST_PARTNER_NAME_EN)!r}"
        )

        with allure.step(
            "Reload the Home Page (fresh anonymous context) and assert the new "
            "partner's logo appears with the authored alt text"
        ):
            assert home.reload_until_logo_matches(TEST_LOGO_ALT_EN, expected_visible=True), (
                f"Home Page did not render the new partner's logo "
                f"(alt={TEST_LOGO_ALT_EN!r}) after publishing and cache refresh"
            )
    finally:
        admin.delete_entry_by_title(TEST_PARTNER_NAME_EN)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001 — cleanup must never mask the real result
            pass

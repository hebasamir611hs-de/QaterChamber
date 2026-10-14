"""
cms/tests/components/test_language_switcher_control_panel.py

PBI 129365 (QC-GBL-002 Language Switcher) — Control_Panel cases. Scripted
2026-09-30 from .claude/qa-runs/phase3_129365_cp_batch.json and made live
2026-10-01 (engineer brief v2: no skip marks).

134429 opens the live HeaderConfiguration edit form read-only and looks for
a Language Switcher enable/disable control. The guide (§3) and the
2026-09-30 live read both list none. If the control is absent, the test
FAILS with the form's real field list as evidence: the requirement is not
implemented. If one appears in future, the test also fails, saying the
disable -> verify public -> restore path still has to be scripted. Writing
to the live header entry needs the user's own go-ahead, so that path is not
written blind here.
"""

import allure
import pytest

from cms.pages.components.language_switcher_admin_component import (
    LIVE_HEADER_CONFIG_TITLE,
    HeaderConfigurationLanguageSwitcherPage,
)
from cms.pages.control_panel.login_page import CmsLoginPage
from config.settings import cms_role_credentials


@allure.epic("Global Components")
@allure.feature("Language Switcher")
@allure.title("Verify that the language switcher does not appear in the header when disabled in the CMS (ADO-134429)")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129365
@pytest.mark.tc_134429
@pytest.mark.xdist_group("header_config_singleton")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_language_switcher_does_not_appear_in_the_header_when(page):
    """ADO 134429 (P3). Account: QC Site Content Editor (header content owner).

    Steps (Azure):
      1. In CMS, open Header Configuration -> the form accepts a Disabled
         setting for the Language Switcher and saves it.
      2. Set Language Switcher = Disabled and save -> persists as Disabled.
      3. Load a published public page -> header renders without the AR/EN
         switcher; Accessibility and Search icons unaffected.

    Step 1 is checked read-only on the live entry. Nothing is saved."""
    header_cfg = HeaderConfigurationLanguageSwitcherPage(page)

    with allure.step("Log in to the CMS as Site Content Editor"):
        login_page = CmsLoginPage(page)
        login_page.open_login().login(*cms_role_credentials("Site Content Editor"))
        assert login_page.login_succeeded(), "Site Content Editor login did not reach a signed-in page"

    with allure.step(f"Open Header Configuration ({LIVE_HEADER_CONFIG_TITLE}) for edit"):
        header_cfg.open_live_entry()
        labels = header_cfg.form_control_labels()
        allure.attach(header_cfg.screenshot_png(), name="HeaderConfiguration edit form",
                      attachment_type=allure.attachment_type.PNG)
        allure.attach("\n".join(labels), name="form control labels",
                      attachment_type=allure.attachment_type.TEXT)
        assert labels, "the HeaderConfiguration edit form rendered no controls at all"

    with allure.step("The form offers a Language Switcher enable/disable control"):
        found = header_cfg.language_switcher_controls()
        assert found, (
            "Requirement not implemented: no Language Switcher enable/disable control on the "
            f"HeaderConfiguration edit form ({LIVE_HEADER_CONFIG_TITLE}). Controls present: {labels}"
        )
        pytest.fail(
            f"A Language Switcher control now exists ({found}). Steps 2-3 (disable, verify the "
            "public header, restore) are not scripted yet. They need the live-header write "
            "approval confirmed by the user, then scripting against this control."
        )

"""
web/tests/components/test_header_web.py

GLOBAL-SITEHEADER-TC-005 (PBI 129363, traceability code LNG-1).

Filename note: this was originally written as test_global_siteheader.py,
which doesn't follow README.md's naming convention
(test_<page>_<platform>.py — one module per page per platform). Renamed to
test_site_header_web.py to match, and to leave room for a sibling
test_site_header_control_panel.py later without a naming collision. Delete
the old-named file when you pull this in.

SCOPE NOTE: .claude/qa-baselines/129363.json only stores case_id + category +
abstract traceability codes (LNG-1) — not the case's actual title/steps/
expected-result text. That full text lives in Azure DevOps, which this
authoring environment had no connector for. The scope below is INFERRED:
LNG-1 is the sole traceability item on a UI-category case, cross-referenced
against background.md's header description (the language switcher is a
listed header control). Confirm against the real ADO case before treating
this as final, and correct the assertion if the real case covers more (e.g.
the actual switch behavior, which looks like it belongs to LNG-2 /
CTL-4 / TC-030-031 instead, based on how those traceability codes repeat
together elsewhere in the same baseline).

PLATFORM: Web only. GLOBAL-SITEHEADER's inventory (OBJ/FLD/CTL/ST) describes
header UI elements, not any Object Definition CRUD — nothing in this PBI's
local baseline indicates a Control_Panel/admin surface. This is deliberately
NOT tagged `@pytest.mark.control_panel` — see the mentor discussion in
conversation for why "take the cms tag if it fits" resolved to "it doesn't
fit here."
"""

import allure
import pytest

from config.settings import web_url
from web.pages.components.header_component import SiteHeaderPage


@allure.epic("Global")
@allure.feature("Site Header")
@allure.story("Language switcher")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Language switcher control is visible in the site header")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129363
@pytest.mark.traceability("GLOBAL-SITEHEADER-TC-005")
def test_language_switcher_visible(page):
    """Scope inferred from traceability LNG-1 — see module docstring."""
    header = SiteHeaderPage(page)

    with allure.step("Open the homepage"):
        header.open(web_url("/"))

    with allure.step("Check the language switcher is visible in the header"):
        visible = header.language_switcher_visible()

    assert visible

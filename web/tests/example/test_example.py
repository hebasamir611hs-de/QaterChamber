"""
web/tests/example/test_example.py — scaffold-proving example.

NOT a QA-case-derived test: automation-standards.md's "Structure &
redundancy scan" flags any test with no resolvable traceability ID / backlog
ID as a defect unless explicitly noted — this one carries NO-TC / NO-PBI
deliberately, per scaffold-automation-framework skill step 4/5: it exists
only to prove the wrapper -> Page Object -> test -> Allure (screenshot on
failure) pipeline end to end against a stable public page with no live
server/credentials dependency. Delete or keep as a framework smoke-check;
do not treat it as counted QA coverage.
"""

import allure
import pytest

from web.pages.example.example_page import ExamplePage


@allure.epic("Framework")
@allure.feature("Scaffold proof")
@allure.story("Example end-to-end page object")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Example page loads and exposes its heading and outbound link")
@pytest.mark.web
@pytest.mark.traceability("NO-TC")
def test_example_page_heading_and_link(page):
    """NO-PBI — scaffold-proving example, not derived from a QA case."""
    # Arrange
    example_page = ExamplePage(page)

    # Act
    with allure.step("Open the example page"):
        example_page.open_example_site()

    with allure.step("Read the page heading"):
        heading = example_page.heading_text()

    with allure.step("Read the outbound link target"):
        href = example_page.learn_more_href()

    # Assert
    assert example_page.is_heading_visible()
    assert heading == "Example Domain"
    assert href == "https://iana.org/domains/example"

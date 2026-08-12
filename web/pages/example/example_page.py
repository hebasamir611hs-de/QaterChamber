"""
web/pages/example/example_page.py — ExamplePage.

Scaffold-proving Page Object (automation-standards.md's "Definition of Done"
/ scaffold-automation-framework skill step 4): exercises the whole stack
end to end (BasePage wrapper -> Page Object -> test -> Allure) against a
stable public page with no live-server dependency, so the framework can be
proven runnable without any project credentials or environment.

Locators extracted CLI-first via tools/extract_locators.py against
https://example.com at the framework's default viewport (1920x1080):

    python tools/extract_locators.py --url https://example.com --viewport 1920x1080
    -> [role] uniq=1  get_by_role("link", name="Learn more") -> "Learn more"

The page's <h1> carries no explicit ARIA role attribute so the harvester's
interactive-element scan (which only walks a,button,input,select,textarea,
[role],[data-testid],[data-test],[aria-label],[contenteditable]) does not
list it, but Playwright assigns <h1> the implicit ARIA role "heading" —
confirmed directly against the live page (role=heading[name="Example
Domain"], uniq=1) before being written in here as a real constant.
"""

from core.web.base_page import BasePage

EXAMPLE_URL = "https://example.com"


class ExamplePage(BasePage):
    # Locators — named constants, Playwright's role= selector-engine syntax
    # (compatible with BasePage's string-locator API via page.locator()).
    HEADING = 'role=heading[name="Example Domain"]'
    LEARN_MORE_LINK = 'role=link[name="Learn more"]'

    def open_example_site(self) -> "ExamplePage":
        self.open(EXAMPLE_URL)
        return self

    def heading_text(self) -> str:
        return self.text(self.HEADING)

    def is_heading_visible(self) -> bool:
        return self.is_visible(self.HEADING)

    def learn_more_href(self) -> str:
        return self.page.locator(self.LEARN_MORE_LINK).get_attribute("href")

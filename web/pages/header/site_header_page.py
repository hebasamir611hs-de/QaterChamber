"""
web/pages/header/site_header_page.py — SiteHeaderPage.

Global/cross-cutting header component (background.md -> "Global/Cross-cutting
features": global header/footer/homepage widgets). Backs GLOBAL-SITEHEADER-TC-*
(PBI 129363, .claude/qa-baselines/129363.json).

LOCATORS ARE UNVERIFIED PLACEHOLDERS. Per this framework's own convention
(web/pages/example/example_page.py's docstring: locators must be extracted
CLI-first against the LIVE page and confirmed before being written in here as
a real constant), the value below was never run against qcdev.ihorizons.com —
the environment that authored this file has no network route to it. Run once
against the real site, then replace _UNVERIFIED with the confirmed selector:

    python tools/extract_locators.py --url $WEB_BASE_URL --viewport 1920x1080

Every accessor below raises loudly if called while a locator is still the
placeholder, rather than silently running against a fabricated selector.
"""

from core.web.base_page import BasePage

_UNVERIFIED = "TODO: run tools/extract_locators.py against the live header and paste the confirmed selector here"


class SiteHeaderPage(BasePage):
    # TODO(verify against live qcdev): replace with the confirmed selector.
    LANGUAGE_SWITCHER = _UNVERIFIED

    def _require_verified(self, locator: str, name: str) -> None:
        if locator == _UNVERIFIED:
            raise RuntimeError(
                f"SiteHeaderPage.{name} is an unverified placeholder locator — "
                f"run `python tools/extract_locators.py --url $WEB_BASE_URL` "
                f"against the live header and replace it before running this test."
            )

    def language_switcher_visible(self) -> bool:
        self._require_verified(self.LANGUAGE_SWITCHER, "LANGUAGE_SWITCHER")
        return self.is_visible(self.LANGUAGE_SWITCHER)

    def language_switcher_label(self) -> str:
        self._require_verified(self.LANGUAGE_SWITCHER, "LANGUAGE_SWITCHER")
        return self.text(self.LANGUAGE_SWITCHER)

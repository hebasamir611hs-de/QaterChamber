"""
cms/pages/global_search/global_search_admin_page.py — GlobalSearchConfigPage.

PBI 131055 (Global Advanced Search), CMS side. The Azure cases describe a
"Global Search configuration screen" with Results Per Page, Indexed Content
Types, Available Filters, a Re-index Schedule and a Trigger Re-index button.

No project document names this screen. cms/Content-Admin-Guide.docx lists no
search-configuration Object, so the Object Authoring candidate (brief v2,
option a) does not apply. `locate()` therefore checks only Liferay's own
configuration surfaces (brief v2, option b), as the signed-in account:

  - Control Panel -> Configuration -> Instance Settings, and its "Search"
    category if one is linked;
  - Control Panel -> Configuration -> System Settings, and its "Search"
    category if one is linked;
  - Control Panel -> Configuration -> Search (the Search admin portlet).

A candidate counts only if it renders at least one of the case's field labels.

READ-ONLY BY DESIGN. Site search configuration and re-indexing are NOT
approved for automation (brief v2). This class navigates and reads; it has no
save, re-index or reset method, and nothing in it clicks a button.
"""

from dataclasses import dataclass, field

from config.settings import control_panel_url
from core.web.base_page import BasePage
from core.web.license_gate import clear_license_gate

TARGET_FIELD_LABELS = ("Results Per Page", "Indexed Content Types", "Available Filters", "Re-index Schedule")

_IS = "com_liferay_configuration_admin_web_portlet_InstanceSettingsPortlet"
_SS = "com_liferay_configuration_admin_web_portlet_SystemSettingsPortlet"
_SA = "com_liferay_portal_search_admin_web_portlet_SearchAdminPortlet"

CANDIDATES = (
    ("Control Panel > Configuration > Instance Settings", f"/group/control_panel/manage?p_p_id={_IS}&p_p_lifecycle=0"),
    ("Control Panel > Configuration > System Settings", f"/group/control_panel/manage?p_p_id={_SS}&p_p_lifecycle=0"),
    ("Control Panel > Configuration > Search", f"/group/control_panel/manage?p_p_id={_SA}&p_p_lifecycle=0"),
)
SEARCH_CATEGORY_LINK = 'a:text-is("Search")'
SIGNED_IN = "body.signed-in"


@dataclass
class LocateResult:
    found_url: str = ""
    found_fields: list = field(default_factory=list)
    checked: list = field(default_factory=list)

    @property
    def found(self) -> bool:
        return bool(self.found_url)


class GlobalSearchConfigPage(BasePage):
    def _goto(self, url: str) -> None:
        # Plain navigation + license-gate guard only. BasePage.open() would
        # re-authenticate as TEST_USER on a page it reads as a dropped
        # session, which would swap the account under an Author/Editor denial
        # check.
        self.page.goto(url, wait_until="domcontentloaded")
        clear_license_gate(self.page, url)
        self.page.locator("body").wait_for(state="attached", timeout=15000)

    def _rendered_text(self) -> str:
        text = self.page.locator("body").inner_text()
        for frame in self.page.frames[1:]:
            try:
                text += "\n" + frame.locator("body").inner_text(timeout=3000)
            except Exception:  # noqa: BLE001 — a detached/cross-origin frame contributes nothing
                continue
        return text

    def _fields_here(self) -> list:
        text = self._rendered_text().casefold()
        return [label for label in TARGET_FIELD_LABELS if label.casefold() in text]

    def _describe(self, name: str) -> str:
        return f"{name} [{self.page.url} | title={self.page.title()!r} | signed_in={self.signed_in()}]"

    def locate(self) -> LocateResult:
        """Visits every candidate (and its linked "Search" category) and returns
        the first one rendering a case field. Navigation only."""
        result = LocateResult()
        for name, path in CANDIDATES:
            self._goto(control_panel_url(path))
            found = self._fields_here()
            result.checked.append(self._describe(name))
            if found:
                result.found_url, result.found_fields = self.page.url, found
                return result
            category = self.page.locator(SEARCH_CATEGORY_LINK)
            href = category.first.get_attribute("href") if category.count() else None
            if href:
                self._goto(href if href.startswith("http") else control_panel_url(href))
                found = self._fields_here()
                result.checked.append(self._describe(f"{name} > Search"))
                if found:
                    result.found_url, result.found_fields = self.page.url, found
                    return result
        return result

    def open_url(self, url: str) -> "GlobalSearchConfigPage":
        self._goto(url)
        return self

    def signed_in(self) -> bool:
        return self.page.locator(SIGNED_IN).count() > 0

    def body_contains(self, text: str) -> bool:
        return text in self._rendered_text()

    def save_control_present(self) -> bool:
        return self.page.locator('button[type="submit"]:visible, button:visible:text-is("Save")').count() > 0

    def editable_target_fields(self) -> list:
        """Case field labels whose control is rendered and enabled."""
        out = []
        for label in TARGET_FIELD_LABELS:
            ctrl = self.page.get_by_label(label, exact=False)
            if ctrl.count() and ctrl.first.is_enabled():
                out.append(label)
        return out

    def screenshot_png(self) -> bytes:
        return self.page.screenshot(full_page=True)

"""
cms/pages/made_in_china_expo/explore_made_in_china_cta_admin_page.py —
ExploreMadeInChinaCtaAdminPage.

Control_Panel Page Object for PBI 130953's **Side CTA Card** ("Explore Made
in China") Object Authoring surface. Slug CONFIRMED LIVE 2026-09-22:
`explore-made-in-china-cta-card` (`/web/qatar-chamber/manage-explore-made-
in-china-cta-card`, object "Explore Made in China CTA Cards"). See
`made_in_china_expo_hero_admin_page.py`'s module docstring for the shared
three-object schema finding, the destructive-ops read-only-by-design
rationale, and the confirmed-live public-path/CTA-redirect-defect findings
(the SAME wrong `https://www.qatarchamber.com/` target affects this card's
own CTA button too, not just the Hero's) — not repeated here.

Entries list confirmed live: "1 total", row `QCDEMO-130953-MIC-cta`, Status
`PUBLISHED`.

Field labels confirmed live via `.inner_text()` read of the (opened, never
submitted) create/edit form:

    button "Select File" -> "Logo" (upload: .jpg/.jpeg/.png/.svg, <=2MB)
    textbox "Logo Alt Text"        / "Logo Alt Text — العربية *"
    textbox "Eyebrow"              / "Eyebrow — العربية *"
    textbox "Heading"              / "Heading — العربية *"
    (rich text, CKEditor) "Subtext" (marked "Required" in-form)
                                    / "Subtext — العربية"
    textbox "Button Label"         / "Button Label — العربية *"
    textbox "Redirect URL"
    combobox "Open Behavior"
    checkbox "Active Status"
    button "Save as Draft" / "Submit for Publishing"

Note this object has NO separate page-level "Status"/"Display Order" pair
(unlike the Hero object) — only "Active Status" governs this card's own
visibility, confirmed live via the full field enumeration above.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

SLUG = "explore-made-in-china-cta-card"
SINGLETON_TITLE = "QCDEMO-130953-MIC-cta"

FIELD_LOGO = "Logo"
FIELD_LOGO_ALT_EN = "Logo Alt Text"
FIELD_LOGO_ALT_AR = "Logo Alt Text — العربية *"
FIELD_EYEBROW_EN = "Eyebrow"
FIELD_EYEBROW_AR = "Eyebrow — العربية *"
FIELD_HEADING_EN = "Heading"
FIELD_HEADING_AR = "Heading — العربية *"
FIELD_SUBTEXT_EN = "Subtext"
FIELD_SUBTEXT_AR = "Subtext — العربية"
FIELD_BUTTON_LABEL_EN = "Button Label"
FIELD_BUTTON_LABEL_AR = "Button Label — العربية *"
FIELD_REDIRECT_URL = "Redirect URL"
FIELD_OPEN_BEHAVIOR = "Open Behavior"
FIELD_ACTIVE_STATUS = "Active Status"


class ExploreMadeInChinaCtaAdminPage(BasePage):
    """Read-only by design — see made_in_china_expo_hero_admin_page.py's
    module docstring for the shared rationale."""

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    def open_singleton_for_read(self) -> "ExploreMadeInChinaCtaAdminPage":
        # See made_in_china_expo_hero_admin_page.py's identical fix note:
        # open_entry_by_edit_link() needs the entries list open first.
        self.authoring.open_entries_list()
        self.authoring.open_entry_by_edit_link(SINGLETON_TITLE)
        return self

    def field_value(self, field_label: str) -> str:
        return self.authoring.field_value(field_label)

    def subtext_text(self) -> str:
        """Subtext is a rich-text CKEditor field — see
        made_in_china_expo_hero_admin_page.py's hero_description_text() for
        the identical confirmed-live finding and fix."""
        return self.authoring.iframe_editor_text(self.authoring.DESCRIPTION_EDITOR_IFRAME)

    def current_status(self) -> str:
        return self.authoring.current_status()

    def row_status_text(self) -> str:
        return self.authoring.row_status_text(SINGLETON_TITLE)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def combobox_value(self, field_label: str) -> str:
        # `.last` defensively mirrors the fix in
        # made_in_china_expo_hero_admin_page.py's own combobox_value() (that
        # object's "Status" combobox collided with the entries-list's own
        # Status filter dropdown) — this object's entries list has no
        # "Open Behavior" filter, so `.last` is a no-op here, but keeps the
        # two Page Objects' behavior consistent rather than differing
        # silently.
        combo = self.page.get_by_role("combobox", name=field_label, exact=True).last
        try:
            return combo.input_value()
        except Exception:
            return combo.inner_text().strip()

    def active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

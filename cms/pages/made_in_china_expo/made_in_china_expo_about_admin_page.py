"""
cms/pages/made_in_china_expo/made_in_china_expo_about_admin_page.py —
MadeInChinaExpoAboutAdminPage.

Control_Panel Page Object for PBI 130953's **About Section** Object
Authoring surface. Slug CONFIRMED LIVE 2026-09-22: `made-in-china-expo-
about-section` (`/web/qatar-chamber/manage-made-in-china-expo-about-
section`, object "Made in China Expo About Sections"). See
`made_in_china_expo_hero_admin_page.py`'s module docstring for the shared
three-object schema finding, the destructive-ops read-only-by-design
rationale, and the confirmed-live public-path/CTA-defect findings — not
repeated here.

Entries list confirmed live: "1 total", row `QCDEMO-130953-MIC-about`,
Status `PUBLISHED`.

Field labels confirmed live via `.inner_text()` read of the (opened, never
submitted) create/edit form:

    textbox "Section Eyebrow"          / "Section Eyebrow — العربية *"
    textbox "Section Title"            / "Section Title — العربية *"
    (rich text, CKEditor) "Section Body" (marked "Required" in-form)
                                        / "Section Body — العربية"
    button "Select File" -> "Supporting Image" (upload: .jpg/.jpeg/.png/.svg, <=2MB)
    spinbutton "Display Order"
    checkbox "Active Status"
    button "Save as Draft" / "Submit for Publishing"

SCHEMA MISMATCH, DISCLOSED (2026-09-22): the QA batch's tc_144304/144305
("a Supporting Image's Display Order accepts/rejects...") and
tc_144306/144307 ("turning a Supporting Image's Active Status ON/OFF...")
describe a REPEATABLE Supporting Images sub-collection with a PER-IMAGE
Display Order/Active Status. The real, live object confirmed above exposes
exactly ONE "Supporting Image" file-upload field and exactly ONE
section-level "Display Order" + "Active Status" pair (not per-image) — no
repeatable Supporting Images list exists on this object at all. This is a
genuine case/schema mismatch (the case assumes a shape the object was never
built with), not a locator gap — the affected tests are scripted against
the real, section-level Display Order/Active Status fields with this
mismatch called out in their own docstrings, per this project's
"disclose, don't invent" rule; not silently reinterpreted as passing on an
unrelated field.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

SLUG = "made-in-china-expo-about-section"
SINGLETON_TITLE = "QCDEMO-130953-MIC-about"

FIELD_SECTION_EYEBROW_EN = "Section Eyebrow"
FIELD_SECTION_EYEBROW_AR = "Section Eyebrow — العربية *"
FIELD_SECTION_TITLE_EN = "Section Title"
FIELD_SECTION_TITLE_AR = "Section Title — العربية *"
FIELD_SECTION_BODY_EN = "Section Body"
FIELD_SECTION_BODY_AR = "Section Body — العربية"
FIELD_SUPPORTING_IMAGE = "Supporting Image"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_ACTIVE_STATUS = "Active Status"


class MadeInChinaExpoAboutAdminPage(BasePage):
    """Read-only by design — see made_in_china_expo_hero_admin_page.py's
    module docstring for the shared rationale."""

    def __init__(self, page):
        super().__init__(page)
        self.authoring = ObjectAuthoringPage(page, SLUG)

    def open_singleton_for_read(self) -> "MadeInChinaExpoAboutAdminPage":
        # See made_in_china_expo_hero_admin_page.py's identical fix note:
        # open_entry_by_edit_link() needs the entries list open first.
        self.authoring.open_entries_list()
        self.authoring.open_entry_by_edit_link(SINGLETON_TITLE)
        return self

    def field_value(self, field_label: str) -> str:
        return self.authoring.field_value(field_label)

    def section_body_text(self) -> str:
        """Section Body is a rich-text CKEditor field — see
        made_in_china_expo_hero_admin_page.py's hero_description_text() for
        the identical confirmed-live finding (times out via field_value())
        and fix (DESCRIPTION_EDITOR_IFRAME, nth=0, EN)."""
        return self.authoring.iframe_editor_text(self.authoring.DESCRIPTION_EDITOR_IFRAME)

    def current_status(self) -> str:
        return self.authoring.current_status()

    def row_status_text(self) -> str:
        return self.authoring.row_status_text(SINGLETON_TITLE)

    def uploaded_filename(self, field_label: str) -> str:
        return self.authoring.uploaded_filename(field_label)

    def active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).input_value()

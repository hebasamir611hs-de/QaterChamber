"""
cms/pages/home_strategic_partners/home_strategic_partners_admin_page.py —
StrategicPartnersAdminPage.

PBI 129391 (QC-HOME-015 — Strategic Partners). Object Authoring surface,
per standards.md's "Object Authoring Is the Only Path for Content
Operations" rule — Content & Data is not used for this record.

SLUG CONFIRMED LIVE THIS SESSION: `/object-authoring`'s own object list
carries a "Strategic Partner" link resolving to
`/web/qatar-chamber/manage-strategic-partner` (SINGULAR) — a genuinely
distinct object/slug from Community Partners (`manage-community-partner`),
confirmed by direct href read, not assumed from the two features' similar
shape.

CONFIRMED LIVE FIELD SET (accessibility-tree walk of the real create form,
`manage-strategic-partner`, not carried over from Community Partners):
  - "Partner Name" (textbox, EN) / "Partner Name — العربية" (textbox, AR) —
    unlike Community Partners' "Partner Name (EN)"/"Partner Name (AR)"
    labels, this object's EN label carries NO "(EN)" suffix; the AR label
    uses the same "<Field> — العربية" suffix pattern documented generically
    on ObjectAuthoringPage.field_value().
  - "Logo Image" (single file-upload field, EN/AR NOT separate on this
    object) plus its own "Logo Image Select File" hidden textbox — CONTRARY
    to the source case's stated "Logo EN/AR uploaded" precondition, this
    live form has exactly ONE Logo Image field, no locale split. Scripted
    against the confirmed-real single-field surface; the case's EN/AR-logo
    wording is treated as a disclosed case-vs-product mismatch, not
    something to force by inventing a second field.
  - "Logo Alt Text" (textbox, EN) / "Logo Alt Text — العربية" (textbox, AR).
  - "Display Order" (spinbutton).
  - "Active Status" (checkbox).
  - Two Month/Day/Year spinbutton triplets (likely Start/End Date fields)
    exist on the form but are OUT OF SCOPE for TC 136232 (not referenced by
    the case) — not modeled here.

CONFIRMED LIVE PUBLIC RENDERING (`/en/home`, Strategic Partners section,
`<h2>Strategic Partners</h2>`): each partner's logo renders as
`img.qc-sp-logo`, `alt` equal to the AUTHORED "Logo Alt Text" field value
verbatim (confirmed live: real records render `alt="QatarEnergy logo"`,
`alt="Qatar Airways logo"`, `alt="QNB logo"` — matching each record's own
Logo Alt Text, not a name+" logo" auto-derivation) — same duplicated-loop
marquee rendering pattern as Community Partners (12 `img.qc-sp-logo` nodes
for 3 active real partners, 4 copies each).
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage

SLUG = "strategic-partner"

PARTNER_NAME_LABEL = "Partner Name"
PARTNER_NAME_AR_LABEL = "Partner Name — العربية"
LOGO_IMAGE_LABEL = "Logo Image"
LOGO_ALT_TEXT_LABEL = "Logo Alt Text"
LOGO_ALT_TEXT_AR_LABEL = "Logo Alt Text — العربية"
DISPLAY_ORDER_LABEL = "Display Order"
ACTIVE_LABEL = "Active Status"

# Confirmed live this session — the 3 real, active records rendering on the
# public carousel (Ooredoo also exists in the admin list but did not render
# on the public carousel at read time — Active Status not confirmed True,
# out of scope for this test).
QATAR_ENERGY_NAME = "QatarEnergy"
QATAR_AIRWAYS_NAME = "Qatar Airways"
QNB_NAME = "QNB"


class StrategicPartnersAdminPage(ObjectAuthoringPage):
    """Strategic Partner's own field-level actions, composed on top of the
    generic Object Authoring Draft/Preview/Publish/Unpublish state machine.
    Every navigation/lifecycle/list method is inherited AS-IS from
    ObjectAuthoringPage — do not re-declare them here."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Field actions — this object's own labels only --------------------
    def set_partner_name_en(self, value: str) -> "StrategicPartnersAdminPage":
        self.fill_text(PARTNER_NAME_LABEL, value)
        return self

    def set_partner_name_ar(self, value: str) -> "StrategicPartnersAdminPage":
        self.fill_text(PARTNER_NAME_AR_LABEL, value)
        return self

    def set_logo_alt_text_en(self, value: str) -> "StrategicPartnersAdminPage":
        self.fill_text(LOGO_ALT_TEXT_LABEL, value)
        return self

    def set_logo_alt_text_ar(self, value: str) -> "StrategicPartnersAdminPage":
        self.fill_text(LOGO_ALT_TEXT_AR_LABEL, value)
        return self

    def set_display_order(self, value: str) -> "StrategicPartnersAdminPage":
        self.fill_number(DISPLAY_ORDER_LABEL, value)
        return self

    def set_active(self, active: bool) -> "StrategicPartnersAdminPage":
        self.set_checkbox(ACTIVE_LABEL, active)
        return self

    def is_active(self) -> bool:
        return self.page.get_by_role("checkbox", name=ACTIVE_LABEL, exact=True).is_checked()

    def upload_logo(self, file_path: str) -> "StrategicPartnersAdminPage":
        self.upload_file(LOGO_IMAGE_LABEL, file_path)
        return self

    def uploaded_logo_filename(self) -> str:
        return self.uploaded_filename(LOGO_IMAGE_LABEL)

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

CORRECTED/EXTENDED 2026-09-15 (live one-off retest of ADO Bug 139081 —
"Strategic Partner: End Date can be set earlier than Start Date"): the
previous entry above ("Month/Day/Year spinbutton triplets") was NOT
confirmed live and turned out to be wrong. The real, confirmed-live Start
Date / End Date fields are a bespoke Liferay Object date-picker widget
(`div.date-input` -> `div.qc-oel__dtp`), not native spinbuttons:
  - A VISIBLE text input (`input.qc-oel__dtp-text`, placeholder
    "dd/mm/yyyy", `type="text"`) is what a user types into — this is the
    element `set_start_date()`/`set_end_date()` below fill.
  - A HIDDEN native `<input type="date">` sibling (`aria-hidden="true"`,
    `tabindex="-1"`, `name="ObjectField_startDate"`/`ObjectField_endDate`)
    holds the real ISO value actually submitted — confirmed live it is
    populated from the visible text input only after a blur/Tab out of that
    field (typing alone does NOT sync it; `set_start_date()`/`set_end_date()`
    below press Tab after typing for exactly this reason).
  - The `<label for=...>` on this widget points at the HIDDEN native input's
    id, not the visible text input's — so `get_by_role("textbox",
    name="Start Date"/"End Date")` resolves to ZERO elements (the only
    accessibly-named match is `aria-hidden`, hence excluded from the
    accessibility tree) — confirmed live. `ObjectAuthoringPage.type_date()`
    (role-based) therefore does NOT work on this field; do not use it here.
    Both fields are scoped instead by their own stable wrapper
    (`div.date-input:has(label:has-text("Start Date"/"End Date"))`), which
    does not depend on the per-load `fragment-<uuid>` id.
  - Ids on this widget (`fragment-<uuid>-date-input`,
    `qc-dtp-fragment-<uuid>-date-input`) mint a fresh UUID per page load,
    same as every other field on this Liferay Page-Builder-fragment-backed
    surface (see ObjectAuthoringPage's own module docstring) — never hard-
    code one.

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

# Save-rejection banner — same `data-qc-oel-editbar`/generic-alert family
# already confirmed live on the sibling Content&Data surface for a duplicate-
# name rejection (see org_structure_admin_page.py's DUPLICATE_NAME_ERROR).
# Used here as the best-effort probe for an object-level validation-rule
# rejection (e.g. ADO Bug 139081's "Partnership Date Range Order" rule) —
# NOT independently confirmed live on THIS specific object/surface before
# this session's own probe (see save_error_text()/is_save_error_shown()).
SAVE_ERROR_BANNER = '[data-qc-oel-editbar], [role="alert"], .alert-danger'

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

    # ---- Start/End Date (bespoke qc-oel__dtp widget — see module docstring's
    # 2026-09-15 CORRECTED/EXTENDED note; NOT the generic
    # ObjectAuthoringPage.type_date(), which is role-based and does not
    # resolve on this field) -------------------------------------------------
    def _date_field_text_input(self, label: str):
        container = self.page.locator(f'div.date-input:has(label:has-text("{label}"))')
        return container.locator("input.qc-oel__dtp-text")

    def _date_field_hidden_input(self, label: str):
        container = self.page.locator(f'div.date-input:has(label:has-text("{label}"))')
        return container.locator('input[type="date"]')

    def set_start_date(self, value: str) -> "StrategicPartnersAdminPage":
        """`value` is typed exactly as shown in the field's own placeholder
        (dd/mm/yyyy). Blurs (Tab) afterward — confirmed live this is required
        for the visible text input to sync into the hidden native
        `<input type="date">` that actually gets submitted; typing alone does
        NOT sync it."""
        field = self._date_field_text_input("Start Date")
        field.click()
        field.fill("")
        self.page.keyboard.type(value, delay=20)
        self.page.keyboard.press("Tab")
        return self

    def set_end_date(self, value: str) -> "StrategicPartnersAdminPage":
        field = self._date_field_text_input("End Date")
        field.click()
        field.fill("")
        self.page.keyboard.type(value, delay=20)
        self.page.keyboard.press("Tab")
        return self

    def start_date_value(self) -> str:
        """ISO (yyyy-mm-dd) value of the real, submitted hidden field."""
        return self._date_field_hidden_input("Start Date").input_value()

    def end_date_value(self) -> str:
        return self._date_field_hidden_input("End Date").input_value()

    # ---- Save-rejection probe (see SAVE_ERROR_BANNER's own docstring) ------
    def save_error_text(self) -> str:
        banner = self.page.locator(self.SAVE_ERROR_BANNER)
        for i in range(banner.count()):
            try:
                text = banner.nth(i).inner_text().strip()
            except Exception:  # noqa: BLE001
                continue
            if text:
                return text
        return ""

    def is_save_error_shown(self) -> bool:
        return bool(self.save_error_text())

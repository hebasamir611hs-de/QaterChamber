"""
cms/pages/vision_mission_objectives/vmo_admin_page.py — VmoAdminPage.

Control_Panel admin surface for PBI 129395 (QC-ABOUT-004 — Vision, Mission,
Objectives). CONFIRMED LIVE 2026-09-07 (fresh CmsLoginPage session, qcdev):
the Object Authoring slug is `vmo-section` (title "Manage: VMO Section"),
confirmed only AFTER re-logging in fresh — the cached `.auth/cp_admin_state.json`
storageState had gone stale this session (every `manage-*` slug, including the
already-known-good `manage-general-manager-message`, rendered the generic
"Coming Soon" public fallback until a fresh `CmsLoginPage` login was performed
in the same test session). Confirms this project's own documented qcdev
session-expiry/connection-limit behavior (see cms/pages/control_panel/login_page.py) —
an infra characteristic, not a slug problem.

**Object shape, confirmed live (overrides this PBI's original singleton
assumption):** `vmo-section` is a 3-ENTRY object, one entry per section —
NOT one page-level record with 3 sub-blocks. Confirmed live entries on
qcdev: `QCDEMO-129395-VMO-VISION`, `QCDEMO-129395-VMO-MISSION`,
`QCDEMO-129395-VMO-OBJECTIVES` (all APPROVED at baseline), plus one
unrelated stray DRAFT entry (a bare UUID title) that predates this session
and is left untouched (not test-created, not ours to delete).

Confirmed-live per-entry field set (`get_by_role("textbox"/"checkbox"/"spinbutton",
name=<label>, exact=True)`, via ObjectAuthoringPage): Section Label (EN/AR),
Headline (EN/AR), Subheading (EN/AR), Body Content (EN/AR, rich text),
Section Image (file upload), Image Badge Label (EN/AR), Display Order
(spinbutton), Active (checkbox). There is NO page-level Page Title / Hero
Banner / Intro Heading / Intro Description field anywhere in this object —
those strings the case text describes do not exist as CMS-editable fields
on this surface (the public page's hero/intro markup — see
web/pages/vision_mission_objectives/vmo_page.py's HERO_TITLE/INTRO_HEADING —
render fixed copy with no corresponding admin control found). Per this
batch's established pattern (assert what's real, document the
discrepancy), tests that reference "page title"/"hero banner"/"intro"
content instead exercise the real per-section fields.

Baseline (confirmed live 2026-09-07, before any mutation this session):
    Vision:     Section Label "Vision",     Headline "INTERNATIONAL LEADERSHIP", Active=True, Approved
    Mission:    Section Label "Mission",    Headline "REPRESENT. SUPPORT. ELEVATE.", Active=True, Approved
    Objectives: Section Label "Objectives", Headline "FIVE PILLARS OF GROWTH",  Active=True, Approved
Display Order values were not readable via the textbox role (spinbutton
role failed to resolve within the probe's timeout live) — `display_order()`
below falls back through spinbutton/textbox/number-input locators and
should be treated as best-effort; tests key off PUBLIC section_number()
(web/pages/vision_mission_objectives/vmo_page.py) for renumbering
assertions instead, since that is what the case actually specifies.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage

SLUG = "vmo-section"

ENTRY_TITLE = {
    "vision": "QCDEMO-129395-VMO-VISION",
    "mission": "QCDEMO-129395-VMO-MISSION",
    "objectives": "QCDEMO-129395-VMO-OBJECTIVES",
}

BILINGUAL_TEXT_FIELDS = ["Section Label", "Headline", "Subheading", "Image Badge Label"]
AR_SUFFIX = " — العربية"


class VmoAdminPage(ObjectAuthoringPage):
    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Navigation convenience ------------------------------------------
    def open_entry(self, section_key: str) -> "VmoAdminPage":
        title = ENTRY_TITLE[section_key]
        self.open_entries_list()
        self.open_entry_by_edit_link(title)
        return self

    # ---- Snapshot / restore ------------------------------------------------
    def snapshot(self, section_key: str) -> dict:
        """Reads back every bilingual text field + Active — used to restore
        a real mutation in a `finally` block. Called on an already-open
        entry (see open_entry())."""
        snap = {}
        for field in BILINGUAL_TEXT_FIELDS:
            snap[field] = self.field_value(field)
            snap[field + AR_SUFFIX] = self.field_value(field + AR_SUFFIX)
        try:
            snap["Active"] = self.page.get_by_role("checkbox", name="Active").is_checked()
        except Exception:
            snap["Active"] = None
        snap["status"] = self.current_status()
        return snap

    def restore(self, section_key: str, snap: dict) -> "VmoAdminPage":
        """Re-opens the entry fresh, re-fills every snapshotted field, sets
        Active back, and re-publishes (Submit for Publishing) so the
        PUBLIC-facing state matches the true baseline — a restore that only
        Saves as Draft would leave the live site wrong (per this task's own
        coordination note)."""
        self.open_entry(section_key)
        if self.is_save_as_draft_disabled():
            # Approved entry -> must unpublish to edit, then republish after.
            self.unpublish_to_edit_as_draft()
        for field in BILINGUAL_TEXT_FIELDS:
            self.fill_text(field, snap[field])
            self.fill_text(field + AR_SUFFIX, snap[field + AR_SUFFIX])
        if snap.get("Active") is not None:
            self.set_checkbox("Active", snap["Active"])
        self.submit_for_publishing()
        return self

    def set_active(self, section_key: str, active: bool) -> "VmoAdminPage":
        self.open_entry(section_key)
        if self.is_save_as_draft_disabled():
            self.unpublish_to_edit_as_draft()
        self.set_checkbox("Active", active)
        self.submit_for_publishing()
        return self

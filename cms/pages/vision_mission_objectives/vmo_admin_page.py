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


# =============================================================================
# Phase 3 (2026-10-14) -- Object Authoring forms read live 2026-10-14
# (reports/probe-vmo-20261014.json, reports/probe-vmo-page-20261014.json),
# QC Site Content Editor.
#
# * `vision-mission-objectives-page` -- ONE record (singleton), code
#   QCDEMO-129395-VISION-MISSION-OBJECTIVES-PAGE-main, title
#   "Vision · Mission · Objectives". Fields: Page Title (+ AR *), Hero Image
#   (ONE image, no per-language twin; .jpg/.jpeg/.png/.svg <= 2 MB),
#   Intro Heading (+ AR *), Intro Description (+ AR, rich text), Active Status.
# * `vmo-section` -- three real rows (VISION / MISSION / OBJECTIVES) plus one
#   stray Draft (a bare UUID, not ours). Fields: Section Label (+ AR *),
#   Headline (+ AR *), Subheading (+ AR), Body Content (+ AR, rich text),
#   Section Image (.jpg/.png/.svg <= 2 MB), Image Badge Label (+ AR),
#   Display Order, Active Status.
# * Only the AR twins carry the "*" in their label on both forms.
# * As an Editor a Published row opens EDITABLE with a "Publish" button
#   ("Publish puts your change on the website straight away") -- no
#   Unpublish needed to edit. Row actions on a Published row: unpublish,
#   history, delete.
# =============================================================================
from cms.pages.components.disposable_object_admin import (  # noqa: E402
    DisposableObjectAdminPage,
    FieldSpec,
)

VMO_PAGE_SLUG = "vision-mission-objectives-page"
VMO_PAGE_CODE = "QCDEMO-129395-VISION-MISSION-OBJECTIVES-PAGE-main"
VMO_SECTION_CODES = {
    "vision": "QCDEMO-129395-VMO-VISION",
    "mission": "QCDEMO-129395-VMO-MISSION",
    "objectives": "QCDEMO-129395-VMO-OBJECTIVES",
}


class _VmoForm(DisposableObjectAdminPage):
    """Shared by both VMO objects: label-addressed fields, locale-picked
    CKEditor instances, the label-independent Publish control."""

    SLUG_CONFIRMED_LIVE = True
    PUBLISH_SUBMIT = 'button[type="submit"][name="status"][value="0"]'

    def _rich_iframe(self, key: str, locale: str) -> str:
        # Each form has exactly ONE bilingual rich-text field, so the two
        # CKEditor iframes on the page are EN (first) and AR (second).
        return f"{self.RICH_TEXT_EDITOR_IFRAME_CSS} >> nth={1 if locale == 'ar' else 0}"

    # ---- rich text, HTML-exact (CKEditor API) ------------------------------
    _EDITOR_JS = (
        "(loc) => { const ks = Object.keys(CKEDITOR.instances);"
        " const ar = ks.filter(k => /ar(_SA)?$/i.test(k) || /_ar_/i.test(k));"
        " const en = ks.filter(k => !ar.includes(k));"
        " const k = loc === 'ar' ? (ar[0] || ks[1]) : (en[0] || ks[0]);"
        " return k; }"
    )

    def editor_instance_names(self) -> list[str]:
        return self.page.evaluate("() => Object.keys(CKEDITOR.instances)")

    def rich_html(self, locale: str = "en") -> str:
        self.page.wait_for_function("() => window.CKEDITOR && Object.keys(CKEDITOR.instances).length >= 2",
                                    timeout=30000)
        name = self.page.evaluate(self._EDITOR_JS, locale)
        return self.page.evaluate("(n) => CKEDITOR.instances[n].getData()", name)

    def set_rich_html(self, html: str, locale: str = "en") -> None:
        self.page.wait_for_function("() => window.CKEDITOR && Object.keys(CKEDITOR.instances).length >= 2",
                                    timeout=30000)
        name = self.page.evaluate(self._EDITOR_JS, locale)
        self.page.evaluate(
            "([n, html]) => new Promise(resolve => { const ed = CKEDITOR.instances[n];"
            " ed.setData(html, { callback: () => { ed.updateElement(); ed.fire('change'); resolve(true); } }); })",
            [name, html],
        )

    def clear_rich_like_a_user(self, locale: str = "en") -> None:
        """Click into the editor body, Ctrl+A, Delete -- how an editor empties it."""
        body = self.page.frame_locator(self._rich_iframe("rich", locale)).locator("body")
        body.click()
        self.page.keyboard.press("Control+A")
        self.page.keyboard.press("Delete")

    # ---- open --------------------------------------------------------------
    def open_record(self, code: str, locale: str = "en") -> "_VmoForm":
        self.open_entry_by_code(code, locale=locale)
        return self

    def publish_click(self) -> list[tuple[str, str]]:
        """Click the form's status=0 control (Publish for an Editor) and return
        the controls the browser still flags invalid right after the click."""
        return self.submit_via_reading_validity(self.PUBLISH_SUBMIT)


VMO_PAGE_TITLE = "Vision · Mission · Objectives"


class VmoPageForm(_VmoForm):
    """The page singleton. Its entries-list row shows the record TITLE
    ("Vision · Mission · Objectives"), not the entry code (read live
    2026-10-14), so every row lookup by code is mapped to the title; the
    `?editEntry=` URL still takes the code."""

    SIDEBAR_LABEL = "Vision Mission Objectives Page"
    SLUG = VMO_PAGE_SLUG
    SINGLETON = True

    @staticmethod
    def _row_key(title_or_code: str) -> str:
        return VMO_PAGE_TITLE if title_or_code == VMO_PAGE_CODE else title_or_code

    def filter_entries(self, text: str):
        return super().filter_entries(self._row_key(text))

    def _row_locator(self, title_or_code: str):
        return super()._row_locator(self._row_key(title_or_code))

    def row_status_text_by_code(self, entry_code: str) -> str:
        return super().row_status_text_by_code(self._row_key(entry_code))

    def row_actions_by_code(self, entry_code: str) -> set:
        return super().row_actions_by_code(self._row_key(entry_code))

    def row_last_modified(self, title_or_code: str) -> str:
        return super().row_last_modified(self._row_key(title_or_code))
    FIELDS = {
        "page_title": FieldSpec("Page Title", bilingual=True, confirmed_live=True),
        "hero": FieldSpec("Hero Image", kind="file", confirmed_live=True),
        "intro_heading": FieldSpec("Intro Heading", bilingual=True, confirmed_live=True),
        "intro_desc": FieldSpec("Intro Description", kind="rich", bilingual=True, confirmed_live=True),
        "active": FieldSpec("Active Status", kind="checkbox", confirmed_live=True),
    }


class VmoSectionForm(_VmoForm):
    SIDEBAR_LABEL = "VMO Section"
    SLUG = SLUG
    FIELDS = {
        "label": FieldSpec("Section Label", bilingual=True, confirmed_live=True),
        "headline": FieldSpec("Headline", bilingual=True, confirmed_live=True),
        "subheading": FieldSpec("Subheading", bilingual=True, confirmed_live=True),
        "body": FieldSpec("Body Content", kind="rich", bilingual=True, confirmed_live=True),
        "image": FieldSpec("Section Image", kind="file", confirmed_live=True),
        "badge": FieldSpec("Image Badge Label", bilingual=True, confirmed_live=True),
        "order": FieldSpec("Display Order", kind="number", confirmed_live=True),
        "active": FieldSpec("Active Status", kind="checkbox", confirmed_live=True),
    }


# ---- picker search (titles drop the extension; the library has 50+ pages) ----
def _vmo_select_library_file(self, field_label: str, file_name: str) -> "_VmoForm":
    """Re-point `field_label` at an EXISTING Documents & Media file via the
    picker's own search box (the root listing shows TITLES without the
    extension and pages 20 at a time -- read live 2026-10-03 on the header
    logo picker, same widget). Raises when the file is not found."""
    import re as _re

    hidden = self.page.get_by_role("textbox", name=f"{field_label} Select File")
    hidden.locator("xpath=..").get_by_role("button", name="Select File").click()
    frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME).first
    stem = file_name.rsplit(".", 1)[0]
    box = frame.locator('input[name$="_keywords"]').first
    box.wait_for(state="visible", timeout=60000)
    box.fill(stem)
    box.press("Enter")
    frame.locator(f'input[name$="_keywords"][value="{stem}"]').first.wait_for(state="attached", timeout=60000)
    wanted = _re.compile(r"^\s*(" + _re.escape(stem) + "|" + _re.escape(file_name) + r")\s*$")
    hit = frame.locator(".card-title").filter(has_text=wanted)
    if hit.count() == 0:
        self.page.keyboard.press("Escape")
        raise AssertionError(f"{file_name!r} not found in the Documents & Media picker")
    hit.first.click()
    if not self._picker_closed(5000):
        hit.first.dblclick()
    if not self._picker_closed(8000):
        raise AssertionError(f"picker stayed open after selecting {file_name!r}")
    return self


_VmoForm.select_library_file = _vmo_select_library_file

"""
cms/pages/home_dynamic_widgets/home_dynamic_widgets_admin_page.py —
HomeDynamicWidgetsAdminPage.

Control_Panel Page Object for PBI 129384 (QC-HOME-008 — Home Page "Dynamic
Widgets": Marhaba Guide / B2B Platform / Weather), backing the "Dynamic
Widget" **Object Authoring** surface
(`https://qcdev.ihorizons.com/web/qatar-chamber/manage-dynamic-widget`) that
feeds the public Home Page `section.qc-home-dynamic-widgets` block (see
home_dynamic_widgets_page.py, `web/pages/home_dynamic_widgets/`, for the
public-frontend counterpart).

CORRECTED 2026-09-07 (mandatory re-verification per
`.claude/context/active/standards.md`'s "Object Authoring Is the Only Path
for Content Operations — Not Content & Data" section, broadened same day):
this file's PRIOR version drove every field write and every "publish"
action through `Content & Data`'s raw Object Definitions grid
(objectDefinitionId=49566) using its inline Active-Status checkbox as the
only lifecycle signal. That surface is retired for this project — a real,
dedicated Object Authoring surface exists for this exact object and was
CONFIRMED LIVE this session (Playwright MCP, qcdev, existing authenticated
super-admin session — not assumed):

  - **Slug: `dynamic-widget`** (singular) — confirmed live navigating
    `/web/qatar-chamber/manage-dynamic-widget` directly; it renders the
    same generic Save-as-Draft / Submit-for-Publishing / Unpublish-to-
    edit-as-draft state machine every other Object Authoring surface in
    this project uses (see `cms/pages/components/object_authoring_page.py`).
  - **Still a flat 2-entry object**, same identity mapping as before (no
    "widget name/type" field anywhere — see the historical note below):
    Entry-column code `QCDEMO-129384-directory` (redirects to
    qatarchamber.com, Display Order 100) mapped to **Marhaba Guide BY
    ELIMINATION ONLY** — the only other seeded entry besides the confirmed
    B2B row; Entry-column code `QCDEMO-129384-b2b-verified` (redirects to
    qcci.org, Display Order 200) **confirmed live** as B2B Platform (its
    public `.qc-dw-card` was independently observed). Both entries'
    workflow Status is `APPROVED` (confirmed live via the Content & Data
    grid's own Status column, and via this surface's editing-banner
    "(approved)" wording) — this IS an Object-Definition-backed record
    with real Draft/Approved lifecycle states, NOT a plain widget-config
    toggle like Upcoming Event Pins (record 49205) — do not conflate the
    two: Dynamic Widgets is the Business-Events/GM-Message class of
    surface, Upcoming Event Pins is the confirmed exception.
  - **Field labels on this surface, confirmed live** (all reachable via
    `page.get_by_role(<role>, name=<label>, exact=True)` per
    `ObjectAuthoringPage`'s generic helpers — no bilingual locale-toggle
    on this form, every field is EN-only): `Redirect URL` (textbox),
    `Display Order` (spinbutton), `Open in New Tab` (checkbox),
    `Active Status` (checkbox), `Widget Image (EN)` / `Widget Image (AR)`
    (file-upload fields, reached via `ObjectAuthoringPage.upload_file()`'s
    confirmed-live "<Field Label> Select File" hidden-textbox pattern).
  - **For an APPROVED entry, `Save as Draft` is disabled but `Submit for
    Publishing` remains enabled** (confirmed live via an accessibility
    snapshot of the real editing banner + button row) — editing a field
    (e.g. flipping Active Status) on an already-Approved entry and
    clicking `submit_for_publishing()` re-commits the same Approved
    record with the new value; there is no need to unpublish first for a
    plain field/toggle change on this object.
  - **No confirmed generic Liferay "success toast" was found on this
    surface** — a live, two-part investigation this session (a real
    `Submit for Publishing` on the `directory` entry with no field change,
    and a real `Save as Draft` on a fresh disposable test entry, both
    polled every ~100ms across the following ~1-2s for any
    `.alert`/`[role="alert"]`/`[role="status"]`/`[class*="toast"]` node
    with non-empty text) found NOTHING — both saves genuinely committed
    (confirmed via the entries list showing the new Draft rows / updated
    timestamp) but produced no visible toast this session. This mirrors
    `GmMessageAdminPage.SUCCESS_TOAST`'s own disclosed, never-confirmed
    placeholder for the same class of surface — TC 135969 is left
    disclosed/skipped in the test module rather than asserting on an
    invented selector (see that module's own docstring). Two disposable
    Draft rows (`0dc3833b-4059-d16e-1b6a-c87167be01b6`,
    `ad39bc5f-55b9-2b7c-0fe6-b4179c2399de`, redirect
    `https://qctest-toast-probe.example.com`) were created by this probe
    and are STILL PRESENT on qcdev — the delete action was blocked by this
    session's own destructive-action guard; flag back for manual cleanup
    or an explicit user-approved delete, do not delete unattended.
  - **Weather still has no confirmed control-panel surface anywhere** —
    re-checked this session (no "Weather" Object Definition entry in the
    Product Menu's Content & Data app list, and no `manage-weather*` slug
    resolved) — same finding as the prior (Content & Data-era) version of
    this file; TC 135968 remains skipped in the test module for the same
    disclosed reason, now re-confirmed under the Object-Authoring-first
    search too.

HISTORICAL NOTE (Content & Data-era finding, still true of the underlying
data model, kept for context): the object has no "widget name/type" field
anywhere — the grid columns are Item Selection, ID, Active Status, Display
Order, Open in New Tab, Redirect URL, Widget Image (AR), Widget Image (EN),
Status, Author, Item Actions — identity is only inferable from each
record's `externalReferenceCode`, which IS what the Object Authoring
surface's own Entry column renders (confirmed live), unlike this project's
other ERC-only object, manage-strategic-pillar-card.

DISPLAY ORDER — SHARED/RELATIVE ORDERING, still applies on this surface
(same underlying Object Definition data, only the editing surface
changed): both entries live under the same object and the public Home page
renders `.qc-dw-card` elements in the same relative order as their Display
Order values. Every test below captures BOTH entries' full baseline
(`active`, `open_in_new_tab`, `display_order`, `redirect_url`) and restores
BOTH in `finally`, not just the one it directly touched.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage

SLUG = "dynamic-widget"

# CORRECTED 2026-09-07 (tc_135966 investigation): the original timeout seen
# here was NOT this surface's own render latency — it was a stale
# `.auth/state.json` (session already expired), so the editing banner never
# rendered at all (the page was effectively unauthenticated) and no
# timeout value would have fixed it. Separately, a real cross-surface bug
# was found and fixed in the SHARED component instead of here: a bare
# `wait_for_load_state("networkidle")` in `ObjectAuthoringPage.
# open_entry_by_code()`/`open_entry_by_edit_link()` could hang the full
# Playwright default (30000ms) because this page's network never fully
# idles (site-wide chatbot-widget polling — the same finding
# `_wait_for_settle()` already documented for a different call site). See
# `ObjectAuthoringPage._wait_for_network_settle()`. No local override is
# needed here anymore — `open_entry()` below uses the shared
# `open_entry_by_code()` directly at its normal
# `APPROVED_BANNER_SETTLE_TIMEOUT_MS` (8000ms) budget, confirmed live to be
# sufficient once authenticated.

# Entry-column codes (== externalReferenceCode) — see module docstring's
# identity-mapping note for the disclosed Marhaba-by-elimination caveat.
MARHABA_ENTRY_CODE = "QCDEMO-129384-directory"
B2B_ENTRY_CODE = "QCDEMO-129384-b2b-verified"

FIELD_REDIRECT_URL = "Redirect URL"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_OPEN_IN_NEW_TAB = "Open in New Tab"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_WIDGET_IMAGE_EN = "Widget Image (EN)"
FIELD_WIDGET_IMAGE_AR = "Widget Image (AR)"


class HomeDynamicWidgetsAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) with this object's own field map. Constructed
    with just `page` (slug is fixed to "dynamic-widget" for this class,
    unlike the shared base class's own `__init__(page, slug)` signature)."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Navigation ---------------------------------------------------------
    def open_entry(self, entry_code: str) -> "HomeDynamicWidgetsAdminPage":
        self.open_entry_by_code(entry_code)
        return self

    def open_marhaba_entry(self) -> "HomeDynamicWidgetsAdminPage":
        """See MARHABA_ENTRY_CODE's docstring note: this entry is mapped
        onto Marhaba Guide BY ELIMINATION (the only other seeded entry
        besides the confirmed B2B one), not by a live-confirmed "Marhaba"
        label anywhere on this surface."""
        return self.open_entry(MARHABA_ENTRY_CODE)

    def open_b2b_entry(self) -> "HomeDynamicWidgetsAdminPage":
        """Confirmed live: redirects to qcci.org, renders as the B2B
        `.qc-dw-card` on the public Home page."""
        return self.open_entry(B2B_ENTRY_CODE)

    # ---- Field actions (thin, named wrappers over the base class's generic
    # role-based helpers) ------------------------------------------------------
    def set_redirect_url(self, value: str) -> "HomeDynamicWidgetsAdminPage":
        self.fill_text(FIELD_REDIRECT_URL, value)
        return self

    def redirect_url_value(self) -> str:
        return self.field_value(FIELD_REDIRECT_URL)

    def set_display_order(self, value: str) -> "HomeDynamicWidgetsAdminPage":
        self.fill_number(FIELD_DISPLAY_ORDER, value)
        return self

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).input_value()

    def set_open_in_new_tab(self, enabled: bool) -> "HomeDynamicWidgetsAdminPage":
        self.set_checkbox(FIELD_OPEN_IN_NEW_TAB, enabled)
        return self

    def is_open_in_new_tab(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_OPEN_IN_NEW_TAB, exact=True).is_checked()

    def set_active(self, active: bool) -> "HomeDynamicWidgetsAdminPage":
        self.set_checkbox(FIELD_ACTIVE_STATUS, active)
        return self

    def is_active(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    def upload_widget_image_en(self, file_path: str) -> "HomeDynamicWidgetsAdminPage":
        self.upload_file(FIELD_WIDGET_IMAGE_EN, file_path)
        return self

    def upload_widget_image_ar(self, file_path: str) -> "HomeDynamicWidgetsAdminPage":
        self.upload_file(FIELD_WIDGET_IMAGE_AR, file_path)
        return self

    def widget_image_en_filename(self) -> str:
        return self.uploaded_filename(FIELD_WIDGET_IMAGE_EN) or self._current_file_from_placeholder(
            FIELD_WIDGET_IMAGE_EN
        )

    def widget_image_ar_filename(self) -> str:
        return self.uploaded_filename(FIELD_WIDGET_IMAGE_AR) or self._current_file_from_placeholder(
            FIELD_WIDGET_IMAGE_AR
        )

    def _current_file_from_placeholder(self, field_label: str) -> str:
        """Fallback for this surface's own idiosyncrasy — CONFIRMED LIVE
        2026-09-07 (Playwright MCP, manage-dynamic-widget, entry
        QCDEMO-129384-directory): the shared ObjectAuthoringPage.
        uploaded_filename()'s `<strong role="textbox">` readout (confirmed
        live and correct on manage-promotional-banner) stays EMPTY on this
        surface for an image that is already committed and being viewed
        after a fresh page load/reload (e.g. right after
        submit_for_publishing() + re-opening the entry) — the real filename
        instead only shows as the field's OWN hidden `"<Field Label> Select
        File"` textbox's placeholder text, literally
        "Current file: <name> — pick a file to replace it". Kept local
        (not raised into the shared component) since manage-promotional-
        banner's own confirmed-live behavior must not be touched by this
        object's quirk."""
        hidden_textbox = self.page.get_by_role("textbox", name=f"{field_label} Select File")
        placeholder = hidden_textbox.get_attribute("placeholder") or ""
        prefix = "Current file:"
        if not placeholder.startswith(prefix):
            return ""
        return placeholder[len(prefix):].split(" — ")[0].strip()

    # ---- Baseline capture/restore -------------------------------------------
    def capture_baseline(self, entry_code: str) -> dict:
        self.open_entry(entry_code)
        return {
            "entry_code": entry_code,
            "active": self.is_active(),
            "open_in_new_tab": self.is_open_in_new_tab(),
            "display_order": self.display_order_value(),
            "redirect_url": self.redirect_url_value(),
        }

    def restore(self, baseline: dict) -> "HomeDynamicWidgetsAdminPage":
        self.open_entry(baseline["entry_code"])
        self.set_active(baseline["active"])
        self.set_open_in_new_tab(baseline["open_in_new_tab"])
        self.set_display_order(baseline["display_order"])
        self.set_redirect_url(baseline["redirect_url"])
        self.submit_for_publishing()
        return self

"""
web/pages/about_chairman_message/chairman_message_admin_page.py — ChairmanMessageAdminPage.

PBI 129393 / QC-ABOUT-002 "Chairman's Message" — Control_Panel-tagged cases
(ADO 134759, 134760, 134774, 134776, 134777, 134778, 134779, 134780, 134783,
134784, 134787, 134828, 134829, 134834): the Liferay "Chairman Message Page"
Object Definition entry that drives the public
/web/qatar-chamber/about-us/chairman-message page (see chairman_message_page.py
for the public-frontend counterpart).

CORRECTED 2026-09-07 (per .claude/context/active/standards.md's "Object
Authoring Is the Only Path for Content Operations — Not Content & Data",
superseded/broadened same day): an EARLIER version of this file drove every
field/lifecycle action through Content & Data (objectDefinitionId=78084) —
that surface is RETIRED project-wide for this kind of record, not merely for
publish/unpublish/draft/preview but for field edits too. This file now
composes `ObjectAuthoringPage` (cms/pages/components/object_authoring_page.py)
— the same generic, per-object-agnostic Page Object `GmMessageAdminPage` /
other already-migrated admin pages use — exactly per that file's own
convention: field-level locators (here, accessible-name label CONSTANTS,
since this surface has no stable ids/classes and is driven via
`page.get_by_role(<role>, name=<label>, exact=True)`) stay on THIS class;
the generic Draft/Preview/Publish/Unpublish state machine stays on
`ObjectAuthoringPage` and is never duplicated here.

REAL, CLI-CONFIRMED FACTS (2026-09-07, headless Chromium against qcdev,
authenticated via `.auth/state.json`; a second, disclosed, scoped Playwright
script — still CLI, never the Playwright MCP — since `tools/extract_locators.py`'s
static harvester does not resolve accessible names the way
`get_by_role(..., name=...)` does):

  - **Slug**: `chairman-message-page` (i.e. `manage-chairman-message-page`),
    confirmed live via the Object Authoring listing page
    (`https://qcdev.ihorizons.com/object-authoring`) — "Chairman Message
    Page" -> `/web/qatar-chamber/manage-chairman-message-page`.
  - **Singleton entry code**: `QCDEMO-129393-chairmans-message` (the entries
    table's own Entry-column text; confirmed live, one row, Status
    "APPROVED").
  - **Field labels** (confirmed live via `page.accessibility.snapshot()` on
    the opened entry, matched with `get_by_role(<role>, name=<label>,
    exact=True)` — trailing whitespace in the raw accessible name of some
    fields, e.g. `"Page Title "`, does NOT prevent `exact=True` from
    matching the plain, trimmed label; confirmed live for every field
    below): each bilingual field renders as TWO separately-named textboxes
    (`"<Label>"` for EN, `"<Label> — العربية"` for AR) — no locale-toggle
    click needed, exactly the pattern `object_authoring_page.py`'s own
    `field_value()` docstring already documents for GM's Message. Field
    inventory confirmed live, in on-screen order: Page Title, Hero Banner
    Image (upload), Hero Banner Alt Text, Chairman Portrait (upload),
    Chairman Portrait Alt Text, Chairman Name, Chairman Designation,
    Message Content (rich text, 2 CKEditor instances EN/AR — same
    `DESCRIPTION_EDITOR_IFRAME`/`fill_rich_text()`/`rich_text_value()`
    generic mechanism `ObjectAuthoringPage` already provides), Hyperlink
    Title, Hyperlink URL (NOT bilingual — confirmed live, no
    "— العربية" counterpart), Status (an extra, redundant combobox on this
    particular object — NOT used; the real lifecycle actions are the
    generic Save as Draft / Submit for Publishing / Unpublish to edit as
    draft buttons `ObjectAuthoringPage` already exposes).
  - **Preview IS a real, working mechanism on this surface** — CONFIRMED
    LIVE, correcting an EARLIER (Content & Data-based) finding that
    wrongly concluded no Preview mechanism exists for this object (that
    finding was reached through the now-retired surface — see standards.md's
    explicit warning to re-verify rather than assume a Content & Data-era
    finding still holds). The entries list's own row-level "Preview" link
    (`ObjectAuthoringPage.row_preview_url_by_code()`, scoped by this
    object's Entry-column CODE since it shows the externalReferenceCode,
    not a friendly title) resolves to
    `/web/qatar-chamber/about-us/chairman-message?qcPreview=chairmanmessagepages%3A78261`
    — a real navigation to the live public page with that record pinned for
    preview, confirmed live to render the status banner
    "PREVIEW — showing a published chairmanmessagepages record, exactly as
    visitors see it." (or the Draft equivalent) via
    `ObjectAuthoringPage.preview_banner_text()`.
  - **No Download mechanism exists for the Chairman Portrait / Hero Banner
    Image fields on this surface** (confirmed live via the full
    accessibility-tree button inventory near both upload fields: only
    "Select File" and "Remove file" — no "Download"), which is WORSE than
    the (also real, but now-retired) Content & Data surface's own Download
    button for the same field. This is why TC 134783 (Replace Portrait) and
    134784 (Upload for the first time) remain scripted as SKIPPED in the
    test module rather than executed — see that module's docstring.

**⚠ REAL, LIVE, DISCLOSED CONTENT FINDING (2026-09-07) — independently
re-confirmed THREE separate ways this session, not a script bug:** (1)
reading `Page Title`/`Chairman Name`/`Chairman Designation`/etc. via the
(now-retired) Content & Data surface, (2) reading the SAME fields via this
corrected Object Authoring surface, and (3) loading the PUBLIC page itself
in a genuinely fresh, unauthenticated browser context — ALL THREE report
**Arabic text** for what this record's own English ("en-us"/default-locale)
fields are supposed to hold (e.g. Chairman Name reads "الشيخ خليفة بن جاسم بن
محمد آل ثاني", Page Title reads "رسالة رئيس مجلس الإدارة" — the Arabic
translation of "Chairman's Message"). This directly contradicts the values
several EXISTING (uncommitted, prior-session) assertions in
`chairman_message_page.py` / `test_chairman_message_web.py` assume are
currently live (English). Root cause undetermined — flagged to the QA
Manager, not silently resolved or worked around. This does NOT block
automating the 8 cases in this batch: every CMS-mutating test here is
TEST_OWNED (cms-profile.md's Test-Data Policy) — it dynamically READS the
record's current value immediately before mutating and restores that SAME
captured value in `finally`, regardless of language, rather than assuming
any particular baseline.

Every OTHER Control_Panel case in this PBI's batch NOT in the current 8-case
scope (134759, 134760, 134779, 134828, 134829, 134834, plus the audit-log
half of any case) still reflects the OLDER, now-superseded Content & Data
findings from 2026-09-01 — flagged here, not silently left stale, for
whichever future pass migrates those to Object Authoring too.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from core.web.base_page import BasePage

# ---- Object Authoring path — the ONLY correct path for this record per
# standards.md's 2026-09-07 rule (confirmed live, see module docstring) -----
CHAIRMAN_MESSAGE_OBJECT_AUTHORING_SLUG = "chairman-message-page"
CHAIRMAN_MESSAGE_ENTRY_CODE = "QCDEMO-129393-chairmans-message"


class ChairmanMessageAdminPage(BasePage):
    """Thin holder of this object's field-label constants + entry
    identity. All navigation/state/lifecycle behaviour is delegated to
    `ObjectAuthoringPage` via `open_object_authoring_form()` — this class
    does not duplicate that state machine (see module docstring)."""

    # ---- Field labels — accessible names, confirmed live 2026-09-07 (see
    # module docstring). Bilingual fields: pass the plain label for EN, or
    # f"{LABEL} — العربية" for AR, directly to ObjectAuthoringPage.fill_text()
    # / .field_value() — no locale-toggle click needed on this surface. -----
    PAGE_TITLE_LABEL = "Page Title"
    HERO_BANNER_ALT_TEXT_LABEL = "Hero Banner Alt Text"
    CHAIRMAN_PORTRAIT_ALT_TEXT_LABEL = "Chairman Portrait Alt Text"
    CHAIRMAN_NAME_LABEL = "Chairman Name"
    CHAIRMAN_DESIGNATION_LABEL = "Chairman Designation"
    HYPERLINK_TITLE_LABEL = "Hyperlink Title"  # not bilingual — confirmed live
    HYPERLINK_URL_LABEL = "Hyperlink URL"  # not bilingual — confirmed live
    CHAIRMAN_PORTRAIT_UPLOAD_LABEL = "Chairman Portrait"
    HERO_BANNER_IMAGE_UPLOAD_LABEL = "Hero Banner Image"
    ARABIC_SUFFIX = " — العربية"

    # HEALED 2026-09-07 (live incident, tc_134777 — see
    # ObjectAuthoringPage.DESCRIPTION_EDITOR_IFRAME's own docstring for the
    # full investigation): Message Content's EN/default-locale CKEditor
    # iframe DOM id is confirmed live to always contain
    # `ObjectField_messageContent` (Liferay's own canonical object-field
    # name for this field), independent of DOM mount order — pass this to
    # `ObjectAuthoringPage.fill_rich_text()`/`.rich_text_value()`'s
    # `field_name` parameter for a locale-safe, reflow-safe read/write of
    # this field, instead of the class's default `nth=0` mount-order guess.
    MESSAGE_CONTENT_FIELD_NAME = "messageContent"

    def __init__(self, page):
        super().__init__(page)

    def open_object_authoring_form(self) -> "ObjectAuthoringPage":
        """Opens the singleton Chairman's Message entry via Object
        Authoring — the ONLY correct path for any field edit or lifecycle
        action on this record (see module docstring). Returns the
        `ObjectAuthoringPage` directly; callers use its own
        fill_text()/field_value()/fill_rich_text()/rich_text_value()/
        save_as_draft()/submit_for_publishing()/unpublish_to_edit_as_draft()/
        current_status()/row_preview_url_by_code()/preview_banner_text()
        API, per this project's established convention (see
        GmMessageAdminPage.open_object_authoring_form() for the identical
        pattern on a sibling object)."""
        authoring = ObjectAuthoringPage(self.page, slug=CHAIRMAN_MESSAGE_OBJECT_AUTHORING_SLUG)
        authoring.open_entry_by_code(CHAIRMAN_MESSAGE_ENTRY_CODE)
        return authoring

    def open_entries_list(self) -> "ObjectAuthoringPage":
        """Opens the entries list (not a specific entry's edit form) — used
        to resolve the row-level Preview link via
        `row_preview_url_by_code(CHAIRMAN_MESSAGE_ENTRY_CODE)` (TC 134778),
        since that link is not present on the edit form itself."""
        authoring = ObjectAuthoringPage(self.page, slug=CHAIRMAN_MESSAGE_OBJECT_AUTHORING_SLUG)
        authoring.open_entries_list()
        return authoring

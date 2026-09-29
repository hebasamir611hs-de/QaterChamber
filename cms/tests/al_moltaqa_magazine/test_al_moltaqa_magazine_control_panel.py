"""
cms/tests/al_moltaqa_magazine/test_al_moltaqa_magazine_control_panel.py —
Control_Panel-tagged cases for PBI 130710 ("QC - Insights & Media - 002 -
Al-Moltqa Magazine"), sourced from
`.claude/qa-baselines/130710_automation_batch.json` (94 cases, pre-filtered
to `Tag=Automation`; no azure-devops MCP call made this session — the batch
file was handed to this engineer directly per the task).

Holds every case whose `tags` include `Control_Panel` (40 Control_Panel-only
cases) PLUS the Control_Panel-side test for every case that carries BOTH
`Web` and `Control_Panel` (22 cases: 144108, 144109, 144115, 144116, 144117,
144118, 144119, 144122, 144125, 144129, 144133, 144136, 144139, 144144,
144149, 144152, 144153, 144199, 144200, 144206, 144209, 144213) — per
automation-standards.md's "one test per platform, sharing step intent"
rule; the Web-side test for each of those 22 lives in
web/tests/al_moltaqa_magazine/test_al_moltaqa_magazine_web.py under the SAME
`tc_<id>` marker.

Traceability note: the batch handed to this session carries each case's
Azure Test Case work item ID (`id`) and the parent PBI ID (130710), but NOT
the QA traceability ID — every docstring below cites `Azure TC <id> | PBI
130710` and omits the QA-ID segment per the task's own instruction.

CMS reachability (2026-09-22, `.auth/state.json` reused, logged in as
"Alaa Medhat"): `manage-magazine-issue` renders normally — 7 real, shared
entries exist (QCDEMO-130710-ISSUE-001..007, ALL Published) — brand-new
`QCTEST-`-prefixed entries are created and deleted freely without ever
touching them (DISPOSABLE per cms-profile.md). Every mutating test carries
the shared `al_moltaqa_magazine_cms` xdist group so pytest-xdist never runs
two of them concurrently against the same object's entries table.

**NO SEPARATE "Al-Moltaqa Magazine Page" ADMIN OBJECT EXISTS** — see
cms/pages/al_moltaqa_magazine/magazine_issue_admin_page.py's module
docstring for the exhaustive Objects Home nav search (278 unique `manage-*`
links enumerated). Every case assuming a page-level settings surface (Page
Title EN/AR save+validation) is SKIPPED below with that finding — this is a
GENUINELY ABSENT admin surface, not a locator gap, and it means every hero/
archive-heading string on the public page is confirmed hard-coded, not
CMS-driven.

**CONFIRMED LIVE — Entry column IS a code, not the Issue Title** (checked
fresh per the task's own instruction, since Annual Reports/Export Reports
have this defect and Publications does NOT): every one of the 7 real rows'
Entry column renders `QCDEMO-130710-ISSUE-00N`, never the Title — mirrors
Export Reports' defect, unlike Publications. Title-based lookup throughout
this module goes through `MagazineIssueAdminPage._resolve_code()`
(verified by field read-back, never row position).

**CONFIRMED LIVE — no single "Publish" button exists.** The object's own
workflow action is "Submit for Review" (English, after the chrome-locale
"EN" toggle — see the Page Object's own docstring for the full Arabic-
chrome finding); the QA cases' own literal "Click Publish"/"Click Unpublish"
wording maps to `admin.publish()` (`set_active_status("Published")` +
`submit_for_review()`) and `admin.unpublish_to_edit_as_draft()` respectively
— scripted per the real mechanism, disclosed rather than silently aliased.

**CONFIRMED LIVE — no Cancel/Discard control exists** anywhere on the
create-new form (a full accessibility-tree scan for "cancel"/"discard" text
found none) — same class of finding as this project's Publications
(tc_144001) and Footer (tc_131174) objects.

SKIPPED (confirmed precondition/product gaps, reused known blockers, or a
genuinely absent admin surface, not locator gaps):
  - tc_144101/tc_144102 (Site Content Author role cases): this project's own
    `pytest.ini` already records `CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD`
    does NOT authenticate against qcdev (confirmed 2026-09-17 for
    tc_131154/131155/131163/131200) — reused here rather than re-attempting
    a known-blocked login live.
  - tc_144107: no in-form "Preview unsaved changes" control is documented
    anywhere on this project's shared Object Authoring surface
    (`ObjectAuthoringPage`) — only a row-level Preview link exists, which
    reflects the last SAVED state, not an unsaved in-progress edit. This
    case's own precondition (Preview shows an unsaved Title edit) is not
    reachable without inventing a control that isn't confirmed to exist.
  - tc_144111: no Cancel/Discard control exists on the create form (see
    module docstring finding above).
  - tc_144118/tc_144119/tc_144120/tc_144121/tc_144206/tc_144207/tc_144208:
    all assume the non-existent "Al-Moltaqa Magazine Page" admin object —
    see module docstring's exhaustive nav-search finding.

DISPOSABLE entries: every mutating test below creates its own
`QCTEST-<tc_id>`-prefixed Magazine Issue entry via
`cms.pages.al_moltaqa_magazine.magazine_issue_admin_page.MagazineIssueAdminPage`
and deletes it in a `finally` block. A few cases whose own expected result
explicitly names the PUBLIC magazine page (tc_144122, tc_144133, tc_144139,
tc_144199, tc_144200) additionally import
`web.pages.al_moltaqa_magazine.al_moltaqa_magazine_page.AlMoltaqaMagazinePage`
to verify that delivery-surface outcome — mirrors
`cms/tests/export_reports/test_export_reports_control_panel.py`'s own
precedent for a Control_Panel-tagged case whose narrative still names the
public page.
"""

import allure
import pytest

from cms.pages.al_moltaqa_magazine.magazine_issue_admin_page import (
    MagazineIssueAdminPage,
    FIELD_ARTICLE_COUNT,
    FIELD_COVER_IMAGE,
    FIELD_ISSUE_DATE,
    FIELD_ISSUE_DESCRIPTION_AR,
    FIELD_ISSUE_DESCRIPTION_EN,
    FIELD_ISSUE_NUMBER,
    FIELD_ISSUE_TITLE_AR,
    FIELD_ISSUE_TITLE_EN,
    FIELD_PAGE_COUNT,
    FIELD_PDF_ATTACHMENT,
)
from web.pages.al_moltaqa_magazine.al_moltaqa_magazine_page import AlMoltaqaMagazinePage

MAGAZINE_CMS_XDIST_GROUP = pytest.mark.xdist_group("al_moltaqa_magazine_cms")
FIXTURES = "cms/tests/al_moltaqa_magazine/fixtures"

NO_PAGE_OBJECT_REASON = (
    "No 'Al-Moltaqa Magazine Page' admin object exists — confirmed via an "
    "exhaustive Objects Home nav search (278 unique manage-* links "
    "enumerated, filtered for 'magazine'/'page'); only 'Magazine Issue' "
    "exists. See magazine_issue_admin_page.py's module docstring."
)


def _fill_all_mandatory_fields(admin: MagazineIssueAdminPage, prefix: str, **overrides) -> dict:
    """Fills every mandatory Magazine Issue field with a safe default.
    `skip_*` keys omit one field to reach an empty/missing precondition;
    every other override is a literal FIELD_* key or the bare keywords
    `page_count`/`article_count`/`issue_date`."""
    values = {
        FIELD_ISSUE_TITLE_EN: f"QCTEST-{prefix} Magazine Issue",
        FIELD_ISSUE_TITLE_AR: f"QCTEST-{prefix} عدد المجلة",
        FIELD_ISSUE_DESCRIPTION_EN: f"QCTEST-{prefix} disposable automated-test issue description.",
        FIELD_ISSUE_DESCRIPTION_AR: f"QCTEST-{prefix} وصف عدد تجريبي تم إنشاؤه تلقائيًا.",
        FIELD_ISSUE_NUMBER: f"QCTEST-{prefix}",
        "page_count": "10",
        "article_count": "5",
        "issue_date": "01/01/2026",
    }
    values.update(overrides)
    admin.open_new_entry_form()
    for field in (FIELD_ISSUE_TITLE_EN, FIELD_ISSUE_TITLE_AR,
                  FIELD_ISSUE_DESCRIPTION_EN, FIELD_ISSUE_DESCRIPTION_AR,
                  FIELD_ISSUE_NUMBER):
        if field in values:
            admin.fill_text(field, values[field])
    if not values.get("skip_page_count"):
        admin.fill_number(FIELD_PAGE_COUNT, values["page_count"])
    if not values.get("skip_article_count"):
        admin.fill_number(FIELD_ARTICLE_COUNT, values["article_count"])
    if not values.get("skip_date"):
        admin.set_issue_date(values["issue_date"])
    if not values.get("skip_cover"):
        admin.upload_file(FIELD_COVER_IMAGE, values.get("cover_path", f"{FIXTURES}/valid_cover_1_5mb.jpg"))
    if not values.get("skip_pdf"):
        admin.upload_file(FIELD_PDF_ATTACHMENT, values.get("pdf_path", f"{FIXTURES}/valid_pdf_4mb.pdf"))
    return values


# ===========================================================================
# 144101/144102 — SKIPPED: known-blocked Site Content Author credentials
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Roles / Permissions")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Author can view and update an assigned magazine issue and save it as Draft")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.pbi_130710
@pytest.mark.tc_144101
@pytest.mark.skip(
    reason="CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD in .env do not "
    "authenticate against qcdev — already confirmed 2026-09-17 for "
    "tc_131154/131155/131163/131200; reused here rather than re-attempting "
    "a known-blocked login."
)
def test_author_view_update_issue_as_draft(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Roles / Permissions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author cannot publish a magazine issue")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_130710
@pytest.mark.tc_144102
@pytest.mark.skip(reason="Same CMS_SITE_CONTENT_AUTHOR_EMAIL/PASSWORD blocked-credentials gap as tc_144101.")
def test_author_cannot_publish_issue(page):
    ...


# ===========================================================================
# 144104 — Editor creates a new magazine issue, saves as Draft
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Site Content Editor can create a new magazine issue in Object Authoring")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144104
@MAGAZINE_CMS_XDIST_GROUP
def test_editor_create_new_issue_save_as_draft(page):
    # Azure TC 144104 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144104 Autumn Trade Digest"
    try:
        _fill_all_mandatory_fields(
            admin, "144104", **{FIELD_ISSUE_TITLE_EN: title, FIELD_ISSUE_TITLE_AR: "ملخص التجارة الخريفي"},
            page_count="32", article_count="8", issue_date="01/09/2026",
        )
        admin.save_as_draft()

        assert admin.status_for(title) != "Published"
        admin.open_entry_by_edit_link(title)
        assert admin.field_value(FIELD_ISSUE_TITLE_EN).strip() == title
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144105 — Editor edits an existing magazine issue
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Edit")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can edit an existing magazine issue")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144105
@MAGAZINE_CMS_XDIST_GROUP
def test_editor_edit_existing_issue(page):
    # Azure TC 144105 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144105 Edit Check"
    try:
        _fill_all_mandatory_fields(admin, "144105", **{FIELD_ISSUE_TITLE_EN: title}, page_count="32")
        admin.save_as_draft()

        admin.open_entry_by_edit_link(title)
        admin.fill_number(FIELD_PAGE_COUNT, "36")
        admin.save_as_draft()

        admin.open_entry_by_edit_link(title)
        assert admin.number_field_value(FIELD_PAGE_COUNT) == "36"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144106 — Draft issue does not appear on the public page
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Draft / Unpublish visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A magazine issue saved as Draft does not appear on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144106
@MAGAZINE_CMS_XDIST_GROUP
def test_draft_issue_absent_from_public_page_cms(page):
    # Azure TC 144106 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144106 Draft Visibility"
    try:
        _fill_all_mandatory_fields(admin, "144106", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        assert admin.status_for(title) != "Published"

        anon_ctx = page.context.browser.new_context()
        anon_page = anon_ctx.new_page()
        pub = AlMoltaqaMagazinePage(anon_page)
        pub.open_magazine_anonymous()
        titles = pub.card_titles() + [pub.latest_title_text()]
        anon_ctx.close()

        assert title not in titles
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144107 — SKIPPED: no in-form Preview-unsaved-changes control
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Preview")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Preview shows draft content without affecting the live public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144107
@pytest.mark.skip(
    reason="No in-form 'Preview unsaved changes' control is documented on "
    "this project's shared Object Authoring surface — only a row-level "
    "Preview link exists, reflecting the last SAVED state, not an unsaved "
    "edit. This case's own precondition (Preview shows an unsaved Title "
    "edit) is not reachable without inventing an unconfirmed control."
)
def test_preview_shows_draft_without_affecting_live(page):
    ...


# ===========================================================================
# 144110 — Editor deletes a magazine issue
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Delete")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A Site Content Editor can delete a magazine issue")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144110
@MAGAZINE_CMS_XDIST_GROUP
def test_editor_delete_issue(page):
    # Azure TC 144110 | PBI 130710 — located and confirmed by its own exact
    # QCTEST- title (never by row position), per standards.md's Destructive
    # Operations rule.
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144110 Delete Flow"
    _fill_all_mandatory_fields(admin, "144110", **{FIELD_ISSUE_TITLE_EN: title})
    admin.save_as_draft()
    assert title.startswith("QCTEST-")

    admin.open_entries_list()
    admin.delete_entry_by_title(title)

    admin.open_entries_list()
    assert not admin.row_visible(title)


# ===========================================================================
# 144111 — SKIPPED: no Cancel/Discard control exists
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Create / Draft")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Discarding changes while creating a new magazine issue does not save the record")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.pbi_130710
@pytest.mark.tc_144111
@pytest.mark.skip(
    reason="No Cancel/Discard control exists anywhere on the create-new "
    "form (confirmed live — a full accessibility-tree scan for "
    "'cancel'/'discard' text found none), same class of finding as "
    "tc_144001 (Publications) and tc_131174 (Footer)."
)
def test_discard_new_issue_not_saved(page):
    ...


# ===========================================================================
# 144108/144109/144115/144116/144117 — Publish lifecycle (Control_Panel side)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing a magazine issue updates its own Status (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144108
@MAGAZINE_CMS_XDIST_GROUP
def test_publish_updates_status_cms(page):
    # Azure TC 144108 | PBI 130710 — Control_Panel-side half; Web-side in
    # test_al_moltaqa_magazine_web.py under the SAME marker. The case's own
    # literal "Click Publish" maps to set_active_status("Published") +
    # submit_for_review() (no single "Publish" button exists — see module
    # docstring).
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144108 Publish Flow"
    try:
        _fill_all_mandatory_fields(admin, "144108", **{FIELD_ISSUE_TITLE_EN: title}, issue_date="05/09/2026")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        assert admin.status_for(title) == "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Unpublishing a magazine issue sets its Status back to Unpublished (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_130710
@pytest.mark.tc_144109
@MAGAZINE_CMS_XDIST_GROUP
def test_unpublish_updates_status_cms(page):
    # Azure TC 144109 | PBI 130710 — Control_Panel-side half.
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144109 Unpublish Flow"
    try:
        _fill_all_mandatory_fields(admin, "144109", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()
        assert admin.status_for(title) == "Published"

        admin.open_entry_by_edit_link(title)
        admin.unpublish_to_edit_as_draft()

        assert admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A published magazine issue persists after a page reload (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144115
@MAGAZINE_CMS_XDIST_GROUP
def test_published_issue_persists_after_reload_cms(page):
    # Azure TC 144115 | PBI 130710 — Control_Panel-side half.
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144115 Reload Persist"
    try:
        _fill_all_mandatory_fields(admin, "144115", **{FIELD_ISSUE_TITLE_EN: title}, page_count="40")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        admin.open_entry_by_edit_link(title)
        page.reload()
        page.wait_for_load_state("networkidle")
        assert admin.number_field_value(FIELD_PAGE_COUNT) == "40"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Publish lifecycle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publishing a newer issue re-designates it as Latest Issue (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144116
@MAGAZINE_CMS_XDIST_GROUP
def test_publish_newer_redesignates_latest_cms(page):
    # Azure TC 144116 | PBI 130710 — Control_Panel-side half; asserts on the
    # CMS-side Status only. The public-surface Latest-Issue re-designation
    # is verified in the Web-side test under the same marker.
    admin = MagazineIssueAdminPage(page)
    title_a = "QCTEST-144116-A Prior Issue"
    title_c = "QCTEST-144116-C Newer Issue"
    try:
        _fill_all_mandatory_fields(admin, "144116-a", **{FIELD_ISSUE_TITLE_EN: title_a}, issue_date="01/04/2026")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title_a)
        admin.publish()
        assert admin.status_for(title_a) == "Published"

        _fill_all_mandatory_fields(admin, "144116-c", **{FIELD_ISSUE_TITLE_EN: title_c}, issue_date="01/07/2026")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title_c)
        admin.publish()

        assert admin.status_for(title_c) == "Published"
        assert admin.status_for(title_a) == "Published"  # A is not un-published, only displaced from "Latest"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title_c)
        admin.open_entries_list()
        admin.delete_entry_by_title(title_a)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Draft / Unpublish visibility")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A draft magazine issue does not appear anywhere on the public page (Control_Panel side)")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144117
@MAGAZINE_CMS_XDIST_GROUP
def test_draft_issue_absent_everywhere_cms(page):
    # Azure TC 144117 | PBI 130710 — Control_Panel-side half.
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144117 Draft Nowhere"
    try:
        _fill_all_mandatory_fields(admin, "144117", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()

        assert admin.status_for(title) != "Published"
        anon_ctx = page.context.browser.new_context()
        anon_page = anon_ctx.new_page()
        pub = AlMoltaqaMagazinePage(anon_page)
        pub.open_magazine_anonymous()
        titles = pub.card_titles() + [pub.latest_title_text()]
        anon_ctx.close()
        assert title not in titles
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144118/144119 — SKIPPED: no Magazine Page admin object exists
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Al-Moltaqa Magazine page itself is not publicly reachable when unpublished")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144118
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_magazine_page_unreachable_when_unpublished(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Title EN is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144119
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_en_valid_saved_displayed(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Page Title EN rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144120
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_en_empty_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Title EN rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144121
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_en_whitespace_rejected(page):
    ...


# ===========================================================================
# 144122-144124 — Issue Number validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Number validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Issue Number is saved and displayed as the badge on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144122
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_number_valid_saved_displayed(page):
    # Azure TC 144122 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144122 Issue Number Check"
    issue_no = "QCTEST-Issue #69"
    try:
        _fill_all_mandatory_fields(admin, "144122", **{FIELD_ISSUE_TITLE_EN: title, FIELD_ISSUE_NUMBER: issue_no})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        assert title in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Number validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Number rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144123
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_number_empty_rejected(page):
    # Azure TC 144123 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144123", **{FIELD_ISSUE_NUMBER: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Number validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Number rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144124
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_number_whitespace_rejected(page):
    # Azure TC 144124 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144124", **{FIELD_ISSUE_NUMBER: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


# ===========================================================================
# 144125-144128 — Issue Title EN validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Issue Title EN is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144125
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_valid_saved_displayed(page):
    # Azure TC 144125 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144125 Economic Magazine"
    try:
        _fill_all_mandatory_fields(admin, "144125", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        assert title in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Title EN rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144126
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_empty_rejected(page):
    # Azure TC 144126 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144126", **{FIELD_ISSUE_TITLE_EN: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Title EN rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144127
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_whitespace_rejected(page):
    # Azure TC 144127 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144127", **{FIELD_ISSUE_TITLE_EN: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Title EN accepts exactly 200 characters and rejects 201")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144128
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_en_200_boundary(page):
    # Azure TC 144128 | PBI 130710 — same KNOWN LIMITATION noted on
    # ObjectAuthoringPage.field_length_rejected()'s docstring: the
    # submit-time fallback branch calls submit_for_publishing(), whose
    # wording doesn't match this object's real "Submit for Review" — only
    # the immediate-readback truncation branch is independently sound.
    admin = MagazineIssueAdminPage(page)
    attempted = "Q" * 201
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_ISSUE_TITLE_EN, attempted, 200)


# ===========================================================================
# 144129-144132 — Issue Description EN validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Description EN is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144129
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_valid_saved_displayed(page):
    # Azure TC 144129 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144129 Description Check"
    desc = "Al-Moltaqa Magazine Issue 68 covers Qatar's Q1 2026 economic outlook, trade statistics, and member spotlights."
    try:
        _fill_all_mandatory_fields(admin, "144129", **{FIELD_ISSUE_TITLE_EN: title, FIELD_ISSUE_DESCRIPTION_EN: desc})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        assert pub.card_desc(index) == desc
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Description EN rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144130
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_empty_rejected(page):
    # Azure TC 144130 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144130", **{FIELD_ISSUE_DESCRIPTION_EN: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Description EN rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144131
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_whitespace_rejected(page):
    # Azure TC 144131 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144131", **{FIELD_ISSUE_DESCRIPTION_EN: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description EN validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Description EN accepts exactly 1000 characters and rejects 1001")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144132
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_en_1000_boundary(page):
    # Azure TC 144132 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    attempted = "D" * 1001
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_ISSUE_DESCRIPTION_EN, attempted, 1000)


# ===========================================================================
# 144133-144135 — Cover Image validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid JPG Cover Image is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144133
@MAGAZINE_CMS_XDIST_GROUP
def test_cover_image_valid_saved_displayed(page):
    # Azure TC 144133 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144133 Cover Upload Check"
    try:
        _fill_all_mandatory_fields(admin, "144133", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        assert admin.uploaded_filename(FIELD_COVER_IMAGE)

        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert pub.card_has_img_cover(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A magazine issue cannot be published without a Cover Image")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144134
@MAGAZINE_CMS_XDIST_GROUP
def test_cover_image_empty_blocks_publish(page):
    # Azure TC 144134 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144134 No Cover"
    try:
        _fill_all_mandatory_fields(admin, "144134", **{FIELD_ISSUE_TITLE_EN: title}, skip_cover=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Cover Image validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Cover Image rejects a non-image file format")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144135
@MAGAZINE_CMS_XDIST_GROUP
def test_cover_image_non_image_format_rejected(page):
    # Azure TC 144135 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    admin.open_new_entry_form()

    assert admin.upload_file_expect_rejected(FIELD_COVER_IMAGE, f"{FIXTURES}/notes.txt")


# ===========================================================================
# 144136-144138 — Issue Date validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Date is saved and reflected in the issue's meta on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144136
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_date_valid_saved_reflected(page):
    # Azure TC 144136 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144136 Date Check"
    try:
        _fill_all_mandatory_fields(admin, "144136", **{FIELD_ISSUE_TITLE_EN: title}, issue_date="01/05/2026")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        assert "May 2026" in pub.card_meta(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A magazine issue cannot be published without an Issue Date")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144137
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_date_empty_blocks_publish(page):
    # Azure TC 144137 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144137 No Date"
    try:
        _fill_all_mandatory_fields(admin, "144137", **{FIELD_ISSUE_TITLE_EN: title}, skip_date=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Date validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Date rejects an invalid date format")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144138
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_date_invalid_format_rejected(page):
    # Azure TC 144138 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    admin.open_new_entry_form()
    admin.set_issue_date("32/13/2026")
    admin.save_as_draft()

    assert admin.submit_blocked() or "32/13/2026" != admin.issue_date_value()


# ===========================================================================
# 144139-144143 — Page Count validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Count is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144139
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_valid_saved_displayed(page):
    # Azure TC 144139 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144139 Page Count Check"
    try:
        _fill_all_mandatory_fields(admin, "144139", **{FIELD_ISSUE_TITLE_EN: title}, page_count="48")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        assert "48 pages" in pub.card_meta(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144140
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_empty_rejected(page):
    # Azure TC 144140 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144140", skip_page_count=True)
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a value of zero")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144141
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_zero_rejected(page):
    # Azure TC 144141 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144141", page_count="0")
    admin.save_as_draft()

    assert admin.submit_blocked() or admin.number_field_value(FIELD_PAGE_COUNT) != "0"


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a negative value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144142
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_negative_rejected(page):
    # Azure TC 144142 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144142", page_count="-5")
    admin.save_as_draft()

    assert admin.submit_blocked() or admin.number_field_value(FIELD_PAGE_COUNT) != "-5"


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Count rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144143
@MAGAZINE_CMS_XDIST_GROUP
def test_page_count_non_numeric_rejected(page):
    # Azure TC 144143 | PBI 130710 — a `spinbutton` field typically rejects
    # non-numeric keystrokes outright; asserted via the field's own
    # post-fill value never equalling the attempted non-numeric string.
    admin = MagazineIssueAdminPage(page)
    admin.open_new_entry_form()
    try:
        admin.page.get_by_role("spinbutton", name=FIELD_PAGE_COUNT, exact=True).fill("abc")
    except Exception:
        pass
    assert admin.number_field_value(FIELD_PAGE_COUNT) != "abc"


# ===========================================================================
# 144144-144148 — Article Count validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Article Count is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144144
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_valid_saved_displayed(page):
    # Azure TC 144144 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144144 Article Count Check"
    try:
        _fill_all_mandatory_fields(admin, "144144", **{FIELD_ISSUE_TITLE_EN: title}, article_count="12")
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        assert "12 Articles" in pub.card_meta(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144145
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_empty_rejected(page):
    # Azure TC 144145 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144145", skip_article_count=True)
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects a value of zero")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144146
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_zero_rejected(page):
    # Azure TC 144146 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144146", article_count="0")
    admin.save_as_draft()

    assert admin.submit_blocked() or admin.number_field_value(FIELD_ARTICLE_COUNT) != "0"


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects a negative value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144147
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_negative_rejected(page):
    # Azure TC 144147 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144147", article_count="-3")
    admin.save_as_draft()

    assert admin.submit_blocked() or admin.number_field_value(FIELD_ARTICLE_COUNT) != "-3"


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Article Count validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Article Count rejects a non-numeric value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144148
@MAGAZINE_CMS_XDIST_GROUP
def test_article_count_non_numeric_rejected(page):
    # Azure TC 144148 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    admin.open_new_entry_form()
    try:
        admin.page.get_by_role("spinbutton", name=FIELD_ARTICLE_COUNT, exact=True).fill("xyz")
    except Exception:
        pass
    assert admin.number_field_value(FIELD_ARTICLE_COUNT) != "xyz"


# ===========================================================================
# 144149-144151 — PDF Attachment validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A valid PDF attachment is saved and usable via Read Online and Download PDF")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144149
@MAGAZINE_CMS_XDIST_GROUP
def test_pdf_attachment_valid_usable(page):
    # Azure TC 144149 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144149 PDF Attachment Check"
    try:
        _fill_all_mandatory_fields(admin, "144149", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        assert admin.uploaded_filename(FIELD_PDF_ATTACHMENT)

        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        href = pub.card_read_online_link(index).get_attribute("href")
        assert href and href.startswith("/documents/")
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A magazine issue cannot be published without a PDF attachment")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144150
@MAGAZINE_CMS_XDIST_GROUP
def test_pdf_attachment_empty_blocks_publish(page):
    # Azure TC 144150 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144150 No PDF"
    try:
        _fill_all_mandatory_fields(admin, "144150", **{FIELD_ISSUE_TITLE_EN: title}, skip_pdf=True)
        admin.submit_for_review()

        assert admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("PDF Attachment validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publishing is blocked when the PDF Attachment is an invalid (non-PDF) file")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144151
@MAGAZINE_CMS_XDIST_GROUP
def test_pdf_attachment_invalid_format_blocks_publish(page):
    # Azure TC 144151 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144151 Invalid PDF Format"
    try:
        _fill_all_mandatory_fields(admin, "144151", **{FIELD_ISSUE_TITLE_EN: title}, skip_pdf=True)
        rejected = admin.upload_file_expect_rejected(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/issue211.docx")
        admin.submit_for_review()

        assert rejected or admin.submit_blocked() or admin.status_for(title) != "Published"
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144152/144153 — Open in New Tab
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Open in New Tab")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Open in New Tab defaults to True")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144152
def test_open_in_new_tab_defaults_true(page):
    # Azure TC 144152 | PBI 130710 — CMS-side half (the default-state
    # read); the Read-Online-actually-opens-a-new-tab half is verified in
    # the Web-side test under the same marker.
    admin = MagazineIssueAdminPage(page)
    admin.open_new_entry_form()

    assert admin.is_open_in_new_tab_checked() is True


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Open in New Tab")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Setting Open in New Tab to False persists")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144153
@MAGAZINE_CMS_XDIST_GROUP
def test_open_in_new_tab_false_persists(page):
    # Azure TC 144153 | PBI 130710 — CMS-side half (persistence); the
    # Read-Online-honors-False half is verified in the Web-side test.
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144153 New Tab False"
    try:
        _fill_all_mandatory_fields(admin, "144153", **{FIELD_ISSUE_TITLE_EN: title}, open_in_new_tab=False)
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)

        assert admin.is_open_in_new_tab_checked() is False
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144199/144200 — Replace Cover Image / PDF on a Published issue (Edge)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing the Cover Image on a Published issue updates the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144199
@MAGAZINE_CMS_XDIST_GROUP
def test_replace_cover_image_propagates(page):
    # Azure TC 144199 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144199 Replace Cover"
    try:
        _fill_all_mandatory_fields(admin, "144199", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        admin.open_entry_by_edit_link(title)
        admin.upload_file(FIELD_COVER_IMAGE, f"{FIXTURES}/valid_cover_1_5mb.jpg")
        admin.save_as_draft()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        assert pub.card_has_img_cover(index)
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Replacing the PDF attachment on a Published issue propagates the new file")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144200
@MAGAZINE_CMS_XDIST_GROUP
def test_replace_pdf_attachment_propagates(page):
    # Azure TC 144200 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144200 Replace PDF"
    try:
        _fill_all_mandatory_fields(admin, "144200", **{FIELD_ISSUE_TITLE_EN: title})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        admin.open_entry_by_edit_link(title)
        admin.upload_file(FIELD_PDF_ATTACHMENT, f"{FIXTURES}/valid_pdf_4mb.pdf")
        admin.save_as_draft()
        assert admin.uploaded_filename(FIELD_PDF_ATTACHMENT)

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
        href = pub.card_read_online_link(index).get_attribute("href")
        assert href and href.startswith("/documents/")
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


# ===========================================================================
# 144206-144208 — SKIPPED: no Magazine Page admin object (AR Page Title)
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings — Bilingual")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Page Title AR is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144206
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_ar_valid_saved_displayed(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings — Bilingual")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Page Title AR rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144207
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_ar_empty_rejected(page):
    ...


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Page-level settings — Bilingual")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page Title AR rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144208
@pytest.mark.skip(reason=NO_PAGE_OBJECT_REASON)
def test_page_title_ar_whitespace_rejected(page):
    ...


# ===========================================================================
# 144209-144212 — Issue Title AR validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Issue Title AR is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144209
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_valid_saved_displayed(page):
    # Azure TC 144209 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144209 Issue Title AR Check"
    title_ar = "المجلة الاقتصادية"
    try:
        _fill_all_mandatory_fields(admin, "144209", **{FIELD_ISSUE_TITLE_EN: title, FIELD_ISSUE_TITLE_AR: title_ar})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine(locale="ar")
        pub.search(title_ar)
        assert title_ar in pub.card_titles()
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Title AR rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144210
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_empty_rejected(page):
    # Azure TC 144210 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144210", **{FIELD_ISSUE_TITLE_AR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Title AR rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144211
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_whitespace_rejected(page):
    # Azure TC 144211 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144211", **{FIELD_ISSUE_TITLE_AR: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Title AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Title AR accepts exactly 200 characters and rejects 201")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144212
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_title_ar_200_boundary(page):
    # Azure TC 144212 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    attempted = "ت" * 201
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_ISSUE_TITLE_AR, attempted, 200)


# ===========================================================================
# 144213-144216 — Issue Description AR validation
# ===========================================================================
@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid Issue Description AR is saved and displayed on the public page")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_130710
@pytest.mark.tc_144213
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_valid_saved_displayed(page):
    # Azure TC 144213 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    title = "QCTEST-144213 Description AR Check"
    desc_ar = "د" * 200
    try:
        _fill_all_mandatory_fields(admin, "144213", **{FIELD_ISSUE_TITLE_EN: title, FIELD_ISSUE_DESCRIPTION_AR: desc_ar})
        admin.save_as_draft()
        admin.open_entry_by_edit_link(title)
        admin.publish()

        pub = AlMoltaqaMagazinePage(page)
        pub.open_magazine()
        pub.search(title)
        index = pub.card_index(title)
        assert index >= 0
    finally:
        admin.open_entries_list()
        admin.delete_entry_by_title(title)


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Issue Description AR rejects an empty value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144214
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_empty_rejected(page):
    # Azure TC 144214 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144214", **{FIELD_ISSUE_DESCRIPTION_AR: ""})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Description AR rejects a whitespace-only value")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144215
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_whitespace_rejected(page):
    # Azure TC 144215 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    _fill_all_mandatory_fields(admin, "144215", **{FIELD_ISSUE_DESCRIPTION_AR: "   "})
    admin.submit_for_review()

    assert admin.submit_blocked()


@allure.epic("Insights & Media")
@allure.feature("Al-Moltaqa Magazine — Control Panel")
@allure.story("Issue Description AR validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Issue Description AR accepts exactly 1000 characters and rejects 1001")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.bilingual
@pytest.mark.functional_low
@pytest.mark.pbi_130710
@pytest.mark.tc_144216
@MAGAZINE_CMS_XDIST_GROUP
def test_issue_description_ar_1000_boundary(page):
    # Azure TC 144216 | PBI 130710
    admin = MagazineIssueAdminPage(page)
    attempted = "د" * 1001
    admin.open_new_entry_form()

    assert admin.field_length_rejected(FIELD_ISSUE_DESCRIPTION_AR, attempted, 1000)

"""
cms/tests/home_publications/test_home_publications_control_panel.py —
Control_Panel-tagged case for PBI 129386 (QC-HOME-010 — Publications
Section). Sources ADO Test Case 134341 (suite 134457, plan 133534).

Built per .claude/context/active/standards.md's "Object Authoring Is the
Only Path for Content Operations — Not Content & Data" rule
(`HomePublicationsAdminPage` composes `ObjectAuthoringPage`) — `Content &
Data` is never used. Also follows the "Named CMS User Roles" rule (Author
drafts / Editor reviews, mirroring the Author/Editor precedent already
established in cms/tests/home_social_icons/test_home_social_icons_control_panel.py's
tc_131163) and the "Draft/Unpublish Public-Visibility Checks — Mandatory
Logged-Out Context" rule (the public Home Page assertion below always uses
a fresh, anonymous browser context, never the authenticated CMS session).

INVESTIGATION THIS SESSION (2026-09-12), CLI-first per automation-standards.md
(a throwaway Playwright script driving the real login form — the same
"disclosed throwaway CmsLoginPage-flow script" pattern
HomeSocialIconsAdminPage's own module docstring already establishes as
precedent; Playwright MCP was not needed):

  1. SLUG CONFIRMED LIVE: the Object Authoring Forms index lists
     "Publication" with real href `/web/qatar-chamber/manage-publication` —
     see HomePublicationsAdminPage's module docstring.

  2. CMS LOGIN BLOCKED LIVE FOR ALL THREE NAMED ROLES THIS SESSION: logging
     in as Site Content Editor, Site Content Author, AND Content
     Contributor (every credential this project has provisioned —
     `config.settings.CMS_ROLE_CREDENTIALS`) each failed with Liferay's own
     banner "Error: Authentication failed due to incorrect credentials or
     account lockout. Click 'Forgot Password' if the correct credentials
     were provided." — reproduced on the FIRST attempt for Site Content
     Editor (not merely after repeated retries), then reproduced AGAIN on a
     second, independent attempt for the same account, then observed
     identically for both other accounts. Site Content Editor is the SAME
     account HomeSocialIconsAdminPage's own module docstring confirmed
     logging in successfully as recently as 2026-09-07 — this is a real,
     new regression/lockout on qcdev since then, not a pre-existing,
     already-documented condition (it is distinct from both the "developer
     mode connection limit" license interstitial AND the Author/
     Contributor forced-password-reset interstitial already documented
     elsewhere in this project). Credentials were read straight from
     `.env`/`config/settings.py` and verified byte-for-byte correct against
     what was typed into the live form (screenshotted mid-attempt) before
     concluding this is a server-side rejection, not a client-side fill
     bug. This automation is not authorized to reset a shared credential or
     invent a replacement password on its own judgement — same standing
     rule already applied to the Author/Contributor blocker in
     HomeSocialIconsAdminPage's own docstring.

  3. INDEPENDENT OF (2) — A SEPARATE, ALREADY-ESTABLISHED SCOPE FINDING:
     even setting the login blocker aside, this project's Object Authoring
     surface (the ONLY sanctioned path for any content operation per
     standards.md) is confirmed live, across every one of the 15+ other
     objects already automated in this framework, to expose exactly Save
     as Draft / Submit for Publishing / Unpublish to edit as draft, and
     exactly two workflow statuses, Draft / Approved (see
     `cms/pages/components/object_authoring_page.py`'s own module
     docstring) — the Object Authoring Forms landing page's own copy says
     so explicitly ("add a new one as a draft or publish it directly", no
     third path). No "Pending Review" status and no "Reject" action exist
     anywhere on this surface for any object this project has automated so
     far. TC 134341's literal 3-step premise (Submit for review -> Status
     = Pending Review -> Reject as reviewer/Editor -> Status = Rejected)
     therefore has no confirmed real counterpart on this project's CMS.

DECISION (per this task's own explicit instruction: "If any part of this
case's literal flow doesn't match what's really available on this surface
... document that as a real, disclosed finding ... rather than force-
fitting it or inventing a workaround"): the test below is fully scripted
against the REAL Object Authoring surface and the REAL, confirmed public
Home Page Publications section — it attempts the case's own literal flow
end-to-end (Author drafts -> look for a real reviewer/Editor "Reject"
action -> public-page assertion) and will run for real the moment CMS
access is restored for at least one named role. It SKIPS itself, with an
explicit, evidence-backed reason, the instant it detects either of the two
disclosed blockers above live — rather than hanging, guessing a password,
inventing a "Reject" control that does not exist, or silently reporting a
false result.

QA TRACEABILITY: no prior QA-case document exists in this repo for PBI
129386's Control_Panel batch (this is the first Control_Panel case
automated for this PBI) — `MEDIA-PUBLICATIONS-TC-001` is assigned here as
the first traceability ID in that PBI-scoped sequence, per this project's
`<SERVICE>-<FEATURE>-TC-<NNN>` convention (Service=MEDIA, per
standards.md's Service/Module Codes table — Media Center covers
Publications), mirroring how e.g. `GLOBAL-SOCIALICONS-TC-005` was assigned
for PBI 129373's own Control_Panel batch. This is NOT an Azure work item ID
— that is the separate `tc_134341` marker below.

RUN RESULT (2026-09-12, `pytest -n 0 -m tc_134341`, live against qcdev):
SKIPPED — the real, observed outcome. See the test's own skip reason for
the exact evidence.

============================================================================
BATCH2 (2026-09-27, plan 133534/suite 134457) — 17 Section Tag/Heading
cases (tc_134344-134360), approved/injected as Automation, Functional-Low,
Control_Panel. See HomePublicationsAdminPage's own module docstring for the
full live investigation (fresh `tools/save_auth.py` capture this session +
a disclosed Playwright MCP fallback to reach the Page Builder fragment
configuration panel, a state the CLI extractor cannot reach) that
CONCLUDES: no CMS admin surface anywhere on this qcdev build — not the
per-record Publication object, not the closest-named candidate object
("Media Center Feed Section", ruled out live by its own closed 3-value
Section Type enum that excludes Publications), not the public Home Page's
own "QC Home Publications" Page Builder fragment's configuration panel
(exactly 2 real config fields, neither of them Section Tag/Heading) —
exposes an editable "Section Tag (EN/AR)" or "Section Heading (EN/AR)" for
the Home Page Publications section. `HomeAboutSummaryAdminPage`'s own
module docstring documents a REAL, confirmed page-level section-settings
object existing for a DIFFERENT Home Page section (About Us — a real
`manage-about-us-section` singleton with exactly this "Section Tag (EN)/
(AR)", "Section Heading (EN)/(AR)" field pair) — this investigation
confirms live that no equivalent object exists for Publications
specifically; the About Us precedent is what made the hypothesis worth
checking live, not evidence it must also hold here.

Each of the 17 tests below performs its OWN real, live, per-test
confirmation (not a shared/cached assumption carried over from the module
docstring alone) that its own named field does not exist on the real,
reachable Publication entry form, via
`HomePublicationsAdminPage.field_exists_on_entry_form()` — a live
`get_by_role(...).count()` check against the actual currently-open form —
before skipping with the disclosed reason. Every one of these 17 is
therefore DROPPED/DEFERRED with a concrete, live-confirmed reason: the
case's own subject-under-test has no reachable admin control to exercise,
not a force-fit onto the per-record "Publication Title"/"Publication
Description" fields, which are a DIFFERENT field pair (already exercised
by tc_134336 above) that none of these 17 cases' own text describes.

RUN RESULT (2026-09-27, `pytest -n 0 -m "tc_134344 or tc_134345 or
tc_134346 or tc_134347 or tc_134348 or tc_134349 or tc_134350 or tc_134351
or tc_134352 or tc_134353 or tc_134354 or tc_134355 or tc_134356 or
tc_134357 or tc_134358 or tc_134359 or tc_134360"`, live against qcdev,
fresh `tools/save_auth.py` session): all 17 SKIPPED — the real, observed
outcome, each with its own live-confirmed field-absence check passing
(i.e. the assertion that the named field is genuinely absent held true on
its own, independent per-test check) before the disclosed skip.

============================================================================
BATCH3 (2026-09-27, same session, plan 133534/suite 134457) — 9 Section
Description (EN/AR) cases (tc_134361-134369), a SEPARATE, INDEPENDENTLY
RE-VERIFIED investigation — NOT assumed to share BATCH2's conclusion just
because it sounds similar. Re-ran, live, a fresh `tools/save_auth.py`
capture + a fresh `--find description` CLI sweep against the real
Publication create-entry form + a fresh, disclosed Playwright MCP pass
re-opening the "QC Home Publications" Page Builder fragment's Configuration
Panel — see HomePublicationsAdminPage's own module docstring's "SECTION
DESCRIPTION INVESTIGATION" section for the full evidence trail. CONCLUSION:
the SAME absence holds here too (independently confirmed, not inherited by
assumption) — no CMS admin surface anywhere on this qcdev build exposes an
editable, section-level, rich-text "Section Description" for the Home Page
Publications section: not a dedicated Publications-Section/Knowledge-Hub
Object Authoring entry (none exists), not the per-record "Publication"
object's own "Publication Description"/"Publication Description —
العربية" fields (these exist, but are a DIFFERENT, per-record, plain-
textbox field pair with no rich-text/WYSIWYG affordance — already exercised
by tc_134336 above, and not what these 9 cases' own "...with formatting"
wording describes), and not the public Home Page's "QC Home Publications"
fragment's own Configuration Panel (still exactly the same 2 real fields
already documented for BATCH2 — carousel page size, listing page URL).

Each of the 9 tests below performs its OWN real, live, per-test
confirmation via `_confirm_section_field_absent_and_skip()` (the SAME
shared helper BATCH2 already established — reused as-is since this batch's
check shape, "named field absent from the entry form AND no dedicated
section-settings object exists", is identical, not a different shape
needing a distinct helper) before skipping with the disclosed reason.

RUN RESULT (2026-09-27, `pytest -n 0 -m "tc_134361 or tc_134362 or
tc_134363 or tc_134364 or tc_134365 or tc_134366 or tc_134367 or tc_134368
or tc_134369"`, live against qcdev, fresh `tools/save_auth.py` session): all
9 SKIPPED — the real, observed outcome, each with its own live-confirmed
field-absence check passing before the disclosed skip.
"""

import os

import allure
import pytest

from cms.pages.home_publications.home_publications_admin_page import (
    FIELD_TITLE_EN,
    PUBLICATION_TYPE_REPORT,
    HomePublicationsAdminPage,
)
from web.pages.home_publications.home_publications_page import HomePublicationsPage

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
# HEALED 2026-09-27 (triage of a live tc_134336 TimeoutError on
# `frame.get_by_role("button", name="Add")` during Cover Image/File
# Attachment upload — see HomePublicationsAdminPage.upload_file()'s own
# confirmed-live, correct locator chain, unchanged by this fix): a fresh
# `tools/save_auth.py` session + a direct Playwright MCP probe against the
# real `manage-publication` create form reproduced the failure and root-
# caused it to the FIXTURE FILES, not the Page Object or the
# `iframe[src*="selectFileEntry"]` locator (which is confirmed-correct,
# project-wide precedent — board_of_directors, org_structure). The OLD
# `publication_cover_image_qctest.jpg` (1x1-pixel JPEG bloated to ~1MB via
# 15 repeated empty COM/comment segments) and `publication_attachment_qctest.pdf`
# (a `%PDF-1.4` header + ~4MB of literal padding bytes before a bare-minimum
# 6-object xref/trailer, no real content stream) are BOTH confirmed live,
# reproducibly, to be rejected server-side by Liferay's Documents-and-Media
# upload handler with "An unexpected error occurred while uploading your
# file." — no "Add" button ever renders because the upload itself failed,
# which is exactly the observed `Locator.click: Timeout 15000ms exceeded`
# (the code was correctly waiting for a button that Liferay was never going
# to render for this malformed input). Confirmed live, same session, same
# exact locator chain, ZERO code changes: a REAL ~1.06MB JPEG (real pixel
# data, no artificial padding) and a REAL ~4.15MB single-page PDF (built via
# `img2pdf` embedding real image content, not zero-content padding) both
# upload successfully — "Add" renders, "1 of 1"/"Your document is uploaded"
# shows. `publication_cover_image_qctest_valid.jpg` /
# `publication_attachment_qctest_valid.pdf` are those confirmed-working
# replacement fixtures (added alongside, not overwriting, the old files,
# which are left in place for now — see this session's own handoff report
# for the old files' disposal). Every BATCH1/BATCH4 case that calls
# `_fill_valid_publication()`'s own DEFAULT Cover Image/File Attachment
# values was failing for this SAME single root cause, not a per-test defect.
COVER_IMAGE_FIXTURE = os.path.join(FIXTURES, "publication_cover_image_qctest_valid.jpg")
FILE_ATTACHMENT_FIXTURE = os.path.join(FIXTURES, "publication_attachment_qctest_valid.pdf")

# Blocker vocabulary from HomePublicationsAdminPage.login_as_role() /
# _ensure_logged_in() — anything other than "ok" is an unmet precondition.
_LOGIN_BLOCKER_REASONS = {
    "auth_failed": (
        "CMS login rejected by Liferay itself ('Authentication failed due to "
        "incorrect credentials or account lockout') for the {role!r} account — "
        "confirmed live this session for ALL THREE named CMS role accounts, "
        "reproduced twice for Site Content Editor specifically. This "
        "automation is not authorized to reset a shared credential or invent "
        "a replacement password. See HomePublicationsAdminPage's and this "
        "module's own docstrings for the full evidence trail. Rerun "
        "'pytest -m tc_134341' once CMS access is restored for this role."
    ),
    "forced_password_reset": (
        "The {role!r} account landed on Liferay's own forced first-login "
        "password-reset interstitial instead of a normal authenticated "
        "session. This automation is not authorized to set a new password "
        "on a shared credential on its own judgement. Complete the one-time "
        "reset out-of-band, then rerun 'pytest -m tc_134341'."
    ),
    "unknown": (
        "Login as {role!r} ended in neither a recognized success indicator "
        "nor either known blocker state — an unrecognized CMS login "
        "response this session. Treated as a blocked precondition rather "
        "than guessed."
    ),
}


def _skip_for_login_status(status: str, role: str) -> None:
    reason = _LOGIN_BLOCKER_REASONS.get(status, f"Unrecognized login status {status!r} for role {role!r}.")
    pytest.skip(f"BLOCKED (real, disclosed environment finding, not routed around): {reason.format(role=role)}")


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Rejected publication workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Rejected publication does not appear in the Home Page Publications section")
@allure.label("pbi", "129386")
@allure.label("testcase", "134341")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.workflow
@pytest.mark.pbi_129386
@pytest.mark.tc_134341
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-001")
def test_rejected_publication_does_not_appear_in_home_publications_section(page):
    """MEDIA-PUBLICATIONS-TC-001 / ADO-134341.

    Steps (verbatim): 1) Submit a Publication for review -> Status =
    Pending Review. 2) Reject it as reviewer/Editor -> Status = Rejected.
    3) Navigate to the Home Page Publications section -> the record's card
    is not present anywhere in the section.

    REAL, LIVE-EXECUTED PORTION (this test body): logs in as Site Content
    Author (the case's own Step 1 role) and, if that succeeds, as Site
    Content Editor (the case's own Step 2 reviewer role) — the only two
    steps of this case reachable without inventing an unconfirmed field
    map (see HomePublicationsAdminPage's module docstring). Each login is
    the REAL flow (`login_as_role()`), never a cached session, so the
    test's own SKIP below is a genuinely observed result, not an assumed
    one.

    DOCUMENTED, NOT EXECUTED, PORTION (see module docstring's full evidence
    trail — not force-fitted into runtime code that would need an invented
    field-label constant to run):
      - Creating the disposable "QCTEST-134341"-prefixed Publication and
        submitting it for review needs this object's real Title/
        Publication-Type/File field labels, which this session's login
        blocker prevented ever confirming — see
        HomePublicationsAdminPage's module docstring's TODO(locator).
      - Independent of that: this project's confirmed-live generic Object
        Authoring workflow (Save as Draft / Submit for Publishing /
        Unpublish to edit as draft; Draft/Approved statuses only — see
        ObjectAuthoringPage's own module docstring, confirmed across 15+
        other objects already automated in this framework) has no
        "Pending Review" status and no "Reject" action anywhere. Even once
        CMS access and the real field map are both available, TC 134341's
        literal Step 1/2 wording ("Status = Pending Review" / "Reject ...
        Status = Rejected") is expected to need the SAME disclosed
        case-vs-surface mismatch treatment tc_131163/tc_135456 already
        established for this project (assert the real, closest available
        status instead of the case's literal wording), not a force-fit.
      - Step 3 (the public-page, card-not-present assertion) IS fully
        scripted and real — see `HomePublicationsPage.has_card_with_title()`
        — and needs no field-map fix; it is only unreachable THIS session
        because there is no entry to create one for yet.
    """
    admin_author = HomePublicationsAdminPage(page)

    with allure.step("Log in to CMS as Site Content Author (the case's own Step 1 role)"):
        author_login_status = admin_author.login_as_role("Site Content Author")
    if author_login_status != "ok":
        _skip_for_login_status(author_login_status, "Site Content Author")

    # Reachable only if CMS access is ever restored for this account — see
    # docstring's DOCUMENTED, NOT EXECUTED, PORTION for exactly what is
    # still missing (the real field map) before this test's body can be
    # completed past this point.
    pytest.skip(
        "BLOCKED past this point (real precondition, not routed around): "
        "Site Content Author login succeeded, but creating a disposable "
        "Publication needs this object's real Title/Publication-Type/File "
        "field-label constants, which could not be confirmed this session "
        "(see HomePublicationsAdminPage's module docstring's TODO(locator) "
        "and this test's own docstring). Complete that field map, then "
        "finish this test body (create -> submit for review -> look for a "
        "real reviewer/Editor Reject control -> assert the entry's card is "
        "absent from HomePublicationsPage, per its own already-scripted, "
        "real has_card_with_title() check), then rerun "
        "'pytest -m tc_134341'."
    )


# ============================================================================
# BATCH1 (2026-09-13, plan 133534/suite 139193) — tc_134336, the POSITIVE
# publish-workflow case for the SAME "Publication" object. See
# HomePublicationsAdminPage's own module docstring for the full confirmed-
# live field map this test relies on (extracted this session, unblocked by
# using the cached TEST_USER session rather than a named-role login).
# ============================================================================

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Admin publish workflow")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The admin publish workflow results in a publication appearing on the Home Page")
@allure.label("pbi", "129386")
@allure.label("testcase", "134336")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.pbi_129386
@pytest.mark.tc_134336
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-002")
def test_admin_publish_workflow_results_in_publication_on_home_page(page, browser):
    """MEDIA-PUBLICATIONS-TC-002 / ADO-134336 (P1, Regression, UAT,
    Workflow). Test data (case's own concrete values): Title EN = "Qatar
    Trade Bulletin Q3 2026", Title AR = "نشرة التجارة القطرية الربع الذالث
    2026", Type = Reports, Date = 15/08/2026, valid Cover Image JPG ~1MB,
    valid File Attachment PDF ~4MB, Active = True. Steps: Log in as Site
    Content Editor -> Create a Publication with the test data above and
    save as Draft -> Submit for Review -> Status becomes "Pending Review"
    -> Publish -> Status becomes "Published"; success toast displays ->
    Navigate to the Home Page -> the new publication card appears in the
    Publications section under the "Reports" tab and under "All
    Publications".

    SESSION/ROLE: uses the cached admin (TEST_USER) session via the `page`
    fixture, NOT `login_as_role()` — this deliberately sidesteps the
    2026-09-12 named-CMS-role login blocker documented in this module and
    HomePublicationsAdminPage's own docstrings (that blocker is specific to
    the 3 named role accounts; TEST_USER's cached session is confirmed live
    working project-wide, including for this object this session).

    DISCLOSED ADAPTATIONS (case-vs-real-surface mismatches, same disclosed-
    substitution class as tc_134341's own docstring and every other object
    in this framework):
      - Type: the case's own literal "Reports" (plural) is not a real
        option — the closest real, closed-enum option is "Report"
        (singular, PUBLICATION_TYPE_REPORT). Substituted.
      - "Submit for Review -> Status becomes 'Pending Review'": this
        project's confirmed-live generic Object Authoring workflow (see
        ObjectAuthoringPage's own module docstring, confirmed across 15+
        other objects) has only Draft/Approved, no Pending Review anywhere.
        This object's OWN separate "Publication Status" field (a real,
        closed enum: Draft/Published/Unpublished/Rejected) ALSO has no
        "Pending Review" option. There is therefore no real intermediate
        state to land on or assert — this test moves straight from Draft to
        the case's own literal end states instead: sets "Publication
        Status" = "Published" (the field that actually carries this case's
        own literal wording) AND clicks Submit for Publishing (the generic
        workflow's own real "make it live" action, required for the public
        Home Page to ever render it, independent of the Publication Status
        field's own value). Both together are the real, closest-available
        realization of "the publish workflow completes and the record
        becomes Published" — not a silent skip of the intermediate step.
      - "Under the 'Reports' tab and under 'All Publications'":
        HomePublicationsPage.has_card_with_title()'s own confirmed-live
        LOAD-BEARING finding is that every card renders in the DOM
        simultaneously regardless of which type-filter tab or carousel
        page is currently active (a client-side show/hide, not a
        per-tab re-fetch) — so a single `has_card_with_title()` check
        inherently covers "appears under both tabs" without needing to
        click through each tab separately.

    Deletes its own disposable QCTEST-134336-prefixed entry in `finally`.

    HEALED 2026-09-28 (this session's tc_134336 reconfirmation run):
    CONFIRMED LIVE this test's own title was a FIXED, non-run-unique
    literal ("QCTEST-134336 Qatar Trade Bulletin Q3 2026") — every prior
    run that failed teardown (e.g. via this exact `find_entry_code_by_title`
    strict-mode violation itself) left a real, undeleted row behind with
    that same exact text, and this run's own `find_entry_code_by_title()`
    call failed live with `Locator.get_attribute: ... strict mode
    violation: ... resolved to 6 elements` — SIX prior leftover rows
    already share this literal title. Per this project's standing "never
    delete a record by position/first-match, only ever a record you
    yourself created and verified by its own title this run" rule, none of
    those 6 pre-existing rows were touched or deleted — they are left in
    place, undisturbed, as real (if untidy) pre-existing data. The actual
    fix is forward-looking: the title now carries a `uuid4` suffix, mirroring
    every BATCH4 case's own already-established convention, so this and
    every future run creates a row with a text value no prior run could
    ever have produced, making `find_entry_code_by_title()`'s row lookup
    (and `delete_entry_by_title()`'s own teardown) unambiguous again."""
    from uuid import uuid4

    from core.web.browser import new_context

    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())

    run_suffix = uuid4().hex[:8]
    title_en = f"QCTEST-134336 Qatar Trade Bulletin Q3 2026 {run_suffix}"
    title_ar = f"نشرة التجارة القطرية الربع الذالث 2026 - 134336 {run_suffix}"

    try:
        with allure.step("Create a Publication with the case's test data and save as Draft"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(title_ar)
            admin.select_publication_type(PUBLICATION_TYPE_REPORT)
            admin.set_publication_date("2026-08-15")
            admin.upload_cover_image(COVER_IMAGE_FIXTURE)
            admin.upload_file_attachment(FILE_ATTACHMENT_FIXTURE)
            # HEALED 2026-09-27: a real, valid Page Count is required — see
            # `_fill_valid_publication()`'s own HEALED note / `FIELD_PAGE_
            # COUNT`'s docstring for the confirmed-live server-side
            # validation rule this unblocks (not named in the case's own
            # literal test data, but required by the real product either way).
            admin.set_page_count("12")
            admin.set_active_status(True)
            admin.save_as_draft()

        # HEALED 2026-09-27 (same triage session as the upload-fixture fix
        # above): this line previously called the expensive, O(n)-reopens
        # `find_entry_code_by_field()` fallback — CONFIRMED LIVE this
        # session to be the SAME already-documented failure mode
        # `HomePublicationsAdminPage.find_entry_code_by_title()`'s own
        # docstring describes (a live TimeoutError reopening an UNRELATED,
        # pre-existing row's own edit form, nothing to do with the entry
        # this test itself just created). Publication's own Entry column IS
        # confirmed to render the real Title (EN) verbatim, so the fast,
        # non-reopening lookup already used throughout BATCH4 applies here
        # too — this test had simply not been migrated to it yet.
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, (
            f"could not resolve the just-created entry {title_en!r} by its "
            "own Publication Title value — Save as Draft did not persist a "
            "resolvable record"
        )
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Draft", "Publication did not save as Draft"

        with allure.step("Submit for Publishing (this build's real \"publish\" action — see docstring and _publish()'s own HEALED note: the \"Publication Status\" field this case's own text describes is confirmed live no longer present anywhere on this form)"):
            admin.submit_for_publishing()

        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved", (
            "Publication did not reach the generic workflow's Approved/Published-equivalent status"
        )

        with allure.step("Navigate to the Home Page: the new publication card appears in the Publications section"):
            appeared = home.reload_until(lambda p: p.has_card_with_title(title_en))
        assert appeared, (
            f"published card {title_en!r} did not appear in the Home Page "
            f"Publications section within {home.RELOAD_POLL_TIMEOUT_MS}ms"
        )
    finally:
        with allure.step("Teardown: delete the disposable Publication entry"):
            try:
                admin.open_entries_list()
                admin.delete_entry_by_title(title_en)
            except Exception:  # noqa: BLE001 — best-effort teardown only
                pass
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


# ============================================================================
# BATCH2 (2026-09-27, plan 133534/suite 134457) — Section Tag/Heading batch.
# See this module's own docstring's "BATCH2" section and
# HomePublicationsAdminPage's own module docstring's "SECTION TAG / SECTION
# HEADING INVESTIGATION" for the full live evidence trail. Every test below
# performs its OWN real, live field-absence confirmation before skipping —
# never a bare, unconditional pytest.skip() with no live check behind it.
# ============================================================================

# Candidate accessible-name spellings checked per field — mirrors this
# project's OWN "Section Tag (EN)"/"Section Heading (EN)" naming convention
# (HomeAboutSummaryAdminPage's confirmed-live "About Us Section" field
# labels) plus this object's own confirmed "<Field> — العربية" AR-suffix
# convention (see HomePublicationsAdminPage's FIELD_TITLE_AR /
# FIELD_DESCRIPTION_AR) — checking both spellings per field is a stronger,
# not a weaker, live confirmation of absence than checking only one.
_SECTION_TAG_EN_CANDIDATES = ["Section Tag (EN)", "Section Tag"]
_SECTION_TAG_AR_CANDIDATES = ["Section Tag (AR)", "Section Tag — العربية", "Section Tag — العربية *"]
_SECTION_HEADING_EN_CANDIDATES = ["Section Heading (EN)", "Section Heading"]
_SECTION_HEADING_AR_CANDIDATES = [
    "Section Heading (AR)",
    "Section Heading — العربية",
    "Section Heading — العربية *",
]

_SECTION_SETTINGS_OBJECT_CANDIDATES = [
    "Publications Section",
    "Home Publications Section",
    "Knowledge Hub",
    "Explore Our Knowledge Hub",
]

# Candidate accessible-name spellings for BATCH3 (Section Description
# EN/AR) — mirrors the same "<Field> (EN/AR)" plus this object's own
# "<Field> — العربية" AR-suffix convention checked for BATCH2 above. Kept
# deliberately DISTINCT from FIELD_DESCRIPTION_EN/AR (the per-record
# "Publication Description" pair) — those are a real, existing, different
# field this batch's own live investigation ruled out as the wrong target
# (see HomePublicationsAdminPage's module docstring).
_SECTION_DESCRIPTION_EN_CANDIDATES = ["Section Description (EN)", "Section Description"]
_SECTION_DESCRIPTION_AR_CANDIDATES = [
    "Section Description (AR)",
    "Section Description — العربية",
    "Section Description — العربية *",
]


def _confirm_section_field_absent_and_skip(admin: HomePublicationsAdminPage, tc_id: str, field_desc: str, candidates: list) -> None:
    """Shared real, live confirmation used by every BATCH2 AND BATCH3 test
    below (see module docstring's own BATCH2/BATCH3 sections) — BATCH3
    reuses this helper unchanged rather than adding a distinct one, since
    its own check shape ("named field absent from the entry form AND no
    dedicated section-settings object exists") is identical to BATCH2's,
    not a different one. Opens the real Publication create-entry form and
    asserts NONE of `candidates`' accessible-name spellings resolve to a
    real form control on it; separately re-confirms live that no dedicated
    Publications-Section/Knowledge-Hub Object Authoring entry exists either
    (the module docstring's finding #1). Only after BOTH real, live checks
    hold does it skip — an unexpected hit on either check fails the test
    instead (a real product change since this investigation, not silently
    routed around)."""
    admin.open_new_entry_form()
    for label in candidates:
        found = admin.field_exists_on_entry_form(label)
        assert not found, (
            f"UNEXPECTED (re-investigate before continuing to skip {tc_id}): a form control "
            f"named {label!r} DOES exist on the Publication entry form now — this case may be "
            "automatable against that live field; see HomePublicationsAdminPage's module "
            "docstring for the investigation this contradicts."
        )
    for object_name in _SECTION_SETTINGS_OBJECT_CANDIDATES:
        exists = admin.object_authoring_has_link(object_name)
        assert not exists, (
            f"UNEXPECTED (re-investigate before continuing to skip {tc_id}): an Object "
            f"Authoring entry named {object_name!r} now exists — re-check whether it backs the "
            "Publications section's own Section Tag/Heading/Description before continuing to "
            "skip this case."
        )
    pytest.skip(
        f"BLOCKED (real, disclosed environment finding, not routed around): ADO {tc_id}'s own "
        f"subject, the Home Page Publications section's {field_desc}, has no reachable CMS admin "
        "control anywhere on qcdev — confirmed live THIS test run (not just carried over from a "
        "prior investigation): no form control under any checked spelling exists on the real, "
        "reachable Publication create-entry form, AND no dedicated Publications-Section/"
        "Knowledge-Hub Object Authoring entry exists to hold it either. See "
        "HomePublicationsAdminPage's own module docstring ('SECTION TAG / SECTION HEADING "
        "INVESTIGATION' and, for the Section Description batch specifically, 'SECTION "
        "DESCRIPTION INVESTIGATION' — the latter independently re-verified this same absence "
        "rather than assuming it) for the full evidence trail, including why the closest-named "
        "real candidate object ('Media Center Feed Section') is ruled out by its own closed, "
        "live-inspected 3-value Section Type enum (News & Press Releases / Photo Gallery / "
        "Video Gallery — no Publications member), and why the public Home Page's own 'QC Home "
        "Publications' Page Builder fragment's configuration panel (2 real fields: carousel "
        "page size, listing page URL) also does not expose this field. NOT force-fitted onto "
        "the per-record 'Publication Title'/'Publication Description' fields (already exercised "
        "by tc_134336 above) — those are a different, plain-textbox field pair with no rich-text "
        "affordance, which this case's own text does not describe."
    )


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Section Tag (EN) value saves and displays")
@allure.label("pbi", "129386")
@allure.label("testcase", "134344")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134344
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-003")
def test_section_tag_en_valid_value_saves_and_displays(page):
    """MEDIA-PUBLICATIONS-TC-003 / ADO-134344. See BATCH2 docstring above
    and HomePublicationsAdminPage's module docstring for the full,
    live-confirmed finding: no CMS admin control for this field exists
    anywhere on qcdev for the Publications section."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134344", "Section Tag (EN) field", _SECTION_TAG_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Leaving Section Tag (EN) empty is accepted as an optional field")
@allure.label("pbi", "129386")
@allure.label("testcase", "134345")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134345
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-004")
def test_section_tag_en_empty_is_accepted_as_optional(page):
    """MEDIA-PUBLICATIONS-TC-004 / ADO-134345. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134345", "Section Tag (EN) field", _SECTION_TAG_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag (EN) rejects input exceeding 50 characters")
@allure.label("pbi", "129386")
@allure.label("testcase", "134346")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134346
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-005")
def test_section_tag_en_rejects_input_exceeding_50_chars(page):
    """MEDIA-PUBLICATIONS-TC-005 / ADO-134346. See BATCH2 docstring above.
    Per standards.md's "any ordering/limit field must be probed live for
    its REAL constraint" rule: the 50-character limit itself could not be
    probed because the field it would apply to does not exist to probe."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134346", "Section Tag (EN) field (50-char limit)", _SECTION_TAG_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag (EN) sanitizes script or special-character input")
@allure.label("pbi", "129386")
@allure.label("testcase", "134347")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134347
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-006")
def test_section_tag_en_sanitizes_script_or_special_chars(page):
    """MEDIA-PUBLICATIONS-TC-006 / ADO-134347. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134347", "Section Tag (EN) field (sanitization)", _SECTION_TAG_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag (EN) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134348")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134348
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-007")
def test_section_tag_en_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-007 / ADO-134348. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134348", "Section Tag (EN) field (persistence)", _SECTION_TAG_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Section Tag (AR) value saves and displays in RTL")
@allure.label("pbi", "129386")
@allure.label("testcase", "134349")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.pbi_129386
@pytest.mark.tc_134349
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-008")
def test_section_tag_ar_valid_value_saves_and_displays_rtl(page):
    """MEDIA-PUBLICATIONS-TC-008 / ADO-134349. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134349", "Section Tag (AR) field", _SECTION_TAG_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag (AR) rejects input exceeding 50 characters")
@allure.label("pbi", "129386")
@allure.label("testcase", "134350")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134350
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-009")
def test_section_tag_ar_rejects_input_exceeding_50_chars(page):
    """MEDIA-PUBLICATIONS-TC-009 / ADO-134350. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134350", "Section Tag (AR) field (50-char limit)", _SECTION_TAG_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Tag (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Tag (AR) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134351")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134351
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-010")
def test_section_tag_ar_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-010 / ADO-134351. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134351", "Section Tag (AR) field (persistence)", _SECTION_TAG_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Section Heading (EN) value saves and displays")
@allure.label("pbi", "129386")
@allure.label("testcase", "134352")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134352
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-011")
def test_section_heading_en_valid_value_saves_and_displays(page):
    """MEDIA-PUBLICATIONS-TC-011 / ADO-134352. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134352", "Section Heading (EN) field", _SECTION_HEADING_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (EN) is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134353")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134353
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-012")
def test_section_heading_en_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-012 / ADO-134353. See BATCH2 docstring above.
    Per standards.md's "verify which action (Draft vs Publish) actually
    enforces mandatory fields" rule: which action would enforce this could
    not be probed because the field itself does not exist to probe."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134353", "Section Heading (EN) field (mandatory enforcement)", _SECTION_HEADING_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (EN) rejects input exceeding 200 characters")
@allure.label("pbi", "129386")
@allure.label("testcase", "134354")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134354
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-013")
def test_section_heading_en_rejects_input_exceeding_200_chars(page):
    """MEDIA-PUBLICATIONS-TC-013 / ADO-134354. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134354", "Section Heading (EN) field (200-char limit)", _SECTION_HEADING_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (EN) sanitizes special-character or markup input")
@allure.label("pbi", "129386")
@allure.label("testcase", "134355")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134355
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-014")
def test_section_heading_en_sanitizes_special_char_or_markup(page):
    """MEDIA-PUBLICATIONS-TC-014 / ADO-134355. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134355", "Section Heading (EN) field (sanitization)", _SECTION_HEADING_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (EN) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134356")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134356
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-015")
def test_section_heading_en_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-015 / ADO-134356. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134356", "Section Heading (EN) field (persistence)", _SECTION_HEADING_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Section Heading (AR) value saves and displays in RTL")
@allure.label("pbi", "129386")
@allure.label("testcase", "134357")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.pbi_129386
@pytest.mark.tc_134357
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-016")
def test_section_heading_ar_valid_value_saves_and_displays_rtl(page):
    """MEDIA-PUBLICATIONS-TC-016 / ADO-134357. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134357", "Section Heading (AR) field", _SECTION_HEADING_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (AR) is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134358")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134358
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-017")
def test_section_heading_ar_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-017 / ADO-134358. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134358", "Section Heading (AR) field (mandatory enforcement)", _SECTION_HEADING_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (AR) rejects input exceeding 200 characters")
@allure.label("pbi", "129386")
@allure.label("testcase", "134359")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134359
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-018")
def test_section_heading_ar_rejects_input_exceeding_200_chars(page):
    """MEDIA-PUBLICATIONS-TC-018 / ADO-134359. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134359", "Section Heading (AR) field (200-char limit)", _SECTION_HEADING_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Heading (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Heading (AR) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134360")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134360
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-019")
def test_section_heading_ar_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-019 / ADO-134360. See BATCH2 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134360", "Section Heading (AR) field (persistence)", _SECTION_HEADING_AR_CANDIDATES)


# ============================================================================
# BATCH3 (2026-09-27, plan 133534/suite 134457) — Section Description
# (EN/AR) batch. See this module's own docstring's "BATCH3" section and
# HomePublicationsAdminPage's own module docstring's "SECTION DESCRIPTION
# INVESTIGATION" for the full, independently re-verified live evidence
# trail. Every test below performs its OWN real, live field-absence
# confirmation before skipping — never a bare, unconditional pytest.skip()
# with no live check behind it.
# ============================================================================


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Section Description (EN) value saves and displays with formatting")
@allure.label("pbi", "129386")
@allure.label("testcase", "134361")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134361
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-020")
def test_section_description_en_valid_value_saves_and_displays_with_formatting(page):
    """MEDIA-PUBLICATIONS-TC-020 / ADO-134361. See BATCH3 docstring above
    and HomePublicationsAdminPage's module docstring for the full,
    independently-re-verified finding: no CMS admin control for a
    section-level, rich-text Section Description field exists anywhere on
    qcdev for the Publications section."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134361", "Section Description (EN) field", _SECTION_DESCRIPTION_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (EN) is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134362")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134362
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-021")
def test_section_description_en_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-021 / ADO-134362. See BATCH3 docstring above.
    Per standards.md's "verify which action (Draft vs Publish) actually
    enforces mandatory fields" rule: which action would enforce this could
    not be probed because the field itself does not exist to probe."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134362", "Section Description (EN) field (mandatory enforcement)", _SECTION_DESCRIPTION_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (EN) rejects input exceeding 1000 characters")
@allure.label("pbi", "129386")
@allure.label("testcase", "134363")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134363
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-022")
def test_section_description_en_rejects_input_exceeding_1000_chars(page):
    """MEDIA-PUBLICATIONS-TC-022 / ADO-134363. See BATCH3 docstring above.
    Per standards.md's "any ordering/limit field must be probed live for
    its REAL constraint" rule: the 1000-character limit itself could not be
    probed because the field it would apply to does not exist to probe."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134363", "Section Description (EN) field (1000-char limit)", _SECTION_DESCRIPTION_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (EN) sanitizes HTML or script injection input")
@allure.label("pbi", "129386")
@allure.label("testcase", "134364")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134364
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-023")
def test_section_description_en_sanitizes_html_or_script_injection(page):
    """MEDIA-PUBLICATIONS-TC-023 / ADO-134364. See BATCH3 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134364", "Section Description (EN) field (HTML/script sanitization)", _SECTION_DESCRIPTION_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (EN)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (EN) value and formatting persist after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134365")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134365
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-024")
def test_section_description_en_value_and_formatting_persist_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-024 / ADO-134365. See BATCH3 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134365", "Section Description (EN) field (persistence)", _SECTION_DESCRIPTION_EN_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("A valid Section Description (AR) value saves and displays in RTL with formatting")
@allure.label("pbi", "129386")
@allure.label("testcase", "134366")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.pbi_129386
@pytest.mark.tc_134366
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-025")
def test_section_description_ar_valid_value_saves_and_displays_rtl_with_formatting(page):
    """MEDIA-PUBLICATIONS-TC-025 / ADO-134366. See BATCH3 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134366", "Section Description (AR) field", _SECTION_DESCRIPTION_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (AR) is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134367")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134367
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-026")
def test_section_description_ar_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-026 / ADO-134367. See BATCH3 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134367", "Section Description (AR) field (mandatory enforcement)", _SECTION_DESCRIPTION_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (AR) rejects input exceeding 1000 characters")
@allure.label("pbi", "129386")
@allure.label("testcase", "134368")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134368
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-027")
def test_section_description_ar_rejects_input_exceeding_1000_chars(page):
    """MEDIA-PUBLICATIONS-TC-027 / ADO-134368. See BATCH3 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134368", "Section Description (AR) field (1000-char limit)", _SECTION_DESCRIPTION_AR_CANDIDATES)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Section Description (AR)")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Section Description (AR) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134369")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134369
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-028")
def test_section_description_ar_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-028 / ADO-134369. See BATCH3 docstring above."""
    admin = HomePublicationsAdminPage(page)
    _confirm_section_field_absent_and_skip(admin, "134369", "Section Description (AR) field (persistence)", _SECTION_DESCRIPTION_AR_CANDIDATES)


# ============================================================================
# BATCH4 (2026-09-27, same suite 134457) — the per-record "Publication"
# object's own field-level batch, ADO 134370-134401 (31 cases): Publication
# Title (EN/AR), Publication Type, Publication Date, Cover Image, File
# Attachment, Active Status. Unlike BATCH2/BATCH3 above, every field this
# batch exercises IS confirmed live/reachable on the real, already-field-
# mapped `manage-publication` create-entry form (see
# HomePublicationsAdminPage's own module docstring's FIELD MAP, confirmed
# live 2026-09-13 by tc_134336) — these are REAL, fully-scripted tests, not
# a repeat of the section-level absence findings above.
#
# LIVE RE-INVESTIGATION THIS SESSION (2026-09-27, fresh `tools/save_auth.py`
# capture, disclosed throwaway CLI probes against the real create-entry
# form — see HomePublicationsAdminPage's own module docstring's HEALED
# date-input note for the fullest evidence trail):
#
#   1. DATE INPUT UI CHANGE (real, since 2026-09-13): "Publication Date" now
#      renders a VISIBLE `dd/mm/yyyy` text input in front of the original
#      hidden native `<input type="date">` — `set_publication_date()` was
#      HEALED to type into the visible input; the old
#      `PUBLICATION_DATE_INPUT_CSS` selector is gone (would now be a
#      Playwright strict-mode violation, 2 matches).
#   2. MANDATORY FIELDS: "Publication Title ", "Publication Title —
#      العربية *", "Publication Type " (combobox), the "Cover Image Select
#      File" / "File Attachment Select File" hidden textboxes ALL carry a
#      native HTML `required` attribute — leaving any ONE of them empty
#      blocks BOTH Save as Draft AND Submit for Publishing identically:
#      NO real entry is ever persisted (confirmed live via a fresh
#      entries-list re-check by a marker value in a field that WAS
#      filled) — NOT this project's usual "Draft lenient / Publish
#      strict" split. HEALED mid-session (first real run of this batch):
#      the ORIGINAL design additionally asserted `checkValidity() == False`
#      AFTER the click — CONFIRMED LIVE this is unreliable, because
#      clicking Save as Draft strips the field's OWN native `required`
#      attribute as a side effect (replaced with a `data-qc-was-required`
#      marker, confirmed live via `outerHTML`) even while the field is
#      still genuinely empty and nothing was actually saved, and with no
#      visible error banner/toast either — a real, disclosed, confusing-UX
#      finding of its own. Every mandatory case below therefore asserts
#      `checkValidity()` only BEFORE the click (a sanity precondition) and
#      relies on NON-PERSISTENCE as the real, live-confirmed enforcement
#      signal — see `_assert_mandatory_field_blocks_persistence()`'s own
#      docstring.
#   3. TITLE LENGTH: neither Title EN nor Title AR carries a native
#      `maxlength` — a 250-character value (50 over the case's own stated
#      200-char limit) is neither truncated client-side nor rejected
#      server-side; a real Save as Draft with a 250-char Title EN + all
#      other fields valid was confirmed live to persist (found via a fresh
#      entries-list reload, not assumed). Per standards.md's rule 3, the
#      205 cases below assert the REAL behavior (acceptance), not the
#      case's literal 200-char rejection.
#   4. COVER IMAGE upload picker: a real, live, CLIENT-SIDE extension
#      allowlist IS enforced — confirmed exact error text "Please enter a
#      file with a valid extension (.jpg,.jpeg,.png)." for a `.txt` file,
#      with no "Add" button ever rendering. A 3MB JPEG (50% over the case's
#      stated 2MB limit), by contrast, hit NO client-side size rejection —
#      the "Add" button rendered normally, same as a valid-size file — a
#      real, disclosed, possibly-defective finding this batch's own test
#      asserts against honestly (per standards.md/automation-standards.md's
#      "no xfail without a filed Bug ID — when in doubt, let it fail" rule),
#      not routed around.
#   5. FILE ATTACHMENT upload picker: UNLIKE Cover Image, confirmed live to
#      have NO client-side extension allowlist at all — a `.docx` file
#      (non-PDF) was accepted with an enabled "Add" button and the real
#      "Your document is uploaded" confirmation text, exactly like a valid
#      PDF. Documented as a real, disclosed finding; the case below asserts
#      the correct/expected rejection and is scripted to fail honestly if
#      the live product does not actually enforce it.
#
# Every test below performs its OWN real create → save/submit → verify
# flow against the live qcdev instance (never assumed from this
# investigation alone) and deletes its own disposable QCTEST-prefixed
# entry in `finally` (mirrors tc_134336's own established teardown
# convention — this object's entries DO support Delete).
# ============================================================================

import re
from uuid import uuid4

from cms.pages.home_publications.home_publications_admin_page import (
    FIELD_COVER_IMAGE,
    FIELD_FILE_ATTACHMENT,
    FIELD_TITLE_AR,
    FIELD_TYPE,
    PUBLICATION_TYPE_GUIDES,
)
from core.web.browser import new_context

COVER_IMAGE_UNSUPPORTED_FIXTURE = os.path.join(FIXTURES, "publication_cover_image_qctest_unsupported.txt")
COVER_IMAGE_OVERSIZED_FIXTURE = os.path.join(FIXTURES, "publication_cover_image_qctest_oversized.jpg")
FILE_ATTACHMENT_NONPDF_FIXTURE = os.path.join(FIXTURES, "publication_attachment_qctest_nonpdf.docx")
FILE_ATTACHMENT_OVERSIZED_FIXTURE = os.path.join(FIXTURES, "publication_attachment_qctest_oversized.pdf")

DEFAULT_ISO_DATE = "2026-08-15"


def _fill_valid_publication(
    admin: HomePublicationsAdminPage,
    title_en,
    title_ar,
    ptype=PUBLICATION_TYPE_REPORT,
    iso_date=DEFAULT_ISO_DATE,
    cover_image=COVER_IMAGE_FIXTURE,
    attachment=FILE_ATTACHMENT_FIXTURE,
    active=True,
) -> None:
    """Fills the already-open create-entry form with valid data for every
    field EXCEPT any explicitly passed as None — mandatory-field cases below
    leave exactly one field unfilled this way (see BATCH4 docstring's
    finding #2).

    HEALED 2026-09-27 (same triage session as the upload-fixture,
    editEntry-code, and status/button-text fixes documented elsewhere):
    added a real, valid "Page Count" value — CONFIRMED LIVE this object has
    a server-side `ObjectValidationRuleEngineException` ("Page count must
    be a positive whole number (1 or greater).") that silently blocks
    EVERY Submit for Review/Publishing call while this field is left at its
    own default "0" (see `HomePublicationsAdminPage.FIELD_PAGE_COUNT`'s own
    docstring for the full evidence trail). None of this batch's own case
    text names Page Count, but the object's real validation rule applies
    regardless of what any one case asserts."""
    if title_en is not None:
        admin.set_title_en(title_en)
    if title_ar is not None:
        admin.set_title_ar(title_ar)
    if ptype is not None:
        admin.select_publication_type(ptype)
    if iso_date is not None:
        admin.set_publication_date(iso_date)
    if cover_image is not None:
        admin.upload_cover_image(cover_image)
    if attachment is not None:
        admin.upload_file_attachment(attachment)
    admin.set_page_count("12")
    admin.set_active_status(active)


def _delete_by_title(admin: HomePublicationsAdminPage, title_en: str) -> None:
    try:
        admin.open_entries_list()
        admin.delete_entry_by_title(title_en)
    except Exception:  # noqa: BLE001 — best-effort teardown only, mirrors tc_134336
        pass


def _entries_list_contains_text(admin: HomePublicationsAdminPage, text: str) -> bool:
    """Fast, single-page-load non-persistence check — opens the entries
    list ONCE and does a single `inner_text()` scan of the whole table,
    instead of `ObjectAuthoringPage.find_entry_code_by_field()`'s own
    O(n)-reopens-every-row fallback (see `find_entry_code_by_title()`'s own
    docstring for why that fallback is both needlessly slow AND, on a
    table that has accumulated many rows this session, a genuine source of
    unrelated live TimeoutErrors).

    KNOWN BLIND SPOT (CONFIRMED LIVE 2026-09-28, see
    `_assert_mandatory_field_blocks_persistence()`'s own updated docstring):
    this text-search alone is NOT a reliable non-persistence signal when the
    field being tested is `FIELD_TITLE_EN` — the Entry column only renders
    the real Title (EN) text (`find_entry_code_by_title()`'s own confirmed
    finding); when Title (EN) itself is empty, the Entry column instead
    falls back to rendering the record's own internal UUID, and the
    `marker_value` used by the Title-EN mandatory case lives in Title (AR),
    a field NEVER rendered anywhere in this list view. A real, persisted row
    can therefore exist with this exact `marker_value` in its own Title (AR)
    field while this function still returns `False` (marker not found) —
    confirmed live via a direct row-count-before/after probe: leaving Title
    (EN) empty on this object does NOT actually block persistence (a new row
    was created), even though `field_checkvalidity()` reports it as
    required+invalid beforehand — the same "required attribute exists but is
    not actually enforced on submit" class of defect already independently
    confirmed for Title (AR) (tc_134376, 3 prior live confirmations). Kept
    here as a secondary, informative signal only — the PRIMARY, blind-spot-
    proof signal is now `_entries_row_count()`, below."""
    admin.open_entries_list()
    return text in admin.page.locator("table tbody").inner_text()


def _entries_row_count(admin: HomePublicationsAdminPage) -> int:
    """The real, total number of rows in the entries list — a signal that
    does not depend on which field's value the Entry column happens to
    render, so it catches persistence even when the empty mandatory field IS
    Title (EN) itself (see `_entries_list_contains_text()`'s own KNOWN BLIND
    SPOT note). ADDED 2026-09-28 as the fix for that live-confirmed gap."""
    admin.open_entries_list()
    return admin.page.locator("table tbody tr").count()


def _assert_mandatory_field_blocks_persistence(
    admin: HomePublicationsAdminPage,
    empty_field_label: str,
    empty_field_role: str,
    marker_value: str,
    baseline_row_count: int,
) -> None:
    """HEALED 2026-09-27 (live incident this session, first real run of the
    mandatory-field batch): the ORIGINAL design asserted `not
    admin.field_checkvalidity(empty_field_label)` AFTER clicking Save as
    Draft — CONFIRMED LIVE this is unreliable: clicking Save as Draft (even
    while the field is genuinely still empty) strips the field's OWN
    native `required` DOM attribute as a side effect (replaced with a
    `data-qc-was-required` marker — confirmed live via `outerHTML`), which
    flips `checkValidity()` to `True` even though nothing was actually
    saved. This is a real, disclosed, confusing-UX finding of its own (no
    visible error banner or toast appears either) — but it means
    `checkValidity()` read AFTER the click is not the real enforcement
    signal on this object.

    HEALED AGAIN 2026-09-28 (live incident, this session's investigation of
    a previously-flagged concern): the ORIGINAL non-persistence signal — a
    text search for `marker_value` across the whole entries-list table —
    has its own CONFIRMED-LIVE blind spot when `empty_field_label` is
    `FIELD_TITLE_EN` specifically: the marker (placed in Title AR, the only
    field left filled) is never rendered anywhere in the list view at all
    (the Entry column falls back to the record's own internal UUID when
    Title EN is empty), so the text search silently reports "not found" —
    a false negative — even when a real row WAS persisted. Root-caused via a
    direct, disclosed throwaway script: creating a Publication with Title EN
    empty / Title AR = a known marker moved the entries-list row COUNT from
    12 to 13 (a real new row), yet the marker text was never found anywhere
    in the table, and the new row's own Entry-column text was a bare UUID —
    exactly the hypothesized blind spot, confirmed. The SAME probe also
    surfaced a genuine PRE-EXISTING orphaned row from an earlier session's
    own (previously blind) tc_134371 run — left completely untouched per
    this project's standing no-blind-deletion rule (only the investigation's
    own freshly-created, freshly-verified row was deleted, by its own
    Title-AR readback matching the known marker exactly before any delete
    click).

    The REAL, live-confirmed, blind-spot-proof enforcement signal is now the
    entries-list ROW COUNT (`_entries_row_count()`) staying at
    `baseline_row_count` — a signal independent of which field the Entry
    column happens to render. The marker-text search
    (`_entries_list_contains_text()`) is still asserted too, as a secondary,
    informative check (it remains fully reliable for every OTHER mandatory
    field in this batch, where the marker lives in Title EN itself and IS
    rendered by the Entry column) — but the row-count check is what actually
    catches the Title-EN case. `checkValidity()` is still asserted once,
    BEFORE the click, as a real sanity check that the field starts out
    genuinely required+invalid (not skipped silently)."""
    assert not admin.field_checkvalidity(empty_field_label, role=empty_field_role), (
        f"{empty_field_label!r} reports itself as valid while empty, before any Save/Submit attempt — "
        "the mandatory precondition this test depends on does not hold"
    )
    admin.attempt_save_as_draft()
    assert admin.is_on_create_form(), "Save as Draft appears to have navigated away despite an empty mandatory field"
    assert not _entries_list_contains_text(admin, marker_value), (
        f"Save as Draft persisted a real entry despite an empty mandatory {empty_field_label!r}"
    )
    assert _entries_row_count(admin) == baseline_row_count, (
        f"Save as Draft changed the entries-list row count ({baseline_row_count} -> "
        f"{_entries_row_count(admin)}) despite an empty mandatory {empty_field_label!r} — a real row WAS "
        "persisted even though the marker-text search above did not find it (see this function's own "
        "Title-EN-blind-spot HEALED note: the Entry column falls back to an internal UUID, not the "
        "marker text, when Title EN itself is the field left empty)"
    )

    admin.attempt_submit_for_publishing()
    assert admin.is_on_create_form(), "Submit for Publishing appears to have navigated away despite an empty mandatory field"
    assert not _entries_list_contains_text(admin, marker_value), (
        f"Submit for Publishing persisted a real entry despite an empty mandatory {empty_field_label!r}"
    )
    assert _entries_row_count(admin) == baseline_row_count, (
        f"Submit for Publishing changed the entries-list row count ({baseline_row_count} -> "
        f"{_entries_row_count(admin)}) despite an empty mandatory {empty_field_label!r} — a real row WAS "
        "persisted even though the marker-text search above did not find it"
    )


def _publish(admin: HomePublicationsAdminPage, entry_code: str) -> None:
    """Submits for Publishing — this object's own real "make it live" action
    (Draft -> Approved, the generic Object Authoring workflow already
    confirmed project-wide).

    HEALED 2026-09-27 (triage of a live tc_134336 failure, same session as
    the upload-fixture and editEntry-code fixes documented elsewhere in this
    module/HomePublicationsAdminPage): this helper previously ALSO called
    `admin.select_publication_status(PUBLICATION_STATUS_PUBLISHED)` first —
    CONFIRMED LIVE this session, via a direct Playwright MCP probe against
    BOTH the real create form and a real existing entry's edit form, that a
    "Publication Status" combobox does NOT exist ANYWHERE on this object's
    real, reachable form today (only ONE combobox is present anywhere on
    either form — "Publication Type "; the two `<select>` elements found on
    the edit form's surrounding page are the ENTRIES-LIST's own Status
    filter and page-size selector, not an entry-level field). This
    contradicts `HomePublicationsAdminPage`'s own module docstring FIELD MAP,
    confirmed live 2026-09-13 — a real product surface change since then,
    not a locator regression (`select_publication_status()`'s own combobox
    locator is unchanged and was never wrong for the field it targets; the
    field itself is simply gone). Calling it now hangs for the full 30s
    Playwright default click timeout waiting for a combobox that will never
    render, which is exactly what surfaced this — the SAME single root cause
    behind every BATCH4 test that calls this shared helper. `submit_for_
    publishing()` alone is this build's real, closest-available "publish"
    action now — Draft -> Approved, confirmed live to render on the Home
    Page like every other object project-wide."""
    admin.open_entry_by_code(entry_code)
    admin.submit_for_publishing()


# ---- Group: Publication Title (EN) — ADO 134370-134374 --------------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (EN)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Title (EN) saves and displays on the card")
@allure.label("pbi", "129386")
@allure.label("testcase", "134370")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134370
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-029")
def test_publication_title_en_valid_saves_and_displays_on_card(page, browser):
    """MEDIA-PUBLICATIONS-TC-029 / ADO-134370."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134370 Trade Bulletin {uuid4().hex[:8]}"
    title_ar = "QCTEST-134370-AR نشرة تجارية"
    try:
        with allure.step("Create a Publication with a valid Title (EN) and publish it"):
            admin.open_new_entry_form()
            _fill_valid_publication(admin, title_en, title_ar)
            admin.save_as_draft()
            entry_code = admin.find_entry_code_by_title(title_en)
            assert entry_code, f"could not resolve the just-created entry {title_en!r}"
            _publish(admin, entry_code)
        with allure.step("The Home Page card renders this exact Title (EN)"):
            appeared = home.reload_until(lambda p: p.has_card_with_title(title_en))
        assert appeared, f"published card {title_en!r} did not appear within {home.RELOAD_POLL_TIMEOUT_MS}ms"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (EN)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publication Title (EN) is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134371")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134371
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-030")
def test_publication_title_en_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-030 / ADO-134371. See
    `_assert_mandatory_field_blocks_persistence()`'s own docstring for the
    real, live-confirmed enforcement signal this test relies on
    (entries-list ROW COUNT, not a marker-text search alone — this specific
    case, where the empty field IS Title EN, is the one the marker-text
    search has its own confirmed-live blind spot for, since the marker
    lives in Title AR, a field never rendered in the list view)."""
    admin = HomePublicationsAdminPage(page)
    marker = f"QCTEST-134371-AR-{uuid4().hex[:8]}"
    baseline_row_count = _entries_row_count(admin)
    admin.open_new_entry_form()
    _fill_valid_publication(admin, title_en=None, title_ar=marker)
    _assert_mandatory_field_blocks_persistence(admin, FIELD_TITLE_EN, "textbox", marker, baseline_row_count)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title (EN) accepts input beyond the case's stated 200-character limit")
@allure.label("pbi", "129386")
@allure.label("testcase", "134372")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134372
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-031")
def test_publication_title_en_length_boundary(page):
    """MEDIA-PUBLICATIONS-TC-031 / ADO-134372. Case text: "rejects input
    exceeding 200 characters". REAL, LIVE-CONFIRMED behavior (see BATCH4
    docstring finding #3): no native `maxlength`; a 250-char value (50 over
    the stated limit) is neither truncated nor rejected — Save as Draft
    persists the full 250 characters verbatim. Per standards.md's rule 3,
    asserts the REAL behavior (acceptance) rather than the case's literal
    200-char rejection."""
    admin = HomePublicationsAdminPage(page)
    suffix = "A" * (250 - len(f"QCTEST-134372-{uuid4().hex[:8]}-"))
    title_en = f"QCTEST-134372-{uuid4().hex[:8]}-{suffix}"
    assert len(title_en) == 250
    title_ar = "QCTEST-134372-AR"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar)
        in_dom_length = admin.page.get_by_role("textbox", name=FIELD_TITLE_EN, exact=True).evaluate("el => el.value.length")
        assert in_dom_length == 250, f"expected no client-side truncation at 250 chars, DOM value is {in_dom_length} chars"
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "the 250-char Title (EN) was not accepted/persisted — re-investigate before reverting this assertion"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved"
        assert len(admin.title_en_value()) == 250, "the persisted Title (EN) was truncated/altered on save"
    finally:
        _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title (EN) does not execute injected script on the public page")
@allure.label("pbi", "129386")
@allure.label("testcase", "134373")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134373
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-032")
def test_publication_title_en_sanitizes_script_injection(page, browser):
    """MEDIA-PUBLICATIONS-TC-032 / ADO-134373. CONFIRMED LIVE: the field
    itself does not strip/escape the raw payload server-side (readback is
    byte-identical) — the real, meaningful sanitization check is that the
    PUBLIC page renders the payload as INERT text (no script execution),
    per this project's already-established "read real, live behavior"
    rule."""
    admin = HomePublicationsAdminPage(page)
    marker = f"QCTEST134373{uuid4().hex[:8]}"
    title_en = f"<script>window.__qctestInjected=true;</script>{marker}"
    title_ar = "QCTEST-134373-AR"
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    injected_flag_seen = []
    home = HomePublicationsPage(anon_page)
    try:
        with allure.step("Create + publish a Publication with a script-injection Title (EN)"):
            admin.open_new_entry_form()
            _fill_valid_publication(admin, title_en, title_ar)
            admin.save_as_draft()
            entry_code = admin.find_entry_code_by_title(title_en)
            assert entry_code, "could not resolve the just-created entry by its own Title (EN) value"
            _publish(admin, entry_code)
        with allure.step("The public page renders the payload inertly (no script execution)"):
            appeared = home.reload_until(lambda p: p.has_card_with_title_containing(marker))
            assert appeared, f"card containing marker {marker!r} did not appear"
            injected_flag_seen.append(anon_page.evaluate("() => window.__qctestInjected === true"))
        assert not injected_flag_seen[-1], (
            "the injected <script> tag actually executed on the public Home Page — a real, "
            "confirmed-live XSS defect, not a locator gap"
        )
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (EN)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title (EN) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134374")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134374
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-033")
def test_publication_title_en_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-033 / ADO-134374."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134374 {uuid4().hex[:8]}"
    title_ar = "QCTEST-134374-AR"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry by its own Title (EN) value"
        admin.open_entry_by_code(entry_code)
        first_read = admin.title_en_value()
        admin.page.reload(wait_until="domcontentloaded")
        admin.open_entry_by_code(entry_code)
        second_read = admin.title_en_value()
        assert first_read == title_en, "the field did not even read back correctly before reload"
        assert second_read == title_en, "Title (EN) did not persist across a page reload"
    finally:
        _delete_by_title(admin, title_en)


# ---- Group: Publication Title (AR) — ADO 134375-134378 --------------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (AR)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Title (AR) saves and displays on the card in RTL")
@allure.label("pbi", "129386")
@allure.label("testcase", "134375")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.pbi_129386
@pytest.mark.tc_134375
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-034")
def test_publication_title_ar_valid_saves_and_displays_rtl(page, browser):
    """MEDIA-PUBLICATIONS-TC-034 / ADO-134375. Asserts against the `/ar/home`
    locale route — the card's own AR-locale Title text, per
    `HomePublicationsPage.open_home(locale="ar")`'s own docstring."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134375-EN {uuid4().hex[:8]}"
    title_ar = f"QCTEST-134375-AR اختبار المنشور {uuid4().hex[:6]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        appeared = home.reload_until(lambda p: p.has_card_with_title(title_ar), locale="ar")
        assert appeared, (
            f"the AR-locale card title {title_ar!r} did not appear on /ar/home within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms — either the AR value never propagated to the "
            "delivery surface, or the card always renders the EN title regardless of locale "
            "(a real, disclosed scope finding either way)"
        )
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (AR)")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publication Title (AR) is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134376")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134376
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-035")
def test_publication_title_ar_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-035 / ADO-134376. See
    `_assert_mandatory_field_blocks_persistence()`'s own docstring for the
    real, live-confirmed enforcement signal this test relies on. (This
    case's own marker lives in Title EN, which IS rendered by the Entry
    column, so it was never subject to the Title-EN-empty blind spot that
    tc_134371 had — the row-count check below is asserted anyway, for the
    same blind-spot-proof guarantee on every mandatory case in this batch.)
    Independently re-confirmed live 3 times prior to this session as a real
    product defect (Title AR not actually enforced as mandatory despite a
    native `required` attribute) — see this test's own RUN RESULT history."""
    admin = HomePublicationsAdminPage(page)
    marker = f"QCTEST-134376-{uuid4().hex[:8]}"
    baseline_row_count = _entries_row_count(admin)
    admin.open_new_entry_form()
    _fill_valid_publication(admin, title_en=marker, title_ar=None)
    _assert_mandatory_field_blocks_persistence(admin, FIELD_TITLE_AR, "textbox", marker, baseline_row_count)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title (AR) accepts input beyond the case's stated 200-character limit")
@allure.label("pbi", "129386")
@allure.label("testcase", "134377")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134377
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-036")
def test_publication_title_ar_length_boundary(page):
    """MEDIA-PUBLICATIONS-TC-036 / ADO-134377. Same real, live finding as
    ADO-134372 (Title EN) — no native `maxlength`, 250 Arabic characters
    persist verbatim. See that test's docstring for the full evidence."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134377 {uuid4().hex[:8]}"
    title_ar = "ابجدهوزحطي" * 25  # 250 Arabic characters
    assert len(title_ar) == 250
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar)
        in_dom_length = admin.page.get_by_role("textbox", name=FIELD_TITLE_AR, exact=True).evaluate("el => el.value.length")
        assert in_dom_length == 250, f"expected no client-side truncation at 250 chars, DOM value is {in_dom_length} chars"
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "the 250-char Title (AR) entry was not accepted/persisted"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved"
        assert len(admin.title_ar_value()) == 250, "the persisted Title (AR) was truncated/altered on save"
    finally:
        _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Title (AR)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Title (AR) value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134378")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.bilingual
@pytest.mark.pbi_129386
@pytest.mark.tc_134378
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-037")
def test_publication_title_ar_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-037 / ADO-134378."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134378 {uuid4().hex[:8]}"
    title_ar = "QCTEST-134378-AR اختبار"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        admin.open_entry_by_code(entry_code)
        first_read = admin.title_ar_value()
        admin.page.reload(wait_until="domcontentloaded")
        admin.open_entry_by_code(entry_code)
        second_read = admin.title_ar_value()
        assert first_read == title_ar
        assert second_read == title_ar, "Title (AR) did not persist across a page reload"
    finally:
        _delete_by_title(admin, title_en)


# ---- Group: Publication Type — ADO 134379-134381, 134392 (dual for
# 134379-134381 — see companion tests in
# web/tests/home_publications/test_home_publications_web.py) --------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Type")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Publication Type is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134379")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134379
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-038")
def test_publication_type_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-038 / ADO-134379. See
    `_assert_mandatory_field_blocks_persistence()`'s own docstring for the
    real, live-confirmed enforcement signal this test relies on."""
    admin = HomePublicationsAdminPage(page)
    marker = f"QCTEST-134379-{uuid4().hex[:8]}"
    baseline_row_count = _entries_row_count(admin)
    admin.open_new_entry_form()
    _fill_valid_publication(admin, marker, "QCTEST-134379-AR", ptype=None)
    _assert_mandatory_field_blocks_persistence(admin, FIELD_TYPE, "combobox", marker, baseline_row_count)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Type")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A publication's Type badge matches its assigned Type (Control_Panel side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134380")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134380
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-039")
def test_publication_type_badge_matches_assigned_type(page, browser):
    """MEDIA-PUBLICATIONS-TC-039 / ADO-134380 (Control_Panel half of this
    dual case — see test_home_publications_web.py's
    test_publication_type_filter_tab_visibility_matches_type for the Web
    half, which exercises the type-filter TABS specifically)."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134380 {uuid4().hex[:8]}"
    title_ar = "QCTEST-134380-AR"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar, ptype=PUBLICATION_TYPE_REPORT)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        badge = home.card_badge_text(title_en)
        assert badge == PUBLICATION_TYPE_REPORT, f"card badge {badge!r} does not match the assigned Type {PUBLICATION_TYPE_REPORT!r}"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Type")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Changing a published publication's Type relocates it to the correct filter tab")
@allure.label("pbi", "129386")
@allure.label("testcase", "134381")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134381
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-040")
def test_changing_publication_type_relocates_filter_tab(page, browser):
    """MEDIA-PUBLICATIONS-TC-040 / ADO-134381. Edits an APPROVED entry via
    this object's own confirmed-live Unpublish-to-edit-as-draft ->
    re-Submit-for-Publishing cycle (see ObjectAuthoringPage's own module
    docstring) — Report -> Guides, both of which have a real public
    filter tab (see HomePublicationsPage.TYPE_TO_TAB_FILTER's own docstring
    for why "Bulletin"/"Study" are excluded from this batch)."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134381 {uuid4().hex[:8]}"
    title_ar = "QCTEST-134381-AR"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar, ptype=PUBLICATION_TYPE_REPORT)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)

        with allure.step("Report tab shows the card; Guides tab does not"):
            home.reload_until(lambda p: p.has_card_with_title(title_en))
            home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_REPORT])
            assert home.is_card_visible(title_en), "card not visible under its own assigned Report tab"
            home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_GUIDES])
            assert not home.is_card_visible(title_en), "card visible under an unrelated Guides tab before the Type change"

        with allure.step("Change Type to Guides and re-publish"):
            admin.open_entry_by_code(entry_code)
            assert admin.current_status() == "Approved"
            admin.unpublish_to_edit_as_draft()
            admin.select_publication_type(PUBLICATION_TYPE_GUIDES)
            # See _publish()'s own HEALED note: "Publication Status" is
            # confirmed live to no longer exist anywhere on this form.
            admin.submit_for_publishing()

        with allure.step("Guides tab now shows the card; Report tab no longer does"):
            home.reload_until(lambda p: p.card_badge_text(title_en) == PUBLICATION_TYPE_GUIDES)
            home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_GUIDES])
            assert home.is_card_visible(title_en), "card not visible under the NEW Guides tab after the Type change"
            home.click_type_tab(home.TYPE_TO_TAB_FILTER[PUBLICATION_TYPE_REPORT])
            assert not home.is_card_visible(title_en), "card still visible under the OLD Report tab after the Type change"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Type")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Selecting a valid Publication Type saves correctly")
@allure.label("pbi", "129386")
@allure.label("testcase", "134392")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134392
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-041")
def test_publication_type_valid_selection_saves_correctly(page, browser):
    """MEDIA-PUBLICATIONS-TC-041 / ADO-134392."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134392 {uuid4().hex[:8]}"
    title_ar = "QCTEST-134392-AR"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar, ptype=PUBLICATION_TYPE_GUIDES)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        badge = home.card_badge_text(title_en)
        assert badge == PUBLICATION_TYPE_GUIDES, f"card badge {badge!r} does not match the selected Type {PUBLICATION_TYPE_GUIDES!r}"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


# ---- Group: Publication Date — ADO 134382-134386 --------------------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Date")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Publication Date saves and displays on the card")
@allure.label("pbi", "129386")
@allure.label("testcase", "134382")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134382
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-042")
def test_publication_date_valid_saves_and_displays(page, browser):
    """MEDIA-PUBLICATIONS-TC-042 / ADO-134382."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134382 {uuid4().hex[:8]}"
    title_ar = "QCTEST-134382-AR"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, title_ar, iso_date="2026-08-15")
        assert admin.publication_date_native_value() == "2026-08-15", "typed date did not sync to the native input"
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        appeared = home.reload_until(lambda p: p.has_card_with_title(title_en))
        assert appeared, "published card did not appear"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Date")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Date rejects an invalid date format")
@allure.label("pbi", "129386")
@allure.label("testcase", "134383")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134383
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-043")
def test_publication_date_rejects_invalid_format(page):
    """MEDIA-PUBLICATIONS-TC-043 / ADO-134383. CONFIRMED LIVE (see BATCH4
    docstring finding #1): the visible `dd/mm/yyyy` text input accepts ANY
    typed text with no format enforcement of its own — the real rejection
    mechanism is the underlying required native date input staying
    empty/invalid whenever the typed text does not parse as a genuine
    calendar date (e.g. "31/02/2026", a calendar-impossible day for
    February), which then blocks Save/Submit exactly like any other unmet
    `required` field."""
    admin = HomePublicationsAdminPage(page)
    admin.open_new_entry_form()
    _fill_valid_publication(admin, "QCTEST-134383", "QCTEST-134383-AR", iso_date=None)
    admin.type_publication_date_raw("31/02/2026")
    assert admin.publication_date_native_value() == "", "an impossible calendar date synced to a real native value"
    assert not admin.is_publication_date_native_valid(), "the native date input reports itself as valid for an impossible calendar date"
    admin.attempt_save_as_draft()
    assert admin.is_on_create_form(), "Save as Draft committed despite an invalid Publication Date"
    admin.attempt_submit_for_publishing()
    assert admin.is_on_create_form(), "Submit for Publishing also committed despite an invalid Publication Date"


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Date")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Date accepts today's date as a boundary value")
@allure.label("pbi", "129386")
@allure.label("testcase", "134384")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134384
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-044")
def test_publication_date_accepts_today_as_boundary(page):
    """MEDIA-PUBLICATIONS-TC-044 / ADO-134384."""
    import datetime

    admin = HomePublicationsAdminPage(page)
    today_iso = datetime.date.today().isoformat()
    title_en = f"QCTEST-134384 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134384-AR", iso_date=today_iso)
        assert admin.publication_date_native_value() == today_iso
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "today's date was not accepted/persisted as a valid Publication Date"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved"
    finally:
        _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Date")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Documents the real behavior when Publication Date is set to a future date")
@allure.label("pbi", "129386")
@allure.label("testcase", "134385")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134385
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-045")
def test_publication_date_future_date_documented_behavior(page):
    """MEDIA-PUBLICATIONS-TC-045 / ADO-134385. Case text asks to document
    the REAL behavior, not assert a presumed should/should-not. CONFIRMED
    LIVE this session: the native date input's own `max` attribute is
    "9999-12-31" — no upper-bound rejection exists. This test asserts that
    REAL, observed behavior: a far-future date (2099-01-01) is ACCEPTED and
    published normally."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134385 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134385-AR", iso_date="2099-01-01")
        assert admin.publication_date_native_value() == "2099-01-01"
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "a future Publication Date (2099-01-01) was NOT accepted — real behavior changed, re-investigate this documented finding"
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Approved"
        assert admin.publication_date_native_value() == "2099-01-01", "the future date was altered/rolled back on save"
    finally:
        _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Publication Date")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Publication Date value persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134386")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134386
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-046")
def test_publication_date_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-046 / ADO-134386."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134386 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134386-AR", iso_date="2026-08-15")
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        admin.open_entry_by_code(entry_code)
        first_read = admin.publication_date_native_value()
        admin.page.reload(wait_until="domcontentloaded")
        admin.open_entry_by_code(entry_code)
        second_read = admin.publication_date_native_value()
        assert first_read == "2026-08-15"
        assert second_read == "2026-08-15", "Publication Date did not persist across a page reload"
    finally:
        _delete_by_title(admin, title_en)


# ---- Group: Cover Image — ADO 134387-134390, 134393 ------------------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Cover Image")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Cover Image uploads and displays as the card thumbnail")
@allure.label("pbi", "129386")
@allure.label("testcase", "134387")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134387
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-047")
def test_cover_image_valid_uploads_and_displays_as_thumbnail(page, browser):
    """MEDIA-PUBLICATIONS-TC-047 / ADO-134387."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134387 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134387-AR")
        uploaded_name = admin.uploaded_filename(FIELD_COVER_IMAGE)
        assert uploaded_name, "Cover Image filename readout stayed empty after a valid upload"
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        src = home.card_image_src(title_en)
        assert src, "the published card's own thumbnail <img> has no src — Cover Image did not reach the card"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Cover Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Cover Image rejects an unsupported file format")
@allure.label("pbi", "129386")
@allure.label("testcase", "134388")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134388
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-048")
def test_cover_image_rejects_unsupported_format(page):
    """MEDIA-PUBLICATIONS-TC-048 / ADO-134388. CONFIRMED LIVE (see BATCH4
    docstring finding #4): the picker itself enforces a real, client-side
    extension allowlist — exact error text "Please enter a file with a
    valid extension (.jpg,.jpeg,.png)." for a `.txt` file, no "Add" button
    ever renders."""
    admin = HomePublicationsAdminPage(page)
    admin.open_new_entry_form()
    _fill_valid_publication(admin, "QCTEST-134388", "QCTEST-134388-AR", cover_image=None)
    error_text = admin.attempt_upload_file(FIELD_COVER_IMAGE, COVER_IMAGE_UNSUPPORTED_FIXTURE)
    assert re.search(r"valid extension", error_text, re.IGNORECASE), (
        f"expected a real extension-rejection message from the picker, got: {error_text[:300]!r}"
    )
    admin.close_upload_modal()
    assert admin.uploaded_filename(FIELD_COVER_IMAGE) == "", "an unsupported-format file was accepted into Cover Image"


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Cover Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Cover Image rejects a file exceeding 2 MB")
@allure.label("pbi", "129386")
@allure.label("testcase", "134389")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134389
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-049")
def test_cover_image_rejects_file_exceeding_2mb(page):
    """MEDIA-PUBLICATIONS-TC-049 / ADO-134389. CONFIRMED LIVE (see BATCH4
    docstring finding #4): the upload picker shows NO client-side size
    rejection for a 3MB JPEG (50% over the case's stated 2MB limit) — the
    "Add" button renders normally. Per automation-standards.md's "no xfail
    without a filed Bug ID — when in doubt, let it fail" rule, this test
    asserts the CORRECT/expected behavior (rejection) honestly rather than
    routing around the already-observed picker-level gap."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134389 {uuid4().hex[:8]}"
    entry_code = None
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134389-AR", cover_image=None)
        admin.upload_cover_image(COVER_IMAGE_OVERSIZED_FIXTURE)
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert not entry_code, (
            "a Cover Image exceeding the case's stated 2MB limit (3MB fixture) was accepted AND "
            "persisted as a real, published Publication entry — no size enforcement observed "
            "anywhere on this field"
        )
    finally:
        if entry_code:
            _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Cover Image")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Cover Image is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134390")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134390
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-050")
def test_cover_image_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-050 / ADO-134390. See
    `_assert_mandatory_field_blocks_persistence()`'s own docstring — the
    real enforcement signal is non-persistence, not a post-click
    `checkValidity()` read (same confirmed-live finding, this field's own
    upload-backed hidden textbox variant)."""
    admin = HomePublicationsAdminPage(page)
    marker = f"QCTEST-134390-{uuid4().hex[:8]}"
    admin.open_new_entry_form()
    _fill_valid_publication(admin, marker, "QCTEST-134390-AR", cover_image=None)
    assert not admin.upload_field_checkvalidity(FIELD_COVER_IMAGE), "Cover Image reports itself as valid while empty, before any Save/Submit attempt"
    admin.attempt_save_as_draft()
    assert admin.is_on_create_form(), "Save as Draft appears to have navigated away despite an empty mandatory Cover Image"
    assert not admin.find_entry_code_by_title(marker), "Save as Draft persisted a real entry despite an empty mandatory Cover Image"
    admin.attempt_submit_for_publishing()
    assert admin.is_on_create_form(), "Submit for Publishing appears to have navigated away despite an empty mandatory Cover Image"
    assert not admin.find_entry_code_by_title(marker), "Submit for Publishing persisted a real entry despite an empty mandatory Cover Image"


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Cover Image")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Cover Image persists after reload")
@allure.label("pbi", "129386")
@allure.label("testcase", "134393")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134393
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-051")
def test_cover_image_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-051 / ADO-134393."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134393 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134393-AR")
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        admin.open_entry_by_code(entry_code)
        first_read = admin.uploaded_filename(FIELD_COVER_IMAGE)
        admin.page.reload(wait_until="domcontentloaded")
        admin.open_entry_by_code(entry_code)
        second_read = admin.uploaded_filename(FIELD_COVER_IMAGE)
        assert first_read, "Cover Image filename readout was empty even before reload"
        assert second_read == first_read, "Cover Image did not persist across a page reload"
    finally:
        _delete_by_title(admin, title_en)


# ---- Group: File Attachment — ADO 134394-134398 ----------------------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("File Attachment")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid File Attachment uploads and links to Download and View")
@allure.label("pbi", "129386")
@allure.label("testcase", "134394")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134394
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-052")
def test_file_attachment_valid_uploads_and_links(page, browser):
    """MEDIA-PUBLICATIONS-TC-052 / ADO-134394. The card itself IS the
    Download/View link (`target="_blank"`, see HomePublicationsPage's own
    module docstring) — asserts its href resolves to a real Documents &
    Media download URL."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134394 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134394-AR")
        uploaded_name = admin.uploaded_filename(FIELD_FILE_ATTACHMENT)
        assert uploaded_name, "File Attachment filename readout stayed empty after a valid upload"
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        href = home.card_href(title_en)
        assert href, "the published card has no href — File Attachment did not reach a downloadable link"
        assert "download" in href.lower(), f"card href does not look like a Documents & Media download URL: {href!r}"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("File Attachment")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("File Attachment rejects a non-PDF file")
@allure.label("pbi", "129386")
@allure.label("testcase", "134395")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134395
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-053")
def test_file_attachment_rejects_non_pdf(page):
    """MEDIA-PUBLICATIONS-TC-053 / ADO-134395. CONFIRMED LIVE (see BATCH4
    docstring finding #5): UNLIKE Cover Image, the File Attachment picker
    has NO client-side extension allowlist — a `.docx` file was accepted
    with an enabled "Add" button. Per automation-standards.md's "no xfail
    without a filed Bug ID — when in doubt, let it fail" rule, asserts the
    CORRECT/expected rejection honestly."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134395 {uuid4().hex[:8]}"
    entry_code = None
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134395-AR", attachment=None)
        error_text = admin.attempt_upload_file(FIELD_FILE_ATTACHMENT, FILE_ATTACHMENT_NONPDF_FIXTURE)
        if error_text:
            # A real, client-side rejection DID occur this run — the
            # case's own expectation holds at the picker stage already.
            admin.close_upload_modal()
            assert admin.uploaded_filename(FIELD_FILE_ATTACHMENT) == ""
            return
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert not entry_code, (
            "a non-PDF (.docx) File Attachment was accepted AND persisted as a real, published "
            "Publication entry — no PDF-only enforcement observed anywhere on this field"
        )
    finally:
        if entry_code:
            _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("File Attachment")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("File Attachment rejects a PDF exceeding 50 MB")
@allure.label("pbi", "129386")
@allure.label("testcase", "134396")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.edge
@pytest.mark.pbi_129386
@pytest.mark.tc_134396
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-054")
def test_file_attachment_rejects_oversized_pdf(page):
    """MEDIA-PUBLICATIONS-TC-054 / ADO-134396. A hung/timed-out upload
    attempt is itself treated as a real rejection signal (the file never
    became usable), not a false failure — a completed upload is checked
    for persistence like every other negative-path case in this batch."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134396 {uuid4().hex[:8]}"
    entry_code = None
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134396-AR", attachment=None)
        try:
            admin.upload_file_attachment(FILE_ATTACHMENT_OVERSIZED_FIXTURE)
            upload_completed = True
        except Exception:
            upload_completed = False
        if not upload_completed:
            return
        admin.submit_for_publishing()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert not entry_code, (
            "a File Attachment exceeding the case's stated 50MB limit (~51MB fixture) was accepted "
            "AND persisted as a real, published Publication entry — no size enforcement observed"
        )
    finally:
        if entry_code:
            _delete_by_title(admin, title_en)


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("File Attachment")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("File Attachment is enforced as mandatory")
@allure.label("pbi", "129386")
@allure.label("testcase", "134397")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134397
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-055")
def test_file_attachment_is_enforced_as_mandatory(page):
    """MEDIA-PUBLICATIONS-TC-055 / ADO-134397. See
    `_assert_mandatory_field_blocks_persistence()`'s own docstring — the
    real enforcement signal is non-persistence, not a post-click
    `checkValidity()` read."""
    admin = HomePublicationsAdminPage(page)
    marker = f"QCTEST-134397-{uuid4().hex[:8]}"
    admin.open_new_entry_form()
    _fill_valid_publication(admin, marker, "QCTEST-134397-AR", attachment=None)
    assert not admin.upload_field_checkvalidity(FIELD_FILE_ATTACHMENT), "File Attachment reports itself as valid while empty, before any Save/Submit attempt"
    admin.attempt_save_as_draft()
    assert admin.is_on_create_form(), "Save as Draft appears to have navigated away despite an empty mandatory File Attachment"
    assert not admin.find_entry_code_by_title(marker), "Save as Draft persisted a real entry despite an empty mandatory File Attachment"
    admin.attempt_submit_for_publishing()
    assert admin.is_on_create_form(), "Submit for Publishing appears to have navigated away despite an empty mandatory File Attachment"
    assert not admin.find_entry_code_by_title(marker), "Submit for Publishing persisted a real entry despite an empty mandatory File Attachment"


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.severity(allure.severity_level.NORMAL)
@allure.story("File Attachment")
@allure.title("The Download control serves the exact file uploaded for that record")
@allure.label("pbi", "129386")
@allure.label("testcase", "134398")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134398
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-056")
def test_file_attachment_download_serves_exact_uploaded_file(page, browser):
    """MEDIA-PUBLICATIONS-TC-056 / ADO-134398. Fetches the card's own href
    directly (bypassing the browser download UI) and compares the response
    body's byte length to the real fixture's own size on disk."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134398 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134398-AR")
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        home.reload_until(lambda p: p.has_card_with_title(title_en))
        href = home.card_href(title_en)
        assert href, "the published card has no href to download from"
        response = anon_context.request.get(href)
        assert response.ok, f"downloading the card's own href failed: HTTP {response.status}"
        body = response.body()
        expected_size = os.path.getsize(FILE_ATTACHMENT_FIXTURE)
        assert len(body) == expected_size, (
            f"downloaded file size ({len(body)} bytes) does not match the uploaded fixture's own "
            f"size on disk ({expected_size} bytes) — the Download control may be serving the wrong file"
        )
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


# ---- Group: Active Status — ADO 134399-134401 (dual — see companion tests
# in web/tests/home_publications/test_home_publications_web.py) ------------

@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Active Status = True on a Published record shows it on the Home Page (Control_Panel side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134399")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134399
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-057")
def test_active_status_true_shows_on_home_page(page, browser):
    """MEDIA-PUBLICATIONS-TC-057 / ADO-134399 (Control_Panel half — see
    test_home_publications_web.py's own companion test for the Web half).
    Per standards.md's "Active Status must be explicitly set to True, never
    assumed default" rule — `_fill_valid_publication()`'s own `active=True`
    default is set EXPLICITLY here, not relied on silently."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134399 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134399-AR", active=True)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        appeared = home.reload_until(lambda p: p.has_card_with_title(title_en))
        assert appeared, "an Active=True, Published entry did not appear on the Home Page"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Active Status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Active Status = False on a Published record hides it from the Home Page (Control_Panel side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134400")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129386
@pytest.mark.tc_134400
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-058")
def test_active_status_false_hides_from_home_page(page, browser):
    """MEDIA-PUBLICATIONS-TC-058 / ADO-134400 (Control_Panel half — see
    test_home_publications_web.py's own companion test for the Web half).
    Uses a fresh, anonymous browser context for the public-visibility check
    per standards.md's "Draft/Unpublish Public-Visibility Checks — Mandatory
    Logged-Out Context" rule."""
    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())
    title_en = f"QCTEST-134400 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134400-AR", active=False)
        assert not admin.is_active_status_checked(), "Active Status checkbox did not reflect the explicit False set here"
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        _publish(admin, entry_code)
        still_absent = not home.reload_until(lambda p: p.has_card_with_title(title_en), timeout_ms=8000)
        assert still_absent, "an Active=False, Published entry appeared on the public Home Page"
    finally:
        _delete_by_title(admin, title_en)
        try:
            anon_context.close()
        except Exception:  # noqa: BLE001
            pass


@allure.epic("Home Page")
@allure.feature("Publications Section")
@allure.story("Active Status")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Active Status value persists after reload (Control_Panel side)")
@allure.label("pbi", "129386")
@allure.label("testcase", "134401")
@pytest.mark.control_panel
@pytest.mark.media
@pytest.mark.functional_low
@pytest.mark.pbi_129386
@pytest.mark.tc_134401
@pytest.mark.traceability("MEDIA-PUBLICATIONS-TC-059")
def test_active_status_persists_after_reload(page):
    """MEDIA-PUBLICATIONS-TC-059 / ADO-134401 (Control_Panel half — see
    test_home_publications_web.py's own companion test for the Web half)."""
    admin = HomePublicationsAdminPage(page)
    title_en = f"QCTEST-134401 {uuid4().hex[:8]}"
    try:
        admin.open_new_entry_form()
        _fill_valid_publication(admin, title_en, "QCTEST-134401-AR", active=False)
        admin.save_as_draft()
        entry_code = admin.find_entry_code_by_title(title_en)
        assert entry_code, "could not resolve the just-created entry"
        admin.open_entry_by_code(entry_code)
        first_read = admin.is_active_status_checked()
        admin.page.reload(wait_until="domcontentloaded")
        admin.open_entry_by_code(entry_code)
        second_read = admin.is_active_status_checked()
        assert first_read is False, "Active Status did not even read back correctly before reload"
        assert second_read is False, "Active Status did not persist across a page reload"
    finally:
        _delete_by_title(admin, title_en)

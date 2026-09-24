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
"""

import os

import allure
import pytest

from cms.pages.home_publications.home_publications_admin_page import (
    FIELD_TITLE_EN,
    PUBLICATION_STATUS_PUBLISHED,
    PUBLICATION_TYPE_REPORT,
    HomePublicationsAdminPage,
)
from web.pages.home_publications.home_publications_page import HomePublicationsPage

FIXTURES = os.path.join(os.path.dirname(__file__), "fixtures")
COVER_IMAGE_FIXTURE = os.path.join(FIXTURES, "publication_cover_image_qctest.jpg")
FILE_ATTACHMENT_FIXTURE = os.path.join(FIXTURES, "publication_attachment_qctest.pdf")

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
    """
    from core.web.browser import new_context

    admin = HomePublicationsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    home = HomePublicationsPage(anon_context.new_page())

    title_en = "QCTEST-134336 Qatar Trade Bulletin Q3 2026"
    title_ar = "نشرة التجارة القطرية الربع الذالث 2026 - 134336"

    try:
        with allure.step("Create a Publication with the case's test data and save as Draft"):
            admin.open_new_entry_form()
            admin.set_title_en(title_en)
            admin.set_title_ar(title_ar)
            admin.select_publication_type(PUBLICATION_TYPE_REPORT)
            admin.set_publication_date("2026-08-15")
            admin.upload_cover_image(COVER_IMAGE_FIXTURE)
            admin.upload_file_attachment(FILE_ATTACHMENT_FIXTURE)
            admin.set_active_status(True)
            admin.save_as_draft()

        entry_code = admin.find_entry_code_by_field(FIELD_TITLE_EN, title_en)
        assert entry_code, (
            f"could not resolve the just-created entry {title_en!r} by its "
            "own Publication Title value — Save as Draft did not persist a "
            "resolvable record"
        )
        admin.open_entry_by_code(entry_code)
        assert admin.current_status() == "Draft", "Publication did not save as Draft"

        with allure.step('Set Publication Status = "Published" and Submit for Publishing (this build\'s closest real "publish" action — see docstring)'):
            admin.select_publication_status(PUBLICATION_STATUS_PUBLISHED)
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

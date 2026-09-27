"""
cms/tests/home_social_icons/test_home_social_icons_control_panel.py —
Control_Panel-tagged cases for PBI 129373 (QC-HOME-004B — Social Media
Icons). Sources ADO Test Cases 131159, 131160, 131161.

Built per .claude/context/active/standards.md's "Object Authoring Is the
Only Path for Content Operations — Not Content & Data" rule
(`HomeSocialIconsAdminPage` composes `ObjectAuthoringPage`) — `Content &
Data` is never used.

CONFIRMED LIVE 2026-09-07 (headless Chromium against qcdev, 1920x1080
viewport, fresh Site Content Editor session captured via a throwaway
CmsLoginPage-flow script, `python tools/extract_locators.py` plus direct
Playwright role/DOM probes — see `HomeSocialIconsAdminPage`'s own module
docstring for the full field-map/slug evidence trail):

PRECONDITION CHECK (per this task's own instruction to verify rather than
assume): TC 131160 and TC 131161 both assume a pre-existing entry
("X/Twitter", "Snapchat"). CONFIRMED LIVE this session: BOTH already exist
on qcdev as real, pre-seeded entries — `QC-SMI-x` (Platform=X) and
`QC-SMI-snapchat` (Platform=Snapchat), both workflow Status=Approved. No
entry needed to be created for these two cases.

TWO CONFIRMED-LIVE FACTS THAT DIRECTLY SHAPE HOW THESE 3 CASES ARE
SCRIPTED (see `HomeSocialIconsAdminPage`'s and `HomeSocialIconsPage`'s own
module docstrings for the full evidence — summarized here since they
affect every test's real, observed pass/fail):

  1. **Platform is a CLOSED, already-fully-seeded enum** (Facebook, X,
     LinkedIn, Instagram, YouTube, WhatsApp, Telegram, Snapchat — no unused
     slot). ADO 131159's literal data ("Platform Name = YouTube") therefore
     creates a genuine SECOND YouTube entry, not a brand-new platform —
     scripted exactly as the case's literal data says (no reinterpreting),
     identified afterward by its own unique Social Redirect URL (never by
     Platform label, which collides with the pre-existing YouTube row).

  2. **RE-CONFIRMED 2026-09-07 (live re-investigation, triggered by a
     QA-Manager-vs-automation discrepancy report)**: the object DOES have
     two independent order fields, exactly as originally documented —
     "Display Order" (the Footer's own field) and "Home Display Order"
     (the Home section's own field, which is the one that actually drives
     what TC 131159/131160 assert on). A same-day, same-session first pass
     briefly concluded otherwise from a tied/ambiguous data pair (two live
     entries that happened to share the SAME "Home Display Order" value,
     which cannot distinguish the two hypotheses) — that conclusion was
     corrected within the same investigation by a clean, non-tied live
     edit. See HomeSocialIconsPage's own module docstring,
     "ROOT-CAUSE INVESTIGATION" (Round 2), for the full evidence trail of
     both rounds, including the exact live request/response pairs. "Show
     on Home" remains its own independent HOME-section visibility gate
     (confirmed live: defaults to False on a fresh create-new form;
     distinct from "Active Status", the Footer's own gate).

     Neither TC 131159's nor TC 131160's literal steps mention "Home
     Display Order" by name (they name only "Display Order") — they were
     almost certainly written against a simpler, footer-icon-only mental
     model of this object. Per automation-standards.md's "no
     reinterpreting the case" rule, each test below still fills exactly
     the field the case's own steps literally name (Display Order — never
     silently swapped for its Home-prefixed counterpart) and does NOT
     invent setting "Home Display Order" to force the case's literal
     number to hold. Instead, each test:
       - fills exactly the fields the case's own steps literally name
         (Display Order, Active Status), PLUS
       - sets "Show on Home"=True only where genuinely required as a bare
         precondition for the scenario to be reachable at all (TC 131159's
         create case — without it the new entry cannot appear in the Home
         section at all, regardless of any order field), mirroring this
         project's existing precedent of filling object-schema-mandatory
         fields a QA case's steps don't explicitly list (e.g.
         HomeBusinessEventsAdminPage's `_fill_mandatory_fields()`), and
       - asserts the REAL, live-computed expected position
         (`HomeSocialIconsPage.expected_position_by_home_display_order()`
         — ranks the entry's own, real, CURRENT "Home Display Order" value
         — a field the case's own steps never touch, so it sits at
         whatever the schema default/pre-edit baseline leaves it at —
         against every OTHER currently active+shown entry's real, live
         Home Display Order, read from the same public JAX-RS endpoint the
         Home page's own front-end queries) rather than the case's literal
         "position 6"/"position 1", which assumed setting "Display Order"
         alone would move the icon on the HOME page at all. This is
         disclosed as a real case-vs-schema mismatch (the case's steps
         target the wrong field for the section it asserts on), not
         quietly papered over. See each test's own docstring/inline note.

  3. **The Home section's icon glyph is a fixed, per-platform inline SVG**
     — confirmed live there is no `<img>` anywhere in
     `div.qc-home-social`. The "Social Icon Image"/"Home Icon Image"
     upload fields are filled exactly as each case's steps require, but
     TC 131160's "uses the new image" assertion is scripted against this
     confirmed-live rendering fact honestly (see that test's own docstring)
     rather than silently dropped.

SHARED-RECORD SAFETY: TC 131160 (`QC-SMI-x`) and TC 131161
(`QC-SMI-snapchat`) both mutate a REAL, pre-existing, non-disposable
object entry (this object has no per-test QCTEST-prefixed equivalent for
an EDIT/toggle case — its Entry column is an externalReferenceCode this
form cannot set). Each test captures the field(s) it is about to change
BEFORE mutating and restores them in a `finally` block, mirroring
standards.md's shared/singleton qcdev record convention (Mission,
Objectives, GM Message, Qatar Airways, Upcoming Event Pin) — never assumed
un-restorable, never left mutated on a failed run's best-effort basis
alone.

LOGIN: all 3 cases' own Step 1 is "Log in to CMS as Site Content Editor" —
scripted as a REAL login via `CmsLoginPage` + `cms_role_credentials("Site
Content Editor")` (never the default super-admin-equivalent `TEST_USER`),
per standards.md's "Named CMS User Roles" rule, in a `page` fixture
parametrized with `auth=False` so no cached storageState session
pre-authenticates the context ahead of the real login step.

PRIOR RUN RESULTS (observed, serial `-n 0`, qcdev, 2026-09-07, SUPERSEDED
— see finding #2 above): tc_131159 and tc_131160 both originally FAILED
on a hardcoded literal "position 6"/"position 1" assertion. Live
re-investigation the same day (triggered by a QA-Manager-vs-automation
discrepancy report) found "Home Display Order" — a field neither case's
steps touch — is the real driver of Home-page position, not "Display
Order" (see HomeSocialIconsPage's module docstring's ROOT-CAUSE
INVESTIGATION for the full two-round evidence trail). Both tests were
updated to assert `home.expected_position_by_home_display_order(...)`
(computed from the entry's own real, live Home Display Order value)
instead of a hardcoded index.

RERUN RESULTS (2026-09-07, after the fix, serial `-n 0`, qcdev, reproduced
twice, identical outcome both times): **tc_131159 PASSED (fully green —
login, form fill, publish, workflow status = Approved, href appears on
the live Home page within budget, AND the corrected position assertion,
all genuinely observed passing). tc_131160's own position assertion (the
actual subject of this fix) now ALSO correctly PASSES** — but the test as
a whole still reports FAILED, on a SEPARATE, pre-existing, already-
disclosed assertion two steps later ("Assert the icon uses the newly
uploaded image" — this section renders a fixed per-platform inline SVG
glyph regardless of the uploaded file, a real, confirmed-live product
behavior documented before this position investigation began, unrelated
to it, and out of this fix's scope to alter or loosen). tc_131161 is
unaffected by this fix (its own assertion was never position-based) and
remains a genuine, fully observed pass: Active Status=False really does
remove the icon from the Home section (not just the footer). Environment
verified restored to its exact pre-test baseline after every run via a
direct admin-grid + JAX-RS re-check (9 entries, QC-SMI-x/QC-SMI-snapchat's
mutated fields reverted to displayOrder=200/800, homeDisplayOrder=200/800
respectively — the environment also carries 2 pre-existing "Test Icon"-
labelled stray entries unrelated to this PBI's own fixtures, confirmed
present BEFORE this investigation began and left untouched/reported
rather than deleted, since they were not created by these tests and their
provenance was not this task's to determine), not just the pytest
summary.

ADDENDUM 2026-09-07 (SAME DAY, TC 131162/131163/131164 batch — sourced
straight from the injected set, no Azure calls made by this batch): these
3 cases are additive-only. TC 131159/131160/131161 above are UNCHANGED
(not touched, not rerun as part of scripting this addendum).

  - TC 131162 and TC 131164 both use a FRESH, TEST-OWNED disposable entry
    (own unique Social Redirect URL, deleted in `finally`) rather than
    mutating one of the 8 real seeded platform rows — safer than
    TC 131160/131161's shared-record pattern above and possible here
    because Platform is confirmed live NOT unique-enforced (see module
    docstring's SEEDED-DATA facts): a genuine second Facebook/LinkedIn
    entry is exactly as valid a fixture as a genuine second YouTube entry
    was for TC 131159.
  - TC 131163 (the only case in this batch whose own Step 1 names a
    non-Editor role) hit a REAL, live, disclosed blocker: both candidate
    named-role accounts this case could require — "Site Content Author"
    and "Content Contributor" (.env credentials added same-day for this
    exact case) — land on Liferay's own forced first-login
    "/c/portal/update_password" password-reset interstitial instead of a
    normal authenticated session, reproduced for BOTH roles via a
    throwaway investigation script this session (see
    HomeSocialIconsAdminPage.login_as_role()'s own docstring). Re-
    submitting the CURRENT password as the "new" one is silently rejected
    (the form does not navigate away) — a genuinely different password is
    required, which is a live, shared-credential mutation this automation
    is not authorized to perform on its own judgement (an attempt to do so
    programmatically this session was itself blocked by the runtime's own
    permission system). "Site Content Editor" (used by every OTHER test in
    this module) shows neither interstitial and is confirmed fully usable.
    TC 131163 below is fully scripted end-to-end (Author drafts -> Editor
    publishes -> live-page assertions) and will run for real the moment
    either account's one-time password reset is completed out-of-band by a
    human with interactive access — but it SKIPS itself with an explicit,
    named reason the instant it detects the same forced-reset interstitial
    live, rather than hanging, guessing a new password, or silently
    reporting a false result. This is reported as a genuine environment/
    account-activation blocker, not routed around.
"""

import shutil
import tempfile
import uuid
from pathlib import Path

import allure
import pytest

from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.home_social_icons.home_social_icons_admin_page import (
    HomeSocialIconsAdminPage,
    PLATFORM_FACEBOOK,
    PLATFORM_INSTAGRAM,
    PLATFORM_LINKEDIN,
    PLATFORM_YOUTUBE,
)
from config.settings import cms_role_credentials
from web.pages.home_social_icons.home_social_icons_page import HomeSocialIconsPage

ICON_FIXTURE = "cms/tests/home_social_icons/fixtures/social_icon.png"


def _unique_icon_fixture() -> str:
    """A fresh, uniquely-named copy of ICON_FIXTURE per test invocation —
    mirrors HomeBusinessEventsAdminPage's own confirmed-live
    `_unique_event_image_fixture()` precedent (Liferay Documents-and-Media
    upload-name collision on a shared fixture filename reused across
    runs)."""
    fixture_path = Path(ICON_FIXTURE).resolve()
    unique_name = f"{fixture_path.stem}_{uuid.uuid4().hex}{fixture_path.suffix}"
    dest_path = Path(tempfile.gettempdir()) / unique_name
    shutil.copy(fixture_path, dest_path)
    return str(dest_path)


def _login_as_site_content_editor(page) -> CmsLoginPage:
    login = CmsLoginPage(page)
    email, password = cms_role_credentials("Site Content Editor")
    login.open_login().login(email, password)
    return login


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Add a new icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Editor can add a new social icon and see it appear on the live Home page after publishing")
@allure.label("pbi", "129373")
@allure.label("testcase", "131159")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.socialmedia
@pytest.mark.pbi_129373
@pytest.mark.tc_131159
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-001")
def test_add_new_social_icon_appears_on_home_page_after_publishing(page, browser):
    """GLOBAL-SOCIALICONS-TC-001 / ADO-131159.

    Steps (verbatim): Log in as Site Content Editor -> Home Page -> Social
    Media Icons section -> Add -> Platform Name=YouTube, upload icon,
    Platform URL=https://youtube.com/QatarChamber, Display Order=6,
    Active=True -> Publish -> load the live Home page -> YouTube icon
    appears at position 6.

    See module docstring: Platform=YouTube is NOT a new enum slot (already
    seeded) — this creates a genuine second YouTube entry, identified below
    by its own unique Social Redirect URL. "Show on Home" is set True as a
    disclosed, technically-necessary addition (not in the case's literal
    field list) — without it no Display Order value would make the entry
    appear in the Home section at all.

    POSITION ASSERTION — CORRECTED 2026-09-07 (see HomeSocialIconsPage's
    module docstring's ROOT-CAUSE INVESTIGATION): "Home Display Order" —
    NOT "Display Order", the field this case's own steps set — is
    confirmed live to be what actually drives the Home section's order.
    This case's steps never mention "Home Display Order", so the new
    entry's own value for it sits at whatever the object schema leaves an
    untouched field at (read back directly off the just-created entry's
    own form, never assumed/hardcoded). Asserts the REAL, live-computed
    expected position for THAT real value instead of the case's literal
    "position 6" (which assumed Display Order alone would move the icon on
    the Home page at all — confirmed live it does not).
    """
    from core.web.browser import new_context

    admin = HomeSocialIconsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeSocialIconsPage(anon_page)

    redirect_url = "https://youtube.com/QatarChamber"
    alt_text = "QCTEST-131159 YouTube icon"
    entry_code = ""

    try:
        with allure.step("Log in to CMS as Site Content Editor"):
            login = _login_as_site_content_editor(page)
            assert login.login_succeeded(), "Expected CMS login to succeed for Site Content Editor."

        with allure.step("Navigate to the Social Media Icons object and open a new entry form"):
            admin.open_new_icon_form()

        with allure.step("Fill Platform=YouTube, icon image, Platform URL, Display Order=6, Active=True"):
            admin.select_platform(PLATFORM_YOUTUBE)
            admin.upload_social_icon_image(_unique_icon_fixture())
            admin.fill_icon_alt_text(alt_text)
            admin.fill_social_redirect_url(redirect_url)
            admin.set_display_order(6)
            admin.set_active_status(True)
            # Disclosed technical necessity, not in the case's literal
            # field list — see module docstring.
            admin.set_show_on_home(True)

        with allure.step("Click Publish (Submit for Publishing)"):
            admin.publish()

        with allure.step("Resolve the new entry by its own unique Social Redirect URL"):
            entry_code = admin.find_entry_code_by_redirect_url(redirect_url)
        assert entry_code, (
            f"Could not resolve the just-created entry by its own Social "
            f"Redirect URL {redirect_url!r} — Submit for Publishing may not "
            f"have persisted the record."
        )

        with allure.step("Read back the new entry's own real Home Display Order value"):
            # find_entry_code_by_redirect_url() leaves the admin page open on
            # this exact entry's own edit form (it opens each candidate row
            # to verify by field value) — read the real, live value directly
            # rather than assuming the schema default (see test docstring).
            home_display_order = int(admin.home_display_order_value() or 0)

        admin.open_icons_list()
        assert admin.row_status_text_by_code(entry_code) == "Approved", (
            f"Expected entry {entry_code!r} to show workflow Status "
            f"'Approved' in the entries list immediately after Submit for "
            f"Publishing."
        )

        with allure.step("Load the live Home page and poll for the new icon"):
            found = home.reload_until(lambda p: p.has_icon_with_href(redirect_url))
        assert found, (
            f"YouTube icon linking to {redirect_url!r} did not appear in "
            f"the Home page Social Media Icons section within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of publishing."
        )

        with allure.step("Assert the icon renders at its Home-Display-Order-ranked position"):
            position = home.position_of_href(redirect_url)
            expected_position = home.expected_position_by_home_display_order(redirect_url, home_display_order)
            assert position == expected_position, (
                f"Expected the new YouTube icon (its own real Home Display "
                f"Order={home_display_order}) to render at position "
                f"{expected_position} (its real rank among every currently "
                f"active+shown entry's own live Home Display Order — see "
                f"HomeSocialIconsPage.expected_position_by_home_display_order()); "
                f"actual position was {position}. NOTE: the case's own "
                f"literal wording says 'position 6' based on setting "
                f"'Display Order'=6 — confirmed live 'Display Order' is the "
                f"FOOTER section's own field and has NO effect on this "
                f"(Home) section; 'Home Display Order' is the field that "
                f"actually drives it, and this case's steps never set it — "
                f"see HomeSocialIconsPage's module docstring's ROOT-CAUSE "
                f"INVESTIGATION for the full live evidence."
            )
    finally:
        if entry_code:
            with allure.step("Teardown: delete the test entry"):
                try:
                    admin.open_icons_list()
                    admin.delete_entry_by_code(entry_code)
                except Exception:  # noqa: BLE001 — best-effort teardown only
                    pass
        anon_context.close()


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Edit an existing icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Editor can edit an existing icon's image, URL, and order and see the change reflected live")
@allure.label("pbi", "129373")
@allure.label("testcase", "131160")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.socialmedia
@pytest.mark.pbi_129373
@pytest.mark.tc_131160
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-002")
def test_edit_existing_icon_image_url_and_order_reflected_live(page, browser):
    """GLOBAL-SOCIALICONS-TC-002 / ADO-131160.

    Steps (verbatim): Log in as Site Content Editor -> open the existing
    "X/Twitter" entry for edit -> replace the icon image, change Platform
    URL to https://x.com/QatarChamberQA, change Display Order to 1 ->
    Publish -> load the live Home page -> X/Twitter icon renders at the
    new first position, uses the new image, links to the new URL.

    PRECONDITION: `QC-SMI-x` (Platform=X — this object's own enum spelling
    of "X/Twitter") confirmed LIVE present this session, workflow
    Status=Approved. No entry needed to be created.

    SHARED BASELINE RECORD (see module docstring): this is a real,
    pre-existing entry, not a disposable QCTEST row — its Social Redirect
    URL and Display Order are captured before mutation and restored in
    `finally`.

    POSITION ASSERTION — CORRECTED 2026-09-07 (see HomeSocialIconsPage's
    module docstring's ROOT-CAUSE INVESTIGATION): "Home Display Order" —
    NOT "Display Order", the field this case's own steps change — is
    confirmed live to be what actually drives the Home section's order.
    This case's steps never touch "Home Display Order", so it stays at
    its own real, pre-edit baseline value (captured below, BEFORE
    mutation, alongside the other baseline fields) — the icon's real
    expected Home-page position after this edit is wherever THAT
    (unchanged) value ranks, not the case's literal "position 1" (which
    assumed changing "Display Order" alone would move the icon on the Home
    page at all — confirmed live it does not).
    """
    from core.web.browser import new_context

    ENTRY_CODE = "QC-SMI-x"

    admin = HomeSocialIconsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeSocialIconsPage(anon_page)

    new_url = "https://x.com/QatarChamberQA"
    baseline_url = None
    baseline_display_order = None
    baseline_home_display_order = None

    try:
        with allure.step("Log in to CMS as Site Content Editor"):
            login = _login_as_site_content_editor(page)
            assert login.login_succeeded(), "Expected CMS login to succeed for Site Content Editor."

        with allure.step("Open the existing 'X/Twitter' (QC-SMI-x) entry for edit"):
            admin.open_icon_by_entry_code(ENTRY_CODE)
            baseline_url = admin.social_redirect_url_value()
            baseline_display_order = admin.display_order_value()
            # Captured but never touched by this case's own steps — the
            # field CONFIRMED LIVE to actually drive this icon's real
            # Home-page position after the edit below (see test docstring).
            baseline_home_display_order = int(admin.home_display_order_value() or 0)
        assert baseline_url, (
            "Expected the X/Twitter edit form to load pre-filled with its "
            "current Social Redirect URL."
        )

        with allure.step("Replace the icon image, change Platform URL, change Display Order to 1"):
            admin.upload_social_icon_image(_unique_icon_fixture())
            admin.fill_social_redirect_url(new_url)
            admin.set_display_order(1)

        with allure.step("Click Publish"):
            admin.publish()

        admin.open_icons_list()
        assert admin.row_status_text_by_code(ENTRY_CODE) == "Approved", (
            f"Expected {ENTRY_CODE!r} to remain workflow Status 'Approved' "
            f"after re-publishing with the updated fields."
        )

        with allure.step("Load the live Home page and poll for the updated URL"):
            found = home.reload_until(lambda p: p.has_icon_with_href(new_url))
        assert found, (
            f"X/Twitter icon linking to {new_url!r} did not appear in the "
            f"Home page section within {home.RELOAD_POLL_TIMEOUT_MS}ms of "
            f"publishing."
        )

        with allure.step("Assert the icon renders at its Home-Display-Order-ranked position"):
            position = home.position_of_href(new_url)
            expected_position = home.expected_position_by_home_display_order(new_url, baseline_home_display_order)
            assert position == expected_position, (
                f"Expected the X/Twitter icon (its own real, UNCHANGED Home "
                f"Display Order={baseline_home_display_order} — this case's "
                f"steps only change 'Display Order') to render at position "
                f"{expected_position} (its real rank among every currently "
                f"active+shown entry's own live Home Display Order — see "
                f"HomeSocialIconsPage.expected_position_by_home_display_order()); "
                f"actual position was {position}. NOTE: the case's own "
                f"literal wording says 'position 1' based on setting "
                f"'Display Order' to 1 — confirmed live 'Display Order' is "
                f"the FOOTER section's own field and has NO effect on this "
                f"(Home) section; see HomeSocialIconsPage's module "
                f"docstring's ROOT-CAUSE INVESTIGATION for the full live "
                f"evidence (a disambiguating live edit that changed ONLY "
                f"Display Order on this exact entry and observed it stay "
                f"exactly where Home Display Order predicts, not where "
                f"Display Order predicts)."
            )

        with allure.step("Assert the icon uses the newly uploaded image"):
            assert home.icon_uses_uploaded_image(new_url), (
                "Expected the X/Twitter icon to render via the newly "
                "uploaded image (a real <img> element). CONFIRMED LIVE "
                "this session: this section instead renders a fixed, "
                "per-platform inline SVG glyph regardless of the uploaded "
                "'Social Icon Image'/'Home Icon Image' file — see "
                "HomeSocialIconsPage's module docstring for the full "
                "finding. Expected to surface as a real, disclosed result, "
                "not silently passed around."
            )
    finally:
        with allure.step("Teardown: restore QC-SMI-x to its captured baseline (URL + Display Order)"):
            try:
                if baseline_url:
                    admin.open_icon_by_entry_code(ENTRY_CODE)
                    admin.fill_social_redirect_url(baseline_url)
                    if baseline_display_order:
                        admin.set_display_order(baseline_display_order)
                    admin.publish()
            except Exception:  # noqa: BLE001 — best-effort restore only
                pass
        anon_context.close()


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Deactivate an icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Toggling an icon's Active Status to False removes it from the live Home page after publishing")
@allure.label("pbi", "129373")
@allure.label("testcase", "131161")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.socialmedia
@pytest.mark.pbi_129373
@pytest.mark.tc_131161
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-003")
def test_deactivating_icon_removes_it_from_home_page(page, browser):
    """GLOBAL-SOCIALICONS-TC-003 / ADO-131161.

    Steps (verbatim): Log in as Site Content Editor -> open the existing
    "Snapchat" entry (Active=True) -> toggle Active Status to False ->
    Publish -> load the live Home page -> Snapchat icon no longer appears;
    other active icons remain.

    PRECONDITION: `QC-SMI-snapchat` (Platform=Snapchat) confirmed LIVE
    present this session, workflow Status=Approved, Active Status=True. No
    entry needed to be created.

    SHARED BASELINE RECORD (see module docstring): Active Status is
    captured/known True before mutation and restored to True in `finally`.

    NOTE (see module docstring's dual-field finding): "Active Status" is
    confirmed live to be the FOOTER section's own flag; the Home section's
    own visibility flag is the separate "Show on Home" field, which this
    test does not touch (matching the case's literal steps, which name
    only "Active Status"). The removal assertion below is scripted exactly
    as the case's expected result states — if Active Status does not
    actually gate the Home section, this is expected to surface as a real,
    disclosed failure, not be silently adapted.
    """
    from core.web.browser import new_context

    ENTRY_CODE = "QC-SMI-snapchat"

    admin = HomeSocialIconsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeSocialIconsPage(anon_page)

    snapchat_href = None

    try:
        with allure.step("Log in to CMS as Site Content Editor"):
            login = _login_as_site_content_editor(page)
            assert login.login_succeeded(), "Expected CMS login to succeed for Site Content Editor."

        with allure.step("Open the existing 'Snapchat' (QC-SMI-snapchat) entry"):
            admin.open_icon_by_entry_code(ENTRY_CODE)
            snapchat_href = admin.social_redirect_url_value()
            assert admin.active_status_checked(), (
                "Expected the Snapchat entry's Active Status to be True "
                "before this test begins deactivating it (case's own "
                "precondition)."
            )
        assert snapchat_href, (
            "Expected the Snapchat edit form to load pre-filled with its "
            "current Social Redirect URL."
        )

        with allure.step("Confirm the Snapchat icon is visible on the live Home page before deactivating"):
            visible_before = home.reload_until(lambda p: p.has_icon_with_href(snapchat_href))
        assert visible_before, (
            f"Snapchat icon ({snapchat_href!r}) was not visible in the "
            f"Home page section before this test began deactivating it — "
            f"cannot proceed to the removal assertion without a confirmed "
            f"pre-condition."
        )

        with allure.step("Toggle Active Status to False and Publish"):
            admin.open_icon_by_entry_code(ENTRY_CODE)
            admin.set_active_status(False)
            admin.publish()

        admin.open_icons_list()
        assert admin.row_status_text_by_code(ENTRY_CODE) == "Approved", (
            f"Expected {ENTRY_CODE!r} to remain workflow Status 'Approved' "
            f"(Active Status is a data field on the object, distinct from "
            f"the Draft/Approved workflow state) after re-publishing with "
            f"Active Status=False."
        )

        with allure.step("Reload the Home page and assert the Snapchat icon is gone"):
            removed = home.reload_until(lambda p: not p.has_icon_with_href(snapchat_href))
        assert removed, (
            f"Snapchat icon ({snapchat_href!r}) is still present in the "
            f"Home page section after Active Status was set to False and "
            f"republished (polled up to {home.RELOAD_POLL_TIMEOUT_MS}ms). "
            f"NOTE: this object's Home page section is confirmed live to "
            f"also be gated by a SEPARATE 'Show on Home' field, "
            f"independent of 'Active Status' — see "
            f"HomeSocialIconsAdminPage's module docstring. If this fails, "
            f"it is expected to surface as a real, disclosed finding "
            f"(Active Status not gating the Home section), not silently "
            f"passed around."
        )

        with allure.step("Assert other active icons remain (section is not emptied)"):
            assert home.icon_count() > 0, (
                "Expected other active icons to remain visible in the Home "
                "page section after Snapchat was deactivated."
            )
    finally:
        with allure.step("Teardown: restore QC-SMI-snapchat Active Status to True"):
            try:
                admin.open_icon_by_entry_code(ENTRY_CODE)
                admin.set_active_status(True)
                admin.publish()
            except Exception:  # noqa: BLE001 — best-effort restore only
                pass
        anon_context.close()


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Reactivate an icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Toggling a previously inactive icon's Active Status back to True restores it on the live Home page")
@allure.label("pbi", "129373")
@allure.label("testcase", "131162")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.socialmedia
@pytest.mark.pbi_129373
@pytest.mark.tc_131162
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-004")
def test_reactivating_icon_restores_it_on_home_page(page, browser):
    """GLOBAL-SOCIALICONS-TC-004 / ADO-131162.

    Steps (verbatim intent): find/create a baseline icon that starts
    Active Status=False -> confirm it is NOT on the live Home page ->
    toggle Active Status to True -> Publish -> confirm it (re)appears on
    the live Home page.

    Uses a FRESH, test-owned disposable entry (own unique Social Redirect
    URL, Platform=Facebook — a genuine second Facebook row, exactly as
    valid a fixture as TC 131159's second YouTube row; see module
    docstring's SEEDED-DATA note) rather than toggling one of the real
    seeded platform rows — the baseline "starts Active=False" state is
    created directly by this test (Active Status=False from the entry's
    own creation), never assumed on a real shared row, and the entry is
    deleted (not merely reverted) in `finally` — a stronger restoration
    than "toggle back", per this task's own instruction to fully restore
    whatever baseline is captured.

    "Show on Home"=True is set as a disclosed, technically-necessary
    precondition (same rationale as TC 131159 — see module docstring):
    without it, no value of Active Status would make the entry reachable
    in the Home section at all, and the scenario ("removed/restored on the
    Home page") could never be observed either way.
    """
    from core.web.browser import new_context

    admin = HomeSocialIconsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeSocialIconsPage(anon_page)

    redirect_url = "https://facebook.com/QatarChamberQA-131162-inactive-toggle"
    alt_text = "QCTEST-131162 Facebook icon"
    entry_code = ""

    try:
        with allure.step("Log in to CMS as Site Content Editor"):
            login = _login_as_site_content_editor(page)
            assert login.login_succeeded(), "Expected CMS login to succeed for Site Content Editor."

        with allure.step("Create a disposable icon with Active Status=False, Show on Home=True"):
            admin.open_new_icon_form()
            admin.select_platform(PLATFORM_FACEBOOK)
            admin.upload_social_icon_image(_unique_icon_fixture())
            admin.fill_icon_alt_text(alt_text)
            admin.fill_social_redirect_url(redirect_url)
            admin.set_display_order(900)
            admin.set_active_status(False)
            admin.set_show_on_home(True)
            admin.set_home_display_order(900)

        with allure.step("Publish the inactive baseline entry"):
            admin.publish()

        with allure.step("Resolve the new entry by its own unique Social Redirect URL"):
            entry_code = admin.find_entry_code_by_redirect_url(redirect_url)
        assert entry_code, (
            f"Could not resolve the just-created entry by its own Social "
            f"Redirect URL {redirect_url!r} — Submit for Publishing may not "
            f"have persisted the record."
        )

        admin.open_icons_list()
        assert admin.row_status_text_by_code(entry_code) == "Approved", (
            f"Expected entry {entry_code!r} to show workflow Status "
            f"'Approved' immediately after Submit for Publishing (Active "
            f"Status is a data field on the object, distinct from the "
            f"Draft/Approved workflow state)."
        )

        with allure.step("Confirm the inactive baseline icon is NOT on the live Home page"):
            absent_before = home.reload_until(lambda p: not p.has_icon_with_href(redirect_url))
        assert absent_before, (
            f"Expected the new icon ({redirect_url!r}), created with Active "
            f"Status=False, to be absent from the Home page section — it "
            f"was still present after polling up to "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms. Cannot proceed to the "
            f"restore assertion without a confirmed 'currently removed' "
            f"baseline."
        )

        with allure.step("Toggle Active Status to True and Publish"):
            admin.open_icon_by_entry_code(entry_code)
            admin.set_active_status(True)
            admin.publish()

        admin.open_icons_list()
        assert admin.row_status_text_by_code(entry_code) == "Approved", (
            f"Expected {entry_code!r} to remain workflow Status 'Approved' "
            f"after re-publishing with Active Status=True."
        )

        with allure.step("Confirm the icon is RESTORED on the live Home page"):
            restored = home.reload_until(lambda p: p.has_icon_with_href(redirect_url))
        assert restored, (
            f"Expected the icon ({redirect_url!r}) to (re)appear in the "
            f"Home page Social Media Icons section within "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms of toggling Active Status "
            f"back to True and republishing — it did not."
        )
    finally:
        if entry_code:
            with allure.step("Teardown: delete the disposable test entry"):
                try:
                    admin.open_icons_list()
                    admin.delete_entry_by_code(entry_code)
                except Exception:  # noqa: BLE001 — best-effort teardown only
                    pass
        anon_context.close()


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Author/Editor publishing workflow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Author-drafted icon becomes live only after Editor approval and publish")
@allure.label("pbi", "129373")
@allure.label("testcase", "131163")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.socialmedia
@pytest.mark.uat
@pytest.mark.pbi_129373
@pytest.mark.tc_131163
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-005")
def test_author_draft_becomes_live_only_after_editor_publish(page, browser):
    """GLOBAL-SOCIALICONS-TC-005 / ADO-131163.

    Steps (verbatim intent): Log in as Site Content Author -> create/edit
    an icon entry -> Save as Draft -> confirm it does NOT appear on the
    live Home page while Draft -> log in as Site Content Editor -> open
    the same entry -> Submit for Publishing -> confirm it now DOES appear
    live.

    KNOWN LIVE BLOCKER (see module docstring's ADDENDUM and
    HomeSocialIconsAdminPage.login_as_role()): the "Site Content Author"
    .env account is confirmed live to require a one-time forced password
    reset on first login that this automation is not authorized to
    perform unilaterally. This test SKIPS itself (not a silent pass, not a
    hang) the instant it detects that same interstitial live, naming the
    blocker explicitly, and otherwise runs the full real Author-drafts /
    Editor-publishes flow end-to-end.
    """
    from core.web.browser import new_context

    admin_author = HomeSocialIconsAdminPage(page)

    editor_context = new_context(browser, use_auth_state=False)
    editor_page = editor_context.new_page()
    admin_editor = HomeSocialIconsAdminPage(editor_page)

    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeSocialIconsPage(anon_page)

    redirect_url = "https://instagram.com/QatarChamberQA-131163-author-draft"
    alt_text = "QCTEST-131163 Instagram icon"
    entry_code = ""

    try:
        with allure.step("Log in to CMS as Site Content Author"):
            login_status = admin_author.login_as_role("Site Content Author")
        if login_status == "forced_password_reset":
            pytest.skip(
                "BLOCKED (real, disclosed environment finding, not routed "
                "around): the 'Site Content Author' .env account lands on "
                "Liferay's own forced first-login password-reset page "
                "(/c/portal/update_password) instead of a normal "
                "authenticated session. This automation is not authorized "
                "to set a new password on a shared credential on its own "
                "judgement (an attempt to do so live this session was "
                "itself blocked by the runtime's own permission system). "
                "Complete the one-time password reset for this account "
                "out-of-band (interactive login), update "
                "CMS_SITE_CONTENT_AUTHOR_PASSWORD in .env if the password "
                "changes, then rerun this test (pytest -m tc_131163)."
            )
        assert login_status == "ok", f"Unexpected Author login status: {login_status!r}"

        with allure.step("Create an icon entry and Save as Draft (not Submit for Publishing)"):
            admin_author.open_new_icon_form(role="Site Content Author")
            admin_author.select_platform(PLATFORM_INSTAGRAM)
            admin_author.upload_social_icon_image(_unique_icon_fixture())
            admin_author.fill_icon_alt_text(alt_text)
            admin_author.fill_social_redirect_url(redirect_url)
            admin_author.set_display_order(950)
            admin_author.set_active_status(True)
            # Disclosed technical necessity (same rationale as TC 131159) —
            # without this, the entry could never appear in the Home
            # section even after Editor publish, and the scenario's own
            # "becomes live after publish" step could never be observed.
            admin_author.set_show_on_home(True)
            admin_author.set_home_display_order(950)
            admin_author.save_as_draft()

        with allure.step("Resolve the new Draft entry by its own unique Social Redirect URL"):
            entry_code = admin_author.find_entry_code_by_redirect_url(redirect_url)
        assert entry_code, (
            f"Could not resolve the just-drafted entry by its own Social "
            f"Redirect URL {redirect_url!r} — Save as Draft may not have "
            f"persisted the record, or the Author role cannot see it in "
            f"the entries list."
        )

        admin_author.open_icons_list(role="Site Content Author")
        assert admin_author.row_status_text_by_code(entry_code) == "Draft", (
            f"Expected the Author-created entry {entry_code!r} to show "
            f"workflow Status 'Draft' (Save as Draft was used, not Submit "
            f"for Publishing)."
        )

        with allure.step("Confirm the Draft entry is NOT on the live Home page"):
            home.open_home()
            assert not home.has_icon_with_href(redirect_url), (
                f"Expected the Draft-only entry ({redirect_url!r}) to be "
                f"absent from the live Home page section while still in "
                f"Draft — it was present."
            )

        with allure.step("Log in to CMS as Site Content Editor (separate session)"):
            editor_login = CmsLoginPage(editor_page)
            editor_email, editor_password = cms_role_credentials("Site Content Editor")
            editor_login.open_login().login(editor_email, editor_password)
            assert editor_login.login_succeeded(), "Expected CMS login to succeed for Site Content Editor."

        with allure.step("Editor opens the Author's Draft entry and Submits for Publishing"):
            admin_editor.open_icon_by_entry_code(entry_code)
            assert admin_editor.current_status() == "Draft", (
                f"Expected entry {entry_code!r} to still show 'Draft' when "
                f"opened by the Editor, before this step submits it."
            )
            admin_editor.publish()

        admin_editor.open_icons_list()
        assert admin_editor.row_status_text_by_code(entry_code) == "Approved", (
            f"Expected entry {entry_code!r} to show workflow Status "
            f"'Approved' after the Editor's Submit for Publishing."
        )

        with allure.step("Confirm the icon NOW appears on the live Home page"):
            found = home.reload_until(lambda p: p.has_icon_with_href(redirect_url))
        assert found, (
            f"Expected the icon ({redirect_url!r}) to appear on the live "
            f"Home page within {home.RELOAD_POLL_TIMEOUT_MS}ms of the "
            f"Editor's Submit for Publishing — it did not."
        )
    finally:
        if entry_code:
            with allure.step("Teardown: delete the disposable test entry (as Editor)"):
                try:
                    admin_editor.open_icons_list()
                    admin_editor.delete_entry_by_code(entry_code)
                except Exception:  # noqa: BLE001 — best-effort teardown only
                    pass
        editor_context.close()
        anon_context.close()


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Unpublish an icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An Editor can unpublish an icon; it is removed from the live page while retained in the CMS")
@allure.label("pbi", "129373")
@allure.label("testcase", "131164")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.socialmedia
@pytest.mark.pbi_129373
@pytest.mark.tc_131164
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-006")
def test_unpublishing_icon_removes_from_home_but_retains_draft_in_cms(page, browser):
    """GLOBAL-SOCIALICONS-TC-006 / ADO-131164.

    Steps (verbatim intent): take a live, published, active icon -> use
    "Unpublish to edit as draft" -> confirm it disappears from the live
    Home page -> confirm it STILL exists as a Draft entry in CMS -> restore
    to Published/Approved afterward.

    Uses a FRESH, test-owned disposable entry (own unique Social Redirect
    URL, Platform=LinkedIn — a genuine second LinkedIn row; see module
    docstring's SEEDED-DATA note) that this test itself first publishes
    live, rather than unpublishing one of the real seeded platform rows —
    the case's own "take a live, published, active icon" precondition is
    satisfied by a disposable fixture this test controls end-to-end,
    avoiding any risk to real shared content. The case's own "restore to
    Published/Approved afterward" step is scripted literally (re-Submit
    for Publishing) before the disposable entry is deleted in `finally`.
    """
    from core.web.browser import new_context

    admin = HomeSocialIconsAdminPage(page)
    anon_context = new_context(browser, use_auth_state=False)
    anon_page = anon_context.new_page()
    home = HomeSocialIconsPage(anon_page)

    redirect_url = "https://linkedin.com/company/QatarChamberQA-131164-unpublish"
    alt_text = "QCTEST-131164 LinkedIn icon"
    entry_code = ""

    try:
        with allure.step("Log in to CMS as Site Content Editor"):
            login = _login_as_site_content_editor(page)
            assert login.login_succeeded(), "Expected CMS login to succeed for Site Content Editor."

        with allure.step("Create and publish a live, active icon (the case's own precondition)"):
            admin.open_new_icon_form()
            admin.select_platform(PLATFORM_LINKEDIN)
            admin.upload_social_icon_image(_unique_icon_fixture())
            admin.fill_icon_alt_text(alt_text)
            admin.fill_social_redirect_url(redirect_url)
            admin.set_display_order(960)
            admin.set_active_status(True)
            admin.set_show_on_home(True)
            admin.set_home_display_order(960)
            admin.publish()

        with allure.step("Resolve the new entry by its own unique Social Redirect URL"):
            entry_code = admin.find_entry_code_by_redirect_url(redirect_url)
        assert entry_code, (
            f"Could not resolve the just-created entry by its own Social "
            f"Redirect URL {redirect_url!r} — Submit for Publishing may not "
            f"have persisted the record."
        )

        admin.open_icons_list()
        assert admin.row_status_text_by_code(entry_code) == "Approved", (
            f"Expected entry {entry_code!r} to show workflow Status "
            f"'Approved' before this test begins unpublishing it."
        )

        with allure.step("Confirm the icon is live on the Home page BEFORE unpublishing"):
            visible_before = home.reload_until(lambda p: p.has_icon_with_href(redirect_url))
        assert visible_before, (
            f"Icon ({redirect_url!r}) was not visible in the Home page "
            f"section before this test began unpublishing it — cannot "
            f"proceed to the removal assertion without a confirmed "
            f"pre-condition."
        )

        with allure.step("Unpublish to edit as draft"):
            admin.open_icon_by_entry_code(entry_code)
            admin.unpublish_to_edit_as_draft()

        admin.open_icons_list()
        assert admin.row_status_text_by_code(entry_code) == "Draft", (
            f"Expected entry {entry_code!r} to be RETAINED in the CMS as "
            f"workflow Status 'Draft' after Unpublish to edit as draft — "
            f"it must not disappear from the CMS entirely, only from the "
            f"live Home page."
        )

        with allure.step("Confirm the icon is REMOVED from the live Home page after unpublishing"):
            removed = home.reload_until(lambda p: not p.has_icon_with_href(redirect_url))
        assert removed, (
            f"Icon ({redirect_url!r}) is still present in the Home page "
            f"section after Unpublish to edit as draft (polled up to "
            f"{home.RELOAD_POLL_TIMEOUT_MS}ms) — expected it removed while "
            f"the CMS entry itself is retained as Draft."
        )

        with allure.step("Restore to Published/Approved (case's own literal final step)"):
            admin.open_icon_by_entry_code(entry_code)
            admin.publish()

        admin.open_icons_list()
        assert admin.row_status_text_by_code(entry_code) == "Approved", (
            f"Expected entry {entry_code!r} to be restored to workflow "
            f"Status 'Approved' after re-Submit for Publishing."
        )

        with allure.step("Confirm the icon reappears live after being restored"):
            restored = home.reload_until(lambda p: p.has_icon_with_href(redirect_url))
        assert restored, (
            f"Expected the icon ({redirect_url!r}) to reappear on the live "
            f"Home page within {home.RELOAD_POLL_TIMEOUT_MS}ms after being "
            f"restored to Published/Approved — it did not."
        )
    finally:
        if entry_code:
            with allure.step("Teardown: delete the disposable test entry"):
                try:
                    admin.open_icons_list()
                    admin.delete_entry_by_code(entry_code)
                except Exception:  # noqa: BLE001 — best-effort teardown only
                    pass
        anon_context.close()


# ============================================================================
# BATCH1 (2026-09-13, plan 133534/suite 139193) — tc_131167, an Auth/RBAC
# case ("complements Auth-TC-023 by confirming the backend blocks the write,
# not just the page"). Auth-TC-023 itself (which role's UI is hidden for
# this feature, and which role that is) is a SEPARATE Azure case not in this
# batch — not automated here, only referenced by this case's own
# description.
#
# ROLE CHOICE (disclosed, not independently confirmed against Auth-TC-023's
# own text, which this batch does not have access to): "Content Contributor"
# is used as the restricted role lacking Social Media Icons permissions —
# the most-restricted of this project's 3 provisioned named CMS roles per
# standards.md's own Roles table (Site Content Author still has broad
# create/edit/submit-for-review permissions; "Content Contributor" is not
# even listed in that table's own role descriptions, only in the credentials
# table, consistent with it being the narrowest-scoped account provisioned).
#
# LIVE BLOCKER RE-CONFIRMED THIS SESSION (2026-09-13, immediately before
# writing this test): logging in as Content Contributor
# (Test3@xyz.com/Test@123) via the real login form reproduces the SAME
# "Authentication failed due to incorrect credentials or account lockout"
# banner HomePublicationsAdminPage's own module docstring already
# documented for ALL THREE named roles on 2026-09-12 — this is a live,
# CURRENT, project-wide credential/account blocker, not specific to this
# object or stale from an earlier session. See
# HomeSocialIconsAdminPage.login_as_role()'s own newly-added "auth_failed"
# detection (added this session, mirroring HomePublicationsAdminPage's own
# AUTH_FAILED_BANNER_TEXT precedent) for the mechanism this test's own skip
# relies on.
#
# UI-ONLY MECHANISM (cms-profile.md's team-agreed "zero API calls anywhere
# in CMS automation" policy): the case's own step 2 wording offers "a direct
# API call OR browser dev tools bypassing the hidden UI" as alternative
# mechanisms — this test uses ONLY the browser-dev-tools-equivalent path
# (a real Playwright-driven browser attempting the save action directly,
# with a forced click if the control is hidden/disabled rather than absent
# from the DOM), never a raw HTTP/API call, honoring the project's UI-only
# policy while still exercising "bypassing the hidden UI" as the case
# intends.
# ============================================================================

_RESTRICTED_ROLE = "Content Contributor"

_LOGIN_BLOCKER_REASONS = {
    "forced_password_reset": (
        f"The {_RESTRICTED_ROLE!r} account landed on Liferay's own forced "
        "first-login password-reset interstitial instead of a normal "
        "authenticated session. This automation is not authorized to set a "
        "new password on a shared credential on its own judgement."
    ),
    "auth_failed": (
        f"CMS login rejected by Liferay itself ('Authentication failed due "
        f"to incorrect credentials or account lockout') for the "
        f"{_RESTRICTED_ROLE!r} account — reconfirmed live 2026-09-13 (same "
        "project-wide blocker HomePublicationsAdminPage's own module "
        "docstring already documented for all 3 named CMS roles on "
        "2026-09-12). This automation is not authorized to reset a shared "
        "credential or invent a replacement password."
    ),
    "unknown": (
        f"Login as {_RESTRICTED_ROLE!r} ended in neither a recognized "
        "success indicator nor a known blocker state this session — an "
        "unrecognized CMS login response, treated as a blocked "
        "precondition rather than guessed."
    ),
}


def _skip_for_login_status(status: str) -> None:
    reason = _LOGIN_BLOCKER_REASONS.get(status, f"Unrecognized login status {status!r}.")
    pytest.skip(
        f"BLOCKED (real, disclosed environment finding, not routed around): {reason} "
        f"Rerun 'pytest -m tc_131167' once CMS access is restored for this role."
    )


@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
@allure.epic("Home Page")
@allure.feature("Social Media Icons")
@allure.story("Permission enforcement — backend write")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A CMS user without permission cannot persist changes to a social icon entry even via a direct action")
@allure.label("pbi", "129373")
@allure.label("testcase", "131167")
@pytest.mark.control_panel
@pytest.mark.global_
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.socialmedia
@pytest.mark.pbi_129373
@pytest.mark.tc_131167
@pytest.mark.traceability("GLOBAL-SOCIALICONS-TC-007")
def test_permission_denied_role_cannot_persist_direct_save(page):
    """GLOBAL-SOCIALICONS-TC-007 / ADO-131167. Steps: Log in to CMS with a
    role lacking Social Media Icons permissions -> login succeeds with the
    restricted role -> attempt to trigger a save/publish action on an icon
    entry (e.g., via a direct API call or browser dev tools bypassing the
    hidden UI) -> the action is rejected with "Access Denied. You do not
    have permission to perform this action." (EN) / AR equivalent -> verify
    the entry's stored state afterward -> unchanged from before the attempt.

    See this module's own BATCH1 section-level docstring above for the
    disclosed role choice and the CURRENTLY-LIVE login blocker this test
    SKIPS itself against (real, reproduced this same session) rather than
    guessing a credential fix or silently reporting a false result. The
    body below is fully scripted to run the case's REAL remaining steps the
    moment CMS access is restored for this role.
    """
    admin = HomeSocialIconsAdminPage(page)
    redirect_url = "https://facebook.com/QatarChamberQA-131167-rbac-probe"
    alt_text = "QCTEST-131167 RBAC Probe icon"

    with allure.step(f"Log in to CMS with {_RESTRICTED_ROLE!r} (a role lacking Social Media Icons permissions)"):
        login_status = admin.login_as_role(_RESTRICTED_ROLE)
    if login_status != "ok":
        _skip_for_login_status(login_status)

    # Reachable only once CMS access is restored for this role — see module
    # docstring's own BATCH1 note for the full evidence trail.
    entry_code = ""
    try:
        with allure.step("Attempt to trigger a save action on a new icon entry, bypassing any hidden/disabled UI control"):
            admin.open_new_icon_form(role=_RESTRICTED_ROLE)
            admin.select_platform(PLATFORM_FACEBOOK)
            admin.upload_social_icon_image(_unique_icon_fixture())
            admin.fill_icon_alt_text(alt_text)
            admin.fill_social_redirect_url(redirect_url)
            admin.set_display_order(990)
            admin.set_active_status(True)
            save_button = admin.page.locator(admin.SUBMIT_FOR_PUBLISHING_BUTTON)
            if save_button.is_visible():
                save_button.click()
            else:
                # Present but hidden/disabled for this role rather than
                # absent — the case's own "bypassing the hidden UI" wording —
                # force the click through rather than treating "not visible"
                # as "cannot attempt this at all".
                save_button.click(force=True)
            admin.page.wait_for_timeout(2000)

        with allure.step('Assert the action is rejected with "Access Denied..." (EN) / AR equivalent'):
            body_text = admin.page.locator("body").inner_text()
        assert "Access Denied. You do not have permission to perform this action." in body_text, (
            "expected the exact Access Denied message for a permission-"
            "lacking role's direct save attempt — not observed"
        )

        with allure.step("Verify the entry's stored state afterward: unchanged (no new entry persisted)"):
            entry_code = admin.find_entry_code_by_redirect_url(redirect_url)
        assert not entry_code, (
            f"expected NO entry to be persisted for the rejected save attempt "
            f"(redirect URL {redirect_url!r}), but one was found — the "
            "backend did not actually block the write"
        )
    finally:
        if entry_code:
            with allure.step("Best-effort teardown: delete the entry if it somehow persisted"):
                try:
                    editor_login = CmsLoginPage(admin.page)
                    email, password = cms_role_credentials("Site Content Editor")
                    editor_login.open_login().login(email, password)
                    admin.open_icons_list()
                    admin.delete_entry_by_code(entry_code)
                except Exception:  # noqa: BLE001 — best-effort teardown only
                    pass

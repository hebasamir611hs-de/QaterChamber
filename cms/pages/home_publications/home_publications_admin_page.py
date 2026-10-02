"""
cms/pages/home_publications/home_publications_admin_page.py —
HomePublicationsAdminPage.

Control_Panel Page Object for PBI 129386 (QC-HOME-010 — Publications
Section), composing the generic Object Authoring state machine
(`ObjectAuthoringPage`, see cms/pages/components/object_authoring_page.py)
with the "Publication" object — per .claude/context/active/standards.md's
"Object Authoring Is the Only Path for Content Operations — Not Content &
Data" rule. `Content & Data` is not used anywhere in this class.

SLUG — CONFIRMED LIVE 2026-09-12: the Object Authoring Forms index
(`https://qcdev.ihorizons.com/web/qatar-chamber/object-authoring`, an
authenticated session captured earlier this project) lists this object as
"Publication" with real href `/web/qatar-chamber/manage-publication` — SLUG
= "publication" below, read straight off that link, not guessed.

FIELD MAP — NOT CONFIRMED THIS SESSION (disclosed, not invented). This
session's attempt to open `manage-publication` and read its create-new
form's real field set was blocked before it could start: logging in as
EVERY ONE of the three provisioned named CMS roles
(`config.settings.cms_role_credentials`) failed live, reproducibly, with
Liferay's own banner "Error: Authentication failed due to incorrect
credentials or account lockout. Click 'Forgot Password' if the correct
credentials were provided." —

  - Site Content Editor (test1@xyz.com) — reproduced TWICE, same session,
    fresh browser context each time (this is the SAME account
    HomeSocialIconsAdminPage's own module docstring confirmed working live
    as recently as 2026-09-07 — a real regression/lockout since then, not a
    pre-existing condition).
  - Site Content Author (Test2@xyz.com) — same banner (previously, per
    HomeSocialIconsAdminPage's own docstring, this account instead hit a
    DIFFERENT blocker, a forced first-login password-reset interstitial —
    this session's "Authentication failed" is a NEW, DIFFERENT failure
    mode, not the same one recurring).
  - Content Contributor (Test3@xyz.com) — same banner.

All three failing identically, on the first attempt (not just after
repeated retries within this session), points to a genuine environment-side
condition (credential rotation not reflected in `.env`, or an account-wide
lockout policy tripped by concurrent activity — see standards.md's "No
concurrent live-browser agents against the shared qcdev session" section)
rather than a locator/script defect — this automation is not authorized to
reset a shared credential or invent a new password on its own judgement
(mirrors the precedent already documented in
HomeSocialIconsAdminPage.login_as_role()'s own docstring for a different,
narrower blocker). `login_as_role()` below detects and reports this exact
state as `"auth_failed"` rather than hanging or guessing.

Because the create-new form was never reached, the field-level constants a
real create-a-disposable-Publication flow would need (Title, Publication
Type, PDF File, Cover Image, Publish Date, etc.) are NOT included here as
named constants — adding them would mean guessing real accessible-name
strings from this project's general "Title"/"<Field> Select File" naming
conventions on other objects, which automation-standards.md's locator rules
forbid ("never invent selectors as real"). This is the narrow, genuinely-
unreachable-app case that same contract allows a disclosed TODO for. Once
CMS access is restored (either the login blocker above is resolved, or a
human confirms one of these three accounts' current real password),
re-run `python tools/extract_locators.py --url
".../manage-publication" --storage-state .auth/state.json` (or a fresh
authenticated throwaway script, mirroring every sibling admin Page
Object's own module docstring) and fill in the real field map here in the
SAME pass — never leave this TODO stale once access exists again.

FIELD MAP — CONFIRMED LIVE 2026-09-13 (batch1, plan 133534/suite 139193,
ADO-134336, the object's positive publish-workflow case): the 2026-09-12
login blocker above was for the THREE NAMED CMS ROLES specifically —
`TEST_USER` (the cached admin session every other module in this framework
already relies on) is confirmed LIVE, this session, to be unaffected and to
reach `manage-publication` normally. A fresh `tools/save_auth.py` capture +
`python tools/extract_locators.py --storage-state .auth/state.json` against
`manage-publication` was run this session — the CLI extractor's own
candidate list under-reported the EN-locale fields (each showed only a
"(Read Only)"-suffixed id-tier candidate, no clean role-based name), root-
caused via a direct `page.accessibility.snapshot()` probe (disclosed
fallback — the stateless CLI tool's generic `get_by_role()` sweep does not
replicate Playwright's own full accessible-name computation for this
form's controls, which resolve via each field's own `aria-labelledby`, not
a plain `aria-label`/`placeholder` attribute the tool's own generic
heuristics check). The REAL, confirmed field-to-accessible-name map,
exact-string (`exact=True`), including two fields whose real name carries a
trailing space:

  - "Publication Title " (EN, textbox, TRAILING SPACE is real/confirmed —
    not a typo) / "Publication Title — العربية *" (AR, required)
  - "Publication Description" (EN, textbox, no trailing space) /
    "Publication Description — العربية" (AR)
  - "Publication Type " (combobox, TRAILING SPACE is real) — real, closed
    option list confirmed live: Report, Bulletin, Study, Research Paper,
    Guides, White Paper, Manuals, Brochure. (The case's own literal "Type =
    Reports" is the closest real option, "Report" (singular) — disclosed
    substitution, not a typo left in.)
  - "Publication Date" — a NATIVE `<input type="date">` rendered by the
    browser as 3 separate Month/Day/Year sub-controls Playwright's own
    accessibility tree exposes with GENERIC (non-field-specific) names
    ("Month Month"/"Day Day"/"Year Year") — confirmed live this makes
    `get_by_role(...)`-based targeting impossible for this one field.
    SUPERSEDED 2026-09-27 (see class-level `PUBLICATION_DATE_VISIBLE_INPUT_CSS`'s
    own HEALED note below): this surface now ALSO layers a visible
    `dd/mm/yyyy` text input in front of the native input — `set_publication_date()`
    types into that visible input instead of `.fill()`-ing the native one
    directly.
  - "Cover Image" (file upload — "Cover Image Select File" hidden textbox +
    "Cover Image" filename readout, the SAME confirmed-live pattern
    `ObjectAuthoringPage.upload_file()`/`uploaded_filename()` already
    handle generically) / "File Attachment" (same pattern, second file field)
  - "Page Count " (spinbutton, TRAILING SPACE is real) — NOT filled by
    tc_134336 (not named in that case's own concrete test data)
  - "Publication Status " (combobox, TRAILING SPACE is real) — a SEPARATE,
    real editorial-status field distinct from the generic Object Authoring
    workflow's own Draft/Approved status column. Real, closed option list
    confirmed live: Draft, Published, Unpublished, Rejected. This is the
    field that actually carries the case's own literal "Published" wording
    — the generic workflow (Save as Draft/Submit for Publishing) has no
    "Published" label of its own (only Draft/Approved, confirmed project-
    wide) and this field ALSO has no "Pending Review" option (matching
    ObjectAuthoringPage's own already-confirmed absence of that status
    anywhere on this project) — see tc_134336's own docstring for how the
    case's "Submit for Review -> Pending Review" step is therefore
    disclosed-adapted.
  - "Active Status" (checkbox, no trailing space)
  - "Download Count " / "View Count " (spinbuttons — read-only counters,
    not filled by any case)

Save as Draft / Submit for Publishing buttons confirmed present, same
generic Object Authoring lifecycle as every other object on this project.

WORKFLOW — SEPARATE, ALREADY-ESTABLISHED FINDING (not new to this session):
this project's Object Authoring surface is confirmed live, across 15+ other
objects already automated in this framework (News Article, Promotional
Banner, Social Media Icon, Business Event, Strategic Pillar Card, GM
Message, Board Member, Hero Banner Slide, ...) to expose EXACTLY: Save as
Draft / Submit for Publishing / Unpublish to edit as draft, and EXACTLY two
workflow statuses, Draft / Approved — see
`cms/pages/components/object_authoring_page.py`'s own module docstring, and
this project's live, unauthenticated Object Authoring Forms landing-page
copy itself ("Each page lists that Object's existing entries and lets you
add a new one as a draft or publish it directly" — no third path named).
There is no "Pending Review" status and no "Reject" action documented or
observed anywhere on this surface for ANY object automated so far. TC
134341's literal premise (Submit for review -> Status=Pending Review ->
Reject as reviewer/Editor -> Status=Rejected) therefore has no confirmed
real counterpart on this project's CMS even independent of this session's
login blocker — see the Control_Panel test module's own docstring for how
this is disclosed rather than force-fitted.

SECTION TAG / SECTION HEADING INVESTIGATION (2026-09-27, batch of 17 ADO
cases 134344-134360) — CONFIRMED LIVE this session, via a fresh
`tools/save_auth.py` capture + a real, disclosed Playwright MCP fallback
(the CLI extractor's own `--find` scan across every route below never
needed widening beyond what it already reports; the MCP was used only to
open the Page Builder fragment configuration panel, a state the stateless
CLI extractor cannot reach): the task's own premise — "Section Tag/Heading/
Description" being a page-level/section-wide settings object for the whole
Home Page Publications section, mirroring `HomeAboutSummaryAdminPage`'s
confirmed "About Us Section" singleton (`Section Tag (EN)/(AR)`, `Section
Heading (EN)/(AR)` fields on a real `manage-about-us-section` Object
Authoring entry) — does NOT have a live counterpart for Publications on
this build. Checked, in order, and each ruled out with a concrete finding:

  1. Object Authoring Forms index (`/web/qatar-chamber/object-authoring`):
     `--find publication` resolves to exactly ONE link, "Publication" (this
     class's own SLUG, the per-record object already field-mapped above).
     `--find section` resolves to 29 "*Section" links project-wide — NONE
     named "Publications Section" (alphabetically, nothing sits between the
     confirmed-present "Our Services Section" and "Qatar Market Overview
     Section"). `--find knowledge` / `--find hub` (the section's own public
     heading text, "Explore Our Knowledge Hub") both resolve to ZERO
     candidates. There is no dedicated "Publications Section"/"Knowledge
     Hub" Object Authoring entry to open.
  2. The "Publication" object's own field map (see FIELD MAP above,
     confirmed live 2026-09-13) has no Section Tag/Section Heading field of
     any kind — only per-record Title/Description/Type/etc.
  3. "Media Center Feed Section" (`manage-media-center-feed-section`) is
     the ONE object on this project that has BOTH a `Section Heading (EN/
     AR)` field (150-char native maxlength, confirmed live via its own
     "0 / 150" live character counter) and an `Eyebrow (EN/AR)` field
     (60-char native maxlength, "0 / 60" counter — this is this object's
     own real name for what a Section Tag/label field would be, NOT
     literally labelled "Section Tag" here) — the closest real candidate
     for "the Publications section's own Tag/Heading settings". CONFIRMED
     LIVE this session this object's own `Section Type` field is a CLOSED,
     3-value enum — clicking its real combobox lists exactly `News & Press
     Releases` / `Photo Gallery` / `Video Gallery` — Publications is NOT a
     member of this enum, and the object's own 3 live entries (Entry codes
     `QCDEMO-130709-FEED-01/02/03`) are exactly those 3 types, none named
     Publications. This object's own Section Heading/Eyebrow fields
     therefore never back the Publications section's own rendered copy —
     ruled out by its own closed, live-inspected enum, not by name alone.
  4. The public Home Page's own "QC Home Publications" Page Builder
     fragment (confirmed live via its Configuration Panel, reached through
     `/en/<draftLayoutUuid>?...p_l_mode=edit`, a state the CLI extractor
     cannot reach — the disclosed Playwright MCP fallback) exposes exactly
     TWO configuration fields on its "General" tab: "Publication cards
     visible per carousel page (desktop)" (current value `5`, matching
     `HomePublicationsPage`'s own confirmed `data-qc-page-size="5"`) and
     "Publications listing page URL (Explore Publications)" (current value
     `/web/qatar-chamber/publications`, matching the public "Explore
     Publications" link's own confirmed href). NEITHER of the section's own
     rendered "Publications" tag, "Explore Our Knowledge Hub" heading, nor
     its description paragraph is exposed anywhere in this fragment's own
     configuration panel (General/Styles/Advanced tabs) — that copy is
     therefore hard-coded in the fragment's own template, not
     CMS-editable through Page Builder either.

CONCLUSION: no CMS admin surface — neither Object Authoring nor Page
Builder fragment configuration — anywhere on this qcdev build exposes an
editable "Section Tag (EN/AR)" or "Section Heading (EN/AR)" for the Home
Page Publications section. All 17 of ADO 134344-134360's own literal
premises ("...saves and displays...", "...rejects input exceeding N
characters...", etc., against THIS pair of fields) have no reachable
admin control to exercise. See the Control_Panel test module's own
docstring for how each of the 17 cases is disclosed (a real, live
per-test confirmation that the named field does not exist anywhere
reachable) rather than force-fitted onto the per-record Publication
Title/Description fields, which are a DIFFERENT field pair the case text
does not describe.

SECTION DESCRIPTION INVESTIGATION (2026-09-27, same session, batch of 9 ADO
cases 134361-134369) — a SEPARATE, independently-re-verified check, NOT
assumed to share the Section Tag/Heading batch's conclusion just because it
sounds similar (per this task's own explicit instruction). Re-ran the same
three-surface sweep against a fresh `tools/save_auth.py` capture:

  1. Object Authoring Forms index — unchanged from the Section Tag/Heading
     investigation above (same live re-check this session): still no
     "Publications Section"/"Knowledge Hub" entry among the 29 "*Section"
     links, and the per-record "Publication" object remains the only
     Publications-named entry.
  2. The "Publication" object's own create-entry form — a live
     `--find description` CLI sweep this session resolved EXACTLY the two
     already-known per-record fields from the FIELD MAP above: "Publication
     Description" (EN, plain `textbox` role, no trailing space) and
     "Publication Description — العربية" (AR, plain `textbox`). Both are
     confirmed live, this session, to be ordinary single-line-styled plain
     textboxes with NO rich-text/WYSIWYG affordance (no toolbar, no CKEditor
     iframe, no formatting controls of any kind) — i.e. even if these were
     the field the 9 cases meant (they are not — see below), they could not
     satisfy the cases' own literal "...with formatting" / "...in RTL with
     formatting" wording, which implies a WYSIWYG field distinct from this
     plain pair. These are the SAME per-record fields tc_134336 already
     exercises for its own Description value — not a section-level field.
  3. The public Home Page's own "QC Home Publications" Page Builder
     fragment's Configuration Panel — RE-OPENED live this session (fresh
     Playwright MCP fallback pass, not carried over from the 2026-09-27
     Section Tag/Heading pass alone): the General tab still exposes EXACTLY
     the same 2 fields already documented above ("Publication cards visible
     per carousel page (desktop)" and "Publications listing page URL
     (Explore Publications)") — no Description field of any kind on
     General, and Styles/Advanced remain pure layout/CSS controls (units,
     overflow, Hide Fragment), not content fields. The section's own
     rendered paragraph ("Access valuable insights, reports, and studies on
     business and market trends. Stay informed with up-to-date research to
     support smart decisions and growth.") is confirmed, same as the
     heading/tag copy, to be hard-coded in the fragment's own template, not
     exposed through this panel.

CONCLUSION (independently re-verified, not inherited by assumption): the
SAME absence holds for Section Description (EN/AR) as for Section Tag/
Heading — no CMS admin surface anywhere on this qcdev build exposes an
editable, section-level, rich-text "Section Description" for the Home Page
Publications section. This investigation used the SAME live-check
methodology as the Section Tag/Heading batch (deliberately re-run end to
end rather than reused from memory), and happened to land on the same
result — it did not assume it going in.
"""

import re

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url, settings

SLUG = "publication"

# Same "Authentication failed" banner text confirmed live this session for
# ALL THREE named CMS role accounts (see module docstring) — a NEW failure
# mode, distinct from HomeSocialIconsAdminPage's own documented
# FORCED_PASSWORD_RESET_PATH blocker. Substring-matched (not exact) since
# Liferay renders this inside a dismissible alert with surrounding
# whitespace/markup that varies by locale/theme.
AUTH_FAILED_BANNER_TEXT = "Authentication failed"
TERMS_OF_USE_AGREE_BUTTON_NAME = "I Agree"

ADMIN_HOME_EN_URL_PATH = "/en/home"
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTROL_MENU_NAV = 'nav[aria-label="Control Menu"]'

# ---- Confirmed-live field labels (2026-09-13, tc_134336) — see module
# docstring's FIELD MAP for the trailing-space/native-date-input evidence.
FIELD_TITLE_EN = "Publication Title "  # trailing space is real, confirmed live
FIELD_TITLE_AR = "Publication Title — العربية *"
FIELD_DESCRIPTION_EN = "Publication Description"
FIELD_DESCRIPTION_AR = "Publication Description — العربية"
FIELD_TYPE = "Publication Type "  # trailing space is real
FIELD_COVER_IMAGE = "Cover Image"
FIELD_FILE_ATTACHMENT = "File Attachment"
FIELD_PUBLICATION_STATUS = "Publication Status "  # trailing space is real
FIELD_ACTIVE_STATUS = "Active Status"
# ADDED 2026-09-27 (SECOND real defect this triage session's tc_134336
# rerun surfaced, after the upload-fixture and editEntry-code fixes): the
# module docstring's own FIELD MAP already lists "Page Count " (spinbutton,
# trailing space real) but no constant/setter existed for it, and every
# BATCH1/BATCH4 test left it at its own default "0". CONFIRMED LIVE via a
# direct Playwright MCP probe (network response body) that this object has
# a REAL, server-side `ObjectValidationRuleEngineException` requiring
# "Page count must be a positive whole number (1 or greater)." — a value of
# 0 makes the `PUT /o/c/publications/<id>` call Submit for
# Review/Publishing fires return a real HTTP 400, which the UI swallows
# silently (no visible error banner/toast — same confusing-UX class as this
# object's already-documented `data-qc-was-required` finding), leaving the
# entry stuck on Draft with no visible error. NOT part of the original
# 2026-09-13 field map's own "NOT filled by tc_134336" note being wrong —
# that note is still accurate (the *case's own test data* never names Page
# Count) — but the *object's own real, live validation rule* requires SOME
# positive value regardless, independent of any one case's data.
FIELD_PAGE_COUNT = "Page Count "  # trailing space is real

# Real, closed option lists confirmed live (see module docstring) — no
# "add a new option" affordance on either combobox.
PUBLICATION_TYPE_REPORT = "Report"
PUBLICATION_TYPE_BULLETIN = "Bulletin"
PUBLICATION_TYPE_STUDY = "Study"
PUBLICATION_TYPE_RESEARCH_PAPER = "Research Paper"
PUBLICATION_TYPE_GUIDES = "Guides"
PUBLICATION_TYPE_WHITE_PAPER = "White Paper"
PUBLICATION_TYPE_MANUALS = "Manuals"
PUBLICATION_TYPE_BROCHURE = "Brochure"

PUBLICATION_STATUS_DRAFT = "Draft"
PUBLICATION_STATUS_PUBLISHED = "Published"
PUBLICATION_STATUS_UNPUBLISHED = "Unpublished"
PUBLICATION_STATUS_REJECTED = "Rejected"

# Native `<input type="date">` for "Publication Date" — Playwright's own
# accessibility tree exposes this as 3 GENERIC (non-field-specific)
# Month/Day/Year spinbuttons, so role-based targeting is impossible for
# this one field (see module docstring). The id SUFFIX below is stable
# across page loads even though Liferay's Page Builder mints a fresh
# `fragment-<uuid>-...` PREFIX every load (this project's own already-
# documented convention) — confirmed live count=1 on this form.
#
# HEALED 2026-09-27 (31-case batch, live re-investigation): this surface now
# renders TWO controls matching the OLD `input[id$="-date-input"]` selector —
# a NEW, VISIBLE `dd/mm/yyyy` text input (`id="qc-dtp-fragment-<uuid>-date-
# input"`, class `qc-oel__dtp-text`) layered in front of the original HIDDEN
# native `<input type="date">` (`id="fragment-<uuid>-date-input"`, `required`,
# `max="9999-12-31"`) — a real UI change since 2026-09-13, not a locator
# regression. `input[id$="-date-input"]` alone is now a Playwright strict-
# mode violation (2 matches). CONFIRMED LIVE this session:
#   - The VISIBLE text input is the one a user actually types into — it
#     accepts ANY typed text with no client-side format enforcement of its
#     own (`inputmode="numeric"` is a soft keyboard hint only — confirmed
#     live that literal garbage text, e.g. "abcXYZ", is accepted and stays
#     as typed).
#   - The HIDDEN native date input only syncs to a real value when the typed
#     text parses as a genuinely valid calendar date (confirmed live:
#     "15/08/2026" synced the native input to "2026-08-15"; "31/02/2026" —a
#     calendar-invalid day for February— left the native input EMPTY, with
#     its own `validationMessage` reading "Please fill out this field.",
#     i.e. still `required`-invalid). This IS the real, live-confirmed
#     mechanism ADO-134383's "rejects an invalid date format" exercises —
#     not a visible inline error banner, but the underlying required native
#     control staying unset/invalid, which blocks Save as Draft/Submit for
#     Publishing exactly like any other unmet `required` field (see
#     `field_checkvalidity()`/`is_publication_date_native_valid()` below).
#   - `max="9999-12-31"` on the native input is the only upper bound
#     confirmed live — a future date (e.g. 2099-01-01) is accepted with no
#     client-side rejection of any kind.
PUBLICATION_DATE_VISIBLE_INPUT_CSS = 'input[id^="qc-dtp-fragment-"]'


class HomePublicationsAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) for the "Publication" object. Constructed with
    just `page` (slug fixed to "publication"). See module docstring for the
    confirmed-unreachable field map and the separate, already-established
    workflow-scope finding (no Reject/Pending Review anywhere on this
    surface)."""

    def delete_entry_by_title(self, title: str) -> bool:
        # This object holds real, irreplaceable publications (14 were lost
        # to an unscoped delete on 2026-09-27/28): only disposable QCTEST
        # titles may ever reach the delete link.
        if not title or "QCTEST" not in title.upper():
            return False
        return super().delete_entry_by_title(title)

    def newest_entry_code(self) -> str:
        raise NotImplementedError("position-based targeting is forbidden on this object")

    # HEALED 2026-09-27 (live incident, tc_134336/BATCH4 triage — see
    # `current_status()`'s own HEALED note for the full evidence trail):
    # CONFIRMED LIVE this object's own real button reads "Submit for
    # Review", never "Submit for Publishing" — the inherited
    # `ObjectAuthoringPage.SUBMIT_FOR_PUBLISHING_BUTTON` class attribute
    # (`button:has-text("Submit for Publishing")`) never matches anything
    # on this form and was the real cause of repeated 30-second
    # `Locator.click` timeouts, in BOTH the inherited `submit_for_
    # publishing()` method AND this class's own `attempt_submit_for_
    # publishing()` (which reads this same class attribute directly).
    # Overriding the class attribute here (rather than only one call site)
    # fixes every caller at once — this object's own real, different button
    # text, not a locator regression; 15+ other, correctly-labeled objects
    # keep the base class's original value unmodified.
    SUBMIT_FOR_PUBLISHING_BUTTON = 'button:has-text("Submit for Review")'

    def __init__(self, page):
        super().__init__(page, SLUG)

    def login_as_role(self, role: str) -> str:
        """Drives a REAL login (never a cached storageState) as `role`,
        mirroring HomeSocialIconsAdminPage.login_as_role()'s own confirmed-
        live pattern, extended to also detect this session's NEW
        "Authentication failed" banner (see module docstring). Returns:
          - "ok" once the normal LOGIN_SUCCESS_INDICATOR is visible,
          - "forced_password_reset" if the flow lands on Liferay's own
            forced first-login password-reset interstitial, or
          - "auth_failed" if the login form itself rejects the credentials
            with AUTH_FAILED_BANNER_TEXT.
        Callers must treat anything other than "ok" as an unmet
        precondition (skip), never attempt to resolve it themselves — same
        contract as the sibling method this mirrors."""
        from cms.pages.control_panel.login_page import CmsLoginPage
        from config.settings import cms_role_credentials

        email, password = cms_role_credentials(role)
        self.open(control_panel_url(CmsLoginPage.LOGIN_PATH))
        self.type(CmsLoginPage.USERNAME_INPUT, email)
        self.type(CmsLoginPage.PASSWORD_INPUT, password)
        self.click(CmsLoginPage.SUBMIT_BUTTON)
        try:
            agree_button = self.page.get_by_role("button", name=TERMS_OF_USE_AGREE_BUTTON_NAME)
            agree_button.wait_for(state="visible", timeout=6000)
            agree_button.click()
        except Exception:  # noqa: BLE001 — interstitial not shown for this account, proceed
            pass
        self.page.wait_for_timeout(1500)
        try:
            body_text = self.page.locator("body").inner_text()
        except Exception:  # noqa: BLE001 — best-effort read, fall through to the normal check below
            body_text = ""
        if AUTH_FAILED_BANNER_TEXT in body_text:
            return "auth_failed"
        try:
            self.page.wait_for_url("**/c/portal/update_password**", timeout=4000)
            return "forced_password_reset"
        except Exception:  # noqa: BLE001 — did not land on the reset page, proceed to the normal check
            pass
        try:
            self.page.locator(CmsLoginPage.LOGIN_SUCCESS_INDICATOR).first.wait_for(state="visible", timeout=10000)
            return "ok"
        except Exception:  # noqa: BLE001 — neither a recognized blocker nor a confirmed success
            return "unknown"

    def _ensure_admin_session(self) -> None:
        """HEALED 2026-09-14 (triage of tc_134336): mirrors OrgStructureAdminPage.
        _ensure_logged_in()/HomeBusinessEventsAdminPage._ensure_logged_in()'s
        already-confirmed-live pattern for the CACHED TEST_USER session
        specifically — deliberately a SEPARATE method from
        `_ensure_logged_in(self, role)` below (which drives a REAL named-
        role login for the tc_134341 RBAC-style flow and has a different,
        mandatory `role` argument/return contract) to avoid silently
        shadowing that existing, differently-shaped method. A stale/absent
        TEST_USER session hitting `manage-publication` directly renders the
        public "Coming Soon" placeholder with no login redirect to react
        to — this class was the confirmed-live gap in that shared pattern
        (it composes ObjectAuthoringPage directly, with no
        TEST_USER-session guard of its own).

        WIDENED 2026-09-14 (second triage round, tc_134336 group): this
        guard previously ran only at the top of `open_new_entry_form()`.
        `open_entries_list()` and `open_entry_by_code()` are also real
        first-admin-actions a test/teardown can call directly (e.g.
        `find_entry_code_by_field()` on the shared ObjectAuthoringPage base
        calls `self.open_entries_list()` then `self.open_entry_by_code()`
        in a loop) and had the exact same confirmed-live gap — none of them
        checked for a stale/absent TEST_USER session before navigating.
        Extended by overriding those two entry points below (not by editing
        the shared `ObjectAuthoringPage` base class itself, which 15+ other
        objects in this framework also compose — the smaller, safer diff:
        this project-wide base class has no session-guard concept today,
        and every other composing Page Object already carries its own,
        differently-shaped `_ensure_logged_in()`/`_ensure_admin_session()`
        variant, so adding one generic guard to the shared base risked
        double-login/role-mismatch interactions with those existing,
        untouched call sites that this triage never investigated).
        `find_entry_code_by_field()` itself needs no separate override: it
        is inherited unmodified from `ObjectAuthoringPage` and calls
        `self.open_entries_list()`/`self.open_entry_by_code()` through
        normal Python polymorphism, so it picks up this class's guarded
        overrides automatically."""
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (
            self.is_visible(CONTROL_MENU_NAV)
            or self.is_visible(CONTENT_DATA_MENU_ITEM)
            or self.is_visible(PRODUCT_MENU_TOGGLE)
        ):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_new_entry_form(self) -> "HomePublicationsAdminPage":
        self._ensure_admin_session()
        return super().open_new_entry_form()

    def open_entries_list(self) -> "HomePublicationsAdminPage":
        self._ensure_admin_session()
        return super().open_entries_list()

    def open_entry_by_code(self, entry_code: str) -> "HomePublicationsAdminPage":
        self._ensure_admin_session()
        return super().open_entry_by_code(entry_code)

    def _ensure_logged_in(self, role: str) -> str:
        """Re-login-if-needed via `/en/home`'s real session check (mirrors
        every sibling admin Page Object's own `_ensure_logged_in()`), used
        by the navigation helpers below. Returns the same status vocabulary
        as `login_as_role()` so callers can skip on a genuine blocker
        instead of hanging inside a subsequent `open_new_entry_form()`."""
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if (
            self.is_visible(CONTROL_MENU_NAV)
            or self.is_visible(CONTENT_DATA_MENU_ITEM)
            or self.is_visible(PRODUCT_MENU_TOGGLE)
        ):
            return "ok"
        return self.login_as_role(role)

    # ---- Field actions (ADDED 2026-09-13, tc_134336 — see module
    # docstring's FIELD MAP for the full confirmed-live evidence) ----------
    def set_title_en(self, value: str) -> "HomePublicationsAdminPage":
        self.fill_text(FIELD_TITLE_EN, value)
        return self

    def set_title_ar(self, value: str) -> "HomePublicationsAdminPage":
        self.fill_text(FIELD_TITLE_AR, value)
        return self

    def title_en_value(self) -> str:
        return self.field_value(FIELD_TITLE_EN)

    def title_ar_value(self) -> str:
        return self.field_value(FIELD_TITLE_AR)

    def set_description_en(self, value: str) -> "HomePublicationsAdminPage":
        self.fill_text(FIELD_DESCRIPTION_EN, value)
        return self

    def select_publication_type(self, option_label: str) -> "HomePublicationsAdminPage":
        """Real, native `role="combobox"` select — opened/closed directly
        (unlike ObjectAuthoringPage.select_combobox_option()'s "Assigned
        Tab"-specific "Open Options Menu" button pattern, confirmed live
        NOT applicable here; this field's own combobox role is clicked
        directly instead, see module docstring)."""
        combo = self.page.get_by_role("combobox", name=FIELD_TYPE, exact=True)
        combo.click()
        self.page.wait_for_timeout(400)
        listbox = self.page.locator('[role="listbox"]:visible').last
        option = listbox.get_by_role("option", name=option_label, exact=True)
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def select_publication_status(self, option_label: str) -> "HomePublicationsAdminPage":
        combo = self.page.get_by_role("combobox", name=FIELD_PUBLICATION_STATUS, exact=True)
        combo.click()
        self.page.wait_for_timeout(400)
        listbox = self.page.locator('[role="listbox"]:visible').last
        option = listbox.get_by_role("option", name=option_label, exact=True)
        option.wait_for(state="visible", timeout=5000)
        option.click()
        return self

    def _date_visible_input(self):
        return self.page.locator(PUBLICATION_DATE_VISIBLE_INPUT_CSS)

    def _date_native_input(self):
        """The hidden native `<input type="date">` twin of the visible
        `dd/mm/yyyy` text field — its `id` is the visible input's own `id`
        with the `qc-dtp-` prefix stripped (confirmed live, see module
        docstring's HEALED note)."""
        visible_id = self._date_visible_input().get_attribute("id") or ""
        native_id = visible_id[len("qc-dtp-"):] if visible_id.startswith("qc-dtp-") else visible_id
        return self.page.locator(f'#{native_id}')

    def set_publication_date(self, iso_date: str) -> "HomePublicationsAdminPage":
        """`iso_date` in `YYYY-MM-DD` — converted to this field's real,
        confirmed-live `dd/mm/yyyy` display format and typed into the
        VISIBLE text input (see module docstring's HEALED note; the
        underlying native `<input type="date">` only syncs when the typed
        text parses as a genuine calendar date)."""
        year, month, day = iso_date.split("-")
        display_value = f"{day}/{month}/{year}"
        visible = self._date_visible_input()
        visible.click()
        visible.fill("")
        self.page.keyboard.type(display_value, delay=20)
        return self

    def type_publication_date_raw(self, raw_text: str) -> "HomePublicationsAdminPage":
        """Types `raw_text` VERBATIM into the visible date text input — used
        by invalid-format cases (e.g. a calendar-impossible day, or
        non-numeric garbage) where the caller needs the exact literal typed,
        not an ISO-to-display conversion."""
        visible = self._date_visible_input()
        visible.click()
        visible.fill("")
        self.page.keyboard.type(raw_text, delay=20)
        return self

    def publication_date_display_value(self) -> str:
        return self._date_visible_input().input_value()

    def publication_date_native_value(self) -> str:
        """The synced, committed ISO value (`YYYY-MM-DD`) of the underlying
        required native date input — empty string if the visible text never
        parsed into a real calendar date (see module docstring)."""
        return self._date_native_input().input_value()

    def is_publication_date_native_valid(self) -> bool:
        return self._date_native_input().evaluate("el => el.checkValidity()")

    def upload_cover_image(self, file_path: str) -> "HomePublicationsAdminPage":
        self.upload_file(FIELD_COVER_IMAGE, file_path)
        return self

    def upload_file_attachment(self, file_path: str) -> "HomePublicationsAdminPage":
        self.upload_file(FIELD_FILE_ATTACHMENT, file_path)
        return self

    def set_active_status(self, active: bool) -> "HomePublicationsAdminPage":
        self.set_checkbox(FIELD_ACTIVE_STATUS, active)
        return self

    def is_active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    def current_status(self) -> str:
        """HEALED 2026-09-27 (THIRD and FOURTH real, distinct defects this
        same triage session surfaced in `tc_134336`, found only after the
        file-upload fixture fix and the `find_entry_code_by_title()`
        editEntry-code fix above both landed and the test finally reached
        this call): `ObjectAuthoringPage.current_status()`'s own inherited
        check is BOTH case-sensitive (`"(draft)" in text` / `"(approved)" in
        text`, lower case only) AND assumes the project-wide "(approved)"
        wording — CONFIRMED LIVE via a direct Playwright MCP probe against a
        real Publication entry, end to end, that THIS object's own editing
        banner instead renders:
          - Draft: 'Editing "<title>" (Draft). Save as Draft or Submit for
            Review updates this record.' (capitalized "(Draft)", and "Submit
            for Review" — not "Submit for Publishing" — in the banner's own
            prose; see `submit_for_publishing()`'s own HEALED override below
            for the real button text this object needs).
          - Live/published: 'Editing "<title>" (Published). It is published.
            Use Unpublish to edit as draft below...' — this object's own
            real terminal status is literally "Published", not "Approved"
            (also confirmed live: the entries-list row's own Status cell
            reads "PUBLISHED", not "APPROVED"/"Approved"). Mapped to the
            SAME `"Approved"` return value the rest of this project's shared
            `ObjectAuthoringPage`-based test assertions already expect
          (this project's own live-vs-Pending-Review workflow finding — see
            module docstring — is unaffected: TEST_USER's admin session was
            confirmed live this session to move Draft straight to Published
            with no visible intermediate Pending Review stop, once the
            REAL blocker, invalid Page Count, see `FIELD_PAGE_COUNT`, was
            fixed).
        The inherited method therefore silently returned "Unknown" for every
        real Publication entry regardless of its true status, masking the
        other real, now-fixed defects behind this false negative. Overridden
        here (mirroring `row_status_text()`'s own precedent of a per-object
        `.capitalize()` normalization for this exact class of wording
        divergence) rather than widening the shared base class, which 15+
        other objects also compose unmodified."""
        text = self.editing_banner_text().lower()
        if "(approved)" in text or "(published)" in text:
            return "Approved"
        if "(draft)" in text:
            return "Draft"
        return "Unknown"

    def set_page_count(self, value: str) -> "HomePublicationsAdminPage":
        self.fill_number(FIELD_PAGE_COUNT, value)
        return self

    def find_entry_code_by_title(self, title_en: str) -> str:
        """HEALED 2026-09-27 (live incident, first real run of the 31-case
        batch): the inherited `find_entry_code_by_field()` is documented on
        `ObjectAuthoringPage` itself as the EXPENSIVE, O(n)-reopens fallback
        for objects whose own Entry column does NOT render the real field
        value — CONFIRMED LIVE this session that "Publication" is NOT one
        of those objects: a fresh entries-list dump shows the Entry column
        renders the real Title (EN) text verbatim (e.g. a row literally
        reading "QCTEST-134376"), the SAME class of object
        `ObjectAuthoringPage`'s own docstring already lists as safe for
        fast, title-based lookup (service-card/promotional-banner/
        news-article). Using the expensive per-row-reopen fallback here
        was BOTH needlessly slow AND, once this session's own accumulated
        QCTEST/probe rows grew the table, a genuine live TimeoutError on an
        UNRELATED row's own edit-form render (confirmed live: the first
        real batch run failed at `test_publication_title_en_valid_...`
        while `find_entry_code_by_field()` was reopening the pre-existing
        seeded "Qatar Trade Outlook 2026" row, nothing to do with the
        entry this test itself had just created).

        HEALED AGAIN 2026-09-27 (SECOND live incident, same triage session —
        found only once the file-upload fixture bug above was fixed and
        `tc_134336` actually reached this call): this method's PRIOR version
        returned `title_en` itself as "the code" — CONFIRMED LIVE via a
        direct Playwright MCP probe that this is WRONG for "Publication":
        the Entry column's rendered Title text is safe for FINDING/matching
        a row (unchanged finding above), but the real `editEntry` query
        value `open_entry_by_code()` needs is a SEPARATE, real
        `externalReferenceCode`-style UUID (e.g.
        `32949f87-a9e5-d396-e1b3-f59e8cceeeda`), carried only in that row's
        own `Edit` link href — NOT the title text, and NOT the same value as
        the row's own `data-qc-oel-delete` id either (confirmed live these
        are two different identifiers on the very same row). A bare
        `?editEntry=<title text>` navigation was confirmed live to never
        resolve to the real entry (the edit form's own "Cancel and add a
        new entry instead" banner never renders, even given a 30-second
        budget) — this was the SECOND real, distinct root cause behind
        `tc_134336`'s own failure (see this object's module docstring /
        this project's fixture-file fix for the FIRST). Reads the row's own
        Edit link href and extracts its real `editEntry` value instead of
        assuming the title doubles as the code."""
        self.open_entries_list()
        row = self.page.locator(f'{self.ENTRIES_TABLE_ROW}:has-text("{title_en}")')
        if row.count() == 0:
            return ""
        href = row.get_by_role("link", name="Edit").get_attribute("href") or ""
        match = re.search(r"[?&]editEntry=([^&]+)", href)
        return match.group(1) if match else ""

    # ---- ADDED 2026-09-27 (31-case field-validation batch, ADO
    # 134370-134401 — see module docstring's HEALED date-input note and this
    # class's own live-confirmed evidence trail) --------------------------
    def field_checkvalidity(self, field_label: str, role: str = "textbox") -> bool:
        """Native `checkValidity()` of the real form control named
        `field_label` — used by every mandatory-field case below instead of
        assuming a server-side error banner exists. CONFIRMED LIVE this
        session: "Publication Title ", "Publication Title — العربية *",
        "Publication Type " (combobox), the "Cover Image Select File" /
        "File Attachment Select File" hidden textboxes ALL carry a native
        HTML `required` attribute — leaving any one empty blocks BOTH Save
        as Draft AND Submit for Publishing identically via the browser's
        own constraint validation (a single shared `<form>`), with ZERO
        network call — not the "Draft lenient / Publish strict" split this
        project's other objects usually show. Documented here as the real,
        disclosed finding for this object rather than assumed."""
        return self.page.get_by_role(role, name=field_label, exact=True).evaluate("el => el.checkValidity()")

    def field_validation_message(self, field_label: str, role: str = "textbox") -> str:
        return self.page.get_by_role(role, name=field_label, exact=True).evaluate("el => el.validationMessage")

    def upload_field_checkvalidity(self, field_label: str) -> bool:
        """Same as `field_checkvalidity()`, scoped to the hidden filename
        textbox backing a file-upload field (e.g. "Cover Image", "File
        Attachment" — its real accessible name is "<field_label> Select
        File", see ObjectAuthoringPage.upload_file()'s own docstring)."""
        return self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        ).evaluate("el => el.checkValidity()")

    def upload_field_validation_message(self, field_label: str) -> str:
        return self.page.get_by_role(
            "textbox", name=f"{field_label} Select File"
        ).evaluate("el => el.validationMessage")

    def attempt_save_as_draft(self) -> None:
        """Clicks Save as Draft WITHOUT the shared `_wait_for_settle()`
        grace this class's inherited `save_as_draft()` applies — used by
        mandatory-field cases where the click is expected to be silently
        blocked by native constraint validation (no navigation, no network
        call to settle on) rather than committing a real save."""
        self.page.locator(self.SAVE_AS_DRAFT_BUTTON).click()
        self.page.wait_for_timeout(800)

    def attempt_submit_for_publishing(self) -> None:
        self.page.locator(self.SUBMIT_FOR_PUBLISHING_BUTTON).click()
        self.page.wait_for_timeout(800)

    def is_on_create_form(self) -> bool:
        """True if the (still-blank-or-unsaved) create form's own Save as
        Draft button is visible — the real, live signal that a
        Save/Submit click did NOT navigate away (i.e. was blocked, e.g. by
        an unmet native `required` field) rather than committing."""
        return self.page.get_by_role("button", name="Save as Draft").is_visible()

    def attempt_upload_file(self, field_label: str, file_path: str) -> str:
        """Opens `field_label`'s own item-selector picker and selects
        `file_path`, WITHOUT waiting for or clicking "Add" — unlike
        `ObjectAuthoringPage.upload_file()`, which assumes a valid,
        acceptable file and would otherwise time out racing a real
        client-side rejection. Returns the picker's own real, live
        rejection/error text (e.g. Cover Image's CONFIRMED-LIVE "Please
        enter a file with a valid extension (.jpg,.jpeg,.png)." message) —
        or "" if the picker instead shows a real, enabled "Add" button
        (i.e. this file was NOT rejected at the picker stage; see
        `upload_cover_image()`/`upload_file_attachment()` for the
        happy-path flow that completes that case)."""
        hidden_textbox = self.page.get_by_role("textbox", name=f"{field_label} Select File")
        select_file_button = hidden_textbox.locator("xpath=..").get_by_role("button", name="Select File")
        select_file_button.click()
        frame = self.page.frame_locator(self.UPLOAD_MODAL_IFRAME)
        frame.locator('input[type="file"]').set_input_files(file_path)
        self.page.wait_for_timeout(4000)
        add_button = frame.get_by_role("button", name=self.UPLOAD_MODAL_ADD_BUTTON_TEXT)
        if add_button.count() > 0:
            return ""
        try:
            return frame.locator("body").inner_text(timeout=5000)
        except Exception:  # noqa: BLE001 — best-effort error-text read
            return ""

    def close_upload_modal(self) -> None:
        """Best-effort close of a still-open item-selector modal (e.g. after
        `attempt_upload_file()` confirms a rejection) so the form is left
        clean for the rest of the test — never raises."""
        try:
            self.page.keyboard.press("Escape")
            self.page.wait_for_timeout(500)
        except Exception:  # noqa: BLE001
            pass

    # ---- ADDED 2026-09-27 (Section Tag/Heading investigation batch,
    # tc_134344-134360 — see module docstring's full evidence trail) --------
    def field_exists_on_entry_form(self, field_label: str) -> bool:
        """True if a form control (textbox/combobox/checkbox/spinbutton)
        with this EXACT accessible name is present anywhere on the
        currently-open Publication create/edit form. Used to give each of
        the 17 Section Tag/Heading cases below its own real, live,
        per-test confirmation that the case's own named field does not
        exist on this object's real, reachable field set — never asserted
        from the module docstring's investigation alone without a live
        per-test check of its own."""
        for role in ("textbox", "combobox", "checkbox", "spinbutton"):
            if self.page.get_by_role(role, name=field_label, exact=True).count() > 0:
                return True
        return False

    def object_authoring_has_link(self, link_name: str) -> bool:
        """True if the Object Authoring Forms index
        (`/web/qatar-chamber/object-authoring`) has a link whose accessible
        name is EXACTLY `link_name` — used to independently confirm, per
        test, that no dedicated "Publications Section"/"Knowledge Hub"
        Object Authoring entry exists (see module docstring's Section
        Tag/Heading investigation, finding #1)."""
        self._ensure_admin_session()
        self.open(control_panel_url("/web/qatar-chamber/object-authoring"))
        return self.page.get_by_role("link", name=link_name, exact=True).count() > 0

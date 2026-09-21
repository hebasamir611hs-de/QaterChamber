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
    `get_by_role(...)`-based targeting impossible for this one field. The
    real, stable-across-page-loads CSS locator used instead:
    `input[id$="-date-input"]` (confirmed live count=1 on this form; the
    UUID PREFIX of the id changes every page load per this project's own
    already-documented Page Builder fragment-id convention, but the FIXED
    SUFFIX this selector matches on does not) — fillable directly with an
    ISO `YYYY-MM-DD` string via Playwright's native date-input `.fill()`
    support (confirmed live).
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
"""

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
PUBLICATION_DATE_INPUT_CSS = 'input[id$="-date-input"]'


class HomePublicationsAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) for the "Publication" object. Constructed with
    just `page` (slug fixed to "publication"). See module docstring for the
    confirmed-unreachable field map and the separate, already-established
    workflow-scope finding (no Reject/Pending Review anywhere on this
    surface)."""

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

    def set_publication_date(self, iso_date: str) -> "HomePublicationsAdminPage":
        """`iso_date` in `YYYY-MM-DD` — native `<input type="date">`.fill()
        support, confirmed live (see module docstring's native-date-input
        note for why role-based targeting is impossible for this field)."""
        self.page.locator(PUBLICATION_DATE_INPUT_CSS).fill(iso_date)
        return self

    def upload_cover_image(self, file_path: str) -> "HomePublicationsAdminPage":
        self.upload_file(FIELD_COVER_IMAGE, file_path)
        return self

    def upload_file_attachment(self, file_path: str) -> "HomePublicationsAdminPage":
        self.upload_file(FIELD_FILE_ATTACHMENT, file_path)
        return self

    def set_active_status(self, active: bool) -> "HomePublicationsAdminPage":
        self.set_checkbox(FIELD_ACTIVE_STATUS, active)
        return self

"""
cms/pages/home_social_icons/home_social_icons_admin_page.py —
HomeSocialIconsAdminPage.

Control_Panel Page Object for PBI 129373 (QC-HOME-004B — Social Media
Icons), composing the generic Object Authoring state machine
(`ObjectAuthoringPage`, see cms/pages/components/object_authoring_page.py)
with the "Social Media Icon" object's own field map — per
.claude/context/active/standards.md's "Object Authoring Is the Only Path
for Content Operations — Not Content & Data" rule. `Content & Data` is not
used anywhere in this class.

CONFIRMED LIVE 2026-09-07 (headless Chromium against qcdev, 1920x1080
viewport, a fresh Site Content Editor session captured via a throwaway
CmsLoginPage-flow script — `cms_role_credentials("Site Content Editor")`,
mirrors the pattern already documented in org_structure_admin_page.py /
home_community_partners_admin_page.py; `python tools/extract_locators.py`
plus direct Playwright role/DOM probes for the parts the extractor's
generic candidate list doesn't disambiguate, e.g. the combobox's real
option list and the object's read-back field values):

SLUG / SURFACE
  - The Object Authoring index (`/web/qatar-chamber/object-authoring`)
    lists this object as "Social Media Icon" (singular) — confirmed href
    `/web/qatar-chamber/manage-social-media-icon`. SLUG = "social-media-icon"
    below. (Not "social-media-icons" — verified via the index link's own
    href, not guessed.)
  - `manage-social-media-icon` renders the SAME generic Save as Draft /
    Submit for Publishing Object Authoring state machine every other
    object on this project uses (page title "Manage: Social Media Icon").

ONE OBJECT BACKS BOTH THE FOOTER (PBI 133231 / QC-GBL-004) AND THE HOME
PAGE WIDGET (PBI 129373 / QC-HOME-004B) — CONFIRMED LIVE, resolving
standards.md's own open "unless confirmed otherwise" note on this exact
question. The SAME 8 "Social Media Icon" entries render in TWO separate
public sections simultaneously (confirmed live, anonymous/logged-out
session, identical hrefs in both):
  - Footer: `div.qc-footer-social-wrap ul.qc-footer-social li a.qc-social-link`
    — keyed by this object's "Display Order" / "Active Status" fields.
  - Home page: `div.qc-home-social ul.qc-social-list li a.qc-social-link`
    — keyed by "Show on Home" / "Home Display Order", layered on the SAME
    entry (NOT a separate object/record). See
    web/pages/home_social_icons/home_social_icons_page.py for the public
    counterpart.

FIELD SET (role-probed, `get_by_role(..., exact=True)`, every one below
resolved to exactly 1 match on the create-new form):
  - "Platform" — a `role="combobox"` select-from-list (NOT free text).
    Confirmed live by opening its dropdown: a FIXED, CLOSED enum of
    exactly Facebook / X / LinkedIn / Instagram / YouTube / WhatsApp /
    Telegram / Snapchat — no "add a new option" affordance anywhere on
    this form. Opened via the SAME unscoped
    `get_by_role("button", name="Open Options Menu")` pattern
    `ObjectAuthoringPage.select_combobox_option()` already uses —
    confirmed live SAFE here (this form has exactly ONE combobox, unlike
    Business Event's 4-combobox form, which needed per-field
    `aria-controls` scoping instead).
  - "Social Icon Image" (file upload, footer icon asset).
  - "Icon Alt Text" (textbox, EN) / "Icon Alt Text — العربية" (AR) — two
    independently addressable textboxes, no locale-toggle click needed,
    mirrors Community Partner's confirmed-live bilingual-pair pattern.
  - "Social Redirect URL" (textbox, EN) / "Social Redirect URL — العربية"
    (AR) — the platform link URL. Renders directly as the public
    `a.qc-social-link`'s `href` in BOTH sections (confirmed live).
  - "Open in New Tab" (checkbox).
  - "Display Order" (spinbutton) — RE-CONFIRMED LIVE 2026-09-07 (see
    web/pages/home_social_icons/home_social_icons_page.py's module
    docstring, "ROOT-CAUSE INVESTIGATION" — Round 2's disambiguating live
    edit): the FOOTER section's own order field. Has NO effect on the Home
    section's own order (a same-day Round 1 experiment briefly concluded
    otherwise from a tied/ambiguous data pair — corrected the same session
    by a cleaner, non-tied live edit; see that docstring for the full
    evidence trail of both rounds).
  - "Active Status" (checkbox) — the FOOTER section's own active flag.
  - "Show on Home" (checkbox) — HOME-page-specific visibility toggle,
    CONFIRMED UNCHECKED by default on a fresh create-new form (a new entry
    does NOT appear in the Home page section unless this is explicitly
    set True — the object schema, not any test bug). This field's own
    independence from "Active Status" IS confirmed live and correct (see
    the Control_Panel test module's tc_131161).
  - "Home Icon Image" (file upload) — independent of "Social Icon Image".
  - "Home Display Order" (spinbutton) — RE-CONFIRMED LIVE 2026-09-07 (same
    Round 2 evidence): the HOME section's own order field, independent of
    "Display Order" — this IS the field that actually drives the Home
    page's rendered order.

CONFIRMED-LIVE SEEDED-DATA FACTS (all 8 platform rows,
`QC-SMI-<platform-slug>` externalReferenceCode, e.g. `QC-SMI-youtube`, all
workflow Status = Approved):
  - CORRECTED 2026-09-07 (live re-investigation, triggered by a
    QA-Manager-vs-automation discrepancy report on TC 131159/131160): the
    claim below that "every seeded row carries Display Order = 500" was
    WRONG — it was read off only the YouTube row (which genuinely is 500)
    and over-generalized without checking the other 7. Re-confirmed live,
    per-row, via each entry's own JAX-RS record this session: **Facebook =
    100, X = 200, LinkedIn = 300, Instagram = 400, YouTube = 500, WhatsApp
    = 600, Telegram = 700, Snapchat = 800** — BOTH `Display Order` AND
    `Home Display Order` carry this same per-row value on every one of the
    8 seeded rows (a coincidence of how the seed data was authored — both
    fields set to the same per-platform value — NOT evidence the two
    fields are linked; see the sibling public Page Object's module
    docstring, Round 2, for the live edit that proves they are
    independent). The public Home-page rendering order (Facebook.
    .Snapchat) is fully explained by ascending `Home Display Order` (which
    happens to equal `Display Order` for these 8 untouched seed rows) —
    the Footer's own rendering order is separately, explicitly sorted by
    `Display Order` server-side.
  - EVERY enum Platform value already has exactly one live entry — there
    is NO unused platform slot on this environment. A test that creates
    "a new" icon for an already-used Platform value (e.g. YouTube, per ADO
    131159's literal test data) therefore creates a genuine SECOND entry
    for that same enum value — confirmed live NOT blocked by any
    client-side validation this session. This is a real, confirmed-live
    data/product fact this PBI's cases are scripted against as-is (per
    automation-standards.md's "no reinterpreting the case" rule) — see the
    Control_Panel test module's own docstring for how each TC's
    assertions identify "its own" entry despite the Platform-label
    collision (by its own unique Social Redirect URL, never by Platform
    label or row position).

ENTRY LOOKUP: this object's Entry column renders the real
externalReferenceCode text (`QC-SMI-<platform>` for the 8 seeded rows) —
never the Platform field value — so this class relies on
ObjectAuthoringPage's CODE-based methods (`open_entry_by_code()`,
`row_status_text_by_code()`, `row_visible_by_code()`,
`find_entry_code_by_field()`, `delete_entry_by_code()`), never the
TITLE-based ones (`open_entry_by_edit_link()`, `row_visible()`), which
would silently fail to match anything on this object's own list rows.
"""

from cms.pages.components.object_authoring_page import ObjectAuthoringPage
from config.settings import control_panel_url

SLUG = "social-media-icon"

# CONFIRMED LIVE 2026-09-07 (TC 131163 investigation): logging in with the
# freshly-added-to-.env "Site Content Author" and "Content Contributor"
# role accounts (both added same-day for this PBI's workflow case) lands
# on Liferay's own forced first-login "you must set a new password before
# continuing" interstitial (`/c/portal/update_password`) instead of the
# normal LOGIN_SUCCESS_INDICATOR — reproduced for BOTH candidate roles.
# Re-submitting the CURRENT password as the "new" one on that form is
# silently rejected (the page does not navigate away) — a genuinely new,
# different password is required, which is a live-credential mutation this
# automation is not authorized to perform unilaterally (attempting it was
# itself blocked by the runtime's own permission system when tried live
# this session). "Site Content Editor" (already activated, used by TC
# 131159-131161) shows NEITHER interstitial. See the Control_Panel test
# module's own TC 131163 docstring for the full disclosed finding.
FORCED_PASSWORD_RESET_PATH = "/c/portal/update_password"
TERMS_OF_USE_AGREE_BUTTON_NAME = "I Agree"

# ADDED 2026-09-13 (TC 131167, PBI 129373 RBAC/permission batch) — a THIRD,
# separate live blocker state, distinct from FORCED_PASSWORD_RESET_PATH
# above: re-confirmed LIVE this same session (Content Contributor,
# Test3@xyz.com) that Liferay now rejects the credential outright with its
# own "Authentication failed due to incorrect credentials or account
# lockout..." banner, staying on the login page (no redirect to
# update_password at all). This is the SAME failure mode
# HomePublicationsAdminPage.login_as_role() independently found for ALL
# THREE named roles on 2026-09-12 — reproduced again here live 2026-09-13
# for Content Contributor specifically. Substring-matched (not exact),
# mirroring HomePublicationsAdminPage's own AUTH_FAILED_BANNER_TEXT constant
# (same literal banner text, same detection rationale).
AUTH_FAILED_BANNER_TEXT = "Authentication failed"

# Same re-login-if-needed entry point every sibling admin Page Object in
# this project uses before touching an Object Authoring `manage-<slug>`
# URL directly — see HomeBusinessEventsAdminPage._ensure_logged_in()'s own
# confirmed-live note: a stale/absent session hitting `manage-<slug>`
# directly renders the public site's generic placeholder with no login
# redirect for this class to react to; routing through `/en/home` first
# (which DOES check for a real signed-in Product Menu / Content & Data
# link and re-logs-in if absent) avoids that gap.
ADMIN_HOME_EN_URL_PATH = "/en/home"
PRODUCT_MENU_TOGGLE = '[data-qa-id="productMenu"]'
CONTENT_DATA_MENU_ITEM = '[role="menuitem"]:text-is("Content & Data")'
# CONFIRMED LIVE 2026-09-07: a "Site Content Editor" role session (this
# PBI's 3 cases all require this specific named role, not the super-admin
# TEST_USER other sibling admin Page Objects default to) shows NEITHER
# PRODUCT_MENU_TOGGLE NOR CONTENT_DATA_MENU_ITEM on /en/home (both
# confirmed live count=0 right after a real, successful login) — the
# sibling classes' own `_ensure_logged_in()` check is a false negative for
# this role and was observed live to trigger a bogus re-login attempt
# against an already-authenticated session (which redirects instead of
# showing the login form — see CmsLoginPage's own module docstring — and
# hangs for the full 30s timeout typing into a field that never renders).
# The Control Menu nav (CmsLoginPage.LOGIN_SUCCESS_INDICATOR's own primary
# signal) IS confirmed present for this role and is checked here instead/
# in addition.
CONTROL_MENU_NAV = 'nav[aria-label="Control Menu"]'

FIELD_PLATFORM = "Platform"
FIELD_SOCIAL_ICON_IMAGE = "Social Icon Image"
FIELD_ICON_ALT_TEXT_EN = "Icon Alt Text"
FIELD_ICON_ALT_TEXT_AR = "Icon Alt Text — العربية"
FIELD_SOCIAL_REDIRECT_URL_EN = "Social Redirect URL"
FIELD_SOCIAL_REDIRECT_URL_AR = "Social Redirect URL — العربية"
FIELD_OPEN_IN_NEW_TAB = "Open in New Tab"
FIELD_DISPLAY_ORDER = "Display Order"
FIELD_ACTIVE_STATUS = "Active Status"
FIELD_SHOW_ON_HOME = "Show on Home"
FIELD_HOME_ICON_IMAGE = "Home Icon Image"
FIELD_HOME_DISPLAY_ORDER = "Home Display Order"

# Confirmed-live CLOSED enum — see module docstring. No other values exist.
PLATFORM_FACEBOOK = "Facebook"
PLATFORM_X = "X"
PLATFORM_LINKEDIN = "LinkedIn"
PLATFORM_INSTAGRAM = "Instagram"
PLATFORM_YOUTUBE = "YouTube"
PLATFORM_WHATSAPP = "WhatsApp"
PLATFORM_TELEGRAM = "Telegram"
PLATFORM_SNAPCHAT = "Snapchat"


class HomeSocialIconsAdminPage(ObjectAuthoringPage):
    """Composes the generic Object Authoring state machine
    (`ObjectAuthoringPage`) with the Social Media Icon object's own field
    map. Constructed with just `page` (slug fixed to "social-media-icon")."""

    def __init__(self, page):
        super().__init__(page, SLUG)

    # ---- Navigation -------------------------------------------------------
    def _ensure_logged_in(self, role: str = "Site Content Editor") -> None:
        """Re-login-if-needed via `/en/home`'s real session check — see
        module-level constants' docstring for why CONTROL_MENU_NAV is
        checked (not just CONTENT_DATA_MENU_ITEM/PRODUCT_MENU_TOGGLE, both
        confirmed live ABSENT for a genuinely-logged-in "Site Content
        Editor" session) before any direct `manage-social-media-icon`
        navigation. Re-login (only if genuinely needed) uses `role` — added
        2026-09-07 (TC 131163) as an explicit parameter, defaulting to
        "Site Content Editor" so every EXISTING caller (TC 131159-131161,
        none of which pass it) is unaffected: previously this was
        hardcoded to "Site Content Editor" unconditionally, which would
        have silently swapped a TC 131163 Author/Contributor session back
        to Editor on any mid-test re-login race — never the super-admin
        `settings.test_user` fallback other sibling admin Page Objects
        use, which would silently swap the acting role a case explicitly
        named."""
        from cms.pages.control_panel.login_page import CmsLoginPage
        from config.settings import cms_role_credentials

        login = CmsLoginPage(self.page)
        self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))
        if not (
            self.is_visible(CONTROL_MENU_NAV)
            or self.is_visible(CONTENT_DATA_MENU_ITEM)
            or self.is_visible(PRODUCT_MENU_TOGGLE)
        ):
            email, password = cms_role_credentials(role)
            login.open_login().login(email, password)
            self.open(control_panel_url(ADMIN_HOME_EN_URL_PATH))

    def open_new_icon_form(self, role: str = "Site Content Editor") -> "HomeSocialIconsAdminPage":
        self._ensure_logged_in(role)
        self.open_new_entry_form()
        return self

    def open_icons_list(self, role: str = "Site Content Editor") -> "HomeSocialIconsAdminPage":
        self._ensure_logged_in(role)
        self.open_entries_list()
        return self

    def open_icon_by_entry_code(self, entry_code: str, role: str = "Site Content Editor") -> "HomeSocialIconsAdminPage":
        self._ensure_logged_in(role)
        self.open_entry_by_code(entry_code)
        return self

    def login_as_role(self, role: str) -> str:
        """Drives a REAL login (never a cached storageState) as `role` via
        CmsLoginPage's own selectors, added for TC 131163 (the only one of
        this batch whose own Step 1 requires a non-Editor role). Handles
        the one-time Terms-of-Use interstitial some accounts show on first
        login, and DETECTS (without attempting to resolve — see module
        docstring) Liferay's own forced first-login password-reset
        interstitial. Returns "ok" once the normal LOGIN_SUCCESS_INDICATOR
        is visible, "forced_password_reset" if the flow instead lands on
        `FORCED_PASSWORD_RESET_PATH`, or "auth_failed" if Liferay rejects
        the credential outright with `AUTH_FAILED_BANNER_TEXT` (added
        2026-09-13 for TC 131167 — see that constant's own docstring) —
        callers must treat any of the non-"ok" results as an unmet
        precondition (skip), never attempt to fill the reset form or
        resolve a rejected credential themselves."""
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
        except Exception:  # noqa: BLE001 — best-effort read, fall through to the checks below
            body_text = ""
        if AUTH_FAILED_BANNER_TEXT in body_text:
            return "auth_failed"
        try:
            self.page.wait_for_url(f"**{FORCED_PASSWORD_RESET_PATH}**", timeout=6000)
            return "forced_password_reset"
        except Exception:  # noqa: BLE001 — did not land on the reset page, proceed to the normal check
            pass
        self.page.locator(CmsLoginPage.LOGIN_SUCCESS_INDICATOR).first.wait_for(state="visible", timeout=10000)
        return "ok"

    # ---- Field actions (thin, named wrappers over the base class's
    # generic role-based helpers — kept here so the test module reads at
    # the feature's own vocabulary rather than repeating field-label
    # strings) ---------------------------------------------------------------
    def select_platform(self, platform: str) -> "HomeSocialIconsAdminPage":
        self.select_combobox_option(FIELD_PLATFORM, platform)
        return self

    def upload_social_icon_image(self, file_path: str) -> "HomeSocialIconsAdminPage":
        self.upload_file(FIELD_SOCIAL_ICON_IMAGE, file_path)
        return self

    def upload_home_icon_image(self, file_path: str) -> "HomeSocialIconsAdminPage":
        self.upload_file(FIELD_HOME_ICON_IMAGE, file_path)
        return self

    def fill_icon_alt_text(self, value_en: str, value_ar: str = None) -> "HomeSocialIconsAdminPage":
        self.fill_text(FIELD_ICON_ALT_TEXT_EN, value_en)
        if value_ar is not None:
            self.fill_text(FIELD_ICON_ALT_TEXT_AR, value_ar)
        return self

    def fill_social_redirect_url(self, value_en: str, value_ar: str = None) -> "HomeSocialIconsAdminPage":
        self.fill_text(FIELD_SOCIAL_REDIRECT_URL_EN, value_en)
        if value_ar is not None:
            self.fill_text(FIELD_SOCIAL_REDIRECT_URL_AR, value_ar)
        return self

    def set_open_in_new_tab(self, checked: bool) -> "HomeSocialIconsAdminPage":
        self.set_checkbox(FIELD_OPEN_IN_NEW_TAB, checked)
        return self

    def set_display_order(self, value) -> "HomeSocialIconsAdminPage":
        self.fill_number(FIELD_DISPLAY_ORDER, str(value))
        return self

    def set_active_status(self, checked: bool) -> "HomeSocialIconsAdminPage":
        self.set_checkbox(FIELD_ACTIVE_STATUS, checked)
        return self

    def set_show_on_home(self, checked: bool) -> "HomeSocialIconsAdminPage":
        self.set_checkbox(FIELD_SHOW_ON_HOME, checked)
        return self

    def set_home_display_order(self, value) -> "HomeSocialIconsAdminPage":
        self.fill_number(FIELD_HOME_DISPLAY_ORDER, str(value))
        return self

    def social_redirect_url_value(self) -> str:
        return self.field_value(FIELD_SOCIAL_REDIRECT_URL_EN)

    def display_order_value(self) -> str:
        return self.page.get_by_role("spinbutton", name=FIELD_DISPLAY_ORDER, exact=True).input_value()

    def home_display_order_value(self) -> str:
        """Read-back for "Home Display Order" — the field CONFIRMED LIVE
        2026-09-07 to be the one that actually drives the public Home
        page's own rendered order (see module docstring's field-map note
        and the sibling public Page Object's "ROOT-CAUSE INVESTIGATION").
        Used by the Control_Panel test module to capture an entry's real,
        current Home-page rank BEFORE a case that only touches "Display
        Order" mutates it, so the test can assert the correct (unchanged)
        expected position instead of a value the case's own steps never
        set."""
        return self.page.get_by_role("spinbutton", name=FIELD_HOME_DISPLAY_ORDER, exact=True).input_value()

    def active_status_checked(self) -> bool:
        return self.page.get_by_role("checkbox", name=FIELD_ACTIVE_STATUS, exact=True).is_checked()

    # ---- Lifecycle ----------------------------------------------------------
    def publish(self) -> "HomeSocialIconsAdminPage":
        self.submit_for_publishing()
        return self

    # ---- Entry-code resolution (never positional — see
    # ObjectAuthoringPage.find_entry_code_by_field()'s own incident note and
    # standards.md's "Destructive Operations Against qcdev" rule) ------------
    def find_entry_code_by_redirect_url(self, redirect_url: str) -> str:
        """Resolves the just-created/just-edited entry's own Entry-column
        code by reading back its (unique, test-owned) Social Redirect URL —
        the identifying value every TC in this batch gives its own test
        entry, since Platform alone is NOT unique on this object (see
        module docstring)."""
        return self.find_entry_code_by_field(FIELD_SOCIAL_REDIRECT_URL_EN, redirect_url)

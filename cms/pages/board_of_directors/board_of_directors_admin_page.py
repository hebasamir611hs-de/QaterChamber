"""
web/pages/board_of_directors/board_of_directors_admin_page.py —
BoardOfDirectorsAdminPage.

Control_Panel Page Object for PBI 129398 (QC-ABOUT-006 — Board of Directors &
General Director)'s PAGE-LEVEL surface — the Liferay Page Design / Fragment
Configuration panel, NOT a Content & Data admin list (that pattern belongs to
web/pages/org_structure/org_structure_admin_page.py and does not apply here).

REAL, LIVE-VERIFIED FACTS (this session, 2026-08-25, headless Chromium
against qcdev, authenticated via TEST_USER, viewport 1920x1080):

Navigation path confirmed live:
  1. Open the public page directly: WEB_BASE_URL +
     "/web/qatar-chamber/about-us/board-of-directors" (no Page Tree UI
     traversal needed to reach it — Site Builder > Page Tree > About Us >
     "Board of Directors & General Manager" resolves to this same URL).
  2. The rendered page carries a control-menu "Edit" link
     (`a[href*="p_l_mode=edit"]`) whose href is a per-session, per-draft
     Liferay Content Page Editor URL (embeds a rotating `p_auth` token and
     `segmentsExperienceId`) — like OrgStructureAdminPage's LIST_URL lesson,
     this href must be READ off the live DOM each run, never hardcoded or
     cached across sessions.
  3. Opening that href lands in the Page Design / Content Page Editor
     (`Experience: Default` dropdown, device-preview toggles, `Page Design`
     dropdown, `Discard Draft` / `Publish` buttons in the top-right toolbar).
  4. The ENTIRE listing page (hero, Chairman, Vice Chairmen, Board Members,
     General Manager sections) is rendered by a SINGLE fragment/widget
     named "QC Board Of Directors And General Manager" — confirmed by
     clicking element text in three different sections (the Chairman
     heading text and the page's H1 hero title) and observing the SAME
     fragment name in the right-side panel header both times. This is NOT
     four independently-configurable sections; there is one config surface
     for the whole page.
  5. Clicking that fragment opens a right-side panel with three tabs
     (General / Styles / Advanced). The **General** tab's **DATA SOURCE**
     group contains EXACTLY these fields, confirmed by scrolling the panel
     to its bottom and reading its full rendered text — no others exist
     anywhere in General, Styles, or Advanced:
       - "Members endpoint" (text input, pre-filled "/o/qc-board/members",
         helper text "Anonymous JAX-RS endpoint that returns the active
         Board Members.")
       - "Member profile page URL" (text input, helper text "Base URL of
         the member profile page; the member ERC is appended as ?erc=.")
       - "Home breadcrumb URL" (text input, pre-filled "/web/qatar-chamber")
       - "Hero banner image URL (optional)" — a PLAIN TEXT/URL input, NOT a
         file-upload control (no "Select File" button, no file picker, no
         accept/size constraint visible anywhere in the DOM). Label itself
         states "(optional)". Helper text: "Optional texture/photo behind
         the maroon hero overlay."
       - "Short bio line limit" — a numeric dropdown/select (options 2/3/4,
         default 3), helper text "Number of lines before the short bio
         truncates with an ellipsis."
     The "FRAME" group below DATA SOURCE (Width/Height/Min/Max, Overflow,
     Hide Fragment) is generic Liferay fragment-frame config, unrelated to
     this feature's content.
  6. There is NO per-field "Save" button anywhere in this panel. Field
     edits apply live to the page's draft; the only persistence actions are
     the page-level "Discard Draft" and "Publish" buttons in the top
     toolbar. This is a draft-then-publish surface, not a form-with-Save.
  7. NO Page Title (EN/AR) field, NO per-section "Eyebrow Label" (EN/AR)
     field (Chairman/Vice Chairmen/Board Members/General Manager each have
     a hardcoded, non-configurable eyebrow/heading in the rendered fragment
     — none of the four appeared as an editable field anywhere in General,
     Styles, or Advanced), and NO "Board Members Count/Counter" field of any
     kind exist on this surface — confirmed by the full-panel text dump
     above, not by a partial/short glance.

  These facts are what drove the batch classification in the test module's
  docstring (12 of 15 sourced cases dropped — see there for the full
  per-case reasoning). Re-verify this docstring if the fragment's
  DATA SOURCE config is later extended.
"""

from core.web.base_page import BasePage
from config.settings import settings, web_url


class BoardOfDirectorsAdminPage(BasePage):
    PUBLIC_LISTING_PATH = "/web/qatar-chamber/about-us/board-of-directors"

    EDIT_LINK = 'a[href*="p_l_mode=edit"]'
    FRAGMENT_ANCHOR_TEXT = "Board of Directors & General Manager"  # hero H1, part of the one page fragment

    GENERAL_TAB = 'text="General"'
    STYLES_TAB = 'text="Styles"'
    ADVANCED_TAB = 'text="Advanced"'

    MEMBERS_ENDPOINT_LABEL = "Members endpoint"
    MEMBER_PROFILE_PAGE_URL_LABEL = "Member profile page URL"
    HOME_BREADCRUMB_URL_LABEL = "Home breadcrumb URL"
    HERO_BANNER_IMAGE_URL_LABEL = "Hero banner image URL (optional)"
    SHORT_BIO_LINE_LIMIT_LABEL = "Short bio line limit"

    DISCARD_DRAFT_BUTTON = 'button:has-text("Discard Draft")'
    PUBLISH_BUTTON = 'button:has-text("Publish")'

    def _field_after_label(self, label: str) -> str:
        """Text-anchored locator: the input/select nearest AFTER the exact
        visible label text — same technique as OrgStructureAdminPage, needed
        here because the fragment config panel's fields carry no stable
        id/name/data-testid either (confirmed same lack of hooks live)."""
        return f'xpath=//*[contains(normalize-space(text()), "{label}")]/following::input[1] | //*[contains(normalize-space(text()), "{label}")]/following::select[1]'

    # ---- Navigation -----------------------------------------------------
    def open_page_design_editor(self) -> "BoardOfDirectorsAdminPage":
        """Open the public listing page authenticated, then follow its live
        "Edit" link into the Page Design / Content Page Editor. The edit
        href is read fresh off the DOM every call (see module docstring —
        it embeds a rotating auth token, never safe to cache).

        The cached .auth/state.json storageState is not a reliable signal
        here — same lesson as OrgStructureAdminPage.open_departments_list():
        an anonymous/stale session still renders the PUBLIC page fine, just
        without the "Edit" link, so BasePage's login-form guard never fires
        (there's no login form to detect, just a missing admin affordance).
        Force a real, fresh login whenever the Edit link isn't present.
        """
        from cms.pages.control_panel.login_page import CmsLoginPage

        login = CmsLoginPage(self.page)
        self.open(web_url(self.PUBLIC_LISTING_PATH))
        if not self.is_visible(self.EDIT_LINK):
            login.open_login().login(settings.test_user, settings.test_password)
            self.open(web_url(self.PUBLIC_LISTING_PATH))

        self.wait_for(self.EDIT_LINK)
        href = self.page.locator(self.EDIT_LINK).first.get_attribute("href")
        self.open(href)
        self.wait_for(f'text="{self.FRAGMENT_ANCHOR_TEXT}"')
        return self

    def open_data_source_panel(self) -> "BoardOfDirectorsAdminPage":
        """Click the page's single content fragment to open its
        General/Styles/Advanced config panel (defaults to General, which
        holds the DATA SOURCE group)."""
        self.click(f'text="{self.FRAGMENT_ANCHOR_TEXT}"')
        self.wait_for(self.GENERAL_TAB)
        return self

    # ---- State queries ----------------------------------------------------
    def data_source_panel_text(self) -> str:
        """Full rendered text of the config panel (General tab), used to
        assert on the presence/absence of a field by its label — the panel
        has no stable container id, so this reads the same ancestor block
        the discovery pass anchored on (the block containing the tab bar)."""
        return self.page.evaluate(
            """() => {
                const cands = Array.from(document.querySelectorAll('*'))
                    .filter(el => el.children.length <= 2 && el.textContent.trim() === 'Advanced');
                if (!cands.length) return '';
                let big = cands[0];
                for (let i = 0; i < 6 && big.parentElement; i++) big = big.parentElement;
                return big.innerText;
            }"""
        )

    def has_field_labeled(self, label: str) -> bool:
        return label in self.data_source_panel_text()

    def field_value(self, label: str) -> str:
        return self.page.locator(self._field_after_label(label)).input_value()

    def is_publish_available(self) -> bool:
        return self.is_visible(self.PUBLISH_BUTTON)

    def is_discard_draft_available(self) -> bool:
        return self.is_visible(self.DISCARD_DRAFT_BUTTON)

    # ---- Actions ------------------------------------------------------------
    def set_field(self, label: str, value: str) -> "BoardOfDirectorsAdminPage":
        self.type(self._field_after_label(label), value)
        return self

    def discard_draft(self) -> "BoardOfDirectorsAdminPage":
        self.click(self.DISCARD_DRAFT_BUTTON)
        return self

    def publish(self) -> "BoardOfDirectorsAdminPage":
        self.click(self.PUBLISH_BUTTON)
        return self

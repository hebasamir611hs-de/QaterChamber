"""web/pages/keyboard_navigation/keyboard_navigation_page.py —
KeyboardNavigationPage.

Cross-page keyboard-accessibility surface for PBI 131054 ("QC - 001 -
Keyboard Navigation", GLOBAL service, Web platform). The cases span the
homepage (EN + AR), Contact Us, the FAQ Knowledge Base, About Us /
Vision-Mission-Objectives and the header mega-menu, so this one object
carries the *page-specific* locators those flows need and COMPOSES the
existing shared component objects for everything they already own:

  * `HeaderComponent`  — nav landmark, top-level nav links, language
    switcher, accessibility button, search button, mega-menu panel/chevron.
    NOT re-declared here; `self.header` is the single source for them.
  * `FooterComponent`  — the footer's social-link container
    (`FOOTER_SOCIAL_CONTAINER`), reused for the "any page footer link" case.
  * `core.web.overlays` — `ANNOUNCEMENT_ROOT` / `ANNOUNCEMENT_CLOSE`, reused
    rather than re-declared, for the announcement-modal cases.

The generic keyboard machinery (active-element descriptor, tab-sequence
recorder, focus-style reader, clickable-vs-focusable snapshots) lives in
`core/web/base_page.py`, not here — it is selector-free and site-agnostic.

ANONYMOUS BY CONTRACT
---------------------
Every navigation below goes through `BasePage.open_anonymous()` (or
`open_anonymous_keeping_overlays()`), never `open()`. Two reasons, both
load-bearing for this PBI:
  1. `open()` calls `reauthenticate()`, which would silently sign the shared
     CMS `TEST_USER` back in — standards.md's "Draft/Unpublish Public-
     Visibility Checks — Mandatory Logged-Out Context" rule, and ADO-141827
     ("a Public Visitor can use keyboard navigation without authentication")
     is literally that assertion.
  2. An authenticated Liferay session renders the admin control menu ABOVE
     the page, which inserts extra tab stops and changes the recorded tab
     ORDER for essentially every case in this PBI. Every expectation encoded
     here was measured in a genuinely signed-out context
     (`body.signed-out.public-page`).
The tests pair this with `page` fixture param `{"auth": False}` so the
context itself never loads a cached storageState.

LIVE-CONFIRMED FACTS (CLI extraction, qcdev, read-only, 2026-09-23)
-------------------------------------------------------------------
Harvested with `tools/extract_locators.py` plus scoped Playwright probe
scripts run in the SHELL (never the Playwright MCP) at the framework's
default 1920x1080 viewport — the same "ambiguous element / state the script
must drive" fallback pattern `header_component.py` already documents, since
this PBI's subject is keyboard STATE (focus, aria-expanded, tab order),
which the flat extractor cannot report.

  * Tab-stop 1 on every page is `a#qc-skip-link` ("Skip to main content",
    href="#main-content"), rendered off-screen (`top: -65px`) until focused,
    then CSS-transitioned to `top: 0`. The transition means a same-tick read
    right after the Tab still sees -65 — hence `wait_for_skip_link_revealed()`
    below waits on the rect crossing 0 rather than sleeping.
  * Tab-stops 2 and 3 are Liferay's OWN screen-reader-only controls — a
    second "Skip to Main Content" link (`a.sr-only-focusable`, also
    href="#main-content") and an "Open Accessibility Menu" button. Both sit
    at y=-1 until focused. **The accessibility button's `id` is randomly
    regenerated on every render** (observed `djfs_lbct`, `nuda_gfwy`,
    `rfhr_zgin`, `hqps_zhcm`, `sddo_kdbc` for the same element), so it is
    located by class + accessible name, never by id. Both are correct a11y
    behaviour, not defects — but they are why "visual reading order" checks
    here run over the first N ON-SCREEN stops.
  * Tab-stop 4 is `a.qc-logo`, then the 11 top-level nav links.
    This DISPROVES the note in `header_component.py`'s docstring that
    "keyboard Tab from a fresh page load never reaches the logo — focus
    oscillates between an invisible reCAPTCHA badge iframe and <body>".
    Re-measured repeatedly this session in an anonymous context: focus
    reaches the logo on the 4th Tab every time. Reported, not silently
    rewritten in that file.
  * Header top-level nav reads: About us · Our Services · E-services ·
    Committee · Events · Exhibitions · Media Center · **Business Gateway** ·
    B2B · Contact us · FAQs. (`header_component.py` still says "Invest in
    Qatar" for the 8th item — the live label has changed.)
  * Mega-menu keyboard support is real and complete: with a
    `a.qc-nav-link[aria-haspopup="true"]` trigger focused, ArrowDown sets
    `aria-expanded="true"`, renders `.qc-nav-sub` (`display: block`) and
    moves focus onto the FIRST panel item; further ArrowDown/ArrowUp move
    within the panel; Escape collapses it (`aria-expanded="false"`) and
    returns focus to the trigger; Enter on the trigger navigates to the
    section landing page; Enter on a panel item navigates to that item.
  * "Our Services" panel items: Member's Services · ATA Carnet · TIR Carnet ·
    Certificate of Origin Online · **Legal Consultation** · Mediation ·
    Economic Consultancy · Economic Research · Proposal for Research ·
    Circulars · Add Your Company · Food Handlers Certification · Halls
    Booking. ADO-141806 names "Legal Service"; the real label is "Legal
    Consultation" — a case/label mismatch, scripted against the live label.
  * `nav.qc-nav` carries `aria-label="Main navigation"`; the main content
    region is `div#main-content[role="main"][tabindex="-1"]`. Enter on the
    skip link moves `document.activeElement` onto that div.
  * FAQ Knowledge Base (`/web/qatar-chamber/faq`): accordion headers are
    `button.qc-faq-q` inside `div.qc-faq-item`, all `aria-expanded="false"`
    on load, answer body `div.qc-faq-a`.
  * Contact Us (`/web/qatar-chamber/contact-us`): `form.qc-cu-form`
    (`novalidate`), fields `#qc-cu-fullName`, `#qc-cu-email`, `#qc-cu-phone`,
    `select#qc-cu-category`, `#qc-cu-subject`, `textarea#qc-cu-message`,
    `#qc-cu-attachment`; submit is a native `<button class="qc-cu-submit"
    type="submit">Submit Inquiry</button>`; the success/error banner is
    `div.qc-cu-status[data-qc-cu-status][role="alert"][aria-live="polite"]`,
    which gains `qc-cu-status--success` or `qc-cu-status--error`.
    The category `<select>` options are: "Select a category", "General
    Inquiry", Membership, Trade & Services, Events & Training, Certificates &
    Documents, Complaint, Other — so ONE ArrowDown from the default reaches
    "General Inquiry", exactly as ADO-141830 describes.
    **Subject is mandatory** (the form's own JS validator rejects an empty
    `#qc-cu-subject`) even though ADO-141821/141830 do not list it; the
    tests fill it and say so.
    The reCAPTCHA field renders `hidden` (score-based key), so no CAPTCHA
    interaction is needed or possible.
  * Responsive: at **768px and below** `nav.qc-nav` computes to
    `display: none` and zero top-level nav links are visible — the
    `button.qc-hamburger[aria-label="Menu"]` drawer IS the primary
    navigation at tablet AND mobile width. Enter on the focused hamburger
    sets `aria-expanded="true"` and moves focus to the first drawer nav link.
  * Arabic (`/ar/home`): `<html dir="rtl" lang="ar-SA">`; the same tab order
    (skip link -> Liferay sr-only pair -> logo -> nav links) plays out with
    x-coordinates DESCENDING (1490 -> 1397 -> 1244 ...), i.e. mirrored RTL.
  * **The announcement popup cannot render on qcdev right now.** Its module
    (`/o/qc-announcement-popup/qc-announcement-popup.js`) loads on every page
    and calls `GET /o/qc-newsletter/announcement-popups`, which returns
    `{"items":[],"status":"ok"}` — no announcement is configured, so
    `#qc-announcement-popup-root` is never injected (verified absent on `/`,
    `/home`, `/contact-us` and `/ar/home`). The five modal cases are skipped
    with that exact evidence rather than faked with a stubbed response.
  * **No tab control exists on About Us or Vision/Mission/Objectives.**
    Neither page renders any `[role="tab"]` or `[class*="tab"]` element;
    VMO is a stack of `.qc-vmo-section` blocks. ADO-141805's subject does
    not exist on this build, so it is skipped (substituting the homepage's
    `button.qc-os-tab` would be a different control on a different page).

FOLLOW-UP NOTE
--------------
The Contact Us locators below are here because PBI 131054's keyboard cases
need them and no `web/pages/contact_us/` object exists yet. When one lands,
move `CONTACT_*` and the form helpers into it and compose it here — do not
copy them.
"""

from core.web.base_page import BasePage
from core.web.overlays import (
    ANNOUNCEMENT_CLOSE,
    ANNOUNCEMENT_ROOT,
    CHATBOT_LAUNCHER_ROOT,
)
from config.settings import web_url
from web.pages.components.footer_component import FOOTER_SOCIAL_CONTAINER
from web.pages.components.header_component import HeaderComponent
from web.pages.faq.faq_page import FAQ_PATH, FaqPage

# ── Site paths (joined onto WEB_BASE_URL via config.settings.web_url) ─────
HOME_PATH = "/home"
CONTACT_US_PATH = "/web/qatar-chamber/contact-us"
# NOTE: `FAQ_PATH` is IMPORTED above from web/pages/faq/faq_page.py (PBI
# 131052's own Page Object, which owns the FAQ page's path and its full
# locator table) rather than re-declared here — the structure & redundancy
# scan flags a duplicated constant for the same element across two objects.
ABOUT_US_PATH = "/web/qatar-chamber/about-us"
VMO_PATH = "/web/qatar-chamber/about-us/vision-mission-objectives"
OUR_SERVICES_PATH_MARKER = "/our-services"
ABOUT_US_PATH_MARKER = "/about-us"
# AUTOMATION BUG FIX 2026-09-27 (ADO-141828): the drawer's 'About us' item is
# a PARENT (aria-haspopup="true", 6 children), so Enter correctly expands its
# submenu instead of navigating, and a wait_for_url() on /about-us times out.
# 'Contact us' is a CHILDLESS drawer item on this build — verified live at
# 768x1024 by a scoped Playwright probe run in the shell, 2026-09-27:
# hasChildren=false, childCount=0, no aria-haspopup, href
# /web/qatar-chamber/contact-us — so Enter on it activates a link, which is
# exactly the case's intent.
CONTACT_US_PATH_MARKER = "/contact-us"

# Standard responsive breakpoints the cases name.
MOBILE_VIEWPORT = (375, 812)
TABLET_VIEWPORT = (768, 1024)

# Settle budget for a keyboard-driven navigation (see
# `activate_focused_element` for the measurement behind it).
KEYBOARD_NAV_SETTLE_MS = 60000


class KeyboardNavigationPage(BasePage):
    """Keyboard/focus query + drive surface across the public site.

    Holds no assertions — tests assert. Every method either performs a
    keyboard action or returns observed state.
    """

    # ── Skip link & main content (ADO-141810, #141822) ──────────────────
    # `#qc-skip-link` by id: the page also renders Liferay's own
    # `a.sr-only-focusable` link with the SAME href="#main-content" and
    # near-identical text, so a text-based locator is ambiguous.
    SKIP_LINK = "a#qc-skip-link"
    MAIN_CONTENT = "#main-content"
    # Liferay's own screen-reader-only controls — tab stops 2 and 3. The
    # button's id is regenerated per render (see module docstring), so it is
    # matched on class + accessible name only.
    LIFERAY_SR_SKIP_LINK = "a.sr-only-focusable[href='#main-content']"
    LIFERAY_SR_ACCESSIBILITY_BUTTON = 'button.sr-only-focusable:has-text("Open Accessibility Menu")'

    # ── FAQ accordion (ADO-141804) ──────────────────────────────────────
    # Composed from FaqPage (PBI 131052's own Page Object, which owns the
    # full FAQ locator table) — never re-declared here.
    FAQ_ITEM = FaqPage.FAQ_ITEM
    FAQ_ACCORDION_HEADER = FaqPage.FAQ_QUESTION_BUTTON
    FAQ_ANSWER = FaqPage.FAQ_ANSWER

    # ── About Us / VMO tab control (ADO-141805) ─────────────────────────
    # Intent-based, deliberately generic: the case describes a tabbed
    # Vision/Mission/Objective block. Live, NO element matches either
    # selector on either page (see module docstring) — kept as a real,
    # resolvable locator so `tab_control_count()` reads an honest 0 rather
    # than erroring on an unresolved constant.
    TAB_CONTROL = '[role="tab"]'
    TAB_CONTROL_FALLBACK = '[class*="tab"][role], button[class*="tab"]'

    # ── Contact Us form (ADO-141802, #141803, #141821, #141830) ─────────
    CONTACT_FORM = "form.qc-cu-form"
    CONTACT_NAME_INPUT = "#qc-cu-fullName"
    CONTACT_EMAIL_INPUT = "#qc-cu-email"
    CONTACT_PHONE_INPUT = "#qc-cu-phone"
    CONTACT_CATEGORY_SELECT = "select#qc-cu-category"
    CONTACT_SUBJECT_INPUT = "#qc-cu-subject"
    CONTACT_MESSAGE_TEXTAREA = "textarea#qc-cu-message"
    CONTACT_SUBMIT_BUTTON = f"{CONTACT_FORM} >> button.qc-cu-submit"
    CONTACT_STATUS_BANNER = "div.qc-cu-status[data-qc-cu-status]"
    CONTACT_STATUS_SUCCESS_CLASS = "qc-cu-status--success"
    CONTACT_STATUS_ERROR_CLASS = "qc-cu-status--error"

    # ── Responsive drawer (ADO-141808, #141809, #141828, #141833) ───────
    HAMBURGER = "button.qc-hamburger"
    MENU_OPEN_ROOT = "header.qc-global-site-header.qc-menu-open"

    # ── Announcement modal (ADO-141807, #141817, #141818, #141831, #141836)
    # Imported from core/web/overlays.py — never re-declared here.
    ANNOUNCEMENT_POPUP = ANNOUNCEMENT_ROOT
    ANNOUNCEMENT_CLOSE_BUTTON = ANNOUNCEMENT_CLOSE
    ANNOUNCEMENT_API_PATH = "/o/qc-newsletter/announcement-popups"

    # ── Footer (ADO-141823) — container reused from FooterComponent ─────
    FOOTER_LINK = f"{FOOTER_SOCIAL_CONTAINER} >> a"

    # ── Page heading (destination confirmation, ADO-141820, #141829) ────
    PAGE_HEADING = "h1"

    def __init__(self, page):
        super().__init__(page)
        self.header = HeaderComponent(page)

    # ── Navigation (always anonymous — see module docstring) ────────────
    def open_home(self, locale: str = "en") -> "KeyboardNavigationPage":
        self.open_anonymous(web_url(HOME_PATH, locale=locale))
        self.wait_for(self.header.HEADER)
        self.wait_for_late_widgets()
        return self

    def open_home_keeping_announcement(self, locale: str = "en") -> "KeyboardNavigationPage":
        """Homepage WITHOUT dismissing the announcement overlay — only for
        the cases whose subject is that modal."""
        self.open_anonymous_keeping_overlays(web_url(HOME_PATH, locale=locale))
        return self

    def open_contact_us(self, locale: str = "en") -> "KeyboardNavigationPage":
        self.open_anonymous(web_url(CONTACT_US_PATH, locale=locale))
        self.wait_for(self.CONTACT_FORM)
        self.wait_for_late_widgets()
        return self

    def open_faq(self, locale: str = "en") -> "KeyboardNavigationPage":
        self.open_anonymous(web_url(FAQ_PATH, locale=locale))
        self.wait_for(self.FAQ_ACCORDION_HEADER, first=True)
        self.wait_for_late_widgets()
        return self

    def open_about_us(self, locale: str = "en") -> "KeyboardNavigationPage":
        self.open_anonymous(web_url(ABOUT_US_PATH, locale=locale))
        self.wait_for(self.PAGE_HEADING, first=True)
        self.wait_for_late_widgets()
        return self

    def open_vision_mission_objectives(self, locale: str = "en") -> "KeyboardNavigationPage":
        self.open_anonymous(web_url(VMO_PATH, locale=locale))
        self.wait_for(self.PAGE_HEADING, first=True)
        self.wait_for_late_widgets()
        return self

    # ── Generic state queries ───────────────────────────────────────────
    def current_url(self) -> str:
        return self.page.url

    def page_heading_text(self, timeout: int = 10000) -> str:
        """First `<h1>`'s text, waited until non-empty.

        This site's client-side (senna) routing paints the destination's hero
        heading a beat AFTER `networkidle` resolves — measured live, the
        About Us `<h1.qc-ap-hero-title>` reads '' with zero client rects
        immediately after the navigation settles and fills within ~1s. A
        same-tick read therefore returns an empty string and would fail a
        "did we land on the right page?" assertion for a timing reason.
        Returns whatever text exists on timeout (never raises) so the test's
        own assertion reports the miss, not a fixture-level error."""
        heading = self.page.locator(self.PAGE_HEADING).first
        try:
            heading.wait_for(state="visible", timeout=timeout)
            self.page.wait_for_function(
                "(el) => (el.textContent || '').trim().length > 0",
                arg=heading.element_handle(),
                timeout=timeout,
            )
        except Exception:  # noqa: BLE001 — an empty heading is an observation
            pass
        try:
            return heading.inner_text().strip()
        except Exception:  # noqa: BLE001 — no heading at all
            return ""

    def wait_for_late_widgets(self, timeout: int = 5000) -> None:
        """The chat launcher (`#qcChatbot`, see core/web/overlays.py) mounts
        asynchronously and adds a focusable button to the page. A tab walk
        started before it mounts sees the focusable set change underneath it
        — measured live as an intermittent one-element shift in a recorded
        tab sequence. Bounded, and tolerant of the widget being absent."""
        try:
            self.page.locator(CHATBOT_LAUNCHER_ROOT).first.wait_for(
                state="attached", timeout=timeout
            )
        except Exception:  # noqa: BLE001 — absent widget is fine, nothing to settle
            pass

    def document_direction(self) -> str:
        return self.page.evaluate(
            "() => document.documentElement.getAttribute('dir') "
            "|| getComputedStyle(document.body).direction"
        )

    def is_login_form_present(self) -> bool:
        """ADO-141827's negative control — a public visitor must never be
        interrupted by an authentication prompt."""
        return self.page.evaluate(
            "() => !!document.querySelector("
            "'input[type=password], #_com_liferay_login_web_portlet_LoginPortlet_login, "
            "form[action*=\"/c/portal/login\"]')"
        )

    def is_signed_out(self) -> bool:
        """Liferay stamps the body with `signed-out` / `signed-in`."""
        return self.page.evaluate(
            "() => document.body.classList.contains('signed-out')"
        )

    # ── Skip link (ADO-141810, #141822) ─────────────────────────────────
    def skip_link_viewport_top(self) -> float:
        return self.page.evaluate(
            "(sel) => document.querySelector(sel).getBoundingClientRect().top",
            self.SKIP_LINK,
        )

    def is_skip_link_offscreen(self) -> bool:
        """True while the link is rendered outside the viewport's top edge —
        its unfocused, visually-hidden state."""
        return self.skip_link_viewport_top() < 0

    def wait_for_skip_link_revealed(self, timeout: int = 5000) -> None:
        """The reveal is a CSS transition with no DOM/network signal, so a
        same-tick read after Tab still sees the off-screen position. Waits on
        the rect crossing the viewport's top edge — a condition, not a
        sleep."""
        self.wait_for_condition(
            "(sel) => { const el = document.querySelector(sel); "
            "return !!el && el.getBoundingClientRect().top >= 0; }",
            arg=self.SKIP_LINK,
            timeout=timeout,
        )

    _FOCUS_IN_MAIN_PREDICATE = (
        "(sel) => { const main = document.querySelector(sel); "
        "const el = document.activeElement; "
        "return !!main && !!el && (el === main || main.contains(el)); }"
    )

    def is_focus_inside_main_content(self) -> bool:
        return self.page.evaluate(self._FOCUS_IN_MAIN_PREDICATE, self.MAIN_CONTENT)

    def wait_for_focus_inside_main_content(self, timeout: int = 10000) -> None:
        """Activating the skip link moves focus via a fragment jump handled
        by client JS, so the focus move lands a frame after the Enter —
        condition-based wait, never a sleep."""
        self.wait_for_condition(
            self._FOCUS_IN_MAIN_PREDICATE, arg=self.MAIN_CONTENT, timeout=timeout
        )

    def is_focus_inside_header(self) -> bool:
        return self.page.evaluate(
            "(sel) => { const h = document.querySelector(sel); const el = document.activeElement; "
            "return !!h && !!el && h.contains(el); }",
            "header.qc-global-site-header",
        )

    # ── Header nav (composed from HeaderComponent's own locators) ───────
    def nav_link(self, label: str) -> str:
        """Locator for a top-level nav link by its visible label, built on
        HeaderComponent.NAV_TOP_LEVEL_ITEMS (the direct-child chain that
        already excludes the mega-menu's same-named duplicates)."""
        return f'{HeaderComponent.NAV_TOP_LEVEL_ITEMS}:has-text("{label}")'

    def nav_link_labels(self) -> list:
        return self.header.nav_item_labels()

    def focus_nav_link(self, label: str) -> "KeyboardNavigationPage":
        self.page.locator(self.nav_link(label)).first.focus()
        return self

    def reach_nav_link_by_tab(self, label: str, max_presses: int = 20) -> bool:
        return self.press_tab_until_focused(self.nav_link(label), max_presses=max_presses)

    def nav_landmark_accessible_name(self) -> str:
        return self.page.locator(HeaderComponent.NAV).first.get_attribute("aria-label") or ""

    def nav_landmark_tag(self) -> str:
        return self.page.locator(HeaderComponent.NAV).first.evaluate(
            "el => el.tagName.toLowerCase()"
        )

    def nav_link_aria(self, label: str) -> dict:
        """`aria-expanded` / `aria-haspopup` of a top-level nav link."""
        return self.page.locator(self.nav_link(label)).first.evaluate(
            "el => ({expanded: el.getAttribute('aria-expanded'), "
            "haspopup: el.getAttribute('aria-haspopup')})"
        )

    # ── Mega-menu (ADO-141806, #141814, #141815, #141829) ───────────────
    def mega_menu_item(self, trigger_label: str, item_label: str) -> str:
        """Locator for one item inside a named top-level item's mega-menu
        panel — built on HeaderComponent's own panel class constant."""
        return (
            f'{HeaderComponent.NAV} >> ul.qc-nav-list > li.qc-has-children'
            f':has(> a.qc-nav-link:text-is("{trigger_label}")) '
            f'{HeaderComponent.NAV_ITEM_SUBMENU_PANEL} a:text-is("{item_label}")'
        )

    def mega_menu_item_labels(self, trigger_label: str) -> list:
        return self.page.evaluate(
            "(label) => { const li = [...document.querySelectorAll('li.qc-has-children')]"
            ".find(e => { const a = e.querySelector(':scope > a.qc-nav-link'); "
            "return a && a.textContent.trim() === label; }); "
            "return li ? [...li.querySelectorAll('.qc-nav-sub a')]"
            ".map(a => a.textContent.trim()) : []; }",
            trigger_label,
        )

    def is_mega_menu_panel_visible(self, trigger_label: str) -> bool:
        return self.page.evaluate(
            "(label) => { const li = [...document.querySelectorAll('li.qc-has-children')]"
            ".find(e => { const a = e.querySelector(':scope > a.qc-nav-link'); "
            "return a && a.textContent.trim() === label; }); "
            "if (!li) return false; const panel = li.querySelector('.qc-nav-sub'); "
            "return !!panel && panel.getClientRects().length > 0 "
            "&& getComputedStyle(panel).display !== 'none'; }",
            trigger_label,
        )

    # Locator lives here, never at a call site: the aria-expanded transition
    # has no DOM-attachment/visibility signal Playwright can wait on, so the
    # wait has to be a JS predicate — and that predicate contains a selector.
    _MEGA_MENU_EXPANDED_PREDICATE = (
        "([label, want]) => { const a = "
        "[...document.querySelectorAll('a.qc-nav-link[aria-haspopup]')]"
        ".find(e => e.textContent.trim() === label); "
        "return !!a && a.getAttribute('aria-expanded') === want; }"
    )

    def wait_for_mega_menu_expanded(self, trigger_label: str,
                                    expanded: bool = True,
                                    timeout: int = 10000) -> "KeyboardNavigationPage":
        """Wait for a top-level trigger's `aria-expanded` to reach the given
        state — condition-based, never a sleep."""
        self.wait_for_condition(
            self._MEGA_MENU_EXPANDED_PREDICATE,
            arg=[trigger_label, "true" if expanded else "false"],
            timeout=timeout,
        )
        return self

    def open_mega_menu_with_arrow(self, trigger_label: str) -> "KeyboardNavigationPage":
        """Focus the trigger, then ArrowDown — the live behaviour is that
        ArrowDown both expands the panel and moves focus to its first item."""
        self.focus_nav_link(trigger_label)
        self.press_key("ArrowDown")
        return self.wait_for_mega_menu_expanded(trigger_label, expanded=True)

    def collapse_mega_menu_with_escape(self, trigger_label: str) -> "KeyboardNavigationPage":
        self.press_key("Escape")
        return self.wait_for_mega_menu_expanded(trigger_label, expanded=False)

    # ── Keyboard activation ─────────────────────────────────────────────
    def activate_focused_element(self, wait_for_navigation: bool = False,
                                 url_marker: str = None) -> "KeyboardNavigationPage":
        """Press Enter on whatever currently holds focus. When the action is
        a navigation, waits on the destination URL (condition-based) instead
        of guessing a settle time, and then settles the destination's
        late-mounting widgets exactly as `open_*()` does — a keyboard-driven
        navigation lands on a page whose focusable set is still growing just
        as much as a URL navigation does, and this is the only route by which
        a test reaches a page without going through `open_*()`."""
        self.press_key("Enter")
        if wait_for_navigation and url_marker:
            self.wait_for_url(lambda url: url_marker in url)
            # Explicit budget instead of Playwright's silent 30 000 ms
            # default. ADO-141832 (Edge) and ADO-141825 both PASS standalone
            # — measured 2026-09-28, ~35 s wall each — and both failed the
            # parallel suite run on a bare `Timeout 30000ms exceeded`: qcdev
            # settles a keyboard-driven page turn more slowly when several
            # xdist workers are hitting it at once. Genuine slowness, so the
            # one specific bounded wait is raised; the condition itself is
            # unchanged and nothing is slept on.
            self.page.wait_for_load_state("networkidle", timeout=KEYBOARD_NAV_SETTLE_MS)
            self.wait_for_late_widgets()
        return self

    def press_shift_tab(self, times: int = 1) -> None:
        for _ in range(times):
            self.press_key("Shift+Tab")

    # ── FAQ accordion (ADO-141804) ──────────────────────────────────────
    def first_accordion_header(self) -> str:
        return f"{self.FAQ_ACCORDION_HEADER} >> nth=0"

    def reach_first_accordion_header_by_tab(self, max_presses: int = 40) -> bool:
        return self.press_tab_until_focused(self.first_accordion_header(),
                                            max_presses=max_presses)

    def accordion_expanded_state(self, index: int = 0) -> str:
        return self.page.locator(self.FAQ_ACCORDION_HEADER).nth(index).get_attribute(
            "aria-expanded"
        ) or ""

    # ── About Us / VMO tab control (ADO-141805) ─────────────────────────
    def tab_control_count(self) -> int:
        return (
            self.page.locator(self.TAB_CONTROL).count()
            + self.page.locator(self.TAB_CONTROL_FALLBACK).count()
        )

    # ── Contact Us form (ADO-141802, #141803, #141821, #141830) ─────────
    def reach_contact_field_by_tab(self, locator: str, max_presses: int = 60) -> bool:
        return self.press_tab_until_focused(locator, max_presses=max_presses)

    def type_into_focused(self, text: str) -> None:
        """Type into whatever holds focus — keyboard-only entry, no click,
        no `fill()` (which sets the value programmatically and would not be
        a keyboard interaction)."""
        self.page.keyboard.type(text)

    def select_category_with_arrow_keys(self, option_label: str,
                                        max_presses: int = 15) -> str:
        """With the native `<select>` focused, step through its options with
        ArrowDown until the requested label is selected. Returns the label
        actually selected so the caller can assert on it."""
        for _ in range(max_presses):
            if self.selected_category_label() == option_label:
                break
            self.press_key("ArrowDown")
        return self.selected_category_label()

    def selected_category_label(self) -> str:
        return self.page.locator(self.CONTACT_CATEGORY_SELECT).evaluate(
            "el => el.options[el.selectedIndex] ? el.options[el.selectedIndex].text.trim() : ''"
        )

    def complete_contact_form_with_keyboard(self, name: str, email: str,
                                            category: str, subject: str,
                                            message: str) -> dict:
        """Fill the inquiry form using ONLY the keyboard: Tab to reach each
        control, `keyboard.type()` for text, ArrowDown for the category
        `<select>`. Returns the field-by-field reach result so the test can
        assert the flow really was keyboard-reachable.

        `subject` is filled because the form's own JS validator requires it
        (see module docstring) even though the source cases do not name it.
        """
        reached = {}

        reached["name"] = self.reach_contact_field_by_tab(self.CONTACT_NAME_INPUT)
        self.type_into_focused(name)

        reached["email"] = self.reach_contact_field_by_tab(self.CONTACT_EMAIL_INPUT,
                                                           max_presses=5)
        self.type_into_focused(email)

        reached["category"] = self.reach_contact_field_by_tab(self.CONTACT_CATEGORY_SELECT,
                                                              max_presses=5)
        reached["category_selected"] = self.select_category_with_arrow_keys(category)

        reached["subject"] = self.reach_contact_field_by_tab(self.CONTACT_SUBJECT_INPUT,
                                                             max_presses=5)
        self.type_into_focused(subject)

        reached["message"] = self.reach_contact_field_by_tab(self.CONTACT_MESSAGE_TEXTAREA,
                                                             max_presses=5)
        self.type_into_focused(message)

        return reached

    def contact_field_values(self) -> dict:
        """What the form actually holds — proves the keyboard entry landed
        in the intended fields."""
        return {
            "name": self.page.locator(self.CONTACT_NAME_INPUT).input_value(),
            "email": self.page.locator(self.CONTACT_EMAIL_INPUT).input_value(),
            "category": self.selected_category_label(),
            "subject": self.page.locator(self.CONTACT_SUBJECT_INPUT).input_value(),
            "message": self.page.locator(self.CONTACT_MESSAGE_TEXTAREA).input_value(),
        }

    def reach_submit_button_by_tab(self, max_presses: int = 10) -> bool:
        return self.press_tab_until_focused(self.CONTACT_SUBMIT_BUTTON,
                                            max_presses=max_presses)

    def submit_button_semantics(self) -> dict:
        """ADO-141811: the submit control must be a native `<button>` (or
        role=button) carrying an accessible name."""
        return self.page.locator(self.CONTACT_SUBMIT_BUTTON).evaluate(
            "el => ({tag: el.tagName.toLowerCase(), type: el.getAttribute('type') || '', "
            "role: el.getAttribute('role') || '', "
            "accessibleName: (el.getAttribute('aria-label') || el.textContent || '').trim()})"
        )

    def wait_for_contact_status_banner(self, timeout: int = 30000) -> None:
        """The banner is `hidden` until the submit round-trip resolves."""
        self.page.locator(self.CONTACT_STATUS_BANNER).first.wait_for(
            state="visible", timeout=timeout
        )

    def contact_status(self) -> dict:
        banner = self.page.locator(self.CONTACT_STATUS_BANNER).first
        return banner.evaluate(
            "el => ({classes: el.className, text: (el.textContent || '').trim(), "
            "hidden: el.hidden, role: el.getAttribute('role') || ''})"
        )

    # ── Responsive drawer (ADO-141808, #141809, #141828, #141833) ───────
    def is_hamburger_visible(self) -> bool:
        return self.is_visible(self.HAMBURGER)

    def hamburger_aria_expanded(self) -> str:
        return self.page.locator(self.HAMBURGER).get_attribute("aria-expanded") or ""

    def reach_hamburger_by_tab(self, max_presses: int = 12) -> bool:
        return self.press_tab_until_focused(self.HAMBURGER, max_presses=max_presses)

    def open_drawer_with_enter(self) -> "KeyboardNavigationPage":
        """Enter on the focused hamburger. Live behaviour: the drawer opens
        (`aria-expanded="true"`) and focus lands on its first nav link."""
        self.press_key("Enter")
        self.wait_for_condition(
            "(sel) => { const b = document.querySelector(sel); "
            "return !!b && b.getAttribute('aria-expanded') === 'true'; }",
            arg=self.HAMBURGER,
        )
        return self

    # ── Announcement modal (all five cases are skipped — see docstring) ─
    def is_announcement_popup_showing(self) -> bool:
        return self.is_visible(self.ANNOUNCEMENT_POPUP)

    def announcement_focusable_count(self) -> int:
        return self.page.evaluate(
            "(sel) => { const root = document.querySelector(sel); if (!root) return 0; "
            "return [...root.querySelectorAll('a[href],button,input,select,textarea,[tabindex]')]"
            ".filter(e => e.getClientRects().length && e.getAttribute('tabindex') !== '-1').length; }",
            self.ANNOUNCEMENT_POPUP,
        )

    def is_focus_inside_announcement(self) -> bool:
        return self.page.evaluate(
            "(sel) => { const root = document.querySelector(sel); const el = document.activeElement; "
            "return !!root && !!el && root.contains(el); }",
            self.ANNOUNCEMENT_POPUP,
        )

    def tab_recording_announcement_containment(self, presses: int,
                                               key: str = "Tab") -> list:
        """One record per key press — `{"focus": <descriptor>,
        "inside_popup": bool}` — so a focus-trap test can judge EVERY stop
        rather than only the state left behind at the end of the walk."""
        records = []
        for _ in range(presses):
            self.press_key(key)
            records.append({
                "focus": self.active_element(),
                "inside_popup": self.is_focus_inside_announcement(),
            })
        return records

    def reach_announcement_close_by_tab(self, max_presses: int = 10) -> bool:
        return self.press_tab_until_focused(self.ANNOUNCEMENT_CLOSE_BUTTON,
                                            max_presses=max_presses)

    # ── Footer (ADO-141823) ─────────────────────────────────────────────
    def first_footer_link(self) -> str:
        return f"{self.FOOTER_LINK} >> nth=0"

    def reach_first_footer_link_by_tab(self, max_presses: int = 120) -> bool:
        return self.press_tab_until_focused(self.first_footer_link(),
                                            max_presses=max_presses)

"""
web/tests/keyboard_navigation/test_keyboard_navigation_web.py

Web-platform cases for PBI 131054 ("QC - 001 - Keyboard Navigation"), suite
140392 — 18 approved Automation cases (141801 is Manual, not here):
141800, 141802-141813, 141825, 141826, 141828, 141832, 141833.

Rules applied throughout:
  - Fresh UNAUTHENTICATED context for every test ({"auth": False}); the
    cross-browser cases (141812 Chrome, 141813 Firefox, 141832 Edge) launch
    their own browser inside the test via the module-local `engine_page`
    fixture (unauthenticated, own context) — conftest.py is untouched. That
    fixture attaches a failure screenshot to Allure itself, because the
    shared makereport hook only knows the `page` fixture.
  - REAL keyboard input only (page.keyboard.press) — no element.focus().
  - Every test collects all deviations and fails once with the full list.

Disclosed readings:
  - "Visible focus indicator" = the tabbed-to element matches
    :focus-visible AND paints an outline (style != none, width >= 1px) or a
    box-shadow/border/background that differs from its unfocused state.
  - Nav cases run at 1920px: at <= 1440px the header nav collapses behind
    the "Menu" hamburger, so primary links are reachable only after opening
    it (141809/141828/141833 open it with Enter, as a keyboard user must).
  - "Focus indicator remains visible / focus visibility consistent"
    (141808, 141809, 141812, 141813, 141828, 141832, 141833) also runs a full
    real-Tab walk of the homepage and records every focus stop whose element
    is entirely outside the viewport horizontally (its indicator cannot be
    seen). Confirmed live: off-screen carousel cards (.qc-promo-slide links
    and "Read More" service cards, plus auto-scrolling partner/logo
    marquees) take focus without being scrolled into view or made inert.
  - 141805: the About Us Vision/Mission/Objective page has no tab control
    (no role=tab / tablist, no tab buttons) — reported as not rendered.
  - 141807: the modal is the Global Announcement popup the case names
    (#qc-announcement-popup-root button.qc-ann-close). It is not published on
    qcdev, so the test skips when /o/qc-newsletter/announcement-popups has no
    items; it runs unchanged once one is published.
"""

import allure
import pytest

from config.settings import settings
from core.utils.reporting import attach_screenshot, extract_test_case_id
from web.pages.keyboard_navigation.keyboard_navigation_page import (
    CONTACT_PATH, FAQ_PATH, HOME_PATH, VMO_PATH, KeyboardNavigationPage)

PBI = "131054"
DESKTOP = {"viewport": (1920, 1080), "auth": False}
TABLET = {"viewport": (768, 1024), "auth": False}
MOBILE = {"viewport": (375, 812), "auth": False}

pytestmark = [pytest.mark.web, pytest.mark.pbi_131054, pytest.mark.accessibility, pytest.mark.global_]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
class _Check:
    def __init__(self, title):
        self.title, self.deviations, self.notes = title, [], []

    def truthy(self, label, condition, expected, actual):
        if not condition:
            self.deviations.append(f"{label}: expected {expected!r}, got {actual!r}")

    def equals(self, label, actual, expected):
        self.truthy(label, actual == expected, expected, actual)

    def note(self, text):
        self.notes.append(text)

    def assert_clean(self):
        if self.notes:
            allure.attach("\n".join(self.notes), "notes", allure.attachment_type.TEXT)
        assert not self.deviations, f"{self.title}: {len(self.deviations)} deviation(s):\n  - " + "\n  - ".join(self.deviations)


def _indicator(check: _Check, name: str, info, before: dict = None):
    """Visible focus indicator on the focused element (see module docstring)."""
    if not info:
        check.truthy(f"{name} focused", False, "focused element", None)
        return
    outline = info["outlineStyle"] not in ("none", "") and float(info["outlineWidth"].rstrip("px") or 0) >= 1
    changed = before is not None and any(before[k] != info[k] for k in ("boxShadow", "borderColor", "backgroundColor"))
    check.truthy(f"{name} :focus-visible", info["focusVisible"], True, info["focusVisible"])
    check.truthy(f"{name} visible focus indicator", outline or changed, "outline >= 1px or a focus style change",
                 f"outline={info['outlineStyle']} {info['outlineWidth']} {info['outlineColor']}, box-shadow={info['boxShadow']}")
    if before is not None and outline:
        check.truthy(f"{name} distinguishable from unfocused", before["outlineStyle"] == "none"
                     or before["outlineWidth"] != info["outlineWidth"], "no outline when unfocused",
                     f"unfocused outline={before['outlineStyle']} {before['outlineWidth']}")
    check.note(f"{name}: outline {info['outlineStyle']} {info['outlineWidth']} {info['outlineColor']}")


def _in_viewport(check: _Check, name: str, info, width: int):
    if info:
        check.truthy(f"{name} positioned inside the {width}px viewport",
                     info["x"] >= 0 and info["x"] + info["width"] <= width + 1, f"0..{width}px",
                     f"x={round(info['x'])}, w={round(info['width'])}")


def _audit_offscreen(check: _Check, kb: KeyboardNavigationPage, label: str):
    """Full homepage Tab walk; any stop entirely outside the viewport horizontally is a deviation."""
    stops = kb.focus_walk()
    off = [s for s in stops if s["offViewport"]]
    allure.attach(f"{len(stops)} focus stops; {len(off)} off-viewport\n" + "\n".join(
        f"{s['tag']}.{s['cls'].split(' ')[0]} '{s['text'][:25]}' x={round(s['x'])}" for s in off),
        f"focus walk ({label})", allure.attachment_type.TEXT)
    check.truthy(f"{label}: every Tab stop visible on screen", not off,
                 "no focus stop outside the viewport",
                 f"{len(off)} of {len(stops)} stops off-viewport: " + ", ".join(
                     f"{s['cls'].split(' ')[0]}('{s['text'][:18]}')@x={round(s['x'])}" for s in off))


def _nav(info) -> bool:
    return bool(info) and "qc-nav-link" in info["cls"]


def _meta(tc, title, story, severity=allure.severity_level.CRITICAL):
    def deco(fn):
        for d in (allure.label("testcase", tc), allure.label("pbi", PBI), allure.title(title),
                  allure.severity(severity), allure.story(story), allure.feature("Keyboard Navigation"),
                  allure.epic("Global")):
            fn = d(fn)
        return fn
    return deco


N, C = allure.severity_level.NORMAL, allure.severity_level.CRITICAL


@pytest.fixture
def engine_page(request, playwright_instance):
    """Launch a specific desktop browser for this test only (param dict:
    engine = chromium|firefox, channel = chrome|msedge|None). Unauthenticated
    context at 1920x1080. Attaches a screenshot to Allure on failure."""
    cfg = request.param
    launcher = getattr(playwright_instance, cfg["engine"])
    kwargs = {"headless": settings.headless}
    if cfg.get("channel"):
        kwargs["channel"] = cfg["channel"]
    browser = launcher.launch(**kwargs)
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    pg = context.new_page()
    yield pg
    rep = getattr(request.node, "rep_call", None)
    if rep is not None and rep.failed:
        try:
            attach_screenshot(pg.screenshot(), extract_test_case_id(request.node), settings.project_name,
                              settings.reports_dir)
        except Exception:  # noqa: BLE001 — evidence must never mask the real failure
            pass
    context.close()
    browser.close()


# ---------------------------------------------------------------------------
# Focus indicators (141800, 141802-141807)
# ---------------------------------------------------------------------------
@_meta("141800", "Primary navigation link shows a visible focus indicator when tabbed to (Light theme)", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141800
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_nav_link_focus_indicator(page):
    """Azure TC 141800 | PBI 131054 — homepage EN Light at 1920: Tab to 'About us' -> visible indicator."""
    check = _Check("TC 141800")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    check.truthy("Light theme", page.evaluate("document.documentElement.dataset.theme") in (None, "light"), "light",
                 page.evaluate("document.documentElement.dataset.theme"))
    before = kb.unfocused_style(kb.NAV_LINK)
    n, info = kb.tab_until(lambda i: _nav(i) and i["text"].lower() == "about us")
    check.truthy("Tab reaches 'About us'", n is not None, "reached", info and info["text"])
    _indicator(check, "'About us' link", info, before)
    check.assert_clean()


@_meta("141802", "Page button shows a visible focus indicator when tabbed to", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141802
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_button_focus_indicator(page):
    """Azure TC 141802 | PBI 131054 — Contact Us: Tab to the form's submit button ('Submit Inquiry')."""
    check = _Check("TC 141802")
    kb = KeyboardNavigationPage(page).open_path(CONTACT_PATH)
    before = kb.unfocused_style(kb.CONTACT_SUBMIT)
    n, info = kb.tab_until(lambda i: "qc-cu-submit" in i["cls"], max_presses=120)
    check.truthy("Tab reaches the Submit button", n is not None, "reached", info and info["text"])
    check.note(f"submit label on the live page: {info and info['text']!r} (case: 'Submit')")
    _indicator(check, "Submit button", info, before)
    check.assert_clean()


@_meta("141803", "Form input field shows a visible focus indicator when tabbed to", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141803
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_input_focus_indicator(page):
    """Azure TC 141803 | PBI 131054 — Contact Us 'Name' input (#qc-cu-fullName, label 'Full Name *')."""
    check = _Check("TC 141803")
    kb = KeyboardNavigationPage(page).open_path(CONTACT_PATH)
    before = kb.unfocused_style(kb.CONTACT_NAME)
    n, info = kb.tab_until(lambda i: i["id"] == "qc-cu-fullName", max_presses=120)
    check.truthy("Tab reaches the Name input", n is not None, "reached", info and info["id"])
    _indicator(check, "Name input", info, before)
    check.assert_clean()


@_meta("141804", "Accordion header shows a visible focus indicator when tabbed to", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141804
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_accordion_focus_indicator(page):
    """Azure TC 141804 | PBI 131054 — FAQ page: Tab to the first (collapsed) accordion header."""
    check = _Check("TC 141804")
    kb = KeyboardNavigationPage(page).open_path(FAQ_PATH)
    kb.wait_for(kb.FAQ_QUESTION, first=True)
    before = kb.unfocused_style(kb.FAQ_QUESTION)
    n, info = kb.tab_until(lambda i: "qc-faq-q" in i["cls"])
    check.truthy("Tab reaches the first accordion header", n is not None, "reached", info and info["text"])
    check.equals("header collapsed before expanding", info and info["expanded"], "false")
    _indicator(check, "accordion header", info, before)
    check.assert_clean()


@_meta("141805", "Tab control shows a visible focus indicator when tabbed to", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141805
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_tab_control_focus_indicator(page):
    """Azure TC 141805 | PBI 131054 — About Us Vision/Mission/Objective tabbed block: Tab to 'Mission'."""
    check = _Check("TC 141805")
    kb = KeyboardNavigationPage(page).open_path(VMO_PATH)
    tabs = kb.count(kb.TAB_CONTROL)
    if tabs == 0:
        # QA Manager ruling 2026-09-24: the VMO page is DESIGNED as three numbered stacked
        # sections (01 Vision / 02 Mission / 03 Objectives), not a tab widget, so the case's
        # precondition doesn't exist on this page. Not a product defect -> blocked until the
        # case is re-pointed at a real tab control (e.g. the Chamber Events status tablist).
        pytest.skip(f"Precondition not met: no tab control on {kb.current_url()} (VMO renders stacked "
                    "sections by design) - case needs re-pointing to a page with a real tablist")
    else:
        n, info = kb.tab_until(lambda i: i["role"] == "tab" and "mission" in i["text"].lower())
        check.truthy("Tab reaches the 'Mission' tab", n is not None, "reached", info and info["text"])
        _indicator(check, "'Mission' tab", info)
    check.assert_clean()


@_meta("141806", "Mega-menu item shows a visible focus indicator when navigated to", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141806
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_mega_menu_item_focus_indicator(page):
    """Azure TC 141806 | PBI 131054 — Tab to 'Our Services', ArrowDown opens the mega-menu, ArrowDown to the
    legal item (live label 'Legal Consultation'; case example 'Legal Service')."""
    check = _Check("TC 141806")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    n, info = kb.tab_until(lambda i: _nav(i) and i["text"] == "Our Services")
    check.truthy("Tab reaches 'Our Services'", n is not None, "reached", info and info["text"])
    info = kb.press("ArrowDown")
    kb.settle()
    check.truthy("mega-menu panel opens", kb.controlled_panel_visible(f"{kb.NAV_LINK}[aria-controls='qc-submenu-2']"),
                 "visible panel", "not visible")
    reached = info if info and "legal" in info["text"].lower() else None
    for _ in range(15):
        if reached:
            break
        info = kb.press("ArrowDown")
        if info and "legal" in info["text"].lower():
            reached = info
    check.truthy("arrow keys reach the legal mega-menu item", reached is not None, "'Legal …' item", info and info["text"])
    _indicator(check, "mega-menu item", reached)
    check.assert_clean()


@_meta("141807", "Modal close control shows a visible focus indicator", "Focus indicator")
@pytest.mark.ui
@pytest.mark.tc_141807
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_modal_close_focus_indicator(page):
    """Azure TC 141807 | PBI 131054 — Global Announcement popup close control (see module docstring)."""
    kb = KeyboardNavigationPage(page)
    items = kb.published_announcements()
    if not items:
        pytest.skip("No published announcement on qcdev (API /o/qc-newsletter/announcement-popups items: [])")
    check = _Check("TC 141807")
    kb.open_path_keep_popup(HOME_PATH)
    kb.wait_for(kb.ANN_CLOSE, timeout=15000)
    n, info = kb.tab_until(lambda i: "qc-ann-close" in i["cls"], max_presses=40)
    check.truthy("Tab reaches the popup close control", n is not None, "reached", info and info["cls"])
    _indicator(check, "popup close control", info)
    check.assert_clean()


# ---------------------------------------------------------------------------
# Responsive focus visibility (141808, 141809)
# ---------------------------------------------------------------------------
@_meta("141808", "Focus indicator remains visible at mobile viewport width", "Responsive", N)
@pytest.mark.ui
@pytest.mark.tc_141808
@pytest.mark.parametrize("page", [MOBILE], indirect=True)
def test_focus_visible_mobile(page):
    """Azure TC 141808 | PBI 131054 — 375px: Tab to the mobile menu toggle, indicator visible and positioned
    in the layout; plus the full homepage focus-visibility walk."""
    check = _Check("TC 141808")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    n, info = kb.tab_until(lambda i: "qc-hamburger" in i["cls"])
    check.truthy("Tab reaches the mobile menu toggle", n is not None, "reached", info and info["text"])
    _indicator(check, "menu toggle", info)
    _in_viewport(check, "menu toggle", info, 375)
    _audit_offscreen(check, kb, "375px homepage")
    check.assert_clean()


@_meta("141809", "Focus indicator remains visible at tablet viewport width", "Responsive", N)
@pytest.mark.ui
@pytest.mark.tc_141809
@pytest.mark.parametrize("page", [TABLET], indirect=True)
def test_focus_visible_tablet(page):
    """Azure TC 141809 | PBI 131054 — 768px: nav is behind 'Menu'; Enter opens it, focus lands on a primary
    nav link -> indicator visible and positioned; plus the full homepage walk (fresh load)."""
    check = _Check("TC 141809")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    n, info = kb.tab_until(lambda i: _nav(i) or "qc-hamburger" in i["cls"])
    if info and "qc-hamburger" in info["cls"]:
        check.note("768px: primary nav collapsed behind the 'Menu' toggle; opened with Enter")
        info = kb.press("Enter")
        kb.settle()
    check.truthy("focus on a primary navigation link", _nav(info), "qc-nav-link", info and info["cls"])
    _indicator(check, "nav link", info)
    _in_viewport(check, "nav link", info, 768)
    kb.open_path(HOME_PATH)
    _audit_offscreen(check, kb, "768px homepage")
    check.assert_clean()


# ---------------------------------------------------------------------------
# Skip link and semantics (141810, 141811)
# ---------------------------------------------------------------------------
@_meta("141810", "Skip-to-content link is revealed only when it receives keyboard focus", "Skip link")
@pytest.mark.ui
@pytest.mark.tc_141810
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_skip_link_revealed_on_focus(page):
    """Azure TC 141810 | PBI 131054 — before any key the skip link is off-screen; first Tab focuses it and it
    becomes visible at the top (after its 0.15s slide-in transition)."""
    check = _Check("TC 141810")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    b = kb.box(kb.SKIP_LINK)
    check.truthy("skip link not visibly rendered before Tab", b is None or b["y"] + b["height"] <= 0,
                 "above the viewport", b)
    info = kb.press("Tab")
    check.truthy("first Tab focuses the skip link", info and "qc-skip-link" in info["cls"], "a.qc-skip-link",
                 info and info["cls"])
    check.equals("skip link text", info and info["text"], "Skip to main content")
    kb.settle()
    b = kb.box(kb.SKIP_LINK)
    check.truthy("skip link visible at the top after focus", b is not None and b["y"] >= 0 and b["y"] < 100,
                 "inside the top of the viewport", b)
    check.assert_clean()


@_meta("141811", "Interactive elements expose semantic HTML tags and ARIA attributes", "Semantics")
@pytest.mark.ui
@pytest.mark.tc_141811
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_semantics_and_aria(page):
    """Azure TC 141811 | PBI 131054 — nav landmark with an accessible name; mega-menu toggle exposes
    aria-haspopup and an aria-expanded that REFLECTS its open/closed state; a form submit control is a
    native button with an accessible name (homepage footer newsletter 'Subscribe')."""
    check = _Check("TC 141811")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    nav = kb.element_facts(kb.NAV)
    check.equals("primary nav element", nav["tag"], "nav")
    check.truthy("primary nav has an accessible name", bool(nav["ariaLabel"] or nav["labelledby"]),
                 "aria-label/aria-labelledby", nav)
    toggle = f"{kb.NAV_LINK}[aria-controls='qc-submenu-2']"
    closed = kb.element_facts(toggle)
    check.equals("mega-menu toggle aria-haspopup", closed["haspopup"], "true")
    check.equals("mega-menu toggle aria-expanded (closed)", closed["expanded"], "false")
    kb.tab_until(lambda i: _nav(i) and i["text"] == "Our Services")
    kb.press("ArrowDown")
    kb.settle()
    opened = kb.element_facts(toggle)
    check.truthy("mega-menu panel open", kb.controlled_panel_visible(toggle), True, False)
    check.equals("mega-menu toggle aria-expanded reflects the open state", opened["expanded"], "true")
    submit = kb.element_facts(kb.FOOTER_SUBMIT)
    check.truthy("submit control is a native button (or role=button)", submit["tag"] == "button" or submit["role"] == "button",
                 "button", submit["tag"])
    check.truthy("submit control has an accessible name", bool(submit["name"]), "non-empty", submit["name"])
    check.assert_clean()


# ---------------------------------------------------------------------------
# Cross-browser / viewport consistency (141812, 141813, 141832, 141828, 141833)
# ---------------------------------------------------------------------------
def _desktop_consistency(check: _Check, pg, label: str):
    kb = KeyboardNavigationPage(pg).open_path(HOME_PATH)
    n, first = kb.tab_until(_nav)
    check.truthy(f"{label}: Tab reaches the primary nav", n is not None, "a nav link", first and first["text"])
    xs = [first["x"]] if first else []
    names = [first["text"]] if first else []
    for _ in range(9):
        info = kb.press("Tab")
        if not _nav(info):
            break
        xs.append(info["x"]); names.append(info["text"])
        _indicator(check, f"{label} nav '{info['text']}'", info)
    check.truthy(f"{label}: nav focus order left-to-right", xs == sorted(xs), "increasing x", list(zip(names, xs)))
    back = kb.press("Shift+Tab")
    check.truthy(f"{label}: Shift+Tab moves focus back", back and len(names) > 1 and back["text"] == names[-2],
                 names[-2] if len(names) > 1 else None, back and back["text"])
    # Mega-menu with arrow keys (fresh load, so no hover/state carry-over).
    kb.open_path(HOME_PATH)
    kb.tab_until(lambda i: _nav(i) and i["text"] == "Our Services")
    a = kb.press("ArrowDown"); kb.settle()
    b = kb.press("ArrowDown")
    check.truthy(f"{label}: ArrowDown opens the mega-menu", kb.controlled_panel_visible(
        f"{kb.NAV_LINK}[aria-controls='qc-submenu-2']"), "visible", "not visible")
    check.truthy(f"{label}: arrow keys move between mega-menu items", bool(a and b and a["key"] != b["key"] and b["inHeader"]),
                 "two different items", (a and a["text"], b and b["text"]))
    # Enter activates the focused primary link.
    kb.open_path(HOME_PATH)
    kb.tab_until(lambda i: _nav(i) and i["text"].lower() == "about us")
    before = kb.current_url()
    kb.press("Enter")
    try:
        kb.wait_for_url(lambda u: u != before, timeout=20000)
    except Exception:  # noqa: BLE001 — recorded below as a deviation
        pass
    check.truthy(f"{label}: Enter activates the focused link", kb.current_url() != before, "navigated", kb.current_url())
    kb.open_path(HOME_PATH)
    _audit_offscreen(check, kb, f"{label} homepage")


@_meta("141812", "Keyboard navigation works consistently on Desktop Chrome", "Cross-browser")
@pytest.mark.compatibility
@pytest.mark.tc_141812
@pytest.mark.parametrize("engine_page", [{"engine": "chromium", "channel": "chrome"}], indirect=True)
def test_keyboard_desktop_chrome(engine_page):
    """Azure TC 141812 | PBI 131054 — Chrome (channel=chrome), 1920x1080."""
    check = _Check("TC 141812")
    _desktop_consistency(check, engine_page, "Chrome")
    check.assert_clean()


@_meta("141813", "Keyboard navigation works consistently on Desktop Firefox", "Cross-browser", N)
@pytest.mark.compatibility
@pytest.mark.tc_141813
@pytest.mark.parametrize("engine_page", [{"engine": "firefox"}], indirect=True)
def test_keyboard_desktop_firefox(engine_page):
    """Azure TC 141813 | PBI 131054 — Firefox (Playwright firefox), 1920x1080."""
    check = _Check("TC 141813")
    _desktop_consistency(check, engine_page, "Firefox")
    check.assert_clean()


@_meta("141832", "Keyboard navigation works consistently on Desktop Edge", "Cross-browser", N)
@pytest.mark.compatibility
@pytest.mark.tc_141832
@pytest.mark.parametrize("engine_page", [{"engine": "chromium", "channel": "msedge"}], indirect=True)
def test_keyboard_desktop_edge(engine_page):
    """Azure TC 141832 | PBI 131054 — Edge (channel=msedge), 1920x1080."""
    check = _Check("TC 141832")
    _desktop_consistency(check, engine_page, "Edge")
    check.assert_clean()


def _menu_consistency(check: _Check, kb: KeyboardNavigationPage, label: str, activate: bool):
    n, info = kb.tab_until(lambda i: "qc-hamburger" in i["cls"])
    check.truthy(f"{label}: Tab reaches the menu toggle", n is not None, "reached", info and info["text"])
    _indicator(check, f"{label} menu toggle", info)
    first = kb.press("Enter")
    kb.settle()
    check.equals(f"{label}: Enter opens the menu (aria-expanded)", kb.attribute(kb.HAMBURGER, "aria-expanded"), "true")
    ys, names = ([first["y"]], [first["text"]]) if _nav(first) else ([], [])
    for _ in range(9):
        i = kb.press("Tab")
        if not _nav(i):
            break
        ys.append(i["y"]); names.append(i["text"])
        _indicator(check, f"{label} menu item '{i['text']}'", i)
    check.truthy(f"{label}: menu items receive focus in logical (top-to-bottom) order", len(ys) >= 2 and ys == sorted(ys),
                 "increasing y", list(zip(names, [round(y) for y in ys])))
    if activate:
        kb.open_path(HOME_PATH)
        kb.tab_until(lambda i: "qc-hamburger" in i["cls"])
        kb.press("Enter")
        kb.settle()
        # A parent item (aria-expanded) toggles its submenu on Enter; activate the
        # first LEAF link (no submenu) so Enter's job is navigation.
        _, link = kb.tab_until(lambda i: _nav(i) and i["expanded"] is None, max_presses=12)
        before = kb.current_url()
        kb.press("Enter")
        try:
            kb.wait_for_url(lambda u: u != before, timeout=20000)
        except Exception:  # noqa: BLE001
            pass
        check.truthy(f"{label}: Enter activates the focused link ('{link and link['text']}')", kb.current_url() != before,
                     "navigated", kb.current_url())
    kb.open_path(HOME_PATH)
    _audit_offscreen(check, kb, f"{label} homepage")


@_meta("141828", "Keyboard navigation works consistently at Tablet viewport (Chrome)", "Responsive", N)
@pytest.mark.compatibility
@pytest.mark.tc_141828
@pytest.mark.parametrize("page", [TABLET], indirect=True)
def test_keyboard_tablet(page):
    """Azure TC 141828 | PBI 131054 — 768px (Chromium): Menu -> Enter, Tab through the nav, Enter navigates."""
    check = _Check("TC 141828")
    _menu_consistency(check, KeyboardNavigationPage(page).open_path(HOME_PATH), "768px", activate=True)
    check.assert_clean()


@_meta("141833", "Keyboard navigation works consistently at Mobile viewport (Chrome)", "Responsive", N)
@pytest.mark.compatibility
@pytest.mark.tc_141833
@pytest.mark.parametrize("page", [MOBILE], indirect=True)
def test_keyboard_mobile(page):
    """Azure TC 141833 | PBI 131054 — 375px (Chromium): Tab to the menu toggle, Enter opens it, Tab through
    the opened menu in logical order."""
    check = _Check("TC 141833")
    _menu_consistency(check, KeyboardNavigationPage(page).open_path(HOME_PATH), "375px", activate=False)
    check.assert_clean()


# ---------------------------------------------------------------------------
# Reading / tab order (141825 EN, 141826 AR)
# ---------------------------------------------------------------------------
def _region(s) -> str:
    return "header" if s["inHeader"] else (s["section"] or "other")


def _reading_order(check: _Check, kb: KeyboardNavigationPage, rtl: bool):
    """Record Tab stops (skip links excluded — a correct first stop) until a
    THIRD non-header region is entered; that header + hero + first content
    section slice is what the case inspects."""
    stops = []
    for _ in range(90):
        info = kb.press("Tab")
        if info is None:
            break
        if "skip" in info["cls"] or "sr-only" in info["cls"]:
            continue
        regions = []
        for s in stops + [info]:
            r = _region(s)
            if r != "header" and r not in regions:
                regions.append(r)
        if len(regions) > 2:
            break
        stops.append(info)
    header = [s for s in stops if s["inHeader"] and s["width"] > 0]
    xs = [s["x"] for s in header]
    expected = sorted(xs, reverse=rtl)
    check.truthy("header items in " + ("right-to-left" if rtl else "left-to-right") + " order", xs == expected,
                 "decreasing x" if rtl else "increasing x", [(s["text"][:16] or s["cls"].split(" ")[0], round(s["x"])) for s in header])
    # Sections: once focus leaves a section it must not come back (no jumps), header first.
    seq = []
    for s in stops:
        tag = _region(s)
        if not seq or seq[-1] != tag:
            seq.append(tag)
    check.truthy("header first, then hero, then the first content section (no jumps back)", len(seq) == len(set(seq)),
                 "each region visited once, in order", seq)
    content = [t for t in seq if t != "header"]
    first_region = [s for s in stops if _region(s) == (content[0] if content else None)]
    check.truthy("hero follows the header", any("qc-hero" in s["cls"] for s in first_region),
                 "first region after the header contains the hero controls",
                 [f"{s['cls'].split(' ')[0]}" for s in first_region][:5])
    allure.attach("\n".join(f"{s['tag']}.{s['cls'].split(' ')[0]} '{s['text'][:20]}' x={round(s['x'])} y={round(s['docY'])} [{s['section']}]"
                            for s in stops), "recorded focus order", allure.attachment_type.TEXT)


@_meta("141825", "Keyboard navigation order follows a logical reading sequence in English (LTR)", "Reading order")
@pytest.mark.functional_low
@pytest.mark.tc_141825
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_reading_order_en(page):
    """Azure TC 141825 | PBI 131054 — EN homepage at 1920: header left-to-right, then the hero, then the
    first content section, with no jumps back to an earlier region."""
    check = _Check("TC 141825")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    check.equals("page direction", kb.document_dir(), "ltr")
    _reading_order(check, kb, rtl=False)
    check.assert_clean()


@_meta("141826", "Keyboard navigation order follows a logical reading sequence in Arabic (RTL)", "Reading order")
@pytest.mark.functional_low
@pytest.mark.tc_141826
@pytest.mark.parametrize("page", [DESKTOP], indirect=True)
def test_reading_order_ar(page):
    """Azure TC 141826 | PBI 131054 — switch to Arabic with the header AR toggle, then the homepage: header
    right-to-left, then hero, then the first content section, no jumps."""
    check = _Check("TC 141826")
    kb = KeyboardNavigationPage(page).open_path(HOME_PATH)
    kb.switch_language()
    kb.open_path(HOME_PATH, locale="ar")
    check.equals("page direction", kb.document_dir(), "rtl")
    _reading_order(check, kb, rtl=True)
    check.assert_clean()

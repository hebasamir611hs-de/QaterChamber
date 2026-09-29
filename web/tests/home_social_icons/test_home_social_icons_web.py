"""
web/tests/home_social_icons/test_home_social_icons_web.py —
Web-tagged cases for PBI 129373 (QC-HOME-004B — Social Media Icons), Test
Plan 133534 / Test Suite 134451, "Frontend UI/Figma rendering" batch
(route-automation hand-off, batch 3 of 4 for this PBI; 2026-09-17).

Case IDs in scope: 131133, 131134, 131135, 131136, 131139, 131141, 131142,
131143, 131144, 131145, 131146, 131147. 131146 ("icon matches CMS-uploaded
asset") is Manual-tagged (`execution_type: Manual`, no `Automation` tag) and
is deliberately NOT authored here — Axis 1b of the tag taxonomy (Automation/
Manual, exactly one per case) forbids scripting a Manual case. This mirrors
the exact precedent already in `pytest.ini` for `tc_136367` and TC 131148 in
the sibling Control_Panel batch. 11 of the 12 handed-off cases are scripted
below.

Page Object: `web/pages/home_social_icons/home_social_icons_page.py`
(`HomeSocialIconsPage`) — the correct, dedicated container for this widget
(`div.qc-home-social`, confirmed live, distinct from the real
`<footer>`; see that module's own docstring for the architecture-fix
history). This module extends it in place with the structural/style/hover/
new-tab query surface these 11 cases need, extracted CLI-first via a
disclosed scoped Playwright script (never the Playwright MCP) — see that
Page Object's EXTENDED module docstring for the full confirmed-live findings
this batch's assertions are built on, including every literal Figma-value
mismatch found (reported honestly, never loosened to force green).

BATCH 4 OF 4 (final batch, 2026-09-17) — "Frontend Compatibility/Edge": TC
131137, 131138, 131140, 131149, 131150, 131151, 131152, 131158, 131165,
131166, 131198, 131199, 131201. 131165, 131166, 131198, 131201 are SKIPPED
with a disclosed, concrete blocker each (see their own docstrings and
pytest.ini's `tc_*` comments) — never faked as an unobserved pass. 131150
(Safari) uses a real WebKit engine launch (`core/web/browser.py`'s new
`launch_webkit_browser()`), confirmed live this session to actually launch in
this environment — not a faked browser switch, and not chromium relabeled.
131199 makes a real, temporary, CMS-side write (duplicate Display Order on
two real production rows, Facebook + LinkedIn) via
`SocialMediaIconAdminPage`, restored in `finally` via
`capture_icon_baseline()`/`restore_icon_baseline()` — same established
project pattern as `cms/tests/components/test_footer_control_panel.py`.

MID-SESSION OUTAGE: qcdev.ihorizons.com became unreachable (TCP connect
timeouts on both `curl` and Playwright) partway through this session's own
probe, after the structural/style data below was already captured live
twice (EN + AR). If the outage has not cleared by the time this batch is
run, every test below will legitimately fail/error on `open_home()` itself —
that is an environment-connectivity failure, not a locator or assertion
defect, and must be reported as such rather than reinterpreted.

ROUTING MISMATCH, flagged for the QA Manager: this batch was handed off as
"Frontend UI/Figma rendering... no CMS admin writes needed for most cases",
but TC 131141 and 131142 each open with their OWN Step 1 being a CMS
authoring action ("Configure and publish 5 icons...", "Publish Snapchat
icon with Active Status = False..."). Neither precondition holds on qcdev's
real, live, production icon set (9 active icons, not the 5/9-with-one-
inactive each case presumes), and this batch has no CMS-write mandate to
establish it. Both are scripted against the real Page Object methods this
batch built, then SKIPPED with a concrete, disclosed reason — never faked
as an unobserved pass, never silently reinterpreted to fit live data (see
automation-standards.md's Result Integrity section). A separate,
independent content observation is also recorded in each: production's own
real order/active-set does not match the case's stated example values
either, which the QA Manager may want to fold back into a CMS-authoring
batch instead.
"""

import allure
import pytest

from core.web.browser import launch_webkit_browser, new_context
from web.pages.home_social_icons.home_social_icons_page import HomeSocialIconsPage


# ── TC 131133 — Section position relative to Latest News ──────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Section position")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Social Media Icons section renders directly after the Latest News section (ADO-131133)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131133")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129373
@pytest.mark.tc_131133
def test_social_icons_section_renders_directly_after_latest_news_131133(page):
    # ADO-131133
    home = HomeSocialIconsPage(page)

    with allure.step("Load the Home page (EN) as a public visitor"):
        home.open_home()

    with allure.step("Scroll past the Latest News grid"):
        home.scroll_to_section()

    with allure.step("The Social Media Icons section appears immediately below Latest News, no gap"):
        assert home.is_immediately_below_latest_news(), (
            "expected the Social Media Icons section's top edge to sit flush against "
            "the Latest News section's bottom edge (no section rendered between them)"
        )


# ── TC 131134 — Container matches Figma desktop style ──────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Container styling (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Social Media Icons section container matches the Figma-verified desktop style (ADO-131134)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131134")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.tc_131134
def test_container_matches_figma_desktop_style_131134(page):
    """ADO-131134. Asserted against the literal Figma values the case states.
    Confirmed live this session (see HomeSocialIconsPage's EXTENDED module
    docstring): none of the 4 values match the container currently rendered
    on qcdev (padding 40px 16px vs 20px 32px stated; solid white background,
    no gradient; no border at all, not the stated 1px gradient border;
    border-radius 0px vs the stated 12px) — a genuine design/implementation
    gap on the confirmed, already-established section container, not a
    locator problem. Scripted and expected to FAIL honestly rather than
    loosened to match live rendering."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on desktop viewport (1920x1080)"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Measure the section container's padding, gap, background, border, and corner radius"):
        style = home.container_style()

    with allure.step("Compare against the Figma-verified values: padding 20px 32px; gradient background "
                      "#FBF6F8->#F6F6F6; 1px gradient border #E3C5CB->#DEDEDD; corner radius 12px"):
        assert style["padding"] == "20px 32px", f"padding: expected '20px 32px', got {style['padding']!r}"
        assert "gradient" in style["backgroundImage"], (
            f"background: expected a gradient (#FBF6F8->#F6F6F6), got backgroundImage={style['backgroundImage']!r}, "
            f"backgroundColor={style['backgroundColor']!r}"
        )
        assert style["borderWidth"] == "1px", f"border width: expected '1px', got {style['borderWidth']!r}"
        assert style["borderRadius"] == "12px", f"corner radius: expected '12px', got {style['borderRadius']!r}"


# ── TC 131135 — Heading typography ──────────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Heading typography (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('The section heading "Find us on social media" matches the Figma-verified desktop typography (ADO-131135)')
@allure.label("pbi", "129373")
@allure.label("testcase", "131135")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.tc_131135
def test_heading_matches_figma_desktop_typography_131135(page):
    """ADO-131135. Font family/weight/size/color are confirmed live to match
    the Figma-verified values exactly; line-height does not (confirmed
    28.8px live vs 32px stated) — see HomeSocialIconsPage's EXTENDED module
    docstring. Asserted literally; the line-height line is expected to FAIL
    honestly, not loosened."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on desktop viewport"):
        home.open_home()
        home.scroll_to_section()

    with allure.step('Heading "Find us on social media" is visible'):
        assert home.heading_text() == "Find us on social media"

    with allure.step("Inspect computed font styles: Cairo Bold 700, size 24px, line-height 32px, color #911731"):
        style = home.heading_style()
        assert "Cairo" in style["fontFamily"]
        assert style["fontWeight"] == "700"
        assert style["fontSize"] == "24px"
        assert style["lineHeight"] == "32px", f"line-height: expected '32px', got {style['lineHeight']!r}"
        assert style["colorHex"] == "#911731"


# ── TC 131136 — Subtext typography ──────────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Subtext typography (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section subtext matches the Figma-verified desktop typography (ADO-131136)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131136")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.tc_131136
def test_subtext_matches_figma_desktop_typography_131136(page):
    """ADO-131136. Font family/weight/size/color confirmed live to match;
    line-height does not (confirmed 27px live vs 28px stated) — see
    HomeSocialIconsPage's EXTENDED module docstring. Asserted literally."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on desktop viewport"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Subtext is visible below the heading"):
        subtext = home.subtext_text()
        assert subtext, "expected a non-empty subtext below the heading"

    with allure.step("Inspect computed font styles: Cairo Regular 400, size 18px, line-height 28px, color #6C6C6B"):
        style = home.subtext_style()
        assert "Cairo" in style["fontFamily"]
        assert style["fontWeight"] == "400"
        assert style["fontSize"] == "18px"
        assert style["lineHeight"] == "28px", f"line-height: expected '28px', got {style['lineHeight']!r}"
        assert style["colorHex"] == "#6C6C6B"


# ── TC 131139 — Icon row alignment / wrap ───────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Icon row alignment (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The icon row on desktop is right-aligned with no wrap per the Figma spec (ADO-131139)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131139")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.tc_131139
def test_icon_row_right_aligned_no_wrap_131139(page):
    """ADO-131139. `justify-content`/`gap` are confirmed live to match; the
    case's own "8 active social icons configured" precondition does not
    hold (qcdev currently renders 9 real production icons) — these 3 row-
    level CSS properties are count-independent, so the case's own literal
    assertion is scripted regardless (see HomeSocialIconsPage's EXTENDED
    module docstring). `flex-wrap` is confirmed live as `wrap`, not the
    stated `nowrap` — asserted literally, expected to FAIL honestly."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on desktop viewport with the real published social icons"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("All active icons render in a single row"):
        assert len(home.social_icon_hrefs()) > 0

    with allure.step("Measure alignment, gap, and wrap behavior: justify-content flex-end, gap 12px, flex-wrap nowrap"):
        style = home.row_style()
        assert style["justifyContent"] == "flex-end"
        assert style["gap"] == "12px"
        assert style["flexWrap"] == "nowrap", f"flex-wrap: expected 'nowrap', got {style['flexWrap']!r}"


# ── TC 131141 — Display Order (SKIPPED — unestablishable precondition) ─────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Configured Display Order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("All active, published social icons display in their configured Display Order (ADO-131141)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131141")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.uat
@pytest.mark.pbi_129373
@pytest.mark.tc_131141
@pytest.mark.skip(
    reason="ROUTING MISMATCH — TC 131141's own Step 1 is a CMS authoring action "
    "(configure/publish exactly 5 icons at Display Order 1-5), out of scope for this "
    "no-CMS-write 'Frontend UI/Figma rendering' batch. The precondition does not hold on "
    "qcdev's real production data either: 9 icons are live (not 5), and their confirmed "
    "left-to-right order is Facebook, X, LinkedIn, YouTube, Instagram, Snapchat, Flickr, "
    "Telegram, WhatsApp — positions 4/5 (YouTube, Instagram) are swapped versus the case's "
    "stated Facebook/X/LinkedIn/Instagram/YouTube. See test module docstring."
)
def test_icons_display_in_configured_order_131141(page):
    # ADO-131141 — not executed; see the skip reason above.
    pass


# ── TC 131142 — Active Status = False exclusion (SKIPPED) ──────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Active Status exclusion")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An icon with Active Status = False is not displayed on the frontend (ADO-131142)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131142")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.tc_131142
@pytest.mark.skip(
    reason="ROUTING MISMATCH — TC 131142's own Step 1 is a CMS authoring action (publish "
    "Snapchat with Active Status = False), out of scope for this no-CMS-write batch. The "
    "precondition does not hold on qcdev's real production data either: Snapchat is "
    "confirmed live as one of the 9 currently ACTIVE production icons. See test module "
    "docstring."
)
def test_inactive_icon_not_displayed_131142(page):
    # ADO-131142 — not executed; see the skip reason above.
    pass


# ── TC 131143 — Click opens configured URL in a new tab ────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Icon click behavior")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Clicking a social media icon opens the configured official URL in a new browser tab (ADO-131143)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131143")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129373
@pytest.mark.tc_131143
def test_click_icon_opens_url_in_new_tab_131143(page):
    """ADO-131143. The new-tab MECHANISM (a second tab opens; the original
    Home page tab is untouched) is asserted unconditionally. The
    destination URL is compared against the case's own literal stated
    target as a SEPARATE assertion — confirmed live this session the real
    LinkedIn href is `https://linkedin.com/company/qatarchamber` (no
    `www.`, no hyphen), not the case's stated
    `https://www.linkedin.com/company/qatar-chamber` — so a failure there
    reads as a content/config mismatch, not a broken click mechanism (see
    module docstring)."""
    home = HomeSocialIconsPage(page)
    original_url = None

    with allure.step("Load the Home page — LinkedIn icon visible"):
        home.open_home()
        home.scroll_to_section()
        linkedin_index = home.index_of_href_marker("linkedin.com")
        assert linkedin_index != -1, "expected a LinkedIn icon among the rendered social links"
        original_url = page.url

    with allure.step("Click the LinkedIn icon"):
        new_tab = home.click_icon_and_capture_new_tab(linkedin_index)

    with allure.step("A new browser tab opens; the original Home page tab remains open and unchanged"):
        assert new_tab is not None
        assert page.url == original_url, "the original Home page tab navigated away — expected it unchanged"

    with allure.step("The new tab's URL matches the configured official LinkedIn URL"):
        assert new_tab.url.rstrip("/") == "https://www.linkedin.com/company/qatar-chamber", (
            f"expected the case's stated LinkedIn target, got {new_tab.url!r}"
        )
        new_tab.close()


# ── TC 131144 — Arabic (RTL) rendering ──────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Bilingual / RTL rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Social Media Icons section renders correctly in Arabic (RTL) (ADO-131144)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131144")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129373
@pytest.mark.tc_131144
def test_section_renders_correctly_in_arabic_rtl_131144(page):
    """ADO-131144. Confirmed live this session (see HomeSocialIconsPage's
    EXTENDED module docstring): `dir="rtl"` / computed `direction: rtl`,
    and the icon row's `justify-content: flex-end` is a logical value, so
    under RTL it anchors the row to the visual LEFT — exactly what this
    case's own Step 3 expects ("row anchors to the left ... logical
    flex-end per RTL flow")."""
    home = HomeSocialIconsPage(page)

    with allure.step("Switch site language to Arabic and load the Home page"):
        home.open_home(locale="ar")
        home.scroll_to_section()

    with allure.step("Section is visible with Arabic heading/subtext"):
        assert home.page_direction() == "rtl"
        assert home.section_direction() == "rtl"
        subtext = home.subtext_text()
        assert subtext, "expected a non-empty Arabic subtext"

    with allure.step("Heading/subtext are right-aligned; icon row anchors left (logical flex-end under RTL); "
                      "no clipped/overlapping text; no horizontal overflow"):
        heading_style = home.heading_style()
        subtext_style = home.subtext_style()
        assert heading_style["textAlign"] in ("start", "right"), heading_style
        assert subtext_style["textAlign"] in ("start", "right"), subtext_style
        assert home.icon_row_horizontal_position() == "left_half"
        assert home.is_no_horizontal_overflow()


# ── TC 131145 — English (LTR) rendering ─────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Bilingual / LTR rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Social Media Icons section renders correctly in English (LTR) (ADO-131145)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131145")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_129373
@pytest.mark.tc_131145
def test_section_renders_correctly_in_english_ltr_131145(page):
    """ADO-131145. Confirmed live this session (see HomeSocialIconsPage's
    EXTENDED module docstring): `dir="ltr"` / computed `direction: ltr`,
    and the icon row's `justify-content: flex-end` anchors it to the
    visual RIGHT under LTR — exactly this case's own stated expectation
    ("icon row is right-anchored per the desktop spec")."""
    home = HomeSocialIconsPage(page)

    with allure.step("Switch site language to English and load the Home page"):
        home.open_home(locale="en")
        home.scroll_to_section()

    with allure.step("Section is visible with English heading/subtext"):
        assert home.page_direction() == "ltr"
        assert home.section_direction() == "ltr"
        assert home.heading_text() == "Find us on social media"

    with allure.step("Heading/subtext are left-aligned; icon row is right-anchored; "
                      "no clipped/overlapping text"):
        heading_style = home.heading_style()
        subtext_style = home.subtext_style()
        assert heading_style["textAlign"] in ("start", "left"), heading_style
        assert subtext_style["textAlign"] in ("start", "left"), subtext_style
        assert home.icon_row_horizontal_position() == "right_half"
        assert home.is_no_horizontal_overflow()


# ── TC 131147 — Hover state ─────────────────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Hover / focus state")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hovering over a social icon on desktop shows a visible hover/focus state (ADO-131147)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131147")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.pbi_129373
@pytest.mark.tc_131147
def test_hover_shows_visible_state_131147(page):
    """ADO-131147. Confirmed live this session (see HomeSocialIconsPage's
    EXTENDED module docstring): hover swaps background/foreground color
    (white<->#911731) and applies a small lift (translateY(-2px)) — a
    real, distinct, observable state change, not merely "hover fires"."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load the Home page on desktop"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Cursor is a pointer over the icon"):
        style_change = home.hover_icon_style_change(0)
        assert style_change["before"]["cursor"] == "pointer"

    with allure.step("The icon shows a distinct hover state (color/background/transform change)"):
        before, after = style_change["before"], style_change["after"]
        assert before != after, f"expected a visible style change on hover, got identical before/after: {before!r}"
        assert (
            before["color"] != after["color"]
            or before["backgroundColor"] != after["backgroundColor"]
            or before["transform"] != after["transform"]
        ), "expected color, background, or transform to change on hover"


# ═══════════════════════════════════════════════════════════════════════════
# BATCH 4 OF 4 — "Frontend Compatibility/Edge" (final batch, 2026-09-17)
# ═══════════════════════════════════════════════════════════════════════════

# ── TC 131137 — Mobile heading typography ──────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Mobile typography (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section heading matches the Figma-verified mobile typography (ADO-131137)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131137")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131137
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_heading_matches_figma_mobile_typography_131137(page):
    """ADO-131137. Real 375px-wide viewport. Batch 3 only measured the
    desktop (1920px) heading; the case's own mobile values (Cairo Bold 700,
    20px, line-height 30px, #911731) were never independently confirmed live
    at 375px before this run — asserted literally, reported honestly on
    whichever way it lands."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on a 375px-wide mobile viewport"):
        home.open_home()
        home.scroll_to_section()

    with allure.step('Heading "Find us on social media" is visible'):
        assert home.heading_text() == "Find us on social media"

    with allure.step("Inspect computed font styles: Cairo Bold 700, size 20px, line-height 30px, color #911731"):
        style = home.heading_style()
        assert "Cairo" in style["fontFamily"]
        assert style["fontWeight"] == "700", f"font-weight: expected '700', got {style['fontWeight']!r}"
        assert style["fontSize"] == "20px", f"font-size: expected '20px', got {style['fontSize']!r}"
        assert style["lineHeight"] == "30px", f"line-height: expected '30px', got {style['lineHeight']!r}"
        assert style["colorHex"] == "#911731", f"color: expected '#911731', got {style['colorHex']!r}"


# ── TC 131138 — Mobile subtext typography ──────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Mobile typography (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The section subtext matches the Figma-verified mobile typography (ADO-131138)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131138")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131138
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_subtext_matches_figma_mobile_typography_131138(page):
    """ADO-131138. Real 375px-wide viewport, asserted literally against the
    case's own stated mobile values (Cairo Regular 400, 14px, line-height
    22px, #6C6C6B) — never independently confirmed live at this viewport
    before this run."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on a 375px-wide mobile viewport"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Subtext is visible"):
        subtext = home.subtext_text()
        assert subtext, "expected a non-empty subtext"

    with allure.step("Inspect computed font styles: Cairo Regular 400, size 14px, line-height 22px, color #6C6C6B"):
        style = home.subtext_style()
        assert "Cairo" in style["fontFamily"]
        assert style["fontWeight"] == "400", f"font-weight: expected '400', got {style['fontWeight']!r}"
        assert style["fontSize"] == "14px", f"font-size: expected '14px', got {style['fontSize']!r}"
        assert style["lineHeight"] == "22px", f"line-height: expected '22px', got {style['lineHeight']!r}"
        assert style["colorHex"] == "#6C6C6B", f"color: expected '#6C6C6B', got {style['colorHex']!r}"


# ── TC 131140 — Mobile icon row center-align / wrap ────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Mobile layout (Figma-verified)")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The icon row on mobile is center-aligned and wraps per the Figma spec (ADO-131140)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131140")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.ui
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131140
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_icon_row_center_aligned_wraps_on_mobile_131140(page):
    """ADO-131140. The case's own "8 active social icons configured"
    precondition does not hold (qcdev renders 9 real production icons) —
    `justify-content`/`gap`/`flex-wrap` are count-independent (same reasoning
    as TC 131139's own desktop equivalent), asserted regardless. "No icon
    clipped or overlapping" is checked via real per-icon bounding-box
    geometry (`has_overlapping_or_clipped_icons()`), not a screenshot diff."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on a 375px-wide mobile viewport with the real published social icons"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Icons render, one row container"):
        assert len(home.social_icon_hrefs()) > 0

    with allure.step("Measure alignment, gap, and wrap behavior: justify-content center, gap 12px, flex-wrap wrap"):
        style = home.row_style()
        assert style["justifyContent"] == "center", f"justify-content: expected 'center', got {style['justifyContent']!r}"
        assert style["gap"] == "12px", f"gap: expected '12px', got {style['gap']!r}"
        assert style["flexWrap"] == "wrap", f"flex-wrap: expected 'wrap', got {style['flexWrap']!r}"

    with allure.step("No icon is clipped (outside the 375px viewport) or overlapping another"):
        assert not home.has_overlapping_or_clipped_icons(viewport_width=375)


# ── TC 131149 — Chrome (Chromium engine) desktop rendering ─────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Cross-browser rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Social Media Icons section renders correctly in Chrome (latest) on desktop (ADO-131149)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131149")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131149
def test_section_renders_correctly_in_chrome_desktop_131149(page):
    """ADO-131149. This project's `page` fixture already launches the real
    Chromium engine (`core/web/browser.py`'s `launch_browser()`) at the
    default desktop viewport — the Chrome/Chromium distinction is branding
    only, not a rendering-engine difference; no separate browser needed
    (contrast TC 131150, which genuinely needs a distinct engine, WebKit)."""
    home = HomeSocialIconsPage(page)

    with allure.step("Open the Home page on desktop — page loads without errors"):
        home.open_home()

    with allure.step("Scroll to the Social Media Icons section — renders per the desktop spec"):
        home.scroll_to_section()
        hrefs = home.social_icon_hrefs()
        assert len(hrefs) > 0, "expected at least one rendered social icon"
        assert not home.has_overlapping_or_clipped_icons()

    with allure.step("Icons are clickable and open new tabs as expected"):
        new_tab = home.click_icon_and_capture_new_tab(0)
        assert new_tab is not None
        assert new_tab.url != "about:blank"
        new_tab.close()


# ── TC 131150 — Safari (WebKit engine) desktop rendering ───────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Cross-browser rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Social Media Icons section renders correctly in Safari on desktop (ADO-131150)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131150")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131150
def test_section_renders_correctly_in_safari_desktop_131150(playwright_instance):
    """ADO-131150. A real WebKit engine launch (`launch_webkit_browser()`,
    confirmed live this session to actually launch here) — the genuine open-
    source engine Safari itself is built on, not chromium relabeled and not
    faked. No branded Safari.app exists on this (non-macOS) environment, so
    WebKit is the closest achievable real equivalent — see module docstring
    and `core/web/browser.py`'s own docstring for that engine. Does not use
    the shared `page`/`browser` fixtures (those are pinned to Chromium) — a
    local, self-contained WebKit browser/context/page, closed in `finally`."""
    browser = launch_webkit_browser(playwright_instance)
    context = new_context(browser)
    page = context.new_page()
    try:
        home = HomeSocialIconsPage(page)

        with allure.step("Open the Home page in WebKit on desktop — page loads without errors"):
            home.open_home()

        with allure.step("Scroll to the Social Media Icons section — no font-fallback or gradient rendering issues"):
            home.scroll_to_section()
            hrefs = home.social_icon_hrefs()
            assert len(hrefs) > 0, "expected at least one rendered social icon"
            assert not home.has_overlapping_or_clipped_icons()

        with allure.step("Icons are clickable and open new tabs as expected"):
            new_tab = home.click_icon_and_capture_new_tab(0)
            assert new_tab is not None
            assert new_tab.url != "about:blank"
            new_tab.close()
    finally:
        context.close()
        browser.close()


# ── TC 131151 — Tablet-width viewport rendering ────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Viewport rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Social Media Icons section renders correctly on a tablet-width viewport (ADO-131151)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131151")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131151
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_section_renders_correctly_on_tablet_viewport_131151(page):
    """ADO-131151. The case itself only commits to "the mobile center/wrap
    pattern (or a documented intermediate pattern once confirmed)" — so no
    literal `justify-content` value is asserted here (that would invent a
    spec the case doesn't state); the measured value is recorded as evidence
    instead. The hard, literal parts of the case (no overlap/clipping, no
    errors) are asserted."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load the Home page at a 768px-wide viewport — page loads without errors"):
        home.open_home()

    with allure.step("Scroll to the Social Media Icons section — renders without overlap or clipping"):
        home.scroll_to_section()
        hrefs = home.social_icon_hrefs()
        assert len(hrefs) > 0, "expected at least one rendered social icon"
        assert not home.has_overlapping_or_clipped_icons(viewport_width=768)

    with allure.step("Record the measured icon-row alignment/wrap behavior at this viewport"):
        style = home.row_style()
        allure.attach(
            f"justify-content={style['justifyContent']!r}, gap={style['gap']!r}, flex-wrap={style['flexWrap']!r}",
            name="Measured tablet row style (131151 — no literal spec stated by the case)",
        )
        assert home.is_no_horizontal_overflow()


# ── TC 131152 — Dark mode rendering ─────────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Dark mode rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Social Media Icons section renders correctly under the site's dark mode variant (ADO-131152)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131152")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.compatibility
@pytest.mark.pbi_129373
@pytest.mark.tc_131152
def test_section_renders_correctly_in_dark_mode_131152(page):
    """ADO-131152. The case names no specific dark-mode token values (unlike
    131134's own literal Figma numbers) — asserted here as: dark mode
    genuinely activates (`data-theme="dark"`, condition-waited, not slept),
    and the section's own container/heading/subtext colors actually change
    from their light-mode reads (real, distinct dark-mode styling, not a
    no-op) while text stays visible/non-empty (a basic legibility control)."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load the Home page"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Capture light-mode colors before toggling"):
        light_container = home.container_style()
        light_heading = home.heading_style()
        light_subtext = home.subtext_style()

    with allure.step("Enable dark mode (site-wide toggle)"):
        home.enable_dark_mode()
        assert home.is_dark_mode_active()

    with allure.step("Section colors switch to the dark-mode variant; text remains legible/visible"):
        dark_container = home.container_style()
        dark_heading = home.heading_style()
        dark_subtext = home.subtext_style()
        assert (
            dark_container["backgroundColor"] != light_container["backgroundColor"]
            or dark_heading["color"] != light_heading["color"]
            or dark_subtext["color"] != light_subtext["color"]
        ), "expected at least one section color to change under dark mode"
        assert home.heading_text(), "expected the heading to remain visible/non-empty under dark mode"
        assert home.subtext_text(), "expected the subtext to remain visible/non-empty under dark mode"


# ── TC 131158 — End-to-end visitor flow ─────────────────────────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("End-to-end visitor flow")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A public visitor can view and follow Qatar Chamber's social channels end-to-end (ADO-131158)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131158")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.pbi_129373
@pytest.mark.tc_131158
def test_visitor_can_view_and_follow_social_channels_end_to_end_131158(page):
    """ADO-131158. Composed entirely from this Page Object's own existing
    primitives (open/scroll/click/new-tab), no new mechanism. The case
    states "6 active icons"; live is 9 (count-independent, same reasoning as
    131139/131140) — the count itself is not asserted literally, only that
    Instagram is among the rendered icons. The new tab's destination is
    compared against the href actually READ off the DOM (the case's own
    "exact configured URL"), never a hardcoded literal."""
    home = HomeSocialIconsPage(page)
    original_url = None

    with allure.step("Load the Home page as an unauthenticated visitor"):
        home.open_home()

    with allure.step("Scroll past Latest News to the Social Media Icons section — visible with active icons"):
        home.scroll_to_section()
        instagram_index = home.index_of_href_marker("instagram.com")
        assert instagram_index != -1, "expected an Instagram icon among the rendered social links"
        expected_href = home.social_icon_hrefs()[instagram_index]
        original_url = page.url

    with allure.step("Click the Instagram icon"):
        new_tab = home.click_icon_and_capture_new_tab(instagram_index)

    with allure.step("A new browser tab opens, navigating to the exact configured Instagram URL; "
                      "the original Home page tab is unaffected"):
        assert new_tab is not None
        assert new_tab.url.rstrip("/") == expected_href.rstrip("/"), (
            f"expected the new tab to navigate to the configured href {expected_href!r}, got {new_tab.url!r}"
        )
        assert page.url == original_url, "the original Home page tab navigated away — expected it unchanged"
        new_tab.close()


# ── TC 131165 — All icons inactive hides section (SKIPPED) ─────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Edge case — all icons inactive")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Social Media Icons section is hidden entirely when all configured icons are inactive (ADO-131165)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131165")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.pbi_129373
@pytest.mark.tc_131165
@pytest.mark.skip(
    reason="Same class of destructive-operations gap already on record for tc_131203 "
    "(pytest.ini): this case's own precondition requires deactivating/unpublishing ALL 9 "
    "real production social icon entries. Those 9 entries live on a CMS object CONFIRMED "
    "SHARED with the real public <footer> (footer_admin_component.py's LOAD-BEARING "
    "FINDING #1) — deactivating them all would take the real site-wide footer down too, "
    "not just this Home widget, on an environment with a documented ~30s session-drop "
    "failure mode mid-restore. Requires explicit, ID-based human confirmation before any "
    "such irreversible change to real qcdev content — flagged to the QA Manager, not "
    "invented around."
)
def test_section_hidden_when_all_icons_inactive_131165(page):
    # ADO-131165 — not executed; see the skip reason above.
    pass


# ── TC 131166 — Section load failure isolation (SKIPPED) ───────────────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Edge case — load-failure isolation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A Social Media Icons section load failure does not affect the rest of the Home page (ADO-131166)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131166")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.functional_high
@pytest.mark.pbi_129373
@pytest.mark.tc_131166
@pytest.mark.skip(
    reason="Confirmed live this session (raw HTML fetch of qcdev's Home page) that "
    "div.qc-home-social's own content — including all real icon links — is fully "
    "SERVER-RENDERED (present in the raw HTML response itself), with no distinct "
    "client-side fetch/XHR for this widget's own data to intercept/abort via "
    "page.route(). The case's own Step 1 precondition ('corrupt/orphaned icon "
    "reference') is therefore a server-side CMS data condition, not something reachable "
    "client-side — inducing it for real would mean corrupting real production CMS "
    "content, out of scope and not attempted."
)
def test_section_load_failure_does_not_affect_rest_of_home_page_131166(page):
    # ADO-131166 — not executed; see the skip reason above.
    pass


# ── TC 131198 — Last remaining active icon hides section (SKIPPED) ─────────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Edge case — last active icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Toggling the last remaining active+published icon to Inactive hides the entire section (ADO-131198)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131198")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131198
@pytest.mark.skip(
    reason="Same destructive-operations gap as tc_131165/tc_131203: this case's own "
    "precondition requires first deactivating/unpublishing 8 of the 9 real production "
    "icons (down to exactly one), then deactivating that last one too — on the CMS "
    "object CONFIRMED SHARED with the real public <footer>, taking it down site-wide. "
    "Requires explicit, ID-based human confirmation before any such irreversible change "
    "to real qcdev content — flagged to the QA Manager, not invented around."
)
def test_toggling_last_active_icon_hides_section_131198(page):
    # ADO-131198 — not executed; see the skip reason above.
    pass


# ── TC 131199 — Duplicate Display Order renders without breaking layout ────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Edge case — duplicate Display Order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Two icons sharing the same Display Order value render without breaking the icon row layout (ADO-131199)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131199")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131199
@pytest.mark.xdist_group("smi_production_rows")
def test_duplicate_display_order_renders_without_breaking_layout_131199(page, browser):
    """ADO-131199. A real, temporary CMS write on TWO real production rows
    (Facebook, LinkedIn) — never a throwaway QCTEST entry (the case itself
    names real platforms already live). LinkedIn's Display Order is set to
    Facebook's own real current value (read live, not hardcoded), producing
    a genuine duplicate regardless of qcdev's current numbers. Both baselines
    are captured up front and restored in `finally`, unconditionally. The
    public-frontend read uses a SEPARATE anonymous context
    (`new_context(browser, use_auth_state=False)`), never the CMS-authenticated
    `page` — mirrors `test_footer_control_panel.py`'s own established
    two-surface pattern (never reads "public" state off an authed session)."""
    from cms.pages.components.footer_admin_component import (
        PRODUCTION_ENTRY_CODES,
        SocialMediaIconAdminPage,
    )

    admin = SocialMediaIconAdminPage(page)
    admin.open_icons_list()
    facebook_code = PRODUCTION_ENTRY_CODES["Facebook"]
    linkedin_code = PRODUCTION_ENTRY_CODES["LinkedIn"]
    baseline_facebook = admin.capture_icon_baseline(facebook_code)
    baseline_linkedin = admin.capture_icon_baseline(linkedin_code)

    try:
        with allure.step('Configure "LinkedIn" with the SAME Display Order as "Facebook" and publish'):
            admin.open_entry_by_code(linkedin_code)
            admin.fill_icon_form(display_order=baseline_facebook["display_order"])
            admin.save()
            assert admin.display_order_value() == baseline_facebook["display_order"]

        with allure.step("Both icons render in the row in a stable, non-overlapping, non-broken layout"):
            anon_ctx = new_context(browser, use_auth_state=False)
            anon_page = anon_ctx.new_page()
            try:
                home = HomeSocialIconsPage(anon_page)
                home.open_home()
                home.scroll_to_section()
                assert home.has_icon_with_href_marker("facebook.com/qatarchamber")
                assert home.has_icon_with_href_marker("linkedin.com/company/qatarchamber")
                assert not home.has_overlapping_or_clipped_icons()
                assert home.is_no_horizontal_overflow()
            finally:
                anon_ctx.close()
    finally:
        admin.restore_icon_baseline(baseline_linkedin)
        admin.restore_icon_baseline(baseline_facebook)
        admin.open_entry_by_code(linkedin_code)
        assert admin.display_order_value() == baseline_linkedin["display_order"], (
            "Teardown restore did not persist: LinkedIn Display Order"
        )


# ── TC 131201 — Broken external URL still renders/navigates (SKIPPED) ──────
@allure.epic("Home Page")
@allure.feature("Social Media Icons Section")
@allure.story("Edge case — broken external URL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An icon whose external Platform URL is broken still renders and attempts navigation (ADO-131201)")
@allure.label("pbi", "129373")
@allure.label("testcase", "131201")
@pytest.mark.web
@pytest.mark.global_
@pytest.mark.edge
@pytest.mark.pbi_129373
@pytest.mark.tc_131201
@pytest.mark.skip(
    reason="BLOCKED by ADO Bug #142266 (CMS image-upload picker broken server-side, "
    "confirmed live in batch 2 — see footer_admin_component.py's module docstring). "
    "This case's own Step 1 requires configuring and publishing a NEW icon entry; "
    "Social Icon Image is a MANDATORY field on this object's create form "
    "(_required_field_locators() includes it), so a new publishable entry cannot "
    "currently be created at all. Not worked around by editing one of the 9 real "
    "production rows' own URL to a broken value either, per this task's explicit "
    "instruction never to touch those destructively."
)
def test_broken_external_url_still_renders_and_navigates_131201(page):
    # ADO-131201 — not executed; see the skip reason above.
    pass

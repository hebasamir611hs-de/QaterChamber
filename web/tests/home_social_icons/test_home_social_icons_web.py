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

UPDATE 2026-10-21 (QA lead decision): 131142 now RUNS on a disposable
`QCTEST-131142-snap-*` record (web/tests/conftest.py `qctest_records`,
cms/pages/components/qctest_record_admin.py), with a positive control -- see
that test's docstring. 131141 is unchanged.
"""

import json
import uuid

import allure
import pytest

from cms.pages.components.qctest_record_admin import PNG_FIXTURE as QCTEST_PNG, SocialIconQctest
from core.web.browser import launch_webkit_browser, new_context
from core.web.design_tokens import px_close
from web.pages.home_social_icons.home_social_icons_page import HomeSocialIconsPage

# Real Social Media Icon rows for the 2026-10-21 reversible-write cases (131141, 131198).
_SMI_OBJ = {"slug": "social-media-icon", "plural": "socialmediaicons"}
_SMI_ACTIVE = {**_SMI_OBJ, "label": "Active Status", "api_field": "activeStatus"}


def _poll_public(predicate, timeout: float = 180.0, poll: float = 10.0) -> bool:
    """Public propagation poll (QA lead: a change landing within 3 min is fine)."""
    from core.utils.waits import WaitTimeoutError, wait_until

    try:
        wait_until(predicate, timeout=timeout, poll=poll)
        return True
    except WaitTimeoutError:
        return False

# bug-rules.md Rule 1: layout (non-image, non-text) geometry is compared at
# ±2 px against Figma; text properties (font size, line height) stay exact.
LAYOUT_TOLERANCE_PX = 2


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

    RETARGETED 2026-10-21: the Figma container is the INNER card
    (`div.qc-social-panel` — rounded, tinted 1px border, gradient fill), not
    the full-width outer wrapper `div.qc-home-social` this test previously
    measured (its 40px 16px padding is the page band, not the card). Layout
    values (padding, border width, corner radius) use the project's ±2 px
    layout tolerance (bug-rules.md Rule 1); the expected Figma values are
    unchanged."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on desktop viewport (1920x1080)"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("Measure the section card's padding, background, border, and corner radius"):
        style = home.card_style()

    with allure.step("Compare against the Figma-verified values (±2 px layout tolerance): padding 20px 32px; "
                      "gradient background #FBF6F8->#F6F6F6; 1px gradient border #E3C5CB->#DEDEDD; "
                      "corner radius 12px"):
        padding = (style["paddingTop"], style["paddingRight"], style["paddingBottom"], style["paddingLeft"])
        for side, actual, expected in zip(("top", "right", "bottom", "left"), padding,
                                          ("20px", "32px", "20px", "32px")):
            assert px_close(actual, expected, tolerance=LAYOUT_TOLERANCE_PX), (
                f"padding-{side}: expected {expected} (±{LAYOUT_TOLERANCE_PX}px), got {actual!r}"
            )
        assert "gradient" in style["backgroundImage"], (
            f"background: expected a gradient (#FBF6F8->#F6F6F6), got backgroundImage={style['backgroundImage']!r}, "
            f"backgroundColor={style['backgroundColor']!r}"
        )
        assert px_close(style["borderTopWidth"], "1px", tolerance=LAYOUT_TOLERANCE_PX), (
            f"border width: expected '1px' (±{LAYOUT_TOLERANCE_PX}px), got {style['borderTopWidth']!r}"
        )
        assert px_close(style["borderRadius"], "12px", tolerance=LAYOUT_TOLERANCE_PX), (
            f"corner radius: expected '12px' (±{LAYOUT_TOLERANCE_PX}px), got {style['borderRadius']!r}"
        )


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
    """ADO-131139. The case's behaviour is "icons on one row, right-aligned,
    no wrap". REWORKED 2026-10-21: asserted as rendered behaviour, not the
    `flex-wrap` CSS property (the row declares `flex-wrap: wrap`, which is
    an implementation choice — whether icons actually wrap is what the case
    is about). One row = every icon's top within ±2 px of the first icon's;
    right-aligned = the last icon's right edge within ±2 px of the card's
    content right edge (bug-rules.md Rule 1 layout tolerance).
    `justify-content`/`gap` are kept as stated Figma values. The case's
    "8 active social icons" precondition does not hold (qcdev renders 9
    real icons); the checks are count-independent."""
    home = HomeSocialIconsPage(page)

    with allure.step("Load Home page on desktop viewport with the real published social icons"):
        home.open_home()
        home.scroll_to_section()

    with allure.step("All active icons render in a single row (no wrap)"):
        boxes = home.icon_bounding_boxes()
        assert boxes and all(boxes), f"expected rendered icon boxes, got {boxes!r}"
        first_top = boxes[0]["y"]
        tops = [round(b["y"], 1) for b in boxes]
        assert all(abs(b["y"] - first_top) <= LAYOUT_TOLERANCE_PX for b in boxes), (
            f"expected all {len(boxes)} icons on one row (tops within ±{LAYOUT_TOLERANCE_PX}px), got tops={tops}"
        )

    with allure.step("The icon row is right-aligned within the card"):
        last = max(boxes, key=lambda b: b["x"] + b["width"])
        icons_right = last["x"] + last["width"]
        card_right = home.card_content_right_edge()
        assert abs(icons_right - card_right) <= LAYOUT_TOLERANCE_PX, (
            f"expected the last icon's right edge at the card's content edge {card_right:.1f}px "
            f"(±{LAYOUT_TOLERANCE_PX}px), got {icons_right:.1f}px"
        )

    with allure.step("Row alignment and gap: justify-content flex-end, gap 12px"):
        style = home.row_style()
        assert style["justifyContent"] == "flex-end"
        assert style["gap"] == "12px"


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
@pytest.mark.xdist_group("smi_production_rows")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_icons_display_in_configured_order_131141(page, real_records):
    """ADO-131141 | PBI 129373.

    Precondition (QA lead instruction 2026-10-21, reversible real writes):
    "exactly 5 active icons at Display Order 1-5". qcdev holds 9 real
    Published + Active icons whose Home Display Order is 1..8 and 700, so
    the minimum change is to untick Active Status on every active icon
    OUTSIDE Home Display Order 1-5 (4 on 2026-10-21: WhatsApp 46165,
    Telegram 46181, Snapchat 46197, Flickr 135360) -- no order is edited,
    no QCTEST record is needed. Saved TEST_USER session (admin; the Editor
    login was locked that day; a content precondition, not a workflow
    case). Snapshot + screenshot first; `real_records` re-ticks and verifies
    each in teardown. Public reads: fresh logged-out `page`."""
    home = HomeSocialIconsPage(page)

    with allure.step("Baseline (logged out): the Home social section renders"):
        home.open_home_settled()
        assert home.is_section_displayed(), "baseline: Home social section not rendered before the change"

    with allure.step("CMS: leave exactly 5 active icons, at Home Display Order 1-5, published"):
        items = real_records.items(**_SMI_OBJ)
        keep = sorted((i for i in items if i.get("activeStatus") and i.get("homeDisplayOrder") in (1, 2, 3, 4, 5)),
                      key=lambda i: i["homeDisplayOrder"])
        assert [i["homeDisplayOrder"] for i in keep] == [1, 2, 3, 4, 5], (
            f"precondition: active icons at Home Display Order 1-5 are "
            f"{[(i['platformName'], i['homeDisplayOrder']) for i in keep]}")
        assert all(i.get("showOnHome") for i in keep), "precondition: an order 1-5 icon is not Show on Home"
        keep_codes = [i["externalReferenceCode"] for i in keep]
        extra = [i["externalReferenceCode"] for i in items
                 if i.get("activeStatus") and i["externalReferenceCode"] not in keep_codes]
        for code in extra:
            real_records.change(code=code, value=False, **_SMI_ACTIVE)
        still = real_records.codes_where(_SMI_OBJ["slug"], _SMI_OBJ["plural"], "activeStatus", True)
        assert sorted(still) == sorted(keep_codes), f"precondition not reached: {still}"
        expected = [i["redirectUrl"] for i in keep]
        configured = [(i["platformName"], i["homeDisplayOrder"]) for i in keep]

    with allure.step("Navigate to the Home page (logged out), polled up to 3 min"):
        seen = {"hrefs": []}

        def _five_rendered() -> bool:
            home.open_home_settled()
            seen["hrefs"] = home.social_icon_hrefs() if home.is_section_displayed() else []
            return len(seen["hrefs"]) == 5

        _poll_public(_five_rendered)
        allure.attach(json.dumps({"configured": configured, "expected_hrefs": expected,
                                  "rendered_hrefs": seen["hrefs"]}, ensure_ascii=False, indent=1),
                      name="131141 order evidence", attachment_type=allure.attachment_type.JSON)

    # Assert
    assert seen["hrefs"] == expected, (
        f"expected the 5 icons in Display Order {configured} -> {expected}; rendered {seen['hrefs']}")


# ── TC 131142 — Active Status = False exclusion (QCTEST record, 2026-10-21) ──────────────────
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
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_inactive_icon_not_displayed_131142(page, qctest_records):
    """ADO-131142 | PBI 129373.

    Precondition (QA lead decision 2026-10-21): a disposable Snapchat icon
    record (`QCTEST-131142-snap-*`, Show on Home ticked, Active Status
    UNticked) Published through Object Authoring as TEST_USER (admin; Publish
    goes live directly -- the Editor login was refused that day), deleted in
    teardown. DATA ADAPTATION: qcdev has 9 real Published + Active icons (the
    real Snapchat among them), not the case's "4 active + Snapchat" -- so
    "Snapchat does not appear" is asserted for THIS record (its unique
    redirect href), and the real icons are the "active icons still render"
    half. POSITIVE CONTROL: the same record is then ticked Active and must
    appear, proving the absence was the Active gate and not a record the
    Home strip could never render. Public reads: fresh logged-out `page`."""
    tag = uuid.uuid4().hex[:6]
    marker = f"QCTEST-131142-snap-{tag}"
    href_marker = f"qctest-131142-{tag}"
    href = f"https://snapchat.com/add/{href_marker}"
    admin = SocialIconQctest(qctest_records.page)
    home = HomeSocialIconsPage(page)

    with allure.step("Publish Snapchat icon with Active Status = False alongside the active icons"):
        code = qctest_records.create(admin, {
            "platform": "Snapchat",
            "image": QCTEST_PNG,
            "alt": (marker, f"{marker} سناب"),
            "url": (href, href),
            "new_tab": True,
            "order": "9900",
            "show_on_home": True,
            "home_order": "9900",
            "active": False,
            "platform_name": ("QCTEST Snapchat", "QCTEST سناب شات"),
        }, marker)
        active_saved = admin.active_of(code)
        show_on_home_saved = admin.flag("show_on_home")
        badge = admin.row_badge(code)

    with allure.step("Load the Home page (logged out) and inspect the rendered icon row"):
        home.open_home()
        hrefs_inactive = home.social_icon_hrefs()

    with allure.step("Positive control: tick Active on the same record, the icon must now render"):
        qctest_records.set_active(admin, code, marker, True)
        appeared = home.reload_until(lambda p: p.has_icon_with_href_marker(href_marker), timeout_ms=180000)
        hrefs_active = home.social_icon_hrefs()

    allure.attach(f"record={code} badge={badge} active_saved={active_saved} show_on_home={show_on_home_saved}\n"
                  f"inactive hrefs={hrefs_inactive}\nafter-activation hrefs={hrefs_active}",
                  name="131142 evidence", attachment_type=allure.attachment_type.TEXT)

    # Assert
    assert active_saved is False and show_on_home_saved is True, (active_saved, show_on_home_saved)
    assert badge in ("INACTIVE", "PUBLISHED"), f"expected the entry saved as Published/Inactive, badge {badge!r}"
    assert any("wa.me/97444559111" in h for h in hrefs_inactive), "positive control: real active icons not rendered"
    assert not any(href_marker in h for h in hrefs_inactive), (
        f"the Active Status = False QCTEST Snapchat icon rendered on the Home page: {hrefs_inactive}")
    assert appeared, ("inconclusive: the same QCTEST icon never rendered even after Active was ticked "
                      f"(3 min), so its absence above cannot be attributed to Active Status: {hrefs_active}")


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
@pytest.mark.xdist_group("smi_production_rows")
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_toggling_last_active_icon_hides_section_131198(page, real_records):
    """ADO-131198 | PBI 129373.

    Precondition (QA lead instruction 2026-10-21, reversible real writes):
    exactly ONE active + published icon. Every other active real icon (8 on
    2026-10-21) gets Active Status unticked; Facebook (46085) is kept as the
    last one and is then unticked too -- the case's own action. The Social
    Media Icon object also feeds the global footer, so its icons are gone
    site-wide for the short window this test holds. Saved TEST_USER session
    (the Editor login was locked that day; a content precondition, not a
    workflow case). Snapshot + screenshot first; `real_records` re-ticks and
    verifies every icon in teardown. Public reads: fresh logged-out `page`."""
    home = HomeSocialIconsPage(page)

    with allure.step("Baseline (logged out): the Home social section renders"):
        home.open_home_settled()
        assert home.is_section_displayed(), "baseline: Home social section not rendered before the change"

    with allure.step("Precondition: only ONE icon remains active + published"):
        active = real_records.codes_where(_SMI_OBJ["slug"], _SMI_OBJ["plural"], "activeStatus", True, status="approved")
        last = "QC-SMI-facebook" if "QC-SMI-facebook" in active else active[0]
        for code in [c for c in active if c != last]:
            real_records.change(code=code, value=False, **_SMI_ACTIVE)
        last_href = next(i["redirectUrl"] for i in real_records.items(**_SMI_OBJ)
                         if i["externalReferenceCode"] == last)
        seen = {"hrefs": []}

        def _only_last() -> bool:
            home.open_home_settled()
            seen["hrefs"] = home.social_icon_hrefs() if home.is_section_displayed() else []
            return seen["hrefs"] == [last_href]

        assert _poll_public(_only_last), (
            f"precondition: expected only {last_href} on the Home section, rendered {seen['hrefs']}")

    with allure.step(f"In CMS, set the last active icon ({last}) to Inactive and publish"):
        real_records.change(code=last, value=False, **_SMI_ACTIVE)

    with allure.step("Reload the Home page (logged out), polled up to 3 min"):
        def _hidden() -> bool:
            home.open_home_settled()
            return not home.is_section_displayed()

        hidden = _poll_public(_hidden)
        allure.attach(json.dumps({"section_nodes": home.section_node_count(),
                                  "rendered_hrefs": home.social_icon_hrefs()}),
                      name="131198 evidence", attachment_type=allure.attachment_type.JSON)

    # Assert
    assert hidden, (f"expected the whole social section hidden with zero active icons; "
                    f"section nodes={home.section_node_count()}, icons={home.social_icon_hrefs()}")


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

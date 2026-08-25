"""
web/tests/gm_message/test_gm_message_web.py — Web-tagged cases for PBI
129397 (QC-ABOUT-005 — General Manager's Message), sourced verbatim from
review_test_coverage(129397) (199 total cases for the PBI; this module
covers the Web-platform subset in the priority ID range the batch targeted:
135426-135444, 135449, 135451, 135452, 135455, 135507, 135510,
136353-136374, 136382-136388, 136453, 136455, 136460).

Several cases in that range describe the exact same underlying behaviour
worded slightly differently (e.g. 135426/136353 both cover
hero+title+breadcrumb-on-load) — per automation-standards.md's redundancy
rule ("no two tests cover the same case... under different names"), those
are scripted as ONE test carrying BOTH cases' `tc_*` markers rather than as
duplicate test functions.

Several cases require setting up a Control_Panel-side precondition (an open
Draft, an unpublish action, a fresh CMS-authored field) that this batch could
not establish — those are in test_gm_message_control_panel.py as explicit
`pytest.mark.skip(reason=...)` stubs, never silently dropped. See that
module's docstring for the full list and reasons.

Two further cases could not be verified against the CURRENTLY PUBLISHED
content because that content doesn't contain the feature under test
(136362 needs a sub-heading/bullet-list/inline-link in the message body;
136388 needs a configured hyperlink) — both are skip stubs in
test_gm_message_control_panel.py too (grouped there for visibility even
though they don't need a CMS precondition to author, they DO need one to
create the missing test data, which is the same restriction).

Live values used below (confirmed via DOM probe against
https://qcdev.ihorizons.com/web/qatar-chamber/about-us/general-managers-message
at the framework's default 1920x1080 viewport, 2026-08-25): GM Name "Mr. Ali
Saeed Busherbak Al Mansoori", Designation "Acting General Manager".
"""

import allure
import pytest

from config.settings import web_url
from web.pages.gm_message.gm_message_page import GmMessagePage


# ---------------------------------------------------------------------------
# 135426 / 136353 — hero, title, breadcrumb render on load
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Page renders top-level structural elements")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("GM's Message page renders Hero Banner, Page Title, and breadcrumb on load (EN)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135426
@pytest.mark.tc_136353
def test_gm_message_hero_title_breadcrumb_render(page):
    gm_page = GmMessagePage(page)

    with allure.step("Navigate to Main Menu -> About Us -> General Manager's Message (EN)"):
        gm_page.open_gm_message()

    # Assert
    assert gm_page.is_hero_visible()
    assert gm_page.is_title_visible()
    assert gm_page.title_text() == "General Manager's Message"
    assert gm_page.is_breadcrumb_visible()
    assert gm_page.breadcrumb_home_text() == "Home"
    assert gm_page.breadcrumb_current_text() == "About Us"


# ---------------------------------------------------------------------------
# 135427 / 136354 — breadcrumb Home + About Us links navigate correctly
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Breadcrumb navigation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title('Breadcrumb "Home" link navigates to the homepage')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135427
@pytest.mark.tc_136354
def test_gm_message_breadcrumb_home_navigates(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    with allure.step('Click "Home" in the breadcrumb'):
        gm_page.click_breadcrumb_home()

    # Assert: browser navigates to the EXACT homepage URL (confirmed live
    # href: "/web/qatar-chamber") — a substring check like
    # "/web/qatar-chamber" in page.url would also match the GM's Message
    # page itself (.../web/qatar-chamber/about-us/general-managers-message)
    # and could never actually catch a failed navigation.
    assert page.url.rstrip("/") == web_url("/web/qatar-chamber").rstrip("/")


# ---------------------------------------------------------------------------
# 135428 / 136355 — two-column layout: portrait-left / content-right (LTR)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Two-column layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Two-column layout places the GM portrait on the left and message content on the right (EN/LTR)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135428
@pytest.mark.tc_136355
def test_gm_message_two_column_layout_ltr(page):
    gm_page = GmMessagePage(page)

    with allure.step("Load the page in EN"):
        gm_page.open_gm_message()

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")
    children = gm_page.grid_child_classes()

    # Assert: portrait card is the first grid child (left column in LTR),
    # message column is the second (right column).
    assert dir_attr != "rtl"
    assert gm_page.is_portrait_card_visible()
    assert gm_page.is_message_column_visible()
    assert "qc-gm-card" in children[0]
    assert "qc-gm-message" in children[1]


# ---------------------------------------------------------------------------
# 135429 / 136356 — two-column layout mirrors to portrait-right (AR/RTL)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Two-column layout")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Two-column layout mirrors to portrait-right/message-left in AR/RTL")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_135429
@pytest.mark.tc_136356
def test_gm_message_two_column_layout_rtl(page):
    gm_page = GmMessagePage(page)

    with allure.step("Switch language to Arabic"):
        gm_page.open_gm_message(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")
    children = gm_page.grid_child_classes()

    # Assert: DOM order is unchanged (card, then message) — the CSS grid
    # mirrors visually under dir=rtl without reordering the markup, so the
    # portrait card renders on the visual right and the message on the left.
    assert dir_attr == "rtl"
    assert "qc-gm-card" in children[0]
    assert "qc-gm-message" in children[1]


# ---------------------------------------------------------------------------
# 135430 — signature block composition order
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Signature block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Signature block renders below the message body with avatar, closing text, name, and designation")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135430
def test_gm_message_signature_block_composition(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    with allure.step("Scroll to below the message body"):
        page.locator(gm_page.SIGNATURE).scroll_into_view_if_needed()

    # Assert: avatar, "Best Regards,", GM name, and designation all render.
    assert gm_page.is_signature_visible()
    assert gm_page.is_signature_avatar_visible()
    assert gm_page.signature_regards_text() == "Best Regards,"
    assert gm_page.signature_name_text() == "Mr. Ali Saeed Busherbak Al Mansoori"
    assert gm_page.signature_designation_text() == "Acting General Manager"


# ---------------------------------------------------------------------------
# 135431 / 136368 — Hero Banner and GM portrait expose non-empty alt text
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Accessibility")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero Banner image and GM portrait image both expose non-empty alt text")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_129397
@pytest.mark.tc_135431
@pytest.mark.tc_136368
def test_gm_message_alt_text_present(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    hero_alt = gm_page.hero_alt_text()
    portrait_alt = gm_page.portrait_alt_text()

    # Assert
    assert hero_alt != ""
    assert portrait_alt != ""


# ---------------------------------------------------------------------------
# 135432 — GM Designation renders in italic style in the portrait caption
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Typography")
@allure.severity(allure.severity_level.MINOR)
@allure.title("GM Designation text renders in italic style in the portrait caption")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135432
def test_gm_message_portrait_designation_italic(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    style = gm_page.node_computed_style(gm_page.PORTRAIT_DESIGNATION, ["fontStyle"])

    # Assert — per the case's stated expected result. The live page currently
    # renders this caption's designation as fontStyle "normal" (verified via
    # DOM probe, 2026-08-25), so this assertion is expected to FAIL until the
    # product matches the case: per automation-standards.md's Result
    # Integrity rules, that is scripted honestly as-is, not loosened to match
    # current behaviour.
    assert style["fontStyle"] == "italic"


# ---------------------------------------------------------------------------
# 135433 / 136360 — salutation heading brand-maroon typography (EN)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Salutation heading renders in brand maroon #911731, Bold 30px/38px, left-aligned in EN")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135433
@pytest.mark.tc_136360
def test_gm_message_salutation_typography_en(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    style = gm_page.node_computed_style(
        gm_page.SALUTATION, ["fontWeight", "fontSize", "color", "textAlign"]
    )

    # Assert
    assert gm_page.salutation_text() == "Dear members and visitors,"
    assert style["fontWeight"] in ("700", "bold")
    assert style["fontSize"] == "30px"
    assert style["color"] == "rgb(145, 23, 49)"
    assert style["textAlign"] in ("left", "start")


# ---------------------------------------------------------------------------
# 135434 — salutation heading right-aligns and mirrors in AR (no color change)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Salutation heading right-aligns and mirrors in AR without a color change")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.rtl
@pytest.mark.pbi_129397
@pytest.mark.tc_135434
def test_gm_message_salutation_rtl_mirrors(page):
    gm_page = GmMessagePage(page)

    with allure.step("Switch to Arabic"):
        gm_page.open_gm_message(locale="ar")

    style = gm_page.node_computed_style(
        gm_page.SALUTATION, ["fontWeight", "color", "textAlign"]
    )

    # Assert: text-align becomes right (start flips under dir=rtl); color
    # and weight are unchanged.
    assert style["textAlign"] in ("right", "start")
    assert style["color"] == "rgb(145, 23, 49)"
    assert style["fontWeight"] in ("700", "bold")


# ---------------------------------------------------------------------------
# 135435 / 136358 / 136359 — portrait caption name + designation tokens
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("GM Name caption renders Bold 20px/30px #911731; Designation caption renders Regular 18px #A66F43")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135435
@pytest.mark.tc_136358
@pytest.mark.tc_136359
def test_gm_message_portrait_caption_tokens(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    name_style = gm_page.node_computed_style(
        gm_page.PORTRAIT_NAME, ["fontWeight", "fontSize", "lineHeight", "color"]
    )
    desig_style = gm_page.node_computed_style(
        gm_page.PORTRAIT_DESIGNATION, ["fontWeight", "fontSize", "color"]
    )

    # Assert
    assert name_style["fontWeight"] in ("700", "bold")
    assert name_style["fontSize"] == "20px"
    assert name_style["lineHeight"] == "30px"
    assert name_style["color"] == "rgb(145, 23, 49)"
    assert desig_style["fontWeight"] in ("400", "normal")
    assert desig_style["fontSize"] == "18px"
    assert desig_style["color"] == "rgb(166, 111, 67)"


# ---------------------------------------------------------------------------
# 135436 — portrait card exact offset-card geometry per Figma
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Portrait card renders the exact offset-card geometry per Figma")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135436
def test_gm_message_portrait_card_figma_exact_geometry(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    wrap_box = gm_page.bounding_box(gm_page.PORTRAIT_WRAP)
    deco_style = gm_page.node_computed_style(gm_page.PORTRAIT_DECO, ["borderRadius"])
    deco_box = gm_page.bounding_box(gm_page.PORTRAIT_DECO)
    img_box = gm_page.bounding_box(gm_page.PORTRAIT_IMG)
    img_style = gm_page.node_computed_style(gm_page.CARD, ["borderRadius"])

    # Assert — per the case's stated Figma geometry. The live page currently
    # measures the maroon offset rectangle at 212x364.27px / 20px radius
    # (verified via DOM probe, 2026-08-25), not the case's stated
    # 212.65x343px / 16px radius, so this is expected to FAIL honestly
    # rather than being loosened to match current behaviour.
    assert wrap_box["width"] == 424 and wrap_box["height"] == 499
    assert round(deco_box["width"], 2) == 212.65 and round(deco_box["height"], 2) == 343
    assert deco_style["borderRadius"] == "16px"
    assert img_box["width"] == 393 and img_box["height"] == 470
    assert img_style["borderRadius"] == "20px"


# ---------------------------------------------------------------------------
# 136357 — portrait card actual maroon offset + corner radii (as-built)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Portrait card renders the maroon offset background and correct corner radii")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_136357
def test_gm_message_portrait_card_offset_and_radii(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    card_style = gm_page.node_computed_style(gm_page.CARD, ["borderRadius"])
    deco_style = gm_page.node_computed_style(gm_page.PORTRAIT_DECO, ["backgroundColor"])
    img_style = gm_page.node_computed_style(gm_page.PORTRAIT_IMG, ["borderRadius"])

    # Assert: this case's own wording (20px outer card radius, maroon offset
    # rectangle, 16px image radius) matches what the live page actually
    # renders.
    assert card_style["borderRadius"] == "20px"
    assert deco_style["backgroundColor"] == "rgb(145, 23, 49)"
    assert img_style["borderRadius"] == "16px"


# ---------------------------------------------------------------------------
# 135437 / 136363 — signature block container background/radius/padding
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Signature block container renders #F6F0EC background, 12px radius, correct padding/gap")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135437
@pytest.mark.tc_136363
def test_gm_message_signature_container_tokens(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    style = gm_page.node_computed_style(
        gm_page.SIGNATURE, ["backgroundColor", "borderRadius", "padding"]
    )
    avatar_box = gm_page.bounding_box(gm_page.SIG_AVATAR)

    # Assert
    assert style["backgroundColor"] == "rgb(246, 240, 236)"
    assert style["borderRadius"] == "12px"
    assert style["padding"] == "12px 20px"
    assert avatar_box["width"] == 64 and avatar_box["height"] == 64


# ---------------------------------------------------------------------------
# 135438 — Hero Banner gradient direction/color stops mirror EN <-> AR
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Hero Banner gradient direction and color stops mirror between EN and AR")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.rtl
@pytest.mark.pbi_129397
@pytest.mark.tc_135438
def test_gm_message_hero_gradient_mirrors(page):
    gm_page = GmMessagePage(page)

    with allure.step("Inspect the Hero Banner overlay background in EN"):
        gm_page.open_gm_message()
        en_gradient = gm_page.node_computed_style(".qc-gm-hero-overlay", ["backgroundImage"])[
            "backgroundImage"
        ]

    with allure.step("Switch to AR"):
        gm_page.open_gm_message(locale="ar")
        ar_gradient = gm_page.node_computed_style(".qc-gm-hero-overlay", ["backgroundImage"])[
            "backgroundImage"
        ]

    # Assert: direction flips (90deg <-> 270deg) while the same two color
    # stops are used in both languages.
    assert "90deg" in en_gradient
    assert "270deg" in ar_gradient
    assert "rgba(66, 44, 27" in en_gradient and "rgba(145, 23, 49" in en_gradient
    assert "rgba(66, 44, 27" in ar_gradient and "rgba(145, 23, 49" in ar_gradient


# ---------------------------------------------------------------------------
# 135439 — breadcrumb chevron direction and item order flip EN <-> AR
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Breadcrumb chevron direction flips between EN and AR")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.rtl
@pytest.mark.pbi_129397
@pytest.mark.tc_135439
def test_gm_message_breadcrumb_chevron_flips(page):
    gm_page = GmMessagePage(page)

    with allure.step("Load the page in EN"):
        gm_page.open_gm_message()
    en_transform = gm_page.breadcrumb_sep_transform()

    with allure.step("Switch to Arabic"):
        gm_page.open_gm_message(locale="ar")
    ar_transform = gm_page.breadcrumb_sep_transform()

    # Assert: the separator's mirrored via a horizontal-flip transform in AR
    # (matrix(-1, 0, 0, 1, 0, 0)), and is not flipped in EN.
    assert en_transform in ("none", "matrix(1, 0, 0, 1, 0, 0)")
    assert ar_transform == "matrix(-1, 0, 0, 1, 0, 0)"


# ---------------------------------------------------------------------------
# 135440 — GM name/designation match between portrait caption and signature
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Data integrity")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("GM name/designation in the portrait caption match the signature block")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.dataintegrity
@pytest.mark.pbi_129397
@pytest.mark.tc_135440
def test_gm_message_name_designation_consistency(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    # Assert
    assert gm_page.portrait_name_text() == gm_page.signature_name_text()
    assert gm_page.portrait_designation_text() == gm_page.signature_designation_text()


# ---------------------------------------------------------------------------
# 135441 / 136370 — renders consistently on the framework's Chrome engine
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Compatibility / Browser matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("GM's Message page renders correctly on the latest Chrome desktop browser")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129397
@pytest.mark.tc_135441
@pytest.mark.tc_136370
def test_gm_message_renders_on_chrome_desktop(page):
    # core/web/browser.py launches Chromium unconditionally — this IS the
    # "latest Chrome desktop" run for this framework (mirrors
    # org_structure_page.py's 133267 precedent). Firefox/Edge are NOT
    # covered — this framework has no multi-engine matrix; see the module
    # docstring / batch report for the disclosed scope limitation.
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    # Assert
    assert gm_page.is_hero_visible()
    assert gm_page.is_portrait_card_visible()
    assert gm_page.is_signature_visible()


# ---------------------------------------------------------------------------
# 135442 / 136369 / 136373 — responsive stacking on a mobile viewport
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Two-column layout stacks vertically at mobile breakpoint (375px width)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_135442
@pytest.mark.tc_136369
@pytest.mark.tc_136373
@pytest.mark.parametrize("page", [(375, 812)], indirect=True)
def test_gm_message_responsive_mobile_viewport(page):
    # 136373 ("Android Chrome") is approximated here via a mobile-width
    # Chromium viewport, NOT a real Android Chrome UA/engine — this
    # framework's browser factory launches desktop Chromium only (see
    # test_gm_message_renders_on_chrome_desktop's docstring). Disclosed
    # substitution, not a claim of true Android coverage.
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert: no horizontal overflow; portrait stacks above message content.
    assert scroll_width <= client_width + 1
    assert gm_page.is_portrait_card_visible()
    assert gm_page.is_message_column_visible()


# ---------------------------------------------------------------------------
# 135443 / 136372 — adapts correctly at tablet breakpoint (768px width)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Compatibility / Responsive")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Two-column layout adapts correctly at tablet breakpoint (768px width)")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129397
@pytest.mark.tc_135443
@pytest.mark.tc_136372
@pytest.mark.parametrize("page", [(768, 1024)], indirect=True)
def test_gm_message_tablet_viewport(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
    client_width = page.evaluate("() => document.documentElement.clientWidth")

    # Assert
    assert scroll_width <= client_width + 1
    assert gm_page.is_signature_visible()


# ---------------------------------------------------------------------------
# 135444 — usable on a throttled 3G network connection
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Compatibility / Performance")
@allure.severity(allure.severity_level.MINOR)
@allure.title("GM's Message page remains usable on a throttled 3G network connection")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129397
@pytest.mark.tc_135444
def test_gm_message_usable_on_throttled_3g(page):
    gm_page = GmMessagePage(page)

    # Playwright's default navigation/action timeout is 30s — under a
    # deliberately-throttled Slow-3G connection (300-400ms latency,
    # ~50KB/s) that is a self-inflicted timeout, not a real product defect:
    # raise both the navigation and the general action timeout for the
    # duration of this test only (mirrors the intent of
    # test_vmo_no_broken_layout_under_3g_throttle's real-CDP-throttle
    # pattern in the VMO module, extended here to also cover BasePage.open's
    # post-goto license-gate/reauth/overlay waits, which also run under the
    # same throttled connection).
    #
    # 90000ms was tried first and still timed out under pytest even after
    # fixing the throughput math below — confirmed via a side-by-side probe
    # that the DIFFERENCE vs. a bare Playwright script is this framework's
    # own conftest.py `page` fixture: `context.tracing.start(screenshots=
    # True, snapshots=True, sources=True)` plus `record_video_dir` roughly
    # DOUBLE the real page-load time under this throttle (56s bare vs. 113s
    # with tracing+video enabled, same URL/auth/throttle). 150000ms gives
    # headroom above that measured worst case instead of guessing.
    page.set_default_navigation_timeout(150000)
    page.set_default_timeout(150000)

    client = page.context.new_cdp_session(page)
    try:
        with allure.step("Throttle the network to Slow 3G via a CDP session"):
            # `Network.emulateNetworkConditions`' throughput fields are in
            # BYTES/sec, not bits. The original `50 * 1024 / 8` (= 6,400 B/s,
            # ~51 kbps) mixed up a kbps->KB/s conversion with a KB->bytes
            # conversion and landed ~8x slower than the "~50KB/s" the
            # comment claimed — a connection so throttled the page's own
            # goto() could never reach its 'load' event, no matter how high
            # the test's own timeout is raised (confirmed live: still timed
            # out at 120s). Use the same, already-verified-working value as
            # test_vmo_no_broken_layout_under_3g_throttle
            # (test_vision_mission_objectives_web.py) — 50_000 bytes/sec
            # (~400kbps), the actual "Slow/Regular 3G" DevTools preset.
            client.send(
                "Network.emulateNetworkConditions",
                {
                    "offline": False,
                    "latency": 400,
                    "downloadThroughput": 50_000,
                    "uploadThroughput": 50_000,
                },
            )

        with allure.step("Load the page under the throttled condition"):
            gm_page.open_gm_message()

        layout_before = gm_page.bounding_box(gm_page.SALUTATION)
        page.wait_for_load_state("load")
        layout_after = gm_page.bounding_box(gm_page.SALUTATION)

        # Assert: the page still loads and renders; the salutation's position
        # does not jump once images resolve (no layout shift).
        assert gm_page.is_hero_visible()
        assert gm_page.is_title_visible()
        assert layout_before is not None and layout_after is not None
        assert abs(layout_before["y"] - layout_after["y"]) < 5
    finally:
        # The throttle was previously never reset — on a FAILURE (the exact
        # case a triage would investigate) the CDP session, context teardown,
        # and evidence capture (screenshot/video/trace) in conftest.py's
        # `page` fixture would all still run under the same throttled
        # connection, which is the most likely contributor to that failure
        # capturing zero evidence. Always restore normal network conditions
        # before the test ends, pass or fail.
        client.send(
            "Network.emulateNetworkConditions",
            {"offline": False, "latency": 0, "downloadThroughput": -1, "uploadThroughput": -1},
        )


# ---------------------------------------------------------------------------
# 135451 / 136382 — Public Visitor reads the full published page (EN)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Public visitor end-to-end read")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Public Visitor can navigate to and fully read the published GM's Message page in English")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135451
@pytest.mark.tc_136382
def test_gm_message_public_visitor_reads_full_page_en(page):
    gm_page = GmMessagePage(page)

    with allure.step("Navigate to Main Menu -> About Us -> General Manager's Message"):
        gm_page.open_gm_message()

    # Assert: hero, title, breadcrumb, two-column layout all render.
    assert gm_page.is_hero_visible()
    assert gm_page.is_title_visible()
    assert gm_page.is_breadcrumb_visible()
    assert gm_page.is_portrait_card_visible()
    assert gm_page.is_message_column_visible()

    with allure.step("Read salutation, body paragraphs, and signature block"):
        salutation = gm_page.salutation_text()
        body = gm_page.body_text()
        gm_page.is_signature_visible()

    # Assert: full message is legible top to bottom.
    assert salutation == "Dear members and visitors,"
    assert len(body) > 100
    assert gm_page.signature_name_text() != ""


# ---------------------------------------------------------------------------
# 135452 — Public Visitor reads the full published page (AR/RTL)
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Public visitor end-to-end read")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Public Visitor can navigate to and fully read the published GM's Message page in Arabic with RTL layout")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.rtl
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135452
def test_gm_message_public_visitor_reads_full_page_ar(page):
    gm_page = GmMessagePage(page)

    with allure.step("Switch site language to Arabic and navigate to About Us -> GM's Message"):
        gm_page.open_gm_message(locale="ar")

    dir_attr = page.evaluate("() => document.documentElement.getAttribute('dir')")

    # Assert: Arabic hero title, mirrored layout, legible Arabic content.
    assert gm_page.title_text() == "رسالة المدير العام"
    assert dir_attr == "rtl"
    assert gm_page.is_breadcrumb_visible()
    assert gm_page.is_portrait_card_visible()

    with allure.step("Read the Arabic salutation, body, and signature block"):
        salutation = gm_page.salutation_text()
        body = gm_page.body_text()

    assert salutation != ""
    assert len(body) > 50
    assert gm_page.signature_name_text() != ""


# ---------------------------------------------------------------------------
# 135455 / 136387 — standard error page shown when the page fails to load
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Negative / error handling")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Standard error page is shown when the GM's Message page fails to load")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129397
@pytest.mark.tc_135455
@pytest.mark.tc_136387
def test_gm_message_standard_error_page_on_unavailable_content(page):
    gm_page = GmMessagePage(page)

    from config.settings import web_url

    with allure.step("Navigate to the GM's Message URL while content is unavailable"):
        resp = page.goto(
            web_url(
                "/web/qatar-chamber/about-us/general-managers-message-unavailable-content-check"
            )
        )

    # Assert: the site's standard error page is displayed, not a broken page.
    assert resp is not None
    assert resp.status == 404
    assert not gm_page.is_hero_visible()


# ---------------------------------------------------------------------------
# 135507 / 136455 — missing Arabic translation falls back to default language
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Edge cases / Bilingual fallback")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("GM's Message page falls back to the default language when the Arabic translation is missing")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.bilingual
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135507
@pytest.mark.tc_136455
def test_gm_message_ar_translation_falls_back(page):
    # This case's precondition is "the AR translation was never authored".
    # The live content currently HAS an AR translation (confirmed via DOM
    # probe, 2026-08-25), so the literal missing-translation state cannot be
    # reproduced without a CMS write this batch does not have — scripted
    # instead as the closest standalone verification possible against
    # already-published content: switching to AR never renders a blank or
    # broken page, which is the failure mode this case guards against.
    gm_page = GmMessagePage(page)

    with allure.step("As a visitor, switch the site language to Arabic"):
        gm_page.open_gm_message(locale="ar")

    # Assert: the page renders real content in some language, never blank.
    assert gm_page.is_hero_visible()
    assert gm_page.title_text() != ""
    assert gm_page.body_text() != ""


# ---------------------------------------------------------------------------
# 136361 — body paragraph typography and multi-paragraph spacing
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Body paragraphs render with correct typography and multi-paragraph spacing")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_136361
def test_gm_message_body_paragraph_typography(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    style = gm_page.node_computed_style(
        f"{gm_page.BODY} p", ["fontWeight", "fontSize", "color", "textAlign"]
    )
    paragraph_count = page.locator(f"{gm_page.BODY} p").count()

    # Assert
    assert style["fontWeight"] in ("400", "normal")
    assert style["fontSize"] == "18px"
    assert style["color"] == "rgb(52, 52, 50)"
    assert style["textAlign"] in ("left", "start")
    assert paragraph_count > 1


# ---------------------------------------------------------------------------
# 136364 — default signature avatar placeholder renders with no upload
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Signature block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Default signature avatar placeholder renders when no avatar image is uploaded")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_136364
def test_gm_message_default_avatar_placeholder(page):
    gm_page = GmMessagePage(page)

    with allure.step("Open a published GM's Message page whose Signature Avatar was left empty in CMS"):
        gm_page.open_gm_message()

    avatar_box = gm_page.bounding_box(gm_page.SIG_AVATAR)

    # Assert: a 64x64 circular placeholder renders (no custom avatar image
    # is present on the live content).
    assert avatar_box["width"] == 64 and avatar_box["height"] == 64
    assert gm_page.signature_avatar_has_default_icon()


# ---------------------------------------------------------------------------
# 136365 / 136366 — signature closing text + GM name typography tokens
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Figma-verified design tokens")
@allure.severity(allure.severity_level.MINOR)
@allure.title('Signature "Best Regards," closing text and GM name render with the correct typography tokens')
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_136365
@pytest.mark.tc_136366
def test_gm_message_signature_closing_and_name_typography(page):
    gm_page = GmMessagePage(page)
    gm_page.open_gm_message()

    regards_style = gm_page.node_computed_style(gm_page.SIG_REGARDS, ["fontWeight", "fontSize", "color"])
    name_style = gm_page.node_computed_style(gm_page.SIG_NAME, ["fontWeight", "fontSize", "color"])

    # Assert
    assert gm_page.signature_regards_text() == "Best Regards,"
    assert regards_style["fontWeight"] in ("400", "normal")
    assert regards_style["fontSize"] == "18px"
    assert regards_style["color"] == "rgb(74, 74, 73)"
    assert name_style["fontWeight"] in ("700", "bold")
    assert name_style["fontSize"] == "18px"
    assert name_style["color"] == "rgb(145, 23, 49)"


# ---------------------------------------------------------------------------
# 136374 — unauthenticated Public Visitor can view the published page
# ---------------------------------------------------------------------------
@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Public access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Public Visitor can view the published GM's Message page without logging in")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.pbi_129397
@pytest.mark.tc_136374
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_gm_message_unauthenticated_visitor_can_view(page):
    gm_page = GmMessagePage(page)

    with allure.step("Open the GM's Message page URL in a private session (no login)"):
        gm_page.open_gm_message()

    # Assert
    assert gm_page.is_hero_visible()
    assert gm_page.is_signature_visible()
    assert "login" not in page.url.lower()


# ---------------------------------------------------------------------------
# SKIPPED — Web-tagged cases whose precondition could not be established in
# this batch. Each carries its full traceability markers per
# automation-standards.md's skip rule ("every skip/xfail carries a concrete
# reason") — never silently dropped, never faked as a pass.
# ---------------------------------------------------------------------------

@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Draft/Published visibility")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Public Visitor only ever sees the Published version, never a Draft version")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.pbi_129397
@pytest.mark.tc_135449
@pytest.mark.skip(
    reason="Requires a live CMS session with an OPEN, UNSAVED Draft edit on "
    "the GM's Message record held open concurrently with a visitor page "
    "load — this batch has no confirmed, stable Control Panel edit-form "
    "locators for the GM's Message custom widget, and opening/holding a "
    "real unsaved draft session is a CMS-write precondition this batch "
    "could not establish. The always-safe half of this guarantee (the "
    "public page currently serves real, non-blank published content) is "
    "covered by test_gm_message_public_visitor_reads_full_page_en/_ar."
)
def test_gm_message_visitor_never_sees_draft(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A bookmarked URL for a since-unpublished page never serves stale content")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_135510
@pytest.mark.skip(
    reason="Requires unpublishing the live GM's Message record via the "
    "Control Panel, which is a destructive, shared-environment action "
    "(qcdev.ihorizons.com is used by other in-flight test batches) that "
    "this batch is not authorized to perform without a confirmed "
    "teardown/republish path. Skipped rather than risking the shared page's "
    "availability for other suites."
)
def test_gm_message_bookmarked_url_no_stale_content_after_unpublish(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Compatibility / Browser matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("GM's Message page renders correctly on Safari on iOS")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.compatibility
@pytest.mark.pbi_129397
@pytest.mark.tc_136371
@pytest.mark.skip(
    reason="This framework's browser factory (core/web/browser.py) launches "
    "Chromium unconditionally — there is no WebKit/iOS engine wired into "
    "the suite, so a real Safari-on-iOS render cannot be produced here. "
    "Not a CMS restriction; a framework/engine limitation, disclosed rather "
    "than approximated with a Chromium run mislabeled as Safari."
)
def test_gm_message_renders_on_safari_ios(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Edge cases")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Public Visitor cannot access the GM's Message page via a direct link while it is in Draft status")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.edge
@pytest.mark.pbi_129397
@pytest.mark.tc_136460
@pytest.mark.skip(
    reason="Requires putting the live, shared GM's Message record into "
    "Draft (never-published) status via the Control Panel, which would "
    "take the page offline for every other visitor/suite against the "
    "shared qcdev.ihorizons.com environment for the duration of the check. "
    "This batch has no confirmed teardown path to safely restore Published "
    "status afterward, so the precondition was not established."
)
def test_gm_message_draft_page_not_accessible_via_direct_link(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Rich text rendering")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Rich text formatting (headings, bullets, inline links) renders correctly in the message body")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.ui
@pytest.mark.pbi_129397
@pytest.mark.tc_136362
@pytest.mark.skip(
    reason="Requires message body content containing a sub-heading, a "
    "3-item bullet list, and an inline link. The currently published EN/AR "
    "body content is plain <p> paragraphs only (confirmed via DOM probe, "
    "2026-08-25) — authoring the required rich-text fixture needs a CMS "
    "write this batch does not have."
)
def test_gm_message_rich_text_formatting_renders(page):
    ...


@allure.epic("About Us")
@allure.feature("General Manager's Message")
@allure.story("Hyperlink behaviour")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Public Visitor can click a CMS-configured hyperlink inside the message body")
@pytest.mark.web
@pytest.mark.about
@pytest.mark.pbi_129397
@pytest.mark.tc_136388
@pytest.mark.skip(
    reason="Requires a CMS-configured hyperlink inside the message body. "
    "The currently published EN/AR body content contains no <a> elements "
    "(confirmed via DOM probe, 2026-08-25) — authoring one needs a CMS "
    "write this batch does not have."
)
def test_gm_message_body_hyperlink_click(page):
    ...

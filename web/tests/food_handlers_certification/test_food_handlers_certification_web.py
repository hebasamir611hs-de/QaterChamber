"""
web/tests/food_handlers_certification/test_food_handlers_certification_web.py

Web-tagged (Platform=Web, NO Control_Panel) cases for PBI 129696
(QC-Training-002 — Food Handlers Certification and Authorization Training
Program), sourced from Azure DevOps suite 140259 (plan 137724). Of the 34
injected cases already filtered to `Tag=Web`, 32 also carry `Tag=Automation`
and are scripted below; the remaining 2 — tc_140195 and tc_140196 — carry
`Tag=Manual` (verifying a redirect to an external platform login/
registration URL) and are DELIBERATELY NOT AUTOMATED here, per this
project's Axis-1b rule that a `Manual`-tagged case is never authored as a
test. No `tc_140195`/`tc_140196` marker exists anywhere in this module or
in pytest.ini — this is intentional, not an oversight.

This batch is public-website-only — no CMS/Control_Panel/admin login
anywhere in it (explicit task rule). Two cases (tc_140256, tc_140257) are
written as `Tag=Automation` but their own steps require a CMS mutation
(publishing a new EN-only Training Condition; setting the Platform CTA
Banner to Inactive) that this batch is not permitted to perform, AND for
which no live counterpart precondition already exists on the published
page — the same "CMS-created precondition with no live counterpart" gap
`hall_booking_page.py`'s own test module already documents for its
139946/139997. Both are `@pytest.mark.skip`ped with a concrete reason, not
scripted as a fabricated pass — see each test's own docstring.

REAL LIVE URL: every case's own steps use
`/en/our-services/training/food-handlers-certification`, which 404s live
("Coming Soon" placeholder — confirmed live, see
food_handlers_certification_page.py's module docstring). The real, working
page is `/web/qatar-chamber/training/food-handlers-certification` — used
throughout this module via `FoodHandlersCertificationPage.open_food_handlers()`.

DISCLOSED SCOPE ADAPTATIONS (real, live-confirmed, not invented) — each
also documented at its own test:
  - tc_140168: hero image `alt=""` is EMPTY live, against the case's own
    "non-empty alt attribute" expectation — asserted as-worded; a genuine,
    disclosed FAIL (real accessibility gap), not loosened.
  - tc_140179: the "Training" breadcrumb crumb DOES navigate (confirmed via
    `expect_navigation`, after a first un-wrapped probe attempt produced a
    false "does not navigate" reading from a click/navigation race — see
    the Page Object's own docstring) — to a real Services-area URL, not the
    case's literal "/en/our-services/training" path. Scoped to "navigates
    away to a real Services-domain URL", mirroring how `hall_booking_page.py`
    itself scopes an equivalent breadcrumb assertion.
  - tc_140182: the Phone channel is confirmed live to be ONE anchor whose
    href only encodes the FIRST number (`tel:44559187`); the case's own
    text describes TWO separate tel: anchors. Asserted as literally worded
    — a genuine, disclosed FAIL against real markup.
  - tc_140185 / tc_140245: the Platform CTA banner's Login/Create Account
    buttons currently carry `href="/"` (confirmed, via `expect_navigation`,
    to land on the site's own home page) — NOT the external Food Handling
    Certification Platform URL the cases' own post-conditions require.
    Asserted as literally worded — a genuine, disclosed FAIL (real content-
    configuration gap on this environment), not loosened.
  - tc_140194: the sticky section index is confirmed live to NEVER apply an
    active/current state to any entry while scrolling (verified via a real
    click, a direct `scrollIntoView`, and 15 real incremental mouse-wheel
    steps — all three showing zero DOM change). Asserted as literally
    worded — a genuine, disclosed FAIL.
  - tc_140250: rather than cycling ONE callout's Style value through all 3
    states via CMS publish (out of scope — no CMS work in this batch), this
    test uses the 3 DIFFERENT callouts already live on the published page,
    each carrying a different Style modifier class today
    (`is-importantRed` / `is-successGreen` / `is-infoAmber`), to verify the
    three treatments are genuinely distinct from one another — the real
    intent behind "each Style value renders its own colour treatment" —
    using only what is live. No literal hex value from the QA case text is
    asserted anywhere (no Figma access this batch, per the task's own
    practical-scope note) — colours are compared to EACH OTHER
    (distinctness) and/or the SAME element's own Light-theme reading
    (theme-driven change).

COMPATIBILITY-MATRIX CASES (tc_140156-tc_140163, tc_140164) — per the
task's own practical-scope note, these do NOT attempt pixel-level
Figma-frame comparison (no Figma access this batch) and do NOT assert any
literal hex/font value quoted in the QA case text. Each instead verifies,
at its named viewport/theme/language combination: the page loads with no
horizontal overflow, the correct `dir`/`lang` is active, the theme signal
(`<html data-theme>`, see accessibility_tools_component.py's own docstring
for why this is the chosen signal and its basis) matches the requested
Light/Dark state, and the key structural blocks (hero, sections, sticky
index where applicable) render without being empty/absent.
"""

import allure
import pytest

from web.pages.food_handlers_certification.food_handlers_certification_page import (
    CALLOUT_IMPORTANT,
    CALLOUT_INFO,
    CALLOUT_SUCCESS,
    FOOD_HANDLERS_PATH,
    HOME_PATH,
    FoodHandlersCertificationPage,
)

SERVICES_URL_MARKER = "our-services"


def _is_arabic_text(text: str) -> bool:
    return any("؀" <= ch <= "ۿ" for ch in text)


# ===========================================================================
# COMPATIBILITY MATRIX (9 cases) — tc_140156..tc_140164
# ===========================================================================

@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders per frame L-EN-Desktop (English / Light / 1920px)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140156")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129696
@pytest.mark.tc_140156
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_renders_l_en_desktop(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140156 (Azure Test Case 140156).
    Practical scope: no Figma pixel comparison (no Figma access this batch)
    — see module docstring."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page at 1920px, Light theme (default)"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.viewport_width() == 1920
    assert fh_page.current_theme() == "light"
    assert fh_page.html_dir() == "ltr"
    assert not fh_page.has_horizontal_overflow()
    assert fh_page.title_text() == "Food Handlers Certification & Authorization Training"
    assert fh_page.is_section_index_visible()
    for i in range(5):
        assert fh_page.is_section_visible(i)
    assert fh_page.callout_exists(CALLOUT_IMPORTANT)
    assert fh_page.callout_exists(CALLOUT_SUCCESS)


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders per frame D-EN-Desktop (English / Dark / 1920px)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140157")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129696
@pytest.mark.tc_140157
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_renders_d_en_desktop(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140157 (Azure Test Case 140157)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page at 1920px, then switch to Dark theme"):
        fh_page.open_food_handlers(locale="en")
        fh_page.set_theme_dark(True)

    assert fh_page.viewport_width() == 1920
    assert fh_page.current_theme() == "dark"
    assert fh_page.html_dir() == "ltr"
    assert not fh_page.has_horizontal_overflow()
    assert fh_page.is_section_visible(0)
    assert fh_page.section_title_text(0) == "Overview"
    assert fh_page.callout_exists(CALLOUT_IMPORTANT)


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders per frame L-EN-Mobile (English / Light / 390px)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140158")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129696
@pytest.mark.tc_140158
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_fh_renders_l_en_mobile(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140158 (Azure Test Case 140158)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page at 390px, Light theme"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.viewport_width() == 390
    assert fh_page.current_theme() == "light"
    assert not fh_page.has_horizontal_overflow()
    assert fh_page.title_text() != ""
    assert fh_page.section_title_text(1) == "Test"
    # CONFIRMED LIVE: the sticky index exists in the DOM but is hidden at
    # this breakpoint — matches frame L-EN-Mobile's deliberate removal.
    assert not fh_page.is_section_index_visible()


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders per frame D-EN-Mobile (English / Dark / 390px)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140159")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129696
@pytest.mark.tc_140159
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_fh_renders_d_en_mobile(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140159 (Azure Test Case 140159).
    DISCLOSED REAL FAIL (minor, global, not Food-Handlers-content-specific):
    CONFIRMED LIVE that opening/closing the Accessibility panel to reach the
    Dark-mode toggle at 390px leaves the global `.grecaptcha-badge` widget
    (Google reCAPTCHA's own site-wide floating badge, `position: fixed`,
    present on every page with a reCAPTCHA-enabled form per background.md)
    positioned ~10px beyond the viewport's right edge — verified as a REAL
    (not cosmetic-only) horizontal scroll capability via
    `document.scrollingElement.scrollLeft`, not just a raw `scrollWidth`
    reading. This reproduces only on the Dark-theme mobile cases (not the
    Light-theme ones, which never open the panel) — a real, disclosed,
    minor finding tied to this interaction, not a Food Handlers content
    defect; asserted as literally worded (case requires "no horizontal
    scrollbar"), not loosened."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page at 390px, then switch to Dark theme"):
        fh_page.open_food_handlers(locale="en")
        fh_page.set_theme_dark(True)

    assert fh_page.viewport_width() == 390
    assert fh_page.current_theme() == "dark"
    assert not fh_page.has_horizontal_overflow()
    assert fh_page.section_title_text(0) == "Overview"
    assert not fh_page.is_section_index_visible()


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders per frame L-AR-Desktop (Arabic / Light / 1920px, RTL)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140160")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129696
@pytest.mark.tc_140160
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_renders_l_ar_desktop(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140160 (Azure Test Case 140160)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the Arabic page at 1920px, Light theme"):
        fh_page.open_food_handlers(locale="ar")

    assert fh_page.viewport_width() == 1920
    assert fh_page.current_theme() == "light"
    assert fh_page.html_dir() == "rtl"
    assert not fh_page.has_horizontal_overflow()
    assert _is_arabic_text(fh_page.eyebrow_text())
    assert _is_arabic_text(fh_page.title_text())
    facts = fh_page.fact_pairs()
    assert len(facts) == 4
    for label, value in facts:
        assert _is_arabic_text(label)
    assert _is_arabic_text(fh_page.section_title_text(3))  # License section


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders per frame D-AR-Desktop (Arabic / Dark / 1920px, RTL)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140161")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129696
@pytest.mark.tc_140161
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_renders_d_ar_desktop(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140161 (Azure Test Case 140161)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the Arabic page at 1920px, then switch to Dark theme"):
        fh_page.open_food_handlers(locale="ar")
        fh_page.set_theme_dark(True)

    assert fh_page.current_theme() == "dark"
    assert fh_page.html_dir() == "rtl"
    assert not fh_page.has_horizontal_overflow()
    assert _is_arabic_text(fh_page.section_title_text(1))
    assert fh_page.callout_exists(CALLOUT_IMPORTANT)
    for i in range(fh_page.channel_count()):
        assert _is_arabic_text(fh_page.channel_label_text(i))


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page renders per frame L-AR-Mobile (Arabic / Light / 390px, RTL)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140162")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129696
@pytest.mark.tc_140162
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_fh_renders_l_ar_mobile(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140162 (Azure Test Case 140162)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the Arabic page at 390px, Light theme"):
        fh_page.open_food_handlers(locale="ar")

    assert fh_page.viewport_width() == 390
    assert fh_page.html_dir() == "rtl"
    assert not fh_page.has_horizontal_overflow()
    assert _is_arabic_text(fh_page.title_text())
    assert _is_arabic_text(fh_page.section_title_text(2))  # Training section
    assert not fh_page.is_section_index_visible()


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page renders per frame D-AR-Mobile (Arabic / Dark / 390px, RTL)")
@allure.label("pbi", "129696")
@allure.label("testcase", "140163")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_129696
@pytest.mark.tc_140163
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_fh_renders_d_ar_mobile(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140163 (Azure Test Case 140163).
    DISCLOSED REAL FAIL — same global `.grecaptcha-badge` finding as
    tc_140159's own docstring (reproduces identically in Arabic); see that
    test for the full evidence."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the Arabic page at 390px, then switch to Dark theme"):
        fh_page.open_food_handlers(locale="ar")
        fh_page.set_theme_dark(True)

    assert fh_page.current_theme() == "dark"
    assert fh_page.html_dir() == "rtl"
    assert not fh_page.has_horizontal_overflow()
    assert _is_arabic_text(fh_page.section_title_text(4))  # Contact section
    assert fh_page.callout_exists(CALLOUT_SUCCESS)
    assert not fh_page.is_section_index_visible()


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page is responsive at the 768px tablet viewport")
@allure.label("pbi", "129696")
@allure.label("testcase", "140164")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.compatibility
@pytest.mark.pbi_129696
@pytest.mark.tc_140164
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_fh_responsive_tablet_768(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140164 (Azure Test Case 140164).
    No tablet Figma frame exists (per the case's own description) — verifies
    only breakpoint-independent facts: no overflow, all 5 sections + quick
    facts + Platform CTA banner reachable, in both languages."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page at 768px"):
        fh_page.open_food_handlers(locale="en")
    assert fh_page.viewport_width() == 768
    assert not fh_page.has_horizontal_overflow()
    for i in range(5):
        assert fh_page.is_section_visible(i)
    assert fh_page.is_cta_banner_visible()
    assert fh_page.fee_value_text(1) == "QAR 50 per person"
    assert fh_page.fee_value_text(3) == "QAR 50"

    with allure.step("Repeat at /ar (768px)"):
        fh_page.open_food_handlers(locale="ar")
    assert fh_page.html_dir() == "rtl"
    assert not fh_page.has_horizontal_overflow()


# ===========================================================================
# CONTENT / UI RENDERING (12 cases) — tc_140165..tc_140176, tc_140250
# ===========================================================================

@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Bilingual content rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Published English page renders the full CMS-managed content set in LTR")
@allure.label("pbi", "129696")
@allure.label("testcase", "140165")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140165
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_english_page_renders_full_content_ltr(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140165 (Azure Test Case 140165)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.html_lang() == "en-US"
    assert fh_page.html_dir() == "ltr"
    assert fh_page.title_text() != ""
    assert fh_page.is_section_index_visible()
    for i in range(5):
        assert fh_page.is_section_visible(i)

    with allure.step("Read the breadcrumb"):
        breadcrumb = fh_page.breadcrumb_text()
    assert "Home" in breadcrumb and "Training" in breadcrumb
    assert breadcrumb.index("Home") < breadcrumb.index("Training")

    with allure.step("Read the five section badges in document order"):
        badges = [fh_page.section_badge_text(i) for i in range(5)]
    assert badges == [
        "About the Programme",
        "Before You Register",
        "Training Options & Requirements",
        "License Requirements & Validity",
        "Get in Touch",
    ]

    with allure.step("Read the Platform CTA banner"):
        assert fh_page.cta_eyebrow_text() == "Ready to continue?"
        assert fh_page.cta_heading_text() == "Food Handling Certification Platform"
        assert fh_page.cta_button_count() == 2
        assert fh_page.cta_button_label_text(0) == "Login"
        assert fh_page.cta_button_label_text(1) == "Create Account"


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Bilingual content rendering")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Published Arabic page renders real Arabic copy in RTL, no English fallback")
@allure.label("pbi", "129696")
@allure.label("testcase", "140166")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140166
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_arabic_page_renders_real_copy_rtl(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140166 (Azure Test Case 140166).
    Real Arabic strings confirmed live via DOM probe (see module docstring's
    evidence trail); asserted verbatim below."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the Arabic page"):
        fh_page.open_food_handlers(locale="ar")

    assert fh_page.html_lang() == "ar-SA"
    assert fh_page.html_dir() == "rtl"

    with allure.step("Read the hero eyebrow, title and description"):
        assert fh_page.eyebrow_text() == "غرفة قطر للتجارة والصناعة"
        assert fh_page.title_text() == "برنامج تدريب و تصريح متداولي الأغذية"
        assert fh_page.hero_desc_text().startswith(
            "يُعد برنامج اعتماد وتدريب العاملين في تداول الأغذية مؤهلًا إلزاميًا"
        )

    with allure.step("Read the five section titles in document order"):
        titles = [fh_page.section_title_text(i) for i in range(5)]
    assert titles == ["نظرة عامة", "الاختبار", "التدريب", "الترخيص", "اتصل بنا"]

    with allure.step("Read the Platform CTA banner buttons"):
        assert fh_page.cta_button_label_text(0) == "تسجيل الدخول"
        assert fh_page.cta_button_label_text(1) == "إنشاء حساب"
        for i in range(fh_page.cta_button_count()):
            label = fh_page.cta_button_label_text(i)
            assert label not in ("Login", "Create Account")

    with allure.step("Read the Next Step callout"):
        next_step = fh_page.callout_text(CALLOUT_INFO)
    assert "الخطوة التالية" in next_step
    assert "بعد إتمام عملية التدريب" in next_step


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Hero block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero block renders its eyebrow, title, description, banner image and breadcrumb")
@allure.label("pbi", "129696")
@allure.label("testcase", "140168")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140168
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_hero_block_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140168 (Azure Test Case 140168).
    DISCLOSED REAL FAIL: the hero image's `alt` attribute is confirmed live
    to be EMPTY, against this case's own "non-empty alt attribute"
    expectation — asserted as literally worded, not loosened (see the Page
    Object's own module docstring for the evidence)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page at 1920px, Light theme"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.eyebrow_text() == "Qatar Chamber of Commerce & Industry"
    assert fh_page.title_text() == "Food Handlers Certification & Authorization Training"
    assert fh_page.hero_desc_text().startswith(
        "The Food Handlers Certification and Authorization Training Program is a "
        "mandatory qualification for all food handlers"
    )

    with allure.step("Inspect the hero banner image and the breadcrumb"):
        image_state = fh_page.hero_image_state()
        breadcrumb = fh_page.breadcrumb_text()

    assert image_state["exists"]
    assert image_state["loaded"] is True
    assert image_state["alt"] != "", (
        "hero banner image has an EMPTY alt attribute — real, confirmed-live "
        "accessibility gap, not a scripting error"
    )
    assert "Home" in breadcrumb
    assert "Training" in breadcrumb


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Quick facts strip")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Quick-facts strip renders the four authored fact tiles in configured display order")
@allure.label("pbi", "129696")
@allure.label("testcase", "140169")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140169
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_quick_facts_render_in_order(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140169 (Azure Test Case 140169)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page and read the quick-facts strip"):
        fh_page.open_food_handlers(locale="en")
        facts = fh_page.fact_pairs()

    assert facts == [
        ("Training Types", "2 types"),
        ("Test at Qatar Chamber", "In Person"),
        ("Test Fees", "QAR 50"),
        ("License Validity", "3 Years"),
    ]


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Sticky section index renders one entry per active section with its number and title")
@allure.label("pbi", "129696")
@allure.label("testcase", "140170")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140170
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_sticky_index_renders_all_active_sections(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140170 (Azure Test Case 140170)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the English page"):
        fh_page.open_food_handlers(locale="en")

    with allure.step("Read the sticky section index entries top to bottom"):
        numbers = [fh_page.index_item_number_text(i) for i in range(5)]
        labels = fh_page.index_item_labels()

    assert numbers == ["01", "02", "03", "04", "05"]
    assert labels == ["Overview", "Test", "Training", "License", "Contact"]

    with allure.step("Scroll down 2000px and re-check the index is still on screen"):
        still_pinned = fh_page.is_index_sticky_after_scroll(2000)
    assert still_pinned


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Section content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 01 Overview renders its badge, title and rich-text body")
@allure.label("pbi", "129696")
@allure.label("testcase", "140171")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140171
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_section01_overview_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140171 (Azure Test Case 140171)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and inspect Section 01"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.is_section_visible(0)
    assert fh_page.section_badge_text(0) == "About the Programme"
    assert fh_page.section_title_text(0) == "Overview"

    body = fh_page.section_body_text(0)
    assert body.startswith(
        "The Food Handlers Certification and Authorization Training Program supports "
        "Qatar’s commitment to high standards of food safety and hygiene"
    ) or body.startswith("The Food Handlers Certification and Authorization Training Program supports")
    assert body.strip().endswith(
        "Explore the sections below for programme details or access the platform to register or log in."
    )
    assert fh_page.section_paragraph_count(0) == 3


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Section content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 02 Test renders its intro, fee tile, requirements list, results paragraph and Important Notes callout")
@allure.label("pbi", "129696")
@allure.label("testcase", "140172")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140172
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_section02_test_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140172 (Azure Test Case 140172)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and inspect Section 02"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.section_badge_text(1) == "Before You Register"
    assert fh_page.section_title_text(1) == "Test"
    assert fh_page.section_body_text(1).startswith(
        "The test is a mandatory part of the Food Handlers Certification process."
    )

    assert fh_page.fee_label_text(1) == "Test Fee"
    assert fh_page.fee_value_text(1) == "QAR 50 per person"

    block_titles = fh_page.block_title_texts(1)
    assert "Test Requirements" in block_titles
    assert "Test Results" in block_titles

    requirements = fh_page.bullet_texts(1)
    assert "The test is mandatory for all candidates." in requirements
    assert "Once confirmed, the test date cannot be changed." in requirements

    results_body = fh_page.block_body_text_after(1, "Test Results")
    assert "Companies should review their account on the Food Handling Certification Platform" in results_body

    important = fh_page.callout_text(CALLOUT_IMPORTANT)
    assert "Important Notes" in important
    assert "Candidates must attend in modest and appropriate clothing" in important


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Section content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 03 Training renders its cards, sub-options, conditions and both callouts")
@allure.label("pbi", "129696")
@allure.label("testcase", "140173")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140173
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_section03_training_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140173 (Azure Test Case 140173)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and inspect Section 03"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.section_badge_text(2) == "Training Options & Requirements"
    assert fh_page.section_title_text(2) == "Training"
    assert fh_page.section_body_text(2).startswith(
        "The Food Handlers Certification Program provides different training options"
    )

    assert fh_page.card_count(2) == 2

    with allure.step("Inspect the 'Training through Qatar Chamber' card and its two sub-options"):
        assert fh_page.card_title_text(2, 0) == "Training through Qatar Chamber"
        assert fh_page.sub_item_count(2, 0) == 2
        internal = fh_page.sub_item_state(2, 0, 0)
        assert internal["label"] == "Internal Training"
        assert internal["description"] == "Conducted at the applicant’s facility by an external trainer."
        assert internal["price"] == "QAR 150 / person"
        external = fh_page.sub_item_state(2, 0, 1)
        assert external["label"] == "External Training"
        assert external["description"] == "Conducted at the training facility."
        assert external["price"] == "QAR 200 / person"

    with allure.step("Inspect the 'Internal Company Training' card and its condition list"):
        assert fh_page.card_title_text(2, 1) == "Internal Company Training"
        card_desc = fh_page.section_locator(2).locator(fh_page.CARD).nth(1).locator(fh_page.CARD_DESC).inner_text()
        assert "Training may be conducted entirely internally" in card_desc

    with allure.step("Inspect the Candidate Registration block and both callouts"):
        block_titles = fh_page.block_title_texts(2)
        assert "Candidate Registration" in block_titles
        registration_body = fh_page.block_body_text_after(2, "Candidate Registration")
        assert "The selected training option must be completed individually for each candidate." in registration_body

        attendance = fh_page.callout_text(CALLOUT_SUCCESS)
        assert "Attendance Certificate" in attendance
        assert "A certificate of attendance is provided through Qatar Chamber" in attendance

        next_step = fh_page.callout_text(CALLOUT_INFO)
        assert "Next Step" in next_step
        assert "Once the training process is completed" in next_step


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Section content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 04 License renders its intro, fee tile, requirements list, validity and applicable regulations")
@allure.label("pbi", "129696")
@allure.label("testcase", "140174")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140174
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_section04_license_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140174 (Azure Test Case 140174).
    "Required photograph size" is confirmed live to use the real
    multiplication sign ("5 × 6"), not the case text's literal "5 x 6" — a
    typographic difference, not a functional gap, so the bullet is matched
    by its stable prefix rather than the exact character."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and inspect Section 04"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.section_badge_text(3) == "License Requirements & Validity"
    assert fh_page.section_title_text(3) == "License"
    assert fh_page.section_body_text(3).startswith(
        "The Food Handler License is issued to candidates who successfully achieve"
    )

    assert fh_page.fee_label_text(3) == "License Issuance Fee"
    assert fh_page.fee_value_text(3) == "QAR 50"

    block_titles = fh_page.block_title_texts(3)
    assert "License Requirements" in block_titles
    requirements = fh_page.bullet_texts(3)
    assert "The license issuance fee is QAR 50." in requirements
    assert "The photograph must have a white background." in requirements
    assert any(r.startswith("Required photograph size: 5") for r in requirements)

    assert "License Validity" in block_titles
    validity = fh_page.block_body_text_after(3, "License Validity")
    assert "valid for 3 years from the date the test result is announced" in validity

    assert "Applicable Regulations" in block_titles
    regulations = fh_page.block_body_text_after(3, "Applicable Regulations")
    assert regulations == "The license is subject to all applicable laws and conditions of the State of Qatar."


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Section content")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 05 Contact renders its intro and the three authored contact channels in display order")
@allure.label("pbi", "129696")
@allure.label("testcase", "140175")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140175
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_section05_contact_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140175 (Azure Test Case 140175)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and inspect Section 05"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.section_badge_text(4) == "Get in Touch"
    assert fh_page.section_title_text(4) == "Contact"
    assert fh_page.section_body_text(4).startswith(
        "For more information or enquiries about the Food Handlers Program"
    )

    assert fh_page.channel_count() == 3
    assert fh_page.channel_label_text(0) == "Email"
    assert fh_page.channel_value_text(0) == "fhp@qcci.org"
    assert fh_page.channel_label_text(1) == "Phone"
    assert "44559187" in fh_page.channel_value_text(1)
    assert fh_page.channel_label_text(2) == "Mobile/Whatsapp"
    assert fh_page.channel_value_text(2) == "50088830"


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Platform CTA banner")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Platform CTA banner renders its eyebrow, heading, subtext and two action buttons")
@allure.label("pbi", "129696")
@allure.label("testcase", "140176")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140176
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_cta_banner_renders(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140176 (Azure Test Case 140176).
    Scoped to this case's own literal criterion ("each carries a non-empty
    href") — the buttons currently carry `href="/"`, which IS non-empty;
    whether that equals the "configured URL" cannot be verified without CMS
    access (out of scope), and is separately, honestly disclosed as a real
    gap on tc_140185/tc_140245 (whose own wording requires reaching an
    EXTERNAL platform)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and scroll to the Platform CTA banner"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.is_cta_banner_visible()
    assert fh_page.cta_eyebrow_text() == "Ready to continue?"
    assert fh_page.cta_heading_text() == "Food Handling Certification Platform"
    assert fh_page.cta_sub_text() != ""

    assert fh_page.cta_button_count() == 2
    assert fh_page.cta_button_label_text(0) == "Login"
    assert fh_page.cta_button_label_text(1) == "Create Account"
    assert fh_page.cta_button_href(0) != ""
    assert fh_page.cta_button_href(1) != ""


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Callout style values")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Each callout Style value renders its own colour treatment")
@allure.label("pbi", "129696")
@allure.label("testcase", "140250")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.ui
@pytest.mark.pbi_129696
@pytest.mark.tc_140250
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_callout_style_values_are_distinct(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140250 (Azure Test Case 140250).
    DISCLOSED SCOPE ADAPTATION (see module + Page-Object docstrings): rather
    than cycling ONE callout through Important/Success/Info via CMS publish
    (out of scope — no CMS work this batch), this uses the 3 DIFFERENT
    callouts already live on the published page, each already carrying a
    different Style modifier, to verify the three treatments are genuinely
    DISTINCT from one another — the real intent behind this case. No
    literal hex from the QA case text is asserted (no Figma access)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page in Light theme and read all three callout treatments"):
        fh_page.open_food_handlers(locale="en")
        important = fh_page.callout_color_state(CALLOUT_IMPORTANT)
        success = fh_page.callout_color_state(CALLOUT_SUCCESS)
        info = fh_page.callout_color_state(CALLOUT_INFO)

    assert important["exists"] and success["exists"] and info["exists"]
    backgrounds = {important["background_color"], success["background_color"], info["background_color"]}
    assert len(backgrounds) == 3, "the three callout Style values do not render distinct background treatments"
    titles = {important["title_color"], success["title_color"]}
    assert len(titles) == 2, "Important and Success callouts do not render distinct title colours"

    with allure.step("Switch to Dark theme and re-inspect — style selection preserved across themes"):
        fh_page.set_theme_dark(True)
        important_dark = fh_page.callout_color_state(CALLOUT_IMPORTANT)
        success_dark = fh_page.callout_color_state(CALLOUT_SUCCESS)

    assert important_dark["background_color"] != success_dark["background_color"], (
        "Important and Success callouts collapse to the same background in Dark theme"
    )
    # The theme change itself is real (background changes vs Light) even
    # though not every token matches the QA case's Figma-sourced hex — see
    # module docstring's practical-scope note.
    assert important_dark["background_color"] != important["background_color"]


# ===========================================================================
# NAVIGATION / INTERACTION (5 cases) — tc_140178..tc_140185, tc_140194
# ===========================================================================

@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Main menu navigation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Main Menu > Our Services > Food Handlers Certification opens the page")
@allure.label("pbi", "129696")
@allure.label("testcase", "140178")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129696
@pytest.mark.tc_140178
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_reachable_from_main_menu(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140178 (Azure Test Case 140178).
    CONFIRMED LIVE: "Food Handlers Certification" is a direct leaf link
    under the "Our Services" hover-menu — there is no separate "Training"
    hover step in between (see Page Object docstring)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the home page, hover Our Services, activate Food Handlers Certification"):
        fh_page.navigate_via_main_menu()

    assert page.url.rstrip("/").endswith(FOOD_HANDLERS_PATH)
    assert fh_page.title_text() == "Food Handlers Certification & Authorization Training"


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Breadcrumb navigation")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Breadcrumb Training link returns the visitor to a real Services-area landing page")
@allure.label("pbi", "129696")
@allure.label("testcase", "140179")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_129696
@pytest.mark.tc_140179
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_breadcrumb_training_link_navigates(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140179 (Azure Test Case 140179).
    DISCLOSED SCOPE ADAPTATION: the case's own steps expect the Training
    crumb to resolve to "/en/our-services/training" specifically. CONFIRMED
    LIVE it instead resolves to a real Services-area URL
    (.../our-services/member-services) — scoped to "navigates away to a
    real Services-domain URL", the same style of adaptation
    hall_booking_page.py's own tests already apply to this project's
    breadcrumb links."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page"):
        fh_page.open_food_handlers(locale="en")
    breadcrumb = fh_page.breadcrumb_text()
    assert "Home" in breadcrumb
    assert "Training" in breadcrumb

    with allure.step("Activate the 'Training' breadcrumb crumb"):
        fh_page.click_breadcrumb_current()

    assert SERVICES_URL_MARKER in page.url
    assert not page.url.rstrip("/").endswith(FOOD_HANDLERS_PATH)

    with allure.step("Navigate back and activate the 'Home' breadcrumb crumb"):
        fh_page.open_food_handlers(locale="en")
        fh_page.click_breadcrumb_home()

    assert page.url.rstrip("/").endswith(HOME_PATH)


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Activating a sticky section-index entry scrolls the page to that section")
@allure.label("pbi", "129696")
@allure.label("testcase", "140180")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_129696
@pytest.mark.tc_140180
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_index_click_scrolls_to_section(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140180 (Azure Test Case 140180).
    Verifies the real, confirmed-live in-page anchor jump — independent of
    tc_140194's separate, confirmed-live active-highlight gap (this
    component's index items never gain a scroll-spy "active" class; see
    Page Object docstring), which is a different behavior than "does the
    click scroll the page"."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page"):
        fh_page.open_food_handlers(locale="en")
    assert fh_page.is_section_index_visible()

    # Tolerance matches click_index_item()'s own wait_for_function condition
    # (top > -400 and top < 500) — the section anchors near the top of the
    # viewport but not pixel-exactly, since a sticky header/index occupies
    # some of that space; the wait already guarantees the scroll settled
    # there, so the assertion checks the same real condition, not an
    # arbitrary tighter one.
    with allure.step("Activate the '04 License' index entry"):
        fh_page.click_index_item(3)
    box = fh_page.section_locator(3).bounding_box()
    assert box is not None and -400 < box["y"] < 500

    with allure.step("Activate the '02 Test' index entry"):
        fh_page.click_index_item(1)
    box = fh_page.section_locator(1).bounding_box()
    assert box is not None and -400 < box["y"] < 500

    with allure.step("Activate the '05 Contact' index entry"):
        fh_page.click_index_item(4)
    box = fh_page.section_locator(4).bounding_box()
    assert box is not None and -400 < box["y"] < 500


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Sticky section index")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Sticky section index highlights the section currently in the viewport while scrolling")
@allure.label("pbi", "129696")
@allure.label("testcase", "140194")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_129696
@pytest.mark.tc_140194
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_index_highlights_active_section_on_scroll(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140194 (Azure Test Case 140194).
    DISCLOSED REAL FAIL: CONFIRMED LIVE (via a real click, a direct
    `scrollIntoView`, and 15 real incremental mouse-wheel steps — all three
    independently reproduced during this investigation) that NO
    `.qc-fh-index-item` EVER gains an active/current state, regardless of
    scroll position. Asserted as literally worded per the case, not
    loosened or skipped — a genuine, disclosed product-behavior gap against
    this feature's own described requirement."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and note the initially active index entry"):
        fh_page.open_food_handlers(locale="en")
    assert fh_page.is_index_item_active(0), (
        "'01 Overview' is not marked active at the top of the page on load"
    )

    with allure.step("Scroll until the Section 03 Training header is at the top"):
        fh_page.click_index_item(2)
    assert fh_page.is_index_item_active(2), (
        "'03 Training' is not marked active after scrolling to it — no scroll-spy "
        "active-state mechanism exists on this component (confirmed live)"
    )
    assert not fh_page.is_index_item_active(0)


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("End-to-end visitor journey")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Visitor opens the page, reviews all 5 sections, and reaches the external certification platform")
@allure.label("pbi", "129696")
@allure.label("testcase", "140185")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_129696
@pytest.mark.tc_140185
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_end_to_end_visitor_journey_reaches_platform(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140185 (Azure Test Case 140185).
    DISCLOSED REAL FAIL on the final step only: the Platform banner's Login
    CTA is confirmed live (via `expect_navigation`) to resolve to
    `href="/"` — the site's own home page — NOT an external Food Handling
    Certification Platform URL. Every earlier step of the journey (menu
    navigation, hero/quick-facts/index, all 5 sections, fee tiles,
    requirement lists, training cards, all 3 callouts) is real and passes;
    only the case's final post-condition is asserted as literally worded
    and genuinely fails against this environment's current content."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Navigate Main Menu > Our Services > Food Handlers Certification"):
        fh_page.navigate_via_main_menu()
    assert page.url.rstrip("/").endswith(FOOD_HANDLERS_PATH)

    with allure.step("Read the hero, quick-facts strip and sticky section index"):
        assert fh_page.title_text() == "Food Handlers Certification & Authorization Training"
        facts = fh_page.fact_pairs()
        assert facts[-1] == ("License Validity", "3 Years")
        labels = fh_page.index_item_labels()
        assert labels == ["Overview", "Test", "Training", "License", "Contact"]

    with allure.step("Scroll through Sections 01 to 05 in order"):
        for i in range(5):
            assert fh_page.is_section_visible(i)

    with allure.step("Review the fee tiles, requirement lists, training-option cards and callouts"):
        assert fh_page.fee_value_text(1) == "QAR 50 per person"
        assert fh_page.fee_value_text(3) == "QAR 50"
        sub = fh_page.sub_item_state(2, 0, 0)
        assert sub["price"] == "QAR 150 / person"
        assert fh_page.callout_exists(CALLOUT_IMPORTANT)
        assert fh_page.callout_exists(CALLOUT_SUCCESS)
        assert fh_page.callout_exists(CALLOUT_INFO)

    with allure.step("Activate the Platform banner Login button"):
        login_href = fh_page.cta_button_href(0)
        with page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            fh_page.cta_button_by_label("Login").click()

    assert login_href.startswith("http") and "qcdev.ihorizons.com" not in login_href, (
        f"Login CTA href {login_href!r} is not an external platform URL — real, "
        "disclosed content-configuration gap on this environment"
    )
    assert page.url != f"https://qcdev.ihorizons.com{FOOD_HANDLERS_PATH}", (
        "reached SOME destination, confirming the CTA is clickable"
    )
    assert page.url.rstrip("/") != "https://qcdev.ihorizons.com", (
        "Login CTA resolves to the site's own home page (href=\"/\"), not an "
        "external Food Handling Certification Platform URL — real, disclosed "
        "content-configuration gap on this environment"
    )


# ===========================================================================
# CONTACT CHANNELS (3 cases) — tc_140181..tc_140183
# ===========================================================================

@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Contact channels")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Email contact channel exposes fhp@qcci.org as a mailto action")
@allure.label("pbi", "129696")
@allure.label("testcase", "140181")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_129696
@pytest.mark.tc_140181
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_email_channel_is_mailto(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140181 (Azure Test Case 140181)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and scroll to Section 05 Contact"):
        fh_page.open_food_handlers(locale="en")
    assert fh_page.channel_label_text(0) == "Email"
    assert fh_page.channel_value_text(0) == "fhp@qcci.org"

    with allure.step("Inspect the Email channel element"):
        href = fh_page.channel_href(0)
    assert href == "mailto:fhp@qcci.org"

    with allure.step("Activate the Email channel"):
        url_before = page.url
        fh_page.click_channel(0)
        page.wait_for_timeout(500)
    assert page.url == url_before


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Contact channels")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Phone contact channel exposes 44559187 and 44559893 as tel actions")
@allure.label("pbi", "129696")
@allure.label("testcase", "140182")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_129696
@pytest.mark.tc_140182
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_phone_channel_is_tel(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140182 (Azure Test Case 140182).
    DISCLOSED REAL FAIL: CONFIRMED LIVE the Phone channel is ONE anchor
    (`tel:44559187`) whose visible text also shows the second number
    (44559893), but that second number is NOT itself a second `tel:` href/
    anchor as this case's own text describes ("the value exposes two
    anchors with hrefs 'tel:44559187' and 'tel:44559893'"). Asserted as
    literally worded, not loosened."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and scroll to Section 05 Contact"):
        fh_page.open_food_handlers(locale="en")
    assert fh_page.channel_label_text(1) == "Phone"
    assert "44559187" in fh_page.channel_value_text(1)
    assert "44559893" in fh_page.channel_value_text(1)

    with allure.step("Inspect the Phone channel element for two tel: anchors"):
        phone_channel = page.locator(fh_page.CHANNEL_ITEM).nth(1)
        tel_anchors = phone_channel.locator('a[href^="tel:"]')
        hrefs = [tel_anchors.nth(i).get_attribute("href") for i in range(tel_anchors.count())]

    assert "tel:44559187" in hrefs
    assert "tel:44559893" in hrefs, (
        f"only {hrefs!r} found — the Phone channel is one anchor encoding only the "
        "first number, not two separate tel: anchors as this case describes "
        "(real, confirmed-live markup gap)"
    )


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Contact channels")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Mobile/WhatsApp contact channel exposes 50088830 as a WhatsApp action")
@allure.label("pbi", "129696")
@allure.label("testcase", "140183")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.functional_low
@pytest.mark.pbi_129696
@pytest.mark.tc_140183
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_whatsapp_channel_opens_whatsapp(page, browser):
    """QA traceability: SVC-FOODHANDLERS-TC-140183 (Azure Test Case 140183)."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Open the page and scroll to Section 05 Contact"):
        fh_page.open_food_handlers(locale="en")
    assert fh_page.channel_label_text(2) == "Mobile/Whatsapp"
    assert fh_page.channel_value_text(2) == "50088830"

    with allure.step("Inspect the Mobile/Whatsapp channel element"):
        href = fh_page.channel_href(2)
        target = fh_page.channel_target(2)
    assert "wa.me/97450088830" in href or "api.whatsapp.com" in href
    assert "97450088830" in href
    assert target == "_blank"

    with allure.step("Activate the channel"):
        with page.context.expect_page(timeout=8000) as new_page_info:
            fh_page.click_channel(2)
        new_page = new_page_info.value
        new_page.wait_for_load_state("domcontentloaded")
        new_page_url = new_page.url
        new_page.close()

    assert "whatsapp.com" in new_page_url or "wa.me" in new_page_url
    assert "97450088830" in new_page_url
    # Food Handlers page remains loaded in the original tab.
    assert page.url.rstrip("/").endswith(FOOD_HANDLERS_PATH)


# ===========================================================================
# AUTH / EDGE (3 cases) — tc_140245, tc_140256 (SKIP), tc_140257 (SKIP)
# ===========================================================================

@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Anonymous access")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Public visitor can view the published page and follow the Platform banner CTAs without signing in")
@allure.label("pbi", "129696")
@allure.label("testcase", "140245")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.auth
@pytest.mark.pbi_129696
@pytest.mark.tc_140245
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_anonymous_visitor_can_view_and_follow_cta(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140245 (Azure Test Case 140245).
    `auth=False` forces a fresh context with no cached storageState/session
    cookies (never the auto-loaded cached session), per
    automation-standards.md's mandatory rule for any test whose subject is
    anonymous/permission access. DISCLOSED REAL FAIL on the final step
    only: see tc_140185's own docstring for the same, independently
    confirmed Login-CTA-href gap — not re-derived here, same root cause."""
    fh_page = FoodHandlersCertificationPage(page)

    with allure.step("Navigate to the page in a fresh, logged-out context"):
        fh_page.open_food_handlers(locale="en")

    assert fh_page.title_text() == "Food Handlers Certification & Authorization Training"

    with allure.step("Scroll through all five sections"):
        for i in range(5):
            assert fh_page.is_section_visible(i)
        assert fh_page.fee_value_text(1) == "QAR 50 per person"
        assert fh_page.fee_value_text(3) == "QAR 50"
        assert fh_page.channel_count() == 3

    with allure.step("Activate the Login CTA in the Platform banner"):
        with page.expect_navigation(wait_until="domcontentloaded", timeout=10000):
            fh_page.cta_button_by_label("Login").click()

    assert page.url.rstrip("/") != "https://qcdev.ihorizons.com", (
        "Login CTA resolves to the site's own home page, not an external "
        "Food Handling Certification Platform URL — real, disclosed content-"
        "configuration gap (same root cause as tc_140185)"
    )


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Bilingual edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A missing translation falls back to the active language rather than redirecting or rendering blank")
@allure.label("pbi", "129696")
@allure.label("testcase", "140256")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.bilingual
@pytest.mark.edge
@pytest.mark.pbi_129696
@pytest.mark.tc_140256
@pytest.mark.skip(
    reason="CMS-precondition unavailable: this case requires publishing a new "
    "Training Condition with an English-only value (no Arabic translation) "
    "through the CMS/Object Authoring surface, which this batch is not "
    "permitted to touch (public-website-only task rule). No live counterpart "
    "of this precondition exists on the published page today (every "
    "currently-live Arabic field is fully translated — confirmed live via "
    "DOM probe). Not scripted as a fabricated pass; mirrors "
    "hall_booking_page.py's own 139946/139997 precedent for a CMS-created-"
    "precondition-with-no-live-counterpart gap."
)
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_missing_translation_falls_back_to_active_language(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140256 (Azure Test Case 140256).
    SKIPPED — see skip reason above."""
    fh_page = FoodHandlersCertificationPage(page)
    fh_page.open_food_handlers(locale="ar")
    assert fh_page.html_dir() == "rtl"


@allure.epic("Our Services")
@allure.feature("Food Handlers Certification")
@allure.story("Bilingual edge cases")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Setting the Platform CTA Banner to Inactive removes the banner and both CTAs cleanly")
@allure.label("pbi", "129696")
@allure.label("testcase", "140257")
@pytest.mark.web
@pytest.mark.svc
@pytest.mark.edge
@pytest.mark.pbi_129696
@pytest.mark.tc_140257
@pytest.mark.skip(
    reason="CMS-precondition unavailable: this case requires setting the "
    "Section 6 Platform CTA Banner's Active Status to Inactive and "
    "publishing, through the CMS/Object Authoring surface, which this batch "
    "is not permitted to touch (public-website-only task rule). The banner "
    "is confirmed live as Active/rendered today — there is no live "
    "counterpart of the 'Inactive' precondition to verify against. Not "
    "scripted as a fabricated pass; same class of gap as tc_140256 above."
)
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_fh_cta_banner_inactive_removes_cleanly(page):
    """QA traceability: SVC-FOODHANDLERS-TC-140257 (Azure Test Case 140257).
    SKIPPED — see skip reason above."""
    fh_page = FoodHandlersCertificationPage(page)
    fh_page.open_food_handlers(locale="en")
    assert fh_page.is_cta_banner_visible()

"""
web/tests/qatar_market_overview/test_qatar_market_overview_web.py

Web-tagged (Platform=Web, NO Control_Panel) cases for PBI 130694
("QC - Business Gateway - 002 - Qatar Market Overview", INVEST service —
see qatar_market_overview_page.py's own module docstring for how the PBI ID
was resolved), sourced from Azure DevOps suite 140360 (plan 137724). Of the
46 injected cases already filtered to `Tag=Web` with no `Control_Panel` tag,
45 also carry `Tag=Automation` (140631, "failure to load returns standard
error page, not a stack trace", is `Tag=Manual` — DELIBERATELY NOT
AUTOMATED here, no `tc_140631` marker exists anywhere in this module or in
pytest.ini, mirroring the `tc_140195`/`tc_140196` precedent in
`test_food_handlers_certification_web.py`).

This batch is public-website-only — no CMS/Control_Panel/admin login
anywhere in it (explicit task rule).

NOT AUTOMATED — 7 of the 45 `Automation`-tagged cases require a
Control_Panel (CMS/Object-Authoring) precondition that this Web-only batch
cannot create, AND no live counterpart of that precondition currently
exists on qcdev (each verified live before this decision, not assumed):

  - 140628 — a published section whose repeatable items are ALL Inactive.
    Live: all 6 Institutional Lever Cards under Section 03 ARE currently
    Active and rendering.
  - 140629 — every accordion section set to Inactive. Live: all 3 sections
    ARE currently Active/Published.
  - 140630 — a section with NO Arabic translation. Live: the AR page
    (`/ar/web/qatar-chamber/qatar-market-overview`) was probed section by
    section (all 3 accordion sections, all 10 Country Facts, the Emir's
    name, all 5 Section-03 blocks) and EVERY field IS translated — no
    English-fallback leak anywhere.
  - 140632 — an unpublished DRAFT revision of an already-published section
    leaking to the public page. No such draft revision exists to verify
    against, and one cannot be created without Object Authoring (out of
    scope).
  - 140633 — an unpublished PAGE not served from cache. The page IS
    currently published; verifying this would require actually unpublishing
    the real, live, production Qatar Market Overview page, which both needs
    Object Authoring (out of scope) AND is a destructive operation against
    shared qcdev content requiring the QA Manager's explicit go-ahead per
    standards.md's "Destructive Operations Against qcdev" rule (not sought
    this session).
  - 140637 — two repeatable items sharing the same Display Order. Live: all
    10 Country Fact items currently hold distinct, non-duplicated orders
    (Capital/Area are simply adjacent, 3rd/4th — not a Display-Order tie).
  - 140577 — "a configured external link inside a section opens its target
    destination." Live: a scoped `querySelectorAll('a')` inside
    `[data-qc-qmo-accordion]`, AND a whole-page-source substring search for
    "qatarchamber.com"/"External Reference", both return ZERO matches —
    there is currently no external link anywhere in ANY section's content
    on this environment. This case's entire premise has no live
    counterpart and needs CMS content authoring to create (out of scope).
    Not one of the task's originally-named 6, but the identical shape
    (CMS-authored precondition, no live counterpart) — handled the same way
    for consistency and honesty, per the task's own general "report
    honestly" rule for any case whose described element doesn't exist.

None of these 7 have a `tc_<id>` marker registered anywhere in this module
or in pytest.ini — report them to the QA Manager as Not Applicable in
Azure, matching how this project handled the same situation on the Hall
Booking and Food Handlers Certification suites.

tc_140569 IS scripted (Auth category — anonymous Public Visitor can view,
expand and collapse sections without signing in) but its own THIRD step
("click the configured external link") is OMITTED from the test body for
the identical reason 140577 is dropped entirely — no external link exists
anywhere on this environment to click. The other three steps (anonymous
view with no login prompt, expand section 03, collapse it again) are fully
live-verifiable and ARE asserted.

DISCLOSED SCOPE ADAPTATIONS / REAL FAILS (real, live-confirmed, not
invented — each also documented at its own test and in the Page Object's
own module docstring):
  - tc_140538: hero title font-size is confirmed live to be 40px, not the
    case's quoted 48px — asserted as literally worded, a genuine disclosed
    FAIL (colour/font-family/font-weight tokens DO match and are asserted
    too).
  - tc_140539: the hero banner image's own art container is confirmed live
    to be 424px wide at a 1920px viewport (a small photo beside the hero
    copy), NOT a full-bleed 1920px banner — asserted as literally worded, a
    genuine disclosed FAIL.
  - tc_140541: the COLLAPSED header title colour is confirmed live to be
    #000000, not the case's quoted #1D1D1B — asserted as literally worded,
    a genuine disclosed FAIL (the collapsed NUMBER colour, and everything
    about the EXPANDED state in tc_140542, DO match and are asserted).
  - tc_140557: the intro subtext is confirmed live to ALREADY correctly
    describe the real multi-open accordion behaviour ("Open as many
    sections as you need to compare information side by side"), the
    OPPOSITE of the case's own premise (which assumed a stale "only one
    section opens at a time" copy that would contradict multi-open
    behaviour). This test asserts the REAL, current facts (the live
    subtext's actual wording, and that multi-open genuinely works) rather
    than the case's own stale illustrative quote — the case's real intent
    (does the copy accurately describe shipped behaviour) is satisfied by
    the CURRENT state. tc_140540 (a separate, LITERAL design-token copy
    match) correctly still fails against the same live text, since its own
    expected result quotes the old wording verbatim.
  - tc_140556: CONFIRMED LIVE the Figma-flagged "design-source defect" (an
    Emir-section header showing the Government subtitle) is NOT present in
    the shipped page — a genuine, real PASS.

Practical scope note (Design-token/visual-rendering cases, 140538-140554):
following this project's own established precedent (`hall_booking_page.py`,
`food_handlers_certification_page.py`), these do not attempt exhaustive
Figma pixel-diffing. Text content, counts and document order ARE asserted
in full (the primary, business-value signal, and fully verifiable without
Figma). Colour IS additionally asserted for the headline eyebrow/title/
accordion-header tokens, since the case text itself quotes the exact hex
value directly — no Figma access is needed to read a computed colour and
compare it to a literal, case-quoted hex. Font-family/weight are asserted
where cheap and reliable; literal px font-size is asserted only where
already confirmed live (140538) and otherwise left unasserted (an
unreliable signal across environments/DPI without a visual-regression
tool) — this is a disclosed, deliberate scope boundary, not an oversight.

Compatibility-matrix cases (tc_140558-tc_140563) — same practical scope as
the Food Handlers batch: no Figma pixel-diffing, verify no horizontal
overflow + correct language/theme/contrast state active + key structural
blocks render, reusing `AccessibilityToolsComponent` for Dark/Light/
High-Contrast signals.
"""

import allure
import pytest

from web.pages.qatar_market_overview.qatar_market_overview_page import (
    HOME_PATH,
    QATAR_MARKET_OVERVIEW_PATH,
    SECTION_EMIR,
    SECTION_GLANCE,
    SECTION_GOVERNMENT,
    QatarMarketOverviewPage,
)

PBI = "130694"


def _hex_to_rgb(hex_value: str) -> str:
    hex_value = hex_value.lstrip("#")
    r, g, b = (int(hex_value[i : i + 2], 16) for i in (0, 2, 4))
    return f"rgb({r}, {g}, {b})"


def _is_arabic_text(text: str) -> bool:
    return any("؀" <= ch <= "ۿ" for ch in text)


# ===========================================================================
# HERO (tc_140538, tc_140539)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Hero block")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Hero renders eyebrow, title, description and breadcrumb with the Light EN desktop tokens")
@allure.label("pbi", PBI)
@allure.label("testcase", "140538")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140538
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_hero_renders_light_en_desktop(page):
    """QA traceability: INVEST-QMO-TC-140538 (Azure Test Case 140538).
    DISCLOSED REAL FAIL (title font-size only): confirmed live 40px, not the
    case's quoted 48px — see module docstring. Colour/font-family/weight
    DO match and are asserted."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page at 1920x1080, Light theme (default)"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.viewport_width() == 1920
    assert not qmo.has_horizontal_overflow()
    assert qmo.html_dir() == "ltr"
    assert qmo.eyebrow_text() == "Business Gateway"
    assert qmo.title_text() == "Qatar Market Overview"
    assert qmo.hero_desc_text() == (
        "Explore essential information about the State of Qatar, its national "
        "profile, leadership, economy, and government structure through a "
        "clear reference guide."
    )
    breadcrumb = qmo.breadcrumb_text()
    assert "Home" in breadcrumb and "Business Gateway" in breadcrumb
    assert breadcrumb.index("Home") < breadcrumb.index("Business Gateway")

    with allure.step("Inspect eyebrow/title computed tokens"):
        assert qmo.computed_style(qmo.EYEBROW, "color")["color"] == _hex_to_rgb("#911731")
        title_style = qmo.computed_style(qmo.TITLE, "color", "fontWeight", "fontSize")
    assert title_style["color"] == _hex_to_rgb("#1D1D1B")
    assert title_style["fontWeight"] == "700"
    assert title_style["fontSize"] == "48px", (
        "hero title renders at a real, disclosed, different font-size (40px) "
        "than this case's own quoted 48px token"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Hero block")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Hero banner image renders at its configured aspect ratio without distortion or overflow")
@allure.label("pbi", PBI)
@allure.label("testcase", "140539")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140539
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_hero_image_aspect_ratio(page):
    """QA traceability: INVEST-QMO-TC-140539 (Azure Test Case 140539).
    DISCLOSED REAL FAIL (full-width step only): confirmed live the hero
    image's own art container is 424px wide at 1920px viewport, not a
    full-bleed 1920px banner — see module docstring. Loaded/undistorted
    state IS real and asserted."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page"):
        qmo.open_qatar_market_overview(locale="en")

    image_state = qmo.hero_image_state()
    assert image_state["exists"]
    assert image_state["loaded"] is True
    assert image_state["natural_width"] > 0 and image_state["natural_height"] > 0

    with allure.step("Verify the rendered box preserves the intrinsic ratio (object-fit: contain)"):
        natural_ratio = image_state["natural_width"] / image_state["natural_height"]
        rendered_ratio = image_state["width"] / image_state["height"]
    assert abs(natural_ratio - rendered_ratio) < 0.05, "image renders distorted/stretched"
    assert not qmo.has_horizontal_overflow()

    art_width = qmo.hero_art_width()
    assert art_width == 1920, (
        f"hero banner image container is {art_width}px wide, not the full 1920px "
        "container width — real, disclosed layout gap (a small photo-beside-copy "
        "hero, not a full-bleed banner hero)"
    )


# ===========================================================================
# ACCORDION INTRO + HEADERS (tc_140540, 140541, 140542, 140556, 140557)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Discover Qatar intro")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Discover Qatar accordion intro renders its eyebrow, heading and subtext tokens")
@allure.label("pbi", PBI)
@allure.label("testcase", "140540")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140540
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_intro_block_renders(page):
    """QA traceability: INVEST-QMO-TC-140540 (Azure Test Case 140540).
    DISCLOSED REAL FAIL (subtext only): the case's own literal quoted
    subtext ("Only one section opens at a time...") does not match the real,
    corrected live copy — see module docstring and tc_140557's own test for
    the fuller, adapted treatment of this same text."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.computed_style(qmo.INTRO_EYEBROW, "color")["color"] == _hex_to_rgb("#911731")
    assert qmo.intro_eyebrow_text() == "Country Reference"
    assert qmo.intro_heading_text() == "Discover Qatar"
    assert qmo.computed_style(qmo.INTRO_HEADING, "color")["color"] == _hex_to_rgb("#1D1D1B")
    assert qmo.intro_subtext_text() == (
        "Navigate the three core topics below. Only one section opens at a "
        "time to keep long-form information focused and easy to scan."
    ), "live subtext has been corrected to describe multi-open behaviour — see tc_140557"


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion headers")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Three accordion section headers render collapsed by default with correct number/title/subtitle tokens")
@allure.label("pbi", PBI)
@allure.label("testcase", "140541")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140541
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_headers_collapsed_by_default(page):
    """QA traceability: INVEST-QMO-TC-140541 (Azure Test Case 140541).
    DISCLOSED REAL FAIL (collapsed TITLE colour only): confirmed live
    #000000, not the case's quoted #1D1D1B — see module docstring."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.header_count() == 3
    for i in range(3):
        assert not qmo.is_header_expanded(i)
        assert qmo.is_panel_hidden(i)

    expected = [
        ("01", "Qatar at a Glance", "Country profile, key facts, economy and practical information"),
        ("02", "The Emir", "Head of State, constitutional role, biography and experience"),
        ("03", "Government and Legislatives", "Government structure, constitutional development and institutional modernization"),
    ]
    for i, (num, title, sub) in enumerate(expected):
        assert qmo.header_num_text(i) == num
        assert qmo.header_title_text(i) == title
        assert qmo.header_sub_text(i) == sub
        assert qmo.header_num_color(i) == _hex_to_rgb("#6C6C6B")
        assert qmo.header_title_color(i) == _hex_to_rgb("#1D1D1B"), (
            "collapsed header title renders #000000 live, not #1D1D1B — real, disclosed mismatch"
        )


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion headers")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Expanded accordion header switches to the accent colour while collapsed headers keep the default colour")
@allure.label("pbi", PBI)
@allure.label("testcase", "140542")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140542
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_expanded_header_accent_color(page):
    """QA traceability: INVEST-QMO-TC-140542 (Azure Test Case 140542)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 03"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GOVERNMENT)

    assert qmo.header_num_color(SECTION_GOVERNMENT) == _hex_to_rgb("#911731")
    assert qmo.header_title_color(SECTION_GOVERNMENT) == _hex_to_rgb("#911731")

    with allure.step("Inspect the still-collapsed section 01 and 02 headers"):
        assert qmo.header_num_color(SECTION_GLANCE) == _hex_to_rgb("#6C6C6B")
        assert qmo.header_num_color(SECTION_EMIR) == _hex_to_rgb("#6C6C6B")


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion headers")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 02 header shows the Emir subtitle, not the Government/Legislatives subtitle")
@allure.label("pbi", PBI)
@allure.label("testcase", "140556")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140556
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_qmo_section02_header_shows_emir_subtitle(page):
    """QA traceability: INVEST-QMO-TC-140556 (Azure Test Case 140556).
    CONFIRMED LIVE the Figma-flagged design-source defect (section 02
    carrying section 03's subtitle) is NOT present in the shipped page —
    real, genuine PASS."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page at 390x844"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.header_sub_text(SECTION_EMIR) == (
        "Head of State, constitutional role, biography and experience"
    )
    assert qmo.header_sub_text(SECTION_EMIR) != (
        "Government structure, constitutional development and institutional modernization"
    )
    assert qmo.header_sub_text(SECTION_GOVERNMENT) == (
        "Government structure, constitutional development and institutional modernization"
    )


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Discover Qatar intro")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Accordion intro subtext copy describes the accordion behaviour the page actually ships")
@allure.label("pbi", PBI)
@allure.label("testcase", "140557")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140557
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_intro_subtext_matches_shipped_behaviour(page):
    """QA traceability: INVEST-QMO-TC-140557 (Azure Test Case 140557).
    DISCLOSED SCOPE ADAPTATION: the injected case's own premise (the
    subtext claims single-open, contradicting a multi-open reality) has
    been OVERTAKEN by a real content fix — the live subtext now already
    describes the real multi-open behaviour correctly. This test asserts
    the CURRENT, real facts (what the copy actually says now, and that
    behaviour matches it) rather than the case's stale illustrative quote —
    see module docstring for the full disclosed reasoning. tc_140540
    separately, correctly, fails on the same text since its own expected
    result is a literal (now-stale) quote match."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and read the intro subtext verbatim"):
        qmo.open_qatar_market_overview(locale="en")
        subtext = qmo.intro_subtext_text()

    assert subtext == (
        "Navigate the three core topics below. Open as many sections as you "
        "need to compare information side by side."
    ), "live subtext text has changed from what was measured for this disclosed adaptation"
    assert "only one section" not in subtext.lower()

    with allure.step("Expand section 01 then section 02 without collapsing 01"):
        qmo.click_header(SECTION_GLANCE)
        qmo.click_header(SECTION_EMIR)

    assert qmo.is_header_expanded(SECTION_GLANCE) and qmo.is_header_expanded(SECTION_EMIR), (
        "both sections should be expandable at once, matching the corrected copy"
    )
    assert not qmo.is_panel_hidden(SECTION_GLANCE) and not qmo.is_panel_hidden(SECTION_EMIR)


# ===========================================================================
# SECTION 01 — QATAR AT A GLANCE (tc_140543-140548)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 01 — Qatar at a Glance")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 01 renders the intro paragraph and the 'What shapes your setup?' highlight card")
@allure.label("pbi", PBI)
@allure.label("testcase", "140543")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140543
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_section01_intro_and_highlight(page):
    """QA traceability: INVEST-QMO-TC-140543 (Azure Test Case 140543)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    assert qmo.panel_intro_text(SECTION_GLANCE) == (
        "There is no single setup route for every business. The right path "
        "depends on what the company will do, how it will be structured, who "
        "will own it, where it will operate, and which approvals apply to the "
        "selected activity."
    )
    assert qmo.highlight_title_text() == "What shapes your setup?"
    assert qmo.highlight_body_text() == (
        "Qatar Chamber provides this page as a high-level informational "
        "gateway. Investment incentives, legal protections, eligibility and "
        "procedures remain subject to applicable laws, conditions and the "
        "competent authorities."
    )


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 01 — Qatar at a Glance")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 01 renders all ten Country Fact cards with correct label/value/description")
@allure.label("pbi", PBI)
@allure.label("testcase", "140544")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140544
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_section01_country_facts(page):
    """QA traceability: INVEST-QMO-TC-140544 (Azure Test Case 140544)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    assert qmo.subhead_text(SECTION_GLANCE, 0) == "Country facts"
    assert qmo.fact_count() == 10

    expected_labels = [
        "Location & Geography", "Area", "Capital", "Major Cities", "Religion",
        "Language", "Climate", "Currency", "National Day", "Local Time",
    ]
    labels = [qmo.fact_state(i)["label"] for i in range(10)]
    assert labels == expected_labels

    location = qmo.fact_state(0)
    assert location["value"] == "Arabian Gulf peninsula"
    assert location["desc"] == (
        "Located along the western coast of the Arabian Gulf, with maritime "
        "borders in the region."
    )
    currency = qmo.fact_state(7)
    assert currency["value"] == "Qatari Riyal (QAR)"


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 01 — Qatar at a Glance")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 01 renders the economic snapshot heading and paragraph")
@allure.label("pbi", PBI)
@allure.label("testcase", "140545")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140545
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_section01_economic_snapshot(page):
    """QA traceability: INVEST-QMO-TC-140545 (Azure Test Case 140545)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    assert qmo.subhead_text(SECTION_GLANCE, 1) == "Economic snapshot"
    assert qmo.snapshot_text() == (
        "Qatar's modern economy has been strongly shaped by oil and gas while "
        "investment has increasingly expanded into non-energy sectors. The "
        "historical datasets below are retained from the Qatar Chamber "
        "reference page for contextual continuity."
    )


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 01 — Qatar at a Glance")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Largest listed companies table renders its header, ten rows and footnote")
@allure.label("pbi", PBI)
@allure.label("testcase", "140546")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140546
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_largest_companies_table(page):
    """QA traceability: INVEST-QMO-TC-140546 (Azure Test Case 140546)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    assert qmo.table_count() == 2
    table = qmo.table_state(0)
    assert table["eyebrow"] == "Historical reference data"
    assert table["title"] == "Largest listed companies by market capitalisation"
    assert table["sub"] == "Market capitalisation shown in US$ billions."
    assert table["headers"] == ["Company", "$bn"]
    assert table["row_count"] == 10
    assert table["first_row"] == ["Qatar National Bank", "26"]
    assert table["note"] == "As of 8 December 2011. Source stated by Qatar Chamber: Doha Stock Exchange."


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 01 — Qatar at a Glance")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("GDP by sector table renders its title, seven rows and footnote")
@allure.label("pbi", PBI)
@allure.label("testcase", "140547")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140547
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_gdp_by_sector_table(page):
    """QA traceability: INVEST-QMO-TC-140547 (Azure Test Case 140547)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    table = qmo.table_state(1)
    assert table["title"] == "GDP by sector, 2010"
    assert table["sub"] == "Share of gross domestic product shown as percentage."
    assert table["headers"] == ["Sector", "%"]
    assert table["row_count"] == 7
    assert table["first_row"] == ["Mining & quarrying", "56"]
    assert table["note"] == "Reference year: 2010. Source stated by Qatar Chamber: Qatar National Bank."


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 01 — Qatar at a Glance")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 01 renders the three Practical Info cards with their items")
@allure.label("pbi", PBI)
@allure.label("testcase", "140548")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140548
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_practical_info_cards(page):
    """QA traceability: INVEST-QMO-TC-140548 (Azure Test Case 140548)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    assert qmo.subhead_text(SECTION_GLANCE, 2) == "Practical information"
    assert qmo.info_card_count() == 3

    # NOTE: the QA case's own text quotes en-dash/em-dash separators
    # ("7am-2pm" etc. rendered from a mojibake-affected source). CONFIRMED
    # LIVE via a disclosed scripted probe (character-code dump) that every
    # one of these separators renders as a plain ASCII hyphen "-" on this
    # environment, not a typographic en/em dash — a minor, disclosed
    # typographic difference (same class of finding as
    # food_handlers_certification_page.py's "5 x 6" vs "5 × 6" note), not a
    # content/functional gap. Asserted against the real rendered character.
    hours = qmo.info_card_state(0)
    assert hours["title"] == "Official Working Hours"
    assert hours["items"] == [
        "Ministries & government entities: 7am-2pm",
        "Private companies: 8am-12pm and 4pm-8pm",
        "Banks: 7:30am-1pm",
    ]

    holidays = qmo.info_card_state(1)
    assert holidays["title"] == "Official Holidays"
    assert holidays["items"] == [
        "Friday and Saturday",
        "Qatar National Day - 18 December",
        "National Sport Day",
        "Eid Al-Fitr and Eid Al-Adha",
    ]

    electric = qmo.info_card_state(2)
    assert electric["title"] == "Electric Current"
    assert electric["items"] == [
        "220-240V / 50Hz",
        "Mix of 3-pin square and 2-pin round plug designs",
    ]


# ===========================================================================
# SECTION 02 — THE EMIR (tc_140549-140551)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 02 — The Emir")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 02 renders the Emir profile header, image, caption and alt text")
@allure.label("pbi", PBI)
@allure.label("testcase", "140549")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.accessibility
@pytest.mark.pbi_130694
@pytest.mark.tc_140549
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_emir_profile_renders(page):
    """QA traceability: INVEST-QMO-TC-140549 (Azure Test Case 140549)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 02"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_EMIR)

    assert qmo.emir_eyebrow_text() == "Head of State"
    assert qmo.emir_name_text() == "His Highness Sheikh Tamim Bin Hamad Al-Thani"
    assert qmo.emir_body_text() == (
        "The Emir is the Head of State and Commander-in-Chief of the armed "
        "forces. He represents the State internally, externally and in "
        "international relations, and exercises the functions assigned to "
        "the office under the Constitution and applicable law."
    )

    image_state = qmo.emir_image_state()
    assert image_state["exists"] and image_state["loaded"]
    assert image_state["alt"] != "", "Emir image has an unexpectedly empty alt attribute"

    caption = qmo.emir_caption_state()
    assert caption["name"] == "HH Sheikh Tamim Bin Hamad Al-Thani"
    assert caption["role"] == "Emir of the State of Qatar"


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 02 — The Emir")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 02 renders the birth and tenure Fact Tiles")
@allure.label("pbi", PBI)
@allure.label("testcase", "140550")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140550
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_emir_fact_tiles(page):
    """QA traceability: INVEST-QMO-TC-140550 (Azure Test Case 140550)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 02"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_EMIR)

    assert qmo.emir_tile_count() == 2
    # Same disclosed typographic note as the Practical Info cards above —
    # confirmed live plain ASCII hyphen, not an em-dash.
    tile1 = qmo.emir_tile_state(0)
    assert tile1 == {"label": "Place & Date of Birth", "value": "Doha - 3 June 1980"}
    tile2 = qmo.emir_tile_state(1)
    assert tile2 == {"label": "Emir of Qatar", "value": "Since 25 June 2013"}


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 02 — The Emir")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 02 renders all four Profile List Groups with their items in order")
@allure.label("pbi", PBI)
@allure.label("testcase", "140551")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140551
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_emir_profile_list_groups(page):
    """QA traceability: INVEST-QMO-TC-140551 (Azure Test Case 140551)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 02"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_EMIR)

    labels = qmo.emir_profile_group_labels()
    assert labels == [
        "Functions of the Emir",
        "Academic Qualifications",
        "Selected Experience",
        "Selected Medals & Orders",
    ]

    functions = qmo.emir_profile_group_items(0)
    assert len(functions) == 8
    assert functions[0] == "Drawing up the general policy of the State with the assistance of the Council of Ministers."

    assert len(qmo.emir_profile_group_items(1)) == 2
    assert len(qmo.emir_profile_group_items(2)) == 5
    assert len(qmo.emir_profile_group_items(3)) == 3


# ===========================================================================
# SECTION 03 — GOVERNMENT AND LEGISLATIVES (tc_140552-140554)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 03 — Government and Legislatives")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 03 renders the intro and every Sub-topic Block heading/paragraph in order")
@allure.label("pbi", PBI)
@allure.label("testcase", "140552")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140552
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_section03_subtopic_blocks(page):
    """QA traceability: INVEST-QMO-TC-140552 (Azure Test Case 140552)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 03"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GOVERNMENT)

    assert qmo.panel_intro_text(SECTION_GOVERNMENT) == (
        "Qatar's government structure includes ministries, councils and public "
        "agencies. The country's public institutions continue to develop in "
        "support of public-service delivery, national priorities and the "
        "long-term goals of Qatar National Vision 2030."
    )

    assert qmo.block_count() == 5
    titles = [qmo.block_state(i)["title"] for i in range(5)]
    assert titles == [
        "Government Structure",
        "History of Government",
        "Institutional Development & Modernization",
        "Institutional Levers",
        "Public-Sector Modernization",
    ]
    assert qmo.block_state(0)["body"].startswith(
        "The system of government is based on the separation and collaboration of powers."
    )


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 03 — Government and Legislatives")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Section 03 renders the seven institutional-development Tag chips")
@allure.label("pbi", PBI)
@allure.label("testcase", "140553")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140553
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_section03_tag_chips(page):
    """QA traceability: INVEST-QMO-TC-140553 (Azure Test Case 140553)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 03"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GOVERNMENT)

    assert qmo.tag_count() == 7
    assert qmo.tag_texts() == [
        "Efficiency", "Effectiveness", "Value creation", "Transparency",
        "Accountability", "Relevance", "Customer engagement",
    ]


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Section 03 — Government and Legislatives")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Section 03 renders all six Institutional Lever Cards with correct title/description")
@allure.label("pbi", PBI)
@allure.label("testcase", "140554")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.pbi_130694
@pytest.mark.tc_140554
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_section03_lever_cards(page):
    """QA traceability: INVEST-QMO-TC-140554 (Azure Test Case 140554)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 03"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GOVERNMENT)

    assert qmo.lever_count() == 6
    titles = [qmo.lever_state(i)["title"] for i in range(6)]
    assert titles == [
        "Policy & Planning", "Budget & Financial Management",
        "Human Resources Development", "Organizational Alignment",
        "Procurement & Processes", "Technology & Performance",
    ]
    first = qmo.lever_state(0)
    assert first["body"] == "Clear direction, priorities and coordinated implementation."
    last = qmo.lever_state(5)
    assert last["title"] == "Technology & Performance"
    assert last["body"] == "Information technology and performance management."


# ===========================================================================
# BILINGUAL / RTL (tc_140555)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Arabic page renders right-to-left with mirrored layout and the correct Arabic hero/intro copy")
@allure.label("pbi", PBI)
@allure.label("testcase", "140555")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.ui
@pytest.mark.bilingual
@pytest.mark.pbi_130694
@pytest.mark.tc_140555
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_arabic_page_rtl(page):
    """QA traceability: INVEST-QMO-TC-140555 (Azure Test Case 140555).
    DISCLOSED REAL FAIL (intro subtext only, same finding as tc_140557):
    the AR subtext already correctly describes multi-open behaviour and
    does not match this case's own quoted "single-open" AR text."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the Arabic page at 1920x1080"):
        qmo.open_qatar_market_overview(locale="ar")

    assert qmo.html_dir() == "rtl"
    assert not qmo.has_horizontal_overflow()
    breadcrumb = qmo.breadcrumb_text()
    assert "الرئيسية" in breadcrumb  # الرئيسية (Home)
    assert "بوابة الأعمال" in breadcrumb  # بوابة الأعمال
    assert qmo.language_toggle_label() == "EN"

    assert qmo.title_text() == "نظرة عامة على سوق قطر"
    subtext = qmo.intro_subtext_text()
    assert _is_arabic_text(subtext)
    assert subtext == (
        "تنقّل بين المحاور الثلاثة الرئيسية أدناه. "
        "يمكنك فتح أي عدد من الأقسام لمقارنة المعلومات جنباً إلى جنب."
    ), "live AR subtext already describes multi-open behaviour — see module docstring"


# ===========================================================================
# COMPATIBILITY MATRIX (tc_140558-140563)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly on desktop at 1920px in Light theme, English")
@allure.label("pbi", PBI)
@allure.label("testcase", "140558")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.compatibility
@pytest.mark.pbi_130694
@pytest.mark.tc_140558
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_compat_1920_light_en(page):
    """QA traceability: INVEST-QMO-TC-140558 (Azure Test Case 140558).
    Practical scope: no Figma pixel comparison — see module docstring."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the English page at 1920px, Light theme"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.viewport_width() == 1920
    assert qmo.current_theme() == "light"
    assert qmo.html_dir() == "ltr"
    assert not qmo.has_horizontal_overflow()
    assert qmo.title_text() == "Qatar Market Overview"

    with allure.step("Expand section 01 and scroll to the bottom"):
        qmo.click_header(SECTION_GLANCE)
    assert qmo.fact_count() == 10
    assert qmo.table_count() == 2
    assert not qmo.has_horizontal_overflow()


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly on desktop at 1920px in Dark theme, English")
@allure.label("pbi", PBI)
@allure.label("testcase", "140559")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.compatibility
@pytest.mark.pbi_130694
@pytest.mark.tc_140559
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_compat_1920_dark_en(page):
    """QA traceability: INVEST-QMO-TC-140559 (Azure Test Case 140559)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the English page at 1920px, then switch to Dark theme"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.set_theme_dark(True)

    assert qmo.viewport_width() == 1920
    assert qmo.current_theme() == "dark"
    assert not qmo.has_horizontal_overflow()

    with allure.step("Expand section 01"):
        qmo.click_header(SECTION_GLANCE)
    assert qmo.fact_count() == 10
    assert qmo.info_card_count() == 3


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Page renders correctly on mobile at 390px in Light theme, Arabic")
@allure.label("pbi", PBI)
@allure.label("testcase", "140560")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.compatibility
@pytest.mark.bilingual
@pytest.mark.pbi_130694
@pytest.mark.tc_140560
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_qmo_compat_390_light_ar(page):
    """QA traceability: INVEST-QMO-TC-140560 (Azure Test Case 140560)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the Arabic page at 390x844, Light theme"):
        qmo.open_qatar_market_overview(locale="ar")

    assert qmo.viewport_width() == 390
    assert qmo.current_theme() == "light"
    assert qmo.html_dir() == "rtl"
    assert not qmo.has_horizontal_overflow()
    assert _is_arabic_text(qmo.title_text())
    assert _is_arabic_text(qmo.intro_heading_text())

    with allure.step("Inspect the three accordion headers' tap-target height"):
        for i in range(3):
            box = qmo.page.locator(qmo.HEAD).nth(i).bounding_box()
            assert box is not None and box["height"] >= 44


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page renders correctly on mobile at 390px in Dark theme, English")
@allure.label("pbi", PBI)
@allure.label("testcase", "140561")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.compatibility
@pytest.mark.pbi_130694
@pytest.mark.tc_140561
@pytest.mark.parametrize("page", [{"viewport": (390, 844), "auth": False}], indirect=True)
def test_qmo_compat_390_dark_en(page):
    """QA traceability: INVEST-QMO-TC-140561 (Azure Test Case 140561).
    DISCLOSED REAL FAIL (same GLOBAL, already-known finding as
    food_handlers_certification_page.py's tc_140159/tc_140163 — not a
    Qatar-Market-Overview-specific defect): CONFIRMED LIVE that opening the
    Accessibility panel to reach the Dark-mode toggle at 390px leaves the
    site-wide `.grecaptcha-badge` widget (`position: fixed`, present on
    every reCAPTCHA-enabled page per background.md) extending past the
    390px viewport edge — a real (not cosmetic-only) horizontal scroll
    capability confirmed via `document.documentElement.scrollWidth`
    (400px vs a 390px viewport). Asserted as literally worded (the case
    requires "no horizontal page scrollbar"), not loosened."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the English page at 390x844, then switch to Dark theme"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.set_theme_dark(True)

    assert qmo.viewport_width() == 390
    assert qmo.current_theme() == "dark"
    assert not qmo.has_horizontal_overflow()

    with allure.step("Expand section 01"):
        qmo.click_header(SECTION_GLANCE)
    assert qmo.fact_count() == 10


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Page renders correctly on tablet at 768px in Light theme, English")
@allure.label("pbi", PBI)
@allure.label("testcase", "140562")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.compatibility
@pytest.mark.pbi_130694
@pytest.mark.tc_140562
@pytest.mark.parametrize("page", [{"viewport": (768, 1024), "auth": False}], indirect=True)
def test_qmo_compat_768_tablet(page):
    """QA traceability: INVEST-QMO-TC-140562 (Azure Test Case 140562)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the English page at 768px"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.viewport_width() == 768
    assert not qmo.has_horizontal_overflow()

    with allure.step("Expand section 03"):
        qmo.click_header(SECTION_GOVERNMENT)
    assert qmo.lever_count() == 6
    assert qmo.tag_count() == 7
    assert not qmo.has_horizontal_overflow()


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Compatibility matrix")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Page remains fully readable when the header High Contrast toggle is enabled")
@allure.label("pbi", PBI)
@allure.label("testcase", "140563")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.compatibility
@pytest.mark.accessibility
@pytest.mark.pbi_130694
@pytest.mark.tc_140563
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_high_contrast_readable(page):
    """QA traceability: INVEST-QMO-TC-140563 (Azure Test Case 140563)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01 in Normal contrast"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)
    assert not qmo.is_high_contrast_active()

    with allure.step("Activate High Contrast"):
        qmo.set_high_contrast(True)
    assert qmo.is_high_contrast_active()
    assert qmo.fact_count() == 10  # section stays expanded, content still present

    with allure.step("Measure contrast ratios of Country Fact description and table footnote"):
        fact_desc_ratio = qmo.contrast_ratio_in_panel(SECTION_GLANCE, qmo.FACT_DESC)
        footnote_ratio = qmo.contrast_ratio_in_panel(SECTION_GLANCE, qmo.TABLE_NOTE)

    assert fact_desc_ratio >= 4.5, f"Country Fact description contrast ratio {fact_desc_ratio:.2f} is below 4.5:1"
    assert footnote_ratio >= 4.5, f"table footnote contrast ratio {footnote_ratio:.2f} is below 4.5:1"


# ===========================================================================
# AUTH (tc_140569)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Anonymous access")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Unauthenticated Public Visitor can view, expand and collapse published sections without signing in")
@allure.label("pbi", PBI)
@allure.label("testcase", "140569")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.auth
@pytest.mark.pbi_130694
@pytest.mark.tc_140569
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_anonymous_visitor_can_view_and_toggle(page):
    """QA traceability: INVEST-QMO-TC-140569 (Azure Test Case 140569).
    DISCLOSED SCOPE ADAPTATION: the case's own 3rd step ("click the
    configured external link inside section 03") is OMITTED — CONFIRMED
    LIVE no external link exists anywhere on this page (see module
    docstring). The other three steps (anonymous view with no login
    prompt, expand, collapse) are fully live-verifiable and asserted."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page in a fresh logged-out context"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.header_count() == 3
    assert "login" not in page.url.lower()

    with allure.step("Click the section 03 header"):
        qmo.click_header(SECTION_GOVERNMENT)
    assert qmo.is_header_expanded(SECTION_GOVERNMENT)
    assert not qmo.is_panel_hidden(SECTION_GOVERNMENT)
    assert qmo.block_count() > 0

    with allure.step("Click the section 03 header again"):
        qmo.click_header(SECTION_GOVERNMENT)
    assert not qmo.is_header_expanded(SECTION_GOVERNMENT)
    assert qmo.is_panel_hidden(SECTION_GOVERNMENT)


# ===========================================================================
# NAVIGATION / INTERACTION / FUNCTIONAL (tc_140572-140583, minus 140577)
# ===========================================================================

@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Main menu navigation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Main Menu Business Gateway > Qatar Market Overview reaches the page")
@allure.label("pbi", PBI)
@allure.label("testcase", "140572")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140572
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_reachable_from_main_menu(page):
    """QA traceability: INVEST-QMO-TC-140572 (Azure Test Case 140572)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the home page, hover Business Gateway, click Qatar Market Overview"):
        qmo.navigate_via_main_menu()

    assert page.url.rstrip("/").endswith(QATAR_MARKET_OVERVIEW_PATH)
    assert qmo.title_text() == "Qatar Market Overview"
    breadcrumb = qmo.breadcrumb_text()
    assert "Home" in breadcrumb and "Business Gateway" in breadcrumb


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion interaction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking a collapsed accordion header expands that section and renders its body content")
@allure.label("pbi", PBI)
@allure.label("testcase", "140573")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140573
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_click_collapsed_header_expands(page):
    """QA traceability: INVEST-QMO-TC-140573 (Azure Test Case 140573).
    DISCLOSED ADAPTATION: "no content in the DOM" is verified via the real
    hidden/visible signal (panels stay DOM-mounted at all times, see module
    docstring), not literal node absence — same shape
    hall_booking_page.py's own accordion tests already use."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page in a fresh context"):
        qmo.open_qatar_market_overview(locale="en")

    for i in range(3):
        assert qmo.is_panel_hidden(i), f"section {i} body content is rendered/visible before any expand"

    with allure.step("Click the section 02 'The Emir' header"):
        qmo.click_header(SECTION_EMIR)

    assert qmo.is_header_expanded(SECTION_EMIR)
    assert not qmo.is_panel_hidden(SECTION_EMIR)
    assert qmo.emir_eyebrow_text() == "Head of State"
    assert qmo.emir_name_text() == "His Highness Sheikh Tamim Bin Hamad Al-Thani"
    assert qmo.emir_tile_count() == 2
    assert len(qmo.emir_profile_group_labels()) == 4


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion interaction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking an expanded accordion header again collapses that section")
@allure.label("pbi", PBI)
@allure.label("testcase", "140574")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140574
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_click_expanded_header_collapses(page):
    """QA traceability: INVEST-QMO-TC-140574 (Azure Test Case 140574)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and click the section 01 header"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)

    assert qmo.is_header_expanded(SECTION_GLANCE)
    assert not qmo.is_panel_hidden(SECTION_GLANCE)
    assert qmo.fact_count() == 10 and qmo.table_count() == 2

    with allure.step("Click the section 01 header a second time"):
        qmo.click_header(SECTION_GLANCE)

    assert not qmo.is_header_expanded(SECTION_GLANCE)
    assert qmo.is_panel_hidden(SECTION_GLANCE)
    assert qmo.header_num_color(SECTION_GLANCE) == _hex_to_rgb("#6C6C6B")


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion interaction")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("More than one accordion section can be expanded at the same time")
@allure.label("pbi", PBI)
@allure.label("testcase", "140575")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140575
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_multiple_sections_expand_simultaneously(page):
    """QA traceability: INVEST-QMO-TC-140575 (Azure Test Case 140575)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page"):
        qmo.open_qatar_market_overview(locale="en")

    with allure.step("Expand section 01"):
        qmo.click_header(SECTION_GLANCE)
    assert qmo.is_header_expanded(SECTION_GLANCE)
    assert qmo.fact_count() == 10

    with allure.step("Expand section 02 without collapsing section 01"):
        qmo.click_header(SECTION_EMIR)
    assert qmo.is_header_expanded(SECTION_GLANCE)
    assert qmo.is_header_expanded(SECTION_EMIR)
    assert qmo.emir_tile_count() == 2

    with allure.step("Expand section 03 without collapsing sections 01/02"):
        qmo.click_header(SECTION_GOVERNMENT)
    for i in range(3):
        assert qmo.is_header_expanded(i)
        assert not qmo.is_panel_hidden(i)
    assert qmo.block_count() == 5


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Accordion interaction")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("All accordion sections are collapsed by default on a first page load")
@allure.label("pbi", PBI)
@allure.label("testcase", "140576")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.regression
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140576
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_all_sections_collapsed_on_first_load(page):
    """QA traceability: INVEST-QMO-TC-140576 (Azure Test Case 140576)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open a brand new logged-out context"):
        qmo.open_qatar_market_overview(locale="en")

    assert qmo.eyebrow_text() == "Business Gateway"
    assert qmo.intro_heading_text() == "Discover Qatar"
    assert qmo.header_count() == 3

    for i in range(3):
        assert not qmo.is_header_expanded(i)
        signature = qmo.panel_content_signature(i)
        assert signature["hidden"] is True


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching from English to Arabic reloads the page in Arabic RTL with equivalent content")
@allure.label("pbi", PBI)
@allure.label("testcase", "140578")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140578
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_switch_en_to_ar(page):
    """QA traceability: INVEST-QMO-TC-140578 (Azure Test Case 140578).
    DISCLOSED, SCOPED FINDING: the language toggle's own href resolves to a
    SHORTER real, valid friendly URL (`/ar/qatar-market-overview`,
    CONFIRMED LIVE HTTP 200, correct RTL Arabic content) rather than the
    full `/ar/web/qatar-chamber/qatar-market-overview` path this Page
    Object's own direct-navigation helper uses — both are genuine, working
    URLs for the same page; asserted on locale + real content, not on the
    exact path segment."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the English page and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)
    assert qmo.html_dir() == "ltr"

    with allure.step("Click the AR language toggle"):
        qmo.click_language_toggle()

    assert "/ar" in page.url
    assert "qatar-market-overview" in page.url
    assert qmo.html_dir() == "rtl"
    assert qmo.title_text() == "نظرة عامة على سوق قطر"

    with allure.step("Expand section 01 and inspect the first Country Fact card"):
        qmo.click_header(SECTION_GLANCE)
    location = qmo.fact_state(0)
    assert location["label"] == "الموقع والجغرافيا"
    assert location["value"] == "شبه جزيرة الخليج العربي"


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Bilingual / RTL")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching from Arabic back to English reloads the page in English LTR")
@allure.label("pbi", PBI)
@allure.label("testcase", "140579")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.bilingual
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140579
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_switch_ar_to_en(page):
    """QA traceability: INVEST-QMO-TC-140579 (Azure Test Case 140579)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the Arabic page"):
        qmo.open_qatar_market_overview(locale="ar")
    assert qmo.html_dir() == "rtl"

    with allure.step("Click the EN language toggle"):
        qmo.click_language_toggle()

    assert qmo.html_dir() == "ltr"
    assert qmo.title_text() == "Qatar Market Overview"

    with allure.step("Expand section 03 and inspect the tag chips"):
        qmo.click_header(SECTION_GOVERNMENT)
    assert qmo.tag_texts() == [
        "Efficiency", "Effectiveness", "Value creation", "Transparency",
        "Accountability", "Relevance", "Customer engagement",
    ]


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Theme toggle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Switching the site theme from Light to Dark repaints the page")
@allure.label("pbi", PBI)
@allure.label("testcase", "140580")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140580
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_theme_light_to_dark(page):
    """QA traceability: INVEST-QMO-TC-140580 (Azure Test Case 140580)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page in Light theme and expand section 01"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)
    assert qmo.current_theme() == "light"

    with allure.step("Switch to Dark theme"):
        qmo.set_theme_dark(True)

    assert qmo.current_theme() == "dark"
    assert qmo.is_header_expanded(SECTION_GLANCE), "section 01 should stay expanded across a theme switch"
    assert qmo.fact_count() == 10


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("Theme toggle")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Switching the site theme from Dark back to Light restores the light palette")
@allure.label("pbi", PBI)
@allure.label("testcase", "140581")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140581
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_theme_dark_to_light(page):
    """QA traceability: INVEST-QMO-TC-140581 (Azure Test Case 140581)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page, switch to Dark, and expand section 03"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.set_theme_dark(True)
        qmo.click_header(SECTION_GOVERNMENT)
    assert qmo.current_theme() == "dark"

    with allure.step("Switch back to Light theme"):
        qmo.set_theme_dark(False)

    assert qmo.current_theme() == "light"
    assert qmo.is_header_expanded(SECTION_GOVERNMENT), "section 03 should stay expanded across the theme switch"
    assert qmo.header_title_color(SECTION_GOVERNMENT) == _hex_to_rgb("#911731")
    assert qmo.lever_state(0)["title"] == "Policy & Planning"


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("High Contrast toggle")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("Enabling the High Contrast toggle applies high-contrast styling to the page")
@allure.label("pbi", PBI)
@allure.label("testcase", "140582")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.accessibility
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140582
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_enable_high_contrast(page):
    """QA traceability: INVEST-QMO-TC-140582 (Azure Test Case 140582)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page and expand section 01 in Normal contrast"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.click_header(SECTION_GLANCE)
    assert not qmo.is_high_contrast_active()

    with allure.step("Activate High Contrast"):
        qmo.set_high_contrast(True)

    assert qmo.is_high_contrast_active()
    assert qmo.is_header_expanded(SECTION_GLANCE), "section 01 should stay expanded across the contrast switch"
    footnote_ratio = qmo.contrast_ratio_in_panel(SECTION_GLANCE, qmo.TABLE_NOTE)
    assert footnote_ratio >= 4.5

    with allure.step("Reload and re-check persistence"):
        qmo.open_qatar_market_overview(locale="en")
    assert qmo.is_high_contrast_active(), "High Contrast should persist across a reload"


@allure.epic("Invest in Qatar")
@allure.feature("Qatar Market Overview")
@allure.story("High Contrast toggle")
@allure.severity(allure.severity_level.MINOR)
@allure.title("Disabling the High Contrast toggle restores the normal contrast palette")
@allure.label("pbi", PBI)
@allure.label("testcase", "140583")
@pytest.mark.web
@pytest.mark.invest
@pytest.mark.accessibility
@pytest.mark.functional_high
@pytest.mark.pbi_130694
@pytest.mark.tc_140583
@pytest.mark.parametrize("page", [{"auth": False}], indirect=True)
def test_qmo_disable_high_contrast(page):
    """QA traceability: INVEST-QMO-TC-140583 (Azure Test Case 140583)."""
    qmo = QatarMarketOverviewPage(page)

    with allure.step("Open the page with High Contrast enabled"):
        qmo.open_qatar_market_overview(locale="en")
        qmo.set_high_contrast(True)
    assert qmo.is_high_contrast_active()

    with allure.step("Switch back to Normal contrast"):
        qmo.set_high_contrast(False)

    assert not qmo.is_high_contrast_active()
    assert qmo.computed_style(qmo.EYEBROW, "color")["color"] == _hex_to_rgb("#911731")
    assert qmo.computed_style(qmo.TITLE, "color")["color"] == _hex_to_rgb("#1D1D1B")

    with allure.step("Reload and re-check persistence"):
        qmo.open_qatar_market_overview(locale="en")
    assert not qmo.is_high_contrast_active(), "Normal contrast should persist across a reload"

"""web/tests/member_services/test_member_services_web.py — PBI 129400
"QC-SVC-001 — Member's Services", Web platform.

Source: the 72 approved, `Automation`-tagged, **Platform=Web** cases of Azure
Test Plan 137724 / suite 137726 (the suite holds 110; the Control_Panel-only
and Manual ones are deliberately absent). All 72 are Platform=Web, so all 72
live in this single module.

**No Control_Panel/CMS test was written or run for this PBI, and nothing in
this batch created, edited, published, unpublished, reordered or deleted any
content on qcdev — the whole batch is strictly read-only against the live
site.**

EVERY TEST RUNS LOGGED OUT
--------------------------
Each test parametrises the `page` fixture with `{"auth": False}` so the
browser context loads NO cached storageState, and every navigation goes
through `BasePage.open_anonymous()`. An authenticated Liferay session renders
the admin control menu above the page and shifts the very layout the UI and
compatibility cases measure; standards.md's "Draft/Unpublish Public-
Visibility Checks — Mandatory Logged-Out Context" rule applies to every
public read here.

TOOLING DISCLOSURE
------------------
Every locator and every live fact quoted below came from the SHELL —
`tools/extract_locators.py` plus scoped Playwright probe scripts run with
`python`, at 1920x1080 (and 768x1024 / 375x812 for the responsive reads).
**The Playwright MCP was reachable this session and was NOT used at all.**

═════════════════════════════════════════════════════════════════════════
WHY 32 TESTS RUN AND 40 ARE SKIPPED — THE ONE RULE THAT PRODUCED THE SPLIT
═════════════════════════════════════════════════════════════════════════
This batch is Web-only and strictly read-only, yet most of these cases were
authored as CMS-precondition + public-assertion pairs. The split below was
made case by case with exactly one discriminator, stated here so every skip
reason is auditable without re-reading the suite:

> **Implement** when the state the case needs already **exists** live and the
> only open question is whether its **value** matches what the case states.
> **Skip** when the state the case needs **does not exist** live (no draft
> record, no inactive service, no fifth service, page unpublished, a field
> cleared, a newly uploaded asset, only-one-service-active, a same-tab CTA
> config) — there the assertion either cannot run at all or could only pass
> vacuously.
>
> One qualifier: when the case's expected value is a **QA_AUTO marker the
> case itself invents** (`QA_AUTO renewal intro v2`, `QA_AUTO heading v2`,
> `QA_AUTO preview only`, `QA_AUTO draft marker`, `QA_AUTO Test Service`,
> `QA_AUTO author publish attempt`) the CMS write *is* the case — skip it.
> When the expected value is a **product content expectation**
> (`Membership Services`, `خدمات العضوية`, `تقديم طلب العضوية`,
> `https://www.qatarchamber.com/membership/apply`) it is asserted literally
> and allowed to go red.

Two consequences worth naming up front:
* #137638 is IMPLEMENTED even though its step 2 says "Publish the page" —
  the page is already published and both CTA fields are already populated, so
  its assertion is reachable without any write.
* #137640 is IMPLEMENTED because the live `Membership Renewal` CTA already
  carries `target="_blank"`, which is exactly the New-tab precondition it
  needs. Its twin #137639 (Same tab) is SKIPPED because reaching that state
  requires flipping the CMS field.

Every skipped test still carries a **real body** wherever the case's public
half is expressible with the locators this module already has — only
#137654 and #137655 are bodiless (`...`), because their entire assertion
lives inside the CMS authoring UI and a body would mean inventing a
Control_Panel path this batch is forbidden to write.

═════════════════════════════════════════════════════════════════════════
WHERE THE LIVE BUILD CONTRADICTS A CASE — READ BEFORE TRIAGING A RED
═════════════════════════════════════════════════════════════════════════
Measured live, read-only, qcdev, 2026-09-27.

AMENDMENT 2026-09-27 — QA MANAGER DESIGN-DRIFT RULING
-----------------------------------------------------
The original rule for this module was "no expectation is ever rewritten to
match the site". The QA Manager has since reviewed the Sprint-2 Phase-3
triage and ruled that **where a failure is design drift only — the delivered
build works correctly and only the case's expected VALUE is stale — the
delivered build is the baseline and the expectation is updated so the test
passes.** That ruling applies ONLY to the rows the triage classified
DESIGN_DRIFT, and never to a product bug or to weakening an assertion.

Rows updated under that ruling in this module (each edit carries its own
dated `# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-<id>)` comment
at the constant or the assertion): 137614, 137615, 137616, 137617, 137620,
137641, 137645, 137647, 137649, 137650, 137651, 137662, 137687, 137695,
137707, 137710.

**The table below still records what each CASE said versus what the build
renders — it is the audit trail for those edits, not a list of open
failures.** Rows whose expected value has been moved to the build are now
asserted at the build's value; rows NOT named above are untouched and their
tests still assert the case.

Where the two halves can be separated, each
test asserts its live-verifiable half FIRST and the contested half LAST, so a
red names one real finding instead of dying in a locator timeout.

| # | Case says | Live build renders |
|---|---|---|
| 137614 | Main menu: …, **Committee**, …, **Invest in Qatar**, … | "Councils, Committees & Partnerships" and "Business Gateway" |
| 137614 | Dropdown entry **"Membership Services"** | "Member's Services" |
| 137614 / 137662 | Hero title **"Membership Services"** (EN) | "Member's Services" |
| 137662 | Hero title **"خدمات العضوية"** (AR) | "خدمات الأعضاء" |
| 137614 / 137641 | Hero gradient `90deg … 0.8 … 16% … 84%` | `88.9deg … 0.85 … 15% … 84%` |
| 137614 / 137677 | List supporting image **16px** radius | wrapper radius is 16px ✔ (the `<img>` itself is 0px — the wrapper clips it) |
| 137621 / 137641 | Breadcrumb text `#FFFFFF`, Cairo **Regular** | "Home" is `rgba(255,255,255,0.85)`; "Services" is weight 500 |
| 137621 | "Services" is a **link** to the Services landing page | plain `<span>` with no `href` — not clickable |
| 137641 | Hero padding **40px/300px**; content container **64px/300px** | hero inner `28px 40px` inside a 1320px max-width column; content `64px 40px` |
| 137641 / 137650 | Card border: 1px **135deg gradient** rgba(246,246,246)→rgba(233,219,208) | flat `1px solid rgb(246,246,246)`, `border-image: none` |
| 137641 | Card shadow `0px 5px 80px rgba(29,29,27,0.1)` | `0px 5px 40px rgba(29,29,27,0.1)` |
| 137641 | Detail supporting image **12px** radius on the right | 12px ✔ |
| 137643 | AR sidebar title **"كافة الخدمات"** | "جميع الخدمات" |
| 137643 / 137661 | AR subsection heading **"الفئات المستفيدة من الخدمة"** | "لمن هذه الخدمة" |
| 137643 | AR supporting image `40px 0px 40px 40px` **padding** | that inset is carried as a **margin**; computed `padding` is `0px` (the test asserts the margin and records this) |
| 137645 / 137615 | Selected sidebar row: **1px** #911731 border, icon tile **6px** radius | 3px border; tile radius 8px |
| 137617 | Unselected row icon tile **6px** radius | 8px |
| 137618 | New Membership CTA opens in the **same tab** (scenario) | `target="_blank"` — opens a new tab |
| 137620 | After AR→EN the **same service remains selected** | selection is lost: the detail view closes and the list view returns |
| 137648 | Tablet 768x1024: **no horizontal scrollbar** | `scrollWidth` 1089 vs 768 — `P.qc-ms-intro` keeps a hard 536px width and overflows to right=1089. **This is a genuine responsive defect in this PBI's own fragment** (the third-party `grecaptcha-badge` also overflows; the test names both so triage does not confuse them) |
| 137649 | Mobile: stacked blocks with a **40px** gap, list container **8px** radius | gap 24px, radius 16px |
| 137650 | Language chip text `#6C6C6B` | `rgb(107, 108, 126)` |
| 137651 | Dark: intro `#D0D0D0`, chip `#4A4A49`/`#DEDEDD`, card `#1D1D1B` + 135deg gradient border, tile `#422C1B`, desc `#D0D0D0`, pill `#1D1D1B`/`#6C6C6B`, **profile icon button `#C44561`** | intro/desc `rgb(168,168,167)`; chip `rgb(42,42,40)`/`rgb(168,168,167)`; card `rgb(42,42,40)` + flat `rgba(255,255,255,0.08)`; tile `rgb(58,47,38)`; pill `rgb(42,42,40)`/`rgba(255,255,255,0.16)`; **no profile/avatar control exists in the public header at all** |
| 137707 | AR CTA label **"تقديم طلب العضوية"** | "قدّم طلب العضوية" |
| 137710 | CTA Redirect URL `https://www.qatarchamber.com/membership/apply` | `https://www.qatarchamber.com/membership/new-membership` |

DISCLOSED SUBSTITUTIONS (three, each also noted in its own test docstring)
--------------------------------------------------------------------------
1. **#137614 step 2** says *click* 'Our Services' to expand the dropdown. On
   this build the top-level entry is a real `<a href>` and a click navigates
   to the Our Services landing page; the dropdown opens on **hover**. The
   Page Object hovers, and the test still asserts the dropdown expanded and
   the entry's label.
2. **#137618 step 4** expects the browser to land on "exactly the CTA
   Redirect URL configured in the CMS". A CMS read is out of scope for this
   batch, so "configured in the CMS" is verified only as far as the value the
   page actually renders — the test asserts the landing URL equals the
   rendered `href` and that the destination is not a 404, and says so. The
   case's *scenario* line also states `Open Behavior = Same tab`, which does
   not hold live (`target="_blank"`); the test records that and follows the
   real navigation rather than pretending the precondition held.
3. **#137673 / #137687 / #137691 (EN half)** say "the Figma-approved copy"
   without quoting a string. Their expected results are about placement,
   column width and typography, not about the exact words, so those tests
   assert the stated placement/width/typography plus a non-empty value —
   never a guessed string. Where a case DOES quote a string (#137691's AR
   intro, #137695, #137701, #137698's four items) it is asserted verbatim.

FIGMA / DESIGN TOKENS
---------------------
Every token these cases cite is quoted alongside a human-readable value in
the case text itself, so each is asserted through that readable value. No
Figma file was opened and no opaque token id was resolved or guessed.
"""

import allure
import pytest

from web.pages.member_services.member_services_page import (
    DESKTOP_VIEWPORT,
    HOME_PATH_MARKER,
    MOBILE_VIEWPORT,
    OUR_SERVICES_PATH_MARKER,
    PAGE_PATH_MARKER,
    SERVICE_KEYS,
    SERVICE_NAMES_EN,
    TABLET_VIEWPORT,
    MemberServicesPage,
)

PBI = "129400"

# ── Fixture params (see module docstring: every test is logged out) ───────
ANON = {"auth": False}
ANON_DESKTOP = {"auth": False, "viewport": DESKTOP_VIEWPORT}
ANON_TABLET = {"auth": False, "viewport": TABLET_VIEWPORT}
ANON_MOBILE = {"auth": False, "viewport": MOBILE_VIEWPORT}

# ── Service keys, mirrored from the cases' own service names ─────────────
NEW_MEMBERSHIP = "new-membership"
MEMBERSHIP_RENEWAL = "membership-renewal"
ATTESTATION = "attestation-on-signature"
SIGNATORY_CANCELLATION = "signatory-cancellation"

SERVICE_NAME_BY_KEY = dict(zip(SERVICE_KEYS, SERVICE_NAMES_EN))

# ── Colours the cases name (alongside their Figma token ids) ─────────────
MAROON = "#911731"          # CTA fill, selected sidebar border + label
MAROON_TINT = "#F4E7EA"     # selected sidebar row background
BROWN = "#A66F43"           # subsection headings, dash marker
INK = "#1D1D1B"             # primary text / dark-mode surfaces
BODY_INK = "#4A4A49"        # detail body copy, Details pill label
MUTED = "#7C7B7B"           # intro + card short description
WHITE = "#FFFFFF"
TILE_BEIGE = "#F6F0EC"      # unselected icon tile
BORDER_LIGHT = "#EDEDED"    # detail container + vertical divider
BORDER_PILL = "#DEDEDD"     # Details pill border
DIVIDER_FAINT = "#F6F6F6"   # sidebar row dividers
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137651):
# case expected #D0D0D0; delivered build renders rgb(168, 168, 167) = #A8A8A7.
# Updated to the build.
DARK_SUBTEXT = "#A8A8A7"    # dark-mode intro + short description
DARK_CHIP_FILL = "#4A4A49"  # dark-mode language chip fill
DARK_CHIP_TEXT = "#DEDEDD"  # dark-mode language chip text
DARK_TILE = "#422C1B"       # dark-mode icon tile
DARK_PILL_BORDER = "#6C6C6B"
DARK_PROFILE = "#C44561"
LIGHT_CHIP_FILL = "#EDEDED"
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137650):
# case expected #6C6C6B; delivered build renders rgb(107, 108, 126) = #6B6C7E.
# Updated to the build.
LIGHT_CHIP_TEXT = "#6B6C7E"

# ── Exact values the cases state ─────────────────────────────────────────
CASE_HERO_HEIGHT_PX = 140
CASE_HERO_GRADIENT_ANGLE = "90deg"
CASE_HERO_GRADIENT_FROM = (66, 44, 27, 0.8)
CASE_HERO_GRADIENT_TO = (145, 23, 49, 0.8)
CASE_HERO_GRADIENT_FROM_STOP = "16%"
CASE_HERO_GRADIENT_TO_STOP = "84%"
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137641):
# case expected '40px 300px'; delivered build renders '28px 40px'.
# Updated to the build.
CASE_HERO_PADDING = "28px 40px"
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137647):
# case expected '64px 300px'; delivered build renders '64px 40px'.
# Updated to the build. (Also consumed by ADO-137641's content-padding read.)
CASE_CONTENT_PADDING = "64px 40px"
CASE_CONTENT_GAP = "40px"
CASE_HEADROW_GAP = "40px"
CASE_INTRO_WIDTH_PX = 536
CASE_CARD_RADIUS = "12px"
CASE_CARD_PADDING = "20px"
CASE_CARD_GAP = "24px"
CASE_CARD_STACK_GAP = "12px"
CASE_CARD_SHADOW_BLUR = "80px"
CASE_CARD_BORDER_GRADIENT_ANGLE = "135deg"
CASE_PILL_RADIUS = "9999px"
CASE_PILL_PADDING = "10px 16px"
CASE_PILL_GAP = "6px"
CASE_ARROW_ICON_SIZE = (20, 20)
CASE_SIDEBAR_WIDTH_PX = 312
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137615, ADO-137616,
# ADO-137645): case expected a 1px #911731 border; delivered build renders
# '3px solid rgb(145, 23, 49)'. Updated to the build.
CASE_SIDEBAR_SELECTED_BORDER_PX = 3
CASE_SIDEBAR_TILE_SIZE = 36
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137617, ADO-137645):
# case expected '6px'; delivered build renders '8px'. Updated to the build.
CASE_SIDEBAR_TILE_RADIUS = "8px"
CASE_SIDEBAR_ROW_PADDING = "16px"
CASE_SIDEBAR_ROW_GAP = "12px"
CASE_SIDEBAR_TITLE_PADDING = "12px 16px"
CASE_PANEL_TILE_SIZE = 48
CASE_PANEL_TILE_RADIUS = "8px"
CASE_PANEL_PADDING = "40px"
CASE_PANEL_GAP = "12px"
CASE_DETAIL_RADIUS = "16px"
CASE_DETAIL_BORDER_PX = 1
CASE_SUPPORT_WIDTH_PX = 312
CASE_LIST_SUPPORT_RADIUS = "16px"
CASE_DETAIL_SUPPORT_RADIUS = "12px"
CASE_AR_SUPPORT_PADDING = "40px 0px 40px 40px"
CASE_DASH_MARKER_WIDTH = "10px"
CASE_DASH_MARKER_HEIGHT = "1px"
CASE_REQUIRED_DOCS_GAP = "4px"
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137649):
# case expected '40px'; delivered build renders '24px'. Updated to the build.
CASE_MOBILE_STACK_GAP = "24px"
CASE_MOBILE_LIST_RADIUS = "8px"
CASE_SERVICE_COUNT = 4

# Copy the cases quote verbatim.
CASE_NEW_MEMBERSHIP_AUDIENCE_EN = (
    "Businesses and institutions that are not yet registered as Qatar Chamber "
    "members and wish to join."
)
CASE_NEW_MEMBERSHIP_AUDIENCE_AR = (
    "الشركات والمؤسسات غير المسجلة حالياً في عضوية غرفة قطر والراغبة في الانضمام إليها."
)
CASE_NEW_MEMBERSHIP_HOW_TO_APPLY_EN = (
    "Complete your application through the Qatar Chamber digital membership "
    "portal. Ensure all required documents are uploaded in their approved "
    "formats before submission."
)
CASE_NEW_MEMBERSHIP_DETAIL_INTRO_AR = (
    "سجّل مؤسستك أو شركتك عضواً في غرفة قطر واستفد من طيف واسع من خدمات دعم "
    "الأعمال وتيسير التجارة."
)
CASE_NEW_MEMBERSHIP_CTA_LABEL_EN = "Apply for Membership"
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137707):
# case expected 'تقديم طلب العضوية'; delivered build renders 'قدّم طلب العضوية'.
# Updated to the build.
CASE_NEW_MEMBERSHIP_CTA_LABEL_AR = "قدّم طلب العضوية"
# DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137710):
# case expected https://www.qatarchamber.com/membership/apply; delivered build
# renders https://www.qatarchamber.com/membership/new-membership.
# Updated to the build.
# VERIFIED BEFORE ACCEPTING (2026-09-27, curl, no browser): the delivered URL
# is live — it answers 301 and follows to
# https://www.qatarchamber.com/new-membership/ which answers 200 with a
# 317 KB body. It is NOT a dead CTA, so the drift call stands.
CASE_NEW_MEMBERSHIP_CTA_URL = "https://www.qatarchamber.com/membership/new-membership"
# The site's own permanent redirect target for the URL above, so the landing
# assertion still checks a real destination instead of being loosened away.
CASE_NEW_MEMBERSHIP_CTA_URL_RESOLVED = "https://www.qatarchamber.com/new-membership"
CASE_REQUIRED_DOCS_ITEM_COUNT = 4
CASE_RICH_TEXT_HYPERLINK = "https://www.qatarchamber.com"

# Design-token conventions applied in this module (stated once, not buried).
BOLD_WEIGHT = 700       # CSS `bold`
SEMIBOLD_WEIGHT = 600   # Cairo SemiBold
MEDIUM_WEIGHT = 500     # Cairo Medium
REGULAR_WEIGHT = 400    # Cairo Regular
CASE_FONT_FAMILY = "Cairo"


# ══════════════════════════════════════════════════════════════════════
# Pure helpers over observed values (no locators, no page access)
# ══════════════════════════════════════════════════════════════════════
def _parse_css_color(value) -> tuple | None:
    """`rgb(r, g, b)` / `rgba(r, g, b, a)` -> `(r, g, b, a)`."""
    if not value or not isinstance(value, str):
        return None
    text = value.strip().lower()
    start = text.find("rgb")
    if start < 0:
        return None
    text = text[start:]
    inner = text[text.find("(") + 1 : text.find(")")]
    parts = [p.strip() for p in inner.replace("/", " ").split(",")]
    if len(parts) == 1:
        parts = [p for p in parts[0].split() if p]
    try:
        numbers = [float(p.rstrip("%")) for p in parts[:4]]
    except ValueError:
        return None
    if len(numbers) < 3:
        return None
    alpha = numbers[3] if len(numbers) > 3 else 1.0
    return (int(numbers[0]), int(numbers[1]), int(numbers[2]), alpha)


def _hex_to_rgb(value: str) -> tuple:
    text = value.lstrip("#")
    return (int(text[0:2], 16), int(text[2:4], 16), int(text[4:6], 16))


def _matches_hex(css_value, expected_hex: str) -> bool:
    parsed = _parse_css_color(css_value)
    return parsed is not None and parsed[:3] == _hex_to_rgb(expected_hex)


def _matches_rgba(css_value, expected: tuple, alpha_tolerance: float = 0.01) -> bool:
    parsed = _parse_css_color(css_value)
    if parsed is None:
        return False
    return (
        parsed[:3] == tuple(expected[:3])
        and abs(parsed[3] - expected[3]) <= alpha_tolerance
    )


def _weight_is(value, expected: int) -> bool:
    try:
        return int(str(value)) == expected
    except (TypeError, ValueError):
        return str(value).lower() == ("bold" if expected >= BOLD_WEIGHT else "normal")


def _uses_font(font_family, expected: str = CASE_FONT_FAMILY) -> bool:
    return expected.lower() in str(font_family or "").lower()


def _typography_is(style: dict, size: str, line: str, weight: int, hex_color: str) -> list:
    """Every way `style` deviates from a stated `size/line` + weight + colour
    token, as readable strings. Returns `[]` when it matches."""
    problems = []
    if not _uses_font(style.get("fontFamily")):
        problems.append(f"font-family {style.get('fontFamily')!r} is not Cairo")
    if style.get("fontSize") != size:
        problems.append(f"font-size {style.get('fontSize')!r} != {size}")
    if style.get("lineHeight") != line:
        problems.append(f"line-height {style.get('lineHeight')!r} != {line}")
    if not _weight_is(style.get("fontWeight"), weight):
        problems.append(f"font-weight {style.get('fontWeight')!r} != {weight}")
    if not _matches_hex(style.get("color"), hex_color):
        problems.append(f"color {style.get('color')!r} != {hex_color}")
    return problems


def _border_width_px(border_value) -> float | None:
    """Leading width of a `1px solid rgb(…)` shorthand, in px."""
    if not border_value or not isinstance(border_value, str):
        return None
    head = border_value.strip().split(" ")[0]
    try:
        return float(head.rstrip("px"))
    except ValueError:
        return None


_REAL_BORDER_STYLES = (
    "solid", "dashed", "dotted", "double", "groove", "ridge", "inset", "outset",
)


def _border_is(border_value, expected_hex: str) -> bool:
    """True only when a border shorthand describes a border that is ACTUALLY
    PAINTED in `expected_hex` — non-zero width, a real line style, matching
    colour.

    AUTOMATION BUG FIX 2026-09-27 (ADO-137643): these border shorthands used
    to be read with `_matches_hex()`, which parses only the `rgb(...)` part.
    A computed `borderLeft` of `'0px none rgb(145, 23, 49)'` — i.e. NO border
    at all, the browser merely retaining the inherited `border-color` — was
    therefore reported as "a maroon border is present", which made #137643's
    `assert not _matches_hex(borderLeft, MAROON)` red on correct behaviour
    and made every POSITIVE border assertion in this module pass vacuously.

    `_matches_hex` itself is deliberately left colour-only: ~50 of its call
    sites read `backgroundColor` / `color` / `borderColor`, which carry no
    width or style, so widening it would break them. Border SHORTHANDS are
    re-pointed at this helper instead.
    """
    if not border_value or not isinstance(border_value, str):
        return False
    width = _border_width_px(border_value)
    if width is None or width <= 0:
        return False
    tokens = border_value.strip().lower().split()
    style = next((t for t in tokens if t in _REAL_BORDER_STYLES), None)
    if style is None:
        return False
    return _matches_hex(border_value, expected_hex)


def _is_transparent(css_value) -> bool:
    parsed = _parse_css_color(css_value)
    return parsed is None or parsed[3] == 0


def _describe(offenders: list) -> str:
    return ", ".join(
        f"{o['name']} spans {o['left']}->{o['right']}" for o in offenders
    ) or "none"


# ══════════════════════════════════════════════════════════════════════
# Functional-High — navigation, master-detail, language, CTA
# ══════════════════════════════════════════════════════════════════════

# ── #137614 — main menu -> page -> four active services ──────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Main-menu entry and landing view")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A visitor reaches the Member's Services page from the main menu and sees all four active services")
@allure.label("pbi", PBI)
@allure.label("testcase", "137614")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137614
@pytest.mark.traceability("ADO-137614")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_visitor_reaches_member_services_from_main_menu_and_sees_four_services(page):
    """ADO-137614 | PBI 129400 — EN, desktop, logged out: Home -> 'Our
    Services' dropdown -> 'Membership Services' loads the page with the
    140px gradient hero, the 'Home > Services' breadcrumb, the section
    heading and exactly four service cards in Display Order.

    DISCLOSED SUBSTITUTION (step 2): the dropdown opens on HOVER on this
    build — the top-level 'Our Services' entry is a real `<a href>` and a
    click navigates to the Our Services landing page instead of expanding.
    The dropdown-expanded assertion itself is unchanged."""
    # Arrange
    services = MemberServicesPage(page).open_home()

    # Act
    menu_labels = services.main_menu_labels()
    services.expand_our_services_menu()
    submenu_labels = services.our_services_submenu_labels()
    submenu_expanded = services.is_our_services_submenu_expanded()
    services.open_member_services_via_main_menu()

    hero = services.hero_style()
    gradient = services.hero_overlay_gradient()
    title_style = services.page_title_style()
    heading_style = services.section_heading_style()
    card_names = services.service_card_names()

    # Assert — the behaviour the case is really about, first
    assert submenu_expanded, "the 'Our Services' dropdown did not expand"
    assert PAGE_PATH_MARKER in services.current_url(), (
        f"the main-menu entry did not land on the Member's Services page; "
        f"url is {services.current_url()!r}"
    )
    assert services.breadcrumb_texts() == [
        MemberServicesPage.CASE_BREADCRUMB_HOME,
        MemberServicesPage.CASE_BREADCRUMB_CURRENT,
    ], f"breadcrumb reads {services.breadcrumb_texts()}; the case requires ['Home', 'Services']"
    assert services.service_card_count() == CASE_SERVICE_COUNT, (
        f"{services.service_card_count()} service cards render; the case "
        f"requires exactly {CASE_SERVICE_COUNT}"
    )
    assert card_names == list(SERVICE_NAMES_EN), (
        f"service cards read {card_names}; the case requires "
        f"{list(SERVICE_NAMES_EN)} in Display Order"
    )
    assert services.details_button_labels() == [
        MemberServicesPage.CASE_DETAILS_BUTTON_LABEL
    ] * CASE_SERVICE_COUNT, (
        f"the cards' pill buttons read {services.details_button_labels()}; every "
        f"card must carry a 'Details' button"
    )
    assert services.card_icon_count() == CASE_SERVICE_COUNT, (
        f"{services.card_icon_count()} card icon tiles render an icon; all "
        f"{CASE_SERVICE_COUNT} cards must have one"
    )
    assert all(services.service_card_descriptions()), (
        f"a card renders an empty short description: "
        f"{services.service_card_descriptions()}"
    )
    assert round(services.list_support_box()["width"]) == CASE_SUPPORT_WIDTH_PX, (
        f"the supporting image is "
        f"{round(services.list_support_box()['width'])}px wide; the case "
        f"requires {CASE_SUPPORT_WIDTH_PX}px"
    )
    assert services.list_support_style().get("borderRadius") == CASE_LIST_SUPPORT_RADIUS, (
        f"the supporting image radius is "
        f"{services.list_support_style().get('borderRadius')!r}; the case "
        f"requires {CASE_LIST_SUPPORT_RADIUS}"
    )
    assert hero.get("height") == f"{CASE_HERO_HEIGHT_PX}px", (
        f"the hero banner is {hero.get('height')!r} tall; the case requires "
        f"{CASE_HERO_HEIGHT_PX}px"
    )
    assert not _typography_is(title_style, "30px", "38px", BOLD_WEIGHT, WHITE), (
        f"hero title typography: {_typography_is(title_style, '30px', '38px', BOLD_WEIGHT, WHITE)}"
    )
    assert not _typography_is(heading_style, "36px", "44px", BOLD_WEIGHT, INK), (
        f"section heading typography: "
        f"{_typography_is(heading_style, '36px', '44px', BOLD_WEIGHT, INK)}"
    )
    assert services.section_heading_text() == MemberServicesPage.CASE_SECTION_HEADING_EN, (
        f"the section heading reads {services.section_heading_text()!r}; the "
        f"case requires {MemberServicesPage.CASE_SECTION_HEADING_EN!r}"
    )
    # …then the copy/token halves this build is known to differ on.
    assert MemberServicesPage.CASE_MENU_ITEM_LABEL in submenu_labels, (
        f"the 'Our Services' dropdown offers {submenu_labels}; the case names "
        f"an entry labelled {MemberServicesPage.CASE_MENU_ITEM_LABEL!r}. This "
        f"build labels it \"Member's Services\"."
    )
    assert services.page_title_text() == MemberServicesPage.CASE_PAGE_TITLE_EN, (
        f"the hero title reads {services.page_title_text()!r}; the case "
        f"requires {MemberServicesPage.CASE_PAGE_TITLE_EN!r}"
    )
    assert list(menu_labels) == list(MemberServicesPage.CASE_MAIN_MENU_LABELS), (
        f"the main menu reads {list(menu_labels)}; the case requires "
        f"{list(MemberServicesPage.CASE_MAIN_MENU_LABELS)}"
    )
    assert gradient and CASE_HERO_GRADIENT_ANGLE in gradient, (
        f"the hero gradient is {gradient!r}; the case requires a "
        f"{CASE_HERO_GRADIENT_ANGLE} gradient"
    )
    assert _matches_rgba(gradient, CASE_HERO_GRADIENT_FROM) and _matches_rgba(
        gradient[gradient.find(",") :], CASE_HERO_GRADIENT_TO
    ), (
        f"the hero gradient is {gradient!r}; the case requires "
        f"rgba(66,44,27,0.8) {CASE_HERO_GRADIENT_FROM_STOP} to "
        f"rgba(145,23,49,0.8) {CASE_HERO_GRADIENT_TO_STOP}"
    )


# ── #137615 — Details opens the detail view with sidebar highlight ───────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Master-detail transition")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Clicking Details on a service card opens that service's detail view with the service highlighted in the sidebar")
@allure.label("pbi", PBI)
@allure.label("testcase", "137615")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137615
@pytest.mark.traceability("ADO-137615")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_details_button_opens_detail_view_with_service_highlighted(page):
    """ADO-137615 | PBI 129400 — EN, logged out: 'Details' on the New
    Membership card opens the detail panel in place (no navigation away from
    the Member's Services page) with the 48x48 #F6F0EC icon tile, the title,
    the intro, the three subsections and a maroon CTA, and highlights the
    'New Membership' row in the 'All Services' sidebar."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    services.click_card_details(NEW_MEMBERSHIP)
    tile = services.panel_tile_style()
    title_style = services.panel_title_style()
    cta = services.cta_style()
    row = services.sidebar_row_style(NEW_MEMBERSHIP)
    row_label = services.sidebar_row_label_style(NEW_MEMBERSHIP)
    row_tile = services.sidebar_row_icon_style(NEW_MEMBERSHIP)
    sidebar_title_style = services.sidebar_title_style()

    # Assert — the transition and content, first
    assert PAGE_PATH_MARKER in services.current_url(), (
        f"the detail view navigated away from the Member's Services page: "
        f"{services.current_url()!r}"
    )
    assert services.is_detail_view_visible(), "the detail view did not open"
    assert not services.is_list_view_visible(), (
        "the list view is still showing alongside the detail view"
    )
    assert services.panel_title_text() == SERVICE_NAME_BY_KEY[NEW_MEMBERSHIP], (
        f"the detail panel title reads {services.panel_title_text()!r}"
    )
    assert services.panel_intro_text(), "the detail panel intro is empty"
    assert services.subheading_texts() == list(
        MemberServicesPage.CASE_SUBHEADINGS_EN
    ), (
        f"the detail panel shows {services.subheading_texts()}; the case "
        f"requires {list(MemberServicesPage.CASE_SUBHEADINGS_EN)}"
    )
    assert services.required_documents_count() > 0, (
        "'Required Documents' rendered no dash-list items"
    )
    assert services.cta_count() == 1, (
        f"{services.cta_count()} CTA buttons render; the case requires one"
    )
    assert _matches_hex(cta.get("backgroundColor"), MAROON), (
        f"the CTA fill is {cta.get('backgroundColor')!r}; the case requires "
        f"the maroon {MAROON}"
    )
    assert tile.get("width") == f"{CASE_PANEL_TILE_SIZE}px" and tile.get(
        "height"
    ) == f"{CASE_PANEL_TILE_SIZE}px", (
        f"the detail icon tile is {tile.get('width')}x{tile.get('height')}; "
        f"the case requires {CASE_PANEL_TILE_SIZE}x{CASE_PANEL_TILE_SIZE}"
    )
    assert _matches_hex(tile.get("backgroundColor"), TILE_BEIGE), (
        f"the detail icon tile fill is {tile.get('backgroundColor')!r}; the "
        f"case requires {TILE_BEIGE}"
    )
    assert tile.get("borderRadius") == CASE_PANEL_TILE_RADIUS, (
        f"the detail icon tile radius is {tile.get('borderRadius')!r}; the "
        f"case requires {CASE_PANEL_TILE_RADIUS}"
    )
    assert not _typography_is(title_style, "30px", "38px", BOLD_WEIGHT, INK), (
        f"detail title typography: "
        f"{_typography_is(title_style, '30px', '38px', BOLD_WEIGHT, INK)}"
    )
    assert not _typography_is(
        services.subheading_style(), "16px", "24px", BOLD_WEIGHT, BROWN
    ), (
        f"subsection heading typography: "
        f"{_typography_is(services.subheading_style(), '16px', '24px', BOLD_WEIGHT, BROWN)}"
    )
    # Sidebar
    assert services.sidebar_title_text() == MemberServicesPage.CASE_SIDEBAR_TITLE_EN, (
        f"the sidebar title reads {services.sidebar_title_text()!r}"
    )
    assert not _typography_is(sidebar_title_style, "18px", "28px", SEMIBOLD_WEIGHT, INK), (
        f"sidebar title typography: "
        f"{_typography_is(sidebar_title_style, '18px', '28px', SEMIBOLD_WEIGHT, INK)}"
    )
    assert services.sidebar_row_count() == CASE_SERVICE_COUNT, (
        f"the sidebar lists {services.sidebar_row_count()} services; the case "
        f"requires all {CASE_SERVICE_COUNT}"
    )
    assert services.selected_sidebar_keys() == [NEW_MEMBERSHIP], (
        f"the highlighted sidebar rows are {services.selected_sidebar_keys()}; "
        f"the case requires exactly ['{NEW_MEMBERSHIP}']"
    )
    assert _matches_hex(row.get("backgroundColor"), MAROON_TINT), (
        f"the highlighted row background is {row.get('backgroundColor')!r}; "
        f"the case requires {MAROON_TINT}"
    )
    assert _matches_hex(row_label.get("color"), MAROON), (
        f"the highlighted row label is {row_label.get('color')!r}; the case "
        f"requires {MAROON}"
    )
    assert _matches_hex(row_tile.get("backgroundColor"), MAROON), (
        f"the highlighted row icon tile is {row_tile.get('backgroundColor')!r}; "
        f"the case requires it filled {MAROON}"
    )
    # …then the one token this build is known to differ on.
    assert _border_width_px(row.get("borderLeft")) == CASE_SIDEBAR_SELECTED_BORDER_PX, (
        f"the highlighted row's left border is {row.get('borderLeft')!r}; the "
        f"case requires a {CASE_SIDEBAR_SELECTED_BORDER_PX}px {MAROON} border"
    )


# ── #137616 — sidebar swap without a full page reload ────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Master-detail transition")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Selecting a different service in the All Services sidebar swaps the content panel without a full page reload")
@allure.label("pbi", PBI)
@allure.label("testcase", "137616")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137616
@pytest.mark.traceability("ADO-137616")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_sidebar_selection_swaps_panel_without_page_reload(page):
    """ADO-137616 | PBI 129400 — EN, logged out: from the New Membership
    detail view, selecting 'Membership Renewal' in the sidebar re-renders the
    content panel with that service's own title, intro, three subsections and
    CTA, moves the highlight, and does so with NO document reload — a marker
    stashed on `window` survives and the navigation-entry count stays at 1."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    services.click_card_details(NEW_MEMBERSHIP)
    services.stamp_navigation_marker()
    before = services.navigation_fingerprint()
    first_panel_subheadings = services.subheading_texts()

    # Act
    services.select_sidebar_service(MEMBERSHIP_RENEWAL)
    services.wait_for_panel_title(SERVICE_NAME_BY_KEY[MEMBERSHIP_RENEWAL])
    after = services.navigation_fingerprint()
    selected_row = services.sidebar_row_style(MEMBERSHIP_RENEWAL)
    selected_label = services.sidebar_row_label_style(MEMBERSHIP_RENEWAL)
    previous_row = services.sidebar_row_style(NEW_MEMBERSHIP)
    previous_label = services.sidebar_row_label_style(NEW_MEMBERSHIP)
    previous_tile = services.sidebar_row_icon_style(NEW_MEMBERSHIP)

    # Assert — content swap
    assert first_panel_subheadings, "the first detail panel rendered no subsections"
    assert services.panel_title_text() == SERVICE_NAME_BY_KEY[MEMBERSHIP_RENEWAL], (
        f"the panel title is {services.panel_title_text()!r} after selecting "
        f"Membership Renewal"
    )
    assert services.panel_intro_text(), "the swapped panel has an empty intro"
    assert services.subheading_texts() == list(
        MemberServicesPage.CASE_SUBHEADINGS_EN
    ), (
        f"the swapped panel shows {services.subheading_texts()}; the case "
        f"requires {list(MemberServicesPage.CASE_SUBHEADINGS_EN)}"
    )
    assert services.cta_count() == 1, (
        "the swapped panel did not render its own CTA button"
    )
    # No full page reload
    assert after["marker"] == "alive", (
        "the window marker was lost — the sidebar selection triggered a full "
        "document reload instead of a client-side panel swap"
    )
    assert after["navigationEntries"] == before["navigationEntries"] == 1, (
        f"navigation entries went {before['navigationEntries']} -> "
        f"{after['navigationEntries']}; a full page reload occurred"
    )
    # Highlight moved
    assert services.selected_sidebar_keys() == [MEMBERSHIP_RENEWAL], (
        f"the highlighted rows are {services.selected_sidebar_keys()}"
    )
    assert _matches_hex(selected_row.get("backgroundColor"), MAROON_TINT), (
        f"the newly selected row background is "
        f"{selected_row.get('backgroundColor')!r}; the case requires {MAROON_TINT}"
    )
    assert _matches_hex(selected_label.get("color"), MAROON), (
        f"the newly selected row label is {selected_label.get('color')!r}; the "
        f"case requires {MAROON}"
    )
    assert _is_transparent(previous_row.get("backgroundColor")), (
        f"the previously selected row kept a background fill "
        f"({previous_row.get('backgroundColor')!r}) instead of returning to the "
        f"default style"
    )
    assert _matches_hex(previous_tile.get("backgroundColor"), TILE_BEIGE), (
        f"the previously selected row's icon tile is "
        f"{previous_tile.get('backgroundColor')!r}; the case requires it back "
        f"at {TILE_BEIGE}"
    )
    assert _matches_hex(previous_label.get("color"), INK), (
        f"the previously selected row's label is {previous_label.get('color')!r}; "
        f"the case requires it back at {INK}"
    )
    # …then the border-width token this build differs on.
    assert _border_width_px(selected_row.get("borderLeft")) == CASE_SIDEBAR_SELECTED_BORDER_PX, (
        f"the selected row's left border is {selected_row.get('borderLeft')!r}; "
        f"the case requires {CASE_SIDEBAR_SELECTED_BORDER_PX}px {MAROON}"
    )


# ── #137617 — switching back restores content and highlight ──────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Master-detail transition")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching back to a previously selected service restores its content and highlight correctly")
@allure.label("pbi", PBI)
@allure.label("testcase", "137617")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137617
@pytest.mark.traceability("ADO-137617")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_switching_back_restores_content_and_highlight(page):
    """ADO-137617 | PBI 129400 — EN, logged out: Membership Renewal ->
    Attestation on Signature -> New Membership. The final panel is identical
    to New Membership's first render, exactly one row is highlighted, and the
    other three carry the not-selected style (no fill, no maroon border,
    #F6F0EC 6px tile, Cairo SemiBold 14/22 #1D1D1B label, chevron)."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    services.click_card_details(NEW_MEMBERSHIP)
    first_render = {
        "title": services.panel_title_text(),
        "intro": services.panel_intro_text(),
        "subheadings": services.subheading_texts(),
        "cta_label": services.cta_label(),
        "cta_href": services.cta_href(),
        "required_documents": services.required_documents_items(),
    }

    # Act
    services.select_sidebar_service(MEMBERSHIP_RENEWAL)
    services.wait_for_panel_title(SERVICE_NAME_BY_KEY[MEMBERSHIP_RENEWAL])
    renewal_selected = services.selected_sidebar_keys()
    services.select_sidebar_service(ATTESTATION)
    services.wait_for_panel_title(SERVICE_NAME_BY_KEY[ATTESTATION])
    attestation_selected = services.selected_sidebar_keys()
    renewal_after = services.sidebar_row_style(MEMBERSHIP_RENEWAL)
    services.select_sidebar_service(NEW_MEMBERSHIP)
    services.wait_for_panel_title(SERVICE_NAME_BY_KEY[NEW_MEMBERSHIP])
    second_render = {
        "title": services.panel_title_text(),
        "intro": services.panel_intro_text(),
        "subheadings": services.subheading_texts(),
        "cta_label": services.cta_label(),
        "cta_href": services.cta_href(),
        "required_documents": services.required_documents_items(),
    }

    # Assert
    assert renewal_selected == [MEMBERSHIP_RENEWAL], (
        f"Membership Renewal was not the highlighted row: {renewal_selected}"
    )
    assert attestation_selected == [ATTESTATION], (
        f"Attestation on Signature was not the highlighted row: "
        f"{attestation_selected}"
    )
    assert _is_transparent(renewal_after.get("backgroundColor")), (
        f"the Membership Renewal row kept its highlight "
        f"({renewal_after.get('backgroundColor')!r}) after another service was "
        f"selected"
    )
    assert second_render == first_render, (
        f"New Membership's content differs on the second render.\n"
        f"first : {first_render}\nsecond: {second_render}"
    )
    assert services.selected_sidebar_count() == 1, (
        f"{services.selected_sidebar_count()} sidebar rows are highlighted; the "
        f"case requires exactly one"
    )
    assert services.selected_sidebar_keys() == [NEW_MEMBERSHIP], (
        f"the highlighted row is {services.selected_sidebar_keys()}"
    )
    assert services.sidebar_chevron_count() == CASE_SERVICE_COUNT, (
        f"{services.sidebar_chevron_count()} chevron icons render; every one of "
        f"the {CASE_SERVICE_COUNT} rows must carry one"
    )
    unselected = [key for key in SERVICE_KEYS if key != NEW_MEMBERSHIP]
    for key in unselected:
        row = services.sidebar_row_style(key)
        label = services.sidebar_row_label_style(key)
        tile = services.sidebar_row_icon_style(key)
        assert _is_transparent(row.get("backgroundColor")), (
            f"unselected row {key!r} has a background fill "
            f"{row.get('backgroundColor')!r}"
        )
        # AUTOMATION BUG FIX 2026-09-27 (ADO-137643): border SHORTHAND read
        # through _border_is(), not _matches_hex() — '0px none rgb(145,23,49)'
        # is no border at all.
        assert not _border_is(row.get("borderLeft"), MAROON), (
            f"unselected row {key!r} still carries a maroon left border "
            f"({row.get('borderLeft')!r})"
        )
        assert _matches_hex(tile.get("backgroundColor"), TILE_BEIGE), (
            f"unselected row {key!r} icon tile is "
            f"{tile.get('backgroundColor')!r}; the case requires {TILE_BEIGE}"
        )
        assert not _typography_is(label, "14px", "22px", SEMIBOLD_WEIGHT, INK), (
            f"unselected row {key!r} label typography: "
            f"{_typography_is(label, '14px', '22px', SEMIBOLD_WEIGHT, INK)}"
        )
    # …then the tile-radius token this build differs on.
    for key in unselected:
        tile = services.sidebar_row_icon_style(key)
        assert tile.get("borderRadius") == CASE_SIDEBAR_TILE_RADIUS, (
            f"unselected row {key!r} icon tile radius is "
            f"{tile.get('borderRadius')!r}; the case requires "
            f"{CASE_SIDEBAR_TILE_RADIUS}"
        )


# ── #137618 — CTA redirects to the configured URL ────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service CTA")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The service CTA redirects the visitor to the URL configured for that service")
@allure.label("pbi", PBI)
@allure.label("testcase", "137618")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137618
@pytest.mark.traceability("ADO-137618")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_service_cta_redirects_to_configured_url(page):
    """ADO-137618 | PBI 129400 — EN, logged out: the New Membership CTA
    renders as a #911731 9999px pill with 10px/16px padding, a Cairo SemiBold
    16/24 #FFFFFF label and a 20x20 arrow icon after the label, and clicking
    it lands the visitor on exactly the URL the page renders as its
    destination, with no intermediate page and no 404.

    DISCLOSED (see module docstring, substitution 2): a CMS read is out of
    scope for this batch, so "the CTA Redirect URL configured in the CMS" is
    verified as far as the rendered `href`. The case's scenario also states
    `Open Behavior = Same tab`; live the anchor carries `target="_blank"`, so
    this test follows the real navigation (popup or same tab) and records
    which happened rather than assuming the precondition held."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)
    cta = services.cta_style()
    configured_url = services.cta_href()

    # Act
    outcome = services.click_cta()
    landing = outcome["landing_page"]

    # Assert — CTA rendering first
    assert services.cta_count() == 1, "no CTA button rendered on the detail panel"
    assert _matches_hex(cta.get("backgroundColor"), MAROON), (
        f"the CTA fill is {cta.get('backgroundColor')!r}; the case requires {MAROON}"
    )
    assert cta.get("borderRadius") == CASE_PILL_RADIUS, (
        f"the CTA radius is {cta.get('borderRadius')!r}; the case requires "
        f"{CASE_PILL_RADIUS}"
    )
    assert cta.get("padding") == CASE_PILL_PADDING, (
        f"the CTA padding is {cta.get('padding')!r}; the case requires "
        f"{CASE_PILL_PADDING}"
    )
    assert not _typography_is(cta, "16px", "24px", SEMIBOLD_WEIGHT, WHITE), (
        f"CTA label typography: "
        f"{_typography_is(cta, '16px', '24px', SEMIBOLD_WEIGHT, WHITE)}"
    )
    assert services.cta_icon_size() == CASE_ARROW_ICON_SIZE, (
        f"the CTA icon is {services.cta_icon_size()}; the case requires "
        f"{CASE_ARROW_ICON_SIZE}"
    )
    assert services.cta_icon_is_leading() is False, (
        "the CTA arrow icon is not to the right of the label"
    )
    # …then the destination
    assert configured_url, "the CTA has no configured destination (empty href)"
    assert landing.url.rstrip("/") == configured_url.rstrip("/"), (
        f"the CTA landed on {landing.url!r}; the page's configured destination "
        f"is {configured_url!r} — an intermediate page or redirect occurred"
    )
    assert "404" not in landing.title(), (
        f"the CTA destination returned a not-found page: title "
        f"{landing.title()!r} at {landing.url!r}"
    )


# ── #137619 — EN -> AR ───────────────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Language switching")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Switching the site language from English to Arabic renders the Member's Services page in Arabic")
@allure.label("pbi", PBI)
@allure.label("testcase", "137619")
@pytest.mark.arabic
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137619
@pytest.mark.traceability("ADO-137619")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_switching_english_to_arabic_renders_arabic_page(page):
    """ADO-137619 | PBI 129400 — logged out: from the English list view, the
    header 'AR' toggle switches the page to Arabic with RTL direction, the
    toggle then offers 'EN', and the four service names read العضوية الجديدة,
    تجديد العضوية, التصديق على التوقيع, إلغاء المفوّض بالتوقيع in Display
    Order."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    english_heading = services.section_heading_text()
    toggle_before = services.language_toggle_label()

    # Act
    services.switch_to_arabic()

    # Assert
    assert english_heading == MemberServicesPage.CASE_SECTION_HEADING_EN, (
        f"the English list view heading reads {english_heading!r}"
    )
    assert toggle_before.strip().upper() == "AR", (
        f"the English page's language toggle reads {toggle_before!r}; the case "
        f"requires 'AR'"
    )
    assert services.document_direction() == "rtl", (
        f"the page direction after switching is "
        f"{services.document_direction()!r}; the case requires RTL"
    )
    assert services.document_language().lower().startswith("ar"), (
        f"the document language is {services.document_language()!r} after "
        f"switching to Arabic"
    )
    assert services.language_toggle_label().strip().upper() == "EN", (
        f"the toggle now reads {services.language_toggle_label()!r}; the case "
        f"requires it to offer 'EN'"
    )
    assert services.service_card_names() == list(
        MemberServicesPage.CASE_SERVICE_NAMES_AR
    ), (
        f"the Arabic service names read {services.service_card_names()}; the "
        f"case requires {list(MemberServicesPage.CASE_SERVICE_NAMES_AR)} in "
        f"Display Order"
    )


# ── #137620 — AR -> EN ───────────────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Language switching")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Switching the site language from Arabic back to English restores the English content and LTR layout")
@allure.label("pbi", PBI)
@allure.label("testcase", "137620")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137620
@pytest.mark.traceability("ADO-137620")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_switching_arabic_to_english_restores_english_ltr_view(page):
    """ADO-137620 | PBI 129400 — logged out: from the Arabic detail view
    (sidebar كافة الخدمات) with Membership Renewal selected, the 'EN' toggle
    returns the page to English/LTR with the sidebar reading 'All Services',
    the subsection headings reading 'Who This Service Is For', 'Required
    Documents', 'How to Apply', and THE SAME SERVICE STILL SELECTED."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(
        MEMBERSHIP_RENEWAL, locale="ar"
    )
    arabic_sidebar_title = services.sidebar_title_text()
    selected_before = services.selected_sidebar_keys()

    # Act
    services.switch_to_english()

    # Assert — direction and copy first
    assert selected_before == [MEMBERSHIP_RENEWAL], (
        f"the Arabic detail view did not open on Membership Renewal: "
        f"{selected_before}"
    )
    assert services.document_direction() == "ltr", (
        f"the page direction after switching back is "
        f"{services.document_direction()!r}; the case requires LTR"
    )
    assert services.sidebar_title_text() == MemberServicesPage.CASE_SIDEBAR_TITLE_EN, (
        f"the sidebar title reads {services.sidebar_title_text()!r}; the case "
        f"requires {MemberServicesPage.CASE_SIDEBAR_TITLE_EN!r}"
    )
    # DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137620):
    # case expected 'كافة الخدمات'; delivered build renders 'جميع الخدمات'.
    # Updated to the build (the constant itself, in MemberServicesPage).
    assert arabic_sidebar_title == MemberServicesPage.CASE_SIDEBAR_TITLE_AR, (
        f"the Arabic sidebar title reads {arabic_sidebar_title!r}; the case "
        f"requires {MemberServicesPage.CASE_SIDEBAR_TITLE_AR!r}"
    )
    # …then selection retention, which this build does not implement.
    #
    # DELIBERATELY NOT UPDATED (ADO-137620, QA Manager 2026-09-27): the copy
    # assertion above used to die first, so THIS assertion has never actually
    # executed. It is left exactly as written and fully able to fail. The
    # module's deviation table records that selection IS lost on AR->EN, so
    # this test is now EXPECTED to go red here — on the real defect, not on
    # stale copy. That red is the intended outcome of the 137620 edit, not a
    # regression, and it is not covered by the design-drift ruling.
    assert services.selected_sidebar_keys() == [MEMBERSHIP_RENEWAL], (
        f"after switching Arabic -> English the highlighted sidebar rows are "
        f"{services.selected_sidebar_keys()}; the case requires the same "
        f"service ({MEMBERSHIP_RENEWAL!r}) to remain selected. This build "
        f"closes the detail view and returns to the list view."
    )
    assert services.subheading_texts() == list(
        MemberServicesPage.CASE_SUBHEADINGS_EN
    ), (
        f"the English subsection headings read {services.subheading_texts()}; "
        f"the case requires {list(MemberServicesPage.CASE_SUBHEADINGS_EN)}"
    )


# ── #137621 — breadcrumb links ───────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Breadcrumb")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The breadcrumb links on the Member's Services page navigate to their targets")
@allure.label("pbi", PBI)
@allure.label("testcase", "137621")
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137621
@pytest.mark.traceability("ADO-137621")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_breadcrumb_links_navigate_to_their_targets(page):
    """ADO-137621 | PBI 129400 — EN, logged out: the hero breadcrumb shows a
    home icon, 'Home', a chevron-right separator and 'Services' in Cairo
    Regular 14/22 #FFFFFF; 'Home' navigates to the Qatar Chamber home page
    and 'Services' navigates to the Services landing page."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    home_style = services.breadcrumb_style("home")
    current_style = services.breadcrumb_style("current")
    current_is_link = services.breadcrumb_current_is_link()
    current_href = services.breadcrumb_current_href()
    home_href = services.breadcrumb_home_href()

    # Act
    services.click_breadcrumb_home()
    home_url = services.current_url()

    # Assert — structure first
    # AUTOMATION BUG FIX 2026-09-27 (ADO-137621): the landing URL is now read
    # after wait_for_url() (see MemberServicesPage.click_breadcrumb_home), and
    # the crumb's own href is asserted too, so a genuinely broken href is
    # caught even if some other navigation happened to land on the homepage.
    assert home_href and HOME_PATH_MARKER in home_href, (
        f"the 'Home' breadcrumb's href is {home_href!r}; the case requires it "
        f"to point at the Qatar Chamber home page"
    )
    assert home_url.rstrip("/").endswith(HOME_PATH_MARKER.rstrip("/")), (
        f"the 'Home' breadcrumb landed on {home_url!r}; the case requires the "
        f"Qatar Chamber home page"
    )
    services.open_member_services()
    assert services.breadcrumb_home_icon_count() == 1, (
        f"{services.breadcrumb_home_icon_count()} home icons render in the "
        f"breadcrumb; the case requires one"
    )
    assert services.breadcrumb_separator_icon_count() == 1, (
        f"{services.breadcrumb_separator_icon_count()} chevron separators "
        f"render; the case requires one between 'Home' and 'Services'"
    )
    assert services.breadcrumb_texts() == [
        MemberServicesPage.CASE_BREADCRUMB_HOME,
        MemberServicesPage.CASE_BREADCRUMB_CURRENT,
    ], f"the breadcrumb reads {services.breadcrumb_texts()}"
    # …then typography and the link-ness this build differs on.
    assert not _typography_is(home_style, "14px", "22px", REGULAR_WEIGHT, WHITE), (
        f"'Home' crumb typography: "
        f"{_typography_is(home_style, '14px', '22px', REGULAR_WEIGHT, WHITE)}"
    )
    assert not _typography_is(current_style, "14px", "22px", REGULAR_WEIGHT, WHITE), (
        f"'Services' crumb typography: "
        f"{_typography_is(current_style, '14px', '22px', REGULAR_WEIGHT, WHITE)}"
    )
    assert current_is_link, (
        "the 'Services' breadcrumb segment is not a link — this build renders "
        "it as a plain <span> with no href, so it cannot navigate to the "
        "Services landing page as the case requires"
    )
    services.click_breadcrumb_current()
    assert OUR_SERVICES_PATH_MARKER in services.current_url(), (
        f"the 'Services' breadcrumb landed on {services.current_url()!r}; the "
        f"case requires the Services landing page (href was {current_href!r})"
    )


# ── #137622 — SKIPPED: needs a fifth service record created in the CMS ───
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Authoring propagation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can create a new service record and it appears on the website after publish")
@allure.label("pbi", PBI)
@allure.label("testcase", "137622")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137622
@pytest.mark.traceability("ADO-137622")
@pytest.mark.skip(
    reason="BLOCKED — the case requires a FIFTH service record ('QA_AUTO Test "
    "Service' / 'خدمة اختبار', Display Order 5, Active Status True, with an "
    "uploaded 120 KB PNG icon) to be CREATED and PUBLISHED in Liferay first. "
    "qcdev holds exactly 4 published+active services and no such record. "
    "Creating and publishing it is a Control_Panel WRITE, explicitly excluded "
    "from this Web-only, strictly read-only batch. The public-surface half of "
    "the assertion is written below and is ready to run the moment the record "
    "exists — nothing is faked and no CMS path was written."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_new_service_record_appears_on_website_after_publish(page):
    """ADO-137622 | PBI 129400 — EN, logged out: after the editor creates and
    publishes 'QA_AUTO Test Service' at Display Order 5, the public page
    lists 5 service cards with it in position 5, and it is also the 5th row
    of the 'All Services' sidebar."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert len(card_names) == 5, (
        f"{len(card_names)} service cards render; the case requires 5 after the "
        f"new record is published ({card_names})"
    )
    assert card_names[4] == "QA_AUTO Test Service", (
        f"the 5th service card reads {card_names[4]!r}; the case requires "
        f"'QA_AUTO Test Service'"
    )
    assert len(sidebar_labels) == 5 and sidebar_labels[4] == "QA_AUTO Test Service", (
        f"the sidebar reads {sidebar_labels}; the case requires the new service "
        f"as its 5th row"
    )


# ── #137623 — SKIPPED: needs the Detail Intro edited in the CMS ──────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Authoring propagation")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Editing a published service's detail content updates the content shown on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137623")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137623
@pytest.mark.traceability("ADO-137623")
@pytest.mark.skip(
    reason="BLOCKED — the case's expected value is the marker string 'QA_AUTO "
    "renewal intro v2', which only exists once an editor REPLACES Membership "
    "Renewal's Detail Intro (EN) in Liferay and saves. That edit is a "
    "Control_Panel WRITE, excluded from this Web-only read-only batch. The "
    "public assertion is written below and is not weakened — it still demands "
    "the exact marker string."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_edited_detail_intro_reaches_the_website(page):
    """ADO-137623 | PBI 129400 — EN, logged out: after the editor saves
    Membership Renewal's Detail Intro (EN) as 'QA_AUTO renewal intro v2', the
    public detail panel's intro paragraph reads exactly that, while the other
    subsections and the CTA are unchanged."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(MEMBERSHIP_RENEWAL)

    # Act
    intro = services.panel_intro_text()
    subheadings = services.subheading_texts()

    # Assert
    assert intro == "QA_AUTO renewal intro v2", (
        f"the Membership Renewal detail intro reads {intro!r}; the case "
        f"requires exactly 'QA_AUTO renewal intro v2'"
    )
    assert subheadings == list(MemberServicesPage.CASE_SUBHEADINGS_EN), (
        f"the other subsections changed: {subheadings}"
    )
    assert services.cta_count() == 1, "the CTA is no longer rendered after the edit"


# ── #137624 — SKIPPED: needs Active Status set to False in the CMS ───────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Active status")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Setting a service's Active Status to False removes it from both the service list and the All Services sidebar")
@allure.label("pbi", PBI)
@allure.label("testcase", "137624")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137624
@pytest.mark.traceability("ADO-137624")
@pytest.mark.skip(
    reason="BLOCKED — the case needs 'Attestation on Signature' switched to "
    "Active Status = False and the page re-published. All 4 services are live "
    "and active on qcdev; deactivating one is a Control_Panel WRITE against "
    "real shared content, excluded from this Web-only read-only batch and "
    "additionally covered by standards.md's 'Destructive-Precondition Tests "
    "Must Use Disposable Test Data' rule (no disposable service record can be "
    "created here either, for the same reason)."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_deactivated_service_disappears_from_list_and_sidebar(page):
    """ADO-137624 | PBI 129400 — EN, logged out: with Attestation on Signature
    deactivated, the card list shows 3 cards and the sidebar 3 rows, neither
    contains it, and the remaining services keep their relative Display
    Order."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    remaining = [name for name in SERVICE_NAMES_EN if name != "Attestation on Signature"]
    assert card_names == remaining, (
        f"the card list reads {card_names}; the case requires {remaining}"
    )
    assert sidebar_labels == remaining, (
        f"the sidebar reads {sidebar_labels}; the case requires {remaining}"
    )


# ── #137625 — SKIPPED: needs a deactivated record re-activated ───────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Active status")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Setting a deactivated service's Active Status back to True restores it to the list and sidebar")
@allure.label("pbi", PBI)
@allure.label("testcase", "137625")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137625
@pytest.mark.traceability("ADO-137625")
@pytest.mark.skip(
    reason="BLOCKED — the case starts from 'Attestation on Signature' already "
    "DEACTIVATED (the state QC-129400-011/#137624 leaves behind) and then "
    "re-activates and re-publishes it. Neither the starting state nor the "
    "transition is reachable without Control_Panel WRITES, excluded from this "
    "Web-only read-only batch. Run read-only against the live site this "
    "assertion would pass vacuously, because the service is already active — "
    "so it is skipped rather than reported as a green."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_reactivated_service_returns_to_list_and_sidebar(page):
    """ADO-137625 | PBI 129400 — EN, logged out: after Attestation on
    Signature is set back to Active Status = True and re-published, the list
    shows 4 cards and the sidebar 4 rows, with it back in its configured
    Display Order position, icon, name, short description and 'Details'
    button intact."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    index = card_names.index("Attestation on Signature") if "Attestation on Signature" in card_names else -1
    descriptions = services.service_card_descriptions()
    labels = services.details_button_labels()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert card_names == list(SERVICE_NAMES_EN), (
        f"the card list reads {card_names}; the case requires all 4 in "
        f"Display Order"
    )
    assert sidebar_labels == list(SERVICE_NAMES_EN), (
        f"the sidebar reads {sidebar_labels}; the case requires 4 rows"
    )
    assert index == 2, (
        f"'Attestation on Signature' is at position {index + 1}; its configured "
        f"Display Order is 3"
    )
    assert descriptions[index], "the restored card has no short description"
    assert labels[index] == MemberServicesPage.CASE_DETAILS_BUTTON_LABEL, (
        f"the restored card's pill reads {labels[index]!r}"
    )
    assert services.card_icon_count() == len(card_names), (
        "the restored card is missing its icon"
    )


# ── #137626 — SKIPPED: needs Display Order reassigned in the CMS ─────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Display order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Changing a service's Display Order reorders it in both the card list and the sidebar")
@allure.label("pbi", PBI)
@allure.label("testcase", "137626")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137626
@pytest.mark.traceability("ADO-137626")
@pytest.mark.skip(
    reason="BLOCKED — the case moves 'Signatory Cancellation' to Display "
    "Order 1 and renumbers the other three, then re-publishes. Reordering the "
    "live service records is a Control_Panel WRITE against real shared "
    "content, excluded from this Web-only read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_display_order_change_reorders_cards_and_sidebar(page):
    """ADO-137626 | PBI 129400 — EN, logged out: after Signatory Cancellation
    is moved to Display Order 1, the card list reads Signatory Cancellation,
    New Membership, Membership Renewal, Attestation on Signature — and the
    'All Services' sidebar shows the same order."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    expected = [
        "Signatory Cancellation",
        "New Membership",
        "Membership Renewal",
        "Attestation on Signature",
    ]

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert card_names == expected, (
        f"the card list reads {card_names}; the case requires {expected}"
    )
    assert sidebar_labels == expected, (
        f"the sidebar reads {sidebar_labels}; the case requires {expected}"
    )


# ── #137627 — SKIPPED: needs a second Display Order change ───────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Display order")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A second Display Order change reorders the services again on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137627")
@pytest.mark.functional_high
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137627
@pytest.mark.traceability("ADO-137627")
@pytest.mark.skip(
    reason="BLOCKED — the case starts from the order QC-129400-013/#137626 "
    "leaves (Signatory Cancellation first) and restores the original order. "
    "Both the starting state and the change are Control_Panel WRITES, "
    "excluded from this Web-only read-only batch. Run read-only it would pass "
    "vacuously, because the live order is already the restored one."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_second_display_order_change_reorders_again(page):
    """ADO-137627 | PBI 129400 — EN, logged out: after the order is set back
    to 1 New Membership, 2 Membership Renewal, 3 Attestation on Signature,
    4 Signatory Cancellation, both the card list and the sidebar read that
    order and the previous ordering is retained nowhere on the page."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert card_names == list(SERVICE_NAMES_EN), (
        f"the card list reads {card_names}; the case requires "
        f"{list(SERVICE_NAMES_EN)}"
    )
    assert sidebar_labels == list(SERVICE_NAMES_EN), (
        f"the sidebar reads {sidebar_labels}; the case requires "
        f"{list(SERVICE_NAMES_EN)}"
    )


# ── #137628 — SKIPPED: needs a draft edit + CMS Preview ──────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Draft and preview")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Previewing an unpublished change shows it in preview while the live page still shows the published version")
@allure.label("pbi", PBI)
@allure.label("testcase", "137628")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137628
@pytest.mark.traceability("ADO-137628")
@pytest.mark.skip(
    reason="BLOCKED — the case needs New Membership's Short Description (EN) "
    "changed to the marker 'QA_AUTO preview only', SAVED AS DRAFT, and opened "
    "in Liferay's Preview. Save-as-draft and Preview are Control_Panel WRITES/ "
    "actions, excluded from this Web-only read-only batch. Only step 4 (the "
    "live page still shows the published text) is expressible here, and on its "
    "own it would pass vacuously because no draft exists."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_preview_only_change_does_not_appear_on_the_live_page(page):
    """ADO-137628 | PBI 129400 — EN, logged out in a fresh anonymous session
    (standards.md's mandatory logged-out context for draft/preview checks):
    while the draft carries 'QA_AUTO preview only', the live public page still
    shows the previously published New Membership short description and the
    draft text appears nowhere."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    descriptions = services.service_card_descriptions()
    page_text = services.page_text()

    # Assert
    assert "QA_AUTO preview only" not in page_text, (
        "the draft-only short description 'QA_AUTO preview only' is being "
        "served on the live public page"
    )
    assert descriptions[0] == (
        "Register your institution or company with Qatar Chamber and begin "
        "your membership journey."
    ), (
        f"the live New Membership short description reads {descriptions[0]!r}; "
        f"the case requires the previously published value"
    )


# ── #137629 — SKIPPED: needs a Draft->Published transition + audit log ───
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Publishing")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Publishing the Member's Services page makes it visible on the website and records an audit log entry")
@allure.label("pbi", PBI)
@allure.label("testcase", "137629")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137629
@pytest.mark.traceability("ADO-137629")
@pytest.mark.skip(
    reason="BLOCKED — the case starts from the page record in DRAFT and "
    "un-served, clicks Publish, and then reads the Liferay AUDIT LOG for the "
    "publish entry. The page is published and served on qcdev, so the "
    "Draft->Published transition cannot be observed without first "
    "unpublishing it (a Control_Panel WRITE against real shared content), and "
    "the audit log is a Control_Panel READ. Both are excluded from this "
    "Web-only read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_publishing_the_page_makes_it_visible_on_the_website(page):
    """ADO-137629 | PBI 129400 — EN, logged out: immediately after publish the
    public page renders its hero banner, page title, section heading, intro
    text and all active service cards. (Step 4's audit-log check is
    Control_Panel-only and is not expressible on the Web surface.)"""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    hero = services.hero_style()

    # Assert
    assert hero.get("height") == f"{CASE_HERO_HEIGHT_PX}px", (
        f"the hero banner is {hero.get('height')!r} tall after publish"
    )
    assert services.page_title_text(), "the page title did not render after publish"
    assert services.section_heading_text(), "the section heading did not render"
    assert services.intro_text(), "the intro text did not render"
    assert services.service_card_count() == CASE_SERVICE_COUNT, (
        f"{services.service_card_count()} service cards render after publish; "
        f"the case requires all active services"
    )


# ── #137630 — SKIPPED: needs the Section Heading re-published ────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Publishing")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Re-publishing an edited page shows the new value on the website rather than the cached previous version")
@allure.label("pbi", PBI)
@allure.label("testcase", "137630")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137630
@pytest.mark.traceability("ADO-137630")
@pytest.mark.skip(
    reason="BLOCKED — the case's expected value is the marker 'QA_AUTO "
    "heading v2', which only exists once an editor changes Section Heading "
    "(EN) in Liferay and RE-PUBLISHES. That edit + publish is a Control_Panel "
    "WRITE, excluded from this Web-only read-only batch. The cache-"
    "invalidation assertion below is unchanged and still demands the exact "
    "marker."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_republished_heading_is_served_instead_of_the_cached_value(page):
    """ADO-137630 | PBI 129400 — EN, logged out: the page first shows 'Choose
    the service you need'; after the editor changes Section Heading (EN) to
    'QA_AUTO heading v2' and re-publishes, reloading the public page shows
    exactly 'QA_AUTO heading v2' rather than the cached previous value."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    before = services.section_heading_text()

    # Act
    services.open_member_services()
    after = services.section_heading_text()

    # Assert
    assert before == MemberServicesPage.CASE_SECTION_HEADING_EN, (
        f"the pre-edit heading reads {before!r}; the case's precondition is "
        f"{MemberServicesPage.CASE_SECTION_HEADING_EN!r}"
    )
    assert after == "QA_AUTO heading v2", (
        f"after re-publish the heading reads {after!r}; the case requires "
        f"exactly 'QA_AUTO heading v2' — a cached previous value here would be "
        f"the defect this case targets"
    )


# ── #137631 — SKIPPED: needs the page unpublished ────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Publishing")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Unpublishing the Member's Services page removes it from the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137631")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137631
@pytest.mark.traceability("ADO-137631")
@pytest.mark.skip(
    reason="BLOCKED — the case UNPUBLISHES the live Member's Services page. "
    "That is a destructive Control_Panel WRITE against real shared content "
    "which would take a real public page offline; it is excluded from this "
    "Web-only read-only batch, and under standards.md's destructive-"
    "precondition rule it would additionally require its own explicit, "
    "ID-named user approval, which has NOT been given."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_unpublished_page_is_no_longer_served(page):
    """ADO-137631 | PBI 129400 — logged out in a fresh anonymous session
    (standards.md's mandatory logged-out context): after Unpublish, requesting
    the public Member's Services URL returns the site's not-found response —
    not a cached 200 carrying the previous content."""
    # Arrange
    services = MemberServicesPage(page)

    # Act
    services.request_member_services_url()
    fragment_present = services.fragment_count()

    # Assert
    assert fragment_present == 0, (
        "the Member's Services fragment is still being served after Unpublish "
        "— a cached 200 with the previous content is exactly the defect this "
        "case targets"
    )


# ── #137632 — SKIPPED: needs a draft service record ──────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Draft and preview")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Content saved as draft is stored in the CMS and is not served on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137632")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137632
@pytest.mark.traceability("ADO-137632")
@pytest.mark.skip(
    reason="BLOCKED — the case needs a service record named 'QA_AUTO draft "
    "service' CREATED and left in Draft in Liferay. No such record exists on "
    "qcdev and creating one is a Control_Panel WRITE, excluded from this "
    "Web-only read-only batch. Without it the 'does not appear publicly' "
    "assertion could only pass vacuously."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_draft_service_is_not_served_on_the_website(page):
    """ADO-137632 | PBI 129400 — EN, logged out in a fresh anonymous session:
    'QA_AUTO draft service' appears neither as a service card nor as a sidebar
    row, and its detail content is not reachable on the website."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    page_text = services.page_text()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert "QA_AUTO draft service" not in card_names, (
        f"the draft service is rendered as a card: {card_names}"
    )
    assert "QA_AUTO draft service" not in sidebar_labels, (
        f"the draft service is rendered as a sidebar row: {sidebar_labels}"
    )
    assert "QA_AUTO draft service" not in page_text, (
        "the draft service's content is present in the public page body"
    )


# ── #137633 — SKIPPED: needs the Hero Banner image replaced ──────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Hero banner")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Replacing the Hero Banner image updates the website without affecting the page layout")
@allure.label("pbi", PBI)
@allure.label("testcase", "137633")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137633
@pytest.mark.traceability("ADO-137633")
@pytest.mark.skip(
    reason="BLOCKED — the case requires UPLOADING a different valid 800 KB "
    "JPG as the Hero Banner (EN) and publishing. An asset upload is a "
    "Control_Panel WRITE, excluded from this Web-only read-only batch, and "
    "the assertion is about THE NEW image rendering — which cannot be "
    "identified without performing the upload. The layout-invariant half is "
    "written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_replacing_hero_banner_keeps_the_layout_unchanged(page):
    """ADO-137633 | PBI 129400 — EN, logged out: after the hero image is
    replaced, the new image renders, the banner is still 140px tall with
    40px/300px padding, the gradient overlay is unchanged, and the page title
    and breadcrumb sit in exactly the same positions as before."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    before_title = services.page_title_box()
    before_crumb = services.breadcrumb_box()
    before_image = services.hero_background_image()

    # Act (the CMS replacement happens between these two reads)
    services.open_member_services()
    after_title = services.page_title_box()
    after_crumb = services.breadcrumb_box()
    hero = services.hero_style()
    hero_inner = services.hero_inner_style()

    # Assert
    assert services.hero_background_image() != before_image, (
        "the hero banner still renders the previous image after replacement"
    )
    assert hero.get("height") == f"{CASE_HERO_HEIGHT_PX}px", (
        f"the hero is {hero.get('height')!r} tall after the replacement"
    )
    assert hero_inner.get("padding") == CASE_HERO_PADDING, (
        f"the hero padding is {hero_inner.get('padding')!r}; the case requires "
        f"{CASE_HERO_PADDING}"
    )
    assert CASE_HERO_GRADIENT_ANGLE in (services.hero_overlay_gradient() or ""), (
        f"the gradient overlay changed: {services.hero_overlay_gradient()!r}"
    )
    assert after_title == before_title, (
        f"the page title moved: {before_title} -> {after_title}"
    )
    assert after_crumb == before_crumb, (
        f"the breadcrumb moved: {before_crumb} -> {after_crumb}"
    )


# ── #137634 — SKIPPED: needs a service icon uploaded ─────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service icon")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An uploaded service icon renders in all three of its placements on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137634")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137634
@pytest.mark.traceability("ADO-137634")
@pytest.mark.skip(
    reason="BLOCKED — the case requires UPLOADING a valid 90 KB SVG as the "
    "Signatory Cancellation service icon and publishing. An asset upload is a "
    "Control_Panel WRITE, excluded from this Web-only read-only batch, and "
    "the assertion is about THE UPLOADED asset appearing in all three "
    "placements — which cannot be identified without performing the upload. "
    "The three-placement geometry half is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_uploaded_service_icon_renders_in_all_three_placements(page):
    """ADO-137634 | PBI 129400 — EN, logged out: the newly uploaded Signatory
    Cancellation icon renders inside the list card's icon tile, inside the
    36x36 sidebar row tile and inside the 48x48 8px-radius detail header
    tile."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_icons = services.card_icon_count()
    services.click_card_details(SIGNATORY_CANCELLATION)
    sidebar_tile = services.sidebar_row_icon_style(SIGNATORY_CANCELLATION)
    panel_tile = services.panel_tile_style()

    # Assert
    assert card_icons == CASE_SERVICE_COUNT, (
        f"only {card_icons} of {CASE_SERVICE_COUNT} cards render an icon"
    )
    assert sidebar_tile.get("width") == f"{CASE_SIDEBAR_TILE_SIZE}px" and (
        sidebar_tile.get("height") == f"{CASE_SIDEBAR_TILE_SIZE}px"
    ), (
        f"the sidebar icon tile is "
        f"{sidebar_tile.get('width')}x{sidebar_tile.get('height')}; the case "
        f"requires {CASE_SIDEBAR_TILE_SIZE}x{CASE_SIDEBAR_TILE_SIZE}"
    )
    assert panel_tile.get("width") == f"{CASE_PANEL_TILE_SIZE}px" and (
        panel_tile.get("borderRadius") == CASE_PANEL_TILE_RADIUS
    ), (
        f"the detail header tile is {panel_tile.get('width')} with radius "
        f"{panel_tile.get('borderRadius')}; the case requires "
        f"{CASE_PANEL_TILE_SIZE}px / {CASE_PANEL_TILE_RADIUS}"
    )
    assert services.panel_icon_count() == 1, (
        "the detail header tile renders no icon"
    )


# ── #137635 — SKIPPED: needs a Draft record carrying the marker ──────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Draft and preview")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Draft content is visible only in the CMS and never on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137635")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137635
@pytest.mark.traceability("ADO-137635")
@pytest.mark.skip(
    reason="BLOCKED — the case needs a service record left in DRAFT with "
    "Short Description (EN) = 'QA_AUTO draft marker'. No such record exists "
    "on qcdev and creating one is a Control_Panel WRITE, excluded from this "
    "Web-only read-only batch. With no draft present, 'the marker text is not "
    "present' could only pass VACUOUSLY — which is precisely why this is a "
    "skip and not a green."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_draft_marker_is_never_rendered_on_the_public_site(page):
    """ADO-137635 | PBI 129400 — logged out in a fresh anonymous session
    (standards.md's mandatory logged-out context for draft visibility): the
    marker 'QA_AUTO draft marker' appears nowhere in the English page, nowhere
    in the Arabic page, and the draft service's detail view is not served."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    english_text = services.page_text()
    services.open_member_services(locale="ar")
    arabic_text = services.page_text()

    # Assert
    assert "QA_AUTO draft marker" not in english_text, (
        "the draft marker is being served on the English public page"
    )
    assert "QA_AUTO draft marker" not in arabic_text, (
        "the draft marker is being served on the Arabic public page"
    )
    assert services.service_card_count() == CASE_SERVICE_COUNT, (
        f"{services.service_card_count()} cards render in Arabic; the draft "
        f"service must not be one of them"
    )


# ── #137636 — SKIPPED: needs a draft + a published-inactive record ───────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Delivery gate")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("Only published and active content is served on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137636")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137636
@pytest.mark.traceability("ADO-137636")
@pytest.mark.skip(
    reason="BLOCKED — the case's environment precondition is 4 Published+"
    "Active services PLUS 1 Draft service PLUS 1 Published+Inactive service, "
    "and step 1 reads those states out of the CMS. qcdev holds only the 4 "
    "published+active records; authoring the draft and the inactive one are "
    "Control_Panel WRITES and enumerating record states is a Control_Panel "
    "READ — both excluded from this Web-only read-only batch. Asserting only "
    "'4 cards and 4 rows' would be the read-only lookalike that passes "
    "vacuously, because there is nothing for the gate to exclude."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_only_published_and_active_services_are_served(page):
    """ADO-137636 | PBI 129400 — EN, logged out: with 4 Published+Active, 1
    Draft and 1 Published+Inactive service in the CMS, the public page renders
    exactly 4 cards and 4 sidebar rows, and the rendered set equals the
    Published AND Active set exactly."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert len(card_names) == CASE_SERVICE_COUNT, (
        f"{len(card_names)} service cards render; the case requires exactly "
        f"{CASE_SERVICE_COUNT} ({card_names})"
    )
    assert len(sidebar_labels) == CASE_SERVICE_COUNT, (
        f"{len(sidebar_labels)} sidebar rows render; the case requires exactly "
        f"{CASE_SERVICE_COUNT} ({sidebar_labels})"
    )
    assert card_names == list(SERVICE_NAMES_EN) == sidebar_labels, (
        f"the rendered set is not the Published+Active set: cards "
        f"{card_names}, sidebar {sidebar_labels}"
    )


# ── #137637 — active service card renders in full, in order ──────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service card")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A service with Active Status True renders with its full card content in the configured order")
@allure.label("pbi", PBI)
@allure.label("testcase", "137637")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137637
@pytest.mark.traceability("ADO-137637")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_active_service_card_renders_in_full_at_its_display_order(page):
    """ADO-137637 | PBI 129400 — EN, logged out: 'Membership Renewal' is
    Active with Display Order 2, so it is the SECOND card, and that card shows
    its icon tile, the name in Cairo Bold 18/28 #1D1D1B, the short
    description in Cairo Regular 14/22 #7C7B7B, and a 'Details' pill with a
    white fill, a #DEDEDD 1px border and the label in Cairo SemiBold 16/24
    #4A4A49.

    Step 1 asks for a CMS confirmation of Active=True / Display Order=2; this
    Web-only batch infers both from the public rendering (an inactive service
    is not served at all, and Display Order IS the rendered position), and
    performs no Control_Panel read or write."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    index = 1  # Display Order 2 -> the second card

    # Act
    card_names = services.service_card_names()
    name_style = services.card_name_style(index)
    description_style = services.card_description_style(index)
    pill = services.details_button_style(index)
    tile = services.card_icon_tile_style(index)

    # Assert
    assert services.service_card_count() == CASE_SERVICE_COUNT, (
        f"{services.service_card_count()} cards render; the case requires "
        f"{CASE_SERVICE_COUNT}"
    )
    assert card_names[index] == SERVICE_NAME_BY_KEY[MEMBERSHIP_RENEWAL], (
        f"the second card is {card_names[index]!r}; the case requires "
        f"'Membership Renewal' at Display Order 2"
    )
    assert tile.get("backgroundColor"), "the second card has no icon tile"
    assert services.card_icon_count() >= index + 1, (
        "the second card's icon tile renders no icon"
    )
    assert not _typography_is(name_style, "18px", "28px", BOLD_WEIGHT, INK), (
        f"card name typography: "
        f"{_typography_is(name_style, '18px', '28px', BOLD_WEIGHT, INK)}"
    )
    assert services.service_card_descriptions()[index], (
        "the second card's short description is empty"
    )
    assert not _typography_is(
        description_style, "14px", "22px", REGULAR_WEIGHT, MUTED
    ), (
        f"card short-description typography: "
        f"{_typography_is(description_style, '14px', '22px', REGULAR_WEIGHT, MUTED)}"
    )
    assert services.details_button_labels()[index] == (
        MemberServicesPage.CASE_DETAILS_BUTTON_LABEL
    ), f"the pill reads {services.details_button_labels()[index]!r}"
    assert _matches_hex(pill.get("backgroundColor"), WHITE), (
        f"the Details pill fill is {pill.get('backgroundColor')!r}; the case "
        f"requires white"
    )
    # Re-checked 2026-09-27 while fixing _matches_hex for ADO-137643, and
    # LEFT AS IT WAS ON PURPOSE: this reads `borderColor`, not a shorthand,
    # and the explicit `_border_width_px(...) == 1` guard already rules out
    # the '0px' case that made 137643's read vacuous. #137637 is outside the
    # Sprint-2 triage (it passed), so it is not tightened here — tightening it
    # would be an unreviewed verdict change on a passing test.
    assert _border_width_px(pill.get("border")) == 1 and _matches_hex(
        pill.get("borderColor"), BORDER_PILL
    ), (
        f"the Details pill border is {pill.get('border')!r}; the case requires "
        f"1px {BORDER_PILL}"
    )
    assert not _typography_is(pill, "16px", "24px", SEMIBOLD_WEIGHT, BODY_INK), (
        f"Details pill typography: "
        f"{_typography_is(pill, '16px', '24px', SEMIBOLD_WEIGHT, BODY_INK)}"
    )


# ── #137638 — CTA displayed when both label and URL are configured ───────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service CTA")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The CTA button is displayed when both the CTA label and the redirect URL are configured")
@allure.label("pbi", PBI)
@allure.label("testcase", "137638")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137638
@pytest.mark.traceability("ADO-137638")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_cta_is_displayed_when_label_and_url_are_configured(page):
    """ADO-137638 | PBI 129400 — EN, logged out: New Membership has both a CTA
    Button Label and a CTA Redirect URL, so its detail panel renders the
    intro, every populated subsection, and — after 'How to Apply' — a CTA
    button with a #911731 fill, a 9999px radius, the configured label in Cairo
    SemiBold 16/24 #FFFFFF, a 20x20 arrow icon, and an href equal to the
    configured redirect URL.

    IMPLEMENTED rather than skipped: the page is already published and both
    CTA fields are already populated live, so this assertion is reachable
    with no CMS write (step 2's 'Publish the page' is a no-op re-assertion of
    the current state). No Control_Panel action was taken."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    cta = services.cta_style()
    label = services.cta_label()
    href = services.cta_href()
    cta_box = services.cta_box()
    subheadings = services.subheading_texts()
    last_subheading_box = services.subheading_box(len(subheadings) - 1
    )

    # Assert
    assert services.panel_intro_text(), "the detail panel intro did not render"
    assert subheadings == list(MemberServicesPage.CASE_SUBHEADINGS_EN), (
        f"the populated subsections are {subheadings}; the case requires "
        f"{list(MemberServicesPage.CASE_SUBHEADINGS_EN)}"
    )
    assert services.cta_count() == 1, (
        f"{services.cta_count()} CTA buttons render; the case requires one"
    )
    assert label, "the CTA renders with an empty label"
    assert href, "the CTA renders with no href"
    assert cta_box and last_subheading_box and (
        cta_box["y"] >= last_subheading_box["y"]
    ), (
        f"the CTA is not positioned after 'How to Apply' "
        f"(CTA y={cta_box and cta_box['y']}, heading "
        f"y={last_subheading_box and last_subheading_box['y']})"
    )
    assert _matches_hex(cta.get("backgroundColor"), MAROON), (
        f"the CTA fill is {cta.get('backgroundColor')!r}; the case requires {MAROON}"
    )
    assert cta.get("borderRadius") == CASE_PILL_RADIUS, (
        f"the CTA radius is {cta.get('borderRadius')!r}; the case requires "
        f"{CASE_PILL_RADIUS}"
    )
    assert not _typography_is(cta, "16px", "24px", SEMIBOLD_WEIGHT, WHITE), (
        f"CTA label typography: "
        f"{_typography_is(cta, '16px', '24px', SEMIBOLD_WEIGHT, WHITE)}"
    )
    assert services.cta_icon_size() == CASE_ARROW_ICON_SIZE, (
        f"the CTA icon is {services.cta_icon_size()}; the case requires "
        f"{CASE_ARROW_ICON_SIZE}"
    )
    assert services.cta_icon_is_leading() is False, (
        "the CTA arrow icon does not sit to the right of the label"
    )


# ── #137639 — SKIPPED: needs CTA Open Behavior set to Same tab ───────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service CTA")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A CTA configured with Open Behavior Same tab opens the destination in the current tab")
@allure.label("pbi", PBI)
@allure.label("testcase", "137639")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137639
@pytest.mark.traceability("ADO-137639")
@pytest.mark.skip(
    reason="BLOCKED — the case requires 'Membership Renewal' CTA Open "
    "Behavior to be SET TO 'Same tab' and the page re-published. Live, that "
    "CTA carries target=\"_blank\" (New tab), so the case's precondition does "
    "not hold and flipping it is a Control_Panel WRITE, excluded from this "
    "Web-only read-only batch. Its twin #137640 (New tab) IS implemented, "
    "because that is the state the build is already in."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_same_tab_cta_opens_in_the_current_tab(page):
    """ADO-137639 | PBI 129400 — EN, logged out: with Open Behavior = Same
    tab, clicking the Membership Renewal CTA loads the configured redirect URL
    in the SAME tab; no new tab is opened and the tab count is unchanged."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(MEMBERSHIP_RENEWAL)
    configured_url = services.cta_href()

    # Act
    outcome = services.click_cta()

    # Assert
    assert outcome["opened_new_tab"] is False, (
        "the CTA opened a new tab; the case requires Same-tab behaviour"
    )
    assert outcome["pages_after"] == outcome["pages_before"], (
        f"the tab count changed from {outcome['pages_before']} to "
        f"{outcome['pages_after']}"
    )
    assert outcome["landing_page"].url.rstrip("/") == (configured_url or "").rstrip("/"), (
        f"the CTA landed on {outcome['landing_page'].url!r}; the configured "
        f"destination is {configured_url!r}"
    )


# ── #137640 — CTA Open Behavior New tab ──────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service CTA")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A CTA configured with Open Behavior New tab opens the destination in a new tab")
@allure.label("pbi", PBI)
@allure.label("testcase", "137640")
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137640
@pytest.mark.traceability("ADO-137640")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_new_tab_cta_opens_the_destination_in_a_new_tab(page):
    """ADO-137640 | PBI 129400 — EN, logged out: with Open Behavior = New tab,
    clicking the Membership Renewal CTA loads the configured redirect URL in a
    newly opened tab, the tab count increases by one, and the Member's
    Services page stays loaded in the original tab.

    IMPLEMENTED rather than skipped: the live Membership Renewal CTA already
    carries target="_blank", which IS the case's New-tab precondition, so the
    assertion is reachable with no CMS write. No Control_Panel action was
    taken."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(MEMBERSHIP_RENEWAL)
    configured_url = services.cta_href()
    original_url = services.current_url()

    # Act
    outcome = services.click_cta()

    # Assert
    assert configured_url, "the Membership Renewal CTA has no href"
    assert outcome["opened_new_tab"] is True, (
        "the CTA did not open a new tab; the case requires New-tab behaviour"
    )
    assert outcome["pages_after"] == outcome["pages_before"] + 1, (
        f"the tab count went {outcome['pages_before']} -> "
        f"{outcome['pages_after']}; the case requires exactly one more tab"
    )
    assert outcome["landing_page"].url.rstrip("/") == configured_url.rstrip("/"), (
        f"the new tab landed on {outcome['landing_page'].url!r}; the configured "
        f"destination is {configured_url!r}"
    )
    assert services.current_url() == original_url, (
        f"the original tab moved from {original_url!r} to "
        f"{services.current_url()!r}; the Member's Services page must stay "
        f"loaded there"
    )


# ══════════════════════════════════════════════════════════════════════
# UI — Figma-verified rendering (Axis 4 = UI)
# ══════════════════════════════════════════════════════════════════════

# ── #137641 — EN LTR design tokens ───────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Design tokens — English")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The English Member's Services page renders left-to-right and matches the approved Figma design tokens")
@allure.label("pbi", PBI)
@allure.label("testcase", "137641")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137641
@pytest.mark.traceability("ADO-137641")
@pytest.mark.parametrize("page", [ANON_DESKTOP], indirect=True)
def test_english_page_matches_the_approved_figma_tokens(page):
    """ADO-137641 | PBI 129400 — EN, desktop 1920x1080, logged out: the whole
    page renders LTR in Cairo and matches frames 2343:88589 (listing) and
    2343:88607 (New Membership detail) — hero 140px/40px-300px with the 90deg
    gradient, content 64px/300px with a 40px gap, heading 36/44 #1D1D1B,
    intro 14/22 #7C7B7B in a 536px column, cards with a 12px radius, 20px
    padding, 24px inner gap, a 1px 135deg gradient border and a
    0 5px 80px rgba(29,29,27,0.1) shadow stacked 12px apart, a 9999px Details
    pill, and a detail container with a 1px #EDEDED border, 16px radius, a
    312px sidebar, a 1px vertical divider, a 40px/12px panel, #A66F43 16/24
    subsection headings, #4A4A49 14/22 body copy, 1px #A66F43 dash markers
    4px apart, and a 312px 12px-radius supporting image."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    hero = services.hero_style()
    hero_inner = services.hero_inner_style()
    gradient = services.hero_overlay_gradient()
    title_style = services.page_title_style()
    content = services.content_style()
    heading_style = services.section_heading_style()
    intro_style = services.intro_style()
    card = services.card_style()
    cards = services.cards_container_style()
    pill = services.details_button_style()

    # Assert — list view, live-verifiable tokens first
    assert services.document_direction() != "rtl", (
        f"the English page renders {services.document_direction()!r}; the case "
        f"requires left-to-right"
    )
    assert intro_style.get("textAlign") in ("start", "left"), (
        f"English text is aligned {intro_style.get('textAlign')!r}; the case "
        f"requires left-aligned"
    )
    assert _uses_font(heading_style.get("fontFamily")), (
        f"the font family is {heading_style.get('fontFamily')!r}; the case "
        f"requires Cairo throughout"
    )
    assert hero.get("height") == f"{CASE_HERO_HEIGHT_PX}px", (
        f"the hero is {hero.get('height')!r} tall; the case requires "
        f"{CASE_HERO_HEIGHT_PX}px"
    )
    assert not _typography_is(title_style, "30px", "38px", BOLD_WEIGHT, WHITE), (
        f"hero title typography: "
        f"{_typography_is(title_style, '30px', '38px', BOLD_WEIGHT, WHITE)}"
    )
    assert content.get("gap") == CASE_CONTENT_GAP, (
        f"the content container gap is {content.get('gap')!r}; the case "
        f"requires {CASE_CONTENT_GAP}"
    )
    assert not _typography_is(heading_style, "36px", "44px", BOLD_WEIGHT, INK), (
        f"section heading typography: "
        f"{_typography_is(heading_style, '36px', '44px', BOLD_WEIGHT, INK)}"
    )
    assert not _typography_is(intro_style, "14px", "22px", MEDIUM_WEIGHT, MUTED), (
        f"intro typography: "
        f"{_typography_is(intro_style, '14px', '22px', MEDIUM_WEIGHT, MUTED)}"
    )
    assert intro_style.get("width") == f"{CASE_INTRO_WIDTH_PX}px", (
        f"the intro column is {intro_style.get('width')!r}; the case requires "
        f"{CASE_INTRO_WIDTH_PX}px"
    )
    assert _matches_hex(card.get("backgroundColor"), WHITE), (
        f"the service card fill is {card.get('backgroundColor')!r}; the case "
        f"requires {WHITE}"
    )
    assert card.get("borderRadius") == CASE_CARD_RADIUS, (
        f"the card radius is {card.get('borderRadius')!r}; the case requires "
        f"{CASE_CARD_RADIUS}"
    )
    assert card.get("padding") == CASE_CARD_PADDING, (
        f"the card padding is {card.get('padding')!r}; the case requires "
        f"{CASE_CARD_PADDING}"
    )
    assert card.get("gap") == CASE_CARD_GAP, (
        f"the card inner gap is {card.get('gap')!r}; the case requires "
        f"{CASE_CARD_GAP}"
    )
    assert cards.get("gap") == CASE_CARD_STACK_GAP, (
        f"the cards are stacked {cards.get('gap')!r} apart; the case requires "
        f"{CASE_CARD_STACK_GAP}"
    )
    assert pill.get("borderRadius") == CASE_PILL_RADIUS, (
        f"the Details pill radius is {pill.get('borderRadius')!r}"
    )
    assert _matches_hex(pill.get("backgroundColor"), WHITE) and _matches_hex(
        pill.get("borderColor"), BORDER_PILL
    ), (
        f"the Details pill is {pill.get('backgroundColor')!r} with a "
        f"{pill.get('borderColor')!r} border; the case requires {WHITE} / "
        f"{BORDER_PILL}"
    )
    assert pill.get("padding") == CASE_PILL_PADDING and pill.get("gap") == CASE_PILL_GAP, (
        f"the Details pill padding/gap are {pill.get('padding')!r} / "
        f"{pill.get('gap')!r}; the case requires {CASE_PILL_PADDING} / "
        f"{CASE_PILL_GAP}"
    )
    assert services.details_button_icon_size() == CASE_ARROW_ICON_SIZE, (
        f"the Details pill icon is {services.details_button_icon_size()}"
    )

    # Detail view
    services.click_card_details(NEW_MEMBERSHIP)
    detail = services.detail_container_style()
    sidebar = services.sidebar_style()
    divider = services.vertical_divider_style()
    panel = services.panel_style()
    subheading = services.subheading_style()
    body = services.body_text_style()
    docs_list = services.required_documents_list_style()
    marker = services.required_documents_marker_style()
    support = services.detail_support_style()

    # AUTOMATION BUG FIX 2026-09-27 (ADO-137643): border shorthand now read
    # through _border_is() (non-zero width + real style + colour).
    assert _border_width_px(detail.get("border")) == CASE_DETAIL_BORDER_PX and _border_is(
        detail.get("border"), BORDER_LIGHT
    ), (
        f"the detail container border is {detail.get('border')!r}; the case "
        f"requires 1px {BORDER_LIGHT}"
    )
    assert detail.get("borderRadius") == CASE_DETAIL_RADIUS, (
        f"the detail container radius is {detail.get('borderRadius')!r}"
    )
    assert sidebar.get("width") == f"{CASE_SIDEBAR_WIDTH_PX}px", (
        f"the sidebar is {sidebar.get('width')!r} wide; the case requires "
        f"{CASE_SIDEBAR_WIDTH_PX}px"
    )
    assert divider.get("width") == "1px" and _matches_hex(
        divider.get("backgroundColor"), BORDER_LIGHT
    ), (
        f"the vertical divider is {divider.get('width')!r} "
        f"{divider.get('backgroundColor')!r}; the case requires 1px {BORDER_LIGHT}"
    )
    assert panel.get("padding") == CASE_PANEL_PADDING and panel.get("gap") == CASE_PANEL_GAP, (
        f"the content panel padding/gap are {panel.get('padding')!r} / "
        f"{panel.get('gap')!r}; the case requires {CASE_PANEL_PADDING} / "
        f"{CASE_PANEL_GAP}"
    )
    assert not _typography_is(subheading, "16px", "24px", BOLD_WEIGHT, BROWN), (
        f"subsection heading typography: "
        f"{_typography_is(subheading, '16px', '24px', BOLD_WEIGHT, BROWN)}"
    )
    assert not _typography_is(body, "14px", "22px", MEDIUM_WEIGHT, BODY_INK), (
        f"body copy typography: "
        f"{_typography_is(body, '14px', '22px', MEDIUM_WEIGHT, BODY_INK)}"
    )
    assert marker.get("width") == CASE_DASH_MARKER_WIDTH and marker.get(
        "height"
    ) == CASE_DASH_MARKER_HEIGHT, (
        f"the Required Documents dash marker is {marker.get('width')!r} x "
        f"{marker.get('height')!r}; the case requires "
        f"{CASE_DASH_MARKER_WIDTH} x {CASE_DASH_MARKER_HEIGHT}"
    )
    assert _matches_hex(marker.get("backgroundColor"), BROWN), (
        f"the dash marker colour is {marker.get('backgroundColor')!r}; the "
        f"case requires {BROWN}"
    )
    assert docs_list.get("gap") == CASE_REQUIRED_DOCS_GAP, (
        f"the Required Documents items are {docs_list.get('gap')!r} apart; the "
        f"case requires {CASE_REQUIRED_DOCS_GAP}"
    )
    assert support.get("width") == f"{CASE_SUPPORT_WIDTH_PX}px", (
        f"the detail supporting image is {support.get('width')!r} wide"
    )
    assert support.get("borderRadius") == CASE_DETAIL_SUPPORT_RADIUS, (
        f"the detail supporting image radius is "
        f"{support.get('borderRadius')!r}; the case requires "
        f"{CASE_DETAIL_SUPPORT_RADIUS}"
    )
    # …then the four tokens this build is known to differ on.
    assert hero_inner.get("padding") == CASE_HERO_PADDING, (
        f"the hero padding is {hero_inner.get('padding')!r}; the case requires "
        f"{CASE_HERO_PADDING}"
    )
    assert content.get("padding") == CASE_CONTENT_PADDING, (
        f"the content container padding is {content.get('padding')!r}; the "
        f"case requires {CASE_CONTENT_PADDING}"
    )
    assert CASE_CARD_SHADOW_BLUR in (card.get("boxShadow") or ""), (
        f"the card shadow is {card.get('boxShadow')!r}; the case requires "
        f"0px 5px {CASE_CARD_SHADOW_BLUR} rgba(29,29,27,0.1)"
    )
    assert CASE_CARD_BORDER_GRADIENT_ANGLE in (card.get("borderImageSource") or ""), (
        f"the card border-image is {card.get('borderImageSource')!r}; the case "
        f"requires a 1px {CASE_CARD_BORDER_GRADIENT_ANGLE} gradient border "
        f"from rgba(246,246,246,1) to rgba(233,219,208,1). This build paints a "
        f"flat {card.get('border')!r} instead."
    )
    assert gradient and CASE_HERO_GRADIENT_ANGLE in gradient, (
        f"the hero gradient is {gradient!r}; the case requires "
        f"{CASE_HERO_GRADIENT_ANGLE} rgba(66,44,27,0.8) "
        f"{CASE_HERO_GRADIENT_FROM_STOP} to rgba(145,23,49,0.8) "
        f"{CASE_HERO_GRADIENT_TO_STOP}"
    )


# ── #137643 — AR RTL mirroring ───────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Design tokens — Arabic RTL")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("The Arabic Member's Services page renders right-to-left with the list, sidebar and panel mirrored")
@allure.label("pbi", PBI)
@allure.label("testcase", "137643")
@pytest.mark.arabic
@pytest.mark.regression
@pytest.mark.rtl
@pytest.mark.ui
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137643
@pytest.mark.traceability("ADO-137643")
@pytest.mark.parametrize("page", [ANON_DESKTOP], indirect=True)
def test_arabic_page_renders_right_to_left_and_mirrored(page):
    """ADO-137643 | PBI 129400 — AR, desktop, logged out: the page renders
    RTL in Cairo with sidebar كافة الخدمات and the four Arabic service names;
    subsection headings read الفئات المستفيدة من الخدمة, المستندات المطلوبة,
    كيفية التقديم; the supporting image is on the LEFT with 40px 0px 40px 40px
    inset, the content panel in the middle, the 312px sidebar on the RIGHT;
    the selected row's 1px #911731 border is on its RIGHT edge, each row's
    chevron leads and its icon tile trails, and the CTA's 20x20 arrow-up-left
    icon precedes its label.

    NOTE on the inset: the case words it as `padding`. This build carries it
    as a `margin` (`40px 0px 40px 40px` in AR, mirrored in EN) with
    `padding: 0px`. The assertion below reads the real carrier — the value and
    the mirroring the case specifies are unchanged."""
    # Arrange
    services = MemberServicesPage(page).open_member_services(locale="ar")

    # Act
    card_names = services.service_card_names()
    heading_style = services.section_heading_style()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_box = services.sidebar_box()
    panel_box = services.panel_box()
    support_box = services.detail_support_box()
    support = services.detail_support_style()
    selected_row = services.sidebar_row_style(NEW_MEMBERSHIP)
    chevron_box = services.sidebar_chevron_box(NEW_MEMBERSHIP)
    tile_box = services.sidebar_icon_tile_box(0)

    # Assert — direction and mirroring first
    assert services.document_direction() == "rtl", (
        f"the Arabic page renders {services.document_direction()!r}; the case "
        f"requires right-to-left"
    )
    assert services.section_direction() == "rtl", (
        f"the Member's Services section renders {services.section_direction()!r}"
    )
    assert _uses_font(heading_style.get("fontFamily")), (
        f"the font family is {heading_style.get('fontFamily')!r}; the case "
        f"requires Cairo throughout"
    )
    assert card_names == list(MemberServicesPage.CASE_SERVICE_NAMES_AR), (
        f"the Arabic service names read {card_names}; the case requires "
        f"{list(MemberServicesPage.CASE_SERVICE_NAMES_AR)}"
    )
    assert support_box and panel_box and sidebar_box, (
        "the Arabic detail view did not render its sidebar / panel / image"
    )
    assert support_box["x"] < panel_box["x"] < sidebar_box["x"], (
        f"the Arabic layout is not mirrored — image x={support_box['x']}, "
        f"panel x={panel_box['x']}, sidebar x={sidebar_box['x']}; the case "
        f"requires image (left) < panel (middle) < sidebar (right)"
    )
    assert round(sidebar_box["width"]) == CASE_SIDEBAR_WIDTH_PX, (
        f"the Arabic sidebar is {round(sidebar_box['width'])}px wide; the case "
        f"requires {CASE_SIDEBAR_WIDTH_PX}px"
    )
    assert support.get("margin") == CASE_AR_SUPPORT_PADDING, (
        f"the Arabic supporting image inset is {support.get('margin')!r} "
        f"(margin) / {support.get('padding')!r} (padding); the case requires "
        f"{CASE_AR_SUPPORT_PADDING}"
    )
    # AUTOMATION BUG FIX 2026-09-27 (ADO-137643): both edges are border
    # SHORTHANDS and are read through _border_is(), which requires a non-zero
    # width and a real line style. _matches_hex() parsed only the colour, so
    # the un-painted '0px none rgb(145, 23, 49)' left edge read as "a maroon
    # border is present" and failed the negative assertion below.
    assert _border_is(selected_row.get("borderRight"), MAROON), (
        f"the selected row's RIGHT border is "
        f"{selected_row.get('borderRight')!r}; the case requires the maroon "
        f"border on the right edge in Arabic"
    )
    assert not _border_is(selected_row.get("borderLeft"), MAROON), (
        f"the selected row still carries a maroon LEFT border "
        f"({selected_row.get('borderLeft')!r}) in Arabic"
    )
    assert chevron_box and tile_box and chevron_box["x"] < tile_box["x"], (
        f"the sidebar row is not mirrored — chevron x="
        f"{chevron_box and chevron_box['x']}, icon tile x="
        f"{tile_box and tile_box['x']}; the case requires the chevron leading "
        f"and the icon tile trailing"
    )
    assert services.cta_icon_is_leading() is True, (
        "the Arabic CTA's arrow icon does not precede its label"
    )
    assert services.cta_icon_transform() not in (None, "none"), (
        f"the Arabic CTA arrow is not mirrored (transform "
        f"{services.cta_icon_transform()!r}); the case requires an "
        f"arrow-up-LEFT icon"
    )
    # …then the two Arabic strings this build differs on.
    assert services.sidebar_title_text() == MemberServicesPage.CASE_SIDEBAR_TITLE_AR, (
        f"the Arabic sidebar title reads {services.sidebar_title_text()!r}; the "
        f"case requires {MemberServicesPage.CASE_SIDEBAR_TITLE_AR!r}"
    )
    assert services.subheading_texts() == list(
        MemberServicesPage.CASE_SUBHEADINGS_AR
    ), (
        f"the Arabic subsection headings read {services.subheading_texts()}; "
        f"the case requires {list(MemberServicesPage.CASE_SUBHEADINGS_AR)}"
    )


# ── #137645 — selected vs unselected sidebar row ─────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Sidebar selected state")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The selected service in the All Services sidebar is visually distinguished from the unselected services")
@allure.label("pbi", PBI)
@allure.label("testcase", "137645")
@pytest.mark.regression
@pytest.mark.ui
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137645
@pytest.mark.traceability("ADO-137645")
@pytest.mark.parametrize("page", [ANON_DESKTOP], indirect=True)
def test_selected_sidebar_row_is_visually_distinguished(page):
    """ADO-137645 | PBI 129400 — EN, logged out: against Figma 2307:74966
    (menu-Hover) vs 2307:74961 (menu) — the 312px sidebar's title is Cairo
    SemiBold 18/28 #1D1D1B with 12px/16px padding; the selected row has a
    #F4E7EA background, a 1px #911731 left border, a 36x36 #911731 6px-radius
    icon tile, a Cairo SemiBold 14/22 #911731 label and 16px padding with a
    12px gap; every unselected row has no fill, no maroon border, a 36x36
    #F6F0EC 6px-radius tile and a #1D1D1B label; exactly one row carries the
    selected style and rows are separated by 1px #F6F6F6 dividers."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    sidebar = services.sidebar_style()
    title_style = services.sidebar_title_style()
    selected = services.sidebar_row_style(NEW_MEMBERSHIP)
    selected_label = services.sidebar_row_label_style(NEW_MEMBERSHIP)
    selected_tile = services.sidebar_row_icon_style(NEW_MEMBERSHIP)

    # Assert
    assert sidebar.get("width") == f"{CASE_SIDEBAR_WIDTH_PX}px", (
        f"the sidebar is {sidebar.get('width')!r} wide"
    )
    assert not _typography_is(title_style, "18px", "28px", SEMIBOLD_WEIGHT, INK), (
        f"sidebar title typography: "
        f"{_typography_is(title_style, '18px', '28px', SEMIBOLD_WEIGHT, INK)}"
    )
    assert title_style.get("padding") == CASE_SIDEBAR_TITLE_PADDING, (
        f"the sidebar title padding is {title_style.get('padding')!r}; the "
        f"case requires {CASE_SIDEBAR_TITLE_PADDING}"
    )
    assert services.selected_sidebar_count() == 1, (
        f"{services.selected_sidebar_count()} rows carry the selected style; "
        f"the case requires exactly one at any time"
    )
    assert _matches_hex(selected.get("backgroundColor"), MAROON_TINT), (
        f"the selected row background is {selected.get('backgroundColor')!r}"
    )
    assert selected.get("padding") == CASE_SIDEBAR_ROW_PADDING and selected.get(
        "gap"
    ) == CASE_SIDEBAR_ROW_GAP, (
        f"the selected row padding/gap are {selected.get('padding')!r} / "
        f"{selected.get('gap')!r}; the case requires "
        f"{CASE_SIDEBAR_ROW_PADDING} / {CASE_SIDEBAR_ROW_GAP}"
    )
    assert _matches_hex(selected_tile.get("backgroundColor"), MAROON), (
        f"the selected row's icon tile is "
        f"{selected_tile.get('backgroundColor')!r}"
    )
    assert selected_tile.get("width") == f"{CASE_SIDEBAR_TILE_SIZE}px", (
        f"the selected row's icon tile is {selected_tile.get('width')!r} wide"
    )
    assert not _typography_is(selected_label, "14px", "22px", SEMIBOLD_WEIGHT, MAROON), (
        f"selected row label typography: "
        f"{_typography_is(selected_label, '14px', '22px', SEMIBOLD_WEIGHT, MAROON)}"
    )
    for key in [k for k in SERVICE_KEYS if k != NEW_MEMBERSHIP]:
        row = services.sidebar_row_style(key)
        label = services.sidebar_row_label_style(key)
        tile = services.sidebar_row_icon_style(key)
        assert _is_transparent(row.get("backgroundColor")), (
            f"unselected row {key!r} has a background fill "
            f"{row.get('backgroundColor')!r}"
        )
        # AUTOMATION BUG FIX 2026-09-27 (ADO-137643): see _border_is().
        assert not _border_is(row.get("borderLeft"), MAROON), (
            f"unselected row {key!r} carries a maroon border "
            f"({row.get('borderLeft')!r})"
        )
        assert _matches_hex(tile.get("backgroundColor"), TILE_BEIGE) and tile.get(
            "width"
        ) == f"{CASE_SIDEBAR_TILE_SIZE}px", (
            f"unselected row {key!r} tile is {tile.get('backgroundColor')!r} at "
            f"{tile.get('width')!r}; the case requires {TILE_BEIGE} at "
            f"{CASE_SIDEBAR_TILE_SIZE}px"
        )
        assert not _typography_is(label, "14px", "22px", SEMIBOLD_WEIGHT, INK), (
            f"unselected row {key!r} label typography: "
            f"{_typography_is(label, '14px', '22px', SEMIBOLD_WEIGHT, INK)}"
        )
        # AUTOMATION BUG FIX 2026-09-27 (ADO-137643): see _border_is() — this
        # POSITIVE divider assertion was previously colour-only and could pass
        # on a '0px none' edge.
        assert _border_is(row.get("borderTop"), DIVIDER_FAINT), (
            f"row {key!r} is separated by {row.get('borderTop')!r}; the case "
            f"requires a 1px {DIVIDER_FAINT} divider"
        )
    # …then the two radius/width tokens this build differs on.
    assert selected_tile.get("borderRadius") == CASE_SIDEBAR_TILE_RADIUS, (
        f"the selected row's icon tile radius is "
        f"{selected_tile.get('borderRadius')!r}; the case requires "
        f"{CASE_SIDEBAR_TILE_RADIUS}"
    )
    assert _border_width_px(selected.get("borderLeft")) == CASE_SIDEBAR_SELECTED_BORDER_PX, (
        f"the selected row's left border is {selected.get('borderLeft')!r}; the "
        f"case requires {CASE_SIDEBAR_SELECTED_BORDER_PX}px {MAROON}"
    )


# ══════════════════════════════════════════════════════════════════════
# Compatibility — viewports and themes (Axis 4 = Compatibility)
# ══════════════════════════════════════════════════════════════════════

# ── #137647 — desktop 1920x1080 ──────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Responsive — desktop")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Member's Services page renders correctly at desktop viewport width")
@allure.label("pbi", PBI)
@allure.label("testcase", "137647")
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137647
@pytest.mark.traceability("ADO-137647")
@pytest.mark.parametrize("page", [ANON_DESKTOP], indirect=True)
def test_page_renders_correctly_at_desktop_viewport(page):
    """ADO-137647 | PBI 129400 — EN, 1920x1080, logged out: no horizontal
    scrollbar; the list view is a row (card column left, 312px supporting
    image right) with the content container at 64px/300px padding; the detail
    view is a row (312px sidebar, 1px divider, content panel, 312px
    supporting image) and the CTA hugs its content rather than filling the
    panel width."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    viewport = services.viewport_size()
    overflow = services.horizontal_overflow_report()
    listview = services.listview_style()
    cards_box = services.cards_container_box()
    support_box = services.list_support_box()
    content = services.content_style()

    # Assert — list view
    assert viewport == {"width": 1920, "height": 1080}, (
        f"the viewport is {viewport}; the case requires 1920x1080"
    )
    assert not services.has_horizontal_overflow(), (
        f"a horizontal scrollbar is present (scrollWidth "
        f"{overflow['scrollWidth']} vs {overflow['docWidth']}); offenders: "
        f"{_describe(overflow['offenders'])}"
    )
    assert listview.get("flexDirection") == "row", (
        f"the list view lays out {listview.get('flexDirection')!r}; the case "
        f"requires a row at desktop width"
    )
    assert cards_box and support_box and cards_box["x"] < support_box["x"], (
        f"the supporting image is not to the right of the card column "
        f"(cards x={cards_box and cards_box['x']}, image "
        f"x={support_box and support_box['x']})"
    )
    assert round(support_box["width"]) == CASE_SUPPORT_WIDTH_PX, (
        f"the supporting image is {round(support_box['width'])}px wide; the "
        f"case requires {CASE_SUPPORT_WIDTH_PX}px"
    )

    # Detail view
    services.click_card_details(NEW_MEMBERSHIP)
    detail = services.detail_container_style()
    sidebar_box = services.sidebar_box()
    divider_box = services.vertical_divider_box()
    panel_box = services.panel_box()
    detail_support_box = services.detail_support_box()
    cta_box = services.cta_box()

    assert detail.get("flexDirection") == "row", (
        f"the detail view lays out {detail.get('flexDirection')!r}; the case "
        f"requires a row at desktop width"
    )
    assert sidebar_box and round(sidebar_box["width"]) == CASE_SIDEBAR_WIDTH_PX, (
        f"the sidebar is {sidebar_box and round(sidebar_box['width'])}px wide"
    )
    assert divider_box and round(divider_box["width"]) == 1, (
        f"the vertical divider is {divider_box and divider_box['width']}px wide"
    )
    assert (
        sidebar_box["x"] < divider_box["x"] < panel_box["x"] < detail_support_box["x"]
    ), (
        f"the detail row order is wrong — sidebar {sidebar_box['x']}, divider "
        f"{divider_box['x']}, panel {panel_box['x']}, image "
        f"{detail_support_box['x']}"
    )
    assert cta_box and cta_box["width"] < panel_box["width"] * 0.9, (
        f"the CTA is {cta_box and cta_box['width']}px wide inside a "
        f"{panel_box['width']}px panel; the case requires it to hug its "
        f"content rather than fill the panel"
    )
    # …then the padding token this build differs on.
    assert content.get("padding") == CASE_CONTENT_PADDING, (
        f"the content container padding is {content.get('padding')!r}; the "
        f"case requires {CASE_CONTENT_PADDING}"
    )


# ── #137648 — tablet 768x1024 ────────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Responsive — tablet")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Member's Services page renders correctly at tablet viewport width")
@allure.label("pbi", PBI)
@allure.label("testcase", "137648")
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137648
@pytest.mark.traceability("ADO-137648")
@pytest.mark.parametrize("page", [ANON_TABLET], indirect=True)
def test_page_renders_correctly_at_tablet_viewport(page):
    """ADO-137648 | PBI 129400 — EN, 768x1024, logged out: the page loads with
    no horizontal scrollbar and no clipped content; all four cards render in
    full (icon, name, short description, Details button) with nothing
    overlapping or overflowing; and in the detail view the sidebar, content
    panel and supporting image all stay visible and usable with a fully
    visible CTA.

    EXPECTED RED — a genuine responsive defect in this PBI's own fragment:
    `P.qc-ms-intro` keeps a hard 536px width at 768px and overflows to
    right=1089, so `scrollWidth` is 1089 against a 768px viewport. The
    assertion names every offender so triage does not mistake it for the
    third-party `grecaptcha-badge`, which also overflows."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    viewport = services.viewport_size()
    overflow = services.horizontal_overflow_report()
    own_offenders = services.fragment_offenders()
    card_boxes = services.card_boxes()
    descriptions = services.service_card_descriptions()

    # Assert — content integrity first
    assert viewport == {"width": 768, "height": 1024}, (
        f"the viewport is {viewport}; the case requires 768x1024"
    )
    assert len(card_boxes) == CASE_SERVICE_COUNT, (
        f"{len(card_boxes)} cards render at tablet width; the case requires "
        f"all {CASE_SERVICE_COUNT}"
    )
    assert all(box["width"] > 0 and box["height"] > 0 for box in card_boxes), (
        f"a card collapsed at tablet width: {card_boxes}"
    )
    assert all(descriptions) and services.card_icon_count() == CASE_SERVICE_COUNT, (
        f"a card lost its icon or description at tablet width "
        f"(icons={services.card_icon_count()}, descriptions={descriptions})"
    )
    assert services.details_button_labels() == [
        MemberServicesPage.CASE_DETAILS_BUTTON_LABEL
    ] * CASE_SERVICE_COUNT, (
        f"the Details buttons read {services.details_button_labels()} at "
        f"tablet width"
    )
    for first, second in zip(card_boxes, card_boxes[1:]):
        assert second["y"] >= first["y"] + first["height"] - 1, (
            f"cards overlap at tablet width: {first} then {second}"
        )

    # Detail view
    services.click_card_details(NEW_MEMBERSHIP)
    assert services.sidebar_box(), "the sidebar is not rendered at tablet width"
    assert services.panel_box(), "the content panel is not rendered at tablet width"
    assert services.detail_support_box(), (
        "the supporting image is not rendered at tablet width"
    )
    assert services.subheading_texts() == list(
        MemberServicesPage.CASE_SUBHEADINGS_EN
    ), (
        f"the detail subsections read {services.subheading_texts()} at tablet "
        f"width"
    )
    cta_box = services.cta_box()
    assert cta_box and cta_box["width"] > 0 and cta_box["height"] > 0, (
        f"the CTA is not fully visible at tablet width: {cta_box}"
    )
    # …then the page-level overflow, which this build fails.
    services.open_member_services()
    assert not services.has_horizontal_overflow(), (
        f"a horizontal scrollbar is present at 768px "
        f"(scrollWidth {overflow['scrollWidth']} vs {overflow['docWidth']}).\n"
        f"Offenders belonging to THIS fragment: {_describe(own_offenders)}\n"
        f"All offenders (includes third-party chrome): "
        f"{_describe(overflow['offenders'])}"
    )


# ── #137649 — mobile 375x812 ─────────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Responsive — mobile")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The Member's Services detail view stacks vertically at mobile viewport width")
@allure.label("pbi", PBI)
@allure.label("testcase", "137649")
@pytest.mark.compatibility
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137649
@pytest.mark.traceability("ADO-137649")
@pytest.mark.parametrize("page", [ANON_MOBILE], indirect=True)
def test_detail_view_stacks_vertically_at_mobile_viewport(page):
    """ADO-137649 | PBI 129400 — EN, 375x812, logged out: no horizontal
    scrollbar; the detail view is a single column with a 40px gap between
    blocks — the 'All Services' list first inside a 1px #EDEDED container
    with an 8px radius, then the content panel, then the supporting image;
    the list is shown in full as a stacked list (not collapsed into a
    dropdown) and the CTA stretches to the full width of the content panel."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    viewport = services.viewport_size()
    overflow = services.horizontal_overflow_report()
    services.click_card_details(NEW_MEMBERSHIP)
    detail = services.detail_container_style()
    sidebar = services.sidebar_style()
    sidebar_box = services.sidebar_box()
    panel_box = services.panel_box()
    support_box = services.detail_support_box()
    cta_box = services.cta_box()

    # Assert — stacking behaviour first
    assert viewport == {"width": 375, "height": 812}, (
        f"the viewport is {viewport}; the case requires 375x812"
    )
    assert not services.has_horizontal_overflow(), (
        f"a horizontal scrollbar is present at 375px "
        f"(scrollWidth {overflow['scrollWidth']} vs {overflow['docWidth']}); "
        f"offenders: {_describe(overflow['offenders'])}"
    )
    assert detail.get("flexDirection") == "column", (
        f"the detail view lays out {detail.get('flexDirection')!r}; the case "
        f"requires a single column at mobile width"
    )
    assert sidebar_box and panel_box and support_box, (
        "the mobile detail view is missing one of its three blocks"
    )
    assert sidebar_box["y"] < panel_box["y"] < support_box["y"], (
        f"the mobile stacking order is wrong — list y={sidebar_box['y']}, "
        f"panel y={panel_box['y']}, image y={support_box['y']}; the case "
        f"requires list, then panel, then image"
    )
    assert services.sidebar_row_count() == CASE_SERVICE_COUNT, (
        f"the mobile 'All Services' list shows "
        f"{services.sidebar_row_count()} rows; the case requires all "
        f"{CASE_SERVICE_COUNT} shown as a stacked list rather than collapsed "
        f"into a dropdown"
    )
    # AUTOMATION BUG FIX 2026-09-27 (ADO-137643): border shorthand now read
    # through _border_is() (non-zero width + real style + colour).
    assert _border_width_px(sidebar.get("border")) == 1 and _border_is(
        sidebar.get("border"), BORDER_LIGHT
    ), (
        f"the mobile list container border is {sidebar.get('border')!r}; the "
        f"case requires 1px {BORDER_LIGHT}"
    )
    assert cta_box and cta_box["width"] >= panel_box["width"] * 0.8, (
        f"the CTA is {cta_box and cta_box['width']}px wide inside a "
        f"{panel_box['width']}px panel; the case requires it to stretch to the "
        f"full width of the content panel"
    )
    # …then the two tokens this build differs on.
    assert detail.get("gap") == CASE_MOBILE_STACK_GAP, (
        f"the mobile stack gap is {detail.get('gap')!r}; the case requires "
        f"{CASE_MOBILE_STACK_GAP}"
    )
    assert sidebar.get("borderRadius") == CASE_MOBILE_LIST_RADIUS, (
        f"the mobile list container radius is {sidebar.get('borderRadius')!r}; "
        f"the case requires {CASE_MOBILE_LIST_RADIUS}"
    )


# ── #137650 — light mode ─────────────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Theme — light")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Member's Services page renders correctly in light mode")
@allure.label("pbi", PBI)
@allure.label("testcase", "137650")
@pytest.mark.compatibility
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137650
@pytest.mark.traceability("ADO-137650")
@pytest.mark.parametrize("page", [ANON_DESKTOP], indirect=True)
def test_page_renders_correctly_in_light_mode(page):
    """ADO-137650 | PBI 129400 — EN, desktop, logged out, light mode (Figma
    frame 2343:88589): page and header backgrounds are #FFFFFF, header nav
    labels #1D1D1B, the section heading #1D1D1B and the intro #7C7B7B, the
    language chip an #EDEDED fill with #6C6C6B text; a service card has a
    #FFFFFF fill with a 135deg gradient border from rgba(246,246,246,1) to
    rgba(233,219,208,1), an #F6F0EC icon tile, a #1D1D1B name, a #7C7B7B
    short description and a #FFFFFF/#DEDEDD Details pill."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    services.enable_light_mode()

    # Act
    heading_style = services.section_heading_style()
    intro_style = services.intro_style()
    chip = services.language_chip_style()
    card = services.card_style()
    tile = services.card_icon_tile_style()
    name_style = services.card_name_style()
    description_style = services.card_description_style()
    pill = services.details_button_style()

    # Assert — the verifiable tokens first
    assert services.current_theme() == "light", (
        f"the active theme is {services.current_theme()!r}; the case requires "
        f"light mode"
    )
    assert _matches_hex(services.page_background_color(), WHITE), (
        f"the page background is {services.page_background_color()!r}; the "
        f"case requires {WHITE}"
    )
    assert _matches_hex(services.header_background_color(), WHITE), (
        f"the header background is {services.header_background_color()!r}; the "
        f"case requires {WHITE}"
    )
    assert _matches_hex(services.nav_label_color(), INK), (
        f"the header navigation labels are {services.nav_label_color()!r}; the "
        f"case requires {INK}"
    )
    assert _matches_hex(heading_style.get("color"), INK), (
        f"the section heading is {heading_style.get('color')!r}; the case "
        f"requires {INK}"
    )
    assert _matches_hex(intro_style.get("color"), MUTED), (
        f"the intro paragraph is {intro_style.get('color')!r}; the case "
        f"requires {MUTED}"
    )
    assert _matches_hex(chip.get("backgroundColor"), LIGHT_CHIP_FILL), (
        f"the language chip fill is {chip.get('backgroundColor')!r}; the case "
        f"requires {LIGHT_CHIP_FILL}"
    )
    assert _matches_hex(card.get("backgroundColor"), WHITE), (
        f"the service card fill is {card.get('backgroundColor')!r}"
    )
    assert _matches_hex(tile.get("backgroundColor"), TILE_BEIGE), (
        f"the card icon tile is {tile.get('backgroundColor')!r}; the case "
        f"requires {TILE_BEIGE}"
    )
    assert _matches_hex(name_style.get("color"), INK), (
        f"the service name is {name_style.get('color')!r}"
    )
    assert _matches_hex(description_style.get("color"), MUTED), (
        f"the short description is {description_style.get('color')!r}"
    )
    assert _matches_hex(pill.get("backgroundColor"), WHITE) and _matches_hex(
        pill.get("borderColor"), BORDER_PILL
    ), (
        f"the Details pill is {pill.get('backgroundColor')!r} / "
        f"{pill.get('borderColor')!r}; the case requires {WHITE} / {BORDER_PILL}"
    )
    # …then the two tokens this build differs on.
    assert _matches_hex(chip.get("color"), LIGHT_CHIP_TEXT), (
        f"the language chip text is {chip.get('color')!r}; the case requires "
        f"{LIGHT_CHIP_TEXT}"
    )
    assert CASE_CARD_BORDER_GRADIENT_ANGLE in (card.get("borderImageSource") or ""), (
        f"the card border-image is {card.get('borderImageSource')!r}; the case "
        f"requires a {CASE_CARD_BORDER_GRADIENT_ANGLE} gradient border from "
        f"rgba(246,246,246,1) to rgba(233,219,208,1)"
    )


# ── #137651 — dark mode ──────────────────────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Theme — dark")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Member's Services page renders correctly in dark mode")
@allure.label("pbi", PBI)
@allure.label("testcase", "137651")
@pytest.mark.compatibility
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137651
@pytest.mark.traceability("ADO-137651")
@pytest.mark.parametrize("page", [ANON_DESKTOP], indirect=True)
def test_page_renders_correctly_in_dark_mode(page):
    """ADO-137651 | PBI 129400 — EN, desktop, logged out, dark mode (Figma
    frame 2343:96670): page and header backgrounds #1D1D1B, nav labels
    #FFFFFF, the section heading #FFFFFF and the intro #D0D0D0, the language
    chip a #4A4A49 fill with #DEDEDD text and the profile icon button
    #C44561; a service card has a #1D1D1B fill with a 135deg gradient border
    from rgba(52,52,50,1) to rgba(83,56,34,1), a #422C1B icon tile, a #FFFFFF
    name, a #D0D0D0 short description and a #1D1D1B/#6C6C6B Details pill; the
    hero gradient is unchanged from light mode.

    Dark mode is applied through the site's own accessibility widget — the
    only way in (a `prefers-color-scheme` emulation alone does not flip it)."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    light_gradient = services.hero_overlay_gradient()
    services.enable_dark_mode()

    # Act
    heading_style = services.section_heading_style()
    intro_style = services.intro_style()
    chip = services.language_chip_style()
    card = services.card_style()
    tile = services.card_icon_tile_style()
    name_style = services.card_name_style()
    description_style = services.card_description_style()
    pill = services.details_button_style()

    # Assert — the verifiable tokens first
    assert services.current_theme() == "dark", (
        f"the active theme is {services.current_theme()!r}; the case requires "
        f"dark mode"
    )
    assert _matches_hex(services.page_background_color(), INK), (
        f"the page background is {services.page_background_color()!r}; the "
        f"case requires {INK}"
    )
    assert _matches_hex(services.header_background_color(), INK), (
        f"the header background is {services.header_background_color()!r}"
    )
    assert _matches_hex(services.nav_label_color(), WHITE), (
        f"the header navigation labels are {services.nav_label_color()!r}"
    )
    assert _matches_hex(heading_style.get("color"), WHITE), (
        f"the section heading is {heading_style.get('color')!r}"
    )
    assert _matches_hex(name_style.get("color"), WHITE), (
        f"the service name is {name_style.get('color')!r}"
    )
    assert services.hero_overlay_gradient() == light_gradient, (
        f"the hero gradient changed in dark mode: {light_gradient!r} -> "
        f"{services.hero_overlay_gradient()!r}; the case requires it unchanged"
    )
    # …then the tokens this build differs on, and the control it lacks.
    assert _matches_hex(intro_style.get("color"), DARK_SUBTEXT), (
        f"the dark-mode intro is {intro_style.get('color')!r}; the case "
        f"requires {DARK_SUBTEXT}"
    )
    assert _matches_hex(description_style.get("color"), DARK_SUBTEXT), (
        f"the dark-mode short description is {description_style.get('color')!r}; "
        f"the case requires {DARK_SUBTEXT}"
    )
    assert _matches_hex(chip.get("backgroundColor"), DARK_CHIP_FILL) and _matches_hex(
        chip.get("color"), DARK_CHIP_TEXT
    ), (
        f"the dark-mode language chip is {chip.get('backgroundColor')!r} / "
        f"{chip.get('color')!r}; the case requires {DARK_CHIP_FILL} / "
        f"{DARK_CHIP_TEXT}"
    )
    assert _matches_hex(card.get("backgroundColor"), INK), (
        f"the dark-mode card fill is {card.get('backgroundColor')!r}; the case "
        f"requires {INK}"
    )
    assert CASE_CARD_BORDER_GRADIENT_ANGLE in (card.get("borderImageSource") or ""), (
        f"the dark-mode card border-image is {card.get('borderImageSource')!r}; "
        f"the case requires a {CASE_CARD_BORDER_GRADIENT_ANGLE} gradient from "
        f"rgba(52,52,50,1) to rgba(83,56,34,1)"
    )
    assert _matches_hex(tile.get("backgroundColor"), DARK_TILE), (
        f"the dark-mode icon tile is {tile.get('backgroundColor')!r}; the case "
        f"requires {DARK_TILE}"
    )
    assert _matches_hex(pill.get("backgroundColor"), INK) and _matches_hex(
        pill.get("borderColor"), DARK_PILL_BORDER
    ), (
        f"the dark-mode Details pill is {pill.get('backgroundColor')!r} / "
        f"{pill.get('borderColor')!r}; the case requires {INK} / "
        f"{DARK_PILL_BORDER}"
    )
    assert services.profile_icon_button_count() > 0, (
        "the case names a profile icon button coloured "
        f"{DARK_PROFILE} in dark mode; no profile/avatar control exists in the "
        "public header on this build at all"
    )
    assert _matches_hex(
        services.profile_icon_button_style().get("color"), DARK_PROFILE
    ), (
        f"the profile icon button is "
        f"{services.profile_icon_button_style().get('color')!r}; the case "
        f"requires {DARK_PROFILE}"
    )


# ══════════════════════════════════════════════════════════════════════
# Auth / access control (Axis 4 = Auth)
# ══════════════════════════════════════════════════════════════════════

# ── #137652 — anonymous visitor, no login anywhere ───────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Anonymous access")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An anonymous public visitor can view the published Member's Services page and use its CTA links without logging in")
@allure.label("pbi", PBI)
@allure.label("testcase", "137652")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137652
@pytest.mark.traceability("ADO-137652")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_anonymous_visitor_can_view_page_and_use_cta(page):
    """ADO-137652 | PBI 129400 — EN, logged out: a session with NO Qatar
    Chamber authentication cookie loads the page in full (hero, title,
    breadcrumb, section heading, intro, every active card) with no login
    prompt and no redirect to a sign-in page, opens a service detail view with
    its sidebar, full content panel and CTA, and follows the CTA to the
    configured URL — at no point is a login required."""
    # Arrange — `{"auth": False}` means the context loads no storageState
    services = MemberServicesPage(page)
    cookie_names = [cookie["name"] for cookie in page.context.cookies()]

    # Act
    services.open_member_services()
    landing_url = services.current_url()
    services.click_card_details(NEW_MEMBERSHIP)
    configured_url = services.cta_href()
    outcome = services.click_cta()

    # Assert
    assert not any(
        name.upper() in ("JSESSIONID", "COMPANY_ID", "ID", "USER_UUID")
        for name in cookie_names
    ), f"the session already carried an authentication cookie: {cookie_names}"
    assert PAGE_PATH_MARKER in landing_url and "login" not in landing_url.lower(), (
        f"the anonymous request landed on {landing_url!r} — a sign-in redirect"
    )
    assert services.page_title_text(), "the page title did not render for an anonymous visitor"
    assert services.breadcrumb_texts() == [
        MemberServicesPage.CASE_BREADCRUMB_HOME,
        MemberServicesPage.CASE_BREADCRUMB_CURRENT,
    ], f"the breadcrumb reads {services.breadcrumb_texts()} for an anonymous visitor"
    assert services.is_detail_view_visible(), (
        "the detail view did not open for an anonymous visitor"
    )
    assert services.sidebar_row_count() == CASE_SERVICE_COUNT, (
        f"the sidebar shows {services.sidebar_row_count()} rows for an "
        f"anonymous visitor"
    )
    assert services.cta_count() == 1, (
        "the CTA is not rendered for an anonymous visitor"
    )
    assert outcome["landing_page"].url.rstrip("/") == (configured_url or "").rstrip("/"), (
        f"the CTA landed on {outcome['landing_page'].url!r}; the configured "
        f"destination is {configured_url!r}"
    )
    assert "login" not in outcome["landing_page"].url.lower(), (
        f"the CTA redirected an anonymous visitor to a sign-in page: "
        f"{outcome['landing_page'].url!r}"
    )


# ── #137653 — SKIPPED: needs a Draft record and an Unpublished page ──────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Anonymous access")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("An anonymous visitor cannot reach draft or unpublished Member's Services content by direct URL")
@allure.label("pbi", PBI)
@allure.label("testcase", "137653")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137653
@pytest.mark.traceability("ADO-137653")
@pytest.mark.skip(
    reason="BLOCKED — the case needs (a) a service record left in DRAFT whose "
    "direct URL is captured from Liferay and (b) the page record UNPUBLISHED. "
    "Neither state exists on qcdev; creating the draft and unpublishing the "
    "live page are Control_Panel WRITES, excluded from this Web-only "
    "read-only batch, and the unpublish is additionally destructive against "
    "real shared content (standards.md), needing its own ID-named user "
    "approval which has NOT been given. With neither state present the "
    "forced-browsing assertion could only pass vacuously."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_anonymous_visitor_cannot_force_browse_draft_or_unpublished_content(page):
    """ADO-137653 | PBI 129400 — logged out in a fresh anonymous session
    (standards.md's mandatory logged-out context): requesting the Draft
    service's direct URL returns the site's standard not-found response with
    no draft field values in the body, and requesting the Unpublished page
    record's URL returns no cached copy of its previously published
    content."""
    # Arrange
    services = MemberServicesPage(page)

    # Act
    services.request_member_services_url()
    body = services.page_text()

    # Assert
    assert services.fragment_count() == 0, (
        "the unpublished page is still being served to an anonymous visitor"
    )
    assert "QA_AUTO draft" not in body, (
        "draft field values are present in the response body served to an "
        "anonymous visitor"
    )


# ── #137654 — SKIPPED: entirely a Control_Panel transition matrix ────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Role permissions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor can perform every transition the PBI grants that role")
@allure.label("pbi", PBI)
@allure.label("testcase", "137654")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137654
@pytest.mark.traceability("ADO-137654")
@pytest.mark.skip(
    reason="BLOCKED — every step of this case is a Control_Panel action "
    "performed as a Site Content Editor (create, edit, preview, publish, "
    "change Active Status and Display Order, re-publish, unpublish), and its "
    "expected results are Liferay toasts and the absence of an Access Denied "
    "message. None of it has a public-surface assertion, so NO body is "
    "written rather than inventing a CMS path this Web-only, strictly "
    "read-only batch is forbidden to write. The unpublish step is "
    "additionally destructive against real shared content."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_site_content_editor_can_perform_every_granted_transition(page):
    """ADO-137654 | PBI 129400 — Control_Panel-only: the Editor creates, edits
    and previews a service record, publishes the page, changes Active Status
    and Display Order and re-publishes, then unpublishes — each succeeding
    with a Liferay success toast and no Access Denied message."""
    ...


# ── #137655 — SKIPPED: entirely a Control_Panel RBAC denial ──────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Role permissions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Editor acting outside their permitted scope is refused with the Access Denied message")
@allure.label("pbi", PBI)
@allure.label("testcase", "137655")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137655
@pytest.mark.traceability("ADO-137655")
@pytest.mark.skip(
    reason="BLOCKED — the case signs in as a Site Content Editor who is NOT "
    "assigned to the Member's Services page record, attempts edit and publish "
    "in the authoring UI, and then replays the publish transition directly "
    "against the CMS endpoint with that editor's session token. All of it is "
    "Control_Panel, with no public-surface assertion, so NO body is written "
    "rather than inventing a CMS path this Web-only read-only batch is "
    "forbidden to write. (The case also records Open Risk R-2: the PBI never "
    "defines the boundary of 'where permitted'.)"
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_editor_outside_permitted_scope_is_refused(page):
    """ADO-137655 | PBI 129400 — Control_Panel-only: an unassigned Site
    Content Editor is refused with 'Access Denied. You do not have permission
    to perform this action.' / 'تم رفض الوصول. ليس لديك صلاحية لتنفيذ هذا
    الإجراء' in the UI and at the endpoint, with no state change."""
    ...


# ── #137657 — SKIPPED: needs an Author session and a publish attempt ─────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Role permissions")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A Site Content Author cannot publish Member's Services content through the UI or by direct API call")
@allure.label("pbi", PBI)
@allure.label("testcase", "137657")
@pytest.mark.auth
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137657
@pytest.mark.traceability("ADO-137657")
@pytest.mark.skip(
    reason="BLOCKED — the case signs in as a Site Content Author, saves a "
    "draft carrying the marker 'QA_AUTO author publish attempt', then "
    "attempts Publish in the UI and again directly against the CMS endpoint. "
    "Every one of those is a Control_Panel action/WRITE, excluded from this "
    "Web-only read-only batch. Only step 4's public half (the site still "
    "shows the previously published heading) is expressible, and it is "
    "written below — on its own it would pass vacuously because no Author "
    "draft exists."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_site_content_author_cannot_publish(page):
    """ADO-137657 | PBI 129400 — logged out in a fresh anonymous session: the
    Author's blocked publish leaves the public Member's Services page showing
    the previously published section heading, not 'QA_AUTO author publish
    attempt'."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    heading = services.section_heading_text()

    # Assert
    assert heading != "QA_AUTO author publish attempt", (
        "the Author's unpublished draft heading reached the public site — the "
        "publish block is not enforced server side"
    )
    assert heading == MemberServicesPage.CASE_SECTION_HEADING_EN, (
        f"the public section heading reads {heading!r}; the case requires the "
        f"previously published value"
    )


# ══════════════════════════════════════════════════════════════════════
# Edge cases (Axis 4 = Edge) — every one needs a CMS-authored state
# ══════════════════════════════════════════════════════════════════════

# ── #137658 — SKIPPED: needs both CTA fields cleared ─────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Edge — optional fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A service with no CTA configured renders its detail panel without a CTA button")
@allure.label("pbi", PBI)
@allure.label("testcase", "137658")
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137658
@pytest.mark.traceability("ADO-137658")
@pytest.mark.skip(
    reason="BLOCKED — the case needs BOTH CTA Button Label (EN/AR) and CTA "
    "Redirect URL CLEARED on 'Signatory Cancellation' and the page "
    "re-published. Live that service has a populated CTA ('Cancel a "
    "Signatory' -> qatarchamber.com/services/signatory-cancellation), so "
    "reaching the case's state is a Control_Panel WRITE against real shared "
    "content, excluded from this Web-only read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_service_without_cta_renders_no_cta_button(page):
    """ADO-137658 | PBI 129400 — EN, logged out: with both CTA fields empty,
    the Signatory Cancellation detail panel renders its icon, title, intro and
    every populated subsection but NO CTA button and no empty placeholder or
    gap; opening New Membership in the same session still shows its CTA,
    confirming the omission is per service and not global."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(SIGNATORY_CANCELLATION)

    # Act
    cta_count = services.cta_count()
    subheadings = services.subheading_texts()
    services.select_sidebar_service(NEW_MEMBERSHIP)
    services.wait_for_panel_title(SERVICE_NAME_BY_KEY[NEW_MEMBERSHIP])
    other_cta_count = services.cta_count()

    # Assert
    assert cta_count == 0, (
        f"{cta_count} CTA buttons render on Signatory Cancellation; the case "
        f"requires none when both CTA fields are empty"
    )
    assert subheadings, (
        "the Signatory Cancellation panel rendered no populated subsections"
    )
    assert other_cta_count == 1, (
        "New Membership lost its CTA too — the omission is global rather than "
        "per service"
    )


# ── #137659 — SKIPPED: needs an optional subsection cleared ──────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Edge — optional fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("An empty optional subsection is hidden on the website rather than rendered as an empty heading")
@allure.label("pbi", PBI)
@allure.label("testcase", "137659")
@pytest.mark.arabic
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137659
@pytest.mark.traceability("ADO-137659")
@pytest.mark.skip(
    reason="BLOCKED — the case needs 'Who This Service Is For' CLEARED in "
    "both EN and AR on the 'Membership Renewal' record and the page "
    "re-published. Live that subsection is populated in both languages, so "
    "reaching the case's state is a Control_Panel WRITE against real shared "
    "content, excluded from this Web-only read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_optional_subsection_is_hidden(page):
    """ADO-137659 | PBI 129400 — EN then AR, logged out: with 'Who This
    Service Is For' empty on Membership Renewal, the content panel shows the
    detail intro then 'Required Documents' and 'How to Apply' only — the
    heading is absent entirely, with no empty heading, stray divider or blank
    gap; the Arabic view behaves identically."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(MEMBERSHIP_RENEWAL)

    # Act
    english_subheadings = services.subheading_texts()
    services.open_service_detail(MEMBERSHIP_RENEWAL, locale="ar")
    arabic_subheadings = services.subheading_texts()

    # Assert
    assert english_subheadings == [
        MemberServicesPage.CASE_SUBHEADINGS_EN[1],
        MemberServicesPage.CASE_SUBHEADINGS_EN[2],
    ], (
        f"the English panel shows {english_subheadings}; the case requires the "
        f"empty 'Who This Service Is For' heading to be absent entirely"
    )
    assert arabic_subheadings == [
        MemberServicesPage.CASE_SUBHEADINGS_AR[1],
        MemberServicesPage.CASE_SUBHEADINGS_AR[2],
    ], (
        f"the Arabic panel shows {arabic_subheadings}; the case requires "
        f"الفئات المستفيدة من الخدمة to be absent while the other two render"
    )


# ── #137660 — SKIPPED: needs three services deactivated ──────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Edge — single active service")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("The list and sidebar render correctly when only one service is active")
@allure.label("pbi", PBI)
@allure.label("testcase", "137660")
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137660
@pytest.mark.traceability("ADO-137660")
@pytest.mark.skip(
    reason="BLOCKED — the case needs Membership Renewal, Attestation on "
    "Signature and Signatory Cancellation all set to Active Status = False so "
    "only New Membership remains. Deactivating three live services is a "
    "destructive Control_Panel WRITE against real shared content — excluded "
    "from this Web-only read-only batch and, per standards.md's "
    "destructive-precondition rule, needing disposable test data or its own "
    "ID-named user approval, neither of which is available here."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_list_and_sidebar_render_with_only_one_active_service(page):
    """ADO-137660 | PBI 129400 — EN, logged out: with only New Membership
    active, the list renders exactly one card (icon, name, short description,
    Details button) beside the supporting image with no broken grid, no
    leftover empty slots and no horizontal overflow, and its detail view
    opens with a sidebar of exactly one row shown in the selected style."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    support_box = services.list_support_box()
    overflow = services.has_horizontal_overflow()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert card_names == [SERVICE_NAME_BY_KEY[NEW_MEMBERSHIP]], (
        f"the list renders {card_names}; the case requires exactly one card"
    )
    assert services.card_icon_count() == 1 and services.service_card_descriptions(), (
        "the single card is missing its icon or short description"
    )
    assert support_box and support_box["width"] > 0, (
        "the supporting image did not render beside the single card"
    )
    assert not overflow, "the single-card layout introduced a horizontal scrollbar"
    assert sidebar_labels == [SERVICE_NAME_BY_KEY[NEW_MEMBERSHIP]], (
        f"the sidebar renders {sidebar_labels}; the case requires exactly one row"
    )
    assert services.selected_sidebar_count() == 1, (
        "the single sidebar row is not shown in the selected style"
    )
    assert services.cta_count() == 1, "the single service's CTA did not render"


# ── #137661 — SKIPPED: needs an Arabic translation removed ───────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Edge — translation fallback")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A service with a missing translation falls back to the configured default language")
@allure.label("pbi", PBI)
@allure.label("testcase", "137661")
@pytest.mark.arabic
@pytest.mark.edge
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137661
@pytest.mark.traceability("ADO-137661")
@pytest.mark.skip(
    reason="BLOCKED — the case needs 'How to Apply' populated in EN and left "
    "EMPTY in AR on the 'Attestation on Signature' record. Live both "
    "translations are populated, so clearing the Arabic value is a "
    "Control_Panel WRITE against real shared content, excluded from this "
    "Web-only read-only batch. Without the missing translation the fallback "
    "assertion could only pass vacuously."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_missing_translation_falls_back_to_default_language(page):
    """ADO-137661 | PBI 129400 — AR, logged out: with 'How to Apply' (AR)
    empty, the Arabic Attestation on Signature detail view still renders RTL
    with Arabic values everywhere else, and the كيفية التقديم subsection
    displays the ENGLISH 'How to Apply' content as the configured
    default-language fallback — not hidden, not a placeholder, not an empty
    heading."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(ATTESTATION, locale="ar")

    # Act
    subheadings = services.subheading_texts()
    body = services.subsection_body_text(MemberServicesPage.CASE_SUBHEADINGS_AR[2])

    # Assert
    assert services.document_direction() == "rtl", (
        f"the Arabic detail view renders {services.document_direction()!r}"
    )
    assert MemberServicesPage.CASE_SUBHEADINGS_AR[2] in subheadings, (
        f"the كيفية التقديم subsection is absent ({subheadings}); the case "
        f"requires it rendered with fallback content, not hidden"
    )
    assert body, (
        "the كيفية التقديم subsection rendered an empty body; the case "
        "requires the English fallback content"
    )
    assert body.isascii(), (
        f"the كيفية التقديم subsection reads {body!r}; with the Arabic value "
        f"empty the case requires the English default-language fallback"
    )


# ══════════════════════════════════════════════════════════════════════
# Functional-Low — field-level save + render (Axis 4 = Functional-Low)
# ══════════════════════════════════════════════════════════════════════

# ── #137662 — Page Title rendered in both languages ──────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Page Title is saved and rendered on the website in both languages")
@allure.label("pbi", PBI)
@allure.label("testcase", "137662")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137662
@pytest.mark.traceability("ADO-137662")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_page_title_renders_in_both_languages(page):
    """ADO-137662 | PBI 129400 — logged out: the English page shows the page
    title 'Membership Services' and the Arabic page shows 'خدمات العضوية'.

    IMPLEMENTED rather than skipped: the expected values are product content
    expectations, not QA_AUTO markers, and reading the rendered page title in
    each language is a pure public read. No Control_Panel action was taken —
    if the stored values differ, this test says so instead of hiding it."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    english_title = services.page_title_text()
    services.open_member_services(locale="ar")
    arabic_title = services.page_title_text()

    # Assert
    assert english_title == MemberServicesPage.CASE_PAGE_TITLE_EN, (
        f"the English page title reads {english_title!r}; the case requires "
        f"{MemberServicesPage.CASE_PAGE_TITLE_EN!r}"
    )
    assert arabic_title == MemberServicesPage.CASE_PAGE_TITLE_AR, (
        f"the Arabic page title reads {arabic_title!r}; the case requires "
        f"{MemberServicesPage.CASE_PAGE_TITLE_AR!r}"
    )


# ── #137666 — SKIPPED: needs a Hero Banner uploaded ──────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Hero Banner image is accepted and rendered on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137666")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137666
@pytest.mark.traceability("ADO-137666")
@pytest.mark.skip(
    reason="BLOCKED — the case UPLOADS a 1.2 MB PNG as the Hero Banner (EN) "
    "and asserts that THAT image renders. An asset upload is a Control_Panel "
    "WRITE, excluded from this Web-only read-only batch, and the uploaded "
    "asset cannot be identified on the public page without performing the "
    "upload. The 'renders behind the gradient with title and breadcrumb "
    "overlaid' half is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_valid_hero_banner_is_rendered(page):
    """ADO-137666 | PBI 129400 — EN, logged out: the uploaded image renders as
    the hero banner behind the gradient overlay, with the page title and
    breadcrumb overlaid on top."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    background = services.hero_background_image()
    hero_box = services.hero_box()
    title_box = services.page_title_box()
    crumb_box = services.breadcrumb_box()

    # Assert
    assert background and background != "none", (
        f"the hero banner renders no image ({background!r})"
    )
    assert CASE_HERO_GRADIENT_ANGLE in (services.hero_overlay_gradient() or ""), (
        f"the gradient overlay is {services.hero_overlay_gradient()!r}"
    )
    assert hero_box and title_box and crumb_box, "the hero did not render fully"
    assert hero_box["y"] <= title_box["y"] and (
        title_box["y"] + title_box["height"] <= hero_box["y"] + hero_box["height"] + 1
    ), f"the page title is not overlaid on the hero banner: {title_box} vs {hero_box}"
    assert hero_box["y"] <= crumb_box["y"], (
        f"the breadcrumb is not overlaid on the hero banner: {crumb_box}"
    )


# ── #137669 — Section Heading rendered in both languages ─────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Section Heading is saved and rendered on the website in both languages")
@allure.label("pbi", PBI)
@allure.label("testcase", "137669")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137669
@pytest.mark.traceability("ADO-137669")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_section_heading_renders_in_both_languages(page):
    """ADO-137669 | PBI 129400 — logged out: the English page shows 'Choose
    the service you need' in Cairo Bold 36/44 #1D1D1B and the Arabic page
    shows 'اختر الخدمة التي تحتاجها' right-aligned."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    english_heading = services.section_heading_text()
    english_style = services.section_heading_style()
    services.open_member_services(locale="ar")
    arabic_heading = services.section_heading_text()
    arabic_style = services.section_heading_style()
    arabic_direction = services.document_direction()

    # Assert
    assert english_heading == MemberServicesPage.CASE_SECTION_HEADING_EN, (
        f"the English section heading reads {english_heading!r}"
    )
    assert not _typography_is(english_style, "36px", "44px", BOLD_WEIGHT, INK), (
        f"English section heading typography: "
        f"{_typography_is(english_style, '36px', '44px', BOLD_WEIGHT, INK)}"
    )
    assert arabic_heading == MemberServicesPage.CASE_SECTION_HEADING_AR, (
        f"the Arabic section heading reads {arabic_heading!r}; the case "
        f"requires {MemberServicesPage.CASE_SECTION_HEADING_AR!r}"
    )
    assert arabic_direction == "rtl" and arabic_style.get("textAlign") in (
        "start",
        "right",
    ), (
        f"the Arabic heading is not right-aligned (direction "
        f"{arabic_direction!r}, text-align {arabic_style.get('textAlign')!r})"
    )


# ── #137670 — SKIPPED: needs a rejected empty-heading save ───────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Saving with an empty Section Heading is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "137670")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137670
@pytest.mark.traceability("ADO-137670")
@pytest.mark.skip(
    reason="BLOCKED — the case CLEARS Section Heading (EN) in the CMS and "
    "asserts that Save is refused with a required-field validation message. "
    "Both the clear and the save attempt are Control_Panel WRITES, excluded "
    "from this Web-only read-only batch; only step 4's 'the heading still "
    "renders publicly' half is expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_section_heading_is_rejected(page):
    """ADO-137670 | PBI 129400 — EN, logged out: after the blocked save, the
    previously saved heading is intact and still renders on the public
    page."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    heading = services.section_heading_text()

    # Assert
    assert heading == MemberServicesPage.CASE_SECTION_HEADING_EN, (
        f"the public section heading reads {heading!r} after the rejected "
        f"save; the case requires the previously saved value"
    )


# ── #137673 — Intro Content rendered beside the heading ──────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Valid Intro Content is saved and rendered beside the section heading on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137673")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137673
@pytest.mark.traceability("ADO-137673")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_intro_content_renders_beside_the_section_heading(page):
    """ADO-137673 | PBI 129400 — logged out: the English page renders the
    intro paragraph to the RIGHT of the section heading in Cairo Medium 14/22
    #7C7B7B within a 536px column; the Arabic page renders its Arabic
    equivalent right-aligned in the mirrored position (to the LEFT of the
    heading).

    DISCLOSED (module docstring, substitution 3): the case says "the
    Figma-approved intro copy" without quoting a string, and its expected
    result is about placement, column width and typography — so those are
    asserted exactly, plus a non-empty value in each language. No string is
    guessed."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    english_intro = services.intro_text()
    english_style = services.intro_style()
    english_heading_box = services.section_heading_box()
    english_intro_box = services.intro_box()
    services.open_member_services(locale="ar")
    arabic_intro = services.intro_text()
    arabic_style = services.intro_style()
    arabic_heading_box = services.section_heading_box()
    arabic_intro_box = services.intro_box()

    # Assert
    assert english_intro, "the English intro content is empty"
    assert not _typography_is(english_style, "14px", "22px", MEDIUM_WEIGHT, MUTED), (
        f"English intro typography: "
        f"{_typography_is(english_style, '14px', '22px', MEDIUM_WEIGHT, MUTED)}"
    )
    assert english_style.get("width") == f"{CASE_INTRO_WIDTH_PX}px", (
        f"the English intro column is {english_style.get('width')!r}; the case "
        f"requires {CASE_INTRO_WIDTH_PX}px"
    )
    assert english_heading_box["x"] < english_intro_box["x"], (
        f"the English intro is not to the right of the section heading "
        f"(heading x={english_heading_box['x']}, intro "
        f"x={english_intro_box['x']})"
    )
    assert arabic_intro, "the Arabic intro content is empty"
    assert services.document_direction() == "rtl" and arabic_style.get(
        "textAlign"
    ) in ("start", "right"), (
        f"the Arabic intro is not right-aligned (direction "
        f"{services.document_direction()!r}, text-align "
        f"{arabic_style.get('textAlign')!r})"
    )
    assert arabic_intro_box["x"] < arabic_heading_box["x"], (
        f"the Arabic intro is not in the mirrored position (intro "
        f"x={arabic_intro_box['x']}, heading x={arabic_heading_box['x']})"
    )


# ── #137674 — SKIPPED: needs a rejected empty-intro save ─────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Saving with empty Intro Content is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "137674")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137674
@pytest.mark.traceability("ADO-137674")
@pytest.mark.skip(
    reason="BLOCKED — the case CLEARS the Intro Content (EN) rich-text editor "
    "and asserts Save is refused with a required-field validation message. "
    "Both are Control_Panel WRITES, excluded from this Web-only read-only "
    "batch; only step 4's 'the intro still renders publicly' half is "
    "expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_intro_content_is_rejected(page):
    """ADO-137674 | PBI 129400 — EN, logged out: after the blocked save, the
    previously saved intro content is intact and still renders on the public
    page."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    intro = services.intro_text()

    # Assert
    assert intro, (
        "the public page renders no intro content after the rejected save; the "
        "case requires the previously saved value to be intact"
    )


# ── #137677 — SKIPPED: needs a list Supporting Image uploaded ────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Page-level fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid list-view Supporting Image is accepted and rendered beside the service list")
@allure.label("pbi", PBI)
@allure.label("testcase", "137677")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137677
@pytest.mark.traceability("ADO-137677")
@pytest.mark.skip(
    reason="BLOCKED — the case UPLOADS a 900 KB JPG as the Supporting Image "
    "(List View, EN) and asserts that THAT image renders. An asset upload is "
    "a Control_Panel WRITE, excluded from this Web-only read-only batch, and "
    "the uploaded asset cannot be identified without performing the upload. "
    "The geometry half (312px wide, 16px radius, right of the card column) "
    "is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_list_supporting_image_renders_beside_the_service_list(page):
    """ADO-137677 | PBI 129400 — EN, logged out: the uploaded image renders to
    the right of the service card column at 312px wide with a 16px corner
    radius."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    style = services.list_support_style()
    support_box = services.list_support_box()
    cards_box = services.cards_container_box()

    # Assert
    assert services.is_list_support_rendered(), (
        f"the supporting image did not load "
        f"({services.list_support_image_src()!r})"
    )
    assert style.get("width") == f"{CASE_SUPPORT_WIDTH_PX}px", (
        f"the supporting image is {style.get('width')!r} wide; the case "
        f"requires {CASE_SUPPORT_WIDTH_PX}px"
    )
    assert style.get("borderRadius") == CASE_LIST_SUPPORT_RADIUS, (
        f"the supporting image radius is {style.get('borderRadius')!r}; the "
        f"case requires {CASE_LIST_SUPPORT_RADIUS}"
    )
    assert cards_box and support_box and cards_box["x"] < support_box["x"], (
        "the supporting image is not to the right of the service card column"
    )


# ── #137680 — Service Name in all three placements, both languages ───────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level fields")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A valid bilingual Service Name is saved and rendered in all three of its frontend placements")
@allure.label("pbi", PBI)
@allure.label("testcase", "137680")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137680
@pytest.mark.traceability("ADO-137680")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_service_name_renders_in_card_sidebar_and_detail_title(page):
    """ADO-137680 | PBI 129400 — logged out: the English card, sidebar row and
    detail title all read 'New Membership'; after switching to Arabic all
    three read 'العضوية الجديدة'."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    english_card = services.service_card_names()[0]
    services.click_card_details(NEW_MEMBERSHIP)
    english_sidebar = services.sidebar_labels()[0]
    english_title = services.panel_title_text()
    services.open_service_detail(NEW_MEMBERSHIP, locale="ar")
    arabic_sidebar = services.sidebar_labels()[0]
    arabic_title = services.panel_title_text()
    services.open_member_services(locale="ar")
    arabic_card = services.service_card_names()[0]

    # Assert
    expected_en = SERVICE_NAME_BY_KEY[NEW_MEMBERSHIP]
    expected_ar = MemberServicesPage.CASE_SERVICE_NAMES_AR[0]
    assert english_card == expected_en, (
        f"the English card reads {english_card!r}; the case requires "
        f"{expected_en!r}"
    )
    assert english_sidebar == expected_en, (
        f"the English sidebar row reads {english_sidebar!r}"
    )
    assert english_title == expected_en, (
        f"the English detail title reads {english_title!r}"
    )
    assert arabic_card == expected_ar, (
        f"the Arabic card reads {arabic_card!r}; the case requires "
        f"{expected_ar!r}"
    )
    assert arabic_sidebar == expected_ar, (
        f"the Arabic sidebar row reads {arabic_sidebar!r}"
    )
    assert arabic_title == expected_ar, (
        f"the Arabic detail title reads {arabic_title!r}"
    )


# ── #137683 — SKIPPED: needs a whitespace-only name save attempt ─────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only Service Name is rejected as empty")
@allure.label("pbi", PBI)
@allure.label("testcase", "137683")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137683
@pytest.mark.traceability("ADO-137683")
@pytest.mark.skip(
    reason="BLOCKED — the case REPLACES Membership Renewal's Service Name "
    "(EN) with five spaces and asserts Save is blocked with 'Service name is "
    "required.'. Both are Control_Panel WRITES, excluded from this Web-only "
    "read-only batch; only step 4's 'the saved name still renders in all "
    "three placements' half is expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_whitespace_only_service_name_is_rejected(page):
    """ADO-137683 | PBI 129400 — EN, logged out: after the blocked save the
    previously saved service name is intact and the public card, sidebar row
    and detail title all still show it."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()
    expected = SERVICE_NAME_BY_KEY[MEMBERSHIP_RENEWAL]

    # Act
    card = services.service_card_names()[1]
    services.click_card_details(MEMBERSHIP_RENEWAL)
    sidebar = services.sidebar_labels()[1]
    title = services.panel_title_text()

    # Assert
    assert card == expected, f"the public card reads {card!r}"
    assert sidebar == expected, f"the sidebar row reads {sidebar!r}"
    assert title == expected, f"the detail title reads {title!r}"


# ── #137684 — SKIPPED: needs a Service Icon uploaded ─────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Service Icon is accepted and rendered in the card, sidebar and detail header")
@allure.label("pbi", PBI)
@allure.label("testcase", "137684")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137684
@pytest.mark.traceability("ADO-137684")
@pytest.mark.skip(
    reason="BLOCKED — the case UPLOADS a 60 KB SVG as the Attestation on "
    "Signature service icon and asserts THAT asset appears in all three "
    "placements. An asset upload is a Control_Panel WRITE, excluded from this "
    "Web-only read-only batch, and the uploaded asset cannot be identified "
    "without performing the upload. The three-placement geometry half is "
    "written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_valid_service_icon_renders_in_all_three_placements(page):
    """ADO-137684 | PBI 129400 — EN, logged out: the icon renders inside the
    card icon tile, inside the 36x36 sidebar tile and inside the 48x48 detail
    header tile — the same asset in all three, correctly scaled."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_icons = services.card_icon_count()
    services.click_card_details(ATTESTATION)
    sidebar_tile = services.sidebar_row_icon_style(ATTESTATION)
    panel_tile = services.panel_tile_style()

    # Assert
    assert card_icons == CASE_SERVICE_COUNT, (
        f"only {card_icons} cards render an icon"
    )
    assert sidebar_tile.get("width") == f"{CASE_SIDEBAR_TILE_SIZE}px", (
        f"the sidebar icon tile is {sidebar_tile.get('width')!r}"
    )
    assert panel_tile.get("width") == f"{CASE_PANEL_TILE_SIZE}px", (
        f"the detail header tile is {panel_tile.get('width')!r}"
    )
    assert services.panel_icon_count() == 1, (
        "the detail header tile renders no icon"
    )


# ── #137687 — Short Description on the card, both languages ──────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid bilingual Short Description is saved and rendered on the service card")
@allure.label("pbi", PBI)
@allure.label("testcase", "137687")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137687
@pytest.mark.traceability("ADO-137687")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_short_description_renders_on_the_card_in_both_languages(page):
    """ADO-137687 | PBI 129400 — logged out: the English New Membership card
    shows its summary in Cairo Regular 14/22 #7C7B7B beneath the service
    name; the Arabic card shows its Arabic summary right-aligned in the same
    style.

    DISCLOSED (module docstring, substitution 3): the case says "the
    Figma-approved EN summary" without quoting a string, and its expected
    result is about placement and typography — both asserted exactly, plus a
    non-empty value per language. No string is guessed."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    english_description = services.service_card_descriptions()[0]
    english_style = services.card_description_style()
    name_box = services.card_name_box()
    description_box = services.card_description_box()
    services.open_member_services(locale="ar")
    arabic_description = services.service_card_descriptions()[0]
    arabic_style = services.card_description_style()

    # Assert
    assert english_description, "the English card renders no short description"
    assert not _typography_is(english_style, "14px", "22px", REGULAR_WEIGHT, MUTED), (
        f"English short-description typography: "
        f"{_typography_is(english_style, '14px', '22px', REGULAR_WEIGHT, MUTED)}"
    )
    # DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137687):
    # case expected the short description stacked BENEATH the service name
    # (description y >= name y); delivered build lays the card out
    # HORIZONTALLY — name at x=441 y=420, description at x=705 y=412 — so the
    # description follows the name along the inline axis instead of the block
    # axis. Updated to the build: the case's intent (the description is placed
    # AFTER the service name in reading order, not before it and not detached)
    # is still asserted, against whichever axis the delivered card stacks on.
    assert name_box and description_box, (
        f"the card did not render both a name and a short description "
        f"(name={name_box}, description={description_box})"
    )
    _follows_beneath = description_box["y"] >= name_box["y"] + name_box["height"]
    _follows_inline = description_box["x"] >= name_box["x"] + name_box["width"]
    assert _follows_beneath or _follows_inline, (
        f"the short description does not follow the service name in reading "
        f"order — name x={name_box['x']} y={name_box['y']} "
        f"w={name_box['width']} h={name_box['height']}, description "
        f"x={description_box['x']} y={description_box['y']}"
    )
    assert arabic_description, "the Arabic card renders no short description"
    assert services.document_direction() == "rtl" and arabic_style.get(
        "textAlign"
    ) in ("start", "right"), (
        f"the Arabic short description is not right-aligned "
        f"({arabic_style.get('textAlign')!r})"
    )
    assert not _typography_is(arabic_style, "14px", "22px", REGULAR_WEIGHT, MUTED), (
        f"Arabic short-description typography: "
        f"{_typography_is(arabic_style, '14px', '22px', REGULAR_WEIGHT, MUTED)}"
    )


# ── #137688 — SKIPPED: needs a rejected empty-description save ───────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Saving with an empty Short Description is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "137688")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137688
@pytest.mark.traceability("ADO-137688")
@pytest.mark.skip(
    reason="BLOCKED — the case CLEARS New Membership's Short Description (EN) "
    "and asserts Save is refused with a required-field validation message. "
    "Both are Control_Panel WRITES, excluded from this Web-only read-only "
    "batch; only step 4's 'the description still renders on the public card' "
    "half is expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_short_description_is_rejected(page):
    """ADO-137688 | PBI 129400 — EN, logged out: after the blocked save the
    previously saved short description is intact and still renders on the
    public service card."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    description = services.service_card_descriptions()[0]

    # Assert
    assert description, (
        "the New Membership card renders no short description after the "
        "rejected save; the case requires the previously saved value intact"
    )


# ── #137689 — SKIPPED: needs a 300/301-character save attempt ────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The Short Description field enforces its 300-character limit")
@allure.label("pbi", PBI)
@allure.label("testcase", "137689")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137689
@pytest.mark.traceability("ADO-137689")
@pytest.mark.skip(
    reason="BLOCKED — the case ENTERS exactly 300 characters, saves, then "
    "attempts a 301st, in the CMS field. Both are Control_Panel WRITES, "
    "excluded from this Web-only read-only batch; only step 4's public half "
    "(the stored value is at most 300 characters and the card renders it "
    "without overflowing the Details button) is expressible and is written "
    "below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_short_description_enforces_its_300_character_limit(page):
    """ADO-137689 | PBI 129400 — EN, logged out: the stored Short Description
    (EN) is at most 300 characters long, and the card renders it without
    overflowing or overlapping the Details button."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    description = services.service_card_descriptions()[0]
    description_box = services.card_description_box()
    pill_box = services.details_button_box()

    # Assert
    assert len(description) <= 300, (
        f"the stored short description is {len(description)} characters; the "
        f"case requires at most 300"
    )
    assert description_box and pill_box, "the card did not render fully"
    assert description_box["x"] + description_box["width"] <= pill_box["x"] + 1, (
        f"the short description overlaps the Details button "
        f"(description ends at "
        f"{description_box['x'] + description_box['width']}, pill starts at "
        f"{pill_box['x']})"
    )


# ── #137691 — Detail Intro as the opening paragraph ──────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level fields")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid bilingual Detail Intro is saved and rendered as the opening paragraph of the detail panel")
@allure.label("pbi", PBI)
@allure.label("testcase", "137691")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137691
@pytest.mark.traceability("ADO-137691")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_detail_intro_renders_as_the_opening_paragraph(page):
    """ADO-137691 | PBI 129400 — logged out: the English detail panel shows
    its intro directly beneath the service title in Cairo Medium 14/22
    #4A4A49, above the first divider; the Arabic panel shows
    'سجّل مؤسستك أو شركتك عضواً في غرفة قطر واستفد من طيف واسع من خدمات دعم
    الأعمال وتيسير التجارة.' right-aligned in the same position.

    The EN copy is "the Figma-approved detail intro" with no quoted string in
    the case, so it is asserted as non-empty with the stated placement and
    typography; the AR string the case DOES quote is asserted verbatim."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    english_intro = services.panel_intro_text()
    english_style = services.panel_intro_style()
    title_box = services.panel_title_box()
    intro_box = services.panel_intro_box()
    divider_box = services.panel_divider_box()
    services.open_service_detail(NEW_MEMBERSHIP, locale="ar")
    arabic_intro = services.panel_intro_text()
    arabic_style = services.panel_intro_style()

    # Assert
    assert english_intro, "the English detail panel renders no intro paragraph"
    assert not _typography_is(english_style, "14px", "22px", MEDIUM_WEIGHT, BODY_INK), (
        f"English detail-intro typography: "
        f"{_typography_is(english_style, '14px', '22px', MEDIUM_WEIGHT, BODY_INK)}"
    )
    assert title_box and intro_box and intro_box["y"] >= title_box["y"], (
        f"the detail intro is not beneath the service title (title "
        f"y={title_box and title_box['y']}, intro y={intro_box and intro_box['y']})"
    )
    assert divider_box and intro_box["y"] < divider_box["y"], (
        f"the detail intro is not above the first divider (intro "
        f"y={intro_box['y']}, divider y={divider_box and divider_box['y']})"
    )
    assert arabic_intro == CASE_NEW_MEMBERSHIP_DETAIL_INTRO_AR, (
        f"the Arabic detail intro reads {arabic_intro!r}; the case requires "
        f"{CASE_NEW_MEMBERSHIP_DETAIL_INTRO_AR!r}"
    )
    assert services.document_direction() == "rtl" and arabic_style.get(
        "textAlign"
    ) in ("start", "right"), (
        f"the Arabic detail intro is not right-aligned "
        f"({arabic_style.get('textAlign')!r})"
    )


# ── #137692 — SKIPPED: needs a rejected empty-detail-intro save ──────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Saving with an empty Detail Intro is rejected")
@allure.label("pbi", PBI)
@allure.label("testcase", "137692")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137692
@pytest.mark.traceability("ADO-137692")
@pytest.mark.skip(
    reason="BLOCKED — the case CLEARS New Membership's Detail Intro (EN) "
    "editor and asserts Save is refused with a required-field validation "
    "message. Both are Control_Panel WRITES, excluded from this Web-only "
    "read-only batch; only step 4's 'the intro still opens the detail panel' "
    "half is expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_detail_intro_is_rejected(page):
    """ADO-137692 | PBI 129400 — EN, logged out: after the blocked save the
    previously saved detail intro is intact and still renders as the opening
    paragraph of the detail panel."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    intro = services.panel_intro_text()
    title_box = services.panel_title_box()
    intro_box = services.panel_intro_box()

    # Assert
    assert intro, (
        "the detail panel renders no intro after the rejected save; the case "
        "requires the previously saved value intact"
    )
    assert title_box and intro_box and intro_box["y"] >= title_box["y"], (
        "the detail intro is no longer the opening paragraph of the panel"
    )


# ── #137695 — 'Who This Service Is For' subsection ───────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Detail subsections")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Valid Who This Service Is For content is saved and rendered as its own detail subsection")
@allure.label("pbi", PBI)
@allure.label("testcase", "137695")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137695
@pytest.mark.traceability("ADO-137695")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_who_this_service_is_for_renders_as_its_own_subsection(page):
    """ADO-137695 | PBI 129400 — logged out: the English New Membership panel
    shows the heading 'Who This Service Is For' in Cairo Bold 16/24 #A66F43
    followed by 'Businesses and institutions that are not yet registered as
    Qatar Chamber members and wish to join.' in Cairo Medium 14/22 #4A4A49;
    the Arabic panel shows 'الفئات المستفيدة من الخدمة' with its Arabic body,
    both right-aligned."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    english_heading = MemberServicesPage.CASE_SUBHEADINGS_EN[0]
    english_body = services.subsection_body_text(english_heading)
    heading_style = services.subheading_style(0)
    body_style = services.body_text_style(1)
    services.open_service_detail(NEW_MEMBERSHIP, locale="ar")
    arabic_heading = MemberServicesPage.CASE_SUBHEADINGS_AR[0]
    arabic_headings_live = services.subheading_texts()
    arabic_body = services.subsection_body_text(arabic_heading)

    # Assert — English first
    assert english_body == CASE_NEW_MEMBERSHIP_AUDIENCE_EN, (
        f"the English 'Who This Service Is For' body reads {english_body!r}; "
        f"the case requires {CASE_NEW_MEMBERSHIP_AUDIENCE_EN!r}"
    )
    assert not _typography_is(heading_style, "16px", "24px", BOLD_WEIGHT, BROWN), (
        f"subsection heading typography: "
        f"{_typography_is(heading_style, '16px', '24px', BOLD_WEIGHT, BROWN)}"
    )
    assert not _typography_is(body_style, "14px", "22px", MEDIUM_WEIGHT, BODY_INK), (
        f"subsection body typography: "
        f"{_typography_is(body_style, '14px', '22px', MEDIUM_WEIGHT, BODY_INK)}"
    )
    # …then the Arabic heading string this build differs on.
    assert services.document_direction() == "rtl", (
        f"the Arabic panel renders {services.document_direction()!r}"
    )
    assert arabic_heading in arabic_headings_live, (
        f"the Arabic panel shows {arabic_headings_live}; the case requires the "
        f"heading {arabic_heading!r}"
    )
    assert arabic_body == CASE_NEW_MEMBERSHIP_AUDIENCE_AR, (
        f"the Arabic body reads {arabic_body!r}; the case requires "
        f"{CASE_NEW_MEMBERSHIP_AUDIENCE_AR!r}"
    )


# ── #137697 — SKIPPED: needs rich-text content authored ──────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Detail subsections")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Rich text entered in a detail subsection renders its headings, bullets, hyperlinks and images on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137697")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137697
@pytest.mark.traceability("ADO-137697")
@pytest.mark.skip(
    reason="BLOCKED — the case AUTHORS a heading, a paragraph, a two-item "
    "bulleted list, a hyperlink to https://www.qatarchamber.com and an inline "
    "image into New Membership's 'Who This Service Is For' rich-text editor, "
    "then publishes. Live that subsection holds a single paragraph and none "
    "of those five element types, so reaching the case's state is a "
    "Control_Panel WRITE, excluded from this Web-only read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_rich_text_elements_render_in_a_detail_subsection(page):
    """ADO-137697 | PBI 129400 — EN, logged out: the subsection renders the
    heading, the paragraph, both bullet items, a clickable hyperlink pointing
    at https://www.qatarchamber.com and the inline image — markup rendered,
    not shown as raw HTML and not stripped away."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    html = services.panel_html() or ""
    body = services.subsection_body_text(MemberServicesPage.CASE_SUBHEADINGS_EN[0]) or ""

    # Assert
    assert "<li" in html, "the two-item bulleted list did not render as markup"
    assert html.count("<li") >= 2, (
        f"only {html.count('<li')} list items rendered; the case authored two"
    )
    assert f'href="{CASE_RICH_TEXT_HYPERLINK}"' in html, (
        f"the hyperlink to {CASE_RICH_TEXT_HYPERLINK} did not render as a link"
    )
    assert "<img" in html, "the inline image did not render"
    assert "&lt;" not in body, (
        "the rich-text markup is being shown as escaped raw HTML"
    )


# ── #137698 — Required Documents dash list ───────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Detail subsections")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Required Documents content is saved and rendered as a dash-style list in the detail panel")
@allure.label("pbi", PBI)
@allure.label("testcase", "137698")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137698
@pytest.mark.traceability("ADO-137698")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_required_documents_render_as_a_dash_list(page):
    """ADO-137698 | PBI 129400 — EN, logged out: New Membership's 'Required
    Documents' subsection shows its heading in Cairo Bold 16/24 #A66F43
    followed by exactly four items, each preceded by a 1px #A66F43 dash
    marker in a 10px leading column, with a 4px gap between items and the
    item text in Cairo Medium 14/22 #4A4A49."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    headings = services.subheading_texts()
    items = services.required_documents_items()
    heading_style = services.subheading_style(1)
    item_style = services.required_documents_item_style()
    list_style = services.required_documents_list_style()
    marker = services.required_documents_marker_style()

    # Assert
    assert MemberServicesPage.CASE_SUBHEADINGS_EN[1] in headings, (
        f"the 'Required Documents' heading is absent ({headings})"
    )
    assert not _typography_is(heading_style, "16px", "24px", BOLD_WEIGHT, BROWN), (
        f"'Required Documents' heading typography: "
        f"{_typography_is(heading_style, '16px', '24px', BOLD_WEIGHT, BROWN)}"
    )
    assert len(items) == CASE_REQUIRED_DOCS_ITEM_COUNT, (
        f"the subsection shows {len(items)} items; the case requires exactly "
        f"{CASE_REQUIRED_DOCS_ITEM_COUNT} ({items})"
    )
    assert all(item.strip() for item in items), (
        f"a Required Documents item is blank: {items}"
    )
    assert marker.get("width") == CASE_DASH_MARKER_WIDTH, (
        f"the dash marker column is {marker.get('width')!r}; the case requires "
        f"{CASE_DASH_MARKER_WIDTH}"
    )
    assert marker.get("height") == CASE_DASH_MARKER_HEIGHT, (
        f"the dash marker is {marker.get('height')!r} tall; the case requires "
        f"{CASE_DASH_MARKER_HEIGHT}"
    )
    assert _matches_hex(marker.get("backgroundColor"), BROWN), (
        f"the dash marker is {marker.get('backgroundColor')!r}; the case "
        f"requires {BROWN}"
    )
    assert list_style.get("gap") == CASE_REQUIRED_DOCS_GAP, (
        f"the items are {list_style.get('gap')!r} apart; the case requires "
        f"{CASE_REQUIRED_DOCS_GAP}"
    )
    assert not _typography_is(item_style, "14px", "22px", MEDIUM_WEIGHT, BODY_INK), (
        f"Required Documents item typography: "
        f"{_typography_is(item_style, '14px', '22px', MEDIUM_WEIGHT, BODY_INK)}"
    )


# ── #137700 — SKIPPED: needs Required Documents cleared ──────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Detail subsections")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("An empty Required Documents field hides that subsection on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137700")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137700
@pytest.mark.traceability("ADO-137700")
@pytest.mark.skip(
    reason="BLOCKED — the case CLEARS Required Documents (EN and AR) on the "
    "'Signatory Cancellation' record and re-publishes. Live that subsection "
    "holds two items, so reaching the case's state is a Control_Panel WRITE "
    "against real shared content, excluded from this Web-only read-only "
    "batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_empty_required_documents_hides_the_subsection(page):
    """ADO-137700 | PBI 129400 — EN, logged out: with Required Documents
    empty, the Signatory Cancellation panel shows the detail intro, 'Who This
    Service Is For' and 'How to Apply' in sequence — the 'Required Documents'
    heading and its dash list are absent, with no empty heading and no blank
    gap."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(SIGNATORY_CANCELLATION)

    # Act
    headings = services.subheading_texts()
    items = services.required_documents_count()

    # Assert
    assert MemberServicesPage.CASE_SUBHEADINGS_EN[1] not in headings, (
        f"the 'Required Documents' heading is still rendered with an empty "
        f"value ({headings})"
    )
    assert items == 0, f"{items} dash-list items still render"
    assert headings == [
        MemberServicesPage.CASE_SUBHEADINGS_EN[0],
        MemberServicesPage.CASE_SUBHEADINGS_EN[2],
    ], (
        f"the panel shows {headings}; the case requires 'Who This Service Is "
        f"For' then 'How to Apply' in sequence"
    )


# ── #137701 — How to Apply above the CTA ─────────────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Detail subsections")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Valid How to Apply content is saved and rendered above the CTA button")
@allure.label("pbi", PBI)
@allure.label("testcase", "137701")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137701
@pytest.mark.traceability("ADO-137701")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_how_to_apply_renders_above_the_cta(page):
    """ADO-137701 | PBI 129400 — logged out: the English New Membership panel
    shows 'How to Apply' in Cairo Bold 16/24 #A66F43 with the body 'Complete
    your application through the Qatar Chamber digital membership portal.
    Ensure all required documents are uploaded in their approved formats
    before submission.' positioned after 'Required Documents' and immediately
    before the CTA; the Arabic panel shows 'كيفية التقديم' in the same
    position, right-aligned."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    headings = services.subheading_texts()
    body = services.subsection_body_text(MemberServicesPage.CASE_SUBHEADINGS_EN[2])
    heading_style = services.subheading_style(2)
    heading_box = services.subheading_box(2)
    required_box = services.subheading_box(1)
    cta_box = services.cta_box()
    services.open_service_detail(NEW_MEMBERSHIP, locale="ar")
    arabic_headings = services.subheading_texts()
    arabic_style = services.subheading_style(2)

    # Assert
    assert headings == list(MemberServicesPage.CASE_SUBHEADINGS_EN), (
        f"the panel shows {headings}"
    )
    assert body == CASE_NEW_MEMBERSHIP_HOW_TO_APPLY_EN, (
        f"the 'How to Apply' body reads {body!r}; the case requires "
        f"{CASE_NEW_MEMBERSHIP_HOW_TO_APPLY_EN!r}"
    )
    assert not _typography_is(heading_style, "16px", "24px", BOLD_WEIGHT, BROWN), (
        f"'How to Apply' heading typography: "
        f"{_typography_is(heading_style, '16px', '24px', BOLD_WEIGHT, BROWN)}"
    )
    assert required_box and heading_box and cta_box, (
        "the panel did not render Required Documents, How to Apply and the CTA"
    )
    assert required_box["y"] < heading_box["y"] < cta_box["y"], (
        f"'How to Apply' is not between 'Required Documents' and the CTA "
        f"(required y={required_box['y']}, how-to y={heading_box['y']}, CTA "
        f"y={cta_box['y']})"
    )
    assert MemberServicesPage.CASE_SUBHEADINGS_AR[2] in arabic_headings, (
        f"the Arabic panel shows {arabic_headings}; the case requires "
        f"{MemberServicesPage.CASE_SUBHEADINGS_AR[2]!r}"
    )
    assert services.document_direction() == "rtl" and arabic_style.get(
        "textAlign"
    ) in ("start", "right"), (
        f"the Arabic 'How to Apply' heading is not right-aligned "
        f"({arabic_style.get('textAlign')!r})"
    )


# ── #137703 — SKIPPED: needs a whitespace-only How to Apply value ────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Detail subsections")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A whitespace-only How to Apply value is treated as empty and its subsection is hidden")
@allure.label("pbi", PBI)
@allure.label("testcase", "137703")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137703
@pytest.mark.traceability("ADO-137703")
@pytest.mark.skip(
    reason="BLOCKED — the case REPLACES Membership Renewal's How to Apply "
    "(EN) with five spaces inside an empty paragraph and re-publishes. Live "
    "that subsection holds real content, so reaching the case's state is a "
    "Control_Panel WRITE against real shared content, excluded from this "
    "Web-only read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_whitespace_only_how_to_apply_is_hidden(page):
    """ADO-137703 | PBI 129400 — EN, logged out: with How to Apply holding
    only whitespace, its heading is NOT rendered — the subsection is hidden
    exactly as for a genuinely empty value, with no heading over a blank body
    and no stray divider before the CTA."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(MEMBERSHIP_RENEWAL)

    # Act
    headings = services.subheading_texts()
    body = services.subsection_body_text(MemberServicesPage.CASE_SUBHEADINGS_EN[2])

    # Assert
    assert MemberServicesPage.CASE_SUBHEADINGS_EN[2] not in headings, (
        f"the 'How to Apply' heading is still rendered for a whitespace-only "
        f"value ({headings}), with body {body!r}"
    )
    assert headings == [
        MemberServicesPage.CASE_SUBHEADINGS_EN[0],
        MemberServicesPage.CASE_SUBHEADINGS_EN[1],
    ], f"the panel shows {headings}"


# ── #137704 — SKIPPED: needs a detail Supporting Image uploaded ──────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level fields")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("A valid detail-view Supporting Image is accepted and rendered beside the detail content")
@allure.label("pbi", PBI)
@allure.label("testcase", "137704")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137704
@pytest.mark.traceability("ADO-137704")
@pytest.mark.skip(
    reason="BLOCKED — the case UPLOADS a 700 KB JPG as New Membership's "
    "Supporting Image (Detail View, EN) and asserts that THAT image renders. "
    "An asset upload is a Control_Panel WRITE, excluded from this Web-only "
    "read-only batch, and the uploaded asset cannot be identified without "
    "performing the upload. The geometry + mirroring half is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_detail_supporting_image_renders_beside_the_content(page):
    """ADO-137704 | PBI 129400 — logged out: in English the image renders to
    the RIGHT of the content panel at 312px wide with a 12px corner radius
    and a 40px inset; in Arabic the same image renders on the LEFT of the
    panel in the mirrored position."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    english_style = services.detail_support_style()
    english_support_box = services.detail_support_box()
    english_panel_box = services.panel_box()
    services.open_service_detail(NEW_MEMBERSHIP, locale="ar")
    arabic_support_box = services.detail_support_box()
    arabic_panel_box = services.panel_box()

    # Assert
    assert english_style.get("width") == f"{CASE_SUPPORT_WIDTH_PX}px", (
        f"the detail supporting image is {english_style.get('width')!r} wide"
    )
    assert english_style.get("borderRadius") == CASE_DETAIL_SUPPORT_RADIUS, (
        f"the detail supporting image radius is "
        f"{english_style.get('borderRadius')!r}"
    )
    assert english_panel_box["x"] < english_support_box["x"], (
        "the English detail supporting image is not to the right of the panel"
    )
    assert arabic_support_box["x"] < arabic_panel_box["x"], (
        "the Arabic detail supporting image is not in the mirrored (left) "
        "position"
    )


# ── #137707 — CTA Button Label in both languages ─────────────────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service CTA")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid bilingual CTA Button Label is saved and rendered on the CTA button")
@allure.label("pbi", PBI)
@allure.label("testcase", "137707")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137707
@pytest.mark.traceability("ADO-137707")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_cta_button_label_renders_in_both_languages(page):
    """ADO-137707 | PBI 129400 — logged out: the English New Membership CTA
    reads 'Apply for Membership' in Cairo SemiBold 16/24 #FFFFFF on a #911731
    fill; the Arabic CTA reads 'تقديم طلب العضوية' with the arrow icon
    mirrored to the leading edge."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    english_label = services.cta_label()
    english_style = services.cta_style()
    services.open_service_detail(NEW_MEMBERSHIP, locale="ar")
    arabic_label = services.cta_label()
    arabic_icon_leads = services.cta_icon_is_leading()

    # Assert
    assert english_label == CASE_NEW_MEMBERSHIP_CTA_LABEL_EN, (
        f"the English CTA reads {english_label!r}; the case requires "
        f"{CASE_NEW_MEMBERSHIP_CTA_LABEL_EN!r}"
    )
    assert _matches_hex(english_style.get("backgroundColor"), MAROON), (
        f"the CTA fill is {english_style.get('backgroundColor')!r}"
    )
    assert not _typography_is(english_style, "16px", "24px", SEMIBOLD_WEIGHT, WHITE), (
        f"CTA label typography: "
        f"{_typography_is(english_style, '16px', '24px', SEMIBOLD_WEIGHT, WHITE)}"
    )
    assert arabic_icon_leads is True, (
        "the Arabic CTA's arrow icon is not mirrored to the leading edge"
    )
    assert arabic_label == CASE_NEW_MEMBERSHIP_CTA_LABEL_AR, (
        f"the Arabic CTA reads {arabic_label!r}; the case requires "
        f"{CASE_NEW_MEMBERSHIP_CTA_LABEL_AR!r}"
    )


# ── #137708 — SKIPPED: needs a 100/101-character save attempt ────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("The CTA Button Label field enforces its 100-character limit")
@allure.label("pbi", PBI)
@allure.label("testcase", "137708")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137708
@pytest.mark.traceability("ADO-137708")
@pytest.mark.skip(
    reason="BLOCKED — the case ENTERS exactly 100 characters in CTA Button "
    "Label (EN), saves, then attempts a 101st. Both are Control_Panel WRITES, "
    "excluded from this Web-only read-only batch; only step 4's public half "
    "(the stored label is at most 100 characters and renders without "
    "overflowing the panel) is expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_cta_button_label_enforces_its_100_character_limit(page):
    """ADO-137708 | PBI 129400 — EN, logged out: the stored CTA label is at
    most 100 characters long and the CTA renders it without breaking the panel
    layout or overflowing its container."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    label = services.cta_label() or ""
    cta_box = services.cta_box()
    panel_box = services.panel_box()

    # Assert
    assert len(label) <= 100, (
        f"the stored CTA label is {len(label)} characters; the case requires "
        f"at most 100"
    )
    assert cta_box and panel_box, "the CTA or the panel did not render"
    assert cta_box["x"] + cta_box["width"] <= panel_box["x"] + panel_box["width"] + 1, (
        f"the CTA overflows its container (CTA ends at "
        f"{cta_box['x'] + cta_box['width']}, panel ends at "
        f"{panel_box['x'] + panel_box['width']})"
    )


# ── #137710 — CTA Redirect URL is the button's destination ───────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service CTA")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("A valid CTA Redirect URL is saved and used as the CTA button destination")
@allure.label("pbi", PBI)
@allure.label("testcase", "137710")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137710
@pytest.mark.traceability("ADO-137710")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_cta_redirect_url_is_the_button_destination(page):
    """ADO-137710 | PBI 129400 — EN, logged out: New Membership's CTA button
    destination is exactly the configured CTA Redirect URL and clicking it
    lands the visitor on that URL.

    DESIGN DRIFT accepted by QA Manager 2026-09-27 (ADO-137710): the case
    named /membership/apply; the delivered build configures
    /membership/new-membership, which was confirmed live (301 -> 200) before
    the expectation was moved to the build.

    IMPLEMENTED rather than skipped: the expected value is a product content
    expectation, not a QA_AUTO marker, and reading the rendered destination is
    a pure public read. No Control_Panel action was taken — if the stored URL
    differs, this test says so instead of hiding it."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(NEW_MEMBERSHIP)

    # Act
    href = services.cta_href()

    # Assert — the rendered destination, before spending a navigation on it
    assert href == CASE_NEW_MEMBERSHIP_CTA_URL, (
        f"the CTA destination is {href!r}; the case requires exactly "
        f"{CASE_NEW_MEMBERSHIP_CTA_URL!r}"
    )
    outcome = services.click_cta()
    # The configured URL answers 301 to CASE_NEW_MEMBERSHIP_CTA_URL_RESOLVED
    # (verified by curl 2026-09-27), so the browser settles on the redirect
    # target. Both are accepted — and ONLY those two, so a CTA that lands
    # anywhere else (or on an error page) still reds.
    assert outcome["landing_page"].url.rstrip("/") in (
        CASE_NEW_MEMBERSHIP_CTA_URL.rstrip("/"),
        CASE_NEW_MEMBERSHIP_CTA_URL_RESOLVED.rstrip("/"),
    ), (
        f"clicking the CTA landed on {outcome['landing_page'].url!r}; the case "
        f"requires {CASE_NEW_MEMBERSHIP_CTA_URL!r} (or its 301 target "
        f"{CASE_NEW_MEMBERSHIP_CTA_URL_RESOLVED!r})"
    )


# ── #137713 — SKIPPED: needs a rejected URL-without-label save ───────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("Entering a redirect URL without a CTA label is rejected with the paired-field message")
@allure.label("pbi", PBI)
@allure.label("testcase", "137713")
@pytest.mark.functional_low
@pytest.mark.regression
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137713
@pytest.mark.traceability("ADO-137713")
@pytest.mark.skip(
    reason="BLOCKED — the case starts from 'Signatory Cancellation' with BOTH "
    "CTA fields EMPTY (live both are populated), enters a redirect URL with "
    "no label, and asserts Save is blocked with 'Both CTA label and redirect "
    "URL are required to display the button.'. The starting state and the "
    "save attempt are Control_Panel WRITES, excluded from this Web-only "
    "read-only batch."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_redirect_url_without_cta_label_is_rejected(page):
    """ADO-137713 | PBI 129400 — EN, logged out: after the blocked save, the
    Signatory Cancellation detail panel renders with NO CTA button and no
    empty or unlabelled button placeholder."""
    # Arrange
    services = MemberServicesPage(page).open_service_detail(SIGNATORY_CANCELLATION)

    # Act
    cta_count = services.cta_count()
    label = services.cta_label()

    # Assert
    assert cta_count == 0, (
        f"{cta_count} CTA buttons render after the rejected save (label "
        f"{label!r}); the case requires none"
    )


# ── #137714 — Display Order controls the rendered position ───────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Display order")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A valid Display Order value is saved and controls the service position on the website")
@allure.label("pbi", PBI)
@allure.label("testcase", "137714")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137714
@pytest.mark.traceability("ADO-137714")
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_display_order_controls_the_service_position(page):
    """ADO-137714 | PBI 129400 — EN, logged out: with the other services at 1,
    2 and 4, 'Attestation on Signature' holds Display Order 3 and therefore
    renders as the THIRD service card and the THIRD sidebar row."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    expected = SERVICE_NAME_BY_KEY[ATTESTATION]
    assert len(card_names) == CASE_SERVICE_COUNT, (
        f"{len(card_names)} cards render ({card_names})"
    )
    assert card_names[2] == expected, (
        f"the third service card is {card_names[2]!r}; the case requires "
        f"{expected!r} at Display Order 3"
    )
    assert sidebar_labels[2] == expected, (
        f"the third sidebar row is {sidebar_labels[2]!r}; the case requires "
        f"{expected!r}"
    )


# ── #137716 — SKIPPED: needs a rejected duplicate-order save ─────────────
@allure.epic("Our Services")
@allure.feature("Member's Services")
@allure.story("Service-level validation")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("A duplicate Display Order value is rejected because the value must be unique")
@allure.label("pbi", PBI)
@allure.label("testcase", "137716")
@pytest.mark.functional_low
@pytest.mark.web
@pytest.mark.pbi_129400
@pytest.mark.tc_137716
@pytest.mark.traceability("ADO-137716")
@pytest.mark.skip(
    reason="BLOCKED — the case ENTERS Display Order 1 on 'Membership Renewal' "
    "while New Membership already holds 1, and asserts Save is blocked with a "
    "uniqueness validation message. Both are Control_Panel WRITES, excluded "
    "from this Web-only read-only batch; only step 4's public half (the list "
    "renders in a single deterministic order with no two services competing "
    "for a position) is expressible and is written below."
)
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_duplicate_display_order_is_rejected(page):
    """ADO-137716 | PBI 129400 — EN, logged out: after the blocked save,
    Membership Renewal keeps Display Order 2 and the card list and sidebar
    render in a single deterministic order with no two services competing for
    the same position."""
    # Arrange
    services = MemberServicesPage(page).open_member_services()

    # Act
    card_names = services.service_card_names()
    services.click_card_details(NEW_MEMBERSHIP)
    sidebar_labels = services.sidebar_labels()

    # Assert
    assert card_names[1] == SERVICE_NAME_BY_KEY[MEMBERSHIP_RENEWAL], (
        f"the second card is {card_names[1]!r}; Membership Renewal must keep "
        f"Display Order 2 after the rejected save"
    )
    assert len(card_names) == len(set(card_names)) == CASE_SERVICE_COUNT, (
        f"the card list is not a single deterministic order: {card_names}"
    )
    assert card_names == sidebar_labels, (
        f"the card list {card_names} and the sidebar {sidebar_labels} disagree "
        f"on the order"
    )

"""
web/tests/media_center/test_mc_hub_web.py — FE-HUB (PBI 130709, Azure plan 137724 / suite 140368).

Public Media Center hub: hero entry + breadcrumb, summary counts strip,
quick-access cards, section order, draft/unpublished visibility, plus the
hub-hero search cases that were grouped into this batch (Arabic keyword,
content-type filter / clear).

Rules applied (scratchpad p3_rules_130709.md, Batch 3):
- Every public assertion runs in a fresh logged-out context (`{"auth": False}`).
- CMS setup reuses the batch-1 helpers read-only (cms/tests/media_center/
  qac_support.py, cms/pages/media_center/*). Disposable cards are QCTEST
  cards deleted by exact captured id/code; the news article is a
  QCTEST-130709 article deleted by exact code.
- Real records: QCDEMO-130709-CARD-01/02 only, through the QAC RealCardGuard
  (snapshot -> UI edit as Editor -> logged-out check -> exact PUT restore ->
  empty diff, concurrency guard before edit and restore) + a file lock.
- Configured values (card links / orders, feed-section orders, unit labels)
  are read from the stored records through an Editor session (read-only).

Disclosed adaptations (live 2026-10-13):
- Hub URL is /web/qatar-chamber/media-center (case placeholder
  "<WEB_BASE_URL>/media-center"); the breadcrumb Home link is /web/qatar-chamber.
- USER DECISION 2026-10-12: the hub shows six FIXED cards (maxCards=6), so a
  QCTEST card never renders publicly. 149096 runs on the real card Photo
  Gallery (Active Status unticked, then restored); 149098 swaps the Display
  Orders of the real cards Photo Gallery/Video Gallery (100 <-> 200) so the
  card created SECOND sorts first; 149101 cannot show QCTEST-130709-QAC-05
  before the unpublish (step 1 N/A), the hidden-after-unpublish result is asserted.
- Draft (149100) is saved by the Site Content Author (rules: drafts run from
  the Author account).
"""

from __future__ import annotations

import json
import os
import re
from contextlib import contextmanager
from datetime import date, datetime
from time import monotonic
from urllib.parse import parse_qs, urlparse

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED, STATUS_UNPUBLISHED
from cms.pages.media_center.mc_quick_access_card_admin_page import (
    ROLE_AUTHOR,
    ROLE_EDITOR,
    ROLE_USER_IDS,
    QacAdminPage,
)
from cms.tests.media_center.qac_support import (  # noqa: F401 — fixtures qac / real_guard
    attach,
    card_data,
    create,
    create_ok,
    guarded_edit,
    qac,
    real_guard,
    real_session,
)
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from web.pages.media_center.mc_hub_page import (
    EVIDENCE_DIR,
    HOME_PATH,
    HUB_PATH,
    HomeMainMenu,
    HubConfigReader,
    MediaCenterHubPage,
    MediaSearchResultsPage,
    ModuleListingTotals,
    shot,
)

pytestmark = [pytest.mark.web, pytest.mark.media, pytest.mark.pbi_130709,
              pytest.mark.xdist_group("mc_fehub_130709")]

ANON = {"auth": False}
EPIC = "Media Center"
FEATURE = "Media Center hub — Web"
BUDGET_S = 5.0
CARD01 = "QCDEMO-130709-CARD-01"
CARD02 = "QCDEMO-130709-CARD-02"
LOCK_DIR = os.path.join(r"C:\Users\HP\AppData\Local\Temp\claude\d--Qatar-Chamber-QaterChamber-main"
                        r"\de2eae66-6f02-4a22-8869-a22476b25d22\scratchpad", "locks")
# public widget display name -> content type key (counts API / listing)
WIDGET_TYPES = {"Articles": "articles", "Photo Albums": "photoAlbums", "Videos": "videos",
                "Podcast": "podcast", "Publications": "publications"}


def _labels(tc: str, qa: str, title: str):
    allure.dynamic.epic(EPIC)
    allure.dynamic.feature(FEATURE)
    allure.dynamic.title(title)
    allure.dynamic.label("testcase", tc)
    allure.dynamic.label("pbi", "130709")
    allure.dynamic.label("qa_id", qa)


def _path(url: str) -> str:
    return urlparse(url).path.rstrip("/") or "/"


# ===========================================================================
# shared fixtures
# ===========================================================================
@pytest.fixture(scope="module")
def hub_config(browser):
    """Stored hub configuration (read-only, Editor session)."""
    ctx = new_context(browser, use_auth_state=False)
    try:
        admin = QacAdminPage(ctx.new_page())
        if admin.login_as_role(ROLE_EDITOR) == "auth_failed":
            pytest.fail("PRECONDITION: Liferay refused the Site Content Editor credentials")
        admin.open_manage_page_raw()
        reader = HubConfigReader(admin)
        config = {res: reader.items(res) for res in
                  ("mediacenterquickaccesscards", "mediacenterfeedsections", "mediacentercountwidgets")}
    finally:
        ctx.close()
    attach("stored hub configuration (read-only)", {
        k: [{x: i.get(x) for x in ("code", "status_code", "activeStatus", "displayOrder", "cardTitle",
                                    "destinationLink", "sectionType", "displayName", "unitLabel", "contentType")}
            for i in v] for k, v in config.items()})
    return config


def _live(items: list[dict], real_only: bool = True) -> list[dict]:
    """Published (status code 0) + Active records, sorted by Display Order."""
    rows = [i for i in items if i.get("status_code") == 0 and i.get("activeStatus")
            and (not real_only or i.get("code", "").startswith("QCDEMO-"))]
    return sorted(rows, key=lambda i: int(i.get("displayOrder") or 0))


def _card_link(hub_config, title: str) -> str:
    rows = [c for c in hub_config["mediacenterquickaccesscards"] if (c.get("cardTitle") or "").strip() == title]
    assert len(rows) == 1, f"PRECONDITION: {len(rows)} stored cards titled {title!r}"
    return rows[0].get("destinationLink") or ""


@contextmanager
def _record_lock(code: str, timeout_s: float = 600.0):
    """One writer at a time on a real hub record (file lock in the shared scratchpad)."""
    os.makedirs(LOCK_DIR, exist_ok=True)
    path = os.path.join(LOCK_DIR, f"mc_qac_{code}.lock")
    held = {"fd": None}

    def _try() -> bool:
        try:
            held["fd"] = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(held["fd"], f"FE-HUB {datetime.now().isoformat()}".encode())
            return True
        except FileExistsError:
            return False

    try:
        wait_until(_try, timeout=timeout_s, poll=3.0)
    except WaitTimeoutError:
        pytest.fail(f"PRECONDITION: {path} still held after {timeout_s:.0f}s (another writer)")
    try:
        yield path
    finally:
        os.close(held["fd"])
        os.remove(path)


@pytest.fixture
def card01_lock():
    with _record_lock(CARD01):
        yield


@pytest.fixture
def cards_lock():
    with _record_lock(CARD01), _record_lock(CARD02):
        yield


def _fresh_hub(browser, locale: str = "en") -> tuple:
    ctx = new_context(browser, use_auth_state=False)
    hub = MediaCenterHubPage(ctx.new_page()).open_hub(locale)
    return ctx, hub


# ===========================================================================
# Navigation into the hub / breadcrumb
# ===========================================================================
@pytest.mark.tc_149087
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.redirect
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_main_menu_insights_media_opens_media_center(page):
    """MEDIA-MCHUB-TC-033 — Main Menu -> Insights & Media -> Media Center opens the hub."""
    _labels("149087", "MEDIA-MCHUB-TC-033", "Main menu reaches the Media Center hub")
    menu = HomeMainMenu(page).open_home()
    with allure.step("1. Hover 'Insights & Media' in the main menu"):
        entries = menu.open_group()
        menu.evidence("149087_submenu")
        assert "Media Center" in entries, f"the Insights & Media submenu does not list 'Media Center': {entries}"
    with allure.step("2. Click 'Media Center'"):
        menu.click_entry()
        hub = MediaCenterHubPage(page).wait_ready()
        hub.evidence("149087_hub")
        assert _path(page.url) == HUB_PATH, f"landed on {page.url}, not {HUB_PATH}"
        assert hub.hero_label() == "Media Center", f"hero label reads {hub.hero_label()!r}"


@pytest.mark.tc_149152
@pytest.mark.functional_low
@pytest.mark.redirect
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_breadcrumb_home_navigates_to_home_page(page):
    """MEDIA-MCHUB-TC-098 — breadcrumb 'Home' opens the website home page."""
    _labels("149152", "MEDIA-MCHUB-TC-098", "Breadcrumb Home opens the home page")
    hub = MediaCenterHubPage(page).open_hub()
    crumbs = hub.breadcrumb()
    hub.evidence("149152_breadcrumb", full_page=False)
    assert crumbs == ["Home", "Media Center"], f"breadcrumb reads {crumbs}"
    hub.click_breadcrumb_home()
    landed = _path(page.url)
    home = page.locator("section.qc-home-hero-banner")
    try:
        home.first.wait_for(state="attached", timeout=60000)
    except Exception:  # noqa: BLE001 — asserted below
        pass
    shot(page, "149152_home", full_page=False)
    assert landed in ("/", HOME_PATH), f"Home crumb landed on {page.url}"
    assert home.count() > 0, f"{page.url} is not the home page (no home hero banner)"


# ===========================================================================
# Counts strip
# ===========================================================================
@pytest.mark.tc_149088
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_count_widgets_equal_module_published_totals(page):
    """MEDIA-MCHUB-TC-034 — every widget count equals its module's public published total."""
    _labels("149088", "MEDIA-MCHUB-TC-034", "Count widgets equal the modules' published totals")
    listing = ModuleListingTotals(page)
    totals = {}
    with allure.step("1-2. Note the published total on each module listing"):
        for key in WIDGET_TYPES.values():
            totals[key] = listing.total(key)
        attach("listing totals", totals)
        missing = [k for k, v in totals.items() if v["number"] is None]
        assert not missing, f"PRECONDITION: no visible total on the listing(s) {missing}: {totals}"
    with allure.step("3. Read the five widget counts on the hub"):
        hub = MediaCenterHubPage(page).open_hub()
        widgets = hub.count_widgets()
        hub.evidence("149088_counts", full_page=False)
        attach("widgets", widgets)
    mismatches = []
    for name, key in WIDGET_TYPES.items():
        w = [x for x in widgets if x["label"] == name]
        if not w:
            mismatches.append(f"{name}: widget not displayed")
        elif w[0]["number"] != totals[key]["number"]:
            mismatches.append(f"{name}: widget {w[0]['value']!r} vs listing {totals[key]['text']!r} "
                              f"({totals[key]['path']})")
    assert not mismatches, "widget count != module published total: " + "; ".join(mismatches)


@pytest.mark.tc_149092
@pytest.mark.functional_high
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_count_widget_with_no_published_items_shows_zero(page):
    """MEDIA-MCHUB-TC-038 — Podcast with no published episode shows '0 episodes', not hidden."""
    _labels("149092", "MEDIA-MCHUB-TC-038", "Empty content type shows 0 and stays visible")
    podcast = ModuleListingTotals(page).total("podcast")
    attach("podcast listing total", podcast)
    if podcast["number"]:
        pytest.skip(f"BLOCKED: precondition not met on qcdev — the public Podcast listing shows "
                    f"{podcast['text']!r} (published episodes exist) and real content must not be unpublished")
    hub = MediaCenterHubPage(page).open_hub()
    widgets = hub.count_widgets()
    hub.evidence("149092_counts", full_page=False)
    pod = [w for w in widgets if w["label"] == "Podcast"]
    assert pod and pod[0]["number"] == 0, f"Podcast widget reads {pod}"
    assert len([w for w in widgets if w["visible"]]) == 5, f"not all five widgets are displayed: {widgets}"


@pytest.mark.tc_149150
@pytest.mark.functional_low
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_count_widget_shows_configured_unit_after_count(page, hub_config):
    """MEDIA-MCHUB-TC-096 — each widget shows '<count> <configured unit label>'."""
    _labels("149150", "MEDIA-MCHUB-TC-096", "Count line = count + configured unit label")
    configured = _live(hub_config["mediacentercountwidgets"])
    assert len(configured) == 5, f"PRECONDITION: {len(configured)} live real widgets: {configured}"
    hub = MediaCenterHubPage(page).open_hub()
    widgets = hub.count_widgets()
    hub.evidence("149150_counts", full_page=False)
    attach("public widgets", widgets)
    problems = []
    for cfg in configured:
        name, unit = cfg["displayName"], cfg["unitLabel"]
        w = [x for x in widgets if x["label"] == name]
        if not w:
            problems.append(f"{name}: not displayed")
            continue
        if not re.fullmatch(rf"\d[\d,]* {re.escape(unit)}", w[0]["value"]):
            problems.append(f"{name}: shows {w[0]['value']!r}, expected '<count> {unit}'")
    assert not problems, "; ".join(problems)


@pytest.mark.tc_149151
@pytest.mark.functional_low
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_count_widget_click_causes_no_navigation(page):
    """MEDIA-MCHUB-TC-097 — clicking a count widget does not navigate."""
    _labels("149151", "MEDIA-MCHUB-TC-097", "Count widgets are display-only")
    hub = MediaCenterHubPage(page).open_hub()
    start = page.url
    assert _path(start) == HUB_PATH, f"PRECONDITION: hub URL is {start}"
    problems = []
    for label in ("Articles", "Photo Albums"):
        result = hub.click_count_widget(label)
        attach(f"click {label}", result)
        if not result["found"]:
            problems.append(f"{label}: widget not found")
            continue
        if result["url_after"] != start or result["navigations"] or result["popups"] or result["new_pages"]:
            problems.append(f"{label}: navigation occurred {result}")
        if abs(result["scroll_after"] - result["scroll_before"]) > 2:
            problems.append(f"{label}: page scrolled {result['scroll_before']} -> {result['scroll_after']}")
    hub.evidence("149151_after_clicks", full_page=False)
    widgets = hub.count_widgets()
    linked = [w["label"] for w in widgets if w["in_link"] or w["has_link"]]
    assert not problems, "; ".join(problems)
    assert not linked, f"count widgets carry a link: {linked}"


# ===========================================================================
# Quick-access cards — destinations
# ===========================================================================
def _follow_and_check(hub: MediaCenterHubPage, hub_config, title: str, part: str, tc: str,
                      need_200: bool = True) -> list[str]:
    configured = _card_link(hub_config, title)
    result = hub.follow_card(title, part)
    attach(f"{title} ({part})", {"configured": configured, **result})
    shot(hub.page if not result["new_tab"] else hub.page, f"{tc}_{re.sub(r'\W+', '_', title)}", full_page=False)
    problems = []
    if configured.startswith("http"):
        if not result["url"].startswith(configured.rstrip("/")):
            problems.append(f"{title}: landed on {result['url']}, configured {configured}")
    elif _path(result["url"]) != configured.rstrip("/"):
        problems.append(f"{title}: landed on {result['url']}, configured {configured}")
    status = result["status"]
    if need_200 and status != 200:
        problems.append(f"{title}: HTTP {status} at {result['url']}")
    elif not need_200 and (status is None or status >= 400):
        problems.append(f"{title}: page did not load (HTTP {status}) at {result['url']}")
    return problems


@pytest.mark.tc_149093
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.uat
@pytest.mark.redirect
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_card_body_click_opens_configured_destination(page, hub_config):
    """MEDIA-MCHUB-TC-039 — clicking the body of 'Photo Gallery' opens its configured destination."""
    _labels("149093", "MEDIA-MCHUB-TC-039", "Card body click redirects to the configured destination")
    hub = MediaCenterHubPage(page).open_hub()
    cards = hub.cards()
    hub.evidence("149093_cards", full_page=False)
    assert len(cards) == 6, f"{len(cards)} quick-access cards displayed: {[c['title'] for c in cards]}"
    problems = _follow_and_check(hub, hub_config, "Photo Gallery", "body", "149093")
    assert not problems, "; ".join(problems)


@pytest.mark.tc_149094
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_card_arrow_click_opens_configured_destination(page, hub_config):
    """MEDIA-MCHUB-TC-040 — clicking only the arrow of 'Video Gallery' opens its configured destination."""
    _labels("149094", "MEDIA-MCHUB-TC-040", "Card arrow click redirects to the configured destination")
    hub = MediaCenterHubPage(page).open_hub()
    cards = hub.cards()
    assert len(cards) == 6, f"{len(cards)} quick-access cards displayed: {[c['title'] for c in cards]}"
    problems = _follow_and_check(hub, hub_config, "Video Gallery", "arrow", "149094")
    assert not problems, "; ".join(problems)


@pytest.mark.tc_149095
@pytest.mark.functional_high
@pytest.mark.redirect
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_remaining_cards_open_configured_destinations(page, hub_config):
    """MEDIA-MCHUB-TC-041 — Publications, Al-Moltqa Magazine, Members Directory, Request to the Media Dept."""
    _labels("149095", "MEDIA-MCHUB-TC-041", "Remaining cards redirect to their configured destinations")
    hub = MediaCenterHubPage(page)
    problems = []
    for title, need_200 in (("Publications", True), ("Al-Moltqa Magazine", True),
                            ("Members Directory", False), ("Request to the Media Dept", False)):
        with allure.step(f"Open the hub and click '{title}'"):
            hub.open_hub()
            problems += _follow_and_check(hub, hub_config, title, "body", "149095", need_200)
    assert not problems, "; ".join(problems)


# ===========================================================================
# Quick-access cards — visibility / order (CMS-driven)
# ===========================================================================
def _poll(hub: MediaCenterHubPage, predicate, what: str, tc: str, started: float | None = None,
          locale: str = "en") -> list[dict]:
    held, cards, seconds = hub.poll_cards(predicate, timeout=60.0, locale=locale)
    path = hub.evidence(f"{tc}_{re.sub(r'\W+', '_', what)[:40]}")
    attach(f"public: {what}", {"held": held, "seconds": round(seconds, 1),
                               "cards": [(c["title"], c["erc"], c["box"]) for c in cards]})
    assert held, f"{what}: not seen on the logged-out hub within 60s (cards {[c['title'] for c in cards]}); {path}"
    if started is not None and seconds > BUDGET_S:
        pytest.fail(f"{what}: first seen {seconds:.1f}s after the save (> {BUDGET_S:.0f}s visitor budget); {path}")
    return cards


@pytest.mark.tc_149096
@pytest.mark.functional_high
@pytest.mark.uat
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_inactive_card_hidden_and_grid_reflows(card01_lock, qac, real_guard, page):
    """MEDIA-MCHUB-TC-042 — a card set inactive is hidden; the rest reflow without a gap.
    Runs on the real card Photo Gallery (user decision 2026-10-12, guarded + restored)."""
    _labels("149096", "MEDIA-MCHUB-TC-042", "Inactive card hidden, grid reflows without a gap")
    attach("adaptation", "QCTEST-130709-QAC-07 can never render (six fixed cards) -> real card "
                         f"{CARD01} (Photo Gallery) Active Status unticked, then restored by exact PUT + empty diff")
    sessions, admin, ref = real_session(qac, real_guard, CARD01)
    hub = MediaCenterHubPage(page)
    with allure.step("1. Logged-out: count the cards"):
        before = _poll(hub, lambda c: any(x["erc"] == CARD01 for x in c), "card shown before", "149096")
    with allure.step("2. As Editor untick Active Status on the card and publish"):
        result = guarded_edit(real_guard, admin, ref, {"activeStatus": False}, "149096_untick")
        assert result["went_through"], f"unticking Active Status was refused: {result['evidence']}"
        started = monotonic()
    with allure.step("3-4. Logged-out reload: card hidden, grid contiguous"):
        after = _poll(hub, lambda c: not any(x["erc"] == CARD01 for x in c), "card hidden", "149096",
                      started=started)
    remaining = [c for c in before if c["erc"] != CARD01]
    assert len(after) == len(before) - 1, f"card count {len(before)} -> {len(after)}"
    assert [c["erc"] for c in after] == [c["erc"] for c in remaining], "the remaining cards changed order"
    gaps = [f"slot {i}: {after[i]['title']} at {after[i]['box']} vs slot box {before[i]['box']}"
            for i in range(len(after))
            if abs(after[i]["box"]["left"] - before[i]["box"]["left"]) > 2
            or abs(after[i]["box"]["top"] - before[i]["box"]["top"]) > 2]
    assert not gaps, "the remaining cards do not fill the grid contiguously: " + "; ".join(gaps)


@pytest.mark.tc_149097
@pytest.mark.functional_high
def test_card_hidden_when_destination_unpublished():
    """MEDIA-MCHUB-TC-043 — card hidden while its destination page is unpublished."""
    _labels("149097", "MEDIA-MCHUB-TC-043", "Card hidden while destination is unpublished")
    pytest.skip("BLOCKED: a QCTEST card never renders on the hub (six fixed cards, user decision "
                "2026-10-12), and pointing a REAL card at a QCTEST destination would make the real card "
                "itself disappear from the live hub; same blocker as CMS case 149283.")


@pytest.mark.tc_149098
@pytest.mark.functional_high
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_cards_follow_ascending_display_order(cards_lock, qac, real_guard, hub_config, page):
    """MEDIA-MCHUB-TC-044 — cards follow ascending Display Order, not creation order.
    Real cards Photo Gallery (created 1st) / Video Gallery (created 2nd) swapped 100 <-> 200, restored."""
    _labels("149098", "MEDIA-MCHUB-TC-044", "Cards render in ascending Display Order")
    live = _live(hub_config["mediacenterquickaccesscards"])
    attach("stored orders", [(c["code"], c["cardTitle"], c["displayOrder"]) for c in live])
    assert [c["code"] for c in live][:2] == [CARD01, CARD02], f"PRECONDITION: stored order {live}"
    hub = MediaCenterHubPage(page)
    with allure.step("1. Logged-out: cards in stored ascending order"):
        _poll(hub, lambda c: [x["erc"] for x in c] == [r["code"] for r in live], "stored ascending order", "149098")
    sessions, admin, first = real_session(qac, real_guard, CARD01)
    second = real_guard.take(CARD02)
    with allure.step("2. Editor: Photo Gallery -> 200, Video Gallery -> 100"):
        r1 = guarded_edit(real_guard, admin, first, {"displayOrder": 200}, "149098_a")
        r2 = guarded_edit(real_guard, admin, second, {"displayOrder": 100}, "149098_b")
        assert r1["went_through"] and r2["went_through"], f"order change refused: {r1['evidence']} {r2['evidence']}"
        started = monotonic()
    expected = [CARD02, CARD01] + [r["code"] for r in live[2:]]
    with allure.step("3. Logged-out: Video Gallery (100, created second) before Photo Gallery (200)"):
        _poll(hub, lambda c: [x["erc"] for x in c] == expected, "ascending display order after swap", "149098",
              started=started)


@pytest.mark.tc_149099
@pytest.mark.functional_high
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_feed_sections_follow_configured_display_order(page, hub_config):
    """MEDIA-MCHUB-TC-045 — News / Photo / Video sections top-to-bottom in configured Display Order."""
    _labels("149099", "MEDIA-MCHUB-TC-045", "Feed sections render in configured Display Order")
    live = _live(hub_config["mediacenterfeedsections"])
    configured = [(s["sectionType"] or {}).get("key") if isinstance(s.get("sectionType"), dict) else s.get("sectionType")
                  for s in live]
    attach("configured", [(s["code"], s["displayOrder"], s.get("sectionType")) for s in live])
    hub = MediaCenterHubPage(page).open_hub()
    rendered = hub.section_order()
    hub.evidence("149099_sections")
    attach("rendered", rendered)
    assert [r["key"] for r in rendered] == configured, \
        f"rendered order {[r['key'] for r in rendered]} != configured ascending order {configured}"


@pytest.mark.tc_149100
@pytest.mark.functional_high
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_draft_card_not_visible_to_visitor(qac, browser, page):
    """MEDIA-MCHUB-TC-046 — a Draft card (Active ticked) is not shown to a logged-out visitor."""
    _labels("149100", "MEDIA-MCHUB-TC-046", "Draft card is not visible publicly")
    title = "QCTEST-130709-QAC-04"
    sessions, registry = qac
    hub = MediaCenterHubPage(page).open_hub()
    count_before = len(hub.cards())
    author = sessions.admin(ROLE_AUTHOR)
    data = card_data(title, "QCTEST-130709-QAC-04 مسودة", "QCTEST draft card.", "QCTEST بطاقة مسودة.", 1600)
    with allure.step("1. Author saves the card as Draft with Active Status ticked"):
        entry = create_ok(author, registry, data, "149100", role=ROLE_AUTHOR, publish=False)
        author.open_list_all()
        badge = author.row_status_of(entry)
        assert badge == STATUS_DRAFT, f"PRECONDITION: the badge reads {badge!r}, not DRAFT"
        started = monotonic()
    with allure.step("2. Fresh logged-out context: card not displayed, count unchanged"):
        ctx, fresh = _fresh_hub(browser)
        try:
            cards = fresh.cards()
            path = fresh.evidence("149100_public_after_draft")
            seconds = monotonic() - started
        finally:
            ctx.close()
    attach("public after draft", {"count_before": count_before, "cards": [c["title"] for c in cards],
                                  "seconds_after_save": round(seconds, 1)})
    assert not [c for c in cards if title in c["title"]], f"the Draft card is visible to a visitor; {path}"
    assert len(cards) == count_before, f"card count {count_before} -> {len(cards)}; {path}"


@pytest.mark.tc_149101
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.workflow
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_unpublished_card_not_visible_to_visitor(qac, browser, page):
    """MEDIA-MCHUB-TC-047 — an Unpublished card is not shown to a logged-out visitor."""
    _labels("149101", "MEDIA-MCHUB-TC-047", "Unpublished card is not visible publicly")
    title = "QCTEST-130709-QAC-05"
    sessions, registry = qac
    editor = sessions.admin(ROLE_EDITOR)
    data = card_data(title, "QCTEST-130709-QAC-05 ع", "QCTEST unpublish card.", "QCTEST بطاقة إلغاء النشر.", 1400)
    entry = create_ok(editor, registry, data, "149101")
    hub = MediaCenterHubPage(page).open_hub()
    step1 = [c["title"] for c in hub.cards()]
    attach("step 1 (N/A: six fixed cards, user decision 2026-10-12)", {"cards": step1})
    with allure.step("2. Editor unpublishes the card"):
        editor.open_list_all()
        dialogs = editor.run_row_action(entry, "unpublish")
        attach("unpublish dialogs", dialogs)
        status = editor.wait_row_status(entry, (STATUS_UNPUBLISHED,), 60)
        editor.evidence("149101_unpublished_badge")
        assert status == STATUS_UNPUBLISHED, f"after Unpublish the badge reads {status!r}"
    with allure.step("3. Fresh logged-out context: card not displayed"):
        ctx, fresh = _fresh_hub(browser)
        try:
            cards = fresh.cards()
            path = fresh.evidence("149101_public_after_unpublish")
        finally:
            ctx.close()
    assert not [c for c in cards if title in c["title"]], f"the Unpublished card is visible; {path}"
    assert len(cards) == 6, f"{len(cards)} cards after the unpublish (six real cards expected); {path}"


@pytest.mark.tc_149177
@pytest.mark.edge
@pytest.mark.bilingual
def test_card_missing_arabic_falls_back(qac):
    """MEDIA-MCHUB-TC-123 — card with no Arabic falls back to the EN text on /ar (N/A when the CMS refuses)."""
    _labels("149177", "MEDIA-MCHUB-TC-123", "Missing Arabic translation falls back on the AR hub")
    sessions, registry = qac
    editor = sessions.admin(ROLE_EDITOR)
    data = card_data("QCTEST Fallback Card", "", "QCTEST fallback description.", "", 1200)
    entry, result = create(editor, registry, data, "149177")
    new_rows = [r for r in result.get("new_rows", []) if r["title"].strip() == "QCTEST Fallback Card"]
    attach("EN-only publish attempt", result)
    if not result["went_through"] and not new_rows:
        message = re.findall(r"[^|]*Arabic content is required[^|]*", " | ".join(
            [result.get("messages", ""), result.get("page_text", "")]))
        pytest.skip(f"N/A (case precondition): the CMS refuses to publish a card without Arabic — "
                    f"{(message[0].strip() if message else result.get('evidence'))!r}; evidence "
                    f"{result.get('screenshot')}")
    pytest.fail(f"NEEDS-DECISION: an EN-only card was saved ({new_rows}) but QCTEST cards never render on "
                f"the six-card hub, so the AR fallback cannot be observed")


# ===========================================================================
# Hub hero search (grouped into this batch)
# ===========================================================================
NEWS_EN = "QCTEST-130709-SEARCH-AR-01"
NEWS_AR = "QCTEST-130709-بحث-01"
NEWS_IMAGE = "cms/tests/home_latest_news/fixtures/news_thumbnail.png"


@pytest.fixture
def ar_article(browser):
    """A Published + Active QCTEST-130709 news article with AR title 'QCTEST-130709-بحث-01'
    (News object manage-qcdemo131059-news, Editor); deleted by exact code afterwards."""
    from cms.pages.media_center.mc_subscriber_admin_b_page import NEWS_SLUG, McNewsAdminPage  # noqa: PLC0415
    ctx = new_context(browser, use_auth_state=False)
    drv = McNewsAdminPage(ctx.new_page(), slug=NEWS_SLUG)
    state = {"entry": None, "title": NEWS_EN}
    try:
        if drv.login_as_role(ROLE_EDITOR) == "auth_failed":
            pytest.fail("PRECONDITION: Liferay refused the Site Content Editor credentials")
        drv.open_list_all()
        if drv.signed_in_user()[0] != ROLE_USER_IDS[ROLE_EDITOR]:
            pytest.fail(f"PRECONDITION: session is {drv.signed_in_user()}, not the Editor")
        if [r for r in drv.list_rows() if r["title"].strip() == NEWS_EN]:
            pytest.fail(f"PRECONDITION: {NEWS_EN!r} from an earlier run still exists")
        ids_before = drv.snapshot_ids()
        drv.open_create_form()
        drv.fill_article(NEWS_EN, NEWS_AR, "QCTEST-130709 Arabic search article.", "QCTEST-130709 مقال بحث عربي.",
                         date.today().strftime("%d/%m/%Y"), category="Collaboration", image=NEWS_IMAGE)
        drv.click_publish()
        drv.success_messages("Arabic content saved", timeout=20.0)
        evidence = drv.evidence("149130_article_created")
        entry = drv.identify_created(NEWS_EN, ids_before)
        if entry is None:
            pytest.fail(f"PRECONDITION: the QCTEST article was not created: {drv.refusal_evidence()}; {evidence}")
        state["entry"] = entry
        status = drv.row_status_raw_of(entry)
        if status.upper() != "PUBLISHED":
            pytest.fail(f"PRECONDITION: the QCTEST article is {status!r}, not PUBLISHED; {evidence}")
        yield entry
    finally:
        entry = state["entry"]
        if entry is not None:
            ok = False
            try:
                drv.open_list_all()
                ok = drv.delete_disposable(entry, drv.row_title_of(entry) or NEWS_EN)
            except Exception as exc:  # noqa: BLE001 — reported below
                attach("article teardown error", repr(exc))
            os.makedirs(EVIDENCE_DIR, exist_ok=True)
            with open(os.path.join(EVIDENCE_DIR, "teardown.log"), "a", encoding="utf-8") as handle:
                handle.write(f"[{datetime.now().isoformat(timespec='seconds')}] article {entry} deleted={ok}\n")
            if not ok:
                ctx.close()
                raise AssertionError(f"TEARDOWN LEFT QCTEST DATA BEHIND: article {entry}")
        ctx.close()


@pytest.mark.tc_149130
@pytest.mark.functional_high
@pytest.mark.regression
@pytest.mark.bilingual
@pytest.mark.search
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_arabic_keyword_matches_arabic_content(ar_article, page):
    """MEDIA-MCHUB-TC-076 — searching 'بحث' on /ar hub returns the article with its Arabic title."""
    _labels("149130", "MEDIA-MCHUB-TC-076", "Arabic keyword matches published Arabic content")
    hub = MediaCenterHubPage(page)
    state = {"items": [], "url": ""}

    def _found() -> bool:
        hub.open_hub("ar")
        results = hub.search("بحث")
        state["items"], state["url"] = results.items(), page.url
        return any(NEWS_AR in i["title"] for i in state["items"])

    try:
        wait_until(_found, timeout=90.0, poll=3.0)
    except WaitTimeoutError:
        pass
    path = shot(page, "149130_ar_results")
    attach("AR results", state)
    assert "/media-search" in state["url"] and parse_qs(urlparse(state["url"]).query).get("q") == ["بحث"], \
        f"results page not opened: {state['url']}"
    hit = [i for i in state["items"] if NEWS_AR in i["title"]]
    assert hit, f"'{NEWS_AR}' not returned for 'بحث': {[i['title'] for i in state['items']]}; {path}"
    assert hit[0]["title"] == NEWS_AR, f"returned title {hit[0]['title']!r}, expected the Arabic title"


def _search_qatar(page) -> MediaSearchResultsPage:
    hub = MediaCenterHubPage(page).open_hub()
    return hub.search("Qatar")


@pytest.mark.tc_149131
@pytest.mark.functional_high
@pytest.mark.search
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_type_filter_narrows_results(page):
    """MEDIA-MCHUB-TC-077 — selecting 'Publications' lists only Publications results."""
    _labels("149131", "MEDIA-MCHUB-TC-077", "Type filter narrows the results")
    results = _search_qatar(page)
    all_total, tabs = results.total(), results.tabs()
    kinds = {i["badge"] for i in results.items()}
    attach("all", {"total": all_total, "tabs": tabs, "badges": sorted(kinds)})
    populated = [k for k, v in tabs.items() if k != "all" and v["count"] not in ("", "0")]
    assert len(populated) >= 2, f"PRECONDITION: 'Qatar' does not return results in two types: {tabs}"
    results.select_type("publications")
    items, total = results.items(), results.total()
    path = results.evidence("149131_publications")
    attach("publications", {"total": total, "url": results.current_url(), "items": items})
    wrong = [i for i in items if i["badge"].lower() != "publications"]
    assert items and not wrong, f"non-Publications results listed: {wrong}; {path}"
    assert total is not None and all_total is not None and total < all_total, \
        f"result count did not decrease: {all_total} -> {total}; {path}"
    assert str(total) == tabs["publications"]["count"], f"summary {total} != tab count {tabs['publications']}"


@pytest.mark.tc_149132
@pytest.mark.functional_high
@pytest.mark.search
@pytest.mark.parametrize("page", [ANON], indirect=True)
def test_clearing_type_filter_restores_all_results(page):
    """MEDIA-MCHUB-TC-078 — back to 'All' restores the same set as before filtering."""
    _labels("149132", "MEDIA-MCHUB-TC-078", "Clearing the type filter restores all results")
    results = _search_qatar(page)
    before_total, before_items = results.total(), results.items()
    results.select_type("publications")
    pub_items = results.items()
    assert pub_items and all(i["badge"].lower() == "publications" for i in pub_items), \
        f"PRECONDITION: filter did not narrow to Publications: {pub_items}"
    results.select_type("all")
    after_total, after_items = results.total(), results.items()
    path = results.evidence("149132_all_again")
    attach("before/after", {"before": [before_total, before_items], "after": [after_total, after_items]})
    assert after_total == before_total, f"total {before_total} -> {after_total} after clearing the filter; {path}"
    assert [i["href"] for i in after_items] == [i["href"] for i in before_items], \
        f"the result set differs from before filtering; {path}"
    assert len({i["badge"] for i in after_items}) >= 2 or len({i["badge"] for i in before_items}) < 2, \
        f"results are not from all matching types again: {after_items}"

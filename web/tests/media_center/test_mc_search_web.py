"""
web/tests/media_center/test_mc_search_web.py — PBI 130709 (Media Center Home
Page), Batch 3 FRONTEND, agent FE-SEARCH: the global media search (hero search
bar on the hub + the unified results page /web/qatar-chamber/media-search).

Every public read runs in a FRESH logged-out context. Cases that need CMS
state create disposable QCTEST-130709-SRCH-* records in the real search SOURCE
modules (News / Photo Album / Video Record / Podcast Episode / Publication)
as the Site Content Editor (156488) through Object Authoring, and delete them
afterwards through the guarded delete (captured id + code + exact title).
The service-unavailable cases use Playwright route interception of the search
API only (no real outage). No real content is edited or unpublished.

Wording-only mismatches (behaviour correct) are recorded as findings and the
test fails with a "WORDING-ONLY:" message, so a reviewer can map them to
"Passed + low wording bug" (rules §5) without the assertion being weakened.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date, datetime

import allure
import pytest

from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED, STATUS_UNPUBLISHED
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from web.pages.media_center.mc_search_page import (
    EVIDENCE_DIR,
    TYPE_ORDER,
    McHeroSearch,
    McResultDetailView,
    McSearchResultsPage,
    SearchEntry,
    SearchSourceAdmin,
    has_arabic,
)

FIXTURES = os.path.join(os.path.dirname(__file__), "search_fixtures")
IMAGE = os.path.join(FIXTURES, "qctest_srch_cover.jpg")
THUMB = os.path.join(FIXTURES, "qctest_srch_thumb.png")
AUDIO = os.path.join(FIXTURES, "qctest_srch_audio.mp3")
DOCUMENT = os.path.join(FIXTURES, "qctest_srch_document.pdf")
FINDINGS = os.path.join(EVIDENCE_DIR, "findings.jsonl")

DESKTOP = (1920, 1080)
EDITOR_ROLE = "Site Content Editor"
EDITOR_USER_ID = "156488"
PUBLIC_WAIT_S = 120.0     # publish -> public search (cms-profile budget + grace)
NEGATIVE_WATCH_S = 20.0   # keep re-querying a "must NOT appear" case this long

# ---- expected copy (cases / PBI) ------------------------------------------------
HERO_LABEL = "Media Center"
HERO_HEADLINE = "Your gateway to Qatar Chamber's official news"
HERO_PLACEHOLDER = "Search across all media – articles, photos, videos, podcasts…"
SEARCH_BUTTON = "Search"
MSG_NO_RESULTS_EN = "No results found for your search."
MSG_NO_RESULTS_AR = "لا توجد نتائج مطابقة لبحثك"
MSG_UNAVAILABLE_EN = "Search is temporarily unavailable. Please try again later."
MSG_UNAVAILABLE_AR = "البحث غير متاح مؤقتاً، يرجى المحاولة لاحقاً."
MIN_CHARS_RE = re.compile(r"(at least|minimum of)\s*(2|two)\s*char", re.I)
EXPECTED_LABEL = {"articles": "Articles/News", "photoAlbums": "Photo Albums", "videos": "Videos",
                  "podcast": "Podcast Episodes", "publications": "Publications"}
DETAIL_PATH = {"articles": "/news-detail", "photoAlbums": "/photo-album-details", "videos": "/video-details",
               "podcast": "/podcast-episode", "publications": "/publication-detail"}

COMMON = [pytest.mark.pbi_130709, pytest.mark.web, pytest.mark.media, pytest.mark.search,
          pytest.mark.xdist_group("mc_search_130709")]


def marks(*extra):
    def _wrap(fn):
        for m in COMMON + list(extra):
            fn = m(fn)
        return fn
    return _wrap


# =============================================================================
# Findings / outcome helpers
# =============================================================================
def record(tc: str, kind: str, **details) -> None:
    item = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(item, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def finish(tc: str, fails: list[str], wording: list[str] | None = None) -> None:
    """Behaviour failures first; wording-only differences last (distinct prefix)."""
    wording = wording or []
    if fails:
        record(tc, "FAILED", fails=fails, wording=wording)
        pytest.fail("\n".join(fails + [f"(also wording) {w}" for w in wording]))
    if wording:
        record(tc, "WORDING-ONLY", wording=wording)
        pytest.fail("WORDING-ONLY: " + "\n".join(wording))
    record(tc, "PASSED")


def needs_decision(tc: str, question: str, **details) -> None:
    record(tc, "NEEDS-DECISION", question=question, **details)
    pytest.skip(f"NEEDS-DECISION: {question}")


def label_wording(tc: str, items: list[dict]) -> list[str]:
    out = []
    for item in items:
        want = EXPECTED_LABEL.get(item["type"])
        if want and item["label"] != want:
            out.append(f"result {item['title']!r} ({item['type']}) is labelled {item['label']!r}; the case expects {want!r}")
    return sorted(set(out))


# =============================================================================
# Fixtures
# =============================================================================
@pytest.fixture
def visitors(browser):
    """Fresh logged-out contexts; every call is a new, cookie-less browser context."""
    contexts = []

    def _make(viewport: tuple = DESKTOP) -> McHeroSearch:
        ctx = new_context(browser, viewport=viewport, use_auth_state=False)
        contexts.append(ctx)
        return McHeroSearch(ctx.new_page())

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


def _hub(visitors, tc: str, locale: str = "en") -> McHeroSearch:
    hero = visitors().open_hub(locale)
    if hero.is_signed_in():
        pytest.fail(f"PRECONDITION ({tc}): the public context is signed in")
    return hero


class Seeder:
    """Editor session + registry of THIS test's disposable records."""

    def __init__(self, browser, tc: str):
        self.browser, self.tc = browser, tc
        self.ctx = None
        self.drv: SearchSourceAdmin | None = None
        self.created: list[tuple[SearchSourceAdmin, SearchEntry]] = []

    def driver(self, type_key: str) -> SearchSourceAdmin:
        if self.drv is None:
            self.ctx = new_context(self.browser, viewport=DESKTOP, use_auth_state=False)
            drv = SearchSourceAdmin(self.ctx.new_page(), type_key)
            outcome = drv.login_as_role(EDITOR_ROLE)
            if outcome != "ok":
                pytest.fail(f"PRECONDITION: Site Content Editor login -> {outcome}")
            self.drv = drv
        return self.drv if self.drv.type_key == type_key else self.drv.switch(type_key)

    def pinned(self, drv: SearchSourceAdmin) -> None:
        user_id = drv.signed_in_user()[0]
        if user_id != EDITOR_USER_ID:
            pytest.fail(f"PRECONDITION: the CMS session is userId {user_id!r}, not the Editor ({EDITOR_USER_ID})")

    def create(self, type_key: str, title: str, title_ar: str, draft: bool = False, **extra) -> tuple:
        drv = self.driver(type_key)
        with allure.step(f"Setup (Editor): {'save as Draft' if draft else 'publish'} {type_key} {title!r}"):
            drv.open_list_all()
            self.pinned(drv)
            stale = [r for r in drv.list_rows() if r["title"].strip() == title]
            if stale:
                pytest.fail(f"PRECONDITION: {title!r} already exists in manage-{drv.slug} (earlier run?): {stale}")
            ids_before = drv.snapshot_ids()
            data = {"title": title, "title_ar": title_ar, "date": date.today().strftime("%d/%m/%Y"),
                    "image": IMAGE, "thumb": THUMB, "audio": AUDIO, "document": DOCUMENT, "active": True, **extra}
            drv.open_create()
            self.pinned(drv)
            drv.fill_record(data)
            drv.click_save_as_draft() if draft else drv.click_publish()
            msgs = drv.success_messages("Arabic content saved", timeout=25.0)
            shot = drv.evidence(f"{self.tc}_setup_{type_key}_saved")
            entry = drv.identify_created(title, ids_before)
            if entry is None:
                pytest.fail(f"PRECONDITION: {title!r} was not created in manage-{drv.slug}: "
                            f"{drv.refusal_evidence()} {msgs}; {shot}")
            self.created.append((drv, entry))
            status = drv.row_status(entry)
            raw = " ".join(drv.row_status_raw(entry).split())
            record(self.tc, "setup (info)", type=type_key, entry=entry.__dict__, status=raw, messages=msgs)
            want = STATUS_DRAFT if draft else STATUS_PUBLISHED
            if status != want:
                pytest.fail(f"PRECONDITION: {title!r} is {raw!r} after the save, not {want}; {shot}")
            return drv, entry, raw

    def cleanup(self) -> list[dict]:
        left = []
        for drv, entry in self.created:
            ok = False
            try:
                ok = drv.delete_own_entry(entry)
            except Exception as exc:  # noqa: BLE001
                record(self.tc, "teardown error", entry=entry.__dict__, error=repr(exc))
            record(self.tc, "teardown (info)", entry=entry.__dict__, deleted=ok,
                   dialogs=getattr(drv, "last_delete_dialogs", []))
            if not ok:
                left.append(entry.__dict__)
                record(self.tc, "LEFTOVER", entry=entry.__dict__)
        if self.ctx is not None:
            try:
                self.ctx.close()
            except Exception:  # noqa: BLE001
                pass
        return left


@pytest.fixture
def seeder(browser, request):
    tc = next((m.name[3:] for m in request.node.iter_markers() if m.name.startswith("tc_")), "NO-TC")
    s = Seeder(browser, tc)
    yield s
    s.cleanup()


def poll_public(visitors, keyword: str, title: str, locale: str = "en", via: str = "click",
                timeout: float = PUBLIC_WAIT_S) -> tuple[McSearchResultsPage, dict | None]:
    """Hero search in a fresh logged-out context; re-queries until `title` is listed."""
    hero = visitors().open_hub(locale)
    if hero.is_signed_in():
        pytest.fail("PRECONDITION: the public context is signed in")
    results = hero.search(keyword, via=via)
    found = {"item": results.find_title(title)}
    if found["item"] is None:
        def _again() -> bool:
            results.open_query(keyword, locale)
            found["item"] = results.find_title(title)
            return found["item"] is not None
        try:
            wait_until(_again, timeout=timeout, poll=5.0)
        except WaitTimeoutError:
            pass
    return results, found["item"]


def watch_absent(visitors, keyword: str, title: str, locale: str = "en",
                 watch_s: float = NEGATIVE_WATCH_S) -> tuple[McSearchResultsPage, dict | None, dict]:
    """Hero search in a fresh logged-out context, then re-queries for `watch_s`;
    returns the first sighting of `title` (None = never listed) and the last state."""
    hero = visitors().open_hub(locale)
    if hero.is_signed_in():
        pytest.fail("PRECONDITION: the public context is signed in")
    results = hero.search(keyword)
    seen = {"item": results.find_title(title)}

    def _sighted() -> bool:
        results.open_query(keyword, locale)
        seen["item"] = results.find_title(title)
        return seen["item"] is not None

    if seen["item"] is None:
        try:
            wait_until(_sighted, timeout=watch_s, poll=5.0)
        except WaitTimeoutError:
            pass
    return results, seen["item"], results.state()


def wait_gone(visitors, keyword: str, title: str, timeout: float = PUBLIC_WAIT_S):
    """Fresh logged-out contexts until `title` is no longer listed for `keyword`."""
    last = {}

    def _gone() -> bool:
        hero = visitors().open_hub("en")
        results = hero.search(keyword)
        last["results"] = results
        last["item"] = results.find_title(title)
        return last["item"] is None

    try:
        wait_until(_gone, timeout=timeout, poll=5.0)
    except WaitTimeoutError:
        pass
    return last.get("results"), last.get("item")


# =============================================================================
# Hero search bar (UI)
# =============================================================================
@marks(pytest.mark.ui, pytest.mark.tc_149056)
def test_149056_hero_label_breadcrumb_headline_and_search_bar(visitors):
    """MEDIA-MCHUB-TC-002: the hero shows the label 'Media Center', the breadcrumb
    Home › Media Center, the headline, the description and the search bar with its
    placeholder and Search button (EN, logged out)."""
    tc, fails, wording = "149056", [], []
    hero = _hub(visitors, tc)
    facts = hero.hero_facts()
    shot = hero.evidence(f"{tc}_hero_en", full_page=False)
    record(tc, "hero facts (info)", facts=facts, screenshot=shot)

    with allure.step("Hero banner over the section background image"):
        if "url(" not in facts["bg_image"] or facts["bg_loaded"] != "true":
            fails.append(f"hero background image not shown: {facts['bg_image'][:120]!r} loaded={facts['bg_loaded']!r}; {shot}")
    with allure.step("Label reads exactly 'Media Center'"):
        if not facts["page_label_visible"] or facts["page_label"] != HERO_LABEL:
            fails.append(f"page label reads {facts['page_label']!r} (visible={facts['page_label_visible']}); expected {HERO_LABEL!r}")
    with allure.step("Breadcrumb Home › Media Center; Home is a link, Media Center is the current item"):
        crumbs = facts["crumbs"]
        if len(crumbs) != 2:
            fails.append(f"breadcrumb has {len(crumbs)} items {crumbs}; expected Home › Media Center")
        else:
            home, current = crumbs
            if home["text"] != "Home" or home["tag"] != "A" or not home["href"]:
                fails.append(f"first crumb is {home}; expected a 'Home' link")
            if current["text"] != "Media Center" or current["tag"] == "A" or current["current"] != "page":
                fails.append(f"last crumb is {current}; expected the current, non-link 'Media Center'")
            if facts["crumb_separators"] < 1:
                fails.append("no separator between the breadcrumb items")
    with allure.step("Headline reads exactly the case text"):
        if facts["headline"] != HERO_HEADLINE:
            if facts["headline"].replace("’", "'") == HERO_HEADLINE:
                wording.append(f"headline uses a typographic apostrophe: {facts['headline']!r} vs {HERO_HEADLINE!r}")
            else:
                fails.append(f"headline reads {facts['headline']!r}; expected {HERO_HEADLINE!r}")
    with allure.step("Supporting description is displayed"):
        if not facts["description_visible"] or not facts["description"]:
            fails.append(f"no supporting description shown ({facts['description']!r})")
    with allure.step("Search input placeholder and 'Search' button"):
        if not facts["input_visible"] or not facts["button_visible"]:
            fails.append(f"search bar not displayed (input={facts['input_visible']}, button={facts['button_visible']})")
        if facts["button_label"] != SEARCH_BUTTON:
            fails.append(f"search button reads {facts['button_label']!r}; expected {SEARCH_BUTTON!r}")
        if facts["placeholder"] != HERO_PLACEHOLDER:
            if facts["placeholder"].replace(" - ", " – ") == HERO_PLACEHOLDER:
                wording.append(f"placeholder uses a hyphen '-' where the case has an en dash '–': "
                               f"{facts['placeholder']!r} vs {HERO_PLACEHOLDER!r}; {shot}")
            else:
                fails.append(f"placeholder reads {facts['placeholder']!r}; expected {HERO_PLACEHOLDER!r}; {shot}")
    finish(tc, fails, wording)


@marks(pytest.mark.ui, pytest.mark.tc_149065)
def test_149065_arabic_hero_search_placeholder_rtl_input_and_button(visitors):
    """MEDIA-MCHUB-TC-011: in Arabic the hero search shows an Arabic placeholder,
    takes Arabic input right-aligned (RTL) and the button label is Arabic on the
    left end of the field."""
    tc, fails = "149065", []
    hero = _hub(visitors, tc, "ar")
    facts = hero.hero_facts()
    with allure.step("Arabic placeholder"):
        if not facts["placeholder"] or not has_arabic(facts["placeholder"]):
            fails.append(f"placeholder is {facts['placeholder']!r}; expected non-empty Arabic text")
    with allure.step("Type 'غرفة' — RTL, right-aligned, caret from the right"):
        hero.type_keyword("غرفة")
        layout = hero.input_layout()
        shot = hero.evidence(f"{tc}_ar_input", full_page=False)
        record(tc, "layout (info)", facts=facts, layout=layout, screenshot=shot)
        if hero.input_value() != "غرفة":
            fails.append(f"field holds {hero.input_value()!r}, not 'غرفة'")
        if layout["direction"] != "rtl":
            fails.append(f"field direction is {layout['direction']!r}; expected rtl; {shot}")
        if layout["text_align"] not in ("right", "start"):
            fails.append(f"field text-align is {layout['text_align']!r}; expected right/start under RTL; {shot}")
    with allure.step("Button label Arabic, on the left end of the field"):
        if not has_arabic(facts["button_label"]):
            fails.append(f"button label is {facts['button_label']!r}; expected Arabic")
        if not layout["button_right"] <= layout["input_left"] + (layout["input_right"] - layout["input_left"]) / 2:
            fails.append(f"button is not on the left end (button {layout['button_left']:.0f}-{layout['button_right']:.0f}, "
                         f"input {layout['input_left']:.0f}-{layout['input_right']:.0f}); {shot}")
    if facts["html_dir"] != "rtl":
        fails.append(f"the Arabic page renders dir={facts['html_dir']!r}")
    finish(tc, fails)


# =============================================================================
# Results page: labels, filter, RTL
# =============================================================================
@marks(pytest.mark.ui, pytest.mark.tc_149068)
def test_149068_results_labelled_by_type_with_type_filter(visitors):
    """MEDIA-MCHUB-TC-014: unified results label every result with its content type
    and offer a filter listing the five content types."""
    tc, fails, wording = "149068", [], []
    results = _hub(visitors, tc).search("Qatar", via="click")
    st = results.state()
    shot = results.evidence(f"{tc}_results_qatar")
    record(tc, "results (info)", state=st, screenshot=shot)
    with allure.step("Unified results page opens"):
        if "/media-search" not in st["url"] or not st["items"]:
            fails.append(f"no unified results for 'Qatar' ({st['url']}, {len(st['items'])} items); {shot}")
    with allure.step("Every result shows a content-type label"):
        unlabelled = [i for i in st["items"] if not i["label"] or i["type"] not in EXPECTED_LABEL]
        if unlabelled:
            fails.append(f"results without a content-type label: {unlabelled}; {shot}")
        wording += label_wording(tc, st["items"])
    with allure.step("Content-type filter lists the five types"):
        tab_types = [t["type"] for t in st["tabs"]]
        missing = [t for t in TYPE_ORDER if t not in tab_types]
        if missing:
            fails.append(f"type filter lacks {missing}; offers {tab_types}; {shot}")
        for tab in st["tabs"]:
            want = EXPECTED_LABEL.get(tab["type"])
            if want and tab["label"] != want:
                wording.append(f"filter option {tab['type']} reads {tab['label']!r}; the case expects {want!r}")
    finish(tc, fails, wording)


@marks(pytest.mark.ui, pytest.mark.tc_149069)
def test_149069_arabic_results_rtl_with_arabic_labels(visitors, seeder):
    """MEDIA-MCHUB-TC-015: an Arabic search renders the results right-to-left with
    Arabic titles, type labels and filter options (QCTEST-130709-بحث-01)."""
    tc, fails = "149069", []
    title_en, title_ar = "QCTEST-130709-SRCH-AR01", "QCTEST-130709-بحث-01"
    seeder.create("articles", title_en, title_ar, description="QCTEST-130709 search RTL article.",
                  description_ar="QCTEST-130709 مقال اختبار البحث.")
    with allure.step("Open /ar Media Center, type 'بحث', press Enter"):
        results, item = poll_public(visitors, "بحث", title_ar, locale="ar", via="enter")
        st = results.state()
        shot = results.evidence(f"{tc}_ar_results")
        record(tc, "results (info)", state=st, item=item, screenshot=shot)
    with allure.step("Results page under /ar with dir=rtl"):
        if "/ar/" not in st["url"] or "/media-search" not in st["url"]:
            fails.append(f"results URL is {st['url']}; expected the /ar media-search page")
        if st["html_dir"] != "rtl" or st["root_direction"] != "rtl":
            fails.append(f"results page dir={st['html_dir']!r} / section direction={st['root_direction']!r}; expected rtl")
    with allure.step("Titles, labels and filter options Arabic and right-aligned"):
        if item is None:
            fails.append(f"the published Arabic article {title_ar!r} is not returned for 'بحث' within {PUBLIC_WAIT_S:.0f}s; {shot}")
        else:
            if item["title_direction"] != "rtl" or item["title_align"] not in ("right", "start"):
                fails.append(f"result title renders direction={item['title_direction']!r} align={item['title_align']!r}")
        not_ar = [i for i in st["items"] if not has_arabic(i["label"])]
        if not_ar:
            fails.append(f"type labels not in Arabic: {[i['label'] for i in not_ar]}")
        titles_not_ar = [i["title"] for i in st["items"] if not has_arabic(i["title"])]
        if titles_not_ar:
            fails.append(f"result titles not in Arabic on the /ar page: {titles_not_ar}")
        tabs_not_ar = [t["label"] for t in st["tabs"] if not has_arabic(t["label"])]
        if tabs_not_ar:
            fails.append(f"filter options not in Arabic: {tabs_not_ar}")
    finish(tc, fails)


# =============================================================================
# Keyboard
# =============================================================================
@marks(pytest.mark.ui, pytest.mark.tc_149071)
def test_149071_keyboard_reaches_search_and_cards_with_focus_indicator(visitors):
    """MEDIA-MCHUB-TC-017: Tab reaches the hero search field, the Search button and
    the six quick-access cards (visible focus indicator, count widgets skipped);
    Enter on 'Photo Gallery' opens its configured destination."""
    tc, fails = "149071", []
    hero = _hub(visitors, tc)
    cards = hero.quick_access_cards()
    trail = hero.tab_trace(max_presses=45)
    shot = hero.evidence(f"{tc}_focus_trail", full_page=False)
    record(tc, "focus trail (info)", trail=trail, cards=cards, screenshot=shot)
    idx_input = next((i for i, f in enumerate(trail) if "qc-mc-hero-input" in f.get("cls", "")), -1)
    with allure.step("Header/menu links first, then the search field, then the Search button"):
        if idx_input < 0:
            fails.append(f"Tab never reached the hero search field in {len(trail)} presses; {shot}")
        else:
            header_before = [f for f in trail[:idx_input] if "qc-nav-link" in f.get("cls", "")]
            if not header_before:
                fails.append("the search field was reached before the global header/menu links")
            nxt = trail[idx_input + 1] if idx_input + 1 < len(trail) else {}
            if "qc-mc-hero-btn" not in nxt.get("cls", ""):
                fails.append(f"after the search field focus went to {nxt}; expected the Search button")
            for f in (trail[idx_input], nxt):
                if f and not f.get("indicator"):
                    fails.append(f"no visible focus indicator on {f.get('cls')} (outline {f.get('outline')!r})")
    with allure.step("Six quick-access cards in visual order; count widgets not focusable"):
        card_trail = [f for f in trail if f.get("is_qa_card")]
        visual = [c["href"] for c in sorted(cards, key=lambda c: (round(c["top"]), c["left"]))]
        if len(cards) != 6:
            fails.append(f"{len(cards)} quick-access cards rendered; expected 6")
        if [f["href"] for f in card_trail] != visual:
            fails.append(f"card focus order {[f['href'] for f in card_trail]} differs from visual order {visual}")
        no_ring = [f["href"] for f in card_trail if not f.get("indicator")]
        if no_ring:
            fails.append(f"cards without a visible focus indicator: {no_ring}")
        if any(f.get("in_counts") for f in trail) or hero.counts_focusables() > 0:
            fails.append(f"count widgets are focusable ({hero.counts_focusables()} focusable elements)")
    with allure.step("Enter on the 'Photo Gallery' card opens its destination"):
        photo = next((c for c in cards if c["title"] == "Photo Gallery"), None)
        if photo is None:
            fails.append(f"no 'Photo Gallery' card among {[c['title'] for c in cards]}")
        else:
            hero.reset_focus_to_top()
            reached = hero.press_tab_until_focused(f"a.qc-mc-qa-card[href='{photo['href']}']", max_presses=45)
            if not reached:
                fails.append("Tab never focused the Photo Gallery card")
            else:
                hero.press_key("Enter")
                try:
                    hero.wait_for_url(re.compile(re.escape(photo["href"]) + r"(\?|#|$)"), timeout=30000)
                except Exception:  # noqa: BLE001 — asserted below
                    pass
                shot2 = hero.evidence(f"{tc}_photo_gallery_opened", full_page=False)
                if not hero.page.url.split("?")[0].endswith(photo["href"]):
                    fails.append(f"Enter on Photo Gallery landed on {hero.page.url}; expected {photo['href']}; {shot2}")
    finish(tc, fails)


# =============================================================================
# Search execution
# =============================================================================
@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat, pytest.mark.tc_149121)
def test_149121_search_click_returns_items_across_types(visitors):
    """MEDIA-MCHUB-TC-067: clicking Search with 'Qatar' opens the unified results
    page listing published items from more than one content type, each labelled."""
    tc, fails, wording = "149121", [], []
    hero = _hub(visitors, tc)
    hero.type_keyword("Qatar")
    if hero.input_value() != "Qatar":
        fails.append(f"keyword not entered ({hero.input_value()!r})")
    hero.click_search()
    hero.wait_for_url(re.compile(r"/media-search"), timeout=30000)
    results = McSearchResultsPage(hero.page).wait_ready()
    st = results.state()
    shot = results.evidence(f"{tc}_results_qatar")
    record(tc, "results (info)", state=st, screenshot=shot)
    types_listed = {i["type"] for i in st["items"]}
    types_counted = {t["type"] for t in st["tabs"] if t["type"] != "all" and t["count"] not in ("", "0")}
    if "q=Qatar" not in st["url"]:
        fails.append(f"results URL {st['url']} does not carry the keyword")
    if len(types_listed) < 2:
        fails.append(f"results list only {sorted(types_listed)} (type counts {sorted(types_counted)}); "
                     f"expected more than one content type; {shot}")
    unlabelled = [i["title"] for i in st["items"] if not i["label"]]
    if unlabelled:
        fails.append(f"results without a type label: {unlabelled}")
    wording += label_wording(tc, st["items"])
    finish(tc, fails, wording)


@marks(pytest.mark.functional_high, pytest.mark.tc_149122)
def test_149122_enter_submits_like_clicking_search(visitors):
    """MEDIA-MCHUB-TC-068: pressing Enter in the hero search submits the search
    (same results as clicking Search)."""
    tc, fails = "149122", []
    enter_page = _hub(visitors, tc).search("Chamber", via="enter")
    by_enter = enter_page.state()
    shot = enter_page.evidence(f"{tc}_results_enter")
    by_click = _hub(visitors, tc).search("Chamber", via="click").state()
    record(tc, "states (info)", enter=by_enter, click=by_click, screenshot=shot)
    if "/media-search" not in by_enter["url"] or "q=Chamber" not in by_enter["url"]:
        fails.append(f"Enter did not open the results page for 'Chamber' ({by_enter['url']})")
    if not by_enter["items"]:
        fails.append(f"Enter search lists no results for 'Chamber' (summary {by_enter['summary']!r})")
    if (by_enter["summary"], [i["href"] for i in by_enter["items"]]) != (by_click["summary"], [i["href"] for i in by_click["items"]]):
        fails.append(f"Enter and click differ: {by_enter['summary']!r} vs {by_click['summary']!r}; {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_low, pytest.mark.tc_149155)
def test_149155_two_character_keyword_triggers_search(visitors):
    """MEDIA-MCHUB-TC-101: a two-character keyword ('QC') opens the unified results page."""
    tc, fails = "149155", []
    results = _hub(visitors, tc).search("QC", via="click")
    st = results.state()
    shot = results.evidence(f"{tc}_results_qc")
    record(tc, "state (info)", state=st, screenshot=shot)
    if "q=QC" not in st["url"]:
        fails.append(f"results URL {st['url']} is not the search for 'QC'")
    if not st["items"] and not st["empty_shown"]:
        fails.append(f"neither results nor the no-results message for 'QC' (hint={st['hint_shown']}); {shot}")
    finish(tc, fails)


# =============================================================================
# Per-type disposable records
# =============================================================================
TYPE_CASES = [
    pytest.param("articles", "QCTEST-130709-SRCH-ART", marks=pytest.mark.tc_149123, id="149123-articles"),
    pytest.param("videos", "QCTEST-130709-SRCH-VID", marks=pytest.mark.tc_149125, id="149125-videos"),
    pytest.param("podcast", "QCTEST-130709-SRCH-POD", marks=pytest.mark.tc_149126, id="149126-podcast"),
    pytest.param("publications", "QCTEST-130709-SRCH-PUB", marks=pytest.mark.tc_149127, id="149127-publications"),
]
TYPE_TC = {"articles": "149123", "photoAlbums": "149124", "videos": "149125", "podcast": "149126",
           "publications": "149127"}


@marks(pytest.mark.functional_high)
@pytest.mark.parametrize("type_key,title", TYPE_CASES)
def test_149123_7_published_item_found_by_title_and_labelled(visitors, seeder, type_key, title):
    """MEDIA-MCHUB-TC-069..073: a published (Active) item of each content type is
    returned by a title-keyword search and labelled with its content type."""
    tc, fails, wording = TYPE_TC[type_key], [], []
    seeder.tc = tc
    seeder.create(type_key, title, title.replace("QCTEST-130709-SRCH", "QCTEST-130709-بحث"))
    results, item = poll_public(visitors, title, title)
    st = results.state()
    shot = results.evidence(f"{tc}_results_{type_key}")
    record(tc, "results (info)", state=st, item=item, screenshot=shot)
    if "/media-search" not in st["url"]:
        fails.append(f"results page did not open ({st['url']})")
    if item is None:
        fails.append(f"{title!r} is not returned within {PUBLIC_WAIT_S:.0f}s (items {[i['title'] for i in st['items']]}, "
                     f"empty={st['empty_shown']}); {shot}")
    else:
        if item["type"] != type_key:
            fails.append(f"{title!r} is typed {item['type']!r}; expected {type_key!r}")
        if not item["label"]:
            fails.append(f"{title!r} carries no content-type label")
        elif item["label"] != EXPECTED_LABEL[type_key]:
            wording.append(f"{title!r} is labelled {item['label']!r}; the case expects {EXPECTED_LABEL[type_key]!r}")
    finish(tc, fails, wording)


@marks(pytest.mark.functional_high, pytest.mark.tc_149128)
def test_149128_search_matches_description_only_keyword(visitors, seeder):
    """MEDIA-MCHUB-TC-074: a keyword present only in the description/excerpt
    ('zephyrmchub') returns QCTEST-130709-SRCH-DSC, labelled Articles/News."""
    tc, fails, wording = "149128", [], []
    title = "QCTEST-130709-SRCH-DSC"
    seeder.create("articles", title, "QCTEST-130709-بحث-DSC",
                  description="QCTEST-130709 excerpt carrying the unique word zephyrmchub for search.",
                  description_ar="QCTEST-130709 نص zephyrmchub")
    results, item = poll_public(visitors, "zephyrmchub", title)
    st = results.state()
    shot = results.evidence(f"{tc}_results_desc_keyword")
    record(tc, "results (info)", state=st, item=item, screenshot=shot)
    if item is None:
        fails.append(f"{title!r} (keyword only in its description) is not returned for 'zephyrmchub' within "
                     f"{PUBLIC_WAIT_S:.0f}s (items {[i['title'] for i in st['items']]}, empty={st['empty_shown']}); {shot}")
    else:
        if item["type"] != "articles":
            fails.append(f"{title!r} is typed {item['type']!r}; expected articles")
        elif item["label"] != EXPECTED_LABEL["articles"]:
            wording.append(f"{title!r} is labelled {item['label']!r}; the case expects 'Articles/News'")
    finish(tc, fails, wording)


@marks(pytest.mark.functional_high, pytest.mark.tc_149129)
def test_149129_search_matches_category_name(visitors, seeder):
    """MEDIA-MCHUB-TC-075: searching an exact category name returns
    QCTEST-130709-SRCH-CAT (assigned that category, word absent from title/excerpt)."""
    tc, fails, wording = "149129", [], []
    title, category = "QCTEST-130709-SRCH-CAT", "Collaboration"
    seeder.create("articles", title, "QCTEST-130709-بحث-CAT", category=category,
                  description="QCTEST-130709 category search article.", description_ar="QCTEST-130709 مقال تصنيف.")
    record(tc, "category (info)", category=category)
    results, item = poll_public(visitors, category, title)
    st = results.state()
    shot = results.evidence(f"{tc}_results_category")
    record(tc, "results (info)", state={k: v for k, v in st.items() if k != "items"}, item=item, screenshot=shot)
    if item is None:
        fails.append(f"{title!r} (category {category!r}, word not in title/excerpt) is not returned for {category!r} "
                     f"within {PUBLIC_WAIT_S:.0f}s (summary {st['summary']!r}); {shot}")
    else:
        if item["type"] != "articles":
            fails.append(f"{title!r} is typed {item['type']!r}; expected articles")
        elif item["label"] != EXPECTED_LABEL["articles"]:
            wording.append(f"{title!r} is labelled {item['label']!r}; the case expects 'Articles/News'")
    finish(tc, fails, wording)


# =============================================================================
# Result click-through
# =============================================================================
@marks(pytest.mark.functional_high, pytest.mark.tc_149133)
def test_149133_clicking_result_opens_its_detail_page(visitors):
    """MEDIA-MCHUB-TC-079: clicking the first 'Qatar' result opens that item's
    detail page (its content type) showing the same title."""
    tc, fails = "149133", []
    results = _hub(visitors, tc).search("Qatar")
    st = results.state()
    if not st["items"]:
        pytest.fail(f"PRECONDITION: no results for 'Qatar' to click ({st['summary']!r})")
    first = st["items"][0]
    record(tc, "first result (info)", first=first)
    href = results.open_result(0)
    detail = McResultDetailView(results.page)
    shown = detail.wait_heading(first["title"])
    shot = detail.evidence(f"{tc}_detail_page")
    record(tc, "detail (info)", url=detail.page.url, headings=detail.headings(), screenshot=shot)
    if DETAIL_PATH[first["type"]] not in detail.page.url:
        fails.append(f"{first['type']} result {first['title']!r} opened {detail.page.url}; expected a "
                     f"{DETAIL_PATH[first['type']]} page (href {href})")
    if not shown:
        fails.append(f"the detail page does not show the title {first['title']!r} (headings {detail.headings()[:6]}); {shot}")
    finish(tc, fails)


# =============================================================================
# Unpublished / Draft never returned
# =============================================================================
@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.tc_149134)
def test_149134_unpublished_item_not_returned(visitors, seeder):
    """MEDIA-MCHUB-TC-080: QCTEST-130709-SRCH-UNP is returned while published; after
    the Editor unpublishes it (badge UNPUBLISHED) it is no longer returned and
    'No results found for your search.' is shown."""
    tc, fails, wording = "149134", [], []
    title = "QCTEST-130709-SRCH-UNP"
    drv, entry, _ = seeder.create("articles", title, "QCTEST-130709-بحث-UNP",
                                  description="QCTEST-130709 unpublish search article.",
                                  description_ar="QCTEST-130709 مقال إلغاء النشر.")
    with allure.step("1. Before unpublishing — the article is returned (logged out)"):
        results, item = poll_public(visitors, title, title)
        shot1 = results.evidence(f"{tc}_step1_returned")
        if item is None:
            pytest.fail(f"PRECONDITION: the published article is never returned for {title!r}; {shot1}")
    with allure.step("2. As Editor unpublish the article — badge UNPUBLISHED"):
        drv.open_list_all()
        seeder.pinned(drv)
        dialogs = drv.run_row_action(entry, "unpublish")
        status = drv.wait_status(entry, (STATUS_UNPUBLISHED,), timeout=60.0)
        raw = " ".join(drv.row_status_raw(entry).split())
        shot2 = drv.evidence(f"{tc}_step2_unpublished")
        record(tc, "unpublish (info)", dialogs=dialogs, status=raw)
        if status != STATUS_UNPUBLISHED or raw.upper() != "UNPUBLISHED":
            pytest.fail(f"PRECONDITION: badge reads {raw!r} after Unpublish, not UNPUBLISHED; {shot2}")
    with allure.step("3. Fresh logged-out search — not returned, no-results message"):
        results3, still = wait_gone(visitors, title, title)
        st = results3.state()
        shot3 = results3.evidence(f"{tc}_step3_not_returned")
        record(tc, "after unpublish (info)", state=st, still=still, screenshot=shot3)
        if still is not None:
            fails.append(f"the UNPUBLISHED article is still returned for {title!r} after {PUBLIC_WAIT_S:.0f}s; {shot3}")
        elif st["items"]:
            fails.append(f"results still listed for {title!r}: {[i['title'] for i in st['items']]}")
        if not st["empty_shown"]:
            fails.append(f"no no-results message shown (summary {st['summary']!r}); {shot3}")
        elif st["empty_text"] != MSG_NO_RESULTS_EN:
            wording.append(f"no-results message reads {st['empty_text']!r}; expected {MSG_NO_RESULTS_EN!r}")
    finish(tc, fails, wording)


@marks(pytest.mark.functional_high, pytest.mark.tc_149135)
def test_149135_draft_item_not_returned(visitors, seeder):
    """MEDIA-MCHUB-TC-081: QCTEST-130709-SRCH-DRF saved as Draft (Active ticked,
    badge DRAFT) is not returned; 'No results found for your search.' is shown."""
    tc, fails, wording = "149135", [], []
    title = "QCTEST-130709-SRCH-DRF"
    _, _, raw = seeder.create("articles", title, "QCTEST-130709-بحث-DRF", draft=True,
                              description="QCTEST-130709 draft search article.",
                              description_ar="QCTEST-130709 مقال مسودة.")
    if raw.upper() != "DRAFT":
        pytest.fail(f"PRECONDITION: badge reads {raw!r}, not DRAFT")
    results, seen, st = watch_absent(visitors, title, title)
    shot = results.evidence(f"{tc}_draft_not_returned")
    record(tc, "draft search (info)", state=st, seen=seen, screenshot=shot)
    if seen is not None:
        fails.append(f"the DRAFT article {title!r} is returned to a logged-out visitor; {shot}")
    elif st["items"]:
        fails.append(f"results listed for {title!r}: {[i['title'] for i in st['items']]}")
    if not st["empty_shown"]:
        fails.append(f"no no-results message shown (summary {st['summary']!r}); {shot}")
    elif st["empty_text"] != MSG_NO_RESULTS_EN:
        wording.append(f"no-results message reads {st['empty_text']!r}; expected {MSG_NO_RESULTS_EN!r}")
    finish(tc, fails, wording)


# =============================================================================
# No results
# =============================================================================
@pytest.mark.parametrize("locale,keyword,expected", [
    pytest.param("en", "xqzvmchub404", MSG_NO_RESULTS_EN, marks=pytest.mark.tc_149136, id="149136-en"),
    pytest.param("ar", "ظظظغغغ", MSG_NO_RESULTS_AR, marks=pytest.mark.tc_149137, id="149137-ar"),
])
@marks(pytest.mark.functional_high)
def test_149136_7_no_results_message(visitors, locale, keyword, expected):
    """MEDIA-MCHUB-TC-082 / TC-083: a search with no matches shows exactly
    'No results found for your search.' (EN) / 'لا توجد نتائج مطابقة لبحثك' (AR)
    and lists no items."""
    tc = "149136" if locale == "en" else "149137"
    fails, wording = [], []
    results = _hub(visitors, tc, locale).search(keyword)
    st = results.state()
    shot = results.evidence(f"{tc}_no_results_{locale}")
    record(tc, "state (info)", state=st, screenshot=shot)
    if "/media-search" not in st["url"]:
        fails.append(f"results page did not open ({st['url']})")
    if locale == "ar" and (st["html_dir"] != "rtl" or st["root_direction"] != "rtl"):
        fails.append(f"Arabic results page renders dir={st['html_dir']!r}/{st['root_direction']!r}; expected rtl")
    if st["items"]:
        fails.append(f"items listed for {keyword!r}: {[i['title'] for i in st['items']]}")
    if not st["empty_shown"]:
        fails.append(f"no no-results message (error={st['error_shown']}, summary {st['summary']!r}); {shot}")
    elif st["empty_text"] != expected:
        wording.append(f"no-results message reads {st['empty_text']!r}; expected {expected!r}")
    finish(tc, fails, wording)


# =============================================================================
# Minimum length (hero)
# =============================================================================
@marks(pytest.mark.functional_low, pytest.mark.tc_149153)
def test_149153_empty_keyword_does_not_search_and_shows_indication(visitors):
    """MEDIA-MCHUB-TC-099: Search with an empty field does not run a search (URL
    unchanged) and indicates that at least two characters are required."""
    tc, fails = "149153", []
    hero = _hub(visitors, tc)
    nav = hero.submit_expecting_no_navigation("", via="click")
    hint = hero.hint()
    shot = hero.evidence(f"{tc}_empty_submit", full_page=False)
    record(tc, "state (info)", nav=nav, hint=hint, screenshot=shot)
    if nav["url_after"] != nav["url_before"] or nav["search_requests"]:
        fails.append(f"an empty keyword ran a search: {nav}")
    if not hint["shown"] or not MIN_CHARS_RE.search(hint["text"]):
        fails.append(f"no 'at least two characters' indication after submitting an empty field "
                     f"(hint shown={hint['shown']}, text={hint['text']!r}, aria-invalid={hint['aria_invalid']!r}); {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_low, pytest.mark.tc_149154)
def test_149154_one_character_keyword_does_not_search(visitors):
    """MEDIA-MCHUB-TC-100: 'Q' + Enter and 'Q' + Search do not search; the 'at
    least two characters' indication is shown and remains."""
    tc, fails = "149154", []
    hero = _hub(visitors, tc)
    with allure.step("Type 'Q' and press Enter"):
        nav1 = hero.submit_expecting_no_navigation("Q", via="enter")
        hint1 = hero.hint()
        shot1 = hero.evidence(f"{tc}_q_enter", full_page=False)
    with allure.step("Click 'Search'"):
        nav2 = hero.submit_expecting_no_navigation("Q", via="click")
        hint2 = hero.hint()
        shot2 = hero.evidence(f"{tc}_q_click", full_page=False)
    record(tc, "state (info)", enter=nav1, hint_enter=hint1, click=nav2, hint_click=hint2)
    for step, nav, hint, shot in (("Enter", nav1, hint1, shot1), ("Search click", nav2, hint2, shot2)):
        if nav["url_after"] != nav["url_before"] or nav["search_requests"]:
            fails.append(f"{step}: a one-character keyword ran a search: {nav}")
        if not hint["shown"] or not MIN_CHARS_RE.search(hint["text"]):
            fails.append(f"{step}: no 'at least two characters' indication (shown={hint['shown']}, "
                         f"text={hint['text']!r}); {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_low, pytest.mark.tc_149156)
def test_149156_whitespace_keyword_does_not_search(visitors):
    """MEDIA-MCHUB-TC-102: two spaces + Search do not search; the 'at least two
    characters' indication is shown."""
    tc, fails = "149156", []
    hero = _hub(visitors, tc)
    nav = hero.submit_expecting_no_navigation("  ", via="click")
    hint = hero.hint()
    shot = hero.evidence(f"{tc}_whitespace_submit", full_page=False)
    record(tc, "state (info)", nav=nav, hint=hint, screenshot=shot)
    if nav["url_after"] != nav["url_before"] or nav["search_requests"]:
        fails.append(f"a whitespace-only keyword ran a search: {nav}")
    if not hint["shown"] or not MIN_CHARS_RE.search(hint["text"]):
        fails.append(f"no 'at least two characters' indication after submitting two spaces "
                     f"(hint shown={hint['shown']}, text={hint['text']!r}); {shot}")
    finish(tc, fails)


# =============================================================================
# Service unavailable (route interception)
# =============================================================================
@pytest.mark.parametrize("locale,keyword,expected", [
    pytest.param("en", "Qatar", MSG_UNAVAILABLE_EN, marks=pytest.mark.tc_149173, id="149173-en"),
    pytest.param("ar", "غرفة", MSG_UNAVAILABLE_AR, marks=pytest.mark.tc_149174, id="149174-ar"),
])
@marks(pytest.mark.edge)
def test_149173_4_search_service_unavailable_message(visitors, locale, keyword, expected):
    """MEDIA-MCHUB-TC-119 / TC-120: with the search service unavailable (search API
    intercepted -> 503) no result list is shown and the page reads exactly the
    unavailable message (EN / AR, RTL) without crashing or a stack trace."""
    tc = "149173" if locale == "en" else "149174"
    fails, wording = [], []
    hero = _hub(visitors, tc, locale)
    hits = hero.block_search_service(503)
    results = hero.search(keyword)
    st = results.state()
    shot = results.evidence(f"{tc}_service_unavailable_{locale}")
    record(tc, "state (info)", state=st, intercepted=hits, screenshot=shot)
    if not hits:
        pytest.fail("PRECONDITION: the search request was not intercepted (no 'service down' state reached)")
    if st["items"]:
        fails.append(f"a result list is shown while the service is down: {[i['title'] for i in st['items']]}")
    if st["trace_like"]:
        fails.append(f"the page shows a stack trace / server error text; {shot}")
    if locale == "ar" and st["root_direction"] != "rtl":
        fails.append(f"the Arabic message area renders direction {st['root_direction']!r}; expected rtl")
    if not st["error_shown"]:
        fails.append(f"no unavailable message shown (empty={st['empty_shown']}, summary {st['summary']!r}); {shot}")
    elif st["error_text"] != expected:
        wording.append(f"unavailable message reads {st['error_text']!r}; expected {expected!r}")
    finish(tc, fails, wording)


# 149124 — decision 2026-10-19: a disposable album cannot be created (the CMS
# refuses Publish with "An album must contain at least one published photo."),
# so the case searches an EXISTING published + Active album, read-only.
LIVE_ALBUM_TITLE = "Qatar Chamber calls on shipping firms to register in the TIR System"
LIVE_ALBUM_CATEGORY = "Institutional"


@marks(pytest.mark.functional_high, pytest.mark.tc_149124)
def test_149124_published_album_found_by_title_and_labelled(visitors):
    """MEDIA-MCHUB-TC-070: a published Photo Albums item is returned by a title-keyword
    search, labelled 'Photo Albums', and the type filter narrows to it (live album,
    read-only — no record created)."""
    tc, fails, wording = "149124", [], []
    results = _hub(visitors, tc).search(LIVE_ALBUM_TITLE)
    item = results.find_title(LIVE_ALBUM_TITLE)
    st = results.state()
    shot = results.evidence(f"{tc}_results_album_title")
    record(tc, "title search (info)", state=st, item=item, screenshot=shot)
    if item is None:
        fails.append(f"the published album {LIVE_ALBUM_TITLE!r} is not returned for its title; {shot}")
    else:
        if item["type"] != "photoAlbums":
            fails.append(f"album is typed {item['type']!r}; expected photoAlbums")
        elif item["label"] != EXPECTED_LABEL["photoAlbums"]:
            wording.append(f"album is labelled {item['label']!r}; the case expects 'Photo Albums'")
    with allure.step("Type filter 'Photo Albums' narrows to albums only"):
        results.select_tab("photoAlbums")
        st2 = results.state()
        shot2 = results.evidence(f"{tc}_filter_photo_albums")
        others = [i for i in st2["items"] if i["type"] != "photoAlbums"]
        if others or not any(i["title"] == LIVE_ALBUM_TITLE for i in st2["items"]):
            fails.append(f"Photo Albums filter shows {[(i['type'], i['title']) for i in st2['items']]}; {shot2}")
    with allure.step(f"Category word {LIVE_ALBUM_CATEGORY!r} (info)"):
        cat = _hub(visitors, tc).search(LIVE_ALBUM_CATEGORY)
        cat.select_tab("photoAlbums")
        record(tc, "category search (info)", category=LIVE_ALBUM_CATEGORY,
               albums=[i["title"] for i in cat.state()["items"]], screenshot=cat.evidence(f"{tc}_category_search"))
    finish(tc, fails, wording)

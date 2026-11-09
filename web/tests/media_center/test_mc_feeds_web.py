"""
web/tests/media_center/test_mc_feeds_web.py — PBI 130709 Media Center Home
Page, FRONTEND (Web) batch 3, FE-FEEDS (suite 140368): News & press releases,
Photo Gallery carousel, Video Gallery, the three CTAs and card -> detail
navigation, plus the feed / count behaviour that needs disposable data.

DATA RULES
  - Every public assertion runs in a FRESH logged-out context.
  - Disposable records are created ONLY by the QC Site Content Editor (156488)
    in the feeds' real source modules: News (manage-qcdemo131059-news — the
    object /o/qc-media-center-api/news reads; batch-1 finding), Photo Album
    (manage-photo-album), Video Record (manage-video-record). Titles are
    QCTEST-130709-<case code> <stamp>; Active Status ticked explicitly.
    Teardown deletes each by captured id + exact title + code — never by
    position. Real QCDEMO-* records are never touched.
  - States the build cannot reach without changing real content (an empty
    Video module) or an outage (failed image) are produced with Playwright
    request interception, never by unpublishing real content.
  - 5-second visitor budget: propagation is measured from the Editor's
    confirmed save to the first logged-out reload that shows it; > 5 s fails
    the step (one slow-propagation finding, reported not filed).
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta

import allure
import pytest

from cms.pages.media_center.mc_subscriber_admin_b_page import ROLE_EDITOR, ROLE_USER_IDS, NewsEntry
from core.utils.waits import WaitTimeoutError, wait_until
from core.web.browser import new_context
from web.pages.media_center.mc_feeds_page import (
    ALBUM_DETAIL_PATH,
    ALBUMS_API,
    EVIDENCE_DIR,
    FEED_PREFIX,
    NEWS_API,
    NEWS_DETAIL_PATH,
    NEWS_LISTING_PATH,
    PHOTO_LISTING_PATH,
    QCTEST_PREFIX,
    VIDEO_DETAIL_PATH,
    VIDEO_LISTING_PATH,
    VIDEOS_API,
    McFeedsAlbumAdmin,
    McFeedsNewsAdmin,
    McFeedsPage,
    McFeedsVideoAdmin,
    McListingPages,
)

STAMP = datetime.now().strftime("%m%d%H%M")
FINDINGS = os.path.join(EVIDENCE_DIR, "findings.jsonl")
TODAY = date.today()
YESTERDAY = TODAY - timedelta(days=1)
BUDGET_S = 5.0
PROPAGATION_CAP_S = 150.0
STABLE_WINDOW_S = 30.0
MSG_ARABIC_SAVED = "Arabic content saved"

COMMON = [pytest.mark.pbi_130709, pytest.mark.web, pytest.mark.media,
          pytest.mark.xdist_group("mc_fefeeds_130709")]


def marks(*extra):
    def _wrap(fn):
        for m in COMMON + list(extra):
            fn = m(fn)
        return fn
    return _wrap


def dmy(d: date) -> str:
    return d.strftime("%d/%m/%Y")


def shown_date(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def title(code: str) -> str:
    return f"{QCTEST_PREFIX}{code} {STAMP}"


# ===========================================================================
# Findings
# ===========================================================================
def record(tc: str, kind: str, **details) -> None:
    item = {"tc": tc, "kind": kind, "at": datetime.now().isoformat(timespec="seconds"), **details}
    allure.attach(json.dumps(item, ensure_ascii=False, indent=1, default=str), name=f"finding: {kind}")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    with open(FINDINGS, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(item, ensure_ascii=False, default=str) + "\n")


def finish(tc: str, fails: list[str]) -> None:
    if fails:
        record(tc, "FAILED", fails=fails)
        pytest.fail("\n".join(fails))
    record(tc, "PASSED")


def precondition(ok: bool, message: str) -> None:
    if not ok:
        pytest.fail(f"PRECONDITION: {message}")


# ===========================================================================
# Fixtures
# ===========================================================================
@pytest.fixture
def visitor(browser):
    """factory -> a fresh logged-out McFeedsPage (or McListingPages)."""
    contexts = []

    def _make(listing: bool = False, open_hub: bool = True, locale: str = "en"):
        ctx = new_context(browser, use_auth_state=False)
        contexts.append(ctx)
        view = (McListingPages if listing else McFeedsPage)(ctx.new_page())
        if open_hub:
            view.open_hub(locale=locale)
            precondition(not view.signed_in(), "the public context is signed in")
        return view

    yield _make
    for ctx in contexts:
        try:
            ctx.close()
        except Exception:  # noqa: BLE001
            pass


class Editor:
    """One Site Content Editor session driving the three source modules, with a
    registry of every record it created (deleted in reverse at teardown)."""

    def __init__(self, browser, tc: str):
        self.tc = tc
        self.ctx = new_context(browser, use_auth_state=False)
        page = self.ctx.new_page()
        self.news = McFeedsNewsAdmin(page)
        if self.news.login_as_role(ROLE_EDITOR) == "auth_failed":
            pytest.fail("PRECONDITION: Liferay refused the Site Content Editor credentials")
        self.albums = McFeedsAlbumAdmin(page)
        self.albums.pinned_role = ROLE_EDITOR
        self.videos = McFeedsVideoAdmin(page)
        self.created: list[tuple[str, object]] = []
        self.saved_at: dict[str, float] = {}

    def check_editor(self) -> None:
        user = self.news.signed_in_user()
        precondition(user[0] == ROLE_USER_IDS[ROLE_EDITOR], f"admin session is {user}, not the Site Content Editor")

    # ---- news -----------------------------------------------------------------
    def create_news(self, name: str, day: date, publish: bool = True, categories=("Collaboration",),
                    arabic: bool = True, **kw) -> tuple[NewsEntry | None, str, list[str]]:
        drv = self.news
        drv.open_list_all()
        self.check_editor()
        precondition(not [r for r in drv.list_rows() if r["title"].strip() == name],
                     f"{name!r} already exists from an earlier run")
        ids_before = drv.snapshot_ids()
        drv.open_create_form()
        drv.fill_feed_article(name, dmy(day), categories=categories,
                              title_ar=f"{name} مقال" if arabic else "",
                              body_ar="مقال اختبار آلي مؤقت." if arabic else None, **kw)
        self.check_editor()
        drv.click_publish() if publish else drv.click_save_as_draft()
        went = drv.save_went_through()
        msgs = drv.success_messages(MSG_ARABIC_SAVED, timeout=25.0) if (went and arabic) else drv.editbar_texts()
        refusal = {} if went else drv.refusal_evidence()
        drv.evidence(f"{self.tc}_{'publish' if publish else 'draft'}_{name[-20:]}")
        entry = drv.identify_created(name, ids_before)
        if entry is not None:
            self.created.append(("news", entry))
        status = drv.row_status_raw_of(entry) if entry else ""
        record(self.tc, "news created (info)", title=name, entry=entry.__dict__ if entry else None,
               status=status, went_through=went, messages=msgs, refusal=refusal)
        return entry, status, msgs + ([json.dumps(refusal, default=str)] if refusal else [])

    def delete_news(self, entry: NewsEntry) -> bool:
        self.news.open_list_all()
        current = self.news.row_title_of(entry) or entry.title
        ok = self.news.delete_disposable(entry, current)
        if ok:
            self.created = [c for c in self.created if c[1] is not entry]
        record(self.tc, "news deleted (info)", entry=entry.__dict__, deleted=ok)
        return ok

    # ---- album ----------------------------------------------------------------
    def create_album(self, name: str, day: date, publish: bool = True):
        drv = self.albums
        precondition(not drv.leftovers() or all(r["title"] != name for r in drv.leftovers()),
                     f"{name!r} already exists")
        self.check_editor()
        ids_before = drv.snapshot_ids()
        drv.open_create_form_en()
        drv.fill_album(drv.album_data(name, dmy(day)))
        self.check_editor()
        drv.click_publish() if publish else drv.click_save_as_draft()
        went = drv.save_went_through()
        refusal = {} if went else drv.refusal_evidence()
        if went:
            drv.wait_arabic_saved()
        drv.evidence(f"{self.tc}_album_{'publish' if publish else 'draft'}")
        entry = drv.identify_created(name, ids_before)
        if entry is not None:
            self.created.append(("album", entry))
        drv.open_list_all()
        status = drv.row_status_raw(entry) if entry else ""
        record(self.tc, "album created (info)", title=name, entry=entry.__dict__ if entry else None,
               status=status, went_through=went, refusal=refusal)
        return entry, status

    # ---- video ----------------------------------------------------------------
    def create_video(self, name: str, day: date, publish: bool = True):
        drv = self.videos
        self.check_editor()
        ids_before = drv.snapshot_ids()
        drv.open_create_form_en()
        drv.fill_video(drv.video_data(name, dmy(day)))
        self.check_editor()
        drv.click_publish() if publish else drv.click_save_as_draft()
        went = drv.save_went_through()
        refusal = {} if went else drv.refusal_evidence()
        if went:
            drv.wait_arabic_saved()
        drv.evidence(f"{self.tc}_video_{'publish' if publish else 'draft'}")
        entry = drv.identify_created(name, ids_before)
        if entry is not None:
            self.created.append(("video", entry))
        drv.open_list_all()
        status = drv.row_status_raw(entry) if entry else ""
        record(self.tc, "video created (info)", title=name, entry=entry.__dict__ if entry else None,
               status=status, went_through=went, refusal=refusal)
        return entry, status

    # ---- teardown --------------------------------------------------------------
    def cleanup(self) -> None:
        for kind, entry in reversed(self.created):
            ok = False
            try:
                if kind == "news":
                    self.news.open_list_all()
                    ok = self.news.delete_disposable(entry, self.news.row_title_of(entry) or entry.title)
                elif kind == "album":
                    ok = self.albums.delete_own_entry(entry)
                else:
                    ok = self.videos.delete_disposable_entry(entry)
            except Exception as exc:  # noqa: BLE001
                record(self.tc, "teardown error", module=kind, entry=entry.__dict__, error=repr(exc))
            record(self.tc, "teardown (info)", module=kind, entry=entry.__dict__, deleted=ok)
            if not ok:
                record(self.tc, "LEFTOVER", module=kind, entry=entry.__dict__)
        self.created = []
        try:
            self.ctx.close()
        except Exception:  # noqa: BLE001
            pass


@pytest.fixture
def editor(browser, request):
    holder: dict = {}

    def _make() -> Editor:
        if "e" not in holder:
            tc = next((m.name[3:] for m in request.node.iter_markers() if m.name.startswith("tc_")), "x")
            holder["e"] = Editor(browser, tc)
        return holder["e"]

    yield _make
    if "e" in holder:
        holder["e"].cleanup()


# ===========================================================================
# helpers
# ===========================================================================
def article_count_expectation(view: McFeedsPage, before_ercs: set[str], before: int, mine_delta: int,
                              mine: set[str]) -> tuple[int, dict]:
    """Expected Articles count = before + our delta + whatever OTHER people's
    articles did meanwhile (read from the guest news API)."""
    now = {i["erc"] for i in view.news_api(limit=500)}
    others_added = (now - before_ercs) - mine
    others_removed = (before_ercs - now) - mine
    expected = before + mine_delta + len(others_added) - len(others_removed)
    return expected, {"others_added": sorted(others_added), "others_removed": sorted(others_removed)}


def timed(fails: list[str], step: str, held: bool, seconds: float, shot: str, what: str) -> None:
    if not held:
        fails.append(f"{step}: {what} not seen within {PROPAGATION_CAP_S:.0f}s; {shot}")
    elif seconds > BUDGET_S:
        fails.append(f"{step}: {what} took {seconds:.1f}s to reach the logged-out hub (> {BUDGET_S:.0f}s "
                     f"visitor budget) [slow-propagation]; {shot}")


# ===========================================================================
# 149086 — feed sections are read-only for a visitor
# ===========================================================================
@marks(pytest.mark.auth, pytest.mark.tc_149086)
def test_149086_feeds_read_only_for_visitor(visitor):
    """MEDIA-MCHUB-TC-032: no create/edit/delete controls on feed cards; card click only navigates."""
    tc, fails = "149086", []
    view = visitor()
    with allure.step("1. Feed sections render"):
        rendered = {s: view.section_rendered(s) for s in (view.NEWS, view.PHOTO, view.VIDEO)}
        shot1 = view.evidence(f"{tc}_step1_hub")
        if not all(rendered.values()):
            fails.append(f"step 1: feed sections not all rendered: {rendered}; {shot1}")
    with allure.step("2. No Edit / Add / Delete / inline-edit control on any card (incl. hover)"):
        view.hover_all_cards()
        controls = view.editing_controls()
        ui = view.page_editing_ui()
        shot2 = view.evidence(f"{tc}_step2_hover")
        record(tc, "edit scan (info)", controls=controls, ui=ui)
        if controls:
            fails.append(f"step 2: editing controls exposed on feed sections: {controls}; {shot2}")
        if ui["control_menu"] or ui["edit_mode"] or ui["contenteditable"]:
            fails.append(f"step 2: authoring UI on the public hub: {ui}; {shot2}")
    with allure.step("3. Click an article card — detail opens, no editing UI"):
        cards = view.news_cards()
        precondition(bool(cards), "no article card on the hub")
        view.click_news_card(0)
        view.page.wait_for_url(lambda u: NEWS_DETAIL_PATH in u, timeout=30000)
        listing = McListingPages(view.page)
        detail = listing.detail_title("news")
        ui3 = view.page_editing_ui()
        shot3 = view.evidence(f"{tc}_step3_detail")
        if NEWS_DETAIL_PATH not in view.page.url or not detail:
            fails.append(f"step 3: the article detail did not open ({view.page.url!r}, title {detail!r}); {shot3}")
        if ui3["control_menu"] or ui3["edit_mode"] or ui3["contenteditable"] or ui3["edit_links"]:
            fails.append(f"step 3: editing UI on the detail page: {ui3}; {shot3}")
    finish(tc, fails)


# ===========================================================================
# 149089 / 149090 / 149091 — Articles count widget
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.tc_149089)
def test_149089_publish_increments_articles_count(visitor, editor):
    """MEDIA-MCHUB-TC-035: publishing an article raises the Articles count by one; deleting restores it."""
    tc, fails = "149089", []
    name = title("CNT-01")
    view = visitor()
    with allure.step("1. Note the Articles count (logged out)"):
        before = view.count_value("Articles")
        before_ercs = {i["erc"] for i in view.news_api(limit=500)}
        shot1 = view.evidence(f"{tc}_step1_count")
        precondition(before is not None, f"no Articles count on the hub; {shot1}")
    ed = editor()
    with allure.step("2. Editor creates + Submits QCTEST-130709-CNT-01 (Active)"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=True)
        precondition(entry is not None, f"article not created: {msgs}")
        if status.upper() != "PUBLISHED":
            fails.append(f"step 2: badge reads {status!r}, not PUBLISHED")
    with allure.step("3. Reload the hub — Articles count = previous + 1"):
        state: dict = {}

        def _plus_one(v: McFeedsPage) -> bool:
            state["expected"], state["others"] = article_count_expectation(v, before_ercs, before, 1, {entry.code})
            state["seen"] = v.count_value("Articles")
            return state["seen"] == state["expected"]

        held, secs = view.poll_hub(_plus_one, timeout=PROPAGATION_CAP_S)
        shot3 = view.evidence(f"{tc}_step3_count_plus_one")
        record(tc, "count +1 (info)", before=before, **state, held=held, seconds=secs)
        timed(fails, "step 3", held, secs, shot3, f"Articles count {state.get('expected')} (saw {state.get('seen')})")
    with allure.step("4. Teardown: delete QCTEST-130709-CNT-01 — count returns to the original value"):
        deleted = ed.delete_news(entry)
        precondition(deleted, f"could not delete {name!r}")
        state4: dict = {}

        def _back(v: McFeedsPage) -> bool:
            state4["expected"], state4["others"] = article_count_expectation(v, before_ercs, before, 0, {entry.code})
            state4["seen"] = v.count_value("Articles")
            return state4["seen"] == state4["expected"]

        held4, secs4 = view.poll_hub(_back, timeout=PROPAGATION_CAP_S)
        shot4 = view.evidence(f"{tc}_step4_count_restored")
        record(tc, "count restored (info)", before=before, **state4, held=held4, seconds=secs4)
        if not held4:
            fails.append(f"step 4: Articles count did not return to {state4.get('expected')} "
                         f"(saw {state4.get('seen')}); {shot4}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149090)
def test_149090_draft_article_not_counted(visitor, editor):
    """MEDIA-MCHUB-TC-036: a Draft article (Active ticked) does not change the Articles count."""
    tc, fails = "149090", []
    name = title("CNT-02")
    view = visitor()
    with allure.step("1. Note the Articles count"):
        before = view.count_value("Articles")
        before_ercs = {i["erc"] for i in view.news_api(limit=500)}
        view.evidence(f"{tc}_step1_count")
        precondition(before is not None, "no Articles count on the hub")
    ed = editor()
    with allure.step("2. Editor saves QCTEST-130709-CNT-02 as Draft (Active ticked)"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=False)
        precondition(entry is not None, f"draft not created: {msgs}")
        if "DRAFT" not in status.upper():
            fails.append(f"step 2: badge reads {status!r}, not DRAFT")
    with allure.step("3. Reload the hub — Articles count unchanged (held for 30 s)"):
        seen: list = []

        def _changed(v: McFeedsPage) -> bool:
            expected, others = article_count_expectation(v, before_ercs, before, 0, {entry.code})
            value = v.count_value("Articles")
            seen.append({"expected": expected, "seen": value, **others})
            return value != expected

        changed, _ = view.poll_hub(_changed, timeout=STABLE_WINDOW_S, poll=5.0)
        in_api = any(i["erc"] == entry.code for i in view.news_api(limit=500))
        shot3 = view.evidence(f"{tc}_step3_count_unchanged")
        record(tc, "draft count (info)", before=before, samples=seen, in_api=in_api)
        if changed or in_api:
            fails.append(f"step 3: the Draft article changed the Articles count / guest feed "
                         f"(samples {seen[-3:]}, in news API {in_api}); {shot3}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149091)
def test_149091_unpublish_decrements_articles_count(visitor, editor):
    """MEDIA-MCHUB-TC-037: unpublishing an article lowers the Articles count by one."""
    tc, fails = "149091", []
    name = title("CNT-03")
    view = visitor()
    base = view.count_value("Articles")
    base_ercs = {i["erc"] for i in view.news_api(limit=500)}
    ed = editor()
    with allure.step("Precondition: QCTEST-130709-CNT-03 Published + Active"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=True)
        precondition(entry is not None and status.upper() == "PUBLISHED", f"article not published: {status} {msgs}")
    with allure.step("1. Note the Articles count (includes CNT-03)"):
        st: dict = {}

        def _includes(v: McFeedsPage) -> bool:
            st["expected"], st["others"] = article_count_expectation(v, base_ercs, base, 1, {entry.code})
            st["seen"] = v.count_value("Articles")
            return st["seen"] == st["expected"]

        held, _ = view.poll_hub(_includes, timeout=PROPAGATION_CAP_S)
        noted = view.count_value("Articles")
        noted_ercs = {i["erc"] for i in view.news_api(limit=500)}
        view.evidence(f"{tc}_step1_count")
        precondition(held, f"the count never included CNT-03: {st}")
    with allure.step("2. Editor Unpublishes CNT-03 — badge UNPUBLISHED"):
        dialogs = ed.news.unpublish_own(entry)
        seen2 = {"s": ""}

        def _unpublished() -> bool:
            ed.news.open_list_all()
            seen2["s"] = ed.news.row_status_raw_of(entry)
            return seen2["s"].upper() == "UNPUBLISHED"

        try:
            wait_until(_unpublished, timeout=60.0, poll=3.0)
        except WaitTimeoutError:
            pass
        status2 = seen2["s"]
        shot2 = ed.news.evidence(f"{tc}_step2_unpublished")
        record(tc, "unpublish (info)", dialogs=dialogs, status=status2)
        if status2.upper() != "UNPUBLISHED":
            fails.append(f"step 2: badge reads {status2!r}, not UNPUBLISHED; {shot2}")
    with allure.step("3. Reload the hub — Articles count = previous - 1"):
        st3: dict = {}

        def _minus_one(v: McFeedsPage) -> bool:
            st3["expected"], st3["others"] = article_count_expectation(v, noted_ercs, noted, -1, {entry.code})
            st3["seen"] = v.count_value("Articles")
            return st3["seen"] == st3["expected"]

        held3, secs3 = view.poll_hub(_minus_one, timeout=PROPAGATION_CAP_S)
        shot3 = view.evidence(f"{tc}_step3_count_minus_one")
        record(tc, "count -1 (info)", noted=noted, **st3, held=held3, seconds=secs3)
        timed(fails, "step 3", held3, secs3, shot3, f"Articles count {st3.get('expected')} (saw {st3.get('seen')})")
    finish(tc, fails)


# ===========================================================================
# 149102 / 149104 / 149180 — News lead
# ===========================================================================
def _lead_is(name: str):
    return lambda v: v.news_lead().get("title") == name


@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat, pytest.mark.tc_149102)
def test_149102_featured_article_is_news_lead(visitor, editor):
    """MEDIA-MCHUB-TC-048: the most recent Featured article is the News lead with every lead element."""
    tc, fails = "149102", []
    name = title("NEWS-01")
    ed = editor()
    with allure.step("Precondition: QCTEST-130709-NEWS-01 Published + Active, Featured, dated today"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=True, categories=("Featured", "Trade & Economy"),
                                             read_time="4", total_views="7")
        precondition(entry is not None and status.upper() == "PUBLISHED", f"article not published: {status} {msgs}")
    view = visitor()
    with allure.step("1-2. Logged-out hub: the lead is NEWS-01 with all its elements"):
        held, secs = view.poll_hub(_lead_is(name), timeout=PROPAGATION_CAP_S)
        lead = view.news_lead()
        shot = view.evidence(f"{tc}_step2_lead")
        record(tc, "lead (info)", lead=lead, held=held, seconds=secs)
        if not view.section_rendered(view.NEWS):
            fails.append(f"step 1: News section not rendered; {shot}")
        if not held:
            fails.append(f"step 2: lead is {lead.get('title')!r}, not {name!r}; {shot}")
        else:
            if secs > BUDGET_S:
                fails.append(f"step 2: NEWS-01 took {secs:.1f}s to lead the logged-out hub (> 5s) "
                             f"[slow-propagation]; {shot}")
            chips = lead["chips"]
            if "Featured" not in chips:
                fails.append(f"step 2: no 'Featured' chip on the lead (chips {chips}); {shot}")
            if not [c for c in chips if c != "Featured"]:
                fails.append(f"step 2: no category chip besides 'Featured' (chips {chips}); {shot}")
            if not lead["img_loaded"]:
                fails.append(f"step 2: the lead image is missing/not loaded ({lead['img_src']!r}); {shot}")
            if not lead["excerpt"]:
                fails.append(f"step 2: the lead shows no excerpt; {shot}")
            meta = " | ".join(lead["meta"])
            if shown_date(TODAY) not in lead["meta"]:
                fails.append(f"step 2: published date {shown_date(TODAY)!r} not shown (meta {meta!r}); {shot}")
            if not any("view" in m.lower() for m in lead["meta"]):
                fails.append(f"step 2: no view count in the lead meta ({meta!r}); {shot}")
            if not any("read" in m.lower() for m in lead["meta"]):
                fails.append(f"step 2: no read time in the lead meta ({meta!r}); {shot}")
            if lead["read_more"] != "Read More":
                fails.append(f"step 2: lead action reads {lead['read_more']!r}, not 'Read More'; {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149104)
def test_149104_newest_article_leads_without_featured(visitor, editor):
    """MEDIA-MCHUB-TC-050: with no Featured article, the most recent published article leads (no Featured chip)."""
    tc, fails = "149104", []
    name = title("NEWS-02")
    probe = visitor()
    featured_live = [i for i in probe.news_api(limit=500) if "Featured" in (i.get("categories") or [])]
    record(tc, "precondition (info)", note="case wants an environment with NO published Featured article; qcdev "
           "has real Featured articles that may not be edited", featured_live=featured_live)
    ed = editor()
    with allure.step("Precondition: QCTEST-130709-NEWS-02 Published + Active today, NOT Featured"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=True, categories=("Collaboration",))
        precondition(entry is not None and status.upper() == "PUBLISHED", f"article not published: {status} {msgs}")
    view = visitor()
    with allure.step("1-2. Lead is NEWS-02 without a 'Featured' chip"):
        held, secs = view.poll_hub(_lead_is(name), timeout=PROPAGATION_CAP_S)
        lead = view.news_lead()
        shot = view.evidence(f"{tc}_step2_lead")
        record(tc, "lead (info)", lead=lead, held=held, seconds=secs, featured_live=len(featured_live))
        if not view.section_rendered(view.NEWS):
            fails.append(f"step 1: News section not rendered; {shot}")
        if not held:
            fails.append(f"step 2: lead is {lead.get('title')!r}, not {name!r}; {shot}")
        elif "Featured" in lead["chips"]:
            fails.append(f"step 2: the non-featured lead carries a 'Featured' chip ({lead['chips']}); {shot}")
        if held and secs > BUDGET_S:
            fails.append(f"step 2: NEWS-02 took {secs:.1f}s to lead the hub (> 5s) [slow-propagation]; {shot}")
    finish(tc, fails)


@marks(pytest.mark.edge, pytest.mark.tc_149180)
def test_149180_draft_featured_not_used_as_lead(visitor, editor):
    """MEDIA-MCHUB-TC-126: a newer Draft Featured article is not the lead and appears nowhere."""
    tc, fails = "149180", []
    published, draft = title("NEWS-01"), title("NEWS-03")
    ed = editor()
    with allure.step("Precondition: NEWS-01 Published Featured (yesterday) + NEWS-03 Draft Featured (today)"):
        e1, s1, m1 = ed.create_news(published, YESTERDAY, publish=True, categories=("Featured", "Collaboration"))
        precondition(e1 is not None and s1.upper() == "PUBLISHED", f"NEWS-01 not published: {s1} {m1}")
        e3, s3, m3 = ed.create_news(draft, TODAY, publish=False, categories=("Featured", "Collaboration"))
        precondition(e3 is not None and "DRAFT" in s3.upper(), f"NEWS-03 not a draft: {s3} {m3}")
    view = visitor()
    with allure.step("1-2. Lead is NEWS-01; NEWS-03 appears nowhere on the page"):
        held, secs = view.poll_hub(_lead_is(published), timeout=PROPAGATION_CAP_S)
        lead = view.news_lead()
        body = view.page.locator("body").inner_text()
        shot = view.evidence(f"{tc}_step2_lead")
        record(tc, "lead (info)", lead=lead, held=held, seconds=secs)
        if not held:
            fails.append(f"step 2: lead is {lead.get('title')!r}, not {published!r}; {shot}")
        if draft in body or any(i["erc"] == e3.code for i in view.news_api(limit=500)):
            fails.append(f"step 2: the Draft {draft!r} is exposed on the hub / guest feed; {shot}")
    finish(tc, fails)


# ===========================================================================
# 149103 — three cards beneath the lead
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.tc_149103)
def test_149103_cards_are_next_three_recent(visitor):
    """MEDIA-MCHUB-TC-049: the three cards are the next three newest articles in descending date order."""
    tc, fails = "149103", []
    listing = visitor(listing=True, open_hub=False)
    with allure.step("1. News & Press Releases listing (newest first)"):
        ordered = listing.news_listing()
        listing.evidence(f"{tc}_step1_listing")
        precondition(len(ordered) >= 4, f"the listing shows fewer than 4 articles: {ordered}")
    view = visitor()
    with allure.step("2. The three cards beneath the lead"):
        lead = view.news_lead().get("title", "")
        cards = view.news_cards()
        shot = view.evidence(f"{tc}_step2_cards")
        expected = [t for t in ordered if t != lead][:3]
        got = [c["title"] for c in cards]
        dates = [datetime.strptime(c["meta"][0], "%b %d, %Y").date() for c in cards if c["meta"]]
        record(tc, "cards (info)", lead=lead, listing=ordered[:6], cards=cards)
        if got != expected:
            fails.append(f"step 2: cards {got} != the next three of the listing {expected}; {shot}")
        if len(dates) != len(cards) or dates != sorted(dates, reverse=True):
            fails.append(f"step 2: card dates are not in descending order: {[c['meta'] for c in cards]}; {shot}")
    finish(tc, fails)


# ===========================================================================
# 149105-149108 / 149181 / 149182 — Photo carousel
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.tc_149105)
def test_149105_carousel_most_recent_first(visitor):
    """MEDIA-MCHUB-TC-051: carousel album order matches the Photo Albums listing, newest first."""
    tc, fails = "149105", []
    listing = visitor(listing=True, open_hub=False)
    ref = listing.photo_listing()
    listing.evidence(f"{tc}_step1_listing")
    precondition(bool(ref["titles"]), "the Photo Albums listing shows no album")
    view = visitor()
    seq = view.carousel_sequence()
    shot = view.evidence(f"{tc}_step2_carousel")
    record(tc, "order (info)", listing=ref, carousel=seq)
    if seq != ref["titles"][:len(seq)]:
        fails.append(f"step 2: carousel order {seq} != listing order {ref['titles'][:len(seq)]}; {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149106)
def test_149106_carousel_next_advances(visitor):
    """MEDIA-MCHUB-TC-052: Next shows the next album; indicator 1 -> 2, total unchanged."""
    tc, fails = "149106", []
    view = visitor()
    published = view.api_json(f"{ALBUMS_API}?groupId=37246&languageId=en_US&sort=recent&page=1&pageSize=100")
    total_published = published.get("totalCount")
    with allure.step("1. Indicator reads position 1 of the published albums"):
        ind = view.indicator()
        first_before = view.photo_titles_visible()
        shot1 = view.evidence(f"{tc}_step1_indicator", full_page=False)
        precondition((total_published or 0) >= 3, f"fewer than 3 published albums ({total_published})")
        if ind["current"] != 1 or ind["total"] != total_published:
            fails.append(f"step 1: indicator {ind['text']!r}, expected 1 / {total_published}; {shot1}")
    with allure.step("2. Click Next — next album shown, position 2, total unchanged"):
        after = view.click_next()
        visible = view.photo_titles_visible()
        shot2 = view.evidence(f"{tc}_step2_next")
        record(tc, "next (info)", before=ind, after=after, visible_before=first_before, visible_after=visible)
        if after["current"] != 2 or after["total"] != ind["total"]:
            fails.append(f"step 2: indicator {after['text']!r}, expected 2 / {ind['total']}; {shot2}")
        if not visible or len(first_before) < 2 or visible[0] != first_before[1]:
            fails.append(f"step 2: the carousel did not advance by one album ({first_before} -> {visible}); {shot2}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149107)
def test_149107_carousel_previous_goes_back(visitor):
    """MEDIA-MCHUB-TC-053: Next then Previous returns to the first album, position 1, total unchanged."""
    tc, fails = "149107", []
    view = visitor()
    start = view.indicator()
    first = view.photo_titles_visible()
    with allure.step("1. Next once — position 2"):
        mid = view.click_next()
        shot1 = view.evidence(f"{tc}_step1_next", full_page=False)
        if mid["current"] != 2:
            fails.append(f"step 1: indicator {mid['text']!r} after Next, expected position 2; {shot1}")
    with allure.step("2. Previous — first album again, position 1, total unchanged"):
        back = view.click_prev()
        visible = view.photo_titles_visible()
        shot2 = view.evidence(f"{tc}_step2_prev")
        record(tc, "prev (info)", start=start, mid=mid, back=back, first=first, visible=visible)
        if back["current"] != 1 or back["total"] != start["total"]:
            fails.append(f"step 2: indicator {back['text']!r}, expected 1 / {start['total']}; {shot2}")
        if visible[:1] != first[:1]:
            fails.append(f"step 2: first album not shown again ({first} -> {visible}); {shot2}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149108)
def test_149108_indicator_total_equals_published_albums(visitor):
    """MEDIA-MCHUB-TC-054: the indicator total equals the published-album total."""
    tc, fails = "149108", []
    listing = visitor(listing=True, open_hub=False)
    ref = listing.photo_listing()
    listing.evidence(f"{tc}_step1_listing")
    noted = len(ref["titles"])
    view = visitor()
    ind = view.indicator()
    widget = view.count_value("Photo Albums")
    shot = view.evidence(f"{tc}_step2_indicator")
    record(tc, "totals (info)", listing=noted, listing_status=ref["status"], widget=widget, indicator=ind)
    precondition(noted > 0, "no published album on the listing")
    if widget is not None and widget != noted:
        record(tc, "widget vs listing (info)", widget=widget, listing=noted)
    if ind["total"] != noted:
        fails.append(f"step 2: indicator total {ind['text']!r} != published albums {noted} "
                     f"(widget {widget}); {shot}")
    finish(tc, fails)


@marks(pytest.mark.edge, pytest.mark.tc_149181)
def test_149181_previous_on_first_position(visitor):
    """MEDIA-MCHUB-TC-127: Previous at position 1 is disabled or wraps; never 0 / > total."""
    tc, fails = "149181", []
    view = visitor()
    ind = view.indicator()
    nav = view.nav_state()
    shot1 = view.evidence(f"{tc}_step1_indicator", full_page=False)
    if ind["current"] != 1 or not ind["total"]:
        fails.append(f"step 1: indicator {ind['text']!r}, expected position 1 of the albums; {shot1}")
    after = view.force_click("prev")
    shot2 = view.evidence(f"{tc}_step2_prev", full_page=False)
    record(tc, "prev at 1 (info)", before=ind, nav=nav, after=after)
    ok = (nav["prev_disabled"] and after["current"] == 1) or after["current"] == ind["total"]
    if not ok or not after["current"] or after["current"] < 1 or after["current"] > (after["total"] or 0):
        fails.append(f"step 2: Previous at position 1 gave {after['text']!r} (prev disabled={nav['prev_disabled']}); "
                     f"{shot2}")
    finish(tc, fails)


@marks(pytest.mark.edge, pytest.mark.tc_149182)
def test_149182_next_on_last_position(visitor):
    """MEDIA-MCHUB-TC-128: Next until position = total, then Next again is disabled or wraps."""
    tc, fails = "149182", []
    view = visitor()
    start = view.indicator()
    trail = [start["text"]]
    for _ in range(60):
        if view.nav_state()["next_disabled"] in (True, None) or view.indicator()["current"] == start["total"]:
            break
        trail.append(view.click_next()["text"])
    end = view.indicator()
    nav = view.nav_state()
    shot1 = view.evidence(f"{tc}_step1_last", full_page=False)
    if end["current"] != end["total"]:
        fails.append(f"step 1: Next stops at {end['text']!r} (Next disabled={nav['next_disabled']}); the current "
                     f"position never reaches the total {end['total']} (trail {trail}); {shot1}")
    after = view.force_click("next")
    shot2 = view.evidence(f"{tc}_step2_next_again", full_page=False)
    record(tc, "next at end (info)", start=start, trail=trail, end=end, nav=nav, after=after)
    if not after["current"] or after["current"] > (after["total"] or 0) or (
            after["current"] not in (end["current"], 1)):
        fails.append(f"step 2: Next at the end gave {after['text']!r}; {shot2}")
    finish(tc, fails)


# ===========================================================================
# 149109 — video order
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.tc_149109)
def test_149109_video_cards_most_recent_first(visitor):
    """MEDIA-MCHUB-TC-055: Video Gallery card order matches the Video Library listing."""
    tc, fails = "149109", []
    listing = visitor(listing=True, open_hub=False)
    ref = listing.video_listing()
    listing.evidence(f"{tc}_step1_listing")
    precondition(bool(ref["titles"]), "the Video Library shows no video")
    view = visitor()
    cards = view.video_titles()
    shot = view.evidence(f"{tc}_step2_cards")
    record(tc, "order (info)", listing=ref["titles"], cards=cards)
    if not cards or [c[:60] for c in cards] != [t[:60] for t in ref["titles"][:len(cards)]]:
        fails.append(f"step 2: video cards {cards} != listing order {ref['titles'][:len(cards)]}; {shot}")
    finish(tc, fails)


# ===========================================================================
# 149110 / 149111 / 149112 — CTAs
# ===========================================================================
CTA_CASES = {
    "149110": ("news", "View All Articles", NEWS_LISTING_PATH, "a.qc-news-feat-card, a.qc-news-card"),
    "149111": ("photo", "View all albums", PHOTO_LISTING_PATH, ".qc-pgl-card"),
    "149112": ("video", "Watch now", VIDEO_LISTING_PATH, "a.qc-vll-card"),
}


def _cta_case(tc: str, visitor) -> None:
    block, label, path, card = CTA_CASES[tc]
    fails: list[str] = []
    view = visitor()
    with allure.step(f"1. '{label}' action is displayed"):
        cta = view.cta(block)
        shot1 = view.evidence(f"{tc}_step1_cta", full_page=False)
        if not cta.get("present") or not cta.get("visible") or cta.get("label") != label:
            fails.append(f"step 1: CTA {cta} is not a visible {label!r}; {shot1}")
    with allure.step(f"2. Click — the listing opens, HTTP 200, cards render"):
        nav = view.click_cta(block)
        try:
            view.page.locator(card).first.wait_for(timeout=40000)
            cards = view.page.locator(card).count()
        except Exception:  # noqa: BLE001
            cards = 0
        shot2 = view.evidence(f"{tc}_step2_listing")
        record(tc, "cta (info)", cta=cta, nav=nav, cards=cards)
        if nav["status"] != 200 or path not in nav["url"]:
            fails.append(f"step 2: CTA went to {nav['url']!r} (HTTP {nav['status']}), not {path}; {shot2}")
        if cards == 0:
            fails.append(f"step 2: the listing rendered no card; {shot2}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.tc_149110)
def test_149110_view_all_articles_cta(visitor):
    """MEDIA-MCHUB-TC-056: 'View All Articles' opens the News & Press Releases listing."""
    _cta_case("149110", visitor)


@marks(pytest.mark.functional_high, pytest.mark.tc_149111)
def test_149111_view_all_albums_cta(visitor):
    """MEDIA-MCHUB-TC-057: 'View all albums' opens the Photo Albums listing."""
    _cta_case("149111", visitor)


@marks(pytest.mark.functional_high, pytest.mark.tc_149112)
def test_149112_watch_now_cta(visitor):
    """MEDIA-MCHUB-TC-058: 'Watch now' opens the Video Library listing."""
    _cta_case("149112", visitor)


# ===========================================================================
# 149113-149116 — card -> detail
# ===========================================================================
def _detail_case(tc: str, visitor, kind: str) -> None:
    fails: list[str] = []
    view = visitor()
    detail = McListingPages(view.page)
    detail.watch_page_errors()
    with allure.step("1. Note the title"):
        if kind == "lead":
            noted, path = view.news_lead().get("title", ""), NEWS_DETAIL_PATH
        elif kind == "news":
            noted, path = (view.news_cards() or [{}])[0].get("title", ""), NEWS_DETAIL_PATH
        elif kind == "album":
            noted, path = (view.photo_cards() or [{}])[0].get("title", ""), ALBUM_DETAIL_PATH
        else:
            noted, path = (view.video_cards() or [{}])[0].get("title", ""), VIDEO_DETAIL_PATH
        view.evidence(f"{tc}_step1_hub", full_page=False)
        precondition(bool(noted), f"no {kind} item on the hub")
    with allure.step("2. Click — the detail page shows the same title"):
        {"lead": view.click_read_more, "news": lambda: view.click_news_card(0),
         "album": lambda: view.click_album_card(0), "video": lambda: view.click_video_card(0)}[kind]()
        try:
            view.page.wait_for_url(lambda u: path in u, timeout=30000)
        except Exception:  # noqa: BLE001 — reported below
            pass
        shown = detail.detail_title({"lead": "news", "news": "news"}.get(kind, kind))
        shot = view.evidence(f"{tc}_step2_detail")
        record(tc, "detail (info)", noted=noted, url=view.page.url, shown=shown, page_errors=detail.page_errors())
        if path not in view.page.url:
            fails.append(f"step 2: clicking went to {view.page.url!r}, not {path}; {shot}")
        if shown[:80] != noted[:80]:
            fails.append(f"step 2: detail page title {shown!r} != noted {noted!r} "
                         f"(page errors {detail.page_errors()}); {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.uat, pytest.mark.tc_149113)
def test_149113_lead_read_more_opens_detail(visitor):
    """MEDIA-MCHUB-TC-059: the lead's 'Read More' opens that article's detail page."""
    _detail_case("149113", visitor, "lead")


@marks(pytest.mark.functional_high, pytest.mark.tc_149114)
def test_149114_article_card_opens_detail(visitor):
    """MEDIA-MCHUB-TC-060: an article card opens that article's detail page."""
    _detail_case("149114", visitor, "news")


@marks(pytest.mark.functional_high, pytest.mark.tc_149115)
def test_149115_album_card_opens_album_details(visitor):
    """MEDIA-MCHUB-TC-061: an album card opens that album's Album Details page."""
    _detail_case("149115", visitor, "album")


@marks(pytest.mark.functional_high, pytest.mark.tc_149116)
def test_149116_video_card_opens_video_details(visitor):
    """MEDIA-MCHUB-TC-062: a video card opens that video's Video Details page."""
    _detail_case("149116", visitor, "video")


# ===========================================================================
# 149117 — empty source module hides the section
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.tc_149117)
def test_149117_empty_video_module_hides_section(visitor):
    """MEDIA-MCHUB-TC-063: with no published video the Video Gallery section is not rendered at all.
    The empty module is simulated by rewriting the guest videos API to zero items (real videos are
    never unpublished)."""
    tc, fails = "149117", []
    empty = lambda data: {**data, "items": [], "total": 0, "totalCount": 0, "hasMore": False}  # noqa: E731
    listing = visitor(listing=True, open_hub=False)
    listing.fulfil_json(VIDEOS_API, empty)
    with allure.step("1. Public Video Library lists no published video"):
        ref = listing.video_listing()
        shot1 = listing.evidence(f"{tc}_step1_listing")
        if ref["titles"]:
            fails.append(f"step 1: the listing still lists videos {ref['titles']}; {shot1}")
    view = visitor(open_hub=False)
    hits = view.fulfil_json(VIDEOS_API, empty)
    with allure.step("2-3. Hub: no Video Gallery section, no empty block between Photo Gallery and the band"):
        view.open_hub()
        precondition(bool(hits), "the hub never requested the videos API")
        state = view.page.evaluate("""() => {
            const v = document.querySelector('section.qc-mc-vf');
            const p = document.querySelector('section.qc-mc-pf');
            const s = document.querySelector('section.qc-mc-sub');
            const r = (e) => e ? e.getBoundingClientRect() : null;
            const between = (p && s) ? Math.round(r(s).top - r(p).bottom) : null;
            return {video_present: !!v, video_hidden: v ? (v.hidden || getComputedStyle(v).display === 'none') : true,
                    video_height: v ? Math.round(r(v).height) : 0,
                    video_text: v && !v.hidden ? v.innerText.trim().slice(0, 120) : '',
                    gap_photo_to_band: between}; }""")
        visible_heading = view.page.locator(f"{view.VIDEO} {view.VIDEO_HEADING}").first
        heading_visible = visible_heading.count() > 0 and visible_heading.is_visible()
        shot2 = view.evidence(f"{tc}_step2_hub")
        record(tc, "empty video (info)", state=state, heading_visible=heading_visible, api_hits=hits[:2])
        if not state["video_hidden"] or state["video_height"] > 0 or heading_visible:
            fails.append(f"step 2: an empty Video Gallery block is rendered: {state}; {shot2}")
        listing_mock = ref["empty_visible"] or not ref["titles"]
        if not listing_mock:
            fails.append(f"step 1: listing not empty under the simulated state; {shot1}")
    finish(tc, fails)


# ===========================================================================
# 149118 / 149119 / 149120 — non-published items stay out of the feeds
# ===========================================================================
@marks(pytest.mark.functional_high, pytest.mark.regression, pytest.mark.tc_149118)
def test_149118_draft_article_not_in_news_feed(visitor, editor):
    """MEDIA-MCHUB-TC-064: a Draft article (today, Active) is not shown in the News feed."""
    tc, fails = "149118", []
    name = title("FEED-01")
    ed = editor()
    with allure.step("1. Editor saves QCTEST-130709-FEED-01 as Draft (today, Active) — badge DRAFT"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=False)
        precondition(entry is not None, f"draft not created: {msgs}")
        if "DRAFT" not in status.upper():
            fails.append(f"step 1: badge reads {status!r}, not DRAFT")
    view = visitor()
    with allure.step("2. Logged-out hub: FEED-01 nowhere in the News feed; newest Published item leads"):
        leaked, _ = view.poll_hub(lambda v: name in v.news_titles(), timeout=STABLE_WINDOW_S, poll=5.0)
        titles = view.news_titles()
        newest = (view.news_api(limit=1) or [{}])[0].get("title", "")
        shot = view.evidence(f"{tc}_step2_feed")
        record(tc, "draft feed (info)", titles=titles, newest_published=newest)
        if leaked or name in titles:
            fails.append(f"step 2: the Draft {name!r} is shown in the News feed {titles}; {shot}")
        if not titles or titles[0] != newest:
            fails.append(f"step 2: the lead {titles[:1]} is not the most recent Published article {newest!r}; {shot}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149119)
def test_149119_unpublished_album_not_in_photo_feed(visitor, editor):
    """MEDIA-MCHUB-TC-065: an album Published today then Unpublished is not shown in the Photo feed."""
    tc, fails = "149119", []
    name = f"{FEED_PREFIX}02 {STAMP}"
    ed = editor()
    view = visitor()
    with allure.step("Precondition: QCTEST-130709-FEED-02 Published + Active today (visible in the feed)"):
        entry, status = ed.create_album(name, TODAY, publish=True)
        precondition(entry is not None and status.upper() == "PUBLISHED", f"album not published: {status}")
        shown, secs = view.poll_hub(lambda v: name in v.carousel_sequence(), timeout=PROPAGATION_CAP_S)
        view.evidence(f"{tc}_pre_album_shown")
        record(tc, "album shown (info)", shown=shown, seconds=secs)
        precondition(shown, f"the published album never surfaced in the carousel within {PROPAGATION_CAP_S:.0f}s")
    with allure.step("1. Editor Unpublishes FEED-02 — badge UNPUBLISHED"):
        ed.albums.open_list_all()
        dialogs = ed.albums.run_row_action(entry, "unpublish")
        status1 = ed.albums.wait_status(entry, ("Unpublished", "UNPUBLISHED"), timeout=60.0)
        raw = ed.albums.row_status_raw(entry)
        shot1 = ed.albums.evidence(f"{tc}_step1_unpublished")
        record(tc, "unpublish (info)", dialogs=dialogs, status=status1, raw=raw)
        if raw.upper() != "UNPUBLISHED":
            fails.append(f"step 1: badge reads {raw!r}, not UNPUBLISHED; {shot1}")
    with allure.step("2. Logged-out hub: FEED-02 nowhere in the Photo feed; newest Published album first"):
        gone, secs2 = view.poll_hub(lambda v: name not in v.carousel_sequence(), timeout=PROPAGATION_CAP_S)
        view.open_hub()
        seq = view.carousel_sequence()
        api = view.api_json(f"{ALBUMS_API}?groupId=37246&languageId=en_US&sort=recent&page=1&pageSize=1")
        newest = ((api.get("items") or [{}])[0]).get("title", "")
        shot2 = view.evidence(f"{tc}_step2_feed")
        record(tc, "album gone (info)", gone=gone, seconds=secs2, carousel=seq, newest=newest)
        timed(fails, "step 2", gone, secs2, shot2, f"removal of {name!r} from the Photo feed")
        if name in seq:
            fails.append(f"step 2: the Unpublished album is still in the carousel {seq}; {shot2}")
        if not seq or seq[0] != newest:
            fails.append(f"step 2: first album {seq[:1]} is not the most recent Published {newest!r}; {shot2}")
    finish(tc, fails)


@marks(pytest.mark.functional_high, pytest.mark.tc_149120)
def test_149120_draft_video_not_in_video_feed(visitor, editor):
    """MEDIA-MCHUB-TC-066: a Draft video (today, Active) is not shown in the Video feed."""
    tc, fails = "149120", []
    name = f"{FEED_PREFIX}03 {STAMP}"
    ed = editor()
    with allure.step("1. Editor saves QCTEST-130709-FEED-03 as Draft (today, Active) — badge DRAFT"):
        entry, status = ed.create_video(name, TODAY, publish=False)
        precondition(entry is not None, "draft video not created")
        if "DRAFT" not in status.upper():
            fails.append(f"step 1: badge reads {status!r}, not DRAFT")
    view = visitor()
    with allure.step("2. Logged-out hub: FEED-03 nowhere in the Video feed; newest Published video first"):
        leaked, _ = view.poll_hub(lambda v: name in v.video_titles(), timeout=STABLE_WINDOW_S, poll=5.0)
        titles = view.video_titles()
        api = view.api_json(f"{VIDEOS_API}?groupId=37246&languageId=en_US&sort=recent&page=1&pageSize=1")
        newest = ((api.get("items") or [{}])[0]).get("title", "")
        shot = view.evidence(f"{tc}_step2_feed")
        record(tc, "draft video (info)", titles=titles, newest=newest)
        if leaked or name in titles:
            fails.append(f"step 2: the Draft video {name!r} is shown in the Video feed {titles}; {shot}")
        if not titles or titles[0] != newest:
            fails.append(f"step 2: first video {titles[:1]} is not the most recent Published {newest!r}; {shot}")
    finish(tc, fails)


# ===========================================================================
# 149175 / 149176 — image failure placeholders
# ===========================================================================
@marks(pytest.mark.edge, pytest.mark.tc_149175)
def test_149175_news_card_image_failure_placeholder(visitor):
    """MEDIA-MCHUB-TC-121: a news card whose image fails shows a placeholder image."""
    tc, fails = "149175", []
    probe = visitor()
    cards = probe.news_cards()
    precondition(bool(cards) and bool(cards[0]["img"]), "the first article card has no image to block")
    target = cards[0]["img"].split("qcdev.ihorizons.com")[-1]
    view = visitor(open_hub=False)
    aborted = view.block_url(target)
    with allure.step("1. Block the first card's image and open the hub"):
        view.open_hub()
        precondition(view.section_rendered(view.NEWS), "the News section did not render")
    with allure.step("2. First card shows a placeholder image; layout intact"):
        sel = f"{view.NEWS} {view.NEWS_CARD} {view.NEWS_CARD_MEDIA}"
        try:
            wait_until(lambda: bool(aborted), timeout=15.0, poll=0.3)
        except WaitTimeoutError:
            pass
        first = view.media_box_state(sel)
        other = view.page.locator(sel).nth(1).evaluate(McFeedsPage._MEDIA_JS) if view.page.locator(sel).count() > 1 else None
        shot_path = os.path.join(EVIDENCE_DIR, f"{tc}_step2_card.png")
        os.makedirs(EVIDENCE_DIR, exist_ok=True)
        view.page.locator(f"{view.NEWS} {view.NEWS_CARD}").first.screenshot(path=shot_path)
        view.evidence(f"{tc}_step2_hub")
        record(tc, "image failure (info)", blocked=target, aborted=aborted[:2], first=first, other=other)
        precondition(bool(aborted), f"the image request {target} was never made/blocked")
        if not view.placeholder_shown(first):
            fails.append(f"step 2: no placeholder image — the media box is a plain fill "
                         f"(background {first and first['background_color']}, img present "
                         f"{first and first['img_present']}); {shot_path}")
        if first and other and (abs(first["width"] - other["width"]) > 2 or abs(first["height"] - other["height"]) > 2):
            fails.append(f"step 2: card layout changed ({first['width']}x{first['height']} vs "
                         f"{other['width']}x{other['height']}); {shot_path}")
        if first and first["img_present"] and not first["img_loaded"]:
            fails.append(f"step 2: a broken <img> is still rendered; {shot_path}")
    finish(tc, fails)


@marks(pytest.mark.edge, pytest.mark.tc_149176)
def test_149176_video_thumbnail_failure_placeholder(visitor):
    """MEDIA-MCHUB-TC-122: a video card whose thumbnail fails shows a placeholder; play + duration stay."""
    tc, fails = "149176", []
    probe = visitor()
    cards = probe.video_cards()
    precondition(bool(cards) and bool(cards[0]["img"]), "the first video card has no thumbnail to block")
    target = cards[0]["img"].split("qcdev.ihorizons.com")[-1]
    view = visitor(open_hub=False)
    aborted = view.block_url(target)
    view.open_hub()
    sel = f"{view.VIDEO} {view.VIDEO_CARD} {view.VIDEO_CARD_MEDIA}"
    try:
        wait_until(lambda: bool(aborted), timeout=15.0, poll=0.3)
    except WaitTimeoutError:
        pass
    first = view.media_box_state(sel)
    card = view.page.locator(f"{view.VIDEO} {view.VIDEO_CARD}").first
    play = card.locator(view.VIDEO_PLAY).first
    duration = card.locator(view.VIDEO_DURATION).first
    shot_path = os.path.join(EVIDENCE_DIR, f"{tc}_step2_card.png")
    os.makedirs(EVIDENCE_DIR, exist_ok=True)
    card.screenshot(path=shot_path)
    view.evidence(f"{tc}_step2_hub")
    record(tc, "thumb failure (info)", blocked=target, aborted=aborted[:2], first=first,
           play=play.is_visible() if play.count() else None, duration=duration.inner_text() if duration.count() else None)
    precondition(bool(aborted), f"the thumbnail request {target} was never made/blocked")
    if not view.placeholder_shown(first):
        fails.append(f"step 2: no placeholder image in place of the thumbnail — plain fill "
                     f"(background {first and first['background_color']}); {shot_path}")
    if not (play.count() and play.is_visible()):
        fails.append(f"step 2: the play overlay is not visible; {shot_path}")
    if not (duration.count() and duration.is_visible() and duration.inner_text().strip()):
        fails.append(f"step 2: the duration badge is not visible; {shot_path}")
    finish(tc, fails)


# ===========================================================================
# 149178 — missing Arabic translation falls back
# ===========================================================================
@marks(pytest.mark.edge, pytest.mark.tc_149178)
def test_149178_missing_arabic_falls_back(visitor, editor):
    """MEDIA-MCHUB-TC-124: an article with no Arabic content shows the EN fallback on /ar (not a blank card).
    Case precondition: 'EN content only (AR empty) if the CMS allows'."""
    tc, fails = "149178", []
    name = title("FB-01")
    ed = editor()
    with allure.step("Precondition: QCTEST-130709-FB-01 Published + Active with EN only (if the CMS allows)"):
        entry, status, msgs = ed.create_news(name, TODAY, publish=True, arabic=False)
        record(tc, "EN-only publish (info)", created=entry is not None, status=status, messages=msgs)
    view = visitor(open_hub=False, locale="ar")
    if entry is not None and status.upper() == "PUBLISHED":
        subject, simulated = name, False
        view.open_hub(locale="ar")
        held, secs = view.poll_hub(lambda v: name in v.news_titles(), timeout=PROPAGATION_CAP_S, locale="ar")
        record(tc, "fallback via CMS (info)", held=held, seconds=secs)
    else:
        # The CMS refuses a published article without Arabic content, so the
        # missing-translation state is reproduced on the guest feed: the first
        # CARD's Arabic title/excerpt are blanked in the /news response.
        simulated = True
        state: dict = {}

        def _blank(data):
            items = data.get("items") or []
            if len(items) > 1:
                state["subject"] = items[1].get("titleEn")
                items[1] = {**items[1], "titleAr": "", "excerptAr": ""}
            return data

        view.fulfil_json(NEWS_API, _blank)
        view.open_hub(locale="ar")
        subject = state.get("subject", "")
        record(tc, "fallback simulated (info)", reason="CMS refused EN-only publish", subject=subject)
    with allure.step("1-2. /ar hub: News renders; the item shows the EN title + image, no blank card"):
        precondition(view.section_rendered(view.NEWS), "the News section did not render on /ar")
        lead = view.news_lead()
        cards = view.news_cards()
        items = ([{"title": lead.get("title", ""), "img": lead.get("img_src", "")}] if lead else []) + cards
        hit = [c for c in items if c["title"] == subject]
        blank = [c for c in items if not c["title"]]
        shot = view.evidence(f"{tc}_step2_ar_feed")
        record(tc, "ar feed (info)", subject=subject, simulated=simulated, items=items)
        precondition(bool(subject), "no subject item to check")
        if not hit:
            fails.append(f"step 2: {subject!r} is not shown with its EN title on /ar (items {items}); {shot}")
        elif not hit[0]["img"]:
            fails.append(f"step 2: the fallback card has no image; {shot}")
        if blank:
            fails.append(f"step 2: blank-title card(s) on /ar: {blank}; {shot}")
    finish(tc, fails)

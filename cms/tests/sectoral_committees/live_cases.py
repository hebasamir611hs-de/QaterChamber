"""
cms/tests/sectoral_committees/live_cases.py - bodies of the PBI 130716
CONDITIONAL cases that act on the LIVE Sectoral Committees Page entry 181385
(user approval 2026-10-04, Engineer A6). Not a test module.

Runs only under reports/live-restore/live_restore.py's snapshot -> run ->
restore cycle (QC_LIVE_SINGLETON_RUN=181385). Drafts are on for this record
type (Save as Draft + Publish). Values the case names are used verbatim
(several equal the live values: the PUT to the live id is then the proof the
publish went out); open values are QCTEST-marked.
"""

from __future__ import annotations

from cms.pages.sectoral_committees.sectoral_committees_admin_page import (
    LIVE_PAGE_ID,
    SectoralCommitteesPageAdminPage as Page,
)
from cms.tests.sectoral_committees import cc_checks as cc
from cms.tests.sectoral_committees import live_checks as lc
from web.pages.sectoral_committees.sectoral_committees_page import SectoralCommitteesPage as P

LID = LIVE_PAGE_ID
PATH = lc.SC_PATH
SETTLE = P.HERO_TITLE


def _edit_publish(page, fields, flags=None, expect_published=True):
    admin = Page(page)
    lc.open_live(admin, LID)
    for key, (en, ar) in fields.items():
        lc.fill_bi(admin, key, en, ar)
    for key, val in (flags or {}).items():
        admin.set_flag(key, val)
    lc.publish_live(admin, LID, expect_published=expect_published)
    return admin


def _render(page, browser, key, sel, en, ar, timeout=60.0, interval=3.0, prepare=None):
    _edit_publish(page, {key: (en, ar)})
    lc.check_text_both(browser, PATH, sel, en, ar, timeout=timeout, interval=interval, settle_sel=SETTLE,
                       prepare=prepare)


def _visible(p, sel) -> bool:
    loc = p.locator(sel)
    return loc.count() > 0 and loc.first.is_visible()


def _open_anon(browser, locale="en", viewport=None):
    ctx, p = lc.anon(browser, viewport=viewport)
    http = lc.visit(p, PATH, locale, SETTLE)
    return ctx, p, http


def _section_state(browser, timeout=60.0, want=None):
    """{name: visible} for the four sections + Head card, polled until `want`
    (a dict subset) matches or the timeout."""
    import time

    names = {"hero": P.HERO, "sector": P.SECTOR, "lead": P.LEAD_CARD, "directory": P.DIRECTORY, "cta": P.CTA}
    t0 = time.monotonic()
    while True:
        ctx, p, http = _open_anon(browser)
        try:
            st = {n: _visible(p, s) for n, s in names.items()}
            st["rows"] = p.locator(P.VISIBLE_ROW).count()
            st["cta_cards"] = p.locator(P.CTA_CARD).count()
            st["http"] = http
        finally:
            cc._close(ctx)
        if not want or all(st.get(k) == v for k, v in want.items()) or time.monotonic() - t0 > timeout:
            return st
        time.sleep(3)


# ---------------------------------------------------------------------------
# hero
# ---------------------------------------------------------------------------
def tc_146892(page, browser):
    _render(page, browser, "hero_title", P.HERO_TITLE, "Sectoral Committees and Business Councils",
            "اللجان القطاعية ومجالس الأعمال", timeout=5.0, interval=0.5)


def tc_146863(page, browser):
    _render(page, browser, "hero_title", P.HERO_TITLE, "QCTEST Published Title", "عنوان اختبار",
            timeout=5.0, interval=0.5)


def tc_146888(page, browser):
    _render(page, browser, "hero_eyebrow", P.HERO_EYEBROW, "Committees & Business Councils",
            "اللجان ومجالس الأعمال", timeout=5.0, interval=0.5)


def tc_146897(page, browser):
    _render(page, browser, "hero_subtitle", P.HERO_SUBTITLE, "QCTEST 146897 explore the sectoral committees",
            "اختبار 146897 تعرّف على اللجان القطاعية")


def tc_146901(page, browser):
    admin = Page(page)
    name = "hero-1.5MB.jpg"
    fx = lc.exact_name_copy(cc.runtime_fixture("hero_1_5mb.jpg", "jpg", int(1.5 * cc.MB)), name)
    lc.open_live(admin, LID)
    admin.upload_file(Page.FIELDS["hero_bg"].label, fx)
    readout = admin.uploaded_filename(Page.FIELDS["hero_bg"].label)
    assert "hero-1.5MB" in readout, f"Hero Background Image readout is {readout!r} (no thumbnail / file shown)"
    lc.publish_live(admin, LID)
    ctx, p, _ = _open_anon(browser, viewport=(1920, 1080))
    try:
        info = p.evaluate("""(h) => { const r = document.querySelector(h); if (!r) return null;
            const imgs = [...r.querySelectorAll('img')].map(i => [i.currentSrc || i.src, i.naturalWidth]);
            const bgs = [...r.querySelectorAll('*')].concat([r]).map(e => getComputedStyle(e).backgroundImage)
              .filter(b => b && b !== 'none'); return {imgs, bgs}; }""", P.HERO)
        assert info, "no hero rendered"
        srcs = " ".join([s for s, _ in info["imgs"]] + info["bgs"])
        assert "hero-1.5MB" in srcs or "hero-1.5mb" in srcs.lower(), f"the hero does not use the uploaded image: {info!r}"
        broken = [s for s, w in info["imgs"] if not w]
        assert not broken, f"broken hero image(s): {broken!r}"
        assert _visible(p, P.HERO_TITLE), "hero text is not shown over the image"
    finally:
        cc._close(ctx)


def tc_146903(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    how = lc.clear_file(admin, "hero_bg")
    print(f"[tc_146903] Hero Background Image cleared via {how!r}")
    lc.publish_live(admin, LID)
    data = lc.live_json(admin, LID)
    assert not (data.get("heroBackgroundImage") or {}).get("id"), f"image still stored: {data.get('heroBackgroundImage')!r}"
    ctx, p, _ = _open_anon(browser)
    try:
        broken = p.evaluate("""(h) => [...document.querySelectorAll(h + ' img')].filter(i => !i.naturalWidth)
            .map(i => i.currentSrc || i.src || '(no src)')""", P.HERO)
        assert not broken, f"the hero shows a broken image: {broken!r}"
        assert _visible(p, P.HERO_TITLE) and cc.squash(p.locator(P.HERO_TITLE).first.inner_text()), "hero title not readable"
    finally:
        cc._close(ctx)


# ---------------------------------------------------------------------------
# sector representation + Head card
# ---------------------------------------------------------------------------
def tc_146907(page, browser):
    _render(page, browser, "sector_eyebrow", P.SECTOR_EYEBROW, "Sector representation", "تمثيل القطاعات")


def tc_146911(page, browser):
    _render(page, browser, "sector_heading", P.SECTOR_HEADING, "QCTEST 146911 where insight informs action",
            "اختبار 146911 حيث توجه الرؤية القرارات")


def tc_146915(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    lc.type_rich_bold(admin, "sector_body", "QCTEST 146915 sectoral committees bring together ", "business leaders",
                      " to review market priorities.")
    ar = "اختبار 146915 تجمع اللجان القطاعية قادة الأعمال."
    lc.set_rich_html(admin, "sector_body", f"<p>{ar}</p>", "ar")
    lc.publish_live(admin, LID)
    lc.check_text_both(browser, PATH, P.SECTOR_BODY, "QCTEST 146915", ar, settle_sel=SETTLE)
    ctx, p, _ = _open_anon(browser)
    try:
        bold = p.locator(f"{P.SECTOR_BODY} :is(strong, b)").filter(has_text="business leaders")
        assert bold.count(), f"'business leaders' is not bold: {p.locator(P.SECTOR_BODY).first.inner_html()[:300]!r}"
    finally:
        cc._close(ctx)


def tc_146919(page, browser):
    """Payload: a script that sets a page marker (no visitor-facing alert on the
    shared live page); executed == the marker is set or a dialog opens."""
    admin = Page(page)
    lc.open_live(admin, LID)
    payload = "<p>Sector text</p><script>window.__qctest146919=1;</script>"
    lc.set_rich_html(admin, "sector_body", payload)
    admin.submit_for_review()
    print(f"[tc_146919] submit: saved={lc.saved(admin, LID)} {admin.save_counts()}")
    ctx, p = lc.anon(browser)
    dialogs = []
    p.on("dialog", lambda d: (dialogs.append(d.message), d.dismiss()))
    try:
        lc.visit(p, PATH, "en", SETTLE)
        p.wait_for_timeout(2000)
        executed = p.evaluate("() => window.__qctest146919 === 1")
        scripts = p.locator(f"{P.SECTOR_BODY} script").count()
        raw = "<script" in (p.locator(P.SECTOR_BODY).first.inner_text() if p.locator(P.SECTOR_BODY).count() else "")
        assert not dialogs and not executed, f"the script markup EXECUTED on the public page (dialogs {dialogs!r}, marker {executed})"
        assert scripts == 0, f"an active <script> element is rendered in the Sector body ({scripts})"
        assert not raw, "raw '<script' markup is shown as text in the Sector body"
    finally:
        cc._close(ctx)


def tc_146920(page, browser):
    _render(page, browser, "card_eyebrow", P.LEAD_EYEBROW, "Leadership directory", "دليل القيادات")


def tc_146924(page, browser):
    _render(page, browser, "card_title", P.LEAD_TITLE, "QCTEST 146924 Head of Sectoral committees",
            "اختبار 146924 رؤساء اللجان القطاعية")


def tc_146928(page, browser):
    _render(page, browser, "card_description", P.LEAD_DESC, "QCTEST 146928 view committee leaders",
            "اختبار 146928 تعرّف على رؤساء اللجان")


def tc_146932(page, browser):
    _edit_publish(page, {}, {"sector_active": True})
    st = _section_state(browser, want={"sector": True, "lead": True})
    assert st["sector"] and st["lead"], f"Sector representation / Head card not shown: {st}"
    ctx, p, _ = _open_anon(browser)
    try:
        for sel in (P.SECTOR_EYEBROW, P.SECTOR_HEADING, P.SECTOR_BODY):
            assert _visible(p, sel) and p.locator(sel).first.inner_text().strip(), f"{sel} is not shown"
    finally:
        cc._close(ctx)


def tc_146933(page, browser):
    _edit_publish(page, {}, {"sector_active": False})
    st = _section_state(browser, want={"sector": False, "lead": False})
    assert not st["sector"] and not st["lead"], f"Sector representation / Head card still shown: {st}"
    assert st["hero"] and st["directory"] and st["cta"], f"other sections disappeared: {st}"


# ---------------------------------------------------------------------------
# committee directory
# ---------------------------------------------------------------------------
def tc_146952(page, browser):
    _render(page, browser, "dir_eyebrow", P.DIR_EYEBROW, "Committee directory", "دليل اللجان")


def tc_146956(page, browser):
    _render(page, browser, "dir_heading", P.DIR_HEADING, "QCTEST 146956 Explore the Committees",
            "اختبار 146956 استكشف اللجان")


def tc_146960(page, browser):
    _render(page, browser, "dir_body", P.DIR_BODY, "QCTEST 146960 open any committee to review its mandate",
            "اختبار 146960 افتح أي لجنة لمراجعة صلاحياتها")


def tc_146964(page, browser):
    import time

    _edit_publish(page, {"search_placeholder": ("Search by committee or sector", "البحث حسب اللجنة أو القطاع")})
    for loc, want in (("en", "Search by committee or sector"), ("ar", "البحث حسب اللجنة أو القطاع")):
        t0, got = time.monotonic(), None
        while True:
            ctx, p, _ = _open_anon(browser, loc)
            try:
                box = p.locator(P.SEARCH).first
                got = (box.get_attribute("placeholder") if box.count() else None, box.input_value() if box.count() else None)
            finally:
                cc._close(ctx)
            if got[0] == want or time.monotonic() - t0 > 60:
                break
            time.sleep(3)
        assert got[0] == want and not got[1], f"{loc.upper()} empty search input placeholder is {got!r}, expected {want!r}"


def tc_146968(page, browser):
    _edit_publish(page, {}, {"dir_active": True})
    st = _section_state(browser, want={"directory": True})
    assert st["directory"], f"Committee directory not shown: {st}"
    ctx, p, _ = _open_anon(browser)
    try:
        for sel in (P.DIR_EYEBROW, P.DIR_HEADING, P.DIR_BODY, P.SEARCH):
            assert _visible(p, sel), f"{sel} is not shown"
        assert p.locator(P.VISIBLE_ROW).count() == 12, f"directory shows {p.locator(P.VISIBLE_ROW).count()} rows, case expects 12"
    finally:
        cc._close(ctx)


def tc_146969(page, browser):
    _edit_publish(page, {}, {"dir_active": False})
    st = _section_state(browser, want={"directory": False})
    assert not st["directory"] and st["rows"] == 0, f"Committee directory still shown: {st}"
    assert st["hero"] and st["sector"] and st["cta"], f"other sections disappeared: {st}"


def _mandate(page, browser, key, sel, en, ar):
    import time

    _edit_publish(page, {key: (en, ar)})
    for loc, want, n in (("en", en, 2), ("ar", ar, 1)):
        t0 = time.monotonic()
        while True:
            ctx, p, _ = _open_anon(browser, loc)
            try:
                got = []
                rows = p.locator(P.ROW)
                for i in range(min(n, rows.count())):
                    head = rows.nth(i).locator(P.ROW_HEAD).first
                    if head.get_attribute("aria-expanded") != "true":
                        head.click()
                        p.wait_for_timeout(600)
                    t = rows.nth(i).locator(f"{P.ROW_PANEL} {sel}")
                    got.append(cc.squash(t.first.inner_text()) if t.count() else "")
            finally:
                cc._close(ctx)
            if (len(got) == n and all(g == want for g in got)) or time.monotonic() - t0 > 60:
                break
            time.sleep(3)
        assert len(got) == n and all(g == want for g in got), f"{loc.upper()} expanded panels show {got!r}, expected {want!r}"


def tc_146982(page, browser):
    _mandate(page, browser, "mandate_eyebrow", P.MANDATE_EYEBROW, "Committee competencies", "اختصاصات اللجنة")


def tc_146986(page, browser):
    _mandate(page, browser, "mandate_heading", P.MANDATE_HEADING, "Mandate and responsibilities", "الصلاحيات والمسؤوليات")


# ---------------------------------------------------------------------------
# CTA panel
# ---------------------------------------------------------------------------
def tc_146994(page, browser):
    _render(page, browser, "cta_eyebrow", P.CTA_EYEBROW, "QCTEST 146994 Continue with Qatar Chamber",
            "اختبار 146994 المتابعة مع غرفة قطر")


def tc_146998(page, browser):
    _render(page, browser, "cta_heading", P.CTA_HEADING, "QCTEST 146998 Choose the appropriate request",
            "اختبار 146998 اختر الطلب المناسب")


def tc_147002(page, browser):
    _render(page, browser, "cta_body", P.CTA_BODY, "QCTEST 147002 use the relevant form",
            "اختبار 147002 استخدم النموذج المناسب")


def tc_147006(page, browser):
    _edit_publish(page, {}, {"cta_active": True})
    st = _section_state(browser, want={"cta": True})
    assert st["cta"] and st["cta_cards"] == 3, f"CTA panel / its three cards not shown: {st}"


def tc_147007(page, browser):
    _edit_publish(page, {}, {"cta_active": False})
    st = _section_state(browser, want={"cta": False})
    assert not st["cta"] and st["cta_cards"] == 0, f"CTA panel still shown: {st}"
    assert st["hero"] and st["sector"] and st["directory"], f"other sections disappeared: {st}"


# ---------------------------------------------------------------------------
# page-level visibility / workflow
# ---------------------------------------------------------------------------
def tc_146905(page, browser):
    _edit_publish(page, {}, {"page_active": True})
    for loc in ("en", "ar"):
        lc.assert_served(browser, PATH, P.HERO_TITLE, loc)


def tc_146906(page, browser):
    _edit_publish(page, {}, {"page_active": False}, expect_published=False)
    for loc in ("en", "ar"):
        lc.assert_not_served(browser, PATH, P.HERO_TITLE, loc)


def tc_147051(page, browser):
    import time

    ctx, p, http = _open_anon(browser)
    try:
        assert http == 200 and _visible(p, P.HERO_TITLE), f"precondition: the page is not displayed (HTTP {http})"
        _edit_publish(page, {}, {"page_active": False}, expect_published=False)
        t0 = time.monotonic()
        while True:
            resp = p.reload(wait_until="domcontentloaded")
            p.wait_for_timeout(2500)
            gone = (resp and resp.status >= 400) or not _visible(p, P.HERO_TITLE)
            if gone or time.monotonic() - t0 > 60:
                break
            time.sleep(3)
        assert gone, f"the reloaded visitor tab still shows the committee content (HTTP {resp.status if resp else None})"
    finally:
        cc._close(ctx)


def _unpublish(page):
    admin = Page(page)
    lc.row_action_live(admin, LID, "unpublish")
    st = lc.wait_status(admin, LID, "Unpublished")
    assert st == "Unpublished", f"after Unpublish the record is {st!r}"
    return admin


def tc_146864(page, browser):
    _unpublish(page)
    for loc in ("en", "ar"):
        lc.assert_not_served(browser, PATH, P.HERO_TITLE, loc)


def tc_146868(page, browser):
    _unpublish(page)
    for loc in ("en", "ar"):
        lc.assert_not_served(browser, PATH, P.HERO_TITLE, loc)
    ctx, p = lc.anon(browser)
    try:
        lc.visit(p, "/web/qatar-chamber", "en", P.HEADER)
        link = p.locator(P.NAV_PAGE_LINK)
        if link.count():
            href = link.first.get_attribute("href")
            resp = p.goto(href if href.startswith("http") else lc.web_url(href), wait_until="domcontentloaded")
            p.wait_for_timeout(2500)
            assert (resp and resp.status >= 400) or not _visible(p, P.HERO_TITLE), (
                f"the menu link {href!r} still serves the committee content (HTTP {resp.status if resp else None})")
    finally:
        cc._close(ctx)


def tc_146850(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    admin.fill("hero_eyebrow", "QCTEST Eyebrow")
    lc.save_draft_live(admin, LID)
    # Preview (the record's own preview surface, authenticated)
    prev = page.locator('a:has-text("Preview")').first
    if prev.count() and prev.get_attribute("href"):
        pv = page.context.new_page()
        try:
            pv.goto(prev.get_attribute("href"), wait_until="domcontentloaded")
            pv.wait_for_timeout(3000)
            assert "QCTEST Eyebrow" in pv.locator("body").inner_text(), "Preview does not render the draft change"
        finally:
            pv.close()
    else:
        raise AssertionError("the draft offers no Preview link")
    lc.open_live(admin, LID)
    lc.publish_live(admin, LID)
    lc.check_text_both(browser, PATH, P.HERO_EYEBROW, "QCTEST Eyebrow", None, settle_sel=SETTLE)
    lc.row_action_live(admin, LID, "unpublish")
    lc.assert_not_served(browser, PATH, P.HERO_TITLE, "en")


def tc_147052(page, browser):
    def snap():
        ctx, p, _ = _open_anon(browser)
        try:
            head = p.locator(P.LEAD_HEAD).first
            if head.count() and head.get_attribute("aria-expanded") != "true":
                head.click()
                p.wait_for_timeout(600)
            return {"leaders": [cc.squash(t) for t in p.locator(P.LEADER_NAME).all_inner_texts()],
                    "committees": [cc.squash(t) for t in p.locator(P.ROW_TITLE).all_inner_texts()],
                    "ctas": [cc.squash(t) for t in p.locator(P.CTA_TITLE).all_inner_texts()]}
        finally:
            cc._close(ctx)

    before = snap()
    print(f"[tc_147052] noted: {len(before['leaders'])} leaders, {len(before['committees'])} committees, "
          f"{len(before['ctas'])} CTA titles")
    assert before["leaders"] and before["committees"] and before["ctas"], f"precondition: nothing to note {before}"
    admin = _unpublish(page)
    lc.row_action_live(admin, LID, "publish")
    st = lc.wait_status(admin, LID, "Published")
    assert st == "Published", f"Publish after Unpublish left the record {st!r}"
    import time

    t0 = time.monotonic()
    while True:
        after = snap()
        if after == before or time.monotonic() - t0 > 60:
            break
        time.sleep(3)
    assert after == before, f"re-published page differs: before={before} after={after}"

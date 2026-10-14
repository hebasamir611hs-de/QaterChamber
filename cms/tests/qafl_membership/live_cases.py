"""
cms/tests/qafl_membership/live_cases.py - bodies of the PBI 130718 CONDITIONAL
cases that act on the LIVE QAFL Page Content entry 208073 (user approval
2026-10-04, Engineer A6). Not a test module.

Runs only under reports/live-restore/live_restore.py's snapshot -> run ->
restore cycle (QC_LIVE_SINGLETON_RUN=208073). Drafts are off for the
Editor's record type (the form's submit reads "Publish").
"""

from __future__ import annotations

from pathlib import Path

from cms.pages.components.disposable_object_admin import ROLE_EDITOR
from cms.pages.qafl_membership.qafl_membership_admin_page import LIVE_PAGE_ID, QaflPageContentAdminPage as Page
from cms.tests.sectoral_committees import cc_checks as cc
from cms.tests.sectoral_committees import live_checks as lc
from config.settings import cms_role_credentials

LID = LIVE_PAGE_ID
PATH = lc.QAFL_PATH
H1 = "h1.qc-qafl-hero__title"
SUB = "p.qc-qafl-hero__subtitle"
HERO = "section.qc-qafl-hero"
MOTIF = "span.qc-qafl-hero__motif"
EYEBROW = "span.qc-qafl-overview__eyebrow"
HEADING = "h2.qc-qafl-overview__heading"
BODY = "div.qc-qafl-overview__body"
CARD_EYEBROW = "span.qc-qafl-card__eyebrow"
CARD_TITLE = "h3.qc-qafl-card__title"
CARD_DESC = "p.qc-qafl-card__desc"
DOWNLOAD = "a.qc-qafl-card__download"
MENU = "header.qc-global-site-header"


def _render(page, browser, tc, key, sel, en, ar):
    admin = Page(page)
    lc.open_live(admin, LID)
    lc.fill_bi(admin, key, en, ar)
    lc.publish_live(admin, LID)
    lc.check_text_both(browser, PATH, sel, en, ar)


def tc_146751(page, browser):
    _render(page, browser, 146751, "hero_title", H1, "QCTEST 146751 QAFL Membership Registration",
            "تسجيل عضوية QAFL اختبار 146751")


def tc_146755(page, browser):
    _render(page, browser, 146755, "hero_subtitle", SUB, "QCTEST 146755 register your company for QAFL membership",
            "اختبار 146755 سجل شركتك لعضوية QAFL")


def tc_146764(page, browser):
    _render(page, browser, 146764, "section_eyebrow", EYEBROW, "QCTEST 146764 About", "اختبار 146764 عن الجمعية")


def tc_146768(page, browser):
    _render(page, browser, 146768, "section_heading", HEADING, "QCTEST 146768 overview heading",
            "اختبار 146768 نظرة عامة")


def tc_146779(page, browser):
    _render(page, browser, 146779, "card_eyebrow", CARD_EYEBROW, "QCTEST 146779 Required template",
            "اختبار 146779 النموذج المطلوب")


def tc_146783(page, browser):
    _render(page, browser, 146783, "card_title", CARD_TITLE, "QCTEST 146783 Authorization Letter",
            "اختبار 146783 خطاب التفويض")


def tc_146787(page, browser):
    _render(page, browser, 146787, "card_description", CARD_DESC, "QCTEST 146787 download and complete the template",
            "اختبار 146787 قم بتنزيل النموذج")


def tc_146791(page, browser):
    _render(page, browser, 146791, "download_label", DOWNLOAD, "QCTEST 146791 Download Letter",
            "اختبار 146791 تنزيل الخطاب")


def tc_146565(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    lc.fill_bi(admin, "section_eyebrow", None, "عن الجمعية QCTEST")
    lc.publish_live(admin, LID)
    lc.check_text_both(browser, PATH, EYEBROW, None, "عن الجمعية QCTEST")
    ctx, p = lc.anon(browser)
    try:
        lc.visit(p, PATH, "ar", EYEBROW)
        direction = p.locator(EYEBROW).first.evaluate("e => getComputedStyle(e).direction")
        assert direction == "rtl", f"AR eyebrow direction is {direction!r}"
    finally:
        cc._close(ctx)
    ok, got, _ = lc.poll_text(browser, PATH, EYEBROW, "About the association", "en", timeout=10)
    assert ok, f"EN eyebrow changed: {got!r} (expected unchanged 'About the association')"


def tc_146772(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    link = "https://www.qatarchamber.com/"
    lc.set_rich_html(admin, "section_body",
                     f'<p>QCTEST 146772 <strong>bold overview</strong> with a <a href="{link}">working link</a>.</p>')
    lc.set_rich_html(admin, "section_body",
                     f'<p>اختبار 146772 <strong>نص عريض</strong> مع <a href="{link}">رابط فعال</a>.</p>', "ar")
    lc.publish_live(admin, LID)
    for loc, bold, anchor in (("en", "bold overview", "working link"), ("ar", "نص عريض", "رابط فعال")):
        ok, got, _ = lc.poll_text(browser, PATH, BODY, bold, loc)
        assert ok, f"{loc.upper()} body does not show {bold!r}: {got[:160]!r}"
        ctx, p = lc.anon(browser)
        try:
            lc.visit(p, PATH, loc, BODY)
            b = p.locator(f"{BODY} :is(strong, b)").filter(has_text=bold)
            a = p.locator(f"{BODY} a").filter(has_text=anchor)
            assert b.count(), f"{loc.upper()}: {bold!r} is not bold on the public page"
            assert a.count() and (a.first.get_attribute("href") or "").rstrip("/") == link.rstrip("/"), (
                f"{loc.upper()}: the link {anchor!r} is missing or points elsewhere "
                f"({a.first.get_attribute('href') if a.count() else None!r})")
            resp = p.request.get(a.first.get_attribute("href"))
            assert resp.status < 400, f"{loc.upper()}: the body link answers HTTP {resp.status}"
        finally:
            cc._close(ctx)


def tc_146805(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    en = [f"QCTEST 146805 point {i}" for i in range(1, 6)]
    ar = [f"اختبار 146805 نقطة {i}" for i in range(1, 6)]
    lc.set_rich_html(admin, "section_body", "<ul>" + "".join(f"<li>{x}</li>" for x in en) + "</ul>")
    lc.set_rich_html(admin, "section_body", "<ul>" + "".join(f"<li>{x}</li>" for x in ar) + "</ul>", "ar")
    lc.publish_live(admin, LID)
    for loc, want in (("en", en), ("ar", ar)):
        ok, got, _ = lc.poll_text(browser, PATH, BODY, want[0], loc)
        assert ok, f"{loc.upper()} body does not show the bullets: {got[:160]!r}"
        ctx, p = lc.anon(browser)
        try:
            lc.visit(p, PATH, loc, BODY)
            items = [cc.squash(t) for t in p.locator(f"{BODY} li").all_inner_texts()]
            assert items == want, f"{loc.upper()} bullets are {items!r}, expected exactly {want!r}"
        finally:
            cc._close(ctx)


def tc_146552(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    lc.save_draft_live(admin, LID)
    for loc in ("en", "ar"):
        lc.assert_not_served(browser, PATH, H1, loc)


def tc_146554(page, browser):
    admin = Page(page)
    en, ar = "QAFL Membership Registration QCTEST", "تسجيل عضوية QAFL QCTEST"
    lc.open_live(admin, LID)
    lc.fill_bi(admin, "hero_title", en, ar)
    lc.save_draft_live(admin, LID)
    lc.open_live(admin, LID)
    lc.publish_live(admin, LID)
    hist = lc.history_live(admin, LID)
    assert hist, "no History (audit) entry is listed for the publish"
    lc.check_text_both(browser, PATH, H1, en, ar)


def tc_146555(page, browser):
    admin = Page(page)
    lc.row_action_live(admin, LID, "unpublish")
    st = lc.wait_status(admin, LID, "Unpublished")
    assert st == "Unpublished", f"after Unpublish the record is {st!r}"
    lc.assert_not_served(browser, PATH, H1, "en")
    # republish, then Page Active Status = Inactive
    lc.row_action_live(admin, LID, "publish")
    st = lc.wait_status(admin, LID, "Published")
    assert st == "Published", f"republish left the record {st!r}"
    lc.open_live(admin, LID)
    admin.set_flag("page_active", False)
    lc.publish_live(admin, LID, expect_published=False)
    lc.assert_not_served(browser, PATH, H1, "en")
    ctx, p = lc.anon(browser)
    try:
        lc.visit(p, "/web/qatar-chamber", "en", MENU)
        links = p.locator(f'{MENU} a[href*="qafl-membership"]').count()
        assert links == 0, f"the site menu still links the inactive QAFL page ({links} link(s))"
    finally:
        cc._close(ctx)


def tc_146763(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    admin.set_flag("page_active", True)
    lc.publish_live(admin, LID)
    lc.assert_served(browser, PATH, H1, "en")
    ctx, p = lc.anon(browser)
    try:
        lc.visit(p, "/web/qatar-chamber", "en", MENU)
        menu = cc.squash(p.locator(MENU).first.evaluate("e => e.textContent"))
        assert "QAFL Membership Registration" in menu, (
            f"the site menu has no 'QAFL Membership Registration' entry (links to the page: "
            f"{p.locator(f'{MENU} a[href*=qafl-membership]').count()})")
    finally:
        cc._close(ctx)


def tc_146795(page, browser):
    admin = Page(page)
    name = "QAFL-Authorization-Letter-v2.docx"
    fx = lc.exact_name_copy(cc.runtime_fixture("qafl_letter_3mb.docx", "docx", 3 * cc.MB), name)
    lc.open_live(admin, LID)
    admin.upload_file(Page.FIELDS["template_file"].label, fx)
    readout = admin.uploaded_filename(Page.FIELDS["template_file"].label)
    assert name in readout, f"Template File readout is {readout!r} after uploading {name}"
    lc.publish_live(admin, LID)
    data = lc.live_json(admin, LID)
    key = lc.file_key(data, "template")
    assert key and (data[key] or {}).get("name") == name, f"stored template file is {data.get(key)!r}"
    fname, blob = lc.download_from(browser, PATH, DOWNLOAD)
    assert fname == name, f"the public download is {fname!r}, expected {name!r}"
    assert blob == Path(fx).read_bytes(), f"the downloaded {fname} ({len(blob)} B) is not the uploaded file"


def tc_146559(page, browser):
    admin = Page(page)
    lc.open_live(admin, LID)
    admin.fill("hero_title", "QCTEST 146559 QAFL Membership Registration")
    lc.publish_live(admin, LID)
    hist = lc.history_live(admin, LID)
    print(f"[tc_146559] history: {hist[:3]}")
    assert hist, "the Editor gets no audit log (History) for the page record"
    newest = hist[0]
    email = cms_role_credentials(ROLE_EDITOR)[0]
    assert newest["who"] and newest["when"], f"the newest audit entry carries no user / timestamp: {newest!r}"
    assert any(w in newest["action"].lower() for w in ("publish", "edit", "updat")), (
        f"the newest audit entry is not the publish action: {newest!r} (editor {email})")


def tc_146759(page, browser):
    admin = Page(page)
    name = "hero-bg.png"
    fx = lc.exact_name_copy(cc.runtime_fixture("hero_bg_1_5mb.png", "png", int(1.5 * cc.MB)), name)
    lc.open_live(admin, LID)
    admin.upload_file(Page.FIELDS["hero_bg"].label, fx)
    readout = admin.uploaded_filename(Page.FIELDS["hero_bg"].label)
    assert name.split(".")[0] in readout, f"Hero Background Image readout is {readout!r}"
    lc.publish_live(admin, LID)
    ctx, p = lc.anon(browser)
    try:
        lc.visit(p, PATH, "en", H1)
        used = p.evaluate("""(sel) => { const h = document.querySelector(sel); if (!h) return '';
            const urls = [...h.querySelectorAll('*')].concat([h]).map(e => getComputedStyle(e).backgroundImage)
              .filter(b => b && b !== 'none'); const imgs = [...h.querySelectorAll('img')].map(i => i.currentSrc || i.src);
            return urls.concat(imgs).join(' '); }""", HERO)
        assert "hero-bg" in used, f"the public hero does not render hero-bg.png (hero images: {used[:300]!r})"
    finally:
        cc._close(ctx)


def tc_146762(page, browser):
    admin = Page(page)
    before = lc.open_live(admin, LID)
    how = lc.clear_file(admin, "hero_bg")
    print(f"[tc_146762] hero image cleared via {how!r}")
    lc.publish_live(admin, LID)
    data = lc.live_json(admin, LID)
    key = lc.file_key(data, "hero")
    assert not (data.get(key) or {}).get("id"), f"the hero image is still stored: {data.get(key)!r}"
    ctx, p = lc.anon(browser)
    try:
        lc.visit(p, PATH, "en", H1)
        assert p.locator(MOTIF).count() and p.locator(MOTIF).first.is_visible(), "the default hero pattern is not shown"
        assert cc.squash(p.locator(H1).first.inner_text()) == (before.get("heroTitle_i18n") or {}).get("en_US"), \
            "the hero title is not intact"
        assert p.locator(SUB).first.inner_text().strip(), "the hero subtitle is not intact"
    finally:
        cc._close(ctx)

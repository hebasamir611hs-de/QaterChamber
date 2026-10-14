"""
cms/tests/live_b11_cases.py - one check per CONDITIONAL live case of PBIs
130947 / 130949 / 130720 (Engineer B11, 2026-10-04). Not a test module; the
test functions in each PBI's test file call these. Mechanics, approval and
the restore contract: cms/tests/live_b11.py.

Account for every write: QC Site Content Editor (cms_role_credentials via
open_list(ROLE_EDITOR)). Public checks: fresh logged-out context.
"""

from __future__ import annotations

import re

from cms.tests import live_b11 as lb
from cms.tests.live_b11 import COO_PATH, PFR_PATH, PO_PATH, squash, texts, buttons
from web.pages.certificate_of_origin.certificate_of_origin_page import CertificateOfOriginPage as C
from web.pages.partners_offers.partners_offers_page import PartnersOffersPage as P
from web.pages.proposal_for_research.proposal_for_research_page import ProposalForResearchPage as R

COO_PAGE, CTA_LOGIN, CTA_VERIFY, DOC_REQ = "93657", "93663", "93667", "93860"
PFR_PAGE, PFR_OVERVIEW, PO_PAGE = "99844", "99886", "167087"


# ===========================================================================
# helpers per page
# ===========================================================================
def _coo_ctas(p) -> dict:
    return {"hero": buttons(p, C.HERO_CTA), "banner": buttons(p, C.BANNER_CTA)}


def _labels(lst) -> list[str]:
    return [b["label"] for b in lst]


def _coo_banner(p) -> dict:
    return {"present": p.locator(C.BANNER).count(), "eyebrow": texts(p, C.BANNER_EYEBROW),
            "title": texts(p, C.BANNER_TITLE), "body": texts(p, C.BANNER_BODY),
            "eyebrow_nodes": p.locator(C.BANNER_EYEBROW).count(), "body_nodes": p.locator(C.BANNER_BODY).count(),
            "ctas": _labels(buttons(p, C.BANNER_CTA)),
            "first_line": squash((p.locator(C.BANNER).first.inner_text() if p.locator(C.BANNER).count() else "")
                                 ).split(" Choose")[0][:80]}


def _set_flag(admin, key, value: bool):
    admin.fill(key, "true" if value else "false")


# ===========================================================================
# 130947 Certificate of Origin - COO Call To Action 93663 / 93667
# ===========================================================================
def coo_141001(page, browser, A):
    """Edit the shared 'Login to COO' CTA: label + redirect; both locations follow."""
    admin = A(page)
    lb.open_live(admin, CTA_LOGIN)
    label, url = "Login to COO QCTEST-130947", "https://coo.qatarchamber.com/login?src=qctest"
    admin.fill("cta_label", label)
    admin.fill("redirect_url", url)
    lb.publish(admin, CTA_LOGIN)

    def probe(p, http):
        c = _coo_ctas(p)
        h = [b for b in c["hero"] if b["label"] == label]
        b = [x for x in c["banner"] if x["label"] == label]
        stale = [x for x in c["hero"] + c["banner"] if x["label"] == "Login to COO"]
        ok = bool(h and b) and h[0]["href"] == url and b[0]["href"] == url and not stale
        return ok, c

    lb.expect_public(browser, COO_PATH, probe, f"hero AND banner button {label!r} -> {url}, no old 'Login to COO'",
                     settle_sel=C.HERO_CTA)


def coo_141022(page, browser, A):
    """CTA Key 'coo-login-qctest-130947' saves, persists, and the button still
    renders in hero and banner resolved through the key."""
    admin = A(page)
    # Discriminating pre-state (coordinator 2026-10-04): the label is first
    # published as a marker, so the final 'Login to COO' can only come from a
    # change that reached the page through the NEW key, never a stale render.
    pre = "Login to COO QCTEST-141022-pre"
    lb.open_live(admin, CTA_LOGIN)
    admin.fill("cta_label", pre)
    lb.publish(admin, CTA_LOGIN)
    lb.expect_public(browser, COO_PATH, lambda p, h: (pre in _labels(_coo_ctas(p)["hero"]), _coo_ctas(p)),
                     f"pre-state marker {pre!r} live", settle_sel=C.HERO_CTA)
    lb.open_live(admin, CTA_LOGIN)
    key = "coo-login-qctest-130947"
    admin.fill("cta_key", key)
    admin.fill("cta_label", "Login to COO")
    lb.publish(admin, CTA_LOGIN)
    lb.open_live(admin, CTA_LOGIN)  # reload the record
    after = lb.live_json(admin, CTA_LOGIN)
    assert after.get("ctaKey") == key, f"CTA Key did not persist: {after.get('ctaKey')!r}"

    def probe(p, http):
        c = _coo_ctas(p)
        all_labels = _labels(c["hero"]) + _labels(c["banner"])
        ok = ("Login to COO" in _labels(c["hero"]) and "Login to COO" in _labels(c["banner"])
              and pre not in all_labels and not any(re.search(r"\$\{|\{\{|coo-login-qctest", x) for x in all_labels))
        return ok, c

    lb.expect_public(browser, COO_PATH, probe, "'Login to COO' in hero AND banner after the key change",
                     settle_sel=C.HERO_CTA)


def coo_141029(page, browser, A):
    admin = A(page)
    lb.open_live(admin, CTA_VERIFY)
    url = "https://coo.qatarchamber.com/verify"
    admin.fill("redirect_url", url)
    lb.publish(admin, CTA_VERIFY)
    lb.open_live(admin, CTA_VERIFY)  # reload the record
    got = admin.value("redirect_url")
    assert got == url, f"Redirect URL after reload is {got!r}, expected {url!r}"

    def probe(p, http):
        c = _coo_ctas(p)
        hrefs = [b["href"] for b in c["hero"] + c["banner"] if b["label"] == "Verify Certificate"]
        return bool(hrefs) and all(h == url for h in hrefs), c

    lb.expect_public(browser, COO_PATH, probe, f"'Verify Certificate' href exactly {url}", settle_sel=C.HERO_CTA)


def _blocked_url(page, A, value, what):
    admin = A(page)
    before = lb.open_live(admin, CTA_LOGIN)
    assert before.get("activeStatus") is True, f"precondition: 'Login to COO' must be Active, is {before.get('activeStatus')!r}"
    admin.fill("redirect_url", value)
    lb.assert_publish_blocked(admin, CTA_LOGIN, before, "redirectUrl", what)


def coo_141031(page, browser, A):
    _blocked_url(page, A, "", "an empty Redirect URL on an Active CTA")


def coo_141032(page, browser, A):
    _blocked_url(page, A, "   ", "a whitespace-only Redirect URL on an Active CTA")


def _open_behavior(page, A, option):
    admin = A(page)
    data = lb.open_live(admin, CTA_LOGIN)
    opts = admin.select_options("open_behavior")
    assert option in opts, f"Open Behavior offers {opts!r}, no {option!r}"
    admin.fill("open_behavior", option)
    lb.publish(admin, CTA_LOGIN)
    return data


def coo_141033(page, browser, A):
    """Same Tab: no target=_blank; a click navigates the current tab, one tab, Back returns."""
    data = _open_behavior(page, A, "Same Tab")
    dest = data.get("redirectUrl") or ""

    def probe(p, http):
        c = _coo_ctas(p)
        h = [b for b in c["hero"] if b["label"] == "Login to COO"]
        return bool(h) and h[0]["target"] != "_blank", c

    lb.expect_public(browser, COO_PATH, probe, "'Login to COO' without target=_blank", settle_sel=C.HERO_CTA)
    ctx, p = lb.anon(browser)
    try:
        lb.visit(p, COO_PATH, settle_sel=C.HERO_CTA)
        start = p.url
        p.locator(C.HERO_CTA).filter(has_text="Login to COO").first.click()
        p.wait_for_load_state("domcontentloaded", timeout=60000)
        p.wait_for_timeout(1500)
        print(f"[141033] after click: url={p.url} tabs={len(ctx.pages)} (case names /login; record holds {dest!r})")
        assert len(ctx.pages) == 1, f"a click opened {len(ctx.pages)} tabs with Same Tab"
        host = re.sub(r"^https?://", "", dest).split("/")[0]
        assert host and host in p.url, f"the current tab did not navigate to {dest!r} (url {p.url})"
        p.go_back(wait_until="domcontentloaded", timeout=60000)
        assert p.url.split("?")[0].rstrip("/") == start.split("?")[0].rstrip("/"), f"Back returned to {p.url}, not {start}"
    finally:
        ctx.close()


def coo_141034(page, browser, A):
    """New Tab: target=_blank; a click opens a second tab, the original stays."""
    data = _open_behavior(page, A, "New Tab")
    dest = data.get("redirectUrl") or ""

    def probe(p, http):
        c = _coo_ctas(p)
        h = [b for b in c["hero"] if b["label"] == "Login to COO"]
        return bool(h) and h[0]["target"] == "_blank", c

    lb.expect_public(browser, COO_PATH, probe, "'Login to COO' with target=_blank", settle_sel=C.HERO_CTA)
    ctx, p = lb.anon(browser)
    try:
        lb.visit(p, COO_PATH, settle_sel=C.HERO_CTA)
        start = p.url
        with ctx.expect_page(timeout=30000) as newp:
            p.locator(C.HERO_CTA).filter(has_text="Login to COO").first.click()
        tab = newp.value
        try:
            tab.wait_for_load_state("domcontentloaded", timeout=60000)
        except Exception:  # noqa: BLE001 - external site load is not the assertion
            pass
        host = re.sub(r"^https?://", "", dest).split("/")[0]
        print(f"[141034] new tab url={tab.url} original={p.url} (case names /login; record holds {dest!r})")
        assert host in tab.url, f"the new tab is on {tab.url}, not {dest!r}"
        assert p.url == start, f"the original tab moved to {p.url}"
    finally:
        ctx.close()


def coo_141035(page, browser, A):
    admin = A(page)
    lb.open_live(admin, CTA_VERIFY)
    _set_flag(admin, "active_status", True)
    lb.publish(admin, CTA_VERIFY)

    def probe(p, http):
        c = _coo_ctas(p)
        ok = (len(c["hero"]) == 2 and len(c["banner"]) == 2 and c["hero"][1]["label"] == "Verify Certificate"
              and c["banner"][1]["label"] == "Verify Certificate" and c["hero"][1]["href"] == c["banner"][1]["href"])
        return ok, c

    lb.expect_public(browser, COO_PATH, probe, "two buttons in hero and banner, second 'Verify Certificate', same href",
                     settle_sel=C.HERO_CTA)


def _verify_hidden_probe(p, http):
    c = _coo_ctas(p)
    ok = _labels(c["hero"]) == ["Login to COO"] and _labels(c["banner"]) == ["Login to COO"]
    slots = {"hero_nodes": p.locator(C.HERO_CTA).count(), "banner_nodes": p.locator(C.BANNER_CTA).count()}
    return ok and slots["hero_nodes"] == 1 and slots["banner_nodes"] == 1, {**c, **slots}


def coo_141036(page, browser, A):
    admin = A(page)
    lb.open_live(admin, CTA_VERIFY)
    _set_flag(admin, "active_status", False)
    lb.publish(admin, CTA_VERIFY, expect_published=False)
    assert lb.saved(admin, CTA_VERIFY)
    lb.expect_public(browser, COO_PATH, _verify_hidden_probe,
                     "exactly one button 'Login to COO' in hero AND banner, no empty slot", settle_sel=C.HERO_CTA)


def coo_141177(page, browser, A):
    admin = A(page)
    lb.open_live(admin, CTA_VERIFY)
    _set_flag(admin, "active_status", False)
    admin.fill("redirect_url", "")
    admin.submit_for_review()
    assert lb.saved(admin, CTA_VERIFY), (
        f"an Inactive CTA with an empty Redirect URL was NOT saved ({admin.save_counts()}, "
        f"invalid_fields={(admin.last_save or {}).get('invalid_fields')})")
    rec = lb.live_json(admin, CTA_VERIFY)
    assert rec.get("activeStatus") is False and not (rec.get("redirectUrl") or ""), (
        f"stored activeStatus={rec.get('activeStatus')!r} redirectUrl={rec.get('redirectUrl')!r}")
    lb.expect_public(browser, COO_PATH, _verify_hidden_probe,
                     "no 'Verify Certificate' in hero or banner, only 'Login to COO'", settle_sel=C.HERO_CTA)
    # step 4: back to Active with the URL still empty -> blocked
    before = lb.open_live(admin, CTA_VERIFY)
    _set_flag(admin, "active_status", True)
    lb.assert_publish_blocked(admin, CTA_VERIFY, before, "activeStatus",
                              "Active Status ticked while the Redirect URL is empty")


# ===========================================================================
# 130947 Certificate of Origin - COO Page Content 93657
# ===========================================================================
def _banner_blocked(page, A, value, what):
    admin = A(page)
    before = lb.open_live(admin, COO_PAGE)
    admin.fill("banner_heading", value)
    lb.assert_publish_blocked(admin, COO_PAGE, before, "bannerHeading_i18n", what)


def coo_141113(page, browser, A):
    _banner_blocked(page, A, "", "an empty Banner Heading EN")


def coo_141115(page, browser, A):
    _banner_blocked(page, A, "    ", "a whitespace-only Banner Heading EN")


def coo_141117(page, browser, A):
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    _set_flag(admin, "banner_active", True)
    lb.publish(admin, COO_PAGE)

    def probe(p, http):
        b = _coo_banner(p)
        ok = (b["present"] and b["eyebrow"] == ["Ready to continue?"] and b["title"] == ["Choose the service you need"]
              and any(b["body"]) and b["ctas"] == ["Login to COO", "Verify Certificate"])
        return ok, b

    lb.expect_public(browser, COO_PATH, probe, "banner: eyebrow, heading, body, two CTAs", settle_sel=C.BANNER)


def coo_141118(page, browser, A):
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    _set_flag(admin, "banner_active", False)
    lb.publish(admin, COO_PAGE)

    def probe(p, http):
        html = p.content()
        hero = _labels(buttons(p, C.HERO_CTA))
        gone = "Ready to continue?" not in html and "Choose the service you need" not in html
        return gone and hero == ["Login to COO", "Verify Certificate"], {
            "banner_nodes": p.locator(C.BANNER).count(), "in_source": not gone, "hero": hero}

    lb.expect_public(browser, COO_PATH, probe, "no banner text in the source, hero keeps both CTAs",
                     settle_sel=C.HERO_CTA)


def coo_141172(page, browser, A):
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    admin.fill("banner_eyebrow", "")
    admin.fill("banner_eyebrow", "", locale="ar")
    lb.publish(admin, COO_PAGE)

    def probe(p, http):
        b = _coo_banner(p)
        first = squash(p.locator(C.BANNER).first.inner_text()) if b["present"] else ""
        ok = (b["present"] and first.startswith("Choose the service you need") and "Ready to continue?" not in first
              and b["eyebrow_nodes"] == 0 and b["ctas"] == ["Login to COO", "Verify Certificate"])
        return ok, {**b, "banner_text": first[:120]}

    lb.expect_public(browser, COO_PATH, probe, "banner starts with the heading, no eyebrow element, both CTAs",
                     settle_sel=C.BANNER)


def coo_141173(page, browser, A):
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    lb.clear_rich(admin, "banner_body", "en")
    lb.clear_rich(admin, "banner_body", "ar")
    lb.publish(admin, COO_PAGE)

    def probe(p, http):
        b = _coo_banner(p)
        ok = (b["present"] and b["eyebrow"] == ["Ready to continue?"] and b["title"] == ["Choose the service you need"]
              and b["body_nodes"] == 0 and b["ctas"] == ["Login to COO", "Verify Certificate"])
        return ok, b

    lb.expect_public(browser, COO_PATH, probe, "banner: eyebrow, heading, CTAs, no body element", settle_sel=C.BANNER)


def coo_141143(page, browser, A):
    """Documents Required stays Active; its only live accordion item (93860) Inactive."""
    admin = A(page)
    lb.open_live(admin, DOC_REQ)
    _set_flag(admin, "active_status", False)
    lb.publish(admin, DOC_REQ, expect_published=False)

    def probe(p, http):
        idx = texts(p, C.INDEX_ITEM)
        sec = p.locator(f"#qc-coo-documents, {C.SECTION}:has-text('Documents Required')").first
        info = {"index": idx}
        if not sec.count():
            return False, {**info, "section": "absent"}
        info.update({"badge": squash(sec.locator(C.SECTION_BADGE).first.inner_text()) if sec.locator(C.SECTION_BADGE).count() else "",
                     "title": squash(sec.locator(C.SECTION_TITLE).first.inner_text()) if sec.locator(C.SECTION_TITLE).count() else "",
                     "pdf": squash(sec.locator(C.PDF_BUTTON).first.inner_text()) if sec.locator(C.PDF_BUTTON).count() else "",
                     "acc_items": sec.locator(C.ACC_ITEM).count(),
                     "accordion_nodes": sec.locator(C.ACCORDION).count()})
        acc = sec.locator(C.ACCORDION)
        info["accordion_height"] = acc.first.bounding_box()["height"] if acc.count() and acc.first.is_visible() else 0
        ok = (any("Documents Required" in t for t in idx) and info["badge"] == "Official Compliance Guide"
              and info["title"] == "Documents Required" and bool(info["pdf"]) and info["acc_items"] == 0
              and info["accordion_height"] == 0)
        return ok, info

    lb.expect_public(browser, COO_PATH, probe,
                     "section 02 renders badge/heading/PDF button, no accordion shell, index keeps '02 Documents Required'",
                     settle_sel=C.INDEX_ITEM)


def coo_140993(page, browser, A):
    """Full lifecycle on the live COO page record: Save as Draft, Preview, Publish, Unpublish."""
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    pg = admin.page
    ctrls = {n: pg.locator(f'button:has-text("{n}"), a:has-text("{n}")').count()
             for n in ("Save as Draft", "Preview", "Publish", "Unpublish")}
    print(f"[140993] controls on the edit form: {ctrls}")
    value = "Export Documentation Service QCTEST-130947-A"
    admin.fill("eyebrow", value)
    lb.save_draft(admin, COO_PAGE)
    # Preview: the form's own control
    lb.open_live(admin, COO_PAGE)
    prev = pg.locator('button:has-text("Preview"), a:has-text("Preview")')
    assert prev.count(), f"the Editor's edit form offers no Preview control (controls {ctrls})"
    with pg.context.expect_page(timeout=15000) as np_:
        prev.first.click()
    pv = np_.value
    pv.wait_for_load_state("domcontentloaded", timeout=60000)
    pv.wait_for_timeout(2000)
    assert value in pv.content(), f"Preview does not render {value!r} ({pv.url})"
    pv.close()
    lb.open_live(admin, COO_PAGE)
    lb.publish(admin, COO_PAGE)
    lb.expect_public(browser, COO_PATH, lambda p, h: (value in texts(p, C.HERO_EYEBROW), texts(p, C.HERO_EYEBROW)),
                     f"hero eyebrow {value!r}", settle_sel=C.HERO_EYEBROW)
    lb.row_action(admin, COO_PAGE, "unpublish")
    st = lb.wait_status(admin, COO_PAGE, "Unpublished")
    assert st == "Unpublished", f"after Unpublish the record is {st!r}"
    lb.expect_public(browser, COO_PATH, lambda p, h: lb.not_served(h, p, [C.HERO_TITLE, C.HERO_EYEBROW]),
                     "page not served (404 / not-found)", settle_sel=C.ROOT)


def coo_141003(page, browser, A):
    """Draft -> Page Status Published + Publish -> public 200; Page Status persists."""
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    # precondition named by the case: the record in Draft (Page Status = Draft)
    admin.fill("page_status", "Draft")
    lb.publish(admin, COO_PAGE, expect_published=False)
    lb.open_live(admin, COO_PAGE)
    assert admin.value("page_status") == "Draft", f"precondition: Page Status reads {admin.value('page_status')!r}"
    admin.fill("page_status", "Published")
    lb.publish(admin, COO_PAGE)
    lb.expect_public(browser, COO_PATH,
                     lambda p, h: (h == 200 and texts(p, C.HERO_TITLE) == ["Certificate of Origin Online"],
                                   {"http": h, "title": texts(p, C.HERO_TITLE)}),
                     "HTTP 200 with hero title 'Certificate of Origin Online'", settle_sel=C.HERO_TITLE)
    lb.open_live(admin, COO_PAGE)
    assert admin.value("page_status") == "Published", f"Page Status after reload: {admin.value('page_status')!r}"


def coo_141004(page, browser, A):
    admin = A(page)
    lb.open_live(admin, COO_PAGE)
    lb.row_action(admin, COO_PAGE, "unpublish")
    st = lb.wait_status(admin, COO_PAGE, "Unpublished")
    assert st == "Unpublished", f"after Unpublish the record is {st!r}"
    for loc in ("en", "ar"):
        lb.expect_public(browser, COO_PATH, lambda p, h: lb.not_served(h, p, [C.HERO_TITLE, C.HERO_EYEBROW, C.SECTION]),
                         "page not served (404 / not-found)", locale=loc, settle_sel=C.ROOT)


# ===========================================================================
# 130949 Proposal for Research - page 99844, Overview 99886
# ===========================================================================
PFR_FACTS = ["Proposal Type", "Research Focus", "Primary Audience", "Responsible Department"]
PFR_SECTIONS = ["Overview", "Service information", "Downloadable resources"]
PFR_CARDS = ["Clear research focus", "Business guidance", "Contact our experts"]
PFR_GROUPS = ["Preparing your proposal", "Supporting information"]
PFR_RESOURCES = ["Research Proposal Template", "Research Proposal Guidelines"]


def _pfr_state(p, http) -> dict:
    return {"http": http, "title": texts(p, R.HERO_TITLE), "facts": texts(p, R.FACT_LABEL),
            "sections": texts(p, R.SECTION_TITLE), "cards": texts(p, R.OVERVIEW_CARD_TITLE),
            "groups": texts(p, R.INFO_GROUP_LABEL),
            "bullets": [p.locator(R.INFO_GROUP).nth(i).locator(R.INFO_GROUP_BULLET).count()
                        for i in range(p.locator(R.INFO_GROUP).count())],
            "resources": texts(p, R.RESOURCE_CARD_TITLE), "downloads": p.locator(R.RESOURCE_DOWNLOAD_BUTTON).count()}


def _pfr_live_ok(p, http):
    s = _pfr_state(p, http)
    return http == 200 and s["title"] == ["Proposal for Research"] and len(s["sections"]) == 3, s


def pfr_141205(page, browser, A):
    admin = A(page)
    lb.open_live(admin, PFR_PAGE)
    btn = admin.page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first
    assert btn.is_enabled(), "the Publish control is not enabled on the live record"
    lb.publish(admin, PFR_PAGE)
    lb.expect_public(browser, PFR_PATH, _pfr_live_ok, "HTTP 200, hero 'Proposal for Research', three sections",
                     settle_sel=R.HERO_TITLE)


def pfr_141209(page, browser, A):
    admin = A(page)
    lb.open_live(admin, PFR_PAGE)
    print(f"[141209] precondition 'page status Draft': the live record opens as {admin.value('page_status')!r} "
          "(case deviation recorded, not built)")
    lb.publish(admin, PFR_PAGE)

    def probe(p, http):
        s = _pfr_state(p, http)
        secs = [re.sub(r"^\d+\s*", "", t) for t in s["sections"]]
        ok = (http == 200 and s["facts"] == PFR_FACTS and secs == PFR_SECTIONS and s["cards"] == PFR_CARDS
              and s["groups"] == PFR_GROUPS and s["bullets"] == [6, 4] and s["resources"] == PFR_RESOURCES)
        return ok, s

    lb.expect_public(browser, PFR_PATH, probe, "every active component in configured order", settle_sel=R.FACT_LABEL)


def pfr_141212(page, browser, A):
    admin = A(page)
    before = lb.open_live(admin, PFR_PAGE)
    lb.row_action(admin, PFR_PAGE, "unpublish")
    st = lb.wait_status(admin, PFR_PAGE, "Unpublished")
    assert st == "Unpublished", f"after Unpublish the record is {st!r}"
    lb.expect_public(browser, PFR_PATH,
                     lambda p, h: lb.not_served(h, p, [R.HERO_TITLE, R.SECTION_TITLE, R.RESOURCE_DOWNLOAD_BUTTON]),
                     "no hero title, sections or Download buttons for a visitor", settle_sel=R.HERO_TITLE)
    after = lb.live_json(admin, PFR_PAGE)
    for k in ("pageTitle_i18n", "eyebrowLabel_i18n", "heroDescription_i18n"):
        assert after.get(k) == before.get(k), f"{k} changed by Unpublish: {after.get(k)!r}"
    assert (after.get("heroBanner") or {}).get("id") == (before.get("heroBanner") or {}).get("id"), "hero banner lost"
    st_, txt = lb.req(admin, "GET", "/o/c/overviewsectionandinfocards/scopes/37246?pageSize=50")
    import json as _j
    cards = [i for i in _j.loads(txt).get("items", []) if str(i.get("externalReferenceCode", "")).startswith("QCDEMO-")]
    assert len(cards) == 3, f"overview info cards retained: {len(cards)} (expected 3)"


def pfr_141268(page, browser, A):
    admin = A(page)
    data = lb.open_live(admin, PFR_OVERVIEW)
    en = data.get("overviewBodyRawText") or squash(re.sub(r"<[^>]+>", " ", data.get("overviewBody") or ""))
    ar = ("تمكّن خدمة مقترح بحث في غرفة قطر الشركات والباحثين والجهات المهتمة من تقديم مقترحات لموضوعات بحثية "
          "اقتصادية وتجارية ليتم دراستها من قبل إدارة البحوث والدراسات.")
    admin.fill("overview_body", en)
    admin.fill("overview_body", ar, locale="ar")
    lb.publish(admin, PFR_OVERVIEW)
    lead = ("Qatar Chamber's Proposal for Research service enables businesses, researchers, and interested "
            "stakeholders to propose economic and business-related topics for c")

    def probe_en(p, http):
        body = texts(p, f"#qc-pfr-overview {R.SECTION_BODY}, {R.SECTION}:has({R.OVERVIEW_CARDS}) {R.SECTION_BODY}")
        st = {}
        if body:
            st = p.locator(f"{R.SECTION}:has({R.OVERVIEW_CARDS}) {R.SECTION_BODY}").first.evaluate(
                "e => { const s = getComputedStyle(e.querySelector('p') || e); return {font: s.fontFamily, weight: s.fontWeight,"
                " size: s.fontSize, lh: s.lineHeight, color: s.color}; }")
        ok = bool(body) and body[0].startswith(lead) and "cairo" in st.get("font", "").lower() and st.get("weight") == "400" \
            and st.get("size") == "16px" and st.get("lh") == "24px" and st.get("color") == "rgb(74, 74, 73)"
        return ok, {"body": [b[:140] for b in body], "style": st}

    lb.expect_public(browser, PFR_PATH, probe_en, "EN Overview body lead + Cairo 400 16px/24px #4A4A49",
                     settle_sel=R.SECTION_BODY)

    def probe_ar(p, http):
        sel = f"{R.SECTION}:has({R.OVERVIEW_CARDS}) {R.SECTION_BODY}"
        body = texts(p, sel)
        align = p.locator(sel).first.evaluate(
            "e => { const s = getComputedStyle(e.querySelector('p') || e); return [s.textAlign, s.direction]; }") if body else []
        ok = bool(body) and ar[:40] in body[0] and (align[0] in ("right", "start") and align[1] == "rtl")
        return ok, {"body": [b[:140] for b in body], "align": align}

    lb.expect_public(browser, PFR_PATH, probe_ar, "AR Overview body text right-aligned", locale="ar",
                     settle_sel=R.SECTION_BODY)


def pfr_141283(page, browser, A):
    admin = A(page)
    lb.open_live(admin, PFR_PAGE)
    opts = admin.select_options("page_status")
    assert opts == ["Draft", "Published", "Unpublished"], f"Page Status offers {opts!r}"
    admin.fill("page_status", "Published")
    lb.publish(admin, PFR_PAGE)
    lb.expect_public(browser, PFR_PATH,
                     lambda p, h: (h == 200 and texts(p, R.HERO_TITLE) == ["Proposal for Research"],
                                   {"http": h, "title": texts(p, R.HERO_TITLE)}),
                     "HTTP 200 with hero title 'Proposal for Research'", settle_sel=R.HERO_TITLE)


def pfr_141284(page, browser, A):
    admin = A(page)
    lb.open_live(admin, PFR_PAGE)
    admin.fill("page_status", "Draft")
    admin.submit_for_review()
    assert lb.saved(admin, PFR_PAGE), f"the save did not reach {PFR_PAGE} ({admin.save_counts()})"
    rec = lb.live_json(admin, PFR_PAGE)
    assert (rec.get("pageStatus") or {}).get("key") == "draft", f"Page Status stored {rec.get('pageStatus')!r}"
    lb.expect_public(browser, PFR_PATH,
                     lambda p, h: lb.not_served(h, p, [R.HERO_TITLE, R.SECTION_TITLE, R.RESOURCE_CARD]),
                     "no hero title, sections or resource cards for a visitor", settle_sel=R.HERO_TITLE)


def pfr_141310(page, browser, A, png_fixture):
    admin = A(page)
    before = lb.open_live(admin, PFR_PAGE)
    old = (before.get("heroBanner") or {}).get("name") or ""
    name = "QCTEST-130949-hero-v2.png"
    admin.upload_file(admin.FIELDS["hero_banner"].label, lb.exact_copy(png_fixture, name))
    lb.publish(admin, PFR_PAGE)
    rec = lb.live_json(admin, PFR_PAGE)
    lb.log_upload_leftover(PFR_PAGE, rec, "heroBanner")
    stored = (rec.get("heroBanner") or {}).get("name") or ""
    assert stored.startswith("QCTEST-130949-hero-v2"), f"the hero banner stored is {stored!r}"
    stem = stored.rsplit(".", 1)[0]

    ctx, p = lb.anon(browser)
    seen = []
    p.on("response", lambda r: seen.append((r.url, r.status)) if "/documents/" in r.url else None)
    try:
        import time as _t
        t0 = _t.monotonic()
        while True:
            seen.clear()
            lb.visit(p, PFR_PATH, settle_sel=R.HERO_BLOCK)
            new = [s for s in seen if stem in s[0]]
            stale = [s for s in seen if old and old.rsplit(".", 1)[0] in s[0]]
            if (new and all(st == 200 for _, st in new) and not stale) or _t.monotonic() - t0 > 75:
                break
            p.wait_for_timeout(3000)
        print(f"[141310] hero requests new={new[:2]} stale={stale[:2]}")
        assert new and all(st == 200 for _, st in new), f"no HTTP 200 request for {stored!r}: {seen[:6]}"
        assert not stale, f"the previous hero {old!r} is still requested: {stale[:2]}"
    finally:
        ctx.close()


# ===========================================================================
# 130720 Partners & Offers - page 167087
# ===========================================================================
PO_VALUES = {
    "eyebrow": ("Councils QCTEST-144410", "المجالس QCTEST-144410"),
    "page_title": ("Partners & Offers QCTEST-144410", "الشركاء والعروض QCTEST-144410"),
    "page_description": ("Partner benefits description QCTEST-144410.", "وصف مزايا الشركاء QCTEST-144410."),
    "section_eyebrow": ("Partner benefits QCTEST-144410", "مزايا الشركاء QCTEST-144410"),
    "section_heading": ("Offers heading QCTEST-144410", "عنوان العروض QCTEST-144410"),
    "section_description": ("Choose a category QCTEST-144410.", "اختر فئة QCTEST-144410."),
    "find_button_label": ("Find QC144410", "بحث QC144410"),
}
PO_SEL = {"eyebrow": P.HERO_EYEBROW, "page_title": P.HERO_TITLE, "page_description": P.HERO_DESCRIPTION,
          "section_eyebrow": P.SECTION_EYEBROW, "section_heading": P.SECTION_HEADING,
          "section_description": P.SECTION_DESCRIPTION, "find_button_label": P.FIND_BUTTON}


def po_144410(page, browser, A):
    admin = A(page)
    lb.open_live(admin, PO_PAGE)
    for key, (en, ar) in PO_VALUES.items():
        admin.fill(key, en)
        admin.fill(key, ar, locale="ar")
    lb.publish(admin, PO_PAGE)
    for i, loc in enumerate(("en", "ar")):
        def probe(p, http, i=i):
            got = {k: texts(p, s) for k, s in PO_SEL.items()}
            ok = all(any(PO_VALUES[k][i] in t for t in got[k]) for k in PO_SEL)
            return ok, got

        lb.expect_public(browser, PO_PATH, probe, f"all 7 fields in {loc.upper()}", locale=loc, settle_sel=P.HERO_TITLE)


def po_144412(page, browser, A, png_fixture):
    admin = A(page)
    lb.open_live(admin, PO_PAGE)
    name = "QCTEST-144412-hero-illustration.png"
    admin.upload_file(admin.FIELDS["hero_illustration"].label, lb.exact_copy(png_fixture, name))
    lb.publish(admin, PO_PAGE)
    rec = lb.live_json(admin, PO_PAGE)
    lb.log_upload_leftover(PO_PAGE, rec, "heroIllustration")
    stored = (rec.get("heroIllustration") or {}).get("name") or ""
    assert stored.startswith("QCTEST-144412-hero-illustration"), f"the hero illustration stored is {stored!r}"
    fid = str((rec.get("heroIllustration") or {}).get("id"))

    # The fragment serves the illustration through the module's own endpoint,
    # /o/qc-partners-offers-api/attachment?id=<fileEntryId> (read live
    # 2026-10-04), not by file name: the hero image must carry the NEW id and load.
    def probe(p, http):
        img = p.locator("img.qc-po__hero-image").first
        if not img.count():
            return False, {"hero_image": "absent"}
        src = img.get_attribute("src") or ""
        info = {"src": src, "hidden": img.get_attribute("hidden") is not None,
                "loaded": img.evaluate("i => i.complete && i.naturalWidth > 0")}
        return (f"id={fid}" in src and info["loaded"] and not info["hidden"] and img.is_visible()), info

    lb.expect_public(browser, PO_PATH, probe, f"hero shows {stored!r}", settle_sel=P.HERO)

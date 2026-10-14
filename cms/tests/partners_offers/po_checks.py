"""
cms/tests/partners_offers/po_checks.py — check bodies for PBI 130720 (Partners &
Offers) Control_Panel cases that the shared cms/tests/authoring_checks.py (ck)
and Engineer B's cms/tests/certificate_of_origin/b_checks.py (bk) do not cover.

Not a test module. Same contract as ck / bk:
  - every record is a disposable QCTEST record with a per-run unique title
    (bk.run_title), deleted BY ID in a finally block (FragmentFormMixin);
  - the account is named: Site Content Editor for create -> Published; never
    TEST_USER;
  - public reads use a fresh logged-out context, and both visibility gates
    (Published by ID, Active Status ticked when the object has one) are
    asserted before anything is called missing;
  - the PUBLIC offers listing renders its cards from
    `/qc-partners-offers-api/offers` with "Load More" paging, so a card is
    searched across every page (Load More until it is gone), polled for the
    delivery lag.
"""

from __future__ import annotations

import time

from cms.pages.certificate_of_origin.fragment_form_mixin import log_leftover
from cms.pages.components.disposable_object_admin import ROLE_EDITOR, ROLE_SITE_MEMBER
from cms.pages.components.object_authoring_page import STATUS_PUBLISHED
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.tests.certificate_of_origin.b_checks import run_title
from web.pages.partners_offers.partners_offers_page import PartnersOffersPage

PUBLIC_POLL_S = 60.0


# ---------------------------------------------------------------------------
# public side
# ---------------------------------------------------------------------------
def _anon(browser):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False)
    return ctx, ctx.new_page()


def _close(ctx):
    try:
        ctx.close()
    except Exception:  # noqa: BLE001
        pass


def _load_all(po: PartnersOffersPage) -> None:
    """Click Load More until it is gone (bounded)."""
    for _ in range(15):
        try:
            if not po.load_more_is_visible():
                return
            po.click_load_more()
        except Exception:  # noqa: BLE001
            return


def find_card(anon, name: str, locale: str = "en", category: str | None = None, expect: bool = True,
              timeout: float = PUBLIC_POLL_S):
    """The public card whose partner name contains `name` (None when absent),
    polled (reload) until its presence matches `expect`. With `category` the
    listing is filtered first (dropdown + Find), as a visitor does."""
    po = PartnersOffersPage(anon)
    deadline = time.monotonic() + timeout
    card = None
    while True:
        po.open_partners_offers(locale=locale)
        try:
            anon.locator(po.CARD).first.wait_for(state="attached", timeout=15000)
        except Exception:  # noqa: BLE001 - empty listing is a valid state
            pass
        if category:
            po.select_category(category)
            po.click_find()
        _load_all(po)
        loc = anon.locator(po.CARD).filter(has=anon.locator(po.CARD_PARTNER_NAME, has_text=name))
        card = loc.first if loc.count() else None
        if (card is not None) == expect or time.monotonic() > deadline:
            return card
        anon.wait_for_timeout(3000)


def _anon_offer_api(anon, title: str) -> str:
    """What the public offers API returns to the logged-out visitor for the
    record titled `title` (contract-related keys), as evidence."""
    js = """async (t) => {
      const r = await fetch('/o/qc-partners-offers-api/offers?languageId=en_US&page=1&pageSize=200',
                            {credentials: 'same-origin', headers: {accept: 'application/json'}});
      let d = {}; try { d = await r.json(); } catch (e) { return 'HTTP ' + r.status + ' (not JSON)'; }
      const it = (d.items || []).find(i => JSON.stringify(i).includes(t));
      if (!it) return 'HTTP ' + r.status + ' item absent of ' + (d.items || []).length;
      const keep = {}; for (const [k, v] of Object.entries(it)) if (/contract|document|url|attach/i.test(k)) keep[k] = v;
      return 'HTTP ' + r.status + ' keys=' + Object.keys(it).join(',') + ' contract=' + JSON.stringify(keep).slice(0, 400);
    }"""
    try:
        return anon.evaluate(js, title)
    except Exception as exc:  # noqa: BLE001
        return f"unreadable: {str(exc)[:120]}"


def _anon_offer_api_logo(anon, title: str) -> str:
    try:
        return anon.evaluate("""async (t) => { const r = await fetch('/o/qc-partners-offers-api/offers?languageId=en_US&page=1&pageSize=200');
          const d = await r.json(); const it = (d.items || []).find(i => JSON.stringify(i).includes(t));
          return it ? JSON.stringify(it.partnerLogo) : 'item absent'; }""", title)
    except Exception as exc:  # noqa: BLE001
        return f"unreadable: {str(exc)[:120]}"


def check_file_save_refused(page, admin_cls, tc_id, key, fixture, files=None):
    """Both steps of an oversized/unsupported upload case: (1) the upload
    attempt is made; (2) the SAVE must be blocked. A picker that refuses the
    file already blocks it; otherwise the record is submitted and must not
    store the file (checked BY ID)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "bigfile")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=files, skip=(key,))
        try:
            admin.upload(key, fixture, tag=str(tc_id))
        except Exception as exc:  # noqa: BLE001 - the picker refused the upload
            print(f"[tc_{tc_id}] picker refused the file: {str(exc)[:160]}")
            return
        stem = (admin.__dict__.get("_qcb_uploads", {}).get(key) or "").rsplit(".", 1)[0]
        admin.submit_for_review()
        if not admin.id_for(title):
            assert admin.refusal_visible(), "nothing stored and no refusal shown"
            return
        data = admin.entry_json(title) or {}
        stored = data.get(admin_cls.FIELDS[key].ref or "", None) if admin_cls.FIELDS[key].ref else None
        blob = str(data)
        assert not (stem and stem in blob), (
            f"{key}: the file {stem!r} was accepted by the picker AND stored on the saved record "
            f"(id {admin.id_for(title)}, status {admin.status_of(title, ROLE_EDITOR)!r}); the save was not blocked {stored or ''}")
    finally:
        delete(admin, title)


def card_probe(locale: str = "en"):
    """ck-style probe(anon, text, expect=True) -> bool over the offer cards."""
    def probe(anon, text, expect=True):
        return find_card(anon, text, locale=locale, expect=expect) is not None
    return probe


def category_options(anon, locale: str = "en") -> list[str]:
    po = PartnersOffersPage(anon)
    po.open_partners_offers(locale=locale)
    anon.locator(po.CATEGORY_DROPDOWN).first.wait_for(state="attached", timeout=20000)
    return [" ".join(t.split()) for t in anon.locator(po.CATEGORY_OPTION).all_text_contents()]


def category_probe(anon, text, expect=True):
    """Probe for the public category dropdown's option list."""
    deadline = time.monotonic() + PUBLIC_POLL_S
    while True:
        seen = any(text in o for o in category_options(anon))
        if seen == expect or time.monotonic() > deadline:
            return seen
        anon.wait_for_timeout(3000)


def open_details(anon, card):
    """Open the card's Offer details modal; returns the modal locator."""
    po = PartnersOffersPage(anon)
    card.locator(po.CARD_OFFER_DETAILS_BUTTON).first.click()
    modal = anon.locator(po.MODAL_DIALOG).first
    modal.wait_for(state="visible", timeout=10000)
    return modal


# ---------------------------------------------------------------------------
# admin side
# ---------------------------------------------------------------------------
def _gates(admin, title) -> str:
    eid = admin.id_for(title)
    st = admin.status_by_id(eid, admin.plural_for(title)) if eid else ""
    data = admin.entry_json(title) or {}
    return f"id={eid} status={st!r} activeStatus={data.get('activeStatus', 'n/a')!r}"


def publish(admin, title, files=None, extra=None, ar_extra=None, skip=()):
    """Editor create (Active ticked where the object has it) -> Submit;
    asserts Published BY ID (with the Editor Pending->Published settle)."""
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(title, active=True, files=files, skip=skip)
    for key, val in (extra or {}).items():
        admin.fill(key, val)
    for key, val in (ar_extra or {}).items():
        admin.fill(key, val, locale="ar")
    admin.submit_for_review()
    eid = admin.id_for(title)
    assert eid, f"{title!r}: the Editor submit stored no record ({admin.save_counts()})"
    status = admin.status_of(title, ROLE_EDITOR)
    assert status == STATUS_PUBLISHED, (
        f"{title!r} (id {eid}) is {status or 'unreadable'!r} after an Editor submit, not Published"
    )


def delete(admin, title) -> bool:
    try:
        ok = admin.delete_disposable(title)
        if not ok:
            log_leftover(f"LEFTOVER {admin.SLUG} id={admin.id_for(title)} {title[:60]!r}")
        return ok
    except Exception as exc:  # noqa: BLE001 - teardown never masks the result
        log_leftover(f"teardown error {title[:60]!r}: {str(exc)[:160]}")
        return False


def _not_rendered(admin, title, what):
    return f"{what} (gates {_gates(admin, title)})"


# ---------------------------------------------------------------------------
# case shapes
# ---------------------------------------------------------------------------
def check_offer_card(page, browser, admin_cls, tc_id, short, files, extra=None, ar_extra=None, skip=(),
                     category=None, card_expect=None, ar_expect=None, modal_expect=None, card_absent=None,
                     check_logo=False):
    """Editor publishes a QCTEST offer, then a logged-out visitor finds its
    card (filtered by `category` when given) and sees every text in
    `card_expect`; `card_absent` texts must NOT be on the card; with
    `ar_expect` the Arabic listing card shows those texts; with
    `modal_expect` the Offer details modal shows those texts."""
    admin = admin_cls(page)
    title = run_title(tc_id, short)
    ctx, anon = _anon(browser)
    try:
        publish(admin, title, files=files, extra=extra, ar_extra=ar_extra, skip=skip)
        card = find_card(anon, title, category=category)
        assert card is not None, _not_rendered(
            admin, title, f"{title!r} is Published but no public card shows it"
            + (f" under category {category!r}" if category else ""))
        if check_logo:
            # the case's "all entered details" include the uploaded logo (2026-10-04 review)
            img = card.locator(PartnersOffersPage.CARD_LOGO).first
            loaded = img.count() and img.evaluate("i => i.complete && i.naturalWidth > 0")
            assert loaded, (f"card for {title!r} renders no loaded logo image; public API item = "
                            f"{_anon_offer_api_logo(anon, title)}")
        # casefold: badges / labels may be upper-cased by CSS (innerText applies text-transform)
        text = " ".join(card.inner_text().split())
        for t in card_expect or ():
            assert t.casefold() in text.casefold(), f"card for {title!r} does not show {t!r}: {text[:300]!r}"
        for t in card_absent or ():
            assert t.casefold() not in text.casefold(), f"card for {title!r} shows {t[:60]!r}, which belongs only in the modal"
        if modal_expect:
            modal = open_details(anon, card)
            mtext = " ".join(modal.inner_text().split())
            for t in modal_expect:
                assert t.casefold() in mtext.casefold(), f"Offer details modal for {title!r} does not show {t[:80]!r}"
        if ar_expect is not None:
            # the Arabic card is found by the Arabic partner name (fill_required's "<title> AR" unless overridden)
            ar_name = (ar_extra or {}).get(admin_cls.TITLE_FIELD) or f"{title} AR"
            ar_card = find_card(anon, ar_name, locale="ar")
            assert ar_card is not None, _not_rendered(
                admin, title, f"Arabic listing shows no card named {ar_name!r}")
            atext = " ".join(ar_card.inner_text().split())
            for t in ar_expect:
                assert t in atext, f"Arabic card does not show {t!r}: {atext[:300]!r}"
        return admin, title
    finally:
        delete(admin, title)
        _close(ctx)


def check_card_without_location(page, browser, admin_cls, tc_id, files, location_key="partner_location"):
    """Location left blank: publish succeeds and the card renders without a
    location line (no empty placeholder, no error)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "noloc")
    ctx, anon = _anon(browser)
    try:
        publish(admin, title, files=files, skip=(location_key,))
        card = find_card(anon, title)
        assert card is not None, _not_rendered(admin, title, f"{title!r} is Published but not on the public listing")
        loc = card.locator(PartnersOffersPage.CARD_LOCATION)
        shown = [t.strip() for t in loc.all_inner_texts() if t.strip()] if loc.count() else []
        assert not shown, f"card renders a location line for an offer with no location: {shown!r}"
        visible_empty = loc.count() and loc.first.is_visible()
        assert not visible_empty, "card renders an empty location placeholder"
    finally:
        delete(admin, title)
        _close(ctx)


def check_logo_on_card(page, browser, admin_cls, tc_id, files, logo_key="partner_logo"):
    """A valid logo uploads, the offer publishes, and the public card's logo
    image is the uploaded file and actually loads (naturalWidth > 0)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "logo")
    ctx, anon = _anon(browser)
    try:
        publish(admin, title, files=files)
        stem = (admin.__dict__.get("_qcb_uploads", {}).get(logo_key) or "").rsplit(".", 1)[0]
        card = find_card(anon, title)
        assert card is not None, _not_rendered(admin, title, f"{title!r} is Published but not on the public listing")
        img = card.locator(PartnersOffersPage.CARD_LOGO).first
        assert img.count(), "the card renders no logo image"
        src = img.get_attribute("src") or ""
        loaded = img.evaluate("i => i.complete && i.naturalWidth > 0")
        assert loaded, f"the card's logo image does not load (src={src[:120]!r})"
        if stem:
            assert stem in src or stem.casefold() in src.casefold(), (
                f"the card's logo src {src[:160]!r} is not the uploaded file {stem!r}")
    finally:
        delete(admin, title)
        _close(ctx)


def check_contract_opens(page, browser, admin_cls, tc_id, files, extra=None, expect_href=None,
                         file_key="contract_file", modal=True):
    """The card's "Contract" (and the modal's "Open contract") open the same
    document in a new tab: same href, target=_blank, and a real popup."""
    admin = admin_cls(page)
    title = run_title(tc_id, "contract")
    ctx, anon = _anon(browser)
    try:
        publish(admin, title, files=files, extra=extra)
        card = find_card(anon, title)
        assert card is not None, _not_rendered(admin, title, f"{title!r} is Published but not on the public listing")
        link = card.locator(PartnersOffersPage.CARD_CONTRACT_BUTTON).first
        if not link.count():
            data = admin.entry_json(title) or {}
            doc = data.get("offerContractDocument")
            doc = (doc or {}).get("name") if isinstance(doc, dict) else doc
            api = _anon_offer_api(anon, title)
            raise AssertionError(
                f"the card shows no 'Contract' action although a contract is configured. Public API item "
                f"(logged-out) = {api}. Stored record "
                f"(id {admin.id_for(title)}): offerContractDocument={doc!r}, "
                f"offerContractUrl={data.get('offerContractUrl')!r}; card links="
                f"{[a.get_attribute('class') for a in card.locator('a').all()][:8]!r}")
        href = link.get_attribute("href") or ""
        assert (link.get_attribute("target") or "") == "_blank", "card 'Contract' does not open in a new tab"
        if expect_href:
            assert href == expect_href, f"card 'Contract' links {href!r}, not the configured {expect_href!r}"
        else:
            stem = (admin.__dict__.get("_qcb_uploads", {}).get(file_key) or "").rsplit(".", 1)[0]
            assert stem and stem.casefold() in href.casefold(), f"card 'Contract' {href!r} is not the uploaded PDF {stem!r}"
        with anon.context.expect_page(timeout=20000) as pinfo:
            link.click()
        popup = pinfo.value
        try:
            popup.wait_for_load_state("domcontentloaded", timeout=20000)
        except Exception:  # noqa: BLE001 - a PDF viewer may never fire it
            pass
        assert popup.url and popup.url != "about:blank", "the 'Contract' tab opened nothing"
        popup.close()
        if modal:
            m = open_details(anon, card)
            open_link = m.locator(PartnersOffersPage.MODAL_OPEN_CONTRACT_BUTTON).first
            assert open_link.count(), "the modal shows no 'Open contract' action"
            assert (open_link.get_attribute("href") or "") == href, "modal 'Open contract' and card 'Contract' differ"
            assert (open_link.get_attribute("target") or "") == "_blank", "modal 'Open contract' is not a new tab"
    finally:
        delete(admin, title)
        _close(ctx)


def check_dates_persist(page, admin_cls, tc_id, start_key, end_key, start, end, files):
    """Start before End: the save goes through and the stored window is the
    one entered (read back from the reopened form)."""
    admin = admin_cls(page)
    title = run_title(tc_id, "dates")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=files, skip=(start_key, end_key))
        admin.fill(start_key, start)
        admin.fill(end_key, end)
        admin.submit_for_review()
        assert admin.id_for(title), f"{title!r}: a valid window {start}..{end} was not saved ({admin.save_counts()})"
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(title)
        got = (admin.value(start_key), admin.value(end_key))
        assert got == (start, end), f"stored validity window {got!r} != entered {(start, end)!r}"
    finally:
        delete(admin, title)


def check_dates_refused(page, admin_cls, tc_id, start_key, end_key, start, end, files, short="dates-bad"):
    """End before Start (or both blank): Submit is refused (positive
    signal) and nothing is published."""
    admin = admin_cls(page)
    title = run_title(tc_id, short)
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, files=files, skip=(start_key, end_key))
        if start:
            admin.fill(start_key, start)
        if end:
            admin.fill(end_key, end)
        admin.submit_for_review()
        refused = admin.refusal_visible()
        status = admin.status_of(title, ROLE_EDITOR)
        if not refused:
            data = admin.entry_json(title) or {}
            stored = (str(data.get("validityStartDate", ""))[:10], str(data.get("validityEndDate", ""))[:10])
            # rule out our side: the record must hold exactly the window the case entered
            if stored != (start, end):
                raise AssertionError(
                    f"AUTOMATION: the stored window {stored!r} is not the entered {(start, end)!r} "
                    f"(id {admin.id_for(title)}); the date fill did not take")
            raise AssertionError(
                f"validity {start or '(blank)'}..{end or '(blank)'}: Submit raised no refusal and the record "
                f"(id {admin.id_for(title)}) was stored with validityStartDate={stored[0]!r}, "
                f"validityEndDate={stored[1]!r}, status {status or 'absent'!r}")
        assert refused, f"validity {start or '(blank)'}..{end or '(blank)'}: Submit raised no refusal (status {status or 'absent'!r})"
        assert status != STATUS_PUBLISHED, f"validity {start or '(blank)'}..{end or '(blank)'}: the record was Published"
    finally:
        delete(admin, title)


def check_category_deactivate_blocked(page, browser, cat_cls, offer_cls, tc_id, offer_files, cat_key="partner_category"):
    """Re-expressed on disposable data: a QCTEST category with a Published
    QCTEST offer assigned is set Inactive and saved. The save must be blocked
    (positive signal) and the category must stay Active. Teardown: offer
    first, then category."""
    cat, offer = cat_cls(page), offer_cls(page)
    c_title, o_title = run_title(tc_id, "cat"), run_title(tc_id, "offer")
    try:
        publish(cat, c_title)
        publish(offer, o_title, files=offer_files, skip=(cat_key,), extra={cat_key: c_title})
        cat.open_list(ROLE_EDITOR)
        cat.open_entry_by_edit_link(c_title)
        cat.set_flag(cat.ACTIVE_FIELD, False)
        cat.submit_for_review()
        data = cat.entry_json(c_title) or {}
        active_now = data.get("activeStatus")
        signals = cat._refusal_signals(cat.last_save or {})
        assert active_now is not False, (
            f"category {c_title!r} with a Published offer assigned was deactivated without a "
            f"reassignment warning (stored activeStatus={active_now!r}; refusal signals={signals!r})")
        assert signals, (
            f"category stayed Active but no warning / refusal was shown (NEEDS_INVESTIGATION): {cat.save_counts()}")
    finally:
        delete(offer, o_title)
        delete(cat, c_title)


def check_role_cannot_publish(page, admin_cls, tc_id, role, files=None):
    """`role` (named by the case) creates a QCTEST record and clicks the form's
    submit. The record must never reach Published (read BY ID, as Editor),
    and the role's list must offer no Publish / Approve row action. Any
    denial text on screen is recorded, not asserted (wording is not a bug).
    ck.check_author_submit_pending hard-codes the Author; this takes the role.
    Teardown runs as Editor."""
    admin = admin_cls(page)
    title = run_title(tc_id, "role")
    try:
        admin.open_form(role)
        assert not admin.has_admin_toolbar(), f"precondition: the {role} session has the admin toolbar"
        admin.fill_required(title, active=True, files=files)
        label = admin.submit_button_label()
        admin.submit_for_review()
        ls = admin.last_save or {}
        denial = ls.get("hidden_refusal") or ls.get("diag_text") or ""
        if not admin.id_for(title):
            # nothing stored: the refusal needs a positive signal (oracle raises otherwise)
            assert admin.refusal_visible(), f"{role}: nothing stored and no refusal shown"
            print(f"[tc_{tc_id}] {role}: submit refused; denial text={denial[:160]!r}")
            return
        status = admin.status_of(title, ROLE_EDITOR)
        print(f"[tc_{tc_id}] {role}: submit button {label!r} -> status {status!r}; denial text={denial[:160]!r}")
        assert status != STATUS_PUBLISHED, f"{role} published {title!r} directly (button {label!r})"
        admin.open_list(role)
        assert not admin.row_offers_action(title, "publish"), f"{role} is offered Publish on {title!r}"
        assert not admin.row_offers_action(title, "approve"), f"{role} is offered Approve on {title!r}"
    finally:
        delete(admin, title)


def check_lookup_saves(page, admin_cls, tc_id, en, ar):
    """Partner Category / Membership Tier: drafts are OFF for these record
    types (live tooltip, 2026-10-04), so the case's 'save' is the Submit.
    Active Status is left unticked so nothing reaches the public dropdown.
    The record is stored (ID from the write), both names persist on reopen,
    and its row is in the lookup list."""
    admin = admin_cls(page)
    key = admin_cls.TITLE_FIELD
    title = run_title(tc_id, en)
    ar_value = f"{ar} {title}"
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(title, active=False)
        admin.fill(key, ar_value, locale="ar")
        admin.submit_for_review()
        assert admin.id_for(title), f"{title!r}: valid EN/AR names were not saved ({admin.save_counts()})"
        admin.open_list(ROLE_EDITOR)
        assert admin.row_visible(title), f"{title!r} (id {admin.id_for(title)}) is not in the lookup list"
        admin.open_entry_by_edit_link(title)
        assert admin.value(key) == title, f"EN name did not persist: {admin.value(key)!r}"
        assert admin.value(key, "ar") == ar_value, f"AR name did not persist: {admin.value(key, 'ar')!r}"
    finally:
        delete(admin, title)


def check_category_public(page, browser, cat_cls, tc_id):
    """Editor adds a QCTEST category with Active ticked and submits; a
    logged-out visitor's category dropdown offers it (no deployment)."""
    admin = cat_cls(page)
    title = run_title(tc_id, "cat")
    ctx, anon = _anon(browser)
    try:
        publish(admin, title)
        assert category_probe(anon, title), _not_rendered(
            admin, title, f"active category {title!r} is not offered in the public dropdown "
            f"(options: {category_options(anon)[:15]!r})")
    finally:
        delete(admin, title)
        _close(ctx)


def check_member_denied_publish(page, admin_cls):
    """Site member (signed in, no CMS role): the offer authoring surface is
    refused positively (ck.check_member_denied), so no publish is possible."""
    from cms.tests import authoring_checks as ck

    ck.check_member_denied(page, admin_cls)


def check_anonymous_edit_link_denied(browser, admin_cls, entry_code: str, leak_text: str):
    """A logged-out deep link to `manage-<slug>?editEntry=<code>` of a real
    (read-only) offer: sign-in / 404, no form, no field data in the page."""
    ctx, anon = _anon(browser)
    try:
        admin = admin_cls(anon)
        resp = anon.goto(admin._manage_url(edit_entry=entry_code, locale="en"), wait_until="domcontentloaded")
        assert anon.locator(admin.SAVE_AS_DRAFT_BUTTON).count() == 0, "anonymous deep link got the authoring form"
        assert leak_text not in anon.content(), f"anonymous deep link exposes the record's data ({leak_text!r})"
        assert (resp is not None and resp.status in (401, 403, 404)) or CmsLoginPage(anon).login_form_visible(), (
            f"anonymous deep link was neither refused nor sent to sign-in (HTTP {resp.status if resp else '?'})")
    finally:
        _close(ctx)


__all__ = [n for n in dir() if n.startswith("check_") or n in ("find_card", "card_probe", "category_probe")]
_ = ROLE_SITE_MEMBER

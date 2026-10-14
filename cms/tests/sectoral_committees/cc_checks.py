"""
cms/tests/sectoral_committees/cc_checks.py — check bodies for Engineer A4's
Councils & Committees Control_Panel modules (PBIs 130716, 130717, 130718,
130719). Not a test module.

Reused by import, not copied: the shared cms/tests/authoring_checks.py (ck),
Engineer B's cms/tests/certificate_of_origin/b_checks.py (bk: run-unique
QCTEST titles, by-ID teardown, logged-out probes) and Partners & Offers'
po_checks (po: role-cannot-publish).

Contract (CLAUDE.md non-negotiables, standards.md):
  - every authored record is QCTEST-<tc>-<short>-<run token>, deleted BY ID
    in a finally block; real QCDEMO content is read only;
  - every submission acted on is one this run created itself through the
    PUBLIC form (company "QCTEST-<tc>-<token> ..."); real visitor submissions
    are never opened, approved or rejected;
  - the account is named per case via cms_role_credentials(); never TEST_USER;
  - public reads use a fresh logged-out context; both visibility gates are
    asserted before anything is called missing;
  - the TEST CASE is the oracle (user rule 2026-10-04): assertions follow its
    expected result; only wording differences and missing toasts are not
    asserted (user rule), and email delivery is skipped as not observable
    AFTER everything observable has been asserted.
"""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

import pytest

from cms.pages.certificate_of_origin.fragment_form_mixin import log_leftover
from cms.pages.components.disposable_object_admin import ROLE_AUTHOR, ROLE_EDITOR
from cms.pages.components.object_authoring_page import STATUS_DRAFT, STATUS_PUBLISHED
from cms.pages.control_panel.login_page import CmsLoginPage
from cms.pages.join_committee.council_base import ROLE_FORM_MANAGER, squash
from cms.tests.certificate_of_origin import b_checks as bk
from config.settings import control_panel_url, web_url

RUN = bk.RUN_TOKEN
PUBLIC_POLL_S = 60.0
EMAIL_NOT_OBSERVABLE = (
    "Email delivery is not observable from automation (no mailbox access is defined for this project); "
    "every observable part of the case was asserted above"
)

# Request Status values of the submissions objects, compared case-insensitively
# (the column shows the picklist label).
REQ_PENDING = "pending"
REQ_APPROVED = "approved"
REQ_REJECTED = "rejected"

_FX = Path(__file__).resolve().parents[1] / "partners_offers" / "fixtures"
VALID_JPG = str(_FX / "valid_image_500kb.jpg")
VALID_PNG = str(_FX / "valid_icon_200kb.png")
VALID_DOCX = str(_FX / "valid_form.docx")
VALID_PDF = str(_FX / "valid_pdf_3mb.pdf")
BAD_EXE = str(_FX / "unsupported_file.exe")
BIG_JPG_3MB = str(_FX / "oversized_image_3mb.jpg")


def runtime_fixture(name: str, kind: str, size: int) -> str:
    """A fixture the case names by size/type, generated at run time in the temp
    dir (tools/fixture_factory makers); no committed fixture is edited."""
    from tools import fixture_factory as ff

    dest = Path(tempfile.gettempdir()) / f"qctest_a4_{name}"
    maker = {"jpg": ff.make_jpg, "png": ff.make_png, "gif": ff.make_gif, "pdf": ff.make_pdf,
             "svg": ff.make_svg, "docx": ff.make_docx}.get(kind)
    if not dest.exists() or dest.stat().st_size != size:
        data = maker(size) if maker else (b"PK\x03\x04" + b"\0" * (size - 4))  # zip magic
        dest.write_bytes(data)
    return str(dest)


MB = 1024 * 1024


def title(tc, short: str) -> str:
    return bk.run_title(tc, short)


# ---------------------------------------------------------------------------
# anonymous context
# ---------------------------------------------------------------------------
def _anon(browser, locale=None):
    from core.web.browser import new_context

    ctx = new_context(browser, use_auth_state=False, locale=locale)
    return ctx, ctx.new_page()


def _close(ctx):
    try:
        ctx.close()
    except Exception:  # noqa: BLE001
        pass


def _delete(admin, t):
    if not t:
        return
    try:
        if not admin.delete_disposable(t):
            log_leftover(f"LEFTOVER {admin.SLUG} id={admin.id_for(t)} {t[:60]!r}")
    except Exception as exc:  # noqa: BLE001 - teardown never masks the result
        log_leftover(f"teardown error {t[:60]!r}: {str(exc)[:160]}")


# ===========================================================================
# Public pages
# ===========================================================================
SC_PATH = "/web/qatar-chamber/sectoral-committees-and-business-councils"
JOIN_PATH = "/web/qatar-chamber/request-to-join-a-committee"
BCMR_PATH = "/web/qatar-chamber/business-council-membership-request"
QAFL_PATH = "/web/qatar-chamber/qafl-membership"


def _open_sc(anon, locale="en"):
    from web.pages.sectoral_committees.sectoral_committees_page import SectoralCommitteesPage

    sc = SectoralCommitteesPage(anon)
    anon.goto(web_url(SC_PATH, locale=locale), wait_until="domcontentloaded")
    try:
        anon.locator(sc.ROW).first.wait_for(state="attached", timeout=25000)
    except Exception:  # noqa: BLE001 - an empty / hidden directory is a valid state
        pass
    return sc


def _expand(anon, sc, expand):
    """expand: None | "lead" | ("row", <committee title>)."""
    try:
        if expand == "lead":
            head = anon.locator(sc.LEAD_HEAD).first
            if head.count() and head.get_attribute("aria-expanded") != "true":
                head.click()
                anon.wait_for_timeout(500)
        elif isinstance(expand, tuple) and expand[0] == "row":
            row = anon.locator(sc.ROW).filter(has_text=expand[1]).first
            if row.count():
                head = row.locator(sc.ROW_HEAD).first
                if head.get_attribute("aria-expanded") != "true":
                    head.click()
                    anon.wait_for_timeout(500)
    except Exception:  # noqa: BLE001 - reported by the caller's assertion
        pass


def sc_text(anon, section=None, expand=None, locale="en") -> str:
    sc = _open_sc(anon, locale)
    _expand(anon, sc, expand)
    loc = anon.locator(section).first if section else anon.locator("body")
    return squash(loc.inner_text()) if loc.count() else ""


def sc_probe(section=None, expand=None, locale="en"):
    """probe(anon, text, expect=True) over the sectoral page (optionally one
    section, optionally after expanding the Head card or one committee row),
    reloaded until the text's presence matches `expect` (upper bound 60 s)."""
    def probe(anon, text, expect=True, _expand_override=None):
        deadline = time.monotonic() + PUBLIC_POLL_S
        seen = not expect
        while True:
            seen = text in sc_text(anon, section, _expand_override or expand, locale)
            if seen == expect or time.monotonic() > deadline:
                return seen
            anon.wait_for_timeout(3000)
    return probe


def sc_list(anon, item_sel, expand=None, locale="en") -> list[str]:
    sc = _open_sc(anon, locale)
    _expand(anon, sc, expand)
    return [squash(t) for t in anon.locator(item_sel).all_inner_texts()]


def page_probe(path):
    def probe(anon, text, expect=True):
        deadline = time.monotonic() + PUBLIC_POLL_S
        while True:
            anon.goto(web_url(path, locale="en"), wait_until="domcontentloaded")
            anon.wait_for_timeout(2500)
            seen = text in anon.locator("body").inner_text()
            if seen == expect or time.monotonic() > deadline:
                return seen
            anon.wait_for_timeout(3000)
    return probe


# ===========================================================================
# Submissions (public form -> Control Panel review)
# ===========================================================================
def create_join_submission(browser, tc, sector_value: str | None = None, locale="en") -> str:
    """Submit the PUBLIC Request to Join a Committee form logged out with a
    QCTEST identity; returns the QCTEST company name. Skips the test with the
    exact reason when the form does not accept the submission (reCAPTCHA)."""
    from web.pages.join_committee.join_committee_page import JoinCommitteePage

    company = f"QCTEST-{tc}-{RUN} Join Co"
    ctx, anon = _anon(browser)
    try:
        jc = JoinCommitteePage(anon)
        jc.open_join_committee(locale=locale)
        jc.fill_all_valid(overrides={"company_name": company, "applicant_name": f"QCTEST-{tc}-{RUN}",
                                     "email": f"qctest.{tc}.{RUN}@example.com"})
        if sector_value:
            anon.locator(jc._field_locator("sector_committee")).select_option(value=sector_value)
        try:
            jc.submit_and_wait_result(timeout=45000)
        except Exception:  # noqa: BLE001
            pass
        if not jc.success_message_is_visible():
            pytest.skip(f"QCTEST submission could not be created through the public form "
                        f"(reCAPTCHA / form refused): {jc.status_banner_text()[:160]!r}")
        return company
    finally:
        _close(ctx)


def create_bcmr_submission(browser, tc, countries=("GB", "DE", "FR", "IT"), locale="en") -> str:
    from web.pages.business_council_membership.business_council_membership_page import (
        BusinessCouncilMembershipPage,
    )

    company = f"QCTEST-{tc}-{RUN} BC Co"
    ctx, anon = _anon(browser)
    try:
        bc = BusinessCouncilMembershipPage(anon)
        bc.open_membership_request(locale=locale)
        data = {f"country_{i}": c for i, c in enumerate(countries, 1)}
        data.update({"applicant_name": f"QCTEST-{tc}-{RUN}", "company_name": company, "cr_number": "1234567",
                     "owner_name": "QCTEST Owner", "email": f"qctest.{tc}.{RUN}@example.com",
                     "mobile_number": "55123456", "company_activity": "QCTEST activity"})
        bc.fill_form(data)
        bc.submit()
        if not bc.has_submission_succeeded(timeout=45000):
            msg = " | ".join(anon.locator("div.qc-bcm-status:visible").all_inner_texts())[:160]
            pytest.skip(f"QCTEST submission could not be created through the public form "
                        f"(reCAPTCHA / form refused): {msg!r}")
        return company
    finally:
        _close(ctx)


def _assert_status(sub, needle, want, role=ROLE_FORM_MANAGER):
    got = sub.request_status(needle, role)
    assert got.casefold() == want, f"{needle!r}: Request Status is {got or 'unreadable'!r}, expected {want!r}"


def _found(sub, needle, role):
    row = sub.find_row(needle, role)
    assert row is not None, (
        f"{role} cannot see the QCTEST submission {needle!r} in the {sub.SLUG} list (it was accepted by the "
        f"public form). Rows visible: {sub.visible_row_count()}"
    )
    return row


def check_submission_listed_pending(page, browser, sub_cls, create, tc, role=ROLE_FORM_MANAGER):
    """A fresh QCTEST submission is in the role's list with Request Status Pending."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    _assert_status(sub, needle, REQ_PENDING, role)
    return sub, needle


def check_submission_view(page, browser, sub_cls, create, tc, expect_texts=(), role=ROLE_FORM_MANAGER):
    """The role opens our QCTEST submission: every submitted value is shown,
    read-only."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    text = sub.view_text(needle, role)
    for t in (needle, *expect_texts):
        assert t in text, f"the record detail does not show {t!r}: {text[:300]!r}"
    assert sub.view_has_editable_inputs() == 0, "the submission detail exposes editable inputs"


def check_status_filter(page, browser, sub_cls, create, tc, statuses, role=ROLE_FORM_MANAGER):
    """The listing can be filtered by Request Status (the case's values); every
    row under a filter carries that status."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    sub.open_list(role)
    opts = [o.casefold() for o in sub.status_filter_options()]
    missing = [s for s in statuses if s.casefold() not in opts]
    assert not missing, f"the listing offers no Request Status filter for {missing!r} (status filter options: {opts!r})"
    for s in statuses:
        sub.page.locator("select[data-qc-oel-status-filter]").select_option(label=next(
            o for o in sub.status_filter_options() if o.casefold() == s.casefold()))
        sub.page.wait_for_timeout(2500)
        rows = sub.page.locator(sub.ROW).filter(has=sub.page.locator("td"))
        for i in range(rows.count()):
            assert s.casefold() in rows.nth(i).inner_text().casefold(), f"a row under filter {s!r} is not {s!r}"


def check_approve(page, browser, sub_cls, create, tc, email_step=True, role=ROLE_FORM_MANAGER):
    """Form Manager approves our Pending QCTEST submission: the status persists
    as Approved (re-read after reload). Email delivery is then skipped as not
    observable."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    _assert_status(sub, needle, REQ_PENDING, role)
    dialogs = sub.approve(needle, role)
    print(f"[tc_{tc}] approve dialogs: {dialogs}")
    _assert_status(sub, needle, REQ_APPROVED, role)
    if email_step:
        pytest.skip(EMAIL_NOT_OBSERVABLE)
    return sub, needle


def check_reject_with_reason(page, browser, sub_cls, create, tc, reason, email_step=True, role=ROLE_FORM_MANAGER):
    """Reject our QCTEST submission with `reason`: status Rejected, the record
    is kept, and the reason is stored on it (record detail)."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    dialogs = sub.reject(needle, reason, role)
    print(f"[tc_{tc}] reject dialogs: {dialogs}")
    _assert_status(sub, needle, REQ_REJECTED, role)
    text = sub.view_text(needle, role)
    assert reason in text, f"the rejection reason is not stored on the record: {text[-300:]!r}"
    if email_step:
        pytest.skip(EMAIL_NOT_OBSERVABLE)


def check_reject_reason_required(page, browser, sub_cls, create, tc, value="", role=ROLE_FORM_MANAGER):
    """Reject with an empty (or whitespace-only) reason is blocked with a
    validation message and the record stays Pending."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    dialogs = sub.reject(needle, value, role)
    print(f"[tc_{tc}] reject({value!r}) dialogs: {dialogs}")
    _assert_status(sub, needle, REQ_PENDING, role)
    blocked = [d for d in dialogs if d[0] == "alert" and "reason" in d[1].casefold()]
    assert blocked, f"no validation message requiring a rejection reason was shown (dialogs {dialogs!r})"


def check_status_flip(page, browser, sub_cls, create, tc, first, then_reason=None, role=ROLE_FORM_MANAGER):
    """first='approve' then Reject with a reason, or first='reject' then Approve:
    the second transition is either applied (status changes, reason stored)
    or refused with a message — never a broken record."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    if first == "approve":
        sub.approve(needle, role)
        _assert_status(sub, needle, REQ_APPROVED, role)
        row = sub.find_row(needle, role)
        assert row.locator("[data-qc-oel-reject]").count(), (
            f"an Approved request offers no Reject action (actions {sub.row_actions(row)})")
        sub.reject(needle, then_reason, role)
        _assert_status(sub, needle, REQ_REJECTED, role)
        assert then_reason in sub.view_text(needle, role), "the rejection reason is not stored"
    else:
        sub.reject(needle, then_reason or f"QCTEST-{tc} reason", role)
        _assert_status(sub, needle, REQ_REJECTED, role)
        row = sub.find_row(needle, role)
        actions = sub.row_actions(row)
        print(f"[tc_{tc}] Rejected row actions: {actions}")
        if row.locator("[data-qc-oel-approve]").count():
            dialogs = sub.approve(needle, role)
            got = sub.request_status(needle, role).casefold()
            assert got in (REQ_APPROVED, REQ_REJECTED), f"status after Rejected->Approve is {got!r}"
            print(f"[tc_{tc}] Rejected->Approve result: {got} (dialogs {dialogs})")


def check_concurrent_review(page, browser, sub_cls, create, tc, role=ROLE_FORM_MANAGER):
    """Two Form Manager sessions act on our Pending QCTEST submission (A
    approves, B rejects right after): the final status is one of the two
    real outcomes, never blank or corrupted."""
    from core.web.browser import new_context

    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, role)
    ctx_b = new_context(browser, use_auth_state=False)
    try:
        sub_b = sub_cls(ctx_b.new_page())
        _found(sub_b, needle, role)
        sub.approve(needle, role)
        sub_b.reject(needle, f"QCTEST-{tc} concurrent", role)
        final = sub.request_status(needle, role).casefold()
        assert final in (REQ_APPROVED, REQ_REJECTED), f"final status after concurrent review is {final!r}"
        print(f"[tc_{tc}] concurrent final status: {final}")
    finally:
        _close(ctx_b)


def check_submissions_denied(page, browser, sub_cls, create, tc, role, control_role=ROLE_FORM_MANAGER):
    """`role` (signed in) must not see submission data: our QCTEST submission
    is absent from its list and it is offered no review action. Positive
    control: `control_role` sees the same record in the same run."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, control_role)
    sub.open_list(role)
    assert CmsLoginPage(page).login_succeeded(), f"{role} is not signed in; a denial would prove nothing"
    row = sub.find_row(needle, role, timeout_s=10)
    assert row is None, (
        f"{role} can see the submission {needle!r} (actions {sub.row_actions(row)}); the case expects access denied"
    )
    for a in ("approve", "reject", "view"):
        assert sub.page.locator(f"[data-qc-oel-{a}]").count() == 0, f"{role} is offered submission action {a!r}"


def check_submissions_anonymous(browser, sub_cls):
    """Logged out: the submissions listing URL renders no submission data and
    no review action; it is refused or sent to sign-in."""
    ctx, anon = _anon(browser)
    try:
        sub = sub_cls(anon)
        resp = anon.goto(sub.manage_url(), wait_until="domcontentloaded")
        anon.wait_for_timeout(4000)
        for a in ("approve", "reject", "view"):
            assert anon.locator(f"[data-qc-oel-{a}]").count() == 0, f"anonymous visitor is offered {a!r}"
        assert anon.locator("table tbody tr td").count() == 0, "anonymous visitor sees submission rows"
        assert (resp is not None and resp.status in (401, 403, 404)) or CmsLoginPage(anon).login_form_visible() or (
            "sign in" in anon.locator("body").inner_text().casefold()), (
            f"anonymous request was neither refused nor sent to sign-in (HTTP {resp.status if resp else '?'})")
    finally:
        _close(ctx)


def check_duplicate_blocked(page, browser, sub_cls, tc, role=ROLE_FORM_MANAGER):
    """BCMR: a second submission with the same Email + Company Name as our
    Pending QCTEST request is blocked at the UI, and the listing holds exactly
    one record for it."""
    from web.pages.business_council_membership.business_council_membership_page import (
        BusinessCouncilMembershipPage,
    )

    company = create_bcmr_submission(browser, tc)
    ctx, anon = _anon(browser)
    try:
        bc = BusinessCouncilMembershipPage(anon)
        bc.open_membership_request(locale="en")
        bc.fill_form({"country_1": "GB", "country_2": "DE", "country_3": "FR", "country_4": "IT",
                      "applicant_name": f"QCTEST-{tc}-{RUN}", "company_name": company, "cr_number": "1234567",
                      "owner_name": "QCTEST Owner", "email": f"qctest.{tc}.{RUN}@example.com",
                      "mobile_number": "55123456", "company_activity": "QCTEST activity"})
        bc.submit()
        bc.wait_for_submit_outcome(45000)
        dup_ok = bc.is_confirmation_visible()
    finally:
        _close(ctx)
    sub = sub_cls(page)
    _found(sub, company, role)
    n = sub.page.locator(f'{sub.ROW}:has-text("{company}")').count()
    assert not dup_ok, "the duplicate submission was accepted by the public form (no block at the UI)"
    assert n == 1, f"the listing holds {n} records for {company!r}, expected exactly 1"


# ---- lookup values (Committee Lookup Status) ------------------------------
def _join_options(anon, locale="en") -> list[list[str]]:
    anon.goto(web_url(JOIN_PATH, locale=locale), wait_until="domcontentloaded")
    anon.locator("#qc-cj-sectorCommittee").wait_for(state="attached", timeout=25000)
    return anon.evaluate("() => [...document.querySelectorAll('#qc-cj-sectorCommittee option')].map(o => [o.value, o.text.trim()])")


def _wait_option(anon, key, present, timeout=PUBLIC_POLL_S):
    deadline = time.monotonic() + timeout
    while True:
        opts = _join_options(anon)
        seen = any(v == key for v, _ in opts)
        if seen == present or time.monotonic() > deadline:
            return seen, opts
        anon.wait_for_timeout(3000)


def _publish_lookup(lk, key, label):
    lk.open_form(ROLE_EDITOR)
    lk.fill_required(key)
    lk.fill("label_en", label)
    lk.fill("label_ar", f"{label} AR")
    lk.submit_for_review()
    assert lk.id_for(key), f"lookup {key!r} was not saved ({lk.save_counts()})"
    st = lk.status_of(key, ROLE_EDITOR)
    assert st == STATUS_PUBLISHED, f"lookup {key!r} is {st!r} after the Editor submit"


def check_lookup_added_public(page, browser, lk_cls, tc, label="Technology"):
    """A new Active QCTEST Sector/Committee lookup value appears in the public
    dropdown with no deployment."""
    lk = lk_cls(page)
    key = title(tc, "lookup")
    shown = f"QCTEST-{tc} {label}"
    ctx, anon = _anon(browser)
    try:
        _publish_lookup(lk, key, shown)
        seen, opts = _wait_option(anon, key, True)
        assert seen, f"{shown!r} (key {key!r}) is not offered in the public dropdown: {[o[1] for o in opts]!r}"
    finally:
        _delete(lk, key)
        _close(ctx)


def check_lookup_deactivated(page, browser, lk_cls, sub_cls, tc, approve_after=False):
    """Re-expressed on disposable data (the real 'Insurance' value is never
    touched): a QCTEST lookup value is used by our QCTEST submission, then set
    Inactive. It leaves the public dropdown; the submission keeps showing it
    (and, with approve_after, can still be approved)."""
    lk = lk_cls(page)
    key = title(tc, "lookup")
    shown = f"QCTEST-{tc} Insurance"
    ctx, anon = _anon(browser)
    try:
        _publish_lookup(lk, key, shown)
        seen, _ = _wait_option(anon, key, True)
        assert seen, f"precondition: {key!r} never reached the public dropdown"
        needle = create_join_submission(browser, tc, sector_value=key)
        sub = sub_cls(page)
        _found(sub, needle, ROLE_FORM_MANAGER)
        lk.open_list(ROLE_EDITOR)
        lk.open_entry_by_edit_link(key)
        lk.fill("active_state", "Inactive")
        lk.submit_for_review()
        gone, opts = _wait_option(anon, key, False)
        assert not gone, f"the Inactive value {key!r} is still offered in the public dropdown"
        text = sub.view_text(needle, ROLE_FORM_MANAGER)
        assert key in text or shown in text, (
            f"the submission no longer shows its Sector/Committee value {shown!r} / {key!r}: {text[:300]!r}")
        _assert_status(sub, needle, REQ_PENDING)
        if approve_after:
            sub.approve(needle)
            _assert_status(sub, needle, REQ_APPROVED)
            pytest.skip(EMAIL_NOT_OBSERVABLE)
    finally:
        _delete(lk, key)
        _close(ctx)


# ===========================================================================
# Authoring helpers beyond ck / bk
# ===========================================================================
def check_ws_refused(page, admin_cls, tc, key, locale="en", files=None, value="   "):
    """Whitespace-only (or any `value`) on one language side of `key`, every
    other required field valid: Submit is refused (positive signal) and
    nothing is Published. Active Status is left unticked (singleton-safe)."""
    admin = admin_cls(page)
    spec = admin_cls.FIELDS[key]
    t = title(tc, f"ws-{locale}")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(t, skip=(key,) if key != admin_cls.TITLE_FIELD else (), files=files)
        if locale == "ar":
            if key != admin_cls.TITLE_FIELD:
                admin.fill(key, spec.default or f"QCTEST {tc}")
            admin.fill(key, value, locale="ar")
        else:
            if key != admin_cls.TITLE_FIELD:
                if spec.bilingual:
                    admin.fill(key, spec.default_ar or "قيمة اختبار", locale="ar")
                admin.fill(key, value)
            else:
                admin.fill(key, value)
        admin.submit_for_review()
        refused = admin.refusal_visible()
        status = admin.status_of(t, ROLE_EDITOR) if key != admin_cls.TITLE_FIELD else ""
        assert refused, f"{key} {locale.upper()}={value!r}: Submit raised no refusal (status {status or 'n/a'!r})"
        assert status != STATUS_PUBLISHED, f"{key} {locale.upper()}={value!r}: the record was Published"
    finally:
        _delete(admin, t)


def check_number_not_overridable(page, admin_cls, tc, key, value="99"):
    """The case: the number is auto-generated and a typed value does not stick.
    The input must be read-only / disabled, or reject the typed value."""
    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    box = page.get_by_role("spinbutton", name=admin.label_pattern(admin_cls.FIELDS[key].label)).first
    editable = box.is_editable()
    if editable:
        box.fill(value)
    got = box.input_value()
    assert not editable or got != value, (
        f"{admin_cls.FIELDS[key].label} is an editable input that accepts a manual value ({got!r}); "
        "the case expects a system-generated number that cannot be overridden"
    )


def check_rtl_input(page, admin_cls, key, text):
    """The AR input of `key` is right-to-left and holds the typed Arabic
    unchanged (nothing is saved)."""
    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    box = page.get_by_role("textbox", name=admin.label_pattern(admin_cls.FIELDS[key].ar_label())).first
    box.click()
    box.fill("")
    box.press_sequentially(text)
    direction = box.evaluate("e => e.getAttribute('dir') || getComputedStyle(e).direction")
    assert direction == "rtl", f"AR {admin_cls.FIELDS[key].label} input direction is {direction!r}"
    assert box.input_value() == text, f"typed Arabic was altered: {box.input_value()!r}"


def check_anonymous_write_refused(browser, plural, body: dict, probe=None):
    """A logged-out POST to /o/c/<plural> is refused (401/403) and nothing is
    created; with `probe` the public page does not show the value."""
    ctx, anon = _anon(browser)
    try:
        anon.goto(web_url(SC_PATH, locale="en"), wait_until="domcontentloaded")
        status, text = anon.evaluate(
            """async ([u, b]) => { const r = await fetch(u, {method: 'POST', credentials: 'same-origin',
                 headers: {'content-type': 'application/json', accept: 'application/json'}, body: b});
                 return [r.status, (await r.text()).slice(0, 300)]; }""",
            [control_panel_url(f"/o/c/{plural}"), json.dumps(body)])
        print(f"anonymous POST /o/c/{plural}: HTTP {status} {text[:120]!r}")
        if 200 <= status < 300:
            log_leftover(f"ANON-CREATED {plural}: {text[:200]}")
        assert status in (401, 403), f"anonymous write answered HTTP {status} (expected 401/403): {text[:160]!r}"
        if probe:
            name = next(iter(body.values()))
            assert not probe(anon, name, False), f"{name!r} appears on the public page"
    finally:
        _close(ctx)


def check_expired_session_refused(page, admin_cls, tc, probe=None, browser=None):
    """Editor fills a QCTEST record, the session cookies are removed, then
    Submit: the request is refused / sent to sign-in and nothing is stored."""
    admin = admin_cls(page)
    t = title(tc, "expired")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(t, files=None if admin_cls.FIELDS.get("card_icon") is None
                            or not admin_cls.FIELDS["card_icon"].required else {"card_icon": VALID_PNG})
        page.context.clear_cookies()
        try:
            admin.submit_for_review()
        except Exception:  # noqa: BLE001 - a redirect to sign-in may abort the watch
            pass
        page.wait_for_timeout(3000)
        on_login = CmsLoginPage(page).login_form_visible() or "login" in page.url
        from cms.pages.control_panel import login_page as _lp
        _lp._SESSION_OWNER.pop(page, None)
        from cms.pages.certificate_of_origin import fragment_form_mixin as _ffm
        _ffm._ROLE_COOKIES.clear()
        exists = admin.entry_exists(t, ROLE_EDITOR)
        assert not exists, f"{t!r} was stored although the session had expired"
        print(f"[tc_{tc}] expired-session submit: redirected to sign-in={on_login}")
        if probe and browser:
            ctx, anon = _anon(browser)
            try:
                assert not probe(anon, t, False), f"{t!r} reached the public page"
            finally:
                _close(ctx)
    finally:
        _delete(admin, t)


def check_form_fields(page, admin_cls, keys, role=ROLE_EDITOR):
    """The role opens the create form and every listed field is present and
    editable (Save / Submit offered)."""
    admin = admin_cls(page)
    admin.open_form(role)
    missing = [admin_cls.FIELDS[k].label for k in keys if not admin.field_present(k)]
    assert not missing, f"{admin_cls.SIDEBAR_LABEL} form lacks {missing!r}"
    assert page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).count(), "no submit control is offered"


def check_role_no_form(page, admin_cls, role, positive_role=ROLE_EDITOR):
    """`role` opens the object's manage URL and is not given the authoring
    form; positive control: `positive_role` is given it at the same URL in the
    same run (so the denial is not a missing-form config gap)."""
    admin = admin_cls(page)
    admin.open_form(positive_role)
    assert page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).count(), f"control: {positive_role} got no form"
    admin.sign_in(role)
    assert CmsLoginPage(page).login_succeeded(), f"{role} did not sign in"
    page.goto(admin.manage_url(), wait_until="domcontentloaded")
    page.wait_for_timeout(6000)
    add = page.locator('button:has-text("+ Add New"), a:has-text("+ Add New")')
    if add.count():
        try:
            add.first.click(timeout=5000)
            page.wait_for_timeout(4000)
        except Exception:  # noqa: BLE001
            pass
    editable = page.locator(f"{admin.SUBMIT_FOR_REVIEW_BUTTON}:not([disabled])").count()
    assert editable == 0, f"{role} is given an enabled submit on {admin_cls.SIDEBAR_LABEL}"
    for a in ("publish", "unpublish", "delete"):
        assert page.locator(f"[data-qc-oel-{a}]").count() == 0, f"{role} is offered row action {a!r}"


def check_icon_picker(page, admin_cls, key):
    """The case selects an icon from an allowed icon SET. The field must offer
    a picker of predefined icons (not only a file upload)."""
    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    label = admin_cls.FIELDS[key].label
    upload = page.get_by_role("textbox", name=f"{label} Select File").count()
    picker = page.get_by_role("combobox", name=admin.label_pattern(label)).count() + page.get_by_role(
        "radiogroup", name=admin.label_pattern(label)).count()
    assert picker, (f"{label} offers no icon-set picker (file upload control present: {bool(upload)}); "
                    "the case selects a predefined icon")


def check_order_first(page, browser, admin_cls, tc, item_sel, expand=None, order="1", files=None, extra=None):
    """A Published QCTEST record with Display Order `order` (below every live
    record) is the FIRST item of its public list."""
    admin = admin_cls(page)
    t = title(tc, "first")
    ctx, anon = _anon(browser)
    try:
        bk._publish(admin, t, files=files, extra={"display_order": order, **(extra or {})})
        deadline = time.monotonic() + PUBLIC_POLL_S
        while True:
            items = sc_list(anon, item_sel, expand)
            if (items and t in items[0]) or time.monotonic() > deadline:
                break
            anon.wait_for_timeout(3000)
        assert items and t in items[0], f"{t!r} (order {order}) is not first: {items[:3]!r}"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_sequential_numbers(browser, num_sel, expand=None):
    """Public numbers read 01, 02, ... with no gap or duplicate."""
    ctx, anon = _anon(browser)
    try:
        nums = sc_list(anon, num_sel, expand)
        assert nums, "no numbered items rendered"
        want = [f"{i:02d}" for i in range(1, len(nums) + 1)]
        assert nums == want, f"numbers are {nums!r}, expected {want!r}"
    finally:
        _close(ctx)


def check_section_public(browser, section, texts=()):
    """The page section is rendered to a logged-out visitor (with its texts)."""
    ctx, anon = _anon(browser)
    try:
        sc_text(anon)
        assert anon.locator(section).count() and anon.locator(section).first.is_visible(), f"{section} is not shown"
        body = squash(anon.locator(section).first.inner_text())
        for t in texts:
            assert t in body, f"{section} does not show {t!r}"
    finally:
        _close(ctx)


def check_missing_refused(page, admin_cls, tc, key, files=None):
    """`key` left empty, every other required field valid, Active / Visible
    left unticked (singleton-safe): Submit must be refused (positive signal)
    and nothing Published."""
    admin = admin_cls(page)
    t = title(tc, "missing")
    try:
        admin.open_form(ROLE_EDITOR)
        admin.fill_required(t, skip=(key,), files=files)
        admin.submit_for_review()
        refused = admin.refusal_visible()
        status = admin.status_of(t, ROLE_EDITOR)
        assert refused, f"{admin_cls.FIELDS[key].label} empty: Submit raised no refusal (status {status or 'absent'!r})"
        assert status != STATUS_PUBLISHED, f"{admin_cls.FIELDS[key].label} empty: the record was Published"
    finally:
        _delete(admin, t)


_SIZE_RE = r"accepts files up to|no larger than|too large|exceeds|not (an )?allowed|unsupported|invalid file|accepts only"


def _pick(page, admin_cls, tc, key, fixture, files=None):
    import re as _re

    from core.utils.waits import WaitTimeoutError, wait_until

    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    label = admin_cls.FIELDS[key].label
    seen = {"msg": "", "readout": None}
    try:
        admin.upload(key, fixture, tag=str(tc))
    except Exception as exc:  # noqa: BLE001 - the picker itself refusing the file
        seen["msg"] = f"picker refused: {str(exc)[:120]}"
        return admin, seen

    def _settled():
        texts = page.locator(".alert-danger, .form-feedback-item, [role=alert]").all_inner_texts()
        hit = [" ".join(t.split()) for t in texts if _re.search(_SIZE_RE, t, _re.I)]
        seen["msg"] = hit[0] if hit else ""
        try:
            seen["readout"] = admin.uploaded_filename(label)
        except Exception:  # noqa: BLE001
            seen["readout"] = None
        return bool(seen["msg"]) or seen["readout"] == "" or bool(seen["readout"])

    try:
        wait_until(_settled, timeout=15.0, poll=0.5, message="no upload outcome")
        page.wait_for_timeout(1500)  # the size check runs after the readout (b9 probe); re-read once
        _settled()
    except WaitTimeoutError:
        pass
    print(f"[tc_{tc}] {key} <- {Path(fixture).name}: message={seen['msg']!r} readout={seen['readout']!r}")
    return admin, seen


def check_pick_refused(page, admin_cls, tc, key, fixture, files=None):
    """An unsupported type / over-size file is refused at the picker: a
    refusal message, or the field ends up with no file attached. Nothing is
    saved (drafts-off record types cannot hold a draft)."""
    _, seen = _pick(page, admin_cls, tc, key, fixture, files)
    assert seen["msg"] or not seen["readout"], (
        f"{key}: {Path(fixture).name} stayed attached ({seen['readout']!r}) with no refusal message")


def check_pick_accepted(page, admin_cls, tc, key, fixture, files=None):
    """A file within the stated limit is accepted by the picker: attached, no
    refusal message. Nothing is saved."""
    _, seen = _pick(page, admin_cls, tc, key, fixture, files)
    assert not seen["msg"] and seen["readout"], (
        f"{key}: {Path(fixture).name} was not accepted (message {seen['msg']!r}, readout {seen['readout']!r})")


def check_draft_available(page, admin_cls, role=ROLE_EDITOR):
    """The case saves the page as a Draft: the form must offer an enabled
    Save as Draft to `role`."""
    admin = admin_cls(page)
    admin.open_form(role)
    btn = page.locator(admin.SAVE_AS_DRAFT_BUTTON).first
    tip = (btn.get_attribute("title") or "") if btn.count() else ""
    ok = btn.count() and btn.is_visible() and btn.is_enabled()
    assert ok, (f"{admin_cls.SIDEBAR_LABEL}: Save as Draft is not available to {role} "
                f"(visible={btn.is_visible() if btn.count() else False}, tooltip {tip[:120]!r}); the case saves a Draft")


# ---- QAFL public wizard ------------------------------------------------------
_QAFL_FILL_JS = r"""([tc, run, company]) => {
  const vis = e => !!(e.offsetParent || e.getClientRects().length);
  const lab = e => ((e.labels && e.labels[0] && e.labels[0].innerText) || e.getAttribute('aria-label') ||
                    e.placeholder || e.name || e.id || '').toLowerCase();
  const set = (e, v) => { const p = Object.getPrototypeOf(e); const d = Object.getOwnPropertyDescriptor(p, 'value');
                          d.set.call(e, v); e.dispatchEvent(new Event('input', {bubbles: true}));
                          e.dispatchEvent(new Event('change', {bubbles: true})); e.dispatchEvent(new Event('blur', {bubbles: true})); };
  // the wizard's own form (the first <form> on the page is the header search)
  const root = [...document.querySelectorAll('form')].find(f => /Next|Submit/.test(f.innerText) && f.querySelector('input[type=file], select')) || document;
  const done = [];
  for (const e of root.querySelectorAll('input, select, textarea')) {
    if (!vis(e) || e.disabled || e.readOnly) continue;
    const l = lab(e), t = (e.type || '').toLowerCase();
    if (['hidden', 'file', 'submit', 'button', 'search', 'checkbox', 'radio'].includes(t)) continue;
    if (e.value && e.tagName !== 'SELECT') continue;
    let v;
    if (e.tagName === 'SELECT') { const o = [...e.options].find(o => o.value); if (o) { e.value = o.value; e.dispatchEvent(new Event('change', {bubbles: true})); done.push(l + '=' + o.text); } continue; }
    if (t === 'email') v = 'qctest.' + tc + '.' + run + '@example.com';
    else if (t === 'url' || /website|url/.test(l)) v = 'https://example.com';
    else if (/arabic/.test(l)) v = 'شركة اختبار';
    else if (/english name|company name|legal name/.test(l)) v = company;
    else if (/mobile/.test(l)) v = '33123456';
    else if (/phone|tel|fax/.test(l)) v = '+974 33123456';
    else if (/number|no\.|cr |count|license|licence|p\.?o|zone|street|building|year/.test(l) || t === 'number' || t === 'tel') v = '1234567';
    else if (/date/.test(l) || t === 'date') v = '2026-10-01';
    else if (/name/.test(l)) v = 'QCTEST-' + tc + '-' + run + ' Person';
    else v = 'QCTEST-' + tc + ' value';
    set(e, v); done.push(l + '=' + v);
  }
  const groups = {};
  for (const r of root.querySelectorAll('input[type=radio]')) if (vis(r) || vis(r.parentElement)) groups[r.name] = groups[r.name] || r;
  for (const r of Object.values(groups)) {
    const all = [...root.querySelectorAll('input[type=radio]')].filter(x => x.name === r.name);
    if (!all.some(x => x.checked)) { r.click(); done.push('radio ' + r.name); }
  }
  for (const c of root.querySelectorAll('input[type=checkbox]')) if ((vis(c) || vis(c.parentElement)) && !c.checked && c.required) { c.click(); done.push('checkbox ' + c.name); }
  return done;
}"""


def create_qafl_submission(browser, tc, docs=None) -> str:
    """Walk the PUBLIC QAFL 5-step wizard logged out with a QCTEST identity and
    small generated PDF documents; returns the QCTEST company name. Skips the
    test with the exact reason when the wizard cannot be completed."""
    company = f"QCTEST-{tc}-{RUN} QAFL Co"
    pdf = docs or runtime_fixture("qafl_doc_100kb.pdf", "pdf", 100 * 1024)
    ctx, anon = _anon(browser)
    try:
        anon.goto(web_url(QAFL_PATH, locale="en"), wait_until="domcontentloaded")
        anon.get_by_role("button", name="Next").first.wait_for(state="visible", timeout=30000)
        for _ in range(7):
            anon.evaluate(_QAFL_FILL_JS, [str(tc), RUN, company])
            for f in anon.locator("form input[type=file]").all():
                try:
                    if f.is_visible() or f.locator("xpath=..").is_visible():
                        if not f.evaluate("e => e.files && e.files.length"):
                            f.set_input_files(pdf)
                except Exception:  # noqa: BLE001
                    pass
            submit = anon.locator("form button[type=submit]:visible").filter(has_text="Submit")
            nxt = anon.get_by_role("button", name="Next")
            if submit.count():
                submit.first.click()
                break
            if nxt.count() and nxt.first.is_visible():
                nxt.first.click()
                anon.wait_for_timeout(1500)
            else:
                break
        try:
            anon.get_by_text("submitted successfully", exact=False).first.wait_for(state="visible", timeout=45000)
        except Exception:  # noqa: BLE001
            errs = [squash(t) for t in anon.locator(
                ".qc-field__error:visible, [class*=error]:visible, [role=alert]:visible").all_inner_texts() if t.strip()][:6]
            try:
                import os as _os
                _d = "reports/bug-evidence/130718-qafl-wizard"
                _os.makedirs(_d, exist_ok=True)
                anon.screenshot(path=f"{_d}/wizard_end_{tc}.png", full_page=True)
            except Exception:  # noqa: BLE001
                pass
            pytest.skip("QCTEST submission could not be created through the public QAFL form "
                        f"(5-step wizard, reCAPTCHA Enterprise): it did not confirm a submission; visible errors {errs!r}")
        return company
    finally:
        _close(ctx)


def check_author_cannot_publish(page, admin_cls, tc, files=None):
    """Site Content Author creates a QCTEST entry (Active / Visible unticked:
    singleton-safe) and submits: it never reaches Published (read BY ID as
    Editor) and the Author is offered no Publish / Approve row action."""
    admin = admin_cls(page)
    t = title(tc, "author")
    try:
        admin.open_form(ROLE_AUTHOR)
        assert not admin.has_admin_toolbar(), "precondition: the Author session has the admin toolbar"
        admin.fill_required(t, files=files)
        admin.submit_for_review()
        if admin.id_for(t):
            st = admin.status_of(t, ROLE_EDITOR)
            assert st != STATUS_PUBLISHED, f"Site Content Author published {t!r} directly"
            admin.open_list(ROLE_AUTHOR)
            for a in ("publish", "approve"):
                assert not admin.row_offers_action(t, a), f"Author is offered {a!r} on {t!r}"
        else:
            assert admin.refusal_visible(), "Author submit stored nothing and showed no refusal"
    finally:
        _delete(admin, t)


def check_live_singleton_public(page, browser, admin_cls, live_id, path, json_key):
    """Read-only: the live singleton entry (by ID) is Published with its
    Active / Visible gate ticked, and a logged-out visitor sees its title."""
    admin = admin_cls(page)
    admin._switch_role(ROLE_EDITOR)
    admin.open(admin._manage_url(locale="en"))
    st = admin.status_by_id(live_id, admin.PLURAL)
    status, text = admin._api("GET", f"/o/c/{admin.PLURAL}/{live_id}")
    data = json.loads(text) if status == 200 else {}
    act = data.get("pageActiveStatus", data.get("pageVisible"))
    assert st == STATUS_PUBLISHED, f"precondition: live entry {live_id} is {st!r}"
    assert act is True, f"precondition: live entry {live_id} active gate is {act!r}"
    want = data.get(json_key) or ""
    ctx, anon = _anon(browser)
    try:
        assert want and page_probe(path)(anon, want), f"the live page does not render {want!r} to a visitor"
    finally:
        _close(ctx)


def check_request_status_control(page, browser, sub_cls, create, tc, options=("pending", "approved", "rejected")):
    """The record offers a Request Status dropdown with exactly the case's
    options."""
    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, ROLE_FORM_MANAGER)
    sub.view_text(needle)
    sel = page.locator("[role=dialog]:visible select, [role=dialog]:visible [role=combobox]")
    if not sel.count():
        page.keyboard.press("Escape")
        actions = sub.row_actions(sub.find_row(needle, ROLE_FORM_MANAGER))
        raise AssertionError("the submission offers no Request Status dropdown (review is by row actions "
                             f"{actions!r})")
    got = sorted(o.strip().casefold() for o in sel.first.locator("option").all_inner_texts() if o.strip())
    assert got == sorted(options), f"Request Status options {got!r} != {sorted(options)!r}"


def check_submission_date(page, browser, sub_cls, create, tc):
    """The stored record carries today's Submission Date (the public form has
    no input for it)."""
    import datetime as _dt
    import re as _re

    sub = sub_cls(page)
    needle = create(browser, tc)
    _found(sub, needle, ROLE_FORM_MANAGER)
    text = sub.view_text(needle)
    d = _dt.date.today()
    pats = [f"{d.month}/{d.day}/{d.year}", f"{d.day}/{d.month}/{d.year}", d.isoformat(), f"{d:%d/%m/%Y}", f"{d:%m/%d/%Y}"]
    assert _re.search("submission date", text, _re.I), f"the record shows no Submission Date: {text[:300]!r}"
    assert any(p in text for p in pats), f"the record's Submission Date is not today's ({pats[0]}): {text[:400]!r}"


def check_no_cms_field(page, admin_cls, key):
    """The case: the value comes from the site menu and NO manual editing field
    is offered in the CMS for it."""
    admin = admin_cls(page)
    admin.open_form(ROLE_EDITOR)
    assert not admin.field_present(key), (
        f"the CMS form offers a manual '{admin_cls.FIELDS[key].label}' field; the case expects none")


# ===========================================================================
# Sectoral Committees list objects (leader cards, committees, mandates, CTAs)
# ===========================================================================
LEAD = "div.qc-sc-lead-panel"
LEADER = "article.qc-sc-leader"
LEADER_NAME = "p.qc-sc-leader-name"
LEADER_NUM = "span.qc-sc-leader-num"
DIRECTORY = "section.qc-sc-directory"
ROW_TITLE = ".qc-sc-row-title"
ROW_NUM = "span.qc-sc-row-num"
CTA = "section.qc-sc-cta"
CTA_TITLE = ".qc-sc-cta-title"


def open_sc_expanded(expand=None):
    def _open(anon):
        sc = _open_sc(anon)
        _expand(anon, sc, expand)
    return _open


def _publish(admin, t, files=None, extra=None, ar_extra=None, active=True):
    """Editor create -> Submit; Published asserted BY ID when Active ticked."""
    admin.open_form(ROLE_EDITOR)
    admin.fill_required(t, active=active, files=files)
    for k, v in (extra or {}).items():
        admin.fill(k, v)
    for k, v in (ar_extra or {}).items():
        admin.fill(k, v, locale="ar")
    admin.submit_for_review()
    eid = admin.id_for(t)
    assert eid, f"{t!r}: the Editor submit stored no record ({admin.save_counts()})"
    if active:
        st = admin.status_of(t, ROLE_EDITOR)
        assert st == STATUS_PUBLISHED, f"{t!r} (id {eid}) is {st or 'unreadable'!r} after an Editor submit"


def _gates(admin, t) -> str:
    eid = admin.id_for(t)
    st = admin.status_by_id(eid, admin.plural_for(t)) if eid else ""
    data = admin.entry_json(t) or {}
    act = {k: v for k, v in data.items() if "active" in k.lower()}
    return f"id={eid} status={st!r} active={act!r}"


def check_render_bilingual(page, browser, admin_cls, tc, key, en, ar, section=None, expand=None, files=None,
                           extra=None):
    """Editor publishes a QCTEST record (Active ticked) with `key` = en / ar; a
    logged-out visitor sees `en` on the EN page and `ar` on the AR page."""
    admin = admin_cls(page)
    is_title = key == admin_cls.TITLE_FIELD
    t = title(tc, en.replace(" ", "-")[:30]) if is_title else title(tc, "render")
    if is_title:
        en, ar = t, f"{ar} {RUN}"
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, files=files, extra={**({} if is_title else {key: en}), **(extra or {})},
                 ar_extra={key: ar})
        assert sc_probe(section, expand)(anon, en), (
            f"{key}={en!r} is Published + Active but not on the EN public page ({_gates(admin, t)})")
        assert sc_probe(section, expand, locale="ar")(anon, ar), (
            f"{key} AR={ar!r} is not on the AR public page ({_gates(admin, t)})")
    finally:
        _delete(admin, t)
        _close(ctx)


def check_inactive_hidden(page, browser, admin_cls, tc, section=None, expand=None, files=None):
    """Editor submits a QCTEST record with Active Status UNTICKED: a logged-out
    visitor never sees it (whatever workflow state the unticked submit lands on)."""
    admin = admin_cls(page)
    t = title(tc, "inactive")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, files=files, active=False)
        print(f"[tc_{tc}] inactive record gates: {_gates(admin, t)}")
        assert not sc_probe(section, expand)(anon, t, False), f"{t!r} (Active unticked) is shown to a visitor"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_active_shown(page, browser, admin_cls, tc, section=None, expand=None, files=None):
    admin = admin_cls(page)
    t = title(tc, "active")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, files=files)
        data = admin.entry_json(t) or {}
        assert any(v is True for k, v in data.items() if "active" in k.lower()), f"Active gate not ticked: {_gates(admin, t)}"
        assert sc_probe(section, expand)(anon, t), f"{t!r} is Published + Active but not shown ({_gates(admin, t)})"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_edit_shows_new(page, browser, admin_cls, tc, key, new_value, section=None, expand=None, files=None):
    """Published QCTEST record; `key` edited and re-submitted: the visitor sees
    the new value and (for the title) not the old one."""
    admin = admin_cls(page)
    t = title(tc, "edit")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, files=files)
        probe = sc_probe(section, expand)
        assert probe(anon, t), f"precondition: {t!r} not shown after publish ({_gates(admin, t)})"
        new = f"{t} {new_value}" if key == admin_cls.TITLE_FIELD else new_value
        admin.open_list(ROLE_EDITOR)
        admin.open_entry_by_edit_link(t)
        admin.fill(key, new)
        admin.submit_for_review()
        st = admin.status_of(t, ROLE_EDITOR)
        assert st == STATUS_PUBLISHED, f"{t!r} is {st!r} after editing"
        assert probe(anon, new), f"the edited value {new!r} is not shown ({_gates(admin, t)})"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_delete_hides(page, browser, admin_cls, tc, section=None, expand=None, files=None):
    admin = admin_cls(page)
    t = title(tc, "del")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, files=files)
        probe = sc_probe(section, expand)
        assert probe(anon, t), f"precondition: {t!r} not shown after publish"
        assert admin.delete_disposable(t), f"{t!r}: delete did not run"
        assert not admin.entry_exists(t, ROLE_EDITOR), f"{t!r} still listed after delete"
        assert not probe(anon, t, False), f"{t!r} still shown after delete"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_cta_navigates(page, browser, cta_cls, tc, target, files=None):
    admin = cta_cls(page)
    t = title(tc, "nav")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, files=files, extra={"target_url": target})
        assert sc_probe(CTA)(anon, t), f"{t!r} not shown in the CTA panel ({_gates(admin, t)})"
        card = anon.locator("a.qc-sc-cta-card").filter(has_text=t).first
        with anon.expect_navigation(timeout=30000):
            card.click()
        resp = anon.goto(anon.url, wait_until="domcontentloaded")
        assert target in anon.url, f"the card navigated to {anon.url!r}, not {target!r}"
        assert resp is not None and resp.status == 200, f"target answered HTTP {resp.status if resp else '?'}"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_new_committee_numbered(page, browser, item_cls, tc):
    """A QCTEST committee added last is listed with the next number, the list
    stays 01..N with no gap, and search still filters all rows."""
    admin = item_cls(page)
    t = title(tc, "c13")
    ctx, anon = _anon(browser)
    try:
        before = sc_list(anon, ROW_TITLE)
        _publish(admin, t)
        assert sc_probe(DIRECTORY)(anon, t), f"{t!r} not listed ({_gates(admin, t)})"
        titles, nums = sc_list(anon, ROW_TITLE), sc_list(anon, ROW_NUM)
        assert len(titles) == len(before) + 1, f"{len(titles)} rows, expected {len(before) + 1}"
        assert t in titles[-1], f"{t!r} is not the last row: {titles[-3:]!r}"
        assert nums == [f"{i:02d}" for i in range(1, len(nums) + 1)], f"numbers {nums!r}"
        assert nums[-1] == f"{len(before) + 1:02d}", f"last badge {nums[-1]!r}"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_delete_middle_renumbers(page, browser, item_cls, tc, order="450"):
    """A QCTEST committee placed mid-list (order 450) is deleted: the badges
    read 01..N again with no gap."""
    admin = item_cls(page)
    t = title(tc, "cmid")
    ctx, anon = _anon(browser)
    try:
        _publish(admin, t, extra={"display_order": order})
        assert sc_probe(DIRECTORY)(anon, t), f"{t!r} not listed"
        assert admin.delete_disposable(t), f"{t!r}: delete did not run"
        assert sc_probe(DIRECTORY)(anon, t, False) is False, f"{t!r} still listed"
        nums = sc_list(anon, ROW_NUM)
        assert nums == [f"{i:02d}" for i in range(1, len(nums) + 1)], f"numbers after delete {nums!r}"
    finally:
        _delete(admin, t)
        _close(ctx)


def check_mandate(page, browser, item_cls, mandate_cls, tc, mode):
    """QCTEST committee (Published, Active) with QCTEST mandate bullets linked
    through the Committee picker. mode: add | edit | reorder | remove | ar |
    remove_last. The checklist is read from the expanded committee row."""
    item, mand = item_cls(page), mandate_cls(page)
    c = title(tc, "cmte")
    b1, b2 = title(tc, "item-1"), title(tc, "item-2")
    made = []
    ctx, anon = _anon(browser)
    expand = ("row", c)

    def bullets(locale="en"):
        return sc_list(anon, "li.qc-sc-mandate-item", expand=("row", c if locale == "en" else c + " AR"), locale=locale)

    def wait_bullets(pred, locale="en"):
        deadline = time.monotonic() + PUBLIC_POLL_S
        while True:
            got = bullets(locale)
            if pred(got) or time.monotonic() > deadline:
                return got
            anon.wait_for_timeout(3000)

    try:
        _publish(item, c)
        assert sc_probe(DIRECTORY)(anon, c), f"precondition: committee {c!r} not listed ({_gates(item, c)})"
        _publish(mand, b1, extra={"committee": c, "display_order": "100"}, ar_extra={"bullet": f"بند اختبار 1 {RUN}"})
        made.append(b1)
        if mode == "remove_last":
            ok = mand.delete_disposable(b1)
            still = mand.entry_exists(b1, ROLE_EDITOR)
            assert still and not ok, "the only mandate bullet of a published committee was removed (the case expects a refusal)"
            return
        _publish(mand, b2, extra={"committee": c, "display_order": "200"}, ar_extra={"bullet": f"بند اختبار 2 {RUN}"})
        made.append(b2)
        got = wait_bullets(lambda g: len(g) >= 2)
        assert [b1 in got[0] if got else False, b2 in got[1] if len(got) > 1 else False] == [True, True], (
            f"checklist of {c!r} is {got!r}, expected [{b1!r}, {b2!r}]")
        if mode == "ar":
            ar = wait_bullets(lambda g: any(f"بند اختبار 1 {RUN}" in x for x in g), locale="ar")
            assert any(f"بند اختبار 1 {RUN}" in x for x in ar), f"AR checklist {ar!r} lacks the AR bullet"
        elif mode == "edit":
            new = f"{b2} edited"
            mand.open_list(ROLE_EDITOR)
            mand.open_entry_by_edit_link(b2)
            mand.fill("bullet", new)
            mand.submit_for_review()
            got = wait_bullets(lambda g: any(new in x for x in g))
            assert any(new in x for x in got), f"checklist {got!r} lacks the edited bullet {new!r}"
        elif mode == "reorder":
            mand.open_list(ROLE_EDITOR)
            mand.open_entry_by_edit_link(b2)
            mand.fill("display_order", "50")
            mand.submit_for_review()
            got = wait_bullets(lambda g: len(g) >= 2 and b2 in g[0])
            assert got and b2 in got[0] and b1 in got[1], f"checklist order {got!r}, expected bullet 2 first"
        elif mode == "remove":
            assert mand.delete_disposable(b1), f"{b1!r}: delete did not run"
            made.remove(b1)
            got = wait_bullets(lambda g: len(g) == 1)
            assert len(got) == 1 and b2 in got[0], f"checklist after removal {got!r}, expected only {b2!r}"
    finally:
        for b in made:
            _delete(mand, b)
        _delete(item, c)
        _close(ctx)


def check_form_fields_readonly(page, admin_cls, keys, role=ROLE_EDITOR):
    """Read-only: the role opens the object's manage page (a singleton shows
    its one record's edit form) and every listed field, EN and AR, is present.
    Nothing is typed or saved."""
    from cms.pages.partners_offers.partners_offers_admin_page import _Po

    admin = admin_cls(page)
    _Po._open_manage(admin, role, "en", form=False)
    page.locator(admin.SUBMIT_FOR_REVIEW_BUTTON).first.wait_for(state="visible", timeout=35000)
    missing = [admin_cls.FIELDS[k].label for k in keys if not admin.field_present(k)]
    assert not missing, f"{admin_cls.SIDEBAR_LABEL} form lacks {missing!r}"
    ar_missing = [admin_cls.FIELDS[k].label for k in keys if admin_cls.FIELDS[k].bilingual
                  and admin_cls.FIELDS[k].kind != "rich"
                  and not page.get_by_role("textbox", name=admin.label_pattern(admin_cls.FIELDS[k].ar_label())).count()]
    assert not ar_missing, f"{admin_cls.SIDEBAR_LABEL} form lacks the AR input of {ar_missing!r}"
